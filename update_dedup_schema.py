#!/usr/bin/env python3
"""
Update database schema to add deduplication fields
Run this script to add the new columns to existing database
"""
import sqlite3
import sys
from pathlib import Path

def update_schema():
    """Add deduplication columns to detections table"""
    
    db_path = Path("data/license_plates.db")
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(detections)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Define new columns to add
        new_columns = [
            ("group_id", "TEXT"),
            ("is_best_shot", "BOOLEAN DEFAULT 0"),
            ("duplicate_of", "TEXT"),
            ("track_id", "TEXT"),
            ("ocr_confidence", "REAL"),
            ("image_saved", "BOOLEAN DEFAULT 1")
        ]
        
        # Add missing columns
        added_columns = []
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE detections ADD COLUMN {col_name} {col_type}")
                    added_columns.append(col_name)
                    print(f"✅ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print(f"ℹ️ Column {col_name} already exists")
                    else:
                        print(f"❌ Error adding column {col_name}: {e}")
        
        # Create indexes for better query performance
        indexes = [
            ("idx_detections_group_id", "detections(group_id)"),
            ("idx_detections_plate_camera", "detections(plate_text, camera_id, detected_at)"),
            ("idx_detections_track_id", "detections(track_id)"),
            ("idx_detections_best_shot", "detections(is_best_shot)")
        ]
        
        for index_name, index_def in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                print(f"✅ Created/verified index: {index_name}")
            except sqlite3.OperationalError as e:
                print(f"ℹ️ Index {index_name} might already exist: {e}")
        
        # Commit changes
        conn.commit()
        
        if added_columns:
            print(f"\n✅ Schema update complete! Added {len(added_columns)} new columns.")
        else:
            print(f"\n✅ Schema is already up to date.")
        
        # Show current schema
        print("\n📊 Current detections table schema:")
        cursor.execute("PRAGMA table_info(detections)")
        for row in cursor.fetchall():
            col_id, name, dtype, notnull, default, pk = row
            print(f"  - {name}: {dtype}{' (PK)' if pk else ''}{' NOT NULL' if notnull else ''}{f' DEFAULT {default}' if default else ''}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Updating database schema for deduplication support...")
    print("-" * 50)
    
    if update_schema():
        print("\n✨ Database schema updated successfully!")
        print("\nNext steps:")
        print("1. Restart the API service to use new schema")
        print("2. The deduplication system will start working automatically")
    else:
        print("\n❌ Schema update failed. Please check the error messages above.")
        sys.exit(1)