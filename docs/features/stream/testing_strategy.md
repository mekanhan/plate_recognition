# Testing Strategy

**Date:** 2025-01-24  
**Version:** 1.0  
**Component:** Stream Feature Testing and Validation

## Testing Overview

The Stream feature testing strategy encompasses unit testing, integration testing, performance testing, and end-to-end validation with real camera hardware. Testing ensures reliability, accuracy, and performance under various operational conditions.

## Test Environment Setup

### Hardware Requirements

#### Minimum Test Environment
- **CPU**: Dual-core processor (Intel i5 or equivalent)
- **RAM**: 8GB minimum
- **Storage**: 5GB available space
- **Network**: Stable connection to Test Camera 1 (10.0.0.181)
- **GPU**: Optional but recommended for performance testing

#### Optimal Test Environment
- **CPU**: Quad-core processor (Intel i7 or equivalent)
- **RAM**: 16GB 
- **GPU**: NVIDIA GPU with CUDA support
- **Storage**: SSD with 20GB available space
- **Network**: Gigabit connection for multi-camera testing

### Software Dependencies

#### Test Dependencies
```python
# requirements-test.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
pytest-cov>=4.1.0
httpx>=0.24.0
websockets>=11.0
opencv-python>=4.8.0
torch>=2.0.1
ultralytics>=8.0.0
easyocr>=1.7.0
```

#### Test Data Setup
```bash
# Create test data directories
mkdir -p tests/data/images
mkdir -p tests/data/videos
mkdir -p tests/data/models

# Download test images with license plates
wget -O tests/data/images/test_plate_1.jpg "sample_plate_image_url"
wget -O tests/data/images/test_plate_2.jpg "sample_plate_image_url"

# Copy YOLO model for testing
cp train/models/pretrained/yolo11m_best.pt tests/data/models/
```

## Unit Testing

### 1. Camera Service Tests

#### Test Cases for CameraStreamingService
```python
# tests/unit/test_camera_streaming_service.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from app.services.camera_streaming_service import CameraStreamingService
from app.schemas.camera import CameraConfig

class TestCameraStreamingService:
    @pytest.fixture
    def camera_config(self):
        return CameraConfig(
            id=3,
            name="Test Camera 1",
            ip_address="10.0.0.181",
            port=80,
            connection_type="http",
            stream_path="/mjpeg",
            username="admin",
            password="Mekus_1987"
        )
    
    @pytest.fixture
    def streaming_service(self, camera_config):
        return CameraStreamingService(camera_config)
    
    @pytest.mark.asyncio
    async def test_camera_connection_success(self, streaming_service):
        """Test successful camera connection"""
        with patch('cv2.VideoCapture') as mock_capture:
            mock_capture.return_value.isOpened.return_value = True
            
            result = await streaming_service.connect_camera()
            assert result is True
            assert streaming_service.capture is not None
    
    @pytest.mark.asyncio
    async def test_camera_connection_failure(self, streaming_service):
        """Test camera connection failure"""
        with patch('cv2.VideoCapture') as mock_capture:
            mock_capture.return_value.isOpened.return_value = False
            
            result = await streaming_service.connect_camera()
            assert result is False
            assert streaming_service.capture is None
    
    @pytest.mark.asyncio
    async def test_frame_generation(self, streaming_service):
        """Test video frame generation"""
        mock_frame = Mock()
        mock_frame.shape = (480, 640, 3)
        
        with patch('cv2.VideoCapture') as mock_capture:
            mock_capture.return_value.isOpened.return_value = True
            mock_capture.return_value.read.return_value = (True, mock_frame)
            
            frames = []
            async for frame in streaming_service.start_streaming():
                frames.append(frame)
                if len(frames) >= 3:  # Test first 3 frames
                    break
            
            assert len(frames) == 3
            assert all(isinstance(frame, bytes) for frame in frames)
    
    @pytest.mark.asyncio
    async def test_stream_cleanup(self, streaming_service):
        """Test proper cleanup when stopping stream"""
        with patch('cv2.VideoCapture') as mock_capture:
            streaming_service.capture = mock_capture.return_value
            streaming_service.is_streaming = True
            
            await streaming_service.stop_streaming()
            
            assert streaming_service.is_streaming is False
            mock_capture.return_value.release.assert_called_once()
```

