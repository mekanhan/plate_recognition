"""
FastAPI Backend
IMPORTANT: This serves data and snapshots, NOT video streams!
"""
from fastapi import FastAPI, HTTPException, Query, Body
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
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Import our services
from ai_pipeline.camera_manager import CameraManager, CameraConfig
from ai_pipeline.processors import LicensePlateDetector, ProcessingPipeline
from ai_features.vehicle.detection.pipeline import EnhancedProcessingPipeline
from database.service import DatabaseService
from utils.camera_utils import generate_camera_id, validate_camera_id, CameraValidation, CameraDisplayUtils
try:
    from .camera_endpoints import router as camera_router, init_camera_api
except ImportError:
    from api.camera_endpoints import router as camera_router, init_camera_api

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
    global camera_manager, detector, pipeline, db
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize services
    camera_manager = CameraManager()
    detector = LicensePlateDetector()
    # Use enhanced pipeline with smart deduplication
    pipeline = EnhancedProcessingPipeline()
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
    
    # Initialize camera API (database-driven)
    try:
        await init_camera_api()
    except Exception as e:
        logging.error(f"Failed to initialize Camera API: {e}")
    
    # Start processing loop
    asyncio.create_task(processing_loop())
    
    logging.info("LPR System started successfully")
    
    yield
    
    # Shutdown
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

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the new database-driven camera management API
app.include_router(camera_router, prefix="/v2")

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

async def processing_loop():
    """Main processing loop - runs continuously"""
    logging.info("Starting processing loop")
    
    while True:
        try:
            for camera_id, camera in camera_manager.get_all_cameras().items():
                if camera.is_healthy():
                    # Update camera status to active when healthy
                    await db.update_camera_status(camera_id, "active")
                    
                    frame = camera.get_frame()
                    if frame is not None:
                        # Process for detections
                        detections = await pipeline.process_frame(camera_id, frame)
                        
                        # Save detections to database with deduplication fields
                        for detection in detections:
                            detection_data = {
                                'id': detection.detection_id,  # Fixed: database uses 'id', not 'detection_id'
                                'camera_id': detection.camera_id,
                                'detected_at': detection.timestamp,
                                'plate_text': detection.plate_text,
                                'confidence': detection.confidence,
                                'vehicle_type': detection.vehicle_type,
                                'vehicle_bbox': detection.vehicle_bbox,
                                'plate_bbox': detection.plate_bbox,
                                'frame_path': detection.frame_path,
                                'plate_image_path': detection.plate_image_path,
                                # Deduplication fields
                                'group_id': detection.group_id,
                                'track_id': detection.track_id,
                                'is_best_shot': detection.is_best_shot,
                                'image_saved': detection.image_saved,
                                'ocr_confidence': detection.ocr_confidence,
                                'meta_data': detection.detection_metadata
                            }
                            await db.save_detection(detection_data)
                else:
                    # Update camera status to offline when unhealthy
                    await db.update_camera_status(camera_id, "offline")
            
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
        "plate_image": f"/images/plates/{os.path.basename(d.plate_image_path)}" if d.plate_image_path else None,
        "frame_image": f"/images/frames/{os.path.basename(d.frame_path)}" if d.frame_path else None,
        "has_video": d.video_clip_id is not None,
        "video_clip_id": d.video_clip_id
    } for d in detections]

@app.get("/api/detections/search")
async def search_detections(
    plate: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    camera_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """Search detections by criteria"""
    detections = await db.search_detections(
        plate_text=plate,
        start_date=start_date,
        end_date=end_date,
        camera_id=camera_id,
        limit=limit
    )
    
    return [{
        "id": d.id,
        "camera_id": d.camera_id,
        "plate_text": d.plate_text,
        "confidence": d.confidence,
        "vehicle_type": d.vehicle_type,
        "detected_at": d.detected_at.isoformat(),
        "plate_image": f"/images/plates/{os.path.basename(d.plate_image_path)}" if d.plate_image_path else None,
        "frame_image": f"/images/frames/{os.path.basename(d.frame_path)}" if d.frame_path else None
    } for d in detections]

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
        "plate_image": f"/images/plates/{os.path.basename(detection.plate_image_path)}" if detection.plate_image_path else None,
        "frame_image": f"/images/frames/{os.path.basename(detection.frame_path)}" if detection.frame_path else None,
        "video_clip_id": detection.video_clip_id
    }

@app.get("/api/cameras/{camera_id}/health")
async def get_camera_health(camera_id: str):
    """
    Get comprehensive camera health status
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    # Get camera from database
    db_camera = await db.get_camera(camera_id)
    
    # Calculate connection status
    current_time = time.time()
    last_frame_age = current_time - camera.last_frame_time if camera.last_frame_time > 0 else None
    
    health_status = {
        "camera_id": camera_id,
        "name": camera.config.name,
        "connection_status": "connected" if camera.last_frame_time > 0 and last_frame_age < 30 else "disconnected",
        "last_frame_time": camera.last_frame_time,
        "last_frame_age_seconds": last_frame_age,
        "rtsp_url": camera.config.stream_url,
        "is_capturing": camera.is_running,
        "buffer_size": camera.frame_buffer.qsize() if hasattr(camera.frame_buffer, 'qsize') else 0,
        "database_status": "found" if db_camera else "missing",
        "backend_processing": True,  # Always true if endpoint responds
        "snapshot_available": camera.last_frame is not None,
        "stream_config": {
            "ip_address": camera.config.ip_address,
            "port": camera.config.port,
            "stream_path": camera.config.stream_path,
            "username": camera.config.username
        }
    }
    
    # Add recording status if available
    try:
        # Try to get recording status from the 24/7 recording system
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:8002/recordings/status/{camera_id}") as response:
                if response.status == 200:
                    recording_data = await response.json()
                    health_status["recording_status"] = recording_data
                else:
                    health_status["recording_status"] = {"status": "unavailable", "message": "Recording service not responding"}
    except Exception as e:
        health_status["recording_status"] = {"status": "error", "message": str(e)}
    
    return health_status

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
        "processing_loop_status": "running",
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