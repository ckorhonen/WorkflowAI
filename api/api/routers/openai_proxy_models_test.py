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
from core.domain.task_group_properties import TaskGroupProperties, ToolChoiceFunction
from core.domain.tool import Tool
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
        assert payload.to_domain() == MessageContent(file=File(url="https://hello.com/image.png", format="image"))


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

    @pytest.mark.parametrize(
        "tool_choice_input, expected_tool_choice_output",
        [
            pytest.param(None, None, id="none"),
            pytest.param("auto", "auto", id="auto"),
            pytest.param("none", "none", id="none"),
            pytest.param(
                {"name": "my_function"},
                ToolChoiceFunction(name="my_function"),
                id="function",
            ),
            pytest.param("invalid_choice", None, id="invalid"),
        ],
    )
    def test_workflowai_tool_choice_function_call(self, tool_choice_input: Any, expected_tool_choice_output: Any):
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
                "function_call": tool_choice_input,
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


class TestOpenAIProxyChatCompletionRequestApplyTo:
    @pytest.fixture()
    def completion_request(self):
        return OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.5,
                "presence_penalty": 0.3,
                "parallel_tool_calls": True,
                "provider": "openai",
                "tool_choice": "auto",
                "max_tokens": 100,
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "description": "A test tool",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    },
                ],
            },
        )

    def test_apply_to_sets_all_fields(self, completion_request: OpenAIProxyChatCompletionRequest):
        """Test that apply_to sets all fields when none are set in properties"""

        properties = TaskGroupProperties()
        completion_request.apply_to(properties)

        assert properties.temperature == 0.7
        assert properties.top_p == 0.9
        assert properties.frequency_penalty == 0.5
        assert properties.presence_penalty == 0.3
        assert properties.parallel_tool_calls is True
        assert properties.provider == "openai"
        assert properties.tool_choice == "auto"
        assert properties.max_tokens == 100
        assert properties.enabled_tools is not None
        assert len(properties.enabled_tools) == 1
        tool = properties.enabled_tools[0]
        assert isinstance(tool, Tool)
        assert tool.name == "test_tool"

    def test_apply_to_does_not_modify_set_fields(self):
        """Test that apply_to does not modify fields that are already set"""
        completion_request = OpenAIProxyChatCompletionRequest(
            messages=[OpenAIProxyMessage(role="user", content="Hello, world!")],
            model="gpt-4o",
        )

        properties = TaskGroupProperties(
            temperature=0.5,
            top_p=0.8,
            frequency_penalty=0.2,
            presence_penalty=0.1,
            parallel_tool_calls=False,
            provider="anthropic",
            tool_choice="none",
            max_tokens=200,
        )
        copied = properties.model_copy()
        completion_request.apply_to(copied)

        assert copied == properties

    def test_apply_to_sets_default_temperature(self):
        """Test that apply_to sets default temperature when not set in request or properties"""
        completion_request = OpenAIProxyChatCompletionRequest(
            messages=[OpenAIProxyMessage(role="user", content="Hello, world!")],
            model="gpt-4o",
        )
        properties = TaskGroupProperties()
        completion_request.apply_to(properties)
        assert properties.temperature == 1.0

    def test_apply_to_handles_max_completion_tokens(self):
        """Test that apply_to handles max_completion_tokens correctly"""
        request = OpenAIProxyChatCompletionRequest(
            messages=[OpenAIProxyMessage(role="user", content="Hello, world!")],
            model="gpt-4o",
            max_completion_tokens=100,
        )
        properties = TaskGroupProperties()
        request.apply_to(properties)
        assert properties.max_tokens == 100

    def test_apply_to_handles_tools(self):
        """Test that apply_to handles tools correctly"""
        request = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "test_tool",
                            "description": "A test tool",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    },
                ],
            },
        )
        properties = TaskGroupProperties()
        request.apply_to(properties)
        assert properties.enabled_tools is not None
        assert len(properties.enabled_tools) == 1
        tool = properties.enabled_tools[0]
        assert isinstance(tool, Tool)
        assert tool.name == "test_tool"

    def test_apply_to_handles_functions(self):
        """Test that apply_to handles deprecated functions correctly"""
        request = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
                "functions": [
                    {
                        "name": "test_function",
                        "description": "A test function",
                        "parameters": {"type": "object", "properties": {}},
                    },
                ],
            },
        )
        properties = TaskGroupProperties()
        request.apply_to(properties)
        assert properties.enabled_tools is not None
        assert len(properties.enabled_tools) == 1
        tool = properties.enabled_tools[0]
        assert isinstance(tool, Tool)
        assert tool.name == "test_function"
