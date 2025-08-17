"""
FastAPI Backend
IMPORTANT: This serves data and snapshots, NOT video streams!
"""
from fastapi import FastAPI, HTTPException, Query, Body, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import cv2
import io
import os
import time
import uuid
from datetime import datetime, timedelta
import asyncio
import logging
import json
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher
from contextlib import asynccontextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Import our services
from ai_pipeline.camera_manager import CameraManager, CameraConfig
from ai_pipeline.processors import LicensePlateDetector, ProcessingPipeline
from ai_features.vehicle.detection.pipeline import EnhancedProcessingPipeline
from ai_features.core.universal_processor import UniversalDetectionPipeline
from database.service import DatabaseService
from utils.camera_utils import generate_camera_id, validate_camera_id, CameraValidation, CameraDisplayUtils
from utils.feature_flags import feature_flags, is_license_plate_detection_enabled, is_universal_detection_enabled, is_continuous_processing_enabled
try:
    from .websocket_manager import websocket_manager, broadcast_camera_status, broadcast_recording_status
    from .background_monitor import start_background_monitoring, stop_background_monitoring
except ImportError:
    from api.websocket_manager import websocket_manager, broadcast_camera_status, broadcast_recording_status
    from api.background_monitor import start_background_monitoring, stop_background_monitoring
try:
    from .camera_endpoints import router as camera_router, init_camera_api
    # Import universal detection router only if needed
    universal_detection_router = None
    if feature_flags.is_enabled('api_features.universal_detection_endpoints'):
        from .universal_detection_endpoints import router as universal_detection_router
except ImportError:
    from api.camera_endpoints import router as camera_router, init_camera_api
    # Import universal detection router only if needed
    universal_detection_router = None
    if feature_flags.is_enabled('api_features.universal_detection_endpoints'):
        from api.universal_detection_endpoints import router as universal_detection_router

# Import authentication system  
from auth.endpoints import auth_router, users_router
from auth.dependencies import (
    get_current_user, get_optional_user, require_admin, require_operator,
    require_camera_view, require_camera_manage, require_detection_view,
    require_recording_view, require_system_config
)
from auth.models import User

# Import monitoring system
from monitoring.endpoints import monitoring_router, periodic_metrics_update
from monitoring.middleware import setup_monitoring_middleware
from monitoring.metrics import metrics
from monitoring.health import health_monitor

# Import analytics system
from analytics.endpoints import analytics_router
from analytics import initialize_analytics_system

# Pydantic models for API requests
class CameraCreate(BaseModel):
    name: str
    ip_address: str
    port: int = 80
    connection_type: str = "http"
    stream_path: str = "/mjpeg"
    location: Optional[str] = None
    username: Optional[str] = "admin"
    password: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    resolution_width: int = 1920
    resolution_height: int = 1080
    max_fps: int = 30
    video_quality: str = "medium"
    low_latency: bool = True

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    connection_type: Optional[str] = None
    stream_path: Optional[str] = None
    location: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    max_fps: Optional[int] = None
    video_quality: Optional[str] = None
    low_latency: Optional[bool] = None
    status: Optional[str] = None

class CameraTestRequest(BaseModel):
    ip_address: str
    port: int = 80
    connection_type: str = "http"
    stream_path: str = "/mjpeg"
    username: Optional[str] = "admin"
    password: Optional[str] = None
    timeout: int = 10
    brand: Optional[str] = None

# Global instances
camera_manager = None
detector = None
pipeline = None
universal_pipeline = None
db = None

# Recording service notification functions
async def notify_recording_service_camera_added(camera_id: str):
    """Notify recording service that a camera was added"""
    try:
        import urllib.request
        import urllib.parse
        import urllib.error
        
        # Use urllib in a thread to avoid blocking
        def make_request():
            try:
                req = urllib.request.Request(f"http://localhost:8002/recordings/cameras/{camera_id}/start", method='POST')
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.status
            except Exception:
                return None
        
        # Run in thread to avoid blocking
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(make_request)
            status = future.result(timeout=10)
            
        if status == 200:
            logger.info(f"Successfully notified recording service to start recording for camera {camera_id}")
        else:
            logger.warning(f"Failed to notify recording service for camera {camera_id}")
    except Exception as e:
        logger.warning(f"Could not notify recording service for camera {camera_id}: {e}")

async def notify_recording_service_camera_updated(camera_id: str):
    """Notify recording service that a camera was updated"""
    try:
        import urllib.request
        import urllib.parse
        import urllib.error
        
        def make_requests():
            try:
                # Stop recording
                req = urllib.request.Request(f"http://localhost:8002/recordings/cameras/{camera_id}/stop", method='POST')
                with urllib.request.urlopen(req, timeout=5) as response:
                    pass  # Don't fail if camera wasn't recording
            except Exception:
                pass
            
            try:
                # Start recording with new config
                req = urllib.request.Request(f"http://localhost:8002/recordings/cameras/{camera_id}/start", method='POST')
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.status
            except Exception:
                return None
        
        # Run in thread to avoid blocking
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(make_requests)
            status = future.result(timeout=15)
            
        if status == 200:
            logger.info(f"Successfully notified recording service to update camera {camera_id}")
        else:
            logger.warning(f"Failed to notify recording service for camera update {camera_id}")
    except Exception as e:
        logger.warning(f"Could not notify recording service for camera update {camera_id}: {e}")

