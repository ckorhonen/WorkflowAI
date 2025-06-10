import json
import logging
import os
from typing import Any, AsyncIterator, Literal, NamedTuple

import workflowai
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from core.domain.message import Message

_logger = logging.getLogger(__name__)


class ImproveVersionMessagesInput(NamedTuple):
    initial_messages: list[dict[str, Any]]

    class Run(BaseModel):
        input: str
        output: str

    run: Run | None
    improvement_instructions: str | None


class ImproveVersionMessagesOutput(BaseModel):
    class Message(BaseModel):
        role: Literal["system", "user", "assistant"]
        content: str

    improved_messages: list[Message]
    changelog: list[str] | None = None


class ImproveVersionMessagesResponse(BaseModel):
    improved_messages: list[Message]
    feedback_token: str | None
    changelog: list[str] | None = None


async def improve_version_messages_agent(
    input: ImproveVersionMessagesInput,
) -> AsyncIterator[ImproveVersionMessagesResponse]:
    client = AsyncOpenAI(
        api_key=os.environ["WORKFLOWAI_API_KEY"],
        base_url=f"{os.environ['WORKFLOWAI_API_URL']}/v1",
    )
    feedback_token: str | None = None

    async with client.beta.chat.completions.stream(
        model=f"improve-version-messages/{workflowai.Model.GEMINI_2_0_FLASH_001.value}",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at improving AI agent input messages. Given initial messages and improvement instructions, return improved messages.\n\nthe improvement instructions are: {{improvement_instructions}}. You must output a concise changelog of the changes you made to the message in the 'changelog' field. Note that changelog should be a list of strings, with each element being an atomic change.",
            },
            {
                "role": "user",
                "content": """The messages to improve are: {{initial_messages}}
                {% if run %}Use this run as additional context on how to improve the messages: {{run}}{% endif %}
                """,
            },
        ],
        response_format=ImproveVersionMessagesOutput,
        extra_body={
            "input": {
                "initial_messages": input.initial_messages,
                "run": input.run.model_dump(mode="json") if input.run else "",
                "improvement_instructions": input.improvement_instructions,
            },
        },
        temperature=0.0,
    ) as response:
        chunk = None
        agg = ""
        yielded_response: ImproveVersionMessagesResponse | None = None
        async for chunk in response:
            feedback_token: str | None = getattr(chunk, "feedback_token", None)
            if hasattr(chunk, "type") and chunk.type == "content.delta" and hasattr(chunk, "delta"):
                if chunk.parsed and isinstance(chunk.parsed, dict):
                    try:
                        parsed_output = ImproveVersionMessagesOutput.model_validate(chunk.parsed)  # pyright: ignore[reportUnknownMemberType]
                        yielded_response = ImproveVersionMessagesResponse(
                            improved_messages=[
                                Message.with_text(message.content, message.role)
                                for message in parsed_output.improved_messages
                            ],
                            feedback_token=feedback_token,
                            changelog=parsed_output.changelog,
                        )
                        yield yielded_response
                    except ValidationError:
                        continue

                # It seems the runs from cache do not have a 'parsed' attribute filled,  so we need to parse the delta manually
                if chunk.delta:
                    try:
                        agg += chunk.delta
                        parsed_output = ImproveVersionMessagesOutput.model_validate(json.loads(agg))
                        yielded_response = ImproveVersionMessagesResponse(
                            improved_messages=[
                                Message.with_text(message.content, message.role)
                                for message in parsed_output.improved_messages
                            ],
                            feedback_token=feedback_token,
                            changelog=parsed_output.changelog,
                        )
                        yield yielded_response
                    except (json.JSONDecodeError, ValidationError):
                        continue

        if yielded_response is None:
            _logger.exception(
                "No response yielded from improve_version_messages_agent",
                extra={"input": input._asdict(), "last_chunk": chunk.model_dump(mode="json") if chunk else ""},
            )
