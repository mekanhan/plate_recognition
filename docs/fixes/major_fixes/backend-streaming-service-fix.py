# camera_streaming_service.py - Enhanced backend streaming service with proper cleanup

from typing import Dict, Optional, Any
import asyncio
import cv2
import logging
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class StreamingService:
    """
    Enhanced streaming service with proper resource management and error handling.
    Follows industry best practices for video streaming.
    """
    
    def __init__(self):
        self.active_streams: Dict[int, 'CameraStream'] = {}
        self.stream_locks: Dict[int, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Initialize the streaming service"""
        logger.info("Starting streaming service")
        # Start periodic cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
    async def stop(self):
        """Gracefully stop the streaming service"""
        logger.info("Stopping streaming service")
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        # Stop all active streams
        stream_ids = list(self.active_streams.keys())
        for stream_id in stream_ids:
            await self.stop_stream(stream_id)
            
    async def _periodic_cleanup(self):
        """Periodically clean up stale streams"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_stale_streams()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                
    async def _cleanup_stale_streams(self):
        """Remove streams that haven't been accessed recently"""
        current_time = datetime.now()
        stale_streams = []
        
        for stream_id, stream in self.active_streams.items():
            if (current_time - stream.last_access).total_seconds() > 300:  # 5 minutes
                stale_streams.append(stream_id)
                
        for stream_id in stale_streams:
            logger.info(f"Cleaning up stale stream {stream_id}")
            await self.stop_stream(stream_id)
            
    def _get_lock(self, camera_id: int) -> asyncio.Lock:
        """Get or create a lock for a camera"""
        if camera_id not in self.stream_locks:
            self.stream_locks[camera_id] = asyncio.Lock()
        return self.stream_locks[camera_id]
        
    async def start_stream(self, camera_id: int, camera_config: dict) -> dict:
        """Start a new stream with proper error handling"""
        async with self._get_lock(camera_id):
            # Check if stream already exists
            if camera_id in self.active_streams:
                stream = self.active_streams[camera_id]
                if stream.is_active:
                    return {"status": "already_active", "camera_id": camera_id}
                else:
                    # Clean up dead stream
                    await stream.stop()
                    del self.active_streams[camera_id]
                    
            try:
                # Create new stream
                stream = CameraStream(camera_id, camera_config)
                await stream.start()
                
                self.active_streams[camera_id] = stream
                
                return {
                    "status": "started",
                    "camera_id": camera_id,
                    "stream_url": f"/stream/video/{camera_id}"
                }
                
            except Exception as e:
                logger.error(f"Failed to start stream {camera_id}: {e}")
                raise
                
    async def stop_stream(self, camera_id: int) -> dict:
        """Stop a stream and clean up resources"""
        async with self._get_lock(camera_id):
            if camera_id not in self.active_streams:
                return {"status": "not_found", "camera_id": camera_id}
                
            try:
                stream = self.active_streams[camera_id]
                await stream.stop()
                del self.active_streams[camera_id]
                
                return {"status": "stopped", "camera_id": camera_id}
                
            except Exception as e:
                logger.error(f"Error stopping stream {camera_id}: {e}")
                raise
                
    async def get_stream_frame(self, camera_id: int) -> Optional[bytes]:
        """Get the latest frame from a stream"""
        if camera_id not in self.active_streams:
            return None
            
        stream = self.active_streams[camera_id]
        return await stream.get_frame()
        
    def get_stream_status(self, camera_id: int) -> dict:
        """Get the status of a stream"""
        if camera_id not in self.active_streams:
            return {"status": "inactive", "camera_id": camera_id}
            
        stream = self.active_streams[camera_id]
        return stream.get_status()


class CameraStream:
    """
    Individual camera stream handler with proper resource management
    """
    
    def __init__(self, camera_id: int, config: dict):
        self.camera_id = camera_id
        self.config = config
        self.rtsp_url = config.get('rtsp_url')
        self.is_active = False
        self.capture: Optional[cv2.VideoCapture] = None
        self.last_frame: Optional[bytes] = None
        self.last_access = datetime.now()
        self.frame_count = 0
        self.error_count = 0
        self._capture_task: Optional[asyncio.Task] = None
        self._frame_lock = asyncio.Lock()
        
    async def start(self):
        """Start the camera stream"""
        if self.is_active:
            return
            
        logger.info(f"Starting stream for camera {self.camera_id}")
        
        # Initialize capture in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self.capture = await loop.run_in_executor(None, self._create_capture)
        
        if not self.capture or not self.capture.isOpened():
            raise Exception(f"Failed to open camera {self.camera_id}")
            
        self.is_active = True
        self._capture_task = asyncio.create_task(self._capture_frames())
        
    def _create_capture(self) -> cv2.VideoCapture:
        """Create OpenCV capture with optimized settings"""
        cap = cv2.VideoCapture(self.rtsp_url)
        
        # Set buffer size to reduce latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Set reasonable FPS
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        # Set resolution if specified
        if 'width' in self.config:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['width'])
        if 'height' in self.config:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['height'])
            
        return cap
        
    async def _capture_frames(self):
        """Continuously capture frames from the camera"""
        loop = asyncio.get_event_loop()
        
        while self.is_active:
            try:
                # Read frame in thread pool
                ret, frame = await loop.run_in_executor(None, self.capture.read)
                
                if not ret:
                    self.error_count += 1
                    if self.error_count > 10:
                        logger.error(f"Too many errors for camera {self.camera_id}")
                        self.is_active = False
                        break
                    await asyncio.sleep(0.1)
                    continue
                    
                # Reset error count on successful frame
                self.error_count = 0
                self.frame_count += 1
                
                # Encode frame
                _, buffer = cv2.imencode('.jpg', frame, [
                    cv2.IMWRITE_JPEG_QUALITY, 80,
                    cv2.IMWRITE_JPEG_OPTIMIZE, True
                ])
                
                # Update last frame
                async with self._frame_lock:
                    self.last_frame = buffer.tobytes()
                    self.last_access = datetime.now()
                    
                # Small delay to control frame rate
                await asyncio.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"Error capturing frame for camera {self.camera_id}: {e}")
                self.error_count += 1
                await asyncio.sleep(0.5)
                
    async def stop(self):
        """Stop the camera stream and clean up resources"""
        logger.info(f"Stopping stream for camera {self.camera_id}")
        
        self.is_active = False
        
        # Cancel capture task
        if self._capture_task:
            self._capture_task.cancel()
            try:
                await self._capture_task
            except asyncio.CancelledError:
                pass
                
        # Release capture in thread pool
        if self.capture:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.capture.release)
            self.capture = None
            
        self.last_frame = None
        
    async def get_frame(self) -> Optional[bytes]:
        """Get the latest frame"""
        async with self._frame_lock:
            self.last_access = datetime.now()
            return self.last_frame
            
    def get_status(self) -> dict:
        """Get stream status information"""
        return {
            "camera_id": self.camera_id,
            "status": "active" if self.is_active else "inactive",
            "frame_count": self.frame_count,
            "error_count": self.error_count,
            "last_access": self.last_access.isoformat(),
            "uptime": (datetime.now() - self.last_access).total_seconds()
        }


