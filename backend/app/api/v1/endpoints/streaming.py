"""
Video streaming endpoints for real-time camera feeds
"""
import cv2
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_database
from app.services.camera_crud import get_camera_by_id, update_camera_status
from app.services.camera_streaming_service import CameraStreamingService, StreamConfig

logger = logging.getLogger(__name__)
router = APIRouter()  # For management endpoints (/api/v1/streams/*)
video_router = APIRouter()  # For direct video endpoints (/stream/*)

# Global dictionary to store active streaming services
active_streams: Dict[int, CameraStreamingService] = {}


class StreamStartRequest(BaseModel):
    """Request model for starting a stream"""
    quality: str = "medium"  # low, medium, high
    max_fps: int = 30
    detection_enabled: bool = False  # For future Phase 2 implementation
    confidence_threshold: float = 0.7  # For future Phase 2 implementation


class StreamStatusResponse(BaseModel):
    """Response model for stream status"""
    camera_id: int
    camera_name: str
    status: str  # active, stopped, error, connecting
    current_fps: Optional[float] = None
    queue_size: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


@video_router.options("/video/{camera_id}")
async def stream_video_options(camera_id: int):
    """Handle CORS preflight for video streaming"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@video_router.get("/video/{camera_id}")
async def stream_video(
    camera_id: int,
    quality: str = Query("medium", regex="^(low|medium|high)$"),
    db: AsyncSession = Depends(get_database)
):
    """
    Stream live video from specified camera as MJPEG
    
    Args:
        camera_id: ID of the camera to stream from
        quality: Video quality (low, medium, high)
        db: Database session
        
    Returns:
        Streaming MJPEG response
    """
    # Get camera from database
    camera = await get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    if not camera.enabled:
        raise HTTPException(status_code=403, detail="Camera is disabled")
    
    # Check if stream is already active for this camera
    streaming_service = active_streams.get(camera_id)
    
    if not streaming_service:
        # Create new streaming service
        config = StreamConfig(quality=quality)
        streaming_service = CameraStreamingService(camera, config)
        
        # Test connection with optimized timeout
        try:
            if not await streaming_service.connect_camera():
                await update_camera_status(db, camera_id, "error")
                raise HTTPException(
                    status_code=503,
                    detail="Failed to connect to camera"
                )
        except Exception as e:
            logger.error(f"Error connecting to camera {camera_id}: {str(e)}")
            await update_camera_status(db, camera_id, "error")
            raise HTTPException(
                status_code=503,
                detail=f"Camera connection error: {str(e)}"
            )
        
        # Store active stream
        active_streams[camera_id] = streaming_service
        await update_camera_status(db, camera_id, "online")
    
    async def generate_frames():
        """Generator function for MJPEG frames"""
        try:
            logger.info(f"Starting video stream for camera {camera_id}")
            
            async for frame_bytes in streaming_service.start_streaming():
                # Format frame for MJPEG multipart response
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + 
                    frame_bytes + 
                    b'\r\n'
                )
                
        except Exception as e:
            logger.error(f"Error in video stream for camera {camera_id}: {str(e)}")
            await update_camera_status(db, camera_id, "error")
            # Remove from active streams
            if camera_id in active_streams:
                await active_streams[camera_id].stop_streaming()
                del active_streams[camera_id]
            raise
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@video_router.options("/thumbnail/{camera_id}")
async def thumbnail_options(camera_id: int):
    """Handle CORS preflight for thumbnail endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@video_router.get("/thumbnail/{camera_id}")
