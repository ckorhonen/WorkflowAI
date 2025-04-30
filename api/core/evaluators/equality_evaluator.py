from typing_extensions import override

from core.domain.evaluator_options import EvaluatorOptions
from core.domain.types import AgentInput, AgentOutput

from .example_based_evaluator import ExampleBasedEvaluator


class EqualityEvaluator(ExampleBasedEvaluator["EqualityEvaluatorOptions"]):
    """
    An evaluator that compares outputs using the equality operator
    """

    @override
    def _version(self) -> str:
        return "1.0.0"

    @override
    async def _compute_score(
        self,
        run_output: AgentOutput,
        example_output: AgentOutput,
        input: AgentInput,
    ) -> tuple[float, str]:
        return float(run_output == example_output), ""

    @classmethod
    def options_class(cls) -> type["EqualityEvaluatorOptions"]:
        return EqualityEvaluatorOptions


class EqualityEvaluatorOptions(EvaluatorOptions):
    name: str = "Equality"
