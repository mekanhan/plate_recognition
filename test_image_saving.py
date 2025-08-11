#!/usr/bin/env python3
"""
Test Image Saving Functionality
Force a detection with image saving to test the pipeline
"""
import asyncio
import cv2
import requests
import sys
import os

# Add project root to path
sys.path.insert(0, '/home/mekanhan/github/learning/plate_recognition')

from ai_features.vehicle.detection.pipeline import EnhancedProcessingPipeline
from ai_features.core.types import PlateInfo

async def test_forced_detection():
    """Force a detection with image saving"""
    print("🔍 Testing Image Saving Functionality")
    print("=" * 50)
    
    # Get snapshot from camera
    print("📸 Getting camera snapshot...")
    snapshot_url = "http://localhost:8001/api/cameras/camera_946701d3/snapshot"
    
    try:
        response = requests.get(snapshot_url, timeout=10)
        if response.status_code == 200:
            # Save snapshot to temp file
            temp_path = "/tmp/test_snapshot_save.jpg"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Load image with OpenCV
            frame = cv2.imread(temp_path)
            if frame is None:
                print("❌ Failed to load snapshot image")
                return
            
            print(f"✅ Loaded snapshot: {frame.shape}")
            
            # Initialize pipeline
            pipeline = EnhancedProcessingPipeline()
            
            # Create a fake plate detection to test image saving
            print("🧪 Creating fake plate detection to test image saving...")
            fake_plate = PlateInfo(
                text='TEXAS',
                confidence=0.5,
                ocr_confidence=0.8,
                bbox=[1800, 900, 2100, 1400],  # Approximate location based on logs
                plate_type='standard',
                region='TX'
            )
            
            # Manually call image saving function
            detection_id = "test_12345"
            frame_path, plate_path = pipeline._save_detection_images(
                "camera_946701d3", detection_id, frame,
                [1700, 800, 2200, 1500],  # Vehicle bbox
                fake_plate.bbox  # Plate bbox
            )
            
            print(f"🎯 Image Saving Results:")
            print(f"   Frame saved: {frame_path}")
            print(f"   Plate saved: {plate_path}")
            
            # Check if files exist
            if os.path.exists(frame_path):
                print(f"   ✅ Frame file exists: {os.path.getsize(frame_path)} bytes")
            else:
                print(f"   ❌ Frame file missing: {frame_path}")
            
            if plate_path and os.path.exists(plate_path):
                print(f"   ✅ Plate file exists: {os.path.getsize(plate_path)} bytes")
            else:
                print(f"   ❌ Plate file missing: {plate_path}")
                
        else:
            print(f"❌ Failed to get snapshot: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_forced_detection())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")