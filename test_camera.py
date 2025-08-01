#!/usr/bin/env python3
"""
Test camera connection and snapshot capture
"""
import sys
import time
import os
from ai_pipeline.camera_manager import CameraManager, CameraConfig
import cv2
import numpy as np

print("🎥 Testing Camera Connection...\n")

# Option 1: Test with mock camera (always works)
def test_mock_camera():
    print("Testing with mock camera...")
    
    # Create a mock frame generator
    class MockCameraStream:
        def __init__(self, config):
            self.config = config
            self.is_running = True
            self.last_frame = self.generate_mock_frame()
            self.last_frame_time = time.time()
            
        def generate_mock_frame(self):
            # Create a test pattern
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add gradient
            for i in range(480):
                frame[i, :, 0] = int(i * 255 / 480)  # Blue gradient
                frame[i, :, 1] = 100  # Green constant
            # Add text
            cv2.putText(frame, f"Mock Camera: {self.config.name}", 
                       (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, time.strftime("%Y-%m-%d %H:%M:%S"), 
                       (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1)
            return frame
            
        def get_snapshot(self):
            self.last_frame = self.generate_mock_frame()
            self.last_frame_time = time.time()
            return self.last_frame.copy()
            
        def is_healthy(self):
            return True
            
        def stop(self):
            self.is_running = False
    
    # Create mock camera
    config = CameraConfig(
        camera_id="mock_cam",
        name="Mock Test Camera",
        ip_address="0.0.0.0",
        username="mock",
        password="mock"
    )
    
    mock_camera = MockCameraStream(config)
    frame = mock_camera.get_snapshot()
    
    if frame is not None:
        cv2.imwrite("test_mock_snapshot.jpg", frame)
        print("✅ Mock camera working! Saved: test_mock_snapshot.jpg")
        return True
    else:
        print("❌ Mock camera failed")
        return False

# Option 2: Test with real camera
def test_real_camera():
    print("\nTesting with real camera...")
    print("NOTE: Update IP address, username, and password for your camera")
    
    # Configuration for real camera - UPDATE THESE VALUES
    config = CameraConfig(
        camera_id="test_cam",
        name="Test Camera",
        ip_address="10.0.0.181",  # ⚠️ UPDATE THIS
        username="admin",          # ⚠️ UPDATE THIS
        password="password",       # ⚠️ UPDATE THIS
        port=554,
        stream_path="/stream"
    )
    
    print(f"Attempting to connect to: {config.stream_url}")
    
    manager = CameraManager()
    success = manager.add_camera(config)
    
    if not success:
        print("❌ Failed to add camera to manager")
        return False
    
    # Wait for connection
    print("Waiting for camera connection (5 seconds)...")
    time.sleep(5)
    
    # Get camera and check health
    camera = manager.get_camera("test_cam")
    if not camera:
        print("❌ Camera not found in manager")
        manager.stop_all()
        return False
    
    if camera.is_healthy():
        print("✅ Camera is healthy")
        
        # Try to get a snapshot
        frame = camera.get_snapshot()
        if frame is not None:
            cv2.imwrite("test_real_snapshot.jpg", frame)
            print(f"✅ Real camera working! Saved: test_real_snapshot.jpg")
            print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
            manager.stop_all()
            return True
        else:
            print("❌ No frame received from camera")
    else:
        print("❌ Camera is not healthy")
        print("   Check:")
        print("   - Camera IP address is correct")
        print("   - Camera is powered on and connected to network")
        print("   - Username and password are correct")
        print("   - RTSP port (usually 554) is correct")
    
    manager.stop_all()
    return False

# Option 3: Test camera URL with OpenCV directly
def test_direct_opencv():
    print("\nTesting direct OpenCV connection...")
    
    # Test URL - UPDATE THESE VALUES
    rtsp_url = "rtsp://admin:Mekus_1987@10.0.0.181:554/h264Preview_01_main"
    
    print(f"Testing URL: {rtsp_url}")
    
    cap = cv2.VideoCapture(rtsp_url)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            cv2.imwrite("test_direct_snapshot.jpg", frame)
            print("✅ Direct OpenCV connection works! Saved: test_direct_snapshot.jpg")
            cap.release()
            return True
        else:
            print("❌ Could not read frame from camera")
    else:
        print("❌ Could not open camera stream")
        print("   Verify the RTSP URL is correct")
    
    cap.release()
    return False

# Run tests
if __name__ == "__main__":
    print("="*60)
    print("Camera Connection Test Suite")
    print("="*60)
    
    # Always test mock camera first
    mock_success = test_mock_camera()
    
    # Test real camera if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--real":
        print("\n" + "-"*60)
        real_success = test_real_camera()
        
        if not real_success:
            print("\n" + "-"*60)
            test_direct_opencv()
    else:
        print("\nTo test with a real camera, run:")
        print("  python test_camera.py --real")
        print("\nMake sure to update the camera IP, username, and password first!")
    
    print("\n" + "="*60)
    print("Test Summary:")
    print(f"Mock Camera: {'✅ PASS' if mock_success else '❌ FAIL'}")
    if len(sys.argv) > 1 and sys.argv[1] == "--real":
        print(f"Real Camera: {'✅ PASS' if 'real_success' in locals() and real_success else '❌ FAIL'}")
    
    # Check for output files
    print("\nGenerated files:")
    for filename in ["test_mock_snapshot.jpg", "test_real_snapshot.jpg", "test_direct_snapshot.jpg"]:
        if os.path.exists(filename):
            print(f"  ✅ {filename}")
    
    print("="*60)