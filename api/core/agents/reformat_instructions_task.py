from pydantic import BaseModel, Field
from workflowai import Model, agent


class TaskInstructionsReformatingTaskInput(BaseModel):
    inital_task_instructions: str = Field(description="The initial instructions to reformat")


class TaskInstructionsReformatingTaskOutput(BaseModel):
    reformated_task_instructions: str = Field(description="The reformated instructions")


@agent(model=Model.GPT_4O_MINI_2024_07_18.value)
async def format_instructions(
    input: TaskInstructionsReformatingTaskInput,
) -> TaskInstructionsReformatingTaskOutput:
    """Your mission is to reformat content, without altering it's meaning at all.

    # Instructions
    Leave any jinja2 template as is.
    Remove markdown if existing. Do not add markdown.
    Remove numbered list, replace by bullet list when relevant.
    Insert line breaks where needed to improve readability
    """
    ...
