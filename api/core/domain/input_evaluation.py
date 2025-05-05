from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, Field

from core.domain.run_identifier import RunIdentifier
from core.domain.types import AgentOutput
from core.domain.users import UserIdentifier


class InputEvaluation(BaseModel):
    id: str = ""

    task_input_hash: str

    correct_outputs: list[AgentOutput]
    incorrect_outputs: list[AgentOutput]

    created_by: UserIdentifier | RunIdentifier | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.min)

    # Evaluation instructions specific for this input
    evaluation_instruction: str | None = None

    is_loading: bool = False

    @property
    def is_usable(self) -> bool:
        # An input evaluation is usable if it has correct outputs
        return bool(self.evaluation_instruction) or bool(self.correct_outputs)

    def add_output(self, output: dict[str, Any], is_correct: bool):
        if is_correct:
            append_to = self.correct_outputs
            other = self.incorrect_outputs
        else:
            append_to = self.incorrect_outputs
            other = self.correct_outputs

        edited = False
        # Remove output from the other list if it exists there
        try:
            other.remove(output)
            edited = True
        except ValueError:
            pass

        if output not in append_to:
            append_to.append(output)
            edited = True

        return edited

    def is_similar_to(self, other: Self) -> bool:
        return (
            other.correct_outputs == self.correct_outputs
            and other.incorrect_outputs == self.incorrect_outputs
            and (other.evaluation_instruction or None) == (self.evaluation_instruction or None)
        )
