# Foundation 3 - Universal Detection Implementation Guide

## 📋 Overview

This guide provides step-by-step instructions for implementing multiple object detection capabilities on top of the existing Foundation 3 license plate recognition system. The implementation is designed to be non-breaking, gradual, and performance-conscious.

**Goal**: Extend the existing LPR system to detect vehicles (enhanced), persons, and eventually other object types without disrupting current functionality.

---

## 🏗️ Architecture Overview

### System Design Principles

1. **Preserve Existing LPR**: Your working license plate system remains untouched
2. **Parallel Processing**: New detectors run alongside, not instead of, current system
3. **Gradual Enablement**: Turn on features one at a time via configuration
4. **Performance Protection**: Automatic fallback when resources are constrained
5. **Unified Data Model**: New tables that complement existing schema

### Processing Flow

```
Camera Frame
    ├─> Existing LPR Pipeline (always runs)
    │     ├─> Vehicle Detection
    │     ├─> License Plate Detection
    │     └─> Save to 'detections' table
    │
    └─> Universal Detection Pipeline (optional)
          ├─> Enhanced Vehicle Attributes
          ├─> Person Detection
          ├─> Future Object Types
          └─> Save to 'universal_detections' table
```

---

## 📁 Implementation Steps

### Step 1: Database Extension (Day 1)

#### 1.1 Create Migration Script

Create `migrations/add_universal_detection_schema.py`:

```python
#!/usr/bin/env python3
"""
Add universal detection schema without modifying existing tables
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def migrate(db_path='data/license_plates.db'):
    """Add universal detection tables"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create object types table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS object_types (
            type_code VARCHAR(50) PRIMARY KEY,
            display_name VARCHAR(100) NOT NULL,
            icon VARCHAR(50),
            color VARCHAR(7),
            priority INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT TRUE,
            metadata_schema JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create universal detections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS universal_detections (
            id VARCHAR(36) PRIMARY KEY,
            camera_id VARCHAR(50) NOT NULL,
            object_type VARCHAR(50) NOT NULL,
            confidence REAL NOT NULL,
            detected_at TIMESTAMP NOT NULL,
            bbox JSON NOT NULL,
            
            -- Media references
            frame_path VARCHAR(500),
            object_image_path VARCHAR(500),
            video_clip_id VARCHAR(36),
            
            -- Flexible metadata storage
            metadata JSON DEFAULT '{}',
            
            -- Status tracking
            status VARCHAR(20) DEFAULT 'unverified',
            flagged BOOLEAN DEFAULT FALSE,
            
            -- Processing info
            processing_time_ms INTEGER,
            model_version VARCHAR(50),
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_type) REFERENCES object_types(type_code)
        )
    """)
    
    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_universal_detections_type_time 
        ON universal_detections(object_type, detected_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_universal_detections_camera 
        ON universal_detections(camera_id, detected_at DESC)
    """)
    
    # Insert default object types
    object_types = [
        {
            'type_code': 'vehicle',
            'display_name': 'Vehicle',
            'icon': 'fa-car',
            'color': '#4361ee',
            'priority': 1,
            'metadata_schema': json.dumps({
                'plate_text': {'type': 'string', 'required': False},
                'vehicle_type': {'type': 'string', 'enum': ['sedan', 'suv', 'truck', 'van', 'motorcycle']},
                'make': {'type': 'string'},
                'model': {'type': 'string'},
                'color': {'type': 'string'}
            })
        },
        {
            'type_code': 'person',
            'display_name': 'Person',
            'icon': 'fa-user',
            'color': '#00b4d8',
            'priority': 2,
            'metadata_schema': json.dumps({
                'zone': {'type': 'string'},
                'behavior': {'type': 'string', 'enum': ['walking', 'running', 'loitering', 'standing']},
                'direction': {'type': 'string', 'enum': ['entering', 'exiting', 'stationary']}
            })
        }
    ]
    
    for obj_type in object_types:
        cursor.execute("""
            INSERT OR IGNORE INTO object_types 
            (type_code, display_name, icon, color, priority, metadata_schema)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            obj_type['type_code'],
            obj_type['display_name'],
            obj_type['icon'],
            obj_type['color'],
            obj_type['priority'],
            obj_type['metadata_schema']
        ))
    
    # Create cross-reference table for backward compatibility
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_mapping (
            legacy_detection_id VARCHAR(36),
            universal_detection_id VARCHAR(36),
            PRIMARY KEY (legacy_detection_id, universal_detection_id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Universal detection schema created successfully")
    print("✅ Existing 'detections' table unchanged")
    print("✅ Ready for multi-object detection")

if __name__ == "__main__":
    migrate()
```

