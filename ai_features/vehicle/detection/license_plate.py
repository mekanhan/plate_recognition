"""
License Plate Detection Model
Enhanced LPR with better OCR and confidence scoring
"""
import os
import logging
from typing import List, Dict, Tuple
import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import re

from ...core.base_model import BaseAIModel
from ...core.types import PlateInfo, VehicleInfo
from ..ocr.enhanced_ocr import EnhancedOCRProcessor
from ..ocr.plate_validator import PlateRegion


class LicensePlateModel(BaseAIModel):
    """Enhanced license plate detection model"""
    
    def __init__(self, 
                 vehicle_model_path: str = "yolov8m.pt",
                 plate_model_path: str = "yolo11m_best.pt",
                 device: str = None):
        
        super().__init__(model_path=plate_model_path, device=device)
        
        self.vehicle_model_path = vehicle_model_path
        self.plate_model_path = plate_model_path
        
        # Models will be loaded lazily
        self.vehicle_model = None
        self.plate_model = None
        self.ocr_reader = None
        
        # Vehicle classes from COCO dataset (optimized for production)
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        self.class_names = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
        
        # Confidence thresholds by vehicle type
        self.vehicle_confidence_thresholds = {
            2: 0.4,   # car - higher confidence
            3: 0.3,   # motorcycle
            5: 0.4,   # bus
            7: 0.4    # truck
        }
        
        # US license plate pattern (basic)
        self.plate_pattern = re.compile(r'^[A-Z0-9\s\-]{4,8}$')
    
    def _load_model(self):
        """Load YOLO models and enhanced OCR processor"""
        models = {}
        
        # Load vehicle detection model
        self.logger.info(f"Loading vehicle model: {self.vehicle_model_path}")
        models['vehicle'] = YOLO(self.vehicle_model_path)
        
        # Load plate detection model
        plate_model_full_path = f"ai_pipeline/train/models/pretrained/{self.plate_model_path}"
        if os.path.exists(plate_model_full_path):
            self.logger.info(f"Loading plate model: {plate_model_full_path}")
            models['plate'] = YOLO(plate_model_full_path)
        else:
            self.logger.warning(f"Plate model not found at {plate_model_full_path}, using vehicle model")
            models['plate'] = models['vehicle']
        
        # Initialize enhanced OCR processor
        self.logger.info("Initializing Enhanced OCR processor")
        gpu_enabled = (self.device == "cuda")
        models['ocr'] = EnhancedOCRProcessor(languages=['en'], gpu_enabled=gpu_enabled)
        
        # Keep legacy OCR reader for backward compatibility
        models['legacy_ocr'] = easyocr.Reader(['en'], gpu=gpu_enabled)
        
        # Store models
        self.vehicle_model = models['vehicle']
        self.plate_model = models['plate']
        self.ocr_processor = models['ocr']  # New enhanced OCR
        self.ocr_reader = models['legacy_ocr']  # Legacy compatibility
        
        return models
    
    def predict(self, frame: np.ndarray) -> Dict:
        """Main prediction method - detects vehicles and plates"""
        if not self.is_loaded:
            if not self.load():
                return {'vehicles': [], 'plates': []}
        
        # Detect vehicles first
        vehicles = self.detect_vehicles(frame)
        self.logger.info(f"Vehicle detection: {len(vehicles)} vehicles found")
        
        # Detect plates within vehicles
        plates = []
        if vehicles:
            plates = self.detect_plates(frame, vehicles)
            self.logger.info(f"Plate detection: {len(plates)} plates found in {len(vehicles)} vehicles")
        else:
            self.logger.info("No vehicles detected, skipping plate detection")
        
        # Also detect plates in full frame (for standalone plates like ceiling-mounted test plates)
        full_frame_plates = self.detect_plates_full_frame(frame)
        self.logger.info(f"Full-frame plate detection: {len(full_frame_plates)} plates found")
        
        # Merge vehicle-based plates and full-frame plates
        all_plates = plates + full_frame_plates
        
        return {
            'vehicles': vehicles,
            'plates': all_plates
        }
    
    def detect_vehicles(self, frame: np.ndarray) -> List[VehicleInfo]:
        """Detect vehicles in frame"""
        results = self.vehicle_model(frame, device=self.device)
        
        vehicles = []
        all_detections = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                class_id = int(box.cls)
                confidence = float(box.conf)
                all_detections.append((class_id, confidence))
                
                # Check if vehicle class is valid and meets confidence threshold
                min_confidence = self.vehicle_confidence_thresholds.get(class_id, 0.5)
                if class_id in self.vehicle_classes and confidence >= min_confidence:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf)
                    
                    vehicle_info = VehicleInfo(
                        vehicle_type=self.class_names.get(class_id, 'unknown'),
                        color='unknown',  # Will be filled by color detector
                        confidence=confidence,
                        bbox=[int(x1), int(y1), int(x2), int(y2)]
                    )
                    vehicles.append(vehicle_info)
        
        # Log all detections for debugging
        if all_detections:
            detection_summary = [f"class {class_id} (conf: {conf:.2f})" for class_id, conf in all_detections]
            self.logger.info(f"All YOLO detections: {', '.join(detection_summary)}")
        
        return vehicles
    
    def detect_plates(self, frame: np.ndarray, vehicles: List[VehicleInfo]) -> List[PlateInfo]:
        """Detect license plates within vehicle bounding boxes"""
        plates = []
        
        for vehicle in vehicles:
            # Extract vehicle region
            x1, y1, x2, y2 = vehicle.bbox
            vehicle_roi = frame[y1:y2, x1:x2]
            
            if vehicle_roi.size == 0:
                continue
            
            # Use trained plate model if available, otherwise estimate plate location
            if self.plate_model != self.vehicle_model:
                # Run plate detection on vehicle ROI
                plate_results = self.plate_model(vehicle_roi, device=self.device)
                
                for r in plate_results:
                    if r.boxes is None:
                        continue
                    
                    for box in r.boxes:
                        # Adjust coordinates to full frame
                        px1, py1, px2, py2 = box.xyxy[0].tolist()
                        plate_bbox = [
                            int(x1 + px1), int(y1 + py1),
                            int(x1 + px2), int(y1 + py2)
                        ]
                        
                        plate_info = PlateInfo(
                            text='',  # Will be filled by OCR
                            confidence=float(box.conf),
                            ocr_confidence=0.0,
                            bbox=plate_bbox
                        )
                        plates.append(plate_info)
            else:
                # Fallback: estimate plate location (lower 40% of vehicle)
                plate_y1 = int(y1 + (y2-y1) * 0.6)
                plate_bbox = [x1, plate_y1, x2, y2]
                
                plate_info = PlateInfo(
                    text='',  # Will be filled by OCR
                    confidence=vehicle.confidence * 0.8,  # Reduced for estimated location
                    ocr_confidence=0.0,
                    bbox=plate_bbox
                )
                plates.append(plate_info)
        
        return plates
    
    def detect_plates_full_frame(self, frame: np.ndarray) -> List[PlateInfo]:
        """Detect license plates directly in the full frame (for standalone/hanging plates)"""
        plates = []
        
        if self.plate_model is None or self.plate_model == self.vehicle_model:
            # No dedicated plate model available, skip full-frame detection
            return plates
        
        # Run plate detection on full frame
        plate_results = self.plate_model(frame, device=self.device)
        
        for r in plate_results:
            if r.boxes is None:
                continue
            
            for box in r.boxes:
                confidence = float(box.conf)
                
                # Adaptive confidence threshold for full-frame detection
                min_confidence = 0.25  # Lower threshold for better detection in various conditions
                if confidence > min_confidence:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    plate_info = PlateInfo(
                        text='',  # Will be filled by OCR
                        confidence=confidence,
                        ocr_confidence=0.0,
                        bbox=[int(x1), int(y1), int(x2), int(y2)],
                        plate_type='standard',  # Default type
                        region='unknown'
                    )
                    plates.append(plate_info)
        
        return plates
    
    def read_plate(self, frame: np.ndarray, plate_bbox: List[int]) -> Tuple[str, float]:
        """Read license plate text using enhanced OCR with validation"""
        x1, y1, x2, y2 = plate_bbox
        
        # Extract plate region with some padding
        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(frame.shape[1], x2 + padding)
        y2 = min(frame.shape[0], y2 + padding)
        
        plate_image = frame[y1:y2, x1:x2]
        
        if plate_image.size == 0:
            return "", 0.0
        
        # Use enhanced OCR processor if available
        if hasattr(self, 'ocr_processor') and self.ocr_processor:
            result = self.ocr_processor.process_plate(
                plate_image, 
                camera_id=None,
                region=PlateRegion.US
            )
            
            # First check if we got raw text from enhanced OCR
            raw_text = result.get('raw_text', '')
            
            if result['is_valid']:
                # Valid result from enhanced OCR
                return result['plate_text'], result['ocr_confidence']
            elif raw_text and not self._is_state_name(raw_text):
                # Enhanced OCR extracted text but validation failed
                # Still use it if it's not a state name
                self.logger.debug(f"Using raw enhanced OCR text despite validation: {raw_text}")
                return raw_text.upper().strip(), result.get('ocr_confidence', 0.5)
            else:
                # Log why it failed for debugging
                self.logger.debug(f"Enhanced OCR failed: {result.get('validation_issues', [])}")
        
        # Fallback to legacy OCR method only if enhanced completely failed
        best_text, best_confidence = self._multi_ocr_attempt(plate_image)
        
        # IMPORTANT: Filter out state names even from legacy OCR
        if self._is_state_name(best_text):
            self.logger.debug(f"Filtered out state name from legacy OCR: {best_text}")
            return "", 0.0
        
        # Validate plate format using legacy validation
        if self._validate_plate_text(best_text):
            return best_text.upper().strip(), best_confidence
        
        return "", 0.0
    
    def _multi_ocr_attempt(self, plate_image: np.ndarray) -> Tuple[str, float]:
        """Try OCR with different preprocessing approaches"""
        attempts = [
            ('original', plate_image),
            ('grayscale', cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)),
            ('enhanced_contrast', self._enhance_contrast(plate_image)),
            ('sharpened', self._sharpen_image(plate_image))
        ]
        
        best_text = ""
        best_confidence = 0.0
        
        for approach, processed_image in attempts:
            try:
                # Resize if too small
                if processed_image.shape[1] < 100:
                    scale = 100 / processed_image.shape[1]
                    new_width = int(processed_image.shape[1] * scale)
                    new_height = int(processed_image.shape[0] * scale)
                    processed_image = cv2.resize(processed_image, (new_width, new_height))
                
                results = self.ocr_reader.readtext(processed_image)
                
                # Priority-based text selection (prioritize larger text and actual plate patterns)
                candidates = []
                for (bbox, text, confidence) in results:
                    if confidence > 0.1 and len(text) >= 3:
                        # Calculate text size
                        text_area = self._calculate_text_area(bbox)
                        
                        # Check if it looks like a plate number vs state name
                        is_state_name = self._is_state_name(text)
                        
                        # Skip state names entirely in legacy OCR
                        if is_state_name:
                            self.logger.debug(f"Skipping state name in legacy OCR: {text}")
                            continue
                        
                        # Calculate priority score for non-state text
                        priority_score = confidence
                        
                        # Bonus for mixed alphanumeric (typical plates)
                        has_letters = any(c.isalpha() for c in text)
                        has_numbers = any(c.isdigit() for c in text)
                        if has_letters and has_numbers:
                            priority_score *= 2.5  # Strong preference for mixed
                        
                        if text_area > 1000:  # Larger text gets bonus
                            priority_score *= 1.5
                        
                        # Length preference (ideal plate length)
                        if 5 <= len(text) <= 7:
                            priority_score *= 1.2
                        
                        candidates.append((text, confidence, priority_score))
                
                # Select best candidate by priority score
                if candidates:
                    candidates.sort(key=lambda x: x[2], reverse=True)
                    text, confidence, _ = candidates[0]
                    
                    # Double-check it's not a state name (extra safety)
                    if not self._is_state_name(text) and confidence > best_confidence:
                        best_text = text
                        best_confidence = confidence
                        
            except Exception as e:
                self.logger.debug(f"OCR attempt '{approach}' failed: {e}")
                continue
        
        return best_text, best_confidence
    
    def _calculate_text_area(self, bbox) -> float:
        """Calculate area of bounding box for text size estimation"""
        try:
            if len(bbox) == 4 and len(bbox[0]) == 2:
                # Format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                width = max(x_coords) - min(x_coords)
                height = max(y_coords) - min(y_coords)
                return width * height
        except:
            pass
        return 0.0
    
    def _is_state_name(self, text: str) -> bool:
        """Check if text is likely a state name rather than license plate number"""
        state_names = {
            'TEXAS', 'CALIFORNIA', 'FLORIDA', 'NEWYORK', 'NEW YORK', 'ILLINOIS', 'OHIO',
            'GEORGIA', 'MICHIGAN', 'PENNSYLVANIA', 'VIRGINIA', 'WASHINGTON',
            'ARIZONA', 'MASSACHUSETTS', 'TENNESSEE', 'INDIANA', 'MISSOURI',
            'MARYLAND', 'WISCONSIN', 'MINNESOTA', 'COLORADO', 'ALABAMA',
            'SOUTHCAROLINA', 'LOUISIANA', 'KENTUCKY', 'OREGON', 'OKLAHOMA',
            'CONNECTICUT', 'IOWA', 'ARKANSAS', 'UTAH', 'NEVADA', 'NEWMEXICO',
            'WESTVIRGINIA', 'NEBRASKA', 'IDAHO', 'HAWAII', 'NEWHAMPSHIRE',
            'MAINE', 'MONTANA', 'RHODEISLAND', 'DELAWARE', 'SOUTHDAKOTA',
            'NORTHDAKOTA', 'ALASKA', 'VERMONT', 'WYOMING',
            'STATE', 'USA', 'AMERICA', 'COUNTY', 'EXEMPT', 'DEALER',
            'VETERAN', 'DISABLED', 'GOVT', 'POLICE', 'FIRE', 'CITY',
            # Common misreads of TEXAS
            'TEAXS', 'TEXSA', 'TXEAS', 'TESAS', 'TEBAS', 'TEKXAS',
            # Other noise words
            'PLATE', 'LICENSE', 'VEHICLE', 'AUTO', 'MOTOR'
        }
        clean_text = text.upper().replace(' ', '').strip()
        return clean_text in {s.replace(' ', '') for s in state_names}
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast for better OCR"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        return clahe.apply(gray)
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """Sharpen image for better OCR"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Sharpening kernel
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        return cv2.filter2D(gray, -1, kernel)
    
    def _validate_plate_text(self, text: str) -> bool:
        """Validate if text looks like a license plate"""
        if not text or len(text) < 4 or len(text) > 8:
            return False
        
        # Remove common OCR mistakes
        cleaned = text.replace('O', '0').replace('I', '1').replace('S', '5')
        
        # Check if it matches basic pattern (letters and numbers)
        return bool(re.match(r'^[A-Z0-9\s\-]{4,8}$', cleaned.upper()))