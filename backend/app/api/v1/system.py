from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_request_settings, require_basic_auth
from app.core.config import Settings
from app.models.system import ConfigRead, HealthRead

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthRead, summary="Read service health")
def read_health(
    settings: Annotated[Settings, Depends(get_request_settings)],
) -> HealthRead:
    """Expose a cheap readiness response for clients and infrastructure probes."""
    return HealthRead(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/config", response_model=ConfigRead, summary="Read public configuration")
def read_config(
    settings: Annotated[Settings, Depends(get_request_settings)],
    _username: Annotated[str, Depends(require_basic_auth)],
) -> ConfigRead:
    """Give clients safe capability metadata without returning secrets."""
    return ConfigRead(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        api_base_path=settings.api_v1_prefix,
        generation_provider=settings.llm_provider,
        generation_model=settings.llm_model,
        rate_limit_requests=settings.rate_limit_requests,
        rate_limit_window_seconds=settings.rate_limit_window_seconds,
    )
