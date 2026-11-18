# Backend

FastAPI owns the HTTP contract, authentication, validation, generation policy,
and provider boundary. Repository-wide setup, API documentation, and production
notes live in the [root README](../README.md).

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:create_app --factory --reload
```

Feature code for generation is colocated in `app/generation/`. Shared
configuration, authentication, application context, and composition stay at the
top level of `app/`.

```bash
uv run python -m pytest
uv run ruff check .
uv run ruff format --check .
```
