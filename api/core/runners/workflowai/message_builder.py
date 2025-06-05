import logging
from collections.abc import Iterator
from typing import Any

from pydantic import ValidationError

from core.domain.consts import FILE_DEFS
from core.domain.errors import BadRequestError
from core.domain.fields.file import File, FileKind, FileWithKeyPath
from core.domain.message import Message, MessageContent, Messages
from core.domain.task_io import RawMessagesSchema, SerializableTaskIO
from core.utils.schemas import InvalidSchemaError, JsonSchema
from core.utils.templates import TemplateManager


class MessageBuilder:
    def __init__(
        self,
        template_manager: TemplateManager,
        input_schema: SerializableTaskIO,
        messages: list[Message] | None,
        logger: logging.Logger,
    ):
        self._template_manager = template_manager
        self._input_schema = input_schema
        self._version_messages = messages
        self._logger = logger

    @classmethod
    def _extract_files(
        cls,
        schema: JsonSchema,
        input: Any,
        base_key_path: list[str | int],
    ) -> Iterator[FileWithKeyPath]:
        """Extracts FileWithKeyPath objects from the input.
        Payload is removed from the original input"""
        if isinstance(input, dict):
            if (ref := schema.schema.get("$ref")) and ref.startswith("#/$defs/"):
                if ref[8:] in FILE_DEFS:
                    # Ref is a file
                    try:
                        file = FileWithKeyPath.model_validate(input[ref])
                    except ValidationError as e:
                        raise BadRequestError(f"Invalid file with key {ref}: {str(e)}", capture=True) from e
                    file.key_path = base_key_path
                    file.format = FileKind.from_ref_name(ref[8:])
                    yield file
                # Ref is something else, we can just skip
                return
            for key, value in input.items():  # pyright: ignore [reportUnknownVariableType]
                if not isinstance(key, str):
                    continue
                try:
                    yield from cls._extract_files(schema.child_schema(key), value, [*base_key_path, key])
                except InvalidSchemaError:
                    # Key is not present in the schema, we can just skip
                    continue

        if isinstance(input, list):
            for idx, item in enumerate(input):  # pyright: ignore [reportUnknownVariableType, reportUnknownArgumentType]
                yield from cls._extract_files(schema.child_schema(idx), item, [*base_key_path, idx])

    def _sanitize_files(self, input: Any):
        return {f.key_path_str: f for f in self._extract_files(JsonSchema(self._input_schema.json_schema), input, [])}

    async def _handle_templated_messages(self, messages: Messages):
        if not messages.model_extra:
            self._logger.warning("No extra fields provided, but the input schema is a templated message schema")
            return messages
        if not self._version_messages:
            # There are no version messages, so nothing to template
            # This would be a very weird case so logging a warning
            self._logger.warning("No version messages provided, but the input schema is not RawMessagesSchema")
            return None

        version_messages = self._version_messages
        if self._input_schema.has_files:
            # TODO: add a test that the input is not updated
            files = self._sanitize_files(messages.model_extra)
        else:
            files = None
        renderer = _MessageRenderer(self._template_manager, messages.model_extra, files or {})

        version_messages = await renderer.render_messages(version_messages)
        return Messages(messages=[*version_messages, *messages.messages])

    async def extract(self, input: Any):
        # No matter what, the input should be a valid Messages object
        if isinstance(input, list):
            input = {"workflowai.messages": input}
        try:
            messages = Messages.model_validate(input)
        except ValidationError as e:
            # Capturing for now just in case
            raise BadRequestError(f"Input is not a valid list of messages: {str(e)}", capture=True) from e

        if self._input_schema.version == RawMessagesSchema.version:
            # Version messages are not templated since there is no field in the input schema
            # So we can just inline as is
            if self._version_messages:
                messages.messages = [*self._version_messages, *messages.messages]
            return messages

        return await self._handle_templated_messages(messages)


class _MessageRenderer:
    def __init__(self, template_manager: TemplateManager, input: Any, files: dict[str, FileWithKeyPath]):
        self._template_manager = template_manager
        self._input = input
        self._files = files

    async def _render_file(self, file: File | None):
        if not file:
            return None
        if template_key := file.template_key():
            # File is a templated file so we can just pop the key
            try:
                return self._files.pop(template_key)
            except KeyError:
                raise BadRequestError(f"Missing file with key {template_key}")
        return None

    async def _render_text(self, text: str | None):
        if not text:
            return None

        return await self._template_manager.render_template(text, self._input)

    async def render_content(self, content: MessageContent):
        update: dict[str, Any] = {}
        if file := await self._render_file(content.file):
            update["file"] = file

        if (text := await self._render_text(content.text)) is not None:
            update["text"] = text

        if update:
            return content.model_copy(update=update)
        return content

    async def render_messages(self, messages: list[Message]):
        rendered = [
            Message(
                role=m.role,
                content=[await self.render_content(c) for c in m.content],
            )
            for m in messages
        ]

        if self._files:
            # Some files were unused
            # TODO: We need to be smarter about this but for now let's just append
            # Them at the end of the last message
            rendered[-1].content.extend([MessageContent(file=f) for f in self._files.values()])
        return rendered
