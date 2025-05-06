import logging
from typing import AsyncIterator

from pydantic import ValidationError

from core.agents.task_input_import_task import (
    TaskInputImportTaskInput,
    stream_task_inputs_import_task,
    task_input_import,
)
from core.domain.errors import InvalidGenerationError
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentInput


class TaskInputService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def import_input(
        self,
        task: SerializableTaskVariant,
        inputs_text: str,
    ) -> list[AgentInput]:
        import_input_task_input = TaskInputImportTaskInput(
            task_name=task.name,
            input_json_schema=task.input_schema.json_schema,
            raw_input_data=inputs_text,
        )
        task_output = await task_input_import(import_input_task_input)
        try:
            return [task.validate_input(input) for input in task_output.extracted_task_inputs or []]
        except ValidationError as e:
            raise InvalidGenerationError(msg=str(e)) from e

    async def stream_import_input(
        self,
        task: SerializableTaskVariant,
        inputs_text: str,
    ) -> AsyncIterator[tuple[int, AgentInput]]:
        import_input_task_input = TaskInputImportTaskInput(
            task_name=task.name,
            input_json_schema=task.input_schema.json_schema,
            raw_input_data=inputs_text,
        )

        idx = 0

        async for task_output in stream_task_inputs_import_task(import_input_task_input):
            if task_output.extracted_task_inputs is None or len(task_output.extracted_task_inputs) == 0:
                continue

            new_idx = len(task_output.extracted_task_inputs) - 1
            if new_idx != idx:
                yield idx, task.validate_input(task_output.extracted_task_inputs[idx])
                idx = new_idx
            try:
                yield idx, task.validate_input(task_output.extracted_task_inputs[idx], partial=True)
            except ValidationError as e:
                raise InvalidGenerationError(msg=str(e)) from e
