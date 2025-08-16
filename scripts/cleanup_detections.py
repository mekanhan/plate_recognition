#!/usr/bin/env python3
"""
Detection Database Cleanup Script
Removes excessive detections and optimizes database for better performance
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DetectionCleaner:
    """Cleans up detection database to reduce bloat"""
    
    def __init__(self, db_path="data/license_plates.db"):
        self.db_path = Path(db_path)
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self):
        """Create backup before cleanup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"license_plates_backup_cleanup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
        
    def analyze_current_state(self):
        """Analyze current database state"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Basic stats
            cursor.execute("SELECT COUNT(*) FROM detections")
            total_detections = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(detected_at), MAX(detected_at) FROM detections")
            date_range = cursor.fetchone()
            
            # Confidence distribution
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN confidence < 0.3 THEN 1 ELSE 0 END) as very_low,
                    SUM(CASE WHEN confidence < 0.5 THEN 1 ELSE 0 END) as low,
                    SUM(CASE WHEN confidence >= 0.7 THEN 1 ELSE 0 END) as high,
                    AVG(confidence) as avg_confidence
                FROM detections
            """)
            conf_stats = cursor.fetchone()
            
            # Top duplicates
            cursor.execute("""
                SELECT plate_text, COUNT(*) as detections
                FROM detections 
                GROUP BY plate_text 
                HAVING COUNT(*) > 10
                ORDER BY detections DESC 
                LIMIT 5
            """)
            top_dupes = cursor.fetchall()
            
            # Database size
            db_size_mb = self.db_path.stat().st_size / 1024 / 1024
            
            logger.info(f"=== CURRENT STATE ANALYSIS ===")
            logger.info(f"Total detections: {total_detections:,}")
            logger.info(f"Date range: {date_range[0]} to {date_range[1]}")
            logger.info(f"Database size: {db_size_mb:.1f} MB")
            logger.info(f"Average confidence: {conf_stats[4]:.3f}")
            logger.info(f"Very low confidence (<0.3): {conf_stats[1]:,} ({conf_stats[1]/total_detections*100:.1f}%)")
            logger.info(f"Low confidence (<0.5): {conf_stats[2]:,} ({conf_stats[2]/total_detections*100:.1f}%)")
            logger.info(f"High confidence (≥0.7): {conf_stats[3]:,} ({conf_stats[3]/total_detections*100:.1f}%)")
            
            if top_dupes:
                logger.info("Top duplicate plates:")
                for plate, count in top_dupes:
                    logger.info(f"  {plate}: {count:,} detections")
                    
            return {
                'total_detections': total_detections,
                'db_size_mb': db_size_mb,
                'avg_confidence': conf_stats[4],
                'low_confidence_count': conf_stats[2]
            }
            
        finally:
            conn.close()
            
    def cleanup_old_data(self, keep_days=1):
        """Remove detections older than specified days"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Count records to be deleted
            cursor.execute("SELECT COUNT(*) FROM detections WHERE detected_at < ?", (cutoff_str,))
            old_count = cursor.fetchone()[0]
            
            if old_count > 0:
                logger.info(f"Deleting {old_count:,} detections older than {keep_days} days...")
                
                # Delete old detections
                cursor.execute("DELETE FROM detections WHERE detected_at < ?", (cutoff_str,))
                
                logger.info(f"✅ Deleted {old_count:,} old detections")
            else:
                logger.info("No old detections to delete")
                
            conn.commit()
            return old_count
            
        except Exception as e:
            logger.error(f"Error cleaning old data: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def cleanup_low_confidence(self, min_confidence=0.5):
        """Remove low confidence detections"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Count low confidence records
            cursor.execute("SELECT COUNT(*) FROM detections WHERE confidence < ?", (min_confidence,))
            low_conf_count = cursor.fetchone()[0]
            
            if low_conf_count > 0:
                logger.info(f"Deleting {low_conf_count:,} detections with confidence < {min_confidence}...")
                
                # Delete low confidence detections
                cursor.execute("DELETE FROM detections WHERE confidence < ?", (min_confidence,))
                
                logger.info(f"✅ Deleted {low_conf_count:,} low confidence detections")
            else:
                logger.info(f"No detections with confidence < {min_confidence}")
                
            conn.commit()
            return low_conf_count
            
        except Exception as e:
            logger.error(f"Error cleaning low confidence: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def cleanup_empty_plates(self):
        """Remove detections with empty or invalid plate text"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Count empty plates
            cursor.execute("""
                SELECT COUNT(*) FROM detections 
                WHERE plate_text = '' OR plate_text IS NULL OR LENGTH(plate_text) < 3
            """)
            empty_count = cursor.fetchone()[0]
            
            if empty_count > 0:
                logger.info(f"Deleting {empty_count:,} detections with empty/invalid plates...")
                
                # Delete empty plates
                cursor.execute("""
                    DELETE FROM detections 
                    WHERE plate_text = '' OR plate_text IS NULL OR LENGTH(plate_text) < 3
                """)
                
                logger.info(f"✅ Deleted {empty_count:,} empty/invalid plate detections")
            else:
                logger.info("No empty/invalid plates to delete")
                
            conn.commit()
            return empty_count
            
        except Exception as e:
            logger.error(f"Error cleaning empty plates: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def mark_duplicates(self, time_window_seconds=30):
        """Mark duplicate detections within time window"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            logger.info(f"Marking duplicates within {time_window_seconds} seconds...")
            
            # Mark duplicates - keep earliest detection
            cursor.execute(f"""
                UPDATE detections 
                SET duplicate_of = (
                    SELECT MIN(id) 
                    FROM detections d2 
                    WHERE d2.plate_text = detections.plate_text 
                    AND d2.camera_id = detections.camera_id
                    AND ABS(strftime('%s', d2.detected_at) - strftime('%s', detections.detected_at)) <= {time_window_seconds}
                    AND d2.id < detections.id
                )
                WHERE duplicate_of IS NULL
                AND EXISTS (
                    SELECT 1 FROM detections d3
                    WHERE d3.plate_text = detections.plate_text 
                    AND d3.camera_id = detections.camera_id
                    AND ABS(strftime('%s', d3.detected_at) - strftime('%s', detections.detected_at)) <= {time_window_seconds}
                    AND d3.id < detections.id
                )
            """)
            
            duplicates_marked = cursor.rowcount
            logger.info(f"✅ Marked {duplicates_marked:,} duplicate detections")
            
            conn.commit()
            return duplicates_marked
            
        except Exception as e:
            logger.error(f"Error marking duplicates: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def optimize_database(self):
        """Optimize database structure"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            logger.info("Optimizing database structure...")
            
            # Get size before
            cursor.execute("PRAGMA page_count")
            pages_before = cursor.fetchone()[0]
            
            # Vacuum and analyze
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            
            # Get size after
            cursor.execute("PRAGMA page_count")
            pages_after = cursor.fetchone()[0]
            
            pages_saved = pages_before - pages_after
            logger.info(f"✅ Database optimized: {pages_saved} pages reclaimed")
            
            return pages_saved
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            raise
        finally:
            conn.close()
            
    def run_full_cleanup(self, keep_days=1, min_confidence=0.5):
        """Run complete cleanup process"""
        logger.info("=== STARTING DETECTION CLEANUP ===")
        
        # Create backup
        backup_path = self.create_backup()
        
        # Analyze current state
        before_stats = self.analyze_current_state()
        
        try:
            # Cleanup phases
            old_deleted = self.cleanup_old_data(keep_days)
            low_conf_deleted = self.cleanup_low_confidence(min_confidence)
            empty_deleted = self.cleanup_empty_plates()
            duplicates_marked = self.mark_duplicates()
            
            # Optimize
            pages_saved = self.optimize_database()
            
            # Final analysis
            logger.info("\n=== CLEANUP RESULTS ===")
            after_stats = self.analyze_current_state()
            
            total_deleted = old_deleted + low_conf_deleted + empty_deleted
            reduction_pct = (total_deleted / before_stats['total_detections']) * 100
            size_reduction = before_stats['db_size_mb'] - after_stats['db_size_mb']
            
            logger.info(f"Detections deleted: {total_deleted:,} ({reduction_pct:.1f}%)")
            logger.info(f"Duplicates marked: {duplicates_marked:,}")
            logger.info(f"Database size: {before_stats['db_size_mb']:.1f} MB → {after_stats['db_size_mb']:.1f} MB (-{size_reduction:.1f} MB)")
            logger.info(f"Avg confidence improved: {before_stats['avg_confidence']:.3f} → {after_stats['avg_confidence']:.3f}")
            logger.info(f"Backup saved: {backup_path}")
            
            return {
                'deleted': total_deleted,
                'duplicates_marked': duplicates_marked,
                'size_reduction_mb': size_reduction,
                'backup_path': backup_path
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            logger.error(f"Restore from backup: {backup_path}")
            raise


def main():
    """Main cleanup entry point"""
    print("License Plate Detection Cleanup Tool")
    print("===================================\n")
    
    cleaner = DetectionCleaner()
    
    if not cleaner.db_path.exists():
        print(f"❌ Database not found: {cleaner.db_path}")
        return
        
    # Show current state
    print("Analyzing current database state...")
    stats = cleaner.analyze_current_state()
    
    print(f"\nCurrent state:")
    print(f"- {stats['total_detections']:,} total detections")
    print(f"- {stats['db_size_mb']:.1f} MB database size")
    print(f"- {stats['avg_confidence']:.3f} average confidence")
    
    # Confirm cleanup
    print("\nThis tool will:")
    print("1. Keep only last 24 hours of detections")
    print("2. Delete detections with confidence < 0.5")
    print("3. Remove empty/invalid plate texts")
    print("4. Mark duplicate detections")
    print("5. Optimize database structure")
    
    response = input("\nProceed with cleanup? (yes/no): ")
    
    if response.lower() == 'yes':
        results = cleaner.run_full_cleanup()
        print(f"\n✅ Cleanup completed successfully!")
        print(f"Deleted {results['deleted']:,} detections")
        print(f"Reduced database by {results['size_reduction_mb']:.1f} MB")
    else:
        print("\nCancelled. No changes made.")


if __name__ == "__main__":
    main()