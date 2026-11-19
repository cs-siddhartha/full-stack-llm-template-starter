# Architecture

```mermaid
flowchart LR
    browser[User / Browser]

    subgraph frontend[Next.js frontend]
        pages[Landing, sign-up, login, app, logout]
        rsc[Server Components]
        action[Authenticated Server Actions]
        client[Server-only API client]

        pages --> rsc
        pages --> action
        rsc --> client
        action --> client
    end

    subgraph backend[FastAPI backend]
        router[Versioned API router<br/>/api/v1]
        auth[Cookie session dependency]
        registration[Registration and email verification]
        health[Health endpoint]
        config[Runtime capabilities]
        validation[Pydantic request validation]
        decorator[Rate-limit decorator]
        cache[Cache service]
        service[GenerationService]
        provider[Demo or production provider]

        router -->|GET /health| health
        router -->|Sign-up and verification| registration
        router -->|Protected routes| auth
        auth --> decorator
        decorator --> config
        decorator --> validation
        decorator --> cache
        validation --> service
        service --> provider
    end

    subgraph postgres[PostgreSQL]
        users[Users and verification tokens]
    end

    subgraph redis[Redis]
        sessions[Opaque sessions]
        counters[Atomic rate counters]
        entries[Namespaced cache entries]
    end

    resend[Resend email API]

    browser -->|HttpOnly session cookie| pages
    client -->|Cookie forwarded server-side| router
    registration --> users
    registration -->|Confirmation email| resend
    resend -->|Confirmation link| browser
    auth --> sessions
    decorator --> counters
    cache --> entries
    provider -->|Provider-neutral response| client

    frontend_env[Frontend server environment]
    backend_env[Backend environment]
    frontend_env -.-> client
    backend_env -.-> auth
    backend_env -.-> decorator
    backend_env -.-> cache
    backend_env -.-> service
```

Next.js owns the browser cookie and forwards it through a server-only client.
FastAPI resolves every protected session from Redis near the endpoint. Proxy
redirects are an optimistic user experience check and are not an authorization
boundary.

```mermaid
flowchart LR
    models[Pydantic request/response models]
    schema[openapi.json]
    types[Generated TypeScript contract]
    client[Next.js API client]

    models -->|FastAPI OpenAPI| schema
    schema -->|openapi-typescript| types
    types --> client
```

FastAPI owns the wire contract. The committed schema and generated TypeScript
make cross-language changes explicit and are checked by the test suite.
