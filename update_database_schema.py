#!/usr/bin/env python3
"""
Update database schema to add missing Camera columns
"""
import sqlite3
import os
from pathlib import Path

def update_schema():
    """Update the database schema"""
    db_path = Path("data/license_plates.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"📊 Updating database schema at {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(cameras)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"Existing columns: {existing_columns}")
        
        # Define new columns to add
        new_columns = [
            ("port", "INTEGER DEFAULT 80"),
            ("connection_type", "VARCHAR(20) DEFAULT 'http'"),
            ("stream_path", "VARCHAR(200) DEFAULT '/mjpeg'"),
            ("username", "VARCHAR(100)"),
            ("password", "VARCHAR(100)"),
            ("brand", "VARCHAR(100)"),
            ("model", "VARCHAR(100)"),
            ("resolution_width", "INTEGER DEFAULT 1920"),
            ("resolution_height", "INTEGER DEFAULT 1080"),
            ("max_fps", "INTEGER DEFAULT 30"),
            ("video_quality", "VARCHAR(20) DEFAULT 'medium'"),
            ("low_latency", "BOOLEAN DEFAULT 1"),
            ("last_test_at", "DATETIME"),
            ("last_test_result", "TEXT"),
            # ONVIF Discovery fields
            ("onvif_service_url", "VARCHAR(500)"),
            ("onvif_port", "INTEGER DEFAULT 80"),
            ("manufacturer", "VARCHAR(100)"),
            ("discovered_via", "VARCHAR(20) DEFAULT 'manual'"),
            ("discovery_timestamp", "DATETIME"),
            ("hardware_id", "VARCHAR(200)"),
            ("onvif_scopes", "TEXT DEFAULT '[]'")
        ]
        
        # Add missing columns
        added_count = 0
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE cameras ADD COLUMN {column_name} {column_def}"
                    cursor.execute(sql)
                    print(f"   ✅ Added column: {column_name}")
                    added_count += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"   ⏭️  Column already exists: {column_name}")
                    else:
                        print(f"   ❌ Failed to add {column_name}: {e}")
        
        conn.commit()
        conn.close()
        
        if added_count > 0:
            print(f"\n✅ Successfully added {added_count} columns to cameras table")
        else:
            print("\n✅ Database schema is already up to date")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        return False

if __name__ == "__main__":
    if update_schema():
        print("\n🎉 Database schema update complete!")
        print("You can now start the services.")
    else:
        print("\n❌ Database schema update failed!")