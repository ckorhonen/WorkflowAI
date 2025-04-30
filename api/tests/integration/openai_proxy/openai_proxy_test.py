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

    await test_client.wait_for_completed_tasks()

    task_id, run_id = res.id.split("/")
    run = await test_client.fetch_run({"id": task_id}, run_id=run_id, v1=True)
    assert run["id"] == run_id
    assert run["task_output"] == "Hello James!"

    agent = await test_client.get(f"/_/agents/{task_id}/schemas/1")
    assert agent["output_schema"]["json_schema"] == {"type": "string"}


async def test_raw_json_mode(test_client: IntegrationTestClient, openai_client: AsyncOpenAI):
    test_client.mock_openai_call(raw_content='{"whatever": "Hello world"}')

    res = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, world!"}],
        response_format={"type": "json_object"},
    )
    assert res.choices[0].message.content == '{"whatever": "Hello world"}'

    await test_client.wait_for_completed_tasks()

    task_id, run_id = res.id.split("/")
    run = await test_client.fetch_run({"id": task_id}, run_id=run_id, v1=True)
    assert run["id"] == run_id
    assert run["task_output"] == {"whatever": "Hello world"}

    agent = await test_client.get(f"/_/agents/{task_id}/schemas/1")
    assert agent["output_schema"]["json_schema"] == {}


async def test_raw_json_mode_array(test_client: IntegrationTestClient, openai_client: AsyncOpenAI):
    test_client.mock_openai_call(raw_content='[{"whatever": "Hello world"}]')

    res = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, world!"}],
        response_format={"type": "json_object"},
    )
    assert res.choices[0].message.content == '[{"whatever": "Hello world"}]'
    await test_client.wait_for_completed_tasks()

    task_id, run_id = res.id.split("/")
    run = await test_client.fetch_run({"id": task_id}, run_id=run_id, v1=True)
    assert run["id"] == run_id
    assert run["task_output"] == [{"whatever": "Hello world"}]


async def test_with_json_schema(test_client: IntegrationTestClient, openai_client: AsyncOpenAI):
    test_client.mock_openai_call(raw_content='{"whatever": "Hello world"}')

    res = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, world!"}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "test",
                "schema": {
                    "type": "object",
                    "properties": {"whatever": {"type": "string"}},
                },
            },
        },
    )
    assert res.choices[0].message.content == '{"whatever": "Hello world"}'

    await test_client.wait_for_completed_tasks()

    task_id, run_id = res.id.split("/")
    run = await test_client.fetch_run({"id": task_id}, run_id=run_id, v1=True)
    assert run["id"] == run_id
    assert run["task_output"] == {"whatever": "Hello world"}

    agent = await test_client.get(f"/_/agents/{task_id}/schemas/1")
    assert agent["output_schema"]["json_schema"] == {"type": "object", "properties": {"whatever": {"type": "string"}}}
