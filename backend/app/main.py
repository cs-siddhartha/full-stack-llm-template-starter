from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.rate_limit import InMemoryFixedWindowRateLimiter
from app.services.generation import GenerationService, build_generation_service


def create_app(
    settings: Settings | None = None,
    generation_service: GenerationService | None = None,
    generation_rate_limiter: InMemoryFixedWindowRateLimiter | None = None,
) -> FastAPI:
    """Build an independently configurable app for production and isolated tests."""
    resolved_settings = settings or get_settings()
    resolved_service = generation_service or build_generation_service(resolved_settings)
    resolved_rate_limiter = generation_rate_limiter or InMemoryFixedWindowRateLimiter(
        limit=resolved_settings.rate_limit_requests,
        window_seconds=resolved_settings.rate_limit_window_seconds,
    )

    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        debug=resolved_settings.debug,
        description="A reusable, provider-neutral API for LLM applications.",
    )
    application.state.settings = resolved_settings
    application.state.generation_service = resolved_service
    application.state.generation_rate_limiter = resolved_rate_limiter
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=resolved_settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
        max_age=600,
    )
    application.include_router(
        api_router,
        prefix=resolved_settings.api_v1_prefix,
    )
    return application
