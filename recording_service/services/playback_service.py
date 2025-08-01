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
        """Get recording availability for calendar display"""
        try:
            async with self.db_service.get_session() as session:
                # Query daily summaries for the month
                query = """
                    SELECT 
                        date,
                        total_duration_seconds,
                        total_size_bytes,
                        coverage_percentage
                    FROM daily_summaries
                    WHERE camera_id = ? 
                    AND strftime('%Y', date) = ?
                    AND strftime('%m', date) = ?
                """
                
                result = await session.execute(
                    text(query), 
                    (camera_id, str(year), str(month).zfill(2))
                )
                rows = result.fetchall()
                
                days = {}
                total_size = 0
                total_duration = 0
                
                for row in rows:
                    day = int(row[0].split('-')[2])
                    days[str(day)] = {
                        "has_recordings": True,
                        "total_duration": row[1],
                        "total_size": row[2],
                        "recording_percentage": row[3]
                    }
                    total_size += row[2]
                    total_duration += row[1]
                
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
        """Get detailed segment list for timeline"""
        try:
            async with self.db_service.get_session() as session:
                # Build query with optional hour filtering
                query = """
                    SELECT 
                        filename,
                        start_time,
                        end_time,
                        duration_seconds,
                        file_size_bytes,
                        file_path
                    FROM video_recordings
                    WHERE camera_id = ?
                    AND date(start_time) = ?
                """
                params = [camera_id, date_str]
                
                if start_hour is not None:
                    query += " AND cast(strftime('%H', start_time) as integer) >= ?"
                    params.append(start_hour)
                
                if end_hour is not None:
                    query += " AND cast(strftime('%H', start_time) as integer) <= ?"
                    params.append(end_hour)
                    
                query += " ORDER BY start_time"
                
                result = await session.execute(text(query), params)
                rows = result.fetchall()
                
                segments = []
                prev_end_time = None
                
                for row in rows:
                    segment = {
                        "filename": row[0],
                        "start_time": row[1],
                        "end_time": row[2],
                        "duration_seconds": row[3],
                        "file_size": row[4],
                        "file_path": row[5],
                        "type": "continuous",
                        "has_gap_before": False,
                        "gap_duration": 0
                    }
                    
                    # Check for gaps
                    if prev_end_time:
                        gap = (datetime.fromisoformat(row[1]) - 
                               datetime.fromisoformat(prev_end_time)).total_seconds()
                        if gap > 60:  # More than 1 minute gap
                            segment["has_gap_before"] = True
                            segment["gap_duration"] = int(gap)
                    
                    segments.append(segment)
                    prev_end_time = row[2]
                
                # Calculate totals
                total_duration = sum(s["duration_seconds"] for s in segments)
                total_size = sum(s["file_size"] for s in segments)
                coverage = (total_duration / 86400) * 100 if segments else 0
                
                return {
                    "camera_id": camera_id,
                    "date": date_str,
                    "segments": segments,
                    "total_segments": len(segments),
                    "total_duration": total_duration,
                    "total_size": total_size,
                    "coverage_percentage": round(coverage, 1)
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
        """Search recordings with filters"""
        try:
            start_date = search_params.get('start_date')
            end_date = search_params.get('end_date')
            start_time = search_params.get('start_time')
            end_time = search_params.get('end_time')
            min_duration = search_params.get('min_duration')
            max_duration = search_params.get('max_duration')
            
            async with self.db_service.get_session() as session:
                # Build search query
                query = """
                    SELECT 
                        filename,
                        date(start_time) as date,
                        start_time,
                        end_time,
                        duration_seconds,
                        file_size_bytes
                    FROM video_recordings
                    WHERE camera_id = ?
                """
                params = [camera_id]
                
                if start_date:
                    query += " AND date(start_time) >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND date(start_time) <= ?"
                    params.append(end_date)
                
                if start_time and end_time:
                    query += " AND (time(start_time) >= ? OR time(start_time) <= ?)"
                    params.extend([start_time, end_time])
                
                if min_duration:
                    query += " AND duration_seconds >= ?"
                    params.append(min_duration)
                
                if max_duration:
                    query += " AND duration_seconds <= ?"
                    params.append(max_duration)
                
                query += " ORDER BY start_time"
                
                result = await session.execute(text(query), params)
                rows = result.fetchall()
                
                segments = []
                total_duration = 0
                total_size = 0
                
                for row in rows:
                    segment = {
                        "filename": row[0],
                        "date": row[1],
                        "start_time": row[2],
                        "end_time": row[3],
                        "duration_seconds": row[4],
                        "file_size": row[5]
                    }
                    segments.append(segment)
                    total_duration += row[4]
                    total_size += row[5]
                
                return {
                    "total_results": len(segments),
                    "total_duration": total_duration,
                    "total_size": total_size,
                    "segments": segments
                }
                
        except Exception as e:
            logger.error(f"Error searching segments: {e}")
            raise HTTPException(status_code=500, detail="Failed to search segments")