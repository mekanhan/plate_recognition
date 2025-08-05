#!/usr/bin/env python3
"""
RTSP URL Finder - Tests common RTSP URL patterns for your camera
"""
import cv2
import sys
import time

# Camera details
IP = "10.0.0.181"
USERNAME = "admin"
PASSWORD = "Mekus_1987"
PORT = 554

# Common RTSP URL patterns for different camera manufacturers
RTSP_PATTERNS = [
    # Hikvision patterns
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264/ch1/main/av_stream",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264/ch1/sub/av_stream",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/Streaming/Channels/101",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/Streaming/Channels/102",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/cam/realmonitor?channel=1&subtype=0",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/cam/realmonitor?channel=1&subtype=1",
    
    # Dahua patterns
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/cam/realmonitor?channel=1&subtype=0",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/cam/realmonitor?channel=1&subtype=1",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/live",
    
    # Axis patterns
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/axis-media/media.amp",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/axis-media/media.amp?videocodec=h264",
    
    # Generic patterns
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/1",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/live.sdp",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/stream",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/video",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264_stream",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264Preview_01_main",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/h264Preview_01_sub",
    
    # ONVIF patterns
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/onvif1",
    f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}/onvif2",
    
    # Without authentication in URL (some cameras require it in headers)
    f"rtsp://{IP}:{PORT}/h264Preview_01_main",
    f"rtsp://{IP}:{PORT}/Streaming/Channels/101",
    f"rtsp://{IP}:{PORT}/cam/realmonitor?channel=1&subtype=0",
]

# Additional patterns with different ports
ALTERNATIVE_PORTS = [554, 8554, 7070, 8557]

def test_rtsp_url(url, timeout=5):
    """Test if RTSP URL works"""
    print(f"Testing: {url}")
    
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Wait a bit for connection
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ SUCCESS! Working URL found: {url}")
                print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
                
                # Save a snapshot
                cv2.imwrite("working_snapshot.jpg", frame)
                print(f"   Snapshot saved: working_snapshot.jpg")
                
                cap.release()
                return True
        time.sleep(0.1)
    
    cap.release()
    return False

def main():
    print("="*80)
    print("RTSP URL Finder for IP Camera")
    print("="*80)
    print(f"Camera IP: {IP}")
    print(f"Username: {USERNAME}")
    print(f"Default Port: {PORT}")
    print("="*80)
    print()
    
    working_urls = []
    
    # Test all patterns
    for i, url in enumerate(RTSP_PATTERNS, 1):
        print(f"\n[{i}/{len(RTSP_PATTERNS)}] ", end="")
        if test_rtsp_url(url, timeout=3):
            working_urls.append(url)
            print("\nFound working URL! Continue searching for alternatives...")
    
    # If no URLs work with default port, try alternative ports
    if not working_urls:
        print("\n\nNo URLs worked with port 554. Trying alternative ports...")
        for port in ALTERNATIVE_PORTS[1:]:  # Skip 554 as we already tried it
            print(f"\n--- Testing with port {port} ---")
            test_url = f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{port}/h264Preview_01_main"
            if test_rtsp_url(test_url, timeout=3):
                working_urls.append(test_url)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if working_urls:
        print(f"\n✅ Found {len(working_urls)} working URL(s):")
        for url in working_urls:
            print(f"   {url}")
        
        print("\n📝 Update your camera configuration with one of these URLs!")
        print("\nExample for api/main.py:")
        print(f"""
        CameraConfig(
            camera_id="entrance_cam",
            name="Entrance Camera",
            ip_address="{IP}",
            username="{USERNAME}",
            password="{PASSWORD}",
            port={PORT},
            stream_path="{working_urls[0].split(f'{IP}:{PORT}')[1]}"
        )
        """)
    else:
        print("\n❌ No working RTSP URLs found!")
        print("\nPossible issues:")
        print("1. Camera is not reachable at the IP address")
        print("2. Username/password is incorrect")
        print("3. Camera uses a non-standard RTSP path")
        print("4. RTSP might be disabled on the camera")
        print("\nSuggestions:")
        print("1. Check camera's web interface for RTSP settings")
        print("2. Look for camera model documentation")
        print("3. Try using ONVIF device manager to discover the stream URL")
        print("4. Check if camera requires special authentication method")
    
    print("="*80)

if __name__ == "__main__":
    main()