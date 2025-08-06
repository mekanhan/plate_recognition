"""
Camera Service for Database-Driven Architecture
Provides CRUD operations for the new camera management schema
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, outerjoin
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import logging
import uuid
from cryptography.fernet import Fernet
import os
import base64

from .models import CameraNew, CameraConnection, CameraRecordingConfig, CameraSetting, CameraStatus
from .service import DatabaseService

class CameraService:
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
        self.logger = logging.getLogger("CameraService")
        
        # Initialize encryption for credentials
        self.cipher_suite = self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption for sensitive data"""
        try:
            # Try to get encryption key from environment
            key = os.getenv('CAMERA_ENCRYPTION_KEY')
            if not key:
                # Generate a new key for development (store this securely in production!)
                key = Fernet.generate_key()
                self.logger.warning("Generated new encryption key - store this securely!")
                # In production, this should be stored in a secure key management system
                
            return Fernet(key)
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            return None
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt sensitive values"""
        if not value or not self.cipher_suite:
            return value
        try:
            return self.cipher_suite.encrypt(value.encode()).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return value
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive values"""
        if not encrypted_value or not self.cipher_suite:
            return encrypted_value
        try:
            return self.cipher_suite.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return encrypted_value
    
    async def create_camera(self, camera_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new camera with all related configurations"""
        async with self.db.get_session() as session:
            try:
                # Create main camera record
                camera_id = camera_data.get('camera_id') or f"camera_{str(uuid.uuid4())[:8]}"
                
                camera = CameraNew(
                    camera_id=camera_id,
                    name=camera_data['name'],
                    location=camera_data.get('location'),
                    status=camera_data.get('status', 'active')
                )
                session.add(camera)
                await session.flush()  # Get the generated ID
                
                # Create connection record
                connection = CameraConnection(
                    camera_id=camera.id,
                    protocol=camera_data.get('protocol', 'RTSP').upper(),
                    ip_address=camera_data['ip_address'],
                    port=camera_data.get('port', 554),
                    username=self._encrypt_value(camera_data.get('username')),
                    password=self._encrypt_value(camera_data.get('password')),
                    stream_path=camera_data.get('stream_path', '/stream1')
                )
                session.add(connection)
                
                # Create recording config with defaults
                recording_config = CameraRecordingConfig(
                    camera_id=camera.id,
                    enabled=camera_data.get('recording_enabled', False),
                    recording_path=f"/recordings/{camera_id}/",
                    segment_duration=camera_data.get('segment_duration', 600),
                    retention_days=camera_data.get('retention_days', 30)
                )
                session.add(recording_config)
                
                # Create initial status record
                status = CameraStatus(
                    camera_id=camera.id,
                    recording_status='stopped',
                    connection_status='disconnected'
                )
                session.add(status)
                
                # Add any custom settings
                if 'settings' in camera_data:
                    for key, value in camera_data['settings'].items():
                        setting = CameraSetting(
                            camera_id=camera.id,
                            setting_key=key,
                            setting_value=str(value),
                            setting_type=type(value).__name__
                        )
                        session.add(setting)
                
                await session.commit()
                
                # Return formatted camera data
                return await self.get_camera(camera.camera_id)
                
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to create camera: {e}")
                raise
    
    async def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get a single camera with all related data"""
        async with self.db.get_session() as session:
            try:
                result = await session.execute(
                    select(CameraNew)
                    .options(
                        selectinload(CameraNew.connections),
                        selectinload(CameraNew.recording_config),
                        selectinload(CameraNew.settings),
                        selectinload(CameraNew.status_record)
                    )
                    .where(CameraNew.camera_id == camera_id)
                )
                camera = result.scalar_one_or_none()
                
                if not camera:
                    return None
                
                return self._format_camera_data(camera)
                
            except Exception as e:
                self.logger.error(f"Failed to get camera {camera_id}: {e}")
                return None
    
    async def get_all_cameras(self) -> List[Dict[str, Any]]:
        """Get all cameras with their status data"""
        async with self.db.get_session() as session:
            try:
                result = await session.execute(
                    select(CameraNew)
                    .options(
                        selectinload(CameraNew.connections),
                        selectinload(CameraNew.recording_config),
                        selectinload(CameraNew.settings),
                        selectinload(CameraNew.status_record)
                    )
                    .where(CameraNew.status == 'active')
                    .order_by(CameraNew.name)
                )
                cameras = result.scalars().all()
                
                return [self._format_camera_data(camera) for camera in cameras]
                
            except Exception as e:
                self.logger.error(f"Failed to get all cameras: {e}")
                return []
    
    async def get_cameras_status(self) -> Dict[str, Any]:
        """Get bulk status for all cameras (optimized for 8-field standard)"""
        async with self.db.get_session() as session:
            try:
                # Use SQLAlchemy query instead of raw SQL
                result = await session.execute(
                    select(
                        CameraNew.camera_id,
                        CameraNew.name,
                        CameraNew.location,
                        CameraConnection.protocol,
                        CameraConnection.ip_address,
                        CameraConnection.port,
                        CameraStatus.recording_status,
                        CameraStatus.connection_status,
                        CameraStatus.ffmpeg_pid,
                        CameraStatus.segments_created,
                        CameraStatus.last_segment_time,
                        CameraStatus.storage_used_bytes,
                        CameraStatus.recording_started_at,
                        CameraStatus.last_heartbeat,
                        CameraStatus.error_message
                    )
                    .select_from(
                        CameraNew.__table__
                        .outerjoin(CameraConnection.__table__, and_(CameraNew.id == CameraConnection.camera_id, CameraConnection.is_active == True))
                        .outerjoin(CameraStatus.__table__, CameraNew.id == CameraStatus.camera_id)
                    )
                    .where(CameraNew.status == 'active')
                    .order_by(CameraNew.name)
                )
                cameras_raw = result.all()
                
                cameras = []
                for cam in cameras_raw:
                    # Convert Row to dict using _mapping
                    cam_dict = cam._mapping
                    cameras.append(self._format_camera_status_data(dict(cam_dict)))
                
                return {
                    "cameras": cameras,
                    "count": len(cameras),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get cameras status: {e}")
                return {"cameras": [], "count": 0, "error": str(e)}
    
    async def update_camera_status(self, camera_id: str, status_data: Dict[str, Any]) -> bool:
        """Update camera status (for real-time updates)"""
        async with self.db.get_session() as session:
            try:
                # Get camera's internal ID
                camera_result = await session.execute(
                    select(CameraNew.id).where(CameraNew.camera_id == camera_id)
                )
                camera_internal_id = camera_result.scalar_one_or_none()
                
                if not camera_internal_id:
                    return False
                
                # Update status record
                status_result = await session.execute(
                    select(CameraStatus).where(CameraStatus.camera_id == camera_internal_id)
                )
                status = status_result.scalar_one_or_none()
                
                if not status:
                    # Create new status record
                    status = CameraStatus(camera_id=camera_internal_id)
                    session.add(status)
                
                # Update fields
                for key, value in status_data.items():
                    if hasattr(status, key):
                        setattr(status, key, value)
                
                status.last_heartbeat = datetime.utcnow()
                status.updated_at = datetime.utcnow()
                
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to update camera status for {camera_id}: {e}")
                return False
    
    async def delete_camera(self, camera_id: str) -> bool:
        """Delete camera and all related data"""
        async with self.db.get_session() as session:
            try:
                result = await session.execute(
                    select(CameraNew).where(CameraNew.camera_id == camera_id)
                )
                camera = result.scalar_one_or_none()
                
                if not camera:
                    return False
                
                await session.delete(camera)
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to delete camera {camera_id}: {e}")
                return False
    
    def _format_camera_data(self, camera: CameraNew) -> Dict[str, Any]:
        """Format camera data for API response"""
        # Get active connection
        connection = next((c for c in camera.connections if c.is_active), None)
        
        formatted = {
            "id": camera.camera_id,
            "name": camera.name,
            "location": camera.location or "Unknown",
            "status": camera.status,
            "created_at": camera.created_at.isoformat() if camera.created_at else None,
            "updated_at": camera.updated_at.isoformat() if camera.updated_at else None,
        }
        
        # Add connection info
        if connection:
            formatted.update({
                "protocol": connection.protocol,
                "ip_address": connection.ip_address,
                "port": connection.port,
                "stream_path": connection.stream_path,
                "username": self._decrypt_value(connection.username) if connection.username else None,
                # Don't include password in API responses for security
                "last_connected": connection.last_connected.isoformat() if connection.last_connected else None,
            })
        
        # Add recording config
        if camera.recording_config:
            formatted["recording_config"] = {
                "enabled": camera.recording_config.enabled,
                "segment_duration": camera.recording_config.segment_duration,
                "retention_days": camera.recording_config.retention_days,
                "video_codec": camera.recording_config.video_codec,
            }
        
        # Add current status
        if camera.status_record:
            formatted["current_status"] = self._format_status_for_8_fields(camera.status_record, formatted)
        
        # Add settings
        if camera.settings:
            formatted["settings"] = {
                setting.setting_key: self._parse_setting_value(setting.setting_value, setting.setting_type)
                for setting in camera.settings
            }
        
        return formatted
    
    def _format_camera_status_data(self, cam_data: Dict) -> Dict[str, Any]:
        """Format camera data according to 8-field standard"""
        return {
            "id": cam_data.get("camera_id"),
            "name": cam_data.get("name"),
            # 8 Standard Fields
            "location": cam_data.get("location") or "Unknown",
            "connection": self._format_connection(cam_data),
            "recording_status": self._format_recording_status(cam_data.get("recording_status")),
            "connection_status": self._format_connection_status(cam_data.get("connection_status")),
            "ffmpeg_pid": str(cam_data.get("ffmpeg_pid")) if cam_data.get("ffmpeg_pid") else "None",
            "segments_created": self._format_segments(cam_data.get("segments_created"), cam_data.get("last_segment_time")),
            "storage_used": self._format_bytes(cam_data.get("storage_used_bytes")),
            "recording_uptime": self._format_uptime(cam_data.get("recording_started_at")),
            # Additional metadata
            "last_heartbeat": cam_data.get("last_heartbeat"),
            "error_message": cam_data.get("error_message"),
        }
    
    def _format_connection(self, cam_data: Dict) -> str:
        """Format connection field according to standard"""
        protocol = cam_data.get("protocol")
        ip_address = cam_data.get("ip_address")
        if protocol and ip_address:
            return f"{protocol} ({ip_address})"
        return "Unknown"
    
    def _format_recording_status(self, status: str) -> str:
        """Format recording status with emoji"""
        if not status or status == 'stopped':
            return "⏹️ Stopped"
        elif status == 'recording':
            return "▶️ Recording"
        elif status == 'paused':
            return "⏸️ Paused"
        return "Not Set"
    
    def _format_connection_status(self, status: str) -> str:
        """Format connection status with emoji"""
        if status == 'connected':
            return "✅ Connected"
        elif status == 'connecting':
            return "🔄 Connecting"
        elif status == 'reconnecting':
            return "⚠️ Reconnecting"
        elif status == 'disconnected':
            return "❌ Disconnected"
        return "Unknown"
    
    def _format_segments(self, count: int, last_time: datetime) -> str:
        """Format segments created field"""
        if not count or count == 0:
            return "0"
        if last_time:
            return f"{count} (last: {last_time.strftime('%I:%M:%S %p')})"
        return f"{count} (last: Unknown)"
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format storage bytes to human readable"""
        if not bytes_value or bytes_value == 0:
            return "0 B"
        
        sizes = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while bytes_value >= 1024 and i < len(sizes) - 1:
            bytes_value /= 1024
            i += 1
        return f"{bytes_value:.1f} {sizes[i]}"
    
    def _format_uptime(self, started_at: datetime) -> str:
        """Format recording uptime"""
        if not started_at:
            return "None"
        
        now = datetime.utcnow()
        delta = now - started_at
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _format_status_for_8_fields(self, status: CameraStatus, camera_data: Dict) -> Dict[str, Any]:
        """Format status data according to 8-field standard"""
        return {
            "location": camera_data.get("location", "Unknown"),
            "connection": f"{camera_data.get('protocol', 'Unknown')} ({camera_data.get('ip_address', 'Unknown')})",
            "recording_status": self._format_recording_status(status.recording_status),
            "connection_status": self._format_connection_status(status.connection_status),
            "ffmpeg_pid": str(status.ffmpeg_pid) if status.ffmpeg_pid else "None",
            "segments_created": self._format_segments(status.segments_created, status.last_segment_time),
            "storage_used": self._format_bytes(status.storage_used_bytes),
            "recording_uptime": self._format_uptime(status.recording_started_at)
        }
    
    def _parse_setting_value(self, value: str, setting_type: str):
        """Parse setting value based on its type"""
        if setting_type == 'int':
            return int(value)
        elif setting_type == 'float':
            return float(value)
        elif setting_type == 'bool':
            return value.lower() in ('true', '1', 'yes')
        elif setting_type == 'json':
            return json.loads(value)
        return value  # string