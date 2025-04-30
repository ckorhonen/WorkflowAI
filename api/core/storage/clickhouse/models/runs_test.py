from datetime import date, datetime
from typing import get_args

import pytest

from core.domain.agent_run import AgentRun
from core.domain.errors import InternalError
from core.domain.fields.internal_reasoning_steps import InternalReasoningStep
from core.domain.llm_completion import LLMCompletion
from core.domain.llm_usage import LLMUsage
from core.domain.models import Provider
from core.domain.search_query import (
    ReviewSearchOptions,
    SearchField,
    SearchOperationSingle,
    SearchOperator,
    SearchQueryNested,
    SearchQuerySimple,
    SimpleSearchField,
    StatusSearchOptions,
)
from core.domain.task_run_query import SerializableTaskRunField
from core.domain.tool_call import ToolCall, ToolCallRequestWithID
from core.storage.clickhouse.models.runs import (
    ClickhouseRun,
)
from core.storage.clickhouse.models.utils import MAX_UINT_32
from core.utils.uuid import uuid7
from tests.models import task_run_ser


@pytest.fixture
def task_run():
    return task_run_ser(id=str(uuid7()), task_uid=1, task_schema_id=1)


class TestClickhouseRunsValidate:
    def test_task_uid(self, task_run: AgentRun):
        task_run.task_uid = MAX_UINT_32 + 1
        with pytest.raises(ValueError):
            ClickhouseRun.from_domain(1, task_run)

        task_run.task_uid = MAX_UINT_32
        ClickhouseRun.from_domain(1, task_run)

    def test_tenant_uid(self, task_run: AgentRun):
        with pytest.raises(ValueError):
            ClickhouseRun.from_domain(MAX_UINT_32 + 1, task_run)

        ClickhouseRun.from_domain(MAX_UINT_32, task_run)

    def test_provider_metadata(self, task_run: AgentRun):
        task_run.group.properties.provider = "openai"
        task_run.metadata = None
        run = ClickhouseRun.from_domain(1, task_run)
        assert run.metadata == {"workflowai.provider": "openai"}

    @pytest.mark.parametrize(
        "completions",
        [
            pytest.param(
                [
                    LLMCompletion(
                        messages=[{"bla": "bla"}],
                        usage=LLMUsage(prompt_token_count=1, completion_token_count=1),
                        provider=Provider.OPEN_AI,
                        config_id="123",
                        preserve_credits=True,
                    ),
                ],
                id="with_config_id",
            ),
            pytest.param(
                [
                    LLMCompletion(
                        messages=[{"bla": "bla"}],
                        usage=LLMUsage(prompt_token_count=1, completion_token_count=1),
                        provider=Provider.OPEN_AI,
                        duration_seconds=1.1,
                    ),
                ],
                id="without_config_id",
            ),
        ],
    )
    def test_llm_completion(self, task_run: AgentRun, completions: list[LLMCompletion]):
        task_run.llm_completions = completions
        run = ClickhouseRun.from_domain(1, task_run)
        sanity = ClickhouseRun.model_validate_json(run.model_dump_json())
        assert sanity.llm_completions == run.llm_completions
        assert sanity.to_domain("").llm_completions == task_run.llm_completions

    def test_tool_calls(self, task_run: AgentRun):
        task_run.tool_calls = [
            ToolCall(id="test", tool_name="test", tool_input_dict={"test": "test"}, result="test"),
        ]
        task_run.tool_call_requests = [
            ToolCallRequestWithID(id="test", tool_name="test", tool_input_dict={"test": "test"}),
        ]
        run = ClickhouseRun.from_domain(1, task_run)
        sanity = ClickhouseRun.model_validate_json(run.model_dump_json())
        assert sanity.tool_calls == run.tool_calls

        sanity = sanity.to_domain("")
        assert sanity.tool_calls == task_run.tool_calls
        assert sanity.tool_call_requests == task_run.tool_call_requests

    def test_reasoning_steps(self, task_run: AgentRun):
        task_run.reasoning_steps = [
            InternalReasoningStep(title="test", explaination="test", output="test"),
        ]
        run = ClickhouseRun.from_domain(1, task_run)
        sanity = ClickhouseRun.model_validate_json(run.model_dump_json())
        assert sanity.reasoning_steps == run.reasoning_steps

        sanity = sanity.to_domain("")
        assert sanity.reasoning_steps == task_run.reasoning_steps

    def test_partial_payload(self):
        """Check that we can validate a partial run payload"""
        payload = {
            "created_at_date": date(2025, 2, 24),
            "run_uuid": 2104046675861711478702752072517678960,
            "task_schema_id": 1,
            "task_uid": 2522560864,
            "tenant_uid": 1393228554,
            "updated_at": datetime(2025, 2, 24, 19, 50, 21),
            "version_id": b"a74516065162c912e8216bef6d2f1c29",
            "version_iteration": 2,
            "version_model": "claude-3-5-sonnet-20240620",
            "version_temperature_percent": 0,
        }
        run = ClickhouseRun.model_validate(payload)
        assert run.output == {}

    def test_empty_payload(self):
        """Check that we can validate a partial run payload"""
        run = ClickhouseRun.model_validate({})
        assert run.output == {}

    def test_empty_output(self):
        """Check that we can payload with an empty output"""
        run = ClickhouseRun.model_validate({"output": ""})
        assert run.output == {}

        run = ClickhouseRun.model_validate({"output": "{}"})
        assert run.output == {}


