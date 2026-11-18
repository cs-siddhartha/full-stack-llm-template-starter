import json
import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings

_AUTH_VECTORS = json.loads(
    (
        Path(__file__).resolve().parents[2] / "contracts/basic-auth-vectors.json"
    ).read_text(encoding="utf-8")
)["credentials"]


def build_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "basic_auth_username": "test-user",
        "basic_auth_password": "test-password",
    }
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
    ("username", "password"),
    [
        ("local", "production-password"),
        ("production-user", "local-development-only"),
    ],
)
def test_settings_reject_local_credentials_in_production(
    username: str,
    password: str,
) -> None:
    with pytest.raises(ValidationError, match="must be changed for production"):
        Settings(
            _env_file=None,
            environment="production",
            basic_auth_username=username,
            basic_auth_password=password,
        )


def test_settings_accept_explicit_production_credentials() -> None:
    settings = build_settings(
        environment="production",
        basic_auth_username="production-user",
        basic_auth_password="production-password",
    )

    assert settings.basic_auth_username == "production-user"
    assert settings.basic_auth_password.get_secret_value() == "production-password"


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


def test_settings_require_explicit_basic_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BASIC_AUTH_USERNAME", raising=False)
    monkeypatch.delenv("BASIC_AUTH_PASSWORD", raising=False)

    with pytest.raises(ValidationError, match="basic_auth"):
        Settings(_env_file=None)


@pytest.mark.parametrize("vector", _AUTH_VECTORS)
def test_basic_credentials_follow_shared_contract(vector: dict[str, object]) -> None:
    values = {
        "basic_auth_username": vector["username"],
        "basic_auth_password": vector["password"],
    }
    if vector["portable"]:
        settings = Settings(_env_file=None, **values)
        assert settings.basic_auth_username == vector["username"]
    else:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **values)


def test_settings_hide_invalid_password_from_validation_errors() -> None:
    invalid_password = "private-p\u00e4ssword"

    with pytest.raises(ValidationError) as captured_error:
        build_settings(basic_auth_password=invalid_password)

    assert invalid_password not in str(captured_error.value)
