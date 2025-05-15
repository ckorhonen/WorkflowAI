from core.domain.fields.file import File, FileKind
from core.utils.schema_sanitation import clean_pydantic_schema


class TestFile:
    def test_validate_url(self):
        img = File(url="https://bla.com/file.png")
        assert img.to_url() == "https://bla.com/file.png"
        assert img.content_type == "image/png"

    def test_validate_data(self):
        img = File(data="iVBORw0KGgoAAAANSUhEUgAAAAUA", content_type="image/png")
        assert img.to_url() == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA"
        assert img.content_type == "image/png"

    def test_validate_data_url(self):
        img = File(url="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA")
        assert img.to_url() == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA"
        assert img.content_type == "image/png"
        assert img.data == "iVBORw0KGgoAAAANSUhEUgAAAAUA"

    def test_validate_data_content_type(self):
        img = File(
            url="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExYXQxbTFybW0wZWs2M3RkY3gzNXZlbXp4aHhkcTl4ZzltN2V6Y21lcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/rkFQ8LrdXcP5e/giphy.webp",
        )
        assert img.content_type == "image/webp"

    def test_validate_data_content_type_none(self):
        img = File(url="https://bla.com/file")
        assert img.content_type is None

    def test_init_with_format(self):
        img = File(url="https://bla.com/file", format="image")
        assert img.format == FileKind.IMAGE


class TestFileJsonSchema:
    def test_json_schema(self):
        """Check that the json schema is expected. Changing the schema could have an impact on
        agents using the file field."""
        assert clean_pydantic_schema(File) == {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the image"},
                "content_type": {
                    "type": "string",
                    "description": "The content type of the file",
                    "examples": [
                        "image/png",
                        "image/jpeg",
                        "audio/wav",
                        "application/pdf",
                    ],
                },
                "data": {"type": "string", "description": "The base64 encoded data of the file"},
            },
        }
