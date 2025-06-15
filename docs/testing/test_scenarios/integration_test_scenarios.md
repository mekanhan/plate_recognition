# Integration Test Scenarios - License Plate Recognition System

## Overview

This document contains comprehensive integration test scenarios for service-to-service interactions, database operations, and external system integrations within the LPR system. These scenarios validate end-to-end functionality across system boundaries.

## Integration Test Categories

### 1. Service Integration Tests
### 2. Database Integration Tests
### 3. Camera Integration Tests
### 4. File System Integration Tests
### 5. ML Model Integration Tests
### 6. WebSocket Integration Tests
### 7. External System Integration Tests
### 8. Data Flow Integration Tests

---

## 1. Service Integration Tests

### SVC-INT-001: Detection Service → Storage Service Integration
**Feature**: Detection to Storage Pipeline
**Scenario**: Verify detection results are properly stored

**Test Flow**:
1. **Setup**: Initialize detection service and storage service
2. **Action**: Trigger license plate detection on test image
3. **Validation**: Verify detection results are stored in both JSON and SQLite storage

**Expected Behavior**:
```python
# Detection Service produces detection result
detection_result = {
    "license_plate": "ABC123",
    "confidence": 0.85,
    "bbox": [100, 200, 300, 250],
    "timestamp": "2024-01-15T10:30:00Z",
    "image_path": "/data/license_plates/plate_001.jpg"
}

# Storage Service should store in both locations
assert json_repository.save(detection_result) == True
assert sql_repository.save(detection_result) == True
```

**Test Cases**:
- Single detection result storage
- Multiple detection results batch storage
- Storage failure handling (disk full, permissions)
- Concurrent detection storage
- Storage service unavailable scenarios
- Data integrity validation across storage types

**Priority**: High
**Test Data**: Sample license plate images, mock detection results
**Automation**: Yes

### SVC-INT-002: Camera Service → Detection Service Integration
**Feature**: Camera to Detection Pipeline
**Scenario**: Verify camera frames are processed by detection service

**Test Flow**:
1. **Setup**: Mock camera service with test video stream
2. **Action**: Start camera streaming to detection service
3. **Validation**: Verify detection service receives frames and processes them

**Expected Behavior**:
```python
# Camera Service provides frame
frame = camera_service.get_frame("camera_001")

# Detection Service processes frame
detections = detection_service.process_frame(frame)

# Verify integration
assert frame is not None
assert len(detections) >= 0
assert detection_service.get_processing_stats()["frames_processed"] > 0
```

**Test Cases**:
- Real-time frame processing
- Frame rate handling (30fps, 60fps)
- Frame quality variations
- Camera disconnection handling
- Multiple camera simultaneous processing
- Frame buffer overflow scenarios

**Priority**: Critical
**Test Data**: Test video streams, mock camera feeds
**Automation**: Yes

### SVC-INT-003: Background Stream Manager → Output Channel Manager Integration
**Feature**: Background Processing to Output Distribution
**Scenario**: Verify background processing results are distributed correctly

**Test Flow**:
1. **Setup**: Configure background stream manager with multiple output channels
2. **Action**: Process test video stream in background mode
3. **Validation**: Verify results are distributed to all configured output channels

**Expected Behavior**:
```python
# Background processing produces results
background_results = background_stream_manager.process_stream("camera_001")

# Output channels receive results
storage_channel.verify_received_results(background_results)
webhook_channel.verify_received_results(background_results)
api_buffer_channel.verify_received_results(background_results)
```

**Test Cases**:
- Multiple output channel distribution
- Output channel failure handling
- Selective channel configuration
- Channel priority handling
- Async output channel processing
- Channel performance monitoring

**Priority**: High
**Test Data**: Test streams, mock webhook endpoints
**Automation**: Yes

### SVC-INT-004: Video Service → Detection Service Integration
**Feature**: Video Processing Pipeline
**Scenario**: Verify video files are processed for license plate detection

**Test Flow**:
1. **Setup**: Video service with test video files
2. **Action**: Process video file through detection pipeline
3. **Validation**: Verify detections are extracted and timestamped correctly