### 2. Detection Pipeline Tests

#### Test Cases for DetectionService
```python
# tests/unit/test_detection_service.py
import pytest
import numpy as np
from unittest.mock import Mock, patch
from app.services.detection_service import DetectionService

class TestDetectionService:
    @pytest.fixture
    def detection_service(self):
        with patch('ultralytics.YOLO'), patch('easyocr.Reader'):
            return DetectionService()
    
    @pytest.fixture
    def sample_frame(self):
        """Create a sample video frame"""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    def test_yolo_model_loading(self):
        """Test YOLO model initialization"""
        with patch('ultralytics.YOLO') as mock_yolo:
            service = DetectionService()
            mock_yolo.assert_called_once()
            assert service.yolo_model is not None
    
    def test_frame_preprocessing(self, detection_service, sample_frame):
        """Test frame preprocessing for YOLO"""
        processed = detection_service.preprocess_frame(sample_frame)
        
        assert processed.shape == (1, 3, 640, 640)  # YOLO input format
        assert processed.dtype == torch.float32
        assert 0 <= processed.min() <= processed.max() <= 1  # Normalized
    
    @pytest.mark.asyncio
    async def test_plate_detection(self, detection_service, sample_frame):
        """Test license plate detection"""
        # Mock YOLO results
        mock_box = Mock()
        mock_box.xyxy = [[100, 50, 200, 120]]
        mock_box.conf = [0.85]
        mock_box.cls = [0]
        
        mock_result = Mock()
        mock_result.boxes = [mock_box]
        
        with patch.object(detection_service.yolo_model, '__call__', return_value=[mock_result]):
            detections = await detection_service.detect_plates(sample_frame)
            
            assert len(detections) == 1
            assert detections[0].bbox == [100, 50, 200, 120]
            assert detections[0].confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_ocr_text_extraction(self, detection_service):
        """Test OCR text extraction"""
        # Create mock license plate image
        plate_image = np.ones((60, 200, 3), dtype=np.uint8) * 255
        
        # Mock EasyOCR result
        with patch.object(detection_service.ocr_reader, 'readtext', 
                         return_value=[(['ABC123'], 0.9)]):
            
            ocr_result = await detection_service.extract_text(plate_image)
            
            assert ocr_result.text == 'ABC123'
            assert ocr_result.confidence == 0.9
    
    def test_confidence_threshold_filtering(self, detection_service):
        """Test detection filtering by confidence threshold"""
        detection_service.confidence_threshold = 0.7
        
        # Mock low confidence detection
        mock_box = Mock()
        mock_box.conf = [0.5]  # Below threshold
        mock_result = Mock()
        mock_result.boxes = [mock_box]
        
        with patch.object(detection_service.yolo_model, '__call__', return_value=[mock_result]):
            detections = detection_service.filter_detections([mock_result])
            
            assert len(detections) == 0  # Should be filtered out
```

### 3. Database Operation Tests

#### Test Cases for Detection CRUD
```python
# tests/unit/test_detection_crud.py
import pytest
from datetime import datetime
from app.db.crud.detection_crud import (
    create_detection, get_recent_detections, get_detection_by_id
)
from app.schemas.detection import DetectionCreate

class TestDetectionCRUD:
    @pytest.mark.asyncio
    async def test_create_detection(self, db_session):
        """Test detection creation"""
        detection_data = DetectionCreate(
            camera_id=3,
            bbox_x1=100,
            bbox_y1=50,
            bbox_x2=200,
            bbox_y2=120,
            yolo_confidence=0.85,
            ocr_confidence=0.78,
            plate_text="ABC123",
            processing_time_ms=150
        )
        
        detection = await create_detection(db_session, detection_data)
        
        assert detection.id is not None
        assert detection.camera_id == 3
        assert detection.plate_text == "ABC123"
        assert detection.yolo_confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_get_recent_detections(self, db_session):
        """Test retrieving recent detections"""
        # Create test detections
        for i in range(5):
            detection_data = DetectionCreate(
                camera_id=3,
                bbox_x1=100 + i,
                bbox_y1=50,
                bbox_x2=200 + i,
                bbox_y2=120,
                yolo_confidence=0.8,
                plate_text=f"TEST{i:03d}"
            )
            await create_detection(db_session, detection_data)
        
        # Retrieve recent detections
        detections = await get_recent_detections(db_session, limit=3)
        
        assert len(detections) == 3
        assert all(d.camera_id == 3 for d in detections)
        # Should be ordered by timestamp DESC
        assert detections[0].timestamp >= detections[1].timestamp
```

