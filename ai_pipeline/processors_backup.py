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
from ai_features.core.types import Detection
from ai_features.vehicle.detection.license_plate import LicensePlateModel
from ai_features.vehicle.detection.pipeline import EnhancedProcessingPipeline

# Re-export Detection for backward compatibility
__all__ = ['Detection', 'LicensePlateDetector', 'ProcessingPipeline']

class LicensePlateDetector:
    """Detects and reads license plates"""
    
    def __init__(self, 
                 vehicle_model_path: str = "ai_pipeline/models/yolov8m.pt",
                 plate_model_path: str = "yolo11m_best.pt",
                 device: str = None):
        
        self.logger = logging.getLogger("LPDetector")
        
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.logger.info(f"Using device: {device}")
        
        # Load models - use existing trained model
        self.vehicle_model = YOLO(vehicle_model_path)
        
        # Check if trained plate model exists, otherwise use vehicle model
        if os.path.exists(f"ai_pipeline/train/models/pretrained/{plate_model_path}"):
            self.plate_model = YOLO(f"ai_pipeline/train/models/pretrained/{plate_model_path}")
        else:
            self.logger.warning(f"Plate model {plate_model_path} not found, using vehicle model for plates")
            self.plate_model = self.vehicle_model
        
        # Initialize OCR
        self.ocr_reader = easyocr.Reader(['en'], gpu=(device == "cuda"))
        
        # Class IDs for vehicles in COCO dataset
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    
    def detect_vehicles(self, frame: np.ndarray) -> List[Dict]:
        """Detect vehicles in frame"""
        results = self.vehicle_model(frame, device=self.device)
        
        vehicles = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                class_id = int(box.cls)
                if class_id in self.vehicle_classes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    vehicles.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(box.conf),
                        'class': r.names[class_id]
                    })
        
        return vehicles
    
    def detect_plates(self, frame: np.ndarray, vehicles: List[Dict]) -> List[Dict]:
        """Detect license plates within vehicle bounding boxes"""
        plates = []
        
        for vehicle in vehicles:
            # Extract vehicle region
            x1, y1, x2, y2 = vehicle['bbox']
            vehicle_roi = frame[y1:y2, x1:x2]
            
            if vehicle_roi.size == 0:
                continue
            
            # For now, use simplified plate detection in lower portion of vehicle
            # In production, you would use a trained license plate detection model
            plate_y1 = int(y1 + (y2-y1) * 0.6)  # Lower 40% of vehicle
            plate_bbox = [x1, plate_y1, x2, y2]
            
            plates.append({
                'vehicle_bbox': vehicle['bbox'],
                'plate_bbox': plate_bbox,
                'confidence': vehicle['confidence'] * 0.8,  # Reduced confidence for estimated plates
                'vehicle_type': vehicle['class']
            })
        
        return plates
    
    def read_plate(self, frame: np.ndarray, plate_bbox: List[int]) -> Tuple[str, float]:
        """Perform OCR on license plate"""
        x1, y1, x2, y2 = plate_bbox
        plate_roi = frame[y1:y2, x1:x2]
        
        if plate_roi.size == 0:
            return "", 0.0
        
        # Preprocess for better OCR
        plate_roi = self._preprocess_plate(plate_roi)
        
        # Perform OCR
        results = self.ocr_reader.readtext(plate_roi)
        
        if not results:
            return "", 0.0
        
        # Combine all detected text
        text_parts = []
        confidences = []
        
        for (bbox, text, confidence) in results:
            text = text.upper().replace(" ", "")
            text_parts.append(text)
            confidences.append(confidence)
        
        combined_text = "".join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return combined_text, avg_confidence
    
    def _preprocess_plate(self, plate_img: np.ndarray) -> np.ndarray:
        """Preprocess license plate image for better OCR"""
        # Resize if too small
        height, width = plate_img.shape[:2]
        if width < 200:
            scale = 200 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            plate_img = cv2.resize(plate_img, (new_width, new_height))
        
        # Convert to grayscale
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img
        
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced)
        
        return denoised

class ProcessingPipeline:
    """Main processing pipeline"""
    
    def __init__(self, 
                 detector: LicensePlateDetector,
                 save_frames: bool = True,
                 output_dir: str = "detections"):
        
        self.detector = detector
        self.save_frames = save_frames
        self.output_dir = output_dir
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger("Pipeline")
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/frames", exist_ok=True)
        os.makedirs(f"{output_dir}/plates", exist_ok=True)
    
    async def process_frame(self, camera_id: str, frame: np.ndarray) -> List[Detection]:
        """Process single frame through detection pipeline"""
        try:
            # Run detection in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            detections = await loop.run_in_executor(
                self.executor,
                self._process_frame_sync,
                camera_id,
                frame
            )
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Processing error for camera {camera_id}: {e}")
            return []
    
    def _process_frame_sync(self, camera_id: str, frame: np.ndarray) -> List[Detection]:
        """Synchronous frame processing"""
        detections = []
        timestamp = datetime.now()
        
        # Detect vehicles
        vehicles = self.detector.detect_vehicles(frame)
        if not vehicles:
            return detections
        
        # Detect plates
        plates = self.detector.detect_plates(frame, vehicles)
        
        for plate_info in plates:
            # Read plate text
            plate_text, confidence = self.detector.read_plate(frame, plate_info['plate_bbox'])
            
            # Skip low confidence or empty plates
            if confidence < 0.5 or len(plate_text) < 4:
                continue
            
            # Generate unique ID
            detection_id = str(uuid.uuid4())
            
            # Save images if enabled
            frame_path = ""
            plate_image_path = ""
            
            if self.save_frames:
                # Save full frame
                frame_filename = f"{detection_id}_frame.jpg"
                frame_path = f"{self.output_dir}/frames/{frame_filename}"
                cv2.imwrite(frame_path, frame)
                
                # Save plate crop
                x1, y1, x2, y2 = plate_info['plate_bbox']
                plate_crop = frame[y1:y2, x1:x2]
                plate_filename = f"{detection_id}_plate.jpg"
                plate_image_path = f"{self.output_dir}/plates/{plate_filename}"
                cv2.imwrite(plate_image_path, plate_crop)
            
            # Create detection object
            detection = Detection(
                detection_id=detection_id,
                camera_id=camera_id,
                timestamp=timestamp,
                plate_text=plate_text,
                confidence=confidence,
                vehicle_type=plate_info['vehicle_type'],
                vehicle_bbox=plate_info['vehicle_bbox'],
                plate_bbox=plate_info['plate_bbox'],
                frame_path=frame_path,
                plate_image_path=plate_image_path
            )
            
            detections.append(detection)
            self.logger.info(f"Detected plate: {plate_text} (confidence: {confidence:.2f})")
        
        return detections
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)