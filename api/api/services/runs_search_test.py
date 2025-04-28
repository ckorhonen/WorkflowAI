from unittest.mock import Mock

import pytest

from api.services.runs_search import RunsSearchService
from core.domain.major_minor import MajorMinor
from core.domain.models import Model
from core.domain.search_query import (
    FieldQuery,
    ReviewSearchOptions,
    SearchField,
    SearchOperationSingle,
    SearchOperator,
    SearchQueryNested,
    SearchQuerySimple,
)
from tests.models import task_variant
from tests.utils import fixtures_json, mock_aiter


@pytest.fixture
def service(mock_storage: Mock):
    return RunsSearchService(mock_storage)


class TestFieldsFromSchema:
    def test_fields_from_schema(self):
        schema = fixtures_json("jsonschemas", "extract_event_output.json")
        fields = {f.key_path: f.type for f in RunsSearchService._fields_from_schema(SearchField.INPUT, schema)}  # pyright: ignore [reportPrivateUsage]

        assert fields == {
            "title": "string",
            "description": "string",
            "start_time.date": "string",
            "start_time.time": "string",
            "start_time.timezone": "string",
            "end_time.date": "string",
            "end_time.time": "string",
            "end_time.timezone": "string",
            "location": "string",
        }

    def test_2(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"},
                "properties": {"type": "object", "properties": {"test": {"type": "string"}}},
                "validated_input": {"type": "boolean"},
            },
            "required": ["name", "age"],
        }
        fields = {f.key_path: f.type for f in RunsSearchService._fields_from_schema(SearchField.INPUT, schema)}  # pyright: ignore [reportPrivateUsage]
        assert fields == {
            "name": "string",
            "age": "integer",
            "email": "string",
            "properties.test": "string",
            "validated_input": "boolean",
        }

    def test_array(self):
        schema = {
            "type": "object",
            "properties": {"list_items": {"type": "array", "items": {"type": "string"}}},
        }
        fields = {f.key_path: f.type for f in RunsSearchService._fields_from_schema(SearchField.INPUT, schema)}  # pyright: ignore [reportPrivateUsage]
        assert fields == {"list_items.length": "array_length", "list_items[]": "string"}

    def test_array_nested(self):
        schema = {
            "type": "object",
            "properties": {
                "list_items": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"name": {"type": "string"}}},
                },
            },
        }
        fields = {f.key_path: f.type for f in RunsSearchService._fields_from_schema(SearchField.INPUT, schema)}  # pyright: ignore [reportPrivateUsage]
        assert fields == {"list_items.length": "array_length", "list_items[].name": "string"}


class TestSchemasSearchFields:
    def test_schema_search_field(self):
        search_field = RunsSearchService._schema_search_field(5)  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "schema"
        assert search_field.operators == [
            "is",
            "is not",
            "greater than",
            "greater than or equal to",
            "less than",
            "less than or equal to",
        ]
        assert search_field.type == "number"
        assert search_field.suggestions == [5, 4, 3, 2, 1]


class TestSchemasSearchField:
    async def test_schemas_search_field(
        self,
        mock_storage: Mock,
        service: RunsSearchService,
    ):
        mock_storage.task_variant_latest_by_schema_id.return_value = task_variant(
            input_schema={"type": "object", "properties": {"field_1": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"field_2": {"type": "integer"}}},
        )
        mock_storage.get_latest_idx.return_value = 2
        mock_storage.task_runs.aggregate_task_metadata_fields.return_value = mock_aiter(
            ("field_1", ["value_1", "value_2"]),
            ("field_2", ["value_3", "value_4"]),
        )
        mock_storage.task_groups.list_task_groups.return_value = [
            MajorMinor(1, 0),
            MajorMinor(1, 1),
        ]

        fields = [f async for f in service.schemas_search_fields(("test_task", 1), 1)]
        assert len(fields) == 14

        expected_fields = set(SearchField)
        expected_fields.remove(SearchField.EVAL_HASH)
        # Check that each search field is returned at least once
        for field in expected_fields:
            assert any(f.field_name == field.value for f in fields), f"Field {field.value} not found"


class TestMetadataFieldsSearchField:
    async def test_metadata_fields_search_field(self, mock_storage: Mock):
        mock_storage.task_runs.aggregate_task_metadata_fields.return_value = mock_aiter(
            ("field_1", [f"value_{i}" for i in range(100)]),
            ("field_2", ["value_3", "value_4"]),
        )
        fields = await RunsSearchService._task_metadata_fields(mock_storage.task_runs, ("test_task", 1))  # pyright: ignore [reportPrivateUsage]
        assert len(fields) == 2
        field_1 = fields[0]
        assert field_1.field_name == "metadata"
        assert field_1.key_path == "field_1"
        assert field_1.suggestions
        assert len(field_1.suggestions) == 30


