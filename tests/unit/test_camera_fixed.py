#!/usr/bin/env python3
"""
Simple Camera Test Script with Working Configuration
Uses the diagnostic results to test the camera with correct settings
"""
import cv2
import os
import time

def test_camera_connection():
    """Test camera connection with known working configuration"""
    
    # Configuration from diagnostic results
    ip_address = "10.0.0.181"
    port = 554
    username = "admin"
    password = "Mekus_1987"
    stream_path = "/h264Preview_01_main"  # Working path found by diagnostics
    
    # Build RTSP URL
    rtsp_url = f"rtsp://{username}:{password}@{ip_address}:{port}{stream_path}"
    display_url = f"rtsp://{username}:****@{ip_address}:{port}{stream_path}"
    
    print(f"🎥 Testing Camera Connection")
    print(f"📍 URL: {display_url}")
    print(f"⏱️  Timeout: 10 seconds")
    print("-" * 50)
    
    try:
        # Set environment for better RTSP handling
        os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|timeout;10000000'
        
        print("🔄 Connecting to camera...")
        cap = cv2.VideoCapture(rtsp_url)
        
        # Set timeout properties
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10 seconds
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)  # 10 seconds
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            print("❌ Failed to open camera stream")
            return False
        
        print("✅ Camera stream opened successfully")
        
        # Try to read frames
        print("📸 Reading test frames...")
        success_count = 0
        for i in range(5):
            ret, frame = cap.read()
            if ret and frame is not None:
                success_count += 1
                height, width = frame.shape[:2]
                print(f"   Frame {i+1}: {width}x{height} ✅")
            else:
                print(f"   Frame {i+1}: Failed ❌")
            
            time.sleep(0.5)  # Small delay between frames
        
        # Get stream properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        cap.release()
        
        print("-" * 50)
        print(f"📊 Stream Properties:")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   Successful frames: {success_count}/5")
        
        if success_count >= 3:
            print("✅ Camera test PASSED")
            return True
        else:
            print("❌ Camera test FAILED - too many frame read failures")
            return False
            
    except Exception as e:
        print(f"❌ Camera test error: {e}")
        return False
    finally:
        if 'OPENCV_FFMPEG_CAPTURE_OPTIONS' in os.environ:
            del os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS']

def main():
    print("🎬 Camera Connection Test")
    print("=" * 50)
    
    success = test_camera_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test completed successfully!")
        print("💡 The camera is working with the correct RTSP path.")
        print("📝 Use '/h264Preview_01_main' as the stream path in your configuration.")
    else:
        print("💥 Test failed!")
        print("🔧 Suggestions:")
        print("   1. Verify camera credentials")
        print("   2. Check camera is powered on and network accessible")
        print("   3. Try alternative stream paths:")
        print("      - /Preview_01_main")
        print("      - /h264Preview_01_sub (lower quality)")
        print("      - / (root path)")

if __name__ == "__main__":
    main()