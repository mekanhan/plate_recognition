```

## 5. Smart Search Implementation

```python
# api/search_service.py

from typing import List, Dict, Optional
import re
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from database.models import UniversalDetection, ObjectType

class SmartSearchService:
    def __init__(self, db_service):
        self.db = db_service
        self.patterns = {
            'object_type': r'\b(vehicle|car|truck|person|people|package|box)\b',
            'color': r'\b(red|blue|green|white|black|silver|gray|yellow)\b',
            'time': r'\b(today|yesterday|(\d+)\s*(hour|minute|day|week)s?\s*ago)\b',
            'confidence': r'\b(high|low|medium)\s*confidence\b',
            'location': r'\b(entrance|exit|parking|loading)\b',
            'plate': r'\b([A-Z0-9]{2,8})\b'
        }
    
    async def parse_and_search(self, query: str, filters: Optional[Dict] = None) -> Dict:
        """Parse natural language query and convert to filters"""
        parsed_filters = self.parse_query(query)
        
        # Merge with existing filters
        if filters:
            parsed_filters = self.merge_filters(parsed_filters, filters)
        
        # Execute search
        results = await self.execute_search(parsed_filters)
        
        return {
            'results': results,
            'parsed_filters': parsed_filters,
            'original_query': query
        }
    
    def parse_query(self, query: str) -> Dict:
        """Parse natural language into structured filters"""
        filters = {
            'object_types': [],
            'time_range': None,
            'confidence_range': None,
            'metadata_filters': {},
            'text_search': []
        }
        
        # Parse object types
        type_matches = re.findall(self.patterns['object_type'], query, re.I)
        if type_matches:
            filters['object_types'] = [self.normalize_object_type(t) for t in type_matches]
        
        # Parse colors
        color_matches = re.findall(self.patterns['color'], query, re.I)
        if color_matches:
            filters['metadata_filters']['color'] = color_matches
        
        # Parse time references
        time_match = re.search(self.patterns['time'], query, re.I)
        if time_match:
            filters['time_range'] = self.parse_time_reference(time_match.group())
        
        # Parse confidence
        conf_match = re.search(self.patterns['confidence'], query, re.I)
        if conf_match:
            filters['confidence_range'] = self.parse_confidence(conf_match.group())
        
        # Parse license plates
        plate_matches = re.findall(self.patterns['plate'], query)
        if plate_matches:
            filters['metadata_filters']['plate_text'] = plate_matches
        
        # Extract remaining text
        remaining = query
        for pattern in self.patterns.values():
            remaining = re.sub(pattern, '', remaining, flags=re.I)
        
        words = remaining.strip().split()
        if words:
            filters['text_search'] = [w for w in words if len(w) > 2]
        
        return filters
    
    def normalize_object_type(self, type_str: str) -> str:
        """Normalize object type variations"""
        mappings = {
            'car': 'vehicle',
            'truck': 'vehicle',
            'people': 'person',
            'box': 'package'
        }
        return mappings.get(type_str.lower(), type_str.lower())
    
    def parse_time_reference(self, time_str: str) -> Dict:
        """Convert time references to datetime range"""
        now = datetime.now()
        
        if 'today' in time_str.lower():
            return {
                'from': now.replace(hour=0, minute=0, second=0),
                'to': now
            }
        elif 'yesterday' in time_str.lower():
            yesterday = now - timedelta(days=1)
            return {
                'from': yesterday.replace(hour=0, minute=0, second=0),
                'to': yesterday.replace(hour=23, minute=59, second=59)
            }
        else:
            # Parse "X hours/days ago"
            match = re.search(r'(\d+)\s*(hour|minute|day|week)', time_str, re.I)
            if match:
                amount = int(match.group(1))
                unit = match.group(2).lower()
                
                if unit == 'minute':
                    delta = timedelta(minutes=amount)
                elif unit == 'hour':
                    delta = timedelta(hours=amount)
                elif unit == 'day':
                    delta = timedelta(days=amount)
                elif unit == 'week':
                    delta = timedelta(weeks=amount)
                
                return {
                    'from': now - delta,
                    'to': now
                }
        
        return None
    
    async def execute_search(self, filters: Dict) -> List[Dict]:
        """Execute search with parsed filters"""
        query = self.db.session.query(UniversalDetection)
        
        # Apply object type filter
        if filters['object_types']:
            query = query.filter(UniversalDetection.object_type.in_(filters['object_types']))
        
        # Apply time range
        if filters['time_range']:
            query = query.filter(
                UniversalDetection.detected_at.between(
                    filters['time_range']['from'],
                    filters['time_range']['to']
                )
            )
        
        # Apply confidence range
        if filters['confidence_range']:
            query = query.filter(
                UniversalDetection.confidence.between(
                    filters['confidence_range']['min'],
                    filters['confidence_range']['max']
                )
            )
        
        # Apply metadata filters
        for key, values in filters['metadata_filters'].items():
            # Use JSON operators for metadata search
            conditions = []
            for value in values:
                conditions.append(
                    UniversalDetection.metadata[key].astext.ilike(f'%{value}%')
                )
            if conditions:
                query = query.filter(or_(*conditions))
        
        # Apply text search
        if filters['text_search']:
            text_conditions = []
            for term in filters['text_search']:
                # Search in multiple fields
                text_conditions.extend([
                    UniversalDetection.camera_id.ilike(f'%{term}%'),
                    UniversalDetection.metadata.astext.ilike(f'%{term}%')
                ])
            if text_conditions:
                query = query.filter(or_(*text_conditions))
        
        # Execute and return results
        results = await self.db.run_sync(query.limit(200).all)
        return [r.to_dict() for r in results]
