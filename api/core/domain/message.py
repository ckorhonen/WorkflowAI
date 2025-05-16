import asyncio
from collections.abc import Iterator, Sequence
from enum import StrEnum, auto
from typing import Any, Literal

from pydantic import BaseModel

from core.domain.fields.file import File, FileKind, FileWithKeyPath
from core.domain.fields.image_options import ImageOptions
from core.domain.tool_call import ToolCall, ToolCallRequestWithID
from core.domain.types import TemplateRenderer


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


class MessageContent(BaseModel):
    text: str | None = None
    file: File | None = None
    tool_call_request: ToolCallRequestWithID | None = None
    tool_call_result: ToolCall | None = None

    async def templated(self, renderer: TemplateRenderer):
        try:
            async with asyncio.TaskGroup() as tg:
                text_task = tg.create_task(renderer(self.text)) if self.text else None
                file_task = tg.create_task(self.file.templated(renderer)) if self.file else None
        except ExceptionGroup as e:
            # Raising the first exception, to avoid having a special kind of exception to handle
            # This is not great and we should return a compound instead
            raise e.exceptions[0]

        return MessageContent(
            text=text_task.result() if text_task else None,
            file=file_task.result() if file_task else None,
            tool_call_request=self.tool_call_request,
            tool_call_result=self.tool_call_result,
        )

    def content_iterator(self) -> Iterator[tuple[str, FileKind | str | None]]:
        if self.text:
            yield self.text, None
        if self.file is not None and self.file.url:
            yield self.file.url, self.file.format or FileKind.ANY


MessageRole = Literal["system", "user", "assistant"]


class Message(BaseModel):
    # It would be nice to use strict validation since we know that certain roles are not allowed to
    # have certain content. Unfortunately it would mean that we would have oneOfs in the schema which
    # we currently do not handle client side
    role: MessageRole
    content: list[MessageContent]
    image_options: ImageOptions | None = None

    async def templated(self, renderer: TemplateRenderer):
        try:
            contents = await asyncio.gather(*[c.templated(renderer) for c in self.content])
        except ExceptionGroup as e:
            # Raising the first exception, to avoid having a special kind of exception to handle
            # This is not great and we should return a compound instead
            raise e.exceptions[0]
        return Message(
            role=self.role,
            content=contents,
            image_options=self.image_options,
        )

    def content_iterator(self) -> Iterator[tuple[str, FileKind | str | None]]:
        for c in self.content:
            yield from c.content_iterator()

    def to_deprecated(self) -> MessageDeprecated:
        # TODO: remove this method
        content = "\n\n".join([c.text for c in self.content if c.text])
        files = [c.file for c in self.content if c.file]
        tool_call_requests = [c.tool_call_request for c in self.content if c.tool_call_request]
        tool_call_results = [c.tool_call_result for c in self.content if c.tool_call_result]
        match self.role:
            case "system":
                return MessageDeprecated(role=MessageDeprecated.Role.SYSTEM, content=content)
            case "user":
                return MessageDeprecated(
                    role=MessageDeprecated.Role.USER,
                    content=content,
                    files=files,
                    tool_call_requests=tool_call_requests,
                    tool_call_results=tool_call_results,
                )
            case "assistant":
                return MessageDeprecated(
                    role=MessageDeprecated.Role.ASSISTANT,
                    content=content,
                    files=files,
                    tool_call_requests=tool_call_requests,
                )
        # We should never reach this point
        from core.domain.errors import InternalError

        raise InternalError("Unexpected message type")

    @classmethod
    def with_text(cls, text: str, role: MessageRole = "user") -> "Message":
        return cls(role=role, content=[MessageContent(text=text)])


class Messages(BaseModel):
    messages: list[Message]

    def content_iterator(self) -> Iterator[tuple[str, FileKind | str | None]]:
        """Iterates over all content"""
        for m in self.messages:
            yield from m.content_iterator()

    async def templated(self, renderer: TemplateRenderer):
        try:
            messages = await asyncio.gather(*[m.templated(renderer) for m in self.messages])
        except ExceptionGroup as e:
            # Raising the first exception, to avoid having a special kind of exception to handle
            # This is not great and we should return a compound instead
            raise e.exceptions[0]
        return Messages(messages=messages)

    def to_deprecated(self) -> list[MessageDeprecated]:
        return [m.to_deprecated() for m in self.messages]

    def to_input_dict(self):
        return self.model_dump(exclude_none=True)

    def file_iterator(self, prefix: str = "messages") -> Iterator[FileWithKeyPath]:
        for i, m in enumerate(self.messages):
            for j, c in enumerate(m.content):
                if c.file:
                    # Returning an empty key path
                    yield FileWithKeyPath(
                        key_path=[prefix, i, "content", j, "file"],
                        **c.file.model_dump(exclude_none=True),
                    )

    def json_schema_for_template(self, base_schema: dict[str, Any] | None):
        """Returns a json schema for template variables present in the messages"""

        # We need to import here to avoid circular imports
        # TODO: we should probably have this in a separate file
        from core.utils.schema_sanitation import streamline_schema
        from core.utils.templates import extract_variable_schema

        templatable: str = ""
        # TODO: handle files as strings in templates
        # var_regexp = re.compile(r"\{\{([^}]+)\}\}")
        templatable_parts: list[str] = []
        files: dict[str, FileKind | str] = {}
        for m, _ in self.content_iterator():
            # If format is not provided, then we treat as a plain string
            # if not format:
            #     templatable_parts.append(m)
            #     continue
            # # If format is provided and the whole content is a variable
            # if match := var_regexp.match(m):
            #     files[match.group(1)] = format
            #     continue
            # We are in a case where the content is a mix of variables and plain text so we can't
            # really extract the file
            templatable_parts.append(m)

        templatable = " ".join(templatable_parts)
        schema = extract_variable_schema(templatable, existing_schema=base_schema)
        for var, kind in files.items():
            # We just add the format here
            # It will be streamlined and replace with the proper
            schema.setdefault("properties", {})[var] = {"$ref": "#/$defs/File", "format": kind}
        return streamline_schema(schema)
