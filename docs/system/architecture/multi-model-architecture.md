# Multi-Model AI Architecture - Scalable Feature Addition

## 🎯 The Beauty of Our Architecture

Since we decode video **once** and get raw pixels, we can feed the **same frame** to multiple AI models simultaneously!

```python
# Single frame → Multiple AI models
ret, frame = capture.read()  # Decode ONCE

# Send SAME frame to all AI models:
plates = license_plate_model(frame)       # Current feature
faces = face_detection_model(frame)       # New feature
objects = object_detection_model(frame)   # New feature  
behavior = behavior_analysis_model(frame) # New feature
```

## Multi-Model Processing Pipeline

### 1. Modular AI Service Architecture

```python
# services/ai_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class AIModel(ABC):
    """Base class for all AI models"""
    
    def __init__(self, model_name: str, confidence_threshold: float = 0.5):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.is_loaded = False
        
    @abstractmethod
    async def load_model(self):
        """Load the AI model"""
        pass
    
    @abstractmethod  
    async def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Process frame and return detections"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup model resources"""
        pass


class LicensePlateModel(AIModel):
    """License plate detection and OCR"""
    
    async def load_model(self):
        from ultralytics import YOLO
        import easyocr
        
        self.vehicle_model = YOLO('yolov8m.pt')
        self.plate_model = YOLO('license_plate_model.pt')
        self.ocr_reader = easyocr.Reader(['en'])
        self.is_loaded = True
        
    async def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        detections = []
        
        # Detect vehicles
        vehicles = self.vehicle_model(frame)
        
        for vehicle in vehicles[0].boxes:
            # Extract vehicle region and detect plates
            # ... (existing implementation)
            
            detections.append({
                'type': 'license_plate',
                'plate_text': plate_text,
                'confidence': confidence,
                'bbox': bbox,
                'metadata': {'vehicle_type': vehicle_type}
            })
            
        return detections


class FaceDetectionModel(AIModel):
    """Face detection for privacy/security"""
    
    async def load_model(self):
        import face_recognition
        self.face_model = face_recognition
        self.is_loaded = True
        
    async def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        # Find faces
        face_locations = self.face_model.face_locations(frame)
        
        detections = []
        for location in face_locations:
            top, right, bottom, left = location
            detections.append({
                'type': 'face',
                'bbox': [left, top, right, bottom],
                'confidence': 0.99,  # face_recognition doesn't give confidence
                'metadata': {}
            })
            
        return detections


class ObjectCountingModel(AIModel):
    """Count various objects (people, vehicles, etc)"""
    
    async def load_model(self):
        from ultralytics import YOLO
        self.model = YOLO('yolov8x.pt')  # Larger model for better accuracy
        self.is_loaded = True
        
    async def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        results = self.model(frame)
        
        # Count objects by class
        counts = {}
        detections = []
        
        for r in results:
            for box in r.boxes:
                class_name = r.names[int(box.cls)]
                counts[class_name] = counts.get(class_name, 0) + 1
                
                detections.append({
                    'type': 'object',
                    'class': class_name,
                    'confidence': float(box.conf),
                    'bbox': box.xyxy[0].tolist(),
                    'metadata': {}
                })
        
        # Add summary detection
        detections.append({
            'type': 'object_count',
            'counts': counts,
            'confidence': 1.0,
            'metadata': {'total_objects': sum(counts.values())}
        })
        
        return detections


class SpeedEstimationModel(AIModel):
    """Estimate vehicle speeds using optical flow"""
    
    def __init__(self, model_name: str, fps: int = 30):
        super().__init__(model_name)
        self.fps = fps
        self.prev_frame = None
        self.tracked_objects = {}
        
    async def load_model(self):
        from ultralytics import YOLO
        self.tracker = YOLO('yolov8x.pt')
        self.is_loaded = True
        
    async def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        # Simplified speed estimation
        # Real implementation would use camera calibration
        
        results = self.tracker.track(frame, persist=True)
        detections = []
        
        if results[0].boxes is not None and results[0].boxes.id is not None:
            for box, track_id in zip(results[0].boxes, results[0].boxes.id):
                track_id = int(track_id)
                bbox = box.xyxy[0].tolist()
                center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                
                if track_id in self.tracked_objects:
                    prev_center = self.tracked_objects[track_id]['center']
                    
                    # Calculate pixel displacement
                    dx = center[0] - prev_center[0]
                    dy = center[1] - prev_center[1]
                    pixel_speed = np.sqrt(dx**2 + dy**2) * self.fps
                    
                    # Rough conversion (needs calibration)
                    estimated_speed_kmh = pixel_speed * 0.1  # Placeholder
                    
                    detections.append({
                        'type': 'speed_estimation',
                        'track_id': track_id,
                        'speed_kmh': estimated_speed_kmh,
                        'confidence': 0.7,
                        'bbox': bbox,
                        'metadata': {'direction': 'left' if dx < 0 else 'right'}
                    })
                
                self.tracked_objects[track_id] = {
                    'center': center,
                    'timestamp': time.time()
                }
        
        return detections
```

