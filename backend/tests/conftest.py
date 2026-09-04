from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_name="Test LLM API",
        app_version="9.9.9",
        environment="test",
        cors_origins=["http://localhost:3000"],
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
def auth() -> tuple[str, str]:
    return ("test-user", "test-password")
