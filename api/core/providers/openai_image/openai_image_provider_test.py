import base64

import pytest
from pytest_httpx import HTTPXMock

from core.domain.errors import ContentModerationError
from core.domain.fields.file import File
from core.domain.message import Message
from core.domain.models.models import Model
from core.domain.structured_output import StructuredOutput
from core.providers.base.provider_options import ProviderOptions
from core.providers.openai_image.openai_image_provider import OpenAIImageProvider
from core.runners.builder_context import BuilderInterface
from tests.utils import approx


@pytest.fixture()
def openai_image_provider():
    return OpenAIImageProvider()


def _provider_options():
    return ProviderOptions(model=Model.GPT_IMAGE_1)


def _output_factory(raw: str, partial: bool):
    return StructuredOutput(output={})


class TestPrepareCompletion:
    async def test_no_options(self, openai_image_provider: OpenAIImageProvider):
        messages = [
            Message(role=Message.Role.USER, content="A beautiful image of a cat"),
        ]
        request, _ = await openai_image_provider._prepare_completion(messages, _provider_options(), False)  # pyright: ignore [reportPrivateUsage]
        assert request.prompt == "A beautiful image of a cat"


class TestComplete:
    async def test_image_generation(
        self,
        openai_image_provider: OpenAIImageProvider,
        httpx_mock: HTTPXMock,
        mock_builder_context: BuilderInterface,
    ):
        httpx_mock.add_response(
            url="https://api.openai.com/v1/images/generations",
            status_code=200,
            json={
                "data": [{"b64_json": base64.b64encode(b"blabla").decode("utf-8")}],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 20,
                    "total_tokens": 30,
                    "input_tokens_details": {
                        "text_tokens": 10,
                        "image_tokens": 20,
                    },
                },
            },
        )
        messages = [
            Message(role=Message.Role.USER, content="A beautiful image of a cat"),
        ]
        completion = await openai_image_provider.complete(messages, _provider_options(), output_factory=_output_factory)

        assert completion.output == {}
        assert completion.files == [
            File(
                data=base64.b64encode(b"blabla").decode("utf-8"),
                content_type="image/png",
            ),
        ]

        assert mock_builder_context.llm_completions[0].usage.prompt_token_count == 10
        assert mock_builder_context.llm_completions[0].usage.completion_image_token_count == 20
        assert mock_builder_context.llm_completions[0].usage.prompt_image_token_count == 20

        assert mock_builder_context.llm_completions[0].usage.cost_usd == approx(5e-05)

    async def test_image_generation_moderation_blocked(
        self,
        openai_image_provider: OpenAIImageProvider,
        httpx_mock: HTTPXMock,
    ):
        httpx_mock.add_response(
            url="https://api.openai.com/v1/images/generations",
            status_code=400,
            json={
                "error": {
                    "message": "Your request was rejected as a result of our safety system. Your request may contain content that is not allowed by our safety system.",
                    "type": "user_error",
                    "param": None,
                    "code": "moderation_blocked",
                },
            },
        )
        messages = [
            Message(role=Message.Role.USER, content="A beautiful image of a cat"),
        ]
        with pytest.raises(ContentModerationError) as e:
            await openai_image_provider.complete(messages, _provider_options(), output_factory=_output_factory)
        assert not e.value.capture
        assert e.value.store_task_run