class TestDomainSanity:
    def test_metadata(self):
        run = task_run_ser(id=str(uuid7()), task_uid=1, task_schema_id=1, metadata={"a": {"b": "c"}, "c": "d"})
        run_db = ClickhouseRun.from_domain(1, run)
        assert run_db.to_domain("").metadata == run.metadata

    def test_exhaustive(self):
        run = task_run_ser(id=str(uuid7()), task_uid=1)
        run_db = ClickhouseRun.from_domain(1, run)
        dumped_no_unset = run_db.model_dump(exclude_unset=True)
        dumped = run_db.model_dump()
        assert dumped_no_unset == dumped

    def test_empty_output(self):
        """Check that we serialize to and from an empty output. An empty string is used in between"""
        run = task_run_ser(id=str(uuid7()), task_uid=1, task_output={})
        run_db = ClickhouseRun.from_domain(1, run)
        dumped = run_db.model_dump()
        assert dumped["output"] == ""
        re_validated = ClickhouseRun.model_validate(dumped).to_domain("")
        assert re_validated.task_output == {}

    def test_string_output(self):
        run = task_run_ser(id=str(uuid7()), task_uid=1, task_output="Hello James!")
        run_db = ClickhouseRun.from_domain(1, run)
        dumped = run_db.model_dump()
        assert dumped["output"] == '"Hello James!"'
        re_validated = ClickhouseRun.model_validate(dumped).to_domain("")
        assert re_validated.task_output == "Hello James!"


class TestToClause:
    def test_json_empty(self):
        query = SearchQueryNested(
            SearchField.INPUT,
            operation=SearchOperationSingle(SearchOperator.IS_EMPTY, None),
            key_path="name",
            field_type="string",
        )
        raw = ClickhouseRun.to_clause(query).to_sql()
        assert raw
        assert raw[0] == "empty(simpleJSONExtractString(input, 'name'))"

    @pytest.mark.parametrize("field", SearchField)
    def test_exhaustive_simple(self, field: SearchField):
        # Check that we suppport all search fields
        # All fields support the IS operator

        is_simple = field in set(get_args(SimpleSearchField))
        supported = True
        match field:
            case SearchField.REVIEW:
                supported = False
                value = ReviewSearchOptions.NEGATIVE
            case SearchField.TIME:
                value = datetime.now()
            case SearchField.TEMPERATURE | SearchField.LATENCY | SearchField.PRICE:
                value = 0.5
            case SearchField.STATUS:
                value = StatusSearchOptions.SUCCESS
            case _:
                value = "bla"
        if is_simple:
            query = SearchQuerySimple(field, SearchOperationSingle(SearchOperator.IS, value))  # pyright: ignore [reportArgumentType]
        else:
            query = SearchQueryNested(field, "string", "bla", SearchOperationSingle(SearchOperator.IS, value))  # pyright: ignore [reportArgumentType]
        if supported:
            assert ClickhouseRun.to_clause(query)
        else:
            with pytest.raises(InternalError):  # noqa: F821
                ClickhouseRun.to_clause(query)


class TestRunColumns:
    @pytest.mark.parametrize("include", get_args(SerializableTaskRunField))
    def test_includes(self, include: SerializableTaskRunField):
        columns = ClickhouseRun.columns(include={include})
        assert len(columns) == 1
        fields = set(ClickhouseRun.model_fields.keys())
        for column in columns:
            assert column in fields


class TestSelectNotHeavy:
    def test_select_not_heavy(self):
        columns = set(ClickhouseRun.select_not_heavy())
        assert "output" in columns
        assert "input" in columns
        assert "llm_completions" not in columns
