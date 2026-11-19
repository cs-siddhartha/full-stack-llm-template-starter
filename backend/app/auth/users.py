from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.auth.models import StoredUser
from app.auth.tables import UserRow
from app.database import DatabaseSessionFactory


class UserStore(Protocol):
    async def create(self, user: StoredUser) -> bool: ...

    async def get_by_email(self, email: str) -> StoredUser | None: ...

    async def mark_verified(self, email: str) -> StoredUser | None: ...

    async def delete(self, email: str) -> None: ...


class PostgresUserStore:
    """Persist registered identities and password hashes in PostgreSQL."""

    def __init__(self, sessions: DatabaseSessionFactory) -> None:
        self._sessions = sessions

    async def create(self, user: StoredUser) -> bool:
        row = UserRow(
            user_id=user.user_id,
            email=user.email,
            password_hash=user.password_hash,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )
        async with self._sessions() as session:
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                return False
        return True

    async def get_by_email(self, email: str) -> StoredUser | None:
        async with self._sessions() as session:
            row = await session.scalar(select(UserRow).where(UserRow.email == email))
        return None if row is None else self._to_model(row)

    async def mark_verified(self, email: str) -> StoredUser | None:
        async with self._sessions() as session:
            row = await session.scalar(select(UserRow).where(UserRow.email == email))
            if row is None:
                return None
            row.email_verified = True
            await session.commit()
            return self._to_model(row)

    async def delete(self, email: str) -> None:
        async with self._sessions.begin() as session:
            await session.execute(delete(UserRow).where(UserRow.email == email))

    @staticmethod
    def _to_model(row: UserRow) -> StoredUser:
        return StoredUser(
            user_id=row.user_id,
            email=row.email,
            password_hash=row.password_hash,
            email_verified=row.email_verified,
            created_at=row.created_at,
        )


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
