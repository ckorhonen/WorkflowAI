from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from api.schemas.build_task_request import BuildAgentIteration, BuildAgentRequest
from core.agents.chat_task_schema_generation.chat_task_schema_generation_task import AgentSchemaJson
from core.domain.events import TaskChatStartedEvent
from core.domain.fields.chat_message import UserChatMessage
from core.domain.fields.file import File
from core.domain.task_group import TaskGroup
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_io import SerializableTaskIO
from core.domain.task_variant import SerializableTaskVariant
from core.domain.version_reference import VersionReference
from core.runners.workflowai import workflowai_options
from core.tools import ToolKind

from .tasks import (
    BaseTaskCreateRequest,
    CreateTaskRequest,
    CreateTaskSchemaRequest,
    _send_task_chat_started_event,  # pyright: ignore [reportPrivateUsage]
    create_task_schema,
)

# Should NOT raise a validation error
CORRECT_FACEBOOK_EMOTION_INPUT_SCHEMA = {
    "properties": {
        "facebook_post": {
            "description": "The content of the Facebook post to be classified.",
            "title": "Facebook Post",
            "type": "string",
        },
    },
    "required": ["facebook_post"],
    "title": "FacebookPostEmotionClassificationTaskInput",
    "type": "object",
}

# Should NOT raise a validation error
CORRECT_FACEBOOK_EMOTION_OUTPUT_SCHEMA = {
    "$defs": {"Category": {"enum": ["SAD", "HAPPY", "ANGRY", "FUNNY"], "title": "Category", "type": "string"}},
    "properties": {
        "categories": {
            "description": "List of categories that the Facebook post is classified into.",
            "items": {"$ref": "#/$defs/Category"},
            "title": "Categories",
            "type": "array",
        },
    },
    "required": ["categories"],
    "title": "FacebookPostEmotionClassificationTaskOutput",
    "type": "object",
}

# Should NOT raise a validation error
CORRECT_SORT_CITIES_SCHEMA = {
    "properties": {
        "cities": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "A city name",
                "examples": ["New York", "Los Angeles", "Chicago"],
            },
            "description": "An array of city names to be sorted",
            "minItems": 1,
        },
    },
    "required": ["cities"],
    "description": "Schema for inputting an array of cities to be sorted alphabetically",
}

# Should raise a validation error
INCORRECT_SIMPLE_SCHEMA = {"properties": "hello"}

# Should raise a validation error
INCORRECT_STRING_AT_ROOT_SCHEMA = {
    "type": "string",
    "description": "A string containing the meal plan",
}


# Should raise a validation error
INCORRECT_ARRAY_AT_ROOT_SCHEMA = {
    "type": "array",
    "description": "An array of recipes",
    "items": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": "Type of meal (e.g., breakfast, snack, lunch)",
                "examples": ["breakfast", "snack", "lunch"],
            },
            "description": {
                "type": "string",
                "description": "Description of the meal",
                "examples": ["A healthy breakfast to start your day", "A light snack to keep you going"],
            },
            "ingredients": {
                "type": "array",
                "description": "List of ingredients in the meal",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the ingredient",
                            "examples": ["chicken breast", "broccoli"],
                        },
                        "calories": {
                            "type": "integer",
                            "description": "Calories in the ingredient",
                            "examples": [200, 50],
                        },
                    },
                    "required": ["name", "calories"],
                },
            },
        },
        "required": ["type", "description", "ingredients"],
    },
}


