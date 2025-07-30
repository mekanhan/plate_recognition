"""
Camera CRUD operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.database import Camera
from app.schemas.camera import CameraCreate, CameraUpdate


async def get_cameras(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Camera]:
    """Get list of cameras with pagination"""
    result = await db.execute(
        select(Camera)
        .offset(skip)
        .limit(limit)
        .order_by(Camera.created_at.desc())
    )
    return result.scalars().all()


async def get_camera_count(db: AsyncSession) -> int:
    """Get total count of cameras"""
    from sqlalchemy import func
    result = await db.execute(select(func.count(Camera.id)))
    return result.scalar()


async def get_camera_by_id(db: AsyncSession, camera_id: int) -> Optional[Camera]:
    """Get camera by ID"""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    return result.scalar_one_or_none()


async def get_camera_by_ip(db: AsyncSession, ip_address: str) -> Optional[Camera]:
    """Get camera by IP address"""
    result = await db.execute(select(Camera).where(Camera.ip_address == ip_address))
    return result.scalar_one_or_none()


async def create_camera(db: AsyncSession, camera: CameraCreate) -> Camera:
    """Create a new camera"""
    db_camera = Camera(
        name=camera.name,
        ip_address=camera.ip_address,
        port=camera.port,
        connection_type=camera.connection_type,
        stream_path=camera.stream_path,
        location=camera.location,
        username=camera.username,
        password=camera.password,
        enabled=camera.enabled,
        status="offline",  # Default to offline until tested
    )
    
    db.add(db_camera)
    await db.commit()
    await db.refresh(db_camera)
    return db_camera


async def update_camera(db: AsyncSession, camera_id: int, camera_update: CameraUpdate) -> Optional[Camera]:
    """Update an existing camera"""
    db_camera = await get_camera_by_id(db, camera_id)
    if not db_camera:
        return None
    
    # Update only provided fields
    update_data = camera_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        for field, value in update_data.items():
            setattr(db_camera, field, value)
        
        await db.commit()
        await db.refresh(db_camera)
    
    return db_camera


async def delete_camera(db: AsyncSession, camera_id: int) -> bool:
    """Delete a camera by ID and clean up all related data"""
    import shutil
    import os
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    db_camera = await get_camera_by_id(db, camera_id)
    if not db_camera:
        return False
    
    logger.info(f"Deleting camera {camera_id} ({db_camera.name}) and cleaning up all related data")
    
    try:
        # 1. Stop any active frame distributors for this camera
        try:
            from app.services.frame_distribution_service import get_frame_distribution_manager
            frame_manager = get_frame_distribution_manager()
            if frame_manager.get_distributor(camera_id):
                logger.info(f"Stopping frame distributor for camera {camera_id}")
                frame_manager.remove_distributor(camera_id)
        except Exception as e:
            logger.warning(f"Could not stop frame distributor for camera {camera_id}: {e}")
        
        # 2. Clean up recording files and database
        recordings_path = Path(f"recordings/camera_{camera_id}")
        if recordings_path.exists():
            logger.info(f"Removing recording directory: {recordings_path}")
            shutil.rmtree(recordings_path, ignore_errors=True)
        
        # 3. Delete camera from main database
        await db.delete(db_camera)
        await db.commit()
        
        logger.info(f"Successfully deleted camera {camera_id} and cleaned up all related data")
        return True
        
    except Exception as e:
        logger.error(f"Error during camera {camera_id} deletion cleanup: {e}")
        # Rollback database transaction if it failed
        await db.rollback()
        return False


async def update_camera_status(db: AsyncSession, camera_id: int, status: str) -> Optional[Camera]:
    """Update camera status (online/offline/error)"""
    db_camera = await get_camera_by_id(db, camera_id)
    if not db_camera:
        return None
    
    db_camera.status = status
    db_camera.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_camera)
    return db_camera


async def get_cameras_by_status(db: AsyncSession, status: str) -> List[Camera]:
    """Get cameras filtered by status"""
    result = await db.execute(
        select(Camera)
        .where(Camera.status == status)
        .order_by(Camera.created_at.desc())
    )
    return result.scalars().all()


async def get_cameras_by_location(db: AsyncSession, location: str) -> List[Camera]:
    """Get cameras filtered by location"""
    result = await db.execute(
        select(Camera)
        .where(Camera.location == location)
        .order_by(Camera.created_at.desc())
    )
    return result.scalars().all()