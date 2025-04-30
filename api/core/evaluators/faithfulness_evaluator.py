from typing import Any

from typing_extensions import override

from core.agents.chat_faithfulness_check_task import (
    ChatFaithfulnessCheckTask,
    ChatFaithfulnessCheckTaskInput,
    ChatFaithfulnessCheckTaskOutput,
)
from core.domain.evaluator_options import EvaluatorOptions
from core.domain.task_evaluation import TaskEvaluation
from core.domain.task_evaluator import FaithfulnessEvaluator
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentInput, AgentOutput
from core.domain.version_reference import VersionReference
from core.evaluators.example_based_evaluator import ExampleBasedEvaluator
from core.utils.dicts import get_at_keypath


class FaithfulnessComputeOptions(EvaluatorOptions):
    config: FaithfulnessEvaluator


class FaithfulnessCompute(ExampleBasedEvaluator[FaithfulnessComputeOptions]):
    def __init__(
        self,
        task: SerializableTaskVariant,
        config: FaithfulnessEvaluator,
        name: str,
        id: str,
    ):
        super().__init__(options=FaithfulnessComputeOptions(config=config))
        self.task = task
        self._definition = TaskEvaluation.Evaluator(
            name=name,
            id=id,
            properties=self.options.config.model_dump(exclude_none=True),
            metric="faithfulness",
        )
        self._log_extras = {"eid": id}

    @override
    def _version(self) -> str:
        raise ValueError("_version should not be used")

    @override
    @classmethod
    def options_class(cls) -> type[FaithfulnessComputeOptions]:
        raise ValueError("options_class should not be used")

    @override
    @classmethod
    def build_options(cls, options: dict[str, Any] | None) -> FaithfulnessComputeOptions:
        raise ValueError("build_options should not be used")

    @classmethod
    def _score_from_faithfulness_category(
        cls,
        faithfulness_category: ChatFaithfulnessCheckTaskOutput.FaithfulnessCategory,
    ) -> float:
        return {
            ChatFaithfulnessCheckTaskOutput.FaithfulnessCategory.A: 0.5,  # assistant answer is lacking information of the expert answer but not opposed, score is 0.5
            ChatFaithfulnessCheckTaskOutput.FaithfulnessCategory.B: 1.0,  # TODO: check the rationale
            ChatFaithfulnessCheckTaskOutput.FaithfulnessCategory.C: 0.0,  # assistant answer is different from the expert answer, score is 0
            ChatFaithfulnessCheckTaskOutput.FaithfulnessCategory.D: 1.0,  # assistant answer is factually identical to the expert answer, score is 1
        }[faithfulness_category]

    async def _run_faithfulness_task(
        self,
        new_user_message: str,
        new_assistant_message: str,
        expert_answer: str,
    ) -> tuple[float, str]:
        from core.deprecated.workflowai import WorkflowAI

        wai = WorkflowAI.from_ctx()

        task = ChatFaithfulnessCheckTask()
        input = ChatFaithfulnessCheckTaskInput(
            new_user_message=new_user_message,
            new_assistant_answer=new_assistant_message,
            expert_answer=expert_answer,
        )
        properties = self.options.config.faithfulness_task_group_properties or TaskGroupProperties()
        group_ref = VersionReference(properties=properties)

        result = await wai.run(
            task,
            group=group_ref,
            input=input,
            trigger="evaluation",
        )

        score = self._score_from_faithfulness_category(result.faithfulness_category)
        return score, result.reason

    @override
    async def _compute_score(
        self,
        run_output: AgentOutput,
        example_output: AgentOutput,
        input: AgentInput,
    ) -> tuple[float, str]:
        new_user_message = get_at_keypath(input, self.options.config.new_user_message_keypath)
        new_assistant_message = get_at_keypath(run_output, self.options.config.new_assistant_answer_keypath)
        expert_answer = get_at_keypath(example_output, self.options.config.new_assistant_answer_keypath)

        return await self._run_faithfulness_task(new_user_message, new_assistant_message, expert_answer)
