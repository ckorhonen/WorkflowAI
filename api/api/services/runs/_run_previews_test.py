from core.domain.tool_call import ToolCallRequest

from ._run_previews import _messages_preview, _tool_call_request_preview  # pyright: ignore [reportPrivateUsage]


class TestMessagesPreview:
    def test_messages_preview(self):
        assert (
            _messages_preview({"messages": [{"role": "user", "content": [{"text": "Hello, world!"}]}]})
            == "Hello, world!"
        )

    def test_messages_preview_with_file(self):
        assert (
            _messages_preview(
                {"messages": [{"role": "user", "content": [{"file": {"url": "https://example.com/file.png"}}]}]},
            )
            == "[[img:https://example.com/file.png]]"
        )


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