### 2. Multi-Model Manager

```python
# services/multi_model_manager.py
import asyncio
from typing import List, Dict, Any
import time
import logging

class MultiModelManager:
    """Manages multiple AI models efficiently"""
    
    def __init__(self, max_workers: int = 4):
        self.models: Dict[str, AIModel] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_times = {}
        self.logger = logging.getLogger("MultiModelManager")
        
    async def register_model(self, model: AIModel):
        """Register a new AI model"""
        await model.load_model()
        self.models[model.model_name] = model
        self.processing_times[model.model_name] = []
        self.logger.info(f"Registered model: {model.model_name}")
        
    async def process_frame(self, frame: np.ndarray, 
                          models: List[str] = None) -> Dict[str, List[Dict]]:
        """Process frame through specified models (or all if none specified)"""
        
        if models is None:
            models = list(self.models.keys())
            
        # Create tasks for parallel processing
        tasks = []
        for model_name in models:
            if model_name in self.models:
                model = self.models[model_name]
                task = asyncio.create_task(self._process_with_timing(model, frame))
                tasks.append((model_name, task))
        
        # Wait for all models to complete
        results = {}
        for model_name, task in tasks:
            try:
                detections, process_time = await task
                results[model_name] = detections
                
                # Track processing time
                self.processing_times[model_name].append(process_time)
                if len(self.processing_times[model_name]) > 100:
                    self.processing_times[model_name].pop(0)
                    
            except Exception as e:
                self.logger.error(f"Error in {model_name}: {e}")
                results[model_name] = []
        
        return results
    
    async def _process_with_timing(self, model: AIModel, frame: np.ndarray):
        """Process frame and measure time"""
        start_time = time.time()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(
            self.executor,
            asyncio.run,
            model.process_frame(frame)
        )
        
        process_time = time.time() - start_time
        return detections, process_time
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for all models"""
        stats = {}
        
        for model_name, times in self.processing_times.items():
            if times:
                stats[model_name] = {
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'fps': 1.0 / (sum(times) / len(times)) if times else 0
                }
            else:
                stats[model_name] = {'avg_time': 0, 'min_time': 0, 'max_time': 0, 'fps': 0}
                
        return stats
```

### 3. Intelligent Processing Pipeline

