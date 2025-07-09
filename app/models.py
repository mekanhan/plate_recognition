# app/models.py
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Boolean, Text, JSON, Enum as SQLEnum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import uuid
import enum

Base = declarative_base()

# Enums for sync status
class SyncStatus(enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    RETRY = "retry"

class Priority(enum.Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class Detection(Base):
    """License plate detection records"""
    __tablename__ = "detections"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plate_text = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False, index=True)  # Added index for confidence filtering
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    
    # Bounding box
    box_x1 = Column(Integer)
    box_y1 = Column(Integer)
    box_x2 = Column(Integer)
    box_y2 = Column(Integer)
    
    # Additional metadata
    frame_id = Column(Integer)
    raw_text = Column(String)
    state = Column(String)
    status = Column(String, default="active", index=True)
    vehicle_type = Column(String)
    direction = Column(String)
    location = Column(String)
    
    # Image and video references
    image_path = Column(String)
    video_path = Column(String)
    video_start_time = Column(DateTime)
    video_end_time = Column(DateTime)
    
    # Sync-related fields
    synced = Column(Boolean, default=False, index=True)
    sync_attempts = Column(Integer, default=0)
    last_sync_attempt = Column(DateTime)
    sync_error = Column(Text)
    
    # Processing metadata
    processing_time_ms = Column(Float)
    ocr_results = Column(JSON)
    
    # Relationships
    enhanced_results = relationship("EnhancedResult", back_populates="detection")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_detection_time_synced', 'timestamp', 'synced'),
        Index('idx_plate_text_time', 'plate_text', 'timestamp'),
        Index('idx_confidence_time', 'confidence', 'timestamp'),
    )

class SyncQueue(Base):
    """Queue for managing data synchronization with cloud"""
    __tablename__ = "sync_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(String, nullable=False, index=True)  # 'detection', 'health', 'logs'
    item_id = Column(String, nullable=False, index=True)    # Reference to the actual record
    data = Column(JSON, nullable=False)                     # Serialized data to sync
    
    # Sync management
    status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, index=True)
    priority = Column(SQLEnum(Priority), default=Priority.NORMAL, index=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    synced_at = Column(DateTime)
    next_retry_at = Column(DateTime, index=True)
    
    # Error handling
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Metadata
    device_id = Column(String, index=True)  # For tracking which device created this
    batch_id = Column(String, index=True)   # For grouping related sync items
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_sync_status_priority', 'status', 'priority', 'created_at'),
        Index('idx_sync_retry_time', 'status', 'next_retry_at'),
        Index('idx_sync_device_time', 'device_id', 'created_at'),
    )

class EnhancedResult(Base):
    """Enhanced license plate results after processing"""
    __tablename__ = "enhanced_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_detection_id = Column(String, ForeignKey("detections.id"), index=True)
    plate_text = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    match_type = Column(String)
    confidence_category = Column(String)
    enhanced_image_path = Column(String)
    
    # Sync fields
    synced = Column(Boolean, default=False, index=True)
    sync_attempts = Column(Integer, default=0)
    
    # Relationship
    detection = relationship("Detection", back_populates="enhanced_results")

class KnownPlate(Base):
    """Known license plates for reference/matching"""
    __tablename__ = "known_plates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plate_text = Column(String, nullable=False, unique=True, index=True)
    state = Column(String)
    added_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    vehicle_type = Column(String)
    notes = Column(Text)
    authorized = Column(Boolean, default=True)

class VideoSegment(Base):
    """Video recording segments"""
    __tablename__ = "video_segments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String, nullable=False, unique=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    resolution = Column(String, nullable=False)
    archived = Column(Boolean, default=False)
    detection_ids = Column(String)  # Comma-separated list of detection IDs
    
    # Sync fields
    synced = Column(Boolean, default=False, index=True)

class SystemEvent(Base):
    """System events for monitoring"""
    __tablename__ = "system_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    event_type = Column(String, nullable=False, index=True)
    details = Column(Text)  # JSON formatted
    level = Column(String, nullable=False, index=True)
    
    # Sync fields  
    synced = Column(Boolean, default=False, index=True)

class DeviceConfig(Base):
    """Device configuration and identity"""
    __tablename__ = "device_config"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String, unique=True, nullable=False)
    api_key_hash = Column(String)  # Hashed for security
    cloud_endpoint = Column(String)
    
    # Device info
    device_type = Column(String, default="edge_lpr")
    capabilities = Column(JSON)
    location_name = Column(String)
    location_lat = Column(Float)
    location_lng = Column(Float)
    
    # Registration
    registration_token = Column(String)
    registered_at = Column(DateTime)
    last_seen = Column(DateTime)
    
    # Sync configuration
    sync_interval = Column(Integer, default=300)  # seconds
    sync_batch_size = Column(Integer, default=50)
    immediate_sync = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
