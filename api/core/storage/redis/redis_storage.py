from datetime import timedelta
from typing import cast, override

from redis.asyncio import Redis

from core.storage.key_value_storage import KeyValueStorage


class RedisStorage(KeyValueStorage):
    def __init__(self, tenant_uid: int, redis_client: Redis):
        self._redis_client = redis_client
        self._tenant_uid = tenant_uid

    def _key(self, key: str) -> str:
        return f"{self._tenant_uid}:{key}"

    @override
    async def get(self, key: str) -> str | None:
        bs = await self._redis_client.get(self._key(key))
        return bs.decode() if bs else None

    @override
    async def set(self, key: str, value: str, expires_in: timedelta) -> None:
        await self._redis_client.set(
            self._key(key),
            value.encode(),
            px=int(expires_in.total_seconds() * 1000),
        )

    @override
    async def expire(self, key: str, expires_in: timedelta) -> None:
        # Important to note that expire only supports seconds not milliseconds
        # Setting milliseconds is basically setting expiration to 0
        await self._redis_client.expire(
            self._key(key),
            time=expires_in,
        )

    @override
    async def pop(self, key: str) -> str | None:
        # Not using getdel because it's not supported by redis 6.0
        pipeline = self._redis_client.pipeline()
        pipeline.get(self._key(key))
        pipeline.delete(self._key(key))
        bs, _ = await pipeline.execute()  # pyright: ignore [reportUnknownVariableType]
        return cast(bytes, bs).decode() if bs else None
