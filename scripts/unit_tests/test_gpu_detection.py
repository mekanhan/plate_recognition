#!/usr/bin/env python
"""
Test script to verify GPU-accelerated license plate detection and storage
"""
import asyncio
import cv2
import numpy as np
import time
import os
import sys
from pathlib import Path

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.license_plate_recognition_service import LicensePlateRecognitionService
from app.services.storage_service import StorageService

async def test_gpu_detection(image_path=None):
    """Test license plate detection with GPU acceleration"""
    print("\n=== Testing GPU-Accelerated License Plate Detection ===\n")
    
    # Create and initialize services
    print("Initializing license plate recognition service...")
    lpr_service = LicensePlateRecognitionService()
    await lpr_service.initialize()
    
    print("Initializing storage service...")
    storage_service = StorageService()
    await storage_service.initialize()
    
    # Load or create test image
    if image_path and os.path.exists(image_path):
        print(f"Loading test image from: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            print(f"Failed to load image: {image_path}")
            image = create_test_image()
    else:
        print("Creating test image with license plate...")
        image = create_test_image()
    
    # Run detection multiple times to measure performance
    num_runs = 5
    total_time = 0
    total_detections = 0
    
    print(f"\nRunning {num_runs} detection tests...")
    
    for i in range(num_runs):
        print(f"\nTest run {i+1}/{num_runs}")
        
        # Run detection with timing
        start_time = time.time()
        detections, annotated_image = await lpr_service.detect_and_recognize(image)
        end_time = time.time()
        
        # Calculate timing
        detection_time = end_time - start_time
        total_time += detection_time
        
        # Print results
        print(f"Detection time: {detection_time*1000:.2f} ms")
        print(f"Found {len(detections)} license plates")
        
        for j, detection in enumerate(detections):
            print(f"  Plate {j+1}: {detection.get('plate_text', 'Unknown')}")
            print(f"    Confidence: {detection.get('confidence', 0):.2f}")
            print(f"    State: {detection.get('state', 'Unknown')}")
        
        total_detections += len(detections)
        
        # Save detections to storage
        if detections:
            for detection in detections:
                detection["detection_id"] = f"test-{i}-{time.time()}"
            
            print(f"Saving {len(detections)} detections to storage...")
            await storage_service.add_detections(detections)
    
    # Calculate average performance
    avg_time = total_time / num_runs
    print(f"\nAverage detection time: {avg_time*1000:.2f} ms")
    print(f"Average detections per image: {total_detections/num_runs:.2f}")
    
    # Check if detections were saved to storage
    print("\nChecking if detections were saved to storage...")
    
    saved_detections = await storage_service.get_detections()
    print(f"Found {len(saved_detections)} saved detections in storage")
    
    # Check if the file exists
    session_file = storage_service.session_file
    if os.path.exists(session_file):
        file_size = os.path.getsize(session_file)
        print(f"Storage file exists: {session_file} ({file_size} bytes)")
    else:
        print(f"Storage file does not exist: {session_file}")
    
    # Shutdown services
    await lpr_service.shutdown()
    await storage_service.shutdown()
    
    # Display annotated image
    if annotated_image is not None:
        # Resize for display if needed
        height, width = annotated_image.shape[:2]
        if width > 1200:
            scale = 1200 / width
            annotated_image = cv2.resize(annotated_image, None, fx=scale, fy=scale)
            
        cv2.imshow("License Plate Detection", annotated_image)
        print("\nShowing annotated image. Press any key to close.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    print("\nTest completed!")

def create_test_image():
    """Create a test image with a license plate"""
    # Create background (road scene)
    img = np.ones((720, 1280, 3), dtype=np.uint8) * 100  # Dark gray
    
    # Draw a car shape
    car_color = (70, 70, 70)  # Dark gray
    cv2.rectangle(img, (400, 300), (880, 500), car_color, -1)  # Car body
    cv2.rectangle(img, (450, 350), (830, 450), (50, 50, 50), -1)  # Windows
    
    # Draw a license plate
    plate_x, plate_y = 540, 400
    plate_width, plate_height = 200, 50
    
    # White plate background
    cv2.rectangle(img, 
                 (plate_x, plate_y), 
                 (plate_x + plate_width, plate_y + plate_height), 
                 (255, 255, 255), 
                 -1)
    
    # Black border
    cv2.rectangle(img, 
                 (plate_x, plate_y), 
                 (plate_x + plate_width, plate_y + plate_height), 
                 (0, 0, 0), 
                 2)
    
    # License plate text
    cv2.putText(img, 
               "ABC123", 
               (plate_x + 20, plate_y + 35), 
               cv2.FONT_HERSHEY_SIMPLEX, 
               1.2, 
               (0, 0, 0), 
               2)
    
    # Add some road markings
    cv2.line(img, (0, 600), (1280, 600), (255, 255, 255), 5)  # Road line
    
    return img

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test GPU-accelerated license plate detection")
    parser.add_argument("--image", help="Path to test image (optional)")
    args = parser.parse_args()
    
    asyncio.run(test_gpu_detection(args.image))