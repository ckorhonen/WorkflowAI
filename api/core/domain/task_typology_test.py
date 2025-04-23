from core.domain.fields.file import File
from core.domain.task_typology import TaskTypology


class TestTypologyFromSchema:
    def test_no_file(self):
        schema = {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
            },
        }
        typology = TaskTypology.from_schema(schema, {})
        assert typology.input.has_image is False
        assert typology.input.has_audio is False

    def test_image_in_input(self):
        schema = {
            "type": "object",
            "properties": {"image": {"$ref": "#/$defs/File", "format": "image"}},
            "$defs": {"File": File.model_json_schema()},
        }
        typology = TaskTypology.from_schema(schema, {})
        assert typology.input.has_image is True
        assert typology.input.has_audio is False

    def test_deprecated_image_in_input(self):
        schema = {
            "type": "object",
            "properties": {"image": {"$ref": "#/$defs/Image"}},
            "$defs": {"Image": File.model_json_schema()},
        }
        typology = TaskTypology.from_schema(schema, {})
        assert typology.input.has_image is True
        assert typology.input.has_audio is False

    def test_array_of_images_in_input(self):
        schema = {
            "type": "object",
            "properties": {"images": {"type": "array", "items": {"$ref": "#/$defs/Image"}}},
            "$defs": {"Image": File.model_json_schema()},
        }
        typology = TaskTypology.from_schema(schema, {})
        assert typology.input.has_image is True
        assert typology.input.has_audio is False
