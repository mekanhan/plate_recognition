# app/routers/cameras.py
# Camera management API endpoints for centralized architecture
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import asyncio
import json
import io

from app.services.multi_camera_service import MultiCameraService
from app.services.camera_registry_service import CameraRegistryService
from app.services.location_service import LocationService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Service instances (will be injected)
multi_camera_service: Optional[MultiCameraService] = None
camera_registry_service: Optional[CameraRegistryService] = None
location_service: Optional[LocationService] = None

# Pydantic models for API
class CameraCreateRequest(BaseModel):
    name: str = Field(..., description="Camera name")
    ip_address: str = Field(..., description="Camera IP address")
    location_id: str = Field(..., description="Location ID")
    camera_group_id: Optional[str] = Field(None, description="Camera group ID")
    camera_type: str = Field("ip_camera", description="Camera type")
    manufacturer: Optional[str] = Field(None, description="Camera manufacturer")
    model: Optional[str] = Field(None, description="Camera model")
    username: str = Field("admin", description="Camera username")
    password: str = Field("", description="Camera password")
    resolution_width: int = Field(1920, description="Camera resolution width")
    resolution_height: int = Field(1080, description="Camera resolution height")
    fps: int = Field(30, description="Camera FPS")
    installation_location: Optional[str] = Field(None, description="Installation location")
    viewing_direction: Optional[str] = Field(None, description="Viewing direction")

class CameraUpdateRequest(BaseModel):
    name: Optional[str] = None
    camera_group_id: Optional[str] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[int] = None
    detection_enabled: Optional[bool] = None
    recording_enabled: Optional[bool] = None
    installation_location: Optional[str] = None
    viewing_direction: Optional[str] = None

class CameraGroupCreateRequest(BaseModel):
    name: str = Field(..., description="Group name")
    location_id: str = Field(..., description="Location ID")
    description: Optional[str] = Field(None, description="Group description")
    purpose: Optional[str] = Field(None, description="Group purpose")
    detection_threshold: float = Field(0.7, description="Detection threshold")
    processing_enabled: bool = Field(True, description="Processing enabled")
    recording_enabled: bool = Field(True, description="Recording enabled")
    alert_enabled: bool = Field(True, description="Alert enabled")

class CameraDiscoveryRequest(BaseModel):
    ip_range: str = Field("192.168.1.0/24", description="IP range to scan")
    location_id: str = Field(..., description="Location ID for discovered cameras")

# Dependency injection
async def get_multi_camera_service() -> MultiCameraService:
    if multi_camera_service is None:
        raise HTTPException(status_code=503, detail="MultiCameraService not available")
    return multi_camera_service

async def get_camera_registry_service() -> CameraRegistryService:
    if camera_registry_service is None:
        raise HTTPException(status_code=503, detail="CameraRegistryService not available")
    return camera_registry_service

async def get_location_service() -> LocationService:
    if location_service is None:
        raise HTTPException(status_code=503, detail="LocationService not available")
    return location_service

