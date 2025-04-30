from datetime import datetime
from typing import Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator

from core.domain.types import AgentInput, AgentOutput
from core.utils.models.previews import compute_preview

TaskExampleQueryUniqueBy = Literal["task_input_hash", "task_output_hash", None]


class SerializableTaskExample(BaseModel):
    id: str = Field(..., description="the id of the example. Read only")

    task_id: str = Field(..., description="the id of the associated task. Read only")
    task_schema_id: int = Field(..., description="the task schema index")

    task_input: AgentInput = {}
    task_input_hash: str = Field(..., description="a hash describing the input")
    task_input_preview: str = Field(default="", description="a preview of the input")
    task_output: AgentOutput = {}
    task_output_hash: str = Field(..., description="a hash describing the output")
    task_output_preview: str = Field(default="", description="a preview of the output")

    created_at: Optional[datetime] = Field(default=None, description="the creation date of the example. Read only")

    from_task_run_id: Optional[str] = None

    in_training_set: bool = Field(default=False, description="whether the example belongs to the training set")

    task_input_vector: Optional[list[float]] = Field(
        default=None,
        description="an optional embedding of the input of the example",
    )

    from_correction: Optional[bool] = Field(
        default=None,
        description="whether the example comes from a correction, "
        "i-e whether the LLM made a mistake in the original task run",
    )

    @model_validator(mode="after")
    def post_validate(self) -> Self:
        if not self.task_input_preview:
            self.task_input_preview = compute_preview(self.task_input)
        if not self.task_output_preview:
            self.task_output_preview = compute_preview(self.task_output)
        return self
