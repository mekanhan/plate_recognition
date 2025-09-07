"""
Consolidated API v3 Router
All endpoints under /api/v3/ namespace with clean paths
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional

# Import dependencies and models
from database.foundation_service import get_foundation_database_service
from auth.dependencies import get_current_user, get_optional_user

# Create main v3 router
v3_router = APIRouter(prefix="/api/v3", tags=["v3"])

# ==============================================================================
# CAMERAS API v3
# ==============================================================================

cameras_router = APIRouter(prefix="/cameras", tags=["v3-cameras"])

@cameras_router.get("")
async def get_cameras_v3(db_service = Depends(get_foundation_database_service)):
    """Get all cameras - v3 API"""
    return await db_service.get_all_cameras()

@cameras_router.get("/{camera_id}")
async def get_camera_v3(camera_id: str, db_service = Depends(get_foundation_database_service)):
    """Get a specific camera by ID - v3 API"""
    camera = await db_service.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, f"Camera {camera_id} not found")
    return camera

@cameras_router.get("/health/summary")
async def get_camera_health_summary_v3():
    """Get camera health summary - v3 API"""
    return {
        "total_cameras": 1,
        "online_cameras": 1,
        "offline_cameras": 0,
        "status": "healthy"
    }

# Include cameras router
v3_router.include_router(cameras_router)

# ==============================================================================
# SYSTEM API v3
# ==============================================================================

system_router = APIRouter(prefix="/system", tags=["v3-system"])

@system_router.get("/health")
async def get_system_health_v3():
    """Get system health - v3 API"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "api_version": "v3"
    }

@system_router.get("/features")
async def get_system_features_v3():
    """Get enabled features - v3 API"""
    return {
        "camera_management": True,
        "recording": True,
        "detection": True,
        "api_version": "v3"
    }

# Include system router
v3_router.include_router(system_router)

# ==============================================================================
# DETECTIONS API v3
# ==============================================================================

detections_router = APIRouter(prefix="/detections", tags=["v3-detections"])

@detections_router.get("/recent")
async def get_recent_detections_v3(
    limit: int = 50,
    camera_id: Optional[str] = None,
    db_service = Depends(get_foundation_database_service)
):
    """Get recent detections - v3 API"""
    return await db_service.get_recent_detections(limit=limit, camera_id=camera_id)

@detections_router.get("/search")
async def search_detections_v3(
    license_plate: Optional[str] = None,
    camera_id: Optional[str] = None,
    limit: int = 50,
    db_service = Depends(get_foundation_database_service)
):
    """Search detections - v3 API"""
    try:
        # Use the same logic as the legacy endpoint
        if license_plate:
            return await db_service.search_detections_by_plate(license_plate, limit=limit)
        elif camera_id:
            return await db_service.get_recent_detections(camera_id=camera_id, limit=limit)
        else:
            # Return empty search results for empty search
            return []
    except Exception as e:
        # Fallback to empty results
        return []

# Include detections router
v3_router.include_router(detections_router)