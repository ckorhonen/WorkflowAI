from typing import Any

from core.domain.input_evaluation import InputEvaluation
from core.storage.mongo.models.base_document import BaseDocumentWithID
from core.storage.mongo.models.pyobjectid import PyObjectID
from core.storage.mongo.models.run_identifier import RunOrUserIdentifier


class InputEvaluationDocument(BaseDocumentWithID):
    task_id: str = ""
    task_schema_id: int = 0

    task_input_hash: str = ""

    is_loading: bool | None = None

    correct_outputs: list[Any] | None = None
    incorrect_outputs: list[Any] | None = None

    evaluation_instruction: str | None = None

    generated_by: RunOrUserIdentifier | None = None

    @classmethod
    def from_domain(
        cls,
        task_id: str,
        task_schema_id: int,
        input_evaluation: InputEvaluation,
    ):
        return cls(
            _id=PyObjectID.from_str(input_evaluation.id),
            task_id=task_id,
            task_schema_id=task_schema_id,
            task_input_hash=input_evaluation.task_input_hash,
            correct_outputs=input_evaluation.correct_outputs,
            incorrect_outputs=input_evaluation.incorrect_outputs,
            evaluation_instruction=input_evaluation.evaluation_instruction,
            generated_by=RunOrUserIdentifier.from_domain(input_evaluation.created_by)
            if input_evaluation.created_by
            else None,
            is_loading=input_evaluation.is_loading or None,
        )

    def to_domain(self) -> InputEvaluation:
        return InputEvaluation(
            id=str(self.id) if self.id else "",
            task_input_hash=self.task_input_hash,
            correct_outputs=self.correct_outputs or [],
            incorrect_outputs=self.incorrect_outputs or [],
            evaluation_instruction=self.evaluation_instruction,
            created_by=self.generated_by.to_domain() if self.generated_by else None,
            created_at=self.generation_time,
            is_loading=self.is_loading or False,
        )
