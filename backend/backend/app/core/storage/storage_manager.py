"""
Storage Manager for 24/7 Recording System
Handles storage cleanup, monitoring, and optimization
"""
import asyncio
import json
import logging
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StorageStats:
    """Storage statistics for a camera or system"""
    total_segments: int = 0
    total_size_bytes: int = 0
    oldest_recording: Optional[datetime] = None
    newest_recording: Optional[datetime] = None
    disk_free_bytes: int = 0
    disk_total_bytes: int = 0
    disk_used_percent: float = 0.0


class StorageConfig:
    """Configuration for storage management"""
    
    def __init__(self, config_dict: Optional[Dict] = None):
        config = config_dict or {}
        
        self.base_storage_path = Path(config.get('base_storage_path', 'recordings'))
        self.retention_days = config.get('retention_days', 30)
        self.hot_storage_days = config.get('hot_storage_days', 7)
        self.max_storage_gb_per_camera = config.get('max_storage_gb_per_camera', 500)
        self.warning_threshold_percent = config.get('warning_threshold_percent', 80)
        self.critical_threshold_percent = config.get('critical_threshold_percent', 90)
        self.cleanup_interval_hours = config.get('cleanup_interval_hours', 1)
        self.monitoring_interval_minutes = config.get('monitoring_interval_minutes', 30)


