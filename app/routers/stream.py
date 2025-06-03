from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import cv2
import asyncio
from app.services.camera_service import CameraService
from app.dependencies.camera import get_camera_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# This will be initialized in the main app if run directly

async def generate_frames(camera: CameraService):
    """Generate video frames for streaming"""
    while True:
        # Get a frame from the camera
        jpeg_bytes, _ = await camera.get_jpeg_frame()

        # Yield the frame in multipart format
        frame_data = b'--frame\r\n'
        frame_data += b'Content-Type: image/jpeg\r\n\r\n'
        frame_data += jpeg_bytes
        frame_data += b'\r\n'
        yield frame_data
        # Slight delay to avoid overwhelming the connection
        await asyncio.sleep(0.03)  # ~30 fps

@router.get("/", response_class=HTMLResponse)
async def stream_page(request: Request):
    """Stream page"""
    return templates.TemplateResponse("stream.html", {"request": request})

@router.get("/video")
async def video_feed(camera: CameraService = Depends(get_camera_service)):
    """Video streaming endpoint"""
    return StreamingResponse(
        generate_frames(camera),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

