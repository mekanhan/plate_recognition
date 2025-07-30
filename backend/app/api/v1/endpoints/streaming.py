"""
Video streaming endpoints for real-time camera feeds using Frame Distribution Architecture
"""
import cv2
import logging
import asyncio
import numpy as np
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
            
            # Set JPEG quality based on request (optimized for uncompressed sources)
            if quality == "low":
                jpeg_quality = 75  # Slightly higher for uncompressed sources
            elif quality == "medium":
                jpeg_quality = 90  # Higher quality to preserve uncompressed detail
            else:  # high quality
                jpeg_quality = 98  # Maximum quality for uncompressed sources
            
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
                
                # Validate and encode frame to JPEG with uncompressed frame handling
                try:
                    # Validate frame quality (especially important for uncompressed sources)
                    if not _validate_frame_for_encoding(frame):
                        logger.warning(f"Frame validation failed for camera {camera_id}, skipping frame")
                        await asyncio.sleep(0.033)  # ~30fps delay
                        continue
                    
                    # Handle different pixel formats from uncompressed sources
                    processed_frame = _prepare_frame_for_jpeg_encoding(frame)
                    
                    # Scale frame to fixed card size (800x600)
                    scaled_frame = _scale_frame_to_card(processed_frame, camera_id)
                    
                    # Encode with optimized parameters for uncompressed sources
                    encode_params = [
                        cv2.IMWRITE_JPEG_QUALITY, jpeg_quality,
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1,  # Optimize for size
                        cv2.IMWRITE_JPEG_PROGRESSIVE, 1  # Progressive JPEG for better streaming
                    ]
                    ret, jpeg_buffer = cv2.imencode('.jpg', scaled_frame, encode_params)
                    
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
    
    # Return the streaming response
    return StreamingResponse(
        generate_mjpeg_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "keep-alive"
        }
    )


def _validate_frame_for_encoding(frame) -> bool:
    """Validate frame quality for JPEG encoding with uncompressed video considerations
    
    Args:
        frame: OpenCV frame to validate
        
    Returns:
        bool: True if frame is suitable for JPEG encoding
    """
    if frame is None:
        return False
        
    # Check basic dimensions
    if len(frame.shape) < 2 or frame.shape[0] < 50 or frame.shape[1] < 50:
        return False
    
    # Check for completely black frames (common in codec corruption)
    if frame.max() < 5:
        return False
    
    # Check for reasonable pixel distribution (avoid corrupted frames)
    if len(frame.shape) == 3:  # Color frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    
    # Count non-zero pixels
    non_zero_pixels = cv2.countNonZero(gray)
    total_pixels = gray.shape[0] * gray.shape[1]
    
    # Frame should have at least 5% non-zero pixels
    if non_zero_pixels < (total_pixels * 0.05):
        return False
    
    return True


def _prepare_frame_for_jpeg_encoding(frame):
    """Prepare frame for JPEG encoding, handling different pixel formats from uncompressed sources
    
    Args:
        frame: OpenCV frame in various formats
        
    Returns:
        OpenCV frame ready for JPEG encoding (BGR format)
    """
    if frame is None:
        return None
    
    # Handle different pixel formats that may come from uncompressed sources
    if len(frame.shape) == 2:
        # Grayscale frame - convert to BGR for consistent JPEG encoding
        return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    elif len(frame.shape) == 3:
        channels = frame.shape[2]
        
        if channels == 3:
            # Could be BGR (OpenCV default) or RGB - assume BGR for now
            # For uncompressed sources, we might need to detect and convert
            return frame
        elif channels == 4:
            # RGBA or BGRA - convert to BGR
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        else:
            # Unknown format - try to use as-is
            return frame
    else:
        # Unknown frame structure - try to use as-is
        return frame


def _scale_frame_to_card(frame, camera_id):
    """Scale frame to fixed card size (800x600) with aspect ratio preservation
    
    Args:
        frame: OpenCV frame to scale
        camera_id: Camera ID for logging
        
    Returns:
        Scaled frame in 800x600 card format
    """
    # Fixed card dimensions
    CARD_WIDTH = 800
    CARD_HEIGHT = 600
    
    if frame is None:
        # Return black card if no frame
        return np.zeros((CARD_HEIGHT, CARD_WIDTH, 3), dtype=np.uint8)
    
    # Get original dimensions
    height, width = frame.shape[:2]
    
    # Calculate scaling to fit in card while maintaining aspect ratio
    scale = min(CARD_WIDTH / width, CARD_HEIGHT / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Resize frame
    frame_resized = cv2.resize(frame, (new_width, new_height))
    
    # Create black canvas of card size
    card = np.zeros((CARD_HEIGHT, CARD_WIDTH, 3), dtype=np.uint8)
    
    # Center the resized frame in the card
    y_offset = (CARD_HEIGHT - new_height) // 2
    x_offset = (CARD_WIDTH - new_width) // 2
    card[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = frame_resized
    
    return card

    
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


@router.get("/camera_info")
async def get_camera_info(db: AsyncSession = Depends(get_database)):
    """
    Get all cameras with their native resolution information
    
    Returns:
        Dictionary containing camera information including native resolutions
    """
    try:
        # Get all cameras from database
        from app.services.camera_crud import get_all_cameras
        cameras = await get_all_cameras(db)
        
        camera_info = []
        
        for camera in cameras:
            if not camera.enabled:
                continue
                
            # Get frame distributor to check resolution
            frame_manager = get_frame_distribution_manager()
            distributor = frame_manager.get_distributor(camera.id)
            
            # Default values
            width = height = fps = 0
            status = "offline"
            
            if distributor and distributor.is_running:
                stats = distributor.get_stats()
                if stats.get("is_connected", False):
                    # Try to get a frame to determine actual resolution
                    frame = distributor.get_latest_frame()
                    if frame is not None:
                        height, width = frame.shape[:2]
                        status = "online"
                        fps = 30  # Default FPS assumption
            
            camera_info.append({
                "id": camera.id,
                "name": camera.name,
                "native_resolution": f"{width}x{height}" if width > 0 else "Unknown",
                "native_width": width,
                "native_height": height,
                "fps": fps,
                "status": status,
                "card_width": 800,  # Fixed card width
                "card_height": 600  # Fixed card height
            })
        
        return {"cameras": camera_info}
        
    except Exception as e:
        logger.error(f"Error getting camera info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get camera info: {str(e)}"
        )


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