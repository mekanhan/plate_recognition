
# Foundation 3 - AI Extension Architecture
## Multiple Object Detection Enhancement

### 📋 Overview
This document extends Foundation 3's core license plate recognition system to support multiple object detection types while maintaining backward compatibility.

**Original Foundation 3 Scope**: License plate recognition only
**Extension Scope**: Vehicle (enhanced) + Person detection
**Future Capability**: Any object type through flexible architecture

---

## 🏗️ Architecture Extension Design

### 1. Database Extension (Non-Breaking)

We ADD new tables without modifying existing ones:

```sql
-- Your existing table (DO NOT MODIFY)
CREATE TABLE IF NOT EXISTS detections (
    id VARCHAR(36) PRIMARY KEY,
    plate_text VARCHAR(20),
    vehicle_type VARCHAR(50),
    confidence REAL,
    detected_at TIMESTAMP,
    -- ... other existing columns
);

-- NEW: Object type registry
CREATE TABLE IF NOT EXISTS object_types (
    id VARCHAR(36) PRIMARY KEY,
    type_code VARCHAR(50) UNIQUE NOT NULL,  -- 'vehicle', 'person'
    display_name VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    metadata_schema JSON,  -- Defines what metadata each type stores
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NEW: Universal detection table
CREATE TABLE IF NOT EXISTS universal_detections (
    id VARCHAR(36) PRIMARY KEY,
    camera_id VARCHAR(50) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    confidence REAL NOT NULL,
    detected_at TIMESTAMP NOT NULL,
    bbox JSON NOT NULL,
    metadata JSON DEFAULT '{}',  -- Flexible: stores type-specific data
    
    -- Media references
    frame_path VARCHAR(500),
    object_image_path VARCHAR(500),
    video_clip_id VARCHAR(36),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'unverified',
    flagged BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (object_type) REFERENCES object_types(type_code),
    INDEX idx_type_time (object_type, detected_at)
);

-- NEW: Cross-reference table for backward compatibility
CREATE TABLE IF NOT EXISTS detection_mapping (
    legacy_detection_id VARCHAR(36),
    universal_detection_id VARCHAR(36),
    PRIMARY KEY (legacy_detection_id, universal_detection_id),
    FOREIGN KEY (legacy_detection_id) REFERENCES detections(id),
    FOREIGN KEY (universal_detection_id) REFERENCES universal_detections(id)
);
```

### 2. AI Pipeline Extension

```python
# ai_pipeline/universal_detector.py
from typing import List, Dict, Any
import asyncio
from abc import ABC, abstractmethod

class ObjectDetector(ABC):
    """Base class for all object detectors"""
    
    @abstractmethod
    async def detect(self, frame) -> List[Dict[str, Any]]:
        pass

class UniversalDetectionOrchestrator:
    """
    Orchestrates multiple detection types while maintaining
    backward compatibility with existing LPR system
    """
    
    def __init__(self):
        self.legacy_lpr_system = None  # Your existing system
        self.detectors = {}
        self.active_types = []
        
    def preserve_legacy_system(self, lpr_system):
        """Keep your existing LPR system unchanged"""
        self.legacy_lpr_system = lpr_system
        
    def register_detector(self, object_type: str, detector: ObjectDetector):
        """Add new detection capabilities"""
        self.detectors[object_type] = detector
        
    async def process_frame(self, frame, camera_id: str):
        """Process frame through all active detectors"""
        
        # ALWAYS run legacy LPR first (maintains existing functionality)
        if self.legacy_lpr_system:
            legacy_results = await self.legacy_lpr_system.process_frame(frame)
            # Continue saving to existing 'detections' table
            await self.save_legacy_detections(legacy_results)
        
        # Run new detectors in parallel
        if self.active_types:
            tasks = []
            for obj_type in self.active_types:
                if obj_type in self.detectors:
                    tasks.append(self.detectors[obj_type].detect(frame))
            
            # Process all detections simultaneously
            results = await asyncio.gather(*tasks)
            
            # Save to new universal table
            for obj_type, detections in zip(self.active_types, results):
                await self.save_universal_detections(obj_type, detections, camera_id)
```

### 3. Enhanced Vehicle Detection (Building on LPR)

