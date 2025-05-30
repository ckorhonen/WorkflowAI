import inspect
import json
import logging
from enum import Enum
from typing import Any, Callable, Iterable, get_type_hints

from core.domain.tool import Tool
from core.tools import ToolKind
from core.tools.browser_text.browser_text_tool import browser_text
from core.tools.search.run_google_search import run_google_search
from core.tools.search.run_perplexity_search import (
    run_perplexity_search_default,
    run_perplexity_search_sonar_pro,
    run_perplexity_search_sonar_reasoning,
)

logger = logging.getLogger(__name__)


# TODO: we should restrict the type here to args and return values that are serializable
type ToolFunction = Callable[..., Any]


def build_tool(name: str, func: ToolFunction) -> Tool:
    """Creates JSON schemas for function input parameters and return type.

    Args:
        func (Callable[[Any], Any]): a Python callable with annotated types

    Returns:
        FunctionJsonSchema: a FunctionJsonSchema object containing the function input/output JSON schemas
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func, include_extras=True)

    input_schema = _build_input_schema(sig, type_hints)
    output_schema = _build_output_schema(type_hints)

    tool_description = inspect.getdoc(func)

    return Tool(
        name=name,
        description=tool_description or "",
        input_schema=input_schema,
        output_schema=output_schema,
    )


def _get_type_schema(param_type: type) -> dict[str, Any]:
    """Convert a Python type to its corresponding JSON schema type.

    Args:
        param_type: The Python type to convert

    Returns:
        A dictionary containing the JSON schema type definition
    """

    # TODO manage more types (objects, list, etc.)
    match param_type:
        case type() if issubclass(param_type, Enum):
            return {"type": "string", "enum": [e.value for e in param_type]}
        case type() if param_type is str:
            return {"type": "string"}
        case type() if param_type in (int, float):
            return {"type": "number"}
        case type() if param_type is bool:
            return {"type": "boolean"}
        case _:
            raise ValueError(f"Unsupported type: {param_type}")


def _build_input_schema(sig: inspect.Signature, type_hints: dict[str, Any]) -> dict[str, Any]:
    input_schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        param_type_hint = type_hints[param_name]
        param_type = param_type_hint.__origin__ if hasattr(param_type_hint, "__origin__") else param_type_hint
        param_description = param_type_hint.__metadata__[0] if hasattr(param_type_hint, "__metadata__") else None

        param_schema = _get_type_schema(param_type) if isinstance(param_type, type) else {"type": "string"}
        if param_description is not None:
            param_schema["description"] = param_description

        if param.default is inspect.Parameter.empty:
            input_schema["required"].append(param_name)

        input_schema["properties"][param_name] = param_schema

    return input_schema


def _build_output_schema(type_hints: dict[str, Any]) -> dict[str, Any]:
    return_type = type_hints.get("return")
    if return_type is None:
        return {"type": "string"}  # default

    return_type_base = return_type.__origin__ if hasattr(return_type, "__origin__") else return_type

    if isinstance(return_type_base, type):
        return _get_type_schema(return_type_base)

    return {"type": "string"}  # default


def get_tool_for_tool_kind(tool_kind: ToolKind) -> ToolFunction:
    # Use match case instead of dict mapping to leverage Pylance's "reportMatchNotExhaustive"

    match tool_kind:
        case ToolKind.WEB_BROWSER_TEXT:
            return browser_text
        case ToolKind.WEB_SEARCH_PERPLEXITY_SONAR:
            return run_perplexity_search_default
        case ToolKind.WEB_SEARCH_PERPLEXITY_SONAR_REASONING:
            return run_perplexity_search_sonar_reasoning
        case ToolKind.WEB_SEARCH_PERPLEXITY_SONAR_PRO:
            return run_perplexity_search_sonar_pro
        case ToolKind.WEB_SEARCH_GOOGLE:
            return run_google_search


def _tool_prompt(tool: Tool):
    desc_line = f"        <tool_description>{tool.description}</tool_description>\n" if tool.description else ""
    return f"""    <tool>
        <tool_name>{tool.name}</tool_name>
{desc_line}        <tool_input_schema>
        ```json
        {json.dumps(tool.input_schema)}
        ```
        </tool_input_schema>
        <tool_output_schema>
        ```json
        {json.dumps(tool.output_schema)}
        ```
        </tool_output_schema>
    </tool>"""


def get_tools_description(tools: Iterable[Tool]) -> str:
    """Build a string containing the tools list in XML format.

    Args:
        tools: The tools to describe
        use_handle: Whether to use the tool handle (ex: "@browser-text") instead of the tool name

    Returns:
        A string containing the tools list in XML format
    """
    return "\n".join(
        (
            "<tools_list>",
            *(_tool_prompt(tool) for tool in tools),
            "</tools_list>",
        ),
    )


def get_tool_description_openai_format(tool: Tool) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


def get_tools_description_openai_format(tools: Iterable[Tool]) -> list[dict[str, Any]]:
    return [get_tool_description_openai_format(tool) for tool in tools]


def get_tools_description_openai_format_str(tools: Iterable[Tool]) -> str:
    return json.dumps(get_tools_description_openai_format(tools), indent=2)
