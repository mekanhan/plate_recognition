"""
Enhanced Processing Pipeline
Orchestrates all vehicle detection and analysis
"""
import asyncio
import time
import uuid
import os
import json
from datetime import datetime
from typing import List, Dict
import logging
import cv2
import numpy as np

from ...core.types import Detection, ProcessingResult
from .license_plate import LicensePlateModel
from ...core.storage_manager import StorageManager
from ...core.deduplication import DeduplicationManager, DetectionRecord
from ...core.object_tracker import SimpleObjectTracker


class EnhancedProcessingPipeline:
    """Enhanced pipeline that orchestrates all AI models with smart storage"""
    
    def __init__(self):
        self.logger = logging.getLogger("ProcessingPipeline")
        
        # Initialize models
        self.lpr_model = LicensePlateModel()
        
        # Load configuration if available
        config = self._load_config()
        
        # Initialize smart storage components with config
        self.storage_manager = StorageManager(config.get('storage_manager'))
        self.dedup_manager = DeduplicationManager(config.get('deduplication'))
        self.object_tracker = SimpleObjectTracker(config.get('object_tracking'))
        
        # Performance tracking
        self.total_frames_processed = 0
        self.average_processing_time = 0.0
        
        # Log configuration
        self.logger.info(f"Deduplication config: cooldown={config.get('deduplication', {}).get('cooldown_minutes', 30)}min, "
                        f"max_per_hour={config.get('deduplication', {}).get('max_per_plate_per_hour', 2)}")
    
    def _load_config(self) -> Dict:
        """Load configuration from file if exists"""
        config_path = "config/storage_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.logger.info(f"Loaded storage config from {config_path}")
                    return config
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}, using defaults")
        return {}
    
    async def process_frame(self, camera_id: str, frame: np.ndarray) -> List[Detection]:
        """Process a single frame and return detections"""
        start_time = time.time()
        detections = []
        
        try:
            # Get predictions from LPR model
            predictions = self.lpr_model.predict(frame)
            
            vehicles = predictions.get('vehicles', [])
            plates = predictions.get('plates', [])
            
            # Log vehicle and plate detection counts
            if len(vehicles) > 0 or len(plates) > 0:
                self.logger.info(f"Frame analysis for {camera_id}: {len(vehicles)} vehicles, {len(plates)} plates detected")
            
            # Match plates to vehicles and create detections
            detections = await self._create_detections(
                camera_id, frame, vehicles, plates
            )
            
            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time)
            
            # Log detection results (always log for debugging)
            self.logger.info(f"Processed frame for {camera_id}: {len(detections)} detections in {processing_time:.1f}ms")
            
        except Exception as e:
            self.logger.error(f"Error processing frame for {camera_id}: {e}")
        
        return detections
    
    async def _create_detections(self, camera_id: str, frame: np.ndarray, 
                               vehicles, plates) -> List[Detection]:
        """Create Detection objects with smart deduplication"""
        detections = []
        timestamp = datetime.now()
        
        # Update object tracker with current detections
        detection_dicts = []
        for i, plate in enumerate(plates):
            vehicle = vehicles[i] if i < len(vehicles) else None
            detection_dicts.append({
                'bbox': plate.bbox,
                'confidence': plate.confidence,
                'object_type': 'plate',
                'plate_text': None  # Will be filled after OCR
            })
        
        # Get track IDs from object tracker
        tracked_detections = self.object_tracker.update(camera_id, detection_dicts)
        
        # Process all detected plates
        for i, plate in enumerate(plates):
            # Try to find corresponding vehicle (for vehicle-based plates)
            vehicle = vehicles[i] if i < len(vehicles) else None
            
            self.logger.info(f"Processing plate {i+1}/{len(plates)}: bbox={plate.bbox}, conf={plate.confidence:.2f}")
            
            # Read plate text
            plate_text, ocr_confidence = self.lpr_model.read_plate(frame, plate.bbox)
            
            self.logger.info(f"OCR result: text='{plate_text}', conf={ocr_confidence:.2f}")
            
            # Production-ready confidence thresholds with smart validation
            is_valid_detection = self._validate_detection(plate_text, ocr_confidence)
            
            if not is_valid_detection:
                self.logger.info(f"Skipping invalid detection: text='{plate_text}', ocr_conf={ocr_confidence:.2f}")
                continue
            
            self.logger.info(f"✅ Valid detection: text='{plate_text}', ocr_conf={ocr_confidence:.2f}")
            
            # Generate unique detection ID
            detection_id = str(uuid.uuid4())
            
            # Get track ID from tracker
            track_id = tracked_detections[i][0] if i < len(tracked_detections) else None
            
            # Create detection record for deduplication check
            detection_record = DetectionRecord(
                detection_id=detection_id,
                camera_id=camera_id,
                plate_text=plate_text,
                confidence=plate.confidence,
                ocr_confidence=ocr_confidence,
                timestamp=timestamp,
                vehicle_bbox=vehicle.bbox if vehicle else [0, 0, 0, 0],
                plate_bbox=plate.bbox
            )
            
            # Check with deduplication manager
            should_save, reason, group_id = self.dedup_manager.should_save_detection(detection_record)
            
            # Initialize paths
            frame_path = ""
            plate_image_path = ""
            
            # Only save images if deduplication allows
            if should_save:
                # Check storage before saving
                if self.storage_manager.check_storage_before_save():
                    frame_path, plate_image_path = self._save_detection_images(
                        camera_id, detection_id, frame,
                        vehicle.bbox if vehicle else [0, 0, 0, 0],
                        plate.bbox
                    )
                    self.logger.info(f"💾 Saved images for {plate_text} (reason: {reason})")
                else:
                    self.logger.warning(f"⚠️ Storage limit reached, skipping image save for {plate_text}")
                    should_save = False
            else:
                self.logger.info(f"🔄 Skipped image save for {plate_text} (reason: {reason})")
            
            # Create enhanced detection (always create DB record, just control image saving)
            detection = Detection(
                detection_id=detection_id,
                camera_id=camera_id,
                timestamp=timestamp,
                plate_text=plate_text,
                confidence=plate.confidence,
                vehicle_type=vehicle.vehicle_type if vehicle else 'standalone',
                vehicle_bbox=vehicle.bbox if vehicle else [0, 0, 0, 0],
                plate_bbox=plate.bbox,
                frame_path=frame_path,
                plate_image_path=plate_image_path,
                
                # Enhanced fields
                vehicle_color=vehicle.color if vehicle else 'unknown',
                vehicle_make=vehicle.make if vehicle else 'unknown',
                vehicle_model=vehicle.model if vehicle else 'unknown',
                ocr_confidence=ocr_confidence,
                plate_type=getattr(plate, 'plate_type', 'unknown'),
                plate_region=getattr(plate, 'region', 'unknown'),
                
                # Deduplication fields
                group_id=group_id,
                track_id=track_id,
                is_best_shot=detection_record.is_best_shot,
                image_saved=should_save,
                
                detection_metadata={
                    'vehicle_confidence': vehicle.confidence if vehicle else 0.0,
                    'plate_confidence': plate.confidence,
                    'processing_version': '2.0',
                    'detection_type': 'vehicle_based' if vehicle else 'full_frame',
                    'dedup_reason': reason
                }
            )
            
            detections.append(detection)
        
        # Periodic cleanup of old groups (every 100 frames)
        if self.total_frames_processed % 100 == 0:
            self.dedup_manager.cleanup_old_groups()
        
        return detections
    
    def _validate_detection(self, plate_text: str, ocr_confidence: float) -> bool:
        """Smart detection validation with multiple criteria"""
        # Basic confidence threshold
        if ocr_confidence < 0.2:
            return False
        
        # Text length validation
        if len(plate_text.strip()) < 2:
            return False
        
        # Character validation - license plates should contain alphanumeric characters
        import re
        clean_text = re.sub(r'[^A-Z0-9]', '', plate_text.upper())
        if len(clean_text) < 2:
            return False
        
        # State name detection (common US states)
        state_patterns = ['TEXAS', 'CALIFORNIA', 'FLORIDA', 'NEW YORK', 'ILLINOIS']
        if any(state in plate_text.upper() for state in state_patterns):
            # Lower confidence threshold for state names
            return ocr_confidence >= 0.15
        
        # Alphanumeric patterns (typical license plate format)
        alphanumeric_pattern = re.compile(r'^[A-Z0-9\s\-]{3,8}$')
        if alphanumeric_pattern.match(clean_text):
            return ocr_confidence >= 0.4  # Higher confidence for license plate numbers
        
        # Special case: single words that might be license plates
        if len(clean_text) >= 3 and clean_text.isalnum():
            return ocr_confidence >= 0.3
        
        # Default: require higher confidence for unknown patterns
        return ocr_confidence >= 0.5
    
    def _save_detection_images(self, camera_id: str, detection_id: str, frame: np.ndarray, 
                              vehicle_bbox: List[int], plate_bbox: List[int]) -> tuple:
        """Save full frame and cropped license plate images"""
        try:
            # Ensure detection directories exist
            frame_dir = "detections/frames"
            plate_dir = "detections/plates"
            os.makedirs(frame_dir, exist_ok=True)
            os.makedirs(plate_dir, exist_ok=True)
            
            # Generate filenames
            frame_filename = f"{detection_id}_frame.jpg"
            plate_filename = f"{detection_id}_plate.jpg"
            
            frame_path = os.path.join(frame_dir, frame_filename)
            plate_path = os.path.join(plate_dir, plate_filename)
            
            # Save full frame with detection bounding boxes
            frame_with_boxes = frame.copy()
            
            # Draw vehicle bounding box (green)
            if vehicle_bbox and len(vehicle_bbox) == 4:
                x1, y1, x2, y2 = vehicle_bbox
                cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(frame_with_boxes, 'Vehicle', (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw license plate bounding box (red)
            if plate_bbox and len(plate_bbox) == 4:
                x1, y1, x2, y2 = plate_bbox
                cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame_with_boxes, 'License Plate', (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Save full frame with annotations
            cv2.imwrite(frame_path, frame_with_boxes)
            
            # Extract and save license plate crop
            if plate_bbox and len(plate_bbox) == 4:
                x1, y1, x2, y2 = plate_bbox
                # Add padding
                padding = 10
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(frame.shape[1], x2 + padding)
                y2 = min(frame.shape[0], y2 + padding)
                
                plate_crop = frame[y1:y2, x1:x2]
                if plate_crop.size > 0:
                    cv2.imwrite(plate_path, plate_crop)
                else:
                    plate_path = ""
            else:
                plate_path = ""
            
            self.logger.info(f"Saved detection images: frame={frame_path}, plate={plate_path}")
            return frame_path, plate_path
            
        except Exception as e:
            self.logger.error(f"Failed to save detection images: {e}")
            return "", ""
    
    def _update_performance_metrics(self, processing_time_ms: float):
        """Update running performance metrics"""
        self.total_frames_processed += 1
        
        # Running average
        alpha = 0.1  # Smoothing factor
        if self.average_processing_time == 0:
            self.average_processing_time = processing_time_ms
        else:
            self.average_processing_time = (
                alpha * processing_time_ms + 
                (1 - alpha) * self.average_processing_time
            )
    
    def get_performance_stats(self) -> Dict:
        """Get processing performance statistics"""
        return {
            'total_frames_processed': self.total_frames_processed,
            'average_processing_time_ms': round(self.average_processing_time, 2),
            'estimated_fps': round(1000 / self.average_processing_time, 1) if self.average_processing_time > 0 else 0,
            'models_loaded': {
                'lpr_model': self.lpr_model.is_loaded if self.lpr_model else False
            }
        }