**Expected Behavior**:
```python
# Video Service provides video segments
video_segments = video_service.get_video_segments("test_video.mp4")

# Detection Service processes each segment
for segment in video_segments:
    detections = detection_service.process_video_segment(segment)
    assert len(detections) >= 0
    assert all(d["timestamp"] is not None for d in detections)
```

**Test Cases**:
- Full video file processing
- Video segment processing
- Multiple video format support (MP4, AVI, MOV)
- Large video file handling
- Corrupted video file handling
- Video processing performance validation

**Priority**: Medium
**Test Data**: Various video files with license plates
**Automation**: Yes

---

## 2. Database Integration Tests

### DB-INT-001: SQLite Database Operations
**Feature**: Database CRUD Operations
**Scenario**: Verify complete database lifecycle operations

**Test Flow**:
1. **Setup**: Initialize SQLite database with test schema
2. **Action**: Perform CRUD operations on detection records
3. **Validation**: Verify data integrity and query performance

**Expected Behavior**:
```python
# Create detection record
detection = Detection(
    license_plate="TEST123",
    confidence=0.95,
    bbox_x1=100, bbox_y1=200, bbox_x2=300, bbox_y2=250,
    timestamp=datetime.utcnow()
)

# Database operations
db_id = db_session.create(detection)
retrieved = db_session.get(db_id)
updated = db_session.update(db_id, {"confidence": 0.97})
deleted = db_session.delete(db_id)

# Verify operations
assert db_id is not None
assert retrieved.license_plate == "TEST123"
assert updated.confidence == 0.97
assert db_session.get(db_id) is None
```

**Test Cases**:
- Basic CRUD operations (Create, Read, Update, Delete)
- Bulk insert operations
- Complex query operations with joins
- Database transaction handling
- Database connection pooling
- Concurrent database access
- Database backup and restore
- Database migration testing

**Priority**: High
**Test Data**: Sample detection records, large datasets for performance
**Automation**: Yes

### DB-INT-002: Database Query Performance
**Feature**: Database Performance Optimization
**Scenario**: Verify database queries meet performance benchmarks

**Test Flow**:
1. **Setup**: Populate database with large dataset (10,000+ records)
2. **Action**: Execute various query types with timing
3. **Validation**: Verify query performance meets SLA requirements

**Expected Behavior**:
```python
# Performance benchmarks
search_time = measure_time(lambda: db.search_license_plates("ABC*"))
filter_time = measure_time(lambda: db.filter_by_date_range(start_date, end_date))
aggregate_time = measure_time(lambda: db.get_detection_statistics())

# Verify performance targets
assert search_time < 0.5  # 500ms max
assert filter_time < 0.3  # 300ms max  
assert aggregate_time < 0.2  # 200ms max
```

**Test Cases**:
- Simple SELECT queries
- Complex JOIN queries
- Wildcard search performance
- Date range filtering performance
- Aggregation query performance
- Index effectiveness validation
- Query optimization verification

**Priority**: Medium
**Test Data**: Large datasets (10K, 50K, 100K records)
**Automation**: Yes

### DB-INT-003: Database Concurrency Testing
**Feature**: Concurrent Database Access
**Scenario**: Verify database handles concurrent access correctly

**Test Flow**:
1. **Setup**: Initialize database with test data
2. **Action**: Simulate multiple concurrent database operations
3. **Validation**: Verify data consistency and no deadlocks

**Expected Behavior**:
```python
import threading
import concurrent.futures

def concurrent_database_operations():
    # Simulate multiple threads performing database operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        
        # Submit concurrent operations
        for i in range(50):
            futures.append(executor.submit(insert_detection_record, f"TEST{i}"))
            futures.append(executor.submit(query_detection_records))
            futures.append(executor.submit(update_detection_record, i))
        
        # Wait for completion and verify results
        results = [future.result() for future in futures]
        assert all(result is not None for result in results)
```

**Test Cases**:
- Concurrent read operations
- Concurrent write operations
- Mixed read/write operations
- Deadlock prevention testing
- Connection pool exhaustion handling
- Transaction isolation testing

**Priority**: High
**Test Data**: Concurrent operation test scripts
**Automation**: Yes

---

## 3. Camera Integration Tests

### CAM-INT-001: USB Camera Integration
**Feature**: USB Camera Support
**Scenario**: Verify USB camera detection and streaming

