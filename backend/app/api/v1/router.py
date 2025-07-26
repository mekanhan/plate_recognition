"""
API v1 Router
"""
from fastapi import APIRouter
from .endpoints import cameras, streaming, playback

api_router = APIRouter()

# Include camera endpoints
api_router.include_router(
    cameras.router,
    prefix="/cameras",
    tags=["cameras"]
)

# Include streaming endpoints
api_router.include_router(
    streaming.router,
    prefix="/streams",
    tags=["streaming"]
)

# Include playback endpoints
api_router.include_router(
    playback.router,
    tags=["playback"]
)