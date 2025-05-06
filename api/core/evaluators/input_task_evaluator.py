import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any, Literal, Protocol, Sequence

from pydantic import field_serializer
from typing_extensions import override
from workflowai import Run as ExternalTaskRun

from core.agents.evaluate_output import (
    EvaluateOutputTaskInput,
    EvaluateOutputTaskOutput,
)
from core.domain.agent_run import TaskRunIO
from core.domain.errors import DefaultError
from core.domain.evaluator_options import EvaluatorOptions
from core.domain.input_evaluation import InputEvaluation
from core.domain.run_identifier import RunIdentifier
from core.domain.task_evaluation import TaskEvaluation
from core.domain.task_evaluator import EvalV2Evaluator
from core.domain.task_example import SerializableTaskExample
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentInput, AgentOutput
from core.evaluators.abstract_evaluator import AbstractEvaluator, InvalidEvaluationError
from core.runners.workflowai.utils import FileWithKeyPath, download_file, extract_files
from core.utils.dicts import set_at_keypath
from core.utils.file_utils.file_utils import extract_text_from_file_base64


class InputTaskEvaluatorOptions(EvaluatorOptions):
    evaluator_id: str | None
    task_data: EvalV2Evaluator
    input_evaluation: InputEvaluation

    @field_serializer("input_evaluation", when_used="json")
    def input_evaluation_dump(self, input_evaluation: InputEvaluation):
        return input_evaluation.model_dump(mode="json", include={"id", "generated_by"}, exclude_none=True)


class InternalTasksForEvaluations(Protocol):
    async def describe_images(
        self,
        images: Sequence[FileWithKeyPath],
        instructions: str | None,
    ) -> list[str] | None: ...

    async def evaluate_output(
        self,
        task_input: EvaluateOutputTaskInput,
    ) -> ExternalTaskRun[EvaluateOutputTaskOutput]: ...


