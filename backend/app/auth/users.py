import hashlib
from typing import Protocol

from redis.asyncio import Redis

from app.auth.models import StoredUser


class UserStore(Protocol):
    async def create(self, user: StoredUser) -> bool: ...

    async def get_by_email(self, email: str) -> StoredUser | None: ...

    async def mark_verified(self, email: str) -> StoredUser | None: ...

    async def delete(self, email: str) -> None: ...


class RedisUserStore:
    """Persist registered users in Redis while keeping email addresses out of keys."""

    def __init__(self, client: Redis, namespace: str) -> None:
        self._client = client
        self._prefix = f"{namespace}:user:"

    def _key(self, email: str) -> str:
        digest = hashlib.sha256(email.encode("utf-8")).hexdigest()
        return f"{self._prefix}{digest}"

    async def create(self, user: StoredUser) -> bool:
        created = await self._client.set(
            self._key(user.email),
            user.model_dump_json(),
            nx=True,
        )
        return bool(created)

    async def get_by_email(self, email: str) -> StoredUser | None:
        value = await self._client.get(self._key(email))
        return None if value is None else StoredUser.model_validate_json(value)

    async def mark_verified(self, email: str) -> StoredUser | None:
        user = await self.get_by_email(email)
        if user is None:
            return None
        verified = user.model_copy(update={"email_verified": True})
        await self._client.set(self._key(email), verified.model_dump_json())
        return verified

    async def delete(self, email: str) -> None:
        await self._client.delete(self._key(email))


class InMemoryUserStore:
    """Store registered users in memory for isolated tests."""

    def __init__(self) -> None:
        self._users: dict[str, StoredUser] = {}

    async def create(self, user: StoredUser) -> bool:
        if user.email in self._users:
            return False
        self._users[user.email] = user
        return True

    async def get_by_email(self, email: str) -> StoredUser | None:
        return self._users.get(email)

    async def mark_verified(self, email: str) -> StoredUser | None:
        user = self._users.get(email)
        if user is None:
            return None
        verified = user.model_copy(update={"email_verified": True})
        self._users[email] = verified
        return verified

    async def delete(self, email: str) -> None:
        self._users.pop(email, None)
