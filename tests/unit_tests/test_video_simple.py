#!/usr/bin/env python3
import cv2
import numpy as np
import os
import time

# Test with relative path
def test_relative_path():
    # Use relative path instead of absolute
    video_path = f"data/videos/2025-06-10/simple_test_{int(time.time())}.mp4"
    print(f"Testing video creation at: {video_path}")
    
    # Ensure directory exists
    os.makedirs("data/videos/2025-06-10", exist_ok=True)
    
    # Create a simple video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 15.0, (640, 480))
    
    if not out.isOpened():
        print("❌ VideoWriter failed to open")
        return False
    
    print("✅ VideoWriter opened successfully")
    
    # Create 15 frames (1 second at 15fps)
    for i in range(15):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (50, 100, 50)  # Dark green background
        cv2.putText(frame, f"Test Frame {i}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        out.write(frame)
        print(f"  Wrote frame {i}")
    
    # Explicitly release and flush
    out.release()
    cv2.destroyAllWindows()
    
    # Force filesystem sync
    import subprocess
    try:
        subprocess.run(['sync'], check=False)
    except:
        pass
    
    # Wait a moment for filesystem sync
    time.sleep(1)
    
    # Check if file exists
    if os.path.exists(video_path):
        file_size = os.path.getsize(video_path)
        print(f"✅ Video created: {video_path}")
        print(f"📏 File size: {file_size} bytes")
        
        # Also try to open it with OpenCV to verify
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"📊 Video verification: {frame_count} frames at {fps} fps")
            cap.release()
            return True
        else:
            print("⚠️ Video file created but cannot be opened")
            return False
    else:
        print("❌ Video file was not created")
        return False

if __name__ == "__main__":
    print("🎥 Testing Video Creation with Relative Path")
    print("=" * 50)
    success = test_relative_path()
    print("=" * 50)
    if success:
        print("✅ Video creation works!")
    else:
        print("❌ Video creation failed!")