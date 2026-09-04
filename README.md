# Reusable Full-Stack LLM Template

A small, production-shaped starting point for server-rendered LLM applications.
The frontend owns the browser experience and talks to the FastAPI service from
the Next.js server. The backend validates configuration and request data with
Pydantic, while a deterministic demo provider keeps local development keyless.

## Architecture

```text
Browser
  -> HTTP Basic gate in Next.js Proxy (`frontend/`)
      -> authenticated server components and server actions
          -> protected FastAPI JSON API (`backend/`)
              -> per-user generation rate limiter
                  -> replaceable generation provider
```

- `frontend/` contains the Next.js application and its shadcn/ui components.
- `backend/` contains the versioned FastAPI API, Pydantic models and settings,
  and provider-neutral generation service.
- The backend URL is server-only. Browsers call the Next.js application, not
  the FastAPI service directly, so provider credentials never enter the client
  bundle.
- The same HTTP Basic header is verified by Next.js and FastAPI. It is forwarded
  only in server-to-server requests.

## Prerequisites

- Node.js 20.9 or newer and npm
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

## Backend

Create local configuration, install the locked dependency set, and start the
development server:

```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:create_app --factory --reload
```

The API runs at `http://localhost:8000`; interactive OpenAPI documentation is
available at `http://localhost:8000/docs`. Defaults work without an API key.
Edit `backend/.env` when you need local overrides. In particular:

- `API_V1_PREFIX` controls the versioned API prefix.
- `CORS_ORIGINS` accepts a comma-separated list or JSON array.
- `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` protect API resources.
- `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` configure the
  generation limit.
- `LLM_PROVIDER` and `LLM_MODEL` select the generation implementation.

## Frontend

Install dependencies, create the server-only environment file, and start the
Next.js development server:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`. `BACKEND_URL` defaults to
`http://127.0.0.1:8000` and `BACKEND_API_PREFIX` defaults to `/api/v1` in the
example file. Both are intentionally free of the `NEXT_PUBLIC_` prefix: they
must remain available only to the Next.js server. If you change
`API_V1_PREFIX` in the backend, set `BACKEND_API_PREFIX` to the same value. Run
the backend at the same time in a second terminal.

The browser will show its native Basic Auth prompt. The local example uses
username `local` and password `local-development-only`. Set the same
`BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` values in `backend/.env` and
`frontend/.env.local`; both settings are required and have no runtime fallback.
Replace the example values before deployment. Basic Auth must be served over
HTTPS outside local development.

Metadata reads and LLM generations use separate server-side timeout settings.
The examples default to 5 seconds for health/config reads and 60 seconds for
generation; adjust `BACKEND_READ_TIMEOUT_MS` and
`BACKEND_GENERATION_TIMEOUT_MS` for your provider and infrastructure.

## Server-first request flow

1. Next.js Proxy challenges unauthenticated page and Server Action requests.
2. Next.js renders static headings and explanatory content immediately.
3. Each independently loading server component gets its own `Suspense`
   boundary and shadcn/ui `Skeleton` fallback, allowing useful UI to stream as
   soon as it is ready.
4. Protected Server Components and the generation Server Action revalidate the
   incoming Basic header rather than relying on Proxy alone.
5. Next.js forwards that header to FastAPI using the private `BACKEND_URL`.
6. FastAPI authenticates again, validates input with Pydantic, and applies the
   generation rate limit before invoking the provider.

This keeps backend topology and future provider credentials out of browser
JavaScript. When adding another data panel, keep static content outside its
boundary and give only that asynchronous panel a matching skeleton.

## API contract

All routes use the configured API prefix, which defaults to `/api/v1`.

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Public | Return readiness, service, version, and environment metadata. |
| `GET` | `/api/v1/config` | Basic Auth | Return frontend-safe API, provider, and limit metadata. |
| `POST` | `/api/v1/generations` | Basic Auth + rate limit | Validate input and create a text generation. |

Example generation request:

```bash
curl --request POST http://localhost:8000/api/v1/generations \
  --user 'local:local-development-only' \
  --header 'Content-Type: application/json' \
  --data '{"prompt":"Explain retrieval-augmented generation simply."}'
```

The request also accepts optional `instructions` and `temperature` fields. The
response has a provider-neutral shape containing an ID, provider, model, output,
and character-based usage metadata. Successful generation responses include
`X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`. Exhausted
windows return `429 Too Many Requests` with `Retry-After`.

The included limiter is intentionally process-local and fixed-window. It is
appropriate for a basic single-process starter, but each worker or replica has
its own counters. Use Redis, a database-backed limiter, or an API gateway before
scaling to multiple processes.

## Replace the demo provider

The API layer depends on the `GenerationService` protocol rather than an LLM
SDK. To connect a real provider:

1. Add its SDK dependency and secret settings in `backend/app/core/config.py`.
2. Implement `GenerationService` in `backend/app/services/generation.py`.
3. Select that implementation in `build_generation_service`.
4. Extend `LLM_PROVIDER` and set the new provider in `backend/.env`.

The routes and frontend integration can stay unchanged as long as the request
and response models retain the same contract.

## Before using a paid model

HTTP Basic is deliberately the smallest reusable authentication layer, not a
full user system. Before connecting a billable provider, replace it with your
identity/session provider, use a shared production rate limiter, keep FastAPI on
a private network when possible, and rotate credentials. CORS is a browser
policy, not access control. Keep provider and auth secrets in server-only
environment variables without a `NEXT_PUBLIC_` prefix.

## Checks

Run backend tests and formatting/lint checks from `backend/`:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Run frontend linting, type checks, and a production build from `frontend/`:

```bash
npm run lint
npm run typecheck
npm run build
```
