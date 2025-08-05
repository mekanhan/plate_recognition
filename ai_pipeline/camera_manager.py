"""
Camera Manager - Handles all camera connections
IMPORTANT: This captures from IP cameras locally, does NOT stream to browsers
"""
import cv2
import threading
import queue
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, List
import numpy as np

@dataclass
class CameraConfig:
    """Camera configuration"""
    camera_id: str
    name: str
    ip_address: str
    username: str
    password: str
    port: int = 554
    stream_path: str = "/stream"
    protocol: str = "rtsp"
    location: str = ""
    
    @property
    def stream_url(self) -> str:
        """Build RTSP URL - NEVER send this to browser!"""
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.ip_address}:{self.port}{self.stream_path}"

class CameraStream:
    """
    Handles individual camera connection
    Captures frames for AI processing - NOT for browser streaming!
    """
    
    def __init__(self, config: CameraConfig, buffer_size: int = 30):
        self.config = config
        self.frame_buffer = queue.Queue(maxsize=buffer_size)
        self.is_running = False
        self.capture = None
        self.capture_thread = None
        self.last_frame = None
        self.last_frame_time = 0
        self.error_count = 0
        self.logger = logging.getLogger(f"Camera.{config.camera_id}")
        
    def start(self):
        """Start capturing frames for AI processing"""
        if not self.is_running:
            self.is_running = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                name=f"Camera-{self.config.camera_id}"
            )
            self.capture_thread.daemon = True
            self.capture_thread.start()
            self.logger.info(f"Started capture: {self.config.name}")
    
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=5.0)
        if self.capture:
            self.capture.release()
        self.logger.info(f"Stopped capture: {self.config.name}")
            
    def _capture_loop(self):
        """
        Main capture loop - Gets frames for AI processing
        This is NOT for streaming to browsers!
        """
        reconnect_delay = 5
        
        while self.is_running:
            try:
                if not self._connect():
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 1.5, 60)
                    continue
                
                reconnect_delay = 5  # Reset on successful connect
                self.error_count = 0
                
                while self.is_running and self.capture.isOpened():
                    ret, frame = self.capture.read()
                    
                    if not ret or frame is None:
                        self.logger.warning("Failed to read frame")
                        break
                    
                    # Store for AI processing
                    self.last_frame = frame.copy()
                    self.last_frame_time = time.time()
                    
                    # Buffer for processing
                    try:
                        self.frame_buffer.put_nowait(frame)
                    except queue.Full:
                        # Drop old frame
                        try:
                            self.frame_buffer.get_nowait()
                            self.frame_buffer.put_nowait(frame)
                        except queue.Empty:
                            pass
                            
            except Exception as e:
                self.logger.error(f"Capture error: {e}")
                self.error_count += 1
                
            finally:
                if self.capture:
                    self.capture.release()
                    self.capture = None
                
    def _connect(self) -> bool:
        """Connect to camera via RTSP"""
        try:
            self.logger.info(f"Connecting to {self.config.stream_url}")
            
            # IMPORTANT: This is local network connection only!
            # For RTSP, use proper transport options
            if self.config.protocol == "rtsp":
                # Set RTSP transport options via OpenCV
                import os
                os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp'
                
            self.capture = cv2.VideoCapture(self.config.stream_url)
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Set reasonable timeouts for RTSP
            if self.config.protocol == "rtsp":
                self.capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10 seconds
                self.capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)  # 10 seconds
            
            if not self.capture.isOpened():
                raise Exception("Failed to open stream")
                
            # Test read with timeout
            ret, frame = self.capture.read()
            if not ret or frame is None:
                raise Exception("Failed to read test frame")
            
            self.logger.info("Successfully connected to camera")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            if self.capture:
                self.capture.release()
                self.capture = None
            return False
        finally:
            # Clean up environment variables
            if 'OPENCV_FFMPEG_CAPTURE_OPTIONS' in os.environ:
                del os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS']
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get frame for AI processing (not for browser!)"""
        try:
            return self.frame_buffer.get_nowait()
        except queue.Empty:
            return self.last_frame.copy() if self.last_frame is not None else None
    
    def get_snapshot(self) -> Optional[np.ndarray]:
        """Get single snapshot for browser display"""
        return self.last_frame.copy() if self.last_frame is not None else None
    
    def is_healthy(self) -> bool:
        """Check if camera stream is healthy"""
        if not self.is_running or not self.capture:
            return False
        
        # Check if we've received frames recently
        if time.time() - self.last_frame_time > 10:
            return False
        
        return self.error_count < 5

class CameraManager:
    """Manages all camera streams for AI processing"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        self.logger = logging.getLogger("CameraManager")
        
    def add_camera(self, config: CameraConfig) -> bool:
        """Add camera for AI processing"""
        if config.camera_id in self.cameras:
            self.logger.warning(f"Camera {config.camera_id} already exists")
            return False
            
        camera = CameraStream(config)
        camera.start()
        self.cameras[config.camera_id] = camera
        return True
        
    def remove_camera(self, camera_id: str):
        """Stop and remove a camera"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
    
    def get_camera(self, camera_id: str) -> Optional[CameraStream]:
        return self.cameras.get(camera_id)
        
    def get_all_cameras(self) -> Dict[str, CameraStream]:
        return self.cameras
        
    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()