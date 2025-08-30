#!/usr/bin/env python3
"""
Cleanup script for orphaned recording directories
Removes recording folders that don't have corresponding active cameras
"""
import asyncio
import sys
import os
import shutil
sys.path.append('.')

from database.db_config import DatabaseConfig
from sqlalchemy import text

async def cleanup_orphaned_recordings(dry_run=True):
    """Clean up orphaned recording directories"""
    db_config = DatabaseConfig()
    
    try:
        async with db_config.get_session() as session:
            print("=== ORPHANED RECORDINGS CLEANUP ===\n")
            
            # Get all active cameras
            result = await session.execute(text("SELECT camera_id, name, stable_camera_id FROM cameras WHERE status = 'active'"))
            active_cameras = result.fetchall()
            
            print(f"Active cameras in database: {len(active_cameras)}")
            for camera in active_cameras:
                camera_id, name, stable_id = camera
                print(f"  - {name} (ID: {camera_id}, Stable: {stable_id})")
            print()
            
            # Check recording directories
            recordings_path = "recordings"
            if not os.path.exists(recordings_path):
                print("No recordings directory found")
                return
            
            dirs = [d for d in os.listdir(recordings_path) if os.path.isdir(os.path.join(recordings_path, d))]
            active_camera_ids = {camera[0] for camera in active_cameras}  # camera_id
            active_stable_ids = {camera[2] for camera in active_cameras if camera[2]}  # stable_camera_id
            
            orphaned_dirs = []
            active_dirs = []
            
            for dir_name in dirs:
                dir_path = os.path.join(recordings_path, dir_name)
                
                # Check if this directory matches any active camera
                # Include both direct camera_id matches and camera_{camera_id} format
                is_active = (dir_name in active_camera_ids or 
                           dir_name in active_stable_ids or
                           any(dir_name == f"camera_{camera_id}" for camera_id in active_camera_ids))
                
                # Get directory size
                size = 0
                try:
                    size = sum(os.path.getsize(os.path.join(dirpath, filename))
                              for dirpath, dirnames, filenames in os.walk(dir_path)
                              for filename in filenames) / (1024*1024*1024)  # GB
                except:
                    pass
                
                if is_active:
                    active_dirs.append((dir_name, size))
                    print(f"✅ KEEPING: {dir_name} ({size:.1f} GB) - Active camera")
                else:
                    orphaned_dirs.append((dir_name, size))
                    print(f"❌ ORPHANED: {dir_name} ({size:.1f} GB) - No matching camera")
            
            print(f"\nSummary:")
            print(f"  Active directories: {len(active_dirs)}")
            print(f"  Orphaned directories: {len(orphaned_dirs)}")
            
            if orphaned_dirs:
                total_orphaned_size = sum(size for _, size in orphaned_dirs)
                print(f"  Total orphaned data: {total_orphaned_size:.1f} GB")
                
                if dry_run:
                    print(f"\n🔍 DRY RUN MODE - Would delete:")
                    for dir_name, size in orphaned_dirs:
                        print(f"    - {dir_name} ({size:.1f} GB)")
                    print(f"\nRun with '--delete' to actually remove these directories")
                else:
                    print(f"\n🗑️  DELETING orphaned directories...")
                    for dir_name, size in orphaned_dirs:
                        dir_path = os.path.join(recordings_path, dir_name)
                        print(f"    Removing {dir_name} ({size:.1f} GB)...")
                        try:
                            shutil.rmtree(dir_path)
                            print(f"    ✅ Deleted {dir_name}")
                        except Exception as e:
                            print(f"    ❌ Failed to delete {dir_name}: {e}")
                    
                    print(f"\n✅ Cleanup completed! Freed {total_orphaned_size:.1f} GB")
            else:
                print(f"\n✅ No orphaned directories found")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dry_run = "--delete" not in sys.argv
    
    if dry_run:
        print("🔍 Running in DRY RUN mode (no files will be deleted)")
        print("Use --delete flag to actually remove orphaned directories\n")
    else:
        print("⚠️  LIVE MODE: Will actually delete orphaned directories\n")
        response = input("Are you sure you want to delete orphaned recordings? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)
    
    asyncio.run(cleanup_orphaned_recordings(dry_run))