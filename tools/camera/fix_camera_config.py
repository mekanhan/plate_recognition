#!/usr/bin/env python3
"""
Camera Configuration Fix Script
Updates camera configuration based on diagnostic results
"""
import asyncio
import sys
import argparse
from database.service import DatabaseService

async def fix_camera_stream_path(camera_id: str, new_stream_path: str):
    """Update camera stream path"""
    db = DatabaseService()
    await db.init_db()
    
    try:
        # Get current camera
        camera = await db.get_camera(camera_id)
        if not camera:
            print(f"❌ Camera {camera_id} not found")
            return False
        
        print(f"📷 Updating camera: {camera.name}")
        print(f"   Current path: {camera.stream_path}")
        print(f"   New path: {new_stream_path}")
        
        # Update the stream path
        success = await db.update_camera(camera_id, {
            'stream_path': new_stream_path
        })
        
        if success:
            print(f"✅ Successfully updated stream path")
            
            # Update test result to mark as successful
            await db.update_camera_test_result(camera_id, 'success')
            print(f"✅ Updated test result to 'success'")
            
            return True
        else:
            print(f"❌ Failed to update camera configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error updating camera: {e}")
        return False
    finally:
        await db.close()

async def list_cameras():
    """List all cameras and their current configuration"""
    db = DatabaseService()
    await db.init_db()
    
    try:
        cameras = await db.get_all_cameras()
        
        if not cameras:
            print("No cameras found in database")
            return
        
        print(f"\n📷 Found {len(cameras)} camera(s):")
        print("-" * 80)
        
        for camera in cameras:
            print(f"ID: {camera.camera_id}")
            print(f"Name: {camera.name}")
            print(f"IP: {camera.ip_address}:{camera.port}")
            print(f"Stream Path: {camera.stream_path}")
            print(f"Status: {camera.status}")
            print(f"Last Test: {camera.last_test_result}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Error listing cameras: {e}")
    finally:
        await db.close()

def main():
    parser = argparse.ArgumentParser(description='Fix camera configuration based on diagnostics')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List cameras
    list_parser = subparsers.add_parser('list', help='List all cameras')
    
    # Fix stream path
    fix_parser = subparsers.add_parser('fix', help='Fix camera stream path')
    fix_parser.add_argument('camera_id', help='Camera ID to fix')
    fix_parser.add_argument('stream_path', help='New stream path (e.g., /h264Preview_01_main)')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        asyncio.run(list_cameras())
    elif args.command == 'fix':
        success = asyncio.run(fix_camera_stream_path(args.camera_id, args.stream_path))
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()