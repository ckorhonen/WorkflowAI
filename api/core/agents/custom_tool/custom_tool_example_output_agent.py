from typing import Any

import workflowai
from pydantic import BaseModel, Field


class ToolOuptutExampleAgentInput(BaseModel):
    tool_name: str | None = Field(
        default=None,
        description="The name of the tool to generate an example input for",
    )
    tool_description: str | None = Field(
        default=None,
        description="The description of the tool to generate an example input for",
    )
    tool_input: dict[str, Any] | None = Field(
        default=None,
        description="The input of the tool to generate an example output for, if any",
    )


class ToolOutputExampleAgentOutput(BaseModel):
    assistant_answer: str | None = Field(
        default=None,
        description="The assistant answer to the user message",
    )
    example_tool_output_string: str | None = Field(
        default=None,
        description="The example output for the tool, if the tool output is a string",
    )
    example_tool_output_json: dict[str, Any] | None = Field(
        default=None,
        description="The example output for the tool, if the tool output is an object",
    )


INSTRUCTIONS = """You are a tool output simulation expert, specialized in generating realistic example outputs for various tools based on their descriptions and inputs.

    Given a tool name, its description, and potential input, generate a plausible example output that demonstrates the tool's functionality.

    - If the tool typically returns a string output, provide the example in 'example_tool_output_string'.
    - If the tool returns structured data, provide the example in 'example_tool_output_json'.

    The example should be representative of what the actual tool would return and maintain consistency with the tool's described purpose and input parameters.

    If 'task_input' is present, generate example output that makes sense with 'task_input'.
    If 'task_input' is absent, generate any example output that makes sense.

    Make sure not to repeat fields from the 'tool_input' in the output."""


@workflowai.agent(
    id="tool-output-example",
    version=workflowai.VersionProperties(
        model=workflowai.Model.CLAUDE_3_7_SONNET_20250219,
        max_tokens=1000,
        instructions=INSTRUCTIONS,
    ),
)
async def tool_output_example_agent(
    input: ToolOuptutExampleAgentInput,
) -> workflowai.Run[ToolOutputExampleAgentOutput]: ...
