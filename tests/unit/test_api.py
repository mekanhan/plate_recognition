#!/usr/bin/env python3
"""
Test API endpoints without starting the full server
"""
import requests
import json
import time

print("🌐 Testing API Endpoints...\n")

API_BASE = "http://localhost:8001"  # Updated to correct port

def check_api_running():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def test_endpoints():
    """Test various API endpoints"""
    
    if not check_api_running():
        print("❌ API server is not running!")
        print("\nTo start the API server, run in another terminal:")
        print("  python -m api.main")
        print("\nThen run this test again.")
        return False
    
    print("✅ API server is running\n")
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Get cameras
    print("\n2. Testing cameras endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/cameras")
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ Found {len(cameras)} cameras:")
            for cam in cameras:
                print(f"   - {cam['name']} ({cam['id']}): {cam['status']}")
        else:
            print(f"❌ Cameras endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cameras endpoint error: {e}")
    
    # Test 3: Get snapshot (will return offline image if no camera)
    print("\n3. Testing snapshot endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/cameras/entrance_cam/snapshot")
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                print(f"✅ Snapshot endpoint working (returned {content_type})")
                # Save snapshot
                with open("test_api_snapshot.jpg", "wb") as f:
                    f.write(response.content)
                print("   Saved as: test_api_snapshot.jpg")
            else:
                print(f"❌ Unexpected content type: {content_type}")
        else:
            print(f"❌ Snapshot endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Snapshot endpoint error: {e}")
    
    # Test 4: Recent detections
    print("\n4. Testing recent detections endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/detections/recent", params={"limit": 5})
        if response.status_code == 200:
            detections = response.json()
            print(f"✅ Recent detections endpoint working ({len(detections)} detections)")
            for det in detections[:3]:  # Show first 3
                print(f"   - {det.get('plate_text', 'N/A')} at {det.get('detected_at', 'N/A')}")
        else:
            print(f"❌ Recent detections failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Recent detections error: {e}")
    
    # Test 5: Analytics overview
    print("\n5. Testing analytics endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/analytics/overview")
        if response.status_code == 200:
            analytics = response.json()
            print("✅ Analytics endpoint working:")
            print(f"   - Detections today: {analytics.get('total_detections_today', 0)}")
            print(f"   - Unique plates: {analytics.get('unique_plates_today', 0)}")
            print(f"   - Active cameras: {analytics.get('active_cameras', {}).get('active', 0)}")
        else:
            print(f"❌ Analytics endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Analytics endpoint error: {e}")
    
    # Test 6: VLC endpoint
    print("\n6. Testing VLC integration endpoint...")
    try:
        response = requests.post(f"{API_BASE}/api/cameras/entrance_cam/open-vlc")
        if response.status_code == 200:
            data = response.json()
            print("✅ VLC endpoint working:")
            print(f"   - RTSP URL: {data.get('rtsp_url', 'N/A')}")
            print(f"   - Instructions: {data.get('instructions', 'N/A')}")
        else:
            print(f"❌ VLC endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ VLC endpoint error: {e}")
    
    # Test 7: API documentation
    print("\n7. Checking API documentation...")
    print(f"   API docs available at: {API_BASE}/docs")
    print(f"   Alternative docs at: {API_BASE}/redoc")
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("API Endpoint Tests")
    print("="*60)
    
    success = test_endpoints()
    
    print("\n" + "="*60)
    if success:
        print("✅ API tests completed!")
        print("\nYou can:")
        print(f"1. View interactive API docs at: {API_BASE}/docs")
        print(f"2. Check the saved snapshot: test_api_snapshot.jpg")
        print("3. Monitor API logs in the terminal running the server")
    else:
        print("❌ API tests could not run - start the server first")
    print("="*60)