# Camera management endpoints
@router.get("/", response_model=List[Dict[str, Any]])
async def get_cameras(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    group_id: Optional[str] = Query(None, description="Filter by group ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    include_inactive: bool = Query(False, description="Include inactive cameras"),
    limit: int = Query(50, ge=1, le=100, description="Maximum cameras to return"),
    registry: CameraRegistryService = Depends(get_camera_registry_service),
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Get list of cameras with optional filtering"""
    try:
        if location_id:
            cameras = await registry.get_cameras_by_location(location_id, include_inactive)
        elif group_id:
            cameras = await registry.get_cameras_by_group(group_id)
        else:
            cameras = await multi_cam.get_all_cameras()
        
        # Apply status filter
        if status:
            cameras = [c for c in cameras if c.get("status") == status]
        
        # Apply limit
        cameras = cameras[:limit]
        
        return cameras
        
    except Exception as e:
        logger.error(f"Failed to get cameras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Dict[str, str])
async def create_camera(
    camera_data: CameraCreateRequest,
    background_tasks: BackgroundTasks,
    registry: CameraRegistryService = Depends(get_camera_registry_service),
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Create a new camera"""
    try:
        # Register camera in registry
        camera_id = await registry.register_camera(camera_data.dict())
        
        # Add camera to multi-camera service
        await multi_cam.add_camera(camera_data.dict())
        
        # Start camera stream in background
        background_tasks.add_task(multi_cam.start_camera_stream, camera_id)
        
        return {"camera_id": camera_id, "message": "Camera created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}", response_model=Dict[str, Any])
async def get_camera(
    camera_id: str,
    include_health: bool = Query(True, description="Include health information"),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get specific camera information"""
    try:
        cameras = await registry.get_cameras_by_location("")  # Get all cameras
        camera = next((c for c in cameras if c["id"] == camera_id), None)
        
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        if include_health:
            health = await registry.get_camera_health(camera_id)
            camera["health"] = health
        
        return camera
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{camera_id}", response_model=Dict[str, str])
async def update_camera(
    camera_id: str,
    updates: CameraUpdateRequest,
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Update camera configuration"""
    try:
        # TODO: Implement camera update in registry service
        # For now, return success
        return {"camera_id": camera_id, "message": "Camera updated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to update camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{camera_id}", response_model=Dict[str, str])
async def delete_camera(
    camera_id: str,
    registry: CameraRegistryService = Depends(get_camera_registry_service),
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Delete a camera"""
    try:
        # Stop camera stream
        await multi_cam.stop_camera_stream(camera_id)
        
        # Remove from multi-camera service
        await multi_cam.remove_camera(camera_id)
        
        # Unregister from registry
        success = await registry.unregister_camera(camera_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        return {"camera_id": camera_id, "message": "Camera deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera streaming endpoints
@router.get("/{camera_id}/stream")
async def get_camera_stream(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Get live video stream from camera"""
    try:
        async def generate_frames():
            while True:
                try:
                    frame_data, timestamp = await multi_cam.get_camera_jpeg_frame(camera_id)
                    
                    if frame_data is None:
                        # Return placeholder frame
                        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b'placeholder' + b'\r\n'
                    else:
                        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n'
                    
                    await asyncio.sleep(0.1)  # ~10 FPS for web streaming
                    
                except Exception as e:
                    logger.error(f"Stream error for camera {camera_id}: {e}")
                    break
        
        return StreamingResponse(
            generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Failed to get camera stream {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/snapshot")
async def get_camera_snapshot(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Get single snapshot from camera"""
    try:
        frame_data, timestamp = await multi_cam.get_camera_jpeg_frame(camera_id)
        
        if frame_data is None:
            raise HTTPException(status_code=404, detail="No frame available")
        
        return StreamingResponse(
            io.BytesIO(frame_data),
            media_type="image/jpeg",
            headers={"X-Timestamp": str(timestamp)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera snapshot {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera control endpoints
@router.post("/{camera_id}/start", response_model=Dict[str, str])
async def start_camera_stream(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Start camera stream"""
    try:
        success = await multi_cam.start_camera_stream(camera_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start camera stream")
        
        return {"camera_id": camera_id, "message": "Camera stream started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start camera stream {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/stop", response_model=Dict[str, str])
async def stop_camera_stream(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Stop camera stream"""
    try:
        success = await multi_cam.stop_camera_stream(camera_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop camera stream")
        
        return {"camera_id": camera_id, "message": "Camera stream stopped"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop camera stream {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera discovery endpoints
@router.post("/discover", response_model=List[Dict[str, Any]])
async def discover_cameras(
    discovery_request: CameraDiscoveryRequest,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Discover cameras on network"""
    try:
        discovered_cameras = await multi_cam.discover_cameras_on_network(
            discovery_request.ip_range
        )
        
        return discovered_cameras
        
    except Exception as e:
        logger.error(f"Failed to discover cameras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera group management
@router.get("/groups/", response_model=List[Dict[str, Any]])
async def get_camera_groups(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get camera groups"""
    try:
        # TODO: Implement get_groups in registry service
        return []
        
    except Exception as e:
        logger.error(f"Failed to get camera groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/", response_model=Dict[str, str])
async def create_camera_group(
    group_data: CameraGroupCreateRequest,
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Create camera group"""
    try:
        group_id = await registry.create_camera_group(group_data.dict())
        
        return {"group_id": group_id, "message": "Camera group created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create camera group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/assign-group", response_model=Dict[str, str])
async def assign_camera_to_group(
    camera_id: str,
    group_id: str = Query(..., description="Group ID"),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Assign camera to group"""
    try:
        success = await registry.assign_camera_to_group(camera_id, group_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to assign camera to group")
        
        return {"camera_id": camera_id, "group_id": group_id, "message": "Camera assigned to group"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign camera to group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera health and statistics
@router.get("/{camera_id}/health", response_model=Dict[str, Any])
async def get_camera_health(
    camera_id: str,
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get camera health information"""
    try:
        health = await registry.get_camera_health(camera_id)
        
        if not health:
            raise HTTPException(status_code=404, detail="Camera health not found")
        
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera health {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/processing-queue", response_model=List[Dict[str, Any]])
async def get_camera_processing_queue(
    camera_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum queue items"),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get camera processing queue"""
    try:
        queue = await registry.get_camera_processing_queue(camera_id, limit)
        
        return queue
        
    except Exception as e:
        logger.error(f"Failed to get processing queue for {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System statistics
@router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_camera_system_statistics(
    multi_cam: MultiCameraService = Depends(get_multi_camera_service),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get overall camera system statistics"""
    try:
        multi_cam_stats = await multi_cam.get_system_stats()
        registry_stats = await registry.get_registry_statistics()
        
        combined_stats = {
            **multi_cam_stats,
            **registry_stats,
            "service": "centralized_camera_system",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return combined_stats
        
    except Exception as e:
        logger.error(f"Failed to get camera system statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))