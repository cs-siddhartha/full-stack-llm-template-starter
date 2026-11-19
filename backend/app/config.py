import tomllib
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_NAME = "reusable-llm-backend"


def _project_version() -> str:
    """Use installed metadata in deployments and pyproject metadata in source checkouts."""
    try:
        return version(_PROJECT_NAME)
    except PackageNotFoundError:
        project = tomllib.loads(
            (_BACKEND_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        return str(project["version"])


class Settings(BaseSettings):
    app_name: str = "LLM API"
    app_version: str = Field(default_factory=_project_version)
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://starter:starter@127.0.0.1:5433/starter"
    database_url_unpooled: str | None = None
    redis_url: str = "redis://127.0.0.1:6379/0"
    redis_namespace: str = Field(default="full-stack-starter", min_length=1)
    demo_login_enabled: bool = True
    resend_api_key: SecretStr | None = None
    resend_from_email: str = "Starter <onboarding@resend.dev>"
    frontend_url: str = "http://localhost:3000"
    backend_public_url: str = "http://localhost:8000"
    email_verification_ttl_seconds: int = Field(default=3_600, gt=0)
    session_cookie_name: str = Field(
        default="starter_session",
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    session_ttl_seconds: int = Field(default=86_400, gt=0)
    login_rate_limit_requests: int = Field(default=5, gt=0)
    login_rate_limit_window_seconds: int = Field(default=60, gt=0)
    signup_rate_limit_requests: int = Field(default=3, gt=0)
    signup_rate_limit_window_seconds: int = Field(default=300, gt=0)
    rate_limit_requests: int = Field(default=10, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)
    cache_flush_rate_limit_requests: int = Field(default=3, gt=0)
    cache_flush_rate_limit_window_seconds: int = Field(default=60, gt=0)
    config_cache_ttl_seconds: int = Field(default=30, gt=0)
    llm_model: str = "demo-v1"

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def reject_local_credentials_in_production(self) -> "Settings":
        if self.environment == "production":
            if self.demo_login_enabled:
                raise ValueError("DEMO_LOGIN_ENABLED must be false in production")
            if self.resend_api_key is None:
                raise ValueError("RESEND_API_KEY is required in production")
        return self

    @property
    def session_cookie_secure(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Share one validated environment snapshot across the process."""
    return Settings()
