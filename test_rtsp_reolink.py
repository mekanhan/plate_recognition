#!/usr/bin/env python3
"""Quick test script for Reolink RTSP paths"""
import asyncio
import subprocess
import time
from urllib.parse import quote

# Your camera details
IP = "10.0.0.181"
USERNAME = "admin"
PASSWORD = "Mekus_1987"
PORT = 554

# Common Reolink RTSP paths to test
REOLINK_PATHS = [
    "/h264Preview_01_main",
    "/h264Preview_01_sub", 
    "/Preview_01_main",
    "/Preview_01_sub",
    "/cam/realmonitor?channel=1&subtype=0",
    "/cam/realmonitor?channel=1&subtype=1",
    "/live/main",
    "/live/sub",
    "/channel1",
    "/Streaming/Channels/101/",
    "/stream1",
    "/stream2"
]

def test_rtsp_url(url, timeout=10):
    """Test RTSP URL with ffprobe"""
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height', 
        '-of', 'csv=p=0', url
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def main():
    print(f"Testing Reolink camera at {IP}")
    print(f"Username: {USERNAME}")
    print(f"Password: {'*' * len(PASSWORD)} (has underscore: {('_' in PASSWORD)})")
    print("-" * 60)
    
    # Test both original and URL-encoded password
    passwords = [PASSWORD, quote(PASSWORD, safe='')]
    
    for password_version, password in enumerate(passwords):
        print(f"\n{'='*20} Password Version {password_version + 1} {'='*20}")
        if password_version == 0:
            print("Testing with original password")
        else:
            print(f"Testing with URL-encoded password: {password}")
            
        working_urls = []
        
        for path in REOLINK_PATHS:
            url = f"rtsp://{USERNAME}:{password}@{IP}:{PORT}{path}"
            print(f"Testing: {url.replace(password, '***')}")
            
            success, output, error = test_rtsp_url(url, timeout=15)
            
            if success:
                print(f"  ✅ SUCCESS: {output}")
                working_urls.append(url)
            else:
                print(f"  ❌ FAILED: {error}")
        
        if working_urls:
            print(f"\n🎉 Found {len(working_urls)} working URLs:")
            for url in working_urls:
                print(f"  - {url.replace(password, '***')}")
            break
    
    if not working_urls:
        print(f"\n❌ No working RTSP URLs found")
        print("\nTroubleshooting suggestions:")
        print("1. Verify RTSP is enabled in camera settings")
        print("2. Check if camera uses non-standard RTSP port")
        print("3. Try different authentication methods")
        print("4. Check camera manual for correct RTSP URL format")

if __name__ == "__main__":
    main()