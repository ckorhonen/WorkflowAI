import base64
from typing import List

import pytest

from core.domain.errors import InvalidRunOptionsError, ModelDoesNotSupportMode, UnpriceableRunError
from core.domain.message import File, MessageDeprecated
from core.domain.models import Model
from core.domain.tool_call import ToolCall, ToolCallRequestWithID
from core.providers.amazon_bedrock.amazon_bedrock_domain import (
    AmazonBedrockMessage,
    AmazonBedrockSystemMessage,
    ContentBlock,
)


def test_AmazonBedrockMessage_from_domain():
    # Test with text content
    text_message = MessageDeprecated(role=MessageDeprecated.Role.USER, content="Hello, world!")
    anthropic_message = AmazonBedrockMessage.from_domain(text_message)
    assert len(anthropic_message.content) == 1
    assert anthropic_message.content[0].text == "Hello, world!"
    assert anthropic_message.role == "user"

    # Test with image content
    image_data = base64.b64encode(b"fake_image_data").decode()
    image_message = MessageDeprecated(
        role=MessageDeprecated.Role.USER,
        content="Check this image:",
        files=[File(data=image_data, content_type="image/png")],
    )
    anthropic_message = AmazonBedrockMessage.from_domain(image_message)
    assert len(anthropic_message.content) == 2
    assert anthropic_message.content[0].text == "Check this image:"
    assert anthropic_message.content[1].image
    assert anthropic_message.content[1].image.format == "png"
    assert anthropic_message.content[1].image.source.bytes == image_data
    assert anthropic_message.role == "user"

    # Test with unsupported image format
    with pytest.raises(ModelDoesNotSupportMode):
        AmazonBedrockMessage.from_domain(
            MessageDeprecated(
                role=MessageDeprecated.Role.USER,
                content="Unsupported image:",
                files=[File(data=image_data, content_type="image/tiff")],
            ),
        )

    # Test assistant message
    assistant_message = MessageDeprecated(role=MessageDeprecated.Role.ASSISTANT, content="I'm here to help!")
    anthropic_message = AmazonBedrockMessage.from_domain(assistant_message)
    assert len(anthropic_message.content) == 1
    assert anthropic_message.content[0].text == "I'm here to help!"
    assert anthropic_message.role == "assistant"


def test_AmazonBedrockSystemMessage_from_domain() -> None:
    # Test valid system message
    system_message = MessageDeprecated(role=MessageDeprecated.Role.SYSTEM, content="You are a helpful assistant.")
    anthropic_system_message = AmazonBedrockSystemMessage.from_domain(system_message)
    assert anthropic_system_message.text == "You are a helpful assistant."

    # Test system message with image (should raise an error)
    image_data = base64.b64encode(b"fake_image_data").decode()
    system_message_with_image = MessageDeprecated(
        role=MessageDeprecated.Role.SYSTEM,
        content="System message with image",
        files=[File(data=image_data, content_type="image/png")],
    )
    with pytest.raises(InvalidRunOptionsError):
        AmazonBedrockSystemMessage.from_domain(system_message_with_image)


@pytest.mark.parametrize(
    "content, expected_tokens",
    [
        (["Hello, world!"], 4),
        (["This is a longer message with multiple words."], 9),
        (["First message", "Second message"], 4),
    ],
)
def test_AmazonBedrockMessage_token_count(content: List[str], expected_tokens: int) -> None:
    message = AmazonBedrockMessage(content=[ContentBlock(text=text) for text in content])
    model = Model.CLAUDE_3_5_SONNET_20240620  # Using this as a placeholder model
    assert message.token_count(model) == expected_tokens


def test_AmazonBedrockMessage_token_count_with_image() -> None:
    message = AmazonBedrockMessage(
        content=[
            ContentBlock(text="Check this image:"),
            ContentBlock(image=ContentBlock.Image(format="png", source=ContentBlock.Image.Source(bytes="fake_data"))),
        ],
    )
    model = Model.CLAUDE_3_5_SONNET_20240620
    with pytest.raises(UnpriceableRunError, match="Token counting for images is not implemented"):
        message.token_count(model)


@pytest.mark.parametrize(
    "text, expected_tokens",
    [
        ("You are a helpful assistant.", 6),
        ("This is a longer system message with multiple words.", 10),
    ],
)
def test_AmazonBedrockSystemMessage_token_count(text: str, expected_tokens: int) -> None:
    system_message = AmazonBedrockSystemMessage(text=text)
    model = Model.CLAUDE_3_5_SONNET_20240620  # Using this as a placeholder model
    assert system_message.token_count(model) == expected_tokens


class TestFileContentBlock:
    def test_from_domain(self) -> None:
        image = File(data=base64.b64encode(b"fake_image_data").decode(), content_type="image/png")
        image_block = ContentBlock.Image.from_domain(image)
        assert image_block.format == "png"
        assert image_block.source.bytes == "ZmFrZV9pbWFnZV9kYXRh"

        assert image.to_url() == "data:image/png;base64,ZmFrZV9pbWFnZV9kYXRh", "sanity"
        assert image_block.to_url() == image.to_url()


