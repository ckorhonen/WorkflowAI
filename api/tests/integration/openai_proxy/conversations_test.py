from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from tests.integration.common import IntegrationTestClient
from tests.integration.openai_proxy.common import fetch_run_from_completion


async def test_raw_string_messages(test_client: IntegrationTestClient, openai_client: AsyncOpenAI):
    # Creating 3 text only completions in quick succession
    test_client.mock_openai_call(raw_content="Hello James!")
    messages: list[ChatCompletionMessageParam] = [{"role": "user", "content": "Hello, world!"}]
    res1 = await openai_client.chat.completions.create(model="gpt-4o", messages=messages)

    test_client.mock_openai_call(raw_content="Hello John!")
    messages.append(res1.choices[0].message.model_dump(exclude_none=True))  # type: ignore
    messages.append({"role": "user", "content": "1"})
    res2 = await openai_client.chat.completions.create(model="gpt-4o", messages=messages)

    test_client.mock_openai_call(raw_content="Hello Eliot!")
    messages.append(res2.choices[0].message.model_dump(exclude_none=True))  # type: ignore
    messages.append({"role": "user", "content": "2"})
    res3 = await openai_client.chat.completions.create(model="gpt-4o", messages=messages)

    await test_client.wait_for_completed_tasks()

    # Now fetching the runs
    run1 = await fetch_run_from_completion(test_client, res1)
    run2 = await fetch_run_from_completion(test_client, res2)
    run3 = await fetch_run_from_completion(test_client, res3)

    assert run1["conversation_id"] == run2["conversation_id"] == run3["conversation_id"]

    assert run2["task_input"] == {
        "messages": [
            {"role": "user", "content": [{"text": "Hello, world!"}]},
            {"role": "assistant", "content": [{"text": "Hello James!"}], "run_id": run1["id"]},
            {"role": "user", "content": [{"text": "1"}]},
        ],
    }

    assert run3["task_input"] == {
        "messages": [
            {"role": "user", "content": [{"text": "Hello, world!"}]},
            {"role": "assistant", "content": [{"text": "Hello James!"}], "run_id": run1["id"]},
            {"role": "user", "content": [{"text": "1"}]},
            {"role": "assistant", "content": [{"text": "Hello John!"}], "run_id": run2["id"]},
            {"role": "user", "content": [{"text": "2"}]},
        ],
    }
