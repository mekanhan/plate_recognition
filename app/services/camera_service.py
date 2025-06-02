import cv2
import asyncio
import time
import numpy as np
from fastapi import HTTPException
from typing import Optional, Dict, Any, Tuple

class CameraService:
    """
    Service for managing camera operations.
    Provides thread-safe access to camera frames.
    """
    
    def __init__(self):
        self.camera = None
        self.frame_buffer = None
        self.last_frame_time = 0
        self.frame_lock = asyncio.Lock()
        self.running = False
        self.task = None
    
    async def initialize(self, camera_id: int = 0, width: int = 1280, height: int = 720) -> None:
        """Initialize the camera service"""
        self.camera = cv2.VideoCapture(camera_id)
        
        # Set camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if not self.camera.isOpened():
            raise HTTPException(status_code=500, detail=f"Could not open camera {camera_id}")
        
        # Start frame capture loop
        self.running = True
        self.task = asyncio.create_task(self._capture_frames())
        
        print(f"Camera initialized: {width}x{height}")
    
    async def shutdown(self) -> None:
        """Shutdown the camera service"""
        self.running = False
        if self.task:
            await self.task
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        print("Camera service shutdown")
    
    async def _capture_frames(self) -> None:
        """Capture frames in a loop"""
        while self.running:
            if self.camera:
                ret, frame = self.camera.read()
                
                if ret:
                    # Update frame buffer with thread safety
                    async with self.frame_lock:
                        self.frame_buffer = frame
                        self.last_frame_time = time.time()
                
            # Small delay to prevent CPU hogging
            await asyncio.sleep(0.03)  # ~30fps
    
    async def get_frame(self) -> Tuple[np.ndarray, float]:
        """
        Get the latest frame from the camera
        
        Returns:
            Tuple[np.ndarray, float]: Frame and timestamp
        """
        async with self.frame_lock:
            if self.frame_buffer is None:
                raise HTTPException(status_code=500, detail="No frame available")
            
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