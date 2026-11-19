from dataclasses import dataclass
from typing import cast

from fastapi import Request

from app.auth.service import AuthService
from app.cache import CacheStore
from app.config import Settings
from app.generation.service import GenerationService
from app.rate_limit import RateLimiter


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Keep app-scoped dependencies typed and capability reporting truthful."""

    settings: Settings
    auth: AuthService
    cache: CacheStore
    generation_service: GenerationService
    rate_limiter: RateLimiter


def get_context(request: Request) -> ApplicationContext:
    return cast(ApplicationContext, request.app.state.context)
