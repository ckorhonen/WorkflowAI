import logging
from itertools import permutations
from numbers import Real
from typing import Any, Optional, Sequence, TypeVar

from typing_extensions import override

from core.domain.agent_run import AgentRun
from core.domain.evaluator_options import EvaluatorOptions
from core.domain.field_based_evaluation_config import (
    ArrayComparisonOptions,
    BaseComparisonOptions,
    FieldBasedEvaluationConfig,
    FieldComparisonOptions,
    NumberComparisonOptions,
    ObjectComparisonOptions,
    StringComparisonOptions,
)
from core.domain.task_evaluation import TaskEvaluation
from core.domain.task_example import SerializableTaskExample
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentInput, AgentOutput
from core.domain.version_reference import VersionReference
from core.domain.workflowai_interface import WorkflowAIInterface
from core.evaluators.example_based_evaluator import ExampleBasedEvaluator
from core.runners.workflowai.workflowai_options import TEXT_EQUIVALENCE_TASK_MODEL
from core.utils.models.dumps import safe_dump_pydantic_model
from core.utils.schemas import JsonSchema
from core.utils.strings import normalize
from core.utils.time_utils import are_time_str_equal


class FieldBasedCompareOptions(EvaluatorOptions):
    config: FieldBasedEvaluationConfig


_logger = logging.getLogger(__name__)


class EvaluationError:
    def __init__(self, message: str, path: list[str] | None = None):
        self.message = message
        self.path = path or []

    @property
    def keypath(self) -> str:
        return ".".join(self.path)

    def __str__(self) -> str:
        return f"Difference at {self.keypath}: {self.message}"


_O = TypeVar("_O", bound=BaseComparisonOptions)


