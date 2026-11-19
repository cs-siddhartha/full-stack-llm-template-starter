from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.auth.dependencies import require_session
from app.auth.service import CurrentSession
from app.context import ApplicationContext, get_context
from app.generation.models import GenerationCreate, GenerationRead
from app.http import ApiError
from app.rate_limit import rate_limited

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
@rate_limited("generation", key="session")
async def create_generation(
    payload: GenerationCreate,
    response: Response,
    http_request: Request,
    context: Annotated[ApplicationContext, Depends(get_context)],
    session: Annotated[CurrentSession, Depends(require_session)],
) -> GenerationRead:
    return await context.generation_service.generate(payload)
