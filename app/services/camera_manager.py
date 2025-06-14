# app/services/camera_manager.py
import asyncio
import uuid
import socket
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models import Camera, CameraSession
from app.schemas import (
    CameraType, CameraStatus, 
    CameraRegistration, CameraInfo, CameraUpdate, 
    CameraDiscovery, NetworkScanResult, CameraConfig,
    CameraCapabilities, CameraHealthCheck
)
from app.database import get_db_session

logger = logging.getLogger(__name__)

class CameraManager:
    """Universal camera management service"""
    
    def __init__(self):
        self.active_cameras: Dict[str, Dict] = {}
        self.camera_sessions: Dict[str, str] = {}  # camera_id -> session_id
        self.discovery_cache: Dict[str, CameraDiscovery] = {}
        self.last_discovery_scan: Optional[datetime] = None
        
    async def register_camera(self, registration: CameraRegistration, db: AsyncSession) -> str:
        """Register a new camera source"""
        try:
            # Generate unique camera ID
            camera_id = str(uuid.uuid4())
            
            # Create camera database record
            camera = Camera(
                id=camera_id,
                name=registration.name,
                type=registration.type.value,
                status=CameraStatus.INITIALIZING.value,
                location=registration.location,
                source_config=registration.config.dict(),
                capabilities=registration.capabilities.dict() if registration.capabilities else None,
                auto_discovered=registration.auto_discovered,
                created_at=datetime.utcnow()
            )
            
            db.add(camera)
            await db.commit()
            
            # Initialize camera in memory
            self.active_cameras[camera_id] = {
                "info": registration,
                "status": CameraStatus.INITIALIZING,
                "last_frame": None,
                "stats": {
                    "frames_processed": 0,
                    "detections_count": 0,
                    "error_count": 0,
                    "start_time": datetime.utcnow()
                },
                "connection": None
            }
            
            # Start camera session tracking
            await self._start_camera_session(camera_id, db)
            
            logger.info(f"Camera registered successfully: {camera_id} ({registration.name})")
            return camera_id
            
        except Exception as e:
            logger.error(f"Failed to register camera {registration.name}: {str(e)}")
            await db.rollback()
            raise

    async def get_camera_info(self, camera_id: str, db: AsyncSession) -> Optional[CameraInfo]:
        """Get detailed camera information"""
        try:
            # Get from database
            result = await db.execute(select(Camera).where(Camera.id == camera_id))
            camera = result.scalar_one_or_none()
            
            if not camera:
                return None
                
            # Get runtime stats
            runtime_stats = self.active_cameras.get(camera_id, {}).get("stats", {})
            uptime = 0
            if runtime_stats.get("start_time"):
                uptime = int((datetime.utcnow() - runtime_stats["start_time"]).total_seconds())
            
            return CameraInfo(
                id=camera.id,
                name=camera.name,
                type=CameraType(camera.type),
                status=CameraStatus(camera.status),
                location=camera.location,
                config=CameraConfig(**camera.source_config),
                capabilities=CameraCapabilities(**camera.capabilities) if camera.capabilities else None,
                auto_discovered=camera.auto_discovered,
                created_at=camera.created_at,
                last_seen=camera.last_seen,
                frames_processed=camera.frames_processed + runtime_stats.get("frames_processed", 0),
                detections_count=camera.detections_count + runtime_stats.get("detections_count", 0),
                error_count=camera.error_count + runtime_stats.get("error_count", 0),
                uptime_seconds=uptime
            )
            
        except Exception as e:
            logger.error(f"Failed to get camera info for {camera_id}: {str(e)}")
            return None

    async def list_cameras(self, db: AsyncSession, include_offline: bool = True) -> List[CameraInfo]:
        """List all registered cameras"""
        try:
            query = select(Camera)
            if not include_offline:
                query = query.where(Camera.status != CameraStatus.OFFLINE.value)
                
            result = await db.execute(query.order_by(Camera.created_at.desc()))
            cameras = result.scalars().all()
            
            camera_list = []
            for camera in cameras:
                info = await self.get_camera_info(camera.id, db)
                if info:
                    camera_list.append(info)
                    
            return camera_list
            
        except Exception as e:
            logger.error(f"Failed to list cameras: {str(e)}")
            return []

    async def update_camera(self, camera_id: str, update: CameraUpdate, db: AsyncSession) -> bool:
        """Update camera configuration"""
        try:
            # Build update dict
            update_data = {}
            if update.name:
                update_data["name"] = update.name
            if update.location is not None:
                update_data["location"] = update.location
            if update.status:
                update_data["status"] = update.status.value
            if update.config:
                update_data["source_config"] = update.config.dict()
                
            if not update_data:
                return True  # Nothing to update
                
            # Update database
            await db.execute(
                update(Camera).where(Camera.id == camera_id).values(**update_data)
            )
            await db.commit()
            
            # Update active camera if running
            if camera_id in self.active_cameras:
                if update.name:
                    self.active_cameras[camera_id]["info"].name = update.name
                if update.config:
                    self.active_cameras[camera_id]["info"].config = update.config
                if update.status:
                    self.active_cameras[camera_id]["status"] = update.status
                    
            logger.info(f"Camera updated successfully: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update camera {camera_id}: {str(e)}")
            await db.rollback()
            return False

    async def remove_camera(self, camera_id: str, db: AsyncSession) -> bool:
        """Remove a camera and clean up resources"""
        try:
            # Stop camera if active
            await self._stop_camera(camera_id)
            
            # End current session
            await self._end_camera_session(camera_id, db, "camera_removed")
            
            # Remove from database
            await db.execute(delete(Camera).where(Camera.id == camera_id))
            await db.execute(delete(CameraSession).where(CameraSession.camera_id == camera_id))
            await db.commit()
            
            # Clean up memory
            if camera_id in self.active_cameras:
                del self.active_cameras[camera_id]
            if camera_id in self.camera_sessions:
                del self.camera_sessions[camera_id]
                
            logger.info(f"Camera removed successfully: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove camera {camera_id}: {str(e)}")
            await db.rollback()
            return False

    async def discover_cameras(self, network_range: str = "192.168.1.0/24") -> NetworkScanResult:
        """Auto-discover cameras on the network"""
        start_time = datetime.utcnow()
        discovered_cameras = []
        
        try:
            logger.info(f"Starting camera discovery on network: {network_range}")
            
            # Parse network range
            network_ips = self._generate_ip_range(network_range)
            
            # Scan for RTSP cameras (port 554)
            rtsp_cameras = await self._scan_rtsp_cameras(network_ips)
            discovered_cameras.extend(rtsp_cameras)
            
            # Scan for HTTP cameras (ports 80, 8080, 8081)
            http_cameras = await self._scan_http_cameras(network_ips)
            discovered_cameras.extend(http_cameras)
            
            # Try UPnP discovery
            upnp_cameras = await self._discover_upnp_cameras()
            discovered_cameras.extend(upnp_cameras)
            
            # Cache results
            for camera in discovered_cameras:
                self.discovery_cache[camera.ip_address] = camera
                
            self.last_discovery_scan = datetime.utcnow()
            scan_duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Discovery completed: {len(discovered_cameras)} cameras found in {scan_duration:.2f}s")
            
            return NetworkScanResult(
                scan_range=network_range,
                discovered_cameras=discovered_cameras,
                scan_duration_seconds=scan_duration,
                total_devices_found=len(discovered_cameras)
            )
            
        except Exception as e:
            logger.error(f"Camera discovery failed: {str(e)}")
            return NetworkScanResult(
                scan_range=network_range,
                discovered_cameras=[],
                scan_duration_seconds=0,
                total_devices_found=0
            )

    async def check_camera_health(self, camera_id: str) -> CameraHealthCheck:
        """Check camera health and connectivity"""
        try:
            if camera_id not in self.active_cameras:
                return CameraHealthCheck(
                    camera_id=camera_id,
                    is_healthy=False,
                    status=CameraStatus.OFFLINE,
                    connection_time_ms=0,
                    error_message="Camera not found in active cameras",
                    suggested_action="Check if camera is registered and online"
                )
                
            camera = self.active_cameras[camera_id]
            start_time = datetime.utcnow()
            
            # Basic connectivity test based on camera type
            camera_type = camera["info"].type
            config = camera["info"].config
            
            is_healthy = False
            error_message = None
            
            if camera_type == CameraType.RTSP:
                is_healthy = await self._test_rtsp_connection(config.url, config.timeout_seconds)
            elif camera_type == CameraType.PWA:
                is_healthy = camera["status"] == CameraStatus.ONLINE
            elif camera_type == CameraType.USB:
                is_healthy = await self._test_usb_camera(config.device_id)
            else:
                is_healthy = True  # Assume healthy for other types
                
            if not is_healthy:
                error_message = f"Connection test failed for {camera_type.value} camera"
                
            connection_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return CameraHealthCheck(
                camera_id=camera_id,
                is_healthy=is_healthy,
                status=camera["status"],
                last_frame_received=camera.get("last_frame"),
                connection_time_ms=connection_time,
                error_message=error_message,
                suggested_action="Check camera configuration and network connectivity" if not is_healthy else None
            )
            
        except Exception as e:
            logger.error(f"Health check failed for camera {camera_id}: {str(e)}")
            return CameraHealthCheck(
                camera_id=camera_id,
                is_healthy=False,
                status=CameraStatus.ERROR,
                connection_time_ms=0,
                error_message=str(e),
                suggested_action="Check camera configuration and try restarting"
            )

    async def update_camera_stats(self, camera_id: str, frames_delta: int = 0, detections_delta: int = 0, errors_delta: int = 0):
        """Update camera runtime statistics"""
        if camera_id in self.active_cameras:
            stats = self.active_cameras[camera_id]["stats"]
            stats["frames_processed"] += frames_delta
            stats["detections_count"] += detections_delta
            stats["error_count"] += errors_delta
            
            # Update last frame time
            if frames_delta > 0:
                self.active_cameras[camera_id]["last_frame"] = datetime.utcnow()

    async def set_camera_status(self, camera_id: str, status: CameraStatus, db: AsyncSession):
        """Update camera status"""
        try:
            await db.execute(
                update(Camera).where(Camera.id == camera_id).values(
                    status=status.value,
                    last_seen=datetime.utcnow() if status == CameraStatus.ONLINE else None
                )
            )
            await db.commit()
            
            if camera_id in self.active_cameras:
                self.active_cameras[camera_id]["status"] = status
                
        except Exception as e:
            logger.error(f"Failed to update camera status for {camera_id}: {str(e)}")

    # Private helper methods
    
    async def _start_camera_session(self, camera_id: str, db: AsyncSession):
        """Start a new camera session"""
        session_id = str(uuid.uuid4())
        session = CameraSession(
            id=session_id,
            camera_id=camera_id,
            session_start=datetime.utcnow()
        )
        db.add(session)
        await db.commit()
        self.camera_sessions[camera_id] = session_id

    async def _end_camera_session(self, camera_id: str, db: AsyncSession, reason: str = "normal_shutdown"):
        """End current camera session"""
        if camera_id in self.camera_sessions:
            session_id = self.camera_sessions[camera_id]
            stats = self.active_cameras.get(camera_id, {}).get("stats", {})
            
            await db.execute(
                update(CameraSession).where(CameraSession.id == session_id).values(
                    session_end=datetime.utcnow(),
                    frames_processed=stats.get("frames_processed", 0),
                    detections_made=stats.get("detections_count", 0),
                    disconnection_reason=reason
                )
            )
            await db.commit()
            del self.camera_sessions[camera_id]

    async def _stop_camera(self, camera_id: str):
        """Stop camera and clean up resources"""
        if camera_id in self.active_cameras:
            camera = self.active_cameras[camera_id]
            # Clean up any active connections
            if camera.get("connection"):
                try:
                    await camera["connection"].close()
                except:
                    pass
            camera["status"] = CameraStatus.OFFLINE

    def _generate_ip_range(self, network_range: str) -> List[str]:
        """Generate list of IPs from network range"""
        # Simple implementation - can be enhanced with ipaddress module
        if "/" in network_range:
            base_ip, mask = network_range.split("/")
            base_parts = base_ip.split(".")
            if mask == "24":
                return [f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}.{i}" for i in range(1, 255)]
        return [network_range]  # Single IP

    async def _scan_rtsp_cameras(self, ip_list: List[str]) -> List[CameraDiscovery]:
        """Scan for RTSP cameras on port 554"""
        discovered = []
        for ip in ip_list[:50]:  # Limit scan size
            try:
                if await self._test_port(ip, 554, timeout=2):
                    discovered.append(CameraDiscovery(
                        ip_address=ip,
                        port=554,
                        type=CameraType.RTSP,
                        supported_streams=[f"rtsp://{ip}:554/stream1"],
                        requires_auth=True
                    ))
            except:
                continue
        return discovered

    async def _scan_http_cameras(self, ip_list: List[str]) -> List[CameraDiscovery]:
        """Scan for HTTP cameras"""
        discovered = []
        for ip in ip_list[:30]:  # Limit scan
            for port in [80, 8080, 8081]:
                try:
                    if await self._test_port(ip, port, timeout=2):
                        discovered.append(CameraDiscovery(
                            ip_address=ip,
                            port=port,
                            type=CameraType.IP_CAMERA,
                            supported_streams=[f"http://{ip}:{port}/video"],
                            requires_auth=False
                        ))
                        break
                except:
                    continue
        return discovered

    async def _discover_upnp_cameras(self) -> List[CameraDiscovery]:
        """Discover UPnP cameras"""
        # Placeholder for UPnP discovery
        return []

    async def _test_port(self, ip: str, port: int, timeout: int = 5) -> bool:
        """Test if port is open"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), 
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False

    async def _test_rtsp_connection(self, url: str, timeout: int = 10) -> bool:
        """Test RTSP connection"""
        # Simple RTSP test - can be enhanced with actual RTSP client
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            # Extract host and port from RTSP URL
            host = url.split("//")[1].split("/")[0].split(":")[0]
            port = 554
            if ":" in url.split("//")[1].split("/")[0]:
                port = int(url.split("//")[1].split("/")[0].split(":")[1])
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    async def _test_usb_camera(self, device_id: int) -> bool:
        """Test USB camera availability"""
        try:
            import cv2
            cap = cv2.VideoCapture(device_id)
            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                return ret
            return False
        except:
            return False