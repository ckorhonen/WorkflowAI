from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from pytest_httpx import HTTPXMock

from core.domain.errors import DefaultError
from core.domain.fields.file import File
from core.domain.input_evaluation import InputEvaluation
from core.domain.task_evaluator import EvalV2Evaluator
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentInput
from core.evaluators.input_task_evaluator import (
    InputTaskEvaluator,
    InputTaskEvaluatorOptions,
    InternalTasksForEvaluations,
)
from core.runners.workflowai.utils import FileWithKeyPath
from core.utils.dicts import set_at_keypath
from tests.models import task_variant


@pytest.fixture
def mock_internal_tasks():
    return AsyncMock(spec=InternalTasksForEvaluations)


@pytest.fixture
def evaluator(mock_internal_tasks: Mock):
    return InputTaskEvaluator(
        task=Mock(spec=SerializableTaskVariant),
        options=InputTaskEvaluatorOptions(
            evaluator_id="mock_evaluator_id",
            task_data=EvalV2Evaluator(instructions="task bla"),
            input_evaluation=InputEvaluation(
                task_input_hash="",
                correct_outputs=[],
                incorrect_outputs=[],
                evaluation_instruction="input boo",
            ),
        ),
        internal_tasks=mock_internal_tasks,
    )


def _set_at_keypath_fn(payload: AgentInput):
    async def _set_at_keypath(keypath: list[str | int], value: Any):
        set_at_keypath(payload, keypath, value)

    return _set_at_keypath


class TestReplaceImagesByTheirDescription:
    async def test_success(self, evaluator: InputTaskEvaluator, mock_internal_tasks: Mock):
        mock_internal_tasks.describe_images.return_value = ["mock description 1", "mock description 2"]

        payload = {
            "mock_key_path_1": {"url": "https://mock_url_1.com/image.png", "content_type": "image/png"},
            "mock_key_path_2": {"url": "https://mock_url_2.com/image.pdf", "content_type": "image/png"},
        }
        images = [
            FileWithKeyPath(
                key_path=["mock_key_path_1"],
                url="https://mock_url_1.com/image.png",
                content_type="image/png",
                format="image",
            ),
            FileWithKeyPath(
                key_path=["mock_key_path_2"],
                url="https://mock_url_2.com/image.pdf",
                content_type="application/pdf",
                format="image",
            ),
        ]

        await evaluator._replace_images_by_their_description(  # pyright: ignore[reportPrivateUsage]
            images=images,
            set_at_keypath=_set_at_keypath_fn(payload),
        )

        assert payload == {
            "mock_key_path_1": {"description": "mock description 1"},
            "mock_key_path_2": {"description": "mock description 2"},
        }

        mock_internal_tasks.describe_images.assert_awaited_once_with(
            images,
            instructions="task bla\n\ninput boo",
        )

    async def test_count_mismatch(self, evaluator: InputTaskEvaluator, mock_internal_tasks: Mock):
        mock_internal_tasks.describe_images.return_value = ["mock description 1"]

        payload = {
            "mock_key_path_1": {"url": "https://mock_url_1.com/image.png", "content_type": "image/png"},
            "mock_key_path_2": {"url": "https://mock_url_2.com/image.png", "content_type": "image/png"},
        }
        payload_copy = deepcopy(payload)
        images = [
            FileWithKeyPath(
                key_path=["mock_key_path_1"],
                url="https://mock_url_1.com/image.png",
                content_type="image/png",
                format="image",
            ),
            FileWithKeyPath(
                key_path=["mock_key_path_2"],
                url="https://mock_url_2.com/image.png",
                content_type="image/png",
                format="image",
            ),
        ]

        with pytest.raises(DefaultError):
            await evaluator._replace_images_by_their_description(  # pyright: ignore[reportPrivateUsage]
                images=images,
                set_at_keypath=_set_at_keypath_fn(payload),
            )

        assert payload == payload_copy