```

## 6. Frontend Integration Script

```javascript
// frontend/src/integration/detectionPageSetup.js

// Initialize the new detection page
async function setupUniversalDetectionPage() {
    // 1. Update navigation
    const navItem = document.querySelector('a[href="#detections"]');
    if (navItem) {
        navItem.innerHTML = '<i class="fas fa-search"></i> Detections';
    }
    
    // 2. Initialize detection page when loaded
    if (window.location.hash === '#detections') {
        window.detectionsPage = new UniversalDetectionsPage();
    }
    
    // 3. Setup WebSocket connection
    window.detectionWebSocket = new DetectionWebSocket(
        (detection) => {
            // Handle new detection
            if (window.detectionsPage) {
                window.detectionsPage.handleNewDetection(detection);
            }
            
            // Show notification
            showNotification({
                type: 'info',
                title: 'New Detection',
                message: `${detection.object_type} detected at ${detection.camera_name}`,
                duration: 5000
            });
        },
        (status) => {
            // Update system status
            updateSystemStatus(status);
        }
    );
    
    // 4. Load object types for filters
    await loadObjectTypes();
}

// Load available object types
async function loadObjectTypes() {
    try {
        const response = await fetch('/api/v2/object-types');
        const objectTypes = await response.json();
        
        // Store globally for filters
        window.availableObjectTypes = objectTypes;
        
        // Update filter dropdowns
        updateObjectTypeFilters(objectTypes);
        
    } catch (error) {
        console.error('Failed to load object types:', error);
    }
}

// Update filter UI with object types
function updateObjectTypeFilters(objectTypes) {
    const filterContainer = document.getElementById('object-type-filters');
    if (!filterContainer) return;
    
    const html = objectTypes.map(type => `
        <label class="checkbox-label">
            <input type="checkbox" value="${type.type_code}" 
                   onchange="detectionsPage.toggleObjectType('${type.type_code}')">
            <i class="${type.icon}" style="color: ${type.color}"></i>
            ${type.display_name}
        </label>
    `).join('');
    
    filterContainer.innerHTML = html;
}

// Export functionality
window.UniversalDetectionsPage = UniversalDetectionsPage;
window.DetectionWebSocket = DetectionWebSocket;
window.SmartSearchParser = SmartSearchParser;

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', setupUniversalDetectionPage);
```

## 7. CSS Variables for Theming

```css
/* frontend/src/styles/variables.css */

