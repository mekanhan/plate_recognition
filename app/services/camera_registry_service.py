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

class CameraConflictException(Exception):
    """Exception raised when a camera IP address conflict occurs"""
    def __init__(self, ip_address: str, existing_camera_id: str, existing_camera_name: str):
        self.ip_address = ip_address
        self.existing_camera_id = existing_camera_id
        self.existing_camera_name = existing_camera_name
        super().__init__(f"Camera with IP {ip_address} already exists: {existing_camera_name} ({existing_camera_id})")

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
                existing_camera = existing.scalar_one_or_none()
                if existing_camera:
                    raise CameraConflictException(
                        camera_config["ip_address"],
                        existing_camera.id,
                        existing_camera.name
                    )
                
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
    
    async def update_camera(self, camera_id: str, camera_config: Dict[str, Any]) -> bool:
        """
        Update an existing camera configuration
        
        Args:
            camera_id: Camera ID to update
            camera_config: Updated camera configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        async with async_session() as session:
            try:
                # Get existing camera
                result = await session.execute(
                    select(Camera).where(Camera.id == camera_id)
                )
                camera = result.scalar_one_or_none()
                
                if not camera:
                    raise ValueError(f"Camera not found: {camera_id}")
                
                # Validate location exists if location_id is being updated
                if "location_id" in camera_config:
                    location_result = await session.execute(
                        select(Location).where(Location.id == camera_config["location_id"])
                    )
                    location = location_result.scalar_one_or_none()
                    
                    if not location:
                        raise ValueError(f"Location not found: {camera_config['location_id']}")
                
                # Check for duplicate IP address (if IP is being changed)
                if "ip_address" in camera_config and camera_config["ip_address"] != camera.ip_address:
                    existing = await session.execute(
                        select(Camera).where(
                            Camera.ip_address == camera_config["ip_address"],
                            Camera.id != camera_id
                        )
                    )
                    existing_camera = existing.scalar_one_or_none()
                    if existing_camera:
                        raise CameraConflictException(
                            camera_config["ip_address"],
                            existing_camera.id,
                            existing_camera.name
                        )
                
                # Update camera fields
                update_fields = {
                    "name": camera_config.get("name", camera.name),
                    "location_id": camera_config.get("location_id", camera.location_id),
                    "camera_group_id": camera_config.get("camera_group_id", camera.camera_group_id),
                    "manufacturer": camera_config.get("manufacturer", camera.manufacturer),
                    "model": camera_config.get("model", camera.model),
                    "serial_number": camera_config.get("serial_number", camera.serial_number),
                    "ip_address": camera_config.get("ip_address", camera.ip_address),
                    "port": camera_config.get("port", camera.port),
                    "username": camera_config.get("username", camera.username),
                    "resolution_width": camera_config.get("resolution_width", camera.resolution_width),
                    "resolution_height": camera_config.get("resolution_height", camera.resolution_height),
                    "fps": camera_config.get("fps", camera.fps),
                    "codec": camera_config.get("codec", camera.codec),
                    "detection_enabled": camera_config.get("detection_enabled", camera.detection_enabled),
                    "recording_enabled": camera_config.get("recording_enabled", camera.recording_enabled),
                    "installation_location": camera_config.get("installation_location", camera.installation_location),
                    "viewing_direction": camera_config.get("viewing_direction", camera.viewing_direction),
                    "mounting_height": camera_config.get("mounting_height", camera.mounting_height),
                    "viewing_angle": camera_config.get("viewing_angle", camera.viewing_angle),
                    "detection_zones": camera_config.get("detection_zones", camera.detection_zones),
                    "recording_schedule": camera_config.get("recording_schedule", camera.recording_schedule),
                    "alert_settings": camera_config.get("alert_settings", camera.alert_settings)
                }
                
                # Update password if provided
                if "password" in camera_config:
                    update_fields["password_hash"] = camera_config["password"]
                
                # Update stream URLs if provided
                if "stream_path" in camera_config:
                    # Could be used to construct main_stream_url, sub_stream_url, snapshot_url
                    update_fields["main_stream_url"] = camera_config.get("main_stream_url")
                    update_fields["sub_stream_url"] = camera_config.get("sub_stream_url")
                    update_fields["snapshot_url"] = camera_config.get("snapshot_url")
                
                # Apply updates
                for field, value in update_fields.items():
                    if hasattr(camera, field):
                        setattr(camera, field, value)
                
                await session.commit()
                
                # Update local registration if location changed
                if camera_id in self.registered_cameras:
                    registration = self.registered_cameras[camera_id]
                    registration.location_id = camera.location_id
                    registration.group_id = camera.camera_group_id
                
                logger.info(f"Updated camera: {camera.name} ({camera.id}) at {camera.ip_address}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update camera {camera_id}: {e}")
                raise
    
    async def unregister_camera(self, camera_id: str) -> bool:
        """
        Unregister a camera from the system
        
        Args:
            camera_id: Camera ID to unregister
            
        Returns:
            True if successful, False otherwise
        """
        # Only handle local registry cleanup since database deletion is handled by MultiCameraService
        try:
            # Remove from local registry
            if camera_id in self.registered_cameras:
                del self.registered_cameras[camera_id]
            
            if camera_id in self.processing_assignments:
                del self.processing_assignments[camera_id]
            
            logger.info(f"Unregistered camera: {camera_id}")
            return True
            
        except Exception as e:
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
    
    async def get_camera_by_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Get camera by IP address
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            Camera information dictionary or None if not found
        """
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Camera)
                    .options(selectinload(Camera.location))
                    .where(Camera.ip_address == ip_address)
                )
                camera = result.scalar_one_or_none()
                
                if camera:
                    return await self._camera_to_dict(camera)
                return None
                
            except Exception as e:
                logger.error(f"Failed to get camera by IP {ip_address}: {e}")
                return None
    
    async def get_all_cameras(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all cameras in the system
        
        Args:
            include_inactive: Include inactive cameras
            
        Returns:
            List of camera information dictionaries
        """
        async with async_session() as session:
            try:
                query = select(Camera).options(
                    selectinload(Camera.camera_group),
                    selectinload(Camera.camera_health),
                    selectinload(Camera.location)
                )
                
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
                logger.error(f"Failed to get all cameras: {e}")
                return []
    
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
        """Convert Camera model to dictionary with robust null handling"""
        try:
            # Safely get location information
            location_name = None
            if hasattr(camera, 'location') and camera.location:
                location_name = camera.location.name
            
            # Safely get camera group information
            group_name = None
            if hasattr(camera, 'camera_group') and camera.camera_group:
                group_name = camera.camera_group.name
            
            # Build basic camera dict with safe attribute access
            camera_dict = {
                "id": camera.id,
                "name": camera.name or "",
                "location_id": camera.location_id,
                "location_name": location_name,
                "location": location_name,  # For frontend compatibility
                "camera_group_id": camera.camera_group_id,
                "group_name": group_name,
                "camera_type": camera.camera_type.value if camera.camera_type else "ip_camera",
                "manufacturer": camera.manufacturer or "",
                "model": camera.model or "",
                "serial_number": camera.serial_number or "",
                "ip_address": camera.ip_address or "",
                "port": camera.port or 554,
                "username": camera.username or "",
                "password": camera.password_hash or "",  # For editing (should be handled securely)
                "resolution": f"{camera.resolution_width or 1920}x{camera.resolution_height or 1080}",
                "resolution_width": camera.resolution_width or 1920,
                "resolution_height": camera.resolution_height or 1080,
                "fps": camera.fps or 30,
                "codec": camera.codec or "",
                "stream_path": camera.main_stream_url or "",  # Map to stream_path for frontend
                "status": camera.status.value if camera.status else "offline",
                "last_seen": camera.last_seen.isoformat() if camera.last_seen else None,
                "health_score": getattr(camera, 'health_score', 0) or 0,
                "detection_enabled": getattr(camera, 'detection_enabled', True),
                "recording_enabled": getattr(camera, 'recording_enabled', True),
                "installation_location": camera.installation_location or "",
                "viewing_direction": camera.viewing_direction or "",
                "created_at": camera.created_at.isoformat() if camera.created_at else None,
                "updated_at": camera.updated_at.isoformat() if camera.updated_at else None
            }
            
            return camera_dict
            
        except Exception as e:
            logger.error(f"Error converting camera to dict: {e}")
            # Return a minimal dict to prevent complete failure
            return {
                "id": camera.id,
                "name": camera.name or "Unknown Camera",
                "ip_address": camera.ip_address or "",
                "status": "error",
                "error": str(e)
            }

    # Enhanced Camera Registration and Validation System
    async def validate_camera_registration(self, camera_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of camera registration data
        
        Args:
            camera_config: Camera configuration to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        try:
            # Required field validation
            required_fields = ["name", "ip_address", "location_id"]
            for field in required_fields:
                if field not in camera_config or not camera_config[field]:
                    validation_result["errors"].append(f"Missing required field: {field}")
                    validation_result["valid"] = False
            
            # IP address validation
            if "ip_address" in camera_config:
                ip_validation = await self._validate_ip_address(camera_config["ip_address"])
                if not ip_validation["valid"]:
                    validation_result["errors"].extend(ip_validation["errors"])
                    validation_result["valid"] = False
                else:
                    validation_result["warnings"].extend(ip_validation.get("warnings", []))
            
            # Location validation
            if "location_id" in camera_config:
                location_validation = await self._validate_location(camera_config["location_id"])
                if not location_validation["valid"]:
                    validation_result["errors"].extend(location_validation["errors"])
                    validation_result["valid"] = False
            
            # Camera group validation
            if camera_config.get("camera_group_id"):
                group_validation = await self._validate_camera_group(
                    camera_config["camera_group_id"], 
                    camera_config.get("location_id")
                )
                if not group_validation["valid"]:
                    validation_result["errors"].extend(group_validation["errors"])
                    validation_result["valid"] = False
            
            # Stream URL validation
            stream_validation = await self._validate_stream_urls(camera_config)
            validation_result["warnings"].extend(stream_validation.get("warnings", []))
            validation_result["suggestions"].extend(stream_validation.get("suggestions", []))
            
            # Network configuration validation
            network_validation = self._validate_network_config(camera_config)
            validation_result["warnings"].extend(network_validation.get("warnings", []))
            validation_result["suggestions"].extend(network_validation.get("suggestions", []))
            
            # LPPR optimization suggestions
            lppr_suggestions = self._generate_lppr_suggestions(camera_config)
            validation_result["suggestions"].extend(lppr_suggestions)
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
            logger.error(f"Camera validation error: {e}")
        
        return validation_result

    async def _validate_ip_address(self, ip_address: str) -> Dict[str, Any]:
        """Validate IP address format and availability"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        try:
            import ipaddress
            
            # Check IP format
            try:
                ip_obj = ipaddress.IPv4Address(ip_address)
            except ipaddress.AddressValueError:
                result["valid"] = False
                result["errors"].append(f"Invalid IP address format: {ip_address}")
                return result
            
            # Check for private IP ranges (warning, not error)
            if ip_obj.is_private:
                result["warnings"].append("Using private IP address - ensure camera is accessible")
            
            # Check for reserved addresses
            if ip_obj.is_loopback or ip_obj.is_multicast or ip_obj.is_reserved:
                result["valid"] = False
                result["errors"].append(f"Invalid IP address type: {ip_address}")
                return result
            
            # Check for duplicate IP in database
            async with async_session() as session:
                existing = await session.execute(
                    select(Camera).where(Camera.ip_address == ip_address)
                )
                if existing.scalar_one_or_none():
                    result["valid"] = False
                    result["errors"].append(f"IP address {ip_address} already in use")
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"IP validation error: {str(e)}")
        
        return result

    async def _validate_location(self, location_id: str) -> Dict[str, Any]:
        """Validate location exists and is active"""
        result = {"valid": True, "errors": []}
        
        try:
            async with async_session() as session:
                location_result = await session.execute(
                    select(Location).where(Location.id == location_id)
                )
                location = location_result.scalar_one_or_none()
                
                if not location:
                    result["valid"] = False
                    result["errors"].append(f"Location not found: {location_id}")
                elif not location.is_active:
                    result["valid"] = False
                    result["errors"].append(f"Location is inactive: {location_id}")
                    
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Location validation error: {str(e)}")
        
        return result

    async def _validate_camera_group(self, group_id: str, location_id: str = None) -> Dict[str, Any]:
        """Validate camera group exists and location compatibility"""
        result = {"valid": True, "errors": []}
        
        try:
            async with async_session() as session:
                group_result = await session.execute(
                    select(CameraGroup).where(CameraGroup.id == group_id)
                )
                group = group_result.scalar_one_or_none()
                
                if not group:
                    result["valid"] = False
                    result["errors"].append(f"Camera group not found: {group_id}")
                elif location_id and group.location_id != location_id:
                    result["valid"] = False
                    result["errors"].append("Camera group must be in the same location as camera")
                    
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Group validation error: {str(e)}")
        
        return result

    async def _validate_stream_urls(self, camera_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate stream URLs format and accessibility"""
        result = {"warnings": [], "suggestions": []}
        
        # Validate RTSP URLs
        for stream_type in ["main_stream_url", "sub_stream_url"]:
            if stream_type in camera_config and camera_config[stream_type]:
                url = camera_config[stream_type]
                if not url.startswith("rtsp://"):
                    result["warnings"].append(f"{stream_type} should use RTSP protocol")
                else:
                    # Extract credentials from URL for security warning
                    import re
                    if re.search(r'rtsp://[^:]+:[^@]+@', url):
                        result["warnings"].append(f"{stream_type} contains embedded credentials")
        
        # Validate snapshot URL
        if "snapshot_url" in camera_config and camera_config["snapshot_url"]:
            url = camera_config["snapshot_url"]
            if not url.startswith("http"):
                result["warnings"].append("Snapshot URL should use HTTP/HTTPS protocol")
        
        # Suggest missing URLs
        if not camera_config.get("main_stream_url"):
            result["suggestions"].append("Consider adding main stream URL for better performance")
        if not camera_config.get("sub_stream_url"):
            result["suggestions"].append("Consider adding sub stream URL for monitoring")
        if not camera_config.get("snapshot_url"):
            result["suggestions"].append("Consider adding snapshot URL for quick previews")
        
        return result

    def _validate_network_config(self, camera_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate network configuration parameters"""
        result = {"warnings": [], "suggestions": []}
        
        # Port validation
        port = camera_config.get("port", 554)
        if port < 1 or port > 65535:
            result["warnings"].append(f"Invalid port number: {port}")
        elif port != 554 and not camera_config.get("main_stream_url"):
            result["warnings"].append(f"Non-standard RTSP port {port} may require custom stream URL")
        
        # Resolution validation
        width = camera_config.get("resolution_width", 1920)
        height = camera_config.get("resolution_height", 1080)
        
        if width < 640 or height < 480:
            result["warnings"].append("Low resolution may affect license plate detection quality")
        elif width > 4096 or height > 2160:
            result["warnings"].append("Very high resolution may impact processing performance")
        
        # FPS validation
        fps = camera_config.get("fps", 30)
        if fps < 5:
            result["warnings"].append("Low FPS may miss fast-moving vehicles")
        elif fps > 60:
            result["suggestions"].append("High FPS may be unnecessary for LPPR - consider 15-30 FPS")
        
        # Codec validation
        codec = camera_config.get("codec", "H.264")
        if codec not in ["H.264", "H.265", "MJPEG"]:
            result["warnings"].append(f"Unsupported codec: {codec}")
        elif codec == "MJPEG":
            result["suggestions"].append("H.264 codec recommended for better compression")
        
        return result

    def _generate_lppr_suggestions(self, camera_config: Dict[str, Any]) -> List[str]:
        """Generate LPPR-specific optimization suggestions"""
        suggestions = []
        
        # Resolution suggestions
        width = camera_config.get("resolution_width", 1920)
        height = camera_config.get("resolution_height", 1080)
        
        if width < 1280 or height < 720:
            suggestions.append("Higher resolution (1920x1080) recommended for better plate recognition")
        
        # FPS suggestions
        fps = camera_config.get("fps", 30)
        if fps > 30:
            suggestions.append("FPS of 15-30 is optimal for LPPR - higher values may not improve accuracy")
        
        # Installation suggestions
        if not camera_config.get("mounting_height"):
            suggestions.append("Consider setting mounting height for optimal detection angle")
        
        if not camera_config.get("viewing_angle"):
            suggestions.append("Set viewing angle for better license plate capture geometry")
        
        # Detection zone suggestions
        if not camera_config.get("detection_zones"):
            suggestions.append("Define detection zones to focus on vehicle paths")
        
        # Recording suggestions
        if camera_config.get("recording_enabled", True):
            if not camera_config.get("recording_schedule"):
                suggestions.append("Configure recording schedule to optimize storage usage")
        
        return suggestions

    async def register_discovered_camera(self, discovered_camera, location_id: str, 
                                      auto_config: Dict[str, Any] = None) -> str:
        """
        Register a discovered camera with automatic configuration
        
        Args:
            discovered_camera: DiscoveredCamera object
            location_id: Location ID to assign camera
            auto_config: Optional auto-configuration results
            
        Returns:
            Camera ID of registered camera
        """
        try:
            # Build camera configuration from discovered camera
            camera_config = {
                "name": f"{discovered_camera.vendor or 'Camera'} {discovered_camera.ip_address}",
                "ip_address": discovered_camera.ip_address,
                "location_id": location_id,
                "camera_type": "ip_camera",
                "manufacturer": discovered_camera.vendor,
                "model": discovered_camera.model,
                "serial_number": discovered_camera.serial_number,
                "username": discovered_camera.default_username,
                "password": discovered_camera.default_password,
                "port": discovered_camera.rtsp_port,
                "main_stream_url": discovered_camera.main_stream_url,
                "sub_stream_url": discovered_camera.sub_stream_url,
                "snapshot_url": discovered_camera.snapshot_url,
                "resolution_width": 1920,
                "resolution_height": 1080,
                "fps": 15,  # LPPR optimized
                "codec": "H.264",
                "detection_enabled": True,
                "recording_enabled": True,
                "installation_location": f"Auto-discovered at {discovered_camera.ip_address}",
                "auto_discovery": True
            }
            
            # Apply auto-configuration if provided
            if auto_config and auto_config.get("status") == "success":
                config_data = auto_config.get("config", {})
                
                # Update credentials if validated
                if auto_config.get("credentials", {}).get("valid"):
                    creds = auto_config["credentials"]
                    camera_config["username"] = creds["username"]
                    camera_config["password"] = creds["password"]
                
                # Update stream URLs if validated
                streams = auto_config.get("streams", {})
                for stream_type in ["main_stream", "sub_stream", "snapshot"]:
                    if streams.get(stream_type, {}).get("valid"):
                        url_key = f"{stream_type}_url" if stream_type != "snapshot" else "snapshot_url"
                        camera_config[url_key] = streams[stream_type]["url"]
                
                # Apply vendor-specific configuration
                vendor_config = config_data.get("vendor_specific", {})
                if vendor_config:
                    camera_config.update(vendor_config)
            
            # Validate configuration
            validation_result = await self.validate_camera_registration(camera_config)
            
            if not validation_result["valid"]:
                raise ValueError(f"Camera validation failed: {validation_result['errors']}")
            
            # Register camera
            camera_id = await self.register_camera(camera_config)
            
            logger.info(f"Successfully registered discovered camera: {camera_id}")
            return camera_id
            
        except Exception as e:
            logger.error(f"Failed to register discovered camera: {e}")
            raise

    async def get_camera_validation_report(self, camera_id: str = None) -> Dict[str, Any]:
        """
        Get validation report for cameras
        
        Args:
            camera_id: Optional specific camera ID
            
        Returns:
            Validation report dictionary
        """
        try:
            async with async_session() as session:
                if camera_id:
                    # Get specific camera validation
                    result = await session.execute(
                        select(Camera).where(Camera.id == camera_id)
                    )
                    cameras = [result.scalar_one_or_none()]
                    if not cameras[0]:
                        return {"error": "Camera not found"}
                else:
                    # Get all cameras
                    result = await session.execute(select(Camera))
                    cameras = result.scalars().all()
                
                report = {
                    "total_cameras": len(cameras),
                    "validated_cameras": 0,
                    "invalid_cameras": 0,
                    "unvalidated_cameras": 0,
                    "validation_summary": {},
                    "cameras": []
                }
                
                for camera in cameras:
                    validation_meta = camera.validation_metadata or {}
                    validation_status = validation_meta.get("validation_status", "unvalidated")
                    
                    if validation_status == "valid":
                        report["validated_cameras"] += 1
                    elif validation_status == "invalid":
                        report["invalid_cameras"] += 1
                    else:
                        report["unvalidated_cameras"] += 1
                    
                    camera_report = {
                        "id": camera.id,
                        "name": camera.name,
                        "ip_address": camera.ip_address,
                        "vendor": camera.manufacturer,
                        "status": camera.status.value,
                        "validation_status": validation_status,
                        "last_validated": camera.last_validated.isoformat() if camera.last_validated else None,
                        "validation_errors": validation_meta.get("validation_errors", []),
                        "validation_warnings": validation_meta.get("validation_warnings", [])
                    }
                    
                    report["cameras"].append(camera_report)
                
                # Generate summary
                report["validation_summary"] = {
                    "valid_percentage": (report["validated_cameras"] / report["total_cameras"] * 100) if report["total_cameras"] > 0 else 0,
                    "needs_attention": report["invalid_cameras"] + report["unvalidated_cameras"]
                }
                
                return report
                
        except Exception as e:
            logger.error(f"Failed to generate validation report: {e}")
            return {"error": str(e)}