"""
Frame Distribution Service for single camera connection with multiple consumers

This service maintains a single RTSP connection to each camera and distributes
frames to multiple consumers (recording, detection, web streaming) without
quality loss or connection conflicts.
"""
import asyncio
import cv2
import logging
import threading
import time
import queue
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from dataclasses import dataclass

from app.database import Camera
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FrameDistributionConfig:
    """Configuration for frame distribution"""
    recording_queue_size: int = settings.FRAME_DIST_RECORDING_QUEUE_SIZE
    detection_queue_size: int = settings.FRAME_DIST_DETECTION_QUEUE_SIZE
    latest_frame_timeout: float = settings.FRAME_DIST_LATEST_FRAME_TIMEOUT
    reconnect_delay: float = settings.FRAME_DIST_RECONNECT_DELAY
    max_reconnect_attempts: int = settings.FRAME_DIST_MAX_RECONNECT_ATTEMPTS
    frame_copy_timeout: float = settings.FRAME_DIST_FRAME_COPY_TIMEOUT


class FrameConsumer:
    """Base class for frame consumers"""
    
    def __init__(self, name: str, queue_size: int = 10):
        self.name = name
        self.frame_queue = queue.Queue(maxsize=queue_size)
        self.is_active = True
        self.frames_received = 0
        self.frames_dropped = 0
    
    def put_frame(self, frame, timeout: float = 0.1) -> bool:
        """Put frame into consumer queue with timeout"""
        if not self.is_active:
            return False
            
        try:
            self.frame_queue.put(frame.copy(), timeout=timeout)
            self.frames_received += 1
            return True
        except queue.Full:
            self.frames_dropped += 1
            return False
    
    def get_frame(self, timeout: float = 1.0):
        """Get frame from consumer queue with timeout"""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics"""
        return {
            'name': self.name,
            'is_active': self.is_active,
            'queue_size': self.frame_queue.qsize(),
            'max_queue_size': self.frame_queue.maxsize,
            'frames_received': self.frames_received,
            'frames_dropped': self.frames_dropped,
            'drop_rate': self.frames_dropped / max(1, self.frames_received + self.frames_dropped)
        }


class FrameDistributor:
    """
    Single camera connection with frame distribution to multiple consumers
    
    This class maintains one RTSP connection per camera and distributes frames
    to multiple consumers without connection conflicts or quality loss.
    """
    
    def __init__(self, camera: Camera, config: Optional[FrameDistributionConfig] = None):
        self.camera = camera
        self.config = config or FrameDistributionConfig()
        
        # Connection state
        self.capture: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.shutdown_event = threading.Event()
        self.capture_thread: Optional[threading.Thread] = None
        
        # Frame distribution
        self.latest_frame = None
        self.latest_frame_time = None
        self.frame_lock = threading.Lock()
        
        # Consumers
        self.consumers: Dict[str, FrameConsumer] = {}
        
        # Statistics
        self.frames_captured = 0
        self.connection_attempts = 0
        self.last_connection_time = None
        self.consecutive_failures = 0
        
    def add_consumer(self, name: str, queue_size: int = 10) -> FrameConsumer:
        """Add a new frame consumer with connection limits"""
        # Limit maximum concurrent consumers to prevent resource exhaustion
        max_consumers = 5
        if len(self.consumers) >= max_consumers:
            logger.warning(f"Maximum consumers ({max_consumers}) reached for camera {self.camera.name}")
            # Remove oldest inactive consumer if any exist
            for consumer_name, consumer in list(self.consumers.items()):
                if not consumer.is_active:
                    logger.info(f"Removing inactive consumer '{consumer_name}' to make room")
                    del self.consumers[consumer_name]
                    break
            else:
                logger.error(f"Cannot add consumer '{name}' - too many active consumers")
                return None
        
        consumer = FrameConsumer(name, queue_size)
        self.consumers[name] = consumer
        logger.info(f"Added consumer '{name}' for camera {self.camera.name} ({len(self.consumers)} total)")
        return consumer
    
    def remove_consumer(self, name: str) -> bool:
        """Remove a frame consumer"""
        if name in self.consumers:
            self.consumers[name].is_active = False
            del self.consumers[name]
            logger.info(f"Removed consumer '{name}' for camera {self.camera.name}")
            return True
        return False
    
    def get_consumer(self, name: str) -> Optional[FrameConsumer]:
        """Get a specific consumer"""
        return self.consumers.get(name)
    
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
            protocol = "http"
        
        # Build URL with authentication if provided
        if self.camera.username and self.camera.password:
            auth = f"{self.camera.username}:{self.camera.password}@"
        else:
            auth = ""
        
        # Construct the full URL
        base_url = f"{protocol}://{auth}{self.camera.ip_address}:{self.camera.port}"
        
        if self.camera.stream_path:
            stream_path = self.camera.stream_path.lstrip('/')
            url = f"{base_url}/{stream_path}"
        else:
            # Default paths based on connection type
            if connection_type in ["rtsp", "rtsps"]:
                url = f"{base_url}/h264Preview_01_main"
            else:
                url = f"{base_url}/mjpeg"
        
        return url
    
    def _connect_camera(self) -> bool:
        """Establish connection to camera with uncompressed video support"""
        try:
            camera_url = self._build_camera_url()
            self.connection_attempts += 1
            
            logger.info(f"Connecting to camera {self.camera.name} at {camera_url} with uncompressed video support")
            
            # Create VideoCapture with FFmpeg backend for better codec support
            self.capture = cv2.VideoCapture(camera_url, cv2.CAP_FFMPEG)
            
            # Set backend-specific properties for uncompressed video
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            
            # Configure for proper color conversion to suppress YUV warnings
            self.capture.set(cv2.CAP_PROP_CONVERT_RGB, 1)  # Enable BGR conversion from YUV
            
            # Set timeouts
            self.capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10s connection timeout for stability
            self.capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 8000)  # 8s read timeout
            
            # Set format properties to ensure proper color conversion
            try:
                # Set format to ensure YUV is properly converted to BGR
                self.capture.set(cv2.CAP_PROP_FORMAT, cv2.CAP_OPENCV_MJPEG)  # MJPEG format for compatibility
                # Force color conversion for YUV streams
                self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            except Exception as format_error:
                logger.debug(f"Could not set format properties for camera {self.camera.name}: {format_error}")
                # Fallback - ensure color conversion is still enabled
                self.capture.set(cv2.CAP_PROP_CONVERT_RGB, 1)
            
            if not self.capture or not self.capture.isOpened():
                logger.error(f"Failed to open camera stream: {camera_url}")
                return False
            
            # Test frame capture with validation
            ret, frame = self.capture.read()
            if not ret or frame is None:
                logger.error(f"Failed to read test frame from camera {self.camera.name}")
                self.capture.release()
                self.capture = None
                return False
            
            # Validate frame quality (ensure it's not corrupted)
            if not self._validate_frame_quality(frame):
                logger.error(f"Test frame from camera {self.camera.name} failed quality validation")
                self.capture.release()
                self.capture = None
                return False
            
            # Get camera properties
            fps = self.capture.get(cv2.CAP_PROP_FPS)
            width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fourcc = self.capture.get(cv2.CAP_PROP_FOURCC)
            
            # Convert fourcc to readable format
            fourcc_str = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])
            
            logger.info(f"Camera {self.camera.name} connected: {int(width)}x{int(height)} @ {fps} FPS, codec: {fourcc_str}")
            logger.info(f"Frame validation passed - frame shape: {frame.shape}, dtype: {frame.dtype}")
            
            self.last_connection_time = datetime.now()
            self.consecutive_failures = 0
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to camera {self.camera.name}: {str(e)}")
            if self.capture:
                self.capture.release()
                self.capture = None
            return False
    
    def _validate_frame_quality(self, frame) -> bool:
        """Validate frame quality to detect corrupted/black frames
        
        Args:
            frame: OpenCV frame to validate
            
        Returns:
            bool: True if frame passes quality checks
        """
        if frame is None:
            return False
        
        # Check frame dimensions
        if len(frame.shape) < 2 or frame.shape[0] < 100 or frame.shape[1] < 100:
            logger.warning(f"Frame too small: {frame.shape}")
            return False
        
        # Check for completely black frames (codec corruption indicator)
        if frame.max() < 10:  # Nearly black frame
            logger.warning("Frame appears to be completely black (possible codec corruption)")
            return False
        
        # Check for reasonable pixel value distribution
        non_zero_pixels = cv2.countNonZero(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame)
        total_pixels = frame.shape[0] * frame.shape[1]
        
        if non_zero_pixels < (total_pixels * 0.1):  # Less than 10% non-zero pixels
            logger.warning(f"Frame has too few non-zero pixels: {non_zero_pixels}/{total_pixels}")
            return False
        
        return True
    
    def _disconnect_camera(self):
        """Disconnect from camera and cleanup"""
        if self.capture:
            try:
                self.capture.release()
            except Exception as e:
                logger.error(f"Error releasing camera capture: {str(e)}")
            finally:
                self.capture = None
        
        logger.info(f"Disconnected from camera {self.camera.name}")
    
    def _read_frame_with_timeout(self, timeout: float = 10.0) -> tuple:
        """
        Read frame from capture with timeout to prevent infinite blocking
        
        Enhanced with shutdown signal checking and better error handling
        
        Args:
            timeout: Maximum time to wait for frame in seconds
            
        Returns:
            Tuple of (success, frame) - same as cv2.VideoCapture.read()
        """
        if not self.capture or not self.capture.isOpened():
            return False, None
        
        # Check for shutdown signal before attempting read
        if self.shutdown_event.is_set():
            return False, None
        
        try:
            # Set shorter timeout for more responsive shutdown
            timeout_ms = int(min(timeout, 2.0) * 1000)  # Max 2 seconds per read
            self.capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_ms)
            
            # Read frame - should respect the timeout
            ret, frame = self.capture.read()
            
            # Check shutdown signal again after potentially blocking read
            if self.shutdown_event.is_set():
                return False, None
            
            return ret, frame
            
        except Exception as e:
            logger.error(f"Exception in frame read for camera {self.camera.name}: {str(e)}")
            return False, None
    
    def _capture_loop(self):
        """Main capture loop that runs in separate thread"""
        logger.info(f"Starting capture loop for camera {self.camera.name}")
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # Check for shutdown signal
                if self.shutdown_event.is_set():
                    break
                
                # Ensure camera is connected
                if not self.capture or not self.capture.isOpened():
                    if not self._connect_camera():
                        self.consecutive_failures += 1
                        delay = min(self.config.reconnect_delay * self.consecutive_failures, 30)
                        logger.warning(f"Failed to connect to camera {self.camera.name}, "
                                     f"retrying in {delay}s (attempt {self.consecutive_failures})")
                        
                        # Interruptible sleep using event.wait()
                        if self.shutdown_event.wait(timeout=delay):
                            logger.info(f"Shutdown requested during camera reconnection for {self.camera.name}")
                            break
                        continue
                
                # Read frame with timeout to prevent infinite blocking
                ret, frame = self._read_frame_with_timeout(timeout=10.0)
                
                if not ret or frame is None:
                    self.consecutive_failures += 1
                    logger.warning(f"Failed to read frame from camera {self.camera.name} "
                                 f"(failure #{self.consecutive_failures})")
                elif not self._validate_frame_quality(frame):
                    # Frame read successfully but quality is poor (likely codec corruption)
                    self.consecutive_failures += 1
                    logger.warning(f"Frame quality validation failed for camera {self.camera.name} "
                                 f"(failure #{self.consecutive_failures}) - possible codec corruption")
                    ret, frame = False, None
                    
                    # If too many consecutive failures, attempt reconnection
                    if self.consecutive_failures >= 3:  # Reduced from 5 to 3 for faster recovery
                        logger.warning(f"Too many failures for camera {self.camera.name}, reconnecting")
                        self._disconnect_camera()
                        continue
                    
                    # Check if this might be a timeout/dead connection
                    if not self.capture or not self.capture.isOpened():
                        logger.warning(f"Camera connection lost for {self.camera.name}, will reconnect")
                        self._disconnect_camera()
                        continue
                    
                    # Brief interruptible pause before retry
                    if self.shutdown_event.wait(timeout=0.1):
                        break
                    continue
                
                # Reset failure counter on successful frame
                self.consecutive_failures = 0
                self.frames_captured += 1
                
                # Distribute frame to all consumers
                self._distribute_frame(frame)
                
                # Update latest frame for web streaming
                with self.frame_lock:
                    self.latest_frame = frame.copy()
                    self.latest_frame_time = datetime.now()
                
            except Exception as e:
                logger.error(f"Error in capture loop for camera {self.camera.name}: {str(e)}")
                self._disconnect_camera()
                # Interruptible sleep before reconnection attempt
                if self.shutdown_event.wait(timeout=self.config.reconnect_delay):
                    logger.info(f"Shutdown requested during error recovery for {self.camera.name}")
                    break
        
        # Cleanup on exit
        self._disconnect_camera()
        logger.info(f"Capture loop stopped for camera {self.camera.name}")
    
    def _distribute_frame(self, frame):
        """Distribute frame to all active consumers"""
        # Create a copy of the values to avoid "dictionary changed size during iteration"
        consumers_snapshot = list(self.consumers.values())
        for consumer in consumers_snapshot:
            if consumer.is_active:
                consumer.put_frame(frame, timeout=self.config.frame_copy_timeout)
    
    def start(self) -> bool:
        """Start the frame distribution service"""
        if self.is_running:
            logger.warning(f"Frame distributor already running for camera {self.camera.name}")
            return False
        
        logger.info(f"Starting frame distributor for camera {self.camera.name}")
        
        self.is_running = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            name=f"FrameCapture-{self.camera.name}",
            daemon=True
        )
        self.capture_thread.start()
        
        return True
    
    def stop(self):
        """Stop the frame distribution service"""
        logger.info(f"Stopping frame distributor for camera {self.camera.name}")
        
        # Signal shutdown to all threads
        self.shutdown_event.set()
        self.is_running = False
        
        # Deactivate all consumers
        for consumer in self.consumers.values():
            consumer.is_active = False
        
        # Force disconnect camera to break any blocking reads
        self._disconnect_camera()
        
        # Wait for capture thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=3.0)
            if self.capture_thread.is_alive():
                logger.warning(f"Capture thread for camera {self.camera.name} did not stop gracefully, forcing termination")
        
        logger.info(f"Frame distributor stopped for camera {self.camera.name}")
    
    def get_latest_frame(self) -> Optional[bytes]:
        """Get the most recent frame for web streaming"""
        with self.frame_lock:
            if self.latest_frame is None:
                return None
            
            # Check if frame is too old
            if self.latest_frame_time:
                age = (datetime.now() - self.latest_frame_time).total_seconds()
                if age > self.config.latest_frame_timeout:
                    logger.warning(f"Latest frame for camera {self.camera.name} is {age:.1f}s old")
                    return None
            
            return self.latest_frame.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get distributor statistics"""
        with self.frame_lock:
            latest_frame_age = None
            if self.latest_frame_time:
                latest_frame_age = (datetime.now() - self.latest_frame_time).total_seconds()
        
        return {
            'camera_id': self.camera.id,
            'camera_name': self.camera.name,
            'is_running': self.is_running,
            'is_connected': self.capture is not None and self.capture.isOpened(),
            'frames_captured': self.frames_captured,
            'connection_attempts': self.connection_attempts,
            'consecutive_failures': self.consecutive_failures,
            'last_connection_time': self.last_connection_time.isoformat() if self.last_connection_time else None,
            'latest_frame_age': latest_frame_age,
            'consumers': {name: consumer.get_stats() for name, consumer in self.consumers.items()}
        }


