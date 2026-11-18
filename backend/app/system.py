from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.auth import require_basic_auth
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
def read_config(
    context: Annotated[ApplicationContext, Depends(get_context)],
    _username: Annotated[str, Depends(require_basic_auth)],
) -> ConfigRead:
    service = context.generation_service
    limiter = context.generation_limiter
    return ConfigRead(
        generation_provider=service.provider,
        generation_model=service.model,
        rate_limit_requests=limiter.limit,
        rate_limit_window_seconds=limiter.window_seconds,
    )
