import logging
from typing import Any, Sequence

from pydantic import ValidationError

from core.domain.agent_run import AgentRun
from core.domain.message import Messages
from core.domain.task_io import RawMessagesSchema, SerializableTaskIO
from core.domain.task_variant import SerializableTaskVariant
from core.domain.tool_call import ToolCallRequest
from core.utils.models.previews import compute_preview


def _messages_preview(payload: Any):
    try:
        validated = Messages.model_validate(payload)
    except ValidationError:
        logging.getLogger("RunsService").warning("Error validating messages", exc_info=True)
        return None

    try:
        first_user_message = next((m for m in validated.messages if m.role == "user"))
    except StopIteration:
        return None

    if not first_user_message.content:
        return None

    content = first_user_message.content[0]
    if content.file:
        return compute_preview(content.file)

    if content.text:
        return compute_preview(content.text)

    return None


def _compute_preview(payload: Any, agent_io: SerializableTaskIO):
    if agent_io.version == RawMessagesSchema.version:
        # Then we try and preview the first user message
        if preview := _messages_preview(payload):
            return preview

    return compute_preview(payload)


def _tool_call_request_preview(tool_call_requests: Sequence[ToolCallRequest]):
    if len(tool_call_requests) == 1:
        return f"tool: {tool_call_requests[0].preview}"

    return f"tools: [{', '.join([t.preview for t in tool_call_requests])}]"


def assign_run_previews(run: AgentRun, variant: SerializableTaskVariant):
    if not run.task_input_preview:
        run.task_input_preview = _compute_preview(run.task_input, variant.input_schema)
    if not run.task_output_preview:
        if run.task_output:
            run.task_output_preview = _compute_preview(run.task_output, variant.output_schema)
        elif run.tool_call_requests:
            run.task_output_preview = _tool_call_request_preview(run.tool_call_requests)
