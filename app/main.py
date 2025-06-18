import uvicorn
import os
import logging
import asyncio
import uuid
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.services.enhancer_service import EnhancerService
from app.services.video_service import VideoRecordingService
from app.services.background_stream_manager import BackgroundStreamManager
from app.services.output_channel_manager import OutputChannelManager
from config.settings import Config
from app.repositories.sql_repository import SQLiteDetectionRepository, SQLiteVideoRepository
from app.database import async_session
from app.routers import stream, detection, results, headless
from app.utils.logging_config import setup_logging
from app.utils.file_helpers import ensure_directory_exists, is_directory_writable

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

# Load application configuration
config = Config()

# Initialize FastAPI app only if web UI is enabled
if config.is_web_ui_enabled:
    app = FastAPI(
        title="License Plate Recognition Microservice",
        description="A microservice for license plate recognition with real-time enhancement",
        version="1.0.0"
    )
    app.state.config = config
    
    # Mount static files and templates only for web UI
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
    logger.info(f"Web UI enabled - FastAPI app initialized on port {config.web_ui_port}")
else:
    # Create minimal FastAPI app for API endpoints in headless mode
    app = FastAPI(
        title="License Plate Recognition API",
        description="Headless license plate recognition service",
        version="1.0.0"
    )
    app.state.config = config
    templates = None
    logger.info("Headless mode - minimal FastAPI app initialized")

# Create data directories with absolute paths
data_dir = os.path.abspath("data")
license_plates_dir = os.path.abspath(config.license_plates_dir)
enhanced_plates_dir = os.path.abspath(config.enhanced_plates_dir)

logger.info(f"Using data directory: {data_dir}")
logger.info(f"Using license plates directory: {license_plates_dir}")
logger.info(f"Using enhanced plates directory: {enhanced_plates_dir}")
logger.info(f"Deployment mode: {config.deployment_mode}")
logger.info(f"Headless mode: {config.is_headless_mode}")
logger.info(f"Background processing enabled: {config.is_background_processing_enabled}")

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

# Initialize core services
camera_service = CameraService()
detection_service = DetectionService()
storage_service = StorageService()
enhancer_service = EnhancerService()

# Initialize video recording service with repositories
detection_repository = SQLiteDetectionRepository(async_session)
video_repository = SQLiteVideoRepository(async_session)
video_recording_service = VideoRecordingService(detection_repository, video_repository)

# Initialize background services for headless operation
output_manager = OutputChannelManager()
background_stream_manager = BackgroundStreamManager(
    camera_service=camera_service,
    detection_service=detection_service,
    storage_service=storage_service,
    output_manager=output_manager,
    video_recording_service=video_recording_service
)

# Connect storage service to both detection and enhancer services
detection_service.storage_service = storage_service
enhancer_service.storage_service = storage_service
# Connect enhancer service to detection service
detection_service.enhancer_service = enhancer_service
# Connect video recording service to detection service
detection_service.video_recording_service = video_recording_service

logger.info("Connected detection service to storage service")
logger.info("Connected enhancer service to storage service")
logger.info("Connected detection service to enhancer service")
logger.info("Connected video recording service to detection service")

