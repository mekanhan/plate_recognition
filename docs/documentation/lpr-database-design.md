# Database Design

## Prerequisites
- PostgreSQL 12+ installed
- Redis installed for queuing
- AI pipeline implemented (Document 03)

## Overview
Database schema for storing cameras, detections, video recordings, and analytics. Designed for efficient queries and video playback integration.

## Database Schema

### 1. Core Tables

```sql
-- cameras table
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    ip_address INET NOT NULL,
    location VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- detections table
CREATE TABLE detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    plate_text VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    vehicle_type VARCHAR(50),
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    vehicle_bbox INTEGER[],
    plate_bbox INTEGER[],
    frame_path VARCHAR(500),
    plate_image_path VARCHAR(500),
    video_clip_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- video_recordings table (NEW - for playback)
CREATE TABLE video_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    file_path VARCHAR(500) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds INTEGER NOT NULL,
    file_size_mb FLOAT,
    format VARCHAR(20) DEFAULT 'mp4',
    resolution VARCHAR(20),
    fps INTEGER,
    has_detections BOOLEAN DEFAULT FALSE,
    detection_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- video_clips table (short clips around detections)
CREATE TABLE video_clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recording_id UUID REFERENCES video_recordings(id),
    detection_id UUID REFERENCES detections(id),
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    file_path VARCHAR(500) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds FLOAT NOT NULL,
    thumbnail_path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- detection_events table (grouped detections)
CREATE TABLE detection_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    plate_text VARCHAR(20) NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    detection_count INTEGER DEFAULT 1,
    video_clips UUID[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index creation for performance
CREATE INDEX idx_detections_camera_time ON detections(camera_id, detected_at DESC);
CREATE INDEX idx_detections_plate_text ON detections(plate_text);
CREATE INDEX idx_detections_detected_at ON detections(detected_at DESC);
CREATE INDEX idx_video_recordings_camera_time ON video_recordings(camera_id, start_time DESC);
CREATE INDEX idx_video_clips_detection ON video_clips(detection_id);
CREATE INDEX idx_detection_events_plate ON detection_events(plate_text);
```

### 2. Analytics Tables

```sql
-- hourly_statistics table
CREATE TABLE hourly_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    hour_start TIMESTAMP WITH TIME ZONE NOT NULL,
    detection_count INTEGER DEFAULT 0,
    unique_plates INTEGER DEFAULT 0,
    avg_confidence FLOAT,
    video_hours FLOAT DEFAULT 0,
    storage_used_mb FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(camera_id, hour_start)
);

-- alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    detection_id UUID REFERENCES detections(id),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Database Access Layer

### 1. Database Models (SQLAlchemy)

```python
# database/models.py
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, JSON, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class Camera(Base):
    __tablename__ = 'cameras'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    ip_address = Column(INET, nullable=False)
    location = Column(String(200))
    status = Column(String(20), default='active')
    config = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    detections = relationship("Detection", back_populates="camera")
    recordings = relationship("VideoRecording", back_populates="camera")

class Detection(Base):
    __tablename__ = 'detections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(50), ForeignKey('cameras.camera_id'))
    plate_text = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    vehicle_type = Column(String(50))
    detected_at = Column(DateTime(timezone=True), nullable=False)
    vehicle_bbox = Column(ARRAY(Integer))
    plate_bbox = Column(ARRAY(Integer))
    frame_path = Column(String(500))
    plate_image_path = Column(String(500))
    video_clip_id = Column(UUID(as_uuid=True), ForeignKey('video_clips.id'))
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="detections")
    video_clip = relationship("VideoClip", back_populates="detection")

class VideoRecording(Base):
    __tablename__ = 'video_recordings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(50), ForeignKey('cameras.camera_id'))
    file_path = Column(String(500), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    file_size_mb = Column(Float)
    format = Column(String(20), default='mp4')
    resolution = Column(String(20))
    fps = Column(Integer)
    has_detections = Column(Boolean, default=False)
    detection_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="recordings")
    clips = relationship("VideoClip", back_populates="recording")

