"""
FastAPI Backend Application
"""
import signal
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.router import api_router
from .api.v1.endpoints.streaming import router as streaming_router, video_router, cleanup_all_streams
from .database import init_database
# from .services.camera_health import start_camera_health_monitor  # Temporarily disabled
from .core.config import settings

logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = asyncio.Event()

# Create FastAPI app
app = FastAPI(
    title="LPR Camera Management API",
    description="License Plate Recognition Camera Management System",
    version="1.0.0"
)


def signal_handler(signum, frame):
    """Handle shutdown signals (SIGINT, SIGTERM)"""
    logger.info(f"Received signal {signum}, initiating immediate shutdown...")
    
    try:
        # Set the shutdown event to trigger cleanup
        shutdown_event.set()
        
        # Try graceful shutdown first
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(graceful_shutdown())
        else:
            asyncio.run(graceful_shutdown())
    except Exception as e:
        logger.error(f"Error in signal handler: {e}")
        # Force exit immediately if graceful shutdown fails
        import os
        logger.info("Forcing immediate exit...")
        os._exit(1)


async def graceful_shutdown():
    """Perform graceful shutdown of all services with timeout"""
    logger.info("Starting graceful shutdown with 5 second timeout...")
    
    try:
        # Set shutdown event
        shutdown_event.set()
        
        # Use asyncio.wait_for to timeout the cleanup
        await asyncio.wait_for(_cleanup_services(), timeout=5.0)
        
        logger.info("Graceful shutdown completed")
        
    except asyncio.TimeoutError:
        logger.warning("Graceful shutdown timed out, forcing exit...")
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")
    
    # Force exit after cleanup
    import os
    logger.info("Forcing exit...")
    os._exit(0)


async def _cleanup_services():
    """Internal cleanup function with proper async handling"""
    # Cleanup all streams and background services
    await cleanup_all_streams()
    
    # Stop frame distribution services
    from .services.frame_distribution_service import get_frame_distribution_manager
    try:
        frame_manager = get_frame_distribution_manager()
        if frame_manager:
            frame_manager.shutdown_all()
    except Exception as e:
        logger.error(f"Error shutting down frame distribution services: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize database and start background services on startup"""
    logger.info("Starting LPR Camera Management API...")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize database
    await init_database()
    
    # Temporarily disable background health monitor to test API
    # start_camera_health_monitor()
    
    logger.info("API startup completed")


@app.on_event("shutdown")
async def shutdown_event_handler():
    """Cleanup resources on shutdown"""
    logger.info("FastAPI shutdown event triggered")
    await graceful_shutdown()

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