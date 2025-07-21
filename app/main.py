# app/main.py
# Centralized LPR processing system - multi-camera license plate recognition
import uvicorn
import os
import logging
import asyncio
import uuid
import time
import json
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Core services for centralized processing
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.services.enhancer_service import EnhancerService
from app.services.video_service import VideoRecordingService
from app.services.multi_camera_service import MultiCameraService
from app.services.location_service import LocationService
from app.services.camera_registry_service import CameraRegistryService
from app.services.gpu_resource_manager import GPUResourceManager
from app.services.multi_stream_processor import MultiStreamProcessor, StreamProcessingConfig
from app.services.websocket_manager import WebSocketMultiplexer
from config.settings import Config
from app.repositories.sql_repository import SQLiteDetectionRepository, SQLiteVideoRepository
from app.database import async_session

# Import centralized routers (including new ones)
from app.routers import stream, detection, results, system, cameras, locations, websocket_router

from app.utils.logging_config import setup_logging
from app.utils.file_helpers import ensure_directory_exists, is_directory_writable

# Set up proper exception handling for asyncio tasks
def handle_task_exception(task):
    """Handle exceptions in background tasks"""
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Unhandled exception in background task: {e}")

setup_logging()
logger = logging.getLogger(__name__)

# Load application configuration
config = Config()

# Initialize FastAPI app for centralized web UI
app = FastAPI(
    title="License Plate Recognition System",
    description="Multi-camera license plate recognition with centralized processing",
    version="2.0.0"
)
app.state.config = config

# Mount static files and templates for web UI
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
logger.info(f"Centralized LPR Web UI initialized on port {config.web_ui_port}")

# Create data directories with absolute paths
data_dir = os.path.abspath("data")
license_plates_dir = os.path.abspath(config.license_plates_dir)
enhanced_plates_dir = os.path.abspath(config.enhanced_plates_dir)
videos_dir = os.path.abspath("data/videos")

logger.info(f"Using data directory: {data_dir}")
logger.info(f"Using license plates directory: {license_plates_dir}")
logger.info(f"Using enhanced plates directory: {enhanced_plates_dir}")
logger.info(f"Using videos directory: {videos_dir}")
logger.info("Deployment mode: CENTRALIZED")

try:
    # Create directories
    ensure_directory_exists(data_dir)
    ensure_directory_exists(license_plates_dir)
    ensure_directory_exists(enhanced_plates_dir)
    ensure_directory_exists(videos_dir)
    
    # Check write permissions
    for directory in [license_plates_dir, enhanced_plates_dir, videos_dir]:
        if not is_directory_writable(directory):
            logger.error(f"Directory is not writable: {directory}")
            raise RuntimeError(f"Directory is not writable: {directory}")

    logger.info("Data directories created and writable")
except Exception as e:
    logger.error(f"Error setting up data directories: {e}")
    raise

# Initialize core services for centralized processing
detection_service = DetectionService()
storage_service = StorageService()
enhancer_service = EnhancerService()
multi_camera_service = MultiCameraService()
location_service = LocationService()
camera_registry_service = CameraRegistryService()

# Initialize GPU resource manager and multi-stream processor
gpu_resource_manager = GPUResourceManager(max_workers_per_gpu=2)
stream_config = StreamProcessingConfig(
    max_concurrent_streams=16,
    detection_threshold=0.7,
    processing_fps=2,
    enable_gpu_acceleration=True,
    adaptive_quality=True
)
multi_stream_processor = MultiStreamProcessor(
    gpu_resource_manager, multi_camera_service, detection_service, stream_config
)

# Initialize WebSocket multiplexer
websocket_multiplexer = WebSocketMultiplexer(
    multi_camera_service, multi_stream_processor, gpu_resource_manager
)

# Initialize video recording service with repositories
detection_repository = SQLiteDetectionRepository(async_session)
video_repository = SQLiteVideoRepository(async_session)
video_recording_service = VideoRecordingService(detection_repository, video_repository)

# Connect services
detection_service.storage_service = storage_service
enhancer_service.storage_service = storage_service
detection_service.enhancer_service = enhancer_service
detection_service.video_recording_service = video_recording_service

logger.info("Core services initialized and connected")

# Set the services in the routers
stream.detection_service = detection_service
stream.video_recording_service = video_recording_service
detection.detection_service = detection_service
results.detection_service = detection_service
results.storage_service = storage_service

# Inject services into new routers
cameras.multi_camera_service = multi_camera_service
cameras.camera_registry_service = camera_registry_service
cameras.location_service = location_service
cameras.gpu_resource_manager = gpu_resource_manager
cameras.multi_stream_processor = multi_stream_processor
locations.location_service = location_service

