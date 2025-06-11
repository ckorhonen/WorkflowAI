import pytest

from core.domain.integration.integration_domain import Integration, IntegrationKind
from core.domain.integration.integration_mapping import safe_get_integration_by_kind


@pytest.mark.parametrize(
    "used_integration_kind, expected_result",
    [
        # Test with None input
        (None, None),
        # Test with empty string
        ("", None),
        # Test with valid IntegrationKind values
        ("instructor-python", IntegrationKind.INSTRUCTOR_PYTHON),
        (IntegrationKind.INSTRUCTOR_PYTHON, IntegrationKind.INSTRUCTOR_PYTHON),
        ("openai-sdk-python", IntegrationKind.OPENAI_SDK_PYTHON),
        ("openai-sdk-ts", IntegrationKind.OPENAI_SDK_TS),
        # Test with invalid integration kind
        ("INVALID_KIND", None),
        ("random_string", None),
        ("123", None),
        # Test with whitespace
        ("  ", None),
        ("\t", None),
        ("\n", None),
        # Test with similar but incorrect values
        ("instructor_python", None),  # underscore instead of dash
        ("INSTRUCTOR-PYTHON", None),  # uppercase
        ("instructor-Python", None),  # mixed case
    ],
)
def test_safe_get_integration_by_kind(
    used_integration_kind: str | None,
    expected_result: IntegrationKind | None,
) -> None:
    """Test the _valid_integration_kind_or_none static method with various inputs."""
    result = safe_get_integration_by_kind(used_integration_kind)  # pyright: ignore[reportPrivateUsage]

    if expected_result is None:
        assert result is None
    else:
        assert isinstance(result, Integration)
        assert result.slug == expected_result.value
