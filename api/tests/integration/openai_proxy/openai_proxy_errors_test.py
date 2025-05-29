import pytest
from openai import AsyncOpenAI, BadRequestError

from tests.integration.common import IntegrationTestClient
from tests.integration.openai_proxy.common import save_version_from_completion


async def test_deployment_with_no_input_variables(
    test_client: IntegrationTestClient,
    openai_client: AsyncOpenAI,
):
    """Check the error when a user triggers a deployment with no input variables but
    passes input variables"""

    test_client.mock_openai_call(raw_content="Hello James!")

    res = await openai_client.chat.completions.create(
        model="my-agent/gpt-4o",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )
    assert res.choices[0].message.content == "Hello James!"
    await test_client.wait_for_completed_tasks()

    # Created version will have no input variables
    version = await save_version_from_completion(test_client, res, "production")
    assert "messages" not in version["properties"]

    # Re-running with the same messages should work
    test_client.mock_openai_call(raw_content="Hello John!")
    res = await openai_client.chat.completions.create(
        model="my-agent/#1/production",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )
    assert res.choices[0].message.content == "Hello John!"

    # If we try and re-run with input variables we should get a bad request
    with pytest.raises(BadRequestError) as e:
        res = await openai_client.chat.completions.create(
            model="my-agent/#1/production",
            messages=[{"role": "user", "content": "Hello, world!"}],
            extra_body={"input": {"name": "John"}},
        )
    assert "You send input variables but the deployment you are trying to use does not expect any" in str(e.value)


async def test_unfulfilled_tool_call_request(
    openai_client: AsyncOpenAI,
):
    """Check that we raise an error when there's an unfulfilled tool request followed by text"""

    with pytest.raises(BadRequestError) as e:
        await openai_client.chat.completions.create(
            model="my-agent/gpt-4o",
            messages=[
                {"role": "user", "content": "What is the weather in Tokyo and in Paris?"},
                {
                    "role": "assistant",
                    "content": "Let me get the weather in tokyo and Paris",
                    "tool_calls": [
                        {
                            "id": "tool_use_01NhMGWVdTLvEuDB6Rx76hYJ",
                            "type": "function",
                            "function": {"name": "get_weather", "arguments": "Tokyo"},
                        },
                        {
                            "id": "tool_use_01NhMGWVdTLvEuDB6Rx76hYF",
                            "type": "function",
                            "function": {"name": "get_weather", "arguments": "Paris"},
                        },
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "tool_use_01NhMGWVdTLvEuDB6Rx76hYJ",
                    "content": "Weather in Tokyo is sunny",
                },
            ],
        )
    assert "still pending" in str(e.value)
