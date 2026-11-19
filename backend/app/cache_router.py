from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, ConfigDict

from app.auth.dependencies import require_session
from app.auth.service import CurrentSession
from app.context import ApplicationContext, get_context
from app.http import ApiError
from app.rate_limit import rate_limited

router = APIRouter(prefix="/cache", tags=["cache"])


class CacheFlushRead(BaseModel):
    deleted_keys: int

    model_config = ConfigDict(frozen=True)


@router.post(
    "/flush",
    response_model=CacheFlushRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiError,
            "description": "Authentication required",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ApiError,
            "description": "Cache flush rate limit exceeded",
        },
    },
)
@rate_limited("cache-flush", key="session")
async def flush_cache(
    response: Response,
    http_request: Request,
    context: Annotated[ApplicationContext, Depends(get_context)],
    session: Annotated[CurrentSession, Depends(require_session)],
) -> CacheFlushRead:
    return CacheFlushRead(deleted_keys=await context.cache.flush())
