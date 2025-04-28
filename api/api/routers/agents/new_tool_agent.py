from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.services.internal_tasks.custom_tool_creation_service import CustomToolService
from core.domain.fields.custom_tool_creation_chat_message import CustomToolCreationChatMessage
from core.utils.streams import format_model_for_sse

router = APIRouter(prefix="/internal/agents/new-tool", tags=["agents"])


class ToolCreationRequest(BaseModel):
    messages: list[CustomToolCreationChatMessage] = Field(
        description="The list of previous messages in the conversation, the last message is the most recent one",
    )


class ToolCreationResponse(BaseModel):
    assistant_message: CustomToolCreationChatMessage = Field(
        description="The agent answer to the user",
    )


@router.post(
    "/messages",
    description="Allows to chat with an agent to create a new tool",
    responses={
        200: {
            "content": {
                "text/event-stream": {
                    "schema": ToolCreationResponse.model_json_schema(),
                },
            },
        },
    },
)
async def stream_custom_tool_agent_answer(
    request: ToolCreationRequest,
) -> StreamingResponse:
    async def _stream():
        async for chunk in CustomToolService.stream_creation_agent(
            messages=request.messages,
        ):
            yield format_model_for_sse(chunk)

    return StreamingResponse(_stream(), media_type="text/event-stream")


class ToolInputExampleRequest(BaseModel):
    class Tool(BaseModel):
        name: str = Field(
            description="The name of the tool to generate an example input for",
        )
        description: str = Field(
            description="The description of the tool to generate an example input for",
        )
        parameters: dict[str, Any] = Field(
            description="The parameters of the tool in JSON Schema format",
        )

    tool: Tool = Field(
        description="The tool to generate an example input for",
    )


class ToolInputExampleResponse(BaseModel):
    input: dict[str, Any] = Field(
        description="The example input for the tool, enforcing the 'tool_schema'",
    )


@router.post(
    "/input",
    description="Allows to generate an example input for a tool",
)
async def stream_tool_input_example(
    request: ToolInputExampleRequest,
) -> StreamingResponse:
    async def _stream():
        async for chunk in CustomToolService.stream_example_input(
            tool_name=request.tool.name,
            tool_description=request.tool.description,
            tool_schema=request.tool.parameters,
        ):
            yield format_model_for_sse(ToolInputExampleResponse(input=chunk))

    return StreamingResponse(_stream(), media_type="text/event-stream")


class ToolOutputExampleRequest(BaseModel):
    class Tool(BaseModel):
        name: str = Field(
            description="The name of the tool to generate an example output for",
        )
        description: str = Field(
            description="The description of the tool to generate an example output for",
        )

    tool: Tool = Field(
        description="The tool to generate an example output for",
    )

    tool_input: dict[str, Any] | None = Field(
        default=None,
        description="The input of the tool to generate an example output for, if any",
    )

    previous_run_id: str | None = Field(
        default=None,
        description="The id of the previous run to use in case of a follow-up request",
    )

    new_user_message: str | None = Field(
        default=None,
        description="The new user message to use in case of a follow-up request",
    )


class ToolOutputExampleResponse(BaseModel):
    assistant_answer: str | None = Field(
        default=None,
        description="The assistant answer to the user message",
    )
    output_string: str | None = Field(
        default=None,
        description="The example output for the tool, if the tool output is a string",
    )
    output_json: dict[str, Any] | None = Field(
        default=None,
        description="The example output for the tool, if the tool output is an object",
    )
    run_id: str | None = Field(
        default=None,
        description="The id of the run",
    )


@router.post(
    "/output",
    description="Allows to generate an example output for a tool",
)
async def stream_tool_output_example(
    request: ToolOutputExampleRequest,
) -> StreamingResponse:
    async def _stream():
        async for chunk in CustomToolService.stream_example_output(
            tool_name=request.tool.name,
            tool_description=request.tool.description,
            tool_input=request.tool_input,
            previous_run_id=request.previous_run_id,
            new_user_message=request.new_user_message,
        ):
            yield format_model_for_sse(
                ToolOutputExampleResponse(
                    assistant_answer=chunk.assistant_answer,
                    output_string=chunk.example_tool_output_string,
                    output_json=chunk.example_tool_output_json,
                    run_id=chunk.run_id,
                ),
            )

    return StreamingResponse(_stream(), media_type="text/event-stream")
