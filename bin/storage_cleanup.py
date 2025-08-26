#!/usr/bin/env python3
"""
Quick Storage Cleanup Script
Cleans up old detection images and optimizes database
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_old_images(max_age_days=1, dry_run=True):
    """Clean up old detection images"""
    print(f"🗂️  Cleaning detection images older than {max_age_days} days ({'DRY RUN' if dry_run else 'EXECUTING'})")
    
    cutoff = (datetime.now() - timedelta(days=max_age_days)).timestamp()
    
    deleted_count = 0
    freed_mb = 0
    
    for image_type in ['frames', 'plates']:
        dir_path = Path('detections') / image_type
        if not dir_path.exists():
            continue
            
        print(f"   Processing {image_type}...")
        
        for img_file in dir_path.glob('*.jpg'):
            if img_file.stat().st_mtime < cutoff:
                size_mb = img_file.stat().st_size / (1024*1024)
                
                if not dry_run:
                    img_file.unlink()
                
                deleted_count += 1
                freed_mb += size_mb
                
                if deleted_count % 1000 == 0:
                    print(f"      Processed {deleted_count:,} files...")
    
    print(f"   ✅ {deleted_count:,} files, {freed_mb:.1f}MB ({freed_mb/1024:.2f}GB)")
    return deleted_count, freed_mb

def optimize_database(dry_run=True):
    """Optimize database and checkpoint WAL"""
    print(f"🗄️  Optimizing database ({'DRY RUN' if dry_run else 'EXECUTING'})")
    
    db_path = 'data/license_plates.db'
    wal_path = f'{db_path}-wal'
    
    # Get WAL size before
    wal_size_before = os.path.getsize(wal_path) / (1024*1024) if os.path.exists(wal_path) else 0
    print(f"   WAL file size: {wal_size_before:.1f}MB")
    
    if not dry_run:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Checkpoint WAL
        print("   Checkpointing WAL...")
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        
        # Optimize
        print("   Running PRAGMA optimize...")
        cursor.execute("PRAGMA optimize")
        
        conn.commit()
        conn.close()
    
    # Get WAL size after
    wal_size_after = os.path.getsize(wal_path) / (1024*1024) if os.path.exists(wal_path) else 0
    freed_mb = wal_size_before - wal_size_after
    
    print(f"   ✅ WAL size reduced by {freed_mb:.1f}MB")
    return freed_mb

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick Storage Cleanup')
    parser.add_argument('--execute', action='store_true', help='Actually perform cleanup (default is dry run)')
    parser.add_argument('--max-age', type=int, default=1, help='Max age in days for images (default: 1)')
    
    args = parser.parse_args()
    dry_run = not args.execute
    
    print("🧹 STORAGE CLEANUP STARTING")
    print(f"   Mode: {'EXECUTE' if not dry_run else 'DRY RUN'}")
    print(f"   Image retention: {args.max_age} days")
    print()
    
    # Clean images
    img_count, img_freed_mb = cleanup_old_images(args.max_age, dry_run)
    
    # Optimize database
    db_freed_mb = optimize_database(dry_run)
    
    # Summary
    total_freed_mb = img_freed_mb + db_freed_mb
    print()
    print("📊 CLEANUP SUMMARY:")
    print(f"   Images: {img_count:,} files, {img_freed_mb:.1f}MB")
    print(f"   Database: {db_freed_mb:.1f}MB")
    print(f"   Total freed: {total_freed_mb:.1f}MB ({total_freed_mb/1024:.2f}GB)")
    
    if dry_run:
        print()
        print("💡 Add --execute to actually perform cleanup")

if __name__ == "__main__":
    main()