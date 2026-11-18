from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import require_basic_auth
from app.context import ApplicationContext, get_context
from app.generation.models import GenerationCreate, GenerationRead
from app.http import ApiError

router = APIRouter(prefix="/generations", tags=["generations"])

_RATE_LIMIT_HEADERS = {
    "X-RateLimit-Limit": {"schema": {"type": "integer"}},
    "X-RateLimit-Remaining": {"schema": {"type": "integer"}},
    "X-RateLimit-Reset": {"schema": {"type": "integer"}},
}


@router.post(
    "",
    response_model=GenerationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a text generation",
    responses={
        status.HTTP_201_CREATED: {"headers": _RATE_LIMIT_HEADERS},
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiError,
            "description": "Authentication required",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ApiError,
            "description": "Generation rate limit exceeded",
            "headers": {
                **_RATE_LIMIT_HEADERS,
                "Retry-After": {"schema": {"type": "integer"}},
            },
        },
    },
)
async def create_generation(
    request: GenerationCreate,
    response: Response,
    context: Annotated[ApplicationContext, Depends(get_context)],
    username: Annotated[str, Depends(require_basic_auth)],
) -> GenerationRead:
    rate_limit = await context.generation_limiter.consume(username)
    if not rate_limit.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers=rate_limit.as_headers(),
        )
    response.headers.update(rate_limit.as_headers())
    return await context.generation_service.generate(request)
