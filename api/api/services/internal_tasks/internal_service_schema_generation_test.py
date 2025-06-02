# pyright: reportPrivateUsage=false

import logging
from typing import Any
from unittest.mock import Mock, patch

import pytest

from api.services.internal_tasks.internal_tasks_service import (
    InternalTasksService,
)


@pytest.fixture(scope="function")
def internal_tasks_service(mock_storage: Mock, mock_event_router: Mock):
    return InternalTasksService(storage=mock_storage, event_router=mock_event_router)


class TestAddExplanationToSchema:
    def test_add_explanation_object_schema_needs_explanation(self):
        # Setup
        schema = {
            "type": "object",
            "properties": {
                "is_valid": {"type": "boolean"},
            },
        }
        logger = logging.getLogger("test")
        service = InternalTasksService(Mock(), Mock())

        # Execute
        with patch("api.services.internal_tasks.internal_tasks_service.schema_needs_explanation", return_value=True):
            result = service.add_explanation_to_schema_if_needed(schema, logger)  # pyright: ignore[reportPrivateUsage]

        # Assert
        assert result["properties"]["explanation"] == {
            "type": "string",
            "description": "Explanation of the choices made in the output",
        }
        assert list(result["properties"].keys()) == ["explanation", "is_valid"]

    def test_add_explanation_not_needed(
        self,
    ):
        # Setup
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }
        logger = logging.getLogger("test")
        service = InternalTasksService(Mock(), Mock())

        # Execute
        with patch("api.services.internal_tasks.internal_tasks_service.schema_needs_explanation", return_value=False):
            result = service.add_explanation_to_schema_if_needed(schema, logger)  # pyright: ignore[reportPrivateUsage]

        # Assert
        assert "explanation" not in result["properties"]
        assert result == schema
        assert result is not schema  # Should be a copy, not the same object

    def test_add_explanation_non_object_schema(self):
        # Setup
        schema = {
            "type": "boolean",
        }
        logger = logging.getLogger("test")
        service = InternalTasksService(Mock(), Mock())

        # Execute
        with patch("api.services.internal_tasks.internal_tasks_service.schema_needs_explanation", return_value=True):
            with patch.object(logger, "warning") as mock_warning:
                result = service.add_explanation_to_schema_if_needed(schema, logger)  # pyright: ignore[reportPrivateUsage]

        # Assert
        assert result == schema
        assert result is not schema  # Should be a copy, not the same object
        mock_warning.assert_called_once()
        assert "Schema is an enum or boolean" in mock_warning.call_args[0][0]

    def test_add_explanation_no_properties(self):
        # Setup
        schema = {
            "type": "object",
        }
        logger = logging.getLogger("test")
        service = InternalTasksService(Mock(), Mock())

        # Execute
        with patch("api.services.internal_tasks.internal_tasks_service.schema_needs_explanation", return_value=True):
            with patch.object(logger, "warning") as mock_warning:
                result = service.add_explanation_to_schema_if_needed(schema, logger)  # pyright: ignore[reportPrivateUsage]

        # Assert
        assert result == schema
        assert result is not schema  # Should be a copy, not the same object
        mock_warning.assert_called_once()
        assert "Schema is an enum or boolean" in mock_warning.call_args[0][0]

    def test_add_explanation_exception_handling(self):
        # Setup
        schema = {
            "type": "object",
            "properties": {
                "is_valid": {"type": "boolean"},
            },
        }
        logger = logging.getLogger("test")
        service = InternalTasksService(Mock(), Mock())

        # Execute
        with patch(
            "api.services.internal_tasks.internal_tasks_service.schema_needs_explanation",
            side_effect=Exception("Test error"),
        ):
            with patch.object(logger, "warning") as mock_warning:
                result = service.add_explanation_to_schema_if_needed(schema, logger)  # pyright: ignore[reportPrivateUsage]
        # Assert
        assert result == schema
        assert result is not schema  # Should be a copy, not the same object
        mock_warning.assert_called_once()
        assert "Error adding explanation to schema" in mock_warning.call_args[0][0]

    @pytest.mark.parametrize(
        "input_schema,expected_properties",
        [
            # Case 2: Object with enum property needs explanation
            (
                {"type": "object", "properties": {"status": {"enum": ["ACTIVE", "INACTIVE"]}}},
                {
                    "explanation": {"type": "string", "description": "Explanation of the choices made in the output"},
                    "status": {"enum": ["ACTIVE", "INACTIVE"]},
                },
            ),
            # Case 3: Regular schema doesn't need explanation
            (
                {"type": "object", "properties": {"name": {"type": "string"}}},
                {"name": {"type": "string"}},
            ),
            # Case 4: Object with boolean property needs explanation
            (
                {"type": "object", "properties": {"is_valid": {"type": "boolean"}}},
                {
                    "explanation": {"type": "string", "description": "Explanation of the choices made in the output"},
                    "is_valid": {"type": "boolean"},
                },
            ),
        ],
    )
    def test_add_explanation_to_schema_parameterized(
        self,
        input_schema: dict[str, Any],
        expected_properties: dict[str, Any] | None,
    ):
        # Setup
        logger = logging.getLogger("test")
        service = InternalTasksService(Mock(), Mock())

        # Execute
        with patch.object(logger, "warning") as mock_warning:
            result = service.add_explanation_to_schema_if_needed(input_schema, logger)  # pyright: ignore[reportPrivateUsage]

        # Assert
        assert result is not input_schema  # Should be a copy, not the same object

        if expected_properties is None:
            # Non-object schema or object without properties
            mock_warning.assert_called_once()
            assert "Schema is an enum or boolean" in mock_warning.call_args[0][0]
        elif "properties" in result:
            assert result["properties"] == expected_properties
