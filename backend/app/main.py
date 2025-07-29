"""
FastAPI Backend Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.router import api_router
from .api.v1.endpoints.streaming import router as streaming_router, video_router, cleanup_all_streams
from .database import init_database
# from .services.camera_health import start_camera_health_monitor  # Temporarily disabled
from .core.config import settings

# Create FastAPI app
app = FastAPI(
    title="LPR Camera Management API",
    description="License Plate Recognition Camera Management System",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and start background services on startup"""
    await init_database()
    # Temporarily disable background health monitor to test API
    # start_camera_health_monitor()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    await cleanup_all_streams()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include direct video streaming routes (not under /api/v1 for simple video URLs)
app.include_router(video_router, prefix="/stream", tags=["video"])

@app.get("/")
async def root():
    return {"message": "LPR Camera Management API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}