from api.services.messages.messages_utils import json_schema_for_template
from core.domain.message import Message


class TestJsonSchemaForTemplate:
    def test_empty_messages(self):
        """Test with empty messages list."""
        messages: list[Message] = []
        base_schema = None
        schema, last_index = json_schema_for_template(messages, base_schema)
        assert schema is None
        assert last_index == -1

    def test_no_templated_messages(self):
        """Test with messages containing no template variables."""
        messages = [
            Message.with_text("Hello world"),
            Message.with_text("This is a test"),
        ]
        base_schema = None
        schema, last_index = json_schema_for_template(messages, base_schema)
        assert schema is None
        assert last_index == -1

    def test_single_templated_message(self):
        """Test with a single message containing template variables."""
        messages = [
            Message.with_text("Hello {{name}}"),
        ]
        base_schema = None
        schema, last_index = json_schema_for_template(messages, base_schema)
        assert schema is not None
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert last_index == 0

    def test_multiple_templated_messages(self):
        """Test with multiple messages containing template variables."""
        messages = [
            Message.with_text("Hello {{name}}"),
            Message.with_text("Your age is {{age}}"),
            Message.with_text("Welcome to {{city}}"),
        ]
        base_schema = None
        schema, last_index = json_schema_for_template(messages, base_schema)
        assert schema == {
            "type": "object",
            "properties": {
                "name": {},
                "age": {},
                "city": {},
            },
        }
        assert last_index == 2

    def test_with_base_schema(self):
        """Test with a provided base schema."""
        messages = [
            Message.with_text("Hello {{name}}"),
        ]
        base_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }
        schema, last_index = json_schema_for_template(messages, base_schema)
        assert schema == {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }
        assert last_index == 0

    def test_mixed_content_messages(self):
        """Test with messages containing both templated and non-templated content."""
        messages = [
            Message.with_text("Hello world"),
            Message.with_text("Welcome {{name}}"),
            Message.with_text("This is a test"),
            Message.with_text("Your age is {{age}}"),
        ]
        base_schema = None
        schema, last_index = json_schema_for_template(messages, base_schema)
        assert schema is not None
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert last_index == 3

    def test_complex_template_variables(self):
        """Test with complex template variable patterns."""
        messages = [
            Message.with_text("User: {{user.name}}"),
            Message.with_text("Address: {{user.address.street}}"),
        ]
        base_schema = None
        schema, last_index = json_schema_for_template(messages, base_schema)
        assert schema is not None
        assert "properties" in schema
        assert "user" in schema["properties"]
        assert "properties" in schema["properties"]["user"]
        assert "name" in schema["properties"]["user"]["properties"]
        assert "address" in schema["properties"]["user"]["properties"]
        assert last_index == 1
