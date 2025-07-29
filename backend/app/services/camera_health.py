"""
Camera Health Monitoring Service

Provides automatic health checking for cameras to maintain accurate status information.
"""
import asyncio
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, Camera
from app.services.camera_crud import get_cameras, update_camera_status

logger = logging.getLogger(__name__)


async def test_camera_connectivity(ip_address: str, port: int, timeout: float = 3.0) -> bool:
    """
    Test if a camera is reachable on the specified IP and port
    
    Args:
        ip_address: Camera IP address
        port: Camera port number
        timeout: Connection timeout in seconds
        
    Returns:
        True if camera is reachable, False otherwise
    """
    try:
        future = asyncio.open_connection(ip_address, port)
        reader, writer = await asyncio.wait_for(future, timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception as e:
        logger.debug(f"Camera {ip_address}:{port} unreachable: {e}")
        return False


async def check_camera_health(camera: Camera) -> str:
    """
    Check health of a single camera and determine its status
    
    Args:
        camera: Camera object to check
        
    Returns:
        New status: "online" if reachable, "offline" if not, "error" unchanged
    """
    # Don't auto-update cameras that are manually set to "error" status
    # This allows manual intervention for problematic cameras
    if camera.status == "error":
        return "error"
    
    # Test camera connectivity
    is_reachable = await test_camera_connectivity(camera.ip_address, camera.port)
    
    if is_reachable:
        new_status = "online"
        logger.debug(f"Camera {camera.id} ({camera.name}) is reachable - setting to online")
    else:
        new_status = "offline"
        logger.debug(f"Camera {camera.id} ({camera.name}) is unreachable - setting to offline")
    
    return new_status


async def check_all_camera_health():
    """
    Check health of all cameras and update their status in the database
    """
    try:
        async with AsyncSessionLocal() as db:
            # Get all cameras
            cameras = await get_cameras(db, skip=0, limit=1000)
            
            if not cameras:
                logger.debug("No cameras found for health check")
                return
            
            logger.info(f"Starting health check for {len(cameras)} cameras")
            
            # Check each camera's health
            status_updates = []
            for camera in cameras:
                try:
                    new_status = await check_camera_health(camera)
                    
                    # Only update if status changed
                    if new_status != camera.status:
                        status_updates.append((camera.id, camera.name, camera.status, new_status))
                        await update_camera_status(db, camera.id, new_status)
                        
                except Exception as e:
                    logger.error(f"Error checking camera {camera.id} ({camera.name}): {e}")
            
            # Log status changes
            if status_updates:
                logger.info(f"Camera status updates:")
                for camera_id, name, old_status, new_status in status_updates:
                    logger.info(f"  Camera {camera_id} ({name}): {old_status} → {new_status}")
            else:
                logger.debug("No camera status changes needed")
                
    except Exception as e:
        logger.error(f"Error during camera health check: {e}")


async def camera_health_monitor():
    """
    Background task that periodically checks camera health
    
    Runs every 5 minutes to update camera statuses automatically
    """
    logger.info("Camera health monitor started")
    
    while True:
        try:
            await check_all_camera_health()
            
            # Wait 5 minutes before next check
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Error in camera health monitor: {e}")
            # Wait 30 seconds before retrying on error
            await asyncio.sleep(30)


def start_camera_health_monitor():
    """
    Start the camera health monitoring background task
    
    This should be called during application startup
    """
    task = asyncio.create_task(camera_health_monitor())
    logger.info("Camera health monitor task created")
    return task