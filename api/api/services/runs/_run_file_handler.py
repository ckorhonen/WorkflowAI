import asyncio
import logging
from typing import Any

from core.domain.agent_run import AgentRun
from core.domain.task_variant import SerializableTaskVariant
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

    async def handle_run(self, run: AgentRun, task_variant: SerializableTaskVariant):
        _, _, input_files = extract_files(task_variant.input_schema.json_schema, run.task_input)
        _, _, output_files = extract_files(task_variant.output_schema.json_schema, run.task_output)

        async with asyncio.TaskGroup() as tg:
            for file in input_files:
                tg.create_task(sentry_wrap(self._handle_file(file)))
            for file in output_files:
                tg.create_task(sentry_wrap(self._handle_file(file)))

        self._apply_files(run.task_input, input_files, {"content_type", "url", "storage_url"})
        self._apply_files(run.task_output, output_files, {"content_type", "url", "storage_url"})

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

    @classmethod
    def _apply_files(
        cls,
        payload: dict[str, Any],
        files: list[FileWithKeyPath],
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
