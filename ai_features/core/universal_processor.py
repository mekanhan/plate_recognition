"""
Universal Detection Processor
Supports detecting any object type, not just vehicles/license plates
"""
import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import cv2
import numpy as np
import logging

# Import existing core types
from .types import Detection


@dataclass
class UniversalDetectionResult:
    """Universal detection result that works for any object type"""
    object_type: str
    confidence: float
    bbox: Dict[str, int]  # {"x": 0, "y": 0, "width": 100, "height": 100}
    metadata: Dict[str, Any]
    frame: np.ndarray
    timestamp: datetime
    processing_time_ms: Optional[int] = None


class BaseDetector(ABC):
    """Abstract base class for all object detectors"""
    
    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[UniversalDetectionResult]:
        """Detect objects in frame"""
        pass
    
    @abstractmethod
    def get_object_type(self) -> str:
        """Return the object type this detector handles"""
        pass
    
    def is_loaded(self) -> bool:
        """Check if detector models are loaded"""
        return True


class VehicleDetector(BaseDetector):
    """Existing vehicle/license plate detector wrapped in new interface"""
    
    def __init__(self, existing_detector=None):
        self.detector = existing_detector
        self.logger = logging.getLogger("VehicleDetector")
        
        # Initialize if detector not provided
        if not self.detector:
            try:
                from ..vehicle.detection.license_plate import LicensePlateModel
                self.detector = LicensePlateModel()
                self.logger.info("Initialized new LicensePlateModel")
            except ImportError:
                # Fallback to legacy detector
                from ai_pipeline.processors import LicensePlateDetector
                self.detector = LicensePlateDetector()
                self.logger.info("Initialized legacy LicensePlateDetector")
    
    def detect(self, frame: np.ndarray) -> List[UniversalDetectionResult]:
        results = []
        timestamp = datetime.now()
        
        try:
            # Check if using new or legacy detector
            if hasattr(self.detector, 'predict'):
                # New LicensePlateModel interface
                predictions = self.detector.predict(frame)
                vehicles = predictions.get('vehicles', [])
                plates = predictions.get('plates', [])
                
                # Process detected plates
                for i, plate_info in enumerate(plates):
                    # Get corresponding vehicle if available
                    vehicle_info = vehicles[i] if i < len(vehicles) else None
                    
                    # Read plate text
                    plate_text, ocr_confidence = self.detector.read_plate(frame, plate_info.bbox)
                    
                    if ocr_confidence > 0.5 and len(plate_text.strip()) >= 2:
                        result = UniversalDetectionResult(
                            object_type='vehicle',
                            confidence=plate_info.confidence,
                            bbox={
                                "x": vehicle_info.bbox[0] if vehicle_info else plate_info.bbox[0],
                                "y": vehicle_info.bbox[1] if vehicle_info else plate_info.bbox[1],
                                "width": (vehicle_info.bbox[2] - vehicle_info.bbox[0]) if vehicle_info else (plate_info.bbox[2] - plate_info.bbox[0]),
                                "height": (vehicle_info.bbox[3] - vehicle_info.bbox[1]) if vehicle_info else (plate_info.bbox[3] - plate_info.bbox[1])
                            },
                            metadata={
                                "plate_text": plate_text,
                                "vehicle_type": vehicle_info.vehicle_type if vehicle_info else "unknown",
                                "vehicle_color": vehicle_info.color if vehicle_info else "unknown",
                                "plate_bbox": plate_info.bbox,
                                "vehicle_bbox": vehicle_info.bbox if vehicle_info else plate_info.bbox,
                                "ocr_confidence": ocr_confidence
                            },
                            frame=frame,
                            timestamp=timestamp
                        )
                        results.append(result)
            
            else:
                # Legacy interface
                vehicles = self.detector.detect_vehicles(frame)
                plates = self.detector.detect_plates(frame, vehicles)
                
                for plate_info in plates:
                    plate_text, ocr_confidence = self.detector.read_plate(frame, plate_info['plate_bbox'])
                    
                    if ocr_confidence > 0.5 and len(plate_text.strip()) >= 2:
                        result = UniversalDetectionResult(
                            object_type='vehicle',
                            confidence=plate_info['confidence'],
                            bbox={
                                "x": plate_info['vehicle_bbox'][0],
                                "y": plate_info['vehicle_bbox'][1],
                                "width": plate_info['vehicle_bbox'][2] - plate_info['vehicle_bbox'][0],
                                "height": plate_info['vehicle_bbox'][3] - plate_info['vehicle_bbox'][1]
                            },
                            metadata={
                                "plate_text": plate_text,
                                "vehicle_type": plate_info['vehicle_type'],
                                "plate_bbox": plate_info['plate_bbox'],
                                "vehicle_bbox": plate_info['vehicle_bbox'],
                                "ocr_confidence": ocr_confidence
                            },
                            frame=frame,
                            timestamp=timestamp
                        )
                        results.append(result)
        
        except Exception as e:
            self.logger.error(f"Error in vehicle detection: {e}")
        
        return results
    
    def get_object_type(self) -> str:
        return 'vehicle'


