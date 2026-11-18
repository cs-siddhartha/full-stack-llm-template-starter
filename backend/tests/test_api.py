from dataclasses import dataclass, field

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import Settings
from app.generation.models import GenerationCreate, GenerationRead, GenerationUsage
from app.generation.rate_limit import InMemoryFixedWindowRateLimiter
from app.main import create_app


@dataclass
class RecordingGenerationService:
    """Expose received requests so route tests can stay provider-independent."""

    provider: str = "recording"
    model: str = "recording-v1"
    requests: list[GenerationCreate] = field(default_factory=list)

    async def generate(self, request: GenerationCreate) -> GenerationRead:
        self.requests.append(request)
        return GenerationRead(
            id="gen_recorded",
            provider=self.provider,
            model=self.model,
            output="Recorded response",
            usage=GenerationUsage(input_characters=7, output_characters=17),
        )


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


def test_config_describes_injected_runtime(
    settings: Settings,
    auth: tuple[str, str],
) -> None:
    service = RecordingGenerationService(provider="custom", model="custom-v2")
    limiter = InMemoryFixedWindowRateLimiter(limit=2, window_seconds=15)

    with TestClient(
        create_app(
            settings=settings,
            generation_service=service,
            generation_rate_limiter=limiter,
        )
    ) as client:
        response = client.get("/api/v1/config", auth=auth)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "generation_provider": "custom",
        "generation_model": "custom-v2",
        "rate_limit_requests": 2,
        "rate_limit_window_seconds": 15,
    }


def test_generation_validates_and_delegates_to_provider(
    settings: Settings,
    auth: tuple[str, str],
) -> None:
    service = RecordingGenerationService()
    payload = {
        "prompt": "  Explain retrieval augmented generation.  ",
        "instructions": "  Keep it concise.  ",
        "temperature": 0.3,
    }

    with TestClient(
        create_app(settings=settings, generation_service=service)
    ) as client:
        response = client.post("/api/v1/generations", json=payload, auth=auth)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "id": "gen_recorded",
        "provider": "recording",
        "model": "recording-v1",
        "output": "Recorded response",
        "usage": {"input_characters": 7, "output_characters": 17},
    }
    assert service.requests == [
        GenerationCreate(
            prompt="Explain retrieval augmented generation.",
            instructions="Keep it concise.",
            temperature=0.3,
        )
    ]


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


def test_invalid_generation_does_not_consume_rate_limit_capacity(
    settings: Settings,
    auth: tuple[str, str],
) -> None:
    limiter = InMemoryFixedWindowRateLimiter(limit=1, window_seconds=60)

    with TestClient(
        create_app(settings=settings, generation_rate_limiter=limiter)
    ) as client:
        invalid = client.post(
            "/api/v1/generations",
            json={"prompt": "   "},
            auth=auth,
        )
        valid = client.post(
            "/api/v1/generations",
            json={"prompt": "Valid"},
            auth=auth,
        )

    assert invalid.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert valid.status_code == status.HTTP_201_CREATED
    assert valid.headers["x-ratelimit-remaining"] == "0"


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