async def notify_recording_service_camera_deleted(camera_id: str):
    """Notify recording service that a camera was deleted"""
    try:
        import urllib.request
        import urllib.parse
        import urllib.error
        
        def make_request():
            try:
                req = urllib.request.Request(f"http://localhost:8002/recordings/cameras/{camera_id}/stop", method='POST')
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.status
            except Exception:
                return None
        
        # Run in thread to avoid blocking
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(make_request)
            status = future.result(timeout=10)
            
        if status == 200:
            logger.info(f"Successfully notified recording service to stop recording for camera {camera_id}")
        else:
            logger.warning(f"Failed to notify recording service for camera deletion {camera_id}")
    except Exception as e:
        logger.warning(f"Could not notify recording service for camera deletion {camera_id}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global camera_manager, detector, pipeline, universal_pipeline, db
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize services
    camera_manager = CameraManager()
    detector = LicensePlateDetector()
    
    # Initialize pipelines based on feature flags
    pipeline = None
    universal_pipeline = None
    
    if is_license_plate_detection_enabled():
        # Use enhanced pipeline with smart deduplication for license plates
        pipeline = EnhancedProcessingPipeline()
        logging.info("License plate detection pipeline initialized")
    
    if is_universal_detection_enabled():
        # Initialize universal detection pipeline
        universal_pipeline = UniversalDetectionPipeline()
        logging.info("Universal detection pipeline initialized")
    
    if not is_license_plate_detection_enabled() and not is_universal_detection_enabled():
        logging.warning("No detection pipelines enabled - detection will not function")
    
    db = DatabaseService()
    
    # Create database tables
    await db.create_tables()
    
    # Create directories
    os.makedirs("detections", exist_ok=True)
    os.makedirs("detections/frames", exist_ok=True)
    os.makedirs("detections/plates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # Load camera configurations
    await load_cameras()
    
    # Initialize authentication system
    try:
        from auth import initialize_auth_system
        initialize_auth_system()
    except Exception as e:
        logging.error(f"Failed to initialize Authentication system: {e}")
    
    # Initialize analytics system
    try:
        initialize_analytics_system()
    except Exception as e:
        logging.error(f"Failed to initialize Analytics system: {e}")
    
    # Initialize camera API (database-driven)
    try:
        await init_camera_api()
    except Exception as e:
        logging.error(f"Failed to initialize Camera API: {e}")
    
    # Start processing loop
    asyncio.create_task(processing_loop())
    
    # Start camera recovery task
    asyncio.create_task(camera_recovery_task())
    
    # Start monitoring tasks
    asyncio.create_task(periodic_metrics_update())
    
    # Initialize metrics with system info
    try:
        metrics.update_system_info("1.0.0", "web_ui", False)  # You'd get these dynamically
        logging.info("Monitoring system initialized")
    except Exception as e:
        logging.error(f"Failed to initialize monitoring: {e}")
    
    # Start background monitoring for WebSocket updates
    try:
        await start_background_monitoring(db)
        logging.info("Background monitoring started for WebSocket updates")
    except Exception as e:
        logging.error(f"Failed to start background monitoring: {e}")
    
    logging.info("LPR System started successfully")
    
    yield
    
    # Shutdown
    # Stop background monitoring
    try:
        await stop_background_monitoring()
        logging.info("Background monitoring stopped")
    except Exception as e:
        logging.error(f"Error stopping background monitoring: {e}")
    
    camera_manager.stop_all()
    # Enhanced pipeline doesn't need cleanup - resources are auto-managed
    await db.close()
    logging.info("LPR System shutdown complete")

app = FastAPI(
    title="LPR System API",
    description="License Plate Recognition System - Serves data and snapshots, NOT video streams",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend - allow all origins for mobile access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for cross-device access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup monitoring middleware
setup_monitoring_middleware(app)

# WebSocket endpoint for real-time updates
@app.websocket("/ws/camera-updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time camera updates"""
    client_id = None
    try:
        # Accept connection and get client ID
        client_id = await websocket_manager.connect(websocket)
        
        # Auto-subscribe to common events
        await websocket_manager.subscribe(client_id, "camera_status")
        await websocket_manager.subscribe(client_id, "recording_status")
        await websocket_manager.subscribe(client_id, "motion_detection")
        await websocket_manager.subscribe(client_id, "universal_detection")
        await websocket_manager.subscribe(client_id, "detection_stats")
        await websocket_manager.subscribe(client_id, "detection_console")
        
        # Listen for incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                await websocket_manager.handle_client_message(client_id, message_data)
            except json.JSONDecodeError:
                logging.warning(f"Invalid JSON from client {client_id}: {data}")
                
    except WebSocketDisconnect:
        logging.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logging.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        if client_id:
            await websocket_manager.disconnect(client_id)

# WebSocket status endpoint
@app.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api") 
app.include_router(monitoring_router)
app.include_router(analytics_router)
app.include_router(camera_router, prefix="/v2")

# Only include universal detection endpoints if feature flag is enabled
if feature_flags.is_enabled('api_features.universal_detection_endpoints') and universal_detection_router:
    app.include_router(universal_detection_router)
    logging.info("Universal detection API endpoints enabled at /api/v2")
else:
    logging.info("Universal detection API endpoints disabled by feature flag")

# Mount static files for images
app.mount("/images", StaticFiles(directory="detections"), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

async def load_cameras():
    """Load camera configurations from database"""
    try:
        # Get all active cameras from database
        cameras = await db.get_all_cameras()
        
        for camera in cameras:
            if camera.status == 'active':
                # Create CameraConfig from database data
                config = CameraConfig(
                    camera_id=camera.camera_id,
                    name=camera.name,
                    ip_address=camera.ip_address,
                    username=camera.username or "admin",
                    password=camera.password or "",
                    port=camera.port or 554,
                    protocol=camera.connection_type or "rtsp",
                    stream_path=camera.stream_path or "/stream",
                    location=camera.location or "Unknown"
                )
                
                # Add to camera manager
                camera_manager.add_camera(config)
                logging.info(f"Loaded camera from database: {camera.name} ({camera.camera_id})")
        
        logging.info(f"Loaded {len([c for c in cameras if c.status == 'active'])} active cameras from database")
        
    except Exception as e:
        logging.error(f"Failed to load cameras from database: {e}")
        logging.info("No cameras loaded - system will rely on database CRUD operations")

async def reload_cameras():
    """Reload cameras from database and sync with camera manager"""
    try:
        # Clear existing cameras from manager
        camera_manager.cameras.clear()
        
        # Reload from database
        await load_cameras()
        
        logging.info("Successfully reloaded cameras from database")
        return True
        
    except Exception as e:
        logging.error(f"Failed to reload cameras: {e}")
        return False

# PERIODIC CAMERA RECOVERY TASK
async def camera_recovery_task():
    """Periodic task to recover offline cameras"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            # Get all offline cameras
            offline_cameras = await db.get_cameras_by_status("offline")
            
            for camera in offline_cameras:
                camera_id = camera.camera_id
                logging.info(f"Attempting recovery for offline camera: {camera_id}")
                
                # Try to restart the camera
                if camera_manager.restart_camera(camera_id):
                    await db.update_camera_status(camera_id, "active")
                    logging.info(f"Successfully recovered offline camera: {camera_id}")
                else:
                    logging.warning(f"Failed to recover offline camera: {camera_id}")
                    
        except Exception as e:
            logging.error(f"Camera recovery task error: {e}")

async def save_universal_detection(detection_data: Dict):
    """Save detection to universal_detections table"""
    try:
        from sqlalchemy import text
        
        query = """
            INSERT INTO universal_detections (
                id, camera_id, object_type, confidence, detected_at,
                bbox, frame_path, object_image_path, video_clip_id,
                video_thumbnail_path, metadata, status, processing_time_ms,
                model_version, created_at, updated_at
            ) VALUES (
                :id, :camera_id, :object_type, :confidence, :detected_at,
                :bbox, :frame_path, :object_image_path, :video_clip_id,
                :video_thumbnail_path, :metadata, :status, :processing_time_ms,
                :model_version, :created_at, :updated_at
            )
        """
        
        params = {
            'id': detection_data['id'],
            'camera_id': detection_data['camera_id'],
            'object_type': detection_data['object_type'],
            'confidence': detection_data['confidence'],
            'detected_at': detection_data['detected_at'],
            'bbox': json.dumps(detection_data['bbox']),
            'frame_path': detection_data.get('frame_path', ''),
            'object_image_path': detection_data.get('object_image_path', ''),
            'video_clip_id': detection_data.get('video_clip_id', ''),
            'video_thumbnail_path': detection_data.get('video_thumbnail_path', ''),
            'metadata': json.dumps(detection_data.get('metadata', {})),
            'status': detection_data.get('status', 'unverified'),
            'processing_time_ms': detection_data.get('processing_time_ms', 0),
            'model_version': detection_data.get('model_version', '2.0'),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        async with db.engine.begin() as conn:
            await conn.execute(text(query), params)
            
    except Exception as e:
        logging.error(f"Error saving universal detection: {e}")

async def processing_loop():
    """Main processing loop - feature-flag aware detection processing"""
    
    # Check if continuous processing is enabled
    if not is_continuous_processing_enabled():
        logging.info("Continuous processing is disabled by feature flag - processing loop will not run")
        return
    
    # Determine which detection system to use based on feature flags
    license_plate_enabled = is_license_plate_detection_enabled()
    universal_enabled = is_universal_detection_enabled()
    
    if license_plate_enabled and universal_enabled:
        logging.warning("Both license plate and universal detection are enabled - this may cause confusion. Consider enabling only one.")
    elif not license_plate_enabled and not universal_enabled:
        logging.warning("No detection systems are enabled - processing loop will run but do nothing")
    
    if license_plate_enabled:
        logging.info("Starting processing loop with LICENSE PLATE DETECTION enabled")
    if universal_enabled:
        logging.info("Starting processing loop with UNIVERSAL DETECTION enabled")
    
    while True:
        try:
            for camera_id, camera in camera_manager.get_all_cameras().items():
                if camera.is_healthy():
                    # Update camera status to active when healthy
                    await db.update_camera_status(camera_id, "active")
                    
                    frame = camera.get_frame()
                    if frame is not None:
                        start_time = time.time()
                        
                        # LICENSE PLATE DETECTION PROCESSING
                        if license_plate_enabled and pipeline:
                            try:
                                # Use the original enhanced processing pipeline for license plates
                                lp_detections = await pipeline.process_frame(camera_id, frame)
                                processing_time = time.time() - start_time
                                
                                # Save license plate detections to the original Detection table
                                for detection in lp_detections:
                                    # Record metrics for license plate detections
                                    metrics.record_detection(
                                        camera_id=detection.camera_id,
                                        vehicle_type=detection.vehicle_type,
                                        confidence=detection.confidence,
                                        ocr_confidence=detection.ocr_confidence,
                                        processing_time=processing_time
                                    )
                                    
                                    # Save to original detections table via database service
                                    # Convert dataclass to dict for database with field mapping
                                    detection_dict = {
                                        'id': detection.detection_id,
                                        'camera_id': detection.camera_id,
                                        'plate_text': detection.plate_text,
                                        'confidence': detection.confidence,
                                        'vehicle_type': detection.vehicle_type,
                                        'detected_at': detection.timestamp,
                                        'vehicle_bbox': detection.vehicle_bbox,
                                        'plate_bbox': detection.plate_bbox,
                                        'frame_path': detection.frame_path,
                                        'plate_image_path': detection.plate_image_path,
                                        'meta_data': detection.detection_metadata or {},
                                        'group_id': detection.group_id,
                                        'is_best_shot': detection.is_best_shot,
                                        'track_id': detection.track_id
                                    }
                                    saved_detection = await db.save_detection(detection_dict)
                                    if saved_detection:
                                        logging.debug(f"Saved license plate detection: {detection.plate_text}")
                                    
                                    # Broadcast license plate detection
                                    try:
                                        from api.websocket_manager import broadcast_detection
                                        await broadcast_detection({
                                            'id': detection.detection_id,
                                            'camera_id': detection.camera_id,
                                            'plate_text': detection.plate_text,
                                            'confidence': detection.confidence,
                                            'vehicle_type': detection.vehicle_type,
                                            'detected_at': detection.timestamp.isoformat()
                                        })
                                    except Exception as e:
                                        logging.debug(f"Failed to broadcast license plate detection: {e}")
                                        
                            except Exception as e:
                                logging.error(f"License plate detection error for camera {camera_id}: {e}")
                        
                        # UNIVERSAL DETECTION PROCESSING (if enabled)
                        if universal_enabled and universal_pipeline:
                            try:
                                # Process for universal detections
                                start_time = time.time()
                                universal_detections = await universal_pipeline.process_frame(camera_id, frame)
                                processing_time = time.time() - start_time
                                
                                # Save universal detections to database
                                for detection in universal_detections:
                                    # Record processing metrics based on object type
                                    if detection['object_type'] == 'vehicle' and 'plate_text' in detection.get('metadata', {}):
                                        metrics.record_detection(
                                            camera_id=detection['camera_id'],
                                            vehicle_type=detection.get('metadata', {}).get('vehicle_type', 'unknown'),
                                            confidence=detection['confidence'],
                                            ocr_confidence=detection.get('metadata', {}).get('ocr_confidence', 0.0),
                                            processing_time=processing_time
                                        )
                                    
                                    # Save to universal detections table
                                    await save_universal_detection(detection)
                                    
                                    # Broadcast to WebSocket clients
                                    try:
                                        from api.websocket_manager import broadcast_universal_detection
                                        await broadcast_universal_detection(detection)
                                    except Exception as e:
                                        logging.debug(f"Failed to broadcast universal detection: {e}")
                                        
                            except Exception as e:
                                logging.error(f"Universal detection error for camera {camera_id}: {e}")
                        
                else:
                    # Only attempt recovery if we haven't tried recently (throttle to prevent spam)
                    current_time = time.time()
                    last_recovery_key = f"last_recovery_{camera_id}"
                    
                    if not hasattr(processing_loop, last_recovery_key) or \
                       current_time - getattr(processing_loop, last_recovery_key, 0) > 60:  # 1 minute throttle
                        
                        setattr(processing_loop, last_recovery_key, current_time)
                        recovery_success = camera_manager.restart_camera(camera_id)
                        if recovery_success:
                            logging.info(f"Successfully recovered camera {camera_id}")
                            await db.update_camera_status(camera_id, "active")
                        else:
                            # Update camera status to offline when unhealthy and recovery fails
                            await db.update_camera_status(camera_id, "offline")
                            # Record camera error
                            metrics.record_camera_error(camera_id, "unhealthy")
                    else:
                        # Skip recovery attempt, too soon since last try
                        pass
            
            await asyncio.sleep(0.1)  # Process at 10 FPS
            
        except Exception as e:
            logging.error(f"Processing loop error: {e}")
            await asyncio.sleep(1)  # Brief pause on error

# API ENDPOINTS - NO VIDEO STREAMING!

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cameras": len(camera_manager.get_all_cameras()),
        "database": "connected"
    }

@app.get("/api/config/features")
async def get_feature_configuration():
    """Get current feature flag configuration"""
    from utils.feature_flags import get_detection_config_summary
    return get_detection_config_summary()

@app.get("/api/cameras")
async def get_cameras():
    """Get all cameras with real-time connection status"""
    cameras = await db.get_all_cameras()
    
    # Try to get recording service status for better accuracy
    recording_statuses = {}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:8002/health/detailed")
            if response.status_code == 200:
                data = response.json()
                if 'recording_status' in data and 'cameras' in data['recording_status']:
                    recording_statuses = data['recording_status']['cameras']
    except Exception as e:
        logging.debug(f"Could not fetch recording service status: {e}")
    
    result = []
    for c in cameras:
        # First check if camera is actively recording (most reliable indicator)
        connection_status = "offline"
        
        # Check recording service first (FFmpeg connection is more reliable)
        if c.camera_id in recording_statuses:
            rec_status = recording_statuses[c.camera_id]
            if rec_status.get('is_recording'):
                connection_status = "online"  # Actively recording means camera is connected
            elif rec_status.get('connection_status') == 'connected':
                connection_status = "online"
        else:
            # Fallback to local camera manager check
            camera_stream = camera_manager.get_camera(c.camera_id)
            
            if camera_stream:
                # Check if camera is actively streaming
                if camera_stream.is_healthy():
                    connection_status = "online"
                elif camera_stream.is_running:
                    connection_status = "connecting"
            elif c.status == 'active':
                # Camera is in database but not in manager - needs connection test
                connection_status = "unknown"
        
        # Create display-friendly summary
        camera_data = {
            "camera_id": c.camera_id,
            "name": c.name,
            "location": c.location,
            "ip_address": c.ip_address,
            "status": connection_status
        }
        display_info = CameraDisplayUtils.create_camera_summary(camera_data)
        
        result.append({
            "id": c.camera_id,
            "camera_id": c.camera_id,
            "name": c.name,
            "display_name": display_info['display_name'],
            "short_id": display_info['short_id'],
            "location": c.location or "",
            "status": connection_status,
            "ip_address": c.ip_address,
            "port": c.port,
            "connection_type": c.connection_type,
            "stream_path": c.stream_path,
            "username": c.username,
            "password": c.password,
            "enabled": c.status == 'active',
            "brand": c.brand,
            "model": c.model,
            "resolution_width": c.resolution_width,
            "resolution_height": c.resolution_height,
            "max_fps": c.max_fps,
            "video_quality": c.video_quality,
            "low_latency": c.low_latency,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "last_detection": await db.get_last_detection_time(c.camera_id),
            "last_test_result": c.last_test_result,
            "last_test_at": c.last_test_at.isoformat() if c.last_test_at else None
        })
    
    return result

@app.post("/api/cameras")
async def create_camera(camera_data: CameraCreate):
    """Create a new camera"""
    try:
        # Generate unique camera ID using utility function
        camera_id = generate_camera_id()
        
        # Create camera data dictionary
        camera_dict = camera_data.dict()
        camera_dict['camera_id'] = camera_id
        
        # Test connection before saving
        test_data = CameraTestRequest(
            ip_address=camera_data.ip_address,
            port=camera_data.port,
            connection_type=camera_data.connection_type,
            stream_path=camera_data.stream_path,
            username=camera_data.username,
            password=camera_data.password,
            timeout=10
        )
        
        connection_test = await _test_camera_connection_internal(test_data)
        
        # Set initial status based on test result
        camera_dict['status'] = 'active' if connection_test.get('success') else 'inactive'
        
        # Save to database
        db_camera_id = await db.add_camera(camera_dict)
        
        # Save test result
        test_result = 'success' if connection_test.get('success') else 'failed'
        await db.update_camera_test_result(camera_id, test_result)
        
        # Get the created camera
        created_camera = await db.get_camera(camera_id)
        
        if not created_camera:
            raise HTTPException(500, "Failed to create camera")
        
        # Reload camera manager to include new camera
        await reload_cameras()
        
        # Notify recording service to start recording for new camera
        await notify_recording_service_camera_added(camera_id)
        
        return {
            "id": created_camera.camera_id,
            "camera_id": created_camera.camera_id,
            "name": created_camera.name,
            "ip_address": created_camera.ip_address,
            "port": created_camera.port,
            "connection_type": created_camera.connection_type,
            "stream_path": created_camera.stream_path,
            "location": created_camera.location,
            "username": created_camera.username,
            "password": created_camera.password,
            "status": created_camera.status,
            "enabled": created_camera.status == 'active',
            "brand": created_camera.brand,
            "model": created_camera.model,
            "resolution_width": created_camera.resolution_width,
            "resolution_height": created_camera.resolution_height,
            "max_fps": created_camera.max_fps,
            "video_quality": created_camera.video_quality,
            "low_latency": created_camera.low_latency,
            "created_at": created_camera.created_at.isoformat(),
            "updated_at": created_camera.updated_at.isoformat() if created_camera.updated_at else None
        }
    except Exception as e:
        logging.error(f"Failed to create camera: {e}")
        raise HTTPException(500, f"Failed to create camera: {str(e)}")

@app.put("/api/cameras/{camera_id}")
async def update_camera(camera_id: str, camera_data: CameraUpdate):
    """Update an existing camera"""
    try:
        # Check if camera exists
        existing_camera = await db.get_camera(camera_id)
        if not existing_camera:
            raise HTTPException(404, "Camera not found")
        
        # Update camera data (exclude None values)
        update_dict = {k: v for k, v in camera_data.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(400, "No data provided for update")
        
        # Update in database
        success = await db.update_camera(camera_id, update_dict)
        
        if not success:
            raise HTTPException(500, "Failed to update camera")
        
        # Get updated camera
        updated_camera = await db.get_camera(camera_id)
        
        # Reload camera manager to reflect changes
        await reload_cameras()
        
        # Notify recording service to reload camera configuration
        await notify_recording_service_camera_updated(camera_id)
        
        return {
            "id": updated_camera.camera_id,
            "name": updated_camera.name,
            "ip_address": updated_camera.ip_address,
            "port": updated_camera.port,
            "connection_type": updated_camera.connection_type,
            "stream_path": updated_camera.stream_path,
            "location": updated_camera.location,
            "status": updated_camera.status,
            "updated_at": updated_camera.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to update camera {camera_id}: {e}")
        raise HTTPException(500, f"Failed to update camera: {str(e)}")

@app.get("/api/cameras/{camera_id}")
async def get_camera(camera_id: str):
    """Get a specific camera by ID"""
    try:
        camera = await db.get_camera(camera_id)
        if not camera:
            raise HTTPException(404, f"Camera {camera_id} not found")
        
        return {
            "id": camera.camera_id,
            "camera_id": camera.camera_id,
            "name": camera.name,
            "ip_address": camera.ip_address,
            "port": camera.port,
            "connection_type": camera.connection_type,
            "stream_path": camera.stream_path,
            "location": camera.location,
            "username": camera.username,
            "password": camera.password,
            "status": camera.status,
            "enabled": camera.status == 'active',
            "brand": camera.brand,
            "model": camera.model,
            "resolution_width": camera.resolution_width,
            "resolution_height": camera.resolution_height,
            "max_fps": camera.max_fps,
            "video_quality": camera.video_quality,
            "low_latency": camera.low_latency,
            "created_at": camera.created_at.isoformat() if camera.created_at else None,
            "updated_at": camera.updated_at.isoformat() if camera.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to get camera {camera_id}: {e}")
        raise HTTPException(500, f"Failed to get camera: {str(e)}")

@app.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """Delete a camera"""
    try:
        # Check if camera exists
        existing_camera = await db.get_camera(camera_id)
        if not existing_camera:
            raise HTTPException(404, "Camera not found")
        
        # Delete from database
        success = await db.delete_camera(camera_id)
        
        if not success:
            raise HTTPException(500, "Failed to delete camera")
        
        # Reload camera manager to remove deleted camera
        await reload_cameras()
        
        # Notify recording service to stop recording for deleted camera
        await notify_recording_service_camera_deleted(camera_id)
        
        return {"message": f"Camera {camera_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to delete camera {camera_id}: {e}")
        raise HTTPException(500, f"Failed to delete camera: {str(e)}")

@app.post("/api/cameras/{camera_id}/test")
async def test_camera_connection(camera_id: str):
    """Test connection to a specific camera"""
    try:
        # Get camera from database
        camera = await db.get_camera(camera_id)
        if not camera:
            raise HTTPException(404, f"Camera {camera_id} not found")
        
        # Create test request from camera data
        test_request = CameraTestRequest(
            ip_address=camera.ip_address,
            port=camera.port,
            username=camera.username,
            password=camera.password,
            stream_path=camera.stream_path,
            connection_type=camera.connection_type,
            timeout=5
        )
        
        # Test the connection
        result = await _test_camera_connection_internal(test_request)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to test camera {camera_id}: {e}")
        raise HTTPException(500, f"Failed to test camera: {str(e)}")

@app.post("/api/cameras/{camera_id}/start")
async def start_camera_recording(camera_id: str):
    """Start recording for a specific camera"""
    try:
        # Get camera from database
        camera = await db.get_camera(camera_id)
        if not camera:
            raise HTTPException(404, f"Camera {camera_id} not found")
        
        # Check if camera is already active
        if camera.status == 'active':
            return {"message": f"Camera {camera_id} is already recording", "status": "active"}
        
        # Update camera status to active
        await db.update_camera(camera_id, {"status": "active"})
        
        # Notify recording service to start recording
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"http://localhost:8002/recordings/camera/{camera_id}/start")
                if response.status_code == 200:
                    return {"message": f"Recording started for camera {camera_id}", "status": "active"}
            except:
                pass  # Recording service might not support this endpoint yet
        
        return {"message": f"Camera {camera_id} set to active, recording will start on next service restart", "status": "active"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to start recording for camera {camera_id}: {e}")
        raise HTTPException(500, f"Failed to start recording: {str(e)}")

@app.post("/api/cameras/{camera_id}/stop")
async def stop_camera_recording(camera_id: str):
    """Stop recording for a specific camera"""
    try:
        # Get camera from database
        camera = await db.get_camera(camera_id)
        if not camera:
            raise HTTPException(404, f"Camera {camera_id} not found")
        
        # Check if camera is already inactive
        if camera.status == 'inactive':
            return {"message": f"Camera {camera_id} is not recording", "status": "inactive"}
        
        # Update camera status to inactive
        await db.update_camera(camera_id, {"status": "inactive"})
        
        # Notify recording service to stop recording
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"http://localhost:8002/recordings/camera/{camera_id}/stop")
                if response.status_code == 200:
                    return {"message": f"Recording stopped for camera {camera_id}", "status": "inactive"}
            except:
                pass  # Recording service might not support this endpoint yet
        
        return {"message": f"Camera {camera_id} set to inactive, recording will stop on next service restart", "status": "inactive"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to stop recording for camera {camera_id}: {e}")
        raise HTTPException(500, f"Failed to stop recording: {str(e)}")

async def _test_camera_connection_internal(test_data: CameraTestRequest):
    """Internal camera connection test function with timeout"""
    import socket
    
    def test_camera_sync():
        """Synchronous camera test function"""
        try:
            # Build connection URL based on connection type
            if test_data.connection_type.lower() == 'rtsp':
                if test_data.username and test_data.password:
                    url = f"rtsp://{test_data.username}:{test_data.password}@{test_data.ip_address}:{test_data.port}{test_data.stream_path}"
                else:
                    url = f"rtsp://{test_data.ip_address}:{test_data.port}{test_data.stream_path}"
            else:  # http/https
                if test_data.username and test_data.password:
                    url = f"{test_data.connection_type}://{test_data.username}:{test_data.password}@{test_data.ip_address}:{test_data.port}{test_data.stream_path}"
                else:
                    url = f"{test_data.connection_type}://{test_data.ip_address}:{test_data.port}{test_data.stream_path}"
            
            # First, test basic network connectivity with socket timeout
            try:
                sock = socket.create_connection((test_data.ip_address, test_data.port), timeout=test_data.timeout or 5)
                sock.close()
            except (socket.timeout, socket.error) as e:
                return {
                    "success": False,
                    "message": "Network connection failed",
                    "url": url.replace(test_data.password or '', '***') if test_data.password else url,
                    "error": f"Cannot reach {test_data.ip_address}:{test_data.port} - {str(e)}"
                }
            
            # If network is reachable, test camera with OpenCV
            # Apply test-specific timeout settings only for connection testing
            import os
            test_timeout = test_data.timeout or 5
            os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '1'  # Only for testing
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = f'rtsp_transport;udp|rw_timeout;{test_timeout * 1000000}|stimeout;{test_timeout * 1000000}'
            
            cap = cv2.VideoCapture(url)
            
            # Set multiple timeout properties for OpenCV (in milliseconds)
            timeout_ms = (test_data.timeout or 5) * 1000
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_ms)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_ms)
            
            # Additional timeout settings
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FPS, 5)  # Lower FPS for faster connection test
            
            if not cap.isOpened():
                cap.release()
                # Check if it's likely an authentication issue
                if test_data.username and test_data.password:
                    return {
                        "success": False,
                        "message": "Authentication failed or camera stream unavailable",
                        "url": url.replace(test_data.password or '', '***') if test_data.password else url,
                        "error": "Check username/password or camera stream path"
                    }
                else:
                    return {
                        "success": False,
                        "message": "Failed to connect to camera stream",
                        "url": url.replace(test_data.password or '', '***') if test_data.password else url,
                        "error": "Camera stream connection refused"
                    }
            
            # Try to read a frame
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                height, width = frame.shape[:2]
                channels = frame.shape[2] if len(frame.shape) > 2 else 1
                return {
                    "success": True,
                    "message": "Camera connection successful",
                    "url": url.replace(test_data.password or '', '***') if test_data.password else url,
                    "resolution": f"{width}x{height}",
                    "channels": channels
                }
            else:
                return {
                    "success": False,
                    "message": "Connected but failed to read frame",
                    "url": url.replace(test_data.password or '', '***') if test_data.password else url,
                    "error": "No video data available from camera"
                }
        except Exception as e:
            logger.error(f"Camera test failed: {e}")
            return {
                "success": False,
                "message": "Camera test failed",
                "error": str(e)
            }
        finally:
            # Reset OpenCV environment variables after testing to not interfere with recording
            import os
            if 'OPENCV_FFMPEG_READ_ATTEMPTS' in os.environ:
                del os.environ['OPENCV_FFMPEG_READ_ATTEMPTS']
            if 'OPENCV_FFMPEG_CAPTURE_OPTIONS' in os.environ:
                del os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS']
    
    # Run the synchronous camera test with shorter asyncio timeout
    # Use a much shorter timeout since OpenCV ignores our settings
    actual_timeout = min(test_data.timeout or 5, 8)  # Max 8 seconds
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, test_camera_sync),
            timeout=actual_timeout
        )
        return result
    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": "Camera test timed out", 
            "error": f"Test exceeded {actual_timeout} second timeout",
            "note": "Camera may be reachable but stream path might be incorrect"
        }
    except Exception as e:
        logger.error(f"Camera test failed: {e}")
        return {
            "success": False,
            "message": "Camera test failed",
            "error": str(e)
        }

@app.post("/api/cameras/test")
async def test_camera_connection(test_data: CameraTestRequest):
    """Test camera connection without saving"""
    return await _test_camera_connection_internal(test_data)

@app.post("/api/cameras/test-all-paths")
async def test_all_camera_paths(test_data: CameraTestRequest):
    """Test camera connection with multiple stream path options"""
    # Common stream paths for different camera brands
    stream_paths = []
    
    # Add current path first
    if test_data.stream_path:
        stream_paths.append(test_data.stream_path)
    
    # Add brand-specific paths based on connection type
    if test_data.connection_type.lower() == 'rtsp':
        brand_paths = {
            'reolink': ['/Preview_01_main', '/Preview_01_sub', '/h265Preview_01_main', '/'],
            'hikvision': ['/h264/ch1/main/av_stream', '/h264/ch1/sub/av_stream'],
            'dahua': ['/cam/realmonitor?channel=1&subtype=0', '/cam/realmonitor?channel=1&subtype=1'],
            'generic': ['/stream1', '/stream', '/live', '/rtsp']
        }
    else:
        brand_paths = {
            'generic': ['/mjpeg', '/video', '/stream', '/cgi-bin/mjpg/video.cgi']
        }
    
    # Get camera brand from request or try common paths
    camera_brand = getattr(test_data, 'brand', '').lower() or 'generic'
    if camera_brand in brand_paths:
        for path in brand_paths[camera_brand]:
            if path not in stream_paths:
                stream_paths.append(path)
    
    # Add generic paths if not already present
    for path in brand_paths.get('generic', []):
        if path not in stream_paths:
            stream_paths.append(path)
    
    results = []
    
    for stream_path in stream_paths:
        # Create a copy of test_data with current stream path
        path_test_data = CameraTestRequest(
            ip_address=test_data.ip_address,
            port=test_data.port,
            connection_type=test_data.connection_type,
            stream_path=stream_path,
            username=test_data.username,
            password=test_data.password,
            timeout=test_data.timeout or 3  # Shorter timeout for multiple tests
        )
        
        logger.info(f"Testing stream path: {stream_path}")
        result = await _test_camera_connection_internal(path_test_data)
        result['stream_path'] = stream_path
        results.append(result)
        
        # If we found a working path, mark it as recommended
        if result.get('success'):
            result['recommended'] = True
            logger.info(f"Found working stream path: {stream_path}")
            break
    
    return {
        'results': results,
        'successful_path': next((r['stream_path'] for r in results if r.get('success')), None),
        'total_tested': len(results)
    }

@app.get("/api/cameras/{camera_id}/snapshot")
async def get_camera_snapshot(
    camera_id: str, 
    quality: str = Query("medium", regex="^(high|medium|low)$")
):
    """
    Get current snapshot from camera with quality control
    This is for browser display - NOT video streaming!
    
    Quality options:
    - high: 95% JPEG quality, full resolution
    - medium: 85% JPEG quality, full resolution (default)
    - low: 70% JPEG quality, 50% resolution
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    frame = camera.get_snapshot()
    if frame is None:
        # Return placeholder image
        placeholder_path = "static/camera_offline.jpg"
        if os.path.exists(placeholder_path):
            return FileResponse(placeholder_path)
        else:
            # Create a simple offline image
            offline_img = create_offline_image()
            _, buffer = cv2.imencode('.jpg', offline_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return StreamingResponse(
                io.BytesIO(buffer.tobytes()),
                media_type="image/jpeg"
            )
    
    # Apply quality settings
    processed_frame = frame.copy()
    
    # Quality-based JPEG compression and resolution scaling
    if quality == "high":
        jpeg_quality = 95
        # Keep full resolution
    elif quality == "medium":
        jpeg_quality = 85
        # Keep full resolution
    else:  # low
        jpeg_quality = 70
        # Scale to 50% resolution
        height, width = processed_frame.shape[:2]
        new_width = int(width * 0.5)
        new_height = int(height * 0.5)
        processed_frame = cv2.resize(processed_frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    # Convert frame to JPEG with specified quality
    _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    
    return StreamingResponse(
        io.BytesIO(buffer.tobytes()),
        media_type="image/jpeg",
        headers={
            "X-Snapshot-Quality": quality,
            "X-JPEG-Quality": str(jpeg_quality)
        }
    )

@app.get("/api/detections/recent")
async def get_recent_detections(
    limit: int = Query(100, ge=1, le=500),
    camera_id: Optional[str] = None
):
    """Get recent detections with images"""
    detections = await db.get_recent_detections(limit, camera_id)
    
    return [{
        "id": d.id,
        "camera_id": d.camera_id,
        "plate_text": d.plate_text,
        "confidence": d.confidence,
        "vehicle_type": d.vehicle_type,
        "detected_at": d.detected_at.isoformat(),
        "plate_image": f"detections/plates/{d.id}_plate.jpg",
        "frame_image": f"detections/frames/{d.id}_frame.jpg",
        "has_video": d.video_clip_id is not None,
        "video_clip_id": d.video_clip_id
    } for d in detections]

@app.get("/api/detections/search")
async def search_detections(
    current_user: User = Depends(require_detection_view),
    plate: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    camera_id: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    vehicle_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    include_count: bool = Query(False)
):
    """Enhanced search detections with advanced filtering and pagination"""
    detections = await db.search_detections(
        plate_text=plate,
        start_date=start_date,
        end_date=end_date,
        camera_id=camera_id,
        min_confidence=min_confidence,
        vehicle_type=vehicle_type,
        limit=limit,
        offset=offset
    )
    
    results = [{
        "id": d.id,
        "camera_id": d.camera_id,
        "plate_text": d.plate_text,
        "confidence": d.confidence,
        "vehicle_type": d.vehicle_type,
        "detected_at": d.detected_at.isoformat(),
        "plate_image": f"detections/plates/{d.id}_plate.jpg",
        "frame_image": f"detections/frames/{d.id}_frame.jpg"
    } for d in detections]
    
    if include_count:
        total_count = await db.get_search_count(
            plate_text=plate,
            start_date=start_date,
            end_date=end_date,
            camera_id=camera_id,
            min_confidence=min_confidence,
            vehicle_type=vehicle_type
        )
        
        return {
            "results": results,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(results)) < total_count
            }
        }
    
    return results

@app.get("/api/detections/similar/{plate_text}")
async def get_similar_plates(plate_text: str, limit: int = Query(10, ge=1, le=50)):
    """Find plates similar to the given text"""
    similar_detections = await db.get_similar_plates(plate_text, limit)
    
    return [{
        "id": d.id,
        "camera_id": d.camera_id,
        "plate_text": d.plate_text,
        "confidence": d.confidence,
        "vehicle_type": d.vehicle_type,
        "detected_at": d.detected_at.isoformat(),
        "plate_image": f"detections/plates/{d.id}_plate.jpg",
        "frame_image": f"detections/frames/{d.id}_frame.jpg",
        "similarity_score": _calculate_similarity_score(plate_text, d.plate_text)
    } for d in similar_detections]

@app.get("/api/detections/history/{plate_text}")
async def get_plate_history(
    plate_text: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get complete history for a specific plate number"""
    history = await db.get_plate_history(plate_text, days)
    
    return [{
        "id": d.id,
        "camera_id": d.camera_id,
        "plate_text": d.plate_text,
        "confidence": d.confidence,
        "vehicle_type": d.vehicle_type,
        "detected_at": d.detected_at.isoformat(),
        "plate_image": f"detections/plates/{d.id}_plate.jpg",
        "frame_image": f"detections/frames/{d.id}_frame.jpg"
    } for d in history]

@app.get("/api/detections/stats")
async def get_detection_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get detection statistics for analysis"""
    stats = await db.get_detection_stats(start_date, end_date)
    return stats

def _calculate_similarity_score(target: str, candidate: str) -> float:
    """Calculate simple similarity score between two plate texts"""
    if not target or not candidate:
        return 0.0
    
    target = target.upper()
    candidate = candidate.upper()
    
    if target == candidate:
        return 1.0
    
    # Simple character-based similarity
    target_chars = set(target)
    candidate_chars = set(candidate)
    
    if not target_chars or not candidate_chars:
        return 0.0
    
    intersection = len(target_chars & candidate_chars)
    union = len(target_chars | candidate_chars)
    
    return intersection / union if union > 0 else 0.0

@app.get("/api/detections/{detection_id}")
async def get_detection(detection_id: str):
    """Get specific detection details"""
    detection = await db.get_detection_by_id(detection_id)
    
    if not detection:
        raise HTTPException(404, "Detection not found")
    
    # Get camera info
    camera = await db.get_camera(detection.camera_id)
    
    return {
        "id": detection.id,
        "camera_id": detection.camera_id,
        "camera_name": camera.name if camera else "Unknown",
        "plate_text": detection.plate_text,
        "confidence": detection.confidence,
        "vehicle_type": detection.vehicle_type,
        "detected_at": detection.detected_at.isoformat(),
        "vehicle_bbox": detection.vehicle_bbox,
        "plate_bbox": detection.plate_bbox,
        "plate_image": f"detections/plates/{detection.id}_plate.jpg",
        "frame_image": f"detections/frames/{detection.id}_frame.jpg",
        "video_clip_id": detection.video_clip_id
    }

@app.get("/api/cameras/{camera_id}/health")
async def get_camera_health(camera_id: str):
    """
    Get comprehensive camera health status with enhanced diagnostics
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    # Get enhanced health status from camera
    health_status = camera.get_health_status()
    
    # Get camera from database
    db_camera = await db.get_camera(camera_id)
    health_status["database_status"] = "found" if db_camera else "missing"
    health_status["backend_processing"] = True  # Always true if endpoint responds
    
    # Add stream configuration details
    if db_camera:
        health_status["stream_config"] = {
            "ip_address": db_camera.ip_address,
            "port": db_camera.port,
            "stream_path": db_camera.stream_path,
            "connection_type": db_camera.connection_type,
            "username": db_camera.username
        }
    
    # Add recording status if available
    try:
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
            async with session.get(f"http://localhost:8002/recordings/status/{camera_id}") as response:
                if response.status == 200:
                    recording_data = await response.json()
                    health_status["recording_status"] = recording_data
                else:
                    health_status["recording_status"] = {"status": "unavailable", "message": "Recording service not responding"}
    except Exception as e:
        health_status["recording_status"] = {"status": "error", "message": str(e)}
    
    return health_status

@app.get("/api/cameras/health/summary")
async def get_cameras_health_summary():
    """Get health summary for all cameras"""
    health_report = camera_manager.get_system_health()
    return health_report

@app.post("/api/cameras/{camera_id}/restart")
async def restart_camera(camera_id: str):
    """Restart a specific camera connection"""
    try:
        # Check if camera exists in database
        db_camera = await db.get_camera(camera_id)
        if not db_camera:
            raise HTTPException(404, "Camera not found in database")
        
        # Check if camera exists in manager
        camera = camera_manager.get_camera(camera_id)
        if not camera:
            raise HTTPException(404, "Camera not found in manager")
        
        # Attempt restart
        success = camera_manager.restart_camera(camera_id)
        
        if success:
            return {
                "success": True,
                "message": f"Camera {camera_id} restart initiated",
                "camera_name": db_camera.name
            }
        else:
            return {
                "success": False,
                "message": f"Failed to restart camera {camera_id}",
                "camera_name": db_camera.name
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting camera {camera_id}: {e}")
        raise HTTPException(500, f"Internal error restarting camera: {str(e)}")

@app.post("/api/cameras/restart/all")
async def restart_all_cameras():
    """Restart all cameras"""
    try:
        results = {}
        cameras = await db.get_all_cameras()
        
        for camera in cameras:
            if camera.status == 'active':
                success = camera_manager.restart_camera(camera.camera_id)
                results[camera.camera_id] = {
                    "name": camera.name,
                    "success": success
                }
        
        successful_restarts = sum(1 for r in results.values() if r["success"])
        total_cameras = len(results)
        
        return {
            "success": successful_restarts > 0,
            "message": f"Restarted {successful_restarts}/{total_cameras} cameras",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error restarting all cameras: {e}")
        raise HTTPException(500, f"Internal error restarting cameras: {str(e)}")

@app.get("/api/cameras/health/detailed")
async def get_detailed_health_status():
    """Get detailed health status including network and performance metrics"""
    try:
        health_report = camera_manager.get_system_health()
        
        # Add system-level metrics
        health_report["system_metrics"] = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - start_time if 'start_time' in globals() else 0,
            "processing_loop_active": True,  # Could be enhanced with actual status
            "ai_models_loaded": {
                "vehicle_detection": hasattr(detector, 'vehicle_model') if detector else False,
                "plate_detection": hasattr(detector, 'plate_model') if detector else False,
                "ocr_reader": hasattr(detector, 'ocr_reader') if detector else False
            }
        }
        
        # Add network connectivity tests for each camera
        for camera_id, camera_health in health_report["cameras"].items():
            db_camera = await db.get_camera(camera_id)
            if db_camera:
                # Test basic network connectivity
                import socket
                try:
                    sock = socket.create_connection((db_camera.ip_address, db_camera.port), timeout=2)
                    sock.close()
                    camera_health["network_reachable"] = True
                except:
                    camera_health["network_reachable"] = False
        
        return health_report
        
    except Exception as e:
        logger.error(f"Error getting detailed health status: {e}")
        raise HTTPException(500, f"Internal error: {str(e)}")

@app.get("/api/cameras/{camera_id}/recording/quality")
async def get_recording_quality(camera_id: str):
    """
    Get recording quality settings for a camera
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    # Try to get current recording quality from 24/7 system
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:8002/recordings/status/{camera_id}") as response:
                if response.status == 200:
                    recording_data = await response.json()
                    # Extract quality info if available
                    return {
                        "camera_id": camera_id,
                        "recording_active": recording_data.get("active", False),
                        "current_quality": recording_data.get("quality", "medium"),
                        "resolution": recording_data.get("resolution", "1920x1080"),
                        "fps": recording_data.get("fps", 30),
                        "bitrate": recording_data.get("bitrate", "2000kbps"),
                        "codec": recording_data.get("codec", "h264")
                    }
    except Exception as e:
        logging.warning(f"Could not get recording quality from recording service: {e}")
    
    # Return default settings if recording service unavailable
    return {
        "camera_id": camera_id,
        "recording_active": False,
        "current_quality": "medium",
        "resolution": "1920x1080",
        "fps": 30,
        "bitrate": "2000kbps",
        "codec": "h264",
        "recording_service_status": "unavailable"
    }

@app.post("/api/cameras/{camera_id}/recording/quality")
async def set_recording_quality(camera_id: str, quality_settings: dict):
    """
    Set recording quality for a camera
    
    Expected quality_settings format:
    {
        "quality": "high|medium|low",
        "resolution": "1920x1080|1280x720|640x480",
        "fps": 30,
        "bitrate": "4000kbps"
    }
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    # Validate quality settings
    valid_qualities = ["high", "medium", "low"]
    valid_resolutions = ["1920x1080", "1280x720", "640x480"]
    
    quality = quality_settings.get("quality", "medium")
    if quality not in valid_qualities:
        raise HTTPException(400, f"Invalid quality. Must be one of: {valid_qualities}")
    
    resolution = quality_settings.get("resolution", "1920x1080")
    if resolution not in valid_resolutions:
        raise HTTPException(400, f"Invalid resolution. Must be one of: {valid_resolutions}")
    
    # Apply preset quality settings
    quality_presets = {
        "high": {"resolution": "1920x1080", "fps": 30, "bitrate": "4000kbps"},
        "medium": {"resolution": "1280x720", "fps": 25, "bitrate": "2000kbps"},
        "low": {"resolution": "640x480", "fps": 15, "bitrate": "1000kbps"}
    }
    
    if quality in quality_presets:
        preset = quality_presets[quality]
        final_settings = {**preset, **quality_settings}
    else:
        final_settings = quality_settings
    
    # Try to send settings to recording service
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://localhost:8002/recordings/{camera_id}/quality",
                json=final_settings
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "message": "Recording quality updated successfully",
                        "applied_settings": result
                    }
                else:
                    return {
                        "success": False,
                        "message": "Failed to update recording service",
                        "fallback": "Settings stored locally"
                    }
    except Exception as e:
        logging.warning(f"Could not update recording service: {e}")
        return {
            "success": False,
            "message": f"Recording service unavailable: {str(e)}",
            "requested_settings": final_settings
        }

@app.get("/api/cameras/{camera_id}/diagnostics")
async def get_camera_diagnostics(camera_id: str):
    """
    Run comprehensive diagnostics for a specific camera
    Returns detailed connection analysis and recommendations
    """
    # Get camera from database
    db_camera = await db.get_camera(camera_id)
    if not db_camera:
        raise HTTPException(404, "Camera not found")
    
    # Import diagnostics module
    from diagnose_camera import CameraDiagnostics
    
    # Run diagnostics
    diag = CameraDiagnostics()
    
    # Extract camera details
    ip_address = db_camera.ip_address
    port = db_camera.port or 554
    username = db_camera.username
    password = db_camera.password
    brand = db_camera.brand or 'generic'
    connection_type = db_camera.connection_type or 'rtsp'
    
    logger.info(f"Running diagnostics for camera {camera_id} at {ip_address}:{port}")
    
    try:
        # Run diagnostic tests
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            diag.run_diagnostic,
            ip_address,
            port,
            username,
            password,
            brand,
            connection_type
        )
        
        # Check current camera stream status
        camera_stream = camera_manager.get_camera(camera_id)
        if camera_stream:
            results['current_stream_status'] = {
                'is_running': camera_stream.is_running,
                'is_healthy': camera_stream.is_healthy(),
                'error_count': camera_stream.error_count,
                'last_frame_age': time.time() - camera_stream.last_frame_time if camera_stream.last_frame_time else None
            }
        else:
            results['current_stream_status'] = {
                'is_running': False,
                'is_healthy': False,
                'error_count': 0,
                'last_frame_age': None
            }
        
        # Add quick actions based on results
        quick_actions = []
        
        # Check if we found working paths
        if 'rtsp_paths' in results['tests'] and results['tests']['rtsp_paths']['working_paths']:
            best_path = results['tests']['rtsp_paths']['working_paths'][0]
            if best_path['path'] != db_camera.stream_path:
                quick_actions.append({
                    'action': 'update_stream_path',
                    'description': f"Update stream path to {best_path['path']}",
                    'current_value': db_camera.stream_path,
                    'recommended_value': best_path['path']
                })
        
        # Check if different port is open
        if 'port_scan' in results['tests']:
            open_ports = results['tests']['port_scan']['open_ports']
            if port not in open_ports and open_ports:
                alternative_port = list(open_ports.keys())[0]
                quick_actions.append({
                    'action': 'update_port',
                    'description': f"Try port {alternative_port} instead of {port}",
                    'current_value': port,
                    'recommended_value': alternative_port
                })
        
        results['quick_actions'] = quick_actions
        
        return {
            'success': True,
            'camera_id': camera_id,
            'diagnostics': results
        }
        
    except Exception as e:
        logger.error(f"Diagnostics failed for camera {camera_id}: {e}")
        return {
            'success': False,
            'camera_id': camera_id,
            'error': str(e),
            'message': 'Failed to run diagnostics'
        }

@app.get("/api/system/health")
async def get_system_health():
    """
    Get overall system health status with storage info
    """
    # Import storage manager for health check
    from ai_features.core.storage_manager import StorageManager
    storage_mgr = StorageManager()
    storage_stats = storage_mgr.get_storage_usage()
    
    system_health = {
        "api_status": "healthy",
        "database_status": "connected",
        "camera_manager_status": "running",
        "total_cameras": len(camera_manager.get_all_cameras()),
        "processing_loop_status": "running" if is_continuous_processing_enabled() else "disabled",
        "ai_models_loaded": {
            "yolo_vehicle": hasattr(detector, 'vehicle_model'),
            "yolo_plate": hasattr(detector, 'plate_model'),
            "ocr_reader": hasattr(detector, 'ocr_reader')
        },
        "storage": {
            "used_gb": storage_stats['total_size_gb'],
            "limit_gb": 10.0,
            "percentage_used": storage_stats['percentage_used'],
            "health_status": storage_mgr._get_health_status(storage_stats)
        }
    }
    
    # Get camera summary
    cameras_summary = []
    for camera_id, camera in camera_manager.get_all_cameras().items():
        current_time = time.time()
        last_frame_age = current_time - camera.last_frame_time if camera.last_frame_time > 0 else None
        
        cameras_summary.append({
            "camera_id": camera_id,
            "name": camera.config.name,
            "status": "online" if camera.last_frame_time > 0 and last_frame_age < 30 else "offline",
            "last_frame_age": last_frame_age
        })
    
    system_health["cameras"] = cameras_summary
    
    return system_health

@app.get("/api/storage/stats")
async def get_storage_stats():
    """Get detailed storage statistics and deduplication metrics"""
    from ai_features.core.storage_manager import StorageManager
    from ai_features.vehicle.detection.pipeline import EnhancedProcessingPipeline
    
    storage_mgr = StorageManager()
    
    # Get storage stats
    storage_report = storage_mgr.get_storage_report()
    
    # Get deduplication stats from pipeline if available
    dedup_stats = {}
    if hasattr(pipeline, 'dedup_manager'):
        dedup_stats = pipeline.dedup_manager.get_stats()
    
    return {
        "storage": storage_report,
        "deduplication": dedup_stats
    }

@app.post("/api/storage/cleanup")
async def trigger_storage_cleanup(force: bool = False):
    """Manually trigger storage cleanup"""
    from ai_features.core.storage_manager import StorageManager
    
    storage_mgr = StorageManager()
    cleanup_result = storage_mgr.cleanup_old_detections(force=force)
    
    return {
        "success": True,
        "cleanup_stats": cleanup_result,
        "storage_after": storage_mgr.get_storage_usage()
    }

@app.post("/api/storage/emergency-cleanup")
async def emergency_cleanup():
    """Emergency storage cleanup - deletes oldest 50% of files"""
    from ai_features.core.storage_manager import StorageManager
    
    storage_mgr = StorageManager()
    cleanup_result = storage_mgr.emergency_cleanup()
    
    return {
        "success": True,
        "cleanup_stats": cleanup_result,
        "storage_after": storage_mgr.get_storage_usage()
    }

@app.get("/api/analytics/overview")
async def get_analytics_overview():
    """Get dashboard analytics"""
    return await db.get_analytics_overview()

@app.get("/api/quality/metrics")
async def get_quality_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    camera_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get POP quality metrics and statistics for detections"""
    try:
        from ai_features.core.quality_metrics import QualityMetrics
        
        # Get recent detections with metadata
        detections = await db.get_recent_detections(limit, camera_id)
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_detections = []
            for detection in detections:
                if start_date and detection.detected_at < start_date:
                    continue
                if end_date and detection.detected_at > end_date:
                    continue
                filtered_detections.append(detection)
            detections = filtered_detections
        
        # Extract POP metrics from detection metadata
        detections_with_pop = []
        for detection in detections:
            detection_dict = {
                "id": detection.id,
                "camera_id": detection.camera_id,
                "plate_text": detection.plate_text,
                "confidence": detection.confidence,
                "detected_at": detection.detected_at.isoformat(),
                "pop_metrics": {}
            }
            
            # Extract POP metrics from metadata if available
            if detection.meta_data and isinstance(detection.meta_data, dict):
                pop_metrics = detection.meta_data.get('pop_metrics', {})
                if pop_metrics:
                    detection_dict['pop_metrics'] = pop_metrics
            
            detections_with_pop.append(detection_dict)
        
        # Calculate quality statistics
        quality_metrics = QualityMetrics()
        quality_stats = quality_metrics.get_quality_statistics(detections_with_pop)
        
        # Group by quality level for breakdown
        quality_breakdown = {
            "excellent": {"count": 0, "percentage": 0, "avg_pixels": 0},
            "good": {"count": 0, "percentage": 0, "avg_pixels": 0},
            "fair": {"count": 0, "percentage": 0, "avg_pixels": 0},
            "poor": {"count": 0, "percentage": 0, "avg_pixels": 0},
            "unusable": {"count": 0, "percentage": 0, "avg_pixels": 0}
        }
        
        # Calculate breakdown
        total_count = len(detections_with_pop)
        pixels_by_level = {"excellent": [], "good": [], "fair": [], "poor": [], "unusable": []}
        
        for detection in detections_with_pop:
            pop_metrics = detection.get('pop_metrics', {}) if isinstance(detection, dict) else {}
            level = pop_metrics.get('quality_level', 'unusable')
            pixels = pop_metrics.get('total_pixels', 0)
            
            if level in quality_breakdown:
                quality_breakdown[level]["count"] += 1
                pixels_by_level[level].append(pixels)
        
        # Calculate percentages and averages
        for level in quality_breakdown:
            count = quality_breakdown[level]["count"]
            quality_breakdown[level]["percentage"] = round((count / total_count * 100), 1) if total_count > 0 else 0
            if pixels_by_level[level]:
                quality_breakdown[level]["avg_pixels"] = round(sum(pixels_by_level[level]) / len(pixels_by_level[level]), 1)
        
        # Camera-specific statistics
        camera_stats = {}
        for detection in detections_with_pop:
            cam_id = detection['camera_id']
            if cam_id not in camera_stats:
                camera_stats[cam_id] = {
                    "total_detections": 0,
                    "avg_quality_score": 0,
                    "avg_pop": 0,
                    "quality_distribution": {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "unusable": 0}
                }
            
            camera_stats[cam_id]["total_detections"] += 1
            pop_metrics = detection.get('pop_metrics', {}) if isinstance(detection, dict) else {}
            
            # Accumulate for averages
            quality_score = pop_metrics.get('quality_score', 0)
            total_pixels = pop_metrics.get('total_pixels', 0)
            quality_level = pop_metrics.get('quality_level', 'unusable')
            
            current_count = camera_stats[cam_id]["total_detections"]
            camera_stats[cam_id]["avg_quality_score"] = (
                (camera_stats[cam_id]["avg_quality_score"] * (current_count - 1) + quality_score) / current_count
            )
            camera_stats[cam_id]["avg_pop"] = (
                (camera_stats[cam_id]["avg_pop"] * (current_count - 1) + total_pixels) / current_count
            )
            camera_stats[cam_id]["quality_distribution"][quality_level] += 1
        
        # Round camera stats
        for cam_id in camera_stats:
            camera_stats[cam_id]["avg_quality_score"] = round(camera_stats[cam_id]["avg_quality_score"], 1)
            camera_stats[cam_id]["avg_pop"] = round(camera_stats[cam_id]["avg_pop"], 1)
        
        return {
            "summary": quality_stats,
            "quality_breakdown": quality_breakdown,
            "camera_statistics": camera_stats,
            "total_detections": total_count,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "filter": {
                "camera_id": camera_id,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality metrics: {e}")
        raise HTTPException(500, f"Failed to get quality metrics: {str(e)}")

@app.get("/api/quality/thresholds")
async def get_quality_thresholds():
    """Get current quality thresholds and settings"""
    try:
        from ai_features.core.quality_metrics import QualityMetrics
        
        quality_metrics = QualityMetrics()
        
        return {
            "pop_thresholds": quality_metrics.pop_thresholds,
            "quality_score_weights": {
                "pop_score": 0.40,
                "sharpness": 0.25,
                "contrast": 0.20,
                "brightness": 0.10,
                "aspect_ratio": 0.05
            },
            "minimum_quality_threshold": 60,
            "recommended_ocr_threshold": 70,
            "description": {
                "pop_thresholds": "Pixel count thresholds for quality classification",
                "quality_score": "Overall quality score calculation (0-100)",
                "weights": "Relative importance of each quality factor"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality thresholds: {e}")
        raise HTTPException(500, f"Failed to get quality thresholds: {str(e)}")

@app.post("/api/quality/filter")
async def filter_detections_by_quality(
    filter_request: dict = Body(...),
    limit: int = Query(100, ge=1, le=1000)
):
    """Filter detections based on quality criteria
    
    Expected filter_request format:
    {
        "min_quality_score": 60,
        "quality_levels": ["good", "excellent"],
        "min_pop": 1000,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "camera_id": "optional"
    }
    """
    try:
        from ai_features.core.quality_metrics import QualityMetrics
        
        # Get detection parameters
        min_quality_score = filter_request.get('min_quality_score', 60)
        quality_levels = filter_request.get('quality_levels', [])
        min_pop = filter_request.get('min_pop', 0)
        start_date_str = filter_request.get('start_date')
        end_date_str = filter_request.get('end_date')
        camera_id = filter_request.get('camera_id')
        
        # Parse dates
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None
        
        # Get detections from database
        detections = await db.get_recent_detections(limit * 2, camera_id)  # Get extra to account for filtering
        
        # Filter by date range
        if start_date or end_date:
            filtered_detections = []
            for detection in detections:
                if start_date and detection.detected_at < start_date:
                    continue
                if end_date and detection.detected_at > end_date:
                    continue
                filtered_detections.append(detection)
            detections = filtered_detections
        
        # Convert to format with POP metrics
        detections_with_pop = []
        for detection in detections:
            detection_dict = {
                "id": detection.id,
                "camera_id": detection.camera_id,
                "plate_text": detection.plate_text,
                "confidence": detection.confidence,
                "vehicle_type": detection.vehicle_type,
                "detected_at": detection.detected_at.isoformat(),
                "plate_image": f"detections/plates/{detection.id}_plate.jpg",
                "frame_image": f"detections/frames/{detection.id}_frame.jpg",
                "pop_metrics": {}
            }
            
            # Extract POP metrics from metadata
            if detection.meta_data and isinstance(detection.meta_data, dict):
                pop_metrics = detection.meta_data.get('pop_metrics', {})
                if pop_metrics:
                    detection_dict['pop_metrics'] = pop_metrics
            
            detections_with_pop.append(detection_dict)
        
        # Apply quality filters
        quality_metrics = QualityMetrics()
        filtered_results = []
        
        for detection in detections_with_pop:
            pop_metrics = detection.get('pop_metrics', {}) if isinstance(detection, dict) else {}
            
            # Check quality score threshold
            quality_score = pop_metrics.get('quality_score', 0)
            if quality_score < min_quality_score:
                continue
            
            # Check quality level filter
            if quality_levels:
                quality_level = pop_metrics.get('quality_level', 'unusable')
                if quality_level not in quality_levels:
                    continue
            
            # Check minimum POP threshold
            total_pixels = pop_metrics.get('total_pixels', 0)
            if total_pixels < min_pop:
                continue
            
            filtered_results.append(detection)
        
        # Limit results
        filtered_results = filtered_results[:limit]
        
        return {
            "detections": filtered_results,
            "total_filtered": len(filtered_results),
            "filter_criteria": filter_request,
            "applied_filters": {
                "min_quality_score": min_quality_score,
                "quality_levels": quality_levels,
                "min_pop": min_pop,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to filter detections by quality: {e}")
        raise HTTPException(500, f"Failed to filter detections: {str(e)}")

@app.get("/api/detections/{detection_id}/quality")
async def get_detection_quality_details(detection_id: str):
    """Get detailed quality metrics for a specific detection"""
    try:
        # Get detection from database
        detection = await db.get_detection_by_id(detection_id)
        if not detection:
            raise HTTPException(404, "Detection not found")
        
        # Extract quality metrics from metadata
        quality_details = {
            "detection_id": detection_id,
            "plate_text": detection.plate_text,
            "confidence": detection.confidence,
            "detected_at": detection.detected_at.isoformat(),
            "pop_metrics": {},
            "quality_assessment": {}
        }
        
        if detection.meta_data and isinstance(detection.meta_data, dict):
            pop_metrics = detection.meta_data.get('pop_metrics', {})
            if pop_metrics:
                quality_details['pop_metrics'] = pop_metrics
                
                # Add quality assessment
                quality_score = pop_metrics.get('quality_score', 0)
                quality_level = pop_metrics.get('quality_level', 'unusable')
                total_pixels = pop_metrics.get('total_pixels', 0)
                
                quality_details['quality_assessment'] = {
                    "overall_grade": quality_level.title(),
                    "score_out_of_100": quality_score,
                    "pixel_resolution": f"{pop_metrics.get('width', 0)}x{pop_metrics.get('height', 0)} ({total_pixels} pixels)",
                    "meets_minimum_quality": pop_metrics.get('meets_minimum_quality', False),
                    "recommended_for_ocr": pop_metrics.get('recommended_for_ocr', False),
                    "sharpness_rating": "High" if pop_metrics.get('sharpness', 0) > 50 else "Medium" if pop_metrics.get('sharpness', 0) > 20 else "Low",
                    "contrast_rating": "High" if pop_metrics.get('contrast', 0) > 40 else "Medium" if pop_metrics.get('contrast', 0) > 20 else "Low",
                    "brightness_rating": "Optimal" if 80 <= pop_metrics.get('brightness', 0) <= 180 else "Suboptimal"
                }
        
        return quality_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get detection quality details: {e}")
        raise HTTPException(500, f"Failed to get quality details: {str(e)}")

@app.post("/api/cameras/{camera_id}/open-vlc")
async def open_vlc(camera_id: str):
    """
    Provide RTSP URL for VLC
    Frontend should open VLC with this URL
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    return {
        "rtsp_url": camera.config.stream_url,
        "instructions": "Open VLC and use Media -> Open Network Stream with this URL",
        "camera_name": camera.config.name
    }

@app.get("/api/video/clip/{clip_id}")
async def get_video_clip(clip_id: str):
    """Serve video clip for playback"""
    clip = await db.get_video_clip(clip_id)
    if not clip:
        raise HTTPException(404, "Video clip not found")
    
    if not os.path.exists(clip.file_path):
        raise HTTPException(404, "Video file not found")
    
    return FileResponse(
        clip.file_path,
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"inline; filename=clip_{clip_id}.mp4",
            "Accept-Ranges": "bytes"
        }
    )

def create_offline_image():
    """Create a simple offline camera image"""
    import numpy as np
    
    # Create a simple offline image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (64, 64, 64)  # Dark gray background
    
    # Add text (simple approach)
    cv2.putText(img, "Camera Offline", (180, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return img

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)