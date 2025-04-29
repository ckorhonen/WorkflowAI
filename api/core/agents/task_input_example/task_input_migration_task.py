from typing import Any, AsyncIterator

from pydantic import BaseModel, Field
from workflowai import Model, agent


class TaskInputMigrationTaskInput(BaseModel):
    current_datetime: str | None = Field(default=None, description="The current datetime in ISO format")
    task_name: str | None = Field(default=None, description="The name of the task that the input belongs to")
    base_input: dict[str, Any] | None = Field(
        default=None,
        description="The input to migrate to the new 'input_json_schema'",
    )
    input_json_schema: dict[str, Any] | None = Field(
        default=None,
        description="The JSON schema to migrate the 'base_input' to",
    )
    output_json_schema: dict[str, Any] | None = Field(
        default=None,
        description="The JSON schema for the output of the task",
    )


class TaskInputMigrationTaskOutput(BaseModel):
    migrated_task_input: dict[str, Any] | None = Field(
        default=None,
        description="The migrated task input, based on the 'base_input' and enforcing the 'input_json_schema'",
    )


@agent(id="task-input-migration", model=Model.GEMINI_2_0_FLASH_LATEST.value)
async def run_task_input_migration_task(
    input: TaskInputMigrationTaskInput,
) -> TaskInputMigrationTaskOutput:
    """You are a data migration specialist focused on transforming and validating input data structures. Your task is to migrate the provided 'base_input' to conform to the target 'input_json_schema' while ensuring all data is properly mapped and validated.

    You MUST generate a 'task_input' that reuses what can be reused in the 'base_input' and fills in the missing fields, deleting the fields that are not present in the 'input_json_schema' and handle field renaming by using the value of the renamed field in the 'task_input' if necessary.

    Example:

    Suppose the 'base_input' is:

    ```json
    {
      "first_name": "Alice",
      "last_name": "Smith",
      "age": 28,
      "city": "Paris"
    }
    ```

    And the 'input_json_schema' requires fields 'full_name' and 'email', you should:

    - Combine 'first_name' and 'last_name' from the 'base_input' to create 'full_name' in the 'task_input'.
    - Fill in the missing 'email' field with a placeholder like "alice.smith@domain.com".
    - Remove 'age' since it's not required by the 'input_json_schema'.
    - Use the value of 'city' from the 'base_input' as 'residence' in the 'task_input', since it looks like 'city' has been renamed to 'residence' in the 'input_json_schema'.

    Resulting 'task_input':

    ```json
    {
      "full_name": "Alice Smith",
      "email": "alice.smith@domain.com",
      "residence": "Paris"
    }
    ```

    If the 'base_input' already aligns with the 'input_json_schema', you must leave the 'base_input' untouched, unless the 'base_input' does not make sense at all anymore with the 'output_json_schema'.

    In case the 'base_input' contains files with URLs, generate a 'task_input' that reuses the file's fields ('url', 'storage_url' and 'content_type')."""
    ...


@agent(id="task-input-migration", model=Model.GEMINI_2_0_FLASH_LATEST.value)
def stream_task_input_migration_task(
    input: TaskInputMigrationTaskInput,
) -> AsyncIterator[TaskInputMigrationTaskOutput]:
    """You are a data migration specialist focused on transforming and validating input data structures. Your task is to migrate the provided 'base_input' to conform to the target 'input_json_schema' while ensuring all data is properly mapped and validated.

    You MUST generate a 'task_input' that reuses what can be reused in the 'base_input' and fills in the missing fields, deleting the fields that are not present in the 'input_json_schema' and handle field renaming by using the value of the renamed field in the 'task_input' if necessary.

    Example:

    Suppose the 'base_input' is:

    ```json
    {
      "first_name": "Alice",
      "last_name": "Smith",
      "age": 28,
      "city": "Paris"
    }
    ```

    And the 'input_json_schema' requires fields 'full_name' and 'email', you should:

    - Combine 'first_name' and 'last_name' from the 'base_input' to create 'full_name' in the 'task_input'.
    - Fill in the missing 'email' field with a placeholder like "alice.smith@domain.com".
    - Remove 'age' since it's not required by the 'input_json_schema'.
    - Use the value of 'city' from the 'base_input' as 'residence' in the 'task_input', since it looks like 'city' has been renamed to 'residence' in the 'input_json_schema'.

    Resulting 'task_input':

    ```json
    {
      "full_name": "Alice Smith",
      "email": "alice.smith@domain.com",
      "residence": "Paris"
    }
    ```

    If the 'base_input' already aligns with the 'input_json_schema', you must leave the 'base_input' untouched, unless the 'base_input' does not make sense at all anymore with the 'output_json_schema'.

    In case the 'base_input' contains files with URLs, generate a 'task_input' that reuses the file's fields ('url', 'storage_url' and 'content_type')."""
    ...