# Set the services in the routers (only if web UI is enabled)
if config.is_web_ui_enabled:
    stream.camera_service = camera_service
    stream.detection_service = detection_service
    stream.video_recording_service = video_recording_service
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
        # Initialize database first
        logger.info("Initializing database...")
        from app.database import init_database
        await init_database()
        logger.info("Database initialized successfully")

        # Initialize storage first with explicit absolute paths
        logger.info(f"Initializing storage service with dirs: {license_plates_dir}, {enhanced_plates_dir}")
        await storage_service.initialize(
            license_plates_dir=license_plates_dir,
            enhanced_plates_dir=enhanced_plates_dir
        )
        logger.info("Storage service initialized")

        # Validate camera availability before initialization
        logger.info(f"Validating camera availability for: {config.camera_id}")
        available_cameras = CameraService.detect_available_cameras()
        selected_camera_available = False
        
        # Check if selected camera is available
        for camera in available_cameras:
            if camera["id"] == config.camera_id and camera["is_working"]:
                selected_camera_available = True
                logger.info(f"Selected camera {config.camera_id} is available and working")
                break
        
        # Graceful fallback if selected camera unavailable
        camera_id_to_use = config.camera_id
        if not selected_camera_available:
            # Try to find first working camera
            working_camera = next((cam for cam in available_cameras if cam["is_working"]), None)
            if working_camera:
                camera_id_to_use = working_camera["id"]
                logger.warning(f"Selected camera {config.camera_id} unavailable, falling back to camera {camera_id_to_use}")
            else:
                logger.warning(f"No working cameras found, attempting to use selected camera {config.camera_id} anyway")
        
        # Initialize camera with validated ID
        await camera_service.initialize(
            camera_id=camera_id_to_use,
            width=config.camera_width,
            height=config.camera_height
        )
        logger.info(f"Camera service initialized: {camera_id_to_use} ({config.camera_width}x{config.camera_height})")

        # Then enhancer service
        await enhancer_service.initialize(storage_service=storage_service)
        logger.info("Enhancer service initialized")

        # Initialize video recording service
        await video_recording_service.initialize()
        logger.info("Video recording service initialized")

        # Finally detection (depends on camera and enhancer)
        await detection_service.initialize(camera_service=camera_service, enhancer_service=enhancer_service)
        logger.info("Detection service initialized")

        logger.info("All core services initialized successfully")

        # Initialize camera cache service for performance optimization
        logger.info("Initializing camera cache service...")
        from app.services.camera_cache_service import camera_cache
        # Perform initial cache population in background
        try:
            import asyncio
            asyncio.create_task(camera_cache.get_cameras())
            logger.info("Camera cache initialization started in background")
        except Exception as e:
            logger.warning(f"Camera cache initialization failed: {e}")

        # Initialize lifecycle service and register all services
        from app.services.lifecycle_service import lifecycle_service
        await lifecycle_service.initialize()
        
        # Register all services for lifecycle management
        lifecycle_service.register_service("camera", camera_service, shutdown_order=10)
        lifecycle_service.register_service("detection", detection_service, shutdown_order=20)
        lifecycle_service.register_service("storage", storage_service, shutdown_order=30)
        lifecycle_service.register_service("enhancer", enhancer_service, shutdown_order=40)
        lifecycle_service.register_service("video_recording", video_recording_service, shutdown_order=50)
        
        logger.info("Lifecycle service initialized with registered services")

        # Initialize background processing if enabled
        if config.is_background_processing_enabled:
            logger.info("Initializing background processing...")
            
            # Configure output channels based on config
            if config.enable_storage_output:
                output_manager.add_channel("storage", "storage", {})
                logger.info("Storage output channel added")
            
            if config.enable_api_output:
                output_manager.add_channel("api", "api", {})
                logger.info("API output channel added")
            
            if config.enable_websocket_output:
                output_manager.add_channel("websocket", "websocket", {})
                logger.info("WebSocket output channel added")
            
            if config.enable_webhook_output and config.webhook_url:
                webhook_config = {
                    "url": config.webhook_url,
                    "timeout": config.webhook_timeout
                }
                output_manager.add_channel("webhook", "webhook", webhook_config)
                logger.info(f"Webhook output channel added: {config.webhook_url}")
            
            # Update background stream manager configuration
            background_config = {
                "frame_skip": config.background_frame_skip,
                "processing_interval": config.background_processing_interval,
                "max_queue_size": config.background_max_queue_size,
                "health_check_interval": config.background_health_check_interval
            }
            background_stream_manager.update_config(background_config)
            
            # Start output manager
            await output_manager.start()
            logger.info("Output channel manager started")
            
            # Start background processing
            await background_stream_manager.start()
            logger.info("Background stream manager started")
            
            # Register background services with lifecycle manager
            lifecycle_service.register_service("output_manager", output_manager, shutdown_order=60)
            lifecycle_service.register_service("background_stream_manager", background_stream_manager, shutdown_order=70)

        # Set the services in app.state after successful initialization
        app.state.camera_service = camera_service
        app.state.detection_service = detection_service
        app.state.storage_service = storage_service
        app.state.enhancer_service = enhancer_service
        app.state.video_recording_service = video_recording_service
        
        # Add headless components to app state
        app.state.output_manager = output_manager
        app.state.background_stream_manager = background_stream_manager
        app.state.lifecycle_service = lifecycle_service
            
        logger.info("All services assigned to app.state")

        # Register exception handlers for background tasks
        if hasattr(storage_service, 'task') and storage_service.task:
            storage_service.task.add_done_callback(handle_task_exception)
            background_tasks.append(storage_service.task)

        # Set processing parameters from configuration
        try:
            # Use the config value directly
            processing_frequency = config.stream_processing_frequency
            
            if hasattr(stream, 'frame_processor'):
                stream.frame_processor["process_every_n_frames"] = processing_frequency
                logger.info(f"Set frame processing interval to every {processing_frequency} frames (from config)")

            # Set queue processing interval
            if hasattr(stream, 'plate_tracker'):
                stream.plate_tracker["process_interval"] = 1.0  # Process queue every 1 second
                logger.info(f"Set detection queue processing interval to {stream.plate_tracker['process_interval']}s")
                
        except Exception as e:
            logger.warning(f"Could not load processing frequency from config, using default: {e}")
            # Fallback to default
            processing_frequency = 5
            if hasattr(stream, 'frame_processor'):
                stream.frame_processor["process_every_n_frames"] = processing_frequency
                logger.info(f"Set frame processing interval to every {processing_frequency} frames (fallback default)")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Re-raise to prevent the app from starting with incomplete initialization
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Properly shut down all services using lifecycle service"""
    logger.info("Starting application shutdown...")

    try:
        # Use lifecycle service for coordinated shutdown
        from app.services.lifecycle_service import lifecycle_service
        
        # Cancel all background tasks first
        for task in background_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete (with a timeout)
        if background_tasks:
            await asyncio.wait(background_tasks, timeout=5.0)

        # Perform graceful shutdown of all registered services
        success = await lifecycle_service.graceful_shutdown(timeout=30.0)
        
        if success:
            logger.info("Application shutdown completed successfully")
        else:
            logger.warning("Application shutdown completed with some failures")
            
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")
        
        # Fallback to individual service shutdown
        logger.info("Falling back to individual service shutdown...")
        
        # Stop headless components first
        if background_stream_manager:
            logger.info("Stopping background stream manager...")
            try:
                await asyncio.wait_for(background_stream_manager.stop(), timeout=10.0)
            except Exception as e:
                logger.error(f"Error stopping background stream manager: {e}")

        if output_manager:
            logger.info("Stopping output manager...")
            try:
                await asyncio.wait_for(output_manager.stop(), timeout=5.0)
            except Exception as e:
                logger.error(f"Error stopping output manager: {e}")

        # Individual service shutdowns
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

    logger.info("Shutting down camera service...")
    if camera_service:
        try:
            await asyncio.wait_for(camera_service.shutdown(), timeout=5.0)
        except Exception as e:
            logger.error(f"Error shutting down camera service: {e}")

    logger.info("Shutting down storage service...")
    if storage_service:
        try:
            await asyncio.wait_for(storage_service.shutdown(), timeout=5.0)
        except Exception as e:
            logger.error(f"Error shutting down storage service: {e}")
    
    logger.info("All services shut down")

# Include routers based on deployment mode
if config.is_web_ui_enabled:
    # Include full web UI routers
    app.include_router(stream.router, prefix="/stream", tags=["streaming"])
    app.include_router(detection.router, prefix="/detection", tags=["detection"])
    app.include_router(results.router, prefix="/results", tags=["results"])
    
    # Add main index route
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Main index page"""
        return templates.TemplateResponse("index.html", {"request": request})
    
    logger.info("Web UI routers included")

