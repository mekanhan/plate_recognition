import asyncio
import cv2
import time
import torch
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import re
import easyocr
from ultralytics import YOLO

from app.services.camera_service import CameraService
from app.services.enhancer_service import EnhancerService
from app.services.storage_service import StorageService
from app.utils.config import get_settings

class DetectionService:
    """Service for license plate detection and OCR"""
    
    def __init__(self):
        self.model = None
        self.reader = None
        self.camera_service = None
        self.enhancer_service = None
        self.storage_service = None
        self.running = False
        self.task = None
        self.detection_lock = asyncio.Lock()
        self.last_detections = []
        self.settings = get_settings()
    
    async def initialize(self, model_path: str, camera_service: CameraService,
                        enhancer_service: Optional[EnhancerService] = None,
                        storage_service: Optional[StorageService] = None) -> None:
        """Initialize the detection service"""
        # Initialize model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")
        self.model = YOLO(model_path).to(device)
        
        # Initialize OCR
        self.reader = easyocr.Reader(['en'])
        
        # Store services
        self.camera_service = camera_service
        self.enhancer_service = enhancer_service
        self.storage_service = storage_service
        
        # Start detection loop
        self.running = True
        self.task = asyncio.create_task(self._detection_loop())
        
        print(f"Detection service initialized with model: {model_path}")
    
    async def shutdown(self) -> None:
        """Shutdown the detection service"""
        self.running = False
        if self.task:
            await self.task
        
        print("Detection service shutdown")
    
    async def _detection_loop(self) -> None:
        """Run the detection loop"""
        last_detection_time = 0
        
        while self.running:
            current_time = time.time()
            
            # Run detection at specified intervals
            if current_time - last_detection_time >= self.settings.detection_interval:
                try:
                    # Get a frame from the camera
                    frame, _ = await self.camera_service.get_frame()
                    
                    # Run detection
                    detections = await self._detect_plates(frame)
                    
                    # Update last detections with thread safety
                    async with self.detection_lock:
                        self.last_detections = detections
                    
                    # If we have a storage service, save the detections
                    if self.storage_service:
                        await self.storage_service.add_detections(detections)
                    
                    last_detection_time = current_time
                    
                except Exception as e:
                    print(f"Error in detection loop: {e}")
            
            # Small delay to prevent CPU hogging
            await asyncio.sleep(0.1)
    
    async def _detect_plates(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect license plates in a frame
        
        Args:
            frame: Input frame
            
        Returns:
            List of detection results
        """
        results = self.model(frame)[0]
        detected_plates = []
        
        for result in results.boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            conf = float(result.conf[0])
            class_id = int(result.cls[0])
            class_name = self.model.names[class_id]
            
            # Skip low confidence detections
            if conf < self.settings.min_detection_confidence:
                continue
            
            # Crop detected plate
            cropped_plate = frame[y1:y2, x1:x2]
            
            # Skip if cropped area is too small
            if cropped_plate.size == 0 or cropped_plate.shape[0] < 15 or cropped_plate.shape[1] < 15:
                continue
            
            # Run OCR only on the detected plate area
            ocr_results = self.reader.readtext(cropped_plate)
            
            for bbox, text, ocr_conf in ocr_results:
                text_cleaned = self._clean_plate_text(text)
                
                if text_cleaned and ocr_conf >= self.settings.min_ocr_confidence:
                    # Create detection record
                    detection = {
                        "plate_text": text_cleaned,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "unix_timestamp": time.time(),
                        "ocr_confidence": float(ocr_conf),
                        "detection_confidence": conf,
                        "class_name": class_name,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)]
                    }
                    
                    # If we have an enhancer service, enhance this detection
                    if self.enhancer_service:
                        enhanced = await self.enhancer_service.enhance_detection(detection)
                        if enhanced:
                            detection["enhanced"] = enhanced
                    
                    detected_plates.append(detection)
        
        return detected_plates
    
    def _clean_plate_text(self, text: str) -> Optional[str]:
        """Clean license plate text"""
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        return text if len(text) >= 6 else None
    
    async def get_latest_detections(self) -> List[Dict[str, Any]]:
        """Get the latest detections"""
        async with self.detection_lock:
            return self.last_detections.copy()
    
    async def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Process a single frame and draw detections
        
        Args:
            frame: Input frame
            
        Returns:
            Tuple of processed frame and detection results
        """
        # Make a copy to avoid modifying the original
        display_frame = frame.copy()
        
        # Run detection
        detections = await self._detect_plates(frame)
        
        # Draw detections on the frame
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            
            # Draw bounding box
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Get plate text and confidence
            plate_text = detection["plate_text"]
            conf = detection["ocr_confidence"]
            
            # Check if we have enhanced data
            if "enhanced" in detection:
                enhanced = detection["enhanced"]
                if enhanced["confidence_category"] == "HIGH":
                    color = (0, 255, 0)  # Green
                elif enhanced["confidence_category"] == "MEDIUM":
                    color = (0, 165, 255)  # Orange
                else:
                    color = (0, 0, 255)  # Red
                
                plate_text = enhanced["plate_text"]
                
                # Add match type indicator
                if enhanced["match_type"] == "known_plate":
                    plate_text += " (KNOWN)"
                elif enhanced["match_type"] == "consensus":
                    plate_text += " (CONSENSUS)"
                
                conf = enhanced["confidence"]
            else:
                color = (0, 0, 255)  # Red for unenhanced
            
            # Draw text above bounding box
            cv2.putText(display_frame, plate_text, (x1, y1 - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Add confidence info below bounding box
            conf_text = f"Conf: {conf:.2f}"
            cv2.putText(display_frame, conf_text, (x1, y2 + 20),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return display_frame, detections