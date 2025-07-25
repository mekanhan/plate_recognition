# Detection Pipeline

**Date:** 2025-01-24  
**Version:** 1.0  
**Component:** License Plate Detection and OCR Pipeline

## Pipeline Overview

The detection pipeline processes live video frames through a multi-stage AI workflow to identify and read license plates in real-time. The pipeline integrates YOLO object detection with EasyOCR text recognition to provide accurate, fast license plate recognition.

```
Video Frame → Preprocessing → YOLO Detection → ROI Processing → EasyOCR → Post-processing → Results
    │             │              │                │             │           │            │
  640x480      Normalize     Bounding Boxes   Crop & Enhance  Extract Text  Validate    Database
   30fps       GPU Ready     Confidence >0.5   License Plates   Accuracy     Format      Storage
```

## Stage 1: Frame Preprocessing

### Input Processing
```python
def preprocess_frame(frame: np.ndarray) -> torch.Tensor:
    """
    Prepare video frame for YOLO inference
    
    Args:
        frame: Raw video frame (H, W, 3) BGR format
        
    Returns:
        tensor: Preprocessed tensor ready for YOLO model
    """
    # Resize to YOLO input size (640x640)
    resized = cv2.resize(frame, (640, 640))
    
    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    
    # Normalize to [0,1] and convert to tensor
    normalized = rgb_frame.astype(np.float32) / 255.0
    tensor = torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0)
    
    # Move to GPU if available
    if torch.cuda.is_available():
        tensor = tensor.cuda()
    
    return tensor
```

### Preprocessing Parameters
- **Input Resolution**: 640x640 pixels (YOLO standard)
- **Color Space**: RGB (converted from BGR)
- **Normalization**: [0, 1] float32 range
- **GPU Transfer**: Automatic CUDA utilization when available

## Stage 2: YOLO License Plate Detection

### Model Configuration
```python
class YOLODetector:
    def __init__(self, model_path: str = "train/models/pretrained/yolo11m_best.pt"):
        self.model = YOLO(model_path)
        self.model.to('cuda' if torch.cuda.is_available() else 'cpu')
        self.confidence_threshold = 0.5
        self.iou_threshold = 0.4
        
    def detect_plates(self, frame_tensor: torch.Tensor) -> List[DetectionResult]:
        """
        Perform license plate detection using YOLO
        
        Returns:
            list: Detection results with bounding boxes and confidence scores
        """
        with torch.no_grad():
            results = self.model(frame_tensor)
            
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    if box.conf.item() >= self.confidence_threshold:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf.item()
                        
                        detections.append(DetectionResult(
                            bbox=[int(x1), int(y1), int(x2), int(y2)],
                            confidence=float(confidence),
                            class_id=int(box.cls.item())
                        ))
        
        return detections
```

### Available Models
1. **yolo11m_best.pt** (Primary)
   - **Size**: ~22MB
   - **Accuracy**: High precision on license plates
   - **Speed**: ~50ms inference time on GPU
   - **Use Case**: Production deployment

2. **yolov8m.pt** (Alternative)
   - **Size**: ~25MB  
   - **Accuracy**: Slightly lower but more general
   - **Speed**: ~45ms inference time on GPU
   - **Use Case**: Fallback option

3. **yolo11n.pt** (Lightweight)
   - **Size**: ~6MB
   - **Accuracy**: Lower precision but faster
   - **Speed**: ~20ms inference time on GPU
   - **Use Case**: High-throughput scenarios

### Detection Parameters
- **Confidence Threshold**: 0.5 (configurable 0.1-0.9)
- **IoU Threshold**: 0.4 (Non-Maximum Suppression)
- **Max Detections**: 100 per frame
- **Input Size**: 640x640 pixels
- **Output**: Bounding boxes in [x1, y1, x2, y2] format

## Stage 3: ROI Processing and Enhancement

### License Plate Extraction
```python
def extract_license_plate_roi(frame: np.ndarray, bbox: List[int]) -> np.ndarray:
    """
    Extract and enhance license plate region of interest
    
    Args:
        frame: Original video frame
        bbox: Bounding box [x1, y1, x2, y2]
        
    Returns:
        Enhanced license plate image
    """
    x1, y1, x2, y2 = bbox
    
    # Add padding around detected region
    padding = 10
    h, w = frame.shape[:2]
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)
    
    # Extract ROI
    roi = frame[y1:y2, x1:x2]
    
    # Enhance for OCR
    enhanced_roi = enhance_license_plate(roi)
    
    return enhanced_roi

def enhance_license_plate(roi: np.ndarray) -> np.ndarray:
    """
    Apply image enhancement techniques for better OCR accuracy
    """
    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply sharpening kernel
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(blurred, -1, kernel)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Resize for better OCR (minimum 200px width)
    h, w = thresh.shape
    if w < 200:
        scale = 200 / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        thresh = cv2.resize(thresh, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    return thresh
```

