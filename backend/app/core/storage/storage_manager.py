"""
Storage Manager for 24/7 Recording System
Handles storage cleanup, monitoring, and optimization
"""
import asyncio
import logging
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

logger = logging.getLogger(__name__)


class StorageConfig:
    """Configuration for storage management"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        config = config_dict or {}
        
        # Retention policies
        self.retention_days = config.get('retention_days', 30)
        self.hot_storage_days = config.get('hot_storage_days', 7)
        self.warm_storage_days = config.get('warm_storage_days', 23)  # 30 - 7 = 23
        
        # Storage limits
        self.max_storage_gb_per_camera = config.get('max_storage_gb_per_camera', 500)
        self.warning_threshold_percent = config.get('warning_threshold_percent', 80)
        self.critical_threshold_percent = config.get('critical_threshold_percent', 90)
        
        # Cleanup intervals
        self.cleanup_interval_hours = config.get('cleanup_interval_hours', 1)
        self.monitoring_interval_minutes = config.get('monitoring_interval_minutes', 30)
        
        # Storage paths
        self.base_storage_path = config.get('base_storage_path', 'recordings')
        self.hot_storage_path = config.get('hot_storage_path', None)  # Optional SSD path
        self.archive_storage_path = config.get('archive_storage_path', None)  # Optional archive


class StorageStats:
    """Storage statistics for a camera or system"""
    
    def __init__(self):
        self.total_size_bytes = 0
        self.total_segments = 0
        self.oldest_recording = None
        self.newest_recording = None
        self.average_segment_size = 0
        self.daily_growth_rate = 0
        self.storage_tiers = {
            'hot': {'size_bytes': 0, 'segments': 0},
            'warm': {'size_bytes': 0, 'segments': 0},
            'cold': {'size_bytes': 0, 'segments': 0}
        }


class StorageManager:
    """Manages storage for the 24/7 recording system"""
    
    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize storage manager
        
        Args:
            config: Storage configuration object
        """
        self.config = config or StorageConfig()
        self.base_path = Path(self.config.base_storage_path)
        self.is_running = False
        self.cleanup_task = None
        self.monitoring_task = None
        
        # Ensure base storage directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage manager initialized with base path: {self.base_path}")
    
    async def start(self):
        """Start storage management background tasks"""
        if self.is_running:
            logger.warning("Storage manager is already running")
            return
        
        self.is_running = True
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Storage manager started")
    
    async def stop(self):
        """Stop storage management background tasks"""
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Storage manager stopped")
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.is_running:
            try:
                await self.cleanup_old_recordings()
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                await self.monitor_storage_health()
                await asyncio.sleep(self.config.monitoring_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def cleanup_old_recordings(self):
        """Clean up old recordings based on retention policies"""
        logger.info("Starting storage cleanup...")
        
        camera_dirs = [d for d in self.base_path.iterdir() if d.is_dir() and d.name.startswith('camera_')]
        
        total_cleaned_size = 0
        total_cleaned_segments = 0
        
        for camera_dir in camera_dirs:
            try:
                camera_id = int(camera_dir.name.split('_')[1])
                cleaned_size, cleaned_segments = await self._cleanup_camera_recordings(camera_id, camera_dir)
                total_cleaned_size += cleaned_size
                total_cleaned_segments += cleaned_segments
                
            except Exception as e:
                logger.error(f"Error cleaning up camera directory {camera_dir}: {e}")
        
        if total_cleaned_segments > 0:
            logger.info(f"Cleanup complete: Removed {total_cleaned_segments} segments, "
                       f"freed {self._format_bytes(total_cleaned_size)}")
        else:
            logger.info("Cleanup complete: No recordings to clean up")
    
    async def _cleanup_camera_recordings(self, camera_id: int, camera_dir: Path) -> Tuple[int, int]:
        """Clean up recordings for a specific camera
        
        Args:
            camera_id: Camera ID
            camera_dir: Path to camera recording directory
            
        Returns:
            Tuple of (cleaned_size_bytes, cleaned_segments_count)
        """
        db_path = camera_dir / "index.db"
        if not db_path.exists():
            logger.warning(f"No index database found for camera {camera_id}")
            return 0, 0
        
        cleaned_size = 0
        cleaned_segments = 0
        
        try:
            # Connect to camera's segment database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Calculate cutoff dates
            now = datetime.now()
            retention_cutoff = now - timedelta(days=self.config.retention_days)
            
            # Find segments to delete
            cursor.execute('''
                SELECT filename, start_time, file_size 
                FROM segments 
                WHERE datetime(start_time) < datetime(?)
                ORDER BY start_time
            ''', (retention_cutoff.isoformat(),))
            
            segments_to_delete = cursor.fetchall()
            
            for filename, start_time, file_size in segments_to_delete:
                try:
                    # Find and delete the actual file
                    file_deleted = await self._delete_segment_file(camera_dir, filename, start_time)
                    
                    if file_deleted:
                        # Remove from database
                        cursor.execute('DELETE FROM segments WHERE filename = ?', (filename,))
                        cleaned_size += file_size or 0
                        cleaned_segments += 1
                        
                        logger.debug(f"Deleted old segment: {filename}")
                
                except Exception as e:
                    logger.error(f"Error deleting segment {filename}: {e}")
            
            # Commit database changes
            conn.commit()
            conn.close()
            
            if cleaned_segments > 0:
                logger.info(f"Camera {camera_id}: Cleaned {cleaned_segments} segments, "
                           f"freed {self._format_bytes(cleaned_size)}")
        
        except Exception as e:
            logger.error(f"Error during camera {camera_id} cleanup: {e}")
        
        return cleaned_size, cleaned_segments
    
    async def _delete_segment_file(self, camera_dir: Path, filename: str, start_time: str) -> bool:
        """Delete a segment file from disk
        
        Args:
            camera_dir: Camera directory path
            filename: Segment filename
            start_time: Segment start time for path calculation
            
        Returns:
            True if file was deleted, False otherwise
        """
        try:
            # Parse start time to build path
            start_dt = datetime.fromisoformat(start_time)
            date_path = start_dt.strftime("%Y/%m/%d/%H")
            file_path = camera_dir / date_path / filename
            
            if file_path.exists():
                file_path.unlink()
                
                # Clean up empty directories
                await self._cleanup_empty_directories(file_path.parent)
                return True
            else:
                logger.warning(f"Segment file not found: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting segment file {filename}: {e}")
            return False
    
    async def _cleanup_empty_directories(self, dir_path: Path):
        """Remove empty directories after file deletion
        
        Args:
            dir_path: Directory to check and clean up
        """
        try:
            current_dir = dir_path
            
            # Walk up the directory tree and remove empty directories
            while current_dir != self.base_path and current_dir.exists():
                if not any(current_dir.iterdir()):
                    current_dir.rmdir()
                    logger.debug(f"Removed empty directory: {current_dir}")
                    current_dir = current_dir.parent
                else:
                    break
                    
        except Exception as e:
            logger.debug(f"Error cleaning up empty directories: {e}")
    
    async def monitor_storage_health(self):
        """Monitor storage health and log warnings/alerts"""
        try:
            # Get system-wide storage stats
            total_stats = await self.get_total_storage_stats()
            
            # Check disk space
            disk_usage = shutil.disk_usage(self.base_path)
            disk_free_percent = (disk_usage.free / disk_usage.total) * 100
            
            # Log storage health
            logger.info(f"Storage Health: {total_stats.total_segments} segments, "
                       f"{self._format_bytes(total_stats.total_size_bytes)} used, "
                       f"{disk_free_percent:.1f}% disk free")
            
            # Check thresholds
            if disk_free_percent < (100 - self.config.critical_threshold_percent):
                logger.error(f"CRITICAL: Disk space critically low! {disk_free_percent:.1f}% free")
            elif disk_free_percent < (100 - self.config.warning_threshold_percent):
                logger.warning(f"WARNING: Disk space low! {disk_free_percent:.1f}% free")
            
            # Check per-camera storage limits
            await self._check_camera_storage_limits()
            
        except Exception as e:
            logger.error(f"Error monitoring storage health: {e}", exc_info=True)
    
    async def _check_camera_storage_limits(self):
        """Check storage limits for each camera"""
        camera_dirs = [d for d in self.base_path.iterdir() if d.is_dir() and d.name.startswith('camera_')]
        
        for camera_dir in camera_dirs:
            try:
                camera_id = int(camera_dir.name.split('_')[1])
                stats = await self.get_camera_storage_stats(camera_id)
                
                size_gb = stats.total_size_bytes / (1024**3)
                limit_gb = self.config.max_storage_gb_per_camera
                
                if size_gb > limit_gb:
                    logger.warning(f"Camera {camera_id} storage exceeds limit: "
                                 f"{size_gb:.1f}GB > {limit_gb}GB")
                
            except Exception as e:
                logger.error(f"Error checking storage limit for {camera_dir}: {e}")
    
    async def get_camera_storage_stats(self, camera_id: int) -> StorageStats:
        """Get storage statistics for a specific camera
        
        Args:
            camera_id: Camera ID
            
        Returns:
            StorageStats object with camera statistics
        """
        stats = StorageStats()
        camera_dir = self.base_path / f"camera_{camera_id}"
        
        if not camera_dir.exists():
            return stats
        
        db_path = camera_dir / "index.db"
        if not db_path.exists():
            return stats
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as segment_count,
                    SUM(file_size) as total_size,
                    MIN(start_time) as oldest,
                    MAX(start_time) as newest,
                    AVG(file_size) as avg_size
                FROM segments
            ''')
            
            result = cursor.fetchone()
            if result:
                stats.total_segments = result[0] or 0
                stats.total_size_bytes = result[1] or 0
                stats.oldest_recording = result[2]
                stats.newest_recording = result[3]
                stats.average_segment_size = result[4] or 0
            
            # Calculate storage tiers
            now = datetime.now()
            hot_cutoff = now - timedelta(days=self.config.hot_storage_days)
            warm_cutoff = now - timedelta(days=self.config.retention_days)
            
            # Hot storage (recent)
            cursor.execute('''
                SELECT COUNT(*), SUM(file_size)
                FROM segments 
                WHERE datetime(start_time) >= datetime(?)
            ''', (hot_cutoff.isoformat(),))
            
            hot_result = cursor.fetchone()
            if hot_result:
                stats.storage_tiers['hot']['segments'] = hot_result[0] or 0
                stats.storage_tiers['hot']['size_bytes'] = hot_result[1] or 0
            
            # Warm storage (older but within retention)
            cursor.execute('''
                SELECT COUNT(*), SUM(file_size)
                FROM segments 
                WHERE datetime(start_time) < datetime(?) 
                AND datetime(start_time) >= datetime(?)
            ''', (hot_cutoff.isoformat(), warm_cutoff.isoformat()))
            
            warm_result = cursor.fetchone()
            if warm_result:
                stats.storage_tiers['warm']['segments'] = warm_result[0] or 0
                stats.storage_tiers['warm']['size_bytes'] = warm_result[1] or 0
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting storage stats for camera {camera_id}: {e}")
        
        return stats
    
    async def get_total_storage_stats(self) -> StorageStats:
        """Get total storage statistics across all cameras
        
        Returns:
            StorageStats object with system-wide statistics
        """
        total_stats = StorageStats()
        
        camera_dirs = [d for d in self.base_path.iterdir() if d.is_dir() and d.name.startswith('camera_')]
        
        for camera_dir in camera_dirs:
            try:
                camera_id = int(camera_dir.name.split('_')[1])
                camera_stats = await self.get_camera_storage_stats(camera_id)
                
                # Aggregate stats
                total_stats.total_size_bytes += camera_stats.total_size_bytes
                total_stats.total_segments += camera_stats.total_segments
                
                # Update oldest/newest
                if camera_stats.oldest_recording:
                    if not total_stats.oldest_recording or camera_stats.oldest_recording < total_stats.oldest_recording:
                        total_stats.oldest_recording = camera_stats.oldest_recording
                
                if camera_stats.newest_recording:
                    if not total_stats.newest_recording or camera_stats.newest_recording > total_stats.newest_recording:
                        total_stats.newest_recording = camera_stats.newest_recording
                
                # Aggregate tiers
                for tier in ['hot', 'warm', 'cold']:
                    total_stats.storage_tiers[tier]['size_bytes'] += camera_stats.storage_tiers[tier]['size_bytes']
                    total_stats.storage_tiers[tier]['segments'] += camera_stats.storage_tiers[tier]['segments']
                
            except Exception as e:
                logger.error(f"Error aggregating stats for {camera_dir}: {e}")
        
        # Calculate average segment size
        if total_stats.total_segments > 0:
            total_stats.average_segment_size = total_stats.total_size_bytes / total_stats.total_segments
        
        return total_stats
    
    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes as human readable string
        
        Args:
            bytes_size: Size in bytes
            
        Returns:
            Formatted string (e.g., "1.5 GB")
        """
        if bytes_size == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while bytes_size >= 1024 and i < len(units) - 1:
            bytes_size /= 1024
            i += 1
        
        return f"{bytes_size:.1f} {units[i]}"
    
    async def force_cleanup_camera(self, camera_id: int) -> Dict[str, Any]:
        """Force cleanup of a specific camera's recordings
        
        Args:
            camera_id: Camera ID to clean up
            
        Returns:
            Cleanup results dictionary
        """
        camera_dir = self.base_path / f"camera_{camera_id}"
        
        if not camera_dir.exists():
            return {"error": f"Camera {camera_id} directory not found"}
        
        logger.info(f"Forcing cleanup for camera {camera_id}")
        
        cleaned_size, cleaned_segments = await self._cleanup_camera_recordings(camera_id, camera_dir)
        
        return {
            "camera_id": camera_id,
            "cleaned_segments": cleaned_segments,
            "cleaned_size_bytes": cleaned_size,
            "cleaned_size_formatted": self._format_bytes(cleaned_size)
        }
    
    async def get_storage_report(self) -> Dict[str, Any]:
        """Generate comprehensive storage report
        
        Returns:
            Dictionary with storage report data
        """
        try:
            # Get system stats
            total_stats = await self.get_total_storage_stats()
            
            # Get disk usage
            disk_usage = shutil.disk_usage(self.base_path)
            
            # Get per-camera stats
            camera_stats = {}
            camera_dirs = [d for d in self.base_path.iterdir() if d.is_dir() and d.name.startswith('camera_')]
            
            for camera_dir in camera_dirs:
                try:
                    camera_id = int(camera_dir.name.split('_')[1])
                    stats = await self.get_camera_storage_stats(camera_id)
                    camera_stats[str(camera_id)] = {
                        "total_size_bytes": stats.total_size_bytes,
                        "total_size_formatted": self._format_bytes(stats.total_size_bytes),
                        "total_segments": stats.total_segments,
                        "oldest_recording": stats.oldest_recording,
                        "newest_recording": stats.newest_recording,
                        "storage_tiers": stats.storage_tiers
                    }
                except Exception as e:
                    logger.error(f"Error getting stats for camera {camera_dir}: {e}")
            
            return {
                "system_stats": {
                    "total_size_bytes": total_stats.total_size_bytes,
                    "total_size_formatted": self._format_bytes(total_stats.total_size_bytes),
                    "total_segments": total_stats.total_segments,
                    "oldest_recording": total_stats.oldest_recording,
                    "newest_recording": total_stats.newest_recording,
                    "average_segment_size": total_stats.average_segment_size,
                    "storage_tiers": total_stats.storage_tiers
                },
                "disk_usage": {
                    "total_bytes": disk_usage.total,
                    "used_bytes": disk_usage.used,
                    "free_bytes": disk_usage.free,
                    "free_percent": (disk_usage.free / disk_usage.total) * 100,
                    "total_formatted": self._format_bytes(disk_usage.total),
                    "used_formatted": self._format_bytes(disk_usage.used),
                    "free_formatted": self._format_bytes(disk_usage.free)
                },
                "camera_stats": camera_stats,
                "config": {
                    "retention_days": self.config.retention_days,
                    "hot_storage_days": self.config.hot_storage_days,
                    "max_storage_gb_per_camera": self.config.max_storage_gb_per_camera,
                    "cleanup_interval_hours": self.config.cleanup_interval_hours
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating storage report: {e}", exc_info=True)
            return {"error": str(e)}