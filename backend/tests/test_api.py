from dataclasses import dataclass, field
from urllib.parse import urlsplit

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.email import RecordingVerificationEmailSender
from app.auth.users import InMemoryUserStore
from app.auth.verification import InMemoryVerificationStore
from app.cache import InMemoryCache
from app.config import Settings
from app.generation.models import GenerationCreate, GenerationRead, GenerationUsage
from app.rate_limit import InMemoryRateLimiter, RateLimitPolicy
from tests.support import create_test_app, login, policies


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
        ("POST", "/api/v1/cache/flush", None),
    ],
)
def test_protected_routes_require_a_session(
    client: TestClient,
    method: str,
    path: str,
    payload: dict[str, str] | None,
) -> None:
    response = client.request(method, path, json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_demo_session_and_logout(client: TestClient) -> None:
    login_response = client.post("/api/v1/auth/demo")

    assert login_response.status_code == status.HTTP_200_OK
    assert login_response.json() == {
        "user_id": "demo:local",
        "username": "demo",
        "role": "demo",
    }
    cookie = login_response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie
    assert client.get("/api/v1/auth/session").status_code == status.HTTP_200_OK
    assert client.post("/api/v1/auth/logout").status_code == status.HTTP_204_NO_CONTENT
    assert (
        client.get("/api/v1/auth/session").status_code == status.HTTP_401_UNAUTHORIZED
    )


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "missing@example.com", "password": "incorrect-password"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_signup_requires_email_confirmation_before_login(settings: Settings) -> None:
    users = InMemoryUserStore()
    verifications = InMemoryVerificationStore()
    sender = RecordingVerificationEmailSender()

    with TestClient(
        create_test_app(
            settings,
            user_store=users,
            verification_store=verifications,
            email_sender=sender,
        )
    ) as client:
        signup = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "person@example.com",
                "password": "correct-horse-battery-staple",
            },
        )
        before_confirmation = client.post(
            "/api/v1/auth/login",
            json={
                "username": "person@example.com",
                "password": "correct-horse-battery-staple",
            },
        )
        verification_path = urlsplit(sender.deliveries[0][1]).path
        verification_query = urlsplit(sender.deliveries[0][1]).query
        confirmation = client.get(
            f"{verification_path}?{verification_query}",
            follow_redirects=False,
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "person@example.com",
                "password": "correct-horse-battery-staple",
            },
        )

    assert signup.status_code == status.HTTP_201_CREATED
    assert signup.json() == {"message": "Check your email to confirm your account"}
    assert sender.deliveries[0][0] == "person@example.com"
    assert before_confirmation.status_code == status.HTTP_403_FORBIDDEN
    assert confirmation.status_code == status.HTTP_303_SEE_OTHER
    assert confirmation.headers["location"].endswith("/login?verification=verified")
    assert login_response.status_code == status.HTTP_200_OK
    assert login_response.json()["username"] == "person@example.com"


def test_signup_rejects_duplicate_email(settings: Settings) -> None:
    users = InMemoryUserStore()
    sender = RecordingVerificationEmailSender()
    app = create_test_app(settings, user_store=users, email_sender=sender)
    payload = {
        "email": "person@example.com",
        "password": "correct-horse-battery-staple",
    }

    with TestClient(app) as client:
        first = client.post("/api/v1/auth/signup", json=payload)
        duplicate = client.post("/api/v1/auth/signup", json=payload)

    assert first.status_code == status.HTTP_201_CREATED
    assert duplicate.status_code == status.HTTP_409_CONFLICT