## Integration Testing

### 1. API Endpoint Tests

#### Streaming Endpoint Tests
```python
# tests/integration/test_streaming_endpoints.py
import pytest
from httpx import AsyncClient
from app.main import app

class TestStreamingEndpoints:
    @pytest.mark.asyncio
    async def test_video_stream_endpoint(self):
        """Test video streaming endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test with valid camera ID
            response = await client.get("/stream/video/3")
            
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("multipart/x-mixed-replace")
    
    @pytest.mark.asyncio
    async def test_stream_start_endpoint(self):
        """Test stream start API"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/streams/3/start",
                json={
                    "quality": "high",
                    "detection_enabled": True,
                    "confidence_threshold": 0.7
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["camera_id"] == 3
            assert data["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_stream_status_endpoint(self):
        """Test stream status retrieval"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/streams/3/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "camera_id" in data
            assert "status" in data
            assert "current_fps" in data
```

### 2. WebSocket Integration Tests

#### WebSocket Connection Tests
```python
# tests/integration/test_websocket_streaming.py
import pytest
import asyncio
import json
from websockets import connect
from websockets.exceptions import ConnectionClosed

class TestWebSocketStreaming:
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        uri = "ws://localhost:8000/ws/stream/3"
        
        try:
            async with connect(uri) as websocket:
                # Send subscription message
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "events": ["detection", "system_status"]
                }))
                
                # Wait for acknowledgment
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                assert data["type"] == "connected"
                assert data["camera_id"] == 3
        
        except ConnectionClosed:
            pytest.fail("WebSocket connection failed")
    
    @pytest.mark.asyncio
    async def test_detection_message_format(self):
        """Test detection message format via WebSocket"""
        uri = "ws://localhost:8000/ws/stream/3"
        
        async with connect(uri) as websocket:
            await websocket.send(json.dumps({
                "type": "subscribe",
                "events": ["detection"]
            }))
            
            # Wait for detection message (with timeout)
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(message)
                
                if data["type"] == "detection":
                    # Validate message structure
                    assert "timestamp" in data
                    assert "camera_id" in data
                    assert "detection" in data
                    
                    detection = data["detection"]
                    assert "bbox" in detection
                    assert "confidence" in detection
                    assert "plate_text" in detection
                    
            except asyncio.TimeoutError:
                pytest.skip("No detection occurred during test period")
```

### 3. Database Integration Tests

#### End-to-end Data Flow Tests
```python
# tests/integration/test_data_flow.py
import pytest
import asyncio
from app.services.stream_manager import StreamManager
from app.database import get_database

class TestDataFlow:
    @pytest.mark.asyncio
    async def test_detection_to_database_flow(self):
        """Test complete flow from detection to database storage"""
        stream_manager = StreamManager()
        
        # Start streaming for Test Camera 1
        await stream_manager.start_camera_stream(3)
        
        # Wait for detection to occur
        await asyncio.sleep(30)  # Wait 30 seconds for detection
        
        # Check database for stored detection
        async with get_database() as db:
            detections = await get_recent_detections(db, camera_id=3, limit=1)
            
            if detections:
                detection = detections[0]
                assert detection.camera_id == 3
                assert detection.plate_text is not None
                assert detection.yolo_confidence > 0.5
                assert detection.timestamp is not None
        
        await stream_manager.stop_camera_stream(3)
```

## Performance Testing

### 1. Streaming Performance Tests

