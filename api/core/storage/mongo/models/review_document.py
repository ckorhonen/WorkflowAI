from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from core.domain.review import Review
from core.domain.utils import compute_eval_hash
from core.storage.mongo.models.base_document import BaseDocumentWithID, TaskIdAndSchemaMixin
from core.storage.mongo.models.pyobjectid import PyObjectID
from core.storage.mongo.models.run_identifier import RunIdentifier


class ReviewDocument(BaseDocumentWithID, TaskIdAndSchemaMixin):
    task_input_hash: str = ""
    task_output_hash: str = ""
    eval_hash: str = ""

    outcome: Literal["positive", "negative", "unsure"] | None = None
    status: Literal["in_progress", "completed"] = "completed"
    comment: str | None = None
    positive_aspects: list[str] | None = None
    negative_aspects: list[str] | None = None
    in_response_to: PyObjectID | None = None

    is_stale: bool = False

    class UserReviewer(BaseModel):
        reviewer_type: Literal["user"] = "user"
        user_id: str | None = None
        user_email: str | None = None

        @classmethod
        def from_domain(cls, reviewer: Review.UserReviewer):
            return cls(user_id=reviewer.user_id, user_email=reviewer.user_email)

        def to_domain(self) -> Review.UserReviewer:
            return Review.UserReviewer(user_id=self.user_id, user_email=self.user_email)

    class AIReviewer(BaseModel):
        reviewer_type: Literal["ai"] = "ai"

        evaluator_id: str | None
        input_evaluation_id: str

        confidence_score: float | None = None
        run_identifier: RunIdentifier | None = None

        @classmethod
        def from_reviewer(cls, reviewer: Review.AIReviewer):
            return cls(
                evaluator_id=reviewer.evaluator_id or None,
                input_evaluation_id=reviewer.input_evaluation_id or "",
                confidence_score=reviewer.confidence_score,
                run_identifier=RunIdentifier.from_domain(reviewer.run_identifier) if reviewer.run_identifier else None,
            )

        def to_domain(self) -> Review.AIReviewer:
            return Review.AIReviewer(
                evaluator_id=self.evaluator_id or None,
                input_evaluation_id=self.input_evaluation_id,
                confidence_score=self.confidence_score,
                run_identifier=self.run_identifier.to_domain() if self.run_identifier else None,
            )

    reviewer: Annotated[UserReviewer | AIReviewer, Field(discriminator="reviewer_type")] | None = None

    @classmethod
    def reviewer_from_domain(
        cls,
        reviewer: Review.UserReviewer | Review.AIReviewer,
    ) -> UserReviewer | AIReviewer:
        if isinstance(reviewer, Review.UserReviewer):
            return cls.UserReviewer.from_domain(reviewer)
        return cls.AIReviewer.from_reviewer(reviewer)

    @classmethod
    def from_domain(cls, review: Review):
        return cls(
            _id=PyObjectID.from_str(review.id),
            reviewer=cls.reviewer_from_domain(review.reviewer),
            task_id=review.task_id,
            task_uid=review.task_uid,
            task_schema_id=review.task_schema_id,
            task_input_hash=review.task_input_hash,
            task_output_hash=review.task_output_hash,
            outcome=review.outcome,
            status=review.status,
            comment=review.comment,
            positive_aspects=review.positive_aspects,
            negative_aspects=review.negative_aspects,
            in_response_to=PyObjectID.from_str(review.responding_to_review_id),
            eval_hash=review.eval_hash,
        )

    def to_domain(self) -> Review:
        return Review(
            id=str(self.id),
            created_at=self.id.generation_time if self.id else datetime.min,
            reviewer=self.reviewer.to_domain() if self.reviewer else Review.AIReviewer(),
            task_id=self.task_id,
            task_uid=self.task_uid,
            task_schema_id=self.task_schema_id,
            task_input_hash=self.task_input_hash,
            task_output_hash=self.task_output_hash,
            eval_hash=self.eval_hash,
            outcome=self.outcome,
            status=self.status,
            comment=self.comment,
            positive_aspects=self.positive_aspects,
            negative_aspects=self.negative_aspects,
            responding_to_review_id=str(self.in_response_to) if self.in_response_to else None,
        )

    @model_validator(mode="after")
    def compute_eval_hash(self):
        # Only compute the eval hash if it's not already set and if all the required fields are present
        if not self.eval_hash and self.task_input_hash and self.task_schema_id:
            self.eval_hash = compute_eval_hash(self.task_schema_id, self.task_input_hash, self.task_output_hash)
        return self
