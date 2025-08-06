#!/usr/bin/env python3
"""
Migration script for Camera Database Schema
Migrates existing hardcoded cameras to new database-driven architecture
"""
import asyncio
import logging
from datetime import datetime
from database.service import DatabaseService
from database.camera_service import CameraService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CameraMigration")

# Default cameras to migrate (based on existing system)
DEFAULT_CAMERAS = [
    {
        "camera_id": "camera_946701d3",
        "name": "Reolink Main Entrance",
        "location": "Main Entrance",
        "ip_address": "10.0.0.181",
        "protocol": "RTSP",
        "port": 554,
        "username": "admin", 
        "password": "Mekus_1987",  # Will be encrypted
        "stream_path": "/h264/ch1/main/av_stream",
        "recording_enabled": True,
        "settings": {
            "resolution": "4K",
            "fps": 30,
            "quality": "high",
            "night_vision": True
        }
    },
    {
        "camera_id": "camera_entrance_cam",
        "name": "Entrance Security Camera",
        "location": "Front Entrance",
        "ip_address": "10.0.0.182",
        "protocol": "RTSP",
        "port": 554,
        "username": "admin",
        "password": "DefaultPass123",  # Will be encrypted
        "stream_path": "/stream1",
        "recording_enabled": True,
        "settings": {
            "resolution": "1080p",
            "fps": 25,
            "quality": "medium"
        }
    },
    {
        "camera_id": "camera_parking_cam",
        "name": "Parking Lot Camera",
        "location": "Parking Lot",
        "ip_address": "192.168.1.100",
        "protocol": "HTTP",
        "port": 8080,
        "username": "admin",
        "password": "ParkingCam2024",  # Will be encrypted
        "stream_path": "/video",
        "recording_enabled": False,
        "settings": {
            "resolution": "720p",
            "fps": 15,
            "quality": "low",
            "motion_detection": True
        }
    }
]

async def main():
    """Main migration function"""
    logger.info("Starting camera database migration...")
    
    try:
        # Initialize services
        db_service = DatabaseService()
        await db_service.init_db()
        logger.info("Database initialized")
        
        camera_service = CameraService(db_service)
        
        # Check if cameras already exist
        existing_cameras = await camera_service.get_all_cameras()
        if existing_cameras:
            logger.info(f"Found {len(existing_cameras)} existing cameras")
            print("\nExisting cameras:")
            for camera in existing_cameras:
                print(f"  - {camera['name']} ({camera['id']}) - {camera.get('location', 'No location')}")
            
            # Ask if user wants to continue
            response = input("\nDo you want to add more cameras? (y/n): ").lower().strip()
            if response != 'y':
                logger.info("Migration cancelled by user")
                return
        else:
            logger.info("No existing cameras found - proceeding with migration")
        
        # Migrate cameras
        migrated_count = 0
        for camera_data in DEFAULT_CAMERAS:
            try:
                # Check if camera already exists
                existing = await camera_service.get_camera(camera_data["camera_id"])
                if existing:
                    logger.info(f"Camera {camera_data['camera_id']} already exists - skipping")
                    continue
                
                logger.info(f"Creating camera: {camera_data['name']}")
                result = await camera_service.create_camera(camera_data)
                
                if result:
                    logger.info(f"✅ Successfully created camera: {result['name']} ({result['id']})")
                    migrated_count += 1
                    
                    # Initialize with default status
                    await camera_service.update_camera_status(result['id'], {
                        "recording_status": "stopped",
                        "connection_status": "disconnected", 
                        "segments_created": 0,
                        "storage_used_bytes": 0
                    })
                    
                else:
                    logger.error(f"❌ Failed to create camera: {camera_data['name']}")
                    
            except Exception as e:
                logger.error(f"❌ Error creating camera {camera_data['name']}: {e}")
        
        # Summary
        logger.info(f"\n🎉 Migration completed!")
        logger.info(f"Cameras migrated: {migrated_count}")
        
        # Show final status
        final_cameras = await camera_service.get_all_cameras()
        logger.info(f"Total cameras in database: {len(final_cameras)}")
        
        print("\n📋 Camera Database Summary:")
        print("=" * 50)
        for camera in final_cameras:
            status = camera.get('current_status', {})
            print(f"🎥 {camera['name']}")
            print(f"   ID: {camera['id']}")
            print(f"   Location: {camera.get('location', 'Unknown')}")
            print(f"   Connection: {camera.get('protocol', 'Unknown')} ({camera.get('ip_address', 'Unknown')})")
            print(f"   Recording: {status.get('recording_status', 'Unknown')}")
            print(f"   Status: {status.get('connection_status', 'Unknown')}")
            print()
        
        # Test the new API
        logger.info("Testing new camera API endpoints...")
        status_data = await camera_service.get_cameras_status()
        logger.info(f"✅ Status API working - {status_data.get('count', 0)} cameras")
        
        print("\n🚀 Migration Complete!")
        print("You can now:")
        print("  1. Start the API server: python3 -m api.main")
        print("  2. Test the new endpoints at: http://localhost:8001/v2/api/cameras/status")
        print("  3. Use the frontend with real-time database-driven camera data")
        print("\n🔗 New API Endpoints Available:")
        print("  - GET    /v2/api/cameras/status          - Bulk camera status (8-field standard)")
        print("  - GET    /v2/api/cameras                 - List all cameras")
        print("  - POST   /v2/api/cameras                 - Create new camera")
        print("  - GET    /v2/api/cameras/{id}/status     - Single camera status")
        print("  - POST   /v2/api/cameras/{id}/start      - Start recording")
        print("  - POST   /v2/api/cameras/{id}/stop       - Stop recording")
        print("  - PUT    /v2/api/cameras/{id}/status     - Update camera status")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🎬 Camera Database Migration Script")
    print("=" * 40)
    print("This script will migrate cameras to the new database-driven architecture.")
    print("It will create the required database tables and populate them with default cameras.")
    print()
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration failed!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        import traceback
        traceback.print_exc()