#### 1.2 Run Migration

```bash
python3 migrations/add_universal_detection_schema.py
```

### Step 2: Create Detection Framework (Day 2)

#### 2.1 Base Detector Interface

Create `ai_pipeline/detectors/base_detector.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
from datetime import datetime

@dataclass
class Detection:
    """Universal detection result"""
    object_type: str
    confidence: float
    bbox: Dict[str, int]  # {x, y, width, height}
    metadata: Dict[str, Any]
    timestamp: datetime
    frame_path: str = None
    object_image_path: str = None

class BaseDetector(ABC):
    """Base class for all object detectors"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.model = None
        self.is_loaded = False
        
    @abstractmethod
    async def load_model(self):
        """Load the detection model"""
        pass
    
    @abstractmethod
    async def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect objects in frame"""
        pass
    
    @abstractmethod
    def get_object_type(self) -> str:
        """Return the object type this detector handles"""
        pass
    
    def is_enabled(self) -> bool:
        """Check if this detector is enabled in config"""
        return self.config.get('enabled', False)
```

#### 2.2 Enhanced Vehicle Detector

Create `ai_pipeline/detectors/vehicle_enhanced.py`:

```python
import numpy as np
from typing import List, Dict, Any
from datetime import datetime
import cv2
import logging

from .base_detector import BaseDetector, Detection

logger = logging.getLogger(__name__)

class EnhancedVehicleDetector(BaseDetector):
    """
    Enhances existing LPR with vehicle attributes
    Reuses the existing license plate detection system
    """
    
    def __init__(self, existing_lpr_system, config=None):
        super().__init__(config)
        self.lpr_system = existing_lpr_system
        self.attribute_model = None
        
    async def load_model(self):
        """Load vehicle attribute recognition model"""
        try:
            # For now, use simple color detection
            # Later: Load specialized make/model classifier
            self.is_loaded = True
            logger.info("Enhanced vehicle detector loaded")
        except Exception as e:
            logger.error(f"Failed to load vehicle attribute model: {e}")
            
    async def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect vehicles with enhanced attributes"""
        detections = []
        
        # Use existing LPR system for vehicle detection
        vehicles = self.lpr_system.detect_vehicles(frame)
        
        for vehicle in vehicles:
            # Get basic vehicle info from existing system
            bbox = vehicle['bbox']
            confidence = vehicle['confidence']
            
            # Extract vehicle region
            x1, y1, x2, y2 = bbox
            vehicle_crop = frame[y1:y2, x1:x2]
            
            # Detect additional attributes
            color = self._detect_color(vehicle_crop)
            vehicle_type = self._classify_vehicle_type(vehicle)
            
            # Check if license plate was detected
            plate_info = vehicle.get('plate', {})
            
            # Create enhanced detection
            detection = Detection(
                object_type='vehicle',
                confidence=confidence,
                bbox={
                    'x': x1,
                    'y': y1,
                    'width': x2 - x1,
                    'height': y2 - y1
                },
                metadata={
                    'plate_text': plate_info.get('text', ''),
                    'plate_confidence': plate_info.get('confidence', 0),
                    'vehicle_type': vehicle_type,
                    'color': color,
                    'make': 'Unknown',  # TODO: Implement make detection
                    'model': 'Unknown',  # TODO: Implement model detection
                },
                timestamp=datetime.now()
            )
            
            detections.append(detection)
            
        return detections
    
    def _detect_color(self, vehicle_crop: np.ndarray) -> str:
        """Simple color detection using HSV"""
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2HSV)
            
            # Define color ranges
            colors = {
                'white': [(0, 0, 200), (180, 30, 255)],
                'black': [(0, 0, 0), (180, 30, 50)],
                'red': [(0, 50, 50), (10, 255, 255)],
                'blue': [(100, 50, 50), (130, 255, 255)],
                'silver': [(0, 0, 100), (180, 30, 200)]
            }
            
            # Find dominant color
            max_pixels = 0
            detected_color = 'unknown'
            
            for color_name, (lower, upper) in colors.items():
                lower = np.array(lower)
                upper = np.array(upper)
                mask = cv2.inRange(hsv, lower, upper)
                pixel_count = cv2.countNonZero(mask)
                
                if pixel_count > max_pixels:
                    max_pixels = pixel_count
                    detected_color = color_name
                    
            return detected_color
            
        except Exception as e:
            logger.error(f"Color detection failed: {e}")
            return 'unknown'
    
    def _classify_vehicle_type(self, vehicle_info: Dict) -> str:
        """Classify vehicle type based on bounding box aspect ratio"""
        bbox = vehicle_info['bbox']
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        aspect_ratio = width / height
        
        # Simple classification based on aspect ratio
        if aspect_ratio > 2.0:
            return 'truck'
        elif aspect_ratio > 1.5:
            return 'suv'
        else:
            return 'sedan'
    
    def get_object_type(self) -> str:
        return 'vehicle'
```

