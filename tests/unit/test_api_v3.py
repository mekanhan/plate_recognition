#!/usr/bin/env python3
"""
Test suite for API v3 endpoints
Tests the consolidated v3 API namespace we implemented
"""
import requests
import json
import sys
from typing import Dict, List

# API Configuration
API_BASE = "http://localhost:8001"
TIMEOUT = 5

class V3APITester:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "endpoint_results": {}
        }
    
    def check_api_running(self) -> bool:
        """Check if API server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
            return response.status_code == 200
        except:
            return False
    
    def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                     data: Dict = None, description: str = "") -> bool:
        """Test a single endpoint"""
        full_url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(full_url, timeout=TIMEOUT)
            elif method.upper() == "POST":
                response = requests.post(full_url, json=data, timeout=TIMEOUT)
            elif method.upper() == "PUT":
                response = requests.put(full_url, json=data, timeout=TIMEOUT)
            elif method.upper() == "DELETE":
                response = requests.delete(full_url, timeout=TIMEOUT)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            result = {
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "description": description,
                "response_size": len(response.content) if response.content else 0
            }
            
            # Try to parse JSON response for additional info
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    json_data = response.json()
                    if isinstance(json_data, list):
                        result["response_items"] = len(json_data)
                    elif isinstance(json_data, dict):
                        result["response_keys"] = list(json_data.keys())
                        # Check for v3 API indicators
                        if "api_version" in json_data and json_data["api_version"] == "v3":
                            result["is_v3_response"] = True
            except:
                pass
            
            self.results["endpoint_results"][endpoint] = result
            
            if success:
                self.results["passed"] += 1
                print(f"✅ {method} {endpoint} - {description}")
                if result.get("response_items"):
                    print(f"   → Returned {result['response_items']} items")
                if result.get("is_v3_response"):
                    print(f"   → ✨ Confirmed v3 API response")
            else:
                self.results["failed"] += 1
                error_msg = f"{method} {endpoint} returned {response.status_code}, expected {expected_status}"
                self.results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                
                # Show response content for debugging
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        json_data = response.json()
                        if "detail" in json_data:
                            print(f"   → Error: {json_data['detail']}")
                except:
                    pass
            
            return success
            
        except Exception as e:
            self.results["failed"] += 1
            error_msg = f"{method} {endpoint} - Exception: {str(e)}"
            self.results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def test_v3_endpoints(self):
        """Test all v3 API endpoints"""
        
        print(f"🔍 Testing v3 API at {self.base_url}/api/v3")
        
        if not self.check_api_running():
            print("❌ API server is not running on port 8001!")
            print("Start with: python3 bin/start_lpr.py")
            return False
        
        print("✅ API server is running\\n")
        
        # V3 System Endpoints
        print("🏥 API v3 - SYSTEM ENDPOINTS")
        print("-" * 40)
        self.test_endpoint("GET", "/api/v3/system/health", 200, description="v3 System health")
        self.test_endpoint("GET", "/api/v3/system/features", 200, description="v3 System features")
        print()
        
        # V3 Camera Endpoints
        print("📷 API v3 - CAMERA ENDPOINTS")
        print("-" * 40)
        self.test_endpoint("GET", "/api/v3/cameras", 200, description="v3 Get all cameras")
        
        # Test specific camera (use actual camera ID from the system)
        test_camera_id = "camera_a171d280fdc7"  # Current camera ID from the system
        self.test_endpoint("GET", f"/api/v3/cameras/{test_camera_id}", 200, description="v3 Get specific camera")
        self.test_endpoint("GET", "/api/v3/cameras/health/summary", 200, description="v3 Camera health summary")
        
        # Test with non-existent camera ID
        fake_camera_id = "fake_camera_123"
        self.test_endpoint("GET", f"/api/v3/cameras/{fake_camera_id}", 404, description="v3 Get non-existent camera (404 expected)")
        print()
        
        # V3 Detection Endpoints
        print("🎯 API v3 - DETECTION ENDPOINTS")
        print("-" * 40)
        self.test_endpoint("GET", "/api/v3/detections/recent", 200, description="v3 Recent detections")
        self.test_endpoint("GET", "/api/v3/detections/search", 200, description="v3 Search detections")
        
        # Test detection search with parameters
        self.test_endpoint("GET", "/api/v3/detections/search?limit=10", 200, description="v3 Search with limit")
        self.test_endpoint("GET", f"/api/v3/detections/search?camera_id={test_camera_id}", 200, description="v3 Search by camera")
        self.test_endpoint("GET", "/api/v3/detections/recent?limit=5", 200, description="v3 Recent with limit")
        print()
        
        return True
    
    def test_backward_compatibility(self):
        """Test that legacy endpoints still work alongside v3"""
        print("🔄 BACKWARD COMPATIBILITY - LEGACY ENDPOINTS")
        print("-" * 40)
        
        # Test that original endpoints still work
        self.test_endpoint("GET", "/api/cameras", 200, description="Legacy cameras endpoint")
        self.test_endpoint("GET", "/api/detections/recent", 200, description="Legacy detections endpoint")
        self.test_endpoint("GET", "/health", 200, description="Legacy health endpoint")
        print()
    
    def compare_v3_vs_legacy(self):
        """Compare v3 responses with legacy endpoints"""
        print("⚖️  V3 vs LEGACY COMPARISON")
        print("-" * 40)
        
        try:
            # Compare cameras endpoint
            legacy_cameras = requests.get(f"{self.base_url}/api/cameras", timeout=TIMEOUT).json()
            v3_cameras = requests.get(f"{self.base_url}/api/v3/cameras", timeout=TIMEOUT).json()
            
            if len(legacy_cameras) == len(v3_cameras):
                print("✅ v3 cameras endpoint returns same count as legacy")
            else:
                print(f"⚠️  v3 cameras ({len(v3_cameras)}) != legacy ({len(legacy_cameras)})")
            
            # Compare detections endpoint
            legacy_detections = requests.get(f"{self.base_url}/api/detections/recent?limit=5", timeout=TIMEOUT).json()
            v3_detections = requests.get(f"{self.base_url}/api/v3/detections/recent?limit=5", timeout=TIMEOUT).json()
            
            if len(legacy_detections) == len(v3_detections):
                print("✅ v3 detections endpoint returns same count as legacy")
            else:
                print(f"⚠️  v3 detections ({len(v3_detections)}) != legacy ({len(legacy_detections)})")
                
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
        print()
    
    def print_summary(self):
        """Print test results summary"""
        total_tests = self.results["passed"] + self.results["failed"]
        pass_rate = (self.results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print("=" * 60)
        print("📊 V3 API TEST RESULTS")
        print("=" * 60)
        print(f"Total v3 endpoints tested: {total_tests}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Pass rate: {pass_rate:.1f}%")
        
        if self.results["errors"]:
            print("\\n❌ FAILED TESTS:")
            for error in self.results["errors"]:
                print(f"   - {error}")
        
        print("\\n🎯 V3 API ENDPOINTS TESTED:")
        print("   - System: /api/v3/system/*")
        print("   - Cameras: /api/v3/cameras/*")
        print("   - Detections: /api/v3/detections/*")
        
        print("\\n✨ V3 API BENEFITS:")
        print("   - Clean namespace under /api/v3/")
        print("   - Backward compatibility maintained")
        print("   - Consolidated endpoint structure")
        print("   - Database-driven responses")
        print("=" * 60)

def main():
    """Main test execution"""
    print("=" * 60)
    print("🚀 API v3 TESTING SUITE")
    print("=" * 60)
    
    tester = V3APITester()
    
    if tester.test_v3_endpoints():
        # Test backward compatibility
        tester.test_backward_compatibility()
        
        # Compare responses
        tester.compare_v3_vs_legacy()
        
        # Print summary
        tester.print_summary()
        
        return tester.results["failed"] == 0
    else:
        print("\\n❌ Could not run v3 tests - API server not available")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\\n{'✅ All v3 tests passed!' if success else '❌ Some v3 tests failed!'}")
    sys.exit(0 if success else 1)