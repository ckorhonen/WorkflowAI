from typing import Optional, override

from redis.asyncio import Redis

from core.domain.events import EventRouter
from core.storage.clickhouse.clickhouse_client import ClickhouseClient
from core.storage.key_value_storage import KeyValueStorage
from core.storage.mongo.mongo_storage import MongoStorage
from core.storage.mongo.mongo_types import AsyncClient
from core.storage.redis.redis_storage import RedisStorage
from core.storage.task_run_storage import TaskRunStorage
from core.utils.encryption import Encryption


class CombinedStorage(MongoStorage):
    def __init__(
        self,
        tenant: str,
        tenant_uid: int,
        encryption: Encryption,
        event_router: EventRouter,
        mongo_dsn: Optional[str] = None,
        mongo_client: Optional[AsyncClient] = None,
        mongo_db_name: Optional[str] = None,
        clickhouse_dsn: Optional[str] = None,
        redis_client: Optional[Redis] = None,
    ):
        super().__init__(
            tenant=tenant,
            tenant_uid=tenant_uid,
            encryption=encryption,
            event_router=event_router,
            connection_string=mongo_dsn,
            client=mongo_client,
            db_name=mongo_db_name,
        )

        self._clickhouse_client = (
            ClickhouseClient(
                connection_string=clickhouse_dsn,
                tenant_uid=tenant_uid,
            )
            if clickhouse_dsn
            else None
        )
        self._kv_storage = RedisStorage(tenant_uid=tenant_uid, redis_client=redis_client) if redis_client else None

    @property
    @override
    def task_runs(self) -> TaskRunStorage:
        return self._clickhouse_client or super().task_runs

    @property
    @override
    def kv(self) -> KeyValueStorage:
        return self._kv_storage or super().kv
