import cv2
import asyncio
import time
import numpy as np
from typing import Optional, Dict, Any, Tuple
import logging
from app.interfaces.camera import Camera  # Import the Camera interface

logger = logging.getLogger(__name__)

class CameraService(Camera):  # Implement the Camera interface
    """
    Service for managing camera operations.
    """
    
    def __init__(self):
        self.camera = None
        self.frame_buffer = None
        self.last_frame_time = 0
        self.frame_lock = asyncio.Lock()
        self.running = False
        self.task = None
    
    async def initialize(self, camera_id: str = "0", width: int = 1280, height: int = 720) -> None:
        """Initialize the camera service"""
        # Convert string camera_id to int if it's numeric
        try:
            camera_index = int(camera_id)
        except ValueError:
            # Assume it's a video file path or RTSP URL
            camera_index = camera_id
        
        logger.info(f"Initializing camera: {camera_id} ({width}x{height})")
        
        self.camera = cv2.VideoCapture(camera_index)
        
        # Set camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if not self.camera.isOpened():
            logger.error(f"Could not open camera {camera_id}")
            logger.info("Creating test pattern fallback for development")
            self.camera = None
            # Continue initialization to provide test frames
        else:
            # Log actual camera properties
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.camera.get(cv2.CAP_PROP_FPS))
            logger.info(f"Camera opened successfully: {actual_width}x{actual_height} @ {fps}fps")
        
        # Start frame capture loop
        self.running = True
        self.task = asyncio.create_task(self._capture_frames())
        
        logger.info("Camera service started")
    
    async def shutdown(self) -> None:
        """Shutdown the camera service"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        logger.info("Camera service shutdown")
    
    async def _capture_frames(self) -> None:
        """Capture frames in a loop"""
        frame_count = 0
        
        while self.running:
            if self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                
                if ret:
                    # Update frame buffer with thread safety
                    async with self.frame_lock:
                        self.frame_buffer = frame
                        self.last_frame_time = time.time()
                else:
                    logger.warning("Failed to read frame from camera")
                    # Generate test pattern on read failure
                    frame = self._generate_test_pattern(frame_count)
                    async with self.frame_lock:
                        self.frame_buffer = frame
                        self.last_frame_time = time.time()
            else:
                # No camera available - generate test pattern
                frame = self._generate_test_pattern(frame_count)
                async with self.frame_lock:
                    self.frame_buffer = frame
                    self.last_frame_time = time.time()
            
            frame_count += 1
            # Small delay to prevent CPU hogging
            await asyncio.sleep(0.03)  # ~30fps
    
    def _generate_test_pattern(self, frame_count: int) -> np.ndarray:
        """Generate a test pattern frame for development/testing"""
        # Create a 640x480 test frame
        height, width = 480, 640
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add gradient background
        frame[:, :, 0] = np.linspace(0, 100, width, dtype=np.uint8)  # Blue gradient
        frame[:, :, 1] = 50  # Green
        frame[:, :, 2] = np.linspace(100, 200, height, dtype=np.uint8).reshape(-1, 1)  # Red gradient
        
        # Add timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"TEST PATTERN", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, timestamp, (50, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame: {frame_count}", (50, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add mock license plate for testing
        plate_x, plate_y = 200, 300
        plate_w, plate_h = 200, 60
        cv2.rectangle(frame, (plate_x, plate_y), (plate_x + plate_w, plate_y + plate_h), (255, 255, 255), -1)
        cv2.rectangle(frame, (plate_x, plate_y), (plate_x + plate_w, plate_y + plate_h), (0, 0, 0), 2)
        cv2.putText(frame, "ABC 123", (plate_x + 30, plate_y + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        return frame
    
    async def get_frame(self) -> Tuple[np.ndarray, float]:
        """
        Get the latest frame from the camera
        
        Returns:
            Tuple[np.ndarray, float]: Frame and timestamp
        """
        async with self.frame_lock:
            if self.frame_buffer is None:
                # Return a black frame if no frame is available
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                return frame, time.time()
            # Return a copy to prevent modification of the buffer
            return self.frame_buffer.copy(), self.last_frame_time
    
    async def get_jpeg_frame(self) -> Tuple[bytes, float]:
        """
        Get the latest frame as JPEG bytes
        
        Returns:
            Tuple[bytes, float]: JPEG encoded frame and timestamp
        """
        frame, timestamp = await self.get_frame()
        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes(), timestamp