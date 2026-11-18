from fastapi import APIRouter

from app.generation.router import router as generation_router
from app.system import router as system_router

API_V1_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(system_router)
api_router.include_router(generation_router)
