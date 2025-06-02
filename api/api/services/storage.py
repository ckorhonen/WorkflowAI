import logging
import os
from base64 import b64decode

from redis.asyncio import Redis

from core.domain.events import EventRouter
from core.storage.backend_storage import SystemBackendStorage
from core.storage.combined.combined_storage import CombinedStorage
from core.storage.key_value_storage import KeyValueStorage
from core.storage.mongo.mongo_storage import MongoStorage
from core.utils import no_op
from core.utils.aeshmac import AESHMAC
from core.utils.encryption import Encryption

_base_client, _db_name = MongoStorage.build_client(os.environ["WORKFLOWAI_MONGO_CONNECTION_STRING"])

_default_encryption = AESHMAC(
    hmac_key=b64decode(os.environ["STORAGE_HMAC"]),
    aes_key=b64decode(os.environ["STORAGE_AES"]),
)


def _get_redis_client() -> Redis | None:
    connection_string = os.environ.get("REDIS_CONNECTION_STRING")
    if not connection_string:
        logging.getLogger(__name__).warning("Redis client is not available")
        return None
    return Redis.from_url(connection_string)  # pyright: ignore [reportUnknownMemberType]


_shared_redis_client = _get_redis_client()


def shared_encryption():
    return _default_encryption


def storage_for_tenant(
    tenant: str,
    tenant_uid: int,
    event_router: EventRouter,
    encryption: Encryption | None = None,
):
    return CombinedStorage(
        tenant=tenant,
        tenant_uid=tenant_uid,
        mongo_client=_base_client,
        mongo_db_name=_db_name,
        encryption=encryption or _default_encryption,
        event_router=event_router,
        clickhouse_dsn=os.getenv("CLICKHOUSE_CONNECTION_STRING"),
        redis_client=_shared_redis_client,
    )


def system_storage(encryption: Encryption | None = None) -> SystemBackendStorage:
    return storage_for_tenant("__system__", -1, no_op.event_router, encryption)


def key_value_storage_for_tenant(tenant_uid: int) -> KeyValueStorage:
    from core.storage.redis.redis_storage import RedisStorage
    from core.utils.redis_cache import shared_redis_client

    if not shared_redis_client:
        logging.getLogger(__name__).warning("Redis client not available, using noop key value storage")
        from core.storage.noop_storage import NoopKeyValueStorage

        return NoopKeyValueStorage()

    return RedisStorage(tenant_uid=tenant_uid, redis_client=shared_redis_client)