**Test Flow**:
1. **Setup**: Connect USB camera to test system
2. **Action**: Initialize camera service with USB camera
3. **Validation**: Verify camera stream quality and frame capture

**Expected Behavior**:
```python
# Camera detection
available_cameras = camera_service.detect_cameras()
assert any(cam["type"] == "USB" for cam in available_cameras)

# Camera initialization
camera = camera_service.initialize_camera("usb:0")
assert camera.is_connected() == True

# Frame capture
frame = camera.capture_frame()
assert frame is not None
assert frame.shape[2] == 3  # RGB channels
assert frame.dtype == np.uint8
```

**Test Cases**:
- USB camera detection and enumeration
- Camera initialization and configuration
- Frame capture in different resolutions
- Camera disconnection handling
- Multiple USB camera support
- USB camera hot-plugging

**Priority**: High
**Test Data**: Physical USB cameras or mock camera devices
**Automation**: Partial (mock cameras for CI/CD)

### CAM-INT-002: RTSP Camera Integration
**Feature**: Network Camera Support
**Scenario**: Verify RTSP camera streaming integration

**Test Flow**:
1. **Setup**: Configure RTSP camera or mock RTSP server
2. **Action**: Connect to RTSP stream through camera service
3. **Validation**: Verify stream stability and quality

**Expected Behavior**:
```python
# RTSP connection
rtsp_url = "rtsp://camera.example.com:554/stream"
camera = camera_service.connect_rtsp(rtsp_url)
assert camera.is_streaming() == True

# Stream validation
for i in range(100):  # Test 100 frames
    frame = camera.get_next_frame()
    assert frame is not None
    assert frame.shape[0] > 0 and frame.shape[1] > 0
```

**Test Cases**:
- RTSP connection establishment
- Stream authentication handling
- Network disconnection recovery
- Stream quality validation
- Multiple RTSP camera handling
- RTSP protocol error handling

**Priority**: High
**Test Data**: Mock RTSP servers, test RTSP streams
**Automation**: Yes (with mock servers)

### CAM-INT-003: Camera Configuration Management
**Feature**: Camera Settings Integration
**Scenario**: Verify camera configuration changes are applied

**Test Flow**:
1. **Setup**: Initialize camera with default settings
2. **Action**: Apply various configuration changes
3. **Validation**: Verify settings are applied and effective

**Expected Behavior**:
```python
# Initial configuration
camera_config = {
    "resolution": "1920x1080",
    "fps": 30,
    "brightness": 50,
    "contrast": 50
}

camera.apply_configuration(camera_config)

# Verify configuration
actual_config = camera.get_current_configuration()
assert actual_config["resolution"] == "1920x1080"
assert actual_config["fps"] == 30
```

**Test Cases**:
- Resolution configuration changes
- Frame rate adjustments
- Image quality settings (brightness, contrast, saturation)
- Invalid configuration handling
- Configuration persistence across reconnections
- Real-time configuration updates during streaming

**Priority**: Medium
**Test Data**: Various camera configurations
**Automation**: Yes

---

## 4. File System Integration Tests

### FS-INT-001: Image Storage Integration
**Feature**: License Plate Image Storage
**Scenario**: Verify detected license plate images are stored correctly

**Test Flow**:
1. **Setup**: Configure image storage directory
2. **Action**: Process detection and trigger image storage
3. **Validation**: Verify images are stored with correct naming and metadata

**Expected Behavior**:
```python
# Detection triggers image storage
detection_result = detection_service.process_image(test_image)
image_path = storage_service.save_detection_image(detection_result)

# Verify file storage
assert os.path.exists(image_path)
assert os.path.getsize(image_path) > 0

# Verify image metadata
metadata = storage_service.get_image_metadata(image_path)
assert metadata["detection_id"] == detection_result["id"]
assert metadata["timestamp"] is not None
```

**Test Cases**:
- Image file creation and naming
- Image quality preservation
- Metadata storage with images
- Directory structure organization
- Storage space management
- File permissions and access
- Image cleanup and archival

**Priority**: Medium
**Test Data**: Test images, detection results
**Automation**: Yes

### FS-INT-002: Video Recording Integration
**Feature**: Video File Recording
**Scenario**: Verify video recording functionality

