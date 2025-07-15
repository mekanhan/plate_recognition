# app/models.py
# Centralized database schema for multi-camera LPR processing
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Boolean, Text, JSON, Enum as SQLEnum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import uuid
import enum

Base = declarative_base()

# Enums for centralized system
class CameraStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    MAINTENANCE = "maintenance"

class CameraType(enum.Enum):
    IP_CAMERA = "ip_camera"
    USB_CAMERA = "usb_camera"
    CSI_CAMERA = "csi_camera"

class ProcessingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Priority(enum.Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class AlertLevel(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# Location management for multiple sites
class Location(Base):
    """Physical locations where cameras are deployed"""
    __tablename__ = "locations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True, index=True)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String, default="USA")
    
    # Geographic coordinates
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Configuration
    timezone = Column(String, default="UTC")
    active = Column(Boolean, default=True, index=True)
    
    # Metadata
    description = Column(Text)
    contact_info = Column(JSON)  # Contact person, phone, email
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    camera_groups = relationship("CameraGroup", back_populates="location")
    cameras = relationship("Camera", back_populates="location")
    detections = relationship("Detection", back_populates="location")

class CameraGroup(Base):
    """Logical grouping of cameras by purpose/zone"""
    __tablename__ = "camera_groups"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False, index=True)
    
    # Group configuration
    description = Column(Text)
    purpose = Column(String)  # entrance, exit, parking, loading, perimeter
    priority = Column(SQLEnum(Priority), default=Priority.NORMAL, index=True)
    
    # Processing settings
    detection_threshold = Column(Float, default=0.7)
    processing_enabled = Column(Boolean, default=True)
    recording_enabled = Column(Boolean, default=True)
    
    # Alert settings
    alert_enabled = Column(Boolean, default=True)
    alert_threshold = Column(Float, default=0.9)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    location = relationship("Location", back_populates="camera_groups")
    cameras = relationship("Camera", back_populates="camera_group")

class Camera(Base):
    """Individual camera configuration and management"""
    __tablename__ = "cameras"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False, index=True)
    camera_group_id = Column(String, ForeignKey("camera_groups.id"), index=True)
    
    # Camera identification
    camera_type = Column(SQLEnum(CameraType), nullable=False)
    manufacturer = Column(String)
    model = Column(String)
    serial_number = Column(String, unique=True)
    
    # Network configuration
    ip_address = Column(String, unique=True, index=True)
    port = Column(Integer, default=554)
    username = Column(String)
    password_hash = Column(String)  # Encrypted password
    
    # Stream configuration
    main_stream_url = Column(String)
    sub_stream_url = Column(String)
    snapshot_url = Column(String)
    
    # Technical specifications
    resolution_width = Column(Integer, default=1920)
    resolution_height = Column(Integer, default=1080)
    fps = Column(Integer, default=30)
    codec = Column(String, default="H.264")
    
    # Status and health
    status = Column(SQLEnum(CameraStatus), default=CameraStatus.OFFLINE, index=True)
    last_seen = Column(DateTime, index=True)
    health_score = Column(Float, default=100.0)  # 0-100
    
    # Processing configuration
    detection_enabled = Column(Boolean, default=True)
    recording_enabled = Column(Boolean, default=True)
    processing_priority = Column(SQLEnum(Priority), default=Priority.NORMAL)
    
    # Physical installation
    installation_location = Column(String)  # "Main Entrance", "Loading Dock 2"
    viewing_direction = Column(String)  # "North", "Inbound", "Outbound"
    mounting_height = Column(Float)  # meters
    viewing_angle = Column(Float)  # degrees
    
    # Configuration
    detection_zones = Column(JSON)  # Polygonal detection zones
    recording_schedule = Column(JSON)  # Recording time schedules
    alert_settings = Column(JSON)  # Alert configuration
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    installed_at = Column(DateTime)
    
    # Relationships
    location = relationship("Location", back_populates="cameras")
    camera_group = relationship("CameraGroup", back_populates="cameras")
    detections = relationship("Detection", back_populates="camera")
    camera_health = relationship("CameraHealth", back_populates="camera", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_camera_location_status', 'location_id', 'status'),
        Index('idx_camera_group_priority', 'camera_group_id', 'processing_priority'),
        Index('idx_camera_ip_status', 'ip_address', 'status'),
    )

