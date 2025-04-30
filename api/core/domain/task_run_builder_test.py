import time
from typing import Any

from core.domain.consts import METADATA_KEY_FILE_DOWNLOAD_SECONDS, METADATA_KEY_INFERENCE_SECONDS
from core.domain.llm_completion import LLMCompletion
from core.domain.llm_usage import LLMUsage
from core.domain.models import Provider
from core.domain.run_output import RunOutput
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_run_builder import TaskRunBuilder
from tests.models import task_variant


def _llm_completion(**kwargs: Any) -> LLMCompletion:
    return LLMCompletion(**kwargs, provider=Provider.OPEN_AI)


class TestBuild:
    def test_build_input_hash(self):
        """Check that the input hash is computed based on the task input at instantiation time.
        as opposed to computed on build"""

        task = task_variant()
        builder = TaskRunBuilder(
            task=task,
            task_input={"input": "John"},
            properties=TaskGroupProperties(),
            start_time=time.time(),
        )
        assert (
            builder.task_input_hash
            == "fc494a0457f7c6846dd48a0412274ac0"
            == task.compute_input_hash(builder.serialized_task_input)
        )
        builder.serialized_task_input["blabla"] = "toto"
        run = builder.build(RunOutput({"output": 1}))
        assert run.task_input_hash == "fc494a0457f7c6846dd48a0412274ac0"

    def test_inference_seconds(self):
        """Check that the inference seconds are computed based on the llm completions at build time"""

        task = task_variant()
        builder = TaskRunBuilder(
            task=task,
            task_input={"input": "John"},
            properties=TaskGroupProperties(),
            start_time=time.time(),
        )
        builder.llm_completions.append(
            _llm_completion(duration_seconds=10, messages=[], usage=LLMUsage(completion_token_count=10)),
        )
        run = builder.build(RunOutput({"output": 1}))
        assert run.metadata is not None
        assert run.metadata[METADATA_KEY_INFERENCE_SECONDS] == 10

    def test_inference_seconds_no_duration(self):
        """Check that the inference seconds are not set if the duration is None"""

        task = task_variant()
        builder = TaskRunBuilder(
            task=task,
            task_input={"input": "John"},
            properties=TaskGroupProperties(),
            start_time=time.time(),
        )
        builder.llm_completions.append(
            _llm_completion(duration_seconds=None, messages=[], usage=LLMUsage(completion_token_count=10)),
        )
        run = builder.build(RunOutput({"output": 1}))
        assert run.metadata is None

    def test_inference_seconds_no_completions(self):
        """Check that the inference seconds are not set if there are no completions"""

        task = task_variant()
        builder = TaskRunBuilder(
            task=task,
            task_input={"input": "John"},
            properties=TaskGroupProperties(),
            start_time=time.time(),
        )
        run = builder.build(RunOutput({"output": 1}))
        assert run.metadata is None

    def test_file_download_seconds(self):
        now = time.time()
        task = task_variant()
        builder = TaskRunBuilder(
            task=task,
            task_input={"input": "John"},
            properties=TaskGroupProperties(),
            start_time=now,
        )
        builder.record_file_download_seconds(5)
        builder.llm_completions.append(
            _llm_completion(duration_seconds=1, messages=[], usage=LLMUsage(completion_token_count=10)),
        )
        run = builder.build(RunOutput({"output": 1}), end_time=now + 10)
        assert run.metadata is not None
        assert run.metadata[METADATA_KEY_FILE_DOWNLOAD_SECONDS] == 5
        assert run.metadata[METADATA_KEY_INFERENCE_SECONDS] == 1
        assert run.overhead_seconds == 4
