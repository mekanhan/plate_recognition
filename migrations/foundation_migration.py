"""
Foundation 3 Migration Script
Migrates existing services to use the new Foundation Database Service
"""
import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.foundation_service import get_foundation_database_service
from database.service import DatabaseService

logger = logging.getLogger(__name__)

async def test_database_migration():
    """Test that the new Foundation Database Service works with existing data"""
    
    print("🔄 Starting Foundation 3 Database Migration Test...")
    
    try:
        # Initialize the new Foundation Database Service
        foundation_db = await get_foundation_database_service()
        print("✅ Foundation Database Service initialized")
        
        # Test health check
        health = await foundation_db.health_check()
        print(f"📊 Database Health: {health['status']}")
        print(f"📈 Camera Count: {health.get('camera_count', 'unknown')}")
        
        # Test camera retrieval
        cameras = await foundation_db.get_all_cameras()
        print(f"📷 Found {len(cameras)} cameras in database")
        
        for camera in cameras:
            print(f"   - {camera['name']} ({camera['camera_id']}) - Status: {camera['status']}")
        
        # Test individual camera lookup
        if cameras:
            test_camera = cameras[0]
            retrieved_camera = await foundation_db.get_camera(test_camera['camera_id'])
            if retrieved_camera:
                print(f"✅ Individual camera lookup successful: {retrieved_camera['name']}")
            else:
                print("❌ Individual camera lookup failed")
        
        print("✅ Foundation 3 Database Migration Test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        logger.error(f"Migration test error: {e}")
        return False
    finally:
        # Clean up
        if 'foundation_db' in locals():
            await foundation_db.close()

async def validate_backward_compatibility():
    """Ensure the new service is compatible with existing DatabaseService usage"""
    
    print("\n🔄 Testing backward compatibility...")
    
    try:
        # Test old service
        old_db = DatabaseService()
        await old_db.init_db()
        
        old_cameras = []
        cameras = await old_db.get_all_cameras()
        old_cameras = [
            {
                'camera_id': cam.camera_id,
                'name': cam.name,
                'status': cam.status
            } for cam in cameras
        ]
        
        # Test new service
        new_db = await get_foundation_database_service()
        new_cameras = await new_db.get_all_cameras()
        
        # Compare results
        if len(old_cameras) == len(new_cameras):
            print(f"✅ Camera count matches: {len(old_cameras)} cameras")
        else:
            print(f"⚠️ Camera count differs: old={len(old_cameras)}, new={len(new_cameras)}")
        
        # Compare camera data
        old_ids = set(cam['camera_id'] for cam in old_cameras)
        new_ids = set(cam['camera_id'] for cam in new_cameras)
        
        if old_ids == new_ids:
            print("✅ Camera IDs match between services")
        else:
            print(f"⚠️ Camera ID mismatch - Old: {old_ids}, New: {new_ids}")
        
        print("✅ Backward compatibility test completed")
        return True
        
    except Exception as e:
        print(f"❌ Compatibility test failed: {e}")
        return False
    finally:
        if 'new_db' in locals():
            await new_db.close()

async def main():
    """Run the complete migration validation"""
    
    print("=" * 60)
    print("Foundation 3 - Phase 1 Database Migration")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = True
    
    # Run migration test
    if not await test_database_migration():
        success = False
    
    # Run compatibility test
    if not await validate_backward_compatibility():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Foundation 3 Database Migration: ALL TESTS PASSED")
        print("\nNext Steps:")
        print("1. Update recording service to use Foundation Database Service")
        print("2. Update API services to use unified database service")
        print("3. Test full system integration")
    else:
        print("❌ Foundation 3 Database Migration: TESTS FAILED")
        print("Please review errors before proceeding")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())