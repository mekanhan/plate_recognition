#!/usr/bin/env python3
"""
Database Improvement Action Plan
Execute improvements in phases to ensure system stability
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseImprover:
    """Manages database improvements in phases"""
    
    def __init__(self, db_path="data/license_plates.db"):
        self.db_path = Path(db_path)
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, phase_name):
        """Create a backup before making changes"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"license_plates_backup_{phase_name}_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
        
    def execute_phase1_critical_indexes(self):
        """Phase 1: Add critical missing indexes"""
        logger.info("Starting Phase 1: Critical Indexes")
        
        backup = self.create_backup("phase1_indexes")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Critical indexes for performance
        indexes = [
            # Detection performance
            ("idx_det_camera_date_plate", 
             "CREATE INDEX IF NOT EXISTS idx_det_camera_date_plate ON detections(camera_id, detected_at DESC, plate_text)"),
            
            ("idx_det_best_shots", 
             "CREATE INDEX IF NOT EXISTS idx_det_best_shots ON detections(is_best_shot, detected_at DESC) WHERE is_best_shot = 1"),
            
            ("idx_det_group_id", 
             "CREATE INDEX IF NOT EXISTS idx_det_group_id ON detections(group_id)"),
            
            ("idx_det_plate_search", 
             "CREATE INDEX IF NOT EXISTS idx_det_plate_search ON detections(plate_text, detected_at DESC)"),
            
            # Recording performance
            ("idx_rec_camera_date", 
             "CREATE INDEX IF NOT EXISTS idx_rec_camera_date ON video_recordings(camera_id, start_time DESC)"),
            
            ("idx_rec_date_range", 
             "CREATE INDEX IF NOT EXISTS idx_rec_date_range ON video_recordings(start_time, end_time)"),
            
            ("idx_rec_filename", 
             "CREATE INDEX IF NOT EXISTS idx_rec_filename ON video_recordings(filename)"),
            
            # Daily summaries
            ("idx_summary_lookup", 
             "CREATE INDEX IF NOT EXISTS idx_summary_lookup ON daily_summaries(camera_id, date DESC)"),
            
            # Camera status
            ("idx_camera_status", 
             "CREATE INDEX IF NOT EXISTS idx_camera_status ON cameras(status, camera_id)")
        ]
        
        try:
            for idx_name, sql in indexes:
                logger.info(f"Creating index: {idx_name}")
                cursor.execute(sql)
                
            conn.commit()
            logger.info("✅ Phase 1 completed successfully")
            
            # Analyze tables for query optimizer
            cursor.execute("ANALYZE")
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 1: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    def execute_phase2_add_missing_columns(self):
        """Phase 2: Add missing columns for features"""
        logger.info("Starting Phase 2: Missing Columns")
        
        backup = self.create_backup("phase2_columns")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Columns to add
        alterations = [
            # Detection enhancements
            ("detections", "detection_zone", "VARCHAR(50)"),
            ("detections", "processing_time_ms", "INTEGER"),
            ("detections", "model_version", "VARCHAR(50)"),
            
            # Camera enhancements
            ("cameras", "tags", "JSON DEFAULT '[]'"),
            ("cameras", "last_error", "TEXT"),
            ("cameras", "total_detections", "INTEGER DEFAULT 0"),
            ("cameras", "total_recordings", "INTEGER DEFAULT 0"),
            
            # Recording enhancements
            ("video_recordings", "thumbnail_path", "VARCHAR(500)"),
            ("video_recordings", "is_corrupted", "BOOLEAN DEFAULT 0"),
            ("video_recordings", "processing_status", "VARCHAR(20) DEFAULT 'complete'")
        ]
        
        try:
            for table, column, datatype in alterations:
                # Check if column exists
                cursor.execute(f"PRAGMA table_info({table})")
                columns = {row[1] for row in cursor.fetchall()}
                
                if column not in columns:
                    logger.info(f"Adding column: {table}.{column}")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype}")
                else:
                    logger.info(f"Column already exists: {table}.{column}")
                    
            conn.commit()
            logger.info("✅ Phase 2 completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 2: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    def execute_phase3_create_new_tables(self):
        """Phase 3: Create new monitoring and analytics tables"""
        logger.info("Starting Phase 3: New Tables")
        
        backup = self.create_backup("phase3_tables")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        new_tables = [
            # System health monitoring
            """
            CREATE TABLE IF NOT EXISTS system_health (
                id VARCHAR(36) PRIMARY KEY,
                service_name VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                last_heartbeat TIMESTAMP NOT NULL,
                error_count INTEGER DEFAULT 0,
                metadata JSON DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Storage statistics
            """
            CREATE TABLE IF NOT EXISTS storage_statistics (
                id VARCHAR(36) PRIMARY KEY,
                date DATE NOT NULL,
                camera_id VARCHAR(50),
                recordings_count INTEGER DEFAULT 0,
                recordings_size_mb REAL DEFAULT 0,
                detections_count INTEGER DEFAULT 0,
                detections_size_mb REAL DEFAULT 0,
                avg_segment_size_mb REAL,
                avg_detection_size_kb REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, camera_id)
            )
            """,
            
            # Audit log
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id VARCHAR(36),
                old_value JSON,
                new_value JSON,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Detection analytics cache
            """
            CREATE TABLE IF NOT EXISTS detection_analytics (
                id VARCHAR(36) PRIMARY KEY,
                date DATE NOT NULL,
                camera_id VARCHAR(50),
                hour INTEGER,
                total_detections INTEGER DEFAULT 0,
                unique_plates INTEGER DEFAULT 0,
                avg_confidence REAL,
                top_plates JSON DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, camera_id, hour)
            )
            """
        ]
        
        # Indexes for new tables
        new_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_health_service_time ON system_health(service_name, last_heartbeat)",
            "CREATE INDEX IF NOT EXISTS idx_storage_date ON storage_statistics(date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_log(user_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_date ON detection_analytics(date DESC, camera_id)"
        ]
        
        try:
            # Create tables
            for sql in new_tables:
                table_name = sql.split("EXISTS")[1].split("(")[0].strip()
                logger.info(f"Creating table: {table_name}")
                cursor.execute(sql)
                
            # Create indexes
            for sql in new_indexes:
                idx_name = sql.split("EXISTS")[1].split("ON")[0].strip()
                logger.info(f"Creating index: {idx_name}")
                cursor.execute(sql)
                
            conn.commit()
            logger.info("✅ Phase 3 completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 3: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    def execute_phase4_data_cleanup(self):
        """Phase 4: Clean up and optimize data"""
        logger.info("Starting Phase 4: Data Cleanup")
        
        backup = self.create_backup("phase4_cleanup")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Remove orphaned detections
            logger.info("Removing orphaned detections...")
            cursor.execute("""
                DELETE FROM detections 
                WHERE camera_id NOT IN (SELECT camera_id FROM cameras)
            """)
            orphaned = cursor.rowcount
            logger.info(f"Removed {orphaned} orphaned detections")
            
            # Mark duplicate detections
            logger.info("Identifying duplicate detections...")
            cursor.execute("""
                UPDATE detections 
                SET duplicate_of = (
                    SELECT MIN(id) 
                    FROM detections d2 
                    WHERE d2.plate_text = detections.plate_text 
                    AND d2.camera_id = detections.camera_id
                    AND datetime(d2.detected_at) BETWEEN datetime(detections.detected_at, '-30 seconds') 
                        AND datetime(detections.detected_at, '+30 seconds')
                    AND d2.id != detections.id
                )
                WHERE duplicate_of IS NULL
                AND EXISTS (
                    SELECT 1 FROM detections d3
                    WHERE d3.plate_text = detections.plate_text 
                    AND d3.camera_id = detections.camera_id
                    AND datetime(d3.detected_at) BETWEEN datetime(detections.detected_at, '-30 seconds') 
                        AND datetime(detections.detected_at, '+30 seconds')
                    AND d3.id < detections.id
                )
            """)
            duplicates_marked = cursor.rowcount
            logger.info(f"Marked {duplicates_marked} duplicate detections")
            
            # Update camera statistics
            logger.info("Updating camera statistics...")
            cursor.execute("""
                UPDATE cameras 
                SET total_detections = (
                    SELECT COUNT(*) FROM detections 
                    WHERE detections.camera_id = cameras.camera_id
                ),
                total_recordings = (
                    SELECT COUNT(*) FROM video_recordings 
                    WHERE video_recordings.camera_id = cameras.camera_id
                )
            """)
            
            # Vacuum and analyze
            logger.info("Optimizing database...")
            conn.commit()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            
            logger.info("✅ Phase 4 completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 4: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    def generate_health_report(self):
        """Generate a database health report"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        report = {
            "database_size_mb": round(self.db_path.stat().st_size / 1024 / 1024, 2),
            "tables": {},
            "indexes": [],
            "recommendations": []
        }
        
        try:
            # Get table statistics
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            for (table_name,) in cursor.fetchall():
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                report["tables"][table_name] = count
                
            # Get index information
            cursor.execute("""
                SELECT name, tbl_name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """)
            
            for idx in cursor.fetchall():
                report["indexes"].append(f"{idx[1]}.{idx[0]}")
                
            # Generate recommendations
            if report["database_size_mb"] > 1000:
                report["recommendations"].append("Consider archiving old detections")
                
            if report["tables"].get("detections", 0) > 100000:
                report["recommendations"].append("Large detection table - ensure indexes are optimized")
                
            # Check for missing indexes
            expected_indexes = [
                "detections.idx_det_camera_date_plate",
                "video_recordings.idx_rec_camera_date",
                "cameras.idx_camera_status"
            ]
            
            for expected in expected_indexes:
                if expected not in report["indexes"]:
                    report["recommendations"].append(f"Missing recommended index: {expected}")
                    
        finally:
            conn.close()
            
        return report
        
    def run_all_phases(self):
        """Execute all improvement phases"""
        phases = [
            ("Phase 1: Critical Indexes", self.execute_phase1_critical_indexes),
            ("Phase 2: Missing Columns", self.execute_phase2_add_missing_columns),
            ("Phase 3: New Tables", self.execute_phase3_create_new_tables),
            ("Phase 4: Data Cleanup", self.execute_phase4_data_cleanup)
        ]
        
        for phase_name, phase_func in phases:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Executing {phase_name}")
                logger.info(f"{'='*60}")
                phase_func()
                
            except Exception as e:
                logger.error(f"Failed at {phase_name}: {e}")
                logger.error("Stopping execution. Please restore from backup if needed.")
                return False
                
        # Generate final report
        logger.info(f"\n{'='*60}")
        logger.info("FINAL HEALTH REPORT")
        logger.info(f"{'='*60}")
        
        report = self.generate_health_report()
        logger.info(f"Database size: {report['database_size_mb']} MB")
        logger.info(f"Total tables: {len(report['tables'])}")
        logger.info(f"Total indexes: {len(report['indexes'])}")
        
        logger.info("\nTable row counts:")
        for table, count in sorted(report['tables'].items()):
            logger.info(f"  - {table}: {count:,} rows")
            
        if report['recommendations']:
            logger.info("\n📋 Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"  - {rec}")
                
        logger.info("\n✅ All improvements completed successfully!")
        return True


def main():
    """Main entry point"""
    print("License Plate Database Improvement Tool")
    print("=====================================\n")
    
    improver = DatabaseImprover()
    
    # Check if database exists
    if not improver.db_path.exists():
        print(f"❌ Database not found at {improver.db_path}")
        return
        
    # Show current state
    report = improver.generate_health_report()
    print(f"Current database size: {report['database_size_mb']} MB")
    print(f"Tables: {len(report['tables'])}")
    print(f"Indexes: {len(report['indexes'])}")
    
    # Confirm before proceeding
    print("\nThis tool will:")
    print("1. Create a backup of your database")
    print("2. Add performance-critical indexes")
    print("3. Add missing columns for new features")
    print("4. Create new monitoring tables")
    print("5. Clean up orphaned data")
    print("6. Optimize the database")
    
    response = input("\nProceed with improvements? (yes/no): ")
    
    if response.lower() == 'yes':
        success = improver.run_all_phases()
        
        if success:
            print("\n✅ Database improvements completed successfully!")
            print(f"Backups saved in: {improver.backup_dir}")
        else:
            print("\n❌ Improvements failed. Check logs for details.")
    else:
        print("\nCancelled. No changes were made.")


if __name__ == "__main__":
    main()
