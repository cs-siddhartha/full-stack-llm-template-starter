from fastapi import FastAPI

from app.auth.email import RecordingVerificationEmailSender, VerificationEmailSender
from app.auth.service import InMemorySessionStore
from app.auth.users import InMemoryUserStore, UserStore
from app.auth.verification import InMemoryVerificationStore, VerificationStore
from app.cache import CacheStore, InMemoryCache
from app.config import Settings
from app.generation.service import GenerationService
from app.main import create_app
from app.rate_limit import InMemoryRateLimiter, RateLimiter, RateLimitPolicy


def policies(settings: Settings) -> dict[str, RateLimitPolicy]:
    return {
        "login": RateLimitPolicy(
            settings.login_rate_limit_requests,
            settings.login_rate_limit_window_seconds,
        ),
        "signup": RateLimitPolicy(
            settings.signup_rate_limit_requests,
            settings.signup_rate_limit_window_seconds,
        ),
        "generation": RateLimitPolicy(
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        ),
        "cache-flush": RateLimitPolicy(
            settings.cache_flush_rate_limit_requests,
            settings.cache_flush_rate_limit_window_seconds,
        ),
    }


def create_test_app(
    settings: Settings,
    *,
    generation_service: GenerationService | None = None,
    cache: CacheStore | None = None,
    rate_limiter: RateLimiter | None = None,
    user_store: UserStore | None = None,
    verification_store: VerificationStore | None = None,
    email_sender: VerificationEmailSender | None = None,
) -> FastAPI:
    return create_app(
        settings=settings,
        generation_service=generation_service,
        session_store=InMemorySessionStore(),
        user_store=user_store or InMemoryUserStore(),
        verification_store=verification_store or InMemoryVerificationStore(),
        email_sender=email_sender or RecordingVerificationEmailSender(),
        cache=cache or InMemoryCache(),
        rate_limiter=rate_limiter or InMemoryRateLimiter(policies(settings)),
    )


def login(client, settings: Settings) -> None:
    response = client.post("/api/v1/auth/demo")
    assert response.status_code == 200
