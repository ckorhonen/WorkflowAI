from abc import abstractmethod
from typing import Optional

from typing_extensions import override

from core.domain.agent_run import AgentRun
from core.domain.task_evaluation import TaskEvaluation
from core.domain.task_example import SerializableTaskExample
from core.domain.types import AgentInput, AgentOutput

from .abstract_evaluator import AbstractEvaluator, EvaluatorOptionsVar


class ExampleBasedEvaluator(AbstractEvaluator[EvaluatorOptionsVar]):
    """An evaluator that requires an example to evaluate a task run.
    Override evaluate_with_example instead of evaluate to implement the evaluation logic.
    """

    @abstractmethod
    async def _compute_score(
        self,
        run_output: AgentOutput,
        example_output: AgentOutput,
        input: AgentInput,
    ) -> tuple[float, str]:
        """Short hand for evaluators that only compute a score."""
        pass

    async def evaluate_with_example(
        self,
        run: AgentRun,
        example: SerializableTaskExample,
        definition: TaskEvaluation.Evaluator,
    ) -> "TaskEvaluation":
        """Overwrite instead of evaluate to implement the evaluation logic with the example.
        Called by evaluate after fetching the example.
        By default it computes the score using _compute_score. Override if you need to output more than scores"""
        score, comment = await self._compute_score(run.task_output, example.task_output, run.task_input)
        return TaskEvaluation(score=score, evaluator=definition, comment=comment, example_id=example.id)

    @override
    async def evaluate(
        self,
        run: AgentRun,
        example: Optional[SerializableTaskExample] = None,
    ) -> "TaskEvaluation":
        definition = self.definition
        if example is None:
            example = await self.fetch_example(run, True)
        return await self.evaluate_with_example(run, example, definition)

    def requires_example(self) -> bool:
        return True