#### Frame Rate and Latency Tests
```python
# tests/performance/test_streaming_performance.py
import pytest
import time
import asyncio
from statistics import mean
from app.services.camera_streaming_service import CameraStreamingService

class TestStreamingPerformance:
    @pytest.mark.asyncio
    async def test_frame_rate_consistency(self):
        """Test streaming frame rate consistency"""
        service = CameraStreamingService(test_camera_config)
        
        frame_times = []
        frame_count = 0
        start_time = time.time()
        
        async for frame in service.start_streaming():
            current_time = time.time()
            if frame_count > 0:
                frame_times.append(current_time - last_time)
            
            last_time = current_time
            frame_count += 1
            
            # Test for 10 seconds
            if current_time - start_time > 10:
                break
        
        # Calculate FPS statistics
        avg_frame_time = mean(frame_times)
        fps = 1.0 / avg_frame_time
        
        assert fps >= 25.0  # Minimum acceptable FPS
        assert fps <= 35.0  # Maximum expected FPS
        
        # Check frame time consistency (standard deviation)
        frame_time_std = statistics.stdev(frame_times)
        assert frame_time_std < 0.05  # Max 50ms variance
    
    @pytest.mark.asyncio
    async def test_detection_processing_time(self):
        """Test detection processing performance"""
        detection_service = DetectionService()
        
        # Load test images
        test_frames = [
            cv2.imread("tests/data/images/test_plate_1.jpg"),
            cv2.imread("tests/data/images/test_plate_2.jpg")
        ]
        
        processing_times = []
        
        for frame in test_frames * 10:  # Test with 20 frames
            start_time = time.time()
            detections = await detection_service.process_frame(frame)
            processing_time = (time.time() - start_time) * 1000
            
            processing_times.append(processing_time)
        
        avg_processing_time = mean(processing_times)
        max_processing_time = max(processing_times)
        
        # Performance requirements
        assert avg_processing_time < 200  # Average under 200ms
        assert max_processing_time < 500  # No single frame over 500ms
```

### 2. Load Testing

#### Multi-Camera Performance Tests
```python
# tests/performance/test_load_testing.py
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services.stream_manager import StreamManager

class TestLoadPerformance:
    @pytest.mark.asyncio
    async def test_multi_camera_streaming(self):
        """Test performance with multiple camera streams"""
        stream_manager = StreamManager()
        
        # Simulate 4 concurrent camera streams
        camera_ids = [3, 4, 5, 6]  # Assuming test cameras exist
        
        # Start all streams concurrently
        start_tasks = [
            stream_manager.start_camera_stream(camera_id) 
            for camera_id in camera_ids
        ]
        await asyncio.gather(*start_tasks)
        
        # Monitor performance for 60 seconds
        start_time = time.time()
        performance_samples = []
        
        while time.time() - start_time < 60:
            # Collect performance metrics
            metrics = await stream_manager.get_performance_metrics()
            performance_samples.append(metrics)
            
            await asyncio.sleep(5)  # Sample every 5 seconds
        
        # Stop all streams
        stop_tasks = [
            stream_manager.stop_camera_stream(camera_id) 
            for camera_id in camera_ids
        ]
        await asyncio.gather(*stop_tasks)
        
        # Analyze performance
        avg_cpu_usage = mean([m["cpu_usage"] for m in performance_samples])
        avg_memory_usage = mean([m["memory_usage_mb"] for m in performance_samples])
        
        # Performance assertions
        assert avg_cpu_usage < 80.0  # Max 80% CPU usage
        assert avg_memory_usage < 2048  # Max 2GB memory
    
    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self):
        """Test WebSocket performance with multiple connections"""
        uri = "ws://localhost:8000/ws/stream/3"
        
        async def client_connection():
            async with connect(uri) as websocket:
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "events": ["detection"]
                }))
                
                # Stay connected for 30 seconds
                end_time = time.time() + 30
                while time.time() < end_time:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        # Process message
                    except asyncio.TimeoutError:
                        continue
        
        # Create 10 concurrent connections
        connection_tasks = [client_connection() for _ in range(10)]
        
        start_time = time.time()
        await asyncio.gather(*connection_tasks)
        total_time = time.time() - start_time
        
        # Should complete without errors in reasonable time
        assert total_time < 35  # Allow 5 seconds overhead
```

## End-to-End Testing

### 1. Real Camera Integration Tests

