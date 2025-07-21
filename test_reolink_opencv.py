#!/usr/bin/env python3
"""Test Reolink RTSP streams with OpenCV directly"""
import cv2
import time
import sys
from urllib.parse import quote

# Camera details
IP = "10.0.0.181"
USERNAME = "admin"
PASSWORD = "Mekus_1987"
PORT = 554

# Comprehensive list of Reolink RTSP paths
REOLINK_PATHS = [
    # Standard Reolink paths
    "/h264Preview_01_main",
    "/h264Preview_01_sub", 
    "/Preview_01_main",
    "/Preview_01_sub",
    
    # Alternative formats
    "/bcs/channel0_main.bcs",
    "/bcs/channel0_sub.bcs",
    "/cam/realmonitor?channel=1&subtype=0",
    "/cam/realmonitor?channel=1&subtype=1",
    
    # Simple paths
    "/live/main",
    "/live/sub",
    "/live/ch00_0",
    "/live/ch00_1",
    "/channel1",
    "/stream1",
    "/stream2",
    
    # ONVIF standard paths
    "/onvif1",
    "/onvif2",
    "/MediaInput/h264",
    "/MediaInput/h264_sub",
]

def test_opencv_stream(url, timeout=15):
    """Test RTSP URL with OpenCV VideoCapture"""
    print(f"  Testing: {url.replace(PASSWORD, '***')}")
    
    cap = None
    try:
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            print("    ❌ Failed to open stream")
            return False
        
        print("    ✅ Stream opened successfully")
        
        # Try to read frames
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if ret and frame is not None:
                frame_count += 1
                if frame_count == 1:
                    print(f"    🎉 FIRST FRAME READ! Resolution: {frame.shape[1]}x{frame.shape[0]}")
                if frame_count >= 5:
                    print(f"    ✅ SUCCESS: Read {frame_count} frames")
                    return True
            time.sleep(0.1)
        
        if frame_count > 0:
            print(f"    ⚠️  Partial success: Read {frame_count} frames")
            return True
        else:
            print(f"    ❌ No frames received after {timeout}s")
            return False
            
    except Exception as e:
        print(f"    ❌ Exception: {e}")
        return False
    finally:
        if cap:
            cap.release()

def main():
    print(f"Testing Reolink camera at {IP} with OpenCV")
    print(f"Username: {USERNAME}")
    print(f"Password: {'*' * len(PASSWORD)}")
    print("-" * 80)
    
    # Test both original and URL-encoded password
    passwords = [
        (PASSWORD, "Original password"),
        (quote(PASSWORD, safe=''), "URL-encoded password")
    ]
    
    working_urls = []
    
    for password, desc in passwords:
        print(f"\n{'='*30} {desc} {'='*30}")
        
        for path in REOLINK_PATHS:
            url = f"rtsp://{USERNAME}:{password}@{IP}:{PORT}{path}"
            
            if test_opencv_stream(url):
                working_urls.append((url, path))
                print(f"    🎯 FOUND WORKING URL: {path}")
                
                # Test a few more frames to be sure
                print("    🔄 Extended test...")
                if test_opencv_stream(url, timeout=30):
                    print(f"    ✅ CONFIRMED: {path} works reliably")
                    break  # Found a working one, stop testing this password version
        
        if working_urls:
            break  # Found working URLs, no need to try encoded password
    
    print("\n" + "="*80)
    if working_urls:
        print(f"🎉 FOUND {len(working_urls)} WORKING URL(S):")
        for url, path in working_urls:
            print(f"  ✅ {path}")
        
        print(f"\n💡 RECOMMENDED RTSP PATH: {working_urls[0][1]}")
    else:
        print("❌ NO WORKING RTSP URLs found")
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Check if RTSP is enabled in camera web interface")
        print("2. Verify username and password are correct")
        print("3. Try different RTSP ports (8554, 10554)")
        print("4. Check camera manual for specific RTSP URL format")
        print("5. Test with VLC media player manually")

if __name__ == "__main__":
    main()