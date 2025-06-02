from datetime import timedelta

from typing_extensions import override

from core.domain.agent_run import AgentRun
from core.domain.analytics_events.analytics_events import SourceType
from core.domain.task_example import SerializableTaskExample
from core.domain.task_group import TaskGroup, TaskGroupIdentifier
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_variant import SerializableTaskVariant
from core.domain.users import UserIdentifier
from core.domain.version_environment import VersionEnvironment
from core.storage import ObjectNotFoundException
from core.storage.key_value_storage import KeyValueStorage

from .abstract_storage import AbstractStorage


class NoopStorage(AbstractStorage):
    """A storage that does nothing. Use to disable storage"""

    @property
    def tenant(self) -> str:
        return ""

    @property
    def kv(self) -> KeyValueStorage:
        return NoopKeyValueStorage()

    @override
    async def store_task_resource(
        self,
        task: SerializableTaskVariant,
        update_created_at: bool = True,
    ) -> tuple[SerializableTaskVariant, bool]:
        return task, False

    @override
    async def store_task_run_resource(
        self,
        task: SerializableTaskVariant,
        run: AgentRun,
        user: UserIdentifier | None,
        source: SourceType | None,
    ) -> AgentRun:
        return run

    @override
    async def example_resource_by_id(self, example_id: str) -> SerializableTaskExample:
        raise ObjectNotFoundException()

    @override
    async def task_group_by_id(
        self,
        task_id: str,
        task_schema_id: int,
        ref: int | VersionEnvironment | TaskGroupIdentifier,
    ) -> TaskGroup:
        return TaskGroup(id="", iteration=0, properties=TaskGroupProperties(), tags=[])


class NoopKeyValueStorage(KeyValueStorage):
    """Dummy, should only be used for testing"""

    @override
    async def get(self, key: str) -> str | None:
        return None

    @override
    async def set(self, key: str, value: str, expires_in: timedelta):
        pass

    @override
    async def pop(self, key: str) -> str | None:
        return None

    @override
    async def expire(self, key: str, expires_in: timedelta):
        pass
