from collections.abc import AsyncIterator
from typing import Any

import workflowai
from pydantic import BaseModel, Field
from workflowai import Model

from core.domain.tool import Tool as DTool


class TaskInstructionsToolUpdateTaskInput(BaseModel):
    class Task(BaseModel):
        name: str = Field(description="The name of the task")
        input_json_schema: dict[str, Any] = Field(description="The JSON schema of the task input")
        output_json_schema: dict[str, Any] = Field(description="The JSON schema of the task output")

    task: Task = Field(description="The task to update the instructions for")

    initial_task_instructions: str = Field(
        description="The initial instructions of the task from which to add or remove tools instructions from",
    )

    tools_to_remove: list[str] = Field(
        description="The handles of the tools to remove from the 'initial_task_instructions'",
    )

    class Tool(BaseModel):
        handle: str = Field(description="The handle of the tool")
        description: str = Field(description="The description of the tool")
        input_json_schema: dict[str, Any] = Field(description="The input JSON schema of the tool")
        output_json_schema: dict[str, Any] = Field(description="The output JSON schema of the tool")

        @classmethod
        def from_domain_tool(cls, tool: DTool):
            return cls(
                handle=tool.name,
                description=tool.description or "",
                input_json_schema=tool.input_schema,
                output_json_schema=tool.output_schema or {},
            )

    tools_to_add: list[Tool] = Field(description="The tools to add to the 'initial_task_instructions'")


class TaskInstructionsToolUpdateTaskOutput(BaseModel):
    updated_task_instructions: str | None = Field(
        default=None,
        description="The updated instructions after adding or removing tools from the 'initial_task_instructions'",
    )


@workflowai.agent(id="task-instructions-tool-update", model=Model.GPT_4O_2024_11_20)
def stream_task_instruction_tool_update(
    input: TaskInstructionsToolUpdateTaskInput,
) -> AsyncIterator[TaskInstructionsToolUpdateTaskOutput]:
    """You are a task instructions manager specializing in updating tool-related content. Your task is to modify the provided initial task instructions by adding or removing tool-related instructions based on the tools specified in 'tools_to_remove' and 'tools_to_add'.

    For tools listed in 'tools_to_remove', eliminate any mentions or instructions related to those specific tool handles from the initial instructions.

    For tools listed in 'tools_to_add', incorporate appropriate instructions for using these new tools, in the context of the 'task'.

    Ensure the updated instructions maintain coherence and flow with the existing content while accurately reflecting the tool changes.

    DO NOT update any other part of the 'initial_task_instructions' that the parts related to 'tools_to_remove' or 'tools_to_add'.
    DO NOT use markdown formatting (**, *, #, etc.), unless markdown is already present in the 'initial_task_instructions'.
    DO NOT add any character around tool handles (quotes, etc.) just use @the-tool-handle"""
    ...
