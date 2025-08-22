#!/usr/bin/env python3
"""
Database Maintenance Utilities
Provides automated database maintenance, cleanup, and monitoring
"""
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_config import db_config
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMaintenance:
    """Database maintenance operations"""
    
    def __init__(self):
        self.db = db_config
        
    async def cleanup_old_detections(self, days: int = 30) -> int:
        """Remove detection records older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            async with self.db.get_session() as session:
                # Count records to delete
                result = await session.execute(
                    text("SELECT COUNT(*) FROM detections WHERE timestamp < :cutoff"),
                    {"cutoff": cutoff_date}
                )
                count = result.scalar()
                
                if count > 0:
                    # Delete old records
                    await session.execute(
                        text("DELETE FROM detections WHERE timestamp < :cutoff"),
                        {"cutoff": cutoff_date}
                    )
                    await session.commit()
                    logger.info(f"Deleted {count} detection records older than {days} days")
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old detections: {e}")
            raise
    
    async def cleanup_orphaned_recordings(self) -> int:
        """Remove recording records without corresponding files"""
        try:
            orphaned_count = 0
            
            async with self.db.get_session() as session:
                # Get all recording records
                result = await session.execute(
                    text("SELECT id, file_path FROM video_recordings")
                )
                recordings = result.fetchall()
                
                for record_id, file_path in recordings:
                    # Check if file exists
                    if file_path and not os.path.exists(file_path):
                        # Delete orphaned record
                        await session.execute(
                            text("DELETE FROM video_recordings WHERE id = :id"),
                            {"id": record_id}
                        )
                        orphaned_count += 1
                
                if orphaned_count > 0:
                    await session.commit()
                    logger.info(f"Removed {orphaned_count} orphaned recording records")
                
                return orphaned_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned recordings: {e}")
            raise
    
    async def update_statistics(self) -> Dict[str, Any]:
        """Update database statistics and return summary"""
        try:
            stats = {}
            
            async with self.db.get_session() as session:
                # Get table statistics
                tables = ['cameras', 'detections', 'video_recordings', 'daily_summaries']
                
                for table in tables:
                    try:
                        result = await session.execute(
                            text(f"SELECT COUNT(*) FROM {table}")
                        )
                        stats[f"{table}_count"] = result.scalar()
                    except:
                        stats[f"{table}_count"] = 0
                
                # Get database size
                if os.path.exists(self.db.db_path):
                    stats['database_size_mb'] = os.path.getsize(self.db.db_path) / (1024 * 1024)
                
                # Get date range of data
                try:
                    result = await session.execute(
                        text("SELECT MIN(timestamp), MAX(timestamp) FROM detections")
                    )
                    min_date, max_date = result.first()
                    stats['oldest_detection'] = min_date
                    stats['newest_detection'] = max_date
                except:
                    pass
                
                # Update SQLite statistics
                await session.execute(text("ANALYZE"))
                
                logger.info(f"Database statistics updated: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
            raise
    
    async def check_integrity(self) -> bool:
        """Run integrity check on database"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute(text("PRAGMA integrity_check"))
                check_result = result.scalar()
                
                if check_result == 'ok':
                    logger.info("Database integrity check passed")
                    return True
                else:
                    logger.error(f"Database integrity check failed: {check_result}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to check database integrity: {e}")
            raise
    
    async def rebuild_indexes(self):
        """Rebuild database indexes for better performance"""
        try:
            async with self.db.get_session() as session:
                # Get all indexes
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='index'")
                )
                indexes = [row[0] for row in result.fetchall()]
                
                # Rebuild each index
                for index in indexes:
                    if not index.startswith('sqlite_'):  # Skip internal indexes
                        await session.execute(text(f"REINDEX {index}"))
                        logger.info(f"Rebuilt index: {index}")
                
                await session.commit()
                logger.info(f"Rebuilt {len(indexes)} indexes")
                
        except Exception as e:
            logger.error(f"Failed to rebuild indexes: {e}")
            raise
    
    async def full_maintenance(self, backup: bool = True) -> Dict[str, Any]:
        """Run full maintenance routine"""
        logger.info("Starting full database maintenance")
        results = {
            'start_time': datetime.now(),
            'backup_path': None,
            'integrity_check': False,
            'detections_cleaned': 0,
            'orphaned_cleaned': 0,
            'statistics': {},
            'optimized': False,
            'errors': []
        }
        
        try:
            # 1. Create backup if requested
            if backup:
                try:
                    results['backup_path'] = await self.db.backup()
                except Exception as e:
                    results['errors'].append(f"Backup failed: {e}")
            
            # 2. Check integrity
            try:
                results['integrity_check'] = await self.check_integrity()
            except Exception as e:
                results['errors'].append(f"Integrity check failed: {e}")
            
            # 3. Cleanup old data
            try:
                results['detections_cleaned'] = await self.cleanup_old_detections()
            except Exception as e:
                results['errors'].append(f"Detection cleanup failed: {e}")
            
            # 4. Cleanup orphaned records
            try:
                results['orphaned_cleaned'] = await self.cleanup_orphaned_recordings()
            except Exception as e:
                results['errors'].append(f"Orphaned cleanup failed: {e}")
            
            # 5. Rebuild indexes
            try:
                await self.rebuild_indexes()
            except Exception as e:
                results['errors'].append(f"Index rebuild failed: {e}")
            
            # 6. Update statistics
            try:
                results['statistics'] = await self.update_statistics()
            except Exception as e:
                results['errors'].append(f"Statistics update failed: {e}")
            
            # 7. Optimize database
            try:
                await self.db.optimize()
                results['optimized'] = True
            except Exception as e:
                results['errors'].append(f"Optimization failed: {e}")
            
            results['end_time'] = datetime.now()
            results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
            
            logger.info(f"Database maintenance completed in {results['duration']:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
            results['errors'].append(str(e))
        
        return results

async def main():
    """Main entry point for maintenance script"""
    parser = argparse.ArgumentParser(description='Database Maintenance Utility')
    parser.add_argument('--cleanup-days', type=int, default=30,
                       help='Delete detections older than N days')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup creation')
    parser.add_argument('--check-only', action='store_true',
                       help='Only run integrity check')
    parser.add_argument('--health', action='store_true',
                       help='Show database health status')
    
    args = parser.parse_args()
    
    maintenance = DatabaseMaintenance()
    
    try:
        if args.health:
            # Show health status
            health = await db_config.health_check()
            print("\n📊 DATABASE HEALTH STATUS")
            print("=" * 50)
            for key, value in health.items():
                if key != 'error':
                    print(f"{key}: {value}")
            if health.get('error'):
                print(f"❌ Error: {health['error']}")
            
        elif args.check_only:
            # Run integrity check only
            result = await maintenance.check_integrity()
            if result:
                print("✅ Database integrity check passed")
            else:
                print("❌ Database integrity check failed")
                sys.exit(1)
        
        else:
            # Run full maintenance
            results = await maintenance.full_maintenance(backup=not args.no_backup)
            
            print("\n🔧 DATABASE MAINTENANCE REPORT")
            print("=" * 50)
            print(f"Duration: {results.get('duration', 0):.2f} seconds")
            print(f"Integrity: {'✅ Passed' if results['integrity_check'] else '❌ Failed'}")
            print(f"Detections cleaned: {results['detections_cleaned']}")
            print(f"Orphaned records cleaned: {results['orphaned_cleaned']}")
            print(f"Database optimized: {'✅' if results['optimized'] else '❌'}")
            
            if results['backup_path']:
                print(f"Backup saved: {results['backup_path']}")
            
            if results['statistics']:
                print("\n📈 Statistics:")
                for key, value in results['statistics'].items():
                    print(f"  {key}: {value}")
            
            if results['errors']:
                print("\n❌ Errors encountered:")
                for error in results['errors']:
                    print(f"  - {error}")
            
    except Exception as e:
        logger.error(f"Maintenance script failed: {e}")
        sys.exit(1)
    
    finally:
        await db_config.close()

if __name__ == "__main__":
    asyncio.run(main())