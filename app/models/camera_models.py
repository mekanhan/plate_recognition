# app/models/camera_models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

class CameraType(str, Enum):
    """Supported camera types"""
    ANDROID = "android"
    IP_CAMERA = "ip_camera"
    USB = "usb"
    RTSP = "rtsp"
    PWA = "pwa"
    WEBSOCKET = "websocket"

class CameraStatus(str, Enum):
    """Camera status states"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    INITIALIZING = "initializing"
    DISCONNECTED = "disconnected"

class CameraCapabilities(BaseModel):
    """Camera technical capabilities"""
    resolutions: List[str] = Field(default=["640x480", "1280x720"])
    formats: List[str] = Field(default=["mjpeg", "h264"])
    fps_options: List[int] = Field(default=[15, 30])
    has_zoom: bool = Field(default=False)
    has_focus: bool = Field(default=False)
    has_exposure_control: bool = Field(default=False)
    supports_audio: bool = Field(default=False)

class CameraConfig(BaseModel):
    """Camera configuration settings"""
    # Connection settings
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    device_id: Optional[int] = None
    
    # Stream settings
    resolution: str = Field(default="1280x720")
    fps: int = Field(default=30)
    quality: str = Field(default="720p")  # 480p, 720p, 1080p
    format: str = Field(default="mjpeg")
    
    # Processing settings
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    frame_skip: int = Field(default=1, ge=1)  # Process every Nth frame
    enable_detection: bool = Field(default=True)
    
    # Network settings
    timeout_seconds: int = Field(default=30)
    retry_attempts: int = Field(default=3)
    buffer_size: int = Field(default=10)

class CameraRegistration(BaseModel):
    """Camera registration request"""
    name: str = Field(..., min_length=1, max_length=100)
    type: CameraType
    config: CameraConfig
    location: Optional[str] = Field(None, max_length=200)
    auto_discovered: bool = Field(default=False)
    capabilities: Optional[CameraCapabilities] = None

class CameraUpdate(BaseModel):
    """Camera update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[CameraConfig] = None
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[CameraStatus] = None

class CameraInfo(BaseModel):
    """Camera information response"""
    id: str
    name: str
    type: CameraType
    status: CameraStatus
    location: Optional[str]
    config: CameraConfig
    capabilities: Optional[CameraCapabilities]
    auto_discovered: bool
    created_at: datetime
    last_seen: Optional[datetime]
    
    # Runtime statistics
    frames_processed: int = Field(default=0)
    detections_count: int = Field(default=0)
    error_count: int = Field(default=0)
    uptime_seconds: int = Field(default=0)

class CameraStats(BaseModel):
    """Camera performance statistics"""
    camera_id: str
    frames_per_second: float
    detection_rate: float
    error_rate: float
    latency_ms: float
    last_frame_time: Optional[datetime]
    connection_quality: str  # excellent, good, fair, poor

class CameraFrame(BaseModel):
    """Camera frame data"""
    camera_id: str
    timestamp: datetime
    frame_data: bytes
    format: str = Field(default="jpeg")
    resolution: str
    frame_number: int

class CameraDiscovery(BaseModel):
    """Auto-discovered camera information"""
    ip_address: str
    port: int
    type: CameraType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    supported_streams: List[str] = Field(default=[])
    requires_auth: bool = Field(default=False)

class NetworkScanResult(BaseModel):
    """Network scan results"""
    scan_range: str
    discovered_cameras: List[CameraDiscovery]
    scan_duration_seconds: float
    total_devices_found: int

class CameraStreamSettings(BaseModel):
    """Stream-specific settings"""
    camera_id: str
    enable_stream: bool = Field(default=True)
    stream_to_web: bool = Field(default=True)
    stream_to_storage: bool = Field(default=True)
    stream_to_api: bool = Field(default=False)
    max_viewers: int = Field(default=10)

class QRCodeRequest(BaseModel):
    """QR code generation request"""
    computer_ip: str
    setup_token: Optional[str] = None
    camera_name: Optional[str] = None
    expires_in_minutes: int = Field(default=3
    0)

class CameraHealthCheck(BaseModel):
    """Camera health check response"""
    camera_id: str
    is_healthy: bool
    status: CameraStatus
    last_frame_received: Optional[datetime]
    connection_time_ms: float
    error_message: Optional[str] = None
    suggested_action: Optional[str] = None

# Database models are now defined in app.models
# Import them here for convenience
from app.models import Camera, CameraSession