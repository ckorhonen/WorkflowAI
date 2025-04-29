import logging
from typing import Any, TypeAlias

from core.domain.fields.file import FileKind
from core.domain.fields.local_date_time import DatetimeLocal
from core.utils import strings

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

FieldConfig: TypeAlias = (
    InputGenericFieldConfig
    | OutputStringFieldConfig
    | EnumFieldConfig
    | InputArrayFieldConfig
    | InputObjectFieldConfig
    | OutputGenericFieldConfig
    | OutputArrayFieldConfig
    | OutputObjectFieldConfig
    | None
)


_logger = logging.getLogger(__name__)


def _create_base_schema(field: FieldConfig) -> dict[str, Any]:
    """Create the base schema with description if present."""
    if field is None:
        return {}
    return {"description": field.description} if field.description is not None else {}


def _handle_string_field(field: OutputStringFieldConfig) -> dict[str, Any]:
    """Handle StringFieldConfig conversion."""
    schema: dict[str, Any] = {"type": "string"}
    if field.examples is not None:
        schema["examples"] = field.examples
    return schema


def _handle_enum_field(field: EnumFieldConfig) -> dict[str, Any]:
    """Handle EnumFieldConfig conversion."""
    return {
        "type": "string",
        "enum": field.values,
    }


def _handle_array_field(
    field: InputArrayFieldConfig | OutputArrayFieldConfig,
    defs: dict[str, Any],
) -> dict[str, Any]:
    """Handle ArrayFieldConfig conversion."""
    items_schema = convert_field_to_json_schema(field.items, defs)
    return {
        "type": "array",
        "items": items_schema,
    }


def _handle_object_field(
    field: InputObjectFieldConfig | OutputObjectFieldConfig,
    defs: dict[str, Any],
) -> dict[str, Any]:
    """Handle ObjectFieldConfig conversion."""

    # Make sure all object fields have a name for the JSON schema
    # This should not happen in the first place, but we add this fallback for sanity
    for index, subfield in enumerate(field.fields):
        if subfield and subfield.name is None:
            _logger.warning(
                "Field has no name, using field_index",
                extra={"field": subfield, "index": index},
            )
            subfield.name = f"field_{index + 1}"

    properties = {subfield.name: convert_field_to_json_schema(subfield, defs) for subfield in field.fields if subfield}
    return {
        "type": "object",
        "properties": properties,
    }


def _handle_file_field(file_kind: FileKind) -> dict[str, Any]:
    """Handle File field conversion."""
    match file_kind:
        case FileKind.IMAGE:
            ref_name = "Image"
        case FileKind.AUDIO:
            ref_name = "Audio"
        case FileKind.DOCUMENT:
            ref_name = "File"
        case FileKind.PDF:
            ref_name = "PDF"

    return {"$ref": f"#/$defs/{ref_name}"}


def _handle_datetime_local_field(defs: dict[str, Any]) -> dict[str, Any]:
    """Handle DatetimeLocal field conversion."""
    defs["DatetimeLocal"] = DatetimeLocal.model_json_schema()
    return {"$ref": "#/$defs/DatetimeLocal"}


def _get_format_schema(field_type: InputSchemaFieldType | OutputSchemaFieldType) -> dict[str, Any]:
    """Get schema for fields with format specification."""
    format_mapping = {
        (InputSchemaFieldType.DATE, OutputSchemaFieldType.DATE): "date",
        (InputSchemaFieldType.DATETIME, OutputSchemaFieldType.DATETIME): "date-time",
        (InputSchemaFieldType.URL, OutputSchemaFieldType.URL): "uri",
        (InputSchemaFieldType.HTML, OutputSchemaFieldType.HTML): "html",
        (InputSchemaFieldType.EMAIL, OutputSchemaFieldType.EMAIL): "email",
        (InputSchemaFieldType.TIMEZONE, OutputSchemaFieldType.TIMEZONE): "timezone",
    }

    for types, format_value in format_mapping.items():
        if field_type in types:
            return {"type": "string", "format": format_value}

    return {"type": field_type.value}


def convert_field_to_json_schema(field: FieldConfig, defs: dict[str, Any]) -> dict[str, Any]:
    """Convert a field configuration to a JSON schema property."""
    base_schema = _create_base_schema(field)

    match field:
        case OutputStringFieldConfig():
            schema = _handle_string_field(field)
        case EnumFieldConfig():
            schema = _handle_enum_field(field)
        case InputArrayFieldConfig() | OutputArrayFieldConfig():
            schema = _handle_array_field(field, defs)
        case InputObjectFieldConfig() | OutputObjectFieldConfig():
            schema = _handle_object_field(field, defs)
        case InputGenericFieldConfig() | OutputGenericFieldConfig():
            schema = _handle_generic_field(field, defs)
        case _:  # pyright: ignore[reportUnnecessaryComparison]
            # We'd rather always have a default case, even if "unnecessary"
            raise ValueError(f"Unsupported field type: {type(field)}")

    return {**base_schema, **schema}


def _handle_generic_field(
    field: InputGenericFieldConfig | OutputGenericFieldConfig,
    defs: dict[str, Any],
) -> dict[str, Any]:
    """Handle generic field types with special formats."""
    match field.type:
        case InputSchemaFieldType.IMAGE_FILE:
            return _handle_file_field(FileKind.IMAGE)
        case OutputSchemaFieldType.IMAGE_FILE:
            return _handle_file_field(FileKind.IMAGE)
        case InputSchemaFieldType.AUDIO_FILE:
            return _handle_file_field(FileKind.AUDIO)
        case InputSchemaFieldType.DOCUMENT_FILE:
            return _handle_file_field(FileKind.DOCUMENT)
        case OutputSchemaFieldType.DATETIME_LOCAL:
            return _handle_datetime_local_field(defs)
        case _ if field.type is not None:
            return _get_format_schema(field.type)
        case _:
            return {}


def build_json_schema_with_defs(field: FieldConfig | None) -> dict[str, Any] | None:
    """Build complete JSON schema with definitions if needed."""
    if field is None:
        return None

    defs: dict[str, Any] = {}
    schema = convert_field_to_json_schema(field, defs)
    return {**schema, "$defs": defs} if defs else schema


def sanitize_agent_name(agent_name: str) -> str:
    agent_name = agent_name.removesuffix("Task")
    return strings.to_pascal_case(agent_name)