class TestCreateTaskRequestWithChatMessages:
    def _request(self, **kwargs: Any) -> CreateTaskRequest:
        base = CreateTaskRequest(
            chat_messages=[UserChatMessage(content="Create a task to classify the emotion of a Facebook post.")],
            name="FacebookPostEmotionClassification",
            input_schema=CORRECT_FACEBOOK_EMOTION_INPUT_SCHEMA,
            output_schema=CORRECT_FACEBOOK_EMOTION_OUTPUT_SCHEMA,
        )

        return CreateTaskRequest.model_validate({**base.model_dump(), **kwargs})

    def test_build(self) -> None:
        task_id = "task_id"
        request = self._request()

        result = request.build(task_id)

        assert result.task_id == task_id
        assert result.name == "FacebookPostEmotionClassification"
        assert result.input_schema.version == "91a3db23b9c76a67b0c8441bc6c0935a"
        assert result.output_schema.version == "c789a89a238be2a090430ee65fd25699"
        assert result.id == "898c2d0ac32a221c14a054f8314dd4ed"

    def test_validate(self) -> None:
        validated = CreateTaskRequest.model_validate(
            {
                "chat_messages": [
                    {
                        "role": "USER",
                        "content": "Create a that sorts cities by attractivity.",
                    },
                ],
                "name": "SortCities",
                "input_schema": CORRECT_SORT_CITIES_SCHEMA,
                "output_schema": CORRECT_SORT_CITIES_SCHEMA,
            },
        )
        assert validated

    @pytest.mark.parametrize(
        "schema",
        [INCORRECT_SIMPLE_SCHEMA, INCORRECT_ARRAY_AT_ROOT_SCHEMA, INCORRECT_STRING_AT_ROOT_SCHEMA],
    )
    def test_check_invalid_json_schema(self, schema: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            self._request(input_schema=schema)
        with pytest.raises(ValidationError):
            self._request(output_schema=schema)


class TestCreateTaskRequest:
    def _request(self, **kwargs: Any) -> CreateTaskRequest:
        base = CreateTaskRequest(
            name="FacebookPostEmotionClassification",
            input_schema=CORRECT_FACEBOOK_EMOTION_INPUT_SCHEMA,
            output_schema=CORRECT_FACEBOOK_EMOTION_OUTPUT_SCHEMA,
        )

        return CreateTaskRequest.model_validate({**base.model_dump(), **kwargs})

    def test_build(self) -> None:
        task_id = "task_id"
        request = self._request()

        result = request.build(task_id)

        assert result.task_id == task_id
        assert result.name == "FacebookPostEmotionClassification"
        assert result.input_schema.version == "91a3db23b9c76a67b0c8441bc6c0935a"
        assert result.output_schema.version == "c789a89a238be2a090430ee65fd25699"
        assert result.id == "898c2d0ac32a221c14a054f8314dd4ed"

    def test_validate(self) -> None:
        validated = CreateTaskRequest.model_validate(
            {
                "name": "SortCities",
                "input_schema": CORRECT_SORT_CITIES_SCHEMA,
                "output_schema": CORRECT_SORT_CITIES_SCHEMA,
            },
        )
        assert validated

    def test_adds_missing_refs_backwards_compatibility(self):
        req = CreateTaskRequest(
            name="FacebookPostEmotionClassification",
            input_schema={
                "properties": {
                    "image": {
                        "$ref": "#/$defs/Image",
                    },
                },
                "title": "FacebookPostEmotionClassificationInput",
                "type": "object",
            },
            output_schema=CORRECT_FACEBOOK_EMOTION_OUTPUT_SCHEMA,
        )
        result = req.build("task_id")
        assert result.input_schema.json_schema == {
            "$defs": {
                "Image": File.model_json_schema(),
            },
            "properties": {
                "image": {
                    "$ref": "#/$defs/Image",
                },
            },
            "title": "FacebookPostEmotionClassificationInput",
            "type": "object",
        }

    def test_adds_missing_refs_backwards(self):
        req = CreateTaskRequest(
            name="FacebookPostEmotionClassification",
            input_schema={
                "properties": {
                    "image": {
                        "$ref": "#/$defs/File",
                        "format": "image",
                    },
                },
                "title": "FacebookPostEmotionClassificationInput",
                "type": "object",
            },
            output_schema=CORRECT_FACEBOOK_EMOTION_OUTPUT_SCHEMA,
        )
        result = req.build("task_id")
        assert result.input_schema.json_schema == {
            "$defs": {
                "File": File.model_json_schema(),
            },
            "properties": {
                "image": {
                    "$ref": "#/$defs/File",
                    "format": "image",
                },
            },
            "title": "FacebookPostEmotionClassificationInput",
            "type": "object",
        }

    @pytest.mark.parametrize(
        "schema",
        [INCORRECT_SIMPLE_SCHEMA, INCORRECT_ARRAY_AT_ROOT_SCHEMA, INCORRECT_STRING_AT_ROOT_SCHEMA],
    )
    def test_check_invalid_json_schema(self, schema: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            self._request(input_schema=schema)
        with pytest.raises(ValidationError):
            self._request(output_schema=schema)


async def test_create_task_schema_happy_path():
    # Mock dependencies
    storage_mock = AsyncMock()
    internal_tasks_mock = AsyncMock()
    group_service_mock = AsyncMock()
    event_router_mock = MagicMock()
    analytics_service_mock = MagicMock()
    user_org_mock = MagicMock()

    # Set up request data
    task_id = "test_task_id"
    request = CreateTaskSchemaRequest(
        name="Test Task",
        input_schema={"type": "object", "properties": {"input_name": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"output_name": {"type": "string"}}},
        skip_generation=False,
        create_first_iteration=True,
        chat_messages=[UserChatMessage(content="test")],
    )

    # Mock storage.store_task_resource
    new_task = SerializableTaskVariant(
        id="new_task_id",
        task_id=task_id,
        task_schema_id=2,
        name="Test Task",
        input_schema=SerializableTaskIO(version="test_input_version", json_schema=request.input_schema),
        output_schema=SerializableTaskIO(version="test_output_version", json_schema=request.output_schema),
        created_at=datetime.now(timezone.utc),
    )
    storage_mock.store_task_resource.return_value = (new_task, None)

    # Mock internal_tasks.update_task_instructions
    internal_tasks_mock.update_task_instructions.return_value = "Updated instructions"

    # Mock storage.get_latest_group_iteration
    storage_mock.task_groups.get_latest_group_iteration.return_value = TaskGroup(
        properties=TaskGroupProperties(instructions="Previous instructions"),
    )

    # Mock storage.task_variants.get_latest_task_variant
    storage_mock.task_variants.get_latest_task_variant.return_value = SerializableTaskVariant(
        id="previous_task_id",
        task_id=task_id,
        task_schema_id=1,
        name="Previous Test Task",
        input_schema=SerializableTaskIO(
            version="prev_input_version",
            json_schema={"type": "object", "properties": {"input_name": {"type": "string"}}},
        ),
        output_schema=SerializableTaskIO(
            version="prev_output_version",
            json_schema={"type": "object", "properties": {"output_name": {"type": "string"}}},
        ),
    )

    internal_tasks_mock.get_required_tool_kinds.return_value = {ToolKind.WEB_SEARCH_GOOGLE}

    result = await create_task_schema(
        task_id,
        request,
        storage_mock,
        internal_tasks_mock,
        group_service_mock,
        event_router_mock,
        analytics_service_mock,
        user_org_mock,
    )

    # Assertions
    assert result == new_task
    storage_mock.store_task_resource.assert_called_once()
    internal_tasks_mock.update_task_instructions.assert_called_once_with(
        chat_messages=[UserChatMessage(content="test")],
        initial_task_schema=AgentSchemaJson(
            agent_name="Previous Test Task",
            input_json_schema={"type": "object", "properties": {"input_name": {"type": "string"}}},
            output_json_schema={"type": "object", "properties": {"output_name": {"type": "string"}}},
        ),
        initial_task_instructions="Previous instructions",
        new_task_schema=AgentSchemaJson(
            agent_name="Test Task",
            input_json_schema={"type": "object", "properties": {"input_name": {"type": "string"}}},
            output_json_schema={"type": "object", "properties": {"output_name": {"type": "string"}}},
        ),
        required_tool_kinds={ToolKind.WEB_SEARCH_GOOGLE},
    )
    internal_tasks_mock.generate_agent_instructions.assert_not_called()
    group_service_mock.get_or_create_group.assert_called_once_with(
        task_id=task_id,
        task_schema_id=new_task.task_schema_id,
        reference=VersionReference(
            properties=TaskGroupProperties(
                model=workflowai_options.GLOBAL_DEFAULT_MODEL,
                instructions="Updated instructions",
            ),
        ),
    )
    event_router_mock.assert_called_once()


async def test_create_task_schema_first_schema():
    # Mock dependencies
    storage_mock = AsyncMock()
    internal_tasks_mock = AsyncMock()
    group_service_mock = AsyncMock()
    event_router_mock = MagicMock()
    analytics_service_mock = MagicMock()
    user_org_mock = MagicMock()

    # Set up request data
    task_id = "test_task_id"
    request = CreateTaskSchemaRequest(
        name="Test Task",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {}},
        skip_generation=False,
        create_first_iteration=True,
    )

    # Mock storage.store_task_resource
    new_task = SerializableTaskVariant(
        id="new_task_id",
        task_id=task_id,
        task_schema_id=1,  # First schema
        name="Test Task",
        input_schema=SerializableTaskIO(version="test_input_version", json_schema=request.input_schema),
        output_schema=SerializableTaskIO(version="test_output_version", json_schema=request.output_schema),
        created_at=datetime.now(timezone.utc),
    )
    storage_mock.store_task_resource.return_value = (new_task, None)

    # Mock storage.task_variants.get_latest_task_variant
    storage_mock.task_variants.get_latest_task_variant.return_value = None

    # Mock internal_tasks.generate_agent_instructions
    internal_tasks_mock.generate_agent_instructions.return_value = "Generated instructions"

    internal_tasks_mock.get_required_tool_kinds.return_value = {ToolKind.WEB_SEARCH_GOOGLE}

    result = await create_task_schema(
        task_id,
        request,
        storage_mock,
        internal_tasks_mock,
        group_service_mock,
        event_router_mock,
        analytics_service_mock,
        user_org_mock,
    )

    # Assertions
    assert result == new_task
    internal_tasks_mock.generate_agent_instructions.assert_called_once_with(
        task_id=task_id,
        task_schema_id=1,
        chat_messages=[],
        task=AgentSchemaJson(
            agent_name="Test Task",
            input_json_schema={"type": "object", "properties": {}},
            output_json_schema={"type": "object", "properties": {}},
        ),
        required_tool_kinds={ToolKind.WEB_SEARCH_GOOGLE},
    )
    internal_tasks_mock.update_task_instructions.assert_not_called()
    group_service_mock.get_or_create_group.assert_called_once_with(
        task_id=task_id,
        task_schema_id=1,
        reference=VersionReference(
            properties=TaskGroupProperties(
                model=workflowai_options.GLOBAL_DEFAULT_MODEL,
                instructions="Generated instructions",
            ),
        ),
    )
    event_router_mock.assert_called_once()


@pytest.mark.parametrize(
    "previous_group",
    [
        None,
        TaskGroup(properties=TaskGroupProperties()),
        TaskGroup(properties=TaskGroupProperties(instructions="")),
        TaskGroup(properties=TaskGroupProperties(instructions=None)),
    ],
)
async def test_create_task_schema_no_previous_task(previous_group: TaskGroup | None):
    # Mock dependencies
    storage_mock = AsyncMock()
    internal_tasks_mock = AsyncMock()
    group_service_mock = AsyncMock()
    event_router_mock = MagicMock()
    analytics_service_mock = MagicMock()
    user_org_mock = MagicMock()

    # Set up request data
    task_id = "test_task_id"
    request = CreateTaskSchemaRequest(
        name="Test Task",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {}},
        skip_generation=False,
        create_first_iteration=True,
    )

    # Mock storage.store_task_resource
    new_task = SerializableTaskVariant(
        id="new_task_id",
        task_id=task_id,
        task_schema_id=2,  # Not the first schema
        name="Test Task",
        input_schema=SerializableTaskIO(version="test_input_version", json_schema=request.input_schema),
        output_schema=SerializableTaskIO(version="test_output_version", json_schema=request.output_schema),
        created_at=datetime.now(timezone.utc),
    )
    storage_mock.store_task_resource.return_value = (new_task, None)

    # Mock storage.get_latest_group_iteration to return None
    storage_mock.task_groups.get_latest_group_iteration.return_value = previous_group

    # Mock internal_tasks.generate_agent_instructions
    internal_tasks_mock.generate_agent_instructions.return_value = "Generated instructions"

    internal_tasks_mock.get_required_tool_kinds.return_value = {ToolKind.WEB_SEARCH_GOOGLE}

    result = await create_task_schema(
        task_id,
        request,
        storage_mock,
        internal_tasks_mock,
        group_service_mock,
        event_router_mock,
        analytics_service_mock,
        user_org_mock,
    )

    # Assertions
    assert result == new_task
    internal_tasks_mock.generate_agent_instructions.assert_called_once_with(
        task_id=task_id,
        task_schema_id=2,
        chat_messages=[],
        task=AgentSchemaJson(
            agent_name="Test Task",
            input_json_schema={"type": "object", "properties": {}},
            output_json_schema={"type": "object", "properties": {}},
        ),
        required_tool_kinds={ToolKind.WEB_SEARCH_GOOGLE},
    )
    internal_tasks_mock.update_task_instructions.assert_not_called()
    group_service_mock.get_or_create_group.assert_called_once_with(
        task_id=task_id,
        task_schema_id=2,
        reference=VersionReference(
            properties=TaskGroupProperties(
                model=workflowai_options.GLOBAL_DEFAULT_MODEL,
                instructions="Generated instructions",
            ),
        ),
    )
    event_router_mock.assert_called_once()


