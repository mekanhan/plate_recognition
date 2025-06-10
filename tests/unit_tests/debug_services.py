#!/usr/bin/env python3
"""
Debug script to check service connections and storage functionality
"""
import asyncio
import sys
import os
import time

# Add the app directory to the path
sys.path.insert(0, '/mnt/c/Users/mekja/Documents/GitHub/plate_recognition')

async def test_storage_service():
    """Test if storage service can save data"""
    print("🔧 Testing Storage Service")
    print("=" * 40)
    
    try:
        from app.services.storage_service import StorageService
        
        # Initialize storage service
        storage_service = StorageService()
        await storage_service.initialize(
            license_plates_dir="data/license_plates",
            enhanced_plates_dir="data/enhanced_plates"
        )
        
        print("✅ Storage service initialized")
        
        # Create a test detection
        test_detection = {
            "detection_id": "test-detection-123",
            "timestamp": time.time(),
            "plate_text": "TEST123",
            "raw_text": "TEST 123",
            "confidence": 0.85,
            "state": "TX",
            "box": [100, 100, 200, 150],
            "frame_id": 1,
            "tracking_id": "trk-test-123",
            "status": "active",
            "processed_at": time.time(),
            "processed_by": "debug_script"
        }
        
        # Add detection to storage
        await storage_service.add_detections([test_detection])
        print("✅ Test detection added to storage")
        
        # Force save
        await storage_service._save_data(force=True)
        print("✅ Forced data save completed")
        
        # Check if files exist
        session_file = storage_service.session_file
        if os.path.exists(session_file):
            file_size = os.path.getsize(session_file)
            print(f"✅ Session file exists: {session_file} ({file_size} bytes)")
        else:
            print(f"❌ Session file missing: {session_file}")
        
        await storage_service.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Storage service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_video_service():
    """Test if video service can initialize"""
    print("\n🎥 Testing Video Service")
    print("=" * 40)
    
    try:
        from app.services.video_service import VideoRecordingService
        from app.repositories.sql_repository import SQLiteDetectionRepository, SQLiteVideoRepository
        from app.database import async_session
        
        # Initialize repositories
        detection_repo = SQLiteDetectionRepository(async_session)
        video_repo = SQLiteVideoRepository(async_session)
        
        # Initialize video service
        video_service = VideoRecordingService(detection_repo, video_repo)
        await video_service.initialize()
        
        print("✅ Video service initialized")
        print(f"📁 Video directory: {video_service.base_video_dir}")
        
        if os.path.exists(video_service.base_video_dir):
            print("✅ Video directory exists")
        else:
            print("❌ Video directory missing")
            
        await video_service.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Video service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_detection_service_connections():
    """Test if detection service has proper connections"""
    print("\n🔗 Testing Detection Service Connections")
    print("=" * 50)
    
    try:
        from app.services.detection_service import DetectionService
        from app.services.storage_service import StorageService
        from app.services.video_service import VideoRecordingService
        from app.repositories.sql_repository import SQLiteDetectionRepository, SQLiteVideoRepository
        from app.database import async_session
        
        # Initialize services
        detection_service = DetectionService()
        storage_service = StorageService()
        
        # Initialize repositories for video service
        detection_repo = SQLiteDetectionRepository(async_session)
        video_repo = SQLiteVideoRepository(async_session)
        video_service = VideoRecordingService(detection_repo, video_repo)
        
        # Initialize storage
        await storage_service.initialize()
        print("✅ Storage service initialized")
        
        # Initialize video service
        await video_service.initialize()
        print("✅ Video service initialized")
        
        # Connect services
        detection_service.storage_service = storage_service
        detection_service.video_recording_service = video_service
        
        # Initialize detection service
        await detection_service.initialize()
        print("✅ Detection service initialized")
        
        # Check connections
        if hasattr(detection_service, 'storage_service') and detection_service.storage_service:
            print("✅ Detection service connected to storage service")
        else:
            print("❌ Detection service NOT connected to storage service")
            
        if hasattr(detection_service, 'video_recording_service') and detection_service.video_recording_service:
            print("✅ Detection service connected to video recording service")
        else:
            print("❌ Detection service NOT connected to video recording service")
        
        # Cleanup
        await detection_service.shutdown()
        await storage_service.shutdown()
        await video_service.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ Service connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all diagnostic tests"""
    print("🚀 Service Diagnostic Tests")
    print("=" * 60)
    
    results = []
    
    # Test storage service
    result1 = await test_storage_service()
    results.append(result1)
    
    # Test video service
    result2 = await test_video_service()
    results.append(result2)
    
    # Test service connections
    result3 = await test_detection_service_connections()
    results.append(result3)
    
    # Summary
    passed = sum(1 for r in results if r is True)
    total = len(results)
    
    print(f"\n📋 Diagnostic Summary")
    print("=" * 30)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n🎉 All diagnostic tests passed!")
        print("Services should be working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        print("Check the error messages above for troubleshooting.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())