**Test Flow**:
1. **Setup**: Configure video recording service
2. **Action**: Trigger video recording from camera stream
3. **Validation**: Verify video files are created and playable

**Expected Behavior**:
```python
# Start video recording
recording_session = video_service.start_recording("camera_001", duration=30)

# Wait for recording completion
time.sleep(35)  # Allow buffer time

# Verify recording
video_file = recording_session.get_output_file()
assert os.path.exists(video_file)
assert video_service.is_video_playable(video_file)

# Verify video properties
properties = video_service.get_video_properties(video_file)
assert properties["duration"] >= 30
assert properties["frame_count"] > 0
```

**Test Cases**:
- Continuous video recording
- Event-triggered recording
- Video format and codec validation
- Recording quality settings
- Multiple camera recording
- Recording interruption handling
- Video file corruption detection

**Priority**: Medium
**Test Data**: Test video streams
**Automation**: Yes

### FS-INT-003: Storage Cleanup Integration
**Feature**: Automated Storage Management
**Scenario**: Verify automated cleanup of old files

**Test Flow**:
1. **Setup**: Populate storage with old files
2. **Action**: Trigger automated cleanup process
3. **Validation**: Verify old files are removed according to policy

**Expected Behavior**:
```python
# Create old files
old_files = create_test_files_with_dates(days_ago=30)
recent_files = create_test_files_with_dates(days_ago=5)

# Run cleanup (policy: delete files older than 14 days)
cleanup_service.run_cleanup(retention_days=14)

# Verify cleanup results
for old_file in old_files:
    assert not os.path.exists(old_file)

for recent_file in recent_files:
    assert os.path.exists(recent_file)
```

**Test Cases**:
- Age-based file cleanup
- Size-based storage management
- Priority-based file retention
- Cleanup scheduling and automation
- Storage quota enforcement
- Cleanup failure handling

**Priority**: Low
**Test Data**: Mock file systems with old files
**Automation**: Yes

---

## 5. ML Model Integration Tests

### ML-INT-001: YOLO Model Loading Integration
**Feature**: ML Model Initialization
**Scenario**: Verify YOLO models load correctly and perform inference

**Test Flow**:
1. **Setup**: Configure detection service with YOLO model
2. **Action**: Load model and perform test inference
3. **Validation**: Verify model loads successfully and produces valid results

**Expected Behavior**:
```python
# Model loading
model_path = "/app/models/yolo11m_best.pt"
detection_service = DetectionService(model_path)

# Verify model loading
assert detection_service.is_model_loaded() == True
assert detection_service.get_model_info()["name"] == "yolo11m_best"

# Test inference
test_image = load_test_image_with_license_plate()
detections = detection_service.detect_license_plates(test_image)

# Verify results
assert len(detections) > 0
assert all(d["confidence"] > 0.0 for d in detections)
assert all("bbox" in d for d in detections)
```

**Test Cases**:
- Different YOLO model versions (v8, v11)
- Model loading performance
- GPU vs CPU inference
- Model switching during runtime
- Memory usage optimization
- Model inference accuracy validation
- Batch inference testing

**Priority**: Critical
**Test Data**: Various YOLO model files, test images with known results
**Automation**: Yes

### ML-INT-002: OCR Integration Testing
**Feature**: License Plate Text Recognition
**Scenario**: Verify OCR service integrates with detection pipeline

**Test Flow**:
1. **Setup**: Initialize OCR service with detection service
2. **Action**: Process image through complete detection + OCR pipeline
3. **Validation**: Verify text recognition accuracy

**Expected Behavior**:
```python
# Complete pipeline processing
image_with_plate = load_test_image("license_plate_ABC123.jpg")
detection_result = detection_service.process_image(image_with_plate)

# OCR integration
for detection in detection_result["detections"]:
    plate_text = ocr_service.extract_text(detection["cropped_image"])
    detection["license_plate"] = plate_text

# Verify OCR results
assert detection_result["detections"][0]["license_plate"] == "ABC123"
```

**Test Cases**:
- Clear license plate text recognition
- Blurry/low-quality image handling
- Various license plate formats (US states, international)
- Text normalization and validation
- OCR confidence scoring
- Performance optimization
- Error handling for unreadable plates

