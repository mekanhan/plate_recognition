"""
Integration tests to verify the interaction between different services.
"""
import pytest
import asyncio
import numpy as np
import cv2
import os
import time
import json
from unittest.mock import patch, MagicMock
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.services.license_plate_recognition_service import LicensePlateRecognitionService

@pytest.mark.asyncio
async def test_detection_to_storage_pipeline(mock_camera_service, mock_storage_service):
    """Test the full pipeline from camera capture to storage"""
    # Set up detection service with mocked dependencies
    detection_service = DetectionService()
    detection_service.camera_service = mock_camera_service
    detection_service.storage_service = mock_storage_service
    
    # Mock the license plate service
    mock_lpr_service = MagicMock(spec=LicensePlateRecognitionService)
    mock_lpr_service.detect_and_recognize.return_value = (
        [
            {
                "plate_text": "TEST123",
                "confidence": 0.9,
                "box": [100, 100, 300, 200],
                "timestamp": time.time(),
                "ocr_confidence": 0.9,
                "state": "CA",
                "raw_text": "TEST LICENSE PLATE"
            }
        ],
        np.zeros((720, 1280, 3), dtype=np.uint8)  # Mock annotated image
    )
    
    # Inject the mocked LPR service
    detection_service.license_plate_service = mock_lpr_service
    
    # Execute the detection from camera
    detection = await detection_service.detect_from_camera()
    
    # Verify detection was successful
    assert detection is not None
    assert detection["plate_text"] == "TEST123"
    
    # Process the detection (would normally be done by a background task)
    detection_id = "test-detection-id"
    await detection_service.process_detection(detection_id, detection)
    
    # Verify the detection was sent to storage
    assert len(mock_storage_service.saved_detections) == 1
    assert mock_storage_service.saved_detections[0]["detection_id"] == detection_id
    assert mock_storage_service.saved_detections[0]["plate_text"] == "TEST123"

@pytest.mark.asyncio
async def test_save_multiple_detections(mock_storage_service):
    """Test saving multiple detections in sequence"""
    # Create test detections
    detections = [
        {
            "detection_id": f"test-{i}",
            "plate_text": f"ABC{i}23",
            "confidence": 0.9,
            "timestamp": time.time(),
            "box": [100, 100, 300, 200],
        } for i in range(5)  # Create 5 different detections
    ]
    
    # Add each detection individually
    for detection in detections:
        await mock_storage_service.add_detections([detection])
    
    # Verify all detections were saved
    assert len(mock_storage_service.saved_detections) == 5
    
    # Verify the detection details
    for i, detection in enumerate(mock_storage_service.saved_detections):
        assert detection["detection_id"] == f"test-{i}"
        assert detection["plate_text"] == f"ABC{i}23"

@pytest.mark.asyncio
async def test_real_file_saving():
    """Test saving to actual files (in a temporary directory)"""
    # Create a temporary directory for testing
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        license_plates_dir = os.path.join(temp_dir, "license_plates")
        enhanced_plates_dir = os.path.join(temp_dir, "enhanced_plates")
        
        # Initialize storage service with the temporary directories
        storage_service = StorageService()
        await storage_service.initialize(
            license_plates_dir=license_plates_dir,
            enhanced_plates_dir=enhanced_plates_dir
        )
        
        # Add test detections
        test_detections = [
            {
                "detection_id": "real-test-1",
                "plate_text": "XYZ789",
                "confidence": 0.95,
                "timestamp": time.time(),
                "box": [100, 100, 300, 200],
                "raw_text": "XYZ 789"
            }
        ]
        
        await storage_service.add_detections(test_detections)
        
        # Force a save
        await storage_service._save_data()
        
        # Verify the file was created
        session_file = storage_service.session_file
        assert os.path.exists(session_file)
        
        # Read the file and verify its contents
        with open(session_file, 'r') as f:
            saved_data = json.load(f)
            
        assert len(saved_data["detections"]) == 1
        assert saved_data["detections"][0]["detection_id"] == "real-test-1"
        assert saved_data["detections"][0]["plate_text"] == "XYZ789"
        
        # Shutdown to clean up
        await storage_service.shutdown()

@pytest.mark.asyncio
async def test_detection_api_to_storage(app_with_mocked_dependencies, test_client, mock_detection_service):
    """Test the API endpoint that should trigger storage"""
    # Create a mock implementation for process_detection that actually adds to storage
    mock_storage_service = MagicMock(spec=StorageService)
    mock_storage_service.saved_detections = []
    
    async def mock_add_detections(detections):
        mock_storage_service.saved_detections.extend(detections)
    
    mock_storage_service.add_detections = mock_add_detections
    
    # Set the storage service on the detection service
    mock_detection_service.storage_service = mock_storage_service
    
    # Make the API request
    response = test_client.post("/detection/detect")
    
    # Verify the API response
    assert response.status_code == 200
    json_data = response.json()
    assert "detection_id" in json_data
    
    # Wait a moment for the background task to complete
    await asyncio.sleep(0.1)
    
    # Verify the detection was sent to storage
    # Note: Since this is mocked, we can only verify if process_detection was called
    assert mock_detection_service.process_detection.called