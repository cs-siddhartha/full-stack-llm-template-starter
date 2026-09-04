import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, TypeAdapter, field_validator, model_validator
from pydantic.networks import AnyHttpUrl
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_HTTP_URL_ADAPTER = TypeAdapter(AnyHttpUrl)
_LOCAL_AUTH_USERNAME = "local"
_LOCAL_AUTH_PASSWORD = "local-development-only"


def _require_printable_ascii(value: str, setting_name: str) -> None:
    """Keep configured credentials compatible across HTTP Basic decoders."""
    if not value.isascii() or not value.isprintable():
        raise ValueError(f"{setting_name} must contain only printable ASCII characters")


class Settings(BaseSettings):
    """Validate environment configuration once before it reaches the app."""

    app_name: str = "Reusable LLM API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    cors_allow_credentials: bool = True
    basic_auth_username: str = Field(min_length=1)
    basic_auth_password: SecretStr = Field(min_length=1)
    rate_limit_requests: int = Field(default=10, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)
    llm_provider: Literal["demo"] = "demo"
    llm_model: str = "demo-v1"

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        hide_input_in_errors=True,
    )

    @field_validator("api_v1_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        """Keep route composition predictable for configured API prefixes."""
        normalized = value.strip()
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        return normalized.rstrip("/")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Support both convenient CSV and standard JSON environment values."""
        if not isinstance(value, str):
            return value

        raw_value = value.strip()
        if raw_value.startswith("["):
            try:
                return json.loads(raw_value)
            except json.JSONDecodeError as error:
                raise ValueError("CORS_ORIGINS must contain valid JSON") from error

        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, origins: list[str]) -> list[str]:
        """Reject malformed origins before Starlette builds CORS headers."""
        normalized_origins: list[str] = []
        for origin in origins:
            if origin == "*":
                normalized_origins.append(origin)
                continue

            parsed_origin = _HTTP_URL_ADAPTER.validate_python(origin)
            if (
                parsed_origin.path not in (None, "/")
                or parsed_origin.query is not None
                or parsed_origin.fragment is not None
                or parsed_origin.username is not None
                or parsed_origin.password is not None
            ):
                raise ValueError(f"CORS origin must not include a path: {origin}")
            normalized_origins.append(str(parsed_origin).rstrip("/"))

        if not normalized_origins:
            raise ValueError("CORS_ORIGINS must include at least one origin")
        return normalized_origins

    @field_validator("basic_auth_username")
    @classmethod
    def validate_basic_auth_username(cls, value: str) -> str:
        """Reject usernames that cannot round-trip through HTTP Basic syntax."""
        _require_printable_ascii(value, "BASIC_AUTH_USERNAME")
        if ":" in value:
            raise ValueError("BASIC_AUTH_USERNAME must not contain ':'")
        return value

    @field_validator("basic_auth_password")
    @classmethod
    def validate_basic_auth_password(cls, value: SecretStr) -> SecretStr:
        """Reject passwords that FastAPI's HTTP Basic decoder cannot accept."""
        _require_printable_ascii(
            value.get_secret_value(),
            "BASIC_AUTH_PASSWORD",
        )
        return value

    @model_validator(mode="after")
    def prevent_credentialed_wildcard_cors(self) -> "Settings":
        """Avoid an invalid and unsafe wildcard-plus-credentials policy."""
        if self.cors_allow_credentials and "*" in self.cors_origins:
            raise ValueError(
                "CORS_ALLOW_CREDENTIALS must be false when CORS_ORIGINS is '*'"
            )
        return self

    @model_validator(mode="after")
    def require_production_auth_credentials(self) -> "Settings":
        """Prevent deployment with credentials intended only for local setup."""
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
    """Reuse the immutable process configuration across request dependencies."""
    return Settings()
