#!/usr/bin/env python3
"""
Test database operations - create tables, add/retrieve data
"""
import asyncio
import os
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.service import DatabaseService
from database.models import Base

print("🗄️  Testing Database Operations...\n")

async def test_database():
    # Create data directory if it doesn't exist
    os.makedirs("../data", exist_ok=True)
    
    # Initialize database service
    print("Initializing database service...")
    db = DatabaseService("sqlite+aiosqlite:///../data/test_license_plates.db")
    
    try:
        # Test 1: Create tables
        print("\n1. Creating database tables...")
        await db.create_tables()
        print("✅ Database tables created successfully")
        
        # Test 2: Add cameras
        print("\n2. Testing camera operations...")
        
        # Add test cameras
        cameras_data = [
            {
                "camera_id": "test_cam_1",
                "name": "Test Camera 1",
                "ip_address": "192.168.1.100",
                "location": "Main Entrance",
                "status": "active"
            },
            {
                "camera_id": "test_cam_2", 
                "name": "Test Camera 2",
                "ip_address": "192.168.1.101",
                "location": "Parking Lot",
                "status": "offline"
            }
        ]
        
        for cam_data in cameras_data:
            camera_id = await db.add_camera(cam_data)
            print(f"✅ Added camera: {cam_data['name']} (ID: {camera_id})")
        
        # Retrieve all cameras
        all_cameras = await db.get_all_cameras()
        print(f"✅ Retrieved {len(all_cameras)} cameras from database")
        
        for cam in all_cameras:
            print(f"   - {cam.name} ({cam.camera_id}): {cam.status}")
        
        # Test 3: Add detections
        print("\n3. Testing detection operations...")
        
        test_detections = [
            {
                "detection_id": "test_det_1",
                "camera_id": "test_cam_1",
                "detected_at": datetime.now(),
                "plate_text": "ABC123",
                "confidence": 0.95,
                "vehicle_type": "car",
                "vehicle_bbox": [100, 100, 300, 250],
                "plate_bbox": [150, 200, 250, 230]
            },
            {
                "detection_id": "test_det_2",
                "camera_id": "test_cam_1",
                "detected_at": datetime.now() - timedelta(minutes=5),
                "plate_text": "XYZ789",
                "confidence": 0.87,
                "vehicle_type": "truck",
                "vehicle_bbox": [50, 80, 400, 300],
                "plate_bbox": [180, 250, 320, 290]
            }
        ]
        
        for det_data in test_detections:
            det_id = await db.save_detection(det_data)
            print(f"✅ Added detection: {det_data['plate_text']} (ID: {det_id})")
        
        # Retrieve recent detections
        recent_detections = await db.get_recent_detections(limit=10)
        print(f"✅ Retrieved {len(recent_detections)} recent detections")
        
        for det in recent_detections:
            print(f"   - {det.plate_text} at {det.detected_at.strftime('%H:%M:%S')} (confidence: {det.confidence:.2f})")
        
        # Test 4: Search detections
        print("\n4. Testing detection search...")
        
        # Search by plate text
        search_results = await db.search_detections(plate_text="ABC")
        print(f"✅ Found {len(search_results)} detections matching 'ABC'")
        
        # Test 5: Analytics
        print("\n5. Testing analytics...")
        
        analytics = await db.get_analytics_overview()
        print("✅ Analytics overview retrieved:")
        print(f"   - Detections today: {analytics['total_detections_today']}")
        print(f"   - Unique plates today: {analytics['unique_plates_today']}")
        print(f"   - Active cameras: {analytics['active_cameras']['active']}/{analytics['active_cameras']['total']}")
        
        # Test 6: Camera status update
        print("\n6. Testing camera status update...")
        
        await db.update_camera_status("test_cam_2", "online")
        updated_cam = await db.get_camera("test_cam_2")
        if updated_cam:
            print(f"✅ Updated camera status: {updated_cam.name} is now {updated_cam.status}")
        
        # Test 7: Last detection time
        print("\n7. Testing last detection time...")
        
        last_det_time = await db.get_last_detection_time("test_cam_1")
        if last_det_time:
            print(f"✅ Last detection for test_cam_1: {last_det_time}")
        
        print("\n" + "="*60)
        print("✅ ALL DATABASE TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Close database connection
        await db.close()
        print("\n✅ Database connection closed")

# Additional test: Check if database file was created
def check_database_file():
    db_path = "../data/test_license_plates.db"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"\n✅ Database file created: {db_path}")
        print(f"   Size: {size:,} bytes")
        return True
    else:
        print(f"\n❌ Database file not found: {db_path}")
        return False

# Main execution
if __name__ == "__main__":
    print("="*60)
    print("Database Operations Test")
    print("="*60)
    
    # Run async database tests
    asyncio.run(test_database())
    
    # Check database file
    check_database_file()
    
    print("\nDatabase test complete!")
    print("You can inspect the test database at: ../data/test_license_plates.db")