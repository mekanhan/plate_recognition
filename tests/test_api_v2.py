# test_api.py (using urllib instead of requests)
import urllib.request
import urllib.error
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:8001"

def print_response(response, title):
    print(f"\n--- {title} ---")
    print(f"Status: {response.status}")
    try:
        data = json.loads(response.read().decode('utf-8'))
        print(json.dumps(data, indent=2))
        return data
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response: {response.read().decode('utf-8')[:200]}")
        return None

# Test video segments endpoint
print("Testing GET /v2/video/segments")
try:
    with urllib.request.urlopen(f"{BASE_URL}/v2/video/segments") as response:
        print_response(response, "Video Segments")
except urllib.error.URLError as e:
    print(f"Error: {e}")

# Test video stats endpoint
print("\nTesting GET /v2/video/stats")
try:
    with urllib.request.urlopen(f"{BASE_URL}/v2/video/stats") as response:
        print_response(response, "Video Stats")
except urllib.error.URLError as e:
    print(f"Error: {e}")

# Test latest detections endpoint
print("\nTesting GET /v2/detection/latest")
try:
    with urllib.request.urlopen(f"{BASE_URL}/v2/detection/latest") as response:
        print_response(response, "Latest Detections")
except urllib.error.URLError as e:
    print(f"Error: {e}")

# Test detect from camera endpoint
print("\nTesting POST /v2/detection/detect-from-camera")
try:
    req = urllib.request.Request(f"{BASE_URL}/v2/detection/detect-from-camera", method="POST")
    with urllib.request.urlopen(req) as response:
        detection = print_response(response, "Detect From Camera")
        
        # Test videos by detection endpoint if we got a valid detection
        if detection and 'detection_id' in detection:
            detection_id = detection['detection_id']
            print(f"\nTesting GET /v2/video/by-detection/{detection_id}")
            try:
                with urllib.request.urlopen(f"{BASE_URL}/v2/video/by-detection/{detection_id}") as resp:
                    print_response(resp, f"Videos for Detection {detection_id}")
            except urllib.error.URLError as e:
                print(f"Error: {e}")
except urllib.error.URLError as e:
    print(f"Error: {e}")

print("\nAPI Testing Complete")