# Inject WebSocket multiplexer
websocket_router.websocket_multiplexer = websocket_multiplexer

# Track background tasks for proper cleanup
background_tasks = []

@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    global background_tasks

    try:
        # Initialize database first
        logger.info("Initializing database...")
        from app.database import init_database
        await init_database()
        logger.info("Database initialized successfully")

        # Initialize storage service with explicit absolute paths
        logger.info(f"Initializing storage service with directories")
        await storage_service.initialize(
            license_plates_dir=license_plates_dir,
            enhanced_plates_dir=enhanced_plates_dir
        )
        logger.info("Storage service initialized")

        # Initialize location service
        await location_service.initialize()
        logger.info("Location service initialized")

        # Initialize camera registry service
        await camera_registry_service.initialize()
        logger.info("Camera registry service initialized")

        # Initialize multi-camera service
        await multi_camera_service.initialize(camera_registry_service, location_service)
        logger.info("Multi-camera service initialized")

        # Initialize GPU resource manager
        await gpu_resource_manager.initialize()
        logger.info("GPU resource manager initialized")

        # Initialize multi-stream processor
        await multi_stream_processor.initialize()
        logger.info("Multi-stream processor initialized")

        # Initialize WebSocket multiplexer
        await websocket_multiplexer.initialize()
        logger.info("WebSocket multiplexer initialized")

        # Initialize enhancer service
        await enhancer_service.initialize(storage_service=storage_service)
        logger.info("Enhancer service initialized")

        # Initialize video recording service
        await video_recording_service.initialize()
        logger.info("Video recording service initialized")

        # Initialize detection service
        await detection_service.initialize(enhancer_service=enhancer_service)
        logger.info("Detection service initialized")

        logger.info("All centralized services initialized successfully")

        # Set the services in app.state after successful initialization
        app.state.detection_service = detection_service
        app.state.storage_service = storage_service
        app.state.enhancer_service = enhancer_service
        app.state.video_recording_service = video_recording_service
        app.state.multi_camera_service = multi_camera_service
        app.state.location_service = location_service
        app.state.camera_registry_service = camera_registry_service
        app.state.gpu_resource_manager = gpu_resource_manager
        app.state.multi_stream_processor = multi_stream_processor
        app.state.websocket_multiplexer = websocket_multiplexer
            
        logger.info("All centralized services assigned to app.state")

        # Register exception handlers for background tasks
        if hasattr(storage_service, 'task') and storage_service.task:
            storage_service.task.add_done_callback(handle_task_exception)
            background_tasks.append(storage_service.task)

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Properly shut down all services"""
    logger.info("Starting application shutdown...")
    try:
        # Cancel all background tasks first
        for task in background_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete (with a timeout)
        if background_tasks:
            await asyncio.wait(background_tasks, timeout=5.0)

        # Individual service shutdowns (in reverse order of initialization)
        logger.info("Shutting down detection service...")
        if detection_service:
            try:
                await asyncio.wait_for(detection_service.shutdown(), timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down detection service: {e}")

        logger.info("Shutting down enhancer service...")
        if enhancer_service:
            try:
                await asyncio.wait_for(enhancer_service.shutdown(), timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down enhancer service: {e}")

        logger.info("Shutting down WebSocket multiplexer...")
        if websocket_multiplexer:
            try:
                await asyncio.wait_for(websocket_multiplexer.shutdown(), timeout=10.0)
            except Exception as e:
                logger.error(f"Error shutting down WebSocket multiplexer: {e}")

        logger.info("Shutting down multi-stream processor...")
        if multi_stream_processor:
            try:
                await asyncio.wait_for(multi_stream_processor.shutdown(), timeout=10.0)
            except Exception as e:
                logger.error(f"Error shutting down multi-stream processor: {e}")

        logger.info("Shutting down GPU resource manager...")
        if gpu_resource_manager:
            try:
                await asyncio.wait_for(gpu_resource_manager.shutdown(), timeout=10.0)
            except Exception as e:
                logger.error(f"Error shutting down GPU resource manager: {e}")

        logger.info("Shutting down multi-camera service...")
        if multi_camera_service:
            try:
                await asyncio.wait_for(multi_camera_service.shutdown(), timeout=10.0)
            except Exception as e:
                logger.error(f"Error shutting down multi-camera service: {e}")

        logger.info("Shutting down camera registry service...")
        if camera_registry_service:
            try:
                await asyncio.wait_for(camera_registry_service.shutdown(), timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down camera registry service: {e}")

        logger.info("Shutting down location service...")
        if location_service:
            try:
                await asyncio.wait_for(location_service.shutdown(), timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down location service: {e}")

        logger.info("Shutting down storage service...")
        if storage_service:
            try:
                await asyncio.wait_for(storage_service.shutdown(), timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down storage service: {e}")
        
        logger.info("All centralized services shut down successfully")
            
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")

# Include routers for centralized web UI
app.include_router(stream.router, prefix="/stream", tags=["streaming"])
app.include_router(detection.router, prefix="/detection", tags=["detection"])
app.include_router(results.router, prefix="/results", tags=["results"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

# Include new centralized management routers
app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
app.include_router(locations.router, prefix="/api/locations", tags=["locations"])

# Include WebSocket router
app.include_router(websocket_router.router, prefix="/api/ws", tags=["websocket"])

# Add alias route for cameras without /api prefix (for backward compatibility)
app.include_router(cameras.router, prefix="/cameras", tags=["cameras-alias"])

logger.info("Centralized management routers included")

# WebSocket connection manager for real-time dashboard updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections[:]:  # Create a copy to iterate
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

# Initialize connection manager for dashboard updates
dashboard_manager = ConnectionManager()

# Web UI endpoints
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main centralized dashboard - Prototype 6 UI"""
    return templates.TemplateResponse("prototype6.html", {"request": request})