**Priority**: High
**Test Data**: License plate images with known text
**Automation**: Yes

### ML-INT-003: Model Performance Integration
**Feature**: ML Pipeline Performance
**Scenario**: Verify ML pipeline meets performance requirements

**Test Flow**:
1. **Setup**: Configure complete ML pipeline
2. **Action**: Process batch of images and measure performance
3. **Validation**: Verify processing times meet SLA requirements

**Expected Behavior**:
```python
# Performance testing
test_images = load_batch_test_images(count=100)
start_time = time.time()

results = []
for image in test_images:
    result = ml_pipeline.process_image(image)
    results.append(result)

total_time = time.time() - start_time
avg_time_per_image = total_time / len(test_images)

# Verify performance targets
assert avg_time_per_image < 0.5  # 500ms per image max
assert total_time < 60  # 1 minute max for 100 images
```

**Test Cases**:
- Single image processing time
- Batch processing performance
- GPU acceleration validation
- Memory usage monitoring
- Concurrent processing capability
- Performance under load
- Resource utilization optimization

**Priority**: High
**Test Data**: Large batches of test images
**Automation**: Yes

---

## 6. WebSocket Integration Tests

### WS-INT-001: Real-time Detection Updates
**Feature**: WebSocket Detection Streaming
**Scenario**: Verify real-time detection updates via WebSocket

**Test Flow**:
1. **Setup**: Establish WebSocket connection to detection stream
2. **Action**: Trigger detection events
3. **Validation**: Verify WebSocket receives updates in real-time

**Expected Behavior**:
```python
# WebSocket client setup
ws_client = WebSocketClient("ws://localhost:8001/ws/stream")
received_messages = []

# Message handler
def on_message(message):
    received_messages.append(json.loads(message))

ws_client.on_message = on_message
ws_client.connect()

# Trigger detection
detection_service.process_image(test_image)
time.sleep(1)  # Allow message propagation

# Verify WebSocket updates
assert len(received_messages) > 0
assert received_messages[0]["type"] == "detection_update"
assert "detections" in received_messages[0]["data"]
```

**Test Cases**:
- Single client connection and updates
- Multiple client connections
- Message ordering and timing
- Connection stability under load
- Message format validation
- Error handling and reconnection
- WebSocket authentication

**Priority**: High
**Test Data**: Test images, mock WebSocket clients
**Automation**: Yes

### WS-INT-002: Dashboard Updates Integration
**Feature**: Dashboard Real-time Updates
**Scenario**: Verify dashboard receives system updates via WebSocket

**Test Flow**:
1. **Setup**: Connect dashboard WebSocket client
2. **Action**: Generate system events (detections, alerts, metrics)
3. **Validation**: Verify dashboard receives appropriate updates

**Expected Behavior**:
```python
# Dashboard WebSocket connection
dashboard_client = DashboardWebSocketClient()
dashboard_client.connect()

# Generate system events
system_event_generator.create_detection_event()
system_event_generator.create_system_alert()
system_event_generator.update_metrics()

# Verify dashboard updates
dashboard_updates = dashboard_client.get_received_updates()
assert any(update["type"] == "detection_count" for update in dashboard_updates)
assert any(update["type"] == "system_alert" for update in dashboard_updates)
assert any(update["type"] == "metrics_update" for update in dashboard_updates)
```

**Test Cases**:
- Detection count updates
- System status changes
- Performance metric updates
- Alert notifications
- Multi-dashboard synchronization
- Update frequency management

**Priority**: Medium
**Test Data**: Mock system events
**Automation**: Yes

---

## 7. External System Integration Tests

### EXT-INT-001: Webhook Integration
**Feature**: External Webhook Notifications
**Scenario**: Verify webhook notifications for detection events

**Test Flow**:
1. **Setup**: Configure webhook endpoint for detection notifications
2. **Action**: Process detection that triggers webhook
3. **Validation**: Verify webhook receives correct notification

