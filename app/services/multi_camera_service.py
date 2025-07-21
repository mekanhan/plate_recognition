# app/services/multi_camera_service.py
# Centralized multi-camera management service
import cv2
import asyncio
import time
import numpy as np
import aiohttp
import logging
from typing import Optional, Dict, Any, Tuple, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from app.interfaces.camera import Camera
from app.models import Camera as CameraModel, CameraStatus, CameraType, CameraHealth, Location
from app.database import async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

# Import the camera discovery service (with fallback)
try:
    from app.services.camera_discovery_service import CameraDiscoveryService
    CAMERA_DISCOVERY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Camera discovery service not available: {e}")
    CAMERA_DISCOVERY_AVAILABLE = False
    CameraDiscoveryService = None

logger = logging.getLogger(__name__)

@dataclass
class CameraStreamInfo:
    """Information about an active camera stream"""
    camera_id: str
    stream_url: str
    frame_buffer: Optional[np.ndarray] = None
    last_frame_time: float = 0
    last_error: Optional[str] = None
    error_count: int = 0
    frame_count: int = 0
    is_connected: bool = False
    connection_attempts: int = 0
    
class StreamStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

class MultiCameraService:
    """
    Centralized service for managing multiple IP cameras concurrently
    """
    
    def __init__(self, max_concurrent_streams: int = 16):
        self.cameras: Dict[str, CameraModel] = {}
        self.streams: Dict[str, CameraStreamInfo] = {}
        self.capture_tasks: Dict[str, asyncio.Task] = {}
        self.frame_locks: Dict[str, asyncio.Lock] = {}
        self.running = False
        self.max_concurrent_streams = max_concurrent_streams
        self.health_check_interval = 30  # seconds
        self.health_task: Optional[asyncio.Task] = None
        self.camera_discovery_service: Optional[CameraDiscoveryService] = None
        
        # Performance tracking
        self.total_frames_processed = 0
        self.stream_stats: Dict[str, Dict] = {}
        
    async def initialize(self, camera_registry: Optional['CameraRegistryService'] = None, 
                        location_service: Optional['LocationService'] = None) -> None:
        """Initialize the multi-camera service"""
        logger.info("Initializing MultiCameraService...")
        
        try:
            # Initialize camera discovery service if dependencies are available
            if CAMERA_DISCOVERY_AVAILABLE and camera_registry and location_service:
                self.camera_discovery_service = CameraDiscoveryService(camera_registry, location_service)
                logger.info("Camera discovery service initialized")
            else:
                logger.warning("Camera discovery service not initialized - missing dependencies or import failed")
            
            # Load cameras from database
            await self._load_cameras_from_database()
            
            # Start health monitoring
            self.running = True
            self.health_task = asyncio.create_task(self._health_monitoring_loop())
            
            logger.info(f"MultiCameraService initialized with {len(self.cameras)} cameras")
            
        except Exception as e:
            logger.error(f"Failed to initialize MultiCameraService: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the multi-camera service"""
        logger.info("Shutting down MultiCameraService...")
        
        self.running = False
        
        # Stop health monitoring
        if self.health_task:
            self.health_task.cancel()
            try:
                await self.health_task
            except asyncio.CancelledError:
                pass
        
        # Stop all camera streams
        await self._stop_all_streams()
        
        logger.info("MultiCameraService shutdown complete")
    
    async def _load_cameras_from_database(self) -> None:
        """Load camera configurations from database"""
        async with async_session() as session:
            try:
                # Load all cameras with their locations (maintenance cameras are now deleted)
                result = await session.execute(
                    select(CameraModel)
                    .options(selectinload(CameraModel.location))
                )
                cameras = result.scalars().all()
                
                for camera in cameras:
                    self.cameras[camera.id] = camera
                    self.frame_locks[camera.id] = asyncio.Lock()
                    self.stream_stats[camera.id] = {
                        "frames_received": 0,
                        "errors": 0,
                        "last_frame_time": 0,
                        "connection_time": 0,
                        "uptime": 0
                    }
                
                logger.info(f"Loaded {len(cameras)} cameras from database")
                
            except Exception as e:
                logger.error(f"Failed to load cameras from database: {e}")
                raise
    
    async def discover_cameras_on_network(self, ip_range: str = "192.168.1.0/24", port_config: Dict[str, List[int]] = None) -> List[Dict[str, Any]]:
        """
        Discover IP cameras on the network
        
        Args:
            ip_range: IP range to scan (CIDR notation)
            port_config: Port configuration for discovery methods
            
        Returns:
            List of discovered camera information
        """
        logger.info(f"Discovering cameras on network: {ip_range}")
        
        try:
            # Check if discovery service is available
            if not self.camera_discovery_service:
                logger.warning("Camera discovery service not available, returning mock data")
                raise Exception("Camera discovery service not initialized")
            
            # Use the dedicated camera discovery service
            discovered_cameras = await self.camera_discovery_service.discover_cameras_on_network(
                ip_range=ip_range,
                port_config=port_config
            )
            
            # Convert DiscoveredCamera objects to dictionaries
            camera_dicts = []
            for camera in discovered_cameras:
                camera_dict = {
                    "ip_address": camera.ip_address,
                    "name": camera.name or f"Camera {camera.ip_address}",
                    "manufacturer": camera.manufacturer or "Unknown",
                    "model": camera.model or "Unknown",
                    "type": camera.camera_type or "ip_camera",
                    "vendor": camera.vendor or "generic",
                    "onvif_port": camera.onvif_port,
                    "rtsp_port": camera.rtsp_port,
                    "http_port": camera.http_port,
                    "resolution": f"{camera.resolution_width}x{camera.resolution_height}" if camera.resolution_width and camera.resolution_height else "Unknown",
                    "resolution_width": camera.resolution_width,
                    "resolution_height": camera.resolution_height,
                    "fps": camera.fps,
                    "username": camera.username or "admin",
                    "password": camera.password or "",
                    "discovery_method": camera.discovery_method.value if camera.discovery_method else "unknown",
                    "capabilities": camera.capabilities or [],
                    "supported_formats": camera.supported_formats or [],
                    "confidence": camera.confidence or 0.0,
                    "last_seen": camera.last_seen.isoformat() if camera.last_seen else None
                }
                camera_dicts.append(camera_dict)
            
            logger.info(f"Discovered {len(camera_dicts)} cameras on network")
            return camera_dicts
            
        except Exception as e:
            logger.error(f"Network discovery failed: {e}")
            # Return empty list if discovery fails
            return []
    
    async def add_camera(self, camera_config: Dict[str, Any]) -> str:
        """
        Add a new camera to the system
        
        Args:
            camera_config: Camera configuration dictionary
            
        Returns:
            Camera ID of the added camera
        """
        async with async_session() as session:
            try:
                # Validate required fields
                required_fields = ["name", "ip_address", "location_id"]
                for field in required_fields:
                    if field not in camera_config:
                        raise ValueError(f"Missing required field: {field}")
                
                # Create new camera model
                camera = CameraModel(
                    name=camera_config["name"],
                    ip_address=camera_config["ip_address"],
                    location_id=camera_config["location_id"],
                    camera_type=CameraType(camera_config.get("camera_type", "ip_camera")),
                    manufacturer=camera_config.get("manufacturer"),
                    model=camera_config.get("model"),
                    username=camera_config.get("username", "admin"),
                    password_hash=camera_config.get("password", ""),  # Should be hashed in production
                    main_stream_url=camera_config.get("main_stream_url"),
                    sub_stream_url=camera_config.get("sub_stream_url"),
                    resolution_width=camera_config.get("resolution_width", 1920),
                    resolution_height=camera_config.get("resolution_height", 1080),
                    fps=camera_config.get("fps", 30),
                    installation_location=camera_config.get("installation_location"),
                    viewing_direction=camera_config.get("viewing_direction")
                )
                
                session.add(camera)
                await session.commit()
                await session.refresh(camera)
                
                # Add to active cameras
                self.cameras[camera.id] = camera
                self.frame_locks[camera.id] = asyncio.Lock()
                self.stream_stats[camera.id] = {
                    "frames_received": 0,
                    "errors": 0,
                    "last_frame_time": 0,
                    "connection_time": 0,
                    "uptime": 0
                }
                
                # Create health record
                health = CameraHealth(camera_id=camera.id)
                session.add(health)
                await session.commit()
                
                logger.info(f"Added camera: {camera.name} ({camera.id})")
                return camera.id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add camera: {e}")
                raise
    
    async def remove_camera(self, camera_id: str) -> bool:
        """
        Remove a camera from the system
        
        Args:
            camera_id: ID of camera to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Stop stream if running
            await self.stop_camera_stream(camera_id)
            
            # Remove from active cameras
            if camera_id in self.cameras:
                del self.cameras[camera_id]
            if camera_id in self.frame_locks:
                del self.frame_locks[camera_id]
            if camera_id in self.stream_stats:
                del self.stream_stats[camera_id]
            
            # Actually delete from database
            async with async_session() as session:
                # First delete related camera health records
                await session.execute(
                    delete(CameraHealth)
                    .where(CameraHealth.camera_id == camera_id)
                )
                
                # Then delete the camera
                await session.execute(
                    delete(CameraModel)
                    .where(CameraModel.id == camera_id)
                )
                await session.commit()
            
            logger.info(f"Removed camera: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove camera {camera_id}: {e}")
            return False
    
    async def start_camera_stream(self, camera_id: str) -> bool:
        """
        Start streaming from a specific camera
        
        Args:
            camera_id: ID of camera to start
            
        Returns:
            True if successful, False otherwise
        """
        if camera_id not in self.cameras:
            logger.error(f"Camera not found: {camera_id}")
            return False
        
        if camera_id in self.capture_tasks:
            logger.warning(f"Camera stream already running: {camera_id}")
            return True
        
        try:
            camera = self.cameras[camera_id]
            
            # Create stream info
            stream_info = CameraStreamInfo(
                camera_id=camera_id,
                stream_url=camera.main_stream_url or self._build_stream_url(camera)
            )
            self.streams[camera_id] = stream_info
            
            # Start capture task
            self.capture_tasks[camera_id] = asyncio.create_task(
                self._capture_camera_frames(camera_id)
            )
            
            logger.info(f"Started camera stream: {camera.name} ({camera_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera stream {camera_id}: {e}")
            return False
    
    async def stop_camera_stream(self, camera_id: str) -> bool:
        """
        Stop streaming from a specific camera
        
        Args:
            camera_id: ID of camera to stop
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Cancel capture task
            if camera_id in self.capture_tasks:
                task = self.capture_tasks[camera_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.capture_tasks[camera_id]
            
            # Remove stream info
            if camera_id in self.streams:
                del self.streams[camera_id]
            
            # Update camera status
            await self._update_camera_status(camera_id, CameraStatus.OFFLINE)
            
            logger.info(f"Stopped camera stream: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop camera stream {camera_id}: {e}")
            return False
    
    async def get_camera_frame(self, camera_id: str) -> Tuple[Optional[np.ndarray], float]:
        """
        Get the latest frame from a specific camera
        
        Args:
            camera_id: ID of camera
            
        Returns:
            Tuple of (frame, timestamp) or (None, 0) if not available
        """
        if camera_id not in self.frame_locks:
            return None, 0
        
        async with self.frame_locks[camera_id]:
            stream_info = self.streams.get(camera_id)
            if not stream_info or stream_info.frame_buffer is None:
                return None, 0
            
            return stream_info.frame_buffer.copy(), stream_info.last_frame_time
    
    async def get_camera_jpeg_frame(self, camera_id: str) -> Tuple[Optional[bytes], float]:
        """
        Get the latest frame from a camera as JPEG bytes
        
        Args:
            camera_id: ID of camera
            
        Returns:
            Tuple of (JPEG bytes, timestamp) or (None, 0) if not available
        """
        frame, timestamp = await self.get_camera_frame(camera_id)
        if frame is None:
            return None, 0
        
        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes(), timestamp
    
    async def get_all_cameras(self) -> List[Dict[str, Any]]:
        """
        Get information about all cameras
        
        Returns:
            List of camera information dictionaries
        """
        cameras_info = []
        
        for camera_id, camera in self.cameras.items():
            stream_info = self.streams.get(camera_id)
            stats = self.stream_stats.get(camera_id, {})
            
            camera_info = {
                "id": camera.id,
                "name": camera.name,
                "ip_address": camera.ip_address,
                "location": camera.location.name if camera.location else "Unknown",
                "status": camera.status.value,
                "resolution": f"{camera.resolution_width}x{camera.resolution_height}",
                "fps": camera.fps,
                "is_streaming": camera_id in self.capture_tasks,
                "last_frame_time": stream_info.last_frame_time if stream_info else 0,
                "frame_count": stats.get("frames_received", 0),
                "error_count": stats.get("errors", 0),
                "uptime": stats.get("uptime", 0)
            }
            cameras_info.append(camera_info)
        
        return cameras_info
    
    async def get_camera_health(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Get health information for a specific camera
        
        Args:
            camera_id: ID of camera
            
        Returns:
            Camera health dictionary or None if not found
        """
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(CameraHealth).where(CameraHealth.camera_id == camera_id)
                )
                health = result.scalar_one_or_none()
                
                if not health:
                    return None
                
                return {
                    "camera_id": health.camera_id,
                    "uptime_percentage": health.uptime_percentage,
                    "connection_failures": health.connection_failures,
                    "avg_response_time": health.avg_response_time,
                    "frame_drop_rate": health.frame_drop_rate,
                    "stream_errors": health.stream_errors,
                    "last_health_check": health.last_health_check.isoformat() if health.last_health_check else None
                }
                
            except Exception as e:
                logger.error(f"Failed to get camera health {camera_id}: {e}")
                return None
    
    async def _capture_camera_frames(self, camera_id: str) -> None:
        """
        Capture frames from a camera in a loop
        
        Args:
            camera_id: ID of camera to capture from
        """
        stream_info = self.streams[camera_id]
        camera = self.cameras[camera_id]
        cap = None
        
        logger.info(f"Starting frame capture for camera: {camera.name}")
        
        try:
            while self.running and camera_id in self.capture_tasks:
                try:
                    # Initialize video capture if not done
                    if cap is None:
                        stream_info.is_connected = False
                        await self._update_camera_status(camera_id, CameraStatus.OFFLINE)
                        
                        # Try to connect to stream with optimized settings for IP cameras
                        cap = cv2.VideoCapture(stream_info.stream_url, cv2.CAP_FFMPEG)
                        
                        # Set buffer size to reduce latency
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # Set timeout for network streams
                        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
                        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
                        
                        # Force specific codec if needed (try H.264)
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H','2','6','4'))
                        
                        if not cap.isOpened():
                            # Fallback: try without specific backend
                            logger.warning(f"FFMPEG backend failed, trying default backend")
                            cap = cv2.VideoCapture(stream_info.stream_url)
                            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                            
                            if not cap.isOpened():
                                raise Exception(f"Failed to open stream: {stream_info.stream_url}")
                        
                        stream_info.is_connected = True
                        stream_info.connection_attempts += 1
                        await self._update_camera_status(camera_id, CameraStatus.ONLINE)
                        self.stream_stats[camera_id]["connection_time"] = time.time()
                        
                        logger.info(f"Connected to camera stream: {camera.name}")
                    
                    # Read frame with retry logic
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        # Update frame buffer with thread safety
                        async with self.frame_locks[camera_id]:
                            stream_info.frame_buffer = frame
                            stream_info.last_frame_time = time.time()
                            stream_info.frame_count += 1
                            stream_info.error_count = 0  # Reset error count on success
                        
                        # Update statistics
                        self.stream_stats[camera_id]["frames_received"] += 1
                        self.stream_stats[camera_id]["last_frame_time"] = time.time()
                        self.total_frames_processed += 1
                        
                        # Log first frame success
                        if stream_info.frame_count == 1:
                            logger.info(f"🎉 First frame received from camera {camera.name}! Resolution: {frame.shape[1]}x{frame.shape[0]}")
                        
                    else:
                        # Frame read failed - this is common with RTSP streams
                        stream_info.error_count += 1
                        logger.debug(f"Frame read failed for {camera.name}, error count: {stream_info.error_count}")
                        
                        # Try to grab() next frame to skip buffered frames
                        cap.grab()
                        
                        if stream_info.error_count > 20:  # Increased tolerance for IP cameras
                            raise Exception(f"Too many consecutive frame read failures ({stream_info.error_count})")
                    
                    # Control frame rate
                    await asyncio.sleep(1.0 / camera.fps)
                    
                except Exception as e:
                    logger.error(f"Camera {camera.name} stream error: {e}")
                    
                    # Clean up video capture
                    if cap:
                        cap.release()
                        cap = None
                    
                    stream_info.is_connected = False
                    stream_info.last_error = str(e)
                    stream_info.error_count += 1
                    self.stream_stats[camera_id]["errors"] += 1
                    
                    await self._update_camera_status(camera_id, CameraStatus.WARNING)
                    
                    # Wait before reconnecting
                    await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info(f"Frame capture cancelled for camera: {camera.name}")
        except Exception as e:
            logger.error(f"Unexpected error in frame capture for {camera.name}: {e}")
        finally:
            # Clean up
            if cap:
                cap.release()
            stream_info.is_connected = False
            await self._update_camera_status(camera_id, CameraStatus.OFFLINE)
    
    async def _stop_all_streams(self) -> None:
        """Stop all camera streams"""
        tasks = []
        for camera_id in list(self.capture_tasks.keys()):
            tasks.append(self.stop_camera_stream(camera_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop for all cameras"""
        while self.running:
            try:
                await self._update_camera_health_stats()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _update_camera_health_stats(self) -> None:
        """Update health statistics for all cameras"""
        async with async_session() as session:
            try:
                for camera_id, camera in self.cameras.items():
                    stats = self.stream_stats.get(camera_id, {})
                    stream_info = self.streams.get(camera_id)
                    
                    # Calculate health metrics
                    now = time.time()
                    connection_time = stats.get("connection_time", now)
                    uptime = now - connection_time if connection_time > 0 else 0
                    
                    # Update health record
                    health_update = {
                        "last_health_check": datetime.utcnow(),
                        "uptime_percentage": min(100.0, (uptime / 86400) * 100),  # 24 hour window
                        "connection_failures": stream_info.connection_attempts if stream_info else 0,
                        "stream_errors": stats.get("errors", 0),
                        "detections_per_hour": 0,  # TODO: Calculate from detection service
                        "avg_detection_confidence": 0.0  # TODO: Calculate from detection service
                    }
                    
                    await session.execute(
                        update(CameraHealth)
                        .where(CameraHealth.camera_id == camera_id)
                        .values(**health_update)
                    )
                
                await session.commit()
                
            except Exception as e:
                logger.error(f"Failed to update camera health stats: {e}")
                await session.rollback()
    
    async def _update_camera_status(self, camera_id: str, status: CameraStatus) -> None:
        """Update camera status in database"""
        async with async_session() as session:
            try:
                await session.execute(
                    update(CameraModel)
                    .where(CameraModel.id == camera_id)
                    .values(status=status, last_seen=datetime.utcnow())
                )
                await session.commit()
                
                # Update local model
                if camera_id in self.cameras:
                    self.cameras[camera_id].status = status
                    self.cameras[camera_id].last_seen = datetime.utcnow()
                
                # Broadcast camera status update to WebSocket clients
                await self._broadcast_camera_status(camera_id, status)
                
            except Exception as e:
                logger.error(f"Failed to update camera status {camera_id}: {e}")
    
    async def _broadcast_camera_status(self, camera_id: str, status: CameraStatus) -> None:
        """Broadcast camera status update to WebSocket clients"""
        try:
            # Import here to avoid circular imports
            from app.main import websocket_multiplexer
            
            if websocket_multiplexer:
                camera = self.cameras.get(camera_id)
                if camera:
                    status_data = {
                        "camera_id": camera_id,
                        "status": status.value,
                        "last_seen": camera.last_seen.isoformat() if camera.last_seen else None,
                        "name": camera.name,
                        "ip_address": camera.ip_address,
                        "location": camera.location.name if camera.location else None,
                        "is_streaming": camera_id in self.capture_tasks,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await websocket_multiplexer.broadcast_camera_status(camera_id, status_data)
                
        except Exception as e:
            logger.error(f"Error broadcasting camera status: {e}")
    
    def _build_stream_url(self, camera: CameraModel) -> str:
        """
        Build RTSP stream URL for camera with manufacturer-specific paths
        
        Args:
            camera: Camera model
            
        Returns:
            RTSP stream URL
        """
        if camera.main_stream_url:
            return camera.main_stream_url
        
        # Build manufacturer-specific RTSP URL
        username = camera.username or "admin"
        password = camera.password_hash or ""  # In production, decrypt this
        ip = camera.ip_address
        port = camera.port or 554
        
        # URL encode password if it contains special characters
        if self._has_special_chars_in_password(password):
            import urllib.parse
            password = urllib.parse.quote(password, safe='')
        
        # Get manufacturer-specific stream path
        stream_path = self._get_manufacturer_stream_path(camera.manufacturer)
        
        return f"rtsp://{username}:{password}@{ip}:{port}{stream_path}"
    
    def _has_special_chars_in_password(self, password: str) -> bool:
        """Check if password contains characters that need URL encoding"""
        special_chars = ['_', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=', '[', ']', '{', '}', '|', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/']
        return any(char in password for char in special_chars)
    
    def _get_manufacturer_stream_path(self, manufacturer: str) -> str:
        """Get manufacturer-specific RTSP stream path"""
        manufacturer_paths = {
            "reolink": "/h264Preview_01_sub",  # Use sub stream for better compatibility
            "hikvision": "/Streaming/Channels/102/",  # Sub stream
            "dahua": "/cam/realmonitor?channel=1&subtype=1",  # Sub stream  
            "axis": "/axis-media/media.amp",
            "generic": "/stream1"
        }
        
        # Default to manufacturer-specific path or generic
        manufacturer_key = manufacturer.lower() if manufacturer else "generic"
        return manufacturer_paths.get(manufacturer_key, manufacturer_paths["generic"])
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get overall system statistics
        
        Returns:
            System statistics dictionary
        """
        active_streams = len(self.capture_tasks)
        total_cameras = len(self.cameras)
        
        online_cameras = sum(1 for c in self.cameras.values() if c.status == CameraStatus.ONLINE)
        warning_cameras = sum(1 for c in self.cameras.values() if c.status == CameraStatus.WARNING)
        offline_cameras = sum(1 for c in self.cameras.values() if c.status == CameraStatus.OFFLINE)
        
        return {
            "total_cameras": total_cameras,
            "active_streams": active_streams,
            "online_cameras": online_cameras,
            "warning_cameras": warning_cameras,
            "offline_cameras": offline_cameras,
            "total_frames_processed": self.total_frames_processed,
            "max_concurrent_streams": self.max_concurrent_streams,
            "uptime": time.time() - (self.stream_stats.get("system_start_time", time.time())),
            "timestamp": time.time()
        }