import logging
import os
from typing import Any

from core.agents.moderation_task import (
    ModerationOutput,
    TaskRunModerationInput,
    TaskVersionModerationInput,
    run_task_run_moderation_task,
    run_task_version_moderation_task,
)
from core.domain.errors import ContentModerationError
from core.domain.fields.chat_message import ChatMessage


def capture_content_moderation_error(e: ContentModerationError, tenant: str, task_name: str):
    # Special management of the content moderation error that are grouped by tenant and task in Sentry
    # In order to simply track their volumetry

    e.fingerprint = [tenant, task_name]
    new_message = f"tenant: {tenant}, task: {task_name}, message: {e.args[0]}"
    e.args = (new_message,)
    e.capture_if_needed()


class ModerationService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def is_moderation_activated(cls) -> bool:
        return os.getenv("MODERATION_ENABLED", "true").lower() == "true"

    async def run_task_version_moderation_process(
        self,
        user_and_org_str: str,
        tenant: str,
        task_id: str,
        task_str: str,
        iteration: int | None,
        task_name: str,
        instructions: str | None,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        chat_messages: list[ChatMessage] | None,
    ) -> None:
        if not self.is_moderation_activated():
            return

        moderation_input = TaskVersionModerationInput(
            chat_messages=chat_messages,
            task_name=task_name,
            task_instructions=instructions,
            task_input_schema=input_schema,
            task_output_schema=output_schema,
        )

        # Run the moderation task
        result = await run_task_version_moderation_task(moderation_input)

        # Handle the moderation result
        await self._handle_task_version_moderation_result(
            tenant,
            task_id,
            user_and_org_str,
            task_str,
            iteration,
            result,
        )

    @classmethod
    async def _handle_task_version_moderation_result(
        cls,
        tenant: str,
        task_id: str,
        user_and_org_str: str,
        task_str: str,
        iteration: int | None,
        result: ModerationOutput,
    ):
        if result.is_breaching_terms:
            reason_str: str = result.term_breaching_category.value if result.term_breaching_category else ""
            if iteration:
                message = f"{user_and_org_str} created an iteration that is breaching terms ({reason_str}): {task_str} (iteration:{iteration})"
            else:
                message = f"{user_and_org_str} created a task that is breaching terms ({reason_str}): {task_str}"

            error = ContentModerationError(message, capture=True)
            capture_content_moderation_error(error, tenant, task_id)

    async def run_task_run_moderation_process(
        self,
        tenant: str,
        task_id: str,
        user_and_org_str: str,
        task_run_str: str,
        task_run_input: dict[str, Any],
    ) -> None:
        # Run moderation is deactivated
        return

        if not self.is_moderation_activated:
            return

        moderation_input = TaskRunModerationInput(
            task_run_input=task_run_input,
        )

        # Run the moderation task
        result = await run_task_run_moderation_task(moderation_input)

        # Handle the moderation result
        await self._handle_task_run_moderation_result(tenant, task_id, user_and_org_str, task_run_str, result)

    @classmethod
    async def _handle_task_run_moderation_result(
        cls,
        tenant: str,
        task_id: str,
        user_and_org_str: str,
        task_run_str: str,
        result: ModerationOutput,
    ) -> None:
        if result.is_breaching_terms:
            reason_str: str = result.term_breaching_category.value if result.term_breaching_category else ""
            message = f"{user_and_org_str} created a task run that is breaching terms ({reason_str}): {task_run_str}"
            error = ContentModerationError(message, capture=True)
            capture_content_moderation_error(error, tenant, task_id)
