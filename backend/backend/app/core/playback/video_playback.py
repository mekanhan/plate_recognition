"""
Video Playback System for 24/7 Recording
Handles timeline generation, segment retrieval, and video streaming
"""
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TimelineSegment:
    """Represents a video segment in the timeline"""
    id: int
    camera_id: int
    filename: str
    file_path: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    file_size: int
    exists: bool = True


@dataclass 
class PlaybackInfo:
    """Information for playing back video at a specific time"""
    segment: TimelineSegment
    offset_seconds: float
    
    
class VideoPlayback:
    """Handles video playback functionality for recorded segments"""
    
    def __init__(self, base_path: str = "recordings"):
        self.base_path = Path(base_path)
        logger.info(f"Video playback initialized with base path: {self.base_path}")
    
    async def get_camera_timeline(
        self, 
        camera_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[TimelineSegment]:
        """
        Get timeline segments for a camera within a time range
        
        Args:
            camera_id: Camera ID
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of TimelineSegment objects
        """
        segments = []
        
        try:
            camera_dir = self.base_path / f"camera_{camera_id}"
            if not camera_dir.exists():
                logger.warning(f"Camera directory not found: {camera_dir}")
                return segments
            
            index_db = camera_dir / "index.db"
            if not index_db.exists():
                logger.warning(f"Index database not found: {index_db}")
                return segments
            
            # Query segments from database
            with sqlite3.connect(str(index_db)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, camera_id, filename, file_path, 
                           start_time, end_time, duration_seconds, file_size
                    FROM video_segments
                    WHERE start_time < ? AND end_time > ?
                    ORDER BY start_time
                """, (end_time.isoformat(), start_time.isoformat()))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    file_path = Path(row['file_path'])
                    segment = TimelineSegment(
                        id=row['id'],
                        camera_id=row['camera_id'],
                        filename=row['filename'],
                        file_path=row['file_path'],
                        start_time=datetime.fromisoformat(row['start_time']),
                        end_time=datetime.fromisoformat(row['end_time']),
                        duration_seconds=row['duration_seconds'],
                        file_size=row['file_size'],
                        exists=file_path.exists()
                    )
                    segments.append(segment)
            
            logger.info(f"Found {len(segments)} segments for camera {camera_id} "
                       f"between {start_time} and {end_time}")
            
        except Exception as e:
            logger.error(f"Error getting timeline: {e}", exc_info=True)
        
        return segments
    
    async def get_segment_by_id(self, segment_id: str) -> Optional[TimelineSegment]:
        """
        Get a specific segment by ID
        
        Args:
            segment_id: Segment ID (filename without extension)
            
        Returns:
            TimelineSegment or None
        """
        try:
            # Parse camera ID from segment ID
            # Format: 3_camera_3_20250725_182548_600
            parts = segment_id.split('_')
            if len(parts) >= 2:
                camera_id = int(parts[0])
            else:
                logger.error(f"Invalid segment ID format: {segment_id}")
                return None
            
            camera_dir = self.base_path / f"camera_{camera_id}"
            index_db = camera_dir / "index.db"
            
            if not index_db.exists():
                return None
            
            with sqlite3.connect(str(index_db)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Search by filename (with or without extension)
                cursor.execute("""
                    SELECT id, camera_id, filename, file_path,
                           start_time, end_time, duration_seconds, file_size
                    FROM video_segments
                    WHERE filename LIKE ?
                """, (f"{segment_id}%",))
                
                row = cursor.fetchone()
                
                if row:
                    file_path = Path(row['file_path'])
                    return TimelineSegment(
                        id=row['id'],
                        camera_id=row['camera_id'],
                        filename=row['filename'],
                        file_path=row['file_path'],
                        start_time=datetime.fromisoformat(row['start_time']),
                        end_time=datetime.fromisoformat(row['end_time']),
                        duration_seconds=row['duration_seconds'],
                        file_size=row['file_size'],
                        exists=file_path.exists()
                    )
        
        except Exception as e:
            logger.error(f"Error getting segment {segment_id}: {e}")
        
        return None
    
    async def get_playback_info(
        self, 
        camera_id: int, 
        timestamp: datetime
    ) -> Optional[Dict]:
        """
        Get playback information for a specific timestamp
        
        Args:
            camera_id: Camera ID
            timestamp: Target timestamp
            
        Returns:
            Dictionary with segment info and offset, or None
        """
        try:
            # Get segments around the timestamp
            segments = await self.get_camera_timeline(
                camera_id,
                timestamp - timedelta(minutes=15),
                timestamp + timedelta(minutes=15)
            )
            
            # Find the segment containing the timestamp
            for segment in segments:
                if segment.start_time <= timestamp <= segment.end_time:
                    # Calculate offset within segment
                    offset_seconds = (timestamp - segment.start_time).total_seconds()
                    
                    return {
                        'segment': segment,
                        'offset_seconds': offset_seconds,
                        'segment_id': segment.filename,
                        'file_path': segment.file_path,
                        'exists': segment.exists
                    }
            
            logger.debug(f"No segment found for camera {camera_id} at {timestamp}")
            
        except Exception as e:
            logger.error(f"Error getting playback info: {e}")
        
        return None
    
    async def get_available_time_ranges(
        self, 
        camera_id: int, 
        date: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """
        Get available time ranges for a specific date
        
        Args:
            camera_id: Camera ID
            date: Date to check (time ignored)
            
        Returns:
            List of (start, end) datetime tuples
        """
        ranges = []
        
        try:
            # Get all segments for the day
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            segments = await self.get_camera_timeline(camera_id, start_of_day, end_of_day)
            
            if not segments:
                return ranges
            
            # Merge continuous segments into ranges
            current_start = segments[0].start_time
            current_end = segments[0].end_time
            
            for segment in segments[1:]:
                # Check if segments are continuous (within 1 minute gap)
                if (segment.start_time - current_end).total_seconds() <= 60:
                    # Extend current range
                    current_end = segment.end_time
                else:
                    # Gap found, save current range and start new one
                    ranges.append((current_start, current_end))
                    current_start = segment.start_time
                    current_end = segment.end_time
            
            # Add the last range
            ranges.append((current_start, current_end))
            
        except Exception as e:
            logger.error(f"Error getting time ranges: {e}")
        
        return ranges
    
    async def search_recordings(
        self,
        camera_id: int,
        start_date: datetime,
        end_date: datetime,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None
    ) -> List[TimelineSegment]:
        """
        Search for recordings with specific criteria
        
        Args:
            camera_id: Camera ID
            start_date: Start date for search
            end_date: End date for search  
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
            
        Returns:
            List of matching segments
        """
        segments = []
        
        try:
            camera_dir = self.base_path / f"camera_{camera_id}"
            index_db = camera_dir / "index.db"
            
            if not index_db.exists():
                return segments
            
            with sqlite3.connect(str(index_db)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query
                query = """
                    SELECT id, camera_id, filename, file_path,
                           start_time, end_time, duration_seconds, file_size
                    FROM video_segments
                    WHERE start_time >= ? AND end_time <= ?
                """
                params = [start_date.isoformat(), end_date.isoformat()]
                
                if min_duration is not None:
                    query += " AND duration_seconds >= ?"
                    params.append(min_duration)
                
                if max_duration is not None:
                    query += " AND duration_seconds <= ?"
                    params.append(max_duration)
                
                query += " ORDER BY start_time"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    file_path = Path(row['file_path'])
                    segment = TimelineSegment(
                        id=row['id'],
                        camera_id=row['camera_id'],
                        filename=row['filename'],
                        file_path=row['file_path'],
                        start_time=datetime.fromisoformat(row['start_time']),
                        end_time=datetime.fromisoformat(row['end_time']),
                        duration_seconds=row['duration_seconds'],
                        file_size=row['file_size'],
                        exists=file_path.exists()
                    )
                    segments.append(segment)
        
        except Exception as e:
            logger.error(f"Error searching recordings: {e}")
        
        return segments
    
    async def export_time_range(
        self,
        camera_id: int,
        start_time: datetime,
        end_time: datetime,
        output_path: str
    ) -> Optional[str]:
        """
        Export video segments for a time range
        
        Args:
            camera_id: Camera ID
            start_time: Start time
            end_time: End time
            output_path: Output file path
            
        Returns:
            Path to exported file or None
        """
        try:
            # Get segments for the time range
            segments = await self.get_camera_timeline(camera_id, start_time, end_time)
            
            if not segments:
                logger.warning(f"No segments found for export")
                return None
            
            # TODO: Implement video concatenation using ffmpeg
            # For now, return the first segment as a placeholder
            if len(segments) == 1:
                # Single segment, just copy it
                import shutil
                source = Path(segments[0].file_path)
                if source.exists():
                    shutil.copy2(source, output_path)
                    return output_path
            else:
                logger.info(f"Export would concatenate {len(segments)} segments")
                # Would use ffmpeg concat here
                return None
                
        except Exception as e:
            logger.error(f"Error exporting time range: {e}")
            return None
    
    def get_segment_info(self, segment_path: str) -> Optional[Dict]:
        """
        Get information about a video segment file
        
        Args:
            segment_path: Path to segment file
            
        Returns:
            Segment information dictionary
        """
        try:
            path = Path(segment_path)
            if not path.exists():
                return None
            
            # Parse filename for metadata
            # Format: camera_3_20250725_182548_600.avi
            name_parts = path.stem.split('_')
            
            if len(name_parts) >= 5:
                camera_id = int(name_parts[1])
                date_str = name_parts[2]
                time_str = name_parts[3]
                duration = int(name_parts[4])
                
                # Parse datetime
                start_time = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                end_time = start_time + timedelta(seconds=duration)
                
                return {
                    'filename': path.name,
                    'camera_id': camera_id,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'file_size': path.stat().st_size,
                    'exists': True
                }
        
        except Exception as e:
            logger.error(f"Error parsing segment info: {e}")
        
        return None