class TestMessageToStandard:
    def test_message_to_standard(self) -> None:
        message = AmazonBedrockMessage(
            role="user",
            content=[
                ContentBlock(text="Hello, world!"),
                ContentBlock(
                    image=ContentBlock.Image(
                        format="png",
                        source=ContentBlock.Image.Source(bytes="ZmFrZV9pbWFnZV9kYXRh"),
                    ),
                ),
            ],
        )
        assert message.to_standard() == {
            "role": "user",
            "content": [
                {"type": "text", "text": "Hello, world!"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,ZmFrZV9pbWFnZV9kYXRh"}},
            ],
        }

    def test_message_text_only(self) -> None:
        message = AmazonBedrockMessage(role="user", content=[ContentBlock(text="Hello, world!")])
        assert message.to_standard() == {"role": "user", "content": "Hello, world!"}

    def test_message_image_jpeg(self):
        """Test that we correclly handle the image format"""
        message = AmazonBedrockMessage(
            role="user",
            content=[
                ContentBlock(
                    image=ContentBlock.Image(
                        format="jpeg",
                        source=ContentBlock.Image.Source(bytes="ZmFrZV9pbWFnZV9kYXRh"),
                    ),
                ),
            ],
        )
        assert message.to_standard() == {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,ZmFrZV9pbWFnZV9kYXRh"}},
            ],
        }


class TestContentBlockWithTools:
    def test_content_block_with_tool_use(self):
        block = ContentBlock(
            toolUse=ContentBlock.ToolUse(
                toolUseId="test_id",
                name="test_tool",
                input={"param": "value"},
            ),
        )
        standard = block.to_standard()
        assert len(standard) == 1
        assert standard[0] == {
            "id": "test_id",
            "tool_name": "test_tool",  # Assuming native_tool_name_to_internal returns same name for test
            "tool_input_dict": {"param": "value"},
            "type": "tool_call_request",
        }

    def test_content_block_with_tool_result_success(self):
        block = ContentBlock(
            toolResult=ContentBlock.ToolResult(
                toolUseId="test_id",
                content=[
                    ContentBlock.ToolResult.ToolResultContentBlock(
                        json={"result": "success_value"},
                    ),
                ],
                status="success",
            ),
        )
        standard = block.to_standard()
        assert len(standard) == 1
        assert standard[0] == {
            "id": "test_id",
            "tool_name": None,
            "tool_input_dict": None,
            "result": {"result": "success_value"},
            "error": None,
            "type": "tool_call_result",
        }

    def test_content_block_with_tool_result_error(self):
        block = ContentBlock(
            toolResult=ContentBlock.ToolResult(
                toolUseId="test_id",
                content=[
                    ContentBlock.ToolResult.ToolResultContentBlock(
                        json={"error": "error_message"},
                    ),
                ],
                status="error",
            ),
        )
        standard = block.to_standard()
        assert len(standard) == 1
        assert standard[0] == {
            "id": "test_id",
            "tool_name": None,
            "tool_input_dict": None,
            "result": {"error": "error_message"},
            "error": "error",
            "type": "tool_call_result",
        }


class TestAmazonBedrockMessageWithTools:
    def test_from_domain_with_tool_call_request(self):
        message = MessageDeprecated(
            role=MessageDeprecated.Role.USER,
            content="Use tool",
            tool_call_requests=[
                ToolCallRequestWithID(
                    id="test_id",
                    tool_name="test_tool",
                    tool_input_dict={"param": "value"},
                ),
            ],
        )
        bedrock_message = AmazonBedrockMessage.from_domain(message)
        assert len(bedrock_message.content) == 2  # text content and tool use
        assert bedrock_message.content[0].text == "Use tool"
        assert bedrock_message.content[1].toolUse is not None
        assert bedrock_message.content[1].toolUse.toolUseId == "test_id"
        assert (
            bedrock_message.content[1].toolUse.name == "test_tool"
        )  # Assuming internal_tool_name_to_native_tool_call returns same name
        assert bedrock_message.content[1].toolUse.input == {"param": "value"}

    def test_from_domain_with_tool_call_result(self):
        message = MessageDeprecated(
            role=MessageDeprecated.Role.ASSISTANT,
            content="Tool result",
            tool_call_results=[
                ToolCall(
                    id="test_id",
                    tool_name="test_tool",
                    tool_input_dict={"param": "value"},
                    result='{"result": "success_value"}',
                ),
            ],
        )
        bedrock_message = AmazonBedrockMessage.from_domain(message)
        assert len(bedrock_message.content) == 2  # text content and tool result
        assert bedrock_message.content[0].text == "Tool result"
        assert bedrock_message.content[1].toolResult is not None
        assert bedrock_message.content[1].toolResult.toolUseId == "test_id"
        assert len(bedrock_message.content[1].toolResult.content) == 1
        assert bedrock_message.content[1].toolResult.content[0].json_content == {"result": "success_value"}

    def test_from_domain_with_non_json_tool_result(self):
        message = MessageDeprecated(
            role=MessageDeprecated.Role.ASSISTANT,
            content="Tool result",
            tool_call_results=[
                ToolCall(
                    id="test_id",
                    tool_name="test_tool",
                    tool_input_dict={"param": "value"},
                    result="plain text result",
                ),
            ],
        )
        bedrock_message = AmazonBedrockMessage.from_domain(message)
        assert len(bedrock_message.content) == 2
        assert bedrock_message.content[1].toolResult is not None
        assert bedrock_message.content[1].toolResult.content[0].json_content == {"result": "plain text result"}

    def test_from_domain_with_invalid_id(self):
        message = MessageDeprecated(
            role=MessageDeprecated.Role.ASSISTANT,
            content="Tool result",
            tool_call_results=[
                ToolCall(
                    id="@whateverIAm",
                    tool_name="test_tool",
                    tool_input_dict={"param": "value"},
                    result="plain text result",
                ),
            ],
        )
        bedrock_message = AmazonBedrockMessage.from_domain(message)
        assert len(bedrock_message.content) == 2
        assert bedrock_message.content[1].toolResult is not None
        assert (
            bedrock_message.content[1].toolResult.toolUseId
            == "b5d2b7dfe4a49cbaf8f3ee7b6b3589703e16d06d4a4f4c73562406a0d205c78b"
        )
        assert bedrock_message.content[1].toolResult.content[0].json_content == {"result": "plain text result"}
