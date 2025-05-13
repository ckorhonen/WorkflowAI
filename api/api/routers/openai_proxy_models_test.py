from typing import Any

import pytest

from api.routers.openai_proxy_models import (
    EnvironmentRef,
    ModelRef,
    OpenAIProxyChatCompletionRequest,
    OpenAIProxyContent,
    OpenAIProxyImageURL,
    OpenAIProxyMessage,
)
from core.domain.errors import BadRequestError
from core.domain.fields.file import File
from core.domain.message import Message, MessageContent
from core.domain.models.models import Model
from core.domain.task_group_properties import ToolChoiceFunction
from core.domain.tool_call import ToolCall
from core.providers.base.provider_error import MissingModelError


class TestOpenAIProxyChatCompletionRequest:
    def test_minimal_payload(self):
        """Check that we have enough defaults to accept minimal payload"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
            },
        )
        assert payload


class TestOpenAIProxyContent:
    def test_image_url_to_domain(self):
        payload = OpenAIProxyContent(
            type="image_url",
            image_url=OpenAIProxyImageURL(
                url="https://hello.com/image.png",
            ),
        )
        assert payload.to_domain() == MessageContent(file=File(url="https://hello.com/image.png"))


class TestOpenAIProxyMessageToDomain:
    def test_with_tool_calls(self):
        payload = OpenAIProxyMessage(
            role="tool",
            content="Hello, world!",
            tool_call_id="1",
        )
        assert payload.to_domain() == Message(
            role="user",
            content=[
                MessageContent(
                    tool_call_result=ToolCall(
                        id="1",
                        tool_name="",
                        tool_input_dict={},
                        result="Hello, world!",
                    ),
                ),
            ],
        )


class TestOpenAIProxyChatCompletionRequestToolChoice:
    @pytest.mark.parametrize(
        "tool_choice_input, expected_tool_choice_output",
        [
            (None, None),
            ("auto", "auto"),
            ("none", "none"),
            ("required", "required"),
            (
                {"type": "function", "function": {"name": "my_function"}},
                ToolChoiceFunction(name="my_function"),
            ),
            ("invalid_choice", None),
        ],
    )
    def test_workflowai_tool_choice(self, tool_choice_input: Any, expected_tool_choice_output: Any):
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
                "tool_choice": tool_choice_input,
            },
        )
        assert payload.worflowai_tool_choice == expected_tool_choice_output


class TestOpenAIProxyChatCompletionRequestExtractReferences:
    def test_model_only(self):
        """Test when only model is provided"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
            },
        )
        refs = payload.extract_references()
        assert isinstance(refs, ModelRef)
        assert refs.model == Model.GPT_4O_LATEST
        assert refs.agent_id is None

    def test_agent_model_format(self):
        """Test when model is in format agent_id/model"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "my-agent/gpt-4o",
            },
        )
        refs = payload.extract_references()
        assert isinstance(refs, ModelRef)
        assert refs.model == Model.GPT_4O_LATEST
        assert refs.agent_id == "my-agent"

    def test_agent_schema_env_format(self):
        """Test when model is in format agent_id/#schema_id/environment"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "my-agent/#123/production",
            },
        )
        refs = payload.extract_references()
        assert isinstance(refs, EnvironmentRef)
        assert refs.agent_id == "my-agent"
        assert refs.schema_id == 123
        assert refs.environment == "production"

    def test_body_parameters(self):
        """Test when references are provided in body parameters"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
                "agent_id": "my-agent",
                "schema_id": 123,
                "environment": "production",
            },
        )
        refs = payload.extract_references()
        assert isinstance(refs, EnvironmentRef)
        assert refs.agent_id == "my-agent"
        assert refs.schema_id == 123
        assert refs.environment == "production"

    def test_invalid_model(self):
        """Test with invalid model"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "invalid-model",
            },
        )
        with pytest.raises(MissingModelError):
            payload.extract_references()

    def test_invalid_environment(self):
        """Test with invalid environment"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "",  # model is empty here otherwise we fallback on the model in the body
                "agent_id": "my-agent",
                "schema_id": 123,
                "environment": "invalid-env",
            },
        )
        with pytest.raises(BadRequestError) as exc_info:
            payload.extract_references()
        assert "is not a valid environment" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test when some required fields are missing"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
                "agent_id": "my-agent",
                "environment": "production",
                # schema_id is missing
            },
        )
        with pytest.raises(BadRequestError) as exc_info:
            payload.extract_references()
        assert "agent_id, environment and schema_id must be provided" in str(exc_info.value)

    def test_provider_prefixed_model(self):
        """Test when model has provider prefix"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "openai/gpt-4o",
                "agent_id": "my-agent",  # otherwise the agent id will be `openai`
            },
        )
        refs = payload.extract_references()
        assert isinstance(refs, ModelRef)
        assert refs.model == Model.GPT_4O_LATEST
        assert refs.agent_id == "my-agent"
