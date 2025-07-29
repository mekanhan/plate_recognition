"""
Video streaming endpoints for real-time camera feeds using Frame Distribution Architecture
"""
import cv2
import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_database
from app.services.camera_crud import get_camera_by_id, update_camera_status
from app.services.camera_streaming_service import CameraStreamingService, StreamConfig
from app.services.frame_distribution_service import FrameDistributionConfig

logger = logging.getLogger(__name__)
router = APIRouter()  # For management endpoints (/api/v1/streams/*)
video_router = APIRouter()  # For direct video endpoints (/stream/*)

# Global dictionary to store active streaming services
# NOTE: With on-demand streaming, this is no longer used for persistent connections
active_streams: Dict[int, CameraStreamingService] = {}


def get_frame_distribution_manager():
    """Lazy-load frame distribution manager to avoid startup deadlocks"""
    from app.services.frame_distribution_service import get_frame_distribution_manager as get_manager
    return get_manager()


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
    
    # Create on-demand streaming service (no persistent connections)
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
            # Cleanup streaming service
            await streaming_service.stop_streaming()
            raise
        finally:
            # Always cleanup when stream ends
            await streaming_service.stop_streaming()
    
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


@video_router.get("/mjpeg/{camera_id}")
async def stream_mjpeg_video(
    camera_id: int,
    quality: str = Query("medium", regex="^(low|medium|high)$"),
    db: AsyncSession = Depends(get_database)
):
    """
    Stream live MJPEG video from camera using Frame Distribution Architecture
    
    This endpoint provides continuous MJPEG streaming with single camera connection
    shared across all consumers (recording, detection, web streaming).
    
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
    
    # Get or create frame distributor (lazy-loaded)
    frame_manager = get_frame_distribution_manager()
    distributor = frame_manager.get_distributor(camera_id)
    
    if not distributor:
        # Create new distributor
        distribution_config = FrameDistributionConfig(
            recording_queue_size=30,
            detection_queue_size=10,
            latest_frame_timeout=5.0
        )
        distributor = frame_manager.create_distributor(camera, distribution_config)
        
        # Start the distributor
        if not distributor.start():
            await update_camera_status(db, camera_id, "error")
            raise HTTPException(
                status_code=503,
                detail="Failed to start camera frame distribution"
            )
    
    # Ensure distributor is running
    if not distributor.is_running:
        await update_camera_status(db, camera_id, "error")
        raise HTTPException(
            status_code=503,
            detail="Camera frame distributor not available"
        )
    
    await update_camera_status(db, camera_id, "online")
    
    async def generate_mjpeg_frames() -> AsyncGenerator[bytes, None]:
        """Generate MJPEG frames from frame distributor"""
        consumer_name = f"mjpeg_streaming_{camera_id}"
        consumer = None
        
        try:
            logger.info(f"Starting MJPEG stream for camera {camera_id}")
            
            # Add consumer to distributor with error handling
            consumer = distributor.add_consumer(consumer_name, queue_size=10)
            
            if consumer is None:
                logger.error(f"Failed to add consumer for camera {camera_id} - too many active consumers")
                raise HTTPException(
                    status_code=503,
                    detail="Too many active streams for this camera"
                )
            
            # Set JPEG quality based on request
            if quality == "low":
                jpeg_quality = 70
            elif quality == "medium":
                jpeg_quality = 85
            else:  # high quality
                jpeg_quality = 95
            
            while True:
                # Get frame from consumer queue with fallback to latest frame
                frame = consumer.get_frame(timeout=3.0) if consumer else None
                
                if frame is None:
                    # Fallback to latest frame from distributor
                    frame = distributor.get_latest_frame()
                    
                    if frame is None:
                        logger.warning(f"No frame available for camera {camera_id}")
                        await asyncio.sleep(0.1)
                        continue
                
                # Encode frame to JPEG
                try:
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
                    ret, jpeg_buffer = cv2.imencode('.jpg', frame, encode_params)
                    
                    if ret:
                        # Yield MJPEG frame
                        yield (
                            b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + 
                            jpeg_buffer.tobytes() + 
                            b'\r\n'
                        )
                    else:
                        logger.warning(f"Failed to encode frame for camera {camera_id}")
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    logger.error(f"Error encoding frame for camera {camera_id}: {str(e)}")
                    await asyncio.sleep(0.1)
                    continue
                    
        except Exception as e:
            logger.error(f"Error in MJPEG stream for camera {camera_id}: {str(e)}")
            await update_camera_status(db, camera_id, "error")
            raise
        finally:
            # Cleanup consumer
            if consumer and distributor:
                distributor.remove_consumer(consumer_name)
                logger.info(f"MJPEG stream stopped for camera {camera_id}")
    
    return StreamingResponse(
        generate_mjpeg_frames(),
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
    
    # Create temporary streaming service for single frame (on-demand)
    config = StreamConfig(quality="medium")
    streaming_service = CameraStreamingService(camera, config)
    
    try:
        frame_bytes = await streaming_service.get_current_frame()
        
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
    finally:
        # Always cleanup temporary connection
        await streaming_service.disconnect_camera()
    
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


@video_router.get("/snapshot/{camera_id}")
async def get_camera_snapshot(
    camera_id: int,
    quality: str = Query("high", regex="^(low|medium|high)$"),
    width: int = Query(None, ge=160, le=1920),
    height: int = Query(None, ge=120, le=1080),
    db: AsyncSession = Depends(get_database)
):
    """
    Get single frame snapshot from camera using Frame Distribution Architecture
    
    Args:
        camera_id: ID of the camera
        quality: JPEG quality (low, medium, high)
        width: Optional width for resizing
        height: Optional height for resizing
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
    
    try:
        # Get or create frame distributor (lazy-loaded)
        frame_manager = get_frame_distribution_manager()
        distributor = frame_manager.get_distributor(camera_id)
        
        if not distributor:
            # Create new distributor
            distribution_config = FrameDistributionConfig(
                recording_queue_size=30,
                detection_queue_size=10,
                latest_frame_timeout=5.0
            )
            distributor = frame_manager.create_distributor(camera, distribution_config)
            
            # Start the distributor
            if not distributor.start():
                await update_camera_status(db, camera_id, "error")
                raise HTTPException(
                    status_code=503,
                    detail="Failed to start camera frame distribution"
                )
        
        # Get latest frame from distributor
        frame = distributor.get_latest_frame()
        
        if frame is None:
            await update_camera_status(db, camera_id, "error")
            raise HTTPException(
                status_code=503,
                detail="No frame available from camera"
            )
        
        # Resize frame if requested
        if width and height:
            frame = cv2.resize(frame, (width, height))
        
        # Set JPEG quality based on request
        if quality == "low":
            jpeg_quality = 70
        elif quality == "medium":
            jpeg_quality = 85
        else:  # high quality
            jpeg_quality = 95
        
        # Encode frame to JPEG
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        ret, jpeg_buffer = cv2.imencode('.jpg', frame, encode_params)
        
        if not ret:
            raise HTTPException(
                status_code=500,
                detail="Failed to encode frame"
            )
        
        await update_camera_status(db, camera_id, "online")
        
        return Response(
            content=jpeg_buffer.tobytes(),
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Content-Disposition": f"inline; filename=camera_{camera_id}_snapshot.jpg",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting snapshot for camera {camera_id}: {str(e)}")
        await update_camera_status(db, camera_id, "error")
        raise HTTPException(
            status_code=503,
            detail=f"Camera error: {str(e)}"
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
    
    # With on-demand streaming, we just test the camera connection
    # Actual streaming happens when /stream/video/{camera_id} is accessed
    config = StreamConfig(
        quality=request.quality,
        max_fps=request.max_fps
    )
    streaming_service = CameraStreamingService(camera, config)
    
    try:
        # Test connection to validate camera is accessible
        if not await streaming_service.connect_camera():
            await update_camera_status(db, camera_id, "error")
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to camera"
            )
        
        # Disconnect immediately (connection will be made on-demand)
        await streaming_service.disconnect_camera()
        await update_camera_status(db, camera_id, "online")
        
        logger.info(f"Camera {camera_id} connection test successful")
        
        return {
            "camera_id": camera_id,
            "status": "ready",  # Camera is ready for streaming
            "message": "Camera connection validated, ready for streaming",
            "settings": {
                "quality": request.quality,
                "max_fps": request.max_fps,
                "detection_enabled": request.detection_enabled,
                "confidence_threshold": request.confidence_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing camera {camera_id}: {str(e)}")
        await update_camera_status(db, camera_id, "error")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test camera: {str(e)}"
        )


@router.post("/stop/{camera_id}")
async def stop_camera_stream(
    camera_id: int,
    db: AsyncSession = Depends(get_database)
):
    """
    Stop streaming session for specified camera
    
    With on-demand streaming, this endpoint is mainly informational
    since streams automatically stop when no longer accessed.
    
    Args:
        camera_id: ID of the camera
        db: Database session
        
    Returns:
        Stream stop confirmation
    """
    # Get camera from database
    camera = await get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # With on-demand streaming, there are no persistent streams to stop
    # This endpoint is mainly for API compatibility
    logger.info(f"Stop requested for camera {camera_id} (on-demand streaming)")
    
    return {
        "camera_id": camera_id,
        "status": "stopped",
        "message": "On-demand streaming - no persistent connection to stop"
    }


@router.get("/status/{camera_id}", response_model=StreamStatusResponse)
async def get_stream_status(
    camera_id: int,
    db: AsyncSession = Depends(get_database)
) -> StreamStatusResponse:
    """
    Get current streaming status for specified camera using Frame Distribution
    
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
    
    # Check frame distributor status (lazy-loaded)
    frame_manager = get_frame_distribution_manager()
    distributor = frame_manager.get_distributor(camera_id)
    
    if not distributor:
        return StreamStatusResponse(
            camera_id=camera_id,
            camera_name=camera.name,
            status="stopped"
        )
    
    # Get distributor stats
    stats = distributor.get_stats()
    
    # Determine status based on distributor state
    if stats.get("is_connected", False) and distributor.is_running:
        status = "active"
        current_fps = None  # Could calculate from frames_captured over time
        queue_size = len(stats.get("consumers", {}))
    else:
        status = "error" if stats.get("consecutive_failures", 0) > 0 else "stopped"
        current_fps = None
        queue_size = None
    
    return StreamStatusResponse(
        camera_id=camera_id,
        camera_name=camera.name,
        status=status,
        current_fps=current_fps,
        queue_size=queue_size,
        settings={
            "frames_captured": stats.get("frames_captured", 0),
            "consecutive_failures": stats.get("consecutive_failures", 0),
            "consumers": list(stats.get("consumers", {}).keys()),
            "latest_frame_age": stats.get("latest_frame_age")
        }
    )


@router.get("/")
async def list_active_streams(
    db: AsyncSession = Depends(get_database)
):
    """
    Get list of all active streaming sessions
    
    With on-demand streaming, this always returns empty since
    no persistent connections are maintained.
    
    Returns:
        Empty list of streams
    """
    return {
        "streams": [],
        "total": 0,
        "message": "On-demand streaming - no persistent connections maintained"
    }


@router.get("/diagnostics/{camera_id}")
async def diagnose_camera_connectivity(
    camera_id: int,
    db: AsyncSession = Depends(get_database)
):
    """
    Run comprehensive connectivity diagnostics for specified camera
    
    Args:
        camera_id: ID of the camera to diagnose
        db: Database session
        
    Returns:
        Detailed diagnostic information including:
        - Network connectivity (ping)
        - Port accessibility 
        - RTSP/HTTP stream tests
        - OpenCV connection tests
    """
    # Get camera from database
    camera = await get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    try:
        # Create temporary streaming service for diagnostics
        config = StreamConfig(quality="medium")
        streaming_service = CameraStreamingService(camera, config)
        
        # Run comprehensive diagnostics
        diagnostics = await streaming_service.diagnose_connectivity()
        
        # Clean up any test connections
        await streaming_service.disconnect_camera()
        
        return diagnostics
        
    except Exception as e:
        logger.error(f"Error running diagnostics for camera {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run diagnostics: {str(e)}"
        )


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