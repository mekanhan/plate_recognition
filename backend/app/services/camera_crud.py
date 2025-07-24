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
    result = await db.execute(select(Camera))
    return len(result.scalars().all())


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
    """Delete a camera by ID"""
    db_camera = await get_camera_by_id(db, camera_id)
    if not db_camera:
        return False
    
    await db.delete(db_camera)
    await db.commit()
    return True


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