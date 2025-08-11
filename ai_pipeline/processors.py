"""
AI Processing Pipeline - Legacy Interface
BACKWARD COMPATIBILITY: This file maintains the existing interface
while delegating to the new organized ai_features modules
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np
import logging
from datetime import datetime
import uuid

# Import from the new organized structure
from ai_features.core.types import Detection, VehicleInfo
from ai_features.vehicle.detection.license_plate import LicensePlateModel
from ai_features.vehicle.detection.pipeline import EnhancedProcessingPipeline

# Re-export Detection for backward compatibility
__all__ = ['Detection', 'LicensePlateDetector', 'ProcessingPipeline']


class LicensePlateDetector:
    """
    Legacy LicensePlateDetector - Facade Pattern
    
    BACKWARD COMPATIBILITY: Maintains exact same interface while 
    delegating to the new enhanced LicensePlateModel
    """
    
    def __init__(self, 
                 vehicle_model_path: str = "yolov8m.pt",
                 plate_model_path: str = "yolo11m_best.pt",
                 device: str = None):
        
        # Delegate to new implementation
        self._model = LicensePlateModel(vehicle_model_path, plate_model_path, device)
        self.logger = logging.getLogger("LPDetector")
        
        # Maintain backward compatibility properties
        self.device = self._model.device
        
        # These properties are accessed by legacy code
        self.vehicle_model = None  # Will be set when model loads
        self.plate_model = None    # Will be set when model loads
        self.ocr_reader = None     # Will be set when model loads
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    
    def _ensure_loaded(self):
        """Ensure the model is loaded and set legacy properties"""
        if not self._model.is_loaded:
            self._model.load()
            # Set legacy properties for backward compatibility
            self.vehicle_model = self._model.vehicle_model
            self.plate_model = self._model.plate_model  
            self.ocr_reader = self._model.ocr_reader
    
    def detect_vehicles(self, frame: np.ndarray) -> List[Dict]:
        """Detect vehicles in frame - legacy format"""
        self._ensure_loaded()
        
        # Get vehicles from new model
        vehicles_info = self._model.detect_vehicles(frame)
        
        # Convert to legacy format
        vehicles = []
        for vehicle_info in vehicles_info:
            vehicles.append({
                'bbox': vehicle_info.bbox,
                'confidence': vehicle_info.confidence,
                'class': vehicle_info.vehicle_type
            })
        
        return vehicles
    
    def detect_plates(self, frame: np.ndarray, vehicles: List[Dict]) -> List[Dict]:
        """Detect license plates within vehicle bounding boxes - legacy format"""
        self._ensure_loaded()
        
        # Convert legacy vehicle format to VehicleInfo
        vehicle_infos = []
        for vehicle in vehicles:
            vehicle_info = VehicleInfo(
                vehicle_type=vehicle['class'],
                color='unknown',
                confidence=vehicle['confidence'],
                bbox=vehicle['bbox']
            )
            vehicle_infos.append(vehicle_info)
        
        # Get plates from new model
        plates_info = self._model.detect_plates(frame, vehicle_infos)
        
        # Convert to legacy format
        plates = []
        for i, plate_info in enumerate(plates_info):
            vehicle = vehicles[i] if i < len(vehicles) else vehicles[0]
            plates.append({
                'vehicle_bbox': vehicle['bbox'],
                'plate_bbox': plate_info.bbox,
                'confidence': plate_info.confidence,
                'vehicle_type': vehicle['class']
            })
        
        return plates
    
    def read_plate(self, frame: np.ndarray, plate_bbox: List[int]) -> Tuple[str, float]:
        """Read license plate text using OCR - enhanced version"""
        self._ensure_loaded()
        
        # Use enhanced OCR from new model
        return self._model.read_plate(frame, plate_bbox)


class ProcessingPipeline:
    """
    Legacy ProcessingPipeline - Facade Pattern
    
    BACKWARD COMPATIBILITY: Maintains exact same interface while
    using the new enhanced pipeline
    """
    
    def __init__(self, detector: LicensePlateDetector):
        self.detector = detector
        self.logger = logging.getLogger("ProcessingPipeline")
        
        # Use new enhanced pipeline internally
        self._pipeline = EnhancedProcessingPipeline()
        
        # Thread executor for async compatibility
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_frame(self, camera_id: str, frame: np.ndarray) -> List[Detection]:
        """Process frame and return detections - enhanced version"""
        try:
            self.logger.info(f"Legacy facade: Processing frame for {camera_id} via enhanced pipeline")
            # Use the new enhanced pipeline
            detections = await self._pipeline.process_frame(camera_id, frame)
            self.logger.info(f"Legacy facade: Enhanced pipeline returned {len(detections)} detections")
            return detections
            
        except Exception as e:
            self.logger.error(f"Processing error for camera {camera_id}: {e}")
            return []
    
    def _process_frame_sync(self, camera_id: str, frame: np.ndarray) -> List[Detection]:
        """
        Legacy synchronous method - maintained for backward compatibility
        """
        detections = []
        timestamp = datetime.now()
        
        try:
            # Detect vehicles using legacy detector interface
            vehicles = self.detector.detect_vehicles(frame)
            if not vehicles:
                return detections
            
            # Detect plates using legacy detector interface
            plates = self.detector.detect_plates(frame, vehicles)
            
            for plate_info in plates:
                # Read plate text using legacy detector interface
                plate_text, confidence = self.detector.read_plate(frame, plate_info['plate_bbox'])
                
                # Skip low confidence or empty plates
                if confidence < 0.5 or len(plate_text) < 4:
                    continue
                
                # Generate unique ID
                detection_id = str(uuid.uuid4())
                
                # Create detection with enhanced fields (backward compatible)
                detection = Detection(
                    detection_id=detection_id,
                    camera_id=camera_id,
                    timestamp=timestamp,
                    plate_text=plate_text,
                    confidence=plate_info['confidence'],
                    vehicle_type=plate_info['vehicle_type'],
                    vehicle_bbox=plate_info['vehicle_bbox'],
                    plate_bbox=plate_info['plate_bbox'],
                    
                    # Enhanced fields with defaults (backward compatible)
                    ocr_confidence=confidence,
                    detection_metadata={
                        'processing_version': '2.0',
                        'legacy_compatibility': True
                    }
                )
                
                detections.append(detection)
                
        except Exception as e:
            self.logger.error(f"Synchronous processing error for {camera_id}: {e}")
        
        return detections