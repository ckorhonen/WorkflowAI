from pydantic import BaseModel
from typing_extensions import override

from core.domain.message import Messages
from core.domain.run_output import RunOutput
from core.domain.task_group import TaskGroup
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentInput
from core.runners.abstract_runner import AbstractRunner, CacheFetcher


class NoopExternalRunnerOptions(BaseModel):
    group: TaskGroup


class NoopNoCacheError(ValueError):
    pass


class NoopExternalRunner(AbstractRunner[NoopExternalRunnerOptions]):
    """
    A runner that generates a prompt based on:
    - the output json schema
    - the input schema and data serialized to a yaml with comments
    - the task instructions

    The prompt is separated in a system and user message and the version is computed based on the generated
    messages for a standard input (an input generated from the input class with default values).
    """

    def __init__(
        self,
        task: SerializableTaskVariant,
        group: TaskGroup,
        cache_fetcher: CacheFetcher | None = None,
    ):
        super().__init__(
            task,
            options=NoopExternalRunnerOptions(group=group),
            properties=group.properties,
            cache_fetcher=cache_fetcher,
        )

    @override
    @classmethod
    def options_class(cls) -> type[NoopExternalRunnerOptions]:
        raise NotImplementedError("Should not be used")

    @override
    @classmethod
    def _build_options(
        cls,
        task: SerializableTaskVariant,
        properties: TaskGroupProperties,
    ) -> NoopExternalRunnerOptions:
        raise NotImplementedError("Should not be used")

    @override
    @classmethod
    def supports(cls, task: SerializableTaskVariant) -> bool:
        raise NotImplementedError("Should not be used")

    @override
    def version(self) -> str:
        raise NotImplementedError("Should not be used")

    @override
    async def _build_task_output(self, input: AgentInput | Messages) -> RunOutput:
        raise NoopNoCacheError("External runner cannot run tasks")

    @override
    def _build_properties(
        self,
        options: NoopExternalRunnerOptions,
        original: TaskGroupProperties | None,
    ) -> TaskGroupProperties:
        return options.group.properties
