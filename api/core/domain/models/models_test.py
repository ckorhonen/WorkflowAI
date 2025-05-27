import pytest

from core.domain.models.models import Model


@pytest.mark.parametrize(
    "value, reasoning, expected",
    [
        pytest.param("gpt-4o-mini-latest", None, Model.GPT_4O_MINI_LATEST, id="exists"),
        pytest.param("gpt-4o", None, Model.GPT_4O_LATEST, id="unversioned"),
        pytest.param(
            "o3-mini-2025-01-31",
            "high",
            Model.O3_MINI_2025_01_31_HIGH_REASONING_EFFORT,
            id="reasoning effort versioned",
        ),
        pytest.param(
            "o3-mini-2025-01-31",
            "high",
            Model.O3_MINI_2025_01_31_HIGH_REASONING_EFFORT,
            id="reasoning effort versioned",
        ),
    ],
)
def test_from_permissive(value: str, reasoning: str | None, expected: Model):
    assert Model.from_permissive(value, reasoning) == expected
