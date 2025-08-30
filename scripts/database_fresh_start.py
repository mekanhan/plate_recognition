#!/usr/bin/env python3
"""
Database Fresh Start Script
Completely clean database and rebuild with proper schema
"""
import os
import sqlite3
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseFreshStart:
    def __init__(self):
        self.db_path = "data/license_plates.db"
        self.backup_dir = "data/backups"
        self.detection_dirs = ["detections", "detections/frames", "detections/plates"]
        
    def step_1_backup_current_database(self):
        """Create backup of current database before cleanup"""
        logger.info("🔄 Step 1: Creating backup of current database...")
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        
        if os.path.exists(self.db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.backup_dir}/license_plates_backup_{timestamp}.db"
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Database backed up to: {backup_path}")
            
            # Get database stats before cleanup
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    stats[table_name] = count
                    
                logger.info(f"📊 Current database stats: {stats}")
                
            except Exception as e:
                logger.warning(f"Could not get database stats: {e}")
            finally:
                conn.close()
                
        else:
            logger.info("📝 No existing database found - starting completely fresh")
            
    def step_2_clean_database_files(self):
        """Remove existing database and related files"""
        logger.info("🗑️  Step 2: Cleaning database files...")
        
        files_to_remove = [
            self.db_path,
            f"{self.db_path}-wal",  # WAL file
            f"{self.db_path}-shm",  # Shared memory file
            "data/license_plates.db-journal"  # Journal file
        ]
        
        removed_count = 0
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️  Removed: {file_path}")
                removed_count += 1
                
        logger.info(f"✅ Cleaned {removed_count} database files")
        
    def step_3_clean_detection_files(self, keep_sample=True):
        """Clean detection image files"""
        logger.info("🖼️  Step 3: Cleaning detection files...")
        
        total_removed = 0
        sample_kept = 0
        
        for detection_dir in self.detection_dirs:
            if os.path.exists(detection_dir):
                files = list(Path(detection_dir).glob("*"))
                
                if keep_sample and detection_dir in ["detections/frames", "detections/plates"]:
                    # Keep first 2 files as samples for testing
                    to_remove = files[2:] if len(files) > 2 else []
                    sample_kept += min(2, len(files))
                else:
                    to_remove = files
                    
                for file_path in to_remove:
                    if file_path.is_file():
                        file_path.unlink()
                        total_removed += 1
                        
        logger.info(f"✅ Removed {total_removed} detection files, kept {sample_kept} samples")
        
    def step_4_create_fresh_database(self):
        """Create fresh database with proper schema"""
        logger.info("🏗️  Step 4: Creating fresh database...")
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Create fresh database with proper schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create cameras table
            cursor.execute("""
                CREATE TABLE cameras (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    connection_type TEXT NOT NULL DEFAULT 'http',
                    stream_path TEXT DEFAULT '/video',
                    username TEXT,
                    password TEXT,
                    status TEXT DEFAULT 'offline',
                    last_seen TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create detections table (main detection table)
            cursor.execute("""
                CREATE TABLE detections (
                    id TEXT PRIMARY KEY,
                    camera_id TEXT NOT NULL,
                    plate_text TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    vehicle_type TEXT DEFAULT 'car',
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    plate_image_path TEXT,
                    frame_path TEXT,
                    video_clip_id TEXT,
                    bbox_x INTEGER,
                    bbox_y INTEGER,
                    bbox_width INTEGER,
                    bbox_height INTEGER,
                    processing_time_ms INTEGER DEFAULT 0,
                    model_version TEXT DEFAULT '1.0',
                    status TEXT DEFAULT 'unverified',
                    flagged BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (id)
                )
            """)
            
            # Create universal_detections table (for enhanced detection system)
            cursor.execute("""
                CREATE TABLE universal_detections (
                    id TEXT PRIMARY KEY,
                    camera_id TEXT NOT NULL,
                    object_type TEXT NOT NULL DEFAULT 'vehicle',
                    confidence REAL NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    bbox TEXT,  -- JSON string for bounding box
                    frame_path TEXT,
                    object_image_path TEXT,
                    video_clip_id TEXT,
                    video_thumbnail_path TEXT,
                    metadata TEXT,  -- JSON string for additional data like plate_text
                    status TEXT DEFAULT 'unverified',
                    flagged BOOLEAN DEFAULT FALSE,
                    processing_time_ms INTEGER DEFAULT 0,
                    model_version TEXT DEFAULT '2.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX idx_detections_camera_id ON detections (camera_id)")
            cursor.execute("CREATE INDEX idx_detections_detected_at ON detections (detected_at)")
            cursor.execute("CREATE INDEX idx_detections_plate_text ON detections (plate_text)")
            
            cursor.execute("CREATE INDEX idx_universal_detections_camera_id ON universal_detections (camera_id)")
            cursor.execute("CREATE INDEX idx_universal_detections_detected_at ON universal_detections (detected_at)")
            cursor.execute("CREATE INDEX idx_universal_detections_object_type ON universal_detections (object_type)")
            
            # Create video recordings table
            cursor.execute("""
                CREATE TABLE video_recordings (
                    id TEXT PRIMARY KEY,
                    camera_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    duration_seconds REAL,
                    file_size_bytes INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (id)
                )
            """)
            
            conn.commit()
            logger.info("✅ Fresh database created with proper schema")
            
            # Verify tables were created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"📋 Created tables: {tables}")
            
        except Exception as e:
            logger.error(f"❌ Error creating database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def step_5_add_test_data(self):
        """Add minimal test data for development"""
        logger.info("📝 Step 5: Adding test data...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Add test camera
            cursor.execute("""
                INSERT INTO cameras (id, name, ip_address, port, connection_type, stream_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "camera_test_001",
                "Test Camera 1",
                "192.168.1.100",
                80,
                "http",
                "/video",
                "online"
            ))
            
            # Add a few test detections
            test_detections = [
                ("det_001", "camera_test_001", "ABC123", 0.95, "car", "2025-08-29 06:45:00"),
                ("det_002", "camera_test_001", "XYZ789", 0.87, "truck", "2025-08-29 06:46:00"),
                ("det_003", "camera_test_001", "TEST01", 0.92, "car", "2025-08-29 06:47:00")
            ]
            
            for detection in test_detections:
                cursor.execute("""
                    INSERT INTO detections (id, camera_id, plate_text, confidence, vehicle_type, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, detection)
            
            conn.commit()
            logger.info("✅ Added test data: 1 camera, 3 detections")
            
        except Exception as e:
            logger.error(f"❌ Error adding test data: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def step_6_verify_database(self):
        """Verify database is working properly"""
        logger.info("🔍 Step 6: Verifying database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Test basic queries
            cursor.execute("SELECT COUNT(*) FROM cameras")
            camera_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM detections")
            detection_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM universal_detections")
            universal_count = cursor.fetchone()[0]
            
            # Test foreign key relationship
            cursor.execute("""
                SELECT d.id, d.plate_text, c.name 
                FROM detections d 
                JOIN cameras c ON d.camera_id = c.id 
                LIMIT 1
            """)
            join_test = cursor.fetchone()
            
            logger.info(f"📊 Database verification:")
            logger.info(f"   - Cameras: {camera_count}")
            logger.info(f"   - Detections: {detection_count}")
            logger.info(f"   - Universal detections: {universal_count}")
            logger.info(f"   - Foreign key test: {'✅ PASS' if join_test else '❌ FAIL'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database verification failed: {e}")
            return False
        finally:
            conn.close()
            
    def run_fresh_start(self, keep_detection_samples=True):
        """Execute complete fresh start process"""
        logger.info("🚀 Starting Database Fresh Start Process")
        logger.info("=" * 50)
        
        try:
            self.step_1_backup_current_database()
            self.step_2_clean_database_files()
            self.step_3_clean_detection_files(keep_sample=keep_detection_samples)
            self.step_4_create_fresh_database()
            self.step_5_add_test_data()
            
            if self.step_6_verify_database():
                logger.info("=" * 50)
                logger.info("✅ DATABASE FRESH START COMPLETED SUCCESSFULLY!")
                logger.info("🎯 Next steps:")
                logger.info("   1. Restart services: python3 bin/start_lpr.py")
                logger.info("   2. Test endpoints: python3 test_endpoints.py")
                logger.info("   3. Check system health: python3 bin/check_services.py")
                return True
            else:
                logger.error("❌ Database verification failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fresh start process failed: {e}")
            return False

def main():
    """Main execution function"""
    print("🗑️  DATABASE FRESH START UTILITY")
    print("=" * 40)
    print("This will completely clean and rebuild the database.")
    print("⚠️  All existing detection data will be lost!")
    print("✅ Current database will be backed up first.")
    print()
    
    response = input("Continue with fresh start? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("❌ Fresh start cancelled by user")
        return False
        
    fresh_starter = DatabaseFreshStart()
    return fresh_starter.run_fresh_start()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)