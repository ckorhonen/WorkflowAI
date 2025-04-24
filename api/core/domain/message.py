import logging
from collections.abc import Sequence
from enum import StrEnum, auto
from typing import Literal

from pydantic import BaseModel

from core.domain.fields.file import File
from core.domain.fields.image_options import ImageOptions
from core.domain.tool_call import ToolCall, ToolCallRequestWithID
from core.providers.base.models import StandardMessage

_logger = logging.getLogger(__name__)


class Message(BaseModel):
    class Role(StrEnum):
        SYSTEM = auto()
        USER = auto()
        ASSISTANT = auto()

        @classmethod
        def from_standard(cls, role: Literal["system", "user", "assistant"] | None):
            if not role:
                _logger.warning("No role provided, using default role")
                # TODO: Using a default role, not the best solution
                return cls.USER
            return cls(role)

        def to_standard(self) -> Literal["system", "user", "assistant"]:
            # Ok to type ignore here, sanity check should cover the case
            return self.value  # type: ignore

    role: Role
    content: str
    files: Sequence[File] | None = None

    tool_call_requests: list[ToolCallRequestWithID] | None = None
    tool_call_results: list[ToolCall] | None = None

    image_options: ImageOptions | None = None

    @classmethod
    def from_standard(cls, message: StandardMessage):
        role = cls.Role.from_standard(message["role"])
        raw = message["content"]
        if isinstance(raw, str):
            return cls(role=role, content=raw)

        content: list[str] = []
        files: list[File] = []
        tool_call_requests: list[ToolCallRequestWithID] = []
        tool_call_results: list[ToolCall] = []

        for item in raw:
            try:
                match item["type"]:
                    case "text":
                        content.append(item["text"])
                    case "image_url":
                        files.append(File(url=item["image_url"]["url"]))
                    case "document_url":
                        files.append(File(url=item["source"]["url"]))
                    case "audio_url":
                        files.append(File(url=item["audio_url"]["url"]))
                    case "tool_call_request":
                        tool_call_requests.append(
                            ToolCallRequestWithID(
                                id=item["id"] or "",
                                tool_name=item["tool_name"],
                                tool_input_dict=item["tool_input_dict"] or {},
                            ),
                        )
                    case "tool_call_result":
                        tool_call_results.append(
                            ToolCall(
                                id=item["id"] or "",
                                tool_name=item["tool_name"] or "",
                                tool_input_dict=item["tool_input_dict"] or {},
                                result=item["result"],
                                error=item["error"],
                            ),
                        )
                    case _:  # pyright: ignore[reportUnnecessaryComparison]
                        _logger.exception("Unsupported content type: %s", item["type"])
            except KeyError:
                _logger.exception("Key error while parsing content", extra={"raw": message})

        return cls(
            role=role,
            content="\n".join(content),
            files=files or None,
            tool_call_requests=tool_call_requests or None,
            tool_call_results=tool_call_results or None,
        )
