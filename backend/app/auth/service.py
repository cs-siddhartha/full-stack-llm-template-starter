import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote

from redis.asyncio import Redis

from app.auth.email import VerificationEmailSender
from app.auth.models import SessionRead, StoredUser
from app.auth.passwords import PasswordHasher
from app.auth.users import UserStore
from app.auth.verification import VerificationStore
from app.config import Settings


class SessionStore(Protocol):
    async def create(self, user: SessionRead, ttl_seconds: int) -> str: ...

    async def get(self, token: str) -> SessionRead | None: ...

    async def delete(self, token: str) -> None: ...


class RedisSessionStore:
    """Store opaque sessions in Redis without persisting raw browser tokens."""

    def __init__(self, client: Redis, namespace: str) -> None:
        self._client = client
        self._prefix = f"{namespace}:session:"

    def _key(self, token: str) -> str:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"{self._prefix}{digest}"

    async def create(self, user: SessionRead, ttl_seconds: int) -> str:
        token = secrets.token_urlsafe(32)
        await self._client.set(
            self._key(token),
            json.dumps(user.model_dump(), separators=(",", ":")),
            ex=ttl_seconds,
        )
        return token

    async def get(self, token: str) -> SessionRead | None:
        value = await self._client.get(self._key(token))
        return None if value is None else SessionRead.model_validate_json(value)

    async def delete(self, token: str) -> None:
        await self._client.delete(self._key(token))


class InMemorySessionStore:
    """Provide deterministic session storage for isolated tests."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionRead] = {}

    async def create(self, user: SessionRead, ttl_seconds: int) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = user
        return token

    async def get(self, token: str) -> SessionRead | None:
        return self._sessions.get(token)

    async def delete(self, token: str) -> None:
        self._sessions.pop(token, None)


@dataclass(frozen=True, slots=True)
class CurrentSession:
    token: str
    user: SessionRead


class DuplicateRegistrationError(Exception):
    pass


class EmailNotVerifiedError(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


class AuthService:
    """Register verified users and issue opaque sessions for users and the demo."""

    def __init__(
        self,
        settings: Settings,
        sessions: SessionStore,
        users: UserStore,
        verifications: VerificationStore,
        email_sender: VerificationEmailSender,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self._settings = settings
        self._sessions = sessions
        self._users = users
        self._verifications = verifications
        self._email_sender = email_sender
        self._password_hasher = password_hasher or PasswordHasher()

    async def signup(self, email: str, password: str) -> None:
        user = StoredUser(
            user_id=f"user:{secrets.token_hex(16)}",
            email=email,
            password_hash=await self._password_hasher.hash(password),
        )
        if not await self._users.create(user):
            raise DuplicateRegistrationError

        token = await self._verifications.create(
            email,
            self._settings.email_verification_ttl_seconds,
        )
        verification_url = (
            f"{self._settings.backend_public_url.rstrip('/')}"
            f"/api/v1/auth/verify-email?token={quote(token)}"
        )
        try:
            await self._email_sender.send_verification(email, verification_url)
        except Exception as error:
            await self._verifications.revoke(token)
            await self._users.delete(email)
            raise EmailDeliveryError from error

    async def verify_email(self, token: str) -> bool:
        email = await self._verifications.consume(token)
        if email is None:
            return False
        return await self._users.mark_verified(email) is not None

    async def login(self, email: str, password: str) -> CurrentSession | None:
        user = await self._users.get_by_email(email.strip().lower())
        if user is None or not await self._password_hasher.verify(
            password,
            user.password_hash,
        ):
            return None
        if not user.email_verified:
            raise EmailNotVerifiedError

        return await self._create_session(
            SessionRead(user_id=user.user_id, username=user.email, role="user")
        )

    async def login_demo(self) -> CurrentSession | None:
        if not self._settings.demo_login_enabled:
            return None
        return await self._create_session(
            SessionRead(user_id="demo:local", username="demo", role="demo")
        )

    async def _create_session(self, user: SessionRead) -> CurrentSession:
        token = await self._sessions.create(user, self._settings.session_ttl_seconds)
        return CurrentSession(token=token, user=user)

    async def resolve(self, token: str) -> CurrentSession | None:
        user = await self._sessions.get(token)
        return None if user is None else CurrentSession(token=token, user=user)

    async def logout(self, token: str) -> None:
        await self._sessions.delete(token)
