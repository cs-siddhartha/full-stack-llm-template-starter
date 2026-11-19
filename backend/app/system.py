from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.auth.dependencies import require_session
from app.auth.service import CurrentSession
from app.context import ApplicationContext, get_context
from app.http import ApiError

router = APIRouter(tags=["system"])


class HealthRead(BaseModel):
    status: Literal["healthy"] = "healthy"
    service: str
    version: str
    environment: str

    model_config = ConfigDict(frozen=True)


class ConfigRead(BaseModel):
    generation_provider: str
    generation_model: str
    rate_limit_requests: int
    rate_limit_window_seconds: int

    model_config = ConfigDict(frozen=True)


@router.get("/health", response_model=HealthRead, summary="Read service health")
def read_health(
    context: Annotated[ApplicationContext, Depends(get_context)],
) -> HealthRead:
    settings = context.settings
    return HealthRead(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/config",
    response_model=ConfigRead,
    summary="Read runtime capabilities",
    responses={
        401: {
            "model": ApiError,
            "description": "Authentication required",
        }
    },
)
async def read_config(
    context: Annotated[ApplicationContext, Depends(get_context)],
    _session: Annotated[CurrentSession, Depends(require_session)],
) -> ConfigRead:
    cached = await context.cache.get_json("runtime-config")
    if cached is not None:
        return ConfigRead.model_validate(cached)

    service = context.generation_service
    policy = context.rate_limiter.policy("generation")
    config = ConfigRead(
        generation_provider=service.provider,
        generation_model=service.model,
        rate_limit_requests=policy.limit,
        rate_limit_window_seconds=policy.window_seconds,
    )
    await context.cache.set_json(
        "runtime-config",
        config.model_dump(),
        context.settings.config_cache_ttl_seconds,
    )
    return config