@pytest.mark.parametrize(
    "previous_group",
    [
        None,
        TaskGroup(properties=TaskGroupProperties()),
        TaskGroup(properties=TaskGroupProperties(instructions="")),
        TaskGroup(properties=TaskGroupProperties(instructions=None)),
    ],
)
async def test_create_task_schema_no_previous_instructions(previous_group: TaskGroup | None):
    # Mock dependencies
    storage_mock = AsyncMock()
    internal_tasks_mock = AsyncMock()
    group_service_mock = AsyncMock()
    event_router_mock = MagicMock()
    analytics_service_mock = MagicMock()
    user_org_mock = MagicMock()

    # Set up request data
    task_id = "test_task_id"
    request = CreateTaskSchemaRequest(
        name="Test Task",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {}},
        skip_generation=False,
        create_first_iteration=True,
    )

    # Mock storage.store_task_resource
    new_task = SerializableTaskVariant(
        id="new_task_id",
        task_id=task_id,
        task_schema_id=2,  # Not the first schema
        name="Test Task",
        input_schema=SerializableTaskIO(version="test_input_version", json_schema=request.input_schema),
        output_schema=SerializableTaskIO(version="test_output_version", json_schema=request.output_schema),
        created_at=datetime.now(timezone.utc),
    )
    storage_mock.store_task_resource.return_value = (new_task, None)

    # Mock storage.get_latest_group_iteration to return None
    storage_mock.task_groups.get_latest_group_iteration.return_value = previous_group

    # Mock internal_tasks.generate_agent_instructions
    internal_tasks_mock.generate_agent_instructions.return_value = "Generated instructions"

    internal_tasks_mock.get_required_tool_kinds.return_value = {ToolKind.WEB_SEARCH_GOOGLE}

    result = await create_task_schema(
        task_id,
        request,
        storage_mock,
        internal_tasks_mock,
        group_service_mock,
        event_router_mock,
        analytics_service_mock,
        user_org_mock,
    )

    # Assertions
    assert result == new_task
    internal_tasks_mock.generate_agent_instructions.assert_called_once_with(
        task_id=task_id,
        task_schema_id=2,
        chat_messages=[],
        task=AgentSchemaJson(
            agent_name="Test Task",
            input_json_schema={"type": "object", "properties": {}},
            output_json_schema={"type": "object", "properties": {}},
        ),
        required_tool_kinds={ToolKind.WEB_SEARCH_GOOGLE},
    )
    internal_tasks_mock.update_task_instructions.assert_not_called()
    group_service_mock.get_or_create_group.assert_called_once_with(
        task_id=task_id,
        task_schema_id=2,
        reference=VersionReference(
            properties=TaskGroupProperties(
                model=workflowai_options.GLOBAL_DEFAULT_MODEL,
                instructions="Generated instructions",
            ),
        ),
    )
    event_router_mock.assert_called_once()