class PersonDetector(BaseDetector):
    """Person detection using YOLOv8"""
    
    def __init__(self, model_path='ai_pipeline/models/yolov8n.pt'):
        self.logger = logging.getLogger("PersonDetector")
        self.model = None
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model for person detection"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            self.logger.info(f"Loaded person detection model: {self.model_path}")
        except ImportError:
            self.logger.warning("ultralytics not available, person detection disabled")
        except Exception as e:
            self.logger.error(f"Failed to load person detection model: {e}")
    
    def detect(self, frame: np.ndarray) -> List[UniversalDetectionResult]:
        results = []
        timestamp = datetime.now()
        
        if not self.model:
            return results
        
        try:
            detections = self.model(frame, verbose=False)
            
            for r in detections:
                for box in r.boxes:
                    if int(box.cls) == 0:  # Person class in COCO
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        confidence = float(box.conf)
                        
                        if confidence > 0.5:  # Minimum confidence threshold
                            result = UniversalDetectionResult(
                                object_type='person',
                                confidence=confidence,
                                bbox={
                                    "x": int(x1),
                                    "y": int(y1),
                                    "width": int(x2 - x1),
                                    "height": int(y2 - y1)
                                },
                                metadata=self._analyze_person(frame[int(y1):int(y2), int(x1):int(x2)]),
                                frame=frame,
                                timestamp=timestamp
                            )
                            results.append(result)
        
        except Exception as e:
            self.logger.error(f"Error in person detection: {e}")
        
        return results
    
    def _analyze_person(self, person_crop):
        """Analyze person attributes (placeholder for actual implementation)"""
        # This could be enhanced with additional models for age, gender, clothing detection
        return {
            "age_range": "adult",
            "clothing": "dark clothing",
            "action": "walking"
        }
    
    def get_object_type(self) -> str:
        return 'person'
    
    def is_loaded(self) -> bool:
        return self.model is not None


class PackageDetector(BaseDetector):
    """Package detection using custom or pre-trained models"""
    
    def __init__(self, model_path='ai_pipeline/models/yolov8n.pt'):
        self.logger = logging.getLogger("PackageDetector")
        self.model = None
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model for package detection"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            self.logger.info(f"Loaded package detection model: {self.model_path}")
        except ImportError:
            self.logger.warning("ultralytics not available, package detection disabled")
        except Exception as e:
            self.logger.error(f"Failed to load package detection model: {e}")
    
    def detect(self, frame: np.ndarray) -> List[UniversalDetectionResult]:
        results = []
        timestamp = datetime.now()
        
        if not self.model:
            return results
        
        try:
            detections = self.model(frame, verbose=False)
            
            # Look for suitcase, handbag, backpack classes (24, 26, 27 in COCO)
            package_classes = [24, 26, 27]
            
            for r in detections:
                for box in r.boxes:
                    if int(box.cls) in package_classes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        confidence = float(box.conf)
                        
                        if confidence > 0.4:  # Lower threshold for packages
                            result = UniversalDetectionResult(
                                object_type='package',
                                confidence=confidence,
                                bbox={
                                    "x": int(x1),
                                    "y": int(y1),
                                    "width": int(x2 - x1),
                                    "height": int(y2 - y1)
                                },
                                metadata=self._analyze_package(frame[int(y1):int(y2), int(x1):int(x2)]),
                                frame=frame,
                                timestamp=timestamp
                            )
                            results.append(result)
        
        except Exception as e:
            self.logger.error(f"Error in package detection: {e}")
        
        return results
    
    def _analyze_package(self, package_crop):
        """Analyze package attributes"""
        # Estimate size based on crop dimensions
        height, width = package_crop.shape[:2]
        area = height * width
        
        if area < 5000:
            size = "small"
        elif area < 20000:
            size = "medium"
        else:
            size = "large"
        
        return {
            "size": size,
            "condition": "intact",
            "label_visible": False
        }
    
    def get_object_type(self) -> str:
        return 'package'
    
    def is_loaded(self) -> bool:
        return self.model is not None


