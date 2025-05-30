import pytest

from tests.e2e.conftest import ApiRunFn


@pytest.mark.requires_deployed
@pytest.mark.parametrize(
    "version,model",
    [
        (13, "llama-3.2-90b-text-preview"),
        (15, "gemini-1.5-pro-002"),
        (19, "gemini-1.5-flash-002"),
    ],
)
async def test_analyze_book_characters(run_fn: ApiRunFn, version: int, model: str | None):
    output = await run_fn(
        "analyze-book-characters",
        1,
        {
            "book_title": "The Shadow of the Wind",
        },
        version,
        assert_model=model,
    )

    assert "characters" in output["task_output"]
