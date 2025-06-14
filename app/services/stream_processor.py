import asyncio
import time
import logging
import cv2
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
import numpy as np
from app.schemas import CameraType, CameraConfig, CameraFrame

logger = logging.getLogger(__name__)

class StreamProcessor:
    """
    Decoupled stream processing service
    
    This service handles the core stream processing logic independent of HTTP requests.
    It can be used by both the web UI stream router and the background stream manager.
    """
    
    def __init__(self):
        self.running = False
        self.processing_callbacks = []
        self.detection_callbacks = []
        
        # Processing control
        self.frame_count = 0
        self.last_frame_time = 0
        self.processing_metrics = {
            "frames_processed": 0,
            "detections_found": 0,
            "average_processing_time": 0,
            "total_processing_time": 0,
            "start_time": time.time()
        }
        
        # Configuration
        self.frame_skip = 5
        self.processing_interval = 0.5
        
    def configure(self, frame_skip: int = 5, processing_interval: float = 0.5):
        """Configure stream processing parameters"""
        self.frame_skip = frame_skip
        self.processing_interval = processing_interval
        logger.info(f"Stream processor configured: frame_skip={frame_skip}, interval={processing_interval}")
    
    def add_processing_callback(self, callback: Callable):
        """Add a callback for frame processing events"""
        if callback not in self.processing_callbacks:
            self.processing_callbacks.append(callback)
    
    def remove_processing_callback(self, callback: Callable):
        """Remove a frame processing callback"""
        if callback in self.processing_callbacks:
            self.processing_callbacks.remove(callback)
    
    def add_detection_callback(self, callback: Callable):
        """Add a callback for detection events"""
        if callback not in self.detection_callbacks:
            self.detection_callbacks.append(callback)
    
    def remove_detection_callback(self, callback: Callable):
        """Remove a detection callback"""
        if callback in self.detection_callbacks:
            self.detection_callbacks.remove(callback)
    
    async def process_frame_with_detection(
        self, 
        frame: np.ndarray, 
        detection_service,
        timestamp: Optional[float] = None
    ) -> tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Process a frame through the detection pipeline
        
        Args:
            frame: The input frame to process
            detection_service: Detection service instance
            timestamp: Frame timestamp (optional)
            
        Returns:
            Tuple of (processed_frame, detections)
        """
        start_time = time.time()
        self.frame_count += 1
        
        # Check if we should skip this frame
        if self.frame_count % self.frame_skip != 0:
            # Return frame with timestamp overlay only
            display_frame = frame.copy()
            current_time = timestamp or time.time()
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
            
            import cv2
            cv2.putText(display_frame, time_str, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(display_frame, f"Frame: {self.frame_count} (skipped)", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            return display_frame, []
        
        try:
            # Notify processing callbacks
            for callback in self.processing_callbacks:
                try:
                    await callback("frame_processing_start", {
                        "frame_count": self.frame_count,
                        "timestamp": timestamp or time.time()
                    })
                except Exception as e:
                    logger.error(f"Error in processing callback: {e}")
            
            # Process frame for detections
            processed_frame, detections = await detection_service.process_frame(frame)
            
            # Update metrics
            processing_time = time.time() - start_time
            self.processing_metrics["frames_processed"] += 1
            self.processing_metrics["total_processing_time"] += processing_time
            self.processing_metrics["average_processing_time"] = (
                self.processing_metrics["total_processing_time"] / 
                self.processing_metrics["frames_processed"]
            )
            
            if detections:
                self.processing_metrics["detections_found"] += len(detections)
                
                # Notify detection callbacks
                for callback in self.detection_callbacks:
                    try:
                        await callback("detections_found", {
                            "detections": detections,
                            "frame_count": self.frame_count,
                            "processing_time": processing_time
                        })
                    except Exception as e:
                        logger.error(f"Error in detection callback: {e}")
            
            # Add processing info to frame
            import cv2
            cv2.putText(processed_frame, f"Processed: {processing_time:.2f}s", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(processed_frame, f"Detections: {len(detections)}", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Notify processing complete
            for callback in self.processing_callbacks:
                try:
                    await callback("frame_processing_complete", {
                        "frame_count": self.frame_count,
                        "processing_time": processing_time,
                        "detections_count": len(detections)
                    })
                except Exception as e:
                    logger.error(f"Error in processing callback: {e}")
                    
            return processed_frame, detections
            
        except Exception as e:
            logger.error(f"Error processing frame {self.frame_count}: {e}")
            
            # Return frame with error indicator
            error_frame = frame.copy()
            import cv2
            cv2.putText(error_frame, f"Error: {str(e)[:50]}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            return error_frame, []
    
    def should_process_frame(self) -> bool:
        """Check if the current frame should be processed"""
        return self.frame_count % self.frame_skip == 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        uptime = time.time() - self.processing_metrics["start_time"]
        
        return {
            "frame_count": self.frame_count,
            "frames_processed": self.processing_metrics["frames_processed"],
            "detections_found": self.processing_metrics["detections_found"],
            "average_processing_time": self.processing_metrics["average_processing_time"],
            "uptime": uptime,
            "processing_rate": self.processing_metrics["frames_processed"] / max(uptime, 1),
            "detection_rate": self.processing_metrics["detections_found"] / max(uptime, 1),
            "frame_skip": self.frame_skip,
            "processing_interval": self.processing_interval
        }
    
    def reset_metrics(self):
        """Reset processing metrics"""
        self.processing_metrics = {
            "frames_processed": 0,
            "detections_found": 0,
            "average_processing_time": 0,
            "total_processing_time": 0,
            "start_time": time.time()
        }
        self.frame_count = 0
        logger.info("Stream processor metrics reset")

class PlateTracker:
    """
    Plate tracking and deduplication service
    
    This service tracks seen license plates and handles deduplication logic.
    """
    
    def __init__(self, cooldown_period: float = 5.0, confidence_threshold: float = 0.5):
        self.last_seen = {}  # Maps plate text to last seen timestamp
        self.cooldown_period = cooldown_period
        self.confidence_threshold = confidence_threshold
        self.detection_queue = []
        self.last_process_time = 0
        self.process_interval = 2.0
        self.processing_lock = asyncio.Lock()
        
    def configure(self, cooldown_period: float = None, confidence_threshold: float = None, 
                 process_interval: float = None):
        """Configure tracker parameters"""
        if cooldown_period is not None:
            self.cooldown_period = cooldown_period
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        if process_interval is not None:
            self.process_interval = process_interval
            
        logger.info(f"Plate tracker configured: cooldown={self.cooldown_period}, "
                   f"confidence={self.confidence_threshold}, interval={self.process_interval}")
    
    async def add_detections(self, detections: List[Dict[str, Any]]):
        """Add detections to the processing queue"""
        valid_detections = [
            d for d in detections 
            if d.get("plate_text") and d.get("confidence", 0) >= self.confidence_threshold
        ]
        
        if valid_detections:
            self.detection_queue.extend(valid_detections)
            logger.debug(f"Added {len(valid_detections)} detections to queue")
    
    async def process_queue(self) -> List[Dict[str, Any]]:
        """Process detection queue and return unique plates"""
        current_time = time.time()
        
        # Only process if enough time has passed
        if current_time - self.last_process_time < self.process_interval:
            return []
        
        # Skip if already processing
        if self.processing_lock.locked():
            return []
        
        async with self.processing_lock:
            self.last_process_time = current_time
            
            # Get and clear queue
            queue = self.detection_queue.copy()
            self.detection_queue = []
            
            if not queue:
                return []
            
            logger.debug(f"Processing {len(queue)} detections from queue")
            
            # Group by plate text to find best confidence
            plates_to_process = {}
            for detection in queue:
                plate_text = detection.get("plate_text", "").upper()
                if not plate_text:
                    continue
                
                # Check if this is better than existing
                current_confidence = detection.get("confidence", 0)
                if (plate_text not in plates_to_process or 
                    current_confidence > plates_to_process[plate_text].get("confidence", 0)):
                    plates_to_process[plate_text] = detection
            
            # Check cooldown and return unique plates
            unique_detections = []
            for plate_text, detection in plates_to_process.items():
                last_seen = self.last_seen.get(plate_text, 0)
                
                if current_time - last_seen >= self.cooldown_period:
                    self.last_seen[plate_text] = current_time
                    unique_detections.append(detection)
                    logger.debug(f"Accepted plate: {plate_text} (confidence: {detection.get('confidence', 0):.2f})")
                else:
                    remaining_cooldown = self.cooldown_period - (current_time - last_seen)
                    logger.debug(f"Skipped plate {plate_text} (cooldown: {remaining_cooldown:.1f}s remaining)")
            
            return unique_detections
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return {
            "tracked_plates": len(self.last_seen),
            "queue_size": len(self.detection_queue),
            "cooldown_period": self.cooldown_period,
            "confidence_threshold": self.confidence_threshold,
            "process_interval": self.process_interval
        }


class UniversalStreamProcessor:
    """
    Universal stream processing service that handles multiple camera sources
    
    Supports Android PWA, IP cameras, USB cameras, RTSP streams, and WebSocket connections
    """
    
    def __init__(self):
        self.active_streams: Dict[str, Dict] = {}  # camera_id -> stream_info
        self.frame_handlers: Dict[CameraType, Callable] = {
            CameraType.PWA: self._handle_pwa_frames,
            CameraType.RTSP: self._handle_rtsp_stream,
            CameraType.USB: self._handle_usb_stream,
            CameraType.IP_CAMERA: self._handle_http_stream,
            CameraType.WEBSOCKET: self._handle_websocket_stream
        }
        
        # Processing components
        self.stream_processor = StreamProcessor()
        self.plate_tracker = PlateTracker()
        
        # Statistics
        self.total_frames_processed = 0
        self.total_detections = 0
        self.start_time = datetime.utcnow()
        
    async def add_camera_source(self, camera_id: str, camera_type: CameraType, config: CameraConfig) -> bool:
        """Add a new camera source for processing"""
        try:
            if camera_id in self.active_streams:
                logger.warning(f"Camera {camera_id} already active, stopping existing stream")
                await self.stop_camera_stream(camera_id)
            
            # Initialize stream info
            stream_info = {
                "camera_id": camera_id,
                "type": camera_type,
                "config": config,
                "status": "initializing",
                "connection": None,
                "last_frame": None,
                "frame_count": 0,
                "error_count": 0,
                "start_time": datetime.utcnow(),
                "task": None
            }
            
            self.active_streams[camera_id] = stream_info
            
            # Start appropriate stream handler
            handler = self.frame_handlers.get(camera_type)
            if handler:
                task = asyncio.create_task(handler(camera_id, config))
                stream_info["task"] = task
                stream_info["status"] = "starting"
                logger.info(f"Started stream processor for camera {camera_id} ({camera_type.value})")
                return True
            else:
                logger.error(f"No handler available for camera type: {camera_type.value}")
                del self.active_streams[camera_id]
                return False
                
        except Exception as e:
            logger.error(f"Failed to add camera source {camera_id}: {str(e)}")
            if camera_id in self.active_streams:
                del self.active_streams[camera_id]
            return False

    async def stop_camera_stream(self, camera_id: str) -> bool:
        """Stop processing for a specific camera"""
        try:
            if camera_id not in self.active_streams:
                return True
                
            stream_info = self.active_streams[camera_id]
            
            # Cancel the processing task
            if stream_info.get("task"):
                stream_info["task"].cancel()
                try:
                    await stream_info["task"]
                except asyncio.CancelledError:
                    pass
            
            # Close connection if exists
            if stream_info.get("connection"):
                try:
                    if hasattr(stream_info["connection"], "release"):
                        stream_info["connection"].release()
                    elif hasattr(stream_info["connection"], "close"):
                        await stream_info["connection"].close()
                except:
                    pass
            
            # Update status and clean up
            stream_info["status"] = "stopped"
            del self.active_streams[camera_id]
            
            logger.info(f"Stopped stream for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping camera stream {camera_id}: {str(e)}")
            return False

    async def process_frame(self, camera_id: str, frame_data: Union[bytes, np.ndarray], detection_service) -> Optional[List[Dict]]:
        """Process a frame from any camera source"""
        try:
            if camera_id not in self.active_streams:
                logger.warning(f"Received frame from unknown camera: {camera_id}")
                return None
            
            stream_info = self.active_streams[camera_id]
            
            # Convert frame data to numpy array if needed
            if isinstance(frame_data, bytes):
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                frame = frame_data
            
            if frame is None:
                stream_info["error_count"] += 1
                return None
            
            # Update stream stats
            stream_info["frame_count"] += 1
            stream_info["last_frame"] = datetime.utcnow()
            stream_info["status"] = "active"
            self.total_frames_processed += 1
            
            # Process frame through detection pipeline
            processed_frame, detections = await self.stream_processor.process_frame_with_detection(
                frame, detection_service, time.time()
            )
            
            if detections:
                # Add camera_id to each detection
                for detection in detections:
                    detection["camera_id"] = camera_id
                    detection["camera_type"] = stream_info["type"].value
                
                # Track unique plates
                await self.plate_tracker.add_detections(detections)
                unique_detections = await self.plate_tracker.process_queue()
                
                if unique_detections:
                    self.total_detections += len(unique_detections)
                    return unique_detections
            
            return detections
            
        except Exception as e:
            logger.error(f"Error processing frame from camera {camera_id}: {str(e)}")
            if camera_id in self.active_streams:
                self.active_streams[camera_id]["error_count"] += 1
            return None

    async def get_camera_stats(self, camera_id: str) -> Optional[Dict]:
        """Get statistics for a specific camera"""
        if camera_id not in self.active_streams:
            return None
            
        stream_info = self.active_streams[camera_id]
        uptime = (datetime.utcnow() - stream_info["start_time"]).total_seconds()
        
        return {
            "camera_id": camera_id,
            "type": stream_info["type"].value,
            "status": stream_info["status"],
            "frame_count": stream_info["frame_count"],
            "error_count": stream_info["error_count"],
            "uptime_seconds": uptime,
            "fps": stream_info["frame_count"] / max(uptime, 1),
            "error_rate": stream_info["error_count"] / max(stream_info["frame_count"], 1),
            "last_frame": stream_info["last_frame"]
        }

    async def get_all_stats(self) -> Dict:
        """Get comprehensive statistics for all cameras"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        camera_stats = {}
        for camera_id in self.active_streams:
            camera_stats[camera_id] = await self.get_camera_stats(camera_id)
        
        return {
            "total_cameras": len(self.active_streams),
            "total_frames_processed": self.total_frames_processed,
            "total_detections": self.total_detections,
            "uptime_seconds": uptime,
            "overall_fps": self.total_frames_processed / max(uptime, 1),
            "detection_rate": self.total_detections / max(uptime, 1),
            "cameras": camera_stats,
            "stream_processor": self.stream_processor.get_metrics(),
            "plate_tracker": self.plate_tracker.get_stats()
        }

    # Camera-specific stream handlers
    
    async def _handle_pwa_frames(self, camera_id: str, config: CameraConfig):
        """Handle PWA camera frames (received via HTTP POST)"""
        try:
            self.active_streams[camera_id]["status"] = "waiting_for_frames"
            logger.info(f"PWA camera {camera_id} ready to receive frames")
            
            # PWA frames are handled by the API endpoint, this just maintains the stream info
            while camera_id in self.active_streams and not self.active_streams[camera_id].get("task", asyncio.Task()).cancelled():
                await asyncio.sleep(1)
                
                # Check for timeout
                stream_info = self.active_streams[camera_id]
                if stream_info.get("last_frame"):
                    time_since_last = (datetime.utcnow() - stream_info["last_frame"]).total_seconds()
                    if time_since_last > config.timeout_seconds:
                        stream_info["status"] = "timeout"
                        logger.warning(f"PWA camera {camera_id} timed out after {time_since_last:.1f}s")
                        break
                        
        except asyncio.CancelledError:
            logger.info(f"PWA camera handler for {camera_id} cancelled")
        except Exception as e:
            logger.error(f"Error in PWA camera handler for {camera_id}: {str(e)}")
            if camera_id in self.active_streams:
                self.active_streams[camera_id]["status"] = "error"

    async def _handle_rtsp_stream(self, camera_id: str, config: CameraConfig):
        """Handle RTSP camera stream"""
        try:
            import cv2
            
            # Construct RTSP URL with auth if provided
            rtsp_url = config.url
            if config.username and config.password:
                # Insert credentials into URL
                protocol, rest = rtsp_url.split("://", 1)
                rtsp_url = f"{protocol}://{config.username}:{config.password}@{rest}"
            
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_TIMEOUT, config.timeout_seconds * 1000)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, config.buffer_size)
            
            self.active_streams[camera_id]["connection"] = cap
            
            if not cap.isOpened():
                raise Exception(f"Failed to open RTSP stream: {rtsp_url}")
            
            logger.info(f"RTSP camera {camera_id} connected to {config.url}")
            self.active_streams[camera_id]["status"] = "connected"
            
            frame_skip_counter = 0
            while camera_id in self.active_streams and not self.active_streams[camera_id].get("task", asyncio.Task()).cancelled():
                ret, frame = cap.read()
                
                if not ret:
                    self.active_streams[camera_id]["error_count"] += 1
                    logger.warning(f"Failed to read frame from RTSP camera {camera_id}")
                    await asyncio.sleep(0.1)
                    continue
                
                # Apply frame skipping for performance
                frame_skip_counter += 1
                if frame_skip_counter % config.frame_skip != 0:
                    continue
                
                # Process frame
                self.active_streams[camera_id]["last_frame"] = datetime.utcnow()
                await asyncio.sleep(1.0 / config.fps)  # Control frame rate
                
        except asyncio.CancelledError:
            logger.info(f"RTSP camera handler for {camera_id} cancelled")
        except Exception as e:
            logger.error(f"Error in RTSP camera handler for {camera_id}: {str(e)}")
            if camera_id in self.active_streams:
                self.active_streams[camera_id]["status"] = "error"
        finally:
            if camera_id in self.active_streams and self.active_streams[camera_id].get("connection"):
                self.active_streams[camera_id]["connection"].release()

    async def _handle_usb_stream(self, camera_id: str, config: CameraConfig):
        """Handle USB camera stream"""
        try:
            import cv2
            
            cap = cv2.VideoCapture(config.device_id)
            if not cap.isOpened():
                raise Exception(f"Failed to open USB camera {config.device_id}")
            
            # Set camera properties
            if config.resolution:
                width, height = map(int, config.resolution.split('x'))
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, config.fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, config.buffer_size)
            
            self.active_streams[camera_id]["connection"] = cap
            logger.info(f"USB camera {camera_id} connected (device {config.device_id})")
            self.active_streams[camera_id]["status"] = "connected"
            
            frame_skip_counter = 0
            while camera_id in self.active_streams and not self.active_streams[camera_id].get("task", asyncio.Task()).cancelled():
                ret, frame = cap.read()
                
                if not ret:
                    self.active_streams[camera_id]["error_count"] += 1
                    await asyncio.sleep(0.1)
                    continue
                
                # Apply frame skipping
                frame_skip_counter += 1
                if frame_skip_counter % config.frame_skip != 0:
                    continue
                
                self.active_streams[camera_id]["last_frame"] = datetime.utcnow()
                await asyncio.sleep(1.0 / config.fps)
                
        except asyncio.CancelledError:
            logger.info(f"USB camera handler for {camera_id} cancelled")
        except Exception as e:
            logger.error(f"Error in USB camera handler for {camera_id}: {str(e)}")
            if camera_id in self.active_streams:
                self.active_streams[camera_id]["status"] = "error"
        finally:
            if camera_id in self.active_streams and self.active_streams[camera_id].get("connection"):
                self.active_streams[camera_id]["connection"].release()

    async def _handle_http_stream(self, camera_id: str, config: CameraConfig):
        """Handle HTTP/IP camera stream"""
        try:
            import aiohttp
            
            auth = None
            if config.username and config.password:
                auth = aiohttp.BasicAuth(config.username, config.password)
            
            timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)
            
            async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                self.active_streams[camera_id]["connection"] = session
                
                async with session.get(config.url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP camera returned status {response.status}")
                    
                    logger.info(f"HTTP camera {camera_id} connected to {config.url}")
                    self.active_streams[camera_id]["status"] = "connected"
                    
                    # Read MJPEG stream
                    async for chunk in response.content.iter_chunked(8192):
                        if camera_id not in self.active_streams:
                            break
                        
                        # Basic MJPEG frame extraction (simplified)
                        # In production, use proper MJPEG parser
                        if b'\xff\xd8' in chunk and b'\xff\xd9' in chunk:
                            self.active_streams[camera_id]["last_frame"] = datetime.utcnow()
                        
                        await asyncio.sleep(1.0 / config.fps)
                        
        except asyncio.CancelledError:
            logger.info(f"HTTP camera handler for {camera_id} cancelled")
        except Exception as e:
            logger.error(f"Error in HTTP camera handler for {camera_id}: {str(e)}")
            if camera_id in self.active_streams:
                self.active_streams[camera_id]["status"] = "error"

    async def _handle_websocket_stream(self, camera_id: str, config: CameraConfig):
        """Handle WebSocket camera stream"""
        try:
            import websockets
            
            uri = config.url.replace("http://", "ws://").replace("https://", "wss://")
            
            async with websockets.connect(uri) as websocket:
                self.active_streams[camera_id]["connection"] = websocket
                logger.info(f"WebSocket camera {camera_id} connected to {uri}")
                self.active_streams[camera_id]["status"] = "connected"
                
                async for message in websocket:
                    if camera_id not in self.active_streams:
                        break
                    
                    # Handle binary frame data
                    if isinstance(message, bytes):
                        self.active_streams[camera_id]["last_frame"] = datetime.utcnow()
                        # Process frame data here
                    
                    await asyncio.sleep(1.0 / config.fps)
                    
        except asyncio.CancelledError:
            logger.info(f"WebSocket camera handler for {camera_id} cancelled")
        except Exception as e:
            logger.error(f"Error in WebSocket camera handler for {camera_id}: {str(e)}")
            if camera_id in self.active_streams:
                self.active_streams[camera_id]["status"] = "error"