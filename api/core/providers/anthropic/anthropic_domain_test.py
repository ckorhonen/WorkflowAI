from core.domain.fields.file import File
from core.domain.message import MessageDeprecated
from core.domain.tool_call import ToolCall, ToolCallRequestWithID
from core.providers.anthropic.anthropic_domain import (
    AnthropicMessage,
    DocumentContent,
    FileSource,
    ImageContent,
    TextContent,
    ToolResultContent,
    ToolUseContent,
)


def test_anthropic_message_from_domain_user() -> None:
    domain_message = MessageDeprecated(
        role=MessageDeprecated.Role.USER,
        content="Hello, how are you?",
    )

    anthropic_message = AnthropicMessage.from_domain(domain_message)

    assert anthropic_message.role == "user"
    assert anthropic_message.content[0].type == "text"
    assert anthropic_message.content[0].text == "Hello, how are you?"


def test_anthropic_message_from_domain_assistant() -> None:
    domain_message = MessageDeprecated(
        role=MessageDeprecated.Role.ASSISTANT,
        content="I'm doing well, thank you!",
    )

    anthropic_message = AnthropicMessage.from_domain(domain_message)

    assert anthropic_message.role == "assistant"
    assert anthropic_message.content[0].type == "text"
    assert anthropic_message.content[0].text == "I'm doing well, thank you!"


def test_anthropic_message_to_standard_with_content_array() -> None:
    anthropic_message = AnthropicMessage(
        role="user",
        content=[
            TextContent(
                type="text",
                text="Which model has the highest human preference win rates?",
            ),
        ],
    )

    standard_message = anthropic_message.to_standard()

    assert standard_message == {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Which model has the highest human preference win rates?",
            },
        ],
    }


def test_anthropic_message_to_standard_with_document_url() -> None:
    anthropic_message = AnthropicMessage(
        role="user",
        content=[
            DocumentContent(
                type="document",
                source=FileSource(
                    type="base64",
                    media_type="application/pdf",
                    data="bla",
                ),
            ),
        ],
    )

    standard_message = anthropic_message.to_standard()

    assert standard_message == {
        "role": "user",
        "content": [{"type": "document_url", "source": {"url": "data:application/pdf;base64,bla"}}],
    }


def test_anthropic_message_to_standard_with_image_file() -> None:
    anthropic_message = AnthropicMessage(
        role="user",
        content=[ImageContent(type="image", source=FileSource(type="base64", media_type="image/png", data="bla"))],
    )

    standard_message = anthropic_message.to_standard()

    assert standard_message == {
        "role": "user",
        "content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64,bla"}}],
    }


def test_anthropic_message_from_domain_text_before_files() -> None:
    message = MessageDeprecated(
        role=MessageDeprecated.Role.USER,
        content="Hello world",
        files=[File(data="test_data", content_type="image/png")],
    )

    anthropic_message = AnthropicMessage.from_domain(message)
    assert len(anthropic_message.content) == 2
    assert isinstance(anthropic_message.content[0], TextContent)
    assert anthropic_message.content[0].text == "Hello world"
    assert isinstance(anthropic_message.content[1], ImageContent)


def test_anthropic_message_from_domain_with_tool_call_requests() -> None:
    message = MessageDeprecated(
        role=MessageDeprecated.Role.ASSISTANT,
        content="Let me check the weather for you.",
        tool_call_requests=[
            ToolCallRequestWithID(
                id="weather_1",
                tool_name="WeatherCheckTask",
                tool_input_dict={"location": {"latitude": 48.8566, "longitude": 2.3522}},
            ),
        ],
    )

    anthropic_message = AnthropicMessage.from_domain(message)
    assert anthropic_message == AnthropicMessage(
        role="assistant",
        content=[
            TextContent(type="text", text="Let me check the weather for you."),
            ToolUseContent(
                type="tool_use",
                id="weather_1",
                name="WeatherCheckTask",
                input={"location": {"latitude": 48.8566, "longitude": 2.3522}},
            ),
        ],
    )


def test_anthropic_message_from_domain_with_tool_call_results() -> None:
    message = MessageDeprecated(
        role=MessageDeprecated.Role.USER,
        content="Here's what I found:",
        tool_call_results=[
            ToolCall(
                id="weather_1",
                tool_name="WeatherCheckTask",
                tool_input_dict={"location": {"latitude": 48.8566, "longitude": 2.3522}},
                result={"temperature": 20, "condition": "sunny"},
                error=None,
            ),
        ],
    )

    anthropic_message = AnthropicMessage.from_domain(message)
    assert anthropic_message == AnthropicMessage(
        role="user",
        content=[
            TextContent(type="text", text="Here's what I found:"),
            ToolResultContent(
                type="tool_result",
                tool_use_id="weather_1",
                content=str({"temperature": 20, "condition": "sunny"}),
            ),
        ],
    )


def test_anthropic_message_from_domain_with_tool_call_error() -> None:
    message = MessageDeprecated(
        role=MessageDeprecated.Role.USER,
        content="I encountered an error:",
        tool_call_results=[
            ToolCall(
                id="weather_1",
                tool_name="WeatherCheckTask",
                tool_input_dict={"location": {"latitude": 48.8566, "longitude": 2.3522}},
                result=None,
                error="API unavailable",
            ),
        ],
    )

    anthropic_message = AnthropicMessage.from_domain(message)
    assert anthropic_message == AnthropicMessage(
        role="user",
        content=[
            TextContent(type="text", text="I encountered an error:"),
            ToolResultContent(
                type="tool_result",
                tool_use_id="weather_1",
                content="Error: API unavailable",
            ),
        ],
    )
