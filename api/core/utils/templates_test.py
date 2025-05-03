import pytest

from core.domain.errors import BadRequestError
from core.utils.templates import InvalidTemplateError, TemplateManager, extract_variable_schema


@pytest.fixture
def template_manager():
    return TemplateManager()


class TestCompileTemplate:
    async def test_compile_template(self, template_manager: TemplateManager):
        compiled, variables = await template_manager.compile_template("Hello, {{ name }}!")
        assert compiled
        assert variables == {"name"}

    async def test_compile_complex_template(self, template_manager: TemplateManager):
        template = """
Team Members:
{% for member in team.members %}
- {{ member.name }} ({{ member.role }})
    Projects:
    {% for project in member.projects %}
    * {{ project.name }} - Status: {{ project.status }}
    {% endfor %}
{% endfor %}

{% for project in projects %}
* {{ project.name }} - Status: {{ project.status }}
{% endfor %}

{% if customer.name == "John" %}
Hello, John!
{% else %}
Hello, {{ customer.name }}!
{% endif %}
"""
        compiled, variables = await template_manager.compile_template(template)
        assert compiled
        assert variables == {"team", "projects", "customer"}

    async def test_error_on_missing_variable(self, template_manager: TemplateManager):
        with pytest.raises(InvalidTemplateError) as e:
            await template_manager.compile_template("Hello, {{ name }!")
        assert e.value.message == "unexpected '}'"
        assert e.value.line_number == 1


class TestRenderTemplate:
    async def test_render_template(self, template_manager: TemplateManager):
        data = {"name": "John"}
        rendered, variables = await template_manager.render_template("Hello, {{ name }}!", data)
        assert rendered == "Hello, John!"
        assert variables == {"name"}
        assert data == {"name": "John"}

    async def test_render_template_remaining(self, template_manager: TemplateManager):
        data = {"name": "John", "hello": "world"}
        rendered, variables = await template_manager.render_template(
            "Hello, {{ name }}!",
            data,
        )
        assert rendered == "Hello, John!"
        assert variables == {"name"}
        assert data == {"name": "John", "hello": "world"}


class TestExtractVariableSchema:
    def test_extract_variable_schema(self):
        schema = extract_variable_schema("Hello, {{ name }}!")
        assert schema == {"type": "object", "properties": {"name": {"type": "string"}}}

    def test_attribute_access(self):
        schema = extract_variable_schema("User: {{ user.name }}")
        assert schema == {
            "type": "object",
            "properties": {"user": {"type": "object", "properties": {"name": {"type": "string"}}}},
        }

    def test_nested_attribute_access(self):
        schema = extract_variable_schema("Email: {{ user.profile.email }}")
        assert schema == {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {"email": {"type": "string"}},
                        },
                    },
                },
            },
        }

    def test_item_access_as_array(self):
        # Note: Getitem is always treated as array access ('*') by the current implementation
        schema = extract_variable_schema("First user: {{ users[0].name }}")
        assert schema == {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                },
            },
        }

    def test_for_loop(self):
        template = "{% for item in items %}{{ item.name }}{% endfor %}"
        schema = extract_variable_schema(template)
        assert schema == {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                },
            },
        }

    def test_nested_for_loop(self):
        template = "{% for user in users %}{% for post in user.posts %}{{ post.title }}{% endfor %}{% endfor %}"
        schema = extract_variable_schema(template)
        assert schema == {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "posts": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {"title": {"type": "string"}},
                                },
                            },
                        },
                    },
                },
            },
        }

    def test_conditional(self):
        template = "{% if user.is_admin %}{{ user.name }}{% else %}Guest{% endif %}"
        schema = extract_variable_schema(template)
        assert schema == {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "is_admin": {"type": "string"},  # Type defaults to string
                        "name": {"type": "string"},
                    },
                },
            },
        }

    def test_combined(self):
        template = "{{ user.name }} {% for project in user.projects %}{{ project.id }}{% endfor %}"
        schema = extract_variable_schema(template)
        assert schema == {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "projects": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {"id": {"type": "string"}},
                            },
                        },
                    },
                },
            },
        }

    def test_no_variables(self):
        schema = extract_variable_schema("Just plain text.")
        assert schema == {"type": "object", "properties": {}}

    def test_function_call_raises_error(self):
        # Functions are not supported
        with pytest.raises(BadRequestError, match="Template functions are not supported"):
            extract_variable_schema("{{ my_func() }}")
