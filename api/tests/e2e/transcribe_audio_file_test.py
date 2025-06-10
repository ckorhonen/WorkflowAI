import pytest

from tests.e2e.conftest import ApiRunFn


@pytest.mark.requires_deployed
@pytest.mark.parametrize(
    "version,model",
    [(11, "gemini-1.5-pro-001"), (12, "gemini-1.5-flash-002"), (13, "gpt-4o-audio-preview-2024-10-01")],
)
async def test_sassy_image_description(run_fn: ApiRunFn, version: int, model: str | None):
    # Image task
    output = await run_fn(
        "transcribe-audio-file",
        2,
        {
            "audio_file": {
                "url": "https://workflowaistaging.blob.core.windows.net/workflowai-public/sample.mp3",
            },
        },
        version,
        assert_model=model,
        max_allowed_duration_seconds=15,
    )

    assert "transcription" in output["task_output"]
