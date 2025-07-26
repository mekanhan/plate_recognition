"""
Playback API endpoints for 24/7 recording system
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_database
from app.core.playback.video_playback import VideoPlayback, TimelineSegment, PlaybackTimeRange
from app.core.storage.storage_manager import StorageManager, StorageConfig

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/playback", tags=["playback"])

# Initialize services
video_playback = VideoPlayback()
storage_manager = StorageManager()


# Pydantic models
class TimelineResponse(BaseModel):
    """Response model for timeline requests"""
    camera_id: int
    start_time: str
    end_time: str
    segments: List[Dict[str, Any]]
    total_segments: int
    total_duration_seconds: int


class PlaybackInfoResponse(BaseModel):
    """Response model for playback info"""
    segment_id: Optional[str]
    segment_start: Optional[str]
    segment_end: Optional[str]
    target_time: str
    offset_seconds: Optional[float]
    file_exists: Optional[bool]
    available: bool


class RecordingSearchResponse(BaseModel):
    """Response model for recording search"""
    camera_id: int
    recordings: List[Dict[str, Any]]
    total_results: int
    search_start: str
    search_end: str


class StorageReportResponse(BaseModel):
    """Response model for storage reports"""
    system_stats: Dict[str, Any]
    disk_usage: Dict[str, Any]
    camera_stats: Dict[str, Any]
    config: Dict[str, Any]
    generated_at: str


@router.get("/cameras/{camera_id}/timeline", response_model=TimelineResponse)
async def get_camera_timeline(
    camera_id: int,
    start_time: datetime = Query(..., description="Start time for timeline (ISO format)"),
    end_time: datetime = Query(..., description="End time for timeline (ISO format)"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get video timeline for a camera within a time range
    
    Args:
        camera_id: ID of the camera
        start_time: Start time for the timeline
        end_time: End time for the timeline
        db: Database session
        
    Returns:
        Timeline with video segments
    """
    try:
        # Validate time range
        if end_time <= start_time:
            raise HTTPException(
                status_code=400, 
                detail="End time must be after start time"
            )
        
        # Limit time range to prevent excessive queries
        max_range_hours = 24
        if (end_time - start_time).total_seconds() > (max_range_hours * 3600):
            raise HTTPException(
                status_code=400,
                detail=f"Time range cannot exceed {max_range_hours} hours"
            )
        
        # Get timeline segments
        segments = await video_playback.get_camera_timeline(camera_id, start_time, end_time)
        
        # Convert segments to response format
        segment_data = []
        total_duration = 0
        
        for segment in segments:
            segment_info = {
                "id": segment.id,
                "filename": segment.filename,
                "start_time": segment.start_time.isoformat(),
                "end_time": segment.end_time.isoformat(),
                "duration_seconds": segment.duration_seconds,
                "file_size": segment.file_size,
                "exists": segment.exists,
                "stream_url": f"/api/v1/playback/segments/{segment.id}/stream"
            }
            segment_data.append(segment_info)
            total_duration += segment.duration_seconds
        
        return TimelineResponse(
            camera_id=camera_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            segments=segment_data,
            total_segments=len(segments),
            total_duration_seconds=total_duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeline for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cameras/{camera_id}/ranges")
async def get_available_ranges(
    camera_id: int,
    date: datetime = Query(..., description="Date to check for available recordings"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get available recording time ranges for a specific date
    
    Args:
        camera_id: ID of the camera
        date: Date to check (time component ignored)
        db: Database session
        
    Returns:
        List of available time ranges
    """
    try:
        ranges = await video_playback.get_available_time_ranges(camera_id, date)
        
        return {
            "camera_id": camera_id,
            "date": date.date().isoformat(),
            "ranges": ranges,
            "total_ranges": len(ranges)
        }
        
    except Exception as e:
        logger.error(f"Error getting available ranges for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cameras/{camera_id}/info")
async def get_playback_info(
    camera_id: int,
    target_time: datetime = Query(..., description="Target time to get playback info for"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get playback information for a specific time
    
    Args:
        camera_id: ID of the camera
        target_time: Target time to find playback info for
        db: Database session
        
    Returns:
        Playback information including segment details
    """
    try:
        playback_info = await video_playback.get_playback_info(camera_id, target_time)
        
        if not playback_info:
            return PlaybackInfoResponse(
                segment_id=None,
                segment_start=None,
                segment_end=None,
                target_time=target_time.isoformat(),
                offset_seconds=None,
                file_exists=None,
                available=False
            )
        
        return PlaybackInfoResponse(
            segment_id=playback_info["segment_id"],
            segment_start=playback_info["segment_start"],
            segment_end=playback_info["segment_end"],
            target_time=target_time.isoformat(),
            offset_seconds=playback_info["offset_seconds"],
            file_exists=playback_info["file_exists"],
            available=True
        )
        
    except Exception as e:
        logger.error(f"Error getting playback info for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/segments/{segment_id}/stream")
async def stream_segment(
    segment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_database)
):
    """
    Stream a video segment with range request support
    
    Args:
        segment_id: ID of the segment to stream
        request: HTTP request object for range headers
        db: Database session
        
    Returns:
        Streaming video response
    """
    try:
        # Get segment information
        segment = await video_playback.get_segment_by_id(segment_id)
        
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")
        
        if not segment.exists:
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Get range header
        range_header = request.headers.get('range')
        
        # Determine content type
        content_type = video_playback.get_segment_content_type(segment)
        
        # Set up response headers
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
        
        # Handle range requests
        if range_header:
            try:
                # Parse range header
                range_match = range_header.replace('bytes=', '').split('-')
                start = int(range_match[0]) if range_match[0] else 0
                end = int(range_match[1]) if range_match[1] else segment.file_size - 1
                
                # Ensure valid range
                end = min(end, segment.file_size - 1)
                content_length = end - start + 1
                
                headers.update({
                    "Content-Length": str(content_length),
                    "Content-Range": f"bytes {start}-{end}/{segment.file_size}"
                })
                
                # Stream with range
                return StreamingResponse(
                    video_playback.stream_segment_file(segment, range_header),
                    status_code=206,  # Partial Content
                    headers=headers
                )
                
            except (ValueError, IndexError):
                # Invalid range header, fall back to full content
                pass
        
        # Stream full content
        headers["Content-Length"] = str(segment.file_size)
        
        return StreamingResponse(
            video_playback.stream_segment_file(segment),
            status_code=200,
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/segments/{segment_id}/info")
async def get_segment_info(
    segment_id: str,
    db: AsyncSession = Depends(get_database)
):
    """
    Get detailed information about a video segment
    
    Args:
        segment_id: ID of the segment
        db: Database session
        
    Returns:
        Detailed segment information
    """
    try:
        segment = await video_playback.get_segment_by_id(segment_id)
        
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")
        
        return {
            "id": segment.id,
            "camera_id": segment.camera_id,
            "filename": segment.filename,
            "start_time": segment.start_time.isoformat(),
            "end_time": segment.end_time.isoformat(),
            "duration_seconds": segment.duration_seconds,
            "file_size": segment.file_size,
            "file_path": segment.file_path,
            "exists": segment.exists,
            "content_type": video_playback.get_segment_content_type(segment),
            "stream_url": f"/api/v1/playback/segments/{segment_id}/stream"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting segment info for {segment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cameras/{camera_id}/search", response_model=RecordingSearchResponse)
async def search_recordings(
    camera_id: int,
    start_date: datetime = Query(..., description="Start date for search"),
    end_date: datetime = Query(..., description="End date for search"),
    min_duration_minutes: int = Query(1, description="Minimum duration in minutes"),
    db: AsyncSession = Depends(get_database)
):
    """
    Search for recordings within a date range
    
    Args:
        camera_id: ID of the camera
        start_date: Start date for search
        end_date: End date for search
        min_duration_minutes: Minimum duration of recordings to include
        db: Database session
        
    Returns:
        List of matching recordings
    """
    try:
        # Validate date range
        if end_date <= start_date:
            raise HTTPException(
                status_code=400, 
                detail="End date must be after start date"
            )
        
        # Limit search range
        max_range_days = 90
        if (end_date - start_date).days > max_range_days:
            raise HTTPException(
                status_code=400,
                detail=f"Search range cannot exceed {max_range_days} days"
            )
        
        # Search recordings
        recordings = await video_playback.search_recordings(
            camera_id, start_date, end_date, min_duration_minutes
        )
        
        # Add stream URLs to recordings
        for recording in recordings:
            recording["stream_url"] = f"/api/v1/playback/segments/{recording['segment_id']}/stream"
        
        return RecordingSearchResponse(
            camera_id=camera_id,
            recordings=recordings,
            total_results=len(recordings),
            search_start=start_date.isoformat(),
            search_end=end_date.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching recordings for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cameras/{camera_id}/continuous")
async def get_continuous_playback(
    camera_id: int,
    start_time: datetime = Query(..., description="Playback start time"),
    duration_minutes: int = Query(60, description="Duration in minutes"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get segments for continuous playback from a start time
    
    Args:
        camera_id: ID of the camera
        start_time: Playback start time
        duration_minutes: Duration of playback in minutes
        db: Database session
        
    Returns:
        List of consecutive segments for continuous playback
    """
    try:
        # Limit duration to prevent excessive resource usage
        max_duration = 720  # 12 hours
        if duration_minutes > max_duration:
            raise HTTPException(
                status_code=400,
                detail=f"Duration cannot exceed {max_duration} minutes"
            )
        
        # Get continuous playback segments
        segments = await video_playback.get_continuous_playback_segments(
            camera_id, start_time, duration_minutes
        )
        
        # Convert to response format
        segment_data = []
        total_duration = 0
        
        for segment in segments:
            segment_info = {
                "id": segment.id,
                "filename": segment.filename,
                "start_time": segment.start_time.isoformat(),
                "end_time": segment.end_time.isoformat(),
                "duration_seconds": segment.duration_seconds,
                "stream_url": f"/api/v1/playback/segments/{segment.id}/stream",
                "exists": segment.exists
            }
            segment_data.append(segment_info)
            total_duration += segment.duration_seconds
        
        return {
            "camera_id": camera_id,
            "playback_start": start_time.isoformat(),
            "requested_duration_minutes": duration_minutes,
            "actual_duration_seconds": total_duration,
            "segments": segment_data,
            "segment_count": len(segments)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting continuous playback for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Storage management endpoints
@router.get("/storage/report", response_model=StorageReportResponse)
async def get_storage_report(db: AsyncSession = Depends(get_database)):
    """
    Get comprehensive storage report
    
    Args:
        db: Database session
        
    Returns:
        Detailed storage report
    """
    try:
        report = await storage_manager.get_storage_report()
        
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        
        return StorageReportResponse(**report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating storage report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/storage/cleanup")
async def trigger_storage_cleanup(
    camera_id: Optional[int] = Query(None, description="Camera ID to clean up (optional)"),
    db: AsyncSession = Depends(get_database)
):
    """
    Trigger storage cleanup manually
    
    Args:
        camera_id: Optional camera ID to clean up specifically
        db: Database session
        
    Returns:
        Cleanup results
    """
    try:
        if camera_id:
            # Clean up specific camera
            result = await storage_manager.force_cleanup_camera(camera_id)
            return {"status": "completed", "camera_cleanup": result}
        else:
            # Clean up all cameras
            await storage_manager.cleanup_old_recordings()
            return {"status": "completed", "message": "Storage cleanup triggered for all cameras"}
        
    except Exception as e:
        logger.error(f"Error during storage cleanup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/storage/cameras/{camera_id}/stats")
async def get_camera_storage_stats(
    camera_id: int,
    db: AsyncSession = Depends(get_database)
):
    """
    Get storage statistics for a specific camera
    
    Args:
        camera_id: ID of the camera
        db: Database session
        
    Returns:
        Camera storage statistics
    """
    try:
        stats = await storage_manager.get_camera_storage_stats(camera_id)
        
        return {
            "camera_id": camera_id,
            "total_size_bytes": stats.total_size_bytes,
            "total_size_formatted": storage_manager._format_bytes(stats.total_size_bytes),
            "total_segments": stats.total_segments,
            "oldest_recording": stats.oldest_recording,
            "newest_recording": stats.newest_recording,
            "average_segment_size": stats.average_segment_size,
            "storage_tiers": stats.storage_tiers
        }
        
    except Exception as e:
        logger.error(f"Error getting storage stats for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/segments/{segment_id}/export")
async def export_segment(
    segment_id: str,
    export_filename: str = Query(..., description="Filename for exported segment"),
    db: AsyncSession = Depends(get_database)
):
    """
    Export a video segment to downloads directory
    
    Args:
        segment_id: ID of the segment to export
        export_filename: Filename for the exported file
        db: Database session
        
    Returns:
        Export status
    """
    try:
        # Create exports directory
        from pathlib import Path
        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)
        
        export_path = exports_dir / export_filename
        
        # Export the segment
        success = await video_playback.export_segment(segment_id, str(export_path))
        
        if success:
            return {
                "status": "success",
                "message": f"Segment exported to {export_path}",
                "export_path": str(export_path)
            }
        else:
            raise HTTPException(status_code=404, detail="Segment not found or export failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@router.get("/health")
async def playback_health_check():
    """
    Health check endpoint for playback service
    
    Returns:
        Service health status
    """
    try:
        # Basic health checks
        storage_accessible = video_playback.base_path.exists()
        
        return {
            "status": "healthy" if storage_accessible else "degraded",
            "storage_accessible": storage_accessible,
            "base_storage_path": str(video_playback.base_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Playback health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }