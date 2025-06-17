import cv2
import asyncio
import time
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
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
        self.consecutive_failures = 0
        self.camera_failed = False
        self.last_error_log = 0
        self.failure_pause_until = 0
    
    async def initialize(self, camera_id: str = "0", width: int = 1280, height: int = 720) -> None:
        """Initialize the camera service"""
        # Convert string camera_id to int if it's numeric
        try:
            camera_index = int(camera_id)
        except ValueError:
            # Assume it's a video file path or RTSP URL
            camera_index = camera_id
        
        logger.info(f"Initializing camera: {camera_id} ({width}x{height})")
        
        # Try different backends for better Windows compatibility
        backends_to_try = []
        if isinstance(camera_index, int):
            backends_to_try = [
                (camera_index, cv2.CAP_DSHOW),  # DirectShow for Windows
                (camera_index, cv2.CAP_MSMF),   # Media Foundation
                (camera_index, None)            # Default backend
            ]
        else:
            backends_to_try = [(camera_index, None)]  # For files/URLs
        
        self.camera = None
        for idx, backend in backends_to_try:
            try:
                if backend is not None:
                    self.camera = cv2.VideoCapture(idx, backend)
                else:
                    self.camera = cv2.VideoCapture(idx)
                
                if self.camera.isOpened():
                    # Set camera properties
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize lag
                    
                    # Test if camera can actually provide frames
                    ret, test_frame = self.camera.read()
                    if ret and test_frame is not None:
                        # Log actual camera properties
                        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = int(self.camera.get(cv2.CAP_PROP_FPS))
                        backend_name = "DirectShow" if backend == cv2.CAP_DSHOW else "MSMF" if backend == cv2.CAP_MSMF else "Default"
                        logger.info(f"Camera opened successfully with {backend_name}: {actual_width}x{actual_height} @ {fps}fps")
                        break
                    else:
                        logger.debug(f"Camera {camera_id} opened but cannot read frames with backend {backend}")
                        self.camera.release()
                        self.camera = None
                else:
                    logger.debug(f"Could not open camera {camera_id} with backend {backend}")
                    if self.camera:
                        self.camera.release()
                        self.camera = None
                        
            except Exception as e:
                logger.debug(f"Error opening camera {camera_id} with backend {backend}: {e}")
                if self.camera:
                    self.camera.release()
                    self.camera = None
        
        if not self.camera:
            logger.error(f"Could not open camera {camera_id} with any backend")
            logger.info("Creating test pattern fallback for development")
            # Continue initialization to provide test frames
        
        # Reset error tracking on new initialization
        self.consecutive_failures = 0
        self.camera_failed = False
        self.failure_pause_until = 0
        
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
        
        try:
            while self.running:
                current_time = time.time()
                
                # Check if we should pause due to consecutive failures
                if current_time < self.failure_pause_until:
                    frame = self._generate_test_pattern(frame_count)
                    async with self.frame_lock:
                        self.frame_buffer = frame
                        self.last_frame_time = current_time
                    
                    frame_count += 1
                    await asyncio.sleep(1.0)  # Longer sleep during pause
                    continue
                
                # Try to read from camera if available
                if self.camera and self.camera.isOpened() and not self.camera_failed:
                    try:
                        # Use timeout for camera read to prevent hanging
                        ret, frame = await asyncio.wait_for(
                            asyncio.to_thread(self.camera.read),
                            timeout=2.0
                        )
                        
                        if ret and frame is not None:
                            # Successful read - reset error count
                            self.consecutive_failures = 0
                            async with self.frame_lock:
                                self.frame_buffer = frame
                                self.last_frame_time = current_time
                        else:
                            # Failed to read frame
                            self._handle_camera_failure("Failed to read frame from camera")
                            frame = self._generate_test_pattern(frame_count)
                            async with self.frame_lock:
                                self.frame_buffer = frame
                                self.last_frame_time = current_time
                                
                    except asyncio.TimeoutError:
                        self._handle_camera_failure("Camera read timeout")
                        frame = self._generate_test_pattern(frame_count)
                        async with self.frame_lock:
                            self.frame_buffer = frame
                            self.last_frame_time = current_time
                            
                    except Exception as e:
                        self._handle_camera_failure(f"Camera read error: {e}")
                        frame = self._generate_test_pattern(frame_count)
                        async with self.frame_lock:
                            self.frame_buffer = frame
                            self.last_frame_time = current_time
                else:
                    # No camera available or camera failed - generate test pattern
                    frame = self._generate_test_pattern(frame_count)
                    async with self.frame_lock:
                        self.frame_buffer = frame
                        self.last_frame_time = current_time
                
                frame_count += 1
                
                # Adaptive sleep based on camera state
                if self.camera_failed or not self.camera:
                    await asyncio.sleep(0.1)  # Slower when using test pattern
                else:
                    await asyncio.sleep(0.03)  # ~30fps for real camera
                    
        except asyncio.CancelledError:
            logger.info("Camera capture loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in camera capture loop: {e}")
        finally:
            logger.info("Camera capture loop ended")
    
    def _handle_camera_failure(self, message: str):
        """Handle camera failure with circuit breaker pattern"""
        self.consecutive_failures += 1
        current_time = time.time()
        
        # Log errors but limit frequency to prevent log flooding
        if current_time - self.last_error_log > 10.0:  # Log at most every 10 seconds
            logger.warning(f"{message} (failure #{self.consecutive_failures})")
            self.last_error_log = current_time
        
        # Circuit breaker: pause camera reads after too many failures
        if self.consecutive_failures >= 50:
            self.failure_pause_until = current_time + 30.0  # Pause for 30 seconds
            if not self.camera_failed:
                logger.error(f"Camera failed after {self.consecutive_failures} attempts. Pausing for 30 seconds.")
            self.consecutive_failures = 0  # Reset for next attempt
        
        # Mark camera as permanently failed after extreme failures
        if self.consecutive_failures >= 100:
            self.camera_failed = True
            logger.error("Camera marked as permanently failed. Using test pattern only.")
    
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
    
    @staticmethod
    def detect_available_cameras(max_cameras: int = 10) -> List[Dict[str, Any]]:
        """
        Detect all available cameras on the system
        
        Args:
            max_cameras: Maximum number of camera indices to check
            
        Returns:
            List of dictionaries with camera information
        """
        available_cameras = []
        
        logger.info(f"Scanning for available cameras (0-{max_cameras-1})")
        
        for camera_id in range(max_cameras):
            cap = None
            try:
                # Try different backends for better compatibility
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)  # DirectShow for Windows
                
                if not cap.isOpened():
                    cap.release()
                    cap = cv2.VideoCapture(camera_id)  # Fallback to default
                
                if cap.isOpened():
                    # Set a short timeout to avoid hanging
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    # Get camera properties
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    
                    # Fix default resolution if camera returns 0
                    if width == 0 or height == 0:
                        width, height = 640, 480
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    
                    # Try to read a frame with timeout
                    is_working = False
                    try:
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            is_working = True
                    except Exception as e:
                        logger.debug(f"Camera {camera_id} frame read failed: {e}")
                    
                    camera_info = {
                        "id": str(camera_id),
                        "name": f"Camera {camera_id}",
                        "description": f"USB/Built-in Camera {camera_id}",
                        "resolution": f"{width}x{height}",
                        "fps": fps if fps > 0 else 30,
                        "is_working": is_working,
                        "type": "usb"
                    }
                    
                    available_cameras.append(camera_info)
                    status = "Working" if is_working else "Not Available"
                    logger.info(f"Found camera {camera_id}: {width}x{height} @ {fps}fps, Status: {status}")
                    
            except Exception as e:
                logger.debug(f"Error checking camera {camera_id}: {e}")
            finally:
                if cap:
                    cap.release()
        
        # Add common IP camera and file options
        available_cameras.extend([
            {
                "id": "ip",
                "name": "IP Camera",
                "description": "Network IP Camera (RTSP/HTTP)",
                "resolution": "Variable",
                "fps": "Variable", 
                "is_working": None,  # Cannot test without URL
                "type": "ip"
            },
            {
                "id": "file",
                "name": "Video File",
                "description": "Local video file playback",
                "resolution": "Variable",
                "fps": "Variable",
                "is_working": None,  # Cannot test without file path
                "type": "file"
            }
        ])
        
        working_cameras = len([c for c in available_cameras if c['type'] == 'usb' and c['is_working']])
        total_cameras = len([c for c in available_cameras if c['type'] == 'usb'])
        logger.info(f"Camera detection complete. Found {working_cameras}/{total_cameras} working USB cameras")
        return available_cameras