#### 2.3 Person Detector

Create `ai_pipeline/detectors/person_detector.py`:

```python
import numpy as np
from typing import List
from datetime import datetime
import logging

from ultralytics import YOLO
from .base_detector import BaseDetector, Detection

logger = logging.getLogger(__name__)

class PersonDetector(BaseDetector):
    """Simple person detection for security monitoring"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.confidence_threshold = config.get('confidence_threshold', 0.8)
        
    async def load_model(self):
        """Load YOLO model for person detection"""
        try:
            # Use lightweight model for better performance
            self.model = YOLO('yolov8n.pt')
            self.is_loaded = True
            logger.info("Person detector loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load person detection model: {e}")
            self.is_loaded = False
    
    async def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect persons in frame"""
        if not self.is_loaded:
            return []
            
        detections = []
        
        try:
            # Run detection (class 0 = person in COCO dataset)
            results = self.model(frame, classes=[0], verbose=False)
            
            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue
                    
                for box in boxes:
                    if box.conf < self.confidence_threshold:
                        continue
                    
                    # Get bounding box
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # Determine zone based on position
                    zone = self._determine_zone(x1, y1, x2, y2, frame.shape)
                    
                    # Create detection
                    detection = Detection(
                        object_type='person',
                        confidence=float(box.conf),
                        bbox={
                            'x': int(x1),
                            'y': int(y1),
                            'width': int(x2 - x1),
                            'height': int(y2 - y1)
                        },
                        metadata={
                            'zone': zone,
                            'behavior': 'unknown',  # TODO: Implement behavior analysis
                            'direction': 'unknown'  # TODO: Implement tracking
                        },
                        timestamp=datetime.now()
                    )
                    
                    detections.append(detection)
                    
        except Exception as e:
            logger.error(f"Person detection failed: {e}")
            
        return detections
    
    def _determine_zone(self, x1, y1, x2, y2, frame_shape) -> str:
        """Determine which zone the person is in"""
        frame_height, frame_width = frame_shape[:2]
        
        # Calculate person center
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Simple grid-based zones
        if center_x < frame_width / 3:
            horizontal = 'left'
        elif center_x < 2 * frame_width / 3:
            horizontal = 'center'
        else:
            horizontal = 'right'
            
        if center_y < frame_height / 2:
            vertical = 'top'
        else:
            vertical = 'bottom'
            
        return f"{vertical}_{horizontal}"
    
    def get_object_type(self) -> str:
        return 'person'
```

### Step 3: Create Universal Detection Orchestrator (Day 3)

#### 3.1 Detection Orchestrator

Create `ai_pipeline/universal_detection_orchestrator.py`:

