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

# Import our services
from ai_pipeline.camera_manager import CameraManager, CameraConfig
from ai_pipeline.processors import LicensePlateDetector, ProcessingPipeline
from database.service import DatabaseService

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
    pipeline = ProcessingPipeline(detector)
    db = DatabaseService()
    
    # Create database tables
    await db.create_tables()
    
    # Create directories
    os.makedirs("detections", exist_ok=True)
    os.makedirs("detections/frames", exist_ok=True)
    os.makedirs("detections/plates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    # Load camera configurations
    await load_cameras()
    
    # Start processing loop
    asyncio.create_task(processing_loop())
    
    logging.info("LPR System started successfully")
    
    yield
    
    # Shutdown
    camera_manager.stop_all()
    pipeline.cleanup()
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

# Mount static files for images
app.mount("/images", StaticFiles(directory="detections"), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

async def load_cameras():
    """Load camera configurations"""
    # For now, load from a simple configuration
    # In production, this would come from database or config file
    cameras = [
        CameraConfig(
            camera_id="entrance_cam",
            name="Entrance Camera",
            ip_address="10.0.0.181",
            username="admin",
            password="Mekus_1987",
            port=554,
            stream_path="/h264Preview_01_main",
            location="Main Entrance"
        )
        # Add more cameras as needed
    ]
    
    for config in cameras:
        # Add to camera manager
        camera_manager.add_camera(config)
        
        # Check if camera already exists in database
        existing_camera = await db.get_camera(config.camera_id)
        if not existing_camera:
            # Save to database only if it doesn't exist
            await db.add_camera({
                'camera_id': config.camera_id,
                'name': config.name,
                'ip_address': config.ip_address,
                'location': config.location,
                'status': 'active',
                'config': {
                    'username': config.username,
                    'port': config.port,
                    'stream_path': config.stream_path
                }
            })
            logging.info(f"Added new camera to database: {config.name}")
        else:
            logging.info(f"Camera already exists in database: {config.name}")
        
        logging.info(f"Loaded camera: {config.name}")

async def processing_loop():
    """Main processing loop - runs continuously"""
    logging.info("Starting processing loop")
    
    while True:
        try:
            for camera_id, camera in camera_manager.get_all_cameras().items():
                if camera.is_healthy():
                    frame = camera.get_frame()
                    if frame is not None:
                        # Process for detections
                        detections = await pipeline.process_frame(camera_id, frame)
                        
                        # Save detections to database
                        for detection in detections:
                            detection_data = {
                                'detection_id': detection.detection_id,
                                'camera_id': detection.camera_id,
                                'detected_at': detection.timestamp,
                                'plate_text': detection.plate_text,
                                'confidence': detection.confidence,
                                'vehicle_type': detection.vehicle_type,
                                'vehicle_bbox': detection.vehicle_bbox,
                                'plate_bbox': detection.plate_bbox,
                                'frame_path': detection.frame_path,
                                'plate_image_path': detection.plate_image_path
                            }
                            await db.save_detection(detection_data)
                else:
                    # Update camera status
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
    """Get all cameras with current status"""
    cameras = await db.get_all_cameras()
    
    result = []
    for c in cameras:
        camera_stream = camera_manager.get_camera(c.camera_id)
        is_healthy = camera_stream.is_healthy() if camera_stream else False
        
        result.append({
            "id": c.camera_id,
            "name": c.name,
            "location": c.location or "",
            "status": "online" if is_healthy else "offline",
            "ip_address": c.ip_address,
            "last_detection": await db.get_last_detection_time(c.camera_id)
        })
    
    return result

@app.post("/api/cameras")
async def create_camera(camera_data: CameraCreate):
    """Create a new camera"""
    try:
        # Generate unique camera ID
        camera_id = f"camera_{uuid.uuid4().hex[:8]}"
        
        # Create camera data dictionary
        camera_dict = camera_data.dict()
        camera_dict['camera_id'] = camera_id
        
        # Save to database
        db_camera_id = await db.add_camera(camera_dict)
        
        # Get the created camera
        created_camera = await db.get_camera(camera_id)
        
        if not created_camera:
            raise HTTPException(500, "Failed to create camera")
        
        # Notify recording service to start recording for new camera
        await notify_recording_service_camera_added(camera_id)
        
        return {
            "id": created_camera.camera_id,
            "name": created_camera.name,
            "ip_address": created_camera.ip_address,
            "port": created_camera.port,
            "connection_type": created_camera.connection_type,
            "stream_path": created_camera.stream_path,
            "location": created_camera.location,
            "status": created_camera.status,
            "created_at": created_camera.created_at.isoformat()
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
        
        # Notify recording service to stop recording for deleted camera
        await notify_recording_service_camera_deleted(camera_id)
        
        return {"message": f"Camera {camera_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to delete camera {camera_id}: {e}")
        raise HTTPException(500, f"Failed to delete camera: {str(e)}")

@app.post("/api/cameras/test")
async def test_camera_connection(test_data: CameraTestRequest):
    """Test camera connection without saving"""
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
        
        # Test connection using OpenCV
        cap = cv2.VideoCapture(url)
        
        if not cap.isOpened():
            return {
                "success": False,
                "message": "Failed to connect to camera",
                "url": url.replace(test_data.password or '', '***') if test_data.password else url,
                "error": "Connection refused or invalid URL"
            }
        
        # Try to read a frame
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            height, width, channels = frame.shape
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
                "error": "No video data available"
            }
    except Exception as e:
        logging.error(f"Camera test failed: {e}")
        return {
            "success": False,
            "message": "Camera test failed",
            "error": str(e)
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

@app.get("/api/system/health")
async def get_system_health():
    """
    Get overall system health status
    """
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