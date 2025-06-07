import uvicorn
import os
import logging
import asyncio
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.services.enhancer_service import EnhancerService
from app.routers import stream, detection, results
from app.utils.logging_config import setup_logging
from app.utils.file_helpers import ensure_directory_exists, is_directory_writable
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # Add the missing fields:
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
    version="1.0.0"
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

# After initializing services
camera_service = CameraService()
detection_service = DetectionService()
storage_service = StorageService()
enhancer_service = EnhancerService()

app.state.camera_service = camera_service
app.state.detection_service = detection_service
app.state.storage_service = storage_service
app.state.enhancer_service = enhancer_service

# Connect storage service to both detection and enhancer services
detection_service.storage_service = storage_service
enhancer_service.storage_service = storage_service
# Connect enhancer service to detection service
detection_service.enhancer_service = enhancer_service

logger.info("Connected detection service to storage service")
logger.info("Connected enhancer service to storage service")
logger.info("Connected detection service to enhancer service")

# Set the services in the routers
stream.camera_service = camera_service
stream.detection_service = detection_service
detection.detection_service = detection_service
results.detection_service = detection_service
results.storage_service = storage_service

# Track background tasks for proper cleanup
background_tasks = []
@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    global background_tasks

    try:
        # Initialize storage first with explicit absolute paths
        logger.info(f"Initializing storage service with dirs: {license_plates_dir}, {enhanced_plates_dir}")
        await storage_service.initialize(
            license_plates_dir=license_plates_dir,
            enhanced_plates_dir=enhanced_plates_dir
        )
        logger.info("Storage service initialized")

        # Then camera
        await camera_service.initialize()
        logger.info("Camera service initialized")

        # Then enhancer service
        await enhancer_service.initialize(storage_service=storage_service)
        logger.info("Enhancer service initialized")

        # Finally detection (depends on camera and enhancer)
        await detection_service.initialize(camera_service=camera_service, enhancer_service=enhancer_service)
        logger.info("Detection service initialized")

        logger.info("All services initialized successfully")

        # Register exception handlers for background tasks
        if hasattr(storage_service, 'task') and storage_service.task:
            storage_service.task.add_done_callback(handle_task_exception)
            background_tasks.append(storage_service.task)

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Re-raise to prevent the app from starting with incomplete initialization
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Properly shut down all services"""
    logger.info("Shutting down services...")

    # Cancel all background tasks
    for task in background_tasks:
        if not task.done():
            task.cancel()

    # Wait for all tasks to complete (with a timeout)
    if background_tasks:
        await asyncio.wait(background_tasks, timeout=5.0)

    # Shutdown services in reverse order of initialization
    logger.info("Shutting down detection service...")
    if detection_service:
        try:
            await asyncio.wait_for(detection_service.shutdown(), timeout=5.0)
        except:
            pass

    logger.info("Shutting down enhancer service...")
    if enhancer_service:
        try:
            await asyncio.wait_for(enhancer_service.shutdown(), timeout=5.0)
        except:
            pass

    logger.info("Shutting down camera service...")
    if camera_service:
        try:
            await asyncio.wait_for(camera_service.shutdown(), timeout=5.0)
        except:
            pass

    logger.info("Shutting down storage service...")
    if storage_service:
        try:
            await asyncio.wait_for(storage_service.shutdown(), timeout=5.0)
        except:
            pass
    logger.info("All services shut down")

# Then include the routers
app.include_router(stream.router, prefix="/stream", tags=["streaming"])
app.include_router(detection.router, prefix="/detection", tags=["detection"])
app.include_router(results.router, prefix="/results", tags=["results"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/detection-test", response_class=HTMLResponse)
async def detection_test_page(request: Request):
    return templates.TemplateResponse("detection_test.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)