# detector.py
import cv2
import easyocr
from ultralytics import YOLO
from datetime import datetime
import numpy as np
import re
import logging

class PlateDetector:
    def __init__(self, model_path: str, language: str = 'en'):
        self.model = self.load_model(model_path)
        self.reader = easyocr.Reader([language])
        
    def load_model(self, model_path: str):
        """Load YOLO model and return it."""
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logging.info(f"Loading model on device: {device}")
        return YOLO(model_path).to(device)
    
    def clean_plate_text(self, text: str) -> str:
        """Clean and validate license plate text."""
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        return text if len(text) >= 6 else None
    
    def detect_and_recognize_plate(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        detected_plates = []
        results = self.model(frame)[0]

        for result in results.boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            conf = float(result.conf[0])
            class_name = self.model.names[int(result.cls[0])]
            
            # Optional: Add checks for minimum bounding box size
            
            cropped_plate = frame[y1:y2, x1:x2]
            ocr_results = self.reader.readtext(cropped_plate)

            for bbox, text, ocr_conf in ocr_results:
                cleaned_text = self.clean_plate_text(text)
                if cleaned_text:
                    detection = {
                        "plate_text": cleaned_text,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "ocr_confidence": float(ocr_conf),
                        "detection_confidence": conf,
                        "class_name": class_name,
                        "bbox": [x1, y1, x2, y2]
                    }
                    detected_plates.append(detection)
                    
        return detected_plates