```python
import asyncio
import logging
from typing import List, Dict, Any
import numpy as np
from datetime import datetime
import uuid

from .detectors.base_detector import BaseDetector, Detection
from .detectors.vehicle_enhanced import EnhancedVehicleDetector
from .detectors.person_detector import PersonDetector

logger = logging.getLogger(__name__)

class UniversalDetectionOrchestrator:
    """
    Orchestrates multiple detection systems while preserving
    backward compatibility with existing LPR
    """
    
    def __init__(self, existing_lpr_system, config_path='config/features.json'):
        self.legacy_lpr_system = existing_lpr_system
        self.detectors: Dict[str, BaseDetector] = {}
        self.active_detectors: List[str] = []
        self.config = self._load_config(config_path)
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize detectors
        self._initialize_detectors()
        
    def _load_config(self, config_path):
        """Load configuration from file"""
        try:
            import json
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}, using defaults")
            return {
                'universal_detection': {
                    'enabled': False,
                    'types': {}
                }
            }
    
    def _initialize_detectors(self):
        """Initialize all available detectors"""
        universal_config = self.config.get('universal_detection', {})
        
        if not universal_config.get('enabled', False):
            logger.info("Universal detection disabled in config")
            return
            
        types_config = universal_config.get('types', {})
        
        # Enhanced vehicle detector (always available if universal is enabled)
        vehicle_config = types_config.get('vehicle', {})
        if vehicle_config.get('enabled', False):
            vehicle_detector = EnhancedVehicleDetector(
                self.legacy_lpr_system,
                vehicle_config
            )
            self.register_detector('vehicle', vehicle_detector)
            
        # Person detector
        person_config = types_config.get('person', {})
        if person_config.get('enabled', False):
            person_detector = PersonDetector(person_config)
            self.register_detector('person', person_detector)
            
    def register_detector(self, object_type: str, detector: BaseDetector):
        """Register a detector and load its model"""
        self.detectors[object_type] = detector
        self.active_detectors.append(object_type)
        
        # Load model asynchronously
        asyncio.create_task(detector.load_model())
        
        logger.info(f"Registered {object_type} detector")
        
    async def process_frame(self, frame: np.ndarray, camera_id: str) -> Dict[str, Any]:
        """
        Process frame through all detection systems
        Always runs legacy LPR, optionally runs universal detectors
        """
        start_time = datetime.now()
        results = {
            'camera_id': camera_id,
            'timestamp': start_time,
            'legacy_detections': [],
            'universal_detections': [],
            'performance': {}
        }
        
        # ALWAYS run legacy LPR first (maintains existing functionality)
        try:
            legacy_results = await self._process_legacy_lpr(frame)
            results['legacy_detections'] = legacy_results
        except Exception as e:
            logger.error(f"Legacy LPR failed: {e}")
            
        # Check if we should run universal detection
        if not self.config.get('universal_detection', {}).get('enabled', False):
            return results
            
        # Check GPU/CPU resources
        gpu_usage = await self.performance_monitor.get_gpu_usage()
        if gpu_usage > 85:
            logger.warning(f"GPU usage high ({gpu_usage}%), skipping universal detection")
            results['performance']['skipped'] = 'high_gpu_usage'
            return results
            
        # Run universal detectors in parallel
        if self.active_detectors:
            universal_results = await self._process_universal_detectors(frame)
            results['universal_detections'] = universal_results
            
        # Record performance metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['performance'] = {
            'processing_time_ms': processing_time * 1000,
            'gpu_usage': gpu_usage,
            'detectors_run': len(self.active_detectors)
        }
        
        return results
        
    async def _process_legacy_lpr(self, frame: np.ndarray) -> List[Dict]:
        """Process frame through existing LPR system"""
        # Call your existing LPR processing method
        return self.legacy_lpr_system.process_frame(frame)
        
    async def _process_universal_detectors(self, frame: np.ndarray) -> List[Detection]:
        """Process frame through all active universal detectors"""
        tasks = []
        
        for detector_type in self.active_detectors:
            detector = self.detectors[detector_type]
            if detector.is_loaded:
                tasks.append(detector.detect(frame))
                
        if not tasks:
            return []
            
        # Run all detectors in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results and filter out errors
            all_detections = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Detection failed: {result}")
                else:
                    all_detections.extend(result)
                    
            return all_detections
            
        except Exception as e:
            logger.error(f"Universal detection failed: {e}")
            return []
            
    async def save_detections(self, results: Dict[str, Any], db_service):
        """Save all detections to database"""
        # Save legacy detections to existing table
        for detection in results['legacy_detections']:
            await db_service.save_legacy_detection(detection)
            
        # Save universal detections to new table
        for detection in results['universal_detections']:
            detection_id = str(uuid.uuid4())
            await db_service.save_universal_detection(detection_id, detection)
            
            # If it's a vehicle with plate, create mapping
            if detection.object_type == 'vehicle' and detection.metadata.get('plate_text'):
                # Find corresponding legacy detection
                for legacy in results['legacy_detections']:
                    if legacy.get('plate_text') == detection.metadata['plate_text']:
                        await db_service.create_detection_mapping(
                            legacy['id'], detection_id
                        )

class PerformanceMonitor:
    """Monitor system performance"""
    
    async def get_gpu_usage(self) -> float:
        """Get current GPU usage percentage"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].load * 100
        except:
            pass
        return 0.0
```

