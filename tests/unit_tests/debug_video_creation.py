#!/usr/bin/env python3
import cv2
import numpy as np
import os
import time

# Test basic video creation
def test_opencv_video():
    video_path = f"/mnt/c/Users/mekja/Documents/GitHub/plate_recognition/data/videos/2025-06-10/debug_test_{int(time.time())}.mp4"
    print(f"Testing video creation at: {video_path}")
    
    # Create a simple video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 15.0, (640, 480))
    
    if not out.isOpened():
        print("❌ VideoWriter failed to open")
        return False
    
    print("✅ VideoWriter opened successfully")
    
    # Create 30 frames (2 seconds at 15fps)
    for i in range(30):
        # Create a simple frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (50, 50, 100)  # Dark blue background
        
        # Add text
        cv2.putText(frame, f"Frame {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    
    # Check if file was created
    if os.path.exists(video_path):
        file_size = os.path.getsize(video_path)
        print(f"✅ Video created: {video_path}")
        print(f"📏 File size: {file_size} bytes")
        return True
    else:
        print("❌ Video file was not created")
        return False

if __name__ == "__main__":
    print("🎥 Testing OpenCV Video Creation")
    print("=" * 40)
    success = test_opencv_video()
    print("=" * 40)
    if success:
        print("✅ OpenCV video creation works!")
    else:
        print("❌ OpenCV video creation failed!")