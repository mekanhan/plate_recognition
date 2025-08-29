"""
Integration example for detection filter with your AI pipeline

Place this in your ai_pipeline service or create a new file like:
ai_pipeline/detection_processor.py
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Your existing imports
from database import Database, Detection
from detection_filter import DetectionFilter

# For production Redis support (optional)
# import redis
# redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

logger = logging.getLogger(__name__)

class DetectionProcessor:
    """
    Processes detections from AI pipeline with deduplication filtering.
    """
    
    def __init__(self, db_path: str = "lpr_system.db"):
        # Initialize database
        self.db = Database(db_path)
        
        # Initialize detection filter
        self.filter = DetectionFilter(
            duplicate_window_seconds=30,      # Ignore duplicates within 30s
            position_threshold=100,           # 100 pixel movement threshold  
            confidence_improvement_threshold=0.10,  # 10% confidence improvement
            exit_timeout_seconds=60,          # Consider gone after 60s
            memory_duration_seconds=300       # Keep history for 5 minutes
        )
        
        # For production with Redis:
        # self.filter = RedisDetectionFilter(
        #     redis_client,
        #     duplicate_window_seconds=30,
        #     ...
        # )
        
        logger.info("Detection processor initialized with filtering")
    
    async def process_detection(
        self,
        detection_data: Dict[str, Any],
        camera_id: str,
        frame_timestamp: Optional[datetime] = None
    ) -> Optional[int]:
        """
        Process a detection through the filter and save if appropriate.
        
        Args:
            detection_data: Dictionary containing detection info:
                - plate: License plate text
                - confidence: Detection confidence (0-1)
                - bbox: Bounding box [x1, y1, x2, y2]
                - vehicle_bbox: Optional vehicle bounding box
                - image_path: Path to detection image
            camera_id: Camera identifier
            frame_timestamp: Timestamp of the frame
            
        Returns:
            Detection ID if stored, None if filtered out
        """
        try:
            # Prepare detection for filter
            filter_detection = {
                'plate': detection_data.get('plate', ''),
                'confidence': detection_data.get('confidence', 0),
                'timestamp': frame_timestamp.timestamp() if frame_timestamp else datetime.now().timestamp()
            }
            
            # Add position from bounding box
            if 'bbox' in detection_data and detection_data['bbox']:
                bbox = detection_data['bbox']
                # Use center point of bounding box
                filter_detection['x'] = (bbox[0] + bbox[2]) // 2
                filter_detection['y'] = (bbox[1] + bbox[3]) // 2
                filter_detection['width'] = bbox[2] - bbox[0]
                filter_detection['height'] = bbox[3] - bbox[1]
            
            # Check if we should store this detection
            should_store, reason = self.filter.should_store(filter_detection, camera_id)
            
            if should_store:
                # Save to database
                detection_id = self._save_detection(
                    detection_data,
                    camera_id,
                    frame_timestamp,
                    reason  # Store the reason for analytics
                )
                
                logger.info(
                    f"Stored detection: plate={detection_data.get('plate')} "
                    f"reason={reason} id={detection_id}"
                )
                
                return detection_id
            else:
                logger.debug(
                    f"Filtered detection: plate={detection_data.get('plate')} "
                    f"reason={reason}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error processing detection: {e}")
            return None
    
    def _save_detection(
        self,
        detection_data: Dict[str, Any],
        camera_id: str,
        timestamp: Optional[datetime],
        filter_reason: str
    ) -> int:
        """Save detection to database with filter metadata."""
        
        # Create detection object
        detection = Detection(
            camera_id=camera_id,
            timestamp=timestamp or datetime.now(),
            plate_number=detection_data.get('plate', 'Unknown'),
            confidence=detection_data.get('confidence', 0),
            vehicle_type=detection_data.get('vehicle_type', 'Unknown'),
            image_path=detection_data.get('image_path', ''),
            plate_bbox=str(detection_data.get('bbox', [])),
            vehicle_bbox=str(detection_data.get('vehicle_bbox', [])),
            metadata={
                'filter_reason': filter_reason,
                'processing_time': detection_data.get('processing_time', 0)
            }
        )
        
        # Save to database
        return self.db.add_detection(detection)
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get filtering statistics."""
        stats = self.filter.get_stats()
        
        # Add database stats
        stats['db_total_detections'] = self.db.get_detection_count()
        
        return stats
    
    def get_camera_status(self, camera_id: str) -> Dict[str, Any]:
        """Get current tracking status for a camera."""
        return self.filter.get_camera_summary(camera_id)
    
    def reset_camera_tracking(self, camera_id: str):
        """Clear tracking history for a camera (useful for testing)."""
        self.filter.clear_camera(camera_id)
        logger.info(f"Reset tracking for camera {camera_id}")