async def get_camera_thumbnail(
    camera_id: int,
    width: int = Query(320, ge=160, le=1920),
    height: int = Query(240, ge=120, le=1080),
    db: AsyncSession = Depends(get_database)
):
    """
    Get current frame from camera as static JPEG image
    
    Args:
        camera_id: ID of the camera
        width: Thumbnail width in pixels
        height: Thumbnail height in pixels
        db: Database session
        
    Returns:
        JPEG image response
    """
    # Get camera from database
    camera = await get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    if not camera.enabled:
        raise HTTPException(status_code=403, detail="Camera is disabled")
    
    # Check if stream is already active
    streaming_service = active_streams.get(camera_id)
    
    if not streaming_service:
        # Create temporary streaming service for single frame
        config = StreamConfig(quality="medium")
        streaming_service = CameraStreamingService(camera, config)
        
        try:
            frame_bytes = await streaming_service.get_current_frame()
            await streaming_service.disconnect_camera()
            
            if not frame_bytes:
                await update_camera_status(db, camera_id, "error")
                raise HTTPException(
                    status_code=503,
                    detail="Failed to capture frame from camera"
                )
                
        except Exception as e:
            logger.error(f"Error getting thumbnail for camera {camera_id}: {str(e)}")
            await update_camera_status(db, camera_id, "error")
            raise HTTPException(
                status_code=503,
                detail=f"Camera error: {str(e)}"
            )
    else:
        # Use active stream to get current frame
        frame_bytes = await streaming_service.get_current_frame()
        if not frame_bytes:
            raise HTTPException(
                status_code=503,
                detail="No frame available from active stream"
            )
    
    return Response(
        content=frame_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": f"inline; filename=camera_{camera_id}_thumbnail.jpg",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post("/start/{camera_id}")
async def start_camera_stream(
    camera_id: int,
    request: StreamStartRequest,
    db: AsyncSession = Depends(get_database)
):
    """
    Start streaming session for specified camera
    
    Args:
        camera_id: ID of the camera
        request: Stream configuration
        db: Database session
        
    Returns:
        Stream session information
    """
    # Get camera from database
    camera = await get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    if not camera.enabled:
        raise HTTPException(status_code=403, detail="Camera is disabled")
    
    # Check if stream is already active
    if camera_id in active_streams:
        streaming_service = active_streams[camera_id]
        if streaming_service.is_streaming:
            return {
                "camera_id": camera_id,
                "status": "already_active",
                "message": "Stream is already active for this camera"
            }
    
    # Create new streaming service
    config = StreamConfig(
        quality=request.quality,
        max_fps=request.max_fps
    )
    streaming_service = CameraStreamingService(camera, config)
    
    try:
        # Test connection (but with optimized timeout)
        if not await streaming_service.connect_camera():
            await update_camera_status(db, camera_id, "error")
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to camera"
            )
        
        # Store active stream
        active_streams[camera_id] = streaming_service
        await update_camera_status(db, camera_id, "online")
        
        logger.info(f"Started stream for camera {camera_id}")
        
        return {
            "camera_id": camera_id,
            "status": "active",
            "started_at": streaming_service.capture.get(cv2.CAP_PROP_POS_MSEC) if streaming_service.capture else None,
            "settings": {
                "quality": request.quality,
                "max_fps": request.max_fps,
                "detection_enabled": request.detection_enabled,
                "confidence_threshold": request.confidence_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"Error starting stream for camera {camera_id}: {str(e)}")
        await update_camera_status(db, camera_id, "error")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start stream: {str(e)}"
        )


@router.post("/stop/{camera_id}")
async def stop_camera_stream(
    camera_id: int,
    db: AsyncSession = Depends(get_database)
):
    """
    Stop active streaming session for specified camera
    
    Args:
        camera_id: ID of the camera
        db: Database session
        
    Returns:
        Stream stop confirmation
    """
    # Check if stream is active
    if camera_id not in active_streams:
        raise HTTPException(
            status_code=404,
            detail="No active stream found for this camera"
        )
    
    streaming_service = active_streams[camera_id]
    
    try:
        # Stop streaming
        await streaming_service.stop_streaming()
        
        # Remove from active streams
        del active_streams[camera_id]
        
        # Update camera status
        await update_camera_status(db, camera_id, "offline")
        
        logger.info(f"Stopped stream for camera {camera_id}")
        
        return {
            "camera_id": camera_id,
            "status": "stopped",
            "message": "Stream stopped successfully"
        }
        
    except Exception as e:
        logger.error(f"Error stopping stream for camera {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop stream: {str(e)}"
        )


@router.get("/status/{camera_id}", response_model=StreamStatusResponse)
async def get_stream_status(
    camera_id: int,
    db: AsyncSession = Depends(get_database)
) -> StreamStatusResponse:
    """
    Get current streaming status for specified camera
    
    Args:
        camera_id: ID of the camera
        db: Database session
        
    Returns:
        Current stream status
    """
    # Get camera from database
    camera = await get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Check if stream is active
    streaming_service = active_streams.get(camera_id)
    
    if streaming_service and streaming_service.is_streaming:
        stream_info = streaming_service.get_stream_info()
        return StreamStatusResponse(
            camera_id=camera_id,
            camera_name=camera.name,
            status="active",
            queue_size=stream_info["queue_size"],
            settings=stream_info["config"]
        )
    else:
        return StreamStatusResponse(
            camera_id=camera_id,
            camera_name=camera.name,
            status="stopped"
        )


@router.get("/")
async def list_active_streams(
    db: AsyncSession = Depends(get_database)
):
    """
    Get list of all active streaming sessions
    
    Returns:
        List of active streams with their status
    """
    active_stream_list = []
    
    for camera_id, streaming_service in active_streams.items():
        if streaming_service.is_streaming:
            # Get camera info from database
            camera = await get_camera_by_id(db, camera_id)
            if camera:
                stream_info = streaming_service.get_stream_info()
                active_stream_list.append({
                    "camera_id": camera_id,
                    "camera_name": camera.name,
                    "status": "active",
                    "queue_size": stream_info["queue_size"],
                    "settings": stream_info["config"]
                })
    
    return {
        "streams": active_stream_list,
        "total": len(active_stream_list)
    }


# Cleanup function to stop all streams (can be called on shutdown)
async def cleanup_all_streams():
    """Stop all active streams and cleanup resources"""
    logger.info("Cleaning up all active streams...")
    
    for camera_id, streaming_service in list(active_streams.items()):
        try:
            await streaming_service.stop_streaming()
            logger.info(f"Stopped stream for camera {camera_id}")
        except Exception as e:
            logger.error(f"Error stopping stream for camera {camera_id}: {str(e)}")
    
    active_streams.clear()
    logger.info("All streams cleaned up")