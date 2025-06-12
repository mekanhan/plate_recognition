# app/repositories/sql_repository.py
import uuid
import datetime
import time
import logging
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.future import select

from app.interfaces.storage import DetectionRepository, EnhancementRepository
from app.models import Detection, EnhancedResult, KnownPlate, VideoSegment, SystemEvent
from app.database import async_session

logger = logging.getLogger(__name__)

class SQLiteDetectionRepository(DetectionRepository):
    """SQLite implementation of the detection repository"""
    """Repository for video recording management"""
    
    def __init__(self, session_factory=async_session):
        self.session_factory = session_factory
        self.initialization_complete = False

    async def add_video_segment(self,
                               file_path: str,
                               start_time: datetime.datetime,
                               end_time: datetime.datetime,
                               duration_seconds: float,
                               file_size_bytes: int,
                               resolution: str,
                               detection_ids: str) -> str:
        """Add a video segment to the repository"""

    async def shutdown(self) -> None:
        """Shutdown the repository and release resources"""
        self.initialization_complete = False
        logger.info("SQLite video repository shutdown")

    def _segment_to_dict(self, segment: VideoSegment) -> Dict[str, Any]:
        self.session_factory = session_factory
        self.initialization_complete = False
        
    async def initialize(self) -> None:
        """Initialize the repository"""
        self.initialization_complete = True
        logger.info("SQLite detection repository initialized")
        
    async def add_detections(self, detections: List[Dict[str, Any]]) -> None:
        """Add detections to the repository"""
        if not detections:
            return
            
        async with self.session_factory() as session:
            added_count = 0
            for detection_data in detections:
                # Generate ID if not present
                if "detection_id" not in detection_data:
                    detection_data["detection_id"] = str(uuid.uuid4())
                
                detection_id = detection_data.get("detection_id")
                
                # Check if detection already exists
                existing = await session.execute(
                    select(Detection).where(Detection.id == detection_id)
                )
                if existing.scalar_one_or_none() is not None:
                    logger.debug(f"Detection {detection_id} already exists, skipping")
                    continue
                
                # Convert timestamp to datetime if it's a float
                timestamp = detection_data.get("timestamp", time.time())
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.datetime.fromtimestamp(timestamp)
                
                # Extract bounding box if present
                box = detection_data.get("box", [None, None, None, None])
                if len(box) < 4:
                    box = [None, None, None, None]
                
                # Create Detection object
                detection = Detection(
                    id=detection_id,
                    plate_text=detection_data.get("plate_text", ""),
                    confidence=detection_data.get("confidence", 0.0),
                    timestamp=timestamp,
                    box_x1=box[0],
                    box_y1=box[1],
                    box_x2=box[2],
                    box_y2=box[3],
                    frame_id=detection_data.get("frame_id"),
                    raw_text=detection_data.get("raw_text", ""),
                    state=detection_data.get("state"),
                    status=detection_data.get("status", "active"),
                    image_path=detection_data.get("image_path")
                )
                session.add(detection)
                added_count += 1
            
            if added_count > 0:
                await session.commit()
                logger.info(f"Stored {added_count} new detections in the database")
            else:
                logger.debug("No new detections to store")

    async def get_detections(self) -> List[Dict[str, Any]]:
        """Get all detections"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Detection)
                .order_by(Detection.timestamp.desc())
            )
            detections = result.scalars().all()
            
            return [self._detection_to_dict(detection) for detection in detections]
    
    async def get_detection_by_id(self, detection_id: str) -> Optional[Dict[str, Any]]:
        """Get a detection by ID"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Detection).where(Detection.id == detection_id)
            )
            detection = result.scalar_one_or_none()
            
            if not detection:
                return None
                
            return self._detection_to_dict(detection)
    
    async def update_detection_video(self, detection_id: str, video_path: str, 
                                    video_start_time: Optional[datetime.datetime] = None,
                                    video_end_time: Optional[datetime.datetime] = None) -> None:
        """Update a detection with video recording information"""
        async with self.session_factory() as session:
            # Build update values
            update_values = {"video_path": video_path}
            if video_start_time:
                update_values["video_start_time"] = video_start_time
            if video_end_time:
                update_values["video_end_time"] = video_end_time
                
            await session.execute(
                update(Detection)
                .where(Detection.id == detection_id)
                .values(**update_values)
            )
            await session.commit()
    
    async def shutdown(self) -> None:
        """Shutdown the repository"""
        self.initialization_complete = False
        logger.info("SQLite detection repository shutdown")
    
    def _detection_to_dict(self, detection: Detection) -> Dict[str, Any]:
        """Convert a Detection object to a dictionary"""
        return {
            "detection_id": detection.id,
            "plate_text": detection.plate_text,
            "confidence": detection.confidence,
            "timestamp": detection.timestamp.timestamp() if detection.timestamp else None,
            "box": [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2] 
                if all(x is not None for x in [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2]) 
                else None,
            "frame_id": detection.frame_id,
            "raw_text": detection.raw_text,
            "state": detection.state,
            "status": detection.status,
            "image_path": detection.image_path,
            "video_path": detection.video_path,
            "video_start_time": detection.video_start_time.timestamp() if detection.video_start_time else None,
            "video_end_time": detection.video_end_time.timestamp() if detection.video_end_time else None
        }

