# Reusable LLM Backend

A small FastAPI service intended to sit behind a server-first web application. It
ships with a deterministic demo generation provider, so the full stack works
without API keys. Replace the provider implementation when connecting a real LLM.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Python 3.12 or newer (uv can install it automatically)

## Setup

```bash
cd backend
cp .env.example .env
uv sync
```

Start the development server:

```bash
uv run uvicorn app.main:create_app --factory --reload
```

The API is available at `http://localhost:8000`. Interactive documentation is at
`http://localhost:8000/docs`.

## API

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Public | Report service readiness and version. |
| `GET` | `/api/v1/config` | Basic Auth | Return frontend-safe provider and limit configuration. |
| `POST` | `/api/v1/generations` | Basic Auth + rate limit | Create a deterministic demo generation. |

Example generation request:

```bash
curl --request POST http://localhost:8000/api/v1/generations \
  --user 'local:local-development-only' \
  --header 'Content-Type: application/json' \
  --data '{"prompt":"Explain retrieval-augmented generation simply."}'
```

Missing or invalid credentials return `401 Unauthorized`. Generation responses
include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
Exhausted windows return `429 Too Many Requests` with `Retry-After`.

## Quality checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Copy `.env.example` to `.env` for local overrides. `CORS_ORIGINS` accepts either a
comma-separated list or a JSON array. Keep explicit origins when credentials are
enabled; wildcard origins are intentionally rejected in that configuration.

Both Basic Auth settings are required. The local example values are also
rejected when `ENVIRONMENT` is `production`. Set strong
`BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` values, use the same values in
the Next.js server environment, and serve Basic Auth only over HTTPS outside
local development.

`RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` control a per-username
fixed window. The included limiter is process-local: every worker or replica has
independent counters. Replace it with shared storage or an API gateway before a
multi-process deployment.

## Connecting a real LLM

Implement `GenerationService` in `app/services/generation.py`, add the provider's
settings, and select the implementation in `build_generation_service`. The API
route depends only on that abstraction, so request handling does not need to
change.

HTTP Basic is a starter boundary with one shared credential, not a full user
system. Before using a paid provider with real users, adopt an identity/session
provider and a distributed rate limiter. Keep this API on a private network when
possible. CORS does not prevent non-browser callers from reaching it.
