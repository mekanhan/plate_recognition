"""
Comprehensive Media Storage Retention Manager for LPR System
Handles automated cleanup, retention policies, and storage monitoring for 24/7 operations
"""
import asyncio
import logging
import psutil
import time
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

try:
    from config.app_config import get_config
    from utils.log_manager import get_service_logger
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


@dataclass
class RetentionPolicy:
    """Defines retention policy for a storage directory"""
    path: str
    max_age_days: int = 30
    max_size_gb: float = 50.0
    emergency_cleanup_threshold: float = 0.95  # 95%
    cleanup_threshold: float = 0.85  # 85%
    min_free_space_gb: float = 5.0
    file_patterns: List[str] = field(default_factory=lambda: ["*"])
    priority: int = 1  # Higher priority = cleaned first


@dataclass
class StorageStats:
    """Storage statistics for a directory"""
    path: str
    total_size_bytes: int
    total_size_gb: float
    file_count: int
    oldest_file_age_days: int
    newest_file_age_days: int
    usage_percentage: float
    requires_cleanup: bool
    priority: int = 1


class MediaRetentionManager:
    """
    Comprehensive media storage retention manager with automated cleanup
    """
    
    def __init__(self):
        if HAS_CONFIG:
            self.config = get_config()
            self.logger = get_service_logger('media_retention')
        else:
            self.config = None
            self.logger = logging.getLogger('media_retention')
        
        # Initialize retention policies from config or defaults
        self.policies = self._initialize_retention_policies()
        
        # Tracking stats
        self.running = False
        self.last_cleanup = {}
        self.cleanup_stats = {
            'total_cleanups': 0,
            'total_files_deleted': 0,
            'total_bytes_freed': 0,
            'last_emergency_cleanup': None
        }
        
        # Cleanup intervals (seconds)
        self.check_interval = 3600  # 1 hour
        self.emergency_check_interval = 300  # 5 minutes
        
    def _initialize_retention_policies(self) -> List[RetentionPolicy]:
        """Initialize retention policies from configuration"""
        policies = []
        
        if self.config:
            # Use centralized configuration
            storage_config = self.config.storage
            
            # Recording retention policy (highest priority for cleanup)
            policies.append(RetentionPolicy(
                path=storage_config.recordings_dir,
                max_age_days=storage_config.recording_retention_days,
                max_size_gb=storage_config.max_recording_storage_gb,
                emergency_cleanup_threshold=storage_config.emergency_cleanup_threshold,
                cleanup_threshold=storage_config.storage_cleanup_threshold,
                file_patterns=["*.avi", "*.mp4", "*.mkv"],
                priority=1  # Highest priority
            ))
            
            # Detection retention policy (lower priority)
            policies.append(RetentionPolicy(
                path=storage_config.detections_dir,
                max_age_days=storage_config.detection_retention_days,
                max_size_gb=storage_config.max_detection_storage_gb,
                emergency_cleanup_threshold=storage_config.emergency_cleanup_threshold,
                cleanup_threshold=storage_config.storage_cleanup_threshold,
                file_patterns=["*.jpg", "*.png", "*.jpeg"],
                priority=2
            ))
            
            # Temp files (highest cleanup priority, shortest retention)
            policies.append(RetentionPolicy(
                path=storage_config.temp_dir,
                max_age_days=1,  # Only keep 1 day
                max_size_gb=5.0,
                emergency_cleanup_threshold=0.8,
                cleanup_threshold=0.7,
                file_patterns=["*"],
                priority=0  # Cleanup first
            ))
            
        else:
            # Fallback defaults
            policies = [
                RetentionPolicy(
                    path="recordings",
                    max_age_days=30,
                    max_size_gb=80.0,
                    file_patterns=["*.avi", "*.mp4"],
                    priority=1
                ),
                RetentionPolicy(
                    path="detections",
                    max_age_days=14,
                    max_size_gb=15.0,
                    file_patterns=["*.jpg", "*.png"],
                    priority=2
                ),
                RetentionPolicy(
                    path="temp",
                    max_age_days=1,
                    max_size_gb=5.0,
                    file_patterns=["*"],
                    priority=0
                )
            ]
        
        return policies
    
    async def get_storage_overview(self) -> Dict[str, Any]:
        """Get comprehensive storage overview for all policies"""
        overview = {
            'total_managed_size_gb': 0.0,
            'total_files': 0,
            'policies': [],
            'system_disk_usage': await self._get_system_disk_usage(),
            'cleanup_recommended': False,
            'emergency_cleanup_required': False,
            'timestamp': datetime.now().isoformat()
        }
        
        for policy in self.policies:
            stats = await self._get_directory_stats(policy)
            overview['policies'].append({
                'path': policy.path,
                'stats': stats.__dict__,
                'policy': {
                    'max_age_days': policy.max_age_days,
                    'max_size_gb': policy.max_size_gb,
                    'priority': policy.priority
                }
            })
            
            overview['total_managed_size_gb'] += stats.total_size_gb
            overview['total_files'] += stats.file_count
            
            if stats.requires_cleanup:
                overview['cleanup_recommended'] = True
            
            if stats.usage_percentage > policy.emergency_cleanup_threshold * 100:
                overview['emergency_cleanup_required'] = True
        
        # Add cleanup statistics
        overview['cleanup_history'] = self.cleanup_stats.copy()
        
        return overview
    
    async def _get_directory_stats(self, policy: RetentionPolicy) -> StorageStats:
        """Get detailed statistics for a directory"""
        path = Path(policy.path)
        
        if not path.exists():
            return StorageStats(
                path=policy.path,
                total_size_bytes=0,
                total_size_gb=0.0,
                file_count=0,
                oldest_file_age_days=0,
                newest_file_age_days=0,
                usage_percentage=0.0,
                requires_cleanup=False,
                priority=policy.priority
            )
        
        total_size = 0
        file_count = 0
        oldest_mtime = None
        newest_mtime = None
        
        # Walk through all matching files
        for pattern in policy.file_patterns:
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        total_size += stat.st_size
                        file_count += 1
                        
                        if oldest_mtime is None or stat.st_mtime < oldest_mtime:
                            oldest_mtime = stat.st_mtime
                        if newest_mtime is None or stat.st_mtime > newest_mtime:
                            newest_mtime = stat.st_mtime
                            
                    except OSError:
                        continue  # Skip files we can't access
        
        # Calculate ages
        now = time.time()
        oldest_age_days = int((now - oldest_mtime) / 86400) if oldest_mtime else 0
        newest_age_days = int((now - newest_mtime) / 86400) if newest_mtime else 0
        
        # Calculate usage percentage against policy limit
        max_size_bytes = policy.max_size_gb * 1024**3
        usage_percentage = (total_size / max_size_bytes) * 100 if max_size_bytes > 0 else 0
        
        # Determine if cleanup is required
        requires_cleanup = (
            usage_percentage > policy.cleanup_threshold * 100 or
            oldest_age_days > policy.max_age_days
        )
        
        return StorageStats(
            path=policy.path,
            total_size_bytes=total_size,
            total_size_gb=total_size / (1024**3),
            file_count=file_count,
            oldest_file_age_days=oldest_age_days,
            newest_file_age_days=newest_age_days,
            usage_percentage=usage_percentage,
            requires_cleanup=requires_cleanup,
            priority=policy.priority
        )
    
    async def _get_system_disk_usage(self) -> Dict[str, Any]:
        """Get system disk usage information"""
        try:
            usage = psutil.disk_usage('/')
            return {
                'total_gb': round(usage.total / (1024**3), 2),
                'used_gb': round(usage.used / (1024**3), 2),
                'free_gb': round(usage.free / (1024**3), 2),
                'percentage_used': round((usage.used / usage.total) * 100, 1)
            }
        except Exception as e:
            self.logger.error(f"Failed to get disk usage: {e}")
            return {'error': str(e)}
    
    async def perform_cleanup(self, policy_path: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """Perform cleanup for specific policy or all policies"""
        cleanup_results = {
            'policies_processed': [],
            'total_files_deleted': 0,
            'total_bytes_freed': 0,
            'cleanup_time_seconds': 0,
            'emergency_cleanup_performed': False
        }
        
        start_time = time.time()
        
        # Determine which policies to process
        if policy_path:
            policies_to_process = [p for p in self.policies if p.path == policy_path]
        else:
            # Sort by priority (emergency cleanup order)
            policies_to_process = sorted(self.policies, key=lambda p: p.priority)
        
        for policy in policies_to_process:
            try:
                stats = await self._get_directory_stats(policy)
                
                # Check if cleanup is needed
                needs_cleanup = force or stats.requires_cleanup
                emergency_cleanup = stats.usage_percentage > policy.emergency_cleanup_threshold * 100
                
                if needs_cleanup:
                    self.logger.info(f"Starting cleanup for {policy.path} (usage: {stats.usage_percentage:.1f}%)")
                    
                    if emergency_cleanup:
                        result = await self._emergency_cleanup(policy, stats)
                        cleanup_results['emergency_cleanup_performed'] = True
                    else:
                        result = await self._standard_cleanup(policy, stats)
                    
                    cleanup_results['policies_processed'].append({
                        'path': policy.path,
                        'files_deleted': result['files_deleted'],
                        'bytes_freed': result['bytes_freed'],
                        'emergency': emergency_cleanup
                    })
                    
                    cleanup_results['total_files_deleted'] += result['files_deleted']
                    cleanup_results['total_bytes_freed'] += result['bytes_freed']
                    
                    # Update tracking
                    self.last_cleanup[policy.path] = datetime.now()
                    
                else:
                    self.logger.debug(f"No cleanup needed for {policy.path}")
                    
            except Exception as e:
                self.logger.error(f"Error during cleanup of {policy.path}: {e}")
                continue
        
        cleanup_results['cleanup_time_seconds'] = round(time.time() - start_time, 2)
        
        # Update global stats
        self.cleanup_stats['total_cleanups'] += 1
        self.cleanup_stats['total_files_deleted'] += cleanup_results['total_files_deleted']
        self.cleanup_stats['total_bytes_freed'] += cleanup_results['total_bytes_freed']
        
        if cleanup_results['emergency_cleanup_performed']:
            self.cleanup_stats['last_emergency_cleanup'] = datetime.now().isoformat()
        
        self.logger.info(
            f"Cleanup complete: {cleanup_results['total_files_deleted']} files deleted, "
            f"{cleanup_results['total_bytes_freed'] / (1024**3):.2f}GB freed"
        )
        
        return cleanup_results
    
    async def _standard_cleanup(self, policy: RetentionPolicy, stats: StorageStats) -> Dict[str, int]:
        """Perform standard cleanup based on age and size policies"""
        files_deleted = 0
        bytes_freed = 0
        
        path = Path(policy.path)
        cutoff_date = datetime.now() - timedelta(days=policy.max_age_days)
        
        # Get all files sorted by age (oldest first)
        all_files = []
        for pattern in policy.file_patterns:
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        all_files.append({
                            'path': file_path,
                            'size': stat.st_size,
                            'mtime': stat.st_mtime,
                            'age_days': (time.time() - stat.st_mtime) / 86400
                        })
                    except OSError:
                        continue
        
        # Sort by age (oldest first)
        all_files.sort(key=lambda f: f['mtime'])
        
        # Calculate how much to clean
        target_size_bytes = policy.max_size_gb * 1024**3 * 0.8  # Target 80% of limit
        current_size = stats.total_size_bytes
        bytes_to_free = max(0, current_size - target_size_bytes)
        
        for file_info in all_files:
            # Delete if too old or if we need space
            should_delete = (
                file_info['age_days'] > policy.max_age_days or
                (bytes_to_free > 0 and file_info['age_days'] > 1)  # Keep at least 1 day
            )
            
            if should_delete:
                try:
                    file_info['path'].unlink()
                    files_deleted += 1
                    bytes_freed += file_info['size']
                    bytes_to_free -= file_info['size']
                    
                    self.logger.debug(f"Deleted: {file_info['path']}")
                    
                    # Stop if we've freed enough space
                    if bytes_to_free <= 0:
                        break
                        
                except Exception as e:
                    self.logger.error(f"Failed to delete {file_info['path']}: {e}")
                    continue
        
        # Clean up empty directories
        await self._cleanup_empty_directories(path)
        
        return {
            'files_deleted': files_deleted,
            'bytes_freed': bytes_freed
        }
    
    async def _emergency_cleanup(self, policy: RetentionPolicy, stats: StorageStats) -> Dict[str, int]:
        """Perform emergency cleanup - more aggressive deletion"""
        self.logger.warning(f"Emergency cleanup for {policy.path} (usage: {stats.usage_percentage:.1f}%)")
        
        files_deleted = 0
        bytes_freed = 0
        
        path = Path(policy.path)
        
        # Get all files sorted by age (oldest first)
        all_files = []
        for pattern in policy.file_patterns:
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        all_files.append({
                            'path': file_path,
                            'size': stat.st_size,
                            'mtime': stat.st_mtime
                        })
                    except OSError:
                        continue
        
        # Sort by age (oldest first)
        all_files.sort(key=lambda f: f['mtime'])
        
        # Emergency target: bring down to 60% of limit
        target_size_bytes = policy.max_size_gb * 1024**3 * 0.6
        current_size = stats.total_size_bytes
        bytes_to_free = current_size - target_size_bytes
        
        for file_info in all_files:
            try:
                file_info['path'].unlink()
                files_deleted += 1
                bytes_freed += file_info['size']
                bytes_to_free -= file_info['size']
                
                # Stop when we've reached target
                if bytes_to_free <= 0:
                    break
                    
            except Exception as e:
                self.logger.error(f"Emergency cleanup failed for {file_info['path']}: {e}")
                continue
        
        # Clean up empty directories
        await self._cleanup_empty_directories(path)
        
        return {
            'files_deleted': files_deleted,
            'bytes_freed': bytes_freed
        }
    
    async def _cleanup_empty_directories(self, base_path: Path):
        """Remove empty directories after cleanup"""
        try:
            # Walk bottom-up to remove empty directories
            for dirpath, dirnames, filenames in base_path.walk(top_down=False):
                if not filenames and not dirnames:
                    try:
                        dirpath.rmdir()
                        self.logger.debug(f"Removed empty directory: {dirpath}")
                    except OSError:
                        pass  # Directory not empty or can't remove
        except Exception as e:
            self.logger.error(f"Error cleaning empty directories: {e}")
    
    async def start_monitoring(self):
        """Start background monitoring and cleanup"""
        self.running = True
        self.logger.info("Media retention monitoring started")
        
        # Start monitoring tasks
        cleanup_task = asyncio.create_task(self._periodic_cleanup())
        emergency_task = asyncio.create_task(self._emergency_monitoring())
        
        try:
            await asyncio.gather(cleanup_task, emergency_task)
        except asyncio.CancelledError:
            self.logger.info("Media retention monitoring stopped")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup monitoring"""
        while self.running:
            try:
                # Wait for the next check interval
                await asyncio.sleep(self.check_interval)
                
                if not self.running:
                    break
                
                self.logger.debug("Running periodic storage check...")
                
                # Check all policies and cleanup if needed
                await self.perform_cleanup(force=False)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _emergency_monitoring(self):
        """Emergency cleanup monitoring (more frequent)"""
        while self.running:
            try:
                # Wait for emergency check interval
                await asyncio.sleep(self.emergency_check_interval)
                
                if not self.running:
                    break
                
                # Check for emergency conditions
                for policy in self.policies:
                    stats = await self._get_directory_stats(policy)
                    
                    if stats.usage_percentage > policy.emergency_cleanup_threshold * 100:
                        self.logger.warning(f"Emergency condition detected for {policy.path}")
                        await self.perform_cleanup(policy_path=policy.path, force=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in emergency monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        self.logger.info("Stopping media retention monitoring...")