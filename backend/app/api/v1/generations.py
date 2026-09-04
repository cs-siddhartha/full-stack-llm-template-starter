from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import (
    enforce_generation_rate_limit,
    get_generation_service,
)
from app.core.rate_limit import RateLimitDecision
from app.models.generation import GenerationCreate, GenerationRead
from app.services.generation import GenerationService

router = APIRouter(prefix="/generations", tags=["generations"])


@router.post(
    "",
    response_model=GenerationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a text generation",
)
async def create_generation(
    request: GenerationCreate,
    response: Response,
    service: Annotated[GenerationService, Depends(get_generation_service)],
    rate_limit: Annotated[
        RateLimitDecision,
        Depends(enforce_generation_rate_limit),
    ],
) -> GenerationRead:
    """Delegate validated input to the configured generation provider."""
    response.headers.update(rate_limit.as_headers())
    return await service.generate(request)
