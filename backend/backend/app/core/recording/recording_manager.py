"""
Recording Manager for 24/7 Recording System
Manages multiple camera recorders with storage integration
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .continuous_recorder import ContinuousRecorder
from ..storage import StorageManager, StorageConfig

logger = logging.getLogger(__name__)


class RecordingManager:
    """Manages continuous recording for multiple cameras"""
    
    def __init__(self, config_file: Optional[str] = None, storage_config: Optional[StorageConfig] = None):
        self.config_file = config_file or "config/cameras.json"
        self.recorders: Dict[int, ContinuousRecorder] = {}
        self.camera_configs: Dict[int, Dict] = {}
        
        # Initialize storage manager
        self.storage_manager = StorageManager(storage_config or StorageConfig())
        
        # Load camera configurations
        self._load_camera_configs()
        
        logger.info(f"Recording manager initialized with {len(self.camera_configs)} cameras")
    
    def _load_camera_configs(self):
        """Load camera configurations from file"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    
                for camera in data.get('cameras', []):
                    self.camera_configs[camera['id']] = camera
                    
                logger.info(f"Loaded {len(self.camera_configs)} camera configurations")
            else:
                logger.warning(f"Camera config file not found: {self.config_file}")
                
        except Exception as e:
            logger.error(f"Error loading camera configs: {e}")
    
    async def start_all_recordings(self):
        """Start recording for all configured cameras"""
        logger.info("Starting all camera recordings...")
        
        # Start storage manager
        await self.storage_manager.start()
        
        # Start recorders for each camera
        for camera_id, config in self.camera_configs.items():
            if config.get('enabled', True):
                await self.start_recording(camera_id)
        
        active_count = len([r for r in self.recorders.values() if r.is_recording])
        logger.info(f"Started recording for {active_count} cameras with storage management")
    
    async def stop_all_recordings(self):
        """Stop all active recordings"""
        logger.info("Stopping all camera recordings...")
        
        # Stop all recorders
        for camera_id in list(self.recorders.keys()):
            await self.stop_recording(camera_id)
        
        # Stop storage manager
        await self.storage_manager.stop()
        
        logger.info("All recordings stopped")
    
    async def start_recording(self, camera_id: int) -> bool:
        """
        Start recording for a specific camera
        
        Args:
            camera_id: Camera ID to start recording
            
        Returns:
            True if started successfully
        """
        try:
            if camera_id in self.recorders and self.recorders[camera_id].is_recording:
                logger.warning(f"Camera {camera_id} is already recording")
                return True
            
            config = self.camera_configs.get(camera_id)
            if not config:
                logger.error(f"No configuration found for camera {camera_id}")
                return False
            
            # Create recorder
            recorder = ContinuousRecorder(
                camera_id=camera_id,
                camera_url=config['url'],
                output_dir="recordings",
                segment_duration=config.get('segment_duration', 600),
                buffer_size=config.get('buffer_size', 300)
            )
            
            # Start recording
            recorder.start()
            self.recorders[camera_id] = recorder
            
            logger.info(f"Started recording for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording for camera {camera_id}: {e}")
            return False
    
    async def stop_recording(self, camera_id: int) -> bool:
        """
        Stop recording for a specific camera
        
        Args:
            camera_id: Camera ID to stop recording
            
        Returns:
            True if stopped successfully
        """
        try:
            if camera_id not in self.recorders:
                logger.warning(f"No recorder found for camera {camera_id}")
                return True
            
            recorder = self.recorders[camera_id]
            recorder.stop()
            
            del self.recorders[camera_id]
            
            logger.info(f"Stopped recording for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording for camera {camera_id}: {e}")
            return False
    
    async def health_check(self):
        """Perform health check on all recorders"""
        try:
            # Check each recorder
            failed_cameras = []
            
            for camera_id, recorder in list(self.recorders.items()):
                if not recorder.is_recording:
                    failed_cameras.append(camera_id)
            
            # Restart failed recorders
            for camera_id in failed_cameras:
                logger.warning(f"Camera {camera_id} failed health check, restarting...")
                await self.stop_recording(camera_id)
                await self.start_recording(camera_id)
            
            # Log storage health
            storage_health = await self.storage_manager.monitor_storage_health()
            if storage_health.get('status') == 'critical':
                logger.critical(f"Storage critical: {storage_health.get('disk_used_percent', 0):.1f}% full")
            elif storage_health.get('status') == 'warning':
                logger.warning(f"Storage warning: {storage_health.get('disk_used_percent', 0):.1f}% full")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def get_recorder(self, camera_id: int) -> Optional[ContinuousRecorder]:
        """Get recorder for a specific camera"""
        return self.recorders.get(camera_id)
    
    def get_status(self, camera_id: int) -> Dict[str, Any]:
        """Get status for a specific camera"""
        recorder = self.recorders.get(camera_id)
        if recorder:
            return recorder.get_status()
        return {
            'camera_id': camera_id,
            'is_recording': False,
            'error': 'No recorder found'
        }
    
    def get_all_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status for all cameras"""
        status = {}
        for camera_id in self.camera_configs:
            status[camera_id] = self.get_status(camera_id)
        return status
    
    async def get_storage_report(self) -> Dict:
        """Get storage report from storage manager"""
        return await self.storage_manager.get_storage_report()
    
    async def get_camera_storage_stats(self, camera_id: int):
        """Get storage statistics for a specific camera"""
        return await self.storage_manager.get_camera_storage_stats(camera_id)
    
    async def cleanup_old_recordings(self, camera_id: Optional[int] = None) -> Dict:
        """Trigger manual cleanup of old recordings"""
        return await self.storage_manager.cleanup_old_recordings(camera_id)