# app/schemas.py
"""
Pydantic schemas for API request/response models.
This file contains all Pydantic models used for API serialization/deserialization.
SQLAlchemy database models are in app/models.py.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class CameraType(str, Enum):
    """Camera connection types"""
    LOCAL = "local"
    IP = "ip"
    USB = "usb"
    RTSP = "rtsp"
    HTTP = "http"


class CameraStatus(str, Enum):
    """Camera operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"


class CameraConfig(BaseModel):
    """Camera configuration settings"""
    width: int = Field(default=1280, ge=320, le=4096, description="Camera width in pixels")
    height: int = Field(default=720, ge=240, le=2160, description="Camera height in pixels")
    fps: int = Field(default=30, ge=1, le=60, description="Frames per second")
    url: Optional[str] = Field(None, description="Camera URL for IP/RTSP cameras")
    device_id: Optional[int] = Field(None, ge=0, description="Device ID for local cameras")
    username: Optional[str] = Field(None, description="Authentication username")
    password: Optional[str] = Field(None, description="Authentication password")
    auto_connect: bool = Field(default=True, description="Auto-connect on startup")
    reconnect_interval: int = Field(default=5, ge=1, le=300, description="Reconnection interval in seconds")
    
    @validator('url')
    def validate_url(cls, v, values):
        camera_type = values.get('type')
        if camera_type in ['ip', 'rtsp', 'http'] and not v:
            raise ValueError(f"URL is required for {camera_type} cameras")
        return v


class CameraRegistration(BaseModel):
    """Camera registration request"""
    name: str = Field(..., min_length=1, max_length=100, description="Camera display name")
    type: CameraType = Field(..., description="Camera connection type")
    config: CameraConfig = Field(..., description="Camera configuration")
    location: Optional[str] = Field(None, max_length=200, description="Camera physical location")
    description: Optional[str] = Field(None, max_length=500, description="Camera description")
    is_primary: bool = Field(default=False, description="Is this the primary camera")


class CameraResponse(BaseModel):
    """Camera information response"""
    id: str = Field(..., description="Unique camera identifier")
    name: str = Field(..., description="Camera display name")
    type: CameraType = Field(..., description="Camera connection type")
    status: CameraStatus = Field(..., description="Current camera status")
    config: CameraConfig = Field(..., description="Camera configuration")
    location: Optional[str] = Field(None, description="Camera physical location")
    description: Optional[str] = Field(None, description="Camera description")
    is_primary: bool = Field(..., description="Is this the primary camera")
    created_at: datetime = Field(..., description="Camera registration timestamp")
    last_seen: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    class Config:
        from_attributes = True