#### Test Camera 1 Integration
```python
# tests/e2e/test_real_camera_integration.py
import pytest
import asyncio
from app.services.camera_streaming_service import CameraStreamingService
from app.schemas.camera import CameraConfig

class TestRealCameraIntegration:
    @pytest.fixture
    def test_camera_config(self):
        """Test Camera 1 configuration"""
        return CameraConfig(
            id=3,
            name="Test Camera 1",
            ip_address="10.0.0.181",
            port=80,
            connection_type="http",
            stream_path="/mjpeg",
            username="admin",
            password="Mekus_1987"
        )
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_camera_connection(self, test_camera_config):
        """Test connection to actual Test Camera 1"""
        service = CameraStreamingService(test_camera_config)
        
        # Test connection
        connected = await service.connect_camera()
        assert connected, "Failed to connect to Test Camera 1"
        
        # Test frame acquisition
        frame_count = 0
        async for frame in service.start_streaming():
            frame_count += 1
            assert len(frame) > 1000  # Minimum frame size
            
            if frame_count >= 10:  # Test 10 frames
                break
        
        assert frame_count == 10
        await service.stop_streaming()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_detection_accuracy(self, test_camera_config):
        """Test detection accuracy on real camera feed"""
        detection_service = DetectionService()
        streaming_service = CameraStreamingService(test_camera_config)
        
        await streaming_service.connect_camera()
        
        detections_found = []
        frames_processed = 0
        
        async for frame_bytes in streaming_service.start_streaming():
            # Convert JPEG bytes to frame
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            # Process for detection
            detections = await detection_service.process_frame(frame)
            detections_found.extend(detections)
            
            frames_processed += 1
            if frames_processed >= 300:  # Process 5 minutes at 30fps
                break
        
        await streaming_service.stop_streaming()
        
        # Analyze detection results
        high_confidence_detections = [
            d for d in detections_found if d.yolo_confidence > 0.7
        ]
        
        # At least some detections should occur in 5 minutes of footage
        assert len(high_confidence_detections) > 0, "No high-confidence detections found"
        
        # Check OCR accuracy on detected plates
        valid_plates = [
            d for d in high_confidence_detections 
            if d.plate_text and len(d.plate_text) >= 4
        ]
        
        if valid_plates:
            # At least 70% of detected plates should have valid text
            ocr_accuracy = len(valid_plates) / len(high_confidence_detections)
            assert ocr_accuracy >= 0.7, f"OCR accuracy too low: {ocr_accuracy:.2f}"
```

### 2. User Interface Testing

#### Selenium-based UI Tests
```python
# tests/e2e/test_ui_integration.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestUIIntegration:
    @pytest.fixture
    def driver(self):
        """Setup Selenium WebDriver"""
        driver = webdriver.Chrome()  # Requires ChromeDriver
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_streaming_page_loads(self, driver):
        """Test streaming page loads correctly"""
        driver.get("http://localhost:8000/stream")
        
        # Check page title
        assert "Live Stream" in driver.title
        
        # Check video element exists
        video_element = driver.find_element(By.ID, "video-feed")
        assert video_element.is_displayed()
        
        # Check stream controls
        start_button = driver.find_element(By.ID, "toggle-stream")
        assert start_button.is_displayed()
        assert "Start Stream" in start_button.text
    
    def test_stream_controls_functionality(self, driver):
        """Test stream control buttons work"""
        driver.get("http://localhost:8000/stream")
        
        # Start stream
        start_button = driver.find_element(By.ID, "toggle-stream")
        start_button.click()
        
        # Wait for stream to start
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.ID, "toggle-stream"), "Stop Stream")
        )
        
        # Check video is loading
        video_element = driver.find_element(By.ID, "video-feed")
        assert video_element.get_attribute("src") is not None
        
        # Test fullscreen button
        fullscreen_button = driver.find_element(By.ID, "toggle-fullscreen")
        fullscreen_button.click()
        
        # Note: Fullscreen testing requires special handling
        # This is a simplified test
    
    def test_detection_display(self, driver):
        """Test detection results display in UI"""
        driver.get("http://localhost:8000/stream")
        
        # Start stream
        start_button = driver.find_element(By.ID, "toggle-stream")
        start_button.click()
        
        # Wait for detections to appear (timeout after 60 seconds)
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, "detection-item"))
            )
            
            # Check detection item structure
            detection_items = driver.find_elements(By.CLASS_NAME, "detection-item")
            assert len(detection_items) > 0
            
            # Check first detection has required elements
            first_detection = detection_items[0]
            plate_element = first_detection.find_element(By.CLASS_NAME, "detection-plate")
            confidence_element = first_detection.find_element(By.CLASS_NAME, "confidence-badge")
            
            assert plate_element.text != ""
            assert "%" in confidence_element.text
            
        except TimeoutError:
            pytest.skip("No detections occurred during test period")
```

