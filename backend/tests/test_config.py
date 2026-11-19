import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def build_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {}
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_default_app_version_matches_project_metadata() -> None:
    project = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )["project"]

    assert build_settings().app_version == project["version"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rate_limit_requests", 0),
        ("rate_limit_window_seconds", 0),
    ],
)
def test_settings_require_positive_rate_limits(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        build_settings(**{field: value})


def test_production_rejects_demo_login() -> None:
    with pytest.raises(ValidationError, match="DEMO_LOGIN_ENABLED"):
        build_settings(environment="production")


def test_production_requires_resend_api_key() -> None:
    with pytest.raises(ValidationError, match="RESEND_API_KEY"):
        build_settings(environment="production", demo_login_enabled=False)