def test_login_rate_limit_uses_endpoint_decorator(settings: Settings) -> None:
    test_policies = policies(settings)
    test_policies["login"] = RateLimitPolicy(1, 60)

    with TestClient(
        create_test_app(
            settings,
            rate_limiter=InMemoryRateLimiter(test_policies),
        )
    ) as client:
        first = client.post(
            "/api/v1/auth/login",
            json={"username": "missing@example.com", "password": "incorrect-password"},
        )
        second = client.post(
            "/api/v1/auth/login",
            json={"username": "missing@example.com", "password": "incorrect-password"},
        )

    assert first.status_code == status.HTTP_401_UNAUTHORIZED
    assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_config_is_cached_and_flushable(settings: Settings) -> None:
    cache = InMemoryCache()
    service = RecordingGenerationService(provider="custom", model="custom-v2")
    custom_policies = policies(settings)
    custom_policies["generation"] = RateLimitPolicy(2, 15)

    with TestClient(
        create_test_app(
            settings,
            generation_service=service,
            cache=cache,
            rate_limiter=InMemoryRateLimiter(custom_policies),
        )
    ) as client:
        login(client, settings)
        config = client.get("/api/v1/config")
        flushed = client.post("/api/v1/cache/flush")

    assert config.status_code == status.HTTP_200_OK
    assert config.json() == {
        "generation_provider": "custom",
        "generation_model": "custom-v2",
        "rate_limit_requests": 2,
        "rate_limit_window_seconds": 15,
    }
    assert flushed.json() == {"deleted_keys": 1}


def test_generation_validates_and_delegates_to_provider(settings: Settings) -> None:
    service = RecordingGenerationService()
    payload = {
        "prompt": "  Explain retrieval augmented generation.  ",
        "instructions": "  Keep it concise.  ",
        "temperature": 0.3,
    }

    with TestClient(create_test_app(settings, generation_service=service)) as client:
        login(client, settings)
        response = client.post("/api/v1/generations", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert service.requests == [
        GenerationCreate(
            prompt="Explain retrieval augmented generation.",
            instructions="Keep it concise.",
            temperature=0.3,
        )
    ]


def test_generation_rejects_invalid_payloads(
    authenticated_client: TestClient,
) -> None:
    blank = authenticated_client.post(
        "/api/v1/generations",
        json={"prompt": "   "},
    )
    unknown = authenticated_client.post(
        "/api/v1/generations",
        json={"prompt": "Hello", "api_key": "must-not-be-accepted"},
    )

    assert blank.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert unknown.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_invalid_generation_does_not_consume_capacity(settings: Settings) -> None:
    test_policies = policies(settings)
    test_policies["generation"] = RateLimitPolicy(1, 60)
    limiter = InMemoryRateLimiter(test_policies)

    with TestClient(create_test_app(settings, rate_limiter=limiter)) as client:
        login(client, settings)
        invalid = client.post("/api/v1/generations", json={"prompt": "   "})
        valid = client.post("/api/v1/generations", json={"prompt": "Valid"})

    assert invalid.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert valid.status_code == status.HTTP_201_CREATED
    assert valid.headers["x-ratelimit-remaining"] == "0"


def test_generation_rate_limit_headers_and_window_reset(settings: Settings) -> None:
    current_time = [100.0]
    test_policies = policies(settings)
    test_policies["generation"] = RateLimitPolicy(2, 10)
    limiter = InMemoryRateLimiter(test_policies, clock=lambda: current_time[0])

    with TestClient(create_test_app(settings, rate_limiter=limiter)) as client:
        login(client, settings)
        first = client.post("/api/v1/generations", json={"prompt": "First"})
        second = client.post("/api/v1/generations", json={"prompt": "Second"})
        rejected = client.post("/api/v1/generations", json={"prompt": "Third"})

        assert first.headers["x-ratelimit-remaining"] == "1"
        assert second.headers["x-ratelimit-remaining"] == "0"
        assert rejected.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert rejected.headers["retry-after"] == "10"

        current_time[0] = 110.0
        after_reset = client.post(
            "/api/v1/generations",
            json={"prompt": "After reset"},
        )

    assert after_reset.status_code == status.HTTP_201_CREATED
    assert after_reset.headers["x-ratelimit-remaining"] == "1"
