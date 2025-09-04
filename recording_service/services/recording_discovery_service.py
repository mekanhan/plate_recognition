"""
Recording Discovery Service
Implements recordings-first approach for playback architecture
Scans filesystem to discover all recordings regardless of camera database status
"""
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class RecordingDiscoveryService:
    """Service for discovering and managing all recordings on the filesystem"""
    
    def __init__(self, recordings_dir: str = "recordings", db_service=None):
        """
        Initialize recording discovery service
        
        Args:
            recordings_dir: Base directory for all recordings
            db_service: Database service for enriching with camera metadata
        """
        self.recordings_dir = Path(recordings_dir)
        self.db_service = db_service
        self._cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache
        
    async def get_all_recording_sources(self, 
                                       include_deleted: bool = True,
                                       include_empty: bool = False) -> List[Dict]:
        """
        Get all cameras that have recordings, regardless of database status
        
        Args:
            include_deleted: Include cameras not in database (orphaned recordings)
            include_empty: Include cameras with no recordings
            
        Returns:
            List of recording sources with metadata
        """
        sources = []
        
        # Scan filesystem for all camera directories
        if not self.recordings_dir.exists():
            logger.warning(f"Recordings directory does not exist: {self.recordings_dir}")
            return sources
            
        try:
            # Get all camera directories
            camera_dirs = [d for d in self.recordings_dir.iterdir() if d.is_dir()]
            
            # Get active cameras from database if available
            active_cameras = {}
            if self.db_service:
                try:
                    cameras = await self.db_service.get_all_cameras()
                    # Cameras are now dictionaries from Foundation Database Service
                    for cam in cameras:
                        camera_data = {
                            'id': cam.get('id'),
                            'camera_id': cam['camera_id'],  # The actual working camera_id
                            'name': cam['name'],
                            'ip_address': cam.get('ip_address'),
                            'status': cam['status']
                        }
                        
                        # Handle all possible camera directory formats:
                        # 1. Legacy formats with camera prefix
                        camera_key1 = f"camera_{cam.get('id')}"
                        camera_key2 = f"camera_camera_{cam.get('id')}"
                        active_cameras[camera_key1] = camera_data
                        active_cameras[camera_key2] = camera_data
                        
                        # 2. Direct camera_id (if different from above)
                        if cam.get('id') not in [camera_key1, camera_key2]:
                            active_cameras[cam.get('id')] = camera_data
                        
                        # 3. Stable camera ID (most important for new system)
                        if cam.get('stable_camera_id'):
                            active_cameras[cam['stable_camera_id']] = camera_data
                except Exception as e:
                    logger.error(f"Failed to get cameras from database: {e}")
            
            # Process each camera directory
            for camera_dir in camera_dirs:
                camera_id = camera_dir.name
                
                # Skip if not including deleted and camera not in DB
                if not include_deleted and camera_id not in active_cameras:
                    continue
                
                # Get recording stats for this camera
                stats = await self._get_recording_stats(camera_dir)
                
                # Skip if no recordings and not including empty
                if not include_empty and stats['recording_count'] == 0:
                    continue
                
                # Build source entry
                source = {
                    'camera_id': camera_id,
                    'has_recordings': stats['recording_count'] > 0,
                    'is_active': camera_id in active_cameras,
                    'status': 'active' if camera_id in active_cameras else 'deleted',
                    'recording_count': stats['recording_count'],
                    'storage_used_mb': stats['storage_used_mb'],
                    'first_recording': stats['first_recording'],
                    'last_recording': stats['last_recording'],
                    'date_range': stats['date_range']
                }
                
                # Add camera metadata if available
                if camera_id in active_cameras:
                    cam = active_cameras[camera_id]
                    source['display_name'] = cam.get('name', f'Camera {camera_id[:8]}')
                    source['ip_address'] = cam.get('ip_address', '')
                    source['camera_status'] = cam.get('status', 'unknown')
                    # Include original database camera_id for frontend matching
                    source['database_camera_id'] = cam.get('camera_id')
                else:
                    # For archived cameras, generate name from camera_id
                    if camera_id.startswith('camera_'):
                        # Remove camera_ prefix for display
                        display_id = camera_id.replace('camera_', '')
                        source['display_name'] = f'Archived Camera {display_id[:8]}'
                    else:
                        source['display_name'] = f'Archived Camera {camera_id[:8]}'
                    source['ip_address'] = ''
                    source['camera_status'] = 'deleted'
                    source['database_camera_id'] = None
                
                sources.append(source)
            
            # Handle duplicate names by adding numbers
            name_counts = {}
            for source in sources:
                name = source['display_name']
                name_counts[name] = name_counts.get(name, 0) + 1
            
            # Add numbering for duplicates
            name_instances = {}
            for source in sources:
                name = source['display_name']
                if name_counts[name] > 1:
                    name_instances[name] = name_instances.get(name, 0) + 1
                    if name_instances[name] == 1:
                        # First instance keeps original name
                        pass
                    else:
                        # Add number for subsequent instances
                        source['display_name'] = f"{name} ({name_instances[name]})"
            
            # Sort by status (active first) then by name
            sources.sort(key=lambda x: (x['status'] != 'active', x['display_name']))
            
            logger.info(f"Discovered {len(sources)} recording sources")
            return sources
            
        except Exception as e:
            logger.error(f"Error discovering recording sources: {e}")
            return []
    
    async def _get_recording_stats(self, camera_dir: Path) -> Dict:
        """
        Get statistics for recordings in a camera directory
        
        Args:
            camera_dir: Path to camera directory
            
        Returns:
            Dictionary with recording statistics
        """
        stats = {
            'recording_count': 0,
            'storage_used_mb': 0,
            'first_recording': None,
            'last_recording': None,
            'date_range': []
        }
        
        try:
            recordings = []
            dates_with_recordings = set()
            
            # Walk through all subdirectories
            for root, dirs, files in os.walk(camera_dir):
                for file in files:
                    if file.endswith('.mp4') or file.endswith('.avi'):
                        file_path = Path(root) / file
                        
                        # Get file stats
                        file_stat = file_path.stat()
                        stats['recording_count'] += 1
                        stats['storage_used_mb'] += file_stat.st_size / (1024 * 1024)
                        
                        # Extract timestamp from filename
                        timestamp = self._extract_timestamp_from_filename(file)
                        if timestamp:
                            recordings.append(timestamp)
                            dates_with_recordings.add(timestamp.date())
            
            # Calculate date range
            if recordings:
                recordings.sort()
                stats['first_recording'] = recordings[0].isoformat()
                stats['last_recording'] = recordings[-1].isoformat()
                stats['date_range'] = [d.isoformat() for d in sorted(dates_with_recordings)]
            
            # Round storage to 2 decimal places
            stats['storage_used_mb'] = round(stats['storage_used_mb'], 2)
            
        except Exception as e:
            logger.error(f"Error getting stats for {camera_dir}: {e}")
        
        return stats
    
    def _extract_timestamp_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract timestamp from recording filename
        Formats: 
        - camera_<id>_YYYYMMDD_HHMMSS.mp4
        - recording_YYYYMMDD_HHMMSS.mp4
        
        Args:
            filename: Recording filename
            
        Returns:
            Datetime object or None if parsing fails
        """
        try:
            # Remove extension
            name = filename.replace('.mp4', '').replace('.avi', '')
            
            # Extract date and time parts (last two parts)
            parts = name.split('_')
            if len(parts) >= 2:
                # Get the last two parts which should be date and time
                date_str = parts[-2]  # YYYYMMDD
                time_str = parts[-1]  # HHMMSS
                
                # Validate format
                if len(date_str) == 8 and len(time_str) == 6:
                    # Parse datetime
                    dt_str = f"{date_str}{time_str}"
                    return datetime.strptime(dt_str, "%Y%m%d%H%M%S")
        except Exception as e:
            logger.debug(f"Failed to extract timestamp from {filename}: {e}")
        
        return None
    
    async def get_orphaned_recordings(self) -> List[Dict]:
        """
        Get recordings from cameras that no longer exist in the database
        
        Returns:
            List of orphaned recording sources
        """
        all_sources = await self.get_all_recording_sources(include_deleted=True)
        return [s for s in all_sources if s['status'] == 'deleted']
    
    async def calculate_storage_usage(self, camera_id: Optional[str] = None) -> Dict:
        """
        Calculate storage usage for a specific camera or all cameras
        
        Args:
            camera_id: Specific camera ID or None for all cameras
            
        Returns:
            Storage usage statistics
        """
        usage = {
            'total_mb': 0,
            'active_cameras_mb': 0,
            'deleted_cameras_mb': 0,
            'cameras': {}
        }
        
        sources = await self.get_all_recording_sources(include_deleted=True)
        
        for source in sources:
            if camera_id and source['camera_id'] != camera_id and source.get('database_camera_id') != camera_id:
                continue
            
            storage_mb = source['storage_used_mb']
            usage['total_mb'] += storage_mb
            
            if source['is_active']:
                usage['active_cameras_mb'] += storage_mb
            else:
                usage['deleted_cameras_mb'] += storage_mb
            
            usage['cameras'][source['camera_id']] = {
                'storage_mb': storage_mb,
                'recording_count': source['recording_count'],
                'is_active': source['is_active'],
                'display_name': source['display_name']
            }
        
        # Round all values
        usage['total_mb'] = round(usage['total_mb'], 2)
        usage['active_cameras_mb'] = round(usage['active_cameras_mb'], 2)
        usage['deleted_cameras_mb'] = round(usage['deleted_cameras_mb'], 2)
        
        return usage
    
    async def cleanup_orphaned_recordings(self, 
                                        older_than_days: int = 30,
                                        dry_run: bool = True) -> Dict:
        """
        Clean up recordings from deleted cameras older than specified days
        
        Args:
            older_than_days: Delete recordings older than this many days
            dry_run: If True, only simulate deletion
            
        Returns:
            Cleanup operation results
        """
        from datetime import timedelta
        
        results = {
            'dry_run': dry_run,
            'older_than_days': older_than_days,
            'files_to_delete': [],
            'space_to_free_mb': 0,
            'errors': []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            orphaned = await self.get_orphaned_recordings()
            
            for source in orphaned:
                camera_dir = self.recordings_dir / source['camera_id']
                
                # Walk through recordings
                for root, dirs, files in os.walk(camera_dir):
                    for file in files:
                        if not file.endswith('.mp4'):
                            continue
                        
                        file_path = Path(root) / file
                        
                        # Check age
                        timestamp = self._extract_timestamp_from_filename(file)
                        if timestamp and timestamp < cutoff_date:
                            file_stat = file_path.stat()
                            size_mb = file_stat.st_size / (1024 * 1024)
                            
                            results['files_to_delete'].append(str(file_path))
                            results['space_to_free_mb'] += size_mb
                            
                            if not dry_run:
                                try:
                                    file_path.unlink()
                                    logger.info(f"Deleted orphaned recording: {file_path}")
                                except Exception as e:
                                    results['errors'].append(f"Failed to delete {file_path}: {e}")
            
            results['space_to_free_mb'] = round(results['space_to_free_mb'], 2)
            results['file_count'] = len(results['files_to_delete'])
            
            if dry_run:
                logger.info(f"Dry run: Would delete {results['file_count']} files, "
                          f"freeing {results['space_to_free_mb']} MB")
            else:
                logger.info(f"Deleted {results['file_count']} orphaned recordings, "
                          f"freed {results['space_to_free_mb']} MB")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            results['errors'].append(str(e))
        
        return results
    
    async def get_recording_inventory_cached(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get cached recording inventory with automatic refresh
        
        Args:
            force_refresh: Force cache refresh
            
        Returns:
            Cached recording sources
        """
        now = datetime.now()
        
        # Check if cache is valid
        if (not force_refresh and 
            self._cache_timestamp and 
            (now - self._cache_timestamp).seconds < self._cache_ttl):
            return self._cache.get('sources', [])
        
        # Refresh cache
        sources = await self.get_all_recording_sources()
        self._cache = {'sources': sources}
        self._cache_timestamp = now
        
        return sources
    
    async def get_all_recording_dates(self) -> List[str]:
        """
        Get all dates that have recordings from any camera.
        
        Returns:
            List of date strings in YYYY-MM-DD format
        """
        try:
            sources = await self.get_all_recording_sources()
            all_dates = set()
            
            for source in sources:
                if source.get('date_range'):
                    all_dates.update(source['date_range'])
            
            # Sort dates chronologically
            sorted_dates = sorted(list(all_dates))
            logger.info(f"Found recordings on {len(sorted_dates)} dates")
            return sorted_dates
            
        except Exception as e:
            logger.error(f"Error getting recording dates: {e}")
            return []
    
    async def get_cameras_for_date(self, date: str) -> List[Dict]:
        """
        Get all cameras that have recordings on a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            List of camera sources with recordings on that date
        """
        try:
            sources = await self.get_all_recording_sources()
            cameras_for_date = []
            
            for source in sources:
                if date in source.get('date_range', []):
                    # Create a copy with date-specific info if needed
                    camera_info = source.copy()
                    cameras_for_date.append(camera_info)
            
            logger.info(f"Found {len(cameras_for_date)} cameras with recordings on {date}")
            return cameras_for_date
            
        except Exception as e:
            logger.error(f"Error getting cameras for date {date}: {e}")
            return []