# Always include system API router for monitoring
from app.routers import system
app.include_router(system.router, prefix="/api/system", tags=["system"])

# Always include headless API router for background processing control
app.include_router(headless.router, prefix="/api/headless", tags=["headless"])

# Add headless-specific API endpoints
if config.is_background_processing_enabled:
    from fastapi import APIRouter
    
    headless_router = APIRouter()
    
    @headless_router.get("/status")
    async def get_background_status():
        """Get background processing status"""
        if not background_stream_manager:
            return {"error": "Background processing not enabled"}
        return await background_stream_manager.get_status()
    
    @headless_router.get("/health")
    async def get_health_status():
        """Get comprehensive health status"""
        health = {"services": {}, "background": None, "output_channels": None}
        
        # Core services health
        health["services"]["camera"] = camera_service is not None
        health["services"]["detection"] = detection_service is not None
        health["services"]["storage"] = storage_service is not None
        
        # Background processing health
        if background_stream_manager:
            health["background"] = await background_stream_manager.get_status()
        
        # Output channels health
        if output_manager:
            health["output_channels"] = output_manager.get_stats()
        
        return health
    
    @headless_router.post("/control/pause")
    async def pause_background_processing():
        """Pause background processing"""
        if background_stream_manager:
            await background_stream_manager.pause()
            return {"status": "paused"}
        return {"error": "Background processing not available"}
    
    @headless_router.post("/control/resume")
    async def resume_background_processing():
        """Resume background processing"""
        if background_stream_manager:
            await background_stream_manager.resume()
            return {"status": "resumed"}
        return {"error": "Background processing not available"}
    
    @headless_router.get("/detections/recent")
    async def get_recent_detections(limit: int = 50):
        """Get recent detections from API output channel"""
        if output_manager:
            api_channel = output_manager.get_channel("api")
            if api_channel:
                return await api_channel.get_recent_detections(limit)
        return {"error": "API output channel not available"}
    
    @headless_router.get("/metrics")
    async def get_metrics():
        """Get comprehensive metrics"""
        metrics = {}
        
        if background_stream_manager:
            metrics["background_stream_manager"] = await background_stream_manager.get_status()
        
        if output_manager:
            metrics["output_channels"] = output_manager.get_stats()
        
        return metrics
    
    @headless_router.post("/control/restart")
    async def restart_background_processing():
        """Restart background processing"""
        if background_stream_manager:
            await background_stream_manager.stop()
            await background_stream_manager.start()
            return {"status": "restarted"}
        return {"error": "Background processing not available"}
    
    @headless_router.post("/output-channels/{channel_name}/enable")
    async def enable_output_channel(channel_name: str):
        """Enable a specific output channel"""
        if output_manager:
            output_manager.enable_channel(channel_name)
            return {"status": f"Channel {channel_name} enabled"}
        return {"error": "Output channel manager not available"}
    
    @headless_router.post("/output-channels/{channel_name}/disable")
    async def disable_output_channel(channel_name: str):
        """Disable a specific output channel"""
        if output_manager:
            output_manager.disable_channel(channel_name)
            return {"status": f"Channel {channel_name} disabled"}
        return {"error": "Output channel manager not available"}
    
    @headless_router.get("/output-channels")
    async def get_output_channels():
        """Get output channel status"""
        if output_manager:
            return output_manager.get_stats()
        return {"error": "Output channel manager not available"}
    
    app.include_router(headless_router, prefix="/api/headless", tags=["headless"])
    logger.info("Headless API endpoints added")