class CameraHealth(Base):
    """Camera health monitoring and metrics"""
    __tablename__ = "camera_health"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), unique=True, nullable=False, index=True)
    
    # Connectivity metrics
    uptime_percentage = Column(Float, default=0.0)  # Last 24 hours
    connection_failures = Column(Integer, default=0)
    last_connection_error = Column(Text)
    
    # Performance metrics
    avg_response_time = Column(Float)  # milliseconds
    frame_drop_rate = Column(Float, default=0.0)  # percentage
    processing_lag = Column(Float)  # seconds
    
    # Stream quality
    stream_errors = Column(Integer, default=0)
    image_quality_score = Column(Float, default=100.0)  # 0-100
    
    # Detection performance
    detections_per_hour = Column(Float, default=0.0)
    avg_detection_confidence = Column(Float, default=0.0)
    false_positive_rate = Column(Float, default=0.0)
    
    # System resources
    bandwidth_usage = Column(Float)  # Mbps
    storage_usage = Column(Float)  # GB per day
    
    # Timestamps
    last_health_check = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="camera_health")

class Detection(Base):
    """License plate detection records - centralized version"""
    __tablename__ = "detections"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False, index=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False, index=True)
    
    # Detection data
    plate_text = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    
    # Bounding box
    box_x1 = Column(Integer)
    box_y1 = Column(Integer)
    box_x2 = Column(Integer)
    box_y2 = Column(Integer)
    
    # Vehicle information
    vehicle_type = Column(String, index=True)
    vehicle_color = Column(String)
    vehicle_make = Column(String)
    vehicle_model = Column(String)
    direction = Column(String, index=True)  # entering, exiting, passing
    speed = Column(Float)  # mph or kmh
    
    # Processing information
    frame_id = Column(Integer)
    processing_time_ms = Column(Float)
    processing_node = Column(String)  # Which server/GPU processed this
    model_version = Column(String)
    
    # Enhanced data
    raw_text = Column(String)
    state = Column(String)
    country = Column(String, default="USA")
    
    # Status and validation
    status = Column(String, default="pending", index=True)  # pending, verified, flagged, archived
    verified_by = Column(String)  # User ID who verified
    verified_at = Column(DateTime)
    flagged_reason = Column(String)
    
    # File references
    image_path = Column(String)
    enhanced_image_path = Column(String)
    video_path = Column(String)
    video_start_time = Column(DateTime)
    video_end_time = Column(DateTime)
    
    # OCR and analysis results
    ocr_results = Column(JSON)
    analysis_metadata = Column(JSON)
    
    # Relationships
    camera = relationship("Camera", back_populates="detections")
    location = relationship("Location", back_populates="detections")
    enhanced_results = relationship("EnhancedResult", back_populates="detection")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_detection_camera_time', 'camera_id', 'timestamp'),
        Index('idx_detection_location_time', 'location_id', 'timestamp'),
        Index('idx_plate_text_time', 'plate_text', 'timestamp'),
        Index('idx_confidence_time', 'confidence', 'timestamp'),
        Index('idx_status_time', 'status', 'timestamp'),
        Index('idx_detection_vehicle_type', 'vehicle_type', 'timestamp'),
    )

class EnhancedResult(Base):
    """Enhanced license plate results after processing - centralized version"""
    __tablename__ = "enhanced_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_detection_id = Column(String, ForeignKey("detections.id"), index=True)
    
    # Enhanced detection data
    plate_text = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    enhancement_method = Column(String)  # OCR engine used
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Enhancement details
    match_type = Column(String)
    confidence_category = Column(String)
    enhancement_quality = Column(Float)  # 0-1 score
    
    # Processing information
    processing_time_ms = Column(Float)
    enhancement_node = Column(String)  # Which server processed this
    
    # File references
    enhanced_image_path = Column(String)
    analysis_data = Column(JSON)
    
    # Relationship
    detection = relationship("Detection", back_populates="enhanced_results")

class KnownPlate(Base):
    """Known license plates for reference/matching - enhanced for multi-location"""
    __tablename__ = "known_plates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plate_text = Column(String, nullable=False, index=True)
    location_id = Column(String, ForeignKey("locations.id"), index=True)
    
    # Plate information
    state = Column(String)
    country = Column(String, default="USA")
    plate_type = Column(String)  # standard, commercial, temporary, etc.
    
    # Vehicle information
    vehicle_type = Column(String)
    vehicle_make = Column(String)
    vehicle_model = Column(String)
    vehicle_year = Column(Integer)
    vehicle_color = Column(String)
    
    # Authorization and access
    authorized = Column(Boolean, default=True, index=True)
    access_level = Column(String, default="standard")
    access_schedule = Column(JSON)  # Time-based access rules
    
    # Administrative information
    owner_name = Column(String)
    owner_contact = Column(String)
    notes = Column(Text)
    tags = Column(JSON)  # Flexible tagging system
    
    # Validity and expiration
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    auto_expire = Column(Boolean, default=False)
    
    # Timestamps
    added_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    added_by = Column(String)  # User ID
    
    # Relationships
    location = relationship("Location")
    
    # Indexes
    __table_args__ = (
        Index('idx_known_plate_location', 'plate_text', 'location_id'),
        Index('idx_known_plate_authorized', 'authorized', 'location_id'),
        Index('idx_known_plate_expiry', 'valid_until', 'auto_expire'),
    )

