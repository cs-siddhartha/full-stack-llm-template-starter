from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from tests.support import create_test_app, login


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_name="Test LLM API",
        app_version="9.9.9",
        environment="test",
        rate_limit_requests=10,
        rate_limit_window_seconds=60,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_test_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_test_app(settings)) as test_client:
        login(test_client, settings)
        yield test_client