async def test_create_task_schema_skip_generation():
    # Mock dependencies
    storage_mock = AsyncMock()
    internal_tasks_mock = AsyncMock()
    group_service_mock = AsyncMock()
    event_router_mock = MagicMock()
    analytics_service_mock = MagicMock()
    user_org_mock = MagicMock()

    # Set up request data
    task_id = "test_task_id"
    request = CreateTaskSchemaRequest(
        name="Test Task",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {}},
        skip_generation=True,
    )

    # Mock storage.store_task_resource
    new_task = SerializableTaskVariant(
        id="new_task_id",
        task_id=task_id,
        task_schema_id=1,  # First schema
        name="Test Task",
        input_schema=SerializableTaskIO(version="test_input_version", json_schema=request.input_schema),
        output_schema=SerializableTaskIO(version="test_output_version", json_schema=request.output_schema),
        created_at=datetime.now(timezone.utc),
    )
    storage_mock.store_task_resource.return_value = (new_task, None)

    # Call the function
    result = await create_task_schema(
        task_id,
        request,
        storage_mock,
        internal_tasks_mock,
        group_service_mock,
        event_router_mock,
        analytics_service_mock,
        user_org_mock,
    )

    # Assertions
    assert result == new_task
    internal_tasks_mock.generate_agent_instructions.assert_not_called()
    internal_tasks_mock.update_task_instructions.assert_not_called()
    group_service_mock.get_or_create_group.assert_not_called()
    event_router_mock.assert_called_once()