:root {
    /* Object Type Colors */
    --vehicle-color: #4361ee;
    --person-color: #00b4d8;
    --package-color: #f77f00;
    --animal-color: #06ffa5;
    
    /* Status Colors */
    --status-unverified: #6c757d;
    --status-verified: #28a745;
    --status-flagged: #dc3545;
    --status-archived: #adb5bd;
    
    /* Confidence Levels */
    --confidence-high: #28a745;
    --confidence-medium: #ffc107;
    --confidence-low: #dc3545;
    
    /* Layout Variables */
    --card-min-width: 320px;
    --card-max-width: 400px;
    --grid-gap: 20px;
    --filter-height: 60px;
}
```

## 8. Implementation Checklist

### Phase 1: Database Setup
- [ ] Run migration script to create new tables
- [ ] Migrate existing detections to universal format
- [ ] Setup object types
- [ ] Create indexes for performance

### Phase 2: Backend Updates
- [ ] Update AI pipeline with universal processor
- [ ] Implement new API endpoints
- [ ] Add WebSocket support
- [ ] Setup thumbnail generation

### Phase 3: Frontend Implementation
- [ ] Replace existing detection page
- [ ] Implement card view with video previews
- [ ] Add smart search functionality
- [ ] Setup real-time updates

### Phase 4: Testing & Optimization
- [ ] Test with multiple object types
- [ ] Optimize search performance
- [ ] Add caching layer
- [ ] Performance testing with large datasets

## 9. Performance Considerations

### Database Optimization
```sql
-- Create indexes for common queries
CREATE INDEX idx_detections_object_type ON universal_detections(object_type);
CREATE INDEX idx_detections_detected_at ON universal_detections(detected_at DESC);
CREATE INDEX idx_detections_camera_id ON universal_detections(camera_id);
CREATE INDEX idx_detections_confidence ON universal_detections(confidence);
CREATE INDEX idx_detections_status ON universal_detections(status);

-- For metadata searches (PostgreSQL)
CREATE INDEX idx_detections_metadata ON universal_detections USING gin(metadata);
```

### Caching Strategy
```python
# api/cache_service.py
from functools import lru_cache
import redis

class DetectionCache:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
        self.cache_ttl = 300  # 5 minutes
    
    async def get_cached_search(self, query_hash: str):
        """Get cached search results"""
        cached = self.redis_client.get(f"search:{query_hash}")
        if cached:
            return json.loads(cached)
        return None
    
    async def cache_search_results(self, query_hash: str, results: List[Dict]):
        """Cache search results"""
        self.redis_client.setex(
            f"search:{query_hash}",
            self.cache_ttl,
            json.dumps(results)
        )
```

This comprehensive solution provides:

1. **Universal Detection Support**: Flexible schema supporting any object type
2. **Advanced Search**: Natural language processing for intuitive searches
3. **Multiple View Modes**: List, card, timeline, and map views
4. **Real-time Updates**: WebSocket integration for live detection feeds
5. **Video Preview**: Hover-to-play video previews in card view
6. **Performance Optimized**: Caching, pagination, and efficient queries
7. **Responsive Design**: Works seamlessly on all devices
8. **Extensible Architecture**: Easy to add new object types and features

The system maintains backward compatibility with your existing license plate detection while enabling detection of any object type through the flexible metadata system.
# Backend Integration Guide for Universal Detection System

## 1. Database Migration Strategy

### Step 1: Create Migration Script

```python
# migrations/migrate_to_universal_detections.py

import asyncio
from sqlalchemy import select
from database.models import Detection, UniversalDetection, ObjectType
from database.service import DatabaseService

async def migrate_existing_detections():
    """Migrate existing license plate detections to universal format"""
    db = DatabaseService()
    
    # First, create the vehicle object type
    vehicle_type = ObjectType(
        type_code='vehicle',
        display_name='Vehicle',
        icon='fas fa-car',
        color='#4361ee',
        priority=1,
        metadata_schema={
            "plate_text": {"type": "string", "required": False},
            "vehicle_type": {"type": "string", "required": False},
            "color": {"type": "string", "required": False},
            "make": {"type": "string", "required": False},
            "model": {"type": "string", "required": False}
        }
    )
    
    await db.add(vehicle_type)
    
    # Migrate existing detections
    old_detections = await db.get_all(Detection)
    
    for old in old_detections:
        new_detection = UniversalDetection(
            id=old.id,
            camera_id=old.camera_id,
            object_type='vehicle',
            confidence=old.confidence,
            detected_at=old.detected_at,
            bbox={
                "x": old.plate_bbox[0] if old.plate_bbox else 0,
                "y": old.plate_bbox[1] if old.plate_bbox else 0,
                "width": old.plate_bbox[2] - old.plate_bbox[0] if old.plate_bbox and len(old.plate_bbox) >= 4 else 0,
                "height": old.plate_bbox[3] - old.plate_bbox[1] if old.plate_bbox and len(old.plate_bbox) >= 4 else 0
            },
            frame_path=old.frame_path,
            object_image_path=old.plate_image_path,
            video_clip_id=str(old.video_clip_id) if old.video_clip_id else None,
            metadata={
                "plate_text": old.plate_text,
                "vehicle_type": old.vehicle_type,
                "vehicle_bbox": old.vehicle_bbox
            },
            status='verified' if old.confidence > 0.8 else 'unverified',
            created_at=old.created_at
        )
        
        await db.add(new_detection)
    
    await db.commit()
    print(f"Migrated {len(old_detections)} detections to universal format")

