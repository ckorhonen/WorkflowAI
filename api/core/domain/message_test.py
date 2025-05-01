import pytest

from core.domain.fields.file import File
from core.domain.message import MessageContent
from core.utils.templates import InvalidTemplateError, TemplateManager


@pytest.fixture(scope="session")
def template_manager():
    return TemplateManager()


class TestMessageContent:
    async def test_templated(self, template_manager: TemplateManager):
        renderer = template_manager.renderer({"name": "John"})
        content = MessageContent(text="Hello, {{ name }}!")
        templated = await content.templated(renderer)
        assert templated.text == "Hello, John!"

    async def test_file_templated(self, template_manager: TemplateManager):
        renderer = template_manager.renderer({"name": "John"})
        content = MessageContent(file=File(url="https://{{name}}.com/image.png"))
        templated = await content.templated(renderer)
        assert templated.file is not None
        assert templated.file.url == "https://John.com/image.png"

    async def test_invalid_template(self, template_manager: TemplateManager):
        renderer = template_manager.renderer({"name": "John"})
        content = MessageContent(file=File(url="https://{%if hello%}{{name}}.com/image.png"))
        with pytest.raises(InvalidTemplateError):
            await content.templated(renderer)
