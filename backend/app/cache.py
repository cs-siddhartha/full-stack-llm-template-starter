import json
from typing import Protocol

from redis.asyncio import Redis


class CacheStore(Protocol):
    async def get_json(self, key: str) -> object | None: ...

    async def set_json(self, key: str, value: object, ttl_seconds: int) -> None: ...

    async def flush(self) -> int: ...


class RedisCache:
    """Store JSON cache entries in an application-owned Redis namespace."""

    def __init__(self, client: Redis, namespace: str) -> None:
        self._client = client
        self._prefix = f"{namespace}:cache:"

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    async def get_json(self, key: str) -> object | None:
        value = await self._client.get(self._key(key))
        return None if value is None else json.loads(value)

    async def set_json(self, key: str, value: object, ttl_seconds: int) -> None:
        await self._client.set(
            self._key(key),
            json.dumps(value, separators=(",", ":")),
            ex=ttl_seconds,
        )

    async def flush(self) -> int:
        keys = [key async for key in self._client.scan_iter(f"{self._prefix}*")]
        return 0 if not keys else int(await self._client.delete(*keys))


class InMemoryCache:
    """Provide a deterministic cache implementation for isolated tests."""

    def __init__(self) -> None:
        self._values: dict[str, object] = {}

    async def get_json(self, key: str) -> object | None:
        return self._values.get(key)

    async def set_json(self, key: str, value: object, ttl_seconds: int) -> None:
        self._values[key] = value

    async def flush(self) -> int:
        count = len(self._values)
        self._values.clear()
        return count
