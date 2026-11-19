import json
from pathlib import Path

from app.config import Settings
from tests.support import create_test_app

_OPENAPI_ARTIFACT = Path(__file__).resolve().parents[2] / "openapi.json"


def test_openapi_artifact_matches_application() -> None:
    """Fail when backend changes have not been propagated to generated clients."""
    settings = Settings(_env_file=None)
    expected_schema = create_test_app(settings).openapi()
    committed_schema = json.loads(_OPENAPI_ARTIFACT.read_text(encoding="utf-8"))

    assert committed_schema == expected_schema

    config_responses = expected_schema["paths"]["/api/v1/config"]["get"]["responses"]
    assert {"200", "401"} <= config_responses.keys()

    generation_responses = expected_schema["paths"]["/api/v1/generations"]["post"][
        "responses"
    ]
    assert {"201", "401", "422", "429"} <= generation_responses.keys()
    assert set(generation_responses["201"]["headers"]) == {
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    }
    assert set(generation_responses["429"]["headers"]) == {
        "Retry-After",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    }