# Integration with your existing AI pipeline
class EnhancedDetectionPipeline:
    """
    Example of integrating the filter with your existing pipeline.
    """
    
    def __init__(self):
        self.processor = DetectionProcessor()
        # Your existing AI models...
        
    async def process_frame(self, frame, camera_id: str):
        """Process a single frame with filtering."""
        
        # Your existing detection logic
        detections = self.run_yolo_detection(frame)
        
        stored_count = 0
        for detection in detections:
            # Extract license plate
            plate_info = self.run_ocr(detection)
            
            # Process through filter
            detection_id = await self.processor.process_detection(
                {
                    'plate': plate_info['text'],
                    'confidence': plate_info['confidence'],
                    'bbox': detection['bbox'],
                    'image_path': detection['cropped_image_path']
                },
                camera_id=camera_id
            )
            
            if detection_id:
                stored_count += 1
        
        return stored_count
    
    def run_yolo_detection(self, frame):
        """Your existing YOLO detection code."""
        # ... existing code ...
        pass
    
    def run_ocr(self, detection):
        """Your existing OCR code."""
        # ... existing code ...
        pass

# API endpoint example (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
processor = DetectionProcessor()

class DetectionRequest(BaseModel):
    camera_id: str
    plate: str
    confidence: float
    bbox: list
    timestamp: Optional[datetime] = None

@app.post("/api/detection")
async def add_detection(detection: DetectionRequest):
    """Process a detection through the filter."""
    detection_id = await processor.process_detection(
        detection.dict(),
        detection.camera_id,
        detection.timestamp
    )
    
    if detection_id:
        return {"status": "stored", "detection_id": detection_id}
    else:
        return {"status": "filtered", "detection_id": None}

@app.get("/api/stats")
async def get_stats():
    """Get filtering statistics."""
    return processor.get_filter_stats()

@app.get("/api/camera/{camera_id}/tracking")
async def get_camera_tracking(camera_id: str):
    """Get current tracking status for a camera."""
    return processor.get_camera_status(camera_id)

# Background task for monitoring (optional)
async def print_stats_periodically():
    """Print statistics every minute for monitoring."""
    while True:
        await asyncio.sleep(60)
        stats = processor.get_filter_stats()
        logger.info(f"Filter Stats: {stats}")

# Testing script
if __name__ == "__main__":
    import time
    
    async def test_filtering():
        processor = DetectionProcessor(":memory:")  # In-memory DB for testing
        
        # Simulate a car parking scenario
        test_detections = [
            # Car arrives
            {"plate": "ABC123", "confidence": 0.85, "bbox": [100, 200, 200, 250]},
            # Same car, 5 seconds later (should be filtered)
            {"plate": "ABC123", "confidence": 0.86, "bbox": [102, 201, 202, 251]},
            # Same car, better image (should update)
            {"plate": "ABC123", "confidence": 0.96, "bbox": [101, 200, 201, 250]},
            # Different car
            {"plate": "XYZ789", "confidence": 0.92, "bbox": [300, 400, 400, 450]},
            # First car leaves and returns (after 70s)
            {"plate": "ABC123", "confidence": 0.88, "bbox": [500, 600, 600, 650]},
        ]
        
        print("Testing detection filtering...\n")
        
        for i, detection in enumerate(test_detections):
            # Add timestamp
            detection['timestamp'] = datetime.now()
            
            # Process detection
            detection_id = await processor.process_detection(
                detection,
                "test_camera_01",
                detection['timestamp']
            )
            
            print(f"Detection {i+1}: Plate={detection['plate']}, "
                  f"Stored={'Yes' if detection_id else 'No'}")
            
            # Wait between detections
            if i < len(test_detections) - 2:
                await asyncio.sleep(2)
            elif i == len(test_detections) - 2:
                # Wait longer before last detection
                print("\nWaiting 70 seconds for exit timeout...\n")
                await asyncio.sleep(70)
        
        # Print final statistics
        print("\n--- Final Statistics ---")
        stats = processor.get_filter_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Show camera tracking status
        print("\n--- Camera Tracking Status ---")
        print(processor.get_camera_status("test_camera_01"))
    
    # Run test
    asyncio.run(test_filtering())
