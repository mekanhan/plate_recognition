#!/usr/bin/env python3
"""
Test script to verify the troubleshooting fixes work properly.
This script tests database initialization, storage, and detection workflow.
"""

import asyncio
import os
import sys
import requests
import time

# Add the app directory to the path
sys.path.insert(0, '/mnt/c/Users/mekja/Documents/GitHub/plate_recognition')

async def test_database_initialization():
    """Test database schema creation"""
    print("Testing database initialization...")
    
    try:
        from app.database import init_database
        await init_database()
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

async def test_storage_service():
    """Test storage service functionality"""
    print("Testing storage service...")
    
    try:
        from app.services.storage_service import StorageService
        
        storage = StorageService()
        await storage.initialize()
        
        # Test adding a detection
        test_detection = {
            "detection_id": "test-123",
            "plate_text": "TEST123",
            "confidence": 0.95,
            "timestamp": time.time(),
            "box": [100, 100, 200, 150],
            "status": "active"
        }
        
        await storage.add_detections([test_detection])
        
        # Verify it was saved
        detections = await storage.get_detections()
        found = any(d.get("plate_text") == "TEST123" for d in detections)
        
        if found:
            print("✓ Storage service working - JSON and SQL storage successful")
            return True
        else:
            print("✗ Storage service failed - detection not found")
            return False
            
    except Exception as e:
        print(f"✗ Storage service test failed: {e}")
        return False

async def test_sql_repository():
    """Test SQL repository directly"""
    print("Testing SQL repository...")
    
    try:
        from app.repositories.sql_repository import SQLiteDetectionRepository
        from app.database import async_session
        
        repo = SQLiteDetectionRepository(async_session)
        await repo.initialize()
        
        # Test adding a detection
        test_detection = {
            "detection_id": "sql-test-456",
            "plate_text": "SQL456",
            "confidence": 0.88,
            "timestamp": time.time(),
            "box": [50, 50, 150, 100],
            "status": "active"
        }
        
        await repo.add_detections([test_detection])
        
        # Try to retrieve it
        detections = await repo.get_detections()
        found = any(d.get("plate_text") == "SQL456" for d in detections)
        
        if found:
            print("✓ SQL repository working correctly")
            return True
        else:
            print("✗ SQL repository failed - detection not found")
            return False
            
    except Exception as e:
        print(f"✗ SQL repository test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints if server is running"""
    print("Testing API endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8001/results/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ Health endpoint working - Status: {health_data.get('status')}")
            return True
        else:
            print(f"✗ Health endpoint failed - Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠ API endpoints not testable - Server not running: {e}")
        return None

async def main():
    """Run all tests"""
    print("=== License Plate Recognition Troubleshooting Test ===\n")
    
    results = []
    
    # Test database
    results.append(await test_database_initialization())
    print()
    
    # Test storage service  
    results.append(await test_storage_service())
    print()
    
    # Test SQL repository
    results.append(await test_sql_repository())
    print()
    
    # Test API endpoints (if server is running)
    api_result = test_api_endpoints()
    if api_result is not None:
        results.append(api_result)
    print()
    
    # Summary
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    total = len(results)
    
    print("=== Test Summary ===")
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The troubleshooting fixes are working correctly.")
    else:
        print(f"\n⚠ {failed} test(s) failed. Please check the error messages above.")
    
    return failed == 0

if __name__ == "__main__":
    asyncio.run(main())