import hashlib
import secrets
from typing import Protocol

from redis.asyncio import Redis


class VerificationStore(Protocol):
    async def create(self, email: str, ttl_seconds: int) -> str: ...

    async def consume(self, token: str) -> str | None: ...

    async def revoke(self, token: str) -> None: ...


class RedisVerificationStore:
    """Store short-lived email verification tokens as SHA-256 digests."""

    def __init__(self, client: Redis, namespace: str) -> None:
        self._client = client
        self._prefix = f"{namespace}:email-verification:"

    def _key(self, token: str) -> str:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"{self._prefix}{digest}"

    async def create(self, email: str, ttl_seconds: int) -> str:
        token = secrets.token_urlsafe(32)
        await self._client.set(self._key(token), email, ex=ttl_seconds)
        return token

    async def consume(self, token: str) -> str | None:
        return await self._client.getdel(self._key(token))

    async def revoke(self, token: str) -> None:
        await self._client.delete(self._key(token))


class InMemoryVerificationStore:
    """Store verification tokens in memory for isolated tests."""

    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    async def create(self, email: str, ttl_seconds: int) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = email
        return token

    async def consume(self, token: str) -> str | None:
        return self._tokens.pop(token, None)

    async def revoke(self, token: str) -> None:
        self._tokens.pop(token, None)
