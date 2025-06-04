from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import cv2
import asyncio
from app.services.camera_service import CameraService

from app.services.detection_service import DetectionService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# This will be initialized in the main app
camera_service = None

detection_service = None

async def get_camera_service():
    """Dependency to get the camera service"""
    return camera_service

async def get_detection_service():
    """Dependency to get the detection service"""
    return detection_service

async def generate_frames(camera: CameraService, detection_service=None):
    """Generate video frames for streaming with license plate detection"""
    while True:
        try:
            # Get raw frame from camera
            raw_frame, timestamp = await camera.get_frame()

            # Default to raw frame
            frame = raw_frame

            if detection_service:
                try:
                    # Process frame to detect license plates
                    processed_frame, detections = await detection_service.process_frame(raw_frame)
                    # Use the processed frame (with annotations)
                    frame = processed_frame
                except Exception as e:
                    print(f"Error in license plate detection: {e}")
                    # Fall back to the original frame if detection fails
                    frame = raw_frame

            # Convert the frame to JPEG
            success, jpeg_buffer = cv2.imencode('.jpg', frame)
            jpeg_bytes = jpeg_buffer.tobytes()

            # Yield the frame in multipart format
            frame_data = b'--frame\r\n'
            frame_data += b'Content-Type: image/jpeg\r\n\r\n'
            frame_data += jpeg_bytes
            frame_data += b'\r\n'
            yield frame_data

            # Slight delay to avoid overwhelming the connection
            await asyncio.sleep(0.03)  # ~30 fps
        except Exception as e:
            print(f"Error in frame generation: {e}")
            await asyncio.sleep(0.1)  # Wait a bit longer on error

@router.get("/", response_class=HTMLResponse)
async def stream_page(request: Request):
    """Stream page"""
    return templates.TemplateResponse("stream.html", {"request": request})

@router.get("/video")
async def video_feed(
    camera: CameraService = Depends(get_camera_service),
    detection_svc = Depends(get_detection_service)
):
    """Video streaming endpoint with license plate detection"""
    return StreamingResponse(
        generate_frames(camera, detection_svc),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
