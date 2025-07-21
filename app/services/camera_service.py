import cv2
import asyncio
import time
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
import logging
import threading
import requests
from requests.auth import HTTPBasicAuth
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
        self.https_mode = False
        self.snapshot_url = None
        self.ip_address = None
        self.username = None
        self.password = None
        self.connection_type = None
    
    async def initialize(self, camera_id: int = 0, width: int = 1280, height: int = 720, ip_address: str = None, username: str = None, password: str = None, stream_path: str = None, connection_type: str = "rtsp") -> None:
        """Initialize the camera service. Supports local, RTSP, and HTTPS cameras."""
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.connection_type = connection_type
        
        if ip_address:
            # Build URL based on connection type
            if connection_type in ["https", "http"]:
                # For HTTPS cameras, we'll use snapshot-based streaming
                self.https_mode = True
                self.snapshot_url = f"{connection_type}://{ip_address}{stream_path or '/cgi-bin/api.cgi?cmd=Snap&channel=0'}"
                logger.info(f"Initializing HTTPS camera at {self.snapshot_url}")
                # Test the HTTPS connection
                if not self._test_https_fallback(ip_address, username, password):
                    logger.warning(f"Could not connect to HTTPS camera at {ip_address}")
                    return
            else:
                # RTSP mode
                self.https_mode = False
                if username and password:
                    url = f"rtsp://{username}:{password}@{ip_address}{stream_path or ''}"
                else:
                    url = f"rtsp://{ip_address}{stream_path or ''}"
                self.camera = cv2.VideoCapture(url)
                logger.info(f"Trying to open RTSP camera at {url}")
                
                if not self.camera.isOpened():
                    logger.warning(f"RTSP failed, trying HTTPS fallback for {ip_address}")
                    # Try HTTPS fallback
                    if self._test_https_fallback(ip_address, username, password):
                        self.https_mode = True
                        self.snapshot_url = f"https://{ip_address}/cgi-bin/api.cgi?cmd=Snap&channel=0"
                        logger.info(f"Switched to HTTPS mode for {ip_address}")
                    else:
                        logger.warning(f"Could not open camera {ip_address} via RTSP or HTTPS")
                        return
        else:
            # Local camera
            self.https_mode = False
            self.camera = cv2.VideoCapture(camera_id)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            if not self.camera.isOpened():
                logger.warning(f"Could not open local camera {camera_id}")
                return
        
        # Start frame capture loop
        self.running = True
        self.task = asyncio.create_task(self._capture_frames())
        logger.info(f"Camera initialized: {ip_address if ip_address else camera_id} ({width}x{height}) - Mode: {'HTTPS' if self.https_mode else 'RTSP/Local'}")
    @staticmethod
    def test_ip_camera(ip_address: str, username: str = None, password: str = None, timeout: int = 30) -> dict:
        """
        Test connection to a specific IP camera with optional credentials.
        Returns dict with success status and detailed information.
        """
        import time
        import threading
        
        if username and password:
            url = f"rtsp://{username}:{password}@{ip_address}"
        else:
            url = f"rtsp://{ip_address}"
        
        result = {
            "success": False,
            "message": "",
            "details": {},
            "url": url
        }
        
        def test_connection():
            try:
                # First try RTSP connection
                cap = cv2.VideoCapture(url)
                
                # Enhanced timeout properties for RTSP
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
                
                # Try different backends if initial fails
                if not cap.isOpened():
                    cap.release()
                    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
                    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
                
                if cap.isOpened():
                    # Try to read a frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        result["success"] = True
                        result["message"] = "Connection successful! Camera is accessible and streaming."
                        result["details"] = {
                            "resolution": f"{width}x{height}",
                            "frame_captured": True,
                            "connection_time": f"< {timeout}s"
                        }
                    else:
                        result["message"] = "Connected to camera but could not capture frames. Camera may be in use or stream may be unavailable."
                        result["details"] = {"frame_captured": False}
                else:
                    # RTSP failed, try HTTPS fallback for supported cameras
                    cap.release()
                    https_success = CameraService._test_https_fallback(ip_address, username, password, timeout)
                    if https_success:
                        result["success"] = True
                        result["message"] = "RTSP failed but HTTPS streaming is available"
                        result["details"] = {"connection_opened": False, "https_fallback": True}
                    else:
                        result["message"] = "Could not establish connection via RTSP or HTTPS. Check IP address, credentials, and network connectivity."
                        result["details"] = {"connection_opened": False, "https_fallback": False}
                    return
                
                cap.release()
                
            except Exception as e:
                result["message"] = f"Connection test failed: {str(e)}"
                result["details"] = {"error": str(e)}
        
        # Run connection test in a thread with timeout
        thread = threading.Thread(target=test_connection)
        thread.daemon = True
        thread.start()
        thread.join(timeout + 5)  # Allow extra time for cleanup
        
        if thread.is_alive():
            result["message"] = f"Connection test timed out after {timeout + 5} seconds. Camera may be unreachable or credentials may be incorrect."
            result["details"] = {"timeout": True, "timeout_seconds": timeout + 5}
        
        return result
    
    @staticmethod
    def _test_https_fallback(ip_address: str, username: str = None, password: str = None, timeout: int = 15) -> bool:
        """Test HTTPS snapshot capability as streaming fallback"""
        try:
            # Common HTTPS snapshot URLs for IP cameras
            snapshot_urls = [
                f"https://{ip_address}/cgi-bin/api.cgi?cmd=Snap&channel=0",  # Reolink
                f"https://{ip_address}/ISAPI/Streaming/channels/101/picture",  # Hikvision
                f"https://{ip_address}/cgi-bin/snapshot.cgi",  # Generic
                f"http://{ip_address}/cgi-bin/api.cgi?cmd=Snap&channel=0",   # HTTP fallback for Reolink
                f"http://{ip_address}/snapshot.cgi"  # Generic HTTP
            ]
            
            for snapshot_url in snapshot_urls:
                try:
                    auth = HTTPBasicAuth(username or 'admin', password or '') if username else None
                    response = requests.get(
                        snapshot_url,
                        auth=auth,
                        timeout=timeout,
                        verify=False
                    )
                    
                    if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                        logger.info(f"HTTPS snapshot successful: {snapshot_url}")
                        return True
                        
                except requests.exceptions.RequestException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"HTTPS fallback test error: {str(e)}")
            return False
    
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
        """Capture frames in a loop - supports both RTSP and HTTPS modes"""
        while self.running:
            if self.https_mode:
                # HTTPS snapshot mode
                frame = await self._get_https_frame()
                if frame is not None:
                    async with self.frame_lock:
                        self.frame_buffer = frame
                        self.last_frame_time = time.time()
                # Slower refresh rate for HTTPS snapshots
                await asyncio.sleep(1.0)  # 1 fps for snapshots
            else:
                # RTSP/Local camera mode
                if self.camera and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    
                    if ret:
                        # Update frame buffer with thread safety
                        async with self.frame_lock:
                            self.frame_buffer = frame
                            self.last_frame_time = time.time()
                    
                # Small delay to prevent CPU hogging
                await asyncio.sleep(0.03)  # ~30fps
    
    async def _get_https_frame(self) -> Optional[np.ndarray]:
        """Get frame from HTTPS snapshot"""
        try:
            auth = HTTPBasicAuth(self.username or 'admin', self.password or '') if self.username else None
            response = requests.get(
                self.snapshot_url,
                auth=auth,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                # Convert image bytes to OpenCV frame
                image_array = np.frombuffer(response.content, np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                return frame
            else:
                logger.warning(f"HTTPS snapshot failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting HTTPS frame: {str(e)}")
            return None
    
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
        Detect available cameras and return them in the expected format
        
        Returns:
            List of dictionaries with camera information
        """
        available_cameras = []
        
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append({
                        "id": i,
                        "is_working": True
                    })
                cap.release()
        
        return available_cameras