from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.auth.email import (
    ResendVerificationEmailSender,
    UnavailableVerificationEmailSender,
    VerificationEmailSender,
)
from app.auth.service import AuthService, RedisSessionStore, SessionStore
from app.auth.users import PostgresUserStore, UserStore
from app.auth.verification import PostgresVerificationStore, VerificationStore
from app.cache import CacheStore, RedisCache
from app.config import Settings, get_settings
from app.context import ApplicationContext
from app.database import create_database_engine, create_session_factory
from app.generation.service import DemoGenerationService, GenerationService
from app.rate_limit import RateLimiter, RateLimitPolicy, RedisRateLimiter
from app.router import api_router


def create_app(
    settings: Settings | None = None,
    generation_service: GenerationService | None = None,
    session_store: SessionStore | None = None,
    user_store: UserStore | None = None,
    verification_store: VerificationStore | None = None,
    email_sender: VerificationEmailSender | None = None,
    cache: CacheStore | None = None,
    rate_limiter: RateLimiter | None = None,
    redis_client: Redis | None = None,
    database_engine: AsyncEngine | None = None,
) -> FastAPI:
    resolved_settings = settings if settings is not None else get_settings()
    resolved_service = (
        generation_service
        if generation_service is not None
        else DemoGenerationService(model=resolved_settings.llm_model)
    )
    needs_redis = session_store is None or cache is None or rate_limiter is None
    client = redis_client
    owns_redis_client = needs_redis and client is None
    if needs_redis and client is None:
        client = Redis.from_url(resolved_settings.redis_url, decode_responses=True)

    if session_store is None:
        assert client is not None
        session_store = RedisSessionStore(client, resolved_settings.redis_namespace)
    needs_database = user_store is None or verification_store is None
    engine = database_engine
    owns_database_engine = needs_database and engine is None
    if needs_database and engine is None:
        engine = create_database_engine(resolved_settings.database_url)
    if needs_database:
        assert engine is not None
        database_sessions = create_session_factory(engine)
        if user_store is None:
            user_store = PostgresUserStore(database_sessions)
        if verification_store is None:
            verification_store = PostgresVerificationStore(database_sessions)
    if email_sender is None:
        resend_key = resolved_settings.resend_api_key
        email_sender = (
            ResendVerificationEmailSender(
                resend_key.get_secret_value(),
                resolved_settings.resend_from_email,
            )
            if resend_key is not None
            else UnavailableVerificationEmailSender()
        )
    if cache is None:
        assert client is not None
        cache = RedisCache(client, resolved_settings.redis_namespace)
    if rate_limiter is None:
        assert client is not None
        rate_limiter = RedisRateLimiter(
            client,
            resolved_settings.redis_namespace,
            {
                "login": RateLimitPolicy(
                    resolved_settings.login_rate_limit_requests,
                    resolved_settings.login_rate_limit_window_seconds,
                ),
                "signup": RateLimitPolicy(
                    resolved_settings.signup_rate_limit_requests,
                    resolved_settings.signup_rate_limit_window_seconds,
                ),
                "generation": RateLimitPolicy(
                    resolved_settings.rate_limit_requests,
                    resolved_settings.rate_limit_window_seconds,
                ),
                "cache-flush": RateLimitPolicy(
                    resolved_settings.cache_flush_rate_limit_requests,
                    resolved_settings.cache_flush_rate_limit_window_seconds,
                ),
            },
        )

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        if owns_redis_client:
            assert client is not None
            await client.ping()
        if owns_database_engine:
            assert engine is not None
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        yield
        if owns_redis_client:
            assert client is not None
            await client.aclose()
        if owns_database_engine:
            assert engine is not None
            await engine.dispose()

    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        debug=resolved_settings.debug,
        description="HTTP API for text generation.",
        lifespan=lifespan,
    )
    application.state.context = ApplicationContext(
        settings=resolved_settings,
        auth=AuthService(
            resolved_settings,
            session_store,
            user_store,
            verification_store,
            email_sender,
        ),
        cache=cache,
        generation_service=resolved_service,
        rate_limiter=rate_limiter,
    )
    application.include_router(api_router)
    return application


app = create_app()
