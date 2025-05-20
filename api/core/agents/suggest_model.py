from collections.abc import Sequence

import workflowai
from pydantic import BaseModel

from core.domain.models.models import Model


class ModelSuggestionInput(BaseModel):
    invalid_model: str
    supported_models: Sequence[str]


class ModelSuggestionOutput(BaseModel):
    suggested_model: str


@workflowai.agent(id="model_suggester", model=Model.LLAMA_4_MAVERICK_FAST)
async def suggest_model(input: ModelSuggestionInput) -> ModelSuggestionOutput:
    """
    Suggest the closest supported model name for a given invalid model input.
    Consider models that are similar to the invalid model if there is no obvious match.
    """
    ...
