#!/usr/bin/env python
"""
Script to test license plate detection and storage functionality.
This can be run directly to test if plate detection and storage is working correctly.
"""
import os
import sys
import asyncio
import argparse
import time
import cv2
import numpy as np
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.services.license_plate_recognition_service import LicensePlateRecognitionService

async def test_with_sample_image(image_path=None):
    """Test the detection and storage with a sample image."""
    print("\n=== License Plate Detection and Storage Test ===\n")
    
    # Create and initialize services
    print("Initializing storage service...")
    storage_service = StorageService()
    await storage_service.initialize()
    print(f"Storage service initialized. Data will be saved to: {storage_service.session_file}")
    
    print("Initializing license plate recognition service...")
    lpr_service = LicensePlateRecognitionService()
    await lpr_service.initialize()
    print("License plate recognition service initialized")

    # Create a detection service and link it to storage
    print("Initializing detection service...")
    detection_service = DetectionService()
    detection_service.storage_service = storage_service
    detection_service.license_plate_service = lpr_service
    await detection_service.initialize()
    print("Detection service initialized and linked to storage")

    # Load test image or create one
    if image_path and os.path.exists(image_path):
        print(f"Loading image from {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            print(f"Failed to load image from {image_path}. Using generated image instead.")
            image = create_test_image()
    else:
        print("No valid image path provided. Using generated test image.")
        image = create_test_image()
    
    # Detect license plates
    print("\nProcessing image for license plate detection...")
    display_frame, detections = await detection_service.process_frame(image)
    
    # Display results
    print(f"Detection complete. Found {len(detections)} license plates.")
    for i, detection in enumerate(detections):
        print(f"  Plate {i+1}: {detection.get('plate_text', 'Unknown')} "
              f"(Confidence: {detection.get('confidence', 0):.2f})")
    
    # Process each detection to trigger storage
    print("\nProcessing detections for storage...")
    for i, detection in enumerate(detections):
        detection_id = f"test-{int(time.time())}-{i}"
        print(f"  Processing detection {detection_id}: {detection.get('plate_text', 'Unknown')}")
        await detection_service.process_detection(detection_id, detection)
    
    # Wait for storage to complete
    print("\nWaiting for storage to complete...")
    await asyncio.sleep(2)
    
    # Check if data was saved
    if os.path.exists(storage_service.session_file):
        file_size = os.path.getsize(storage_service.session_file)
        print(f"Storage file exists: {storage_service.session_file} ({file_size} bytes)")
        
        # Check if there's actual data in the file
        import json
        try:
            with open(storage_service.session_file, 'r') as f:
                data = json.load(f)
                saved_count = len(data.get("detections", []))
                print(f"Storage file contains {saved_count} detections")
                
                if saved_count > 0:
                    print("\nStorage test PASSED! Detections were successfully saved.")
                else:
                    print("\nStorage test INCOMPLETE. File exists but no detections were saved.")
        except json.JSONDecodeError:
            print("\nStorage test FAILED. File exists but is not valid JSON.")
    else:
        print(f"\nStorage test FAILED. File not found: {storage_service.session_file}")
    
    # Clean up
    print("\nShutting down services...")
    await detection_service.shutdown()
    await storage_service.shutdown()
    print("Test complete!")
    
    # Optional: Display the annotated image
    if display_frame is not None:
        # Resize for display if needed
        height, width = display_frame.shape[:2]
        if width > 1200:
            scale = 1200 / width
            display_frame = cv2.resize(display_frame, None, fx=scale, fy=scale)
        
        cv2.imshow("License Plate Detection", display_frame)
        print("\nShowing annotated image. Press any key to close.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def create_test_image():
    """Create a test image with a license plate."""
    # Create blank image (gray background)
    img = np.ones((720, 1280, 3), dtype=np.uint8) * 200
    
    # Add a car-like shape
    cv2.rectangle(img, (440, 300), (840, 500), (120, 120, 120), -1)
    cv2.rectangle(img, (500, 350), (780, 450), (150, 150, 150), -1)
    
    # Add license plate
    plate_x1, plate_y1 = 550, 380
    plate_x2, plate_y2 = 730, 430
    
    # White plate background
    cv2.rectangle(img, (plate_x1, plate_y1), (plate_x2, plate_y2), (255, 255, 255), -1)
    # Black border
    cv2.rectangle(img, (plate_x1, plate_y1), (plate_x2, plate_y2), (0, 0, 0), 2)
    
    # Add license plate text
    cv2.putText(img, "ABC123", (plate_x1 + 20, plate_y1 + 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    return img

async def test_camera_detection():
    """Test detection from camera feed."""
    print("\n=== License Plate Detection from Camera Test ===\n")
    
    # Create and initialize services
    print("Initializing services...")
    storage_service = StorageService()
    await storage_service.initialize()
    
    camera_service = CameraService()
    await camera_service.initialize()
    
    detection_service = DetectionService()
    detection_service.storage_service = storage_service
    await detection_service.initialize(camera_service=camera_service)
    
    print("All services initialized")
    
    # Run detection loop
    print("\nStarting detection loop (press 'q' to quit)...")
    try:
        detection_count = 0
        start_time = time.time()
        
        while time.time() - start_time < 30:  # Run for 30 seconds
            # Get frame from camera
            frame, timestamp = await camera_service.get_frame()
            
            # Process frame
            display_frame, detections = await detection_service.process_frame(frame)
            
            # Process any detections for storage
            for detection in detections:
                detection_id = f"camera-{int(time.time())}-{detection_count}"
                await detection_service.process_detection(detection_id, detection)
                detection_count += 1
                print(f"Detected plate: {detection.get('plate_text', 'Unknown')} "
                      f"(Confidence: {detection.get('confidence', 0):.2f})")
            
            # Display the frame
            cv2.imshow("Camera Feed", display_frame)
            
            # Break if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Short delay
            await asyncio.sleep(0.1)
        
        print(f"\nDetection loop completed. Detected {detection_count} license plates.")
        
        # Check if data was saved
        if os.path.exists(storage_service.session_file):
            import json
            with open(storage_service.session_file, 'r') as f:
                data = json.load(f)
                saved_count = len(data.get("detections", []))
                print(f"Storage file contains {saved_count} detections")
        else:
            print(f"Storage file not found: {storage_service.session_file}")
    
    finally:
        # Clean up
        print("\nShutting down services...")
        await camera_service.shutdown()
        await detection_service.shutdown()
        await storage_service.shutdown()
        cv2.destroyAllWindows()
        print("Test complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test license plate detection and storage")
    parser.add_argument("--image", help="Path to test image (optional)")
    parser.add_argument("--camera", action="store_true", help="Test with camera feed")
    args = parser.parse_args()
    
    if args.camera:
        asyncio.run(test_camera_detection())
    else:
        asyncio.run(test_with_sample_image(args.image))