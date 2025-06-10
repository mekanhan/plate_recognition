"""
Improved application entry point using service factory and interfaces.
"""
import uvicorn
import os
import logging
import asyncio
import uuid
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings

from app.utils.logging_config import setup_logging
from app.utils.file_helpers import ensure_directory_exists, is_directory_writable

from app.factories.service_factory import service_factory
from app.dependencies.services import (
    get_camera, 
    get_detector, 
    get_enhancer, 
    get_detection_repository,
    get_enhancement_repository,
    get_video_repository
)
from app.services.detection_service_v2 import DetectionServiceV2
from app.interfaces.camera import Camera
from app.interfaces.detector import LicensePlateDetector
from app.interfaces.enhancer import LicensePlateEnhancer
from app.interfaces.storage import DetectionRepository, EnhancementRepository
from app.services.video_service import VideoRecordingService
from app.dependencies.services import get_video_recording_service

# Import our v2 routers
from app.routers import detection_v2, stream_v2, results_v2, video

# Import original routers for backward compatibility
from app.routers import stream, detection, results

class Config(BaseSettings):
    # Application configuration
    camera_id: str = "0"
    camera_width: str = "1280"
    camera_height: str = "720"
    model_path: str = "app/models/yolo11m_best.pt"
    license_plates_dir: str = "data/license_plates"
    enhanced_plates_dir: str = "data/enhanced_plates"
    known_plates_path: str = "data/known_plates.json"
    github_token: str = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields to be ignored

# Set up proper exception handling for asyncio tasks
def handle_task_exception(task):
    """Handle exceptions in background tasks"""
    try:
        # This will re-raise the exception if one occurred
        task.result()
    except asyncio.CancelledError:
        # This is normal during shutdown, ignore
        pass
    except Exception as e:
        logging.error(f"Unhandled exception in background task: {e}")

setup_logging()
logger = logging.getLogger(__name__)

config = Config()
app = FastAPI(
    title="License Plate Recognition Microservice",
    description="A microservice for license plate recognition with real-time enhancement",
    version="2.0.0"
)
app.state.config = config

# Create data directories with absolute paths
data_dir = os.path.abspath("data")
license_plates_dir = os.path.abspath(config.license_plates_dir)
enhanced_plates_dir = os.path.abspath(config.enhanced_plates_dir)

logger.info(f"Using data directory: {data_dir}")
logger.info(f"Using license plates directory: {license_plates_dir}")
logger.info(f"Using enhanced plates directory: {enhanced_plates_dir}")

try:
    # Create directories
    ensure_directory_exists(data_dir)
    ensure_directory_exists(license_plates_dir)
    ensure_directory_exists(enhanced_plates_dir)
    
    # Check write permissions
    if not is_directory_writable(license_plates_dir):
        logger.error(f"License plates directory is not writable: {license_plates_dir}")
        raise RuntimeError(f"License plates directory is not writable: {license_plates_dir}")

    if not is_directory_writable(enhanced_plates_dir):
        logger.error(f"Enhanced plates directory is not writable: {enhanced_plates_dir}")
        raise RuntimeError(f"Enhanced plates directory is not writable: {enhanced_plates_dir}")

    logger.info("Data directories created and writable")
except Exception as e:
    logger.error(f"Error setting up data directories: {e}")
    raise

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configure service factory with application config
service_factory.set_config({
    "camera_id": int(config.camera_id),
    "camera_width": int(config.camera_width),
    "camera_height": int(config.camera_height),
    "model_path": config.model_path,
    "license_plates_dir": license_plates_dir,
    "enhanced_plates_dir": enhanced_plates_dir,
    "known_plates_path": config.known_plates_path
})

# Track background tasks for proper cleanup
background_tasks = []

# Create the improved detection service
detection_service_v2 = None

# For backward compatibility with original routers
camera_service = None
detection_service = None
storage_service = None
enhancer_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    global detection_service_v2
    try:
        # Initialize database
        from app.database import init_db
        await init_db()
        logger.info("Database initialized")

        # Initialize services through the factory
        logger.info("Initializing services through factory")
        
        # Initialize repositories first
        detection_repo = await get_detection_repository()
        enhancement_repo = await get_enhancement_repository()
        video_repo = await get_video_repository()
        logger.info("Repositories initialized")
        
        # Then initialize other services
        camera = await get_camera()
        detector = await get_detector()
        enhancer = await get_enhancer()
        video_recording_service = await get_video_recording_service()
        logger.info("Core services initialized")

        # Initialize the improved detection service
        detection_service_v2 = DetectionServiceV2()
        await detection_service_v2.initialize(
            camera=camera,
            detector=detector,
            detection_repository=detection_repo,
            enhancer=enhancer,
            enhancement_repository=enhancement_repo,
            video_recording_service=video_recording_service
        )
        logger.info("Detection service initialized")
        
        # Store in app state for use in routes
        app.state.detection_service_v2 = detection_service_v2
        
        # Set the detection service in the routers
        detection_v2.detection_service = detection_service_v2
        stream_v2.detection_service = detection_service_v2
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Re-raise to prevent the app from starting with incomplete initialization
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Properly shut down all services"""
    logger.info("Shutting down services...")
    
    # Shutdown the detection service
    if detection_service_v2:
        await detection_service_v2.shutdown()
    
    # Shutdown all services managed by the factory
    await service_factory.shutdown_all()
    
    logger.info("All services shut down")

# Include the v2 routers
app.include_router(stream_v2.router, prefix="/v2/stream", tags=["streaming-v2"])
app.include_router(detection_v2.router, prefix="/v2/detection", tags=["detection-v2"])
app.include_router(results_v2.router, prefix="/v2/results", tags=["results-v2"])
app.include_router(video.router, prefix="/v2/video", tags=["video"])  # Add this line

# Include the original routers for backward compatibility
app.include_router(stream.router, prefix="/stream", tags=["streaming"])
app.include_router(detection.router, prefix="/detection", tags=["detection"])
app.include_router(results.router, prefix="/results", tags=["results"])

# Direct video feed adapter for backward compatibility
@app.get("/stream")
async def stream_adapter(
    camera: Camera = Depends(get_camera),
    detector: LicensePlateDetector = Depends(get_detector)
):
    """Adapter for the original /stream endpoint"""
    # This endpoint redirects to the original video feed endpoint
    return StreamingResponse(
        stream_v2.generate_frames(camera, detection_service_v2),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/detection-test", response_class=HTMLResponse)
async def detection_test_page(request: Request):
    return templates.TemplateResponse("detection_test.html", {"request": request})

@app.get("/v2", response_class=HTMLResponse)
async def v2_root(request: Request):
    """Root page for v2 API with updated information"""
    return templates.TemplateResponse("v2_index.html", {"request": request})

# Simple endpoint to test the improved detection service
@app.get("/api/v2/test-detection")
async def test_detection(
    camera: Camera = Depends(get_camera),
    detector: LicensePlateDetector = Depends(get_detector),
    detection_service: DetectionServiceV2 = Depends(lambda: app.state.detection_service_v2)
):
    frame, timestamp = await camera.get_frame()
    detection = await detection_service.detect_from_camera()
    return {
        "status": "success",
        "timestamp": timestamp,
        "detection": detection
    }

# Add this route to the existing routes
@app.get("/video-browser", response_class=HTMLResponse)
async def video_browser_page(request: Request):
    """Video browser page"""
    return templates.TemplateResponse("video_browser.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app.main_v2:app", host="0.0.0.0", port=8001, reload=True)