# FastAPI integration example
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import StreamingResponse

app = FastAPI()
streaming_service = StreamingService()

@app.on_event("startup")
async def startup_event():
    await streaming_service.start()
    
@app.on_event("shutdown")
async def shutdown_event():
    await streaming_service.stop()
    
@app.post("/api/v1/streams/start/{camera_id}")
async def start_stream(camera_id: int, camera_config: dict):
    try:
        result = await streaming_service.start_stream(camera_id, camera_config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.post("/api/v1/streams/stop/{camera_id}")
async def stop_stream(camera_id: int):
    result = await streaming_service.stop_stream(camera_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Stream not found")
    return result
    
@app.get("/api/v1/streams/status/{camera_id}")
async def get_stream_status(camera_id: int):
    return streaming_service.get_stream_status(camera_id)
    
@app.get("/stream/video/{camera_id}")
async def stream_video(camera_id: int):
    frame = await streaming_service.get_stream_frame(camera_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    return Response(content=frame, media_type="image/jpeg")
    
async def generate_mjpeg_stream(camera_id: int):
    """Generate MJPEG stream for continuous video"""
    while True:
        frame = await streaming_service.get_stream_frame(camera_id)
        if not frame:
            break
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        await asyncio.sleep(0.033)  # ~30 FPS
        
@app.get("/stream/mjpeg/{camera_id}")
async def stream_mjpeg(camera_id: int):
    return StreamingResponse(
        generate_mjpeg_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )