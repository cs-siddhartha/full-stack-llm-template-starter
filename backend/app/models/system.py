from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthRead(BaseModel):
    """Describe service readiness without exposing private configuration."""

    status: Literal["healthy"] = "healthy"
    service: str
    version: str
    environment: str

    model_config = ConfigDict(frozen=True)


class ConfigRead(BaseModel):
    """Publish only configuration that server-rendered clients may safely use."""

    service: str
    version: str
    environment: str
    api_base_path: str
    generation_provider: str
    generation_model: str
    rate_limit_requests: int
    rate_limit_window_seconds: int

    model_config = ConfigDict(frozen=True)
