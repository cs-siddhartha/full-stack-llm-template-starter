# Full-Stack LLM Template

This repository contains a Next.js frontend and a FastAPI backend for text
generation. Next.js owns the browser boundary. FastAPI owns request validation,
authentication, Redis sessions, caching, rate-limit policy, and the
provider-neutral API contract.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for component and request-flow diagrams.

## Prerequisites

- Node.js 20.9 or newer and npm
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Docker

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
docker compose up -d redis
```

Run the applications in separate terminals:

```bash
uv run --directory backend uvicorn app.main:app --reload
npm --workspace frontend run dev
```

Open `http://localhost:3000`. FastAPI runs at `http://localhost:8000`, with
OpenAPI documentation at `http://localhost:8000/docs`.

The login page includes a demo account button for local development. Set
`RESEND_API_KEY` in `backend/.env` to enable registration emails. Set
`RESEND_FROM_EMAIL` to a sender allowed by your Resend account. Production
requires a Resend API key, requires demo login to be disabled, and marks session
cookies as secure.

`BACKEND_URL` is a server-only origin. Endpoint paths come from the generated
OpenAPI contract. Metadata reads and generations have separate timeout settings
because provider calls can be much slower than health/configuration requests.

## API

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Public | Return service readiness metadata. |
| `POST` | `/api/v1/auth/signup` | Public + rate limit | Create an unverified account and send a confirmation email. |
| `GET` | `/api/v1/auth/verify-email` | Public | Confirm a short-lived email token. |
| `POST` | `/api/v1/auth/login` | Public + rate limit | Create a Redis-backed cookie session. |
| `POST` | `/api/v1/auth/demo` | Public + rate limit | Create a local demo session when enabled. |
| `GET` | `/api/v1/auth/session` | Session | Read the current user. |
| `POST` | `/api/v1/auth/logout` | Session | Revoke the current session. |
| `GET` | `/api/v1/config` | Session | Return cached runtime capabilities. |
| `POST` | `/api/v1/generations` | Session + rate limit | Create a text generation. |
| `POST` | `/api/v1/cache/flush` | Session + rate limit | Delete this app's cache entries. |

```bash
curl --cookie-jar /tmp/starter.cookies \
  --request POST http://localhost:8000/api/v1/auth/demo

curl --cookie /tmp/starter.cookies \
  --request POST http://localhost:8000/api/v1/generations \
  --header 'Content-Type: application/json' \
  --data '{"prompt":"Explain retrieval-augmented generation simply."}'
```

The generation request accepts `prompt`, optional `instructions`, and optional
`temperature`. Successful responses include `X-RateLimit-Limit`,
`X-RateLimit-Remaining`, and `X-RateLimit-Reset`; exhausted windows return `429`
with `Retry-After`.

Registered users are stored in Redis with scrypt password hashes. Verification
tokens are stored as SHA-256 digests, expire after one hour by default, and are
consumed once. Resend delivers the confirmation link back through the FastAPI
verification endpoint.

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
`backend/app/main.py`. The route, generated client types, and UI use the same
provider-neutral response contract.

`@rate_limited` applies named Redis policies to endpoints. `RedisCache` stores
JSON under an application namespace. The flush endpoint deletes cache keys in
that namespace and preserves sessions, rate counters, and unrelated Redis data.

## Checks and commit hooks

```bash
npm test
npm run build:frontend
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

Husky runs `npm test` before each commit. The `commit-msg` hook enforces
Conventional Commits through Commitlint.
