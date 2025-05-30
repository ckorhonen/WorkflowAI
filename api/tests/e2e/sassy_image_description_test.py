import pytest

from tests.e2e.conftest import ApiRunFn


@pytest.mark.requires_deployed
@pytest.mark.parametrize(
    "version,model",
    [(39, "gemini-1.5-flash-002"), (36, "gpt-4o-2024-08-06"), ("production", None)],
)
async def test_sassy_image_description(run_fn: ApiRunFn, version: int, model: str | None):
    # Image task
    output = await run_fn(
        "sassy-image-description",
        3,
        {
            "image": {
                "url": "https://eu-cdn.5h1pm3n7.com/eda24beee2d10000/graff/7256727772247097344_1536x2048",
            },
        },
        version,
        assert_model=model,
        max_allowed_duration_seconds=5,
    )

    assert "description" in output["task_output"]