if __name__ == "__main__":
    asyncio.run(migrate_existing_detections())
```

### Step 2: Add Object Types

```python
# scripts/setup_object_types.py

async def setup_object_types():
    """Initialize all object types for the system"""
    db = DatabaseService()
    
    object_types = [
        {
            "type_code": "vehicle",
            "display_name": "Vehicle",
            "icon": "fas fa-car",
            "color": "#4361ee",
            "priority": 1,
            "metadata_schema": {
                "plate_text": {"type": "string", "required": False},
                "vehicle_type": {"type": "string", "enum": ["sedan", "suv", "truck", "van", "motorcycle", "bus"]},
                "color": {"type": "string"},
                "make": {"type": "string"},
                "model": {"type": "string"},
                "year": {"type": "integer", "min": 1900, "max": 2030}
            }
        },
        {
            "type_code": "person",
            "display_name": "Person",
            "icon": "fas fa-user",
            "color": "#00b4d8",
            "priority": 2,
            "metadata_schema": {
                "age_range": {"type": "string", "enum": ["child", "teenager", "adult", "elderly"]},
                "gender": {"type": "string", "enum": ["male", "female", "unknown"]},
                "clothing": {"type": "string"},
                "accessories": {"type": "array", "items": {"type": "string"}},
                "action": {"type": "string", "enum": ["walking", "running", "standing", "sitting", "carrying"]}
            }
        },
        {
            "type_code": "package",
            "display_name": "Package",
            "icon": "fas fa-box",
            "color": "#f77f00",
            "priority": 3,
            "metadata_schema": {
                "size": {"type": "string", "enum": ["small", "medium", "large", "oversized"]},
                "carrier": {"type": "string", "enum": ["fedex", "ups", "amazon", "usps", "dhl", "unknown"]},
                "label_visible": {"type": "boolean"},
                "condition": {"type": "string", "enum": ["intact", "damaged", "wet", "opened"]}
            }
        },
        {
            "type_code": "animal",
            "display_name": "Animal",
            "icon": "fas fa-paw",
            "color": "#06ffa5",
            "priority": 4,
            "metadata_schema": {
                "species": {"type": "string", "enum": ["dog", "cat", "bird", "other"]},
                "size": {"type": "string", "enum": ["small", "medium", "large"]},
                "behavior": {"type": "string"},
                "collar_visible": {"type": "boolean"}
            }
        }
    ]
    
    for obj_type in object_types:
        existing = await db.get_by_field(ObjectType, "type_code", obj_type["type_code"])
        if not existing:
            await db.add(ObjectType(**obj_type))
    
    await db.commit()
    print(f"Setup {len(object_types)} object types")
```

## 2. Update AI Pipeline for Multiple Object Types

### Step 1: Create Universal Processor

```python
# ai_pipeline/universal_processor.py

from typing import List, Dict, Any
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

@dataclass
class UniversalDetectionResult:
    """Universal detection result that works for any object type"""
    object_type: str
    confidence: float
    bbox: Dict[str, int]  # {"x": 0, "y": 0, "width": 100, "height": 100}
    metadata: Dict[str, Any]
    frame: np.ndarray
    timestamp: datetime

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

