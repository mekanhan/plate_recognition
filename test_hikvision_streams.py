#!/usr/bin/env python3
"""
Test common Hikvision RTSP stream paths
"""
import cv2
import time

# Camera details
IP = "10.0.0.181"
USERNAME = "admin"
PASSWORD = "Mekus_1987"
PORT = 554

# Common Hikvision RTSP patterns
HIKVISION_PATTERNS = [
    # Most common Hikvision patterns
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/Streaming/Channels/101",  # Main stream channel 1
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/Streaming/Channels/102",  # Sub stream channel 1
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/Streaming/Channels/1",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/Streaming/Channels/2",
    
    # Older Hikvision formats
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264/ch1/main/av_stream",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264/ch1/sub/av_stream",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/MPEG-4/ch1/main/av_stream",
    
    # Alternative formats
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/cam/realmonitor?channel=1&subtype=0",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/cam/realmonitor?channel=1&subtype=1",
    
    # Your original path
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264Preview_01_main",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264Preview_01_sub",
]

def test_url(url):
    """Test RTSP URL"""
    print(f"\nTesting: {url}")
    
    # Try with TCP first
    tcp_url = url + "?tcp"
    cap = cv2.VideoCapture(tcp_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Quick timeout
    start = time.time()
    while time.time() - start < 3:
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ SUCCESS with TCP! Resolution: {frame.shape[1]}x{frame.shape[0]}")
                cv2.imwrite("test_success.jpg", frame)
                cap.release()
                return url
        time.sleep(0.1)
    
    cap.release()
    
    # Try without TCP
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    start = time.time()
    while time.time() - start < 3:
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ SUCCESS without TCP! Resolution: {frame.shape[1]}x{frame.shape[0]}")
                cv2.imwrite("test_success.jpg", frame)
                cap.release()
                return url
        time.sleep(0.1)
    
    cap.release()
    print("❌ Failed")
    return None

# Test all patterns
print("Testing common Hikvision RTSP patterns...")
print("="*60)

working_url = None
for url in HIKVISION_PATTERNS:
    result = test_url(url)
    if result:
        working_url = result
        break

if working_url:
    # Extract the stream path
    stream_path = working_url.split(f"{IP}:{PORT}")[1]
    print(f"\n✅ Found working URL!")
    print(f"Full URL: {working_url}")
    print(f"Stream path: {stream_path}")
    print(f"\nUpdate your api/main.py with:")
    print(f'stream_path="{stream_path}"')
else:
    print("\n❌ No working URLs found")
    print("\nThis camera might:")
    print("1. Use a different RTSP path")
    print("2. Have RTSP disabled")
    print("3. Require different authentication")
    print("\nCheck the camera's web interface for RTSP settings")