```python
# pipeline/intelligent_processor.py
class IntelligentProcessor:
    """Smart frame processing with model selection"""
    
    def __init__(self, model_manager: MultiModelManager):
        self.model_manager = model_manager
        self.frame_count = 0
        
        # Processing strategies
        self.strategies = {
            'full': {  # Process everything
                'license_plate': 1,  # Every frame
                'face_detection': 3,  # Every 3 frames
                'object_counting': 10,  # Every 10 frames
                'speed_estimation': 2  # Every 2 frames
            },
            'efficient': {  # Balanced
                'license_plate': 3,
                'face_detection': 10,
                'object_counting': 30,
                'speed_estimation': 5
            },
            'minimal': {  # Low resource
                'license_plate': 5,
                'face_detection': 30,
                'object_counting': 60,
                'speed_estimation': 10
            }
        }
        
        self.current_strategy = 'efficient'
        
    async def process_frame(self, camera_id: str, frame: np.ndarray):
        """Intelligently process frame based on strategy"""
        self.frame_count += 1
        
        # Determine which models to run this frame
        models_to_run = []
        strategy = self.strategies[self.current_strategy]
        
        for model_name, interval in strategy.items():
            if self.frame_count % interval == 0:
                models_to_run.append(model_name)
        
        if not models_to_run:
            return {}
            
        # Process through selected models
        results = await self.model_manager.process_frame(frame, models_to_run)
        
        # Post-process results
        all_detections = []
        for model_name, detections in results.items():
            for detection in detections:
                detection['camera_id'] = camera_id
                detection['frame_number'] = self.frame_count
                detection['timestamp'] = datetime.now()
                all_detections.append(detection)
        
        # Handle special cases
        await self._handle_special_detections(all_detections, frame)
        
        return {
            'frame_number': self.frame_count,
            'detections': all_detections,
            'models_used': models_to_run
        }
    
    async def _handle_special_detections(self, detections: List[Dict], frame: np.ndarray):
        """Handle special scenarios based on detections"""
        
        # Example: If many people detected, trigger face blur
        people_count = sum(1 for d in detections 
                          if d.get('type') == 'object' and d.get('class') == 'person')
        
        if people_count > 5:
            # Could trigger privacy mode
            self.logger.info(f"High people count ({people_count}), consider privacy mode")
        
        # Example: If vehicle detected but no plate, save for manual review
        has_vehicle = any(d.get('class') in ['car', 'truck', 'bus'] for d in detections)
        has_plate = any(d.get('type') == 'license_plate' for d in detections)
        
        if has_vehicle and not has_plate:
            # Save frame for manual review
            cv2.imwrite(f"manual_review/no_plate_{self.frame_count}.jpg", frame)
```

### 4. Configuration for Multiple Models

```yaml
# config/ai_models.yaml
models:
  license_plate:
    enabled: true
    class: "LicensePlateModel"
    confidence_threshold: 0.7
    priority: 1  # Highest priority
    gpu_memory: 2048  # MB
    
  face_detection:
    enabled: true
    class: "FaceDetectionModel"
    confidence_threshold: 0.8
    priority: 2
    gpu_memory: 512
    privacy_mode: blur  # blur, blackout, or ignore
    
  object_counting:
    enabled: true
    class: "ObjectCountingModel"
    confidence_threshold: 0.5
    priority: 3
    gpu_memory: 1024
    classes_of_interest:
      - person
      - car
      - truck
      - bicycle
      
  speed_estimation:
    enabled: false  # Disabled by default
    class: "SpeedEstimationModel"
    confidence_threshold: 0.6
    priority: 4
    gpu_memory: 512
    speed_limit_kmh: 50  # For alerts

# Processing strategies based on system resources
processing_strategies:
  high_performance:
    description: "All models, high frequency"
    min_gpu_memory: 8192
    min_cpu_cores: 8
    
  balanced:
    description: "Selected models, moderate frequency"
    min_gpu_memory: 4096
    min_cpu_cores: 4
    
  edge_device:
    description: "Essential models only"
    min_gpu_memory: 2048
    min_cpu_cores: 2
```

### 5. Usage Example

