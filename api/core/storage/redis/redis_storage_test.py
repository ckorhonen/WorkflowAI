# pyright: reportPrivateUsage=false
import asyncio
from datetime import timedelta

import pytest
from redis.asyncio import Redis

from core.storage.redis.redis_storage import RedisStorage


@pytest.fixture(scope="function")
async def redis_storage(redis_client: Redis) -> RedisStorage:
    return RedisStorage(
        tenant_uid=1,
        redis_client=redis_client,
    )


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
    await redis_storage.expire("test", timedelta(seconds=1))
    await asyncio.sleep(0.01)
    assert await redis_storage.get("test") == "test", "key expired after resetting expiration"
