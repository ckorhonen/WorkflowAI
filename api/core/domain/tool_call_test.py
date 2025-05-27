import pytest

from core.domain.tool_call import ToolCall, ToolCallOutput, ToolCallRequestWithID


class TestToolCallWithID:
    def test_validate_no_id(self):
        tool_call = ToolCallRequestWithID.model_validate({"tool_name": "test", "tool_input_dict": {"test": "test"}})
        assert tool_call.id == "test_828bcef8763c1bc616e25a06be4b90ff"
        assert tool_call.tool_name == "test"
        assert tool_call.tool_input_dict == {"test": "test"}

    def test_validate_with_id(self):
        tool_call = ToolCallRequestWithID.model_validate(
            {"id": "test", "tool_name": "test", "tool_input_dict": {"test": "test"}},
        )
        assert tool_call.id == "test"
        assert tool_call.tool_name == "test"
        assert tool_call.tool_input_dict == {"test": "test"}

    def test_with_result(self):
        tool_call = ToolCallRequestWithID.model_validate(
            {"id": "test", "tool_name": "test", "tool_input_dict": {"test": "test"}},
        )
        with_result = tool_call.with_result("test")
        assert with_result.id == "test"
        assert with_result.tool_name == "test"
        assert with_result.tool_input_dict == {"test": "test"}
        assert with_result.result == "test"
        assert with_result.error is None

    def test_with_error(self):
        tool_call = ToolCallRequestWithID.model_validate(
            {"id": "test", "tool_name": "test", "tool_input_dict": {"test": "test"}},
        )
        with_error = tool_call.with_error("test")
        assert with_error.id == "test"
        assert with_error.tool_name == "test"
        assert with_error.tool_input_dict == {"test": "test"}
        assert with_error.result is None
        assert with_error.error == "test"

    def test_with_result_none(self):
        tool_call = ToolCallRequestWithID.model_validate(
            {"id": "test", "tool_name": "test", "tool_input_dict": {"test": "test"}},
        )
        with_result = tool_call.with_result(None)
        assert with_result.id == "test"
        assert with_result.tool_name == "test"
        assert with_result.tool_input_dict == {"test": "test"}
        assert with_result.result is None
        assert with_result.error is None


class TestToolCallFinalCombine:
    def test_combine(self):
        tool_calls = [
            ToolCallRequestWithID(id="test", tool_name="test", tool_input_dict={"test": "test"}),
            ToolCallRequestWithID(id="test2", tool_name="test2", tool_input_dict={"test2": "test2"}),
        ]
        outputs = [ToolCallOutput(id="test", output="test"), ToolCallOutput(id="test2", error="test2")]
        combined = ToolCall.combine(tool_calls, outputs)
        assert combined == [
            ToolCall(id="test", tool_name="test", tool_input_dict={"test": "test"}, result="test"),
            ToolCall(id="test2", tool_name="test2", tool_input_dict={"test2": "test2"}, error="test2"),
        ]

    def test_combine_no_output(self):
        # Check that if there is no output, the tool call is not included in the result
        tool_calls = [
            ToolCallRequestWithID(id="test", tool_name="test", tool_input_dict={"test": "test"}),
            ToolCallRequestWithID(id="test2", tool_name="test2", tool_input_dict={"test2": "test2"}),
        ]
        outputs = [ToolCallOutput(id="test", error="test")]
        combined = ToolCall.combine(tool_calls, outputs)
        assert combined == [
            ToolCall(id="test", tool_name="test", tool_input_dict={"test": "test"}, error="test"),
        ]


def test_tool_call_request_with_id_creation() -> None:
    # Given
    tool_call = ToolCallRequestWithID(
        id="test_id",
        tool_name="test_name",
        tool_input_dict={"arg": "value"},
    )

    # Then
    assert tool_call.id == "test_id"
    assert tool_call.tool_name == "test_name"
    assert tool_call.tool_input_dict == {"arg": "value"}


def test_tool_call_request_with_id_hash() -> None:
    # Given
    tool_call1 = ToolCallRequestWithID(
        id="test_id",
        tool_name="test_name",
        tool_input_dict={"arg": "value"},
    )
    tool_call2 = ToolCallRequestWithID(
        id="test_id",
        tool_name="test_name",
        tool_input_dict={"arg": "value"},
    )
    tool_call3 = ToolCallRequestWithID(
        id="different_id",
        tool_name="test_name",
        tool_input_dict={"arg": "value"},
    )

    # Then
    assert hash(tool_call1) == hash(tool_call2)
    assert hash(tool_call1) != hash(tool_call3)


def test_tool_call_request_with_id_equality() -> None:
    # Given
    tool_call1 = ToolCallRequestWithID(
        id="test_id",
        tool_name="test_name",
        tool_input_dict={"arg": "value"},
    )
    tool_call2 = ToolCallRequestWithID(
        id="test_id",
        tool_name="test_name",
        tool_input_dict={"arg": "value"},
    )
    tool_call3 = ToolCallRequestWithID(
        id="different_id",
        tool_name="test_name",
        tool_input_dict={"arg": "value"},
    )
    not_a_tool_call = "not a tool call"

    # Then
    assert tool_call1 == tool_call2
    assert tool_call1 != tool_call3
    assert tool_call1 != not_a_tool_call  # type: ignore[comparison-overlap]


class TestToolCallPreview:
    @pytest.mark.parametrize(
        ("tool", "expected"),
        [
            pytest.param(
                ToolCall(tool_name="test_name", tool_input_dict={"arg": "value"}),
                "test_name(arg: value)",
                id="string_only",
            ),
            pytest.param(
                ToolCall(tool_name="test_name", tool_input_dict={"arg": 1}),
                "test_name(arg: 1)",
                id="number",
            ),
            pytest.param(
                ToolCall(tool_name="get_weather", tool_input_dict={"latitude": 1.0, "longitude": 2.0}),
                "get_weather(latitude: 1, longitude: 2)",
                id="two_floats",
            ),
            pytest.param(
                ToolCall(tool_name="get_weather", tool_input_dict={"latitude": "1" * 50, "longitude": 2.0}),
                f"get_weather(latitude: {'1' * 30}..., longitude: 2)",
                id="long_string",
            ),
        ],
    )
    def test_preview(self, tool: ToolCall, expected: str):
        assert tool.preview == expected