class VideoClip(Base):
    __tablename__ = 'video_clips'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recording_id = Column(UUID(as_uuid=True), ForeignKey('video_recordings.id'))
    detection_id = Column(UUID(as_uuid=True), ForeignKey('detections.id'))
    camera_id = Column(String(50), ForeignKey('cameras.camera_id'))
    file_path = Column(String(500), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Float, nullable=False)
    thumbnail_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    recording = relationship("VideoRecording", back_populates="clips")
    detection = relationship("Detection", back_populates="video_clip")
```

### 2. Database Service

```python
# database/service.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json
import redis.asyncio as redis

class DatabaseService:
    def __init__(self, database_url: str, redis_url: str = "redis://localhost"):
        self.engine = create_async_engine(database_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.redis = redis.from_url(redis_url)
        
    async def save_detection(self, detection_data: Dict):
        """Save detection to database"""
        async with self.async_session() as session:
            detection = Detection(**detection_data)
            session.add(detection)
            await session.commit()
            return detection.id
    
    async def process_detection_queue(self):
        """Process detections from Redis queue"""
        while True:
            # Get detection from queue
            data = await self.redis.rpop("detection_queue")
            if not data:
                await asyncio.sleep(0.1)
                continue
            
            try:
                detection_data = json.loads(data)
                detection_data['detected_at'] = datetime.fromisoformat(
                    detection_data['timestamp']
                )
                del detection_data['timestamp']
                
                await self.save_detection(detection_data)
                
            except Exception as e:
                logging.error(f"Error saving detection: {e}")
                # Put back in queue for retry
                await self.redis.lpush("detection_queue", data)
    
    async def save_video_recording(self, recording_data: Dict) -> UUID:
        """Save video recording metadata"""
        async with self.async_session() as session:
            recording = VideoRecording(**recording_data)
            session.add(recording)
            await session.commit()
            return recording.id
    
    async def create_video_clip(self, detection_id: UUID, recording_id: UUID, 
                               clip_data: Dict) -> UUID:
        """Create video clip for detection"""
        async with self.async_session() as session:
            clip = VideoClip(
                detection_id=detection_id,
                recording_id=recording_id,
                **clip_data
            )
            session.add(clip)
            
            # Update detection with clip reference
            detection = await session.get(Detection, detection_id)
            detection.video_clip_id = clip.id
            
            await session.commit()
            return clip.id
    
    async def get_recent_detections(self, limit: int = 100) -> List[Detection]:
        """Get recent detections"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Detection)
                .order_by(Detection.detected_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def get_detections_with_video(self, 
                                       start_time: datetime,
                                       end_time: datetime,
                                       camera_id: Optional[str] = None) -> List[Dict]:
        """Get detections with video playback info"""
        async with self.async_session() as session:
            query = select(
                Detection, VideoClip, VideoRecording
            ).join(
                VideoClip, Detection.video_clip_id == VideoClip.id
            ).join(
                VideoRecording, VideoClip.recording_id == VideoRecording.id
            ).where(
                and_(
                    Detection.detected_at >= start_time,
                    Detection.detected_at <= end_time
                )
            )
            
            if camera_id:
                query = query.where(Detection.camera_id == camera_id)
            
            result = await session.execute(query)
            
            detections = []
            for detection, clip, recording in result:
                detections.append({
                    'detection': detection,
                    'clip': clip,
                    'recording': recording,
                    'playback_url': f"/api/video/clip/{clip.id}"
                })
            
            return detections
    
    async def update_hourly_statistics(self, camera_id: str, hour: datetime):
        """Update hourly statistics"""
        async with self.async_session() as session:
            # Get detection count for the hour
            result = await session.execute(
                select(func.count(Detection.id), func.count(func.distinct(Detection.plate_text)))
                .where(
                    and_(
                        Detection.camera_id == camera_id,
                        Detection.detected_at >= hour,
                        Detection.detected_at < hour + timedelta(hours=1)
                    )
                )
            )
            detection_count, unique_plates = result.first()
            
            # Update or create statistics
            stats = await session.execute(
                select(HourlyStatistics).where(
                    and_(
                        HourlyStatistics.camera_id == camera_id,
                        HourlyStatistics.hour_start == hour
                    )
                )
            )
            stats = stats.scalar_one_or_none()
            
            if stats:
                stats.detection_count = detection_count
                stats.unique_plates = unique_plates
            else:
                stats = HourlyStatistics(
                    camera_id=camera_id,
                    hour_start=hour,
                    detection_count=detection_count,
                    unique_plates=unique_plates
                )
                session.add(stats)
            
            await session.commit()
```

## Video Storage Integration

### Video Recording Service

```python
# services/video_recorder.py
import cv2
import os
from datetime import datetime
import asyncio
from pathlib import Path

class VideoRecorder:
    """Records continuous video and creates clips for detections"""
    
    def __init__(self, 
                 output_dir: str = "recordings",
                 segment_duration: int = 300,  # 5 minute segments
                 clip_duration: int = 30,      # 30 second clips
                 fps: int = 30,
                 codec: str = "mp4v"):
        
        self.output_dir = Path(output_dir)
        self.segment_duration = segment_duration
        self.clip_duration = clip_duration
        self.fps = fps
        self.codec = codec
        self.recordings = {}
        
        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "continuous").mkdir(exist_ok=True)
        (self.output_dir / "clips").mkdir(exist_ok=True)
        (self.output_dir / "thumbnails").mkdir(exist_ok=True)
    
    def start_recording(self, camera_id: str, frame_size: tuple):
        """Start recording for a camera"""
        if camera_id not in self.recordings:
            self.recordings[camera_id] = {
                'buffer': [],
                'writer': None,
                'start_time': datetime.now(),
                'frame_count': 0
            }
    
    async def add_frame(self, camera_id: str, frame):
        """Add frame to recording buffer and continuous recording"""
        if camera_id not in self.recordings:
            return
        
        rec = self.recordings[camera_id]
        
        # Add to circular buffer for clips (keep last 30 seconds)
        rec['buffer'].append({
            'frame': frame.copy(),
            'timestamp': datetime.now()
        })
        
        # Keep only last N seconds in buffer
        buffer_size = self.fps * self.clip_duration
        if len(rec['buffer']) > buffer_size:
            rec['buffer'] = rec['buffer'][-buffer_size:]
        
        # Write to continuous recording
        if rec['writer'] is None or rec['frame_count'] >= self.fps * self.segment_duration:
            await self._start_new_segment(camera_id, frame.shape[:2][::-1])
        
        rec['writer'].write(frame)
        rec['frame_count'] += 1
    
    async def create_detection_clip(self, 
                                   camera_id: str, 
                                   detection_time: datetime,
                                   detection_id: str) -> Dict:
        """Create video clip around detection time"""
        if camera_id not in self.recordings:
            return None
        
        rec = self.recordings[camera_id]
        
        # Find frames around detection time
        clip_start = detection_time - timedelta(seconds=10)
        clip_end = detection_time + timedelta(seconds=20)
        
        clip_frames = [
            f for f in rec['buffer']
            if clip_start <= f['timestamp'] <= clip_end
        ]
        
        if not clip_frames:
            return None
        
        # Write clip
        clip_path = self.output_dir / "clips" / f"{detection_id}.mp4"
        height, width = clip_frames[0]['frame'].shape[:2]
        
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        writer = cv2.VideoWriter(
            str(clip_path), fourcc, self.fps, (width, height)
        )
        
        for frame_data in clip_frames:
            writer.write(frame_data['frame'])
        
        writer.release()
        
        # Create thumbnail
        middle_frame = clip_frames[len(clip_frames) // 2]['frame']
        thumbnail_path = self.output_dir / "thumbnails" / f"{detection_id}.jpg"
        cv2.imwrite(str(thumbnail_path), middle_frame)
        
        return {
            'file_path': str(clip_path),
            'thumbnail_path': str(thumbnail_path),
            'start_time': clip_frames[0]['timestamp'],
            'end_time': clip_frames[-1]['timestamp'],
            'duration_seconds': (clip_frames[-1]['timestamp'] - clip_frames[0]['timestamp']).total_seconds()
        }
```

## Common Pitfalls

### ❌ DON'T:
1. Store raw video frames in database
2. Keep all video in memory
3. Create clips synchronously during detection
4. Store video without indexing

### ✅ DO:
1. Store video files on disk with metadata in DB
2. Use circular buffers for clip creation
3. Create clips asynchronously after detection
4. Index by time and camera for fast retrieval

## Next Steps

Continue to: **[05 - Web Dashboard](./05-web-dashboard.md)**

---

*AI Agent Note: Video storage is separate from streaming. We store for playback, not live viewing. Browser can play back stored clips easily using standard HTML5 video tags.*