from collections.abc import Sequence
from enum import StrEnum, auto
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field

from core.domain.fields.file import File
from core.domain.fields.image_options import ImageOptions
from core.domain.tool_call import ToolCall, ToolCallRequestWithID


class MessageDeprecated(BaseModel):
    class Role(StrEnum):
        SYSTEM = auto()
        USER = auto()
        ASSISTANT = auto()

    role: Role
    content: str
    files: Sequence[File] | None = None

    tool_call_requests: list[ToolCallRequestWithID] | None = None
    tool_call_results: list[ToolCall] | None = None

    image_options: ImageOptions | None = None


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class FileContent(BaseModel):
    type: Literal["file"] = "file"
    file: File


class ToolCallRequestContent(BaseModel):
    type: Literal["tool_call_request"] = "tool_call_request"
    tool_call_request: ToolCallRequestWithID


class SystemMessage(BaseModel):
    role: Literal["system"] = "system"
    content: str | TextContent
    image_options: ImageOptions | None = None


class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: (
        str
        | Annotated[
            list[TextContent | FileContent],
            Field(discriminator="type"),
        ]
    )


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: (
        str
        | Annotated[
            list[TextContent | FileContent | ToolCallRequestContent],
            Field(discriminator="type"),
        ]
    )


class ToolMessage(BaseModel):
    role: Literal["tool"] = "tool"
    content: ToolCall


Message: TypeAlias = Annotated[
    SystemMessage | UserMessage | AssistantMessage | ToolMessage,
    Field(discriminator="role"),
]