class TestInlineTextFiles:
    async def test_success(self, evaluator: InputTaskEvaluator, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url="https://mock_url_1.com/image.txt", content=b"i am the content")
        payload = {"mock_key_path_1": {"url": "https://mock_url_1.com/image.txt"}}

        files = [
            FileWithKeyPath(
                key_path=["mock_key_path_1"],
                url="https://mock_url_1.com/image.txt",
                content_type="text/plain",
            ),
        ]

        await evaluator._inline_text_files(  # pyright: ignore[reportPrivateUsage]
            files,
            _set_at_keypath_fn(payload),
        )
        assert payload == {
            "mock_key_path_1": "i am the content",
        }

    async def test_one_fails(self, evaluator: InputTaskEvaluator, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url="https://mock_url_1.com/image.txt", content=b"i am the content")
        httpx_mock.add_response(url="https://mock_url_2.com/image.txt", status_code=404)
        payload = {
            "mock_key_path_1": {"url": "https://mock_url_1.com/image.txt"},
            "mock_key_path_2": {"url": "https://mock_url_2.com/image.txt"},
        }

        files = [
            FileWithKeyPath(
                key_path=["mock_key_path_1"],
                url="https://mock_url_1.com/image.txt",
                content_type="text/plain",
            ),
            FileWithKeyPath(
                key_path=["mock_key_path_2"],
                url="https://mock_url_2.com/image.txt",
                content_type="text/plain",
            ),
        ]

        await evaluator._inline_text_files(  # pyright: ignore[reportPrivateUsage]
            files,
            _set_at_keypath_fn(payload),
        )
        assert payload == {
            "mock_key_path_1": "i am the content",
            "mock_key_path_2": {
                "url": "https://mock_url_2.com/image.txt",
            },
        }


class TestSanitizeInput:
    async def test_no_files(self, evaluator: InputTaskEvaluator, mock_internal_tasks: Mock):
        evaluator.task = task_variant(input_schema={"type": "object", "properties": {"bla": {"type": "string"}}})
        sanitized = await evaluator._sanitize_input({"bla": "blabla"})  # pyright: ignore[reportPrivateUsage]
        assert sanitized == {"bla": "blabla"}

    @pytest.fixture
    def evaluator_with_file(self, evaluator: InputTaskEvaluator):
        evaluator.task = task_variant(
            input_schema={
                "type": "object",
                "properties": {"file": {"$ref": "#/$defs/File"}},
                "$defs": {"File": File.model_json_schema()},
            },
        )
        return evaluator

    async def test_files_in_input(self, evaluator_with_file: InputTaskEvaluator, mock_internal_tasks: Mock):
        task_input = {"file": {"url": "https://mock_url_1.com/image.png"}}

        mock_internal_tasks.describe_images.return_value = ["mock description 1"]

        assert await evaluator_with_file._sanitize_input(task_input) == {"file": {"description": "mock description 1"}}  # pyright: ignore[reportPrivateUsage]

        mock_internal_tasks.describe_images.assert_awaited_once()

    async def test_replace_images_fails(self, evaluator_with_file: InputTaskEvaluator, mock_internal_tasks: Mock):
        mock_internal_tasks.describe_images.side_effect = Exception("mock error")
        task_input = {"file": {"url": "https://mock_url_1.com/image.png"}}
        # check that we don't crash
        await evaluator_with_file._sanitize_input(task_input)  # pyright: ignore[reportPrivateUsage]
        assert task_input == {"file": {"url": "https://mock_url_1.com/image.png"}}

        mock_internal_tasks.describe_images.assert_awaited_once()

    async def test_inline_text_files_fails(self, evaluator_with_file: InputTaskEvaluator, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url="https://mock_url_1.com/image.txt", status_code=404)
        task_input = {"file": {"url": "https://mock_url_1.com/image.txt"}}
        # check that we don't crash
        await evaluator_with_file._sanitize_input(task_input)  # pyright: ignore[reportPrivateUsage]
        assert task_input == {"file": {"url": "https://mock_url_1.com/image.txt"}}
        assert httpx_mock.get_request(url="https://mock_url_1.com/image.txt") is not None

    async def test_text_and_image_files(
        self,
        evaluator: InputTaskEvaluator,
        httpx_mock: HTTPXMock,
        mock_internal_tasks: Mock,
    ):
        evaluator.task = task_variant(
            input_schema={
                "type": "object",
                "properties": {"files": {"type": "array", "items": {"$ref": "#/$defs/File"}}},
                "$defs": {"File": File.model_json_schema()},
            },
        )

        httpx_mock.add_response(url="https://mock_url_2.com/image.txt", content=b"i am the content")
        mock_internal_tasks.describe_images.return_value = ["mock description 1"]

        task_input = {
            "files": [
                {"url": "https://mock_url_1.com/image.png"},
                {"url": "https://mock_url_2.com/image.txt"},
            ],
        }
        assert await evaluator._sanitize_input(task_input) == {  # pyright: ignore[reportPrivateUsage]
            "files": [
                {"description": "mock description 1"},
                "i am the content",
            ],
        }

        mock_internal_tasks.describe_images.assert_awaited_once()
        assert httpx_mock.get_request(url="https://mock_url_2.com/image.txt") is not None