class VehicleDetector(BaseDetector):
    """Existing vehicle/license plate detector wrapped in new interface"""
    
    def __init__(self, existing_detector):
        self.detector = existing_detector
    
    def detect(self, frame: np.ndarray) -> List[UniversalDetectionResult]:
        results = []
        
        # Use existing detection logic
        vehicles = self.detector.detect_vehicles(frame)
        plates = self.detector.detect_plates(frame, vehicles)
        
        for plate_info in plates:
            plate_text, confidence = self.detector.read_plate(frame, plate_info['plate_bbox'])
            
            if confidence > 0.5:
                result = UniversalDetectionResult(
                    object_type='vehicle',
                    confidence=confidence,
                    bbox={
                        "x": plate_info['vehicle_bbox'][0],
                        "y": plate_info['vehicle_bbox'][1],
                        "width": plate_info['vehicle_bbox'][2] - plate_info['vehicle_bbox'][0],
                        "height": plate_info['vehicle_bbox'][3] - plate_info['vehicle_bbox'][1]
                    },
                    metadata={
                        "plate_text": plate_text,
                        "vehicle_type": plate_info['vehicle_type'],
                        "plate_bbox": plate_info['plate_bbox']
                    },
                    frame=frame,
                    timestamp=datetime.now()
                )
                results.append(result)
        
        return results
    
    def get_object_type(self) -> str:
        return 'vehicle'

class PersonDetector(BaseDetector):
    """Person detection using YOLOv8"""
    
    def __init__(self, model_path='yolov8n.pt'):
        from ultralytics import YOLO
        self.model = YOLO(model_path)
    
    def detect(self, frame: np.ndarray) -> List[UniversalDetectionResult]:
        results = []
        detections = self.model(frame)
        
        for r in detections:
            for box in r.boxes:
                if self.model.names[int(box.cls)] == 'person':
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    result = UniversalDetectionResult(
                        object_type='person',
                        confidence=float(box.conf),
                        bbox={
                            "x": int(x1),
                            "y": int(y1),
                            "width": int(x2 - x1),
                            "height": int(y2 - y1)
                        },
                        metadata=self._analyze_person(frame[int(y1):int(y2), int(x1):int(x2)]),
                        frame=frame,
                        timestamp=datetime.now()
                    )
                    results.append(result)
        
        return results
    
    def _analyze_person(self, person_crop):
        """Analyze person attributes (placeholder for actual implementation)"""
        return {
            "age_range": "adult",
            "clothing": "dark clothing",
            "action": "walking"
        }
    
    def get_object_type(self) -> str:
        return 'person'

class UniversalDetectionPipeline:
    """Orchestrates multiple detectors"""
    
    def __init__(self):
        self.detectors: Dict[str, BaseDetector] = {}
        self.active_detectors: List[str] = []
    
    def register_detector(self, detector: BaseDetector):
        """Register a new detector"""
        object_type = detector.get_object_type()
        self.detectors[object_type] = detector
    
    def enable_detector(self, object_type: str):
        """Enable a specific detector"""
        if object_type in self.detectors and object_type not in self.active_detectors:
            self.active_detectors.append(object_type)
    
    def disable_detector(self, object_type: str):
        """Disable a specific detector"""
        if object_type in self.active_detectors:
            self.active_detectors.remove(object_type)
    
    async def process_frame(self, camera_id: str, frame: np.ndarray) -> List[Dict]:
        """Process frame through all active detectors"""
        all_detections = []
        
        for object_type in self.active_detectors:
            detector = self.detectors[object_type]
            try:
                detections = detector.detect(frame)
                for detection in detections:
                    # Convert to database format
                    db_detection = {
                        'camera_id': camera_id,
                        'object_type': detection.object_type,
                        'confidence': detection.confidence,
                        'detected_at': detection.timestamp,
                        'bbox': detection.bbox,
                        'metadata': detection.metadata
                    }
                    all_detections.append(db_detection)
            except Exception as e:
                print(f"Error in {object_type} detector: {e}")
        
        return all_detections
```

## 3. Update Main API Service

### Step 1: Modify CameraManager to Use Universal Pipeline

```python
# api/camera_manager.py - Update existing file

from ai_pipeline.universal_processor import UniversalDetectionPipeline, VehicleDetector, PersonDetector

