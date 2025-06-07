# 📸 License Plate Recognition System: Code Structure and Flow

## 🧱 System Architecture Overview

The license plate recognition system follows a modular service-oriented architecture with clear separation of concerns. Each component handles a specific part of the processing pipeline while maintaining loose coupling through well-defined interfaces.

---

## 🔧 Core Services

### CameraService
- Handles video frame acquisition from cameras or files
- Provides frame buffering and timestamping
- Controls frame rate and resolution

### DetectionService
- Manages license plate detection using YOLOv11
- Coordinates with tracking and OCR processing
- Processes detection results for storage

### EnhancerService
- Improves plate recognition accuracy through various techniques
- Applies confidence boosting and error correction
- Provides final determination of plate text

### StorageService
- Handles all data persistence operations
- Maintains in-memory database of detections and results
- Manages file I/O and ensures data integrity

### TrackerService (integrated in detection pipeline)
- Implements Deep SORT algorithm for object tracking
- Assigns and maintains unique tracking IDs
- Links detections across multiple frames

---

## 📊 System Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │     │             │
│   Camera    │────▶│  Detection  │────▶│  Enhancer   │────▶│   Storage   │
│   Service   │     │   Service   │     │   Service   │     │   Service   │
│             │     │             │     │             │     │             │
└─────────────┘     └──────┬──────┘     └─────────────┘     └─────────────┘
                           │                                        ▲
                           │                                        │
                           ▼                                        │
                    ┌─────────────┐                                 │
                    │             │                                 │
                    │   Tracker   │─────────────────────────────────┘
                    │             │
                    └─────────────┘
```

---

## 🔁 Detailed Process Flow

### 🟢 Initialization Flow

`main.py`
- Create service instances
- Initialize StorageService
  - Create session files
- Initialize CameraService
  - Connect to video source
- Initialize EnhancerService
  - Link to StorageService
- Initialize DetectionService
  - Link to CameraService
  - Link to EnhancerService
  - Link to StorageService

---

### 🎞️ Frame Processing Flow

`CameraService`
- `get_frame()`
  - `DetectionService.process_frame()`
    - YOLOv11 detection
    - Deep SORT tracking
    - For each tracked object:
      - OCR processing
      - Record new detection
        - Add to in-memory database
        - `StorageService.add_detections()`
      - Check if object needs enhancement
        - `EnhancerService.enhance_detection()`
          - `StorageService.add_enhanced_results()`

---

### 💾 Storage Operations Flow

`StorageService`
- `add_detections()`
  - Lock acquisition
  - Append to in-memory database
  - Trigger immediate save
- `add_enhanced_results()`
  - Lock acquisition
  - Append to in-memory enhanced database
  - Trigger immediate save
- `_periodic_save()` [Background Task]
  - Check save interval
  - If interval elapsed:
    - `_save_data()`
- `_save_data()`
  - Lock acquisition
  - Save detection database to file
  - Save enhanced database to file

---

### 🧠 Enhancer Processing Flow

`EnhancerService`
- `enhance_detection()`
  - Analyze plate text
  - Check against known plates
  - Apply text correction algorithms
  - Calculate new confidence score
  - Create enhanced result record
  - `StorageService.add_enhanced_results()`

---

### 🧾 Object Finalization Flow

`DetectionService`
- During frame processing:
  - For each tracked object:
    - If object not detected for N frames:
      - Mark as finalized
      - Trigger final enhancement
        - `EnhancerService.enhance_detection()`
      - Update storage with final status
        - `StorageService.add_detections()` with `status="finalized"`

---

## 📁 Code Organization

```
app/
├── main.py
├── dependencies/
├── models/
├── routers/
│   ├── stream.py
│   ├── detection.py
│   └── results.py
├── services/
│   ├── camera_service.py
│   ├── detection_service.py
│   ├── enhancer_service.py
│   ├── storage_service.py
│   └── tracker.py
└── utils/
    ├── license_plate_processor.py
    ├── plate_database.py
    └── logging_config.py
