"""
Configuration for pytest fixtures shared across test files.
"""
import pytest
import os
import sys
import asyncio
from fastapi.testclient import TestClient
import numpy as np
import cv2
from unittest.mock import MagicMock, patch

# Make sure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.services.license_plate_recognition_service import LicensePlateRecognitionService
from app.dependencies.detection import get_detection_service

# Sample test data
@pytest.fixture
def sample_license_plate_image():
    """Create a sample image with a license plate-like object"""
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Draw a white rectangle representing a license plate
    cv2.rectangle(img, (500, 400), (800, 500), (255, 255, 255), -1)
    # Add some black text
    cv2.putText(img, "ABC123", (520, 470), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 5)
    return img

@pytest.fixture
def sample_license_plate_image_bytes(sample_license_plate_image):
    """Convert sample image to bytes for API testing"""
    _, buffer = cv2.imencode('.jpg', sample_license_plate_image)
    return buffer.tobytes()

@pytest.fixture
def mock_camera_service():
    """Mock camera service that returns a sample frame"""
    service = MagicMock(spec=CameraService)
    async def mock_get_frame():
        # Create a sample frame with timestamp
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Draw a white rectangle representing a license plate
        cv2.rectangle(img, (500, 400), (800, 500), (255, 255, 255), -1)
        # Add some black text
        cv2.putText(img, "ABC123", (520, 470), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 5)
        return img, 123456789.0
    
    service.get_frame = mock_get_frame
    service.initialize = MagicMock(return_value=asyncio.Future())
    service.initialize.return_value.set_result(None)
    return service

@pytest.fixture
def mock_storage_service():
    """Mock storage service that records saved detections"""
    service = MagicMock(spec=StorageService)
    service.saved_detections = []
    
    async def mock_add_detections(detections):
        service.saved_detections.extend(detections)
        return len(detections)
    
    service.add_detections = mock_add_detections
    service.initialize = MagicMock(return_value=asyncio.Future())
    service.initialize.return_value.set_result(None)
    return service

@pytest.fixture
def test_client():
    """Create a test client for FastAPI"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_detection_service():
    """Mock detection service for API testing"""
    service = MagicMock(spec=DetectionService)
    service.detections_processed = 0
    service.last_detection_time = 123456789.0
    
    async def mock_detect_from_camera():
        return {
            "plate_text": "ABC123", 
            "confidence": 0.9,
            "box": [500, 400, 800, 500],
            "timestamp": 123456789.0,
            "ocr_confidence": 0.9,
            "state": "CA",
            "raw_text": "ABC123"
        }
    
    async def mock_detect_from_image(image_data):
        return {
            "plate_text": "XYZ789", 
            "confidence": 0.85,
            "box": [100, 100, 300, 200],
            "timestamp": 123456789.0,
            "ocr_confidence": 0.85,
            "state": "TX",
            "raw_text": "XYZ789"
        }
    
    async def mock_process_detection(detection_id, detection_result):
        service.detections_processed += 1
    
    service.detect_from_camera = mock_detect_from_camera
    service.detect_from_image = mock_detect_from_image
    service.process_detection = mock_process_detection
    service.initialize = MagicMock(return_value=asyncio.Future())
    service.initialize.return_value.set_result(None)
    
    return service

# Override app dependencies for testing
@pytest.fixture
def app_with_mocked_dependencies(mock_detection_service):
    """Set up the app with mocked dependencies for testing"""
    app.dependency_overrides[get_detection_service] = lambda: mock_detection_service
    yield app
    # Clean up
    app.dependency_overrides = {}