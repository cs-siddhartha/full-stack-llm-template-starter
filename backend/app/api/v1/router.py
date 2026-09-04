from fastapi import APIRouter

from app.api.v1 import generations, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(generations.router)
