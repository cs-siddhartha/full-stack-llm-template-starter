# Architecture

```mermaid
flowchart LR
    browser[User / Browser]

    subgraph frontend[Next.js frontend]
        proxy[HTTP Basic proxy]
        rsc[Server Components]
        action[Generation Server Action]
        client[Server-only API client]

        proxy --> rsc
        proxy --> action
        rsc --> client
        action --> client
    end

    subgraph backend[FastAPI backend]
        router[Versioned API router<br/>/api/v1]
        health[Health endpoint]
        config_auth[HTTP Basic authentication]
        generation_auth[HTTP Basic authentication]
        config[Runtime capabilities]
        validation[Pydantic request validation]
        limiter[Credential-scoped rate limiter]
        service[GenerationService]
        provider[Demo or production provider]

        router -->|GET /health| health
        router -->|GET /config| config_auth
        config_auth --> config
        router -->|POST /generations| generation_auth
        generation_auth --> validation
        validation --> limiter
        limiter --> service
        service --> provider
    end

    browser -->|HTTPS + Basic Auth| proxy
    client -->|Server-to-server HTTP<br/>Authorization forwarded| router
    provider -->|Provider-neutral response| client

    frontend_env[Frontend server environment]
    backend_env[Backend environment]
    frontend_env -.-> proxy
    frontend_env -.-> client
    backend_env -.-> config_auth
    backend_env -.-> generation_auth
    backend_env -.-> service
```

The browser never calls FastAPI directly. Next.js revalidates authentication
inside protected server operations rather than relying on the proxy alone. The
backend is therefore private and does not carry browser CORS configuration.

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
