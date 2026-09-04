import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.rate_limit import InMemoryFixedWindowRateLimiter
from app.main import create_app


def test_health_returns_readiness_metadata(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "healthy",
        "service": "Test LLM API",
        "version": "9.9.9",
        "environment": "test",
    }


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/api/v1/config", None),
        ("POST", "/api/v1/generations", {"prompt": "Hello"}),
    ],
)
def test_protected_routes_reject_missing_auth(
    client: TestClient,
    method: str,
    path: str,
    payload: dict[str, str] | None,
) -> None:
    request_options = {"json": payload} if payload is not None else {}

    response = client.request(method, path, **request_options)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers["www-authenticate"] == "Basic"


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/api/v1/config", None),
        ("POST", "/api/v1/generations", {"prompt": "Hello"}),
    ],
)
def test_protected_routes_reject_incorrect_auth(
    client: TestClient,
    method: str,
    path: str,
    payload: dict[str, str] | None,
) -> None:
    request_options = {"json": payload} if payload is not None else {}

    response = client.request(
        method,
        path,
        auth=("test-user", "wrong-password"),
        **request_options,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect username or password"}
    assert response.headers["www-authenticate"] == "Basic"


def test_config_returns_only_safe_capabilities(
    client: TestClient,
    auth: tuple[str, str],
) -> None:
    response = client.get("/api/v1/config", auth=auth)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "service": "Test LLM API",
        "version": "9.9.9",
        "environment": "test",
        "api_base_path": "/api/v1",
        "generation_provider": "demo",
        "generation_model": "demo-v1",
        "rate_limit_requests": 10,
        "rate_limit_window_seconds": 60,
    }


def test_generation_is_deterministic_and_provider_neutral(
    client: TestClient,
    auth: tuple[str, str],
) -> None:
    payload = {
        "prompt": "Explain retrieval augmented generation.",
        "instructions": "Keep it concise.",
        "temperature": 0.3,
    }

    first_response = client.post("/api/v1/generations", json=payload, auth=auth)
    second_response = client.post("/api/v1/generations", json=payload, auth=auth)

    assert first_response.status_code == status.HTTP_201_CREATED
    assert first_response.json() == second_response.json()
    body = first_response.json()
    assert body["id"].startswith("gen_demo_")
    assert body["object"] == "generation"
    assert body["provider"] == "demo"
    assert body["model"] == "demo-v1"
    assert payload["prompt"] in body["output"]
    expected_input_characters = len(payload["prompt"]) + len(payload["instructions"])
    assert body["usage"]["input_characters"] == expected_input_characters
    assert body["usage"]["output_characters"] == len(body["output"])


def test_generation_rejects_blank_prompts(
    client: TestClient,
    auth: tuple[str, str],
) -> None:
    response = client.post(
        "/api/v1/generations",
        json={"prompt": "   "},
        auth=auth,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"][0]["loc"] == ["body", "prompt"]


def test_generation_rejects_unknown_fields(
    client: TestClient,
    auth: tuple[str, str],
) -> None:
    response = client.post(
        "/api/v1/generations",
        json={"prompt": "Hello", "api_key": "must-not-be-accepted"},
        auth=auth,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_generation_rate_limit_headers_and_window_reset(
    settings: Settings,
    auth: tuple[str, str],
) -> None:
    current_time = [100.0]
    limiter = InMemoryFixedWindowRateLimiter(
        limit=2,
        window_seconds=10,
        clock=lambda: current_time[0],
    )

    with TestClient(
        create_app(settings=settings, generation_rate_limiter=limiter)
    ) as client:
        first = client.post(
            "/api/v1/generations",
            json={"prompt": "First"},
            auth=auth,
        )
        second = client.post(
            "/api/v1/generations",
            json={"prompt": "Second"},
            auth=auth,
        )
        rejected = client.post(
            "/api/v1/generations",
            json={"prompt": "Third"},
            auth=auth,
        )

        assert first.status_code == status.HTTP_201_CREATED
        assert first.headers["x-ratelimit-limit"] == "2"
        assert first.headers["x-ratelimit-remaining"] == "1"
        assert first.headers["x-ratelimit-reset"] == "110"
        assert second.status_code == status.HTTP_201_CREATED
        assert second.headers["x-ratelimit-remaining"] == "0"
        assert rejected.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert rejected.json() == {"detail": "Rate limit exceeded"}
        assert rejected.headers["x-ratelimit-limit"] == "2"
        assert rejected.headers["x-ratelimit-remaining"] == "0"
        assert rejected.headers["x-ratelimit-reset"] == "110"
        assert rejected.headers["retry-after"] == "10"

        current_time[0] = 110.0
        after_reset = client.post(
            "/api/v1/generations",
            json={"prompt": "After reset"},
            auth=auth,
        )

        assert after_reset.status_code == status.HTTP_201_CREATED
        assert after_reset.headers["x-ratelimit-remaining"] == "1"
        assert after_reset.headers["x-ratelimit-reset"] == "120"


def test_cors_preflight_allows_configured_frontend(client: TestClient) -> None:
    response = client.options(
        "/api/v1/generations",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["access-control-allow-origin"] == ("http://localhost:3000")
    assert response.headers["access-control-allow-credentials"] == "true"