**Expected Behavior**:
```python
# Webhook server setup
webhook_server = MockWebhookServer()
webhook_server.start()

# Configure webhook in system
webhook_config = {
    "url": webhook_server.get_url(),
    "events": ["detection_created", "high_confidence_detection"],
    "auth_token": "test_token"
}
webhook_service.configure(webhook_config)

# Trigger detection
detection_result = detection_service.process_image(test_image)

# Verify webhook notification
webhook_requests = webhook_server.get_received_requests()
assert len(webhook_requests) > 0
assert webhook_requests[0]["event_type"] == "detection_created"
assert webhook_requests[0]["data"]["license_plate"] == detection_result["license_plate"]
```

**Test Cases**:
- Successful webhook delivery
- Webhook authentication
- Retry mechanism for failed webhooks
- Webhook rate limiting
- Multiple webhook endpoints
- Webhook payload validation
- Error handling for unreachable webhooks

**Priority**: Medium
**Test Data**: Mock webhook servers
**Automation**: Yes

### EXT-INT-002: API Integration Testing
**Feature**: External API Consumption
**Scenario**: Verify integration with external APIs (if applicable)

**Test Flow**:
1. **Setup**: Mock external API services
2. **Action**: Trigger system functionality that calls external APIs
3. **Validation**: Verify correct API calls and response handling

**Expected Behavior**:
```python
# Mock external API
external_api_mock = ExternalAPIMock()
external_api_mock.setup_response("/validate_plate", {"valid": True})

# System calls external API
validation_result = license_validation_service.validate_plate("ABC123")

# Verify integration
api_calls = external_api_mock.get_received_calls()
assert len(api_calls) > 0
assert api_calls[0]["endpoint"] == "/validate_plate"
assert validation_result["valid"] == True
```

**Test Cases**:
- Successful API integration
- API authentication handling
- Error response handling
- Timeout and retry logic
- Rate limiting compliance
- API version compatibility

**Priority**: Low (if external APIs are used)
**Test Data**: Mock external API responses
**Automation**: Yes

---

## 8. Data Flow Integration Tests

### FLOW-INT-001: End-to-End Detection Flow
**Feature**: Complete Detection Pipeline
**Scenario**: Verify complete data flow from camera to storage

**Test Flow**:
1. **Setup**: Initialize complete system pipeline
2. **Action**: Process camera input through entire pipeline
3. **Validation**: Verify data flows correctly through all components

**Expected Behavior**:
```python
# End-to-end pipeline test
pipeline = DetectionPipeline()
pipeline.initialize_all_services()

# Input: Camera frame
test_frame = load_test_camera_frame()

# Pipeline processing
result = pipeline.process_frame(test_frame)

# Verify each stage
assert result["detection_service"]["processed"] == True
assert result["ocr_service"]["text_extracted"] == True
assert result["storage_service"]["saved"] == True
assert result["webhook_service"]["notified"] == True

# Verify final storage
stored_detection = storage_service.get_latest_detection()
assert stored_detection["license_plate"] is not None
```

**Test Cases**:
- Happy path: successful end-to-end processing
- Partial failure scenarios (one service fails)
- Performance validation across pipeline
- Data consistency throughout pipeline
- Error propagation and handling
- Pipeline scalability testing

**Priority**: Critical
**Test Data**: Complete test datasets
**Automation**: Yes

### FLOW-INT-002: Background Processing Flow
**Feature**: Headless Operation Data Flow
**Scenario**: Verify background processing pipeline works correctly

**Test Flow**:
1. **Setup**: Configure background processing mode
2. **Action**: Start headless processing with test input
3. **Validation**: Verify continuous processing and output distribution

**Expected Behavior**:
```python
# Background processing setup
background_processor = BackgroundProcessor()
background_processor.configure_input_sources(["camera_001", "video_file"])
background_processor.configure_output_channels(["storage", "api_buffer", "webhook"])

# Start processing
background_processor.start()
time.sleep(30)  # Allow processing time

# Verify continuous operation
stats = background_processor.get_processing_stats()
assert stats["frames_processed"] > 0
assert stats["detections_found"] >= 0
assert stats["output_channels_active"] == 3

# Verify output distribution
storage_count = storage_service.count_recent_detections(minutes=1)
api_buffer_count = api_buffer_service.count_recent_detections(minutes=1)
assert storage_count > 0
assert api_buffer_count > 0
```

**Test Cases**:
- Continuous background processing
- Output channel distribution
- Processing interruption and recovery
- Resource usage monitoring
- Multi-input source handling
- Processing queue management

