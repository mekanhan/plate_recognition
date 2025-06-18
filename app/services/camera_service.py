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
        # First, reset any previous failure state
        self.consecutive_failures = 0
        self.camera_failed = False
        self.failure_pause_until = 0
        self.last_error_log = 0
        
        # Clean up any existing camera connection
        if self.camera:
            logger.info("Cleaning up existing camera connection...")
            self.camera.release()
            self.camera = None
        
        # Convert string camera_id to int if it's numeric
        try:
            camera_index = int(camera_id)
        except ValueError:
            # Assume it's a video file path or RTSP URL
            camera_index = camera_id
        
        logger.info(f"Initializing camera: {camera_id} ({width}x{height}) - Failure state reset")
        
        # Clean up any existing camera connection
        if self.camera:
            try:
                self.camera.release()
            except Exception:
                pass
            self.camera = None
        
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
                    
                    # For Windows laptops, try different buffer sizes
                    if backend == cv2.CAP_DSHOW:
                        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Slightly larger buffer for DirectShow
                    else:
                        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize lag for other backends
                    
                    # Set additional properties for better Windows compatibility
                    # Force FPS setting - some cameras need this set after resolution
                    if backend == cv2.CAP_DSHOW:
                        # For DirectShow, set properties in specific order for Windows laptops
                        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Use MJPEG format first
                        self.camera.set(cv2.CAP_PROP_FPS, 30)  # Then set FPS
                        # Some Windows laptop cameras need these additional settings
                        self.camera.set(cv2.CAP_PROP_FRAME_COUNT, -1)  # Infinite frames
                        self.camera.set(cv2.CAP_PROP_CONVERT_RGB, 1)  # Ensure RGB conversion
                    else:
                        self.camera.set(cv2.CAP_PROP_FPS, 30)  # Set FPS for other backends
                    
                    # Test if camera can actually provide frames
                    ret, test_frame = self.camera.read()
                    if ret and test_frame is not None:
                        # Log actual camera properties
                        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = int(self.camera.get(cv2.CAP_PROP_FPS))
                        buffer_size = int(self.camera.get(cv2.CAP_PROP_BUFFERSIZE))
                        fourcc = int(self.camera.get(cv2.CAP_PROP_FOURCC))
                        backend_name = "DirectShow" if backend == cv2.CAP_DSHOW else "MSMF" if backend == cv2.CAP_MSMF else "Default"
                        
                        logger.info(f"Camera opened successfully with {backend_name}: {actual_width}x{actual_height} @ {fps}fps")
                        logger.info(f"Camera buffer size: {buffer_size}, FOURCC: {fourcc}")
                        logger.info(f"Test frame shape: {test_frame.shape}")
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
                
                # Auto-recovery: if pause period expired, try to reset failure state
                if (self.failure_pause_until > 0 and current_time >= self.failure_pause_until) or \
                   (self.camera_failed and current_time >= self.failure_pause_until):
                    logger.info("Failure pause period expired, attempting camera recovery...")
                    self.failure_pause_until = 0
                    self.camera_failed = False
                    self.consecutive_failures = max(0, self.consecutive_failures - 25)  # Reduce failure count
                    logger.info("Camera failure state reset for recovery attempt")
                    # Try to reconnect in background
                    asyncio.create_task(self._attempt_camera_reconnection())
                
                # Try to read from camera if available
                if self.camera and self.camera.isOpened() and not self.camera_failed:
                    try:
                        # Use timeout for camera read to prevent hanging
                        # For Windows laptops, sometimes multiple reads help clear buffer
                        ret, frame = await asyncio.wait_for(
                            asyncio.to_thread(self._read_frame_with_buffer_clear),
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
                    # For Windows laptop cameras, slightly slower frame rate reduces errors
                    await asyncio.sleep(0.05)  # ~20fps to reduce Windows camera issues
                    
        except asyncio.CancelledError:
            logger.info("Camera capture loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in camera capture loop: {e}")
        finally:
            logger.info("Camera capture loop ended")
    
    def _read_frame_with_buffer_clear(self):
        """Read frame with buffer clearing for Windows laptops"""
        if not self.camera or not self.camera.isOpened():
            return False, None
        
        # For Windows laptops, especially DirectShow cameras, use improved reading strategy
        try:
            # Method 1: Try grab/retrieve (good for DirectShow cameras with buffering issues)
            if self.camera.grab():
                ret, frame = self.camera.retrieve()
                if ret and frame is not None and frame.size > 0:
                    return ret, frame
            
            # Method 2: Fallback to regular read
            ret, frame = self.camera.read()
            if ret and frame is not None and frame.size > 0:
                return ret, frame
            
            # Method 3: Multiple read attempts for stubborn cameras
            for attempt in range(3):
                ret, frame = self.camera.read()
                if ret and frame is not None and frame.size > 0:
                    return ret, frame
                
            return False, None
            
        except Exception as e:
            logger.debug(f"Error in frame read with buffer clear: {e}")
            # Final fallback
            try:
                return self.camera.read()
            except Exception:
                return False, None

    def _handle_camera_failure(self, message: str):
        """Handle camera failure with circuit breaker pattern"""
        self.consecutive_failures += 1
        current_time = time.time()
        
        # Log errors but limit frequency to prevent log flooding
        if current_time - self.last_error_log > 10.0:  # Log at most every 10 seconds
            logger.warning(f"{message} (failure #{self.consecutive_failures})")
            self.last_error_log = current_time
        
        # For Windows laptops: try reconnecting after moderate failures
        if self.consecutive_failures == 25:
            logger.info("Attempting camera reconnection due to streaming failures...")
            asyncio.create_task(self._attempt_camera_reconnection())
        
        # Circuit breaker: pause camera reads after too many failures (increased threshold)
        if self.consecutive_failures >= 75:  # Increased from 50 to be less aggressive
            self.failure_pause_until = current_time + 30.0  # Pause for 30 seconds
            if not self.camera_failed:
                logger.warning(f"Camera experiencing issues after {self.consecutive_failures} attempts. Pausing for 30 seconds.")
            self.consecutive_failures = 0  # Reset for next attempt
        
        # Mark camera as failed after extreme failures (but don't make it permanent)
        if self.consecutive_failures >= 150:  # Increased threshold and made it recoverable
            self.camera_failed = True
            self.failure_pause_until = current_time + 60.0  # Longer pause
            logger.error(f"Camera marked as failed after {self.consecutive_failures} attempts. Pausing for 60 seconds before retry.")
            self.consecutive_failures = 0  # Reset to allow eventual recovery
    
    async def _attempt_camera_reconnection(self):
        """Attempt to reconnect camera when streaming fails"""
        try:
            logger.info("Attempting camera reconnection...")
            
            # Stop current capture loop if running  
            was_running = self.running
            if self.running:
                self.running = False
                if self.task:
                    self.task.cancel()
                    try:
                        await self.task
                    except asyncio.CancelledError:
                        pass
            
            # Release current camera connection
            if self.camera:
                logger.info("Releasing current camera connection...")
                self.camera.release()
                self.camera = None
                await asyncio.sleep(2.0)  # Give camera time to release
            
            # Try to reinitialize with the same settings
            logger.info("Reinitializing camera after reconnection...")
            await self.initialize("0", 1280, 720)  # Use default settings
            
            logger.info("Camera reconnection completed successfully")
                
        except Exception as e:
            logger.error(f"Camera reconnection failed: {e}")
    
    async def reset_failure_state(self):
        """Reset camera failure state to allow recovery"""
        logger.info("Resetting camera failure state...")
        self.consecutive_failures = 0
        self.camera_failed = False
        self.failure_pause_until = 0
        self.last_error_log = 0
        logger.info("Camera failure state reset - ready to retry camera operations")
    
    async def is_showing_test_pattern(self) -> bool:
        """Check if the current frame is a test pattern (not real camera feed)"""
        try:
            frame, _ = await self.get_frame()
            if frame is None or frame.size == 0:
                return True
            
            # Check if frame dimensions match test pattern (640x480)
            height, width = frame.shape[:2]
            if height == 480 and width == 640:
                # Additional check: look for "TEST PATTERN" text in the frame
                # Convert frame to grayscale for text detection
                import cv2
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Check a specific region where "TEST PATTERN" text appears
                # In test pattern, this text is at coordinates (50, 100)
                text_region = gray[80:120, 40:250]  # Region around the text
                
                # If the region has significant contrast (text), it's likely a test pattern
                if text_region.std() > 20:  # Standard deviation indicates text presence
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking test pattern: {e}")
            return True  # Assume test pattern if we can't check
    
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
        
        # Try different backends in order of preference for Windows
        backends_to_try = [
            ("DirectShow", cv2.CAP_DSHOW),
            ("Media Foundation", cv2.CAP_MSMF),
            ("Default", None)
        ]
        
        for camera_id in range(max_cameras):
            camera_found = False
            best_camera_info = None
            
            for backend_name, backend in backends_to_try:
                if camera_found:
                    break
                    
                cap = None
                try:
                    # Try to open camera with specific backend
                    if backend is not None:
                        cap = cv2.VideoCapture(camera_id, backend)
                    else:
                        cap = cv2.VideoCapture(camera_id)
                    
                    if cap.isOpened():
                        # Set timeout and buffer size
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # Try to set a common resolution first
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        
                        # For DirectShow cameras, set additional properties early
                        if backend == cv2.CAP_DSHOW:
                            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                            cap.set(cv2.CAP_PROP_FPS, 30)
                            cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
                        
                        # Get camera properties
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = int(cap.get(cv2.CAP_PROP_FPS))
                        
                        # Get additional device capabilities
                        device_capabilities = CameraService._get_device_capabilities(cap, backend)
                        
                        # Fix default resolution if camera returns 0
                        if width == 0 or height == 0:
                            width, height = 640, 480
                            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        
                        # Fix FPS if it's 0 (common Windows laptop camera issue)
                        if fps == 0:
                            cap.set(cv2.CAP_PROP_FPS, 30)
                            fps = 30  # Assume 30fps for display purposes
                        
                        # Try to read frames to verify camera is working and capture fingerprint
                        is_working = False
                        frame_read_error = None
                        frame_fingerprint = None
                        
                        try:
                            # Read multiple frames to get a stable sample
                            sample_frames = []
                            for attempt in range(3):
                                ret, frame = cap.read()
                                if ret and frame is not None and frame.size > 0:
                                    sample_frames.append(frame)
                                    is_working = True
                                else:
                                    break
                            
                            if is_working and sample_frames:
                                # Create fingerprint from the last frame
                                logger.info(f"Creating fingerprint for camera {camera_id} from {len(sample_frames)} sample frames")
                                try:
                                    frame_fingerprint = CameraService._create_frame_fingerprint(sample_frames[-1])
                                    logger.info(f"Camera {camera_id} fingerprint: {frame_fingerprint}")
                                except Exception as fp_error:
                                    logger.error(f"Fingerprint creation failed for camera {camera_id}: {fp_error}")
                                    frame_fingerprint = None
                                logger.info(f"Camera {camera_id} working with {backend_name}: {width}x{height} @ {fps}fps")
                            else:
                                frame_read_error = "Frame read returned False or empty frame"
                                
                        except Exception as e:
                            frame_read_error = str(e)
                            logger.error(f"Camera {camera_id} frame read failed with {backend_name}: {e}")
                        
                        # Determine camera description with more details
                        if camera_id == 0:
                            description = f"Built-in/Primary Camera ({backend_name})"
                        else:
                            description = f"USB/External Camera {camera_id} ({backend_name})"
                        
                        # Add resolution and format info to description if available
                        if width > 0 and height > 0:
                            description += f" - {width}x{height}"
                        
                        # Add format info if available
                        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC)) if cap else 0
                        if fourcc > 0:
                            try:
                                fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4) if (fourcc >> 8 * i) & 0xFF != 0])
                                if fourcc_str:
                                    description += f" [{fourcc_str}]"
                            except:
                                pass
                        
                        camera_info = {
                            "id": str(camera_id),
                            "name": description,  # Use the detailed description as the name
                            "description": description,
                            "resolution": f"{width}x{height}",
                            "fps": fps if fps > 0 else 30,
                            "is_working": is_working,
                            "type": "usb",
                            "backend": backend_name,
                            "error": frame_read_error if not is_working else None,
                            "frame_fingerprint": frame_fingerprint,
                            "capabilities": device_capabilities
                        }
                        
                        # If this is the first working camera we found for this ID, or if it's working, keep it
                        if best_camera_info is None or is_working:
                            best_camera_info = camera_info
                            
                        # If the camera is working, we found a good one
                        if is_working:
                            camera_found = True
                            
                except Exception as e:
                    logger.debug(f"Error checking camera {camera_id} with {backend_name}: {e}")
                finally:
                    if cap:
                        cap.release()
            
            # Add the best camera info we found for this ID (even if not working)
            if best_camera_info:
                available_cameras.append(best_camera_info)
                status = "Working" if best_camera_info["is_working"] else f"Not Available ({best_camera_info.get('error', 'Unknown error')})"
                logger.info(f"Camera {camera_id}: {status}")
        
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
        
        # Detect and mark duplicate cameras
        logger.info(f"Before duplicate detection: {len(available_cameras)} cameras")
        available_cameras = CameraService._detect_duplicate_cameras(available_cameras)
        logger.info(f"After duplicate detection: {len(available_cameras)} cameras")
        
        return available_cameras
    
    @staticmethod
    async def get_cached_cameras(force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get cameras using cache for performance optimization
        
        Args:
            force_refresh: If True, bypass cache and scan immediately
            
        Returns:
            Camera detection results with cache metadata
        """
        from app.services.camera_cache_service import camera_cache
        return await camera_cache.get_cameras(force_refresh=force_refresh)
    
    @staticmethod
    async def refresh_camera_cache() -> Dict[str, Any]:
        """
        Trigger cache refresh and return current results immediately
        
        Returns:
            Current cache results with background refresh initiated
        """
        from app.services.camera_cache_service import camera_cache
        return await camera_cache.refresh_cache_async()
    
    @staticmethod
    def get_cache_status() -> Dict[str, Any]:
        """Get current camera cache status"""
        from app.services.camera_cache_service import camera_cache
        return camera_cache.get_cache_info()
    
    @staticmethod
    def invalidate_camera_cache():
        """Force invalidation of camera cache"""
        from app.services.camera_cache_service import camera_cache
        camera_cache.invalidate_cache()
    
    @staticmethod
    def _create_frame_fingerprint(frame: np.ndarray) -> str:
        """Create a unique fingerprint from a camera frame for duplicate detection"""
        import hashlib
        
        if frame is None or frame.size == 0:
            return None
            
        try:
            # Resize frame to small size for consistent comparison
            small_frame = cv2.resize(frame, (64, 48))
            
            # Convert to grayscale to reduce noise from lighting variations
            gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            # Apply slight blur to reduce noise
            blurred = cv2.GaussianBlur(gray_frame, (3, 3), 0)
            
            # Create hash of the frame content
            frame_bytes = blurred.tobytes()
            fingerprint = hashlib.md5(frame_bytes).hexdigest()[:16]  # Short hash
            
            return fingerprint
            
        except Exception as e:
            logger.error(f"Error creating frame fingerprint: {e}")
            import traceback
            logger.debug(f"Fingerprint error traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def _detect_duplicate_cameras(cameras: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect cameras that might be the same device with different indices"""
        usb_cameras = [c for c in cameras if c['type'] == 'usb' and c['is_working']]
        logger.info(f"Analyzing {len(usb_cameras)} working USB cameras for duplicates")
        
        # Group cameras by fingerprint
        fingerprint_groups = {}
        for camera in usb_cameras:
            fingerprint = camera.get('frame_fingerprint')
            logger.info(f"Camera {camera['id']} fingerprint: {fingerprint}")
            if fingerprint:
                if fingerprint not in fingerprint_groups:
                    fingerprint_groups[fingerprint] = []
                fingerprint_groups[fingerprint].append(camera)
        
        logger.info(f"Found {len(fingerprint_groups)} unique fingerprint groups")
        
        # Mark duplicates
        for camera in cameras:
            if camera['type'] == 'usb' and camera['is_working']:
                fingerprint = camera.get('frame_fingerprint')
                if fingerprint and fingerprint in fingerprint_groups:
                    group = fingerprint_groups[fingerprint]
                    if len(group) > 1:
                        # Mark as potential duplicate
                        camera['is_duplicate'] = True
                        camera['duplicate_group'] = fingerprint
                        camera['duplicate_count'] = len(group)
                        
                        # Update description to indicate duplicate
                        primary_id = min(int(c['id']) for c in group)
                        if int(camera['id']) == primary_id:
                            camera['description'] += " (Primary)"
                        else:
                            camera['description'] += f" (Duplicate of Camera {primary_id})"
                        
                        logger.info(f"Camera {camera['id']} marked as duplicate (group: {fingerprint})")
                    else:
                        camera['is_duplicate'] = False
                else:
                    camera['is_duplicate'] = False
            else:
                camera['is_duplicate'] = False
        
        return cameras
    
    @staticmethod
    def _get_device_capabilities(cap, backend) -> Dict[str, Any]:
        """Extract device capabilities and metadata from camera"""
        capabilities = {
            "backend": backend,
            "supported_formats": [],
            "device_properties": {},
            "auto_features": {}
        }
        
        if not cap or not cap.isOpened():
            return capabilities
            
        try:
            # Get basic device properties
            properties = {
                "brightness": cap.get(cv2.CAP_PROP_BRIGHTNESS),
                "contrast": cap.get(cv2.CAP_PROP_CONTRAST),
                "saturation": cap.get(cv2.CAP_PROP_SATURATION),
                "hue": cap.get(cv2.CAP_PROP_HUE),
                "gain": cap.get(cv2.CAP_PROP_GAIN),
                "exposure": cap.get(cv2.CAP_PROP_EXPOSURE),
                "buffer_size": cap.get(cv2.CAP_PROP_BUFFERSIZE),
                "fourcc": cap.get(cv2.CAP_PROP_FOURCC)
            }
            
            # Filter out -1 values (unsupported properties)
            capabilities["device_properties"] = {k: v for k, v in properties.items() if v != -1}
            
            # Check auto features
            auto_features = {
                "auto_exposure": cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
                "autofocus": cap.get(cv2.CAP_PROP_AUTOFOCUS) if hasattr(cv2, 'CAP_PROP_AUTOFOCUS') else -1,
                "auto_wb": cap.get(cv2.CAP_PROP_AUTO_WB) if hasattr(cv2, 'CAP_PROP_AUTO_WB') else -1
            }
            
            capabilities["auto_features"] = {k: v for k, v in auto_features.items() if v != -1}
            
            # Try to determine FOURCC format
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            if fourcc > 0:
                # Convert FOURCC to readable format
                fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
                capabilities["current_format"] = fourcc_str
            
        except Exception as e:
            logger.debug(f"Error getting device capabilities: {e}")
            
        return capabilities