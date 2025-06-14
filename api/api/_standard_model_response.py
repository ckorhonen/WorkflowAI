import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from core.domain.models.model_data import FinalModelData
from core.domain.models.model_data_supports import ModelDataSupports


class SupportsModality(BaseModel):
    image: bool
    audio: bool
    pdf: bool
    text: bool


class ModelSupports(BaseModel):
    """Data about what the model supports on the WorkflowAI platform.
    Note that a single model might have different capabilities based on the provider, or that sometimes WorkflowAI
    might choose not to a use a capability when it is not deemed beneficial."""

    input: SupportsModality = Field(
        description="Whether the model supports input of the given modality.",
    )
    output: SupportsModality = Field(
        description="Whether the model supports output of the given modality. "
        "If false, the model will not return any output.",
    )

    json_mode: bool = Field(
        description="Whether the model supports JSON mode natively. "
        "JSON mode guarantees that the inference will return a valid JSON object. If the model does not support JSON "
        "mode but JSON is requested, the schema matching is guaranteed by WorkflowAI and not the model itself.",
    )
    structured_output: bool = Field(
        description="Whether the model supports structured output natively. "
        "Structured output guarantees that the inference will return an object matching a given schema. If the model "
        "does not structured output but a JSON schema is provided, the schema matching is guaranteed by WorkflowAI "
        "and not the model itself.",
    )
    system_message: bool = Field(
        description="Whether the model supports system messages. "
        "If false and the request contains a system message, the system message will be converted to a user message.",
    )
    parallel_tool_calls: bool = Field(
        description="Whether the model supports parallel tool calls, i.e. if the model can return multiple tool calls "
        "in a single inference. If the model does not support parallel tool calls, the parallel_tool_calls parameter "
        "will be ignored.",
    )
    tools: bool = Field(
        description="Whether the model supports tools. If false, the model will not support tool calling. "
        "Request containing tools will be rejected.",
    )
    top_p: bool = Field(
        description="Whether the model supports top_p. If false, the top_p parameter will be ignored",
    )
    temperature: bool = Field(
        description="Whether the model supports temperature. If false, the temperature parameter will be ignored.",
    )


class ModelPricing(BaseModel):
    input_token_usd: float
    output_token_usd: float


class ModelReasoning(BaseModel):
    """A mapping from a reasoning effort (disabled, low, medium, high) to a
    reasoning token budget. The reasoning token budget represents the max number
    of tokens that can be used for reasoning.
    """

    can_be_disabled: bool = Field(
        description="Whether the reasoning can be disabled for the model.",
    )
    low: int = Field(description="The max number of tokens that can be used for reasoning at low effort for the model.")
    medium: int = Field(
        description="The max number of tokens that can be used for reasoning at medium effort for the model.",
    )
    high: int = Field(
        description="The max number of tokens that can be used for reasoning at high effort for the model.",
    )


class ModelContextWindow(BaseModel):
    max_tokens: int = Field(
        description="The max number of tokens that can be used for the context window for the model.",
    )
    max_output_tokens: int = Field(
        description="The max number of tokens that the model can output.",
    )


class Model(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str
    display_name: str
    icon_url: str

    supports: ModelSupports = Field(
        description="Data about what the model supports.",
    )

    pricing: ModelPricing = Field(
        description="Pricing information for the model.",
    )

    release_date: datetime.date = Field(
        description="The date the model was released on the WorkflowAI platform.",
    )

    reasoning: ModelReasoning | None = Field(
        default=None,
        description="Reasoning information for the model. None if the model does not support reasoning.",
    )

    context_window: ModelContextWindow = Field(
        description="Context window information for the model.",
    )


# TODO:use Model above instead of ModelItem
class StandardModelResponse(BaseModel):
    """A model response compatible with the OpenAI API"""

    object: Literal["list"] = "list"

    class ModelItem(BaseModel):
        id: str
        object: Literal["model"] = "model"
        created: int
        owned_by: str
        display_name: str
        icon_url: str
        supports: dict[str, Any]

        class Pricing(BaseModel):
            input_token_usd: float
            output_token_usd: float

        pricing: Pricing

        release_date: datetime.date

        @classmethod
        def from_model_data(cls, id: str, model: FinalModelData):
            provider_data = model.providers[0][1]
            return cls(
                id=id,
                created=int(datetime.datetime.combine(model.release_date, datetime.time(0, 0)).timestamp()),
                owned_by=model.provider_name,
                display_name=model.display_name,
                icon_url=model.icon_url,
                supports={
                    k.removeprefix("supports_"): v
                    for k, v in model.model_dump(
                        mode="json",
                        include=set(ModelDataSupports.model_fields.keys()),
                    ).items()
                },
                pricing=cls.Pricing(
                    input_token_usd=provider_data.text_price.prompt_cost_per_token,
                    output_token_usd=provider_data.text_price.completion_cost_per_token,
                ),
                release_date=model.release_date,
            )

    data: list[ModelItem]
