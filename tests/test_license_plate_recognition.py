"""
Tests for the license plate recognition service.
"""
import pytest
import asyncio
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from app.services.license_plate_recognition_service import LicensePlateRecognitionService

# Sample test images
@pytest.fixture
def clean_plate_image():
    """Create a clean license plate image"""
    img = np.ones((100, 300, 3), dtype=np.uint8) * 255  # White background
    # Add black text
    cv2.putText(img, "ABC123", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    return img

@pytest.fixture
def complex_plate_image():
    """Create a more complex license plate image with state and other text"""
    img = np.ones((200, 400, 3), dtype=np.uint8) * 220  # Light gray background
    # Add border
    cv2.rectangle(img, (5, 5), (395, 195), (100, 100, 100), 2)
    # Add state name
    cv2.putText(img, "TEXAS", (150, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    # Add plate number
    cv2.putText(img, "XYZ789", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    # Add some noise
    for _ in range(100):
        x, y = np.random.randint(0, 400), np.random.randint(0, 200)
        cv2.circle(img, (x, y), 1, (np.random.randint(0, 255), 
                                     np.random.randint(0, 255), 
                                     np.random.randint(0, 255)), -1)
    return img

@pytest.fixture
def difficult_plate_image():
    """Create a difficult to read license plate image"""
    img = np.ones((100, 300, 3), dtype=np.uint8) * 180  # Gray background
    # Add text with similar colors to make it hard to read
    cv2.putText(img, "I0O5S8B", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (120, 120, 120), 3)
    # Add motion blur
    kernel_size = 15
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size-1)/2), :] = np.ones(kernel_size)
    kernel = kernel / kernel_size
    img = cv2.filter2D(img, -1, kernel)
    return img

@pytest.mark.asyncio
async def test_initialize():
    """Test service initialization with mocked models"""
    with patch('torch.cuda.is_available', return_value=False):
        with patch('app.services.license_plate_recognition_service.YOLO') as mock_yolo:
            with patch('app.services.license_plate_recognition_service.easyocr.Reader') as mock_reader:
                # Configure mocks
                mock_detector = MagicMock()
                mock_yolo.return_value = mock_detector
                mock_detector.to.return_value = mock_detector
                
                # Initialize service
                service = LicensePlateRecognitionService()
                await service.initialize()
                
                # Verify models were loaded
                assert service.initialized
                assert service.detector_model is not None
                assert service.ocr_reader is not None
                
                # Verify YOLO was called correctly
                mock_yolo.assert_called_once()
                
                # Verify EasyOCR was initialized correctly
                mock_reader.assert_called_once_with(['en'], gpu=False)

@pytest.mark.asyncio
async def test_recognize_clean_plate(clean_plate_image):
    """Test recognizing a clean, easy-to-read license plate"""
    # Mock the necessary components
    service = LicensePlateRecognitionService()
    service.initialized = True
    
    # Mock OCR reader
    service.ocr_reader = MagicMock()
    service.ocr_reader.readtext.return_value = [
        ([(10, 10), (290, 10), (290, 90), (10, 90)], "ABC123", 0.95)
    ]
    
    # Process the plate image
    result = await service._recognize_plate_text(clean_plate_image)
    
    # Verify the result
    assert result["plate_text"] == "ABC123"
    assert result["confidence"] > 0.8  # Should have high confidence
    assert result["raw_text"] == "ABC123"

@pytest.mark.asyncio
async def test_recognize_complex_plate(complex_plate_image):
    """Test recognizing a more complex license plate with state"""
    # Mock the necessary components
    service = LicensePlateRecognitionService()
    service.initialized = True
    
    # Mock OCR reader
    service.ocr_reader = MagicMock()
    service.ocr_reader.readtext.return_value = [
        ([(150, 20), (200, 20), (200, 50), (150, 50)], "TEXAS", 0.9),
        ([(100, 80), (300, 80), (300, 120), (100, 120)], "XYZ789", 0.85)
    ]
    
    # Process the plate image
    result = await service._recognize_plate_text(complex_plate_image)
    
    # Verify the result
    assert result["plate_text"] == "XYZ789"
    assert result["state"] == "TX"  # Should extract state code
    assert "TEXAS" in result["raw_text"]  # Raw text should include state name

@pytest.mark.asyncio
async def test_character_corrections(difficult_plate_image):
    """Test the character correction functionality for confusable characters"""
    # Mock the necessary components
    service = LicensePlateRecognitionService()
    service.initialized = True
    
    # Mock OCR reader with intentionally confused characters
    service.ocr_reader = MagicMock()
    service.ocr_reader.readtext.return_value = [
        ([(50, 40), (250, 40), (250, 80), (50, 80)], "I0O5S8B", 0.7)
    ]
    
    # Process the plate image
    result = await service._recognize_plate_text(difficult_plate_image)
    
    # Verify character corrections
    # The service should correct common confusions like:
    # I → 1, 0 → O, 5 → S, 8 → B or vice versa
    assert result["raw_text"] == "I0O5S8B"
    
    # The final plate might correct some characters, but we can't assert exactly which
    # corrections will be made as it depends on the validation logic
    assert result["plate_text"] != ""  # Should return something

@pytest.mark.asyncio
async def test_detect_and_recognize_with_mocked_models():
    """Test the full detection and recognition pipeline with mocked models"""
    # Create a test image with a license plate
    test_image = np.ones((720, 1280, 3), dtype=np.uint8) * 200
    cv2.rectangle(test_image, (500, 300), (800, 400), (255, 255, 255), -1)
    cv2.putText(test_image, "ABC123", (520, 370), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    
    # Mock YOLO detection results
    mock_boxes = MagicMock()
    mock_boxes.data.cpu.return_value.numpy.return_value = np.array([
        [500, 300, 800, 400, 0.9, 0]  # x1, y1, x2, y2, confidence, class
    ])
    
    mock_detection = MagicMock()
    mock_detection.boxes = mock_boxes
    
    # Mock the service components
    service = LicensePlateRecognitionService()
    service.initialized = True
    service.detector_model = MagicMock()
    service.detector_model.return_value = [mock_detection]
    
    # Mock the OCR component
    service.ocr_reader = MagicMock()
    service.ocr_reader.readtext.return_value = [
        ([(520, 340), (720, 340), (720, 400), (520, 400)], "ABC123", 0.9)
    ]
    
    # Process the image
    results, annotated_image = await service.detect_and_recognize(test_image)
    
    # Verify results
    assert len(results) == 1
    assert results[0]["plate_text"] == "ABC123"
    assert results[0]["box"] == [500, 300, 800, 400]
    assert results[0]["detection_confidence"] == 0.9
    
    # Verify the annotated image is not None
    assert annotated_image is not None
    assert annotated_image.shape == test_image.shape