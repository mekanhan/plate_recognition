# app/services/camera_registry_service.py
# Camera registry service for centralized camera management
import logging
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import json

from app.models import (
    Camera, CameraGroup, CameraStatus, CameraType, CameraHealth, 
    Location, ProcessingQueue, ProcessingStatus
)
from app.database import async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

@dataclass
class CameraRegistration:
    """Camera registration information"""
    camera_id: str
    location_id: str
    group_id: Optional[str] = None
    priority: int = 2  # Normal priority
    auto_discovery: bool = False
    registration_time: datetime = None
    
    def __post_init__(self):
        if self.registration_time is None:
            self.registration_time = datetime.utcnow()

class CameraRegistryService:
    """
    Service for managing camera registration, grouping, and assignment
    """
    
    def __init__(self):
        self.registered_cameras: Dict[str, CameraRegistration] = {}
        self.camera_groups: Dict[str, CameraGroup] = {}
        self.processing_assignments: Dict[str, str] = {}  # camera_id -> processing_node
        self.health_check_interval = 60  # seconds
        self.health_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def initialize(self) -> None:
        """Initialize the camera registry service"""
        logger.info("Initializing CameraRegistryService...")
        
        try:
            # Load existing cameras and groups
            await self._load_cameras_from_database()
            await self._load_groups_from_database()
            
            # Start health monitoring
            self.running = True
            self.health_task = asyncio.create_task(self._health_monitoring_loop())
            
            logger.info(f"CameraRegistryService initialized with {len(self.registered_cameras)} cameras and {len(self.camera_groups)} groups")
            
        except Exception as e:
            logger.error(f"Failed to initialize CameraRegistryService: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the camera registry service"""
        logger.info("Shutting down CameraRegistryService...")
        
        self.running = False
        
        if self.health_task:
            self.health_task.cancel()
            try:
                await self.health_task
            except asyncio.CancelledError:
                pass
        
        logger.info("CameraRegistryService shutdown complete")
    
    async def register_camera(self, camera_config: Dict[str, Any]) -> str:
        """
        Register a new camera in the system
        
        Args:
            camera_config: Camera configuration dictionary
            
        Returns:
            Camera ID of registered camera
        """
        async with async_session() as session:
            try:
                # Validate location exists
                location_result = await session.execute(
                    select(Location).where(Location.id == camera_config["location_id"])
                )
                location = location_result.scalar_one_or_none()
                
                if not location:
                    raise ValueError(f"Location not found: {camera_config['location_id']}")
                
                # Check for duplicate IP address
                existing = await session.execute(
                    select(Camera).where(Camera.ip_address == camera_config["ip_address"])
                )
                if existing.scalar_one_or_none():
                    raise ValueError(f"Camera with IP {camera_config['ip_address']} already exists")
                
                # Create camera record
                camera = Camera(
                    name=camera_config["name"],
                    location_id=camera_config["location_id"],
                    camera_group_id=camera_config.get("camera_group_id"),
                    camera_type=CameraType(camera_config.get("camera_type", "ip_camera")),
                    manufacturer=camera_config.get("manufacturer"),
                    model=camera_config.get("model"),
                    serial_number=camera_config.get("serial_number"),
                    ip_address=camera_config["ip_address"],
                    port=camera_config.get("port", 554),
                    username=camera_config.get("username", "admin"),
                    password_hash=camera_config.get("password", ""),  # Should be encrypted
                    main_stream_url=camera_config.get("main_stream_url"),
                    sub_stream_url=camera_config.get("sub_stream_url"),
                    snapshot_url=camera_config.get("snapshot_url"),
                    resolution_width=camera_config.get("resolution_width", 1920),
                    resolution_height=camera_config.get("resolution_height", 1080),
                    fps=camera_config.get("fps", 30),
                    codec=camera_config.get("codec", "H.264"),
                    detection_enabled=camera_config.get("detection_enabled", True),
                    recording_enabled=camera_config.get("recording_enabled", True),
                    installation_location=camera_config.get("installation_location"),
                    viewing_direction=camera_config.get("viewing_direction"),
                    mounting_height=camera_config.get("mounting_height"),
                    viewing_angle=camera_config.get("viewing_angle"),
                    detection_zones=camera_config.get("detection_zones", []),
                    recording_schedule=camera_config.get("recording_schedule", {}),
                    alert_settings=camera_config.get("alert_settings", {})
                )
                
                session.add(camera)
                await session.commit()
                await session.refresh(camera)
                
                # Create health record
                health = CameraHealth(camera_id=camera.id)
                session.add(health)
                await session.commit()
                
                # Register locally
                registration = CameraRegistration(
                    camera_id=camera.id,
                    location_id=camera.location_id,
                    group_id=camera.camera_group_id,
                    auto_discovery=camera_config.get("auto_discovery", False)
                )
                self.registered_cameras[camera.id] = registration
                
                logger.info(f"Registered camera: {camera.name} ({camera.id}) at {camera.ip_address}")
                return camera.id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to register camera: {e}")
                raise
    
    async def unregister_camera(self, camera_id: str) -> bool:
        """
        Unregister a camera from the system
        
        Args:
            camera_id: Camera ID to unregister
            
        Returns:
            True if successful, False otherwise
        """
        async with async_session() as session:
            try:
                # Update camera status to maintenance
                await session.execute(
                    update(Camera)
                    .where(Camera.id == camera_id)
                    .values(status=CameraStatus.MAINTENANCE)
                )
                await session.commit()
                
                # Remove from local registry
                if camera_id in self.registered_cameras:
                    del self.registered_cameras[camera_id]
                
                if camera_id in self.processing_assignments:
                    del self.processing_assignments[camera_id]
                
                logger.info(f"Unregistered camera: {camera_id}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to unregister camera {camera_id}: {e}")
                return False
    
    async def create_camera_group(self, group_config: Dict[str, Any]) -> str:
        """
        Create a new camera group
        
        Args:
            group_config: Group configuration dictionary
            
        Returns:
            Group ID of created group
        """
        async with async_session() as session:
            try:
                # Validate location exists
                location_result = await session.execute(
                    select(Location).where(Location.id == group_config["location_id"])
                )
                location = location_result.scalar_one_or_none()
                
                if not location:
                    raise ValueError(f"Location not found: {group_config['location_id']}")
                
                # Create group
                group = CameraGroup(
                    name=group_config["name"],
                    location_id=group_config["location_id"],
                    description=group_config.get("description"),
                    purpose=group_config.get("purpose"),
                    detection_threshold=group_config.get("detection_threshold", 0.7),
                    processing_enabled=group_config.get("processing_enabled", True),
                    recording_enabled=group_config.get("recording_enabled", True),
                    alert_enabled=group_config.get("alert_enabled", True),
                    alert_threshold=group_config.get("alert_threshold", 0.9)
                )
                
                session.add(group)
                await session.commit()
                await session.refresh(group)
                
                # Cache locally
                self.camera_groups[group.id] = group
                
                logger.info(f"Created camera group: {group.name} ({group.id})")
                return group.id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create camera group: {e}")
                raise
    
    async def assign_camera_to_group(self, camera_id: str, group_id: str) -> bool:
        """
        Assign a camera to a group
        
        Args:
            camera_id: Camera ID
            group_id: Group ID
            
        Returns:
            True if successful, False otherwise
        """
        async with async_session() as session:
            try:
                # Verify both camera and group exist
                camera_result = await session.execute(
                    select(Camera).where(Camera.id == camera_id)
                )
                camera = camera_result.scalar_one_or_none()
                
                group_result = await session.execute(
                    select(CameraGroup).where(CameraGroup.id == group_id)
                )
                group = group_result.scalar_one_or_none()
                
                if not camera:
                    raise ValueError(f"Camera not found: {camera_id}")
                if not group:
                    raise ValueError(f"Group not found: {group_id}")
                
                # Verify camera and group are in same location
                if camera.location_id != group.location_id:
                    raise ValueError("Camera and group must be in the same location")
                
                # Update camera group assignment
                await session.execute(
                    update(Camera)
                    .where(Camera.id == camera_id)
                    .values(camera_group_id=group_id)
                )
                await session.commit()
                
                # Update local registration
                if camera_id in self.registered_cameras:
                    self.registered_cameras[camera_id].group_id = group_id
                
                logger.info(f"Assigned camera {camera_id} to group {group_id}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to assign camera to group: {e}")
                return False
    
    async def get_cameras_by_location(self, location_id: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all cameras in a location
        
        Args:
            location_id: Location ID
            include_inactive: Include inactive cameras
            
        Returns:
            List of camera information dictionaries
        """
        async with async_session() as session:
            try:
                query = select(Camera).options(
                    selectinload(Camera.camera_group),
                    selectinload(Camera.camera_health)
                ).where(Camera.location_id == location_id)
                
                if not include_inactive:
                    query = query.where(Camera.status != CameraStatus.MAINTENANCE)
                
                result = await session.execute(query.order_by(Camera.name))
                cameras = result.scalars().all()
                
                camera_list = []
                for camera in cameras:
                    camera_dict = await self._camera_to_dict(camera)
                    camera_list.append(camera_dict)
                
                return camera_list
                
            except Exception as e:
                logger.error(f"Failed to get cameras by location {location_id}: {e}")
                return []
    
    async def get_cameras_by_group(self, group_id: str) -> List[Dict[str, Any]]:
        """
        Get all cameras in a group
        
        Args:
            group_id: Group ID
            
        Returns:
            List of camera information dictionaries
        """
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Camera)
                    .options(
                        selectinload(Camera.location),
                        selectinload(Camera.camera_health)
                    )
                    .where(Camera.camera_group_id == group_id)
                    .order_by(Camera.name)
                )
                cameras = result.scalars().all()
                
                camera_list = []
                for camera in cameras:
                    camera_dict = await self._camera_to_dict(camera)
                    camera_list.append(camera_dict)
                
                return camera_list
                
            except Exception as e:
                logger.error(f"Failed to get cameras by group {group_id}: {e}")
                return []
    
    async def get_camera_processing_queue(self, camera_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get processing queue for a camera
        
        Args:
            camera_id: Camera ID
            limit: Maximum queue items to return
            
        Returns:
            List of queue item dictionaries
        """
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(ProcessingQueue)
                    .where(ProcessingQueue.camera_id == camera_id)
                    .order_by(ProcessingQueue.created_at.desc())
                    .limit(limit)
                )
                queue_items = result.scalars().all()
                
                queue_list = []
                for item in queue_items:
                    queue_dict = {
                        "id": item.id,
                        "camera_id": item.camera_id,
                        "status": item.status.value,
                        "priority": item.priority.value,
                        "assigned_node": item.assigned_node,
                        "assigned_gpu": item.assigned_gpu,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                        "assigned_at": item.assigned_at.isoformat() if item.assigned_at else None,
                        "started_at": item.started_at.isoformat() if item.started_at else None,
                        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                        "processing_time_ms": item.processing_time_ms,
                        "retry_count": item.retry_count,
                        "error_message": item.error_message
                    }
                    queue_list.append(queue_dict)
                
                return queue_list
                
            except Exception as e:
                logger.error(f"Failed to get processing queue for camera {camera_id}: {e}")
                return []
    
    async def assign_processing_node(self, camera_id: str, node_id: str) -> bool:
        """
        Assign a camera to a processing node
        
        Args:
            camera_id: Camera ID
            node_id: Processing node ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.processing_assignments[camera_id] = node_id
            logger.info(f"Assigned camera {camera_id} to processing node {node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to assign processing node: {e}")
            return False
    
    async def get_registry_statistics(self) -> Dict[str, Any]:
        """
        Get camera registry statistics
        
        Returns:
            Statistics dictionary
        """
        async with async_session() as session:
            try:
                # Get camera counts by status
                camera_stats = await session.execute(
                    select(
                        Camera.status,
                        func.count(Camera.id).label('count')
                    )
                    .group_by(Camera.status)
                )
                
                status_counts = {row.status.value: row.count for row in camera_stats}
                
                # Get total cameras and groups
                total_cameras = await session.execute(select(func.count(Camera.id)))
                total_cameras = total_cameras.scalar()
                
                total_groups = await session.execute(select(func.count(CameraGroup.id)))
                total_groups = total_groups.scalar()
                
                # Get location distribution
                location_stats = await session.execute(
                    select(
                        Location.name,
                        func.count(Camera.id).label('camera_count')
                    )
                    .select_from(Location)
                    .outerjoin(Camera)
                    .group_by(Location.id, Location.name)
                )
                
                location_distribution = {row.name: row.camera_count for row in location_stats}
                
                return {
                    "total_cameras": total_cameras,
                    "total_groups": total_groups,
                    "registered_cameras": len(self.registered_cameras),
                    "processing_assignments": len(self.processing_assignments),
                    "status_counts": status_counts,
                    "location_distribution": location_distribution,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Failed to get registry statistics: {e}")
                return {}
    
    async def _load_cameras_from_database(self) -> None:
        """Load cameras from database into local registry"""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Camera).where(Camera.status != CameraStatus.MAINTENANCE)
                )
                cameras = result.scalars().all()
                
                for camera in cameras:
                    registration = CameraRegistration(
                        camera_id=camera.id,
                        location_id=camera.location_id,
                        group_id=camera.camera_group_id,
                        registration_time=camera.created_at
                    )
                    self.registered_cameras[camera.id] = registration
                
                logger.info(f"Loaded {len(cameras)} cameras into registry")
                
            except Exception as e:
                logger.error(f"Failed to load cameras from database: {e}")
                raise
    
    async def _load_groups_from_database(self) -> None:
        """Load camera groups from database"""
        async with async_session() as session:
            try:
                result = await session.execute(select(CameraGroup))
                groups = result.scalars().all()
                
                for group in groups:
                    self.camera_groups[group.id] = group
                
                logger.info(f"Loaded {len(groups)} camera groups")
                
            except Exception as e:
                logger.error(f"Failed to load groups from database: {e}")
                raise
    
    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop for camera registry"""
        while self.running:
            try:
                await self._check_camera_registrations()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _check_camera_registrations(self) -> None:
        """Check health of camera registrations"""
        async with async_session() as session:
            try:
                # Check for cameras that haven't been seen recently
                threshold = datetime.utcnow() - timedelta(minutes=5)
                
                result = await session.execute(
                    select(Camera)
                    .where(
                        and_(
                            Camera.status == CameraStatus.ONLINE,
                            or_(
                                Camera.last_seen < threshold,
                                Camera.last_seen.is_(None)
                            )
                        )
                    )
                )
                stale_cameras = result.scalars().all()
                
                # Update stale cameras to warning status
                for camera in stale_cameras:
                    await session.execute(
                        update(Camera)
                        .where(Camera.id == camera.id)
                        .values(status=CameraStatus.WARNING)
                    )
                    logger.warning(f"Camera {camera.name} marked as warning - not seen recently")
                
                if stale_cameras:
                    await session.commit()
                
            except Exception as e:
                logger.error(f"Failed to check camera registrations: {e}")
    
    async def _camera_to_dict(self, camera: Camera) -> Dict[str, Any]:
        """Convert Camera model to dictionary"""
        return {
            "id": camera.id,
            "name": camera.name,
            "location_id": camera.location_id,
            "location_name": camera.location.name if hasattr(camera, 'location') and camera.location else None,
            "camera_group_id": camera.camera_group_id,
            "group_name": camera.camera_group.name if hasattr(camera, 'camera_group') and camera.camera_group else None,
            "camera_type": camera.camera_type.value,
            "manufacturer": camera.manufacturer,
            "model": camera.model,
            "serial_number": camera.serial_number,
            "ip_address": camera.ip_address,
            "port": camera.port,
            "resolution": f"{camera.resolution_width}x{camera.resolution_height}",
            "fps": camera.fps,
            "codec": camera.codec,
            "status": camera.status.value,
            "last_seen": camera.last_seen.isoformat() if camera.last_seen else None,
            "health_score": camera.health_score,
            "detection_enabled": camera.detection_enabled,
            "recording_enabled": camera.recording_enabled,
            "installation_location": camera.installation_location,
            "viewing_direction": camera.viewing_direction,
            "created_at": camera.created_at.isoformat() if camera.created_at else None,
            "updated_at": camera.updated_at.isoformat() if camera.updated_at else None
        }