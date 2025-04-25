from typing import Any

import pytest

from .chat_task_schema_generation_task import (
    EnumFieldConfig,
    InputArrayFieldConfig,
    InputGenericFieldConfig,
    InputObjectFieldConfig,
    InputSchemaFieldType,
    OutputArrayFieldConfig,
    OutputGenericFieldConfig,
    OutputObjectFieldConfig,
    OutputSchemaFieldType,
    OutputStringFieldConfig,
)
from .chat_task_schema_generation_task_utils import (
    build_json_schema_with_defs,
)


@pytest.mark.parametrize(
    "field, expected_schema",
    [
        pytest.param(  # Input Object field with String field with description and examples
            InputObjectFieldConfig(
                name="test_string",
                fields=[
                    InputGenericFieldConfig(
                        name="test_string",
                        type=InputSchemaFieldType.STRING,
                        description="A test string field",
                    ),
                ],
            ),
            {
                "properties": {
                    "test_string": {
                        "description": "A test string field",
                        "type": "string",
                    },
                },
                "type": "object",
            },
            id="input string field and example",
        ),
        pytest.param(  # Output Object field with String field with description and examples
            OutputObjectFieldConfig(
                name="test_string",
                fields=[
                    OutputStringFieldConfig(
                        name="test_string",
                        description="A test string field",
                        examples=["example1", "example2"],
                    ),
                ],
            ),
            {
                "properties": {
                    "test_string": {
                        "description": "A test string field",
                        "type": "string",
                        "examples": ["example1", "example2"],
                    },
                },
                "type": "object",
            },
            id="output string field and example",
        ),
        pytest.param(  # Input object field with String field without description and examples
            InputObjectFieldConfig(
                name="test_string",
                fields=[
                    InputGenericFieldConfig(
                        name="test_string",
                        type=InputSchemaFieldType.STRING,
                    ),
                ],
            ),
            {
                "properties": {
                    "test_string": {
                        "type": "string",
                    },
                },
                "type": "object",
            },
            id="input string field without description and examples",
        ),
        pytest.param(  # Output object field with String field without description and examples
            OutputObjectFieldConfig(
                name="test_string",
                fields=[
                    OutputStringFieldConfig(
                        name="test_string",
                    ),
                ],
            ),
            {
                "properties": {
                    "test_string": {
                        "type": "string",
                    },
                },
                "type": "object",
            },
            id="output string field without description and examples",
        ),
        pytest.param(  # Image file in input
            InputObjectFieldConfig(
                name="test_object",
                fields=[InputGenericFieldConfig(name="input_image", type=InputSchemaFieldType.IMAGE_FILE)],
            ),
            {
                "type": "object",
                "properties": {
                    "input_image": {
                        "$ref": "#/$defs/Image",
                    },
                },
            },
            id="image file in input",
        ),
        pytest.param(  # Datetime local in output
            OutputObjectFieldConfig(
                name="test_object",
                fields=[
                    OutputGenericFieldConfig(name="test_datetime_local", type=OutputSchemaFieldType.DATETIME_LOCAL),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_datetime_local": {
                        "$ref": "#/$defs/DatetimeLocal",
                    },
                },
                "$defs": {
                    "DatetimeLocal": {
                        "description": "This class represents a local datetime, with a datetime and a timezone.",
                        "properties": {
                            "date": {
                                "description": "The date of the local datetime.",
                                "format": "date",
                                "title": "Date",
                                "type": "string",
                            },
                            "local_time": {
                                "description": "The time of the local datetime without timezone info.",
                                "format": "time",
                                "title": "Local Time",
                                "type": "string",
                            },
                            "timezone": {
                                "description": "The timezone of the local time, in the 'Europe/Paris', 'America/New_York' format.",
                                "format": "timezone",
                                "title": "Timezone",
                                "type": "string",
                            },
                        },
                        "required": ["date", "local_time", "timezone"],
                        "title": "DatetimeLocal",
                        "type": "object",
                    },
                },
            },
            id="datetime local in output",
        ),
        pytest.param(  # Input Datetime field
            InputGenericFieldConfig(
                name="test_datetime",
                description="A test datetime field",
                type=InputSchemaFieldType.DATETIME,
            ),
            {"type": "string", "format": "date-time", "description": "A test datetime field"},
            id="input datetime field",
        ),
        pytest.param(  # Output Datetime field
            OutputGenericFieldConfig(
                name="test_datetime",
                description="A test datetime field",
                type=OutputSchemaFieldType.DATETIME,
            ),
            {"type": "string", "format": "date-time", "description": "A test datetime field"},
            id="output datetime field",
        ),
        pytest.param(  # Input Date Field
            InputGenericFieldConfig(
                name="test_date",
                description="A test date field",
                type=InputSchemaFieldType.DATE,
            ),
            {"type": "string", "format": "date", "description": "A test date field"},
            id="input date field",
        ),
        pytest.param(  # Output Date Field
            OutputGenericFieldConfig(
                name="test_date",
                description="A test date field",
                type=OutputSchemaFieldType.DATE,
            ),
            {"type": "string", "format": "date", "description": "A test date field"},
            id="output date field",
        ),
        pytest.param(  # Enum field
            EnumFieldConfig(
                name="test_enum",
                description="A test enum field",
                values=["value1", "value2"],
            ),
            {
                "description": "A test enum field",
                "type": "string",
                "enum": ["value1", "value2"],
            },
            id="enum field",
        ),
        pytest.param(  # Enum field without description
            EnumFieldConfig(
                name="test_enum",
                values=["value1", "value2"],
            ),
            {"type": "string", "enum": ["value1", "value2"]},
            id="enum field without description",
        ),
        pytest.param(  # Array field
            InputArrayFieldConfig(
                name="test_array",
                items=InputGenericFieldConfig(
                    name="item1",
                    type=InputSchemaFieldType.STRING,
                    description="An item",
                ),
            ),
            {
                "type": "array",
                "items": {
                    "description": "An item",
                    "type": "string",
                },
            },
            id="array field",
        ),
        pytest.param(  # Array field without description
            InputArrayFieldConfig(
                name="test_array",
                items=InputGenericFieldConfig(name="item1", type=InputSchemaFieldType.STRING),
            ),
            {"type": "array", "items": {"type": "string"}},
            id="array field without description",
        ),
        pytest.param(  # Output array without description
            OutputArrayFieldConfig(
                name="test_array",
                items=OutputStringFieldConfig(name="item1"),
            ),
            {"type": "array", "items": {"type": "string"}},
            id="output array without description",
        ),
        pytest.param(  # Input Datetime field wrapped
            InputObjectFieldConfig(
                name="test_datetime",
                fields=[
                    InputGenericFieldConfig(
                        name="test_datetime",
                        description="A test datetime field",
                        type=InputSchemaFieldType.DATETIME,
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_datetime": {
                        "type": "string",
                        "format": "date-time",
                        "description": "A test datetime field",
                    },
                },
            },
            id="input datetime field wrapped",
        ),
        pytest.param(  # Output Datetime field wrapped
            OutputObjectFieldConfig(
                name="test_datetime",
                fields=[
                    OutputGenericFieldConfig(
                        name="test_datetime",
                        description="A test datetime field",
                        type=OutputSchemaFieldType.DATETIME,
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_datetime": {
                        "type": "string",
                        "format": "date-time",
                        "description": "A test datetime field",
                    },
                },
            },
            id="output datetime field wrapped",
        ),
        pytest.param(  # Input Date Field wrapped
            InputObjectFieldConfig(
                name="test_date",
                fields=[
                    InputGenericFieldConfig(
                        name="test_date",
                        description="A test date field",
                        type=InputSchemaFieldType.DATE,
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_date": {
                        "type": "string",
                        "format": "date",
                        "description": "A test date field",
                    },
                },
            },
            id="input date field wrapped",
        ),
        pytest.param(  # Output Date Field wrapped
            OutputObjectFieldConfig(
                name="test_date",
                fields=[
                    OutputGenericFieldConfig(
                        name="test_date",
                        description="A test date field",
                        type=OutputSchemaFieldType.DATE,
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_date": {
                        "type": "string",
                        "format": "date",
                        "description": "A test date field",
                    },
                },
            },
            id="output date field wrapped",
        ),
        pytest.param(  # Enum field wrapped in InputObjectFieldConfig
            InputObjectFieldConfig(
                name="test_enum",
                fields=[
                    EnumFieldConfig(
                        name="test_enum",
                        description="A test enum field",
                        values=["value1", "value2"],
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_enum": {
                        "description": "A test enum field",
                        "type": "string",
                        "enum": ["value1", "value2"],
                    },
                },
            },
            id="enum field wrapped in InputObjectFieldConfig",
        ),
        pytest.param(  # Enum field without description wrapped
            InputObjectFieldConfig(
                name="test_enum",
                fields=[
                    EnumFieldConfig(
                        name="test_enum",
                        values=["value1", "value2"],
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_enum": {
                        "type": "string",
                        "enum": ["value1", "value2"],
                    },
                },
            },
            id="enum field without description wrapped",
        ),
        pytest.param(  # Input Array field wrapped
            InputObjectFieldConfig(
                name="test_array_wrapper",
                fields=[
                    InputArrayFieldConfig(
                        name="test_array",
                        items=InputGenericFieldConfig(
                            name="item1",
                            type=InputSchemaFieldType.STRING,
                            description="First item",
                        ),
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_array": {
                        "type": "array",
                        "items": {
                            "description": "First item",
                            "type": "string",
                        },
                    },
                },
            },
            id="input array field wrapped",
        ),
        pytest.param(  # Input Array field without description wrapped
            InputObjectFieldConfig(
                name="test_array_wrapper",
                fields=[
                    InputArrayFieldConfig(
                        name="test_array",
                        items=InputGenericFieldConfig(name="item1", type=InputSchemaFieldType.STRING),
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_array": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            id="input array field without description wrapped",
        ),
        pytest.param(  # Output array without description wrapped
            OutputObjectFieldConfig(
                name="test_array_wrapper",
                fields=[
                    OutputArrayFieldConfig(
                        name="test_array",
                        items=OutputStringFieldConfig(name="item1"),
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "test_array": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            id="output array without description wrapped",
        ),
        pytest.param(  # Complex nested input structure
            InputObjectFieldConfig(
                name="complex_input",
                fields=[
                    InputGenericFieldConfig(
                        name="title",
                        description="Main title",
                        type=InputSchemaFieldType.STRING,
                    ),
                    InputGenericFieldConfig(
                        name="created_at",
                        description="Creation timestamp",
                        type=InputSchemaFieldType.DATETIME,
                    ),
                    InputArrayFieldConfig(
                        name="sections",
                        items=InputObjectFieldConfig(
                            name="section",
                            fields=[
                                InputGenericFieldConfig(name="section_title", type=InputSchemaFieldType.STRING),
                                InputGenericFieldConfig(name="section_date", type=InputSchemaFieldType.DATE),
                                EnumFieldConfig(name="section_type", values=["chapter", "appendix", "reference"]),
                                InputArrayFieldConfig(
                                    name="attachments",
                                    items=InputObjectFieldConfig(
                                        name="attachment",
                                        fields=[
                                            InputGenericFieldConfig(name="filename", type=InputSchemaFieldType.STRING),
                                            InputGenericFieldConfig(name="file", type=InputSchemaFieldType.IMAGE_FILE),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Main title"},
                    "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "section_title": {"type": "string"},
                                "section_date": {"type": "string", "format": "date"},
                                "section_type": {"type": "string", "enum": ["chapter", "appendix", "reference"]},
                                "attachments": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "filename": {"type": "string"},
                                            "file": {"$ref": "#/$defs/Image"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            id="complex nested input structure",
        ),
        pytest.param(  # Complex nested output structure
            OutputObjectFieldConfig(
                name="complex_output",
                fields=[
                    OutputStringFieldConfig(name="analysis_id", description="Unique identifier for the analysis"),
                    OutputGenericFieldConfig(
                        name="processed_at",
                        description="Processing timestamp",
                        type=OutputSchemaFieldType.DATETIME,
                    ),
                    OutputArrayFieldConfig(
                        name="results",
                        items=OutputObjectFieldConfig(
                            name="result",
                            fields=[
                                OutputStringFieldConfig(name="category", description="Result category"),
                                OutputGenericFieldConfig(name="detection_date", type=OutputSchemaFieldType.DATE),
                                EnumFieldConfig(name="confidence_level", values=["high", "medium", "low"]),
                                OutputArrayFieldConfig(
                                    name="findings",
                                    items=OutputObjectFieldConfig(
                                        name="finding",
                                        fields=[
                                            OutputStringFieldConfig(
                                                name="description",
                                                description="Detailed finding description",
                                            ),
                                            OutputGenericFieldConfig(
                                                name="severity",
                                                type=OutputSchemaFieldType.NUMBER,
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            {
                "type": "object",
                "properties": {
                    "analysis_id": {"type": "string", "description": "Unique identifier for the analysis"},
                    "processed_at": {"type": "string", "format": "date-time", "description": "Processing timestamp"},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string", "description": "Result category"},
                                "detection_date": {"type": "string", "format": "date"},
                                "confidence_level": {"type": "string", "enum": ["high", "medium", "low"]},
                                "findings": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "description": {
                                                "type": "string",
                                                "description": "Detailed finding description",
                                            },
                                            "severity": {"type": "number"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            id="complex nested output structure",
        ),
        pytest.param(  # Input Object field with String field without name
            OutputObjectFieldConfig(
                name="test_string",
                fields=[
                    OutputStringFieldConfig(
                        description="A test string field",
                        examples=["example1", "example2"],
                    ),
                    OutputStringFieldConfig(
                        name="a_named_field",
                        description="A test string field",
                        examples=["example1", "example2"],
                    ),
                    OutputStringFieldConfig(
                        description="Another test string field",
                        examples=["example1", "example2"],
                    ),
                ],
            ),
            {
                "properties": {
                    "field_1": {
                        "description": "A test string field",
                        "type": "string",
                        "examples": ["example1", "example2"],
                    },
                    "a_named_field": {
                        "description": "A test string field",
                        "type": "string",
                        "examples": ["example1", "example2"],
                    },
                    "field_3": {
                        "description": "Another test string field",
                        "type": "string",
                        "examples": ["example1", "example2"],
                    },
                },
                "type": "object",
            },
            id="input object field with String field without name",
        ),
    ],
)
def test_convert_string_field_to_json_schema(field: OutputStringFieldConfig, expected_schema: dict[str, Any]) -> None:
    """Test converting StringFieldConfig to JSON schema."""
    schema = build_json_schema_with_defs(field)

    assert schema == expected_schema


def test_convert_field_to_json_schema_unsupported_type() -> None:
    """Test that converting an unsupported field type raises ValueError."""

    class UnsupportedField:
        description = None

    with pytest.raises(ValueError, match="Unsupported field type"):
        build_json_schema_with_defs(UnsupportedField())  # type: ignore
