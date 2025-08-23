"""
Playback Service - Handles video playback API endpoints
Provides calendar data, timeline segments, and video streaming
"""
import os
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import logging
from sqlalchemy import text
from database.models import VideoRecording, DailySummary

logger = logging.getLogger(__name__)

class PlaybackService:
    """Handles video playback and timeline data"""
    
    def __init__(self, db_service, recordings_path: str):
        self.db_service = db_service
        self.recordings_path = Path(recordings_path)
        logger.info("Playback Service initialized")
    
    async def get_calendar_data(self, camera_id: str, year: int, month: int) -> Dict:
        """Get recording availability for calendar display - File-based approach"""
        try:
            # Scan filesystem for recordings instead of using database
            # Handle both formats: direct camera_id and prefixed camera_camera_id
            if camera_id.startswith('camera_'):
                camera_path = self.recordings_path / camera_id
            else:
                camera_path = self.recordings_path / f"camera_{camera_id}"
                
            if not camera_path.exists():
                logger.warning(f"No recordings directory for camera {camera_id} at path {camera_path}")
                return {"days": {}, "total_size": 0, "total_duration": 0}
                
            logger.info(f"Found camera directory at {camera_path}")
            
            # Build month path
            month_path = camera_path / str(year) / str(month).zfill(2)
            if not month_path.exists():
                logger.info(f"No recordings for {camera_id} in {year}-{month:02d} at path {month_path}")
                return {"days": {}, "total_size": 0, "total_duration": 0}
                
            logger.info(f"Found month directory at {month_path}")
            
            days = {}
            total_size = 0
            total_duration = 0
            
            # Scan all days in the month
            for day_path in month_path.glob("*"):
                if not day_path.is_dir():
                    continue
                    
                day_number = int(day_path.name)
                day_size = 0
                day_duration = 0
                segment_count = 0
                
                # Scan all hours in the day
                for hour_path in day_path.glob("*"):
                    if not hour_path.is_dir():
                        continue
                    
                    # Count video files in this hour
                    # Look for both .avi and .mp4 files
                video_files = list(hour_path.glob("*.avi")) + list(hour_path.glob("*.mp4"))
                for video_file in video_files:
                        if video_file.is_file():
                            segment_count += 1
                            day_size += video_file.stat().st_size
                            # Each segment is 10 minutes (600 seconds)
                            day_duration += 600
                
                if segment_count > 0:
                    days[day_number] = {
                        "has_recordings": True,
                        "segment_count": segment_count,
                        "total_size": day_size,
                        "duration_seconds": day_duration,
                        "coverage_percentage": min(100.0, (day_duration / 86400.0) * 100.0)
                    }
                    total_size += day_size
                    total_duration += day_duration
            
            return {
                "year": year,
                "month": month,
                "days": days,
                "total_size": total_size,
                "total_duration": total_duration
            }
                
        except Exception as e:
            logger.error(f"Error getting calendar data: {e}")
            raise HTTPException(status_code=500, detail="Failed to get calendar data")
    
    async def get_timeline_segments(
        self, 
        camera_id: str, 
        date_str: str,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None
    ) -> Dict:
        """Get detailed segment list for timeline - File-based approach"""
        try:
            # Parse date string (YYYY-MM-DD)
            year, month, day = date_str.split('-')
            
            # Build path to recordings for this date
            # Handle both formats: direct camera_id and prefixed camera_camera_id
            if camera_id.startswith('camera_'):
                date_path = self.recordings_path / camera_id / year / month / day
            else:
                date_path = self.recordings_path / f"camera_{camera_id}" / year / month / day
            
            if not date_path.exists():
                logger.info(f"No recordings for {camera_id} on {date_str} at {date_path}")
                return {
                    "segments": [],
                    "total_duration": 0,
                    "total_size": 0,
                    "coverage_percentage": 0.0,
                    "date": date_str
                }
            
            segments = []
            total_size = 0
            total_duration = 0
            
            # Parse filename pattern to extract metadata and sort chronologically
            video_files_info = []
            for hour_path in date_path.glob("*"):
                if not hour_path.is_dir():
                    continue
                    
                hour = int(hour_path.name)
                # Apply hour filtering if specified
                if start_hour is not None and hour < start_hour:
                    continue
                if end_hour is not None and hour > end_hour:
                    continue
                
                # Look for both .avi and .mp4 files
                hour_video_files = list(hour_path.glob("*.avi")) + list(hour_path.glob("*.mp4"))
                for video_file in hour_video_files:
                    if video_file.is_file():
                        # Parse filename: supports both old (with duration) and new (without duration) formats
                        # Old: camera_camera_946701d3_20250802_022919_600.avi
                        # New: camera_e4036ff5-fd9a-431a-8583-3ec721f53f1a_20250803_001742.mp4
                        try:
                            parts = video_file.stem.split('_')
                            
                            # Check if this is new format (without duration) or old format (with duration)
                            if len(parts) >= 3:
                                if len(parts) >= 4 and parts[-1].isdigit() and len(parts[-1]) == 3:
                                    # Old format with duration suffix
                                    date_part = parts[-3]  # 20250802
                                    time_part = parts[-2]  # 022919
                                    duration = int(parts[-1])  # 600
                                else:
                                    # New format without duration suffix
                                    date_part = parts[-2]  # 20250803
                                    time_part = parts[-1]  # 001742
                                    duration = 600  # Default 10-minute segment duration
                                
                                # Parse start time
                                start_time = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                                end_time = start_time + timedelta(seconds=duration)
                                
                                video_files_info.append({
                                    "file": video_file,
                                    "start_time": start_time,
                                    "end_time": end_time,
                                    "duration": duration
                                })
                        except Exception as e:
                            logger.warning(f"Could not parse filename {video_file.name}: {e}")
            
            # Sort by start time
            video_files_info.sort(key=lambda x: x["start_time"])
            
            # Build segments
            prev_end_time = None
            for video_info in video_files_info:
                file_size = video_info["file"].stat().st_size
                
                # Check for gaps between segments
                has_gap_before = False
                gap_duration = 0
                if prev_end_time and video_info["start_time"] > prev_end_time:
                    gap_duration = (video_info["start_time"] - prev_end_time).total_seconds()
                    has_gap_before = gap_duration > 30  # Gap > 30 seconds
                
                segment = {
                        "filename": video_info["file"].name,
                        "start_time": video_info["start_time"].isoformat(),
                        "end_time": video_info["end_time"].isoformat(),
                        "duration_seconds": video_info["duration"],
                        "file_size": file_size,
                        "file_path": str(video_info["file"]),
                        "type": "continuous",
                        "has_gap_before": has_gap_before,
                        "gap_duration": gap_duration
                    }
                    
                segments.append(segment)
                total_size += file_size
                total_duration += video_info["duration"]
                prev_end_time = video_info["end_time"]
            
            # Calculate coverage percentage (total duration vs 24 hours)
            coverage_percentage = min(100.0, (total_duration / 86400.0) * 100.0) if total_duration > 0 else 0.0
            
            return {
                "segments": segments,
                "total_duration": total_duration,
                "total_size": total_size,
                "coverage_percentage": coverage_percentage,
                "date": date_str,
                "segment_count": len(segments)
            }
                
        except Exception as e:
            logger.error(f"Error getting timeline segments: {e}")
            raise HTTPException(status_code=500, detail="Failed to get timeline segments")
    
    async def stream_segment(
        self, 
        segment_filename: str, 
        range_header: Optional[str] = None
    ) -> StreamingResponse:
        """Stream video segment with HTTP 206 Partial Content support"""
        
        # Find segment in database
        try:
            async with self.db_service.get_session() as session:
                result = await session.execute(
                    text("SELECT file_path FROM video_recordings WHERE filename = ?"),
                    (segment_filename,)
                )
                row = result.fetchone()
                
                if not row:
                    raise HTTPException(404, "Video segment not found")
                
                file_path = Path(row[0])
                
        except Exception as e:
            logger.error(f"Database error finding segment: {e}")
            raise HTTPException(500, "Database error")
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(404, "Video file not found on disk")
        
        file_size = file_path.stat().st_size
        
        # Parse range header
        start = 0
        end = file_size - 1
        
        if range_header:
            try:
                range_str = range_header.replace("bytes=", "")
                range_parts = range_str.split("-")
                start = int(range_parts[0]) if range_parts[0] else 0
                end = int(range_parts[1]) if range_parts[1] else file_size - 1
            except:
                raise HTTPException(400, "Invalid range header")
        
        # Validate range
        if start >= file_size or end >= file_size or start > end:
            raise HTTPException(416, "Requested range not satisfiable")
        
        # Create response headers
        headers = {
            "Content-Type": "video/mp4",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Range": f"bytes {start}-{end}/{file_size}",
        }
        
        async def stream_file():
            async with aiofiles.open(file_path, 'rb') as file:
                await file.seek(start)
                chunk_size = 1024 * 1024  # 1MB chunks
                current = start
                
                while current <= end:
                    remaining = end - current + 1
                    size = min(chunk_size, remaining)
                    data = await file.read(size)
                    if not data:
                        break
                    current += len(data)
                    yield data
        
        return StreamingResponse(
            stream_file(),
            status_code=206 if range_header else 200,
            headers=headers,
            media_type="video/mp4"
        )
    
    async def get_recording_details(self, camera_id: str, date_str: str) -> Dict:
        """Get detailed recording statistics for a date"""
        try:
            async with self.db_service.get_session() as session:
                # Get segments for the date
                result = await session.execute(
                    text("""
                    SELECT 
                        COUNT(*) as segment_count,
                        SUM(duration_seconds) as total_duration,
                        SUM(file_size_bytes) as total_size,
                        AVG(file_size_bytes) as avg_segment_size,
                        video_codec,
                        video_width,
                        video_height,
                        video_fps
                    FROM video_recordings
                    WHERE camera_id = ? AND date(start_time) = ?
                    """),
                    (camera_id, date_str)
                )
                
                stats = result.fetchone()
                
                if not stats or stats[0] == 0:
                    return {
                        "camera_id": camera_id,
                        "date": date_str,
                        "stats": {
                            "total_duration": 0,
                            "total_size": 0,
                            "total_size_formatted": "0 B",
                            "segment_count": 0,
                            "recording_percentage": 0.0
                        }
                    }
                
                # Get hourly breakdown
                hourly_result = await session.execute(
                    text("""
                    SELECT 
                        strftime('%H', start_time) as hour,
                        COUNT(*) as segments,
                        SUM(duration_seconds) as duration,
                        SUM(file_size_bytes) as size
                    FROM video_recordings
                    WHERE camera_id = ? AND date(start_time) = ?
                    GROUP BY strftime('%H', start_time)
                    ORDER BY hour
                    """),
                    (camera_id, date_str)
                )
                
                hourly_breakdown = {}
                for row in hourly_result.fetchall():
                    hourly_breakdown[str(int(row[0]))] = {
                        "segments": row[1],
                        "duration": row[2],
                        "size": row[3]
                    }
                
                # Calculate statistics
                total_duration = stats[1] or 0
                total_size = stats[2] or 0
                recording_percentage = (total_duration / 86400) * 100 if total_duration else 0
                
                # Format file size
                def format_bytes(bytes_val):
                    if bytes_val < 1024:
                        return f"{bytes_val} B"
                    elif bytes_val < 1024**2:
                        return f"{bytes_val/1024:.1f} KB"
                    elif bytes_val < 1024**3:
                        return f"{bytes_val/1024**2:.1f} MB"
                    else:
                        return f"{bytes_val/1024**3:.1f} GB"
                
                return {
                    "camera_id": camera_id,
                    "date": date_str,
                    "stats": {
                        "total_duration": total_duration,
                        "total_size": total_size,
                        "total_size_formatted": format_bytes(total_size),
                        "segment_count": stats[0],
                        "average_segment_size": stats[3] or 0,
                        "recording_percentage": round(recording_percentage, 1),
                        "gaps_count": 0,  # TODO: Calculate gaps
                        "gaps_duration": 0,
                        "video_codec": stats[4] or "unknown",
                        "video_quality": f"{stats[5] or 0}x{stats[6] or 0} @ {stats[7] or 0}fps",
                        "average_bitrate": 0,  # TODO: Calculate bitrate
                        "compression_ratio": "10:1"  # TODO: Calculate from data
                    },
                    "hourly_breakdown": hourly_breakdown
                }
                
        except Exception as e:
            logger.error(f"Error getting recording details: {e}")
            raise HTTPException(status_code=500, detail="Failed to get recording details")
    
    async def search_segments(self, camera_id: str, search_params: dict) -> Dict:
        """Search recordings with filters - File-based approach"""
        try:
            logger.info(f"Searching segments for camera {camera_id} with params: {search_params}")
            
            # Get filter parameters
            start_date = search_params.get('start_date')
            end_date = search_params.get('end_date') 
            start_time = search_params.get('start_time')
            end_time = search_params.get('end_time')
            min_duration = search_params.get('min_duration', 0)
            max_duration = search_params.get('max_duration', 99999)
            
            # Parse dates if provided
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Scan filesystem for matching segments
            camera_path = self.recordings_path / f"camera_{camera_id}"
            if not camera_path.exists():
                logger.warning(f"No recordings directory for camera {camera_id}")
                return {
                    "total_results": 0,
                    "total_duration": 0,
                    "total_size": 0,
                    "segments": []
                }
            
            segments = []
            total_duration = 0
            total_size = 0
            
            # Walk through the directory structure
            for year_dir in camera_path.iterdir():
                if not year_dir.is_dir():
                    continue
                    
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                        
                    for day_dir in month_dir.iterdir():
                        if not day_dir.is_dir():
                            continue
                            
                        # Check if this date is within our search range
                        try:
                            file_date = datetime.strptime(f"{year_dir.name}-{month_dir.name}-{day_dir.name}", '%Y-%m-%d')
                            if start_dt and file_date < start_dt:
                                continue
                            if end_dt and file_date > end_dt:
                                continue
                        except ValueError:
                            continue
                            
                        for hour_dir in day_dir.iterdir():
                            if not hour_dir.is_dir():
                                continue
                                
                            # Look for both .avi and .mp4 files
                            video_files = list(hour_dir.glob("*.avi")) + list(hour_dir.glob("*.mp4"))
                            for video_file in video_files:
                                if not video_file.is_file():
                                    continue
                                    
                                try:
                                    # Parse filename: supports both old and new formats
                                    parts = video_file.stem.split('_')
                                    if len(parts) >= 3:
                                        if len(parts) >= 4 and parts[-1].isdigit() and len(parts[-1]) == 3:
                                            # Old format with duration suffix
                                            date_part = parts[-3]  # 20250802
                                            time_part = parts[-2]  # 022919
                                            duration = int(parts[-1])  # 600
                                        else:
                                            # New format without duration suffix
                                            date_part = parts[-2]  # 20250803
                                            time_part = parts[-1]  # 001742
                                            duration = 600  # Default 10-minute segment duration
                                        
                                        # Check duration filter
                                        if duration < min_duration or duration > max_duration:
                                            continue
                                        
                                        # Parse start time
                                        start_datetime = datetime.strptime(f"{date_part}_{time_part}", '%Y%m%d_%H%M%S')
                                        end_datetime = start_datetime + timedelta(seconds=duration)
                                        
                                        # Check time filter
                                        if start_time:
                                            start_time_obj = datetime.strptime(start_time, '%H:%M:%S').time()
                                            if start_datetime.time() < start_time_obj:
                                                continue
                                        
                                        if end_time:
                                            end_time_obj = datetime.strptime(end_time, '%H:%M:%S').time()
                                            if start_datetime.time() > end_time_obj:
                                                continue
                                        
                                        file_size = video_file.stat().st_size
                                        
                                        segment = {
                                            "filename": video_file.name,
                                            "date": start_datetime.strftime('%Y-%m-%d'),
                                            "start_time": start_datetime.isoformat(),
                                            "end_time": end_datetime.isoformat(),
                                            "duration_seconds": duration,
                                            "file_size": file_size,
                                            "camera_id": camera_id
                                        }
                                        
                                        segments.append(segment)
                                        total_duration += duration
                                        total_size += file_size
                                        
                                except (ValueError, IndexError) as e:
                                    logger.warning(f"Failed to parse filename {video_file.name}: {e}")
                                    continue
            
            # Sort by start time
            segments.sort(key=lambda x: x['start_time'])
            
            logger.info(f"Found {len(segments)} matching segments")
            
            return {
                "total_results": len(segments),
                "total_duration": total_duration,
                "total_size": total_size,
                "segments": segments
            }
                
        except Exception as e:
            logger.error(f"Error searching segments: {e}")
            raise HTTPException(status_code=500, detail="Failed to search segments")
    
    async def stream_segment_file_based(
        self, 
        segment_filename: str, 
        range_header: Optional[str] = None
    ) -> StreamingResponse:
        """Stream video segment using file-system approach (bypasses database)"""
        
        try:
            # Extract camera_id from filename pattern
            # Format: camera_camera_946701d3_20250802_025038_600.avi
            if not segment_filename.startswith("camera_"):
                raise HTTPException(404, "Invalid segment filename format")
            
            # Find the file by scanning all camera directories
            file_path = None
            for camera_dir in self.recordings_path.iterdir():
                if camera_dir.is_dir() and camera_dir.name.startswith("camera_"):
                    # Search through the directory tree
                    for year_dir in camera_dir.iterdir():
                        if year_dir.is_dir():
                            for month_dir in year_dir.iterdir():
                                if month_dir.is_dir():
                                    for day_dir in month_dir.iterdir():
                                        if day_dir.is_dir():
                                            for hour_dir in day_dir.iterdir():
                                                if hour_dir.is_dir():
                                                    potential_file = hour_dir / segment_filename
                                                    if potential_file.exists():
                                                        file_path = potential_file
                                                        break
                                                if file_path:
                                                    break
                                            if file_path:
                                                break
                                        if file_path:
                                            break
                                if file_path:
                                    break
                        if file_path:
                            break
            
            if not file_path or not file_path.exists():
                logger.warning(f"Video file not found: {segment_filename}")
                raise HTTPException(404, "Video file not found")
            
            file_size = file_path.stat().st_size
            logger.info(f"Streaming file: {file_path} (size: {file_size} bytes)")
            
            # Handle range requests for video seeking
            start = 0
            end = file_size - 1
            status_code = 200
            
            if range_header:
                # Parse Range header (e.g., "bytes=0-1023")
                try:
                    range_match = range_header.replace('bytes=', '').split('-')
                    if len(range_match) == 2:
                        if range_match[0]:
                            start = int(range_match[0])
                        if range_match[1]:
                            end = int(range_match[1])
                        status_code = 206  # Partial Content
                except (ValueError, IndexError):
                    # Invalid range, serve full file
                    pass
            
            # Ensure valid range
            start = max(0, start)
            end = min(file_size - 1, end)
            content_length = end - start + 1
            
            def file_generator():
                """Generator to stream file chunks"""
                try:
                    with open(file_path, 'rb') as video_file:
                        video_file.seek(start)
                        remaining = content_length
                        
                        while remaining > 0:
                            chunk_size = min(8192, remaining)  # 8KB chunks
                            chunk = video_file.read(chunk_size)
                            if not chunk:
                                break
                            remaining -= len(chunk)
                            yield chunk
                            
                except Exception as e:
                    logger.error(f"Error streaming file: {e}")
                    yield b""  # End stream on error
            
            # Prepare headers with correct content type and CORS
            content_type = 'video/mp4' if file_path.suffix.lower() == '.mp4' else 'video/avi'
            headers = {
                'Content-Length': str(content_length),
                'Accept-Ranges': 'bytes',
                'Content-Type': content_type,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                'Access-Control-Allow-Headers': 'Range, Content-Type'
            }
            
            if status_code == 206:
                headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            
            logger.info(f"Streaming {segment_filename}: bytes {start}-{end}/{file_size} (status: {status_code})")
            
            return StreamingResponse(
                file_generator(),
                status_code=status_code,
                headers=headers
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error streaming video segment: {e}")
            raise HTTPException(status_code=500, detail="Failed to stream video")