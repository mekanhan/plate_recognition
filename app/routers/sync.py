"""
Sync management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_sync_service():
    """Dependency to get sync service from app state"""
    def _get_sync_service(request: Request):
        return getattr(request.app.state, 'sync_service', None)
    return _get_sync_service

def get_device_service():
    """Dependency to get device service from app state"""
    def _get_device_service(request: Request):
        return getattr(request.app.state, 'device_service', None)
    return _get_device_service

@router.get("/status")
async def get_sync_status(sync_service = Depends(get_sync_service())):
    """Get current sync queue status"""
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")
    
    try:
        status = await sync_service.get_sync_status()
        return status
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/force")
async def force_sync_all(sync_service = Depends(get_sync_service())):
    """Force immediate sync of all pending items"""
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")
    
    try:
        result = await sync_service.force_sync_all()
        return {
            "message": "Force sync completed",
            "accepted": result.accepted_count,
            "rejected": result.rejected_count,
            "errors": result.errors
        }
    except Exception as e:
        logger.error(f"Error during force sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/failed")
async def clear_failed_items(sync_service = Depends(get_sync_service())):
    """Clear all failed sync items"""
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")
    
    try:
        count = await sync_service.clear_failed_items()
        return {
            "message": f"Cleared {count} failed items",
            "count": count
        }
    except Exception as e:
        logger.error(f"Error clearing failed items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/device/info")
async def get_device_info(device_service = Depends(get_device_service())):
    """Get device information"""
    if not device_service:
        raise HTTPException(status_code=503, detail="Device service not available")
    
    try:
        info = device_service.get_device_info()
        return info
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/device/heartbeat")
async def device_heartbeat(device_service = Depends(get_device_service())):
    """Update device last seen timestamp"""
    if not device_service:
        raise HTTPException(status_code=503, detail="Device service not available")
    
    try:
        await device_service.update_last_seen()
        return {"status": "heartbeat updated"}
    except Exception as e:
        logger.error(f"Error updating heartbeat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_sync_config(sync_service = Depends(get_sync_service())):
    """Get current sync configuration"""
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")
    
    return {
        "sync_mode": sync_service.sync_mode,
        "sync_interval": sync_service.sync_interval,
        "sync_batch_size": sync_service.sync_batch_size,
        "max_retries": sync_service.max_retries,
        "data_retention_days": sync_service.data_retention_days,
        "compression_threshold": sync_service.compression_threshold
    }

@router.post("/test-connection")
async def test_cloud_connection(device_service = Depends(get_device_service())):
    """Test connection to cloud platform"""
    if not device_service:
        raise HTTPException(status_code=503, detail="Device service not available")
    
    try:
        # Try to validate device with cloud
        is_valid = await device_service._validate_device()
        
        return {
            "connected": is_valid,
            "endpoint": device_service.cloud_endpoint,
            "device_id": device_service.device_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error testing cloud connection: {e}")
        return {
            "connected": False,
            "error": str(e),
            "endpoint": device_service.cloud_endpoint if device_service else "unknown"
        }