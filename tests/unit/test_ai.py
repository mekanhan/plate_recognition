#!/usr/bin/env python3
"""
Test AI detection pipeline - vehicle detection and license plate OCR
"""
import sys
import os
import cv2
import numpy as np
import asyncio

# Add project root to path for local imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ai_pipeline.processors import LicensePlateDetector, ProcessingPipeline

print("🤖 Testing AI Detection Pipeline...\n")

# Check if YOLO models exist
def check_models():
    print("Checking for AI models...")
    
    model_paths = [
        "yolov8m.pt",
        "yolo11m_best.pt",
        "ai_pipeline/train/models/pretrained/yolo11m_best.pt"
    ]
    
    found_models = []
    for path in model_paths:
        if os.path.exists(path):
            print(f"✅ Found model: {path}")
            found_models.append(path)
        else:
            print(f"❌ Model not found: {path}")
    
    return found_models

# Create test images
def create_test_images():
    print("\nCreating test images...")
    
    # Test image 1: Simple synthetic image
    img1 = np.zeros((640, 480, 3), dtype=np.uint8)
    img1[:] = (100, 100, 100)  # Gray background
    
    # Add a rectangle that looks like a vehicle
    cv2.rectangle(img1, (100, 200), (380, 400), (50, 50, 150), -1)  # Dark blue "car"
    cv2.rectangle(img1, (150, 350), (330, 390), (200, 200, 200), -1)  # "License plate"
    cv2.putText(img1, "TEST123", (180, 375), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    cv2.imwrite("test_synthetic.jpg", img1)
    print("✅ Created test_synthetic.jpg")
    
    # Test image 2: Use snapshot if available
    snapshot_files = ["test_real_snapshot.jpg", "test_mock_snapshot.jpg", "test_snapshot.jpg"]
    snapshot_found = None
    
    for snapshot in snapshot_files:
        if os.path.exists(snapshot):
            snapshot_found = snapshot
            print(f"✅ Found existing snapshot: {snapshot}")
            break
    
    return ["test_synthetic.jpg", snapshot_found] if snapshot_found else ["test_synthetic.jpg"]

# Test vehicle detection
def test_vehicle_detection(detector, test_images):
    print("\nTesting vehicle detection...")
    
    for img_path in test_images:
        if not img_path:
            continue
            
        print(f"\nProcessing: {img_path}")
        img = cv2.imread(img_path)
        
        if img is None:
            print(f"❌ Could not load image: {img_path}")
            continue
        
        # Detect vehicles
        vehicles = detector.detect_vehicles(img)
        print(f"✅ Detected {len(vehicles)} vehicles")
        
        # Draw detection results
        result_img = img.copy()
        for i, vehicle in enumerate(vehicles):
            x1, y1, x2, y2 = vehicle['bbox']
            confidence = vehicle['confidence']
            vehicle_type = vehicle['class']
            
            # Draw bounding box
            cv2.rectangle(result_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add label
            label = f"{vehicle_type}: {confidence:.2f}"
            cv2.putText(result_img, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            print(f"  Vehicle {i+1}: {vehicle_type} (confidence: {confidence:.2f})")
        
        # Save result
        result_path = img_path.replace('.jpg', '_vehicles.jpg')
        cv2.imwrite(result_path, result_img)
        print(f"✅ Saved detection result: {result_path}")

# Test full pipeline
async def test_full_pipeline(test_images):
    print("\nTesting full processing pipeline...")
    
    detector = LicensePlateDetector()
    pipeline = ProcessingPipeline(detector)
    
    for img_path in test_images:
        if not img_path:
            continue
            
        print(f"\nProcessing with full pipeline: {img_path}")
        img = cv2.imread(img_path)
        
        if img is None:
            continue
        
        # Process frame
        detections = await pipeline.process_frame("test_camera", img)
        
        print(f"✅ Pipeline processed, found {len(detections)} license plates")
        
        for det in detections:
            print(f"  Plate: {det.plate_text} (confidence: {det.confidence:.2f})")
            print(f"  Vehicle: {det.vehicle_type}")
            print(f"  Detection ID: {det.detection_id}")
    
    # pipeline.cleanup()

# Test OCR capability
def test_ocr_capability():
    print("\nTesting OCR capability...")
    
    try:
        import easyocr
        reader = easyocr.Reader(['en'])
        
        # Create a simple text image
        test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255  # White background
        cv2.putText(test_img, "ABC123", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        cv2.imwrite("test_ocr.jpg", test_img)
        
        # Test OCR
        results = reader.readtext("test_ocr.jpg")
        
        if results:
            text = ''.join([r[1] for r in results])
            print(f"✅ OCR working! Detected text: {text}")
        else:
            print("❌ OCR did not detect any text")
            
    except Exception as e:
        print(f"❌ OCR test failed: {e}")

# Main test execution
if __name__ == "__main__":
    print("="*60)
    print("AI Detection Pipeline Test")
    print("="*60)
    
    # Check models
    found_models = check_models()
    
    if not found_models:
        print("\n⚠️  No YOLO models found!")
        print("Downloading yolov8m.pt...")
        from ultralytics import YOLO
        model = YOLO('yolov8m.pt')  # This will download if not present
        print("✅ Model downloaded")
    
    # Create test images
    test_images = create_test_images()
    
    # Initialize detector
    try:
        print("\nInitializing AI detector...")
        detector = LicensePlateDetector()
        print("✅ Detector initialized successfully")
        
        # Test vehicle detection
        test_vehicle_detection(detector, test_images)
        
        # Test OCR
        test_ocr_capability()
        
        # Test full pipeline
        print("\nRunning full pipeline test...")
        asyncio.run(test_full_pipeline(test_images))
        
    except Exception as e:
        print(f"❌ Error during AI testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("AI Pipeline Test Complete")
    print("Check generated images:")
    for img in ["test_synthetic_vehicles.jpg", "test_ocr.jpg"]:
        if os.path.exists(img):
            print(f"  ✅ {img}")
    
    # Check detection output folder
    if os.path.exists("detections"):
        frame_count = len(os.listdir("detections/frames") if os.path.exists("detections/frames") else [])
        plate_count = len(os.listdir("detections/plates") if os.path.exists("detections/plates") else [])
        print(f"\nDetection outputs:")
        print(f"  Frames saved: {frame_count}")
        print(f"  Plates saved: {plate_count}")
    
    print("="*60)