#!/usr/bin/env python3
"""
Manual Detection Test
Test the enhanced LPR pipeline with a camera snapshot
"""
import asyncio
import cv2
import requests
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, '/home/mekanhan/github/learning/plate_recognition')

from ai_features.vehicle.detection.pipeline import EnhancedProcessingPipeline

async def test_detection_on_snapshot():
    """Test detection on a camera snapshot"""
    print("🔍 Manual Detection Test")
    print("=" * 40)
    
    # Get snapshot from camera
    print("📸 Getting camera snapshot...")
    snapshot_url = "http://localhost:8001/api/cameras/camera_946701d3/snapshot"
    
    try:
        response = requests.get(snapshot_url, timeout=10)
        if response.status_code == 200:
            # Save snapshot to temp file
            temp_path = "/tmp/test_snapshot.jpg"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Load image with OpenCV
            frame = cv2.imread(temp_path)
            if frame is None:
                print("❌ Failed to load snapshot image")
                return
            
            print(f"✅ Loaded snapshot: {frame.shape}")
            
            # Initialize enhanced pipeline
            print("🧠 Initializing enhanced detection pipeline...")
            pipeline = EnhancedProcessingPipeline()
            
            # Process frame
            print("⚡ Processing frame for detections...")
            detections = await pipeline.process_frame("camera_946701d3", frame)
            
            print(f"🎯 Detection Results: {len(detections)} detections found")
            
            if detections:
                for i, detection in enumerate(detections):
                    print(f"   Detection {i+1}:")
                    print(f"     Plate Text: {detection.plate_text}")
                    print(f"     Confidence: {detection.confidence:.2f}")
                    print(f"     Vehicle Type: {detection.vehicle_type}")
                    print(f"     OCR Confidence: {detection.ocr_confidence:.2f}")
            else:
                print("   No detections found")
                
        else:
            print(f"❌ Failed to get snapshot: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_detection_on_snapshot())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")