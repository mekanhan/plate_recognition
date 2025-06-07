"""
End-to-end tests focusing on the saving functionality with real data.
"""
import pytest
import asyncio
import os
import time
import json
import tempfile
import cv2
import numpy as np
import uuid
from unittest.mock import patch
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.services.license_plate_recognition_service import LicensePlateRecognitionService

# Sample license plate images
def create_license_plate_image(text, state=None):
    """Create a sample license plate image with text"""
    img = np.ones((200, 500, 3), dtype=np.uint8) * 255  # White background
    # Add border
    cv2.rectangle(img, (10, 10), (490, 190), (0, 0, 0), 2)
    
    # Add state text if provided
    if state:
        cv2.putText(img, state, (200, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Add license plate text
    cv2.putText(img, text, (100, 120), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    return img

@pytest.fixture
def sample_plates():
    """Create a list of sample license plate images"""
    return [
        (create_license_plate_image("ABC123", "CALIFORNIA"), "ABC123", "CA"),
        (create_license_plate_image("XYZ789", "TEXAS"), "XYZ789", "TX"),
        (create_license_plate_image("DEF456", "NEW YORK"), "DEF456", "NY"),
        (create_license_plate_image("GHI789"), "GHI789", None),
        (create_license_plate_image("JKL012", "FLORIDA"), "JKL012", "FL")
    ]

class TestEndToEndSaving:
    """End-to-end tests for the saving functionality"""
    
    @pytest.mark.asyncio
    async def test_multiple_detections_save_to_file(self, sample_plates):
        """Test saving multiple sequential detections to files"""
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up directories for license plates
            license_plates_dir = os.path.join(temp_dir, "license_plates")
            enhanced_plates_dir = os.path.join(temp_dir, "enhanced_plates")
            os.makedirs(license_plates_dir, exist_ok=True)
            os.makedirs(enhanced_plates_dir, exist_ok=True)
            
            # Create and initialize services
            storage_service = StorageService()
            await storage_service.initialize(
                license_plates_dir=license_plates_dir,
                enhanced_plates_dir=enhanced_plates_dir
            )
            
            # Adjust save interval to ensure quicker saving
            storage_service.save_interval = 0.5
            
            # Set up a detection service using the storage service
            detection_service = DetectionService()
            detection_service.storage_service = storage_service
            
            # Process each sample plate
            for img, plate_text, state in sample_plates:
                # Create a detection result
                detection_result = {
                    "plate_text": plate_text,
                    "confidence": 0.9,
                    "box": [50, 50, 450, 150],
                    "timestamp": time.time(),
                    "ocr_confidence": 0.9,
                    "state": state,
                    "raw_text": f"{state if state else ''} {plate_text}"
                }
                
                # Generate a unique ID
                detection_id = str(uuid.uuid4())
                
                # Process the detection
                await detection_service.process_detection(detection_id, detection_result)
                
                # Brief pause to simulate real-world timing
                await asyncio.sleep(0.1)
            
            # Wait for periodic save to occur
            await asyncio.sleep(1.0)
            
            # Check if the file exists
            session_file = storage_service.session_file
            assert os.path.exists(session_file), f"Session file {session_file} doesn't exist"
            
            # Read the contents
            with open(session_file, 'r') as f:
                saved_data = json.load(f)
            
            # Verify all detections were saved
            assert len(saved_data["detections"]) == len(sample_plates)
            
            # Verify each plate text is in the saved data
            saved_plates = [d["plate_text"] for d in saved_data["detections"]]
            expected_plates = [plate[1] for plate in sample_plates]
            
            for plate in expected_plates:
                assert plate in saved_plates, f"Plate {plate} not found in saved data"
            
            # Clean up
            await storage_service.shutdown()
    
    @pytest.mark.asyncio
    async def test_high_frequency_saving(self):
        """Test saving detections at high frequency"""
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up directories for license plates
            license_plates_dir = os.path.join(temp_dir, "license_plates")
            enhanced_plates_dir = os.path.join(temp_dir, "enhanced_plates")
            os.makedirs(license_plates_dir, exist_ok=True)
            os.makedirs(enhanced_plates_dir, exist_ok=True)
            
            # Create and initialize services
            storage_service = StorageService()
            await storage_service.initialize(
                license_plates_dir=license_plates_dir,
                enhanced_plates_dir=enhanced_plates_dir
            )
            
            # Set very short save interval
            storage_service.save_interval = 0.2
            
            # Generate 20 rapid detections
            detection_tasks = []
            for i in range(20):
                detection = {
                    "detection_id": f"rapid-test-{i}",
                    "plate_text": f"TEST{i:03d}",
                    "confidence": 0.9,
                    "timestamp": time.time(),
                    "box": [100, 100, 300, 200],
                    "raw_text": f"TEST {i:03d}"
                }
                
                # Add detection task
                detection_tasks.append(storage_service.add_detections([detection]))
                
                # Very brief pause
                await asyncio.sleep(0.01)
            
            # Wait for all tasks to complete
            await asyncio.gather(*detection_tasks)
            
            # Wait for periodic save to occur
            await asyncio.sleep(0.5)
            
            # Check if the file exists and has all detections
            session_file = storage_service.session_file
            assert os.path.exists(session_file)
            
            # Read the contents
            with open(session_file, 'r') as f:
                saved_data = json.load(f)
            
            # Verify all detections were saved
            assert len(saved_data["detections"]) == 20
            
            # Clean up
            await storage_service.shutdown()
    
    @pytest.mark.asyncio
    async def test_mixed_valid_invalid_detections(self):
        """Test saving a mix of valid and invalid detections"""
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up directories for license plates
            license_plates_dir = os.path.join(temp_dir, "license_plates")
            enhanced_plates_dir = os.path.join(temp_dir, "enhanced_plates")
            os.makedirs(license_plates_dir, exist_ok=True)
            os.makedirs(enhanced_plates_dir, exist_ok=True)
            
            # Create and initialize services
            storage_service = StorageService()
            await storage_service.initialize(
                license_plates_dir=license_plates_dir,
                enhanced_plates_dir=enhanced_plates_dir
            )
            
            # Create some valid detections
            valid_detections = [
                {
                    "detection_id": "valid-1",
                    "plate_text": "ABC123",
                    "confidence": 0.9,
                    "timestamp": time.time(),
                    "box": [100, 100, 300, 200],
                    "raw_text": "ABC 123"
                },
                {
                    "detection_id": "valid-2",
                    "plate_text": "DEF456",
                    "confidence": 0.85,
                    "timestamp": time.time(),
                    "box": [200, 200, 400, 300],
                    "raw_text": "DEF 456"
                }
            ]
            
            # Create some invalid/empty detections
            invalid_detections = [
                {
                    "detection_id": "invalid-1",
                    "plate_text": "",  # Empty plate text
                    "confidence": 0.1,
                    "timestamp": time.time(),
                    "box": [300, 300, 500, 400],
                    "raw_text": "???"
                }
            ]
            
            # Add all detections
            await storage_service.add_detections(valid_detections)
            await storage_service.add_detections(invalid_detections)
            
            # Force a save
            await storage_service._save_data()
            
            # Check the file
            session_file = storage_service.session_file
            assert os.path.exists(session_file)
            
            # Read the contents
            with open(session_file, 'r') as f:
                saved_data = json.load(f)
            
            # Verify all detections were saved (even invalid ones)
            assert len(saved_data["detections"]) == 3
            
            # Verify the detection details
            plate_texts = [d["plate_text"] for d in saved_data["detections"]]
            assert "ABC123" in plate_texts
            assert "DEF456" in plate_texts
            assert "" in plate_texts  # Empty plate text should still be saved
            
            # Clean up
            await storage_service.shutdown()
            
    @pytest.mark.asyncio
    async def test_extended_detection_session(self):
        """
        Test an extended detection session with periodic saves,
        simulating a real-world scenario of continuous operation
        """
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up directories for license plates
            license_plates_dir = os.path.join(temp_dir, "license_plates")
            enhanced_plates_dir = os.path.join(temp_dir, "enhanced_plates")
            os.makedirs(license_plates_dir, exist_ok=True)
            os.makedirs(enhanced_plates_dir, exist_ok=True)
            
            # Create and initialize services
            storage_service = StorageService()
            await storage_service.initialize(
                license_plates_dir=license_plates_dir,
                enhanced_plates_dir=enhanced_plates_dir
            )
            
            # Set a short save interval for testing
            storage_service.save_interval = 0.5
            
            # Simulate a detection session with plates detected over time
            total_detections = 0
            
            # Run for 3 simulated intervals
            for session in range(3):
                # Add 5 detections in each session
                for i in range(5):
                    detection = {
                        "detection_id": f"session-{session}-det-{i}",
                        "plate_text": f"S{session}D{i}",
                        "confidence": 0.9,
                        "timestamp": time.time(),
                        "box": [100, 100, 300, 200],
                        "raw_text": f"Session {session} Detection {i}"
                    }
                    
                    await storage_service.add_detections([detection])
                    total_detections += 1
                
                # Wait for the periodic save to occur
                await asyncio.sleep(0.6)
                
                # Verify file exists and has the right number of detections
                with open(storage_service.session_file, 'r') as f:
                    saved_data = json.load(f)
                    assert len(saved_data["detections"]) == total_detections
            
            # Final verification
            assert total_detections == 15
            
            # Clean up
            await storage_service.shutdown()