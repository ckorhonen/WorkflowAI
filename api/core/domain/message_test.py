from unittest import mock

import pytest

from core.domain.fields.file import File
from core.domain.message import Message, MessageContent, Messages
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

        # Check that no field is unset
        assert templated.model_fields_set == set(MessageContent.model_fields.keys())

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


class TestMessage:
    async def test_templated(self, template_manager: TemplateManager):
        renderer = template_manager.renderer({"name": "John"})
        message = Message(role="user", content=[MessageContent(text="Hello, {{ name }}!")])
        templated = await message.templated(renderer)
        assert templated.content[0].text == "Hello, John!"

        # Check that no field is unset
        assert templated.model_fields_set == set(Message.model_fields.keys())


class TestJsonSchemaForTemplate:
    def test_string_only(self):
        messages = Messages(messages=[Message.with_text("Hello, {{ name }}!")])
        schema = messages.json_schema_for_template(base_schema=None)
        assert schema == {
            "type": "object",
            "properties": {"name": {}},
        }

    @pytest.mark.skip(reason="TODO: Add image support")
    def test_file_only(self):
        messages = Messages(
            messages=[Message(role="user", content=[MessageContent(file=File(url="{{a_file_url}}"))])],
        )
        schema = messages.json_schema_for_template(base_schema=None)
        assert schema == {
            "$defs": {"File": mock.ANY},
            "type": "object",
            "properties": {"a_file_url": {"$ref": "#/$defs/File"}},
        }

    @pytest.mark.skip(reason="TODO: Add image support")
    def test_file_and_text(self):
        messages = Messages(
            messages=[
                Message(
                    role="user",
                    content=[
                        MessageContent(text="Hello, {{ name }}!"),
                        MessageContent(file=File(url="{{a_file_url}}")),
                    ],
                ),
            ],
        )
        schema = messages.json_schema_for_template(base_schema=None)
        assert schema == {
            "$defs": {"File": mock.ANY},
            "type": "object",
            "properties": {
                "name": {},
                "a_file_url": {"$ref": "#/$defs/File"},
            },
        }

    @pytest.mark.skip(reason="TODO: Add image support")
    def test_image_url(self):
        messages = Messages(
            messages=[Message(role="user", content=[MessageContent(file=File(url="{{a_file_url}}", format="image"))])],
        )
        schema = messages.json_schema_for_template(base_schema=None)
        assert schema == {
            "$defs": {"Image": mock.ANY},
            "type": "object",
            "properties": {"a_file_url": {"$ref": "#/$defs/Image"}},
        }
