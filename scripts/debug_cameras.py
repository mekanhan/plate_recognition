#!/usr/bin/env python3
"""
Debug script to check camera database directly
"""
import asyncio
import sys
import os
sys.path.append('.')

from database.db_config import DatabaseConfig
from sqlalchemy import text

async def debug_cameras():
    """Debug camera entries in database"""
    db_config = DatabaseConfig()
    
    try:
        async with db_config.get_session() as session:
            print("=== CAMERA DATABASE DEBUG ===\n")
            
            # Get all cameras
            result = await session.execute(text("SELECT camera_id, name, status, ip_address, stable_camera_id FROM cameras"))
            cameras = result.fetchall()
            
            print(f"Found {len(cameras)} camera entries:")
            for i, camera in enumerate(cameras, 1):
                camera_id, name, status, ip, stable_id = camera
                print(f"{i}. ID: {camera_id}")
                print(f"   Name: {name}")
                print(f"   Status: {status}")
                print(f"   IP: {ip}")
                print(f"   Stable ID: {stable_id}")
                print()
            
            # Check recording directories
            print("=== RECORDING DIRECTORIES ===\n")
            import os
            recordings_path = "recordings"
            if os.path.exists(recordings_path):
                dirs = [d for d in os.listdir(recordings_path) if os.path.isdir(os.path.join(recordings_path, d))]
                print(f"Found {len(dirs)} recording directories:")
                for dir_name in dirs:
                    dir_path = os.path.join(recordings_path, dir_name)
                    # Check if this directory has a corresponding active camera
                    matching_camera = None
                    for camera in cameras:
                        if camera[0] == dir_name or (camera[4] and camera[4] == dir_name):  # camera_id or stable_camera_id
                            matching_camera = camera
                            break
                    
                    # Get directory size
                    size = sum(os.path.getsize(os.path.join(dirpath, filename))
                              for dirpath, dirnames, filenames in os.walk(dir_path)
                              for filename in filenames) / (1024*1024*1024)  # GB
                    
                    status = "✅ ACTIVE CAMERA" if matching_camera else "❌ ORPHANED"
                    print(f"  📁 {dir_name} ({size:.1f} GB) - {status}")
                    if not matching_camera:
                        print(f"     ⚠️  No matching camera in database")
                print()
            else:
                print("No recordings directory found")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_cameras())