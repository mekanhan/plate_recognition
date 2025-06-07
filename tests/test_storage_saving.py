# tests/test_storage_saving.py
import pytest
from app.services.storage_service import StorageService
from app.models.detection import Detection

def test_storage_saves_detections():
    """Test that detections are properly saved to storage."""
    # Arrange
    storage = StorageService()
    storage.clear_database()  # Start with clean state
    detection = Detection(
        plate_text="ABC123",
        confidence=0.95,
        timestamp="2023-06-14T12:00:00",
        region="somewhere",
        vehicle_type="car",
        image_path="sample.jpg"
    )
    
    # Act
    storage.add_detection(detection)
    saved_detections = storage.get_detections()
    
    # Assert
    assert len(saved_detections) == 1
    assert saved_detections[0].plate_text == "ABC123"
    assert storage.is_in_storage("ABC123")

def test_empty_storage_returns_no_detections():
    """Test that an empty storage returns no detections."""
    # Arrange
    storage = StorageService()
    storage.clear_database()
    
    # Act
    detections = storage.get_detections()
    
    # Assert
    assert len(detections) == 0

def test_multiple_detections_saved():
    """Test that multiple detections are saved correctly."""
    # Arrange
    storage = StorageService()
    storage.clear_database()
    plates = ["ABC123", "XYZ789", "DEF456"]
    
    # Act
    for i, plate in enumerate(plates):
        detection = Detection(
            plate_text=plate,
            confidence=0.9,
            timestamp=f"2023-06-14T12:0{i}:00",
            region="somewhere",
            vehicle_type="car",
            image_path=f"sample{i}.jpg"
        )
        storage.add_detection(detection)
    
    # Assert
    saved_detections = storage.get_detections()
    assert len(saved_detections) == 3
    saved_plates = [d.plate_text for d in saved_detections]
    for plate in plates:
        assert plate in saved_plates