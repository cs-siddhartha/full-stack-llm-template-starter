from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_name="Test LLM API",
        app_version="9.9.9",
        environment="test",
        basic_auth_username="test-user",
        basic_auth_password="test-password",
        rate_limit_requests=10,
        rate_limit_window_seconds=60,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings=settings)) as test_client:
        yield test_client


@pytest.fixture
def auth(settings: Settings) -> tuple[str, str]:
    return (
        settings.basic_auth_username,
        settings.basic_auth_password.get_secret_value(),
    )