class InputTaskEvaluator(AbstractEvaluator[InputTaskEvaluatorOptions]):
    def __init__(
        self,
        task: SerializableTaskVariant,
        options: InputTaskEvaluatorOptions,
        internal_tasks: InternalTasksForEvaluations,
    ):
        super().__init__(options=options)
        self.internal_tasks = internal_tasks
        self.task = task

    @override
    def _definition_id(self) -> str:
        return f"{super()._definition_id()}/{self.options.input_evaluation.id}"

    @override
    @classmethod
    def name(cls) -> str:
        # TODO: use a proper name
        return "eval_v2"

    @override
    def _version(self) -> str:
        # TODO: use a proper version
        return "v1"

    def _combined_instructions(self):
        arr = [
            self.options.task_data.instructions,
            self.options.input_evaluation.evaluation_instruction,
        ]
        return (
            "\n\n".join(
                (a for a in arr if a),
            )
            or None
        )

    async def _replace_images_by_their_description(
        self,
        images: list[FileWithKeyPath],
        set_at_keypath: Callable[[list[str | int], Any], Awaitable[None]],
    ):
        try:
            descriptions = await self.internal_tasks.describe_images(images, instructions=self._combined_instructions())
        except Exception as e:
            raise e

        if not descriptions or len(descriptions) != len(images):
            raise DefaultError(
                "Number of descriptions does not match number of images",
                extras={"descriptions": descriptions},
            )

        for i, image in enumerate(images):
            await set_at_keypath(image.key_path, {"description": descriptions[i]})

    async def _safe_replace_text_files_by_their_content(
        self,
        file: FileWithKeyPath,
        set_at_keypath: Callable[[list[str | int], Any], Awaitable[None]],
    ):
        try:
            if not file.data:
                await download_file(file)
            content = extract_text_from_file_base64(file.data or "")
            await set_at_keypath(file.key_path, content)
        except Exception:
            self._logger.exception(
                "Failed to replace text file by its content",
                extra={"file": file.model_dump(exclude={"data"})},
            )

    async def _inline_text_files(
        self,
        text_files: list[FileWithKeyPath],
        set_at_keypath: Callable[[list[str | int], Any], Awaitable[None]],
    ):
        async with asyncio.TaskGroup() as tg:
            for file in text_files:
                tg.create_task(self._safe_replace_text_files_by_their_content(file, set_at_keypath))

    # Make sure we replace files when possible before evaluating
    async def _sanitize_files_in_input(self, files: list[FileWithKeyPath], task_input: AgentInput):
        # Separate files into images and others
        images: list[FileWithKeyPath] = []
        text_files: list[FileWithKeyPath] = []
        other_files: list[FileWithKeyPath] = []
        for file in files:
            if file.is_image or file.is_pdf:
                images.append(file)
            elif file.is_text:
                # We inline the text files
                text_files.append(file)
            else:
                other_files.append(file)

        if other_files:
            self._logger.warning(
                "Task input contains non-image files when evaluating",
                extra={"files": [f.model_dump(exclude={"data"}) for f in other_files]},
            )
            # In this case there are files we can't process so we just return an empty input
            # TODO: try and be smarter and replace the files we can ?
            # Actually multimodel tasks are pretty rare so ok to skip for now
            return None

        payload_lock = asyncio.Lock()

        async def _set_at_keypath(keypath: list[str | int], value: Any):
            async with payload_lock:
                set_at_keypath(task_input, keypath, value)

        try:
            await self._replace_images_by_their_description(images, _set_at_keypath)
            await self._inline_text_files(text_files, _set_at_keypath)
            return task_input
        except Exception as e:
            self._logger.error(
                "Failed to replace images by their description",
                extra={"images": [f.model_dump(exclude={"data"}) for f in images]},
                exc_info=e,
            )
            return None

    def _build_evaluation(
        self,
        score: float,
        positive_aspects: list[str] | None,
        negative_aspects: list[str] | None,
        confidence_score: float | None,
        run_identifier: RunIdentifier | None = None,
    ) -> TaskEvaluation:
        return TaskEvaluation(
            score=score,
            positive_aspects=positive_aspects,
            negative_aspects=negative_aspects,
            evaluator=self.definition,
            metadata={
                "confidence_score": confidence_score,
                "generated_by": run_identifier,
            },
        )

    async def _call_evaluation_task(
        self,
        evaluated_input: AgentInput | None,
        evaluated_output: AgentOutput,
    ) -> TaskEvaluation:
        task_input = EvaluateOutputTaskInput(
            task_input=json.dumps(evaluated_input) if evaluated_input else None,
            correct_outputs=[json.dumps(output) for output in self.options.input_evaluation.correct_outputs],
            incorrect_outputs=[json.dumps(output) for output in self.options.input_evaluation.incorrect_outputs],
            evaluation_instruction=self.options.task_data.instructions,
            input_evaluation_instruction=self.options.input_evaluation.evaluation_instruction,
            evaluated_output=json.dumps(evaluated_output),
        )

        evaluation_run = await self.internal_tasks.evaluate_output(task_input)
        evaluation = evaluation_run.output
        if evaluation.evaluation_result is None:
            raise InvalidEvaluationError("Evaluation result is not conclusive")

        return self._build_evaluation(
            score=evaluation.evaluation_result.to_score(),
            positive_aspects=evaluation.positive_aspects,
            negative_aspects=evaluation.negative_aspects,
            confidence_score=evaluation.confidence_score,
            run_identifier=RunIdentifier(
                tenant="workflowai",  # TODO: use dynamic value
                task_id=evaluation_run.agent_id,
                task_schema_id=evaluation_run.schema_id,
                run_id=evaluation_run.id,
            ),
        )

    async def _sanitize_input(self, input: AgentInput):
        # We extract files before sanitizing since storage_url is not in the json schema
        new_payload, _, files = extract_files(self.task.input_schema.json_schema, input)
        if not files:
            return self.task.input_schema.sanitize(input)

        sanitized_input = self.task.input_schema.sanitize(new_payload)
        return await self._sanitize_files_in_input(files, sanitized_input)

    @override
    async def evaluate(
        self,
        run: TaskRunIO,
        example: SerializableTaskExample | None = None,
    ) -> TaskEvaluation:
        evaluated_output = self.task.output_schema.sanitize(run.task_output)
        for correct_output in self.options.input_evaluation.correct_outputs:
            if correct_output == evaluated_output:
                return self._build_evaluation(
                    score=1.0,
                    positive_aspects=["Evaluated output is in correct outputs"],
                    negative_aspects=None,
                    confidence_score=1.0,
                )

        for incorrect_output in self.options.input_evaluation.incorrect_outputs:
            if incorrect_output == evaluated_output:
                return self._build_evaluation(
                    score=0.0,
                    negative_aspects=["Evaluated output is in incorrect outputs"],
                    positive_aspects=None,
                    confidence_score=1.0,
                )

        evaluated_input = await self._sanitize_input(run.task_input)
        return await self._call_evaluation_task(evaluated_input, evaluated_output)

    @classmethod
    def score_to_outcome(cls, score: float) -> Literal["positive", "negative", "unsure"]:
        if score == 1.0:
            return "positive"
        if score == 0.0:
            return "negative"
        return "unsure"

    @classmethod
    def parse_evaluation(cls, evaluation: TaskEvaluation):
        # This is only needed because we rely on the old evaluator format
        outcome = cls.score_to_outcome(evaluation.score)
        if evaluation.metadata:
            confidence_score = evaluation.metadata.get("confidence_score")
            run_identifier = evaluation.metadata.get("generated_by")
            if not isinstance(run_identifier, RunIdentifier):
                run_identifier = None
        else:
            confidence_score = None
            run_identifier = None

        # TODO: this was broken when we migrated to the new agent SDK. Run identifier and confidence score were not used
        # Anyway, if we ever need it, we should re-enable the log
        #
        # if confidence_score is None or run_identifier is None:
        #     logging.getLogger(__name__).error(
        #         "Evaluation metadata is missing confidence score or run identifier",
        #         extra={"evaluation": safe_dump_pydantic_model(evaluation)},
        #     )

        return (
            outcome,
            confidence_score,
            run_identifier,
        )
