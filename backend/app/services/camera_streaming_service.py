"""
Camera Streaming Service for live video streaming from IP cameras
Updated to use Frame Distribution Architecture for single connection sharing
"""
import asyncio
import cv2
import logging
import numpy as np
from typing import Optional, AsyncGenerator, Tuple
from datetime import datetime
from dataclasses import dataclass

from app.database import Camera
from app.services.frame_distribution_service import get_frame_distribution_manager, FrameDistributionConfig

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Configuration for camera streaming"""
    quality: str = "medium"  # low, medium, high
    max_fps: int = 30
    buffer_size: int = 5  # Balanced: not too high for latency, not too low for stability
    jpeg_quality: int = 80
    frame_timeout: float = 3.0  # Balanced timeout for stability
    low_latency: bool = True  # Enable low latency optimizations
    max_reconnect_attempts: int = 3  # Number of reconnection attempts
    reconnect_delay: float = 2.0  # Delay between reconnection attempts


class CameraStreamingService:
    """
    Service for streaming video from IP cameras using Frame Distribution Architecture
    
    This service now uses the frame distribution system to avoid connection conflicts
    and ensures single RTSP connection per camera shared across all consumers.
    """
    
    def __init__(self, camera: Camera, config: Optional[StreamConfig] = None):
        self.camera = camera
        self.config = config or StreamConfig()
        
        # Frame distribution setup
        self.distributor = None
        self.consumer = None
        self.consumer_name = f"web_streaming_{camera.id}"
        
        # Streaming state
        self.is_streaming = False
        self._streaming_task: Optional[asyncio.Task] = None
        
    def _setup_frame_distribution(self) -> bool:
        """Setup frame distribution for this camera"""
        try:
            # Get or create distributor for this camera
            self.distributor = get_frame_distribution_manager().get_distributor(self.camera.id)
            
            if not self.distributor:
                # Create new distributor
                distribution_config = FrameDistributionConfig(
                    recording_queue_size=30,
                    detection_queue_size=10,
                    latest_frame_timeout=5.0
                )
                self.distributor = get_frame_distribution_manager().create_distributor(
                    self.camera, distribution_config
                )
                
                # Start the distributor
                if not self.distributor.start():
                    logger.error(f"Failed to start frame distributor for camera {self.camera.id}")
                    return False
            
            # Add this service as a consumer
            self.consumer = self.distributor.add_consumer(
                self.consumer_name, 
                queue_size=self.config.buffer_size
            )
            
            logger.info(f"Frame distribution setup complete for camera {self.camera.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up frame distribution for camera {self.camera.id}: {str(e)}")
            return False
    
    async def connect_camera(self) -> bool:
        """
        Connect to camera via frame distribution service
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Setup frame distribution (creates distributor if needed)
            if not self._setup_frame_distribution():
                return False
            
            # Verify distributor is running and connected
            if not self.distributor.is_running:
                logger.error(f"Frame distributor not running for camera {self.camera.name}")
                return False
            
            # Test that we can get frames from the distributor
            test_frame = self.distributor.get_latest_frame()
            if test_frame is None:
                # Give it a moment to start producing frames
                await asyncio.sleep(1.0)
                test_frame = self.distributor.get_latest_frame()
                
                if test_frame is None:
                    logger.warning(f"No frames available yet from camera {self.camera.name}")
                    # Don't fail here - frames might come soon
            
            logger.info(f"Successfully connected to camera {self.camera.name} via frame distribution")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to camera {self.camera.name}: {str(e)}")
            await self.disconnect_camera()
            return False
    
    async def disconnect_camera(self):
        """Disconnect from camera and cleanup resources"""
        try:
            # Remove this service as a consumer
            if self.distributor and self.consumer:
                self.distributor.remove_consumer(self.consumer_name)
                self.consumer = None
            
            # Note: We don't stop the distributor here as other consumers 
            # (recording, detection) may still be using it
            
            logger.info(f"Disconnected from camera {self.camera.name}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from camera {self.camera.name}: {str(e)}")
    
    
    def get_connection_health(self) -> dict:
        """
        Get connection health information from frame distribution
        
        Returns:
            Dictionary with health status information
        """
        if not self.distributor:
            return {
                "is_streaming": self.is_streaming,
                "healthy": False,
                "error": "No frame distributor available"
            }
        
        distributor_stats = self.distributor.get_stats()
        
        return {
            "is_streaming": self.is_streaming,
            "is_connected": distributor_stats.get("is_connected", False),
            "consecutive_failures": distributor_stats.get("consecutive_failures", 0),
            "frames_captured": distributor_stats.get("frames_captured", 0),
            "latest_frame_age": distributor_stats.get("latest_frame_age"),
            "healthy": (
                distributor_stats.get("is_connected", False) and
                distributor_stats.get("consecutive_failures", 0) < 5 and
                (distributor_stats.get("latest_frame_age") or 0) < 10
            )
        }
    
    async def diagnose_connectivity(self) -> dict:
        """
        Comprehensive connectivity diagnostics for the camera using frame distribution
        
        Returns:
            Dictionary with detailed diagnostic information
        """
        try:
            # Ensure frame distribution is available
            if not self.distributor:
                if not await self.connect_camera():
                    return {
                        "camera_id": self.camera.id,
                        "camera_name": self.camera.name,
                        "timestamp": datetime.now().isoformat(),
                        "error": "Failed to setup frame distribution",
                        "success": False
                    }
            
            # Get comprehensive stats from distributor
            stats = self.distributor.get_stats()
            
            return {
                "camera_id": self.camera.id,
                "camera_name": self.camera.name,
                "timestamp": datetime.now().isoformat(),
                "frame_distribution": stats,
                "connection_health": self.get_connection_health(),
                "success": stats.get("is_connected", False)
            }
            
        except Exception as e:
            return {
                "camera_id": self.camera.id,
                "camera_name": self.camera.name,
                "timestamp": datetime.now().isoformat(),
                "error": f"Diagnostics failed: {str(e)}",
                "success": False
            }
    
    async def _encode_frame(self, frame: np.ndarray) -> Optional[bytes]:
        """
        Encode frame to JPEG bytes - minimal processing for performance
        
        Args:
            frame: OpenCV frame (numpy array)
            
        Returns:
            JPEG encoded frame as bytes, or None if encoding failed
        """
        try:
            # Set JPEG quality based on config - no resizing for performance
            if self.config.quality == "low":
                jpeg_quality = 70
            elif self.config.quality == "medium":
                jpeg_quality = 85
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
        Start video streaming and yield JPEG frames from frame distribution
        
        Yields:
            bytes: JPEG encoded video frames
        """
        if self.is_streaming:
            logger.warning(f"Stream already active for camera {self.camera.name}")
            return
        
        # Connect to frame distribution service
        if not await self.connect_camera():
            raise RuntimeError(f"Failed to connect to camera {self.camera.name}")
        
        self.is_streaming = True
        logger.info(f"Started streaming for camera {self.camera.name}")
        
        try:
            while self.is_streaming:
                try:
                    # Get frame from distributor consumer queue
                    frame = None
                    if self.consumer:
                        frame = self.consumer.get_frame(timeout=self.config.frame_timeout)
                    
                    if frame is None:
                        # Fallback to latest frame from distributor
                        frame = self.distributor.get_latest_frame() if self.distributor else None
                        
                        if frame is None:
                            logger.warning(f"No frame available for camera {self.camera.name}")
                            await asyncio.sleep(0.1)  # Brief pause
                            continue
                    
                    # Encode frame to JPEG
                    frame_bytes = await self._encode_frame(frame)
                    if frame_bytes:
                        yield frame_bytes
                    else:
                        await asyncio.sleep(0.1)  # Brief pause on encoding failure
                    
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
        
        # Disconnect from frame distribution (removes consumer)
        await self.disconnect_camera()
        
        logger.info(f"Stream stopped for camera {self.camera.name}")
    
    async def get_current_frame(self) -> Optional[bytes]:
        """
        Get the current frame as JPEG bytes (for thumbnail generation)
        
        Returns:
            Current frame as JPEG bytes, or None if not available
        """
        try:
            # Ensure frame distribution is setup
            if not self.distributor:
                if not await self.connect_camera():
                    return None
            
            # Get latest frame from distributor
            frame = self.distributor.get_latest_frame()
            if frame is not None:
                return await self._encode_frame(frame)
            
            logger.warning(f"No current frame available for camera {self.camera.name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting current frame for camera {self.camera.name}: {str(e)}")
            return None
    
    def get_stream_info(self) -> dict:
        """Get information about the current stream"""
        consumer_info = {}
        if self.consumer:
            consumer_stats = self.consumer.get_stats()
            consumer_info = {
                "queue_size": consumer_stats.get("queue_size", 0),
                "max_queue_size": consumer_stats.get("max_queue_size", 0),
                "frames_received": consumer_stats.get("frames_received", 0),
                "frames_dropped": consumer_stats.get("frames_dropped", 0),
                "drop_rate": consumer_stats.get("drop_rate", 0.0)
            }
        
        distributor_info = {}
        if self.distributor:
            distributor_stats = self.distributor.get_stats()
            distributor_info = {
                "is_connected": distributor_stats.get("is_connected", False),
                "frames_captured": distributor_stats.get("frames_captured", 0),
                "consecutive_failures": distributor_stats.get("consecutive_failures", 0)
            }
        
        return {
            "camera_id": self.camera.id,
            "camera_name": self.camera.name,
            "is_streaming": self.is_streaming,
            "consumer": consumer_info,
            "distributor": distributor_info,
            "config": {
                "quality": self.config.quality,
                "max_fps": self.config.max_fps,
                "jpeg_quality": self.config.jpeg_quality
            }
        }