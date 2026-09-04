import pytest
from pydantic import ValidationError

from app.core.config import Settings


def build_settings(**overrides: object) -> Settings:
    """Supply valid test credentials while isolating each settings assertion."""
    values: dict[str, object] = {
        "basic_auth_username": "test-user",
        "basic_auth_password": "test-password",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_settings_parse_comma_separated_cors_origins() -> None:
    settings = build_settings(
        cors_origins="http://localhost:3000,https://app.example.com",
    )

    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://app.example.com",
    ]


def test_settings_parse_json_cors_origins() -> None:
    settings = build_settings(
        cors_origins='["http://localhost:3000", "https://app.example.com"]',
    )

    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://app.example.com",
    ]


def test_settings_reject_credentialed_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="CORS_ALLOW_CREDENTIALS"):
        build_settings(cors_origins="*")


def test_settings_allow_wildcard_without_credentials() -> None:
    settings = build_settings(
        cors_origins="*",
        cors_allow_credentials=False,
    )

    assert settings.cors_origins == ["*"]


def test_settings_normalize_api_prefix() -> None:
    settings = build_settings(api_v1_prefix="custom/v1/")

    assert settings.api_v1_prefix == "/custom/v1"


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


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("basic_auth_username", "user:name", "must not contain"),
        ("basic_auth_username", "t\u00e9st", "printable ASCII"),
        ("basic_auth_password", "p\u00e4ss", "printable ASCII"),
        ("basic_auth_password", "line\nbreak", "printable ASCII"),
    ],
)
def test_settings_reject_incompatible_basic_credentials(
    field: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        build_settings(**{field: value})


def test_settings_hide_invalid_password_from_validation_errors() -> None:
    invalid_password = "private-p\u00e4ssword"

    with pytest.raises(ValidationError) as captured_error:
        build_settings(basic_auth_password=invalid_password)

    assert invalid_password not in str(captured_error.value)
