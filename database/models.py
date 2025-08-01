"""
Database models
Uses SQLAlchemy for async SQLite (following existing system architecture)
"""
from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Camera(Base):
    __tablename__ = 'cameras'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)
    location = Column(String(200))
    status = Column(String(20), default='active')
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Detection(Base):
    __tablename__ = 'detections'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(50), nullable=False)
    plate_text = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    vehicle_type = Column(String(50))
    detected_at = Column(DateTime, nullable=False)
    vehicle_bbox = Column(JSON)  # Store as JSON array [x1, y1, x2, y2]
    plate_bbox = Column(JSON)    # Store as JSON array [x1, y1, x2, y2]
    frame_path = Column(String(500))
    plate_image_path = Column(String(500))
    video_clip_id = Column(String(36))
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

class VideoRecording(Base):
    __tablename__ = 'video_recordings'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    file_size_mb = Column(Float)
    format = Column(String(20), default='mp4')
    resolution = Column(String(20))
    fps = Column(Integer)
    has_detections = Column(Boolean, default=False)
    detection_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class VideoClip(Base):
    __tablename__ = 'video_clips'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id = Column(String(36))
    detection_id = Column(String(36))
    camera_id = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    thumbnail_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

class DetectionEvent(Base):
    __tablename__ = 'detection_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(50), nullable=False)
    plate_text = Column(String(20), nullable=False)
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    detection_count = Column(Integer, default=1)
    video_clips = Column(JSON, default=[])  # Array of clip IDs
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

class HourlyStatistics(Base):
    __tablename__ = 'hourly_statistics'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(50), nullable=False)
    hour_start = Column(DateTime, nullable=False)
    detection_count = Column(Integer, default=0)
    unique_plates = Column(Integer, default=0)
    avg_confidence = Column(Float)
    video_hours = Column(Float, default=0)
    storage_used_mb = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    camera_id = Column(String(50))
    detection_id = Column(String(36))
    message = Column(Text, nullable=False)
    meta_data = Column(JSON, default={})
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)