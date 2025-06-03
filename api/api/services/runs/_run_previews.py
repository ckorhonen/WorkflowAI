from typing import Sequence

from api.services.runs._stored_message import StoredMessages
from core.domain.agent_run import AgentRun
from core.domain.task_variant import SerializableTaskVariant
from core.domain.tool_call import ToolCallRequest
from core.utils.models.previews import DEFAULT_PREVIEW_MAX_LEN, compute_preview


def _messages_preview(
    messages: StoredMessages,
    include_roles: set[str] = {"user"},
    max_len: int = DEFAULT_PREVIEW_MAX_LEN,
):
    if not messages.messages:
        return None

    first_user_message = next((m for m in messages.messages if m.role in include_roles), messages.messages[0])

    if not first_user_message.content:
        return None

    content = first_user_message.content[0]
    if content.file:
        return compute_preview(content.file, max_len=max_len)

    if content.text:
        return compute_preview(content.text)

    return None


def _tool_call_request_preview(tool_call_requests: Sequence[ToolCallRequest]):
    if len(tool_call_requests) == 1:
        return f"tool: {tool_call_requests[0].preview}"

    return f"tools: [{', '.join([t.preview for t in tool_call_requests])}]"


def _compute_messages_preview(messages: StoredMessages):
    if extra := messages.model_extra:
        first_preview = compute_preview(extra)
        if len(first_preview) < DEFAULT_PREVIEW_MAX_LEN:
            if second_preview := _messages_preview(
                messages,
                include_roles={"user", "assistant"},
                max_len=DEFAULT_PREVIEW_MAX_LEN - len(first_preview),
            ):
                first_preview += f" | messages: {second_preview}"
        return first_preview
    return _messages_preview(messages) or ""


def assign_run_previews(run: AgentRun, variant: SerializableTaskVariant, messages: StoredMessages | None):
    if not run.task_input_preview:
        run.task_input_preview = _compute_messages_preview(messages) if messages else compute_preview(run.task_input)
    if not run.task_output_preview:
        if run.task_output:
            run.task_output_preview = compute_preview(run.task_output)
        elif run.tool_call_requests:
            run.task_output_preview = _tool_call_request_preview(run.tool_call_requests)
