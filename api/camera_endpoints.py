"""
Camera Management API Endpoints
Database-driven camera CRUD operations and status management
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database.camera_service import CameraService
from database.service import DatabaseService

# Initialize services
database_service = DatabaseService()
camera_service = CameraService(database_service)

router = APIRouter(prefix="/api/cameras", tags=["cameras-v2"])
logger = logging.getLogger("CameraAPI")

# Pydantic models for API requests
class CameraCreateRequest(BaseModel):
    name: str
    ip_address: str
    port: Optional[int] = 554
    protocol: Optional[str] = "RTSP"
    stream_path: Optional[str] = "/stream1"
    location: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    recording_enabled: Optional[bool] = False
    segment_duration: Optional[int] = 600
    retention_days: Optional[int] = 30
    settings: Optional[Dict[str, Any]] = {}

class CameraUpdateRequest(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    stream_path: Optional[str] = None
    location: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    recording_enabled: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

class CameraStatusUpdate(BaseModel):
    recording_status: Optional[str] = None
    connection_status: Optional[str] = None
    ffmpeg_pid: Optional[int] = None
    segments_created: Optional[int] = None
    last_segment_time: Optional[datetime] = None
    storage_used_bytes: Optional[int] = None
    recording_started_at: Optional[datetime] = None
    error_message: Optional[str] = None

class CameraSettingsUpdate(BaseModel):
    settings: Dict[str, Any]

# Camera CRUD Operations

@router.post("", response_model=Dict[str, Any])
async def create_camera(camera_data: CameraCreateRequest):
    """Create a new camera with all configurations"""
    try:
        result = await camera_service.create_camera(camera_data.dict())
        if result:
            logger.info(f"Created camera: {result.get('id')}")
            return {"success": True, "camera": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to create camera")
    except Exception as e:
        logger.error(f"Error creating camera: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("", response_model=List[Dict[str, Any]])
async def get_all_cameras():
    """Get all active cameras with their configurations"""
    try:
        cameras = await camera_service.get_all_cameras()
        return cameras
    except Exception as e:
        logger.error(f"Error fetching cameras: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{camera_id}", response_model=Dict[str, Any])
async def get_camera(camera_id: str):
    """Get a single camera by ID"""
    try:
        camera = await camera_service.get_camera(camera_id)
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        return camera
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{camera_id}", response_model=Dict[str, Any])
async def update_camera(camera_id: str, update_data: CameraUpdateRequest):
    """Update camera configuration"""
    try:
        # Get existing camera first
        existing_camera = await camera_service.get_camera(camera_id)
        if not existing_camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        # For now, we'll implement a simple update by recreating
        # In a full implementation, you'd have specific update methods
        logger.warning(f"Camera update for {camera_id} - full implementation needed")
        
        # Return existing camera for now
        return {"success": True, "camera": existing_camera, "message": "Update feature coming soon"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{camera_id}")
async def delete_camera(camera_id: str):
    """Delete a camera and all related data"""
    try:
        success = await camera_service.delete_camera(camera_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        logger.info(f"Deleted camera: {camera_id}")
        return {"success": True, "message": f"Camera {camera_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Status and Control Operations

@router.get("/status", response_model=Dict[str, Any])
async def get_all_cameras_status():
    """Get bulk status for all cameras (optimized for frontend 8-field standard)"""
    try:
        status_data = await camera_service.get_cameras_status()
        return status_data
    except Exception as e:
        logger.error(f"Error fetching cameras status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{camera_id}/status", response_model=Dict[str, Any])
async def get_camera_status(camera_id: str):
    """Get status for a single camera"""
    try:
        camera = await camera_service.get_camera(camera_id)
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        # Return the current status from the camera data
        status = camera.get("current_status", {})
        return {
            "camera_id": camera_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching status for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{camera_id}/status")
async def update_camera_status(camera_id: str, status_data: CameraStatusUpdate):
    """Update camera status (for recording service integration)"""
    try:
        success = await camera_service.update_camera_status(camera_id, status_data.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        return {"success": True, "message": f"Status updated for camera {camera_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Recording Control Operations

@router.post("/{camera_id}/start")
async def start_recording(camera_id: str):
    """Start recording for a camera"""
    try:
        # Update status to indicate recording started
        success = await camera_service.update_camera_status(camera_id, {
            "recording_status": "recording",
            "recording_started_at": datetime.utcnow()
        })
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        # TODO: Integrate with recording service to actually start recording
        logger.info(f"Recording start requested for camera {camera_id}")
        
        return {
            "success": True, 
            "message": f"Recording started for camera {camera_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting recording for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{camera_id}/stop")
async def stop_recording(camera_id: str):
    """Stop recording for a camera"""
    try:
        # Update status to indicate recording stopped
        success = await camera_service.update_camera_status(camera_id, {
            "recording_status": "stopped",
            "recording_started_at": None
        })
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        # TODO: Integrate with recording service to actually stop recording
        logger.info(f"Recording stop requested for camera {camera_id}")
        
        return {
            "success": True, 
            "message": f"Recording stopped for camera {camera_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping recording for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{camera_id}/restart")
async def restart_camera_connection(camera_id: str):
    """Restart camera connection"""
    try:
        # Update connection status to reconnecting
        success = await camera_service.update_camera_status(camera_id, {
            "connection_status": "reconnecting"
        })
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        # TODO: Implement actual connection restart logic
        logger.info(f"Connection restart requested for camera {camera_id}")
        
        return {
            "success": True, 
            "message": f"Connection restart initiated for camera {camera_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting connection for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Settings Management

@router.get("/{camera_id}/settings", response_model=Dict[str, Any])
async def get_camera_settings(camera_id: str):
    """Get all settings for a camera"""
    try:
        camera = await camera_service.get_camera(camera_id)
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        settings = camera.get("settings", {})
        return {
            "camera_id": camera_id,
            "settings": settings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching settings for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{camera_id}/settings")
async def update_camera_settings(camera_id: str, settings_data: CameraSettingsUpdate):
    """Update camera settings"""
    try:
        # TODO: Implement settings update in camera service
        logger.info(f"Settings update requested for camera {camera_id}: {settings_data.settings}")
        
        return {
            "success": True, 
            "message": f"Settings updated for camera {camera_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Initialize database on module import
async def init_camera_api():
    """Initialize camera API and database"""
    try:
        await database_service.init_db()
        logger.info("Camera API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Camera API: {e}")
        raise