class CameraUpdate(BaseModel):
    """Camera update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[CameraConfig] = None
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_primary: Optional[bool] = None


class CameraStats(BaseModel):
    """Camera statistics"""
    total_frames: int = Field(default=0, description="Total frames captured")
    fps: float = Field(default=0.0, description="Current frames per second")
    uptime_seconds: int = Field(default=0, description="Camera uptime in seconds")
    last_frame_timestamp: Optional[datetime] = Field(None, description="Last frame timestamp")
    error_count: int = Field(default=0, description="Total error count")
    reconnect_count: int = Field(default=0, description="Total reconnection count")


class DetectionBoundingBox(BaseModel):
    """Detection bounding box coordinates"""
    x1: int = Field(..., description="Top-left X coordinate")
    y1: int = Field(..., description="Top-left Y coordinate") 
    x2: int = Field(..., description="Bottom-right X coordinate")
    y2: int = Field(..., description="Bottom-right Y coordinate")
    
    @validator('x2')
    def x2_greater_than_x1(cls, v, values):
        if 'x1' in values and v <= values['x1']:
            raise ValueError('x2 must be greater than x1')
        return v
    
    @validator('y2')
    def y2_greater_than_y1(cls, v, values):
        if 'y1' in values and v <= values['y1']:
            raise ValueError('y2 must be greater than y1')
        return v


class DetectionRequest(BaseModel):
    """Detection processing request"""
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    image_path: Optional[str] = Field(None, description="Path to image file")
    camera_id: Optional[str] = Field(None, description="Source camera ID")
    timestamp: Optional[datetime] = Field(None, description="Detection timestamp")
    frame_id: Optional[int] = Field(None, description="Frame sequence ID")
    
    @validator('image_data', 'image_path')
    def at_least_one_image_source(cls, v, values):
        if not v and not values.get('image_data') and not values.get('image_path'):
            raise ValueError('Either image_data or image_path must be provided')
        return v


class DetectionResponse(BaseModel):
    """Detection result response"""
    id: str = Field(..., description="Unique detection ID")
    plate_text: str = Field(..., description="Detected license plate text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bounding_box: DetectionBoundingBox = Field(..., description="Detection bounding box")
    timestamp: datetime = Field(..., description="Detection timestamp")
    camera_id: Optional[str] = Field(None, description="Source camera ID")
    frame_id: Optional[int] = Field(None, description="Frame sequence ID")
    image_path: Optional[str] = Field(None, description="Saved detection image path")
    raw_text: Optional[str] = Field(None, description="Raw OCR text before processing")
    state: Optional[str] = Field(None, description="Detected state/region")
    vehicle_type: Optional[str] = Field(None, description="Detected vehicle type")
    direction: Optional[str] = Field(None, description="Vehicle direction")
    location: Optional[str] = Field(None, description="Detection location")
    
    class Config:
        from_attributes = True


class DetectionFilter(BaseModel):
    """Detection filtering parameters"""
    start_date: Optional[datetime] = Field(None, description="Filter start date")
    end_date: Optional[datetime] = Field(None, description="Filter end date")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence")
    plate_text: Optional[str] = Field(None, description="Plate text search")
    camera_id: Optional[str] = Field(None, description="Filter by camera ID")
    state: Optional[str] = Field(None, description="Filter by state")
    status: Optional[str] = Field(None, description="Filter by status")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum results")
    offset: Optional[int] = Field(0, ge=0, description="Results offset")


class SystemHealth(BaseModel):
    """System health status"""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    services: Dict[str, bool] = Field(..., description="Service availability status")
    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage")
    disk_usage: float = Field(..., ge=0.0, le=100.0, description="Disk usage percentage")
    gpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0, description="GPU usage percentage")
    active_cameras: int = Field(..., ge=0, description="Number of active cameras")
    total_detections: int = Field(..., ge=0, description="Total detections count")
    detections_today: int = Field(..., ge=0, description="Today's detections count")


class SystemConfig(BaseModel):
    """System configuration"""
    detection_confidence_threshold: float = Field(0.5, ge=0.1, le=1.0)
    max_concurrent_cameras: int = Field(4, ge=1, le=16)
    auto_enhance_detections: bool = Field(True)
    save_detection_images: bool = Field(True)
    video_recording_enabled: bool = Field(False)
    webhook_notifications: bool = Field(False)
    webhook_url: Optional[str] = Field(None)
    log_level: str = Field("INFO")
    data_retention_days: int = Field(30, ge=1, le=365)


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = Field(True)
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VideoSegmentResponse(BaseModel):
    """Video segment information"""
    id: str = Field(..., description="Video segment ID")
    file_path: str = Field(..., description="Video file path")
    start_time: datetime = Field(..., description="Segment start time")
    end_time: datetime = Field(..., description="Segment end time")
    duration_seconds: float = Field(..., description="Segment duration")
    file_size_bytes: int = Field(..., description="File size in bytes")
    resolution: str = Field(..., description="Video resolution")
    detection_count: int = Field(0, description="Number of detections in segment")
    
    class Config:
        from_attributes = True


class LiveStreamConfig(BaseModel):
    """Live stream configuration"""
    camera_id: str = Field(..., description="Camera ID for streaming")
    quality: str = Field("medium", description="Stream quality (low/medium/high)")
    fps: int = Field(15, ge=5, le=30, description="Stream FPS")
    enable_detection_overlay: bool = Field(True, description="Show detection overlays")
    enable_recording: bool = Field(False, description="Record stream to video")


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = Field(None, description="Message source")


# API Response wrapper models
class CameraListResponse(BaseModel):
    """Camera list response"""
    cameras: List[CameraResponse] = Field(..., description="List of cameras")
    total: int = Field(..., description="Total camera count")


class DetectionListResponse(BaseModel):
    """Detection list response"""
    detections: List[DetectionResponse] = Field(..., description="List of detections") 
    total: int = Field(..., description="Total detection count")
    has_more: bool = Field(..., description="More results available")


class VideoListResponse(BaseModel):
    """Video list response"""
    videos: List[VideoSegmentResponse] = Field(..., description="List of video segments")
    total: int = Field(..., description="Total video count")
    total_size_bytes: int = Field(..., description="Total size in bytes")