```python
# main_multi_model.py
async def main():
    # Initialize components
    camera_manager = CameraManager()
    model_manager = MultiModelManager(max_workers=4)
    
    # Register AI models based on config
    config = load_config('config/ai_models.yaml')
    
    for model_config in config['models'].values():
        if model_config['enabled']:
            model_class = globals()[model_config['class']]
            model = model_class(
                model_name=model_config['class'],
                confidence_threshold=model_config['confidence_threshold']
            )
            await model_manager.register_model(model)
    
    # Create intelligent processor
    processor = IntelligentProcessor(model_manager)
    
    # Main processing loop
    while True:
        for camera_id, camera in camera_manager.get_all_cameras().items():
            if camera.is_healthy():
                frame = camera.get_frame()
                if frame is not None:
                    # Process with multiple models
                    results = await processor.process_frame(camera_id, frame)
                    
                    # Handle results
                    for detection in results['detections']:
                        if detection['type'] == 'license_plate':
                            await save_plate_detection(detection)
                        elif detection['type'] == 'face':
                            await handle_privacy(detection, frame)
                        elif detection['type'] == 'speed_estimation':
                            await check_speed_violation(detection)
                        # ... handle other types
        
        # Show performance stats periodically
        if processor.frame_count % 300 == 0:  # Every 10 seconds at 30fps
            stats = model_manager.get_performance_stats()
            logger.info(f"Model Performance: {stats}")
            
        await asyncio.sleep(0.033)  # ~30 FPS
```

## Adding New AI Features

### Example: Adding Parking Violation Detection

```python
class ParkingViolationModel(AIModel):
    """Detect parking violations"""
    
    def __init__(self, model_name: str, parking_zones: List[Dict]):
        super().__init__(model_name)
        self.parking_zones = parking_zones  # Defined areas
        self.parked_vehicles = {}  # Track stationary vehicles
        
    async def load_model(self):
        from ultralytics import YOLO
        self.model = YOLO('yolov8m.pt')
        self.is_loaded = True
        
    async def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        detections = []
        current_time = time.time()
        
        # Detect vehicles
        results = self.model(frame)
        
        for box in results[0].boxes:
            if results[0].names[int(box.cls)] in ['car', 'truck']:
                bbox = box.xyxy[0].tolist()
                center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                
                # Check if in no-parking zone
                in_violation_zone = self._check_zone_violation(center)
                
                # Track stationary time
                vehicle_id = self._get_vehicle_id(bbox)
                
                if vehicle_id in self.parked_vehicles:
                    parked_duration = current_time - self.parked_vehicles[vehicle_id]['first_seen']
                    
                    if in_violation_zone and parked_duration > 60:  # 1 minute
                        detections.append({
                            'type': 'parking_violation',
                            'duration_seconds': parked_duration,
                            'bbox': bbox,
                            'confidence': 0.9,
                            'metadata': {
                                'zone': 'no_parking',
                                'severity': 'high' if parked_duration > 300 else 'medium'
                            }
                        })
                else:
                    self.parked_vehicles[vehicle_id] = {
                        'first_seen': current_time,
                        'bbox': bbox
                    }
        
        # Cleanup old entries
        self._cleanup_old_vehicles(current_time)
        
        return detections
```

## Benefits of This Architecture

1. **Efficiency**: Process same frame through multiple models without re-decoding
2. **Scalability**: Add/remove models without changing core pipeline
3. **Flexibility**: Different models can run at different frequencies
4. **Performance**: Parallel processing with controlled resource usage
5. **Modularity**: Each model is independent and pluggable

## Resource Management

```python
class GPUResourceManager:
    """Manage GPU memory across models"""
    
    def __init__(self, total_gpu_memory: int = 8192):
        self.total_memory = total_gpu_memory
        self.allocated = {}
        
    def can_load_model(self, model_name: str, required_memory: int) -> bool:
        used_memory = sum(self.allocated.values())
        return (used_memory + required_memory) <= self.total_memory
        
    def allocate(self, model_name: str, memory: int):
        if self.can_load_model(model_name, memory):
            self.allocated[model_name] = memory
            return True
        return False
        
    def get_available_memory(self) -> int:
        return self.total_memory - sum(self.allocated.values())
```

## Summary

This architecture allows you to:
- Start with license plate recognition
- Add face detection for privacy compliance
- Add object counting for analytics
- Add speed estimation for traffic monitoring
- Add parking violation detection
- Add ANY computer vision model

All using the **same video stream** with **no additional camera load**!

---

*AI Agent Note: The key is that we decode the video stream ONCE, then feed the raw frames to multiple AI models in parallel. This is incredibly efficient and scalable.*