### Step 4: Update Configuration (Day 4)

#### 4.1 Update Features Configuration

Update your `config/features.json`:

```json
{
  "detection_features": {
    "license_plate_detection": true,
    "continuous_processing": true,
    "save_detections": true
  },
  
  "universal_detection": {
    "enabled": false,
    "types": {
      "vehicle": {
        "enabled": true,
        "enhanced_attributes": true,
        "confidence_threshold": 0.7
      },
      "person": {
        "enabled": false,
        "confidence_threshold": 0.8,
        "zones_enabled": true
      }
    },
    "performance": {
      "max_gpu_usage": 85,
      "frame_skip": 3,
      "max_concurrent_detectors": 2
    }
  },
  
  "api_features": {
    "universal_detection_endpoints": false,
    "legacy_detection_endpoints": true
  }
}
```

### Step 5: Integration with Existing System (Day 5)

#### 5.1 Update Processing Pipeline

Create `ai_pipeline/enhanced_processing_pipeline.py`:

```python
import logging
from typing import Dict, Any
import numpy as np

from .processors import ProcessingPipeline  # Your existing pipeline
from .universal_detection_orchestrator import UniversalDetectionOrchestrator

logger = logging.getLogger(__name__)

class EnhancedProcessingPipeline(ProcessingPipeline):
    """
    Enhanced pipeline that adds universal detection
    while maintaining existing LPR functionality
    """
    
    def __init__(self):
        super().__init__()  # Initialize existing pipeline
        
        # Add universal detection orchestrator
        self.universal_orchestrator = UniversalDetectionOrchestrator(
            existing_lpr_system=self.detector  # Your existing detector
        )
        
    async def process_frame(self, frame: np.ndarray, camera_id: str) -> Dict[str, Any]:
        """
        Process frame through both legacy and universal pipelines
        """
        # Run the orchestrator which handles both systems
        results = await self.universal_orchestrator.process_frame(frame, camera_id)
        
        # Log summary
        legacy_count = len(results['legacy_detections'])
        universal_count = len(results['universal_detections'])
        
        logger.info(
            f"Processed frame from {camera_id}: "
            f"{legacy_count} legacy detections, "
            f"{universal_count} universal detections"
        )
        
        return results
```

#### 5.2 Update Database Service

Add methods to your database service:

```python
# In database/service.py, add these methods:

async def save_universal_detection(self, detection_id: str, detection: Detection):
    """Save universal detection to new table"""
    query = """
        INSERT INTO universal_detections (
            id, camera_id, object_type, confidence,
            detected_at, bbox, metadata, processing_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    values = (
        detection_id,
        detection.camera_id,
        detection.object_type,
        detection.confidence,
        detection.timestamp,
        json.dumps(detection.bbox),
        json.dumps(detection.metadata),
        detection.processing_time_ms
    )
    
    await self.execute(query, values)
    
async def create_detection_mapping(self, legacy_id: str, universal_id: str):
    """Create mapping between legacy and universal detection"""
    query = """
        INSERT INTO detection_mapping (legacy_detection_id, universal_detection_id)
        VALUES (?, ?)
    """
    await self.execute(query, (legacy_id, universal_id))
```

