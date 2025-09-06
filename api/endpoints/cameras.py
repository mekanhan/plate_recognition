"""
Camera management endpoints
Extracted from monolithic main.py for better organization
"""
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import cv2
import io
import os
import time
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Optional, List, Dict, Any

# Import our core utilities
from ..core.errors import (
    APIError, CameraNotFoundError, CameraConnectionError, 
    ValidationError, log_and_raise_error
)

# Import services and utilities
from database.foundation_service import get_foundation_database_service
from utils.camera_utils import generate_camera_id, validate_camera_id, CameraValidation, CameraDisplayUtils
from utils.feature_flags import feature_flags
from auth.dependencies import get_current_user, require_camera_view, require_camera_manage
from auth.models import User

# Create camera router
router = APIRouter(prefix="/api/cameras", tags=["cameras"])

logger = logging.getLogger(__name__)

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

class CameraTestRequest(BaseModel):
    name: str
    ip_address: str
    port: int = 80
    connection_type: str = "http"
    stream_path: str = "/mjpeg"
    username: str = "admin"
    password: str = ""

# Helper functions (extracted from main.py)
async def notify_recording_service(endpoint: str, data: Dict = None):
    """Notify recording service of camera changes"""
    try:
        # Implementation would use aiohttp to notify recording service
        # For now, just log the notification
        logger.info(f"Would notify recording service: {endpoint} with data: {data}")
        return True
    except Exception as e:
        logger.warning(f"Failed to notify recording service: {e}")
        return False

# Camera CRUD endpoints
@router.get("", dependencies=[Depends(require_camera_view)])
async def get_cameras(db_service = Depends(get_foundation_database_service)):
    """Get all cameras with real-time connection status"""
    try:
        cameras = await db_service.get_all_cameras()
        
        result = []
        for c in cameras:
            connection_status = c.status if c.status else "offline"
            
            result.append({
                "id": c.camera_id,
                "camera_id": c.camera_id,
                "name": c.name,
                "display_name": c.name,
                "short_id": c.camera_id[-8:],
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
                "last_detection": await db_service.get_last_detection_time(c.camera_id),
                "last_test_result": c.last_test_result,
                "last_test_at": c.last_test_at.isoformat() if c.last_test_at else None
            })
        
        return result
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get cameras")