async def test_send_task_chat_started_event_first_message():
    event_router_mock = MagicMock()
    request = BuildAgentRequest(user_message="Create a task", previous_iterations=None)

    _send_task_chat_started_event(request, event_router_mock)

    event_router_mock.assert_called_once_with(
        TaskChatStartedEvent(
            user_message="Create a task",
        ),
    )


async def test_send_task_chat_started_event_first_message_schema_update():
    event_router_mock = MagicMock()
    request = BuildAgentRequest(
        user_message="Update the task",
        previous_iterations=[
            BuildAgentIteration(
                user_message="",
                assistant_answer="",
                task_schema=BuildAgentIteration.AgentSchema(
                    task_name="Existing Task",
                    input_json_schema={},
                    output_json_schema={},
                ),
            ),
        ],
    )

    _send_task_chat_started_event(request, event_router_mock)

    event_router_mock.assert_called_once_with(
        TaskChatStartedEvent(
            existing_task_name="Existing Task",
            user_message="Update the task",
        ),
    )


async def test_send_task_chat_started_event_subsequent_message():
    event_router_mock = MagicMock()
    request = BuildAgentRequest(
        user_message="Refine the task",
        previous_iterations=[
            BuildAgentIteration(
                user_message="Create a task",
                assistant_answer="Okay, let's create a task.",
                task_schema=None,
            ),
            BuildAgentIteration(
                user_message="Add more details",
                assistant_answer="Sure, I'll add more details.",
                task_schema=None,
            ),
        ],
    )

    _send_task_chat_started_event(request, event_router_mock)

    event_router_mock.assert_not_called()


