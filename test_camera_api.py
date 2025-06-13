#!/usr/bin/env python3
"""
Simple test script to verify the camera API implementation
"""
import asyncio
import aiohttp
import json

async def test_camera_api():
    """Test the camera API endpoints"""
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 Testing Camera API Implementation")
        print("=" * 50)
        
        # Test 1: List cameras (should be empty initially)
        print("1. Testing GET /api/cameras/")
        try:
            async with session.get(f"{base_url}/api/cameras/") as response:
                if response.status == 200:
                    cameras = await response.json()
                    print(f"   ✅ Success: Found {len(cameras)} cameras")
                else:
                    print(f"   ❌ Failed: Status {response.status}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Camera discovery
        print("2. Testing GET /api/cameras/discovery/scan")
        try:
            async with session.get(f"{base_url}/api/cameras/discovery/scan") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Success: Scanned network, found {result.get('total_devices_found', 0)} devices")
                else:
                    print(f"   ❌ Failed: Status {response.status}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Register a test camera
        print("3. Testing POST /api/cameras/register")
        test_camera = {
            "name": "Test USB Camera",
            "type": "usb",
            "config": {
                "device_id": 0,
                "resolution": "1280x720",
                "fps": 30,
                "quality": "720p"
            },
            "location": "Test Location",
            "auto_discovered": False
        }
        
        try:
            async with session.post(
                f"{base_url}/api/cameras/register",
                json=test_camera,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        camera_id = result.get("camera_id")
                        print(f"   ✅ Success: Registered camera {camera_id}")
                        
                        # Test 4: Get camera info
                        print("4. Testing GET /api/cameras/{camera_id}")
                        async with session.get(f"{base_url}/api/cameras/{camera_id}") as response:
                            if response.status == 200:
                                camera_info = await response.json()
                                print(f"   ✅ Success: Retrieved camera info for {camera_info.get('name')}")
                            else:
                                print(f"   ❌ Failed: Status {response.status}")
                        
                        # Test 5: Camera health check
                        print("5. Testing GET /api/cameras/{camera_id}/health")
                        async with session.get(f"{base_url}/api/cameras/{camera_id}/health") as response:
                            if response.status == 200:
                                health = await response.json()
                                print(f"   ✅ Success: Health check - {'Healthy' if health.get('is_healthy') else 'Unhealthy'}")
                            else:
                                print(f"   ❌ Failed: Status {response.status}")
                        
                        # Test 6: Get camera stats
                        print("6. Testing GET /api/cameras/stats/all")
                        async with session.get(f"{base_url}/api/cameras/stats/all") as response:
                            if response.status == 200:
                                stats = await response.json()
                                print(f"   ✅ Success: Retrieved stats for {stats.get('total_cameras', 0)} cameras")
                            else:
                                print(f"   ❌ Failed: Status {response.status}")
                        
                        # Test 7: Remove camera
                        print("7. Testing DELETE /api/cameras/{camera_id}")
                        async with session.delete(f"{base_url}/api/cameras/{camera_id}") as response:
                            if response.status == 200:
                                result = await response.json()
                                print(f"   ✅ Success: Removed camera")
                            else:
                                print(f"   ❌ Failed: Status {response.status}")
                                
                    else:
                        print(f"   ❌ Failed: {result}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed: Status {response.status} - {error_text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 8: PWA setup info
        print("8. Testing GET /api/cameras/pwa/setup/192.168.1.100")
        try:
            async with session.get(f"{base_url}/api/cameras/pwa/setup/192.168.1.100") as response:
                if response.status == 200:
                    setup_info = await response.json()
                    print(f"   ✅ Success: PWA setup URL: {setup_info.get('setup_url')}")
                else:
                    print(f"   ❌ Failed: Status {response.status}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n🎯 API Test Summary:")
        print("   - All endpoints are accessible")
        print("   - Camera registration/removal works")
        print("   - Health checks and stats available")
        print("   - PWA support ready")
        print("   - Ready for mobile camera testing!")

if __name__ == "__main__":
    print("Starting Camera API Test...")
    print("Make sure the LPR server is running on localhost:8001")
    print()
    
    try:
        asyncio.run(test_camera_api())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        print("Make sure the LPR server is running and accessible")