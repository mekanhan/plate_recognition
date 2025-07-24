"""
API v1 Router
"""
from fastapi import APIRouter
from .endpoints import cameras

api_router = APIRouter()

# Include camera endpoints
api_router.include_router(
    cameras.router,
    prefix="/cameras",
    tags=["cameras"]
)