class TestBaseTaskCreateRequestValidation:
    @pytest.mark.parametrize(
        "request_class",
        [CreateTaskRequest, CreateTaskSchemaRequest],
    )
    @pytest.mark.parametrize(
        "schema",
        [INCORRECT_SIMPLE_SCHEMA, INCORRECT_ARRAY_AT_ROOT_SCHEMA, INCORRECT_STRING_AT_ROOT_SCHEMA],
    )
    def test_check_invalid_json_schema(
        self,
        request_class: type[BaseTaskCreateRequest],
        schema: dict[str, Any],
    ) -> None:
        """Test that both CreateTaskRequest and CreateTaskSchemaRequest validate their schemas correctly"""
        with pytest.raises(ValidationError):
            request_class.model_validate(
                {
                    "name": "Test Task",
                    "input_schema": schema,
                    "output_schema": CORRECT_FACEBOOK_EMOTION_OUTPUT_SCHEMA,
                },
            )
        with pytest.raises(ValidationError):
            request_class.model_validate(
                {
                    "name": "Test Task",
                    "input_schema": CORRECT_FACEBOOK_EMOTION_INPUT_SCHEMA,
                    "output_schema": schema,
                },
            )

    @pytest.mark.parametrize(
        "request_class",
        [CreateTaskRequest, CreateTaskSchemaRequest],
    )
    def test_valid_schemas_pass_validation(self, request_class: type[BaseTaskCreateRequest]) -> None:
        """Test that both request classes accept valid schemas"""
        validated = request_class.model_validate(
            {
                "name": "Test Task",
                "input_schema": CORRECT_FACEBOOK_EMOTION_INPUT_SCHEMA,
                "output_schema": CORRECT_FACEBOOK_EMOTION_OUTPUT_SCHEMA,
            },
        )
        assert validated.input_schema == CORRECT_FACEBOOK_EMOTION_INPUT_SCHEMA
        assert validated.output_schema == CORRECT_FACEBOOK_EMOTION_OUTPUT_SCHEMA
