import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable
import numpy as np

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