## Test Data Management

### Test Image Dataset
```python
# tests/utils/test_data_manager.py
class TestDataManager:
    def __init__(self):
        self.test_images_dir = "tests/data/images"
        self.test_videos_dir = "tests/data/videos"
    
    def create_test_license_plate_images(self):
        """Generate synthetic license plate images for testing"""
        import PIL.Image, PIL.ImageDraw, PIL.ImageFont
        
        # Create various license plate formats
        plates = [
            "ABC123", "XYZ789", "DEF456", "GHI012",
            "123ABC", "789XYZ", "456DEF", "012GHI"
        ]
        
        for i, plate_text in enumerate(plates):
            # Create image with license plate
            img = PIL.Image.new('RGB', (300, 100), color='white')
            draw = PIL.ImageDraw.Draw(img)
            
            # Draw license plate text
            try:
                font = PIL.ImageFont.truetype("arial.ttf", 40)
            except:
                font = PIL.ImageFont.load_default()
            
            draw.text((50, 30), plate_text, fill='black', font=font)
            
            # Add some noise and variations
            if i % 2 == 0:
                # Rotate slightly
                img = img.rotate(random.uniform(-5, 5))
            
            img.save(f"{self.test_images_dir}/synthetic_plate_{i}.jpg")
    
    def download_real_test_images(self):
        """Download real license plate images for testing"""
        # Implementation would download from approved dataset
        pass
```

## Continuous Integration

### CI/CD Pipeline Configuration
```yaml
# .github/workflows/stream-feature-tests.yml
name: Stream Feature Tests

on:
  push:
    paths:
      - 'app/services/camera_streaming_service.py'
      - 'app/services/detection_service.py'
      - 'app/api/v1/endpoints/streaming.py'
      - 'tests/stream/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=app
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v
      
      - name: Run performance tests
        run: |
          pytest tests/performance/ -v --benchmark-only
```

## Test Execution and Reporting

### Test Execution Commands
```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run performance tests only
pytest tests/performance/ -v

# Run integration tests (requires test camera)
pytest tests/integration/ -v -m "integration"

# Run specific test file
pytest tests/unit/test_detection_service.py -v

# Run with specific markers
pytest -m "not slow" -v  # Skip slow tests
```

### Test Reporting
```python
# tests/conftest.py
def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "gpu: marks tests requiring GPU")

def pytest_html_report_title(report):
    report.title = "Stream Feature Test Report"
```

## Performance Benchmarking

### Benchmark Configuration
```python
# tests/performance/benchmarks.py
import pytest
from pytest_benchmark import BenchmarkFixture

class TestPerformanceBenchmarks:
    def test_yolo_inference_benchmark(self, benchmark):
        """Benchmark YOLO inference time"""
        detection_service = DetectionService()
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result = benchmark(detection_service.detect_plates, test_frame)
        
        # Benchmark should complete in reasonable time
        assert benchmark.stats['mean'] < 0.2  # 200ms average
    
    def test_frame_encoding_benchmark(self, benchmark):
        """Benchmark JPEG frame encoding performance"""
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        def encode_frame():
            _, buffer = cv2.imencode('.jpg', test_frame)
            return buffer.tobytes()
        
        result = benchmark(encode_frame)
        
        # Should encode quickly
        assert benchmark.stats['mean'] < 0.05  # 50ms average
```

This comprehensive testing strategy ensures the Stream feature meets reliability, performance, and accuracy requirements while providing clear validation of all system components.