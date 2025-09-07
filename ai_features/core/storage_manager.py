"""
Storage Manager for Detection Images
Manages storage with hard caps and automatic cleanup
"""
import os
import shutil
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json


class StorageManager:
    """Manages detection storage with configurable limits"""
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger("StorageManager")
        
        # Default configuration
        self.config = {
            'max_storage_gb': 200.0,
            'cleanup_threshold_gb': 180.0,
            'min_free_space_gb': 20.0,
            'detection_dirs': {
                'frames': 'detections/frames',
                'plates': 'detections/plates'
            },
            'cleanup_strategy': 'oldest_first',  # oldest_first, lowest_confidence
            'retention_days': 30,  # Keep detections for max 30 days
        }
        
        # Load from config file if no config provided
        if config is None:
            try:
                config_path = Path('config/storage_config.json')
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        storage_config = json.load(f)
                        if 'storage_manager' in storage_config:
                            config = storage_config['storage_manager']
                            self.logger.info(f"Loaded storage config from file: max_storage_gb={config.get('max_storage_gb', 'not set')}")
            except Exception as e:
                self.logger.warning(f"Failed to load storage config from file: {e}, using defaults")
        
        # Update with provided config
        if config:
            self.config.update(config)
        
        # Convert GB to bytes for calculations
        self.max_storage_bytes = self.config['max_storage_gb'] * 1024**3
        self.cleanup_threshold_bytes = self.config['cleanup_threshold_gb'] * 1024**3
        
        # Ensure directories exist
        for dir_path in self.config['detection_dirs'].values():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Track storage stats
        self.last_cleanup = datetime.now()
        self.total_cleanups = 0
        self.total_files_deleted = 0
        self.total_bytes_freed = 0
    
    def get_storage_usage(self) -> Dict:
        """Get current storage usage statistics"""
        stats = {
            'total_size_bytes': 0,
            'total_size_gb': 0.0,
            'frames': {'count': 0, 'size_bytes': 0},
            'plates': {'count': 0, 'size_bytes': 0},
            'percentage_used': 0.0,
            'requires_cleanup': False
        }
        
        # Calculate usage for each directory
        for key, dir_path in self.config['detection_dirs'].items():
            if os.path.exists(dir_path):
                dir_stats = self._get_directory_stats(dir_path)
                stats[key] = dir_stats
                stats['total_size_bytes'] += dir_stats['size_bytes']
        
        # Calculate totals
        stats['total_size_gb'] = stats['total_size_bytes'] / (1024**3)
        stats['percentage_used'] = (stats['total_size_bytes'] / self.max_storage_bytes) * 100
        stats['requires_cleanup'] = stats['total_size_bytes'] >= self.cleanup_threshold_bytes
        
        return stats
    
    def _get_directory_stats(self, dir_path: str) -> Dict:
        """Get statistics for a directory"""
        total_size = 0
        file_count = 0
        
        try:
            for entry in os.scandir(dir_path):
                if entry.is_file():
                    total_size += entry.stat().st_size
                    file_count += 1
        except Exception as e:
            self.logger.error(f"Error scanning directory {dir_path}: {e}")
        
        return {
            'count': file_count,
            'size_bytes': total_size,
            'size_mb': total_size / (1024**2)
        }
    
    def check_storage_before_save(self, estimated_size_bytes: int = 500000) -> bool:
        """Check if there's space for new detection (returns True if OK to save)"""
        stats = self.get_storage_usage()
        
        # Check if we're already over limit
        if stats['total_size_bytes'] >= self.max_storage_bytes:
            self.logger.warning(f"Storage limit reached: {stats['total_size_gb']:.2f}GB / {self.config['max_storage_gb']}GB")
            # Try cleanup
            self.cleanup_old_detections()
            # Re-check
            stats = self.get_storage_usage()
            return stats['total_size_bytes'] + estimated_size_bytes < self.max_storage_bytes
        
        # Check if adding this would exceed limit
        if stats['total_size_bytes'] + estimated_size_bytes >= self.cleanup_threshold_bytes:
            self.logger.info(f"Approaching storage limit, running cleanup...")
            self.cleanup_old_detections()
        
        return True
    
    def cleanup_old_detections(self, force: bool = False) -> Dict:
        """Clean up old detection files based on strategy"""
        cleanup_stats = {
            'files_deleted': 0,
            'bytes_freed': 0,
            'cleanup_time_ms': 0
        }
        
        start_time = datetime.now()
        
        # Get current usage
        stats = self.get_storage_usage()
        
        if not force and stats['total_size_bytes'] < self.cleanup_threshold_bytes:
            self.logger.info("Storage within limits, no cleanup needed")
            return cleanup_stats
        
        self.logger.info(f"Starting cleanup (current: {stats['total_size_gb']:.2f}GB)")
        
        # Get all detection files with metadata
        all_files = self._get_all_detection_files()
        
        if self.config['cleanup_strategy'] == 'oldest_first':
            # Sort by modification time (oldest first)
            all_files.sort(key=lambda x: x['mtime'])
        elif self.config['cleanup_strategy'] == 'lowest_confidence':
            # Would need to parse filenames or check database
            all_files.sort(key=lambda x: x['mtime'])  # Fallback to oldest
        
        # Calculate how much to free (target 80% of limit)
        target_size = self.max_storage_bytes * 0.8
        bytes_to_free = stats['total_size_bytes'] - target_size
        
        if bytes_to_free <= 0:
            self.logger.info("Storage within target range")
            return cleanup_stats
        
        # Delete files until we reach target
        for file_info in all_files:
            # Check retention policy
            file_age_days = (datetime.now() - datetime.fromtimestamp(file_info['mtime'])).days
            
            # Skip if within minimum retention (keep at least 1 day unless forced)
            if not force and file_age_days < 1:
                continue
            
            # Delete file
            try:
                os.remove(file_info['path'])
                cleanup_stats['files_deleted'] += 1
                cleanup_stats['bytes_freed'] += file_info['size']
                
                # Also try to delete corresponding file in other directory
                # (if deleting frame, also delete plate and vice versa)
                self._delete_corresponding_file(file_info['path'])
                
                if cleanup_stats['bytes_freed'] >= bytes_to_free:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error deleting {file_info['path']}: {e}")
        
        # Update tracking stats
        self.total_cleanups += 1
        self.total_files_deleted += cleanup_stats['files_deleted']
        self.total_bytes_freed += cleanup_stats['bytes_freed']
        self.last_cleanup = datetime.now()
        
        cleanup_stats['cleanup_time_ms'] = (datetime.now() - start_time).total_seconds() * 1000
        
        self.logger.info(
            f"Cleanup complete: deleted {cleanup_stats['files_deleted']} files, "
            f"freed {cleanup_stats['bytes_freed'] / (1024**2):.2f}MB"
        )
        
        return cleanup_stats
    
    def _get_all_detection_files(self) -> List[Dict]:
        """Get all detection files with metadata"""
        files = []
        
        for dir_type, dir_path in self.config['detection_dirs'].items():
            if not os.path.exists(dir_path):
                continue
            
            try:
                for entry in os.scandir(dir_path):
                    if entry.is_file():
                        stat = entry.stat()
                        files.append({
                            'path': entry.path,
                            'name': entry.name,
                            'type': dir_type,
                            'size': stat.st_size,
                            'mtime': stat.st_mtime
                        })
            except Exception as e:
                self.logger.error(f"Error scanning {dir_path}: {e}")
        
        return files
    
    def _delete_corresponding_file(self, file_path: str):
        """Delete corresponding frame/plate file"""
        try:
            # Extract detection ID from filename
            filename = os.path.basename(file_path)
            if '_frame.jpg' in filename:
                # This is a frame, delete corresponding plate
                detection_id = filename.replace('_frame.jpg', '')
                plate_path = os.path.join(
                    self.config['detection_dirs']['plates'],
                    f"{detection_id}_plate.jpg"
                )
                if os.path.exists(plate_path):
                    os.remove(plate_path)
                    
            elif '_plate.jpg' in filename:
                # This is a plate, delete corresponding frame
                detection_id = filename.replace('_plate.jpg', '')
                frame_path = os.path.join(
                    self.config['detection_dirs']['frames'],
                    f"{detection_id}_frame.jpg"
                )
                if os.path.exists(frame_path):
                    os.remove(frame_path)
                    
        except Exception as e:
            self.logger.debug(f"Could not delete corresponding file for {file_path}: {e}")
    
    def get_storage_report(self) -> Dict:
        """Get comprehensive storage report"""
        stats = self.get_storage_usage()
        
        return {
            'current_usage': stats,
            'limits': {
                'max_storage_gb': self.config['max_storage_gb'],
                'cleanup_threshold_gb': self.config['cleanup_threshold_gb']
            },
            'cleanup_history': {
                'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None,
                'total_cleanups': self.total_cleanups,
                'total_files_deleted': self.total_files_deleted,
                'total_gb_freed': self.total_bytes_freed / (1024**3)
            },
            'health_status': self._get_health_status(stats)
        }
    
    def _get_health_status(self, stats: Dict) -> str:
        """Determine storage health status"""
        percentage = stats['percentage_used']
        
        if percentage >= 100:
            return 'critical'
        elif percentage >= 90:
            return 'warning'
        elif percentage >= 75:
            return 'attention'
        else:
            return 'healthy'
    
    def emergency_cleanup(self) -> Dict:
        """Emergency cleanup - delete oldest 50% of files"""
        self.logger.warning("Running emergency cleanup!")
        
        all_files = self._get_all_detection_files()
        all_files.sort(key=lambda x: x['mtime'])  # Oldest first
        
        # Delete oldest 50%
        files_to_delete = len(all_files) // 2
        cleanup_stats = {
            'files_deleted': 0,
            'bytes_freed': 0
        }
        
        for file_info in all_files[:files_to_delete]:
            try:
                os.remove(file_info['path'])
                cleanup_stats['files_deleted'] += 1
                cleanup_stats['bytes_freed'] += file_info['size']
                self._delete_corresponding_file(file_info['path'])
            except Exception as e:
                self.logger.error(f"Emergency cleanup error: {e}")
        
        self.logger.info(
            f"Emergency cleanup: deleted {cleanup_stats['files_deleted']} files, "
            f"freed {cleanup_stats['bytes_freed'] / (1024**3):.2f}GB"
        )
        
        return cleanup_stats