class SQLiteEnhancementRepository(EnhancementRepository):
    """SQLite implementation of the enhancement repository"""
    
    def __init__(self, session_factory=async_session):
        self.session_factory = session_factory
        self.initialization_complete = False
    
    async def initialize(self) -> None:
        """Initialize the repository"""
        self.initialization_complete = True
        logger.info("SQLite enhancement repository initialized")
    
    async def add_enhanced_results(self, results: List[Dict[str, Any]]) -> None:
        """Add enhanced results to the repository"""
        if not results:
            return
            
        async with self.session_factory() as session:
            for result_data in results:
                # Generate ID if not present
                if "enhanced_id" not in result_data and "id" not in result_data:
                    result_id = str(uuid.uuid4())
                else:
                    result_id = result_data.get("enhanced_id", result_data.get("id"))
                
                # Convert timestamp to datetime if it's a float
                timestamp = result_data.get("timestamp", time.time())
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.datetime.fromtimestamp(timestamp)
                
                # Create EnhancedResult object
                enhanced_result = EnhancedResult(
                    id=result_id,
                    original_detection_id=result_data.get("original_detection_id"),
                    plate_text=result_data.get("plate_text", ""),
                    confidence=result_data.get("confidence", 0.0),
                    timestamp=timestamp,
                    match_type=result_data.get("match_type"),
                    confidence_category=result_data.get("confidence_category"),
                    enhanced_image_path=result_data.get("enhanced_image_path")
                )
                session.add(enhanced_result)
            
            await session.commit()
    
    async def get_enhanced_results(self) -> List[Dict[str, Any]]:
        """Get all enhanced results"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(EnhancedResult)
                .order_by(EnhancedResult.timestamp.desc())
            )
            enhanced_results = result.scalars().all()
            
            return [self._enhanced_result_to_dict(enhanced_result) for enhanced_result in enhanced_results]
    
    async def get_enhanced_result_by_id(self, enhanced_id: str) -> Optional[Dict[str, Any]]:
        """Get an enhanced result by ID"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(EnhancedResult).where(EnhancedResult.id == enhanced_id)
            )
            enhanced_result = result.scalar_one_or_none()
            
            if not enhanced_result:
                return None
                
            return self._enhanced_result_to_dict(enhanced_result)
    
    async def shutdown(self) -> None:
        """Shutdown the repository"""
        self.initialization_complete = False
        logger.info("SQLite enhancement repository shutdown")
    
    def _enhanced_result_to_dict(self, enhanced_result: EnhancedResult) -> Dict[str, Any]:
        """Convert an EnhancedResult object to a dictionary"""
        return {
            "enhanced_id": enhanced_result.id,
            "original_detection_id": enhanced_result.original_detection_id,
            "plate_text": enhanced_result.plate_text,
            "confidence": enhanced_result.confidence,
            "timestamp": enhanced_result.timestamp.timestamp() if enhanced_result.timestamp else None,
            "match_type": enhanced_result.match_type,
            "confidence_category": enhanced_result.confidence_category,
            "enhanced_image_path": enhanced_result.enhanced_image_path
        }

