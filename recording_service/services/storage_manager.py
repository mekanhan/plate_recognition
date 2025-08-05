"""
Storage Manager - Handles storage management, cleanup, and monitoring
Maintains storage limits and provides storage statistics
"""
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import asyncio
from database.models import VideoRecording, StorageStats

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages recording storage and cleanup"""
    
    def __init__(self, recordings_path: str, storage_limit_gb: int = 10):
        self.recordings_path = Path(recordings_path)
        self.storage_limit_bytes = storage_limit_gb * 1024 * 1024 * 1024
        self.storage_limit_gb = storage_limit_gb
        
        # Ensure recordings directory exists
        self.recordings_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Storage Manager initialized: {recordings_path}, limit: {storage_limit_gb}GB")
    
    async def get_storage_report(self) -> Dict:
        """Get comprehensive storage statistics"""
        try:
            # Calculate total used storage
            total_used_bytes = 0
            camera_stats = {}
            
            for camera_dir in self.recordings_path.glob("camera_*"):
                if camera_dir.is_dir():
                    camera_id = camera_dir.name.replace("camera_", "")
                    camera_size = await self._calculate_directory_size(camera_dir)
                    total_used_bytes += camera_size
                    
                    # Get oldest and newest recordings for this camera
                    oldest, newest, segment_count = await self._get_camera_recording_range(camera_id)
                    
                    camera_stats[camera_id] = {
                        "total_size": camera_size,
                        "total_segments": segment_count,
                        "oldest_recording": oldest.isoformat() if oldest else None,
                        "newest_recording": newest.isoformat() if newest else None
                    }
            
            # Calculate usage percentages
            percentage_used = (total_used_bytes / self.storage_limit_bytes) * 100
            available_bytes = max(0, self.storage_limit_bytes - total_used_bytes)
            available_gb = available_bytes / (1024 * 1024 * 1024)
            
            # Estimate days remaining (rough calculation)
            if total_used_bytes > 0:
                # Assume current usage rate continues
                daily_usage = total_used_bytes / max(1, (datetime.now() - datetime.now().replace(day=1)).days)
                estimated_days_remaining = available_bytes / max(daily_usage, 1)
            else:
                estimated_days_remaining = float('inf')
            
            return {
                "storage_limit_gb": self.storage_limit_gb,
                "storage_limit_bytes": self.storage_limit_bytes,
                "total_used_bytes": total_used_bytes,
                "total_used_gb": round(total_used_bytes / (1024 * 1024 * 1024), 2),
                "percentage_used": round(percentage_used, 1),
                "available_bytes": available_bytes,
                "available_gb": round(available_gb, 2),
                "cameras": camera_stats,
                "cleanup_required": percentage_used > 90,
                "estimated_days_remaining": round(min(estimated_days_remaining, 999), 1)
            }
            
        except Exception as e:
            logger.error(f"Error generating storage report: {e}")
            raise
    
    async def cleanup_storage(
        self, 
        target_size_gb: Optional[float] = None,
        delete_before_date: Optional[str] = None
    ) -> Dict:
        """Perform storage cleanup"""
        try:
            if target_size_gb is None:
                target_size_bytes = int(self.storage_limit_bytes * 0.8)  # 80% of limit
            else:
                target_size_bytes = int(target_size_gb * 1024 * 1024 * 1024)
            
            # Get current storage usage
            storage_report = await self.get_storage_report()
            current_size = storage_report["total_used_bytes"]
            
            if current_size <= target_size_bytes and not delete_before_date:
                return {
                    "cleaned": False,
                    "reason": "Within storage limit",
                    "current_size_gb": round(current_size / (1024 * 1024 * 1024), 2),
                    "target_size_gb": round(target_size_bytes / (1024 * 1024 * 1024), 2)
                }
            
            # Get list of segments to delete (oldest first)
            segments_to_delete = await self._get_segments_for_cleanup(
                target_size_bytes, 
                current_size,
                delete_before_date
            )
            
            deleted_count = 0
            deleted_size = 0
            
            for segment in segments_to_delete:
                try:
                    # Delete file
                    file_path = Path(segment['file_path'])
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_size += file_size
                        deleted_count += 1
                        
                        logger.info(f"Deleted segment: {segment['filename']}")
                    
                    # Remove from database
                    await self._remove_segment_from_db(segment['filename'])
                    
                    # Check if we've freed enough space
                    if current_size - deleted_size <= target_size_bytes:
                        break
                        
                except Exception as e:
                    logger.error(f"Error deleting segment {segment['filename']}: {e}")
                    continue
            
            # Clean up empty directories
            await self._cleanup_empty_directories()
            
            return {
                "cleaned": True,
                "deleted_count": deleted_count,
                "deleted_size": deleted_size,
                "deleted_size_gb": round(deleted_size / (1024 * 1024 * 1024), 2),
                "new_total_size": current_size - deleted_size,
                "new_total_size_gb": round((current_size - deleted_size) / (1024 * 1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error during storage cleanup: {e}")
            raise
    
    async def _calculate_directory_size(self, directory: Path) -> int:
        """Calculate total size of a directory"""
        total_size = 0
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating directory size for {directory}: {e}")
        return total_size
    
    async def _get_camera_recording_range(self, camera_id: str) -> tuple:
        """Get oldest and newest recording times for a camera"""
        try:
            # This would need database service access - simplified for now
            # In real implementation, query the database
            camera_dir = self.recordings_path / f"camera_{camera_id}"
            
            if not camera_dir.exists():
                return None, None, 0
            
            # Count video files (both AVI and MP4 formats)
            video_files = list(camera_dir.rglob("*.avi")) + list(camera_dir.rglob("*.mp4"))
            segment_count = len(video_files)
            
            if not video_files:
                return None, None, 0
            
            # Get oldest and newest from file modification times
            oldest_file = min(video_files, key=lambda f: f.stat().st_mtime)
            newest_file = max(video_files, key=lambda f: f.stat().st_mtime)
            
            oldest_time = datetime.fromtimestamp(oldest_file.stat().st_mtime)
            newest_time = datetime.fromtimestamp(newest_file.stat().st_mtime)
            
            return oldest_time, newest_time, segment_count
            
        except Exception as e:
            logger.error(f"Error getting recording range for camera {camera_id}: {e}")
            return None, None, 0
    
    async def _get_segments_for_cleanup(
        self, 
        target_size_bytes: int, 
        current_size: int,
        delete_before_date: Optional[str] = None
    ) -> list:
        """Get list of segments to delete (oldest first)"""
        # This is a simplified version - in real implementation,
        # this would query the database for segments ordered by date
        segments = []
        
        try:
            # Walk through all video files, oldest first
            for camera_dir in self.recordings_path.glob("camera_*"):
                if not camera_dir.is_dir():
                    continue
                
                camera_id = camera_dir.name.replace("camera_", "")
                
                # Get all video files for this camera (both AVI and MP4 formats)
                video_files = list(camera_dir.rglob("*.avi")) + list(camera_dir.rglob("*.mp4"))
                
                # Sort by modification time (oldest first)
                video_files.sort(key=lambda f: f.stat().st_mtime)
                
                for video_file in video_files:
                    # Check date filter if provided
                    if delete_before_date:
                        file_date = datetime.fromtimestamp(video_file.stat().st_mtime)
                        if file_date >= datetime.fromisoformat(delete_before_date):
                            continue
                    
                    segments.append({
                        'filename': video_file.name,
                        'file_path': str(video_file),
                        'camera_id': camera_id,
                        'file_size': video_file.stat().st_size
                    })
            
            return segments
            
        except Exception as e:
            logger.error(f"Error getting segments for cleanup: {e}")
            return []
    
    async def _remove_segment_from_db(self, filename: str):
        """Remove segment from database (placeholder)"""
        # This would need database service access
        # In real implementation, execute DELETE query
        logger.info(f"Would remove segment from DB: {filename}")
    
    async def _cleanup_empty_directories(self):
        """Remove empty directories after cleanup"""
        try:
            for camera_dir in self.recordings_path.glob("camera_*"):
                if not camera_dir.is_dir():
                    continue
                
                # Remove empty year/month/day/hour directories
                for year_dir in camera_dir.glob("*"):
                    if not year_dir.is_dir():
                        continue
                    
                    for month_dir in year_dir.glob("*"):
                        if not month_dir.is_dir():
                            continue
                        
                        for day_dir in month_dir.glob("*"):
                            if not day_dir.is_dir():
                                continue
                            
                            for hour_dir in day_dir.glob("*"):
                                if hour_dir.is_dir() and not any(hour_dir.iterdir()):
                                    hour_dir.rmdir()
                                    logger.info(f"Removed empty directory: {hour_dir}")
                            
                            if not any(day_dir.iterdir()):
                                day_dir.rmdir()
                                logger.info(f"Removed empty directory: {day_dir}")
                        
                        if not any(month_dir.iterdir()):
                            month_dir.rmdir()
                            logger.info(f"Removed empty directory: {month_dir}")
                    
                    if not any(year_dir.iterdir()):
                        year_dir.rmdir()
                        logger.info(f"Removed empty directory: {year_dir}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up empty directories: {e}")
    
    async def start_maintenance_tasks(self):
        """Start background maintenance tasks"""
        # Start periodic storage monitoring
        asyncio.create_task(self._periodic_storage_check())
        logger.info("Storage maintenance tasks started")
    
    async def _periodic_storage_check(self):
        """Periodic storage monitoring and auto-cleanup"""
        while True:
            try:
                # Check storage every hour
                await asyncio.sleep(3600)
                
                # Get storage report
                report = await self.get_storage_report()
                
                # Auto-cleanup if over 90% full
                if report["percentage_used"] > 90:
                    logger.warning(f"Storage usage at {report['percentage_used']}%, triggering cleanup")
                    await self.cleanup_storage()
                
                # Log storage status
                logger.info(f"Storage status: {report['percentage_used']}% used ({report['total_used_gb']}GB)")
                
            except Exception as e:
                logger.error(f"Error in periodic storage check: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error