import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import delete

from app.auth.tables import EmailVerificationRow
from app.database import DatabaseSessionFactory


class VerificationStore(Protocol):
    async def create(self, email: str, ttl_seconds: int) -> str: ...

    async def consume(self, token: str) -> str | None: ...

    async def revoke(self, token: str) -> None: ...


class PostgresVerificationStore:
    """Persist short-lived email verification token digests in PostgreSQL."""

    def __init__(self, sessions: DatabaseSessionFactory) -> None:
        self._sessions = sessions

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def create(self, email: str, ttl_seconds: int) -> str:
        token = secrets.token_urlsafe(32)
        row = EmailVerificationRow(
            token_digest=self._digest(token),
            email=email,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )
        async with self._sessions.begin() as session:
            session.add(row)
        return token

    async def consume(self, token: str) -> str | None:
        statement = (
            delete(EmailVerificationRow)
            .where(EmailVerificationRow.token_digest == self._digest(token))
            .returning(
                EmailVerificationRow.email,
                EmailVerificationRow.expires_at,
            )
        )
        async with self._sessions.begin() as session:
            result = (await session.execute(statement)).one_or_none()
        if result is None or result.expires_at <= datetime.now(UTC):
            return None
        return str(result.email)

    async def revoke(self, token: str) -> None:
        async with self._sessions.begin() as session:
            await session.execute(
                delete(EmailVerificationRow).where(
                    EmailVerificationRow.token_digest == self._digest(token)
                )
            )


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
