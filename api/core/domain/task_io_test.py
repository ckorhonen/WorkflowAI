from copy import deepcopy
from typing import Any
from unittest import mock

import pytest

from core.domain.errors import JSONSchemaValidationError
from tests.utils import fixtures_json

from .task_io import RawJSONSchema, RawStringSchema, SerializableTaskIO


@pytest.fixture
def array_schema() -> SerializableTaskIO:
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "companyName": {"type": "string", "description": "Name of the company", "examples": ["Thrive Capital"]},
                "companyId": {
                    "type": "string",
                    "description": "Unique identifier for the company",
                    "examples": ["comp123"],
                },
                "logoUrl": {
                    "type": "string",
                    "format": "uri",
                    "description": "Logo URL of the company",
                    "examples": ["https://example.com/logo.png"],
                },
                "articleCollections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Topic of the article collection",
                                "examples": ["Innovation in Finance"],
                            },
                            "summary": {
                                "type": "string",
                                "description": "Summary of the article collection",
                                "examples": ["Summary encompassing the general theme of the articles"],
                            },
                            "articles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Title of the article",
                                            "examples": ["Tech Innovations in Finance"],
                                        },
                                        "url": {
                                            "type": "string",
                                            "format": "uri",
                                            "description": "URL of the article",
                                            "examples": ["https://example.com/article"],
                                        },
                                        "author": {
                                            "type": "string",
                                            "description": "Author of the article",
                                            "examples": ["John Doe"],
                                        },
                                        "source": {
                                            "type": "string",
                                            "description": "Source of the article",
                                            "examples": ["New York Times"],
                                        },
                                        "published": {
                                            "type": "number",
                                            "description": "Publication timestamp",
                                            "examples": [{"$numberLong": "1625097600000"}],
                                        },
                                        "sentiment": {
                                            "type": "string",
                                            "enum": ["positive", "negative", "neutral"],
                                            "description": "Sentiment of the article",
                                            "examples": ["positive"],
                                        },
                                        "businessEvents": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "label": {
                                                        "type": "string",
                                                        "description": "Label of the business event",
                                                        "examples": ["Product Launch"],
                                                    },
                                                    "salienceLevel": {
                                                        "type": "string",
                                                        "description": "Salience level of the business event",
                                                        "examples": ["High"],
                                                    },
                                                },
                                                "required": ["label", "salienceLevel"],
                                            },
                                            "description": "Business events mentioned in the article",
                                        },
                                    },
                                    "required": ["title", "url", "published", "businessEvents"],
                                },
                            },
                        },
                        "required": ["topic", "summary", "articles"],
                    },
                },
            },
            "required": ["companyName", "companyId", "articleCollections"],
        },
    }
    return SerializableTaskIO(version="1", json_schema=schema)


def test_validate_array_invalid(array_schema: SerializableTaskIO):
    output = {
        "companyName": "Thrive Health",
        "companyId": "thrive001",
        "logoUrl": "https://thrivehealth.com/logo.png",
        "articleCollections": [
            {
                "topic": "Revolutionizing Health: New Wellness Techniques",
                "summary": "This article focuses on new wellness techniques that are transforming the healthcare landscape.",
                "articles": [
                    {
                        "title": "Revolutionizing Health: New Wellness Techniques",
                        "url": "https://healthnews.com/articles/new-wellness",
                        "author": "Alice Johnson",
                        "source": "Health Daily",
                        "published": 1660303200000,
                        "sentiment": "positive",
                        "businessEvents": [{"label": "Healthcare Conference", "salienceLevel": "Medium"}],
                    },
                ],
            },
        ],
    }

    with pytest.raises(JSONSchemaValidationError):
        array_schema.enforce(output)

    # sanity
    array_schema.enforce([output])


