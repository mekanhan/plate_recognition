#!/usr/bin/env python3
"""
Database migration script to update camera schema with manufacturer-specific fields
"""

import sqlite3
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_camera_schema():
    """Migrate camera schema to add manufacturer-specific fields"""
    db_path = "data/license_plates.db"
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current schema
        cursor.execute("PRAGMA table_info(cameras)")
        columns = [column[1] for column in cursor.fetchall()]
        
        logger.info(f"Current camera table columns: {columns}")
        
        # Add new columns if they don't exist
        migrations = [
            ("connection_type", "TEXT DEFAULT 'rtsp'"),
            ("stream_path", "TEXT"),
            ("auth_type", "TEXT DEFAULT 'basic'"),
            ("manufacturer_config", "TEXT"),  # JSON stored as TEXT
            ("supported_codecs", "TEXT"),     # JSON stored as TEXT
            ("capabilities", "TEXT"),         # JSON stored as TEXT
            ("connection_test_results", "TEXT"),  # JSON stored as TEXT
            ("last_tested_at", "TIMESTAMP"),
            ("last_successful_connection", "TIMESTAMP"),
        ]
        
        for column_name, column_type in migrations:
            if column_name not in columns:
                logger.info(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE cameras ADD COLUMN {column_name} {column_type}")
            else:
                logger.info(f"Column {column_name} already exists, skipping")
        
        # Create a backup table name with timestamp
        backup_table = f"cameras_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create backup of current cameras table
        cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM cameras")
        logger.info(f"Created backup table: {backup_table}")
        
        # Update existing cameras with default values where appropriate
        cursor.execute("""
            UPDATE cameras 
            SET connection_type = 'rtsp',
                auth_type = 'basic',
                manufacturer_config = '{}',
                supported_codecs = '["H.264", "MJPEG"]',
                capabilities = '["video"]'
            WHERE connection_type IS NULL
        """)
        
        # Update stream_path based on existing main_stream_url if available
        cursor.execute("""
            UPDATE cameras 
            SET stream_path = CASE 
                WHEN main_stream_url IS NOT NULL AND main_stream_url != '' 
                THEN substr(main_stream_url, instr(main_stream_url, '/') + 1)
                ELSE '/stream1'
            END
            WHERE stream_path IS NULL
        """)
        
        # Update port based on connection_type if not set
        cursor.execute("""
            UPDATE cameras 
            SET port = CASE 
                WHEN connection_type = 'rtsp' THEN 554
                WHEN connection_type = 'rtsps' THEN 322
                WHEN connection_type = 'http' THEN 80
                WHEN connection_type = 'https' THEN 443
                WHEN connection_type = 'onvif' THEN 80
                ELSE 554
            END
            WHERE port IS NULL OR port = 0
        """)
        
        conn.commit()
        logger.info("Migration completed successfully")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(cameras)")
        new_columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Updated camera table columns: {new_columns}")
        
        # Count rows to verify data integrity
        cursor.execute("SELECT COUNT(*) FROM cameras")
        count = cursor.fetchone()[0]
        logger.info(f"Camera table has {count} rows after migration")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """Verify the migration was successful"""
    db_path = "data/license_plates.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if all expected columns exist
        cursor.execute("PRAGMA table_info(cameras)")
        columns = [column[1] for column in cursor.fetchall()]
        
        expected_columns = [
            'connection_type', 'stream_path', 'auth_type', 
            'manufacturer_config', 'supported_codecs', 'capabilities',
            'connection_test_results', 'last_tested_at', 'last_successful_connection'
        ]
        
        missing_columns = [col for col in expected_columns if col not in columns]
        
        if missing_columns:
            logger.error(f"Missing columns after migration: {missing_columns}")
            return False
        
        logger.info("Migration verification successful - all columns present")
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting camera schema migration")
    
    # Run migration
    success = migrate_camera_schema()
    
    if success:
        # Verify migration
        if verify_migration():
            logger.info("Camera schema migration completed successfully")
        else:
            logger.error("Migration verification failed")
    else:
        logger.error("Migration failed")