```

---

## 🧩 Key Code Components

### 1. Detection Pipeline

```python
# Detection service core logic (simplified)
async def process_frame(self, frame):
    # Detect license plates
    detections = await self.license_plate_service.detect(frame)

    for detection in detections:
        tracking_id = self.tracker.update(detection)
        detection['tracking_id'] = tracking_id

        plate_text, confidence = await self.ocr_service.recognize(
            frame, detection['box']
        )
        detection['plate_text'] = plate_text
        detection['confidence'] = confidence

        detection_id = str(uuid.uuid4())
        detection['detection_id'] = detection_id

        await self.storage_service.add_detections([detection])

        if self._should_enhance(tracking_id):
            await self.enhancer_service.enhance_detection(detection)

        if self._should_finalize(tracking_id):
            await self._finalize_object(tracking_id)

    return detections
```

---

### 2. Storage Operations

```python
# Storage service core operations (simplified)
async def add_detections(self, detections):
    async with self.storage_lock:
        self.plate_database["detections"].extend(detections)
        await self._save_data()

async def _save_data(self):
    try:
        with open(self.session_file, 'w') as f:
            json.dump(self.plate_database, f, indent=2)

        with open(self.enhanced_session_file, 'w') as f:
            json.dump(self.enhanced_database, f, indent=2)

        self.last_save_time = time.time()
    except Exception as e:
        logger.error(f"Error saving data: {e}")
```

---

### 3. Enhancement Logic

```python
# Enhancer service core logic (simplified)
async def enhance_detection(self, detection):
    plate_text = detection.get("plate_text", "")
    if not plate_text:
        return None

    if plate_text in self.known_plates:
        enhanced_confidence = 0.9
        match_type = "known_plate"
    else:
        enhanced_text = self._apply_corrections(plate_text)
        enhanced_confidence = min(detection.get("confidence", 0) + 0.1, 1.0)
        match_type = "enhanced"

    enhanced_result = {
        "enhanced_id": f"enh-{uuid.uuid4()}",
        "original_detection_id": detection.get("detection_id"),
        "tracking_id": detection.get("tracking_id"),
        "plate_text": enhanced_text or plate_text,
        "confidence": enhanced_confidence,
        "match_type": match_type,
        "timestamp": time.time()
    }

    await self.storage_service.add_enhanced_results([enhanced_result])
    return enhanced_result
```

---

### 4. Object Finalization

```python
# Detection service finalization logic (simplified)
async def _finalize_object(self, tracking_id):
    tracking_detections = [
        d for d in self.processed_detections.values() 
        if d.get("tracking_id") == tracking_id
    ]

    for detection in tracking_detections:
        detection["status"] = "finalized"

    await self.storage_service.update_detections(tracking_detections)
    await self.enhancer_service.enhance_detections(tracking_detections)
    logger.info(f"Finalized tracking object: {tracking_id}")
```

---

## 🔄 Critical Path Data Flow

1. Frame is captured by `CameraService`
2. DetectionService processes the frame and finds license plates
3. Each license plate is tracked and OCR is applied
4. Detection record is created with unique ID and tracking ID
5. StorageService adds the detection to in-memory database
6. StorageService immediately writes to detection JSON file
7. EnhancerService processes the detection to improve accuracy
8. Enhanced result is created with reference to original detection
9. StorageService adds enhanced result to in-memory database
10. StorageService writes to enhanced JSON file

---

## 🧵 Threading and Concurrency Model

- Main processing occurs in the FastAPI async event loop
- Background tasks (like periodic saving) run as asyncio tasks
- File I/O operations are protected by locks to prevent race conditions
- Services communicate through async method calls, not through message passing

---

This comprehensive code structure and flow diagram provides a clear blueprint for implementing the license plate recognition system with proper real-time data storage capabilities.
