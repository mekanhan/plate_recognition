#!/usr/bin/env python3
"""Test MJPEG stream endpoint directly"""
import requests
import time

def test_mjpeg_stream():
    """Test the camera MJPEG stream endpoint"""
    camera_id = "87db1778-391d-4022-b4b6-941d4082abeb"
    stream_url = f"http://localhost:8002/api/cameras/{camera_id}/stream"
    
    print(f"Testing MJPEG stream: {stream_url}")
    
    try:
        response = requests.get(stream_url, stream=True, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            # Read first few bytes to see if we get image data
            data = b""
            for chunk in response.iter_content(chunk_size=1024):
                data += chunk
                if len(data) > 10000:  # Got some data
                    break
            
            print(f"Received {len(data)} bytes of data")
            
            # Look for JPEG markers
            if b'\xff\xd8' in data:  # JPEG start marker
                print("✅ JPEG data detected in stream!")
                return True
            else:
                print("❌ No JPEG data found in stream")
                print(f"First 100 bytes: {data[:100]}")
                return False
        else:
            print(f"❌ Stream request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing stream: {e}")
        return False

if __name__ == "__main__":
    success = test_mjpeg_stream()
    print(f"\nStream test {'PASSED' if success else 'FAILED'}")