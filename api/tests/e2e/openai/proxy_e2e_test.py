import json
import os
from typing import Any

import openai
from dotenv import load_dotenv
from openai.types.chat.chat_completion import ChatCompletion

load_dotenv(override=True)

openai.api_key = os.environ["WORKFLOWAI_API_KEY"]
openai.base_url = f"{os.environ['WORKFLOWAI_API_URL']}/v1/"


def _print(res: Any):
    print(res)  # noqa: T201


def _print_completion(completion: ChatCompletion):
    _print(completion.id)
    _print(completion.choices[0].message.content)


def test_string_completion():
    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )
    _print_completion(res)


def test_json_mode():
    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Return a JSON object with a greeting field"}],
        response_format={"type": "json_object"},
    )
    _print_completion(res)
    assert res.choices[0].message.content
    json_res = json.loads(res.choices[0].message.content)
    _print(json_res["greeting"])


def test_json_mode_with_schema():
    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Return a JSON object with a greeting field"}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "greeting_12345",
                "schema": {
                    "type": "object",
                    "properties": {"greeting": {"type": "string"}},
                },
            },
        },
    )
    _print_completion(res)
    assert res.choices[0].message.content
    json_res = json.loads(res.choices[0].message.content)
    _print(json_res["greeting"])


def test_with_image():
    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the image in a sassy manner"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://media.npr.org/assets/img/2023/01/14/this-is-fine_custom-b7c50c845a78f5d7716475a92016d52655ba3115.jpg",
                        },
                    },
                ],
            },
        ],
    )
    _print_completion(res)
