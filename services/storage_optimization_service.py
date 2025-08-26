#!/usr/bin/env python3
"""
Storage Optimization Service
Provides automated cleanup and retention management for LPR system storage.
Addresses critical storage capacity issues.
"""

import os
import sys
import sqlite3
import shutil
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class StorageStats:
    """Storage statistics for reporting"""
    total_size_gb: float
    used_size_gb: float
    available_size_gb: float
    usage_percentage: float
    cleanup_potential_gb: float
    
@dataclass
class CleanupResult:
    """Results of a cleanup operation"""
    files_deleted: int
    space_freed_mb: float
    errors: List[str]
    categories: Dict[str, int]

class StorageOptimizationService:
    """
    Comprehensive storage optimization and cleanup service
    """
    
    def __init__(self, config_path: str = "config/storage_config.json"):
        self.config_path = config_path
        self.base_path = Path(".")
        self.db_path = "data/license_plates.db"
        self.detections_path = Path("detections")
        self.logs_path = Path("logs")
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/storage_optimization.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self.load_config()
        
    def load_config(self) -> dict:
        """Load storage optimization configuration"""
        default_config = {
            "retention_policies": {
                "detection_images": {
                    "max_age_days": 7,
                    "max_count": 10000,
                    "cleanup_batch_size": 1000
                },
                "detection_records": {
                    "max_age_days": 30,
                    "archive_threshold_days": 90
                },
                "log_files": {
                    "max_age_days": 30,
                    "max_size_mb": 100
                },
                "database": {
                    "wal_checkpoint_interval": 3600,  # 1 hour
                    "vacuum_threshold_mb": 100
                }
            },
            "storage_limits": {
                "warning_threshold": 80.0,  # Percentage
                "critical_threshold": 90.0,
                "emergency_cleanup_threshold": 95.0
            },
            "cleanup_schedule": {
                "daily_cleanup_hour": 2,  # 2 AM
                "deep_cleanup_day": 0,  # Sunday
                "emergency_cleanup_enabled": True
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                return {**default_config, **config}
            else:
                # Create config file with defaults
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                self.logger.info(f"Created default storage config at {self.config_path}")
                return default_config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}, using defaults")
            return default_config
    
    def get_storage_stats(self) -> StorageStats:
        """Get comprehensive storage statistics"""
        try:
            # Get filesystem stats
            statvfs = os.statvfs('.')
            total_size = (statvfs.f_frsize * statvfs.f_blocks) / (1024**3)  # GB
            available_size = (statvfs.f_frsize * statvfs.f_available) / (1024**3)  # GB
            used_size = total_size - available_size
            usage_percentage = (used_size / total_size) * 100
            
            # Calculate cleanup potential
            cleanup_potential = 0.0
            
            # Detection images cleanup potential
            detection_images = self.count_old_detection_images()
            if detection_images['count'] > 0:
                cleanup_potential += detection_images['size_mb'] / 1024  # Convert to GB
            
            # Database cleanup potential
            db_stats = self.get_database_stats()
            cleanup_potential += db_stats['wal_size_mb'] / 1024  # WAL file
            
            return StorageStats(
                total_size_gb=total_size,
                used_size_gb=used_size,
                available_size_gb=available_size,
                usage_percentage=usage_percentage,
                cleanup_potential_gb=cleanup_potential
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return StorageStats(0, 0, 0, 0, 0)
    
    def count_old_detection_images(self, max_age_days: Optional[int] = None) -> Dict:
        """Count old detection images for cleanup estimation"""
        if max_age_days is None:
            max_age_days = self.config['retention_policies']['detection_images']['max_age_days']
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        old_files = {'count': 0, 'size_mb': 0.0}
        
        try:
            for image_dir in ['frames', 'plates']:
                dir_path = self.detections_path / image_dir
                if dir_path.exists():
                    for file_path in dir_path.glob('*.jpg'):
                        if file_path.stat().st_mtime < cutoff_timestamp:
                            old_files['count'] += 1
                            old_files['size_mb'] += file_path.stat().st_size / (1024*1024)
        except Exception as e:
            self.logger.error(f"Error counting old detection images: {e}")
        
        return old_files
    
    def get_database_stats(self) -> Dict:
        """Get database size and optimization stats"""
        stats = {'size_mb': 0, 'wal_size_mb': 0, 'record_count': 0}
        
        try:
            # Main database file size
            if os.path.exists(self.db_path):
                stats['size_mb'] = os.path.getsize(self.db_path) / (1024*1024)
            
            # WAL file size
            wal_path = f"{self.db_path}-wal"
            if os.path.exists(wal_path):
                stats['wal_size_mb'] = os.path.getsize(wal_path) / (1024*1024)
            
            # Record count from detections table
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM detections")
            stats['record_count'] = cursor.fetchone()[0]
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
        
        return stats
    
    async def cleanup_old_detection_images(self, max_age_days: Optional[int] = None, dry_run: bool = True) -> CleanupResult:
        """Clean up old detection images"""
        if max_age_days is None:
            max_age_days = self.config['retention_policies']['detection_images']['max_age_days']
        
        self.logger.info(f"Starting detection image cleanup (max_age: {max_age_days} days, dry_run: {dry_run})")
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        result = CleanupResult(
            files_deleted=0,
            space_freed_mb=0.0,
            errors=[],
            categories={'frames': 0, 'plates': 0}
        )\n        \n        try:\n            batch_size = self.config['retention_policies']['detection_images']['cleanup_batch_size']\n            \n            for image_dir in ['frames', 'plates']:\n                dir_path = self.detections_path / image_dir\n                if not dir_path.exists():\n                    continue\n                \n                files_to_delete = []\n                for file_path in dir_path.glob('*.jpg'):\n                    try:\n                        if file_path.stat().st_mtime < cutoff_timestamp:\n                            files_to_delete.append(file_path)\n                            \n                        # Process in batches to avoid memory issues\n                        if len(files_to_delete) >= batch_size:\n                            await self._process_file_batch(files_to_delete, result, image_dir, dry_run)\n                            files_to_delete.clear()\n                            \n                    except Exception as e:\n                        result.errors.append(f\"Error processing {file_path}: {e}\")\n                \n                # Process remaining files\n                if files_to_delete:\n                    await self._process_file_batch(files_to_delete, result, image_dir, dry_run)\n        \n        except Exception as e:\n            self.logger.error(f\"Error during detection image cleanup: {e}\")\n            result.errors.append(str(e))\n        \n        self.logger.info(\n            f\"Detection image cleanup complete: {result.files_deleted} files, \"\n            f\"{result.space_freed_mb:.2f} MB freed, {len(result.errors)} errors\"\n        )\n        \n        return result\n    \n    async def _process_file_batch(self, files: List[Path], result: CleanupResult, category: str, dry_run: bool):\n        \"\"\"Process a batch of files for deletion\"\"\"\n        for file_path in files:\n            try:\n                file_size_mb = file_path.stat().st_size / (1024*1024)\n                \n                if not dry_run:\n                    file_path.unlink()\n                \n                result.files_deleted += 1\n                result.space_freed_mb += file_size_mb\n                result.categories[category] += 1\n                \n                # Small delay to prevent overwhelming the filesystem\n                if result.files_deleted % 100 == 0:\n                    await asyncio.sleep(0.01)\n                    \n            except Exception as e:\n                result.errors.append(f\"Failed to delete {file_path}: {e}\")\n    \n    async def cleanup_old_database_records(self, max_age_days: Optional[int] = None, dry_run: bool = True) -> CleanupResult:\n        \"\"\"Clean up old detection records from database\"\"\"\n        if max_age_days is None:\n            max_age_days = self.config['retention_policies']['detection_records']['max_age_days']\n        \n        self.logger.info(f\"Starting database cleanup (max_age: {max_age_days} days, dry_run: {dry_run})\")\n        \n        result = CleanupResult(\n            files_deleted=0,\n            space_freed_mb=0.0,\n            errors=[],\n            categories={'detections': 0}\n        )\n        \n        try:\n            cutoff_date = datetime.now() - timedelta(days=max_age_days)\n            \n            conn = sqlite3.connect(self.db_path)\n            cursor = conn.cursor()\n            \n            # Count records to be deleted\n            cursor.execute(\n                \"SELECT COUNT(*) FROM detections WHERE timestamp < ?\",\n                (cutoff_date.isoformat(),)\n            )\n            old_count = cursor.fetchone()[0]\n            \n            if old_count > 0:\n                # Get database size before cleanup\n                db_size_before = os.path.getsize(self.db_path) / (1024*1024)\n                \n                if not dry_run:\n                    # Delete old records\n                    cursor.execute(\n                        \"DELETE FROM detections WHERE timestamp < ?\",\n                        (cutoff_date.isoformat(),)\n                    )\n                    \n                    # Vacuum to reclaim space\n                    cursor.execute(\"VACUUM\")\n                    conn.commit()\n                    \n                    # Calculate space saved\n                    db_size_after = os.path.getsize(self.db_path) / (1024*1024)\n                    result.space_freed_mb = db_size_before - db_size_after\n                \n                result.files_deleted = old_count\n                result.categories['detections'] = old_count\n            \n            conn.close()\n            \n        except Exception as e:\n            self.logger.error(f\"Error during database cleanup: {e}\")\n            result.errors.append(str(e))\n        \n        self.logger.info(\n            f\"Database cleanup complete: {result.files_deleted} records, \"\n            f\"{result.space_freed_mb:.2f} MB freed, {len(result.errors)} errors\"\n        )\n        \n        return result\n    \n    async def optimize_database(self, dry_run: bool = True) -> CleanupResult:\n        \"\"\"Optimize database performance and storage\"\"\"\n        self.logger.info(f\"Starting database optimization (dry_run: {dry_run})\")\n        \n        result = CleanupResult(\n            files_deleted=0,\n            space_freed_mb=0.0,\n            errors=[],\n            categories={'wal_checkpoint': 0, 'vacuum': 0}\n        )\n        \n        try:\n            conn = sqlite3.connect(self.db_path)\n            cursor = conn.cursor()\n            \n            # Get WAL size before optimization\n            wal_path = f\"{self.db_path}-wal\"\n            wal_size_before = 0\n            if os.path.exists(wal_path):\n                wal_size_before = os.path.getsize(wal_path) / (1024*1024)\n            \n            if not dry_run:\n                # WAL checkpoint to commit pending transactions\n                cursor.execute(\"PRAGMA wal_checkpoint(TRUNCATE)\")\n                result.categories['wal_checkpoint'] = 1\n                \n                # Optimize database\n                cursor.execute(\"PRAGMA optimize\")\n                \n                # Vacuum if database is large enough\n                db_stats = self.get_database_stats()\n                vacuum_threshold = self.config['retention_policies']['database']['vacuum_threshold_mb']\n                if db_stats['size_mb'] > vacuum_threshold:\n                    cursor.execute(\"VACUUM\")\n                    result.categories['vacuum'] = 1\n                \n                conn.commit()\n                \n                # Calculate space saved\n                wal_size_after = 0\n                if os.path.exists(wal_path):\n                    wal_size_after = os.path.getsize(wal_path) / (1024*1024)\n                \n                result.space_freed_mb = wal_size_before - wal_size_after\n            \n            conn.close()\n            \n        except Exception as e:\n            self.logger.error(f\"Error during database optimization: {e}\")\n            result.errors.append(str(e))\n        \n        self.logger.info(\n            f\"Database optimization complete: {result.space_freed_mb:.2f} MB freed, {len(result.errors)} errors\"\n        )\n        \n        return result\n    \n    async def cleanup_log_files(self, max_age_days: Optional[int] = None, dry_run: bool = True) -> CleanupResult:\n        \"\"\"Clean up old log files\"\"\"\n        if max_age_days is None:\n            max_age_days = self.config['retention_policies']['log_files']['max_age_days']\n        \n        self.logger.info(f\"Starting log file cleanup (max_age: {max_age_days} days, dry_run: {dry_run})\")\n        \n        cutoff_time = datetime.now() - timedelta(days=max_age_days)\n        cutoff_timestamp = cutoff_time.timestamp()\n        \n        result = CleanupResult(\n            files_deleted=0,\n            space_freed_mb=0.0,\n            errors=[],\n            categories={'log_files': 0}\n        )\n        \n        try:\n            if self.logs_path.exists():\n                for log_file in self.logs_path.glob('*.log*'):\n                    try:\n                        if log_file.stat().st_mtime < cutoff_timestamp:\n                            file_size_mb = log_file.stat().st_size / (1024*1024)\n                            \n                            if not dry_run:\n                                log_file.unlink()\n                            \n                            result.files_deleted += 1\n                            result.space_freed_mb += file_size_mb\n                            result.categories['log_files'] += 1\n                    \n                    except Exception as e:\n                        result.errors.append(f\"Error processing {log_file}: {e}\")\n        \n        except Exception as e:\n            self.logger.error(f\"Error during log cleanup: {e}\")\n            result.errors.append(str(e))\n        \n        self.logger.info(\n            f\"Log cleanup complete: {result.files_deleted} files, \"\n            f\"{result.space_freed_mb:.2f} MB freed, {len(result.errors)} errors\"\n        )\n        \n        return result\n    \n    async def comprehensive_cleanup(self, dry_run: bool = True) -> Dict[str, CleanupResult]:\n        \"\"\"Run comprehensive cleanup of all components\"\"\"\n        self.logger.info(f\"Starting comprehensive cleanup (dry_run: {dry_run})\")\n        \n        results = {}\n        \n        # 1. Clean up old detection images (highest impact)\n        results['detection_images'] = await self.cleanup_old_detection_images(dry_run=dry_run)\n        \n        # 2. Optimize database\n        results['database_optimization'] = await self.optimize_database(dry_run=dry_run)\n        \n        # 3. Clean up old database records\n        results['database_records'] = await self.cleanup_old_database_records(dry_run=dry_run)\n        \n        # 4. Clean up log files\n        results['log_files'] = await self.cleanup_log_files(dry_run=dry_run)\n        \n        # Summary\n        total_files = sum(r.files_deleted for r in results.values())\n        total_space = sum(r.space_freed_mb for r in results.values())\n        total_errors = sum(len(r.errors) for r in results.values())\n        \n        self.logger.info(\n            f\"Comprehensive cleanup complete: {total_files} files/records, \"\n            f\"{total_space:.2f} MB freed, {total_errors} errors\"\n        )\n        \n        return results\n    \n    def generate_cleanup_report(self, results: Dict[str, CleanupResult]) -> dict:\n        \"\"\"Generate a detailed cleanup report\"\"\"\n        total_files = sum(r.files_deleted for r in results.values())\n        total_space = sum(r.space_freed_mb for r in results.values())\n        total_errors = sum(len(r.errors) for r in results.values())\n        \n        report = {\n            'timestamp': datetime.now().isoformat(),\n            'summary': {\n                'total_files_deleted': total_files,\n                'total_space_freed_mb': total_space,\n                'total_space_freed_gb': total_space / 1024,\n                'total_errors': total_errors\n            },\n            'details': {},\n            'storage_stats_after': self.get_storage_stats().__dict__\n        }\n        \n        for category, result in results.items():\n            report['details'][category] = {\n                'files_deleted': result.files_deleted,\n                'space_freed_mb': result.space_freed_mb,\n                'errors': result.errors,\n                'categories': result.categories\n            }\n        \n        return report\n    \n    def should_run_emergency_cleanup(self) -> bool:\n        \"\"\"Check if emergency cleanup should be triggered\"\"\"\n        stats = self.get_storage_stats()\n        threshold = self.config['storage_limits']['emergency_cleanup_threshold']\n        \n        return (\n            stats.usage_percentage > threshold and \n            self.config['cleanup_schedule']['emergency_cleanup_enabled']\n        )\n    \n    def get_storage_health_status(self) -> str:\n        \"\"\"Get current storage health status\"\"\"\n        stats = self.get_storage_stats()\n        \n        if stats.usage_percentage < self.config['storage_limits']['warning_threshold']:\n            return 'healthy'\n        elif stats.usage_percentage < self.config['storage_limits']['critical_threshold']:\n            return 'warning'\n        elif stats.usage_percentage < self.config['storage_limits']['emergency_cleanup_threshold']:\n            return 'critical'\n        else:\n            return 'emergency'\n\n\nasync def main():\n    \"\"\"Main entry point for running storage optimization\"\"\"\n    import argparse\n    \n    parser = argparse.ArgumentParser(description='Storage Optimization Service')\n    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')\n    parser.add_argument('--images-only', action='store_true', help='Only clean detection images')\n    parser.add_argument('--db-only', action='store_true', help='Only optimize database')\n    parser.add_argument('--max-age', type=int, help='Override max age in days')\n    \n    args = parser.parse_args()\n    \n    service = StorageOptimizationService()\n    \n    # Show current storage stats\n    stats = service.get_storage_stats()\n    print(f\"\\n📊 Current Storage Status:\")\n    print(f\"   Total: {stats.total_size_gb:.2f} GB\")\n    print(f\"   Used: {stats.used_size_gb:.2f} GB ({stats.usage_percentage:.1f}%)\")\n    print(f\"   Available: {stats.available_size_gb:.2f} GB\")\n    print(f\"   Cleanup Potential: {stats.cleanup_potential_gb:.2f} GB\")\n    print(f\"   Health Status: {service.get_storage_health_status().upper()}\")\n    \n    if args.images_only:\n        results = {'detection_images': await service.cleanup_old_detection_images(args.max_age, args.dry_run)}\n    elif args.db_only:\n        results = {\n            'database_optimization': await service.optimize_database(args.dry_run),\n            'database_records': await service.cleanup_old_database_records(args.max_age, args.dry_run)\n        }\n    else:\n        results = await service.comprehensive_cleanup(args.dry_run)\n    \n    # Generate and display report\n    report = service.generate_cleanup_report(results)\n    \n    print(f\"\\n✅ Cleanup {'Preview' if args.dry_run else 'Complete'}:\")\n    print(f\"   Files/Records: {report['summary']['total_files_deleted']:,}\")\n    print(f\"   Space Freed: {report['summary']['total_space_freed_gb']:.2f} GB\")\n    print(f\"   Errors: {report['summary']['total_errors']}\")\n    \n    if args.dry_run:\n        print(f\"\\n💡 Run without --dry-run to actually perform cleanup\")\n    \n    # Save detailed report\n    report_path = f\"logs/storage_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json\"\n    os.makedirs('logs', exist_ok=True)\n    with open(report_path, 'w') as f:\n        json.dump(report, f, indent=2)\n    print(f\"📄 Detailed report saved to: {report_path}\")\n\n\nif __name__ == \"__main__\":\n    asyncio.run(main())"