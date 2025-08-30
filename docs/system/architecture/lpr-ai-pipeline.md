# AI Processing Pipeline

## Prerequisites
- Camera integration completed (Document 02)
- YOLOv8 installed (`pip install ultralytics`)
- EasyOCR installed (`pip install easyocr`)
- GPU drivers installed (optional but recommended)

## Overview
This pipeline processes camera frames locally to detect vehicles, locate license plates, and perform OCR. Results are queued for database storage.

## Step-by-Step Implementation

### 1. AI Models Setup

```python
# models/ai_models.py
import torch
from ultralytics import YOLO
import easyocr
import numpy as np
from typing import List, Dict, Tuple, Optional
import cv2
import logging

class LicensePlateDetector:
    """Handles vehicle and license plate detection"""
    
    def __init__(self, 
                 vehicle_model_path: str = "yolov8m.pt",
                 plate_model_path: str = "license_plate_detector.pt",
                 device: str = None):
        
        self.logger = logging.getLogger("LPDetector")
        
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.logger.info(f"Using device: {device}")
        
        # Load models
        self.vehicle_model = YOLO(vehicle_model_path)
        self.plate_model = YOLO(plate_model_path)
        
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
            
            # Detect plates in vehicle ROI
            results = self.plate_model(vehicle_roi, device=self.device)
            
            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue
                    
                for box in boxes:
                    px1, py1, px2, py2 = box.xyxy[0].tolist()
                    
                    # Convert to frame coordinates
                    plate_bbox = [
                        int(x1 + px1),
                        int(y1 + py1),
                        int(x1 + px2),
                        int(y1 + py2)
                    ]
                    
                    plates.append({
                        'vehicle_bbox': vehicle['bbox'],
                        'plate_bbox': plate_bbox,
                        'confidence': float(box.conf),
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
```

### 2. Processing Pipeline

```python
# pipeline/processor.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import uuid
from typing import Optional
import json
import redis
from dataclasses import dataclass, asdict

@dataclass
class Detection:
    """Detection result"""
    detection_id: str
    camera_id: str
    timestamp: datetime
    plate_text: str
    confidence: float
    vehicle_type: str
    vehicle_bbox: List[int]
    plate_bbox: List[int]
    frame_path: str
    plate_image_path: str

class ProcessingPipeline:
    """Main processing pipeline"""
    
    def __init__(self, 
                 detector: LicensePlateDetector,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 save_frames: bool = True,
                 output_dir: str = "detections"):
        
        self.detector = detector
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
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
            
            # Queue detections for database storage
            for detection in detections:
                await self._queue_detection(detection)
            
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
    
    async def _queue_detection(self, detection: Detection):
        """Queue detection for database storage"""
        # Convert to JSON
        detection_data = asdict(detection)
        detection_data['timestamp'] = detection.timestamp.isoformat()
        
        # Add to Redis queue
        self.redis_client.lpush(
            "detection_queue",
            json.dumps(detection_data)
        )
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        self.redis_client.close()
```

### 3. Main Processing Loop

```python
# main_processor.py
import asyncio
from camera_manager import CameraManager, CameraConfig
from models.ai_models import LicensePlateDetector
from pipeline.processor import ProcessingPipeline

async def main():
    # Initialize components
    camera_manager = CameraManager()
    detector = LicensePlateDetector()
    pipeline = ProcessingPipeline(detector)
    
    # Load cameras from config
    # ... (same as before)
    
    # Processing loop
    try:
        while True:
            tasks = []
            
            for camera_id, camera in camera_manager.get_all_cameras().items():
                if camera.is_healthy():
                    frame = camera.get_frame()
                    if frame is not None:
                        # Process frame asynchronously
                        task = pipeline.process_frame(camera_id, frame)
                        tasks.append(task)
            
            # Wait for all frames to be processed
            if tasks:
                await asyncio.gather(*tasks)
            
            # Control processing rate (10 FPS)
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        camera_manager.stop_all()
        pipeline.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Pitfalls

### ❌ DON'T:
1. Process every single frame (wastes resources)
2. Run AI synchronously (blocks other cameras)
3. Keep all frames in memory (memory leak)
4. Ignore error handling (crashes on bad frames)

### ✅ DO:
1. Sample frames at reasonable rate (5-10 FPS)
2. Use async/threading for parallel processing
3. Queue results for database storage
4. Handle errors gracefully

## Performance Optimization

### 1. GPU Acceleration
```python
# Check GPU availability
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
```

### 2. Batch Processing
```python
# Process multiple frames at once
def process_batch(frames: List[np.ndarray]):
    # YOLO can process batches
    results = model(frames)
    return results
```

### 3. Model Optimization
```python
# Use smaller models for edge devices
models = {
    "nano": "yolov8n.pt",     # Fastest, least accurate
    "small": "yolov8s.pt",    # Balanced
    "medium": "yolov8m.pt",   # Better accuracy
    "large": "yolov8l.pt",    # Best accuracy, slowest
}
```

## Verification

### Test Detection:
```python
# test_detection.py
def test_detection():
    # Load test image
    frame = cv2.imread("test_image.jpg")
    
    # Initialize detector
    detector = LicensePlateDetector()
    
    # Detect vehicles
    vehicles = detector.detect_vehicles(frame)
    print(f"Found {len(vehicles)} vehicles")
    
    # Detect plates
    plates = detector.detect_plates(frame, vehicles)
    print(f"Found {len(plates)} license plates")
    
    # Read plates
    for plate in plates:
        text, conf = detector.read_plate(frame, plate['plate_bbox'])
        print(f"Plate: {text} (confidence: {conf:.2f})")
```

### Expected Performance:
- Vehicle detection: ~50ms per frame
- Plate detection: ~30ms per vehicle
- OCR: ~100ms per plate
- Total: ~200ms per frame with plates

## Next Steps

Continue to: **[04 - Database Design](./04-database-design.md)**

---

*AI Agent Note: This pipeline processes frames locally without any network transmission. Results are queued in Redis for reliable database storage.*