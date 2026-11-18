import tomllib
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_NAME = "reusable-llm-backend"
_LOCAL_AUTH_USERNAME = "local"
_LOCAL_AUTH_PASSWORD = "local-development-only"


def _project_version() -> str:
    """Use installed metadata in deployments and pyproject metadata in source checkouts."""
    try:
        return version(_PROJECT_NAME)
    except PackageNotFoundError:
        project = tomllib.loads(
            (_BACKEND_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        return str(project["version"])


def _require_printable_ascii(value: str, setting_name: str) -> None:
    """Keep credentials compatible with HTTP Basic decoders in both runtimes."""
    if not value.isascii() or not value.isprintable():
        raise ValueError(f"{setting_name} must contain only printable ASCII characters")


class Settings(BaseSettings):
    app_name: str = "Reusable LLM API"
    app_version: str = Field(default_factory=_project_version)
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    basic_auth_username: str = Field(min_length=1)
    basic_auth_password: SecretStr = Field(min_length=1)
    rate_limit_requests: int = Field(default=10, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)
    llm_model: str = "demo-v1"

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        hide_input_in_errors=True,
    )

    @field_validator("basic_auth_username")
    @classmethod
    def validate_basic_auth_username(cls, value: str) -> str:
        _require_printable_ascii(value, "BASIC_AUTH_USERNAME")
        if ":" in value:
            raise ValueError("BASIC_AUTH_USERNAME must not contain ':'")
        return value

    @field_validator("basic_auth_password")
    @classmethod
    def validate_basic_auth_password(cls, value: SecretStr) -> SecretStr:
        _require_printable_ascii(value.get_secret_value(), "BASIC_AUTH_PASSWORD")
        return value

    @model_validator(mode="after")
    def require_production_auth_credentials(self) -> "Settings":
        """Prevent production from starting with either documented local credential."""
        uses_local_username = self.basic_auth_username == _LOCAL_AUTH_USERNAME
        uses_local_password = (
            self.basic_auth_password.get_secret_value() == _LOCAL_AUTH_PASSWORD
        )
        if self.environment == "production" and (
            uses_local_username or uses_local_password
        ):
            raise ValueError(
                "BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD must be changed "
                "for production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Share one validated environment snapshot across the process."""
    return Settings()