# WebSocket endpoints for real-time updates
from fastapi import WebSocket, WebSocketDisconnect
import json

class ConnectionManager:
	def __init__(self):
		self.active_connections: list[WebSocket] = []

	async def connect(self, websocket: WebSocket):
		await websocket.accept()
		self.active_connections.append(websocket)

	def disconnect(self, websocket: WebSocket):
		self.active_connections.remove(websocket)

	async def send_personal_message(self, message: str, websocket: WebSocket):
		await websocket.send_text(message)

	async def broadcast(self, message: str):
		for connection in self.active_connections:
			try:
				await connection.send_text(message)
			except:
				# Remove dead connections
				if connection in self.active_connections:
					self.active_connections.remove(connection)

# Initialize connection manager (always available for output channels)
dashboard_manager = ConnectionManager()

# Add WebSocket output channel if enabled
# Note: WebSocketOutputChannel implementation pending
# if config.is_background_processing_enabled and config.enable_websocket_output:
#     if output_manager:
#         websocket_channel = WebSocketOutputChannel(dashboard_manager)
#         # This will be added during startup event
        
# Web UI endpoints (only if web UI is enabled)
if config.is_web_ui_enabled:
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        if not templates:
            return HTMLResponse("Web UI not available in headless mode", status_code=503)
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/detection-test", response_class=HTMLResponse)
    async def detection_test_page(request: Request):
        if not templates:
            return HTMLResponse("Web UI not available in headless mode", status_code=503)
        return templates.TemplateResponse("detection_test.html", {"request": request})

    @app.get("/system/monitoring", response_class=HTMLResponse)
    async def system_monitoring_page(request: Request):
        if not templates:
            return HTMLResponse("Web UI not available in headless mode", status_code=503)
        return templates.TemplateResponse("system_monitoring.html", {"request": request})

    @app.get("/system/config", response_class=HTMLResponse)
    async def system_config_page(request: Request):
        if not templates:
            return HTMLResponse("Web UI not available in headless mode", status_code=503)
        return templates.TemplateResponse("system_config.html", {"request": request})
else:
    # Minimal root endpoint for headless mode
    @app.get("/")
    async def headless_root():
        return {
            "service": "License Plate Recognition API",
            "mode": "headless",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/headless/health",
                "status": "/api/headless/status",
                "recent_detections": "/api/headless/detections/recent",
                "api_docs": "/docs"
            }
        }

@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
	await dashboard_manager.connect(websocket)
	try:
		while True:
			# Keep connection alive and handle incoming messages
			data = await websocket.receive_text()
			# Echo back or handle commands
			await dashboard_manager.send_personal_message(f"Echo: {data}", websocket)
	except WebSocketDisconnect:
		dashboard_manager.disconnect(websocket)

# Helper function to broadcast system updates
async def broadcast_system_update(data):
	"""Broadcast system updates to all connected dashboard clients"""
	message = json.dumps(data)
	await dashboard_manager.broadcast(message)

# Helper function to broadcast detection updates
async def broadcast_detection_update(detection_data):
	"""Broadcast detection updates to dashboard clients"""
	data = {
		"type": "detection",
		"detection": detection_data,
		"timestamp": detection_data.get("timestamp", time.time())
	}
	await broadcast_system_update(data)

# Store reference to main app's dashboard manager in stream router
def setup_stream_integration():
	"""Setup integration between stream router and dashboard"""
	from app.routers import stream
	# Add a callback to stream router for broadcasting detections
	stream.dashboard_broadcast_callback = broadcast_detection_update

# Call integration setup
setup_stream_integration()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)