class TestVersionSearchField:
    def test_version_search_field(self):
        majors = [MajorMinor(1, 2), MajorMinor(2, 3), MajorMinor(1, 0)]
        search_field = RunsSearchService._version_search_field(majors)  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "version"
        assert search_field.operators == ["is", "is not"]
        assert search_field.type == "string"
        assert search_field.suggestions == ["Production", "Staging", "Dev", "2.3", "1.2", "1.0"]


class TestPriceSearchField:
    def test_price_search_field(self):
        search_field = RunsSearchService._price_search_field()  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "price"
        assert search_field.operators == [
            "is",
            "is not",
            "greater than",
            "greater than or equal to",
            "less than",
            "less than or equal to",
        ]
        assert search_field.type == "number"


class TestLatencySearchField:
    def test_latency_search_field(self):
        search_field = RunsSearchService._latency_search_field()  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "latency"
        assert search_field.operators == [
            "is",
            "is not",
            "greater than",
            "greater than or equal to",
            "less than",
            "less than or equal to",
        ]
        assert search_field.type == "number"


class TestStatusSearchField:
    def test_status_search_field(self):
        search_field = RunsSearchService._status_search_field()  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "status"
        assert search_field.operators == ["is"]
        assert search_field.type == "string"

        assert search_field.suggestions == ["success", "failure"]


class TestTemperatureSearchField:
    def test_temperature_search_field(self):
        search_field = RunsSearchService._temperature_search_field()  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "temperature"
        assert search_field.operators == ["is", "is not"]
        assert search_field.type == "string"
        assert search_field.suggestions == [
            "Precise",
            "0.1",
            "0.2",
            "0.3",
            "0.4",
            "Balanced",
            "0.6",
            "0.7",
            "0.8",
            "0.9",
            "Creative",
        ]


class TestModelSearchField:
    def test_model_search_field(self):
        search_field = RunsSearchService._model_search_field()  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "model"
        assert search_field.operators == ["is", "is not", "contains", "does not contain"]
        assert search_field.type == "string"
        assert search_field.suggestions == [m.value for m in Model]


class TestSourceSearchField:
    def test_source_search_field(self):
        search_field = RunsSearchService._source_search_field()  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "source"
        assert search_field.operators == ["is", "is not"]
        assert search_field.type == "string"
        assert search_field.suggestions == ["my app", "WorkflowAI"]


class TestReviewSearchField:
    def test_review_search_field(self):
        search_field = RunsSearchService._review_search_field()  # pyright: ignore [reportPrivateUsage]
        assert search_field.field_name == "review"
        assert search_field.operators == ["is"]
        assert search_field.type == "string"
        assert search_field.suggestions == ["positive", "negative", "unsure", "any"]


class TestProcessFieldQuery:
    async def test_process_field_query_exhaustive(self, service: RunsSearchService):
        # Check that all fields are valid fields
        field_queries = [
            FieldQuery(field_name=SearchField.TEMPERATURE, operator=SearchOperator.IS, values=["Precise"]),
            FieldQuery(field_name=SearchField.VERSION, operator=SearchOperator.IS, values=["Production"]),
            FieldQuery(field_name=SearchField.SOURCE, operator=SearchOperator.IS, values=["my app"]),
            FieldQuery(field_name=SearchField.REVIEW, operator=SearchOperator.IS, values=["positive"]),
            FieldQuery(field_name=SearchField.SCHEMA_ID, operator=SearchOperator.IS, values=[1]),
            FieldQuery(field_name=SearchField.PRICE, operator=SearchOperator.IS, values=[100]),
            FieldQuery(field_name=SearchField.LATENCY, operator=SearchOperator.IS, values=[100]),
            FieldQuery(field_name=SearchField.STATUS, operator=SearchOperator.IS, values=["success"]),
            FieldQuery(field_name=SearchField.MODEL, operator=SearchOperator.IS, values=["gpt-4"]),
            FieldQuery(field_name=SearchField.TIME, operator=SearchOperator.IS, values=["2021-01-01"]),
            FieldQuery(field_name=SearchField.EVAL_HASH, operator=SearchOperator.IS, values=["123"]),
            FieldQuery(field_name="input.name", operator=SearchOperator.IS, values=["hello"]),
            FieldQuery(field_name="output.f2", operator=SearchOperator.IS, values=["world"]),
            FieldQuery(field_name="metadata.f1", operator=SearchOperator.IS, values=["hello"]),
        ]
        processed = [  # using an array and not a set since priocessing review will return an eval hash
            a.field
            async for a in service._process_field_query(task_id="test_task", field_queries=field_queries)  # pyright: ignore [reportPrivateUsage]
        ]
        assert len(processed) == len(field_queries)
        # Sanity check to make sure we didn't miss any fields
        assert len(processed) == len(SearchField), "sanity"

    async def test_process_nested_field_query(self, service: RunsSearchService):
        field_queries = [
            FieldQuery(field_name="input.name.bla", operator=SearchOperator.IS, values=["hello"]),
        ]
        processed = [
            a
            async for a in service._process_field_query(task_id="test_task", field_queries=field_queries)  # pyright: ignore [reportPrivateUsage]
        ]
        assert len(processed) == 1
        assert processed[0] == SearchQueryNested(
            field=SearchField.INPUT,
            field_type=None,
            key_path="name.bla",
            operation=SearchOperationSingle(operator=SearchOperator.IS, value="hello"),
        )

    async def test_process_array_length_field_query(self, service: RunsSearchService):
        field_queries = [
            FieldQuery(
                field_name="output.list_items.length",
                operator=SearchOperator.IS,
                values=[1],
                type="array_length",
            ),
        ]
        processed = [
            a
            async for a in service._process_field_query(task_id="test_task", field_queries=field_queries)  # pyright: ignore [reportPrivateUsage]
        ]
        assert len(processed) == 1
        assert processed[0] == SearchQueryNested(
            field=SearchField.OUTPUT,
            field_type="array_length",
            key_path="list_items",
            operation=SearchOperationSingle(operator=SearchOperator.IS, value=1),
        )

    async def test_process_review_field_query(self, service: RunsSearchService, mock_storage: Mock):
        mock_storage.reviews.eval_hashes_for_review.return_value = {"123", "456"}
        field_queries = [
            FieldQuery(field_name=SearchField.REVIEW, operator=SearchOperator.IS, values=["positive"]),
        ]
        processed = [
            a
            async for a in service._process_field_query(task_id="test_task", field_queries=field_queries)  # pyright: ignore [reportPrivateUsage]
        ]
        assert len(processed) == 1
        assert processed[0] == SearchQuerySimple(
            field=SearchField.EVAL_HASH,
            operation=SearchOperationSingle(operator=SearchOperator.IS, value={"123", "456"}),
            field_type="string",
        )
        mock_storage.reviews.eval_hashes_for_review.assert_awaited_once_with("test_task", ReviewSearchOptions.POSITIVE)