**Priority**: High
**Test Data**: Long-running test streams
**Automation**: Yes

---

## Test Environment Setup

### Docker-based Integration Testing
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  lpr-app:
    build: .
    environment:
      - TESTING=true
      - DATABASE_URL=sqlite:///test_data/test.db
    volumes:
      - ./test_data:/app/test_data
    depends_on:
      - test-database
      - mock-camera-server
  
  test-database:
    image: sqlite:latest
    volumes:
      - ./test_db:/var/lib/sqlite
  
  mock-camera-server:
    image: nginx:alpine
    volumes:
      - ./test_streams:/usr/share/nginx/html
```

### Test Data Management
```python
# Test data fixtures
@pytest.fixture
def sample_detection_data():
    return {
        "license_plate": "TEST123",
        "confidence": 0.95,
        "bbox": [100, 200, 300, 250],
        "timestamp": datetime.utcnow(),
        "camera_id": "test_camera"
    }

@pytest.fixture
def test_database():
    # Create test database
    db = create_test_database()
    yield db
    # Cleanup
    db.cleanup()
```

### Mock Service Setup
```python
# Mock external dependencies
class MockCameraService:
    def __init__(self):
        self.frames = load_test_frames()
    
    def get_frame(self, camera_id):
        return self.frames.get(camera_id)

class MockWebhookServer:
    def __init__(self):
        self.received_requests = []
    
    def receive_webhook(self, request):
        self.received_requests.append(request)
```

## Performance Benchmarks

### Integration Performance Targets
- **End-to-end processing**: < 1 second per frame
- **Database operations**: < 200ms per query
- **WebSocket message delivery**: < 50ms
- **File storage operations**: < 100ms per file
- **ML model inference**: < 500ms per image

### Throughput Targets
- **Concurrent detections**: 10 per second
- **Database transactions**: 100 per second
- **WebSocket connections**: 50 concurrent
- **File operations**: 20 per second

## Automation Framework Integration

### TestNG Configuration
```xml
<!-- testng.xml -->
<suite name="Integration Tests">
    <groups>
        <define name="critical">
            <include name="service-integration"/>
            <include name="database-integration"/>
        </define>
        <define name="performance">
            <include name="performance-tests"/>
        </define>
    </groups>
    
    <test name="Critical Integration Tests">
        <groups>
            <include name="critical"/>
        </groups>
        <packages>
            <package name="com.lpr.integration.services"/>
            <package name="com.lpr.integration.database"/>
        </packages>
    </test>
</suite>
```

### Test Execution Strategy
```python
# Integration test base class
class IntegrationTestBase:
    @classmethod
    def setup_class(cls):
        cls.test_environment = TestEnvironment()
        cls.test_environment.start_all_services()
    
    @classmethod
    def teardown_class(cls):
        cls.test_environment.cleanup_all_services()
    
    def setup_method(self):
        self.test_data = TestDataManager()
        self.test_data.prepare_test_data()
    
    def teardown_method(self):
        self.test_data.cleanup_test_data()
```

## Test Reporting and Monitoring

### Test Metrics Collection
- Integration test execution time
- Service response times
- Database query performance
- Error rates and types
- Resource utilization during tests

### Test Result Analysis
- Success/failure rates by integration category
- Performance trend analysis
- Flaky test identification
- Test coverage analysis
- Integration point failure analysis

## Traceability Matrix

| Integration Category | Test Count | Priority | Automation | Dependencies |
|---------------------|------------|----------|------------|--------------|
| Service Integration | 4 | High | 100% | Mock services |
| Database Integration | 3 | High | 100% | Test database |
| Camera Integration | 3 | High | 75% | Mock cameras |
| File System Integration | 3 | Medium | 100% | Test filesystem |
| ML Model Integration | 3 | Critical | 100% | Test models |
| WebSocket Integration | 2 | High | 100% | Mock clients |
| External Integration | 2 | Medium | 100% | Mock servers |
| Data Flow Integration | 2 | Critical | 100% | Full system |

**Total Integration Tests**: 22  
**Critical Priority**: 8 tests  
**High Priority**: 12 tests  
**Medium Priority**: 2 tests  
**Automation Coverage**: 95%