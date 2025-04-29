from typing import Any, AsyncIterator

import workflowai
from pydantic import BaseModel, Field
from workflowai import Model, agent

from core.domain.url_content import URLContent
from core.utils.hash import compute_obj_hash

TASK_INPUT_EXAMPLE_TASK_ID = "task-input-example"


class TaskInputExampleTaskInput(BaseModel):
    current_datetime: str | None = Field(default=None, description="The current datetime in ISO format")
    task_name: str | None = Field(default=None, description="The name of the task that the input belongs to")
    input_json_schema: dict[str, Any] | None = Field(
        default=None,
        description="The JSON schema for the input of the task",
    )
    output_json_schema: dict[str, Any] | None = Field(
        default=None,
        description="The JSON schema for the output of the task",
    )
    additional_instructions: str | None = Field(
        default=None,
        description="Any additional instructions from the user for generating the example input",
    )
    additional_instructions_url_contents: list[URLContent] | None = Field(
        default=None,
        description="A list of URL contents from the 'additional_instructions', if the 'additional_instructions' contains URLs",
    )
    previous_task_inputs: list[dict[str, Any]] | None = Field(
        default=None,
        description="A list of previous task inputs that the generated input should be different from",
    )

    def memory_id(self) -> str:
        """A label identifiying the input by ignoring the previous task inputs and number of examples."""
        return compute_obj_hash(
            self.model_dump(exclude={"previous_task_inputs", "current_datetime", "base_input"}, exclude_none=True),
        )


class TaskInputExampleTaskOutput(BaseModel):
    task_input: dict[str, Any] | None = Field(
        default=None,
        description="Generated input for the task. The input must conform to the 'input_json_schema' of the task input",
    )


INSTRUCTIONS = """The goal here is to a generate realistic, lengthy and articulate 'task_input' (enforcing 'input_json_schema') for a task whose goal is to produce valid outputs (enforcing 'output_json_schema').
    Step 1: Analyze the 'output_json_schema' and 'input_json_schema'. Analyze what is the goal of the task in order to generate a meaningful input.
    Step 2: Generate a 'task_input' for a task based on the task's 'input_json_schema'.
    Do not repeat the 'examples' included in the schema, but rather use those as an inspiration for what a correct value looks like. Consider the 'previous_task_inputs' to avoid generating the same inputs.

    Also, generate inputs that:
    - Don't be lazy and generate output with realistic length. Recomended lenght: for email 5-20 lines, for transcripts 10-20 back and forths, for songs 3-6 verse + chorus, etc. Use your best judgement to find a length that suits the use case, but DO NOT BE LAZY, generate data that look real.
    - Have datetime values that are close to the current datetime, unless otherwise specified.
    - Look realistic, e.g., a call transcript must include a back and forth between two persons, etc.
    - Will be able to yield various outputs and explore the space of possible outputs. E.g., for classification tasks, generate inputs that can be classified into multiple categories as well as positive and negative examples.
    - Are nicely formatted, in order to ease reading."""


@agent(
    id=TASK_INPUT_EXAMPLE_TASK_ID,
    version=workflowai.VersionProperties(
        instructions=INSTRUCTIONS,
        model=Model.GEMINI_2_0_FLASH_LATEST,  # For speed
        temperature=0.7,  # For more diverse outputs
    ),
)
async def run_task_input_example_task(
    input: TaskInputExampleTaskInput,
) -> TaskInputExampleTaskOutput: ...


@agent(
    id=TASK_INPUT_EXAMPLE_TASK_ID,
    version=workflowai.VersionProperties(
        instructions=INSTRUCTIONS,
        model=Model.GEMINI_2_0_FLASH_LATEST,  # For speed
        temperature=0.7,  # For more diverse outputs
    ),
)
def stream_task_input_example_task(
    input: TaskInputExampleTaskInput,
) -> AsyncIterator[TaskInputExampleTaskOutput]: ...
