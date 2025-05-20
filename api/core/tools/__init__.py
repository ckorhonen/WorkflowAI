import re
from enum import StrEnum

from core.domain.tool import Tool


def is_handle_in(instructions: str, handle: str) -> bool:
    """
    The reason why we use such a regex is that we want to avoid matching handles
    that are substrings of other words while still allowing punctuation and whitespace before/after
    the handle as valid boundaries.
    """
    pattern = rf"(?i)(?<![a-z0-9_\-]){re.escape(handle)}(?![a-z0-9_\-]|\.[a-z0-9])"
    return bool(re.search(pattern, instructions))


class ToolKind(StrEnum):
    WEB_SEARCH_GOOGLE = "@search-google"
    WEB_SEARCH_PERPLEXITY_SONAR = "@perplexity-sonar"
    WEB_SEARCH_PERPLEXITY_SONAR_REASONING = "@perplexity-sonar-reasoning"
    WEB_SEARCH_PERPLEXITY_SONAR_PRO = "@perplexity-sonar-pro"
    WEB_BROWSER_TEXT = "@browser-text"

    @classmethod
    def from_str(cls, handle: str) -> "ToolKind":
        try:
            return ToolKind(handle)
        except ValueError:
            try:
                return cls.alias_map()[handle]
            except KeyError:
                raise ValueError(f"'{handle}' is not a valid WorkflowAI tool")

    @classmethod
    def alias_map(cls) -> dict[str, "ToolKind"]:
        return {
            "@search": ToolKind.WEB_SEARCH_GOOGLE,
            "WEB_SEARCH_GOOGLE": ToolKind.WEB_SEARCH_GOOGLE,
            "WEB_BROWSER_TEXT": ToolKind.WEB_BROWSER_TEXT,
        }

    @property
    def aliases(self) -> set[str]:
        return {alias for alias, tool_kind in self.alias_map().items() if self == tool_kind}

    @classmethod
    def replace_tool_aliases_with_handles(cls, instructions: str) -> str:
        # Replaces outdated aliases in instructions with new ones

        for tool_kind in ToolKind:
            for alias in list(tool_kind.aliases):
                if is_handle_in(instructions, alias):
                    instructions = instructions.replace(alias, tool_kind.value)
        return instructions


_tool_handle_regex = re.compile(r"@[a-z0-9_-]+")


def get_tools_in_instructions(instructions: str) -> set[ToolKind | Tool]:
    enabled_tools: set[ToolKind | Tool] = set()
    for match in _tool_handle_regex.finditer(instructions):
        handle = match.group(0)
        try:
            enabled_tools.add(ToolKind.from_str(handle))
        except ValueError:
            pass
    return enabled_tools
