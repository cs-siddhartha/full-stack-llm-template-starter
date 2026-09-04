import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import Settings
from app.core.rate_limit import InMemoryFixedWindowRateLimiter, RateLimitDecision
from app.services.generation import GenerationService

basic_auth = HTTPBasic()


def get_request_settings(request: Request) -> Settings:
    """Read the validated app-scoped settings used to create this server."""
    return request.app.state.settings


def get_generation_service(request: Request) -> GenerationService:
    """Resolve the app-scoped provider without coupling routes to its SDK."""
    return request.app.state.generation_service


def get_generation_rate_limiter(request: Request) -> InMemoryFixedWindowRateLimiter:
    """Resolve the app-scoped limiter so tests and deployments can replace it."""
    return request.app.state.generation_rate_limiter


def require_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(basic_auth)],
    settings: Annotated[Settings, Depends(get_request_settings)],
) -> str:
    """Authenticate configured credentials without leaking comparison timing."""
    supplied_username = credentials.username.encode("utf-8")
    configured_username = settings.basic_auth_username.encode("utf-8")
    supplied_password = credentials.password.encode("utf-8")
    configured_password = settings.basic_auth_password.get_secret_value().encode(
        "utf-8"
    )

    username_matches = secrets.compare_digest(
        supplied_username,
        configured_username,
    )
    password_matches = secrets.compare_digest(
        supplied_password,
        configured_password,
    )
    if not (username_matches and password_matches):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


async def enforce_generation_rate_limit(
    username: Annotated[str, Depends(require_basic_auth)],
    limiter: Annotated[
        InMemoryFixedWindowRateLimiter,
        Depends(get_generation_rate_limiter),
    ],
) -> RateLimitDecision:
    """Consume per-user generation capacity before invoking an LLM provider."""
    decision = await limiter.consume(username)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers=decision.as_headers(),
        )
    return decision
