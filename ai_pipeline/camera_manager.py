"""
Camera Manager - Handles all camera connections
IMPORTANT: This captures from IP cameras locally, does NOT stream to browsers
"""
import cv2
import threading
import queue
import time
import logging
import os
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
        Enhanced capture loop with improved stability and recovery
        This is NOT for streaming to browsers!
        """
        reconnect_delay = 5
        consecutive_failures = 0
        frame_count = 0
        last_fps_check = time.time()
        
        while self.is_running:
            try:
                if not self._connect():
                    consecutive_failures += 1
                    # Exponential backoff with jitter
                    jitter = min(consecutive_failures * 0.5, 5)
                    sleep_time = min(reconnect_delay + jitter, 60)
                    self.logger.info(f"Reconnect attempt {consecutive_failures}, waiting {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                    reconnect_delay = min(reconnect_delay * 1.2, 30)
                    continue
                
                # Reset on successful connection
                reconnect_delay = 5
                consecutive_failures = 0
                self.error_count = 0
                frame_count = 0
                last_fps_check = time.time()
                
                # Main frame capture loop with health monitoring
                frames_since_last_check = 0
                last_health_check = time.time()
                
                while self.is_running and self.capture.isOpened():
                    try:
                        ret, frame = self.capture.read()
                        
                        if not ret or frame is None:
                            self.logger.warning("Failed to read frame, attempting recovery")
                            consecutive_failures += 1
                            if consecutive_failures > 3:
                                self.logger.warning("Multiple frame read failures, reconnecting")
                                break
                            time.sleep(0.1)  # Brief pause before retry
                            continue
                        
                        # Reset failure counter on successful read
                        consecutive_failures = 0
                        frame_count += 1
                        frames_since_last_check += 1
                        
                        # Validate frame quality
                        if frame.size == 0 or frame.shape[0] < 100 or frame.shape[1] < 100:
                            self.logger.warning("Received invalid/corrupt frame")
                            continue
                        
                        # Store for AI processing
                        self.last_frame = frame.copy()
                        self.last_frame_time = time.time()
                        
                        # Buffer management with frame dropping strategy
                        try:
                            if self.frame_buffer.full():
                                # Drop multiple old frames to maintain real-time processing
                                dropped = 0
                                while not self.frame_buffer.empty() and dropped < 3:
                                    try:
                                        self.frame_buffer.get_nowait()
                                        dropped += 1
                                    except queue.Empty:
                                        break
                            
                            self.frame_buffer.put_nowait(frame)
                            
                        except queue.Full:
                            # Emergency frame drop
                            try:
                                self.frame_buffer.get_nowait()
                                self.frame_buffer.put_nowait(frame)
                            except queue.Empty:
                                pass
                        
                        # Periodic health monitoring and FPS reporting
                        now = time.time()
                        if now - last_health_check > 30:  # Every 30 seconds
                            fps = frames_since_last_check / (now - last_health_check)
                            self.logger.info(f"Camera {self.config.camera_id}: {fps:.1f} FPS, buffer: {self.frame_buffer.qsize()}")
                            frames_since_last_check = 0
                            last_health_check = now
                            
                            # Check for potential issues
                            if fps < 5:
                                self.logger.warning(f"Low FPS detected: {fps:.1f}, may indicate network issues")
                            
                        # Brief yield to prevent CPU monopolization
                        if frame_count % 30 == 0:  # Every 30 frames
                            time.sleep(0.001)
                            
                    except Exception as frame_error:
                        self.logger.warning(f"Frame processing error: {frame_error}")
                        consecutive_failures += 1
                        if consecutive_failures > 5:
                            break
                        time.sleep(0.1)
                        
            except Exception as e:
                self.logger.error(f"Capture loop error: {e}")
                self.error_count += 1
                consecutive_failures += 1
                
                # If we have too many errors, increase delay significantly
                if self.error_count > 10:
                    self.logger.error("Too many capture errors, entering extended retry mode")
                    time.sleep(min(60, self.error_count * 5))
                    
            finally:
                if self.capture:
                    self.capture.release()
                    self.capture = None
                    
        self.logger.info(f"Capture loop ended for camera {self.config.camera_id}")
                
    def _connect(self) -> bool:
        """Enhanced connection with better timeout handling and network resilience"""
        try:
            # Mask credentials in logs for security
            safe_url = self.config.stream_url
            if self.config.password:
                safe_url = safe_url.replace(self.config.password, '***')
            self.logger.info(f"Connecting to {safe_url}")
            
            # Test network connectivity first
            if not self._test_network_connectivity():
                self.logger.warning(f"Network connectivity test failed for {self.config.ip_address}")
                return False
            
            # Enhanced RTSP/HTTP connection setup
            if self.config.protocol == "rtsp":
                # Optimized RTSP transport options
                ffmpeg_options = [
                    'rtsp_transport;tcp',  # Use TCP for reliability
                    'stimeout;5000000',    # 5 second timeout (microseconds)
                    'rw_timeout;5000000',  # 5 second read/write timeout
                    'rtsp_flags;prefer_tcp',  # Prefer TCP over UDP
                    'buffer_size;1024000'  # 1MB buffer for network jitter
                ]
                os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = '|'.join(ffmpeg_options)
            
            # Create capture with enhanced settings
            self.capture = cv2.VideoCapture(self.config.stream_url, cv2.CAP_FFMPEG)
            
            # Optimize capture settings for stability
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 2)  # Small buffer for real-time
            
            # Enhanced timeout configuration
            timeout_ms = 8000  # 8 seconds for initial connection
            self.capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_ms)
            self.capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # 5 seconds for reads
            
            # Additional stability settings
            if self.config.protocol == "rtsp":
                self.capture.set(cv2.CAP_PROP_FPS, 15)  # Limit FPS for stability
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Reasonable resolution
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # Verify connection
            if not self.capture.isOpened():
                raise Exception("Failed to open video stream")
            
            # Test multiple frame reads to ensure stability
            test_frames = 0
            for i in range(3):  # Try 3 frames
                ret, frame = self.capture.read()
                if ret and frame is not None and frame.size > 0:
                    test_frames += 1
                    if i == 0:  # Store first good frame
                        self.last_frame = frame.copy()
                        self.last_frame_time = time.time()
                else:
                    self.logger.warning(f"Test frame {i+1} failed")
                    
                if i < 2:  # Brief pause between test reads
                    time.sleep(0.1)
            
            if test_frames == 0:
                raise Exception("No valid frames received during connection test")
            
            # Log connection success with details
            actual_fps = self.capture.get(cv2.CAP_PROP_FPS)
            actual_width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            self.logger.info(f"Successfully connected: {actual_width:.0f}x{actual_height:.0f} @ {actual_fps:.1f}FPS, {test_frames}/3 test frames OK")
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
    
    def _test_network_connectivity(self) -> bool:
        """Test basic network connectivity to camera IP"""
        try:
            import socket
            
            # Quick TCP connection test
            sock = socket.create_connection((self.config.ip_address, self.config.port), timeout=3)
            sock.close()
            return True
            
        except (socket.timeout, socket.error, ConnectionRefusedError) as e:
            self.logger.warning(f"Network connectivity test failed: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Unexpected network test error: {e}")
            return False
    
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
        """Enhanced health check with multiple criteria"""
        if not self.is_running:
            return False
        
        # Check if capture object exists and is opened
        if not self.capture or not self.capture.isOpened():
            return False
        
        current_time = time.time()
        
        # Check if we've received frames recently (allow longer timeout for stability)
        if self.last_frame_time > 0 and (current_time - self.last_frame_time) > 15:
            return False
        
        # Check error threshold
        if self.error_count >= 8:  # Increased tolerance
            return False
        
        # Check if frame buffer is receiving data
        if hasattr(self, 'frame_buffer') and self.frame_buffer.empty() and self.last_frame_time > 0:
            # Buffer empty but we've had frames before - might be temporary
            if (current_time - self.last_frame_time) > 5:
                return False
        
        return True
    
    def get_health_status(self) -> dict:
        """Get detailed health status information"""
        current_time = time.time()
        
        status = {
            "camera_id": self.config.camera_id,
            "is_running": self.is_running,
            "is_healthy": self.is_healthy(),
            "capture_active": self.capture is not None and self.capture.isOpened(),
            "error_count": self.error_count,
            "last_frame_age": current_time - self.last_frame_time if self.last_frame_time > 0 else None,
            "buffer_size": self.frame_buffer.qsize() if hasattr(self, 'frame_buffer') else 0,
            "buffer_full": self.frame_buffer.full() if hasattr(self, 'frame_buffer') else False,
            "connection_url": self.config.stream_url.replace(self.config.password, '***') if self.config.password else self.config.stream_url
        }
        
        # Add health assessment
        if not self.is_running:
            status["health_issue"] = "Camera not running"
        elif not status["capture_active"]:
            status["health_issue"] = "No active capture connection"
        elif status["last_frame_age"] and status["last_frame_age"] > 15:
            status["health_issue"] = f"No frames for {status['last_frame_age']:.1f}s"
        elif self.error_count >= 5:
            status["health_issue"] = f"High error count: {self.error_count}"
        else:
            status["health_issue"] = None
        
        return status
    
    def restart_connection(self):
        """Force restart of camera connection"""
        self.logger.info(f"Restarting connection for camera {self.config.camera_id}")
        
        # Close current connection
        if self.capture:
            self.capture.release()
            self.capture = None
        
        # Reset error counters
        self.error_count = 0
        
        # Clear buffer
        while not self.frame_buffer.empty():
            try:
                self.frame_buffer.get_nowait()
            except queue.Empty:
                break

class CameraManager:
    """Enhanced camera manager with health monitoring and recovery"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        self.logger = logging.getLogger("CameraManager")
        self._health_monitor_thread = None
        self._health_monitor_running = False
        self._start_health_monitor()
        
    def add_camera(self, config: CameraConfig) -> bool:
        """Add camera for AI processing"""
        if config.camera_id in self.cameras:
            self.logger.warning(f"Camera {config.camera_id} already exists, replacing")
            self.remove_camera(config.camera_id)
            
        camera = CameraStream(config)
        camera.start()
        self.cameras[config.camera_id] = camera
        self.logger.info(f"Added camera {config.camera_id}: {config.name}")
        return True
        
    def remove_camera(self, camera_id: str):
        """Stop and remove a camera"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
            self.logger.info(f"Removed camera {camera_id}")
    
    def get_camera(self, camera_id: str) -> Optional[CameraStream]:
        return self.cameras.get(camera_id)
        
    def get_all_cameras(self) -> Dict[str, CameraStream]:
        return self.cameras
    
    def restart_camera(self, camera_id: str) -> bool:
        """Restart a specific camera connection"""
        camera = self.cameras.get(camera_id)
        if not camera:
            self.logger.error(f"Camera {camera_id} not found for restart")
            return False
        
        try:
            camera.restart_connection()
            self.logger.info(f"Restarted camera {camera_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restart camera {camera_id}: {e}")
            return False
    
    def get_system_health(self) -> dict:
        """Get comprehensive health status for all cameras"""
        health_report = {
            "total_cameras": len(self.cameras),
            "healthy_cameras": 0,
            "unhealthy_cameras": 0,
            "cameras": {},
            "summary": {}
        }
        
        for camera_id, camera in self.cameras.items():
            camera_health = camera.get_health_status()
            health_report["cameras"][camera_id] = camera_health
            
            if camera_health["is_healthy"]:
                health_report["healthy_cameras"] += 1
            else:
                health_report["unhealthy_cameras"] += 1
        
        # Generate summary
        if health_report["total_cameras"] == 0:
            health_report["summary"]["status"] = "no_cameras"
            health_report["summary"]["message"] = "No cameras configured"
        elif health_report["unhealthy_cameras"] == 0:
            health_report["summary"]["status"] = "all_healthy"
            health_report["summary"]["message"] = "All cameras operating normally"
        elif health_report["healthy_cameras"] == 0:
            health_report["summary"]["status"] = "all_unhealthy"
            health_report["summary"]["message"] = "All cameras experiencing issues"
        else:
            health_report["summary"]["status"] = "mixed"
            health_report["summary"]["message"] = f"{health_report['healthy_cameras']} healthy, {health_report['unhealthy_cameras']} unhealthy"
        
        return health_report
    
    def _start_health_monitor(self):
        """Start background health monitoring"""
        if not self._health_monitor_running:
            self._health_monitor_running = True
            self._health_monitor_thread = threading.Thread(
                target=self._health_monitor_loop,
                name="CameraHealthMonitor",
                daemon=True
            )
            self._health_monitor_thread.start()
            self.logger.info("Started camera health monitor")
    
    def _health_monitor_loop(self):
        """Background health monitoring and recovery"""
        check_interval = 60  # Check every 60 seconds
        
        while self._health_monitor_running:
            try:
                health_report = self.get_system_health()
                
                # Log periodic summary
                if health_report["total_cameras"] > 0:
                    self.logger.info(f"Health check: {health_report['summary']['message']}")
                    
                    # Check for cameras that need attention
                    for camera_id, camera_health in health_report["cameras"].items():
                        if not camera_health["is_healthy"] and camera_health["health_issue"]:
                            self.logger.warning(f"Camera {camera_id}: {camera_health['health_issue']}")
                            
                            # Auto-recovery for certain issues
                            if ("No frames" in camera_health["health_issue"] or 
                                "No active capture" in camera_health["health_issue"]):
                                self.logger.info(f"Attempting auto-recovery for camera {camera_id}")
                                self.restart_camera(camera_id)
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                time.sleep(30)  # Shorter sleep on error
    
    def stop_all(self):
        """Stop all cameras and health monitoring"""
        self.logger.info("Stopping all cameras and health monitoring")
        
        # Stop health monitor
        self._health_monitor_running = False
        if self._health_monitor_thread:
            self._health_monitor_thread.join(timeout=5.0)
        
        # Stop all cameras
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()
        
        self.logger.info("All cameras stopped")