@pytest.mark.parametrize(
    "output",
    [
        {
            "description": "",
            "end_time": None,
            "start_time": {"date": "2023-10-20", "time": "11:00:00", "timezone": "Europe/London"},
            "title": "Quarterly Review Meeting",
        },
        {
            "description": "",
            "end_time": {"date": None},
            "start_time": {"date": "2023-10-20", "time": "11:00:00", "timezone": "Europe/London"},
            "title": "Quarterly Review Meeting",
        },
    ],
)
def test_optional_nulls(output: dict[str, Any]):
    # Check that we remove optional nulls
    schema = fixtures_json("jsonschemas", "extract_event_output.json")
    task_io = SerializableTaskIO(version="1", json_schema=schema)
    with pytest.raises(JSONSchemaValidationError):
        task_io.enforce(output, strip_opt_none_and_empty_strings=False)

    task_io.enforce(output, strip_opt_none_and_empty_strings=True)

    if "end_time" in output:
        assert output["end_time"] == {}


def test_strip_extras():
    schema = fixtures_json("jsonschemas", "extract_event_output.json")
    task_io = SerializableTaskIO(version="1", json_schema=schema)

    output = {
        "description": "",
        "start_time": {"date": "2023-10-20", "time": "11:00:00", "timezone": "Europe/London", "bla": "bla"},
        "title": "Quarterly Review Meeting",
        "extra": "extra",
    }
    cloned = deepcopy(output)

    task_io.enforce(output, strip_extras=True)

    assert "extra" not in output
    assert "bla" not in output["start_time"]
    del cloned["extra"]
    del cloned["start_time"]["bla"]  # type: ignore
    assert output == cloned


def test_strip_empty_strings():
    schema = fixtures_json("jsonschemas", "extract_event_output.json")
    task_io = SerializableTaskIO(version="1", json_schema=schema)

    output = {
        "description": "",
        "start_time": {"date": "2023-10-20", "time": "11:00:00", "timezone": "Europe/London"},
        "end_time": {"date": "", "time": None, "timezone": ""},
        "title": "Quarterly Review Meeting",
    }

    task_io.enforce(output, strip_opt_none_and_empty_strings=True)

    assert output == {
        "description": "",
        "start_time": {"date": "2023-10-20", "time": "11:00:00", "timezone": "Europe/London"},
        "title": "Quarterly Review Meeting",
        "end_time": {},
    }


class TestSanitize:
    def test_sanitize(self):
        task_io = SerializableTaskIO.from_json_schema(
            {
                "type": "object",
                "properties": {
                    "a": {"type": "string"},
                    "b": {"type": "object", "properties": {"c": {"type": "string"}}},
                    "c": {"type": "array", "items": {"type": "object", "properties": {"d": {"type": "string"}}}},
                },
            },
        )

        obj = {"a": "a", "f": "f", "b": {"1": "1", "c": "c"}, "c": [{"d": "d", "e": "e"}]}
        obj_copy = deepcopy(obj)
        sanitized = task_io.sanitize(obj)
        assert obj == obj_copy  # check it has not changed
        assert sanitized == {"a": "a", "b": {"c": "c"}, "c": [{"d": "d"}]}


class TestFromJsonSchema:
    def test_raises_on_invalid_schema(self):
        with pytest.raises(JSONSchemaValidationError):
            SerializableTaskIO.from_json_schema({"items": "hello"})

    def test_adds_refs(self):
        """Check that we correctly validate and add internal refs when streamline is True"""

        schema: dict[str, Any] = {
            "$defs": {"Image": {}},
            "type": "object",
            "properties": {
                "field": {"$ref": "#/$defs/Image"},
            },
        }
        task_io = SerializableTaskIO.from_json_schema(schema, streamline=True)
        assert task_io.json_schema == {
            "$defs": {"Image": mock.ANY},
            "type": "object",
            "properties": {
                "field": {"$ref": "#/$defs/Image"},
            },
        }


class TestRawStringSchema:
    def test_raw_string_schema(self):
        # Check that we don't raise when returning a string
        RawStringSchema.enforce("hello")


class TestRawJSONSchema:
    @pytest.mark.parametrize(
        "obj",
        [
            pytest.param(["hello"], id="array"),
            pytest.param({"hello": "world"}, id="dict"),
        ],
    )
    def test_enforce(self, obj: Any):
        # Check that we don't raise when returning a dict
        RawJSONSchema.enforce(obj)
