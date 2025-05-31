from datetime import timedelta
from typing import Protocol


class KeyValueStorage(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def pop(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, expires_in: timedelta) -> None: ...

    async def expire(self, key: str, expires_in: timedelta, gt: bool = False, lt: bool = False) -> None:
        """
        Set the expiry of the key.

        Args:
            key: The key to set the expiry for.
            expires_in: The expiry time.
            gt: Set expiry only when the new expiry is greater than current one.
            lt: Set expiry only when the new expiry is less than current one.
        """
        ...
