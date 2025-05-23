import pytest

from core.tools import ToolKind, get_tools_in_instructions, is_handle_in


@pytest.mark.parametrize(
    ("handle", "expected"),
    [
        # Valid handles
        ("@search-google", ToolKind.WEB_SEARCH_GOOGLE),
        ("@perplexity-sonar", ToolKind.WEB_SEARCH_PERPLEXITY_SONAR),
        ("@browser-text", ToolKind.WEB_BROWSER_TEXT),
        # Deprecated handles
        ("WEB_SEARCH_GOOGLE", ToolKind.WEB_SEARCH_GOOGLE),
        ("WEB_BROWSER_TEXT", ToolKind.WEB_BROWSER_TEXT),
        # Aliases
        ("@search", ToolKind.WEB_SEARCH_GOOGLE),
    ],
)
def test_from_str_valid_cases(handle: str, expected: ToolKind) -> None:
    """Test that from_str correctly handles valid tool handles, including deprecated and aliased ones."""
    assert ToolKind.from_str(handle) == expected


@pytest.mark.parametrize(
    "invalid_handle",
    [
        "@invalid-tool",
    ],
)
def test_from_str_invalid_handle(invalid_handle: str) -> None:
    """Test that from_str raises ValueError for invalid tool handles."""
    with pytest.raises(ValueError):
        ToolKind.from_str(invalid_handle)


@pytest.mark.parametrize(
    ("tool_kind", "expected_aliases"),
    [
        (ToolKind.WEB_SEARCH_GOOGLE, {"@search", "WEB_SEARCH_GOOGLE"}),
        (ToolKind.WEB_BROWSER_TEXT, {"WEB_BROWSER_TEXT"}),
        (ToolKind.WEB_SEARCH_PERPLEXITY_SONAR, set[str]()),
        (ToolKind.WEB_SEARCH_PERPLEXITY_SONAR_REASONING, set[str]()),
        (ToolKind.WEB_SEARCH_PERPLEXITY_SONAR_PRO, set[str]()),
    ],
)
def test_aliases(tool_kind: ToolKind, expected_aliases: set[str]) -> None:
    """Test that tools return the correct set of aliases."""
    assert tool_kind.aliases == expected_aliases


@pytest.mark.parametrize(
    "instructions,expected",
    [
        # Test replacing @search with @search-google
        (
            "Use @search to perform the task",
            "Use @search-google to perform the task",
        ),
        # Test no replacement when no aliases are present
        (
            "Use @search-google and @browser-text to perform the task",
            "Use @search-google and @browser-text to perform the task",
        ),
        # Test multiple replacements
        (
            "First use @search and then use @search again",
            "First use @search-google and then use @search-google again",
        ),
        # Test replacements replacement at the end of the string
        (
            "First use @search",
            "First use @search-google",
        ),
    ],
)
def test_replace_tool_aliases_with_handles(instructions: str, expected: str) -> None:
    result = ToolKind.replace_tool_aliases_with_handles(instructions)  # pyright: ignore[reportPrivateUsage]
    assert result == expected


@pytest.mark.parametrize(
    ("instructions", "handle", "expected"),
    [
        # Test handle in middle
        ("Use @browser-text to get content", "@browser-text", True),
        # Test handle at end
        ("Please use @browser-text", "@browser-text", True),
        # Test case insensitive
        ("Use @BROWSER-TEXT to get content", "@browser-text", True),
        # Test handle not present
        ("Use something else", "@browser-text", False),
        # Test partial match
        ("Use @browser", "@browser-text", False),
        # Test without space
        ("Use @browser-text.now", "@browser-text", False),
        # Test with single quote
        ("Use '@browser-text' to get content", "@browser-text", True),
        ("Use ' @browser-text ' to get content", "@browser-text", True),
        # Test with double quote
        ('Use "@browser-text" to get content', "@browser-text", True),
        ('Use " @browser-text " to get content', "@browser-text", True),
        # Test with semicolon
        ("Use @browser-text; to get content", "@browser-text", True),
        ("Use @browser-text ; to get content", "@browser-text", True),
        # Test with comma
        ("Use @browser-text, to get content", "@browser-text", True),
        ("Use @browser-text , to get content", "@browser-text", True),
        # Test with colon
        ("Use @browser-text: to get content", "@browser-text", True),
        ("Use @browser-text : to get content", "@browser-text", True),
        # Test with asterisk
        ("Use **@browser-text** to get content", "@browser-text", True),
        ("Use ** @browser-text ** to get content", "@browser-text", True),
        # Test with handle that is a substring of another word
        ("Use @browser-text to get content", "@browser", False),
        ("Use @perplexity-sonar to get content", "@perplexity-sonar-pro", False),
    ],
)
def test_tool_handle_variations(instructions: str, handle: str, expected: bool) -> None:
    """Test various scenarios for tool handle detection in instructions."""
    assert is_handle_in(instructions, handle) is expected


@pytest.mark.parametrize(
    ("instructions", "expected_tools"),
    [
        # Single tool with alias
        (
            "Please use @search for research.",
            {ToolKind.WEB_SEARCH_GOOGLE},
        ),
        # Single tool with direct handle
        (
            "Please use @search-google for research.",
            {ToolKind.WEB_SEARCH_GOOGLE},
        ),
        # Multiple tools
        (
            "Please use @search and also use @browser-text for an overview.",
            {ToolKind.WEB_SEARCH_GOOGLE, ToolKind.WEB_BROWSER_TEXT},
        ),
        pytest.param(
            "Use '@search' with quotes.",
            {ToolKind.WEB_SEARCH_GOOGLE},
            id="Quotes",
        ),
        pytest.param(
            "Use @search: with colon",
            {ToolKind.WEB_SEARCH_GOOGLE},
            id="Colon",
        ),
        (
            "Use @search; with semicolon",
            {ToolKind.WEB_SEARCH_GOOGLE},
        ),
        (
            "Use @perplexity-sonar-pro to get content",
            {ToolKind.WEB_SEARCH_PERPLEXITY_SONAR_PRO},
        ),
        pytest.param(
            "Use @search-google and tell @guillaume to do something for once",
            {ToolKind.WEB_SEARCH_GOOGLE},
            id="Invalid handle",
        ),
        *[
            pytest.param(
                t.value,
                {t},
                id=t.value,
            )
            for t in ToolKind
        ],
    ],
)
def test_get_tools_in_instructions(instructions: str, expected_tools: set[ToolKind]) -> None:
    """Test various scenarios for tool detection in instructions."""
    tools = get_tools_in_instructions(instructions)
    assert tools == expected_tools