# TODO[search]
# class TestSearchTaskRuns:
#     async def test_search_task_runs(
#         self,
#         runs_service: RunsService,
#         mock_storage: AsyncMock,
#     ):
#         # Setup mock data
#         task_id = "test_task"
#         field_queries = [
#             FieldQuery(field_name="temperature", operator=SearchOperator.IS, values=["Precise"]),
#             FieldQuery(field_name="input.text", operator=SearchOperator.CONTAINS, values=["hello"]),
#             FieldQuery(field_name="version", operator=SearchOperator.IS, values=["Production"]),
#             FieldQuery(field_name="source", operator=SearchOperator.IS, values=["my app"]),
#         ]
#         limit = 10
#         offset = 0

#         # Mock task runs
#         mock_runs = [
#             Run(
#                 id="1",
#                 task_id=task_id,
#                 group=TaskGroup(id="group1", iteration=1, properties=TaskGroupProperties()),
#                 task_schema_id=1,
#                 task_input_hash="hash1",
#                 task_output_hash="hash1",
#                 task_input={"text": "hello world"},
#                 task_output={},
#                 status="success",
#             ),
#             Run(
#                 id="2",
#                 task_id=task_id,
#                 group=TaskGroup(id="group2", iteration=2, properties=TaskGroupProperties()),
#                 task_schema_id=1,
#                 task_input_hash="hash2",
#                 task_output_hash="hash2",
#                 task_input={"text": "hello test"},
#                 task_output={},
#                 status="success",
#             ),
#         ]

#         async def mock_aiter():
#             for run in mock_runs:
#                 yield run

#         mock_storage.task_runs.search_task_runs.return_value = mock_aiter()
#         mock_storage.task_runs.count_filtered_task_runs.return_value = len(mock_runs)

#         # Execute
#         result = await runs_service.search_task_runs(
#             task_id=task_id,
#             field_queries=field_queries,
#             limit=limit,
#             offset=offset,
#             map=lambda x: x,
#         )

#         # Verify
#         assert result.count == 2
#         assert len(result.items) == 2
#         assert result.items[0].id == "1"
#         assert result.items[0].group.id == "group1"  # Unchanged
#         assert result.items[1].id == "2"
#         assert result.items[1].group.id == "group2"  # Unchanged

#     async def test_search_task_runs_invalid_query(self, runs_service: RunsService):
#         # Test with invalid temperature value
#         with pytest.raises(BadRequestError):
#             await runs_service.search_task_runs(
#                 task_id="test_task",
#                 field_queries=[
#                     FieldQuery(
#                         field_name="temperature",
#                         operator=SearchOperator.IS,
#                         values=["InvalidTemp"],
#                     ),
#                 ],
#                 limit=10,
#                 offset=0,
#                 map=lambda x: x,
#             )
