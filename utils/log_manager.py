"""
Log Management System for 24/7 LPR Operations
Provides log rotation, cleanup, and disk space monitoring
"""
import os
import logging
import logging.handlers
import time
import shutil
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class LPRLogManager:
    """
    Centralized log management for LPR system with automatic rotation and cleanup
    """
    
    def __init__(self, 
                 log_dir: Optional[str] = None,
                 max_file_size: Optional[int] = None,
                 max_files_per_service: Optional[int] = None,
                 retention_days: Optional[int] = None,
                 disk_usage_threshold: Optional[float] = None):
        
        # Load from centralized config if available
        try:
            from config.app_config import get_config
            config = get_config()
            log_config = config.logging
            
            self.log_dir = Path(log_dir or log_config.log_dir)
            self.max_file_size = max_file_size or (log_config.max_file_size_mb * 1024 * 1024)
            self.max_files_per_service = max_files_per_service or log_config.max_files_per_service
            self.retention_days = retention_days or log_config.retention_days
            self.disk_usage_threshold = disk_usage_threshold or log_config.disk_usage_threshold
        except ImportError:
            # Fallback to defaults
            self.log_dir = Path(log_dir or "logs")
            self.max_file_size = max_file_size or (10 * 1024 * 1024)  # 10MB
            self.max_files_per_service = max_files_per_service or 5
            self.retention_days = retention_days or 7
            self.disk_usage_threshold = disk_usage_threshold or 0.85
        
        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)
        
        # Track active loggers
        self.active_loggers: Dict[str, logging.Logger] = {}
        
    def get_logger(self, service_name: str, level: int = logging.INFO) -> logging.Logger:
        """
        Get or create a logger for a service with automatic rotation
        """
        if service_name in self.active_loggers:
            return self.active_loggers[service_name]
            
        logger = logging.getLogger(f"lpr.{service_name}")
        logger.setLevel(level)
        
        # Clear any existing handlers
        logger.handlers.clear()
        logger.propagate = False
        
        # Create rotating file handler
        log_file = self.log_dir / f"{service_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size,
            backupCount=self.max_files_per_service,
            encoding='utf-8'
        )
        
        # Create console handler for errors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.active_loggers[service_name] = logger
        return logger
    
    def cleanup_old_logs(self) -> Dict[str, int]:
        """
        Clean up logs older than retention period
        Returns count of files removed per pattern
        """
        cleanup_stats = {}
        cutoff_time = time.time() - (self.retention_days * 24 * 3600)
        
        # Clean up timestamped log files (legacy format)
        for pattern in ['*_202*.log', '*.log.*']:
            files_removed = 0
            for log_file in self.log_dir.glob(pattern):
                try:
                    if log_file.stat().st_mtime < cutoff_time:
                        log_file.unlink()
                        files_removed += 1
                except (OSError, FileNotFoundError):
                    continue
            cleanup_stats[pattern] = files_removed
        
        return cleanup_stats
    
    def get_disk_usage(self) -> Dict[str, float]:
        """
        Get disk usage statistics for log directory
        """
        usage = shutil.disk_usage(self.log_dir)
        
        total_gb = usage.total / (1024**3)
        used_gb = usage.used / (1024**3)
        free_gb = usage.free / (1024**3)
        usage_percent = used_gb / total_gb
        
        return {
            'total_gb': round(total_gb, 2),
            'used_gb': round(used_gb, 2),
            'free_gb': round(free_gb, 2),
            'usage_percent': round(usage_percent, 3),
            'above_threshold': usage_percent > self.disk_usage_threshold
        }
    
    def get_log_stats(self) -> Dict[str, any]:
        """
        Get comprehensive logging statistics
        """
        stats = {
            'total_log_files': 0,
            'total_size_mb': 0,
            'services': {},
            'disk_usage': self.get_disk_usage(),
            'cleanup_recommended': False
        }
        
        for log_file in self.log_dir.glob('*.log*'):
            stats['total_log_files'] += 1
            size_mb = log_file.stat().st_size / (1024**2)
            stats['total_size_mb'] += size_mb
            
            # Extract service name
            service_name = log_file.stem.split('_')[0]
            if service_name not in stats['services']:
                stats['services'][service_name] = {
                    'file_count': 0,
                    'total_size_mb': 0
                }
            
            stats['services'][service_name]['file_count'] += 1
            stats['services'][service_name]['total_size_mb'] += size_mb
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        stats['cleanup_recommended'] = (
            stats['disk_usage']['above_threshold'] or 
            stats['total_log_files'] > 50 or
            stats['total_size_mb'] > 500
        )
        
        return stats
    
    def emergency_cleanup(self) -> Dict[str, int]:
        """
        Emergency cleanup when disk usage is critical
        Removes oldest 50% of log files
        """
        log_files = list(self.log_dir.glob('*.log*'))
        log_files.sort(key=lambda f: f.stat().st_mtime)
        
        files_to_remove = len(log_files) // 2
        removed_count = 0
        
        for log_file in log_files[:files_to_remove]:
            try:
                log_file.unlink()
                removed_count += 1
            except (OSError, FileNotFoundError):
                continue
        
        return {
            'emergency_cleanup': True,
            'files_removed': removed_count,
            'files_remaining': len(log_files) - removed_count
        }
    
    def monitor_and_cleanup(self) -> Dict[str, any]:
        """
        Comprehensive monitoring and cleanup operation
        """
        stats = self.get_log_stats()
        cleanup_results = {}
        
        # Regular cleanup
        cleanup_results['regular_cleanup'] = self.cleanup_old_logs()
        
        # Emergency cleanup if needed
        if stats['disk_usage']['above_threshold']:
            cleanup_results.update(self.emergency_cleanup())
        
        # Final stats after cleanup
        cleanup_results['final_stats'] = self.get_log_stats()
        cleanup_results['timestamp'] = datetime.now().isoformat()
        
        return cleanup_results


# Global log manager instance
log_manager = LPRLogManager()


def get_service_logger(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Convenience function to get a properly configured logger for any service
    """
    return log_manager.get_logger(service_name, level)


def cleanup_logs() -> Dict[str, any]:
    """
    Convenience function for manual log cleanup
    """
    return log_manager.monitor_and_cleanup()


if __name__ == "__main__":
    # CLI interface for log management
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            stats = log_manager.get_log_stats()
            print(f"Log Statistics:")
            print(f"  Total files: {stats['total_log_files']}")
            print(f"  Total size: {stats['total_size_mb']} MB")
            print(f"  Disk usage: {stats['disk_usage']['usage_percent']*100:.1f}%")
            print(f"  Cleanup recommended: {stats['cleanup_recommended']}")
            
        elif command == "cleanup":
            results = log_manager.monitor_and_cleanup()
            print("Log cleanup completed:")
            print(f"  Regular cleanup: {sum(results['regular_cleanup'].values())} files")
            if 'emergency_cleanup' in results:
                print(f"  Emergency cleanup: {results['files_removed']} files")
                
        elif command == "emergency":
            results = log_manager.emergency_cleanup()
            print(f"Emergency cleanup: {results['files_removed']} files removed")
            
        else:
            print("Usage: python log_manager.py [stats|cleanup|emergency]")
    else:
        print("LPR Log Manager - use 'stats', 'cleanup', or 'emergency'")