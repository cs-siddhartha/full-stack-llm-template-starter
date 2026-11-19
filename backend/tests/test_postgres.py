import asyncio
import os
import secrets

import pytest

from app.auth.models import StoredUser
from app.auth.users import PostgresUserStore
from app.auth.verification import PostgresVerificationStore
from app.config import Settings
from app.database import create_database_engine, create_session_factory

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1",
    reason="Set RUN_POSTGRES_TESTS=1 to run PostgreSQL integration tests",
)


def test_postgres_auth_records_persist_across_repository_instances() -> None:
    """Verify durable auth repositories against the migrated PostgreSQL schema."""

    async def exercise_repositories() -> None:
        settings = Settings()
        engine = create_database_engine(settings.database_url)
        sessions = create_session_factory(engine)
        email = f"integration-{secrets.token_hex(8)}@example.com"
        user = StoredUser(
            user_id=f"user:{secrets.token_hex(16)}",
            email=email,
            password_hash="scrypt$integration-test",
        )

        first_users = PostgresUserStore(sessions)
        verifications = PostgresVerificationStore(sessions)
        try:
            assert await first_users.create(user)
            token = await verifications.create(email, 60)

            second_users = PostgresUserStore(sessions)
            persisted = await second_users.get_by_email(email)
            assert persisted == user
            assert await verifications.consume(token) == email
            assert await verifications.consume(token) is None

            verified = await second_users.mark_verified(email)
            assert verified is not None
            assert verified.email_verified is True
        finally:
            await first_users.delete(email)
            await engine.dispose()

    asyncio.run(exercise_repositories())
