from core.domain.message import Message
from core.domain.tool_call import ToolCall, ToolCallRequestWithID
from core.providers.groq.groq_domain import GroqMessage, _ToolCall  # pyright: ignore [reportPrivateUsage]


class TestMessageToStandard:
    def test_message_to_standard(self) -> None:
        message = GroqMessage(content='{"message": "Hello you"}', role="assistant")
        assert message.to_standard() == {
            "role": "assistant",
            "content": [{"type": "text", "text": '{"message": "Hello you"}'}],
        }


class TestGroqMessageFromDomain:
    def test_groq_message_from_domain(self) -> None:
        messages = [
            Message(content="Hello you", role=Message.Role.SYSTEM),
            Message(content="What is the current time ?", role=Message.Role.USER),
            Message(
                content="",
                tool_call_requests=[
                    ToolCallRequestWithID(
                        id="1",
                        tool_name="get_current_time",
                        tool_input_dict={"timezone": "Europe/Paris"},
                    ),
                ],
                role=Message.Role.ASSISTANT,
            ),
            Message(
                content="",
                tool_call_results=[
                    ToolCall(
                        id="1",
                        tool_name="get_current_time",
                        tool_input_dict={"timezone": "Europe/Paris"},
                        result="2021-01-01 12:00:00",
                    ),
                ],
                role=Message.Role.USER,
            ),
        ]
        groq_messages: list[GroqMessage] = []
        for m in messages:
            groq_messages.extend(GroqMessage.from_domain(m))
        assert groq_messages == [
            GroqMessage(content="Hello you", role="system"),
            GroqMessage(content="What is the current time ?", role="user"),
            GroqMessage(
                role="assistant",
                tool_calls=[
                    _ToolCall(
                        id="1",
                        function=_ToolCall.Function(
                            name="get_current_time",
                            arguments='{"timezone": "Europe/Paris"}',
                        ),
                    ),
                ],
            ),
            GroqMessage(
                role="tool",
                content="2021-01-01 12:00:00",
                tool_call_id="1",
            ),
        ]
