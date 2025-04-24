import pytest

from core.domain.message import Message
from core.domain.models.models import Model
from core.providers.base.provider_options import ProviderOptions
from core.providers.openai_image.openai_image_provider import OpenAIImageProvider


@pytest.fixture()
def openai_image_provider():
    return OpenAIImageProvider()


def _provider_options():
    return ProviderOptions(model=Model.GPT_IMAGE_1)


class TestPrepareCompletion:
    async def test_no_options(self, openai_image_provider: OpenAIImageProvider):
        messages = [
            Message(role=Message.Role.USER, content="A beautiful image of a cat"),
        ]
        request, _ = await openai_image_provider._prepare_completion(messages, _provider_options(), False)  # pyright: ignore [reportPrivateUsage]
        assert request.prompt == "A beautiful image of a cat"
