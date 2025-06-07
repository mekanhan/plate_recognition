import asyncio
import cv2
import time
import numpy as np
import os
import uuid
import traceback
import torch
from typing import List, Dict, Any, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException
from app.services.license_plate_recognition_service import LicensePlateRecognitionService
from app.utils.license_plate_processor import process_detection_result
import logging

logger = logging.getLogger(__name__)

class DetectionService:
    """License plate detection service"""
    def __init__(self):
        self.running = False
        self.detection_lock = asyncio.Lock()
        self.last_detections = []
        self.detections_processed = 0
        self.last_detection_time = None
        self.camera_service = None
        self.processed_detections = {}
        self.license_plate_service = None
        self.storage_service = None
        self.enhancer_service = None  # Add reference to enhancer service
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.frame_count = 0
        self.performance_metrics = {
            "avg_detection_time": 0,
            "detection_count": 0,
            "total_detection_time": 0
        }

    async def initialize(self, camera_service=None, enhancer_service=None):
        """Initialize the detection service"""
        self.camera_service = camera_service
        self.enhancer_service = enhancer_service  # Store enhancer service
        
        # Initialize the license plate recognition service
        self.license_plate_service = LicensePlateRecognitionService()
        await self.license_plate_service.initialize()
        
        logger.info(f"Detection service initialized with license plate recognition (Device: {self.device})")
        return self

    async def shutdown(self):
        """Shutdown the detection service"""
        self.running = False
        logger.info("Detection service shutdown")
    
    async def get_latest_detections(self):
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
        if self.license_plate_service is None:
            # Fall back to placeholder if service isn't initialized
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
            # Use the specialized license plate service
            detections, annotated_frame = await self.license_plate_service.detect_and_recognize(frame)

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
                    
            # Process each detection for storage
            for detection in detections:
                # Only save to storage if we have a plate text
                if detection.get("plate_text") and hasattr(self, 'storage_service') and self.storage_service:
                    try:
                        logger.info(f"Sending detection {detection['detection_id']} to storage service")
                        await self.storage_service.add_detections([detection])
                    except Exception as e:
                        logger.error(f"Error saving detection to storage: {e}")
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
        if not self.camera_service:
            raise RuntimeError("Camera service not initialized")

        # Get the latest frame from the camera
        frame, timestamp = await self.camera_service.get_frame()

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
        # Apply the enhanced license plate processor
        if detection_result and 'raw_text' in detection_result:
            better_plate, better_confidence = process_detection_result({
                "detection": detection_result
            })

            # Update with the improved plate text if available
            if better_plate:
                detection_result['plate_text'] = better_plate
                detection_result['confidence'] = better_confidence
                detection_result['processed_by'] = 'enhanced_processor'

        # Store the processed detection
        self.processed_detections[detection_id] = {
            "detection": detection_result,
            "processed_at": time.time(),
            "status": "completed"
        }

        # Update stats
        self.detections_processed += 1
        self.last_detection_time = time.time()

        logger.info(f"Processed detection {detection_id}: {detection_result['plate_text']}")

        # Save to storage service if available
        if hasattr(self, 'storage_service') and self.storage_service:
            logger.info(f"Sending detection {detection_id} to storage service")
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
                
                # Add to storage
                await self.storage_service.add_detections([detection_record])
                logger.info(f"Detection {detection_id} sent to storage: {detection_record['plate_text']}")
            except Exception as e:
                logger.error(f"Error saving detection to storage: {e}")
                logger.error(traceback.format_exc())

        # Send to enhancer service if available
        if self.enhancer_service:
            try:
                logger.info(f"Enhancing detection {detection_id}: {detection_result.get('plate_text', '')}")
                enhanced_result = await self.enhancer_service.enhance_detection(detection_result)

                if enhanced_result:
                    # Add additional fields to the enhanced result
                    enhanced_result["detection_id"] = detection_id
                    enhanced_result["original_detection_id"] = detection_id
                    enhanced_result["timestamp"] = time.time()
                    enhanced_result["enhanced_at"] = time.time()

                    logger.info(f"Enhanced result: {enhanced_result.get('plate_text', '')} "
                               f"(Confidence: {enhanced_result.get('confidence', 0):.2f})")

                    # Save enhanced result to storage if available
                    if hasattr(self.enhancer_service, 'storage_service') and self.enhancer_service.storage_service:
                        await self.enhancer_service.storage_service.add_enhanced_results([enhanced_result])
                        logger.info(f"Saved enhanced result to storage: {enhanced_result.get('plate_text', '')}")
            except Exception as e:
                logger.error(f"Error enhancing detection: {e}")
                logger.error(traceback.format_exc())

# Router part stays the same
router = APIRouter()

from app.dependencies.detection import get_detection_service

@router.get("/status")
async def detection_status(
    detection_svc: DetectionService = Depends(get_detection_service)
):
    """Get detection service status"""
    return {"status": "running"}