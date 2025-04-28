import logging
from enum import StrEnum
from typing import NamedTuple


# TODO: use jinja2 templates instead of complext template picking
class TemplateName(StrEnum):
    # Legacy templates (keys can't be changed, since we store those values in the database in old groups)
    V1 = "v1"
    NO_OUTPUT_SCHEMA = "no_output_schema"
    WITH_TOOL_USE = "with_tool_use"
    WITH_TOOL_USE_AND_NO_OUTPUT_SCHEMA = "with_tool_use_and_no_output_schema"

    # New templates
    V2_DEFAULT = "v2_default"
    V2_STRUCTURED_GENERATION = "v2_structured_generation"
    V2_TOOL_USE = "v2_tool_use"
    V2_NATIVE_TOOL_USE = "v2_,_tool_use"
    V2_STRUCTURED_GENERATION_AND_TOOL_USE = "v2_structured_generation_and_tool_use"
    V2_STRUCTURED_GENERATION_AND_NATIVE_TOOL_USE = "v2_structured_generation_and_native_tool_use"
    V2_DEFAULT_NO_INPUT_SCHEMA = "v2_default_no_input_schema"
    V2_STRUCTURED_GENERATION_NO_INPUT_SCHEMA = "v2_structured_generation_no_input_schema"
    V2_TOOL_USE_NO_INPUT_SCHEMA = "v2_tool_use_no_input_schema"
    V2_NATIVE_TOOL_USE_NO_INPUT_SCHEMA = "v2_native_tool_use_no_input_schema"
    V2_STRUCTURED_GENERATION_AND_TOOL_USE_NO_INPUT_SCHEMA = "v2_structured_generation_and_tool_use_no_input_schema"
    V2_STRUCTURED_GENERATION_AND_NATIVE_TOOL_USE_NO_INPUT_SCHEMA = (
        "v2_structured_generation_and_native_tool_use_no_input_schema"
    )
    V2_NO_INPUT_OR_OUTPUT_SCHEMA = "v2_no_input_or_output_schema"


DEPRECATED_TEMPLATES = {
    TemplateName.V1,
    TemplateName.NO_OUTPUT_SCHEMA,
    TemplateName.WITH_TOOL_USE,
    TemplateName.WITH_TOOL_USE_AND_NO_OUTPUT_SCHEMA,
    TemplateName.V2_TOOL_USE,
    TemplateName.V2_STRUCTURED_GENERATION_AND_TOOL_USE,
    TemplateName.V2_STRUCTURED_GENERATION_AND_TOOL_USE_NO_INPUT_SCHEMA,
    TemplateName.V2_TOOL_USE_NO_INPUT_SCHEMA,
}


_v2_user_message = """Input is:
```json
{{input_data}}
```{{examples}}"""


_default_system = """<instructions>
{{instructions}}
</instructions>

Input will be provided in the user message using a JSON following the schema:
```json
{{input_schema}}
```

Return a single JSON object enforcing the following schema:
```json
{{output_schema}}
```"""

_default_no_input_schema_system = """<instructions>
{{instructions}}
</instructions>

Return a single JSON object enforcing the following schema:
```json
{{output_schema}}
```"""

_structured_generation_system = """<instructions>
{{instructions}}
</instructions>

Input will be provided in the user message using a JSON following the schema:
```json
{{input_schema}}
```"""

_structured_generation_no_input_schema_system = """<instructions>
{{instructions}}
</instructions>"""

_native_tool_use_system = """<instructions>
{{instructions}}
</instructions>

Input will be provided in the user message using a JSON following the schema:
```json
{{input_schema}}
```

Return either tool call(s) or a single JSON object enforcing the following schema:
```json
{{output_schema}}
```"""


_native_tool_use_no_input_schema_system = """<instructions>
{{instructions}}
</instructions>

Before actually computing the output, you can use any of the available tools to help you.

Return either tool call(s) or a single JSON object enforcing the following schema:
```json
{{output_schema}}
```"""

_with_structured_generation_and_native_tool_use_system = """<instructions>
{{instructions}}
</instructions>

Input will be provided in the user message using a JSON following the schema:
```json
{{input_schema}}
```

Before actually computing the output, you can use any of the available tools to help you.
"""


_with_structured_generation_and_native_tool_use_no_input_schema_system = """<instructions>
{{instructions}}
</instructions>

Before actually computing the output, you can use the any of the available tools to help you."""

_no_input_or_output_schema_system = """{{instructions}}"""
_no_input_or_output_schema_user = """Input is:
```json
{{input_data}}
```{{examples}}"""


class TemplateConfig(NamedTuple):
    system_template: str
    user_template: str