### Step 6: Testing Strategy (Day 6-7)

#### 6.1 Test Universal Detection

Create `test_universal_detection.py`:

```python
#!/usr/bin/env python3
"""Test universal detection system"""

import asyncio
import cv2
import json
from ai_pipeline.enhanced_processing_pipeline import EnhancedProcessingPipeline

async def test_universal_detection():
    """Test the universal detection system"""
    
    # Initialize pipeline
    pipeline = EnhancedProcessingPipeline()
    
    # Test with a sample image
    frame = cv2.imread('test_image.jpg')
    if frame is None:
        print("❌ Could not load test image")
        return
        
    # Process frame
    results = await pipeline.process_frame(frame, 'test_camera')
    
    # Display results
    print("\n=== Detection Results ===")
    print(f"Legacy detections: {len(results['legacy_detections'])}")
    for det in results['legacy_detections']:
        print(f"  - License plate: {det.get('plate_text', 'N/A')}")
        
    print(f"\nUniversal detections: {len(results['universal_detections'])}")
    for det in results['universal_detections']:
        print(f"  - {det.object_type}: {det.confidence:.2f}")
        if det.object_type == 'vehicle':
            print(f"    Color: {det.metadata.get('color', 'unknown')}")
            print(f"    Type: {det.metadata.get('vehicle_type', 'unknown')}")
        elif det.object_type == 'person':
            print(f"    Zone: {det.metadata.get('zone', 'unknown')}")
            
    print(f"\nPerformance: {results['performance']}")
    
    # Draw results
    output_frame = draw_detections(frame, results)
    cv2.imwrite('test_universal_output.jpg', output_frame)
    print("\n✅ Results saved to test_universal_output.jpg")

def draw_detections(frame, results):
    """Draw all detections on frame"""
    import copy
    output = copy.deepcopy(frame)
    
    # Colors for different object types
    colors = {
        'vehicle': (0, 255, 0),    # Green
        'person': (255, 0, 0),      # Blue
        'default': (255, 255, 0)    # Cyan
    }
    
    # Draw universal detections
    for det in results['universal_detections']:
        bbox = det.bbox
        color = colors.get(det.object_type, colors['default'])
        
        # Draw bounding box
        cv2.rectangle(
            output,
            (bbox['x'], bbox['y']),
            (bbox['x'] + bbox['width'], bbox['y'] + bbox['height']),
            color, 2
        )
        
        # Add label
        label = f"{det.object_type}: {det.confidence:.2f}"
        cv2.putText(
            output, label,
            (bbox['x'], bbox['y'] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5, color, 2
        )
        
    return output

if __name__ == "__main__":
    asyncio.run(test_universal_detection())
```

#### 6.2 Performance Test

Create `test_performance.py`:

```python
#!/usr/bin/env python3
"""Test performance with multiple detectors"""

import asyncio
import time
import cv2
import numpy as np
from ai_pipeline.enhanced_processing_pipeline import EnhancedProcessingPipeline

async def test_performance():
    """Test system performance with different configurations"""
    
    pipeline = EnhancedProcessingPipeline()
    
    # Create test frames (simulate video)
    frames = []
    for i in range(100):
        # Create synthetic frame
        frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        frames.append(frame)
        
    print("Testing performance with 100 frames...")
    
    # Test 1: Legacy only
    print("\n1. Legacy LPR only:")
    # Disable universal detection
    pipeline.universal_orchestrator.config['universal_detection']['enabled'] = False
    
    start = time.time()
    for frame in frames:
        await pipeline.process_frame(frame, 'test_cam')
    legacy_time = time.time() - start
    print(f"   Time: {legacy_time:.2f}s ({100/legacy_time:.1f} FPS)")
    
    # Test 2: Legacy + Vehicle
    print("\n2. Legacy + Enhanced Vehicle:")
    pipeline.universal_orchestrator.config['universal_detection']['enabled'] = True
    pipeline.universal_orchestrator.config['universal_detection']['types']['vehicle']['enabled'] = True
    pipeline.universal_orchestrator.config['universal_detection']['types']['person']['enabled'] = False
    
    start = time.time()
    for frame in frames:
        await pipeline.process_frame(frame, 'test_cam')
    vehicle_time = time.time() - start
    print(f"   Time: {vehicle_time:.2f}s ({100/vehicle_time:.1f} FPS)")
    
    # Test 3: Legacy + Vehicle + Person
    print("\n3. Legacy + Vehicle + Person:")
    pipeline.universal_orchestrator.config['universal_detection']['types']['person']['enabled'] = True
    
    start = time.time()
    for frame in frames:
        await pipeline.process_frame(frame, 'test_cam')
    full_time = time.time() - start
    print(f"   Time: {full_time:.2f}s ({100/full_time:.1f} FPS)")
    
    # Summary
    print("\n=== Performance Summary ===")
    print(f"Legacy overhead: baseline")
    print(f"Vehicle overhead: +{((vehicle_time/legacy_time)-1)*100:.1f}%")
    print(f"Full overhead: +{((full_time/legacy_time)-1)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_performance())
```

