#!/usr/bin/env python3
"""
Updated Database Improvement Plan
Tailored for current database state with 63K detections and existing indexes
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


class DatabaseImproverUpdated:
    """Updated database improvements for current system state"""
    
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
        
    def execute_phase1_missing_indexes(self):
        """Phase 1: Add missing performance indexes"""
        logger.info("Starting Phase 1: Missing Performance Indexes")
        
        backup = self.create_backup("phase1_indexes")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Check which indexes don't exist yet
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        existing_indexes = {row[0] for row in cursor.fetchall()}
        
        # Only add indexes that don't exist
        potential_indexes = [
            ("idx_det_camera_date_plate", 
             "CREATE INDEX IF NOT EXISTS idx_det_camera_date_plate ON detections(camera_id, detected_at DESC, plate_text)"),
            
            ("idx_det_confidence_filter", 
             "CREATE INDEX IF NOT EXISTS idx_det_confidence_filter ON detections(confidence DESC) WHERE confidence > 0.8"),
            
            ("idx_rec_date_range_lookup", 
             "CREATE INDEX IF NOT EXISTS idx_rec_date_range_lookup ON video_recordings(start_time, end_time)"),
            
            ("idx_rec_filename_lookup", 
             "CREATE INDEX IF NOT EXISTS idx_rec_filename_lookup ON video_recordings(filename)"),
            
            ("idx_rec_size_analysis", 
             "CREATE INDEX IF NOT EXISTS idx_rec_size_analysis ON video_recordings(file_size_bytes DESC, created_at)"),
            
            ("idx_det_duplicate_analysis", 
             "CREATE INDEX IF NOT EXISTS idx_det_duplicate_analysis ON detections(duplicate_of, detected_at) WHERE duplicate_of IS NOT NULL"),
            
            ("idx_camera_status_monitoring", 
             "CREATE INDEX IF NOT EXISTS idx_camera_status_monitoring ON cameras(status, updated_at DESC)")
        ]
        
        try:
            indexes_added = 0
            for idx_name, sql in potential_indexes:
                if idx_name not in existing_indexes:
                    logger.info(f"Creating missing index: {idx_name}")
                    cursor.execute(sql)
                    indexes_added += 1
                else:
                    logger.info(f"Index already exists: {idx_name}")
                    
            conn.commit()
            logger.info(f"✅ Phase 1 completed - Added {indexes_added} new indexes")
            
            # Analyze tables for query optimizer
            cursor.execute("ANALYZE")
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 1: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    def execute_phase2_add_useful_columns(self):
        """Phase 2: Add columns that would actually be useful"""
        logger.info("Starting Phase 2: Useful Missing Columns")
        
        backup = self.create_backup("phase2_columns")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Check existing columns first
        def get_existing_columns(table_name):
            cursor.execute(f"PRAGMA table_info({table_name})")
            return {row[1] for row in cursor.fetchall()}
        
        # Only add columns that would be genuinely useful
        useful_columns = [
            # Detection enhancements
            ("detections", "processing_time_ms", "INTEGER"),
            ("detections", "model_version", "VARCHAR(50)"),
            ("detections", "detection_zone", "VARCHAR(50)"),
            
            # Camera operational data
            ("cameras", "last_error", "TEXT"),
            ("cameras", "error_count", "INTEGER DEFAULT 0"),
            ("cameras", "uptime_percentage", "REAL DEFAULT 100.0"),
            ("cameras", "avg_detection_confidence", "REAL"),
            
            # Video recording enhancements
            ("video_recordings", "thumbnail_path", "VARCHAR(500)"),
            ("video_recordings", "is_corrupted", "BOOLEAN DEFAULT 0"),
            ("video_recordings", "processing_status", "VARCHAR(20) DEFAULT 'complete'"),
            ("video_recordings", "motion_detected", "BOOLEAN DEFAULT 0"),
        ]
        
        try:
            columns_added = 0
            for table, column, datatype in useful_columns:
                existing_columns = get_existing_columns(table)
                
                if column not in existing_columns:
                    logger.info(f"Adding useful column: {table}.{column}")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype}")
                    columns_added += 1
                else:
                    logger.info(f"Column already exists: {table}.{column}")
                    
            conn.commit()
            logger.info(f"✅ Phase 2 completed - Added {columns_added} new columns")
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 2: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    def execute_phase3_monitoring_tables(self):
        """Phase 3: Create monitoring tables that don't exist"""
        logger.info("Starting Phase 3: Missing Monitoring Tables")
        
        backup = self.create_backup("phase3_monitoring")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        # Only create tables that don't exist and would be useful
        monitoring_tables = {
            "system_health_log": """
            CREATE TABLE IF NOT EXISTS system_health_log (
                id VARCHAR(36) PRIMARY KEY,
                service_name VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                response_time_ms INTEGER,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON DEFAULT '{}'
            )
            """,
            
            "detection_performance_log": """
            CREATE TABLE IF NOT EXISTS detection_performance_log (
                id VARCHAR(36) PRIMARY KEY,
                camera_id VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                hour INTEGER NOT NULL,
                detections_count INTEGER DEFAULT 0,
                avg_processing_time_ms REAL,
                avg_confidence REAL,
                best_detection_confidence REAL,
                unique_plates_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(camera_id, date, hour)
            )
            """,
            
            "audit_log": """
            CREATE TABLE IF NOT EXISTS audit_log (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) DEFAULT 'system',
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id VARCHAR(36),
                old_value JSON,
                new_value JSON,
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        }
        
        # Indexes for monitoring tables
        monitoring_indexes = {
            "system_health_log": [
                "CREATE INDEX IF NOT EXISTS idx_health_service_time ON system_health_log(service_name, timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_health_status_time ON system_health_log(status, timestamp DESC)"
            ],
            "detection_performance_log": [
                "CREATE INDEX IF NOT EXISTS idx_perf_camera_date ON detection_performance_log(camera_id, date DESC)",
                "CREATE INDEX IF NOT EXISTS idx_perf_date_hour ON detection_performance_log(date DESC, hour)"
            ],
            "audit_log": [
                "CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_log(user_id, created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_action_time ON audit_log(action, created_at DESC)"
            ]
        }
        
        try:
            tables_created = 0
            for table_name, sql in monitoring_tables.items():
                if table_name not in existing_tables:
                    logger.info(f"Creating monitoring table: {table_name}")
                    cursor.execute(sql)
                    tables_created += 1
                    
                    # Create indexes for this table
                    if table_name in monitoring_indexes:
                        for idx_sql in monitoring_indexes[table_name]:
                            cursor.execute(idx_sql)
                else:
                    logger.info(f"Table already exists: {table_name}")
                    
            conn.commit()
            logger.info(f"✅ Phase 3 completed - Created {tables_created} new monitoring tables")
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 3: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    def execute_phase4_data_optimization(self):
        """Phase 4: Optimize existing data (63K detections)"""
        logger.info("Starting Phase 4: Data Optimization for 63K detections")
        
        backup = self.create_backup("phase4_optimization")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # 1. Find and mark duplicate detections (important with 63K records)
            logger.info("Analyzing duplicate detections...")
            cursor.execute("""
                UPDATE detections 
                SET duplicate_of = (
                    SELECT MIN(id) 
                    FROM detections d2 
                    WHERE d2.plate_text = detections.plate_text 
                    AND d2.camera_id = detections.camera_id
                    AND datetime(d2.detected_at) BETWEEN datetime(detections.detected_at, '-30 seconds') 
                        AND datetime(detections.detected_at, '+30 seconds')
                    AND d2.id < detections.id
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
            
            # 2. Update camera statistics based on actual data
            logger.info("Updating camera statistics...")
            cursor.execute("""
                UPDATE cameras 
                SET avg_detection_confidence = (
                    SELECT AVG(confidence) 
                    FROM detections 
                    WHERE detections.camera_id = cameras.camera_id
                    AND duplicate_of IS NULL
                )
            """)
            
            # 3. Find orphaned records
            logger.info("Checking for orphaned records...")
            cursor.execute("""
                SELECT COUNT(*) FROM detections 
                WHERE camera_id NOT IN (SELECT camera_id FROM cameras)
            """)
            orphaned_detections = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM video_recordings 
                WHERE camera_id NOT IN (SELECT camera_id FROM cameras)
            """)
            orphaned_recordings = cursor.fetchone()[0]
            
            logger.info(f"Found {orphaned_detections} orphaned detections, {orphaned_recordings} orphaned recordings")
            
            # 4. Clean up old temporary data if any
            logger.info("Cleaning up temporary data...")
            cursor.execute("DELETE FROM detections WHERE plate_text = '' OR plate_text IS NULL")
            empty_plates = cursor.rowcount
            logger.info(f"Removed {empty_plates} detections with empty plates")
            
            # 5. Update video recording statistics
            logger.info("Updating video recording statistics...")
            cursor.execute("""
                UPDATE video_recordings 
                SET detection_count = (
                    SELECT COUNT(*) 
                    FROM detections 
                    WHERE detections.video_clip_id = video_recordings.id
                ),
                has_detections = (
                    SELECT COUNT(*) > 0
                    FROM detections 
                    WHERE detections.video_clip_id = video_recordings.id
                )
            """)
            
            # 6. Optimize database
            logger.info("Optimizing database structure...")
            conn.commit()
            
            # Get size before optimization
            cursor.execute("PRAGMA page_count")
            pages_before = cursor.fetchone()[0]
            
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            
            # Get size after optimization
            cursor.execute("PRAGMA page_count")
            pages_after = cursor.fetchone()[0]
            
            pages_saved = pages_before - pages_after
            logger.info(f"Database optimized: {pages_saved} pages reclaimed")
            
            logger.info("✅ Phase 4 completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 4: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    def generate_performance_report(self):
        """Generate a performance-focused report"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        report = {
            "database_size_mb": round(self.db_path.stat().st_size / 1024 / 1024, 2),
            "tables": {},
            "indexes": [],
            "performance_stats": {},
            "recommendations": []
        }
        
        try:
            # Get table row counts
            important_tables = ['cameras', 'detections', 'video_recordings', 'daily_summaries']
            for table in important_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    report["tables"][table] = cursor.fetchone()[0]
                except:
                    report["tables"][table] = "error"
            
            # Get index count
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            report["indexes"] = cursor.fetchone()[0]
            
            # Performance statistics
            cursor.execute("SELECT COUNT(*) FROM detections WHERE duplicate_of IS NOT NULL")
            report["performance_stats"]["duplicate_detections"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(confidence) FROM detections WHERE duplicate_of IS NULL")
            avg_conf = cursor.fetchone()[0]
            report["performance_stats"]["avg_confidence"] = round(avg_conf, 3) if avg_conf else 0
            
            cursor.execute("SELECT COUNT(DISTINCT plate_text) FROM detections WHERE duplicate_of IS NULL")
            report["performance_stats"]["unique_plates"] = cursor.fetchone()[0]
            
            # Recommendations based on actual data
            detections_count = report["tables"].get("detections", 0)
            
            if detections_count > 50000:
                report["recommendations"].append(f"Large detection table ({detections_count:,} records) - consider archiving old data")
            
            if report["performance_stats"]["duplicate_detections"] > detections_count * 0.1:
                report["recommendations"].append("High duplicate detection rate - review detection logic")
            
            if report["performance_stats"]["avg_confidence"] < 0.8:
                report["recommendations"].append("Low average confidence - consider tuning detection parameters")
                
            if report["database_size_mb"] > 500:
                report["recommendations"].append("Large database size - consider implementing data retention policies")
                
        finally:
            conn.close()
            
        return report
        
    def run_targeted_improvements(self):
        """Execute targeted improvements for current database state"""
        phases = [
            ("Phase 1: Missing Performance Indexes", self.execute_phase1_missing_indexes),
            ("Phase 2: Useful Missing Columns", self.execute_phase2_add_useful_columns),
            ("Phase 3: Missing Monitoring Tables", self.execute_phase3_monitoring_tables),
            ("Phase 4: Data Optimization", self.execute_phase4_data_optimization)
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
        logger.info("PERFORMANCE REPORT")
        logger.info(f"{'='*60}")
        
        report = self.generate_performance_report()
        logger.info(f"Database size: {report['database_size_mb']} MB")
        logger.info(f"Total indexes: {report['indexes']}")
        
        logger.info("\nTable row counts:")
        for table, count in report['tables'].items():
            logger.info(f"  - {table}: {count:,} rows")
            
        logger.info("\nPerformance statistics:")
        for stat, value in report['performance_stats'].items():
            logger.info(f"  - {stat}: {value}")
            
        if report['recommendations']:
            logger.info("\n📋 Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"  - {rec}")
                
        logger.info("\n✅ All targeted improvements completed!")
        return True


def main():
    """Main entry point for updated improvement plan"""
    print("Updated License Plate Database Improvement Tool")
    print("==============================================\n")
    
    improver = DatabaseImproverUpdated()
    
    # Check if database exists
    if not improver.db_path.exists():
        print(f"❌ Database not found at {improver.db_path}")
        return
        
    # Show current state
    report = improver.generate_performance_report()
    print(f"Current database size: {report['database_size_mb']} MB")
    print(f"Detection records: {report['tables'].get('detections', 0):,}")
    print(f"Video recordings: {report['tables'].get('video_recordings', 0):,}")
    print(f"Existing indexes: {report['indexes']}")
    
    if report['performance_stats']['duplicate_detections'] > 0:
        print(f"Duplicate detections: {report['performance_stats']['duplicate_detections']:,}")
    
    # Confirm before proceeding
    print("\nThis updated tool will:")
    print("1. Add missing performance indexes (only if needed)")
    print("2. Add useful columns for monitoring and features")
    print("3. Create monitoring tables for system health")
    print("4. Optimize your 63K detection records")
    print("5. Mark duplicate detections and update statistics")
    
    response = input("\nProceed with targeted improvements? (yes/no): ")
    
    if response.lower() == 'yes':
        success = improver.run_targeted_improvements()
        
        if success:
            print("\n✅ Database improvements completed successfully!")
            print(f"Backups saved in: {improver.backup_dir}")
        else:
            print("\n❌ Improvements failed. Check logs for details.")
    else:
        print("\nCancelled. No changes were made.")


if __name__ == "__main__":
    main()