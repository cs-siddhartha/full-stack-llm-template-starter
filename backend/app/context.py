from dataclasses import dataclass
from typing import cast

from fastapi import Request

from app.config import Settings
from app.generation.rate_limit import GenerationRateLimiter
from app.generation.service import GenerationService


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Keep app-scoped dependencies typed and capability reporting truthful."""

    settings: Settings
    generation_service: GenerationService
    generation_limiter: GenerationRateLimiter


def get_context(request: Request) -> ApplicationContext:
    return cast(ApplicationContext, request.app.state.context)
