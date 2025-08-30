"""
Detection Processor with Filtering Integration

This module integrates the detection filter with the existing AI pipeline
to reduce duplicate detections while maintaining compatibility.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import time

from ai_features.core.types import Detection
from database.service import DatabaseService
from .detection_filter import get_detection_filter

logger = logging.getLogger(__name__)


class FilteredDetectionProcessor:
    """
    Processes detections from AI pipeline with deduplication filtering.
    """
    
    def __init__(self):
        # Get the global detection filter
        self.filter = get_detection_filter()
        logger.info("Initialized filtered detection processor")
    
    async def process_detection(
        self,
        detection: Detection,
        camera_id: str,
        frame_timestamp: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Process a detection through the filter and save if appropriate.
        
        Args:
            detection: Detection object from AI pipeline
            camera_id: Camera identifier
            frame_timestamp: Timestamp of the frame
            
        Returns:
            Detection ID if stored, None if filtered out
        """
        try:
            # Prepare detection for filter
            filter_detection = {
                'plate': detection.plate_text,
                'confidence': detection.confidence,
                'timestamp': frame_timestamp.timestamp() if frame_timestamp else datetime.now().timestamp()
            }
            
            # Add position from bounding box
            if detection.plate_bbox:
                bbox = detection.plate_bbox
                if len(bbox) >= 4:
                    # Use center point of bounding box
                    filter_detection['x'] = (bbox[0] + bbox[2]) // 2
                    filter_detection['y'] = (bbox[1] + bbox[3]) // 2
                    filter_detection['width'] = bbox[2] - bbox[0]
                    filter_detection['height'] = bbox[3] - bbox[1]
            
            # Check if we should store this detection
            should_store, reason = self.filter.should_store(filter_detection, camera_id)
            
            if should_store:
                # Save to database
                detection_id = await self._save_detection(
                    detection,
                    camera_id,
                    frame_timestamp,
                    reason  # Store the reason for analytics
                )
                
                logger.info(
                    f"Stored detection: plate={detection.plate_text} "
                    f"reason={reason} id={detection_id}"
                )
                
                return detection_id
            else:
                logger.debug(
                    f"Filtered detection: plate={detection.plate_text} "
                    f"reason={reason}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error processing detection: {e}")
            return None
    
    async def process_detections_batch(
        self,
        detections: List[Detection],
        camera_id: str,
        frame_timestamp: Optional[datetime] = None
    ) -> List[Optional[str]]:
        """Process multiple detections in a batch."""
        results = []
        for detection in detections:
            result = await self.process_detection(detection, camera_id, frame_timestamp)
            results.append(result)
        return results
    
    async def _save_detection(
        self,
        detection: Detection,
        camera_id: str,
        timestamp: Optional[datetime],
        filter_reason: str
    ) -> str:
        """Save detection to database with filter metadata."""
        
        db_service = None
        try:
            db_service = DatabaseService()
            
            # Prepare detection data for original detections table
            detection_data = {
                'camera_id': camera_id,
                'plate_text': detection.plate_text.upper(),  # Ensure uppercase for consistency
                'confidence': detection.confidence,
                'vehicle_type': detection.vehicle_type,
                'detected_at': timestamp or datetime.now(),
                'vehicle_bbox': detection.vehicle_bbox,
                'plate_bbox': detection.plate_bbox,
                'frame_path': getattr(detection, 'frame_path', ''),
                'plate_image_path': getattr(detection, 'plate_image_path', ''),
                'ocr_confidence': detection.ocr_confidence,
                'meta_data': {
                    'filter_reason': filter_reason,
                    'processing_time': getattr(detection, 'processing_time', 0),
                    'model_version': getattr(detection, 'model_version', '2.0')
                }
            }
            
            # Save using the database service
            detection_id = await db_service.save_detection(detection_data)
            
            logger.debug(f"Successfully saved detection {detection_id} to database")
            
            return detection_id
            
        except Exception as e:
            logger.error(f"Error saving detection to database: {e}")
            raise
        finally:
            # Ensure database connection is closed
            if db_service:
                try:
                    await db_service.close()
                except Exception as close_error:
                    logger.error(f"Error closing database connection: {close_error}")
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get filtering statistics."""
        return self.filter.get_stats()
    
    def get_camera_status(self, camera_id: str) -> Dict[str, Any]:
        """Get current tracking status for a camera."""
        return self.filter.get_camera_summary(camera_id)
    
    def reset_camera_tracking(self, camera_id: str):
        """Clear tracking history for a camera (useful for testing)."""
        self.filter.clear_camera(camera_id)
        logger.info(f"Reset tracking for camera {camera_id}")


# Global processor instance
_processor_instance = None


def get_filtered_detection_processor() -> FilteredDetectionProcessor:
    """Get the global filtered detection processor instance."""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = FilteredDetectionProcessor()
        logger.info("Initialized global filtered detection processor")
    return _processor_instance