class StorageManager:
    """Manages storage for the 24/7 recording system"""
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self._cleanup_task = None
        self._monitoring_task = None
        self._is_running = False
        
        logger.info(f"Storage manager initialized with {self.config.retention_days} days retention")
    
    async def start(self):
        """Start background storage management tasks"""
        if self._is_running:
            logger.warning("Storage manager already running")
            return
        
        self._is_running = True
        
        # Start cleanup and monitoring tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Storage manager started")
    
    async def stop(self):
        """Stop background storage management tasks"""
        self._is_running = False
        
        # Cancel tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Storage manager stopped")
    
    async def _cleanup_loop(self):
        """Background task for periodic cleanup"""
        while self._is_running:
            try:
                await self.cleanup_old_recordings()
                
                # Sleep for configured interval
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(300)  # Retry after 5 minutes on error
    
    async def _monitoring_loop(self):
        """Background task for storage monitoring"""
        while self._is_running:
            try:
                await self.monitor_storage_health()
                
                # Sleep for configured interval
                await asyncio.sleep(self.config.monitoring_interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def cleanup_old_recordings(self, camera_id: Optional[int] = None) -> Dict:
        """
        Clean up old recordings based on retention policies
        
        Args:
            camera_id: Optional camera ID to cleanup (None for all cameras)
            
        Returns:
            Cleanup statistics
        """
        logger.info(f"Starting cleanup (retention: {self.config.retention_days} days)")
        
        stats = {
            'removed_segments': 0,
            'freed_bytes': 0,
            'errors': []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            
            # Get list of camera directories
            if camera_id:
                camera_dirs = [self.config.base_storage_path / f"camera_{camera_id}"]
            else:
                camera_dirs = [d for d in self.config.base_storage_path.iterdir() 
                             if d.is_dir() and d.name.startswith('camera_')]
            
            for camera_dir in camera_dirs:
                if not camera_dir.exists():
                    continue
                
                # Get segments from database
                index_db = camera_dir / "index.db"
                if not index_db.exists():
                    continue
                
                try:
                    # Use context manager for database connection
                    with sqlite3.connect(str(index_db)) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        
                        # Find old segments
                        cursor.execute("""
                            SELECT id, filename, file_path, file_size
                            FROM video_segments
                            WHERE start_time < ?
                        """, (cutoff_date.isoformat(),))
                        
                        old_segments = cursor.fetchall()
                        
                        for segment in old_segments:
                            # Delete file
                            file_path = Path(segment['file_path'])
                            if file_path.exists():
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                stats['removed_segments'] += 1
                                stats['freed_bytes'] += file_size
                                
                                # Remove empty directories
                                self._cleanup_empty_dirs(file_path.parent)
                            
                            # Remove from database
                            cursor.execute("DELETE FROM video_segments WHERE id = ?", (segment['id'],))
                        
                        conn.commit()
                        
                except Exception as e:
                    logger.error(f"Error cleaning camera {camera_dir.name}: {e}")
                    stats['errors'].append(f"{camera_dir.name}: {str(e)}")
            
            logger.info(f"Cleanup complete: Removed {stats['removed_segments']} segments, "
                       f"freed {self._format_bytes(stats['freed_bytes'])}")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            stats['errors'].append(str(e))
        
        return stats
    
    async def monitor_storage_health(self) -> Dict:
        """
        Monitor storage health and log warnings/alerts
        
        Returns:
            Health status dictionary
        """
        try:
            # Get disk usage
            disk_usage = shutil.disk_usage(self.config.base_storage_path)
            disk_used_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Get total storage stats
            total_stats = await self.get_total_storage_stats()
            
            health_status = {
                'disk_free_gb': disk_usage.free / (1024**3),
                'disk_used_percent': disk_used_percent,
                'total_segments': total_stats.total_segments,
                'total_size_gb': total_stats.total_size_bytes / (1024**3),
                'status': 'healthy'
            }
            
            # Check thresholds
            if disk_used_percent >= self.config.critical_threshold_percent:
                health_status['status'] = 'critical'
                logger.critical(f"CRITICAL: Disk usage at {disk_used_percent:.1f}%! "
                              f"Only {health_status['disk_free_gb']:.1f} GB free")
            elif disk_used_percent >= self.config.warning_threshold_percent:
                health_status['status'] = 'warning'
                logger.warning(f"WARNING: Disk usage at {disk_used_percent:.1f}%. "
                             f"Only {health_status['disk_free_gb']:.1f} GB free")
            else:
                logger.info(f"Storage Health: {total_stats.total_segments} segments, "
                          f"{self._format_bytes(total_stats.total_size_bytes)} used, "
                          f"{disk_used_percent:.1f}% disk full")
            
            # Check per-camera limits
            camera_dirs = [d for d in self.config.base_storage_path.iterdir() 
                         if d.is_dir() and d.name.startswith('camera_')]
            
            for camera_dir in camera_dirs:
                camera_id = int(camera_dir.name.split('_')[1])
                camera_stats = await self.get_camera_storage_stats(camera_id)
                
                camera_size_gb = camera_stats.total_size_bytes / (1024**3)
                if camera_size_gb > self.config.max_storage_gb_per_camera:
                    logger.warning(f"Camera {camera_id} exceeds storage limit: "
                                 f"{camera_size_gb:.1f} GB / {self.config.max_storage_gb_per_camera} GB")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Storage monitoring failed: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
    
    async def get_camera_storage_stats(self, camera_id: int) -> StorageStats:
        """
        Get storage statistics for a specific camera
        
        Args:
            camera_id: Camera ID
            
        Returns:
            StorageStats object
        """
        stats = StorageStats()
        
        try:
            camera_dir = self.config.base_storage_path / f"camera_{camera_id}"
            if not camera_dir.exists():
                return stats
            
            # Get disk stats
            disk_usage = shutil.disk_usage(self.config.base_storage_path)
            stats.disk_free_bytes = disk_usage.free
            stats.disk_total_bytes = disk_usage.total
            stats.disk_used_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Get segment stats from database
            index_db = camera_dir / "index.db"
            if index_db.exists():
                with sqlite3.connect(str(index_db)) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Get counts and sizes
                    cursor.execute("""
                        SELECT COUNT(*) as count, 
                               SUM(file_size) as total_size,
                               MIN(start_time) as oldest,
                               MAX(start_time) as newest
                        FROM video_segments
                    """)
                    
                    row = cursor.fetchone()
                    if row:
                        stats.total_segments = row['count'] or 0
                        stats.total_size_bytes = row['total_size'] or 0
                        
                        if row['oldest']:
                            stats.oldest_recording = datetime.fromisoformat(row['oldest'])
                        if row['newest']:
                            stats.newest_recording = datetime.fromisoformat(row['newest'])
            
        except Exception as e:
            logger.error(f"Error getting camera {camera_id} stats: {e}")
        
        return stats
    
    async def get_total_storage_stats(self) -> StorageStats:
        """
        Get total storage statistics across all cameras
        
        Returns:
            StorageStats object
        """
        total_stats = StorageStats()
        
        try:
            # Get disk stats
            disk_usage = shutil.disk_usage(self.config.base_storage_path)
            total_stats.disk_free_bytes = disk_usage.free
            total_stats.disk_total_bytes = disk_usage.total
            total_stats.disk_used_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Aggregate stats from all cameras
            camera_dirs = [d for d in self.config.base_storage_path.iterdir() 
                         if d.is_dir() and d.name.startswith('camera_')]
            
            oldest_overall = None
            newest_overall = None
            
            for camera_dir in camera_dirs:
                camera_id = int(camera_dir.name.split('_')[1])
                camera_stats = await self.get_camera_storage_stats(camera_id)
                
                total_stats.total_segments += camera_stats.total_segments
                total_stats.total_size_bytes += camera_stats.total_size_bytes
                
                # Track oldest/newest across all cameras
                if camera_stats.oldest_recording:
                    if not oldest_overall or camera_stats.oldest_recording < oldest_overall:
                        oldest_overall = camera_stats.oldest_recording
                
                if camera_stats.newest_recording:
                    if not newest_overall or camera_stats.newest_recording > newest_overall:
                        newest_overall = camera_stats.newest_recording
            
            total_stats.oldest_recording = oldest_overall
            total_stats.newest_recording = newest_overall
            
        except Exception as e:
            logger.error(f"Error getting total storage stats: {e}")
        
        return total_stats
    
    async def get_storage_report(self) -> Dict:
        """
        Generate comprehensive storage report
        
        Returns:
            Storage report dictionary
        """
        try:
            # Get total stats
            total_stats = await self.get_total_storage_stats()
            
            # Get per-camera stats
            camera_stats = []
            camera_dirs = [d for d in self.config.base_storage_path.iterdir() 
                         if d.is_dir() and d.name.startswith('camera_')]
            
            for camera_dir in camera_dirs:
                camera_id = int(camera_dir.name.split('_')[1])
                stats = await self.get_camera_storage_stats(camera_id)
                
                camera_stats.append({
                    'camera_id': camera_id,
                    'segments': stats.total_segments,
                    'size_bytes': stats.total_size_bytes,
                    'size_formatted': self._format_bytes(stats.total_size_bytes),
                    'oldest_recording': stats.oldest_recording.isoformat() if stats.oldest_recording else None,
                    'newest_recording': stats.newest_recording.isoformat() if stats.newest_recording else None
                })
            
            # Sort by size
            camera_stats.sort(key=lambda x: x['size_bytes'], reverse=True)
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'retention_days': self.config.retention_days,
                'system_stats': {
                    'total_segments': total_stats.total_segments,
                    'total_size_bytes': total_stats.total_size_bytes,
                    'total_size_formatted': self._format_bytes(total_stats.total_size_bytes),
                    'disk_free_bytes': total_stats.disk_free_bytes,
                    'disk_free_formatted': self._format_bytes(total_stats.disk_free_bytes),
                    'disk_used_percent': round(total_stats.disk_used_percent, 1),
                    'oldest_recording': total_stats.oldest_recording.isoformat() if total_stats.oldest_recording else None,
                    'newest_recording': total_stats.newest_recording.isoformat() if total_stats.newest_recording else None
                },
                'camera_stats': camera_stats
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating storage report: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _cleanup_empty_dirs(self, directory: Path):
        """Recursively clean up empty directories"""
        try:
            # Check if directory is empty
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
                
                # Check parent
                if directory.parent != self.config.base_storage_path:
                    self._cleanup_empty_dirs(directory.parent)
                    
        except Exception as e:
            logger.debug(f"Could not remove directory {directory}: {e}")
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"