class VideoSegment(Base):
    """Video recording segments - centralized version"""
    __tablename__ = "video_segments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False, index=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False, index=True)
    
    # File information
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    
    # Video specifications
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    resolution = Column(String, nullable=False)
    fps = Column(Integer)
    codec = Column(String)
    bitrate = Column(Integer)
    
    # Content information
    detection_ids = Column(JSON)  # List of detection IDs in this segment
    detection_count = Column(Integer, default=0)
    motion_events = Column(JSON)  # Motion detection events
    
    # Storage management
    archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime)
    storage_tier = Column(String, default="active")  # active, cold, archived
    
    # Metadata
    recording_reason = Column(String)  # continuous, motion, detection, manual
    quality_score = Column(Float)  # Video quality assessment
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera")
    location = relationship("Location")
    
    # Indexes
    __table_args__ = (
        Index('idx_video_camera_time', 'camera_id', 'start_time'),
        Index('idx_video_location_time', 'location_id', 'start_time'),
        Index('idx_video_archived', 'archived', 'start_time'),
    )

class SystemEvent(Base):
    """System events for monitoring - centralized version"""
    __tablename__ = "system_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    
    # Event classification
    event_type = Column(String, nullable=False, index=True)  # camera, detection, system, user
    event_category = Column(String, nullable=False, index=True)  # error, warning, info, success
    level = Column(SQLEnum(AlertLevel), nullable=False, index=True)
    
    # Event details
    title = Column(String, nullable=False)
    description = Column(Text)
    details = Column(JSON)  # Structured event data
    
    # Context
    camera_id = Column(String, ForeignKey("cameras.id"), index=True)
    location_id = Column(String, ForeignKey("locations.id"), index=True)
    user_id = Column(String, index=True)
    session_id = Column(String)
    
    # Resolution tracking
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_by = Column(String)
    acknowledged_at = Column(DateTime)
    resolved = Column(Boolean, default=False, index=True)
    resolved_by = Column(String)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Relationships
    camera = relationship("Camera")
    location = relationship("Location")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_type_level_time', 'event_type', 'level', 'timestamp'),
        Index('idx_event_camera_time', 'camera_id', 'timestamp'),
        Index('idx_event_location_time', 'location_id', 'timestamp'),
        Index('idx_event_status', 'acknowledged', 'resolved', 'timestamp'),
    )

class ProcessingQueue(Base):
    """Queue for managing detection processing across multiple cameras"""
    __tablename__ = "processing_queue"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False, index=True)
    
    # Queue information
    frame_data = Column(JSON)  # Frame metadata and references
    priority = Column(SQLEnum(Priority), default=Priority.NORMAL, index=True)
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    
    # Processing assignment
    assigned_node = Column(String, index=True)  # Which processing node
    assigned_gpu = Column(Integer)  # GPU ID
    worker_id = Column(String)  # Worker process ID
    
    # Timing
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    assigned_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    detection_id = Column(String, ForeignKey("detections.id"), index=True)
    processing_time_ms = Column(Float)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    camera = relationship("Camera")
    detection = relationship("Detection")
    
    # Indexes
    __table_args__ = (
        Index('idx_queue_status_priority', 'status', 'priority', 'created_at'),
        Index('idx_queue_camera_status', 'camera_id', 'status'),
        Index('idx_queue_node_status', 'assigned_node', 'status'),
    )

class User(Base):
    """User management for centralized system"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    
    # Profile information
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    
    # Access control
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False, index=True)
    role = Column(String, default="viewer", index=True)  # admin, operator, viewer
    
    # Location access
    location_access = Column(JSON)  # List of accessible location IDs
    permissions = Column(JSON)  # Detailed permissions
    
    # Security
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_active_role', 'is_active', 'role'),
        Index('idx_user_login', 'last_login', 'is_active'),
    )