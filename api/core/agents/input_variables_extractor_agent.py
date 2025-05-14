from typing import Any

import workflowai
from pydantic import BaseModel


class InputVariablesExtractorInput(BaseModel):
    agent_inputs: list[dict[str, Any]]


class InputVariablesExtractorOutput(BaseModel):
    instructions_with_input_variables: str
    input_variables_example: dict[str, Any]


INSTRUCTIONS = """
You are an expert at extracting input variables from agent instructions contained in OpenAI chat completions messages.

Your goal is to analyze several LLM runs to find what are the 'static' parts of the instructions and what are the 'dynamic' parts of the instructions that change from run to run.

Then you must propose a templated version of the instruction with placeholders to inject the variables surrounded by double curly braces in 'instructions_with_input_variables'

Also provide a JSON example of the input variables extract from one the 'agent_inputs' in 'input_variables_example'.

You must not change anything in the 'static' parts of the instructions, only add placeholders for the input variables.
"""


@workflowai.agent(
    id="input-variables-extractor-agent",
    version=workflowai.VersionProperties(
        model=workflowai.Model.GEMINI_2_0_FLASH_001,
        instructions=INSTRUCTIONS,
    ),
)
async def input_variables_extractor_agent(input: InputVariablesExtractorInput) -> InputVariablesExtractorOutput: ...
