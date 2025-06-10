"""
Improved detection service using interfaces for dependency injection.
"""
import asyncio
import cv2
import time
import numpy as np
import os
import uuid
import traceback
from typing import List, Dict, Any, Optional, Tuple
import logging

from app.interfaces.camera import Camera
from app.interfaces.detector import LicensePlateDetector
from app.interfaces.enhancer import LicensePlateEnhancer
from app.interfaces.storage import DetectionRepository, EnhancementRepository

logger = logging.getLogger(__name__)

class DetectionServiceV2:
    """Improved license plate detection service using interfaces"""
    
    def __init__(self):
        self.running = False
        self.detection_lock = asyncio.Lock()
        self.last_detections = []
        self.detections_processed = 0
        self.last_detection_time = None
        self.processed_detections = {}
        self.frame_count = 0
        self.performance_metrics = {
            "avg_detection_time": 0,
            "detection_count": 0,
            "total_detection_time": 0
        }
        
        # These will be set during initialization
        self.camera: Optional[Camera] = None
        self.detector: Optional[LicensePlateDetector] = None
        self.detection_repository: Optional[DetectionRepository] = None
        self.enhancer: Optional[LicensePlateEnhancer] = None
        self.enhancement_repository: Optional[EnhancementRepository] = None
    
    async def initialize(self, 
                        camera: Camera = None,
                        detector: LicensePlateDetector = None,
                        detection_repository: DetectionRepository = None,
                        enhancer: LicensePlateEnhancer = None,
                        enhancement_repository: EnhancementRepository = None,
                        video_recording_service = None) -> None:
        """
        Initialize the detection service with required dependencies.
        
        Args:
            camera: Camera interface for frame capture
            detector: License plate detector for processing frames
            detection_repository: Repository for storing detections
            enhancer: License plate enhancer for post-processing
            enhancement_repository: Repository for storing enhanced results
            video_recording_service: Service for video recording
        """
        # Store dependencies
        self.camera = camera
        self.detector = detector
        self.detection_repository = detection_repository
        self.enhancer = enhancer
        self.enhancement_repository = enhancement_repository
        self.video_recording_service = video_recording_service
        
        # Validate required dependencies
        if not self.camera:
            raise ValueError("Camera is required")
        
        if not self.detector:
            raise ValueError("Detector is required")
        
        if not self.detection_repository:
            raise ValueError("Detection repository is required")
        
        logger.info(f"Detection service initialized")
        return self
    
    async def shutdown(self) -> None:
        """Shutdown the detection service"""
        self.running = False
        logger.info("Detection service shutdown")
    
    async def get_latest_detections(self) -> List[Dict[str, Any]]:
        """Get the latest detections"""
        async with self.detection_lock:
            return self.last_detections.copy()
    
    async def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Process a single frame to detect license plates
        
        Args:
            frame: Input frame
            
        Returns:
            Tuple of processed frame and detection results
        """
        if not self.detector:
            return self._placeholder_detection(frame)
        
        # Make a copy to avoid modifying the original
        display_frame = frame.copy()
        
        # Add timestamp to the frame
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(display_frame, timestamp, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                   
        # Increment frame counter
        self.frame_count += 1
        
        try:
            # Use the detector to process the frame
            detections, annotated_frame = await self.detector.detect_and_recognize(frame)
            
            # Use the annotated frame for display
            display_frame = annotated_frame
            
            # Add tracking IDs and detection IDs to detections
            for detection in detections:
                # Generate a detection ID if not present
                if "detection_id" not in detection:
                    detection["detection_id"] = str(uuid.uuid4())
                    
                # Add frame timestamp
                if "timestamp" not in detection:
                    detection["timestamp"] = time.time()
                    
                # Add frame ID
                detection["frame_id"] = self.frame_count
            
            # Update latest detections for UI display if we have valid plate texts
            valid_detections = [d for d in detections if d.get("plate_text") and d.get("confidence", 0) > 0.4]
            if valid_detections:
                async with self.detection_lock:
                    # Add to latest detections (keep most recent 10)
                    self.last_detections.extend(valid_detections)
                    # Keep only the 10 most recent detections
                    self.last_detections = self.last_detections[-10:]
            
            # Process each detection for storage and video recording
            if valid_detections and self.detection_repository:
                try:
                    logger.info(f"Sending {len(valid_detections)} detections to storage repository")
                    await self.detection_repository.add_detections(valid_detections)
                    
                    # Trigger video recording for each detection if video service is available
                    if self.video_recording_service:
                        for detection in valid_detections:
                            try:
                                detection_id = detection.get("detection_id")
                                if detection_id:
                                    logger.info(f"Triggering video recording for detection {detection_id}")
                                    await self.video_recording_service.trigger_recording(detection_id)
                            except Exception as e:
                                logger.error(f"Error triggering video recording: {e}")
                    
                    # Process with enhancer if available
                    if self.enhancer and self.enhancement_repository:
                        for detection in valid_detections:
                            try:
                                enhanced_result = await self.enhancer.enhance_detection(detection)
                                if enhanced_result:
                                    enhanced_result["detection_id"] = detection.get("detection_id")
                                    enhanced_result["original_detection_id"] = detection.get("detection_id")
                                    enhanced_result["timestamp"] = time.time()
                                    enhanced_result["enhanced_at"] = time.time()
                                    
                                    await self.enhancement_repository.add_enhanced_results([enhanced_result])
                                    logger.info(f"Enhanced detection {detection.get('detection_id')}: {enhanced_result.get('plate_text', '')}")
                            except Exception as e:
                                logger.error(f"Error enhancing detection: {e}")
                                
                except Exception as e:
                    logger.error(f"Error saving detections to repository: {e}")
                    logger.error(traceback.format_exc())
            
            return display_frame, detections
            
        except Exception as e:
            logger.error(f"Error in license plate detection: {e}")
            logger.error(traceback.format_exc())
            # Fall back to placeholder on error
            return self._placeholder_detection(frame)
    
    def _placeholder_detection(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Placeholder detection when service isn't available"""
        # Make a copy to avoid modifying the original
        display_frame = frame.copy()
        
        # Add timestamp to the frame
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(display_frame, timestamp, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Create a mock detection result
        height, width = frame.shape[:2]
        x1, y1 = int(width * 0.4), int(height * 0.6)
        x2, y2 = int(width * 0.6), int(height * 0.7)
        
        # Draw rectangle and text
        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(display_frame, "ABC123", (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        detection_id = str(uuid.uuid4())
        detections = [{
            "detection_id": detection_id,
            "plate_text": "ABC123",
            "confidence": 0.85,
            "box": [x1, y1, x2, y2],
            "timestamp": time.time(),
            "frame_id": self.frame_count,
            "ocr_confidence": 0.85,
            "state": "CA"
        }]
        
        return display_frame, detections
    
    async def detect_from_camera(self) -> Dict[str, Any]:
        """
        Detect license plate from the current camera frame
        
        Returns:
            Dict with detection results
        """
        if not self.camera:
            raise RuntimeError("Camera service not initialized")
        
        # Get the latest frame from the camera
        frame, timestamp = await self.camera.get_frame()
        
        # Process the frame
        processed_frame, detections = await self.process_frame(frame)
        
        if not detections:
            return None
        
        # Update detection stats
        self.last_detection_time = time.time()
        
        # Return the first detection
        return detections[0]
    
    async def detect_from_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Detect license plate from an uploaded image
        
        Args:
            image_data: Image bytes
            
        Returns:
            Dict with detection results
        """
        # Convert bytes to image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise RuntimeError("Could not decode image")
        
        # Process the image
        processed_frame, detections = await self.process_frame(img)
        
        if not detections:
            return None
        
        # Update detection stats
        self.last_detection_time = time.time()
        
        # Return the first detection
        return detections[0]
    
    async def process_detection(self, detection_id: str, detection_result: Dict[str, Any]) -> None:
        """
        Process a detection (background task)
        
        Args:
            detection_id: Unique detection ID
            detection_result: Detection result dict
        """
        # Store the processed detection
        self.processed_detections[detection_id] = {
            "detection": detection_result,
            "processed_at": time.time(),
            "status": "completed"
        }
        
        # Update latest detections for the UI
        async with self.detection_lock:
            # Add to latest detections (limit to 10 most recent)
            self.last_detections.append(detection_result)
            # Keep only the 10 most recent detections
            self.last_detections = self.last_detections[-10:]
        
        # Update stats
        self.detections_processed += 1
        self.last_detection_time = time.time()
        
        logger.info(f"Processed detection {detection_id}: {detection_result['plate_text']}")
        
        # Save to detection repository if available
        if self.detection_repository:
            logger.info(f"Sending detection {detection_id} to detection repository")
            try:
                # Create a properly formatted detection record
                detection_record = {
                    "detection_id": detection_id,
                    "timestamp": time.time(),
                    "plate_text": detection_result.get('plate_text', ''),
                    "raw_text": detection_result.get('raw_text', ''),
                    "confidence": detection_result.get('confidence', 0),
                    "state": detection_result.get('state', None),
                    "box": detection_result.get('box', []),
                    "frame_id": detection_result.get('frame_id', 0),
                    "tracking_id": detection_result.get('tracking_id', f"trk-{detection_id}"),
                    "status": "active",
                    "processed_at": time.time(),
                    "processed_by": detection_result.get('processed_by', 'detection_service')
                }
                
                # Add to repository
                await self.detection_repository.add_detections([detection_record])
                logger.info(f"Detection {detection_id} sent to repository: {detection_record['plate_text']}")
            except Exception as e:
                logger.error(f"Error saving detection to repository: {e}")
                logger.error(traceback.format_exc())
        
        # Send to enhancer if available
        if self.enhancer:
            try:
                logger.info(f"Enhancing detection {detection_id}: {detection_result.get('plate_text', '')}")
                enhanced_result = await self.enhancer.enhance_detection(detection_result)
                
                if enhanced_result and self.enhancement_repository:
                    # Add additional fields to the enhanced result
                    enhanced_result["detection_id"] = detection_id
                    enhanced_result["original_detection_id"] = detection_id
                    enhanced_result["timestamp"] = time.time()
                    enhanced_result["enhanced_at"] = time.time()
                    
                    logger.info(f"Enhanced result: {enhanced_result.get('plate_text', '')} "
                               f"(Confidence: {enhanced_result.get('confidence', 0):.2f})")
                    
                    # Save enhanced result to repository
                    await self.enhancement_repository.add_enhanced_results([enhanced_result])
                    logger.info(f"Saved enhanced result to repository: {enhanced_result.get('plate_text', '')}")
            except Exception as e:
                logger.error(f"Error enhancing detection: {e}")
                logger.error(traceback.format_exc())


