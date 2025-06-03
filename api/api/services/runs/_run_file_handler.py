import asyncio
import logging
from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError

from core.domain.agent_run import TaskRunIO
from core.domain.consts import INPUT_KEY_MESSAGES
from core.domain.message import Messages
from core.domain.task_io import RawMessagesSchema, SerializableTaskIO
from core.domain.task_variant import VariantIO
from core.runners.workflowai.utils import (
    FileWithKeyPath,
    download_file,
    extract_files,
)
from core.storage.azure.azure_blob_file_storage import FileStorage
from core.storage.file_storage import FileData
from core.utils.coroutines import sentry_wrap
from core.utils.dicts import InvalidKeyPathError, set_at_keypath

_logger = logging.getLogger("RunsService")


class FileHandler:
    def __init__(self, file_storage: FileStorage, folder_path: str):
        self._file_storage = file_storage
        self._folder_path = folder_path

    @classmethod
    def _extract_files(
        cls,
        agent_io: SerializableTaskIO,
        payload: Any,
    ) -> list[FileWithKeyPath]:
        if agent_io.version == RawMessagesSchema.version:
            messages = Messages.model_validate(payload)
            return list(messages.file_iterator())

        _, _, input_files = extract_files(agent_io.json_schema, payload)

        if agent_io.uses_messages:
            try:
                messages = Messages.model_validate(payload)
            except ValidationError:
                _logger.exception("Error validating extra messages")
                return input_files

            # Here there could be an issue if we had an old input
            # using a deprecated key for messages
            # We should be good because the ConversationHandler rewrites the input anyway
            # It's just a lot of unnecessary work
            # TODO: We should really just serialize to messages once and the sanitize the input
            input_files.extend(list(messages.file_iterator(prefix=INPUT_KEY_MESSAGES)))

        return input_files

    async def handle_run(self, run: TaskRunIO, task_variant: VariantIO):
        input_files = self._extract_files(task_variant.input_schema, run.task_input)
        output_files = self._extract_files(task_variant.output_schema, run.task_output)

        async with asyncio.TaskGroup() as tg:
            for file in input_files:
                tg.create_task(sentry_wrap(self._handle_file(file)))
            for file in output_files:
                tg.create_task(sentry_wrap(self._handle_file(file)))

        self._apply_files(run.task_input, input_files, include={"content_type", "url", "storage_url"})
        self._apply_files(run.task_output, output_files, include={"content_type", "url", "storage_url"})

    async def _handle_file(self, file: FileWithKeyPath):
        if not file.url and not file.data:
            # Skipping, only reason a file might not have data is if it's private
            return

        if file.url and not file.data:
            await download_file(file)

        bts = file.content_bytes()
        if not bts:
            _logger.warning("file has no content bytes", extra={"file": file.model_dump(exclude={"data"})})
            # Skipping, only reason a file might not have data is if it's private
            return

        file.storage_url = await self._file_storage.store_file(
            FileData(contents=bts, content_type=file.content_type),
            folder_path=self._folder_path,
        )

        if file.url and file.url.startswith("data:"):
            file.url = None

    @classmethod
    def _apply_files(
        cls,
        payload: dict[str, Any],
        files: Iterable[FileWithKeyPath],
        include: set[str] | None,
    ):
        for file in files:
            if not file.url:
                file.url = file.storage_url
            try:
                set_at_keypath(
                    payload,
                    file.key_path,
                    file.model_dump(include=include, exclude_none=True),
                )
            except InvalidKeyPathError as e:
                _logger.exception(
                    "Error setting file in task run input",
                    extra={"file": file.model_dump(exclude={"data"})},
                    exc_info=e,
                )
                continue
