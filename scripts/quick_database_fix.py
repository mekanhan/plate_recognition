#!/usr/bin/env python3
"""
Quick Database Fix - Create proper schema matching SQLAlchemy models
"""
import os
import sys
import asyncio
import logging

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_proper_database():
    """Create database with proper schema using SQLAlchemy models"""
    logger.info("🏗️ Creating database with proper SQLAlchemy schema...")
    
    try:
        from database.service import DatabaseService
        from database.models import Base
        
        # Initialize database service
        db_service = DatabaseService()
        
        # Create all tables using SQLAlchemy models
        await db_service.create_tables()
        
        logger.info("✅ Database created with proper schema")
        
        # Add test data
        logger.info("📝 Adding test data...")
        
        # Add test camera
        camera_data = {
            "camera_id": "test_cam_001",
            "name": "Test Camera 1",
            "ip_address": "192.168.1.100",
            "port": 80,
            "connection_type": "http",
            "stream_path": "/video",
            "status": "active"
        }
        
        camera_id = await db_service.add_camera(camera_data)
        logger.info(f"✅ Added test camera: {camera_id}")
        
        # Test the connection
        cameras = await db_service.get_all_cameras()
        detections = await db_service.get_recent_detections(5)
        
        logger.info(f"📊 Database verification:")
        logger.info(f"   - Cameras: {len(cameras)}")
        logger.info(f"   - Detections: {len(detections)}")
        
        await db_service.close()
        
        logger.info("🎉 Database fix completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database fix failed: {e}")
        return False

async def main():
    """Main execution"""
    print("🔧 QUICK DATABASE SCHEMA FIX")
    print("=" * 35)
    print("This will recreate the database with proper SQLAlchemy schema")
    print()
    
    success = await create_proper_database()
    
    if success:
        print("✅ Database fix completed!")
        print("🔄 Next steps:")
        print("   1. Restart services: python3 bin/start_lpr.py")
        print("   2. Test endpoints working")
    else:
        print("❌ Database fix failed!")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)