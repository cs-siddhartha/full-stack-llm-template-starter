# Frontend

The Next.js application owns browser authentication, Server Components, Server
Actions, and the private FastAPI client. Repository-wide setup and architecture
live in the [root README](../README.md).

```bash
cp .env.example .env.local
npm --workspace frontend run dev
```

Generation form, action, and UI state are colocated in
`src/features/generation/`. `src/lib/backend.ts` is the server-only HTTP boundary
and consumes types generated from FastAPI's OpenAPI schema.

`src/components/ui/` is an intentionally reusable primitive boundary. Its
variant and theme surface may be broader than the starter page's current usage.

```bash
npm --workspace frontend run test
npm --workspace frontend run lint
npm --workspace frontend run typecheck
npm --workspace frontend run build
```