class SQLiteVideoRepository:
    """Repository for video recording management"""
    
    def __init__(self, session_factory=async_session):
        self.session_factory = session_factory
        self.initialization_complete = False
    
    async def add_video_segment(self, 
                               file_path: str,
                               start_time: datetime.datetime,
                               end_time: datetime.datetime,
                               duration_seconds: float,
                               file_size_bytes: int,
                               resolution: str,
                               detection_ids: str) -> str:
        """Add a video segment to the repository"""
        async with self.session_factory() as session:
            segment_id = str(uuid.uuid4())
            segment = VideoSegment(
                id=segment_id,
                file_path=file_path,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                file_size_bytes=file_size_bytes,
                resolution=resolution,
                detection_ids=detection_ids
            )
            session.add(segment)
            await session.commit()
            return segment_id
    
    async def update_video_segment(self, 
                                  segment_id: str,
                                  end_time: datetime.datetime,
                                  duration_seconds: float,
                                  file_size_bytes: int) -> None:
        """Update a video segment with final information"""
        async with self.session_factory() as session:
            await session.execute(
                update(VideoSegment)
                .where(VideoSegment.id == segment_id)
                .values(
                    end_time=end_time,
                    duration_seconds=duration_seconds,
                    file_size_bytes=file_size_bytes
                )
            )
            await session.commit()
    
    async def get_video_segments(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get video segments with pagination"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(VideoSegment)
                .order_by(VideoSegment.start_time.desc())
                .limit(limit).offset(offset)
            )
            segments = result.scalars().all()
            
            return [self._segment_to_dict(segment) for segment in segments]
    
    async def get_video_segment_by_id(self, segment_id: str) -> Optional[Dict[str, Any]]:
        """Get a video segment by ID"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(VideoSegment).where(VideoSegment.id == segment_id)
            )
            segment = result.scalar_one_or_none()
            
            if not segment:
                return None
                
            return self._segment_to_dict(segment)
    
    async def get_video_segment_by_detection_id(self, detection_id: str) -> Optional[Dict[str, Any]]:
        """Find a video segment containing a specific detection"""
        async with self.session_factory() as session:
            # This is a simple but not efficient implementation
            # A more robust solution would use a proper relation or a better query
            result = await session.execute(
                select(VideoSegment)
                .where(VideoSegment.detection_ids.like(f"%{detection_id}%"))
            )
            segment = result.scalar_one_or_none()
            
            if not segment:
                return None
                
            return self._segment_to_dict(segment)
    
    async def cleanup_old_videos(self, days: int = 30) -> int:
        """Archive videos older than specified days"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        async with self.session_factory() as session:
            result = await session.execute(
                update(VideoSegment)
                .where(VideoSegment.start_time < cutoff_date)
                .values(archived=True)
                .returning(VideoSegment.id)
            )
            archived_ids = result.scalars().all()
            await session.commit()
            
            return len(archived_ids)
    
    def _segment_to_dict(self, segment: VideoSegment) -> Dict[str, Any]:
        """Convert a VideoSegment object to a dictionary"""
        return {
            "id": segment.id,
            "file_path": segment.file_path,
            "start_time": segment.start_time.timestamp() if segment.start_time else None,
            "end_time": segment.end_time.timestamp() if segment.end_time else None,
            "duration_seconds": segment.duration_seconds,
            "file_size_bytes": segment.file_size_bytes,
            "resolution": segment.resolution,
            "archived": segment.archived,
            "detection_ids": segment.detection_ids.split(",") if segment.detection_ids else []
        }