class UniversalDetectionPipeline:
    """Orchestrates multiple detectors for universal object detection"""
    
    def __init__(self):
        self.logger = logging.getLogger("UniversalDetectionPipeline")
        self.detectors: Dict[str, BaseDetector] = {}
        self.active_detectors: List[str] = []
        self.performance_stats = {}
        
        # Initialize with default detectors
        self._initialize_detectors()
    
    def _initialize_detectors(self):
        """Initialize all available detectors"""
        try:
            # Always add vehicle detector (existing functionality)
            vehicle_detector = VehicleDetector()
            self.register_detector(vehicle_detector)
            self.enable_detector('vehicle')
            
            # Add person detector
            person_detector = PersonDetector()
            if person_detector.is_loaded():
                self.register_detector(person_detector)
                self.logger.info("Person detector available")
            
            # Add package detector
            package_detector = PackageDetector()
            if package_detector.is_loaded():
                self.register_detector(package_detector)
                self.logger.info("Package detector available")
            
        except Exception as e:
            self.logger.error(f"Error initializing detectors: {e}")
    
    def register_detector(self, detector: BaseDetector):
        """Register a new detector"""
        object_type = detector.get_object_type()
        self.detectors[object_type] = detector
        self.logger.info(f"Registered {object_type} detector")
    
    def enable_detector(self, object_type: str):
        """Enable a specific detector"""
        if object_type in self.detectors and object_type not in self.active_detectors:
            self.active_detectors.append(object_type)
            self.logger.info(f"Enabled {object_type} detector")
    
    def disable_detector(self, object_type: str):
        """Disable a specific detector"""
        if object_type in self.active_detectors:
            self.active_detectors.remove(object_type)
            self.logger.info(f"Disabled {object_type} detector")
    
    def get_available_detectors(self) -> List[str]:
        """Get list of available detector types"""
        return list(self.detectors.keys())
    
    def get_active_detectors(self) -> List[str]:
        """Get list of currently active detector types"""
        return self.active_detectors.copy()
    
    async def process_frame(self, camera_id: str, frame: np.ndarray) -> List[Dict]:
        """Process frame through all active detectors"""
        start_time = time.time()
        all_detections = []
        
        self.logger.debug(f"Processing frame for {camera_id} with {len(self.active_detectors)} active detectors")
        
        for object_type in self.active_detectors:
            detector = self.detectors[object_type]
            try:
                detector_start = time.time()
                detections = detector.detect(frame)
                detector_time = (time.time() - detector_start) * 1000
                
                self.logger.debug(f"{object_type} detector: {len(detections)} detections in {detector_time:.1f}ms")
                
                for detection in detections:
                    # Convert to database format
                    db_detection = {
                        'id': str(uuid.uuid4()),
                        'camera_id': camera_id,
                        'object_type': detection.object_type,
                        'confidence': detection.confidence,
                        'detected_at': detection.timestamp,
                        'bbox': detection.bbox,
                        'metadata': detection.metadata,
                        'processing_time_ms': int(detector_time),
                        'status': 'unverified'
                    }
                    all_detections.append(db_detection)
                
            except Exception as e:
                self.logger.error(f"Error in {object_type} detector: {e}")
        
        total_time = (time.time() - start_time) * 1000
        
        if all_detections:
            self.logger.info(f"Universal pipeline: {len(all_detections)} detections from {camera_id} in {total_time:.1f}ms")
        
        return all_detections
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics for all detectors"""
        stats = {
            'active_detectors': self.active_detectors,
            'available_detectors': list(self.detectors.keys()),
            'detector_status': {}
        }
        
        for obj_type, detector in self.detectors.items():
            stats['detector_status'][obj_type] = {
                'loaded': detector.is_loaded(),
                'active': obj_type in self.active_detectors
            }
        
        return stats