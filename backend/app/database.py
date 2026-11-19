from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Collect application table metadata for Alembic migrations."""


DatabaseSessionFactory = async_sessionmaker[AsyncSession]


def create_database_engine(database_url: str) -> AsyncEngine:
    """Create the shared async PostgreSQL engine used by application repositories."""
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> DatabaseSessionFactory:
    """Create short-lived sessions so concurrent requests never share transactions."""
    return async_sessionmaker(engine, expire_on_commit=False)
