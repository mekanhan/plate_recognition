"""
Playback API endpoints for 24/7 recording system
Provides timeline access, video streaming, and storage management
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from app.core.playback import VideoPlayback, TimelineSegment
from app.core.storage import StorageManager, StorageConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/playback", tags=["playback"])

# Initialize services
playback_service = VideoPlayback()
storage_manager = StorageManager()


# Pydantic models for API responses
class TimelineSegmentResponse(BaseModel):
    """Response model for timeline segments"""
    id: int
    camera_id: int
    filename: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    file_size: int
    exists: bool


class TimelineResponse(BaseModel):
    """Response model for timeline queries"""
    camera_id: int
    start_time: datetime
    end_time: datetime
    total_segments: int
    total_duration_seconds: int
    segments: List[TimelineSegmentResponse]


class PlaybackInfoResponse(BaseModel):
    """Response model for playback information"""
    segment_id: str
    file_path: str
    offset_seconds: float
    exists: bool


class StorageStatsResponse(BaseModel):
    """Response model for storage statistics"""
    total_segments: int
    total_size_bytes: int
    total_size_formatted: str
    oldest_recording: Optional[datetime]
    newest_recording: Optional[datetime]
    disk_free_bytes: int
    disk_free_formatted: str
    disk_used_percent: float


class CameraStorageResponse(BaseModel):
    """Response model for camera storage stats"""
    camera_id: int
    segments: int
    size_bytes: int
    size_formatted: str
    oldest_recording: Optional[datetime]
    newest_recording: Optional[datetime]


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    storage_status: str
    playback_status: str
    message: Optional[str] = None


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health status of playback system"""
    try:
        # Check storage health
        storage_health = await storage_manager.monitor_storage_health()
        
        return HealthResponse(
            status="healthy",
            storage_status=storage_health.get('status', 'unknown'),
            playback_status="operational",
            message=f"Disk usage: {storage_health.get('disk_used_percent', 0):.1f}%"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/cameras/{camera_id}/timeline", response_model=TimelineResponse)
async def get_camera_timeline(
    camera_id: int,
    start_time: datetime = Query(..., description="Start time for timeline"),
    end_time: datetime = Query(..., description="End time for timeline")
):
    """Get video timeline for a camera within a time range"""
    try:
        # Validate time range
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        if (end_time - start_time).days > 7:
            raise HTTPException(status_code=400, detail="Time range cannot exceed 7 days")
        
        # Get timeline segments
        segments = await playback_service.get_camera_timeline(camera_id, start_time, end_time)
        
        # Calculate totals
        total_duration = sum(s.duration_seconds for s in segments)
        
        # Convert to response models
        segment_responses = [
            TimelineSegmentResponse(
                id=s.id,
                camera_id=s.camera_id,
                filename=s.filename,
                start_time=s.start_time,
                end_time=s.end_time,
                duration_seconds=s.duration_seconds,
                file_size=s.file_size,
                exists=s.exists
            ) for s in segments
        ]
        
        return TimelineResponse(
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            total_segments=len(segments),
            total_duration_seconds=total_duration,
            segments=segment_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to get timeline")


@router.get("/cameras/{camera_id}/info", response_model=PlaybackInfoResponse)
async def get_playback_info(
    camera_id: int,
    timestamp: datetime = Query(..., description="Timestamp to find playback info for")
):
    """Get playback information for a specific timestamp"""
    try:
        info = await playback_service.get_playback_info(camera_id, timestamp)
        
        if not info:
            raise HTTPException(status_code=404, detail="No recording found for timestamp")
        
        return PlaybackInfoResponse(
            segment_id=info['segment_id'],
            file_path=info['file_path'],
            offset_seconds=info['offset_seconds'],
            exists=info['exists']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting playback info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get playback info")


@router.get("/segments/{segment_id}/stream")
async def stream_video_segment(
    segment_id: str,
    range: Optional[str] = None
):
    """Stream a video segment with optional range request support"""
    try:
        # Get segment information
        segment = await playback_service.get_segment_by_id(segment_id)
        
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")
        
        if not segment.exists:
            raise HTTPException(status_code=404, detail="Segment file missing")
        
        file_path = Path(segment.file_path)
        file_size = file_path.stat().st_size
        
        # Handle range request
        if range:
            # Parse range header
            range_start = 0
            range_end = file_size - 1
            
            if range.startswith("bytes="):
                range_spec = range[6:]
                parts = range_spec.split("-")
                if parts[0]:
                    range_start = int(parts[0])
                if parts[1]:
                    range_end = int(parts[1])
            
            # Validate range
            if range_start >= file_size:
                raise HTTPException(status_code=416, detail="Range not satisfiable")
            
            range_end = min(range_end, file_size - 1)
            content_length = range_end - range_start + 1
            
            # Create partial response
            def iterfile():
                with open(file_path, 'rb') as f:
                    f.seek(range_start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        remaining -= len(data)
                        yield data
            
            return StreamingResponse(
                iterfile(),
                status_code=206,
                headers={
                    "Content-Type": "video/x-msvideo",
                    "Content-Length": str(content_length),
                    "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
                    "Accept-Ranges": "bytes"
                }
            )
        else:
            # Full file response
            return FileResponse(
                file_path,
                media_type="video/x-msvideo",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(file_size)
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming segment: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream segment")


@router.get("/segments/{segment_id}/info")
async def get_segment_info(segment_id: str):
    """Get information about a specific segment"""
    try:
        segment = await playback_service.get_segment_by_id(segment_id)
        
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
            "exists": segment.exists
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting segment info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get segment info")


@router.get("/cameras/{camera_id}/search")
async def search_recordings(
    camera_id: int,
    start_date: datetime = Query(..., description="Start date for search"),
    end_date: datetime = Query(..., description="End date for search"),
    min_duration: Optional[int] = Query(None, description="Minimum duration in seconds"),
    max_duration: Optional[int] = Query(None, description="Maximum duration in seconds")
):
    """Search for recordings with specific criteria"""
    try:
        segments = await playback_service.search_recordings(
            camera_id,
            start_date,
            end_date,
            min_duration,
            max_duration
        )
        
        return {
            "camera_id": camera_id,
            "search_criteria": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "min_duration": min_duration,
                "max_duration": max_duration
            },
            "total_results": len(segments),
            "segments": [
                {
                    "id": s.id,
                    "filename": s.filename,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "duration_seconds": s.duration_seconds,
                    "file_size": s.file_size,
                    "exists": s.exists
                } for s in segments
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching recordings: {e}")
        raise HTTPException(status_code=500, detail="Failed to search recordings")


@router.get("/storage/report")
async def get_storage_report():
    """Get comprehensive storage report"""
    try:
        report = await storage_manager.get_storage_report()
        
        if 'error' in report:
            raise HTTPException(status_code=500, detail=report['error'])
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting storage report: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage report")


@router.get("/storage/cameras/{camera_id}/stats", response_model=CameraStorageResponse)
async def get_camera_storage_stats(camera_id: int):
    """Get storage statistics for a specific camera"""
    try:
        stats = await storage_manager.get_camera_storage_stats(camera_id)
        
        return CameraStorageResponse(
            camera_id=camera_id,
            segments=stats.total_segments,
            size_bytes=stats.total_size_bytes,
            size_formatted=storage_manager._format_bytes(stats.total_size_bytes),
            oldest_recording=stats.oldest_recording,
            newest_recording=stats.newest_recording
        )
        
    except Exception as e:
        logger.error(f"Error getting camera storage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get camera storage stats")


@router.post("/storage/cleanup")
async def trigger_storage_cleanup(
    camera_id: Optional[int] = Query(None, description="Optional camera ID to cleanup")
):
    """Manually trigger storage cleanup"""
    try:
        result = await storage_manager.cleanup_old_recordings(camera_id)
        
        return {
            "status": "completed",
            "removed_segments": result['removed_segments'],
            "freed_bytes": result['freed_bytes'],
            "freed_formatted": storage_manager._format_bytes(result['freed_bytes']),
            "errors": result['errors']
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform cleanup")