@router.post("", dependencies=[Depends(require_camera_manage)])
async def create_camera(
    camera_data: CameraCreate, 
    db_service = Depends(get_foundation_database_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new camera"""
    try:
        # Generate unique camera ID using utility function
        camera_id = generate_camera_id()
        
        # Create camera data dictionary
        camera_dict = camera_data.dict()
        camera_dict['camera_id'] = camera_id
        camera_dict['status'] = 'active'
        camera_dict['created_at'] = datetime.utcnow()
        camera_dict['updated_at'] = datetime.utcnow()
        
        # Save to database
        await db_service.create_camera(camera_dict)
        
        # Notify recording service
        await notify_recording_service("camera_added", {"camera_id": camera_id})
        
        # Get the created camera
        camera = await db_service.get_camera(camera_id)
        if not camera:
            raise APIError(500, "Failed to retrieve created camera")
        
        logger.info(f"Camera {camera_id} created by user {current_user.username}")
        
        return {
            "id": camera.camera_id,
            "camera_id": camera.camera_id,
            "name": camera.name,
            "status": "created",
            "message": "Camera created successfully"
        }
        
    except Exception as e:
        log_and_raise_error(e, f"Failed to create camera: {camera_data.name}")

@router.get("/{camera_id}", dependencies=[Depends(require_camera_view)])
async def get_camera(camera_id: str, db_service = Depends(get_foundation_database_service)):
    """Get a specific camera by ID"""
    try:
        camera = await db_service.get_camera(camera_id)
        if not camera:
            raise CameraNotFoundError(camera_id)
        
        return {
            "id": camera.camera_id,
            "camera_id": camera.camera_id,
            "name": camera.name,
            "display_name": camera.name,
            "location": camera.location or "",
            "status": camera.status or "offline",
            "ip_address": camera.ip_address,
            "port": camera.port,
            "connection_type": camera.connection_type,
            "stream_path": camera.stream_path,
            "username": camera.username,
            "password": camera.password,
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
        
    except Exception as e:
        log_and_raise_error(e, f"Failed to get camera {camera_id}")

@router.put("/{camera_id}", dependencies=[Depends(require_camera_manage)])
async def update_camera(
    camera_id: str, 
    camera_data: CameraUpdate,
    db_service = Depends(get_foundation_database_service),
    current_user: User = Depends(get_current_user)
):
    """Update a camera"""
    try:
        # Check if camera exists
        existing_camera = await db_service.get_camera(camera_id)
        if not existing_camera:
            raise CameraNotFoundError(camera_id)
        
        # Update only provided fields
        update_data = {k: v for k, v in camera_data.dict().items() if v is not None}
        update_data['updated_at'] = datetime.utcnow()
        
        # Update in database
        await db_service.update_camera(camera_id, update_data)
        
        # Notify recording service
        await notify_recording_service("camera_updated", {"camera_id": camera_id})
        
        logger.info(f"Camera {camera_id} updated by user {current_user.username}")
        
        return {
            "id": camera_id,
            "status": "updated",
            "message": "Camera updated successfully"
        }
        
    except Exception as e:
        log_and_raise_error(e, f"Failed to update camera {camera_id}")

@router.delete("/{camera_id}", dependencies=[Depends(require_camera_manage)])
async def delete_camera(
    camera_id: str,
    db_service = Depends(get_foundation_database_service),
    current_user: User = Depends(get_current_user)
):
    """Delete a camera"""
    try:
        # Check if camera exists
        camera = await db_service.get_camera(camera_id)
        if not camera:
            raise CameraNotFoundError(camera_id)
        
        # Delete from database
        await db_service.delete_camera(camera_id)
        
        # Notify recording service
        await notify_recording_service("camera_deleted", {"camera_id": camera_id})
        
        logger.info(f"Camera {camera_id} deleted by user {current_user.username}")
        
        return {
            "id": camera_id,
            "status": "deleted",
            "message": "Camera deleted successfully"
        }
        
    except Exception as e:
        log_and_raise_error(e, f"Failed to delete camera {camera_id}")

@router.post("/{camera_id}/test", dependencies=[Depends(require_camera_manage)])
async def test_camera_connection(
    camera_id: str,
    db_service = Depends(get_foundation_database_service)
):
    """Test camera connection"""
    try:
        camera = await db_service.get_camera(camera_id)
        if not camera:
            raise CameraNotFoundError(camera_id)
        
        # Test connection using camera validation utility
        validation = CameraValidation(
            camera.ip_address,
            camera.port,
            camera.username,
            camera.password
        )
        
        test_result = await validation.test_connection()
        
        # Update test results in database
        await db_service.update_camera(camera_id, {
            'last_test_result': 'success' if test_result.success else 'failed',
            'last_test_at': datetime.utcnow()
        })
        
        if test_result.success:
            return {
                "camera_id": camera_id,
                "status": "success",
                "message": "Camera connection test passed",
                "details": test_result.details
            }
        else:
            raise CameraConnectionError(camera_id, test_result.error_message)
            
    except Exception as e:
        log_and_raise_error(e, f"Failed to test camera {camera_id}")

@router.get("/{camera_id}/snapshot", dependencies=[Depends(require_camera_view)])
async def get_camera_snapshot(
    camera_id: str,
    db_service = Depends(get_foundation_database_service)
):
    """Get a snapshot from the camera"""
    try:
        camera = await db_service.get_camera(camera_id)
        if not camera:
            raise CameraNotFoundError(camera_id)
        
        # For now, return a placeholder image
        # In full implementation, this would capture from the camera stream
        placeholder_path = "static/images/camera-offline.png"
        
        if os.path.exists(placeholder_path):
            return FileResponse(placeholder_path, media_type="image/png")
        else:
            # Generate a simple placeholder
            import numpy as np
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(img, f"Camera {camera_id[-8:]}", (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            _, buffer = cv2.imencode('.png', img)
            return StreamingResponse(io.BytesIO(buffer.tobytes()), media_type="image/png")
            
    except Exception as e:
        log_and_raise_error(e, f"Failed to get snapshot for camera {camera_id}")

# Legacy endpoint for compatibility
@router.get("/list", dependencies=[Depends(require_camera_view)])
async def get_cameras_list(db_service = Depends(get_foundation_database_service)):
    """Legacy endpoint - use GET /api/cameras instead"""
    return await get_cameras(db_service)