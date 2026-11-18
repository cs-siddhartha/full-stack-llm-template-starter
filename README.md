# Reusable Full-Stack LLM Template

A server-first starter for LLM applications. Next.js owns the browser boundary
and calls a private FastAPI service; FastAPI owns request validation, generation
policy, and the provider-neutral API contract. A deterministic demo provider
keeps local development keyless.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for component and request-flow diagrams.

## Prerequisites

- Node.js 20.9 or newer and npm
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

## Setup

Install repository tooling and the frontend workspace from the repository root:

```bash
npm install
```

Prepare each application environment and install the backend dependencies:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
uv sync --directory backend
```

Run the applications in separate terminals:

```bash
uv run --directory backend uvicorn app.main:create_app --factory --reload
npm --workspace frontend run dev
```

Open `http://localhost:3000`. FastAPI runs at `http://localhost:8000`, with
OpenAPI documentation at `http://localhost:8000/docs`.

The example environments use `local` / `local-development-only`. Both processes
must use the same `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` values because
Next.js verifies the browser request and forwards the same Basic Auth header to
FastAPI. Replace the examples before deployment and use HTTPS outside local
development.

`BACKEND_URL` is a server-only origin. Endpoint paths come from the generated
OpenAPI contract. Metadata reads and generations have separate timeout settings
because provider calls can be much slower than health/configuration requests.

## API

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Public | Return service readiness metadata. |
| `GET` | `/api/v1/config` | Basic Auth | Return active provider and rate-limit capabilities. |
| `POST` | `/api/v1/generations` | Basic Auth + rate limit | Validate input and create a text generation. |

```bash
curl --request POST http://localhost:8000/api/v1/generations \
  --user 'local:local-development-only' \
  --header 'Content-Type: application/json' \
  --data '{"prompt":"Explain retrieval-augmented generation simply."}'
```

The generation request accepts `prompt`, optional `instructions`, and optional
`temperature`. Successful responses include `X-RateLimit-Limit`,
`X-RateLimit-Remaining`, and `X-RateLimit-Reset`; exhausted windows return `429`
with `Retry-After`.

FastAPI is the contract source. `openapi.json`,
`frontend/src/lib/api.generated.ts`, and
`frontend/src/lib/api-constraints.generated.ts` are generated artifacts:

```bash
npm run generate:api
```

Backend tests fail when `openapi.json` drifts from the application, and the root
test command checks that the generated TypeScript is current.

## Replace the demo provider

Implement the `GenerationService` protocol in
`backend/app/generation/service.py` and select it in the composition root at
`backend/app/main.py`. The route, generated client types, and UI remain
provider-neutral while the response contract stays unchanged.

The included fixed-window limiter is process-local. Replace the
`GenerationRateLimiter` implementation with shared storage or an API-gateway
policy before running multiple workers or replicas.

## Checks and commit hooks

```bash
npm test
npm run build:frontend
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

Husky runs `npm test` before each commit. The `commit-msg` hook enforces
Conventional Commits through Commitlint.
