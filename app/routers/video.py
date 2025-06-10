# app/routers/video.py
import os
import time
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import logging

from app.services.video_service import VideoRecordingService
from app.dependencies.services import get_video_recording_service
from app.repositories.sql_repository import SQLiteVideoRepository
from app.dependencies.services import get_video_repository

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/segments")
async def get_video_segments(
    limit: int = Query(20, description="Maximum number of video segments to return"),
    offset: int = Query(0, description="Number of video segments to skip"),
    video_repository: SQLiteVideoRepository = Depends(get_video_repository)
):
    """
    Get a list of video segments with pagination
    
    Args:
        limit: Maximum number of segments to return
        offset: Number of segments to skip
    """
    try:
        segments = await video_repository.get_video_segments(limit=limit, offset=offset)
        
        return {
            "count": len(segments),
            "segments": segments
        }
    except Exception as e:
        logger.error(f"Error getting video segments: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving video segments: {str(e)}")

@router.get("/segments/{segment_id}")
async def get_video_segment(
    segment_id: str,
    video_repository: SQLiteVideoRepository = Depends(get_video_repository)
):
    """
    Get information about a specific video segment
    
    Args:
        segment_id: ID of the video segment
    """
    try:
        segment = await video_repository.get_video_segment_by_id(segment_id)
        
        if not segment:
            raise HTTPException(status_code=404, detail=f"Video segment with ID {segment_id} not found")
        
        return segment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving video segment: {str(e)}")

@router.get("/segments/{segment_id}/download")
async def download_video_segment(
    segment_id: str,
    video_repository: SQLiteVideoRepository = Depends(get_video_repository)
):
    """
    Download a specific video segment
    
    Args:
        segment_id: ID of the video segment
    """
    try:
        segment = await video_repository.get_video_segment_by_id(segment_id)
        
        if not segment:
            raise HTTPException(status_code=404, detail=f"Video segment with ID {segment_id} not found")
        
        file_path = segment["file_path"]
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Video file not found")
        
        # Return the video file
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="video/mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading video segment: {str(e)}")

@router.get("/by-detection/{detection_id}")
async def get_videos_by_detection(
    detection_id: str,
    video_recording_service: VideoRecordingService = Depends(get_video_recording_service)
):
    """
    Get videos containing a specific detection
    
    Args:
        detection_id: ID of the detection
    """
    try:
        videos = await video_recording_service.get_videos_for_detection(detection_id)
        
        return {
            "count": len(videos),
            "videos": videos
        }
    except Exception as e:
        logger.error(f"Error getting videos for detection {detection_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving videos: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_videos(
    retention_days: int = Query(30, description="Number of days to keep videos"),
    video_recording_service: VideoRecordingService = Depends(get_video_recording_service)
):
    """
    Clean up old video recordings
    
    Args:
        retention_days: Number of days to keep videos
    """
    try:
        archived_count = await video_recording_service.cleanup_old_videos(retention_days=retention_days)
        
        return {
            "status": "success",
            "message": f"Archived {archived_count} old videos",
            "archived_count": archived_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up old videos: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up old videos: {str(e)}")

@router.get("/stats")
async def get_video_stats(
    video_repository: SQLiteVideoRepository = Depends(get_video_repository)
):
    """Get statistics about video recordings"""
    try:
        # Get all video segments
        segments = await video_repository.get_video_segments(limit=1000)
        
        # Calculate statistics
        total_count = len(segments)
        total_size_bytes = sum(segment.get("file_size_bytes", 0) for segment in segments)
        total_duration_seconds = sum(segment.get("duration_seconds", 0) for segment in segments)
        
        # Get count by date
        videos_by_date = {}
        for segment in segments:
            if "start_time" in segment:
                date_str = time.strftime("%Y-%m-%d", time.localtime(segment["start_time"]))
                videos_by_date[date_str] = videos_by_date.get(date_str, 0) + 1
        
        return {
            "total_count": total_count,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "total_duration_minutes": round(total_duration_seconds / 60, 2),
            "average_duration_seconds": round(total_duration_seconds / total_count, 2) if total_count > 0 else 0,
            "average_size_mb": round(total_size_bytes / total_count / (1024 * 1024), 2) if total_count > 0 else 0,
            "videos_by_date": videos_by_date
        }
    except Exception as e:
        logger.error(f"Error getting video stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving video statistics: {str(e)}")