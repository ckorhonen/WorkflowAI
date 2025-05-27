from typing import Any

import workflowai
from pydantic import BaseModel


class OutputSchemaExtractorInput(BaseModel):
    class AgentRun(BaseModel):
        raw_messages: list[list[dict[str, Any]]]
        input: str
        output: str

    agent_runs: list[AgentRun]
    programming_language: str
    structured_object_class: str


class OutputSchemaExtractorOutput(BaseModel):
    proposed_structured_object_class: str
    instructions_parts_to_remove: list[str]


INSTRUCTIONS = """
You are an expert at extracting output schema from agent contained in OpenAI chat completions messages.

Your goal is to analyze several LLM runs to find what is the output schema of the agent.

You must propose a class that implements 'structured_object_class' that will be used as the output schema of the agent. Please always included the required imports in the code block.

When relevant you must add description and examples to the fields of the class. By using Field(description="...", examples=["..."]) for Pydantic classes and .describe("...") for Zod classes.
Do not forget to import 'Field' from pydantic and any other imports you need.

You must also eventually remove some instructions from the original instructions that does not make sense to when using structured generations (ex: "You must return a JSON object").
"""


@workflowai.agent(
    id="output-schema-extractor-agent",
    version=workflowai.VersionProperties(
        model=workflowai.Model.GEMINI_2_0_FLASH_001,
        instructions=INSTRUCTIONS,
    ),
)
async def output_schema_extractor_agent(input: OutputSchemaExtractorInput) -> OutputSchemaExtractorOutput: ...
