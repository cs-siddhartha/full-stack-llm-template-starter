# Frontend

The Next.js application owns the public landing, sign-up, login, and logout
flows, the protected application route, HttpOnly browser cookies, Server
Actions, and the private FastAPI client. Repository-wide setup lives in the
[root README](../README.md).

```bash
cp .env.example .env.local
npm --workspace frontend run dev
```

Generation form, action, and UI state are colocated in
`src/features/generation/`. `src/lib/backend.ts` is the server-only HTTP boundary
and consumes types generated from FastAPI's OpenAPI schema.

`src/components/ui/` is a shared primitive boundary. Its variant and theme
surface may be broader than the current page's usage.

```bash
npm --workspace frontend run test
npm --workspace frontend run lint
npm --workspace frontend run typecheck
npm --workspace frontend run build
```