### Enhancement Techniques
1. **Noise Reduction**: Gaussian blur filtering
2. **Sharpening**: Unsharp mask for text clarity
3. **Thresholding**: Adaptive binary thresholding
4. **Scaling**: Minimum 200px width for OCR accuracy
5. **Contrast Enhancement**: Histogram equalization when needed

## Stage 4: EasyOCR Text Recognition

### OCR Configuration
```python
class LicensePlateOCR:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
        self.min_confidence = 0.6
        self.plate_patterns = [
            r'^[A-Z0-9]{2,3}[- ]?[A-Z0-9]{3,4}$',  # Standard US format
            r'^[A-Z]{3}[- ]?[0-9]{3,4}$',           # Letter-Number format
            r'^[0-9]{3}[- ]?[A-Z]{3}$',             # Number-Letter format
        ]
    
    def extract_text(self, enhanced_roi: np.ndarray) -> OCRResult:
        """
        Extract text from enhanced license plate image
        
        Returns:
            OCR result with text, confidence, and validation status
        """
        # Perform OCR
        results = self.reader.readtext(enhanced_roi)
        
        if not results:
            return OCRResult(text="", confidence=0.0, valid=False)
        
        # Find best result
        best_result = max(results, key=lambda x: x[2])  # Sort by confidence
        text, bbox, confidence = best_result
        
        # Clean and validate text
        cleaned_text = self.clean_text(text)
        is_valid = self.validate_plate_format(cleaned_text)
        
        return OCRResult(
            text=cleaned_text,
            confidence=float(confidence),
            valid=is_valid,
            raw_text=text
        )
    
    def clean_text(self, raw_text: str) -> str:
        """Clean OCR output for license plate format"""
        # Remove special characters and normalize
        cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
        
        # Remove common OCR errors
        replacements = {
            'O': '0',  # Letter O -> Number 0
            'I': '1',  # Letter I -> Number 1
            'S': '5',  # Letter S -> Number 5 (context dependent)
        }
        
        # Apply replacements based on position context
        # This is a simplified version - production would use more sophisticated logic
        return cleaned
    
    def validate_plate_format(self, text: str) -> bool:
        """Validate text matches expected license plate patterns"""
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
        return False
```

### OCR Parameters
- **Languages**: English ('en')
- **GPU Acceleration**: Enabled when available
- **Confidence Threshold**: 0.6 minimum
- **Text Filtering**: Alphanumeric characters only
- **Pattern Validation**: Multiple license plate format patterns

## Stage 5: Post-Processing and Validation

### Result Validation
```python
class DetectionValidator:
    def __init__(self):
        self.min_plate_length = 4
        self.max_plate_length = 10
        self.min_yolo_confidence = 0.5
        self.min_ocr_confidence = 0.6
        self.min_combined_confidence = 0.4
    
    def validate_detection(self, detection: DetectionResult, ocr_result: OCRResult) -> bool:
        """
        Comprehensive validation of detection + OCR results
        """
        # Check YOLO confidence
        if detection.confidence < self.min_yolo_confidence:
            return False
        
        # Check OCR confidence
        if ocr_result.confidence < self.min_ocr_confidence:
            return False
        
        # Check text length
        if not (self.min_plate_length <= len(ocr_result.text) <= self.max_plate_length):
            return False
        
        # Check format validation
        if not ocr_result.valid:
            return False
        
        # Calculate combined confidence score
        combined_confidence = (detection.confidence + ocr_result.confidence) / 2
        if combined_confidence < self.min_combined_confidence:
            return False
        
        return True
    
    def calculate_quality_score(self, detection: DetectionResult, ocr_result: OCRResult) -> float:
        """
        Calculate overall quality score for the detection
        """
        # Base score from confidences
        base_score = (detection.confidence + ocr_result.confidence) / 2
        
        # Bonus for larger bounding box (more visible plate)
        bbox_area = (detection.bbox[2] - detection.bbox[0]) * (detection.bbox[3] - detection.bbox[1])
        size_bonus = min(0.1, bbox_area / 10000)  # Normalize area contribution
        
        # Bonus for clean text (fewer corrections needed)
        text_quality = len(ocr_result.text) / 8.0  # Normalize to typical plate length
        
        # Combined quality score
        quality_score = min(1.0, base_score + size_bonus + text_quality * 0.1)
        
        return quality_score
```

