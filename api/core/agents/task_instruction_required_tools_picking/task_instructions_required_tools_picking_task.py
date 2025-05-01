from typing import Any, Self

import workflowai
from pydantic import BaseModel, Field
from workflowai import Model, Run

from core.domain.fields.chat_message import ChatMessage
from core.domain.tool import Tool


class TaskInstructionsRequiredToolsPickingTaskInput(BaseModel):
    chat_messages: list[ChatMessage] = Field(description="The chat messages that originated the creation of the task")

    class Task(BaseModel):
        name: str = Field(description="The name of the task")
        input_json_schema: dict[str, Any] = Field(description="The JSON schema of the task input")
        output_json_schema: dict[str, Any] = Field(description="The JSON schema of the task output")

    task: Task = Field(description="The task to generate the instructions for")

    class ToolDescriptionStr(BaseModel):
        handle: str = Field(description="The handle of the tool")
        description: str = Field(description="The description of the tool")
        input_json_schema: dict[str, Any] = Field(description="The input JSON schema of the tool")
        output_json_schema: dict[str, Any] = Field(description="The output JSON schema of the tool")

        @classmethod
        def from_tool_description(cls, tool_description: Tool) -> Self:
            return cls(
                handle=tool_description.name,
                description=tool_description.description or "",
                input_json_schema=tool_description.input_schema,
                output_json_schema=tool_description.output_schema or {},
            )

    available_tools_description: list[ToolDescriptionStr] = Field(
        description="The description of the available tools, potentially available for the task we are generating the schema for",
    )


class TaskInstructionsRequiredToolsPickingTaskOutput(BaseModel):
    required_tools: list[str] = Field(
        default_factory=list,
        description="The handles of the tools that are required to complete the task",
    )


@workflowai.agent(id="task-instructions-required-tools-picking", model=Model.O3_MINI_2025_01_31_MEDIUM_REASONING_EFFORT)
async def run_task_instructions_required_tools_picking(
    task_input: TaskInstructionsRequiredToolsPickingTaskInput,
) -> Run[TaskInstructionsRequiredToolsPickingTaskOutput]:
    """You are a tool selection specialist tasked with analyzing task requirements to identify the necessary tools.

    Examine the input data, which includes chat messages, task details, and available tools.

    Based on this information, determine which tools from the 'available_tools_description' set are absolutely required to complete the task.

    The tools can be included in the 'required_tools' for very specific use cases.
    ONLY add tools in the 'required_tools' if the output can not be generated at all without using the tool.

    ONLY add perplexity-sonar-pro for:
    - open-ended web browsing (market research, etc.) where we do not know the URL to browse in advance
    - when in need for very "fresh" data (ex: real-time weather, stock price, news, etc.)
    DO NOT add perplexity-sonar-pro for travel destination searchs and similar, nor search about artists. Those are considered as 'internal knownledge' of models.

    ONLY add browser-text when:
    - there is a specific need to fetch an URL that present in the 'input_json_schema'
    - when there is a need to browse an URL that would have been found by the perplexity-sonar-pro tool

    DO NOT use tools for general knowledge like travel destinations, etc.

    If the "ASSISTANT" has proposed to use a tool in the "chat_messages" and if the "USER" either not answered or answered negativelly, do not add the proposed tool in "required_tools"

    Keep in mind that the user can always add tools later, so when in doubt or if the conditions above are not fully met, do not add tools in the 'required_tools'.

    WARNING: you can only include handles from the 'available_tools_description' in the 'required_tools'"""
    ...
