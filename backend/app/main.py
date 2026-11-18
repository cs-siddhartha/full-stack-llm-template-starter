from fastapi import FastAPI

from app.config import Settings, get_settings
from app.context import ApplicationContext
from app.generation.rate_limit import (
    GenerationRateLimiter,
    InMemoryFixedWindowRateLimiter,
)
from app.generation.service import DemoGenerationService, GenerationService
from app.router import api_router


def create_app(
    settings: Settings | None = None,
    generation_service: GenerationService | None = None,
    generation_rate_limiter: GenerationRateLimiter | None = None,
) -> FastAPI:
    resolved_settings = settings if settings is not None else get_settings()
    resolved_service = (
        generation_service
        if generation_service is not None
        else DemoGenerationService(model=resolved_settings.llm_model)
    )
    resolved_rate_limiter = (
        generation_rate_limiter
        if generation_rate_limiter is not None
        else InMemoryFixedWindowRateLimiter(
            limit=resolved_settings.rate_limit_requests,
            window_seconds=resolved_settings.rate_limit_window_seconds,
        )
    )

    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        debug=resolved_settings.debug,
        description="A reusable, provider-neutral API for LLM applications.",
    )
    application.state.context = ApplicationContext(
        settings=resolved_settings,
        generation_service=resolved_service,
        generation_limiter=resolved_rate_limiter,
    )
    application.include_router(api_router)
    return application
