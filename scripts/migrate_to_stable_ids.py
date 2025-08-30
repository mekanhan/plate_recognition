#!/usr/bin/env python3
"""
Migration script to move recordings from camera_id folders to stable_camera_id folders
"""
import asyncio
import sys
import os
import shutil
from pathlib import Path
sys.path.append('.')

from database.db_config import DatabaseConfig
from sqlalchemy import text

async def migrate_recordings_to_stable_ids(dry_run=True):
    """Migrate recording folders to use stable camera IDs"""
    db_config = DatabaseConfig()
    
    try:
        async with db_config.get_session() as session:
            print("=== MIGRATION TO STABLE CAMERA IDS ===\n")
            
            # Get all active cameras with their stable IDs
            result = await session.execute(text("SELECT camera_id, name, stable_camera_id FROM cameras WHERE status = 'active'"))
            cameras = result.fetchall()
            
            print(f"Active cameras: {len(cameras)}")
            for camera_id, name, stable_id in cameras:
                print(f"  - {name}")
                print(f"    camera_id: {camera_id}")
                print(f"    stable_camera_id: {stable_id}")
                print()
            
            # Check current recording directories
            recordings_path = Path("recordings")
            if not recordings_path.exists():
                print("No recordings directory found")
                return
            
            migrations_needed = []
            
            for camera_id, name, stable_id in cameras:
                if not stable_id:
                    print(f"⚠️  Camera {name} has no stable_camera_id, skipping")
                    continue
                
                # Look for existing recording directories
                possible_dirs = [
                    recordings_path / camera_id,
                    recordings_path / f"camera_{camera_id}"
                ]
                
                existing_dir = None
                for dir_path in possible_dirs:
                    if dir_path.exists():
                        existing_dir = dir_path
                        break
                
                if existing_dir:
                    target_dir = recordings_path / stable_id
                    
                    if existing_dir != target_dir:
                        # Calculate directory size
                        size = 0
                        try:
                            size = sum(f.stat().st_size for f in existing_dir.rglob('*') if f.is_file()) / (1024*1024*1024)
                        except:
                            pass
                        
                        migrations_needed.append({
                            'camera_name': name,
                            'source': existing_dir,
                            'target': target_dir,
                            'size_gb': size
                        })
                        
                        print(f"📦 Migration needed for {name}:")
                        print(f"   From: {existing_dir}")
                        print(f"   To: {target_dir}")
                        print(f"   Size: {size:.1f} GB")
                        print()
            
            if not migrations_needed:
                print("✅ No migrations needed - all cameras already using correct folder structure")
                return
            
            total_size = sum(m['size_gb'] for m in migrations_needed)
            print(f"Summary: {len(migrations_needed)} migrations needed, {total_size:.1f} GB total")
            
            if dry_run:
                print("\n🔍 DRY RUN MODE - Would perform these migrations:")
                for migration in migrations_needed:
                    print(f"  - {migration['camera_name']}: {migration['source'].name} → {migration['target'].name}")
                print("\nRun with --migrate to perform actual migration")
            else:
                print("\n🚚 Performing migrations...")
                for migration in migrations_needed:
                    source = migration['source']
                    target = migration['target']
                    camera_name = migration['camera_name']
                    
                    print(f"  Migrating {camera_name}...")
                    
                    if target.exists():
                        print(f"    ❌ Target directory already exists: {target}")
                        continue
                    
                    try:
                        # Move the directory
                        shutil.move(str(source), str(target))
                        print(f"    ✅ Moved {source.name} → {target.name}")
                    except Exception as e:
                        print(f"    ❌ Failed to move {source.name}: {e}")
                
                print(f"\n✅ Migration completed!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dry_run = "--migrate" not in sys.argv
    
    if dry_run:
        print("🔍 Running in DRY RUN mode")
        print("Use --migrate flag to perform actual migration\n")
    else:
        print("⚠️  MIGRATION MODE: Will move recording folders\n")
        response = input("Are you sure you want to migrate recording folders? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)
    
    asyncio.run(migrate_recordings_to_stable_ids(dry_run))