# TODO: If template count and complexity continues to grow, we should consider using a different approach
# Like composing templates from content blocks or using a template engine.
TEMPLATES = {
    # New templates after system message simplification
    TemplateName.V2_DEFAULT: TemplateConfig(_default_system, _v2_user_message),
    TemplateName.V2_STRUCTURED_GENERATION: TemplateConfig(_structured_generation_system, _v2_user_message),
    TemplateName.V2_NATIVE_TOOL_USE: TemplateConfig(_native_tool_use_system, _v2_user_message),
    TemplateName.V2_STRUCTURED_GENERATION_AND_NATIVE_TOOL_USE: TemplateConfig(
        _with_structured_generation_and_native_tool_use_system,
        _v2_user_message,
    ),
    TemplateName.V2_DEFAULT_NO_INPUT_SCHEMA: TemplateConfig(_default_no_input_schema_system, _v2_user_message),
    TemplateName.V2_STRUCTURED_GENERATION_NO_INPUT_SCHEMA: TemplateConfig(
        _structured_generation_no_input_schema_system,
        _v2_user_message,
    ),
    TemplateName.V2_NATIVE_TOOL_USE_NO_INPUT_SCHEMA: TemplateConfig(
        _native_tool_use_no_input_schema_system,
        _v2_user_message,
    ),
    TemplateName.V2_STRUCTURED_GENERATION_AND_NATIVE_TOOL_USE_NO_INPUT_SCHEMA: TemplateConfig(
        _with_structured_generation_and_native_tool_use_no_input_schema_system,
        _v2_user_message,
    ),
    TemplateName.V2_NO_INPUT_OR_OUTPUT_SCHEMA: TemplateConfig(
        _no_input_or_output_schema_system,
        _no_input_or_output_schema_user,
    ),
}


def get_template_content(template_name: TemplateName) -> TemplateConfig:
    try:
        return TEMPLATES[template_name]
    except KeyError:
        _logger.warning(
            "Template not found, using default",
            extra={"template_name": template_name},
        )
        return TEMPLATES[TemplateName.V2_DEFAULT]


def get_template_without_input_schema(template_name: TemplateName) -> TemplateConfig:
    match template_name:
        case TemplateName.V2_DEFAULT:
            return TEMPLATES[TemplateName.V2_DEFAULT_NO_INPUT_SCHEMA]
        case TemplateName.V2_STRUCTURED_GENERATION:
            return TEMPLATES[TemplateName.V2_STRUCTURED_GENERATION_NO_INPUT_SCHEMA]
        case TemplateName.V2_TOOL_USE:
            return TEMPLATES[TemplateName.V2_TOOL_USE_NO_INPUT_SCHEMA]
        case TemplateName.V2_STRUCTURED_GENERATION_AND_TOOL_USE:
            return TEMPLATES[TemplateName.V2_STRUCTURED_GENERATION_AND_TOOL_USE_NO_INPUT_SCHEMA]
        case _:
            return get_template_content(template_name)


_logger = logging.getLogger(__name__)


def _pick_default_template_name(  # noqa: C901
    is_tool_use_enabled: bool,
    is_structured_generation_enabled: bool,
    supports_input_schema: bool,
) -> TemplateName:
    # TODO: avoid combinatorial explosion, use templatings system like Jinja2

    match (
        is_tool_use_enabled,
        is_structured_generation_enabled,
        supports_input_schema,
    ):
        case (True, True, False):
            return TemplateName.V2_STRUCTURED_GENERATION_AND_NATIVE_TOOL_USE_NO_INPUT_SCHEMA
        case (True, False, False):
            return TemplateName.V2_NATIVE_TOOL_USE_NO_INPUT_SCHEMA
        case (False, True, False):
            return TemplateName.V2_STRUCTURED_GENERATION_NO_INPUT_SCHEMA
        case (False, False, False):
            return TemplateName.V2_DEFAULT_NO_INPUT_SCHEMA
        case (True, True, True):
            return TemplateName.V2_STRUCTURED_GENERATION_AND_NATIVE_TOOL_USE
        case (True, False, True):
            return TemplateName.V2_NATIVE_TOOL_USE
        case (False, True, True):
            return TemplateName.V2_STRUCTURED_GENERATION
        case _:
            return TemplateName.V2_DEFAULT


def sanitize_template_name(
    template_name: str | None,
    is_tool_use_enabled: bool,
    is_structured_generation_enabled: bool,
    supports_input_schema: bool,
) -> TemplateName:
    # We override the template name the template name is deprecated
    # Because we might have some bad templates in the database
    # Since the frontend was always sending 'v1'
    # And 'v1' will not work with tools, for example.

    if template_name and template_name not in DEPRECATED_TEMPLATES:
        try:
            return TemplateName(template_name)
        except ValueError:
            _logger.warning(
                "Template not found, using default",
                extra={"template_name": template_name},
            )
            pass

    # If no template name is provided, we use the default logic
    return _pick_default_template_name(
        is_tool_use_enabled=is_tool_use_enabled,
        is_structured_generation_enabled=is_structured_generation_enabled,
        supports_input_schema=supports_input_schema,
    )
