# pyright: reportPrivateUsage=false
import asyncio
from datetime import timedelta

import pytest
from redis.asyncio import Redis

from core.storage.redis.redis_storage import RedisStorage


@pytest.fixture(scope="session")
def session_redis_storage() -> RedisStorage:
    # Storage string always maps to localhost for safety
    connection_string = "redis://localhost:6379/15"
    return RedisStorage(
        tenant_uid=1,
        redis_client=Redis.from_url(connection_string),  # pyright: ignore [reportUnknownMemberType]
    )


@pytest.fixture()
async def redis_storage(session_redis_storage: RedisStorage):
    # Flusing all keys to avoid conflicts
    await session_redis_storage._redis_client.flushall()  # pyright: ignore [reportUnknownMemberType]
    yield session_redis_storage


async def test_redis_storage_set_get_pop(redis_storage: RedisStorage):
    assert await redis_storage.get("test") is None
    await redis_storage.set("test", "test", timedelta(seconds=1))
    assert await redis_storage.get("test") == "test"
    assert await redis_storage.pop("test") == "test"
    assert await redis_storage.get("test") is None


async def test_redis_storage_expire(redis_storage: RedisStorage):
    await redis_storage.set("test", "test", timedelta(milliseconds=10))
    assert await redis_storage.get("test") == "test"
    await asyncio.sleep(0.01)
    assert await redis_storage.get("test") is None


async def test_redis_storage_expire_gt(redis_storage: RedisStorage):
    await redis_storage.set("test", "test", timedelta(milliseconds=10))
    assert await redis_storage.get("test") == "test"
    await redis_storage.expire("test", timedelta(seconds=1), gt=True)
    await asyncio.sleep(0.01)
    assert await redis_storage.get("test") == "test", "key expired after resetting expiration"
