# pyright: reportPrivateUsage=false

from api.services.runs._stored_message import StoredMessages
from core.domain.fields.file import File
from core.domain.message import Message, MessageContent
from core.domain.tool_call import ToolCallRequest

from ._run_previews import (
    _messages_list_preview,
    _messages_preview,
    _tool_call_request_preview,
)


class TestMessagesPreview:
    def test_messages_preview(self):
        messages = [Message.with_text("Hello, world!", role="user")]
        assert _messages_list_preview(messages) == "Hello, world!"

    def test_with_system_message(self):
        messages = [
            Message.with_text("You are a helpful assistant.", role="system"),
            Message.with_text("Hello, world!", role="user"),
        ]
        assert _messages_list_preview(messages) == "Hello, world!"

    def test_messages_preview_with_file(self):
        messages = [Message(content=[MessageContent(file=File(url="https://example.com/file.png"))], role="user")]
        assert _messages_list_preview(messages) == "[[img:https://example.com/file.png]]"

    def test_system_only(self):
        messages = [Message.with_text("Hello, world!", role="system")]
        assert _messages_list_preview(messages) == "Hello, world!"


class TestToolCallRequestPreview:
    def test_tool_call_request_preview(self):
        assert (
            _tool_call_request_preview([ToolCallRequest(tool_name="test_name", tool_input_dict={"arg": "value"})])
            == "tool: test_name(arg: value)"
        )

    def test_tool_call_request_preview_multiple(self):
        assert (
            _tool_call_request_preview(
                [
                    ToolCallRequest(tool_name="test_name", tool_input_dict={"arg": "value"}),
                    ToolCallRequest(tool_name="test_name2", tool_input_dict={"arg": "value2"}),
                ],
            )
            == "tools: [test_name(arg: value), test_name2(arg: value2)]"
        )


class TestPrivateComputePreview:
    def test_with_message_replies(self):
        messages = StoredMessages.model_validate(
            {
                "value": "Hello, world!",
                "workflowai.messages": [{"role": "user", "content": [{"text": "Hello, world!"}]}],
            },
        )
        assert _messages_preview(messages) == 'value: "Hello, world!" | messages: Hello, world!'

    def test_reply_empty_object(self):
        messages = StoredMessages.model_validate(
            {
                "value": "Hello, world!",
                "workflowai.messages": [{"role": "user", "content": [{"text": "Hello, world!"}]}],
            },
        )
        assert _messages_preview(messages) == 'value: "Hello, world!" | messages: Hello, world!'