class FrameDistributionManager:
    """
    Manages frame distributors for multiple cameras
    
    This is a singleton service that coordinates frame distribution
    across all cameras in the system.
    """
    
    def __init__(self):
        self.distributors: Dict[int, FrameDistributor] = {}
        self.config = FrameDistributionConfig()
    
    def create_distributor(self, camera: Camera, config: Optional[FrameDistributionConfig] = None) -> FrameDistributor:
        """Create and register a frame distributor for a camera"""
        if camera.id in self.distributors:
            logger.warning(f"Distributor already exists for camera {camera.id}")
            return self.distributors[camera.id]
        
        distributor = FrameDistributor(camera, config or self.config)
        self.distributors[camera.id] = distributor
        
        logger.info(f"Created frame distributor for camera {camera.name} (ID: {camera.id})")
        return distributor
    
    def get_distributor(self, camera_id: int) -> Optional[FrameDistributor]:
        """Get frame distributor for a camera"""
        return self.distributors.get(camera_id)
    
    def remove_distributor(self, camera_id: int) -> bool:
        """Remove and stop frame distributor for a camera"""
        if camera_id in self.distributors:
            distributor = self.distributors[camera_id]
            distributor.stop()
            del self.distributors[camera_id]
            logger.info(f"Removed frame distributor for camera {camera_id}")
            return True
        return False
    
    def start_all(self):
        """Start all frame distributors"""
        for distributor in self.distributors.values():
            distributor.start()
    
    def stop_all(self):
        """Stop all frame distributors"""
        for distributor in self.distributors.values():
            distributor.stop()
    
    def shutdown_all(self):
        """Forcefully shutdown all frame distributors and clean up resources"""
        logger.info(f"Force shutting down {len(self.distributors)} frame distributors")
        
        # Signal shutdown to all distributors
        for distributor in self.distributors.values():
            distributor.shutdown_event.set()
            distributor.is_running = False
        
        # Stop all distributors
        distributors_to_remove = list(self.distributors.keys())
        for camera_id in distributors_to_remove:
            try:
                self.remove_distributor(camera_id)
            except Exception as e:
                logger.error(f"Error shutting down distributor for camera {camera_id}: {e}")
        
        logger.info("All frame distributors shutdown completed")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics for all distributors"""
        return {
            'total_distributors': len(self.distributors),
            'distributors': {camera_id: distributor.get_stats() 
                           for camera_id, distributor in self.distributors.items()}
        }


# Global instance - lazy initialized to avoid startup deadlocks
_frame_distribution_manager = None

def get_frame_distribution_manager() -> FrameDistributionManager:
    """Get the global frame distribution manager with lazy initialization"""
    global _frame_distribution_manager
    if _frame_distribution_manager is None:
        _frame_distribution_manager = FrameDistributionManager()
    return _frame_distribution_manager