"""
Video Playback Service for 24/7 Recording System
Handles video segment retrieval, timeline generation, and playback functionality
"""
import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
from dataclasses import dataclass
import mimetypes

logger = logging.getLogger(__name__)


@dataclass
class TimelineSegment:
    """Represents a video segment in the timeline"""
    id: str
    camera_id: int
    filename: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    file_size: int
    file_path: str
    exists: bool = True
    

@dataclass
class PlaybackTimeRange:
    """Represents a time range for playback requests"""
    start_time: datetime
    end_time: datetime
    camera_id: int
    quality: str = "original"
    

class VideoPlayback:
    """Handles video playback functionality for recorded segments"""
    
    def __init__(self, base_storage_path: str = "recordings"):
        """Initialize video playback service
        
        Args:
            base_storage_path: Base path where recordings are stored
        """
        self.base_path = Path(base_storage_path)
        self.segment_cache: Dict[str, TimelineSegment] = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        
        logger.info(f"Video playback service initialized with storage path: {self.base_path}")
    
    async def get_camera_timeline(
        self, 
        camera_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[TimelineSegment]:
        """Get timeline segments for a camera within a time range
        
        Args:
            camera_id: Camera ID
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of TimelineSegment objects
        """
        camera_dir = self.base_path / f"camera_{camera_id}"
        db_path = camera_dir / "index.db"
        
        if not db_path.exists():
            logger.warning(f"No recording database found for camera {camera_id}")
            return []
        
        segments = []
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Query segments that overlap with the requested time range
            cursor.execute('''
                SELECT filename, start_time, end_time, duration, file_size
                FROM segments 
                WHERE datetime(start_time) <= datetime(?) 
                AND datetime(end_time) >= datetime(?)
                ORDER BY start_time
            ''', (end_time.isoformat(), start_time.isoformat()))
            
            results = cursor.fetchall()
            
            for filename, seg_start, seg_end, duration, file_size in results:
                try:
                    segment_start = datetime.fromisoformat(seg_start)
                    segment_end = datetime.fromisoformat(seg_end)
                    
                    # Build file path
                    date_path = segment_start.strftime("%Y/%m/%d/%H")
                    file_path = camera_dir / date_path / filename
                    
                    # Create timeline segment
                    segment = TimelineSegment(
                        id=f"{camera_id}_{filename}",
                        camera_id=camera_id,
                        filename=filename,
                        start_time=segment_start,
                        end_time=segment_end,
                        duration_seconds=duration or 0,
                        file_size=file_size or 0,
                        file_path=str(file_path),
                        exists=file_path.exists()
                    )
                    
                    segments.append(segment)
                    
                except Exception as e:
                    logger.error(f"Error processing segment {filename}: {e}")
            
            conn.close()
            
            logger.info(f"Retrieved {len(segments)} segments for camera {camera_id} "
                       f"between {start_time} and {end_time}")
            
        except Exception as e:
            logger.error(f"Error retrieving timeline for camera {camera_id}: {e}")
        
        return segments
    
    async def get_segment_by_id(self, segment_id: str) -> Optional[TimelineSegment]:
        """Get a specific segment by ID
        
        Args:
            segment_id: Segment ID (format: camera_id_filename)
            
        Returns:
            TimelineSegment object or None if not found
        """
        # Check cache first
        if segment_id in self.segment_cache:
            return self.segment_cache[segment_id]
        
        try:
            # Parse segment ID
            parts = segment_id.split('_', 2)
            if len(parts) < 3:
                logger.error(f"Invalid segment ID format: {segment_id}")
                return None
            
            camera_id = int(parts[1])
            filename = parts[2]
            
            # Find segment in database
            camera_dir = self.base_path / f"camera_{camera_id}"
            db_path = camera_dir / "index.db"
            
            if not db_path.exists():
                return None
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filename, start_time, end_time, duration, file_size
                FROM segments 
                WHERE filename = ?
            ''', (filename,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                seg_filename, seg_start, seg_end, duration, file_size = result
                segment_start = datetime.fromisoformat(seg_start)
                segment_end = datetime.fromisoformat(seg_end)
                
                # Build file path
                date_path = segment_start.strftime("%Y/%m/%d/%H")
                file_path = camera_dir / date_path / seg_filename
                
                segment = TimelineSegment(
                    id=segment_id,
                    camera_id=camera_id,
                    filename=seg_filename,
                    start_time=segment_start,
                    end_time=segment_end,
                    duration_seconds=duration or 0,
                    file_size=file_size or 0,
                    file_path=str(file_path),
                    exists=file_path.exists()
                )
                
                # Cache the segment
                self.segment_cache[segment_id] = segment
                
                return segment
            
        except Exception as e:
            logger.error(f"Error retrieving segment {segment_id}: {e}")
        
        return None
    
    async def get_continuous_playback_segments(
        self, 
        camera_id: int, 
        start_time: datetime, 
        duration_minutes: int = 60
    ) -> List[TimelineSegment]:
        """Get segments for continuous playback from a start time
        
        Args:
            camera_id: Camera ID
            start_time: Playback start time
            duration_minutes: Duration of playback in minutes
            
        Returns:
            List of consecutive TimelineSegment objects
        """
        end_time = start_time + timedelta(minutes=duration_minutes)
        segments = await self.get_camera_timeline(camera_id, start_time, end_time)
        
        # Sort by start time to ensure proper order
        segments.sort(key=lambda s: s.start_time)
        
        # Filter segments that actually contain data in our time range
        filtered_segments = []
        
        for segment in segments:
            # Check if segment overlaps with our requested time range
            if (segment.start_time <= end_time and segment.end_time >= start_time):
                filtered_segments.append(segment)
        
        logger.info(f"Found {len(filtered_segments)} segments for continuous playback "
                   f"from {start_time} for {duration_minutes} minutes")
        
        return filtered_segments
    
    async def stream_segment_file(
        self, 
        segment: TimelineSegment, 
        range_header: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """Stream a video segment file with optional range support
        
        Args:
            segment: TimelineSegment to stream
            range_header: HTTP Range header value for partial content requests
            
        Yields:
            Bytes of video data
        """
        file_path = Path(segment.file_path)
        
        if not file_path.exists():
            logger.error(f"Video file not found: {file_path}")
            return
        
        file_size = file_path.stat().st_size
        
        # Parse range header
        start = 0
        end = file_size - 1
        
        if range_header:
            try:
                # Parse "bytes=start-end" format
                range_match = range_header.replace('bytes=', '').split('-')
                if len(range_match) == 2:
                    if range_match[0]:
                        start = int(range_match[0])
                    if range_match[1]:
                        end = int(range_match[1])
                    
                    # Ensure end doesn't exceed file size
                    end = min(end, file_size - 1)
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid range header: {range_header}, error: {e}")
                start = 0
                end = file_size - 1
        
        chunk_size = 8192  # 8KB chunks
        bytes_to_read = end - start + 1
        
        try:
            with open(file_path, 'rb') as f:
                f.seek(start)
                bytes_read = 0
                
                while bytes_read < bytes_to_read:
                    remaining = bytes_to_read - bytes_read
                    current_chunk_size = min(chunk_size, remaining)
                    
                    chunk = f.read(current_chunk_size)
                    if not chunk:
                        break
                    
                    bytes_read += len(chunk)
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error streaming segment file {file_path}: {e}")
    
    def get_segment_content_type(self, segment: TimelineSegment) -> str:
        """Get the content type for a video segment
        
        Args:
            segment: TimelineSegment object
            
        Returns:
            MIME type string
        """
        # Determine content type from filename
        mime_type, _ = mimetypes.guess_type(segment.filename)
        
        if mime_type:
            return mime_type
        
        # Default content types based on file extension
        extension = Path(segment.filename).suffix.lower()
        
        content_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm'
        }
        
        return content_types.get(extension, 'video/mp4')
    
    async def get_playback_info(
        self, 
        camera_id: int, 
        target_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get playback information for a specific time
        
        Args:
            camera_id: Camera ID
            target_time: Target time to find playback info for
            
        Returns:
            Dictionary with playback information or None
        """
        # Find segment containing the target time
        segments = await self.get_camera_timeline(
            camera_id, 
            target_time - timedelta(minutes=5),  # Search 5 minutes before
            target_time + timedelta(minutes=5)   # Search 5 minutes after
        )
        
        target_segment = None
        for segment in segments:
            if segment.start_time <= target_time <= segment.end_time:
                target_segment = segment
                break
        
        if not target_segment:
            return None
        
        # Calculate offset within segment
        offset_seconds = (target_time - target_segment.start_time).total_seconds()
        
        return {
            "segment_id": target_segment.id,
            "segment_start": target_segment.start_time.isoformat(),
            "segment_end": target_segment.end_time.isoformat(),
            "target_time": target_time.isoformat(),
            "offset_seconds": offset_seconds,
            "file_exists": target_segment.exists,
            "file_size": target_segment.file_size,
            "duration_seconds": target_segment.duration_seconds
        }
    
    async def get_available_time_ranges(
        self, 
        camera_id: int, 
        date: datetime
    ) -> List[Dict[str, Any]]:
        """Get available recording time ranges for a specific date
        
        Args:
            camera_id: Camera ID
            date: Date to check (time component ignored)
            
        Returns:
            List of time range dictionaries
        """
        # Get segments for the entire day
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        segments = await self.get_camera_timeline(camera_id, day_start, day_end)
        
        if not segments:
            return []
        
        # Group consecutive segments into ranges
        ranges = []
        current_range_start = None
        current_range_end = None
        
        segments.sort(key=lambda s: s.start_time)
        
        for segment in segments:
            if not segment.exists:
                continue
            
            if current_range_start is None:
                # Start new range
                current_range_start = segment.start_time
                current_range_end = segment.end_time
            else:
                # Check if this segment is consecutive to the previous one
                gap = (segment.start_time - current_range_end).total_seconds()
                
                if gap <= 60:  # Allow up to 1 minute gap
                    # Extend current range
                    current_range_end = segment.end_time
                else:
                    # Save current range and start new one
                    ranges.append({
                        "start_time": current_range_start.isoformat(),
                        "end_time": current_range_end.isoformat(),
                        "duration_seconds": int((current_range_end - current_range_start).total_seconds())
                    })
                    
                    current_range_start = segment.start_time
                    current_range_end = segment.end_time
        
        # Add the last range
        if current_range_start and current_range_end:
            ranges.append({
                "start_time": current_range_start.isoformat(),
                "end_time": current_range_end.isoformat(),
                "duration_seconds": int((current_range_end - current_range_start).total_seconds())
            })
        
        logger.info(f"Found {len(ranges)} recording time ranges for camera {camera_id} on {date.date()}")
        
        return ranges
    
    async def search_recordings(
        self, 
        camera_id: int, 
        start_date: datetime, 
        end_date: datetime,
        min_duration_minutes: int = 1
    ) -> List[Dict[str, Any]]:
        """Search for recordings within a date range
        
        Args:
            camera_id: Camera ID
            start_date: Start date for search
            end_date: End date for search
            min_duration_minutes: Minimum duration of recordings to include
            
        Returns:
            List of recording information dictionaries
        """
        segments = await self.get_camera_timeline(camera_id, start_date, end_date)
        
        # Filter by minimum duration and existing files
        valid_segments = [
            s for s in segments 
            if s.exists and s.duration_seconds >= (min_duration_minutes * 60)
        ]
        
        # Convert to search results
        results = []
        for segment in valid_segments:
            results.append({
                "segment_id": segment.id,
                "filename": segment.filename,
                "start_time": segment.start_time.isoformat(),
                "end_time": segment.end_time.isoformat(),
                "duration_seconds": segment.duration_seconds,
                "duration_formatted": self._format_duration(segment.duration_seconds),
                "file_size": segment.file_size,
                "file_size_formatted": self._format_bytes(segment.file_size)
            })
        
        # Sort by start time (most recent first)
        results.sort(key=lambda r: r["start_time"], reverse=True)
        
        logger.info(f"Found {len(results)} recordings for camera {camera_id} "
                   f"between {start_date.date()} and {end_date.date()}")
        
        return results
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable string
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string (e.g., "2h 30m 15s")
        """
        if seconds < 60:
            return f"{seconds}s"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes < 60:
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds}s"
            return f"{minutes}m"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        parts = [f"{hours}h"]
        if remaining_minutes > 0:
            parts.append(f"{remaining_minutes}m")
        if remaining_seconds > 0:
            parts.append(f"{remaining_seconds}s")
        
        return " ".join(parts)
    
    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes as human readable string
        
        Args:
            bytes_size: Size in bytes
            
        Returns:
            Formatted string (e.g., "1.5 GB")
        """
        if bytes_size == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while bytes_size >= 1024 and i < len(units) - 1:
            bytes_size /= 1024
            i += 1
        
        return f"{bytes_size:.1f} {units[i]}"
    
    async def export_segment(
        self, 
        segment_id: str, 
        export_path: str
    ) -> bool:
        """Export a video segment to a specified path
        
        Args:
            segment_id: Segment ID to export
            export_path: Destination path for export
            
        Returns:
            True if export successful, False otherwise
        """
        segment = await self.get_segment_by_id(segment_id)
        
        if not segment or not segment.exists:
            logger.error(f"Segment not found or file missing: {segment_id}")
            return False
        
        try:
            import shutil
            
            source_path = Path(segment.file_path)
            dest_path = Path(export_path)
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            
            logger.info(f"Exported segment {segment_id} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting segment {segment_id}: {e}")
            return False
    
    def clear_cache(self):
        """Clear the segment cache"""
        self.segment_cache.clear()
        logger.info("Segment cache cleared")