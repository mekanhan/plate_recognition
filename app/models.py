# app/models.py
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime
import uuid

Base = declarative_base()

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
    
    # Camera information
    camera_id = Column(String, ForeignKey("cameras.id"), index=True)
    camera_name = Column(String)  # Cached camera name for performance
    
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
    
    # Relationships
    enhanced_results = relationship("EnhancedResult", back_populates="detection")

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

class SystemEvent(Base):
    """System events for monitoring"""
    __tablename__ = "system_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    event_type = Column(String, nullable=False, index=True)
    details = Column(Text)  # JSON formatted
    level = Column(String, nullable=False, index=True)

class Camera(Base):
    """Camera registry database model"""
    __tablename__ = "cameras"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="offline", index=True)
    location = Column(String(200))
    
    # JSON columns for complex data
    source_config = Column(JSON, nullable=False)
    capabilities = Column(JSON)
    
    # Metadata
    auto_discovered = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    last_seen = Column(DateTime, index=True)
    
    # Performance tracking
    frames_processed = Column(Integer, default=0)
    detections_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    uptime_seconds = Column(Integer, default=0)
    
    # Relationships
    detections = relationship("Detection", backref="camera")

class CameraSession(Base):
    """Camera session tracking"""
    __tablename__ = "camera_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False, index=True)
    session_start = Column(DateTime, nullable=False, default=func.now())
    session_end = Column(DateTime)
    frames_processed = Column(Integer, default=0)
    detections_made = Column(Integer, default=0)
    disconnection_reason = Column(String(100))