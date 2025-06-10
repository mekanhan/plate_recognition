"""
Improved stream routes using the new service architecture.
"""
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.responses import Response
import logging
from typing import Optional
import cv2

from app.interfaces.camera import Camera
from app.dependencies.services import get_camera
from app.services.detection_service_v2 import DetectionServiceV2

# Logger for this module
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Reference to services, set during app startup
detection_service: Optional[DetectionServiceV2] = None

# Global setting for frame processing
frame_processor = {
    "process_every_n_frames": 5,  # Only process every 5th frame
    "frame_count": 0,
    "processing_time_ms": 0
}

# Global settings for plate tracking
plate_tracker = {
    "process_interval": 1.0  # Process queue every 1 second
}

async def generate_frames(
    camera: Camera,
    detection_svc: Optional[DetectionServiceV2] = None
):
    """
    Generate video frames for streaming with license plate detection.
    
    Args:
        camera: Camera interface for capturing frames
        detection_svc: Detection service for processing frames
    """
    global frame_processor
    
    while True:
        try:
            start_time = time.time()
            
            # Get frame from camera
            frame, timestamp = await camera.get_frame()
            
            # Increment frame counter
            frame_processor["frame_count"] += 1
            
            # Process frame with detection (only every Nth frame to reduce CPU usage)
            if detection_svc and frame_processor["frame_count"] % frame_processor["process_every_n_frames"] == 0:
                try:
                    # Process the frame with a timeout to avoid blocking too long
                    process_task = asyncio.create_task(detection_svc.process_frame(frame))
                    processed_frame, detections = await asyncio.wait_for(process_task, timeout=0.5)
                    
                    # Update the frame with the processed version (annotated frame)
                    frame = processed_frame
                    
                    # Send annotated frame to video recording service if available
                    if detection_svc.video_recording_service:
                        try:
                            await detection_svc.video_recording_service.add_frame(processed_frame, timestamp)
                        except Exception as e:
                            logger.error(f"Error adding frame to video recording: {e}")
                    
                    # Calculate processing time
                    frame_processor["processing_time_ms"] = (time.time() - start_time) * 1000
                except asyncio.TimeoutError:
                    logger.warning("Frame processing timed out")
                except Exception as e:
                    logger.error(f"Error processing frame: {e}")

            else:
                # Send raw frame to video recording service if available and no detection processing
                if detection_svc and detection_svc.video_recording_service:
                    try:
                        await detection_svc.video_recording_service.add_frame(frame, timestamp)
                    except Exception as e:
                        logger.error(f"Error adding raw frame to video recording: {e}")
                
                # Just add timestamp to the frame without detection
                cv2.putText(
                    frame,
                    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )
            
            # Add performance metrics to the frame if we processed it
            if frame_processor["frame_count"] % frame_processor["process_every_n_frames"] == 0:
                processing_time = frame_processor["processing_time_ms"]
                cv2.putText(
                    frame,
                    f"Process: {processing_time:.1f}ms",
                    (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1
                )
                
                cv2.putText(
                    frame,
                    f"Frame: {frame_processor['frame_count']}",
                    (10, frame.shape[0] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1
                )
            
            # Convert to JPEG
            _, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()
            
            # Yield the frame in MJPEG format
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            
            # Calculate frame time and adaptive sleep
            frame_time = time.time() - start_time
            target_frame_time = 0.03  # ~30fps
            sleep_time = max(0.001, target_frame_time - frame_time)
            await asyncio.sleep(sleep_time)
        except Exception as e:
            logger.error(f"Error in video feed: {e}")
            # Yield an error frame
            import numpy as np
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                error_frame,
                "Error: Video feed interrupted",
                (50, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            _, jpeg = cv2.imencode('.jpg', error_frame)
            frame_bytes = jpeg.tobytes()
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            await asyncio.sleep(0.5)  # Wait longer on error

@router.get("/video-feed")
async def video_feed(
    camera: Camera = Depends(get_camera)
):
    """
    Stream the video feed with license plate detection overlays.
    """
    if not camera:
        raise HTTPException(status_code=503, detail="Camera service not initialized")
    
    if not detection_service:
        raise HTTPException(status_code=503, detail="Detection service not initialized")
    
    return StreamingResponse(
        generate_frames(camera, detection_service),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/snapshot")
async def snapshot(
    camera: Camera = Depends(get_camera)
):
    """
    Get a single snapshot from the camera.
    """
    if not camera:
        raise HTTPException(status_code=503, detail="Camera service not initialized")
    
    try:
        # Get a JPEG frame from the camera
        jpeg_bytes, timestamp = await camera.get_jpeg_frame()
        
        return Response(
            content=jpeg_bytes,
            media_type="image/jpeg"
        )
    except Exception as e:
        logger.error(f"Error getting snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/annotated-snapshot")
async def annotated_snapshot(
    camera: Camera = Depends(get_camera)
):
    """
    Get a single snapshot from the camera with license plate detection overlays.
    """
    if not camera:
        raise HTTPException(status_code=503, detail="Camera service not initialized")
    
    if not detection_service:
        raise HTTPException(status_code=503, detail="Detection service not initialized")
    
    try:
        # Get frame from camera
        frame, timestamp = await camera.get_frame()
        
        # Process frame with detection
        processed_frame, detections = await detection_service.process_frame(frame)
        
        # Convert to JPEG
        import cv2
        _, jpeg = cv2.imencode('.jpg', processed_frame)
        
        return Response(
            content=jpeg.tobytes(),
            media_type="image/jpeg",
            headers={
                "X-Detections-Count": str(len(detections)),
                "X-Timestamp": str(timestamp)
            }
        )
    except Exception as e:
        logger.error(f"Error getting annotated snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))