### Step 7: Gradual Rollout Plan

#### 7.1 Week 1: Vehicle Enhancement Only

1. **Enable enhanced vehicle detection**:
   ```json
   {
     "universal_detection": {
       "enabled": true,
       "types": {
         "vehicle": {"enabled": true},
         "person": {"enabled": false}
       }
     }
   }
   ```

2. **Monitor performance**:
   - Check GPU usage stays under 85%
   - Verify FPS remains above 20
   - Confirm legacy LPR still working

3. **Validate results**:
   - Compare vehicle colors detected
   - Check vehicle type classification
   - Verify no false positives

#### 7.2 Week 2: Add Person Detection

1. **Enable person detection**:
   ```json
   {
     "universal_detection": {
       "types": {
         "person": {"enabled": true}
       }
     }
   }
   ```

2. **Tune confidence thresholds**:
   - Start with high threshold (0.8)
   - Gradually lower if missing detections
   - Monitor for false positives

3. **Test zone detection**:
   - Verify zones are logical
   - Adjust zone boundaries if needed

#### 7.3 Week 3-4: Production Optimization

1. **Performance tuning**:
   - Adjust frame skip rates
   - Optimize model loading
   - Implement result caching

2. **API integration**:
   - Enable universal detection endpoints
   - Update frontend to display new data
   - Add filtering by object type

3. **Monitoring**:
   - Set up alerts for high GPU usage
   - Track detection accuracy metrics
   - Monitor storage growth

---

## 🎯 Success Criteria

### Technical Success
- ✅ Existing LPR continues working unchanged
- ✅ GPU usage stays under 85%
- ✅ Processing maintains 20+ FPS
- ✅ No memory leaks after 24 hours
- ✅ Database queries remain fast (<100ms)

### Business Success
- ✅ Enhanced vehicle attributes (color, type) 80%+ accurate
- ✅ Person detection 90%+ accurate
- ✅ Zone detection helps identify patterns
- ✅ Storage growth manageable (<10% increase)
- ✅ New insights from multi-object correlation

---

## 🔧 Troubleshooting

### Common Issues

1. **High GPU Usage**
   - Reduce frame processing rate
   - Lower model resolution
   - Disable person detection temporarily

2. **Slow Database Queries**
   - Add missing indexes
   - Implement pagination
   - Archive old detections

3. **Memory Growth**
   - Check for detection object leaks
   - Limit detection history in memory
   - Restart services nightly

4. **False Positives**
   - Increase confidence thresholds
   - Add environment-specific filters
   - Implement detection deduplication

---

## 📚 Next Steps

After successfully implementing vehicle + person detection:

1. **Add Package Detection** (Month 2)
   - Useful for delivery monitoring
   - Correlate with person detection

2. **Implement Behavior Analysis** (Month 2-3)
   - Loitering detection
   - Speed estimation
   - Abnormal behavior alerts

3. **Advanced Analytics** (Month 3+)
   - Cross-camera tracking
   - Pattern recognition
   - Predictive analytics

---

This implementation guide provides a complete, gradual path to adding multiple object detection to your Foundation 3 system without breaking existing functionality.