class FieldBasedCompare(ExampleBasedEvaluator[FieldBasedCompareOptions]):
    def __init__(
        self,
        task: SerializableTaskVariant,
        config: FieldBasedEvaluationConfig,
        name: str,
        id: str,
        workflowai: WorkflowAIInterface | None = None,
    ):
        super().__init__(options=FieldBasedCompareOptions(config=config))
        self.task = task
        self._name = name
        self._definition = TaskEvaluation.Evaluator(
            name=name,
            id=id,
            properties=self.options.model_dump(exclude_none=True),
        )
        self._log_extras = {"eid": id}
        self.workflowai = workflowai

    @override
    def _version(self) -> str:
        raise ValueError("_version should not be used")

    @override
    @classmethod
    def options_class(cls) -> type[FieldBasedCompareOptions]:
        raise ValueError("options_class should not be used")

    @override
    @classmethod
    def build_options(cls, options: Optional[dict[str, Any]]) -> FieldBasedCompareOptions:
        raise ValueError("build_options should not be used")

    def _ensure_config(self, config: FieldComparisonOptions | None, config_cls: type[_O]) -> _O:
        if not config:
            return config_cls()

        if isinstance(config, config_cls):
            return config
        _logger.error(
            "Invalid field based config",
            extra={
                **self._log_extras,
                "config": safe_dump_pydantic_model(config),
                "config_cls": config_cls.__name__,
            },
        )
        return config_cls()

    def _add_errors(self, errors: dict[str, EvaluationError], new_errors: list[EvaluationError]) -> None:
        for error in new_errors:
            if error.keypath not in errors:
                errors[error.keypath] = error

    async def _compare_objects(
        self,
        expected: dict[str, Any],
        actual: dict[str, Any],
        config: FieldComparisonOptions | None,
        schema: JsonSchema,
        path: list[str] = [],
    ) -> list[EvaluationError]:
        obj_config = self._ensure_config(config, ObjectComparisonOptions)
        property_evaluations = obj_config.property_evaluations
        errors: dict[str, EvaluationError] = {}

        for key in expected.keys():
            key_is_ignored = (
                property_evaluations and key in property_evaluations and property_evaluations[key].ignore is True
            )
            if key_is_ignored:
                continue

            if key not in actual:
                self._add_errors(errors, [EvaluationError(f"Key {key} not found in actual object", path + [key])])
                continue
            sub_errors = await self.compare(
                expected[key],
                actual[key],
                property_evaluations.get(key) if property_evaluations else None,
                schema.child_schema(key),
                path + [key],
            )
            self._add_errors(errors, sub_errors)

        return list(errors.values())

    async def _compare_list_items(
        self,
        expected: Sequence[Any],
        actual: Sequence[Any],
        item_config: FieldComparisonOptions | None,
        schema: JsonSchema,
        path: list[str] = [],
    ) -> list[EvaluationError]:
        errors: dict[str, EvaluationError] = {}
        for i in range(len(expected)):
            sub_errors = await self.compare(expected[i], actual[i], item_config, schema, path + [str(i)])
            self._add_errors(errors, sub_errors)
        return list(errors.values())

    async def _compare_lists(
        self,
        expected: list[Any],
        actual: list[Any],
        config: FieldComparisonOptions | None,
        schema: JsonSchema,
        path: list[str] = [],
    ) -> list[EvaluationError]:
        array_config = self._ensure_config(config, ArrayComparisonOptions)
        item_config = array_config.element_evaluation

        if len(expected) != len(actual):
            return [
                EvaluationError(
                    f"Lists have different lengths (got {len(actual)} expected {len(expected)})",
                    path,
                ),
            ]

        # First we try comparing the same order no matter what
        same_order_errors = await self._compare_list_items(expected, actual, item_config, schema.child_schema(0), path)
        if not same_order_errors:
            # Evaluation succeeded with the same order, so we are good
            return []

        if not array_config.ignore_order:
            # Order is important, so we return the error
            return same_order_errors

        # TODO: we should cache the results of item comparisons to avoid recalculating them
        for perm in permutations(actual):
            perm_errors = await self._compare_list_items(expected, perm, item_config, schema.child_schema(0), path)
            if not perm_errors:
                return []

        # We try every permutation of the list, this can be pretty expensive
        # We could try sorting based on deterministic fields to reduce the number of permutations
        for perm in permutations(actual):
            if list(perm) == actual:
                # Skipping the same order since we already checked above
                continue

            # if compare_list_items returns a truthy value, we will continue to check the next permutation
            if await self._compare_list_items(expected, perm, item_config, schema.child_schema(0), path):
                continue
            return []

        return [EvaluationError("Could not find a list ordering that matches.", path), *same_order_errors]

    async def _compare_bool(
        self,
        expected: bool,
        actual: bool,
        config: FieldComparisonOptions | None,
        path: list[str] = [],
    ) -> list[EvaluationError]:
        if not expected == actual:
            return [EvaluationError(f"Bool values do not match. Got {actual} expected {expected}", path)]
        return []

    async def _fuzzy_compare_str(self, expected: str, actual: str, path: list[str] = []) -> list[EvaluationError]:
        # TODO: figure out circulat import
        from core.agents.text_equivalence_task import (
            TextEquivalenceTask,
            TextEquivalenceTaskInput,
        )
        from core.deprecated.workflowai import WorkflowAI

        input = TextEquivalenceTaskInput(
            correct_text=expected,
            candidate_text=actual,
        )

        group = VersionReference(
            properties=self.options.config.default_semantic_matching_group_properties
            or TaskGroupProperties(temperature=0, model=TEXT_EQUIVALENCE_TASK_MODEL.value),
        )
        wai = self.workflowai or WorkflowAI.from_ctx()
        out = await wai.run(TextEquivalenceTask(), input=input, group=group)
        if out.are_texts_functionally_equivalent is False:
            return [
                EvaluationError(
                    f"Semantics did not match between '{expected}' and '{actual}': {out.reason_not_equivalent}",
                    path,
                ),
            ]
        return []

    def _soft_compare_str(
        self,
        expected: str,
        actual: str,
        case_sensitive: bool,
        path: list[str] = [],
    ) -> list[EvaluationError]:
        if normalize(expected, case_sensitive=case_sensitive) == normalize(actual, case_sensitive=case_sensitive):
            return []
        return [EvaluationError(f"String values do not soft match. Got '{actual}' expected '{expected}'", path)]

    @classmethod
    def _str_for_comparison(cls, val: str, config: StringComparisonOptions) -> str:
        if config.strict_equality:
            return val
        return normalize(val, case_sensitive=config.case_sensitive is True)

    async def _compare_str(
        self,
        expected: str,
        actual: str,
        config: FieldComparisonOptions | None,
        schema: JsonSchema,
        path: list[str] = [],
    ) -> list[EvaluationError]:
        config = self._ensure_config(config, StringComparisonOptions)

        if expected == actual:
            return []

        if schema.format == "time":
            if not are_time_str_equal(expected, actual):
                return [EvaluationError(f"Times do not match. Got {actual} expected {expected}", path)]
            return []

        if config.semantics:
            return await self._fuzzy_compare_str(expected=expected, actual=actual, path=path)

        norm_str_exp = self._str_for_comparison(expected, config)
        norm_str_act = self._str_for_comparison(actual, config)
        if not norm_str_exp == norm_str_act:
            return [
                EvaluationError(
                    f"String values do not match. Compared '{norm_str_act}' to expected '{norm_str_exp}'",
                    path,
                ),
            ]
        return []

    async def _compare_number(
        self,
        expected: int | float,
        actual: int | float,
        config: FieldComparisonOptions | None,
        path: list[str] = [],
    ) -> list[EvaluationError]:
        config = self._ensure_config(config, NumberComparisonOptions)
        if config and config.delta:
            if abs(expected - actual) > config.delta:
                return [
                    EvaluationError(
                        f"Value difference |{expected} - {actual}| is greater than delta {config.delta}",
                        path,
                    ),
                ]
        if not expected == actual:
            return [EvaluationError(f"Number values do not match. Got {actual} expected {expected}", path)]
        return []

    def _check_null_mismatch(
        self,
        expected: Any,
        actual: Any,
        errors: dict[str, EvaluationError],
        path: list[str],
    ) -> list[EvaluationError]:
        if expected is None and actual is not None:
            return [EvaluationError(f"Expected null got '{actual}'", path)]
        if expected is not None and actual is None:
            return [EvaluationError(f"Expected '{expected}' got null", path)]
        return []

    def _check_type_mismatch(
        self,
        expected: Any,
        actual: Any,
        errors: dict[str, EvaluationError],
        path: list[str],
    ) -> list[EvaluationError]:
        if type(expected) is not type(actual):
            if isinstance(expected, Real) and isinstance(actual, Real):
                expected = float(expected)
                actual = float(actual)
            else:
                return [
                    EvaluationError(
                        f"Types do not match. Got <{type(actual).__name__}> expected <{type(expected).__name__}>",
                        path,
                    ),
                ]
        return []

    async def compare(
        self,
        expected: Any,
        actual: Any,
        config: FieldComparisonOptions | None,
        schema: JsonSchema,
        path: list[str] = [],
    ) -> list[EvaluationError]:
        if config and config.ignore:
            return []

        errors: dict[str, EvaluationError] = {}

        if null_errors := self._check_null_mismatch(expected=expected, actual=actual, errors=errors, path=path):
            self._add_errors(errors, null_errors)
            return list(errors.values())

        if type_mismatch_errors := self._check_type_mismatch(
            expected=expected,
            actual=actual,
            errors=errors,
            path=path,
        ):
            self._add_errors(errors, type_mismatch_errors)
            return list(errors.values())

        sub_errors = await self._compare_by_type(expected, actual, config, schema, path)
        self._add_errors(errors, sub_errors)

        return list(errors.values())

    async def _compare_by_type(
        self,
        expected: Any,
        actual: Any,
        config: FieldComparisonOptions | None,
        schema: JsonSchema,
        path: list[str],
    ) -> list[EvaluationError]:
        match expected:
            case dict():
                return await self._compare_objects(expected, actual, config, schema, path)  # pyright: ignore [reportUnknownArgumentType]
            case list():
                return await self._compare_lists(expected, actual, config, schema, path)  # pyright: ignore [reportUnknownArgumentType]
            case bool():
                return await self._compare_bool(expected, actual, config, path)
            case str():
                return await self._compare_str(expected, actual, config, schema, path)
            case int() | float():
                return await self._compare_number(expected, actual, config, path)
            case None:
                if actual is not None:
                    return [EvaluationError(f"Expected null, got {actual}", path)]
            case _:
                return [EvaluationError(f"Unsupported type {type(expected)}", path)]
        return []

    def _output_schema(self) -> JsonSchema:
        return self.task.output_json_schema()

    @override
    async def _compute_score(
        self,
        run_output: AgentOutput,
        example_output: AgentOutput,
        input: AgentInput,
    ) -> tuple[float, str]:
        errors = await self.compare(
            expected=example_output,
            actual=run_output,
            config=self.options.config.options,
            schema=self._output_schema(),
        )
        if errors:
            return 0.0, "Multiple errors found"
        return 1.0, ""

    @override
    async def evaluate_with_example(
        self,
        run: AgentRun,
        example: SerializableTaskExample,
        definition: TaskEvaluation.Evaluator,
    ) -> TaskEvaluation:
        errors = await self.compare(
            expected=example.task_output,
            actual=run.task_output,
            config=self.options.config.options,
            schema=self._output_schema(),
        )

        comment = ""
        if len(errors) > 0:
            comment = "Multiple errors found" if len(errors) > 1 else str(errors[0])

        return TaskEvaluation(
            score=0.0 if len(errors) > 0 else 1.0,
            evaluator=definition,
            example_id=example.id,
            comment=comment,
            error_details=[TaskEvaluation.ByFieldError(key_path=err.keypath, reason=str(err)) for err in errors],
        )
