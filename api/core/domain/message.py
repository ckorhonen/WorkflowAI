from collections.abc import Sequence
from enum import StrEnum, auto
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field

from core.domain.errors import InternalError
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
    role: Literal["system", "developer"] = "system"
    content: str | TextContent
    image_options: ImageOptions | None = None


MessageContent: TypeAlias = Annotated[TextContent | FileContent, Field(discriminator="type")]


class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: str | list[MessageContent]


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str | list[Annotated[TextContent | FileContent | ToolCallRequestContent, Field(discriminator="type")]]


class ToolMessage(BaseModel):
    role: Literal["tool"] = "tool"
    content: ToolCall


Message: TypeAlias = Annotated[
    SystemMessage | UserMessage | AssistantMessage | ToolMessage,
    Field(discriminator="role"),
]


def _parse_message_content(content: str | list[MessageContent]) -> tuple[str, list[File]]:
    if isinstance(content, str):
        return content, []
    return "".join([c.text for c in content if isinstance(c, TextContent)]), [
        c.file for c in content if isinstance(c, FileContent)
    ]


class Messages(BaseModel):
    messages: list[Message]

    def to_deprecated(self) -> list[MessageDeprecated]:
        # TODO: remove this method
        out: list[MessageDeprecated] = []
        for m in self.messages:
            content, files = _parse_message_content(m.content)  # type: ignore
            match m:
                case SystemMessage():
                    out.append(MessageDeprecated(role=MessageDeprecated.Role.SYSTEM, content=content))
                case UserMessage():
                    out.append(MessageDeprecated(role=MessageDeprecated.Role.USER, content=content, files=files))
                case _:
                    raise InternalError("Unexpected message type")
        return out
