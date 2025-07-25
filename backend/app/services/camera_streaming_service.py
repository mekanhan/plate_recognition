"""
Camera Streaming Service for live video streaming from IP cameras
"""
import asyncio
import cv2
import logging
import numpy as np
from typing import Optional, AsyncGenerator, Tuple
from datetime import datetime
from dataclasses import dataclass

from app.database import Camera

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Configuration for camera streaming"""
    quality: str = "medium"  # low, medium, high
    max_fps: int = 30
    buffer_size: int = 30
    jpeg_quality: int = 80
    frame_timeout: float = 5.0


class CameraStreamingService:
    """Service for streaming video from IP cameras"""
    
    def __init__(self, camera: Camera, config: Optional[StreamConfig] = None):
        self.camera = camera
        self.config = config or StreamConfig()
        self.capture: Optional[cv2.VideoCapture] = None
        self.is_streaming = False
        self.frame_queue = asyncio.Queue(maxsize=self.config.buffer_size)
        self._streaming_task: Optional[asyncio.Task] = None
        self._frame_producer_task: Optional[asyncio.Task] = None
        
    def _build_camera_url(self) -> str:
        """Build the camera stream URL from camera configuration"""
        connection_type = self.camera.connection_type.lower()
        
        if connection_type == "http":
            protocol = "http"
        elif connection_type == "https":
            protocol = "https"
        elif connection_type == "rtsp":
            protocol = "rtsp"
        elif connection_type == "rtsps":
            protocol = "rtsps"
        else:
            # Default to http for unknown types
            protocol = "http"
        
        # Build URL with authentication if provided
        if self.camera.username and self.camera.password:
            auth = f"{self.camera.username}:{self.camera.password}@"
        else:
            auth = ""
        
        # Construct the full URL
        base_url = f"{protocol}://{auth}{self.camera.ip_address}:{self.camera.port}"
        
        if self.camera.stream_path:
            # Remove leading slash if present in stream_path
            stream_path = self.camera.stream_path.lstrip('/')
            url = f"{base_url}/{stream_path}"
        else:
            # Default paths based on connection type
            if connection_type in ["rtsp", "rtsps"]:
                url = f"{base_url}/h264Preview_01_main"  # Default RTSP path
            else:
                url = f"{base_url}/mjpeg"  # Default HTTP MJPEG path
        
        logger.info(f"Camera URL constructed: {protocol}://{self.camera.ip_address}:{self.camera.port}/{stream_path if self.camera.stream_path else ('h264Preview_01_main' if connection_type in ['rtsp', 'rtsps'] else 'mjpeg')}")
        return url
    
    async def connect_camera(self) -> bool:
        """
        Establish connection to IP camera
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            camera_url = self._build_camera_url()
            
            # Create VideoCapture in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.capture = await loop.run_in_executor(
                None, cv2.VideoCapture, camera_url
            )
            
            if not self.capture or not self.capture.isOpened():
                logger.error(f"Failed to open camera stream: {camera_url}")
                return False
            
            # Configure capture properties based on connection type
            connection_type = self.camera.connection_type.lower()
            
            if connection_type in ["rtsp", "rtsps"]:
                # RTSP-specific configuration
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer delay for real-time
                self.capture.set(cv2.CAP_PROP_FPS, self.config.max_fps)
                # Additional RTSP optimizations
                self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            else:
                # HTTP/MJPEG configuration
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer delay
                self.capture.set(cv2.CAP_PROP_FPS, self.config.max_fps)
            
            # Test reading a frame
            ret, frame = self.capture.read()
            if not ret or frame is None:
                logger.error("Failed to read test frame from camera")
                await self.disconnect_camera()
                return False
            
            logger.info(f"Successfully connected to camera {self.camera.name} at {camera_url}")
            logger.info(f"Frame size: {frame.shape[1]}x{frame.shape[0]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to camera {self.camera.name}: {str(e)}")
            await self.disconnect_camera()
            return False
    
    async def disconnect_camera(self):
        """Disconnect from camera and cleanup resources"""
        if self.capture:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.capture.release)
            except Exception as e:
                logger.error(f"Error releasing camera capture: {str(e)}")
            finally:
                self.capture = None
        
        logger.info(f"Disconnected from camera {self.camera.name}")
    
    async def _frame_producer(self):
        """Producer coroutine that captures frames and puts them in the queue"""
        frame_count = 0
        last_fps_time = datetime.now()
        
        while self.is_streaming and self.capture:
            try:
                # Read frame in executor to avoid blocking
                loop = asyncio.get_event_loop()
                ret, frame = await asyncio.wait_for(
                    loop.run_in_executor(None, self.capture.read),
                    timeout=self.config.frame_timeout
                )
                
                if not ret or frame is None:
                    logger.warning("Failed to read frame from camera")
                    await asyncio.sleep(0.1)  # Brief pause before retry
                    continue
                
                # Encode frame to JPEG
                jpeg_frame = await self._encode_frame(frame)
                if jpeg_frame:
                    # Try to put frame in queue without blocking
                    try:
                        self.frame_queue.put_nowait(jpeg_frame)
                    except asyncio.QueueFull:
                        # Queue is full, remove oldest frame and add new one
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(jpeg_frame)
                        except asyncio.QueueEmpty:
                            pass
                
                frame_count += 1
                
                # Log FPS every 100 frames
                if frame_count % 100 == 0:
                    now = datetime.now()
                    elapsed = (now - last_fps_time).total_seconds()
                    fps = 100 / elapsed if elapsed > 0 else 0
                    logger.debug(f"Camera {self.camera.name} FPS: {fps:.1f}")
                    last_fps_time = now
                
                # Control frame rate
                await asyncio.sleep(1.0 / self.config.max_fps)
                
            except asyncio.TimeoutError:
                logger.warning(f"Frame read timeout for camera {self.camera.name}")
                continue
            except Exception as e:
                logger.error(f"Error in frame producer for camera {self.camera.name}: {str(e)}")
                break
        
        logger.info(f"Frame producer stopped for camera {self.camera.name}")
    
    async def _encode_frame(self, frame: np.ndarray) -> Optional[bytes]:
        """
        Encode frame to JPEG bytes
        
        Args:
            frame: OpenCV frame (numpy array)
            
        Returns:
            JPEG encoded frame as bytes, or None if encoding failed
        """
        try:
            # Resize frame based on quality setting
            if self.config.quality == "low":
                height, width = frame.shape[:2]
                new_width = min(320, width)
                new_height = int(height * (new_width / width))
                frame = cv2.resize(frame, (new_width, new_height))
                jpeg_quality = 60
            elif self.config.quality == "medium":
                height, width = frame.shape[:2]
                new_width = min(640, width)
                new_height = int(height * (new_width / width))
                frame = cv2.resize(frame, (new_width, new_height))
                jpeg_quality = 80
            else:  # high quality
                jpeg_quality = 95
            
            # Encode to JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
            ret, jpeg_buffer = cv2.imencode('.jpg', frame, encode_params)
            
            if ret:
                return jpeg_buffer.tobytes()
            else:
                logger.warning("Failed to encode frame to JPEG")
                return None
                
        except Exception as e:
            logger.error(f"Error encoding frame: {str(e)}")
            return None
    
    async def start_streaming(self) -> AsyncGenerator[bytes, None]:
        """
        Start video streaming and yield JPEG frames
        
        Yields:
            bytes: JPEG encoded video frames
        """
        if self.is_streaming:
            logger.warning(f"Stream already active for camera {self.camera.name}")
            return
        
        # Connect to camera if not already connected
        if not self.capture:
            if not await self.connect_camera():
                raise RuntimeError(f"Failed to connect to camera {self.camera.name}")
        
        self.is_streaming = True
        
        # Start frame producer task
        self._frame_producer_task = asyncio.create_task(self._frame_producer())
        
        logger.info(f"Started streaming for camera {self.camera.name}")
        
        try:
            while self.is_streaming:
                try:
                    # Get frame from queue with timeout
                    frame_bytes = await asyncio.wait_for(
                        self.frame_queue.get(), 
                        timeout=self.config.frame_timeout
                    )
                    yield frame_bytes
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Frame timeout for camera {self.camera.name}")
                    # Check if camera is still connected
                    if not self.capture or not self.capture.isOpened():
                        logger.error(f"Camera {self.camera.name} disconnected")
                        break
                    continue
                    
                except Exception as e:
                    logger.error(f"Error in streaming loop for camera {self.camera.name}: {str(e)}")
                    break
        
        finally:
            await self.stop_streaming()
    
    async def stop_streaming(self):
        """Stop video streaming and cleanup resources"""
        if not self.is_streaming:
            return
        
        logger.info(f"Stopping stream for camera {self.camera.name}")
        
        self.is_streaming = False
        
        # Cancel frame producer task
        if self._frame_producer_task and not self._frame_producer_task.done():
            self._frame_producer_task.cancel()
            try:
                await self._frame_producer_task
            except asyncio.CancelledError:
                pass
        
        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # Disconnect camera
        await self.disconnect_camera()
        
        logger.info(f"Stream stopped for camera {self.camera.name}")
    
    async def get_current_frame(self) -> Optional[bytes]:
        """
        Get the current frame as JPEG bytes (for thumbnail generation)
        
        Returns:
            Current frame as JPEG bytes, or None if not available
        """
        if not self.capture or not self.capture.isOpened():
            if not await self.connect_camera():
                return None
        
        try:
            loop = asyncio.get_event_loop()
            ret, frame = await asyncio.wait_for(
                loop.run_in_executor(None, self.capture.read),
                timeout=self.config.frame_timeout
            )
            
            if ret and frame is not None:
                return await self._encode_frame(frame)
            
        except Exception as e:
            logger.error(f"Error getting current frame for camera {self.camera.name}: {str(e)}")
        
        return None
    
    def get_stream_info(self) -> dict:
        """Get information about the current stream"""
        return {
            "camera_id": self.camera.id,
            "camera_name": self.camera.name,
            "is_streaming": self.is_streaming,
            "queue_size": self.frame_queue.qsize(),
            "max_queue_size": self.frame_queue.maxsize,
            "config": {
                "quality": self.config.quality,
                "max_fps": self.config.max_fps,
                "jpeg_quality": self.config.jpeg_quality
            }
        }