```python
# ai_pipeline/vehicle_enhanced.py
class EnhancedVehicleDetector(ObjectDetector):
    """
    Extends existing LPR with make/model/color detection
    """
    
    def __init__(self, existing_lpr_system):
        self.lpr = existing_lpr_system  # Reuse existing
        self.attribute_model = self.load_vehicle_attributes_model()
        
    async def detect(self, frame) -> List[Dict[str, Any]]:
        results = []
        
        # Use existing vehicle detection
        vehicles = self.lpr.detect_vehicles(frame)
        
        for vehicle in vehicles:
            # Get license plate (existing functionality)
            plate_info = await self.lpr.read_plate(frame, vehicle['bbox'])
            
            # NEW: Get additional attributes
            attributes = await self.detect_attributes(frame, vehicle['bbox'])
            
            results.append({
                'bbox': vehicle['bbox'],
                'confidence': vehicle['confidence'],
                'metadata': {
                    'plate_text': plate_info.get('text', ''),
                    'plate_confidence': plate_info.get('confidence', 0),
                    'make': attributes.get('make', 'Unknown'),
                    'model': attributes.get('model', 'Unknown'),
                    'color': attributes.get('color', 'Unknown'),
                    'vehicle_type': vehicle.get('class', 'vehicle')
                }
            })
            
        return results
```

### 4. Person Detection Addition

```python
# ai_pipeline/person_detector.py
class PersonDetector(ObjectDetector):
    """
    Simple person detection for security monitoring
    """
    
    def __init__(self):
        self.model = YOLO('yolov8n.pt')  # Lightweight model
        
    async def detect(self, frame) -> List[Dict[str, Any]]:
        results = []
        
        # Detect people
        detections = self.model(frame, classes=[0])  # Class 0 = person
        
        for det in detections[0].boxes:
            if det.conf > 0.7:  # Higher threshold for people
                bbox = det.xyxy[0].tolist()
                
                results.append({
                    'bbox': bbox,
                    'confidence': float(det.conf),
                    'metadata': {
                        'detection_time': datetime.now().isoformat(),
                        'zone': self.determine_zone(bbox, frame.shape)
                    }
                })
                
        return results
        
    def determine_zone(self, bbox, frame_shape):
        """Simple zone detection based on position"""
        center_x = (bbox[0] + bbox[2]) / 2
        if center_x < frame_shape[1] / 3:
            return 'left'
        elif center_x > 2 * frame_shape[1] / 3:
            return 'right'
        return 'center'
```

### 5. Configuration System

```json
{
  "detection_features": {
    "legacy_lpr": {
      "enabled": true,
      "preserve_existing": true
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
      }
    }
  }
}
```

### 6. Gradual Migration Path

#### Phase 1: Preparation (Current)
- ✅ Keep existing LPR system running
- ✅ Add new database tables
- ✅ Create detection orchestrator
- ✅ Test with existing cameras

#### Phase 2: Vehicle Enhancement (Week 1)
- Enable enhanced vehicle detection
- Run BOTH systems in parallel
- Compare results for accuracy
- No disruption to existing system

#### Phase 3: Person Detection (Week 2)
- Enable person detection
- Monitor performance impact
- Adjust thresholds based on environment
- Add to UI gradually

#### Phase 4: Consolidation (Week 3-4)
- Verify all features working
- Consider deprecating legacy table
- Update reporting to use universal data
- Full system documentation

---

## 🎯 Key Design Principles

1. **Non-Breaking**: Existing LPR continues to work exactly as before
2. **Gradual**: Enable features one at a time
3. **Flexible**: Metadata JSON allows any object attributes
4. **Performant**: Parallel processing, no blocking
5. **Configurable**: Enable/disable via configuration
6. **Backward Compatible**: Mapping table links old and new data

---

## 📁 New Files to Create

```
ai_pipeline/
├── universal_detector.py      # Orchestration logic
├── vehicle_enhanced.py        # Enhanced vehicle detection
├── person_detector.py         # Person detection
└── detection_config.py        # Configuration management

migrations/
├── add_universal_detection_tables.sql
└── seed_object_types.sql

api/
└── v2/
    └── universal_detections.py  # New API endpoints
```

---

## 🚀 Implementation Commands

```bash
# Step 1: Create new tables (safe - doesn't touch existing)
python3 migrations/add_universal_detection_schema.py

# Step 2: Test enhanced vehicle detection
python3 test_universal_detection.py --type vehicle

# Step 3: Enable in configuration
# Edit config/features.json - set universal_detection.enabled = true

# Step 4: Monitor both systems running
tail -f logs/detection_service.log
```

---

## 📊 Benefits of This Approach

1. **Zero Risk**: Existing system untouched
2. **Gradual Learning**: Test each feature separately
3. **Easy Rollback**: Just disable in config
4. **Future Proof**: Add any object type later
5. **Performance**: Only process what you need
6. **Storage Efficient**: Your deduplication works on all types

This extension properly builds on Foundation 3 without breaking anything!