class CameraManager:
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize universal pipeline
        self.detection_pipeline = UniversalDetectionPipeline()
        
        # Register detectors
        self.detection_pipeline.register_detector(
            VehicleDetector(self.plate_detector)
        )
        self.detection_pipeline.register_detector(
            PersonDetector()
        )
        
        # Enable based on configuration
        self.load_detector_config()
    
    def load_detector_config(self):
        """Load which detectors should be active"""
        # This could come from database or config file
        active_types = ['vehicle', 'person']  # Example
        
        for obj_type in active_types:
            self.detection_pipeline.enable_detector(obj_type)
    
    async def process_camera_frame(self, camera_id: str):
        """Updated to use universal pipeline"""
        camera = self.cameras.get(camera_id)
        if not camera:
            return
        
        try:
            # Get frame
            frame = await self._get_camera_frame(camera)
            if frame is None:
                return
            
            # Store latest frame
            camera['last_frame'] = frame
            camera['last_frame_time'] = datetime.now()
            
            # Process through universal pipeline
            detections = await self.detection_pipeline.process_frame(camera_id, frame)
            
            # Save to database
            for detection in detections:
                await self._save_detection(detection, frame)
            
        except Exception as e:
            logger.error(f"Error processing camera {camera_id}: {e}")
```

### Step 2: Add New API Endpoints

```python
# api/main.py - Add to existing file

from api.detection_endpoints import router as detection_router

# Add the new router
app.include_router(detection_router)

# Add WebSocket endpoint for real-time updates
@app.websocket("/ws/detections")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Add to active connections
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket
    
    try:
        while True:
            # Receive and process messages
            data = await websocket.receive_json()
            
            if data.get('action') == 'subscribe':
                # Handle subscription to specific filters
                await handle_subscription(connection_id, data.get('filters', {}))
            
    except WebSocketDisconnect:
        # Remove from active connections
        del active_connections[connection_id]

# Function to broadcast new detections
async def broadcast_detection(detection: Dict):
    """Send new detection to all connected clients"""
    message = {
        'type': 'new_detection',
        'detection': detection
    }
    
    for connection_id, websocket in active_connections.items():
        try:
            await websocket.send_json(message)
        except:
            # Handle disconnected clients
            pass
```

## 4. Video Thumbnail Generation

```python
# api/video_thumbnail_service.py

import cv2
import os
from pathlib import Path

class VideoThumbnailService:
    def __init__(self, thumbnail_dir='data/thumbnails'):
        self.thumbnail_dir = Path(thumbnail_dir)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_thumbnail(self, video_path: str, detection_id: str, 
                                timestamp_ms: int = None) -> str:
        """Generate thumbnail from video clip"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if timestamp_ms:
                cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Resize to thumbnail size
                height, width = frame.shape[:2]
                target_width = 320
                target_height = int(height * (target_width / width))
                
                thumbnail = cv2.resize(frame, (target_width, target_height))
                
                # Save thumbnail
                thumbnail_path = self.thumbnail_dir / f"{detection_id}_thumb.jpg"
                cv2.imwrite(str(thumbnail_path), thumbnail)
                
                return f"/thumbnails/{detection_id}_thumb.jpg"
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
        
        return None

# Add to detection saving process
async def _save_detection(self, detection_data: Dict, frame: np.ndarray):
    """Enhanced save detection with thumbnail generation"""
    detection_id = str(uuid.uuid4())
    
    # Save frame and object crop
    frame_path = await self._save_frame(detection_id, frame)
    object_path = await self._save_object_crop(detection_id, frame, detection_data['bbox'])
    
    # Generate video thumbnail if available
    thumbnail_path = None
    if detection_data.get('video_clip_id'):
        thumbnail_service = VideoThumbnailService()
        thumbnail_path = await thumbnail_service.generate_thumbnail(
            f"recordings/{detection_data['video_clip_id']}.mp4",
            detection_id
        )
    
    # Create database entry
    db_detection = UniversalDetection(
        id=detection_id,
        camera_id=detection_data['camera_id'],
        object_type=detection_data['object_type'],
        confidence=detection_data['confidence'],
        detected_at=detection_data['detected_at'],
        bbox=detection_data['bbox'],
        frame_path=frame_path,
        object_image_path=object_path,
        video_thumbnail_path=thumbnail_path,
        metadata=detection_data['metadata'],
        status='unverified',
        processing_time_ms=detection_data.get('processing_time', 0)
    )
    
    # Save to database
    await self.db_service.add(db_detection)
    
    # Broadcast to WebSocket clients
    await broadcast_detection(db_detection.to_dict())