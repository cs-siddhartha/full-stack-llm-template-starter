# Backend

FastAPI owns the HTTP contract, Redis-backed cookie sessions, protected routes,
rate limits, cache storage, validation, and the generation provider boundary.
Repository-wide setup lives in the [root README](../README.md).

```bash
cp .env.example .env
uv sync
docker compose -f ../compose.yaml up -d redis
uv run uvicorn app.main:app --reload
```

`app/auth/` owns registration, Resend email confirmation, password hashing,
login, demo access, and session behavior. Add `RESEND_API_KEY` and an allowed
`RESEND_FROM_EMAIL` to `.env` before testing registration. `app/rate_limit.py`
provides the endpoint decorator and Redis counter implementation. `app/cache.py`
provides namespaced JSON caching. Feature code for generation stays in
`app/generation/`.

```bash
uv run python -m pytest
uv run ruff check .
uv run ruff format --check .
```
