import pytest
from httpx import HTTPStatusError

from tests.e2e.conftest import ApiRunFn


@pytest.mark.requires_deployed
@pytest.mark.parametrize(
    "version,model",
    [(11, "gemini-1.5-pro-002"), (10, "gemini-1.5-flash-002")],
)
async def test_sassy_image_description(run_fn: ApiRunFn, version: int, model: str | None):
    # Image task
    output = await run_fn(
        "analyze-audio-tone-of-voice",
        2,
        {
            "audio": {
                "url": "https://workflowaistaging.blob.core.windows.net/workflowai-public/sample.mp3",
            },
        },
        version,
        assert_model=model,
        max_allowed_duration_seconds=15,
    )

    assert "tone_of_voice" in output["task_output"]


@pytest.mark.requires_deployed
@pytest.mark.parametrize(
    "version,model",
    [(12, "gpt-4o-audio-preview-2024-10-01")],
)
async def test_audio_refusal(run_fn: ApiRunFn, version: int, model: str | None):
    with pytest.raises(HTTPStatusError) as e:
        await run_fn(
            "analyze-audio-tone-of-voice",
            2,
            {
                "audio": {
                    "url": "https://workflowaistaging.blob.core.windows.net/workflowai-public/sample.mp3",
                },
            },
            version,
            assert_model=model,
            max_allowed_duration_seconds=15,
        )

    json_response = e.value.response.json()
    assert "error" in json_response
    assert json_response["error"]["code"] == "failed_generation"
    msg = json_response["error"]["message"]
    assert "sorry" in msg.lower()
    assert msg.startswith("Model refused to generate a response")