@app.get("/simple-camera", response_class=HTMLResponse)
async def simple_camera_modal(request: Request):
    """Simple working camera modal"""
    return templates.TemplateResponse("simple_camera_modal.html", {"request": request})

@app.get("/detection-test", response_class=HTMLResponse)
async def detection_test_page(request: Request):
    """Detection testing interface"""
    return templates.TemplateResponse("detection_test.html", {"request": request})

@app.get("/cameras", response_class=HTMLResponse)
async def cameras_page(request: Request):
    """Camera management interface"""
    return templates.TemplateResponse("cameras.html", {"request": request})

@app.get("/detections", response_class=HTMLResponse)
async def detections_page(request: Request):
    """Detection results interface"""
    return templates.TemplateResponse("detections.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics dashboard"""
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/system/monitoring", response_class=HTMLResponse)
async def system_monitoring_page(request: Request):
    """System monitoring interface"""
    return templates.TemplateResponse("system_monitoring.html", {"request": request})

@app.get("/system/config", response_class=HTMLResponse)
async def system_config_page(request: Request):
    """System configuration interface"""
    return templates.TemplateResponse("system_config.html", {"request": request})

@app.get("/modal/ip-camera", response_class=HTMLResponse)
async def ip_camera_modal_standalone(request: Request):
    """Standalone IP Camera Modal"""
    return templates.TemplateResponse("ip_camera_modal_standalone.html", {"request": request})

@app.get("/websocket-demo", response_class=HTMLResponse)
async def websocket_demo_page(request: Request):
    """WebSocket multiplexing demo interface"""
    return templates.TemplateResponse("websocket_demo.html", {"request": request})

# WebSocket endpoint for real-time dashboard updates
@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await dashboard_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Handle dashboard commands or echo back
            await dashboard_manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)

# Helper functions for broadcasting updates
async def broadcast_system_update(data):
    """Broadcast system updates to all connected dashboard clients"""
    message = json.dumps(data)
    await dashboard_manager.broadcast(message)

async def broadcast_detection_update(detection_data):
    """Broadcast detection updates to dashboard clients"""
    data = {
        "type": "detection",
        "detection": detection_data,
        "timestamp": detection_data.get("timestamp", time.time())
    }
    await broadcast_system_update(data)

async def broadcast_camera_update(camera_data):
    """Broadcast camera status updates to dashboard clients"""
    data = {
        "type": "camera",
        "camera": camera_data,
        "timestamp": time.time()
    }
    await broadcast_system_update(data)

# Store reference to dashboard manager in stream router for integration
def setup_stream_integration():
    """Setup integration between stream router and dashboard"""
    from app.routers import stream
    # Add callbacks to stream router for broadcasting updates
    stream.dashboard_broadcast_callback = broadcast_detection_update

# Call integration setup
setup_stream_integration()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for centralized system"""
    health = {
        "status": "healthy",
        "mode": "centralized",
        "services": {
            "detection": detection_service is not None,
            "storage": storage_service is not None,
            "enhancer": enhancer_service is not None,
            "video_recording": video_recording_service is not None
        },
        "timestamp": time.time()
    }
    return health

# System info endpoint
@app.get("/api/system/info")
async def system_info():
    """Get centralized system information"""
    return {
        "name": "Centralized LPR System",
        "version": "2.0.0",
        "mode": "centralized",
        "features": [
            "multi_camera_support",
            "centralized_processing",
            "gpu_resource_management",
            "multi_stream_processing",
            "camera_discovery",
            "websocket_multiplexing",
            "real_time_dashboard",
            "advanced_analytics",
            "web_ui"
        ],
        "timestamp": time.time()
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)