import pytest
from openai import AsyncOpenAI

from tests.integration.common import IntegrationTestClient
from tests.integration.conftest import _TEST_JWT  # pyright: ignore [reportPrivateUsage]


@pytest.fixture()
def openai_client(test_client: IntegrationTestClient):
    yield AsyncOpenAI(http_client=test_client.int_api_client, api_key=_TEST_JWT)


async def test_raw_string_output(test_client: IntegrationTestClient, openai_client: AsyncOpenAI):
    test_client.mock_openai_call(raw_content="Hello James!")

    res = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )

    assert res.choices[0].message.content == "Hello James!"


async def test_raw_json_mode(test_client: IntegrationTestClient, openai_client: AsyncOpenAI):
    test_client.mock_openai_call(raw_content='{"whatever": "Hello world"}')

    res = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, world!"}],
        response_format={"type": "json_object"},
    )
    assert res.choices[0].message.content == '{"whatever": "Hello world"}'
