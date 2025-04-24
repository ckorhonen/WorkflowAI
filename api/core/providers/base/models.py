from datetime import datetime
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

from core.domain.llm_usage import LLMUsage
from core.utils.fields import datetime_factory


class RawCompletion(BaseModel):
    response: str | None
    usage: LLMUsage
    finish_reason: str | None = None

    start_time: datetime = Field(default_factory=datetime_factory)

    model_config = ConfigDict(extra="allow")


class TextContentDict(TypedDict):
    type: Literal["text"]
    text: str


class DocumentURLDict(TypedDict):
    url: str


class DocumentContentDict(TypedDict):
    type: Literal["document_url"]
    source: DocumentURLDict


class ImageURLDict(TypedDict):
    url: str


class AudioURLDict(TypedDict):
    url: str


class ImageContentDict(TypedDict):
    type: Literal["image_url"]
    image_url: ImageURLDict


class AudioContentDict(TypedDict):
    type: Literal["audio_url"]
    audio_url: AudioURLDict


class ToolCallRequestDict(TypedDict):
    type: Literal["tool_call_request"]
    id: str | None
    tool_name: str
    tool_input_dict: dict[str, Any] | None


class ToolCallResultDict(TypedDict):
    type: Literal["tool_call_result"]
    id: str | None
    tool_name: str | None
    tool_input_dict: dict[str, Any] | None
    result: Any | None
    error: str | None


class StandardMessage(TypedDict):
    # NOTE: The structure is standard for all providers.
    # So keep consistent with client side as well.
    role: Literal["system", "user", "assistant"] | None
    content: (
        str
        | list[
            TextContentDict
            | ImageContentDict
            | AudioContentDict
            | DocumentContentDict
            | ToolCallRequestDict
            | ToolCallResultDict
        ]
    )
