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
    port = Column(Integer, default=80)
    connection_type = Column(String(20), default='http')  # http, rtsp, https
    stream_path = Column(String(200), default='/mjpeg')
    location = Column(String(200))
    username = Column(String(100))
    password = Column(String(100))
    # Video settings
    brand = Column(String(50))
    model = Column(String(50))
    resolution_width = Column(Integer, default=1920)
    resolution_height = Column(Integer, default=1080)
    max_fps = Column(Integer, default=30)
    video_quality = Column(String(20), default='medium')  # high, medium, low
    low_latency = Column(Boolean, default=True)
    # Status and metadata
    status = Column(String(20), default='active')  # active, inactive, error
    last_test_at = Column(DateTime)
    last_test_result = Column(String(20))  # success, failed, timeout
    config = Column(JSON, default={})  # Additional configuration
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
    filename = Column(String(255), unique=True, nullable=False)  # Unique segment filename
    camera_id = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    file_size_bytes = Column(Integer)  # Changed from MB to bytes for precision
    video_codec = Column(String(20), default='h264')
    video_width = Column(Integer, default=3840)  # 4K width
    video_height = Column(Integer, default=2160)  # 4K height
    video_fps = Column(Integer, default=30)
    is_compressed = Column(Boolean, default=True)
    compression_ratio = Column(Float)
    has_audio = Column(Boolean, default=False)
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

class DailySummary(Base):
    __tablename__ = 'daily_summaries'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(50), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    total_segments = Column(Integer, default=0)
    total_duration_seconds = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    first_segment_time = Column(DateTime)
    last_segment_time = Column(DateTime)
    coverage_percentage = Column(Float, default=0.0)
    gaps_count = Column(Integer, default=0)
    gaps_duration_seconds = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StorageStats(Base):
    __tablename__ = 'storage_stats'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_size_bytes = Column(Integer, nullable=False)
    segment_count = Column(Integer, nullable=False)
    camera_count = Column(Integer, nullable=False)
    oldest_segment_date = Column(String(10))  # YYYY-MM-DD
    newest_segment_date = Column(String(10))  # YYYY-MM-DD

# Database indexes for efficient queries
from sqlalchemy import Index

# Indexes for VideoRecording (segments) table - critical for playback performance
Index('idx_video_recording_camera_time', VideoRecording.camera_id, VideoRecording.start_time)
Index('idx_video_recording_filename', VideoRecording.filename)
Index('idx_video_recording_date', VideoRecording.start_time)

# Indexes for DailySummary table - for calendar queries
Index('idx_daily_summary_camera_date', DailySummary.camera_id, DailySummary.date)

# Indexes for Detection table - for timeline event markers
Index('idx_detection_camera_time', Detection.camera_id, Detection.detected_at)

# Indexes for Camera table
Index('idx_camera_camera_id', Camera.camera_id)