import logging
from contextlib import asynccontextmanager

from core.utils.redis_cache import shared_redis_client

_logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Exception raised when a lock cannot be acquired."""

    pass


@asynccontextmanager
async def redis_lock(lock_key: str, expire_seconds: int = 60):
    """
    Simple Redis lock context manager for deduplication scenarios.

    Args:
        lock_key: Unique key to use for the lock
        expire_seconds: Lock expiration time in seconds

    Raises:
        LockAcquisitionError: If the lock cannot be acquired
    """
    if shared_redis_client is None:
        _logger.warning("Redis client not available, proceeding without lock", extra={"lock_key": lock_key})
        yield
        return

    # Try to acquire the lock - simply set a key if it doesn't exist
    acquired = await shared_redis_client.set(lock_key, "1", nx=True, ex=expire_seconds)

    if not acquired:
        _logger.info("Failed to acquire lock, resource already locked", extra={"lock_key": lock_key})
        raise LockAcquisitionError(f"Could not acquire lock: {lock_key}")

    try:
        _logger.debug("Lock acquired", extra={"lock_key": lock_key})
        yield
    finally:
        _logger.debug("Lock completed", extra={"lock_key": lock_key})