### Quality Metrics
- **Combined Confidence**: Average of YOLO and OCR confidence
- **Text Quality**: Length and format compliance
- **Bounding Box Quality**: Size and aspect ratio
- **Processing Time**: Total pipeline execution time

## Stage 6: Result Storage and Distribution

### Database Storage
```python
@dataclass
class ProcessedDetection:
    camera_id: int
    timestamp: datetime
    bbox: List[int]
    yolo_confidence: float
    ocr_confidence: float
    plate_text: str
    quality_score: float
    processing_time_ms: int
    original_image_path: str
    enhanced_image_path: str

async def store_detection(detection: ProcessedDetection, db: AsyncSession):
    """Store detection result in database"""
    db_detection = Detection(
        camera_id=detection.camera_id,
        timestamp=detection.timestamp,
        bbox_x1=detection.bbox[0],
        bbox_y1=detection.bbox[1],
        bbox_x2=detection.bbox[2],
        bbox_y2=detection.bbox[3],
        confidence=detection.yolo_confidence,
        ocr_confidence=detection.ocr_confidence,
        plate_text=detection.plate_text,
        quality_score=detection.quality_score,
        processing_time_ms=detection.processing_time_ms,
        image_path=detection.original_image_path,
        enhanced_image_path=detection.enhanced_image_path
    )
    
    db.add(db_detection)
    await db.commit()
    return db_detection
```

## Performance Optimization

### GPU Acceleration
```bash
# CUDA optimization flags
export CUDA_VISIBLE_DEVICES=0
export TORCH_CUDA_ARCH_LIST="7.5;8.0;8.6"  # Target GPU architectures
```

### Batch Processing
```python
def process_frame_batch(frames: List[np.ndarray]) -> List[DetectionResult]:
    """Process multiple frames in a single GPU batch for efficiency"""
    batch_tensor = torch.stack([preprocess_frame(frame) for frame in frames])
    
    with torch.no_grad():
        batch_results = self.model(batch_tensor)
    
    return [parse_yolo_results(result) for result in batch_results]
```

### Memory Management
```python
def cleanup_gpu_memory():
    """Clean up GPU memory after processing"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
```

## Configuration Parameters

### Pipeline Settings
```yaml
detection_pipeline:
  yolo:
    model_path: "train/models/pretrained/yolo11m_best.pt"
    confidence_threshold: 0.5
    iou_threshold: 0.4
    input_size: 640
    max_detections: 100
    
  ocr:
    languages: ["en"]
    min_confidence: 0.6
    gpu_enabled: true
    
  enhancement:
    padding: 10
    min_width: 200
    blur_kernel: 5
    sharpen_enabled: true
    adaptive_threshold: true
    
  validation:
    min_plate_length: 4
    max_plate_length: 10
    min_combined_confidence: 0.4
    pattern_validation: true
    
  performance:
    batch_size: 4
    max_queue_size: 30
    gpu_memory_fraction: 0.8
    processing_threads: 2
```

## Error Handling and Recovery

### Common Issues and Solutions
1. **Model Loading Failure**: Fallback to alternative YOLO model
2. **CUDA Out of Memory**: Reduce batch size and clear cache
3. **OCR Recognition Failure**: Return detection without text
4. **Invalid Text Format**: Flag for manual review
5. **Processing Timeout**: Skip frame and continue pipeline

### Performance Monitoring
```python
class PipelineMonitor:
    def __init__(self):
        self.processing_times = deque(maxlen=100)
        self.detection_counts = deque(maxlen=100)
        self.error_counts = defaultdict(int)
    
    def record_processing_time(self, time_ms: float):
        self.processing_times.append(time_ms)
    
    def get_average_processing_time(self) -> float:
        return sum(self.processing_times) / len(self.processing_times)
    
    def get_detection_rate(self) -> float:
        return sum(self.detection_counts) / len(self.detection_counts)
```

This detection pipeline provides a robust, efficient foundation for real-time license plate recognition with high accuracy and performance optimization for production deployment.