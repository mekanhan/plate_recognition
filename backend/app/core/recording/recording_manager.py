"""
Recording Manager - Manages multiple camera recorders
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from .continuous_recorder import ContinuousRecorder
from ..storage.storage_manager import StorageManager, StorageConfig

logger = logging.getLogger(__name__)


class RecordingManager:
    """Manages continuous recording for multiple cameras"""
    
    def __init__(self, config_file: Optional[str] = None, storage_config: Optional[StorageConfig] = None):
        """Initialize the recording manager
        
        Args:
            config_file: Path to camera configuration file
            storage_config: Storage configuration object
        """
        self.recorders: Dict[int, ContinuousRecorder] = {}
        self.config_file = config_file or "config/cameras.json"
        self.is_running = False
        
        # Initialize storage manager
        self.storage_manager = StorageManager(storage_config or StorageConfig())
        logger.info("Recording manager initialized with storage management")
        
    async def start_all_recordings(self):
        """Start recording for all configured cameras"""
        logger.info("Starting all camera recordings...")
        
        try:
            # Start storage manager first
            await self.storage_manager.start()
            logger.info("Storage manager started")
            
            cameras = await self.load_camera_configs()
            
            for camera in cameras:
                if camera.get('recording_enabled', True):
                    await self.start_camera_recording(camera)
                else:
                    logger.info(f"Skipping camera {camera['id']} - recording disabled")
            
            self.is_running = True
            logger.info(f"Started recording for {len(self.recorders)} cameras with storage management")
            
        except Exception as e:
            logger.error(f"Failed to start recordings: {e}")
            # Stop storage manager if startup failed
            if hasattr(self, 'storage_manager'):
                await self.storage_manager.stop()
            raise
    
    async def start_camera_recording(self, camera_config: Dict[str, Any]):
        """Start recording for a specific camera
        
        Args:
            camera_config: Camera configuration dictionary
        """
        camera_id = camera_config['id']
        
        try:
            if camera_id in self.recorders:
                logger.warning(f"Camera {camera_id} is already recording")
                return
            
            # Create recorder instance
            recorder = ContinuousRecorder(camera_config)
            self.recorders[camera_id] = recorder
            
            # Start recording
            await recorder.start_recording()
            logger.info(f"Started recording for camera {camera_id}: {camera_config.get('name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to start recording for camera {camera_id}: {e}")
            # Remove from recorders if failed
            if camera_id in self.recorders:
                del self.recorders[camera_id]
            raise
    
    def stop_camera_recording(self, camera_id: int):
        """Stop recording for a specific camera
        
        Args:
            camera_id: ID of the camera to stop recording
        """
        if camera_id in self.recorders:
            logger.info(f"Stopping recording for camera {camera_id}")
            self.recorders[camera_id].stop_recording()
            del self.recorders[camera_id]
        else:
            logger.warning(f"Camera {camera_id} is not currently recording")
    
    async def stop_all_recordings(self):
        """Stop all active recordings"""
        logger.info("Stopping all camera recordings...")
        
        # Stop all recorders
        camera_ids = list(self.recorders.keys())
        for camera_id in camera_ids:
            self.stop_camera_recording(camera_id)
        
        # Stop storage manager
        await self.storage_manager.stop()
        logger.info("Storage manager stopped")
        
        self.is_running = False
        logger.info("All recordings and storage management stopped")
    
    async def load_camera_configs(self) -> List[Dict[str, Any]]:
        """Load camera configurations from file or database
        
        Returns:
            List of camera configuration dictionaries
        """
        # For now, load from JSON file
        # In production, this would load from database
        config_path = Path(self.config_file)
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('cameras', [])
        else:
            # Return demo camera config if no config file
            logger.warning(f"Config file {self.config_file} not found, using demo configuration")
            return [
                {
                    'id': 3,
                    'name': 'Test Camera 1',
                    'rtsp_url': 'rtsp://admin:Mekus_1987@10.0.0.181:554/h264Preview_01_sub',
                    'recording_enabled': True
                }
            ]
    
    async def health_check(self):
        """Perform health check on all recorders and storage"""
        unhealthy_cameras = []
        
        for camera_id, recorder in self.recorders.items():
            status = recorder.get_status()
            
            # Check if recording is active
            if not status['is_recording']:
                unhealthy_cameras.append(camera_id)
                logger.warning(f"Camera {camera_id} is not recording")
            
            # Check queue size (indicates if frames are being processed)
            elif status['queue_size'] > 250:  # Near max capacity
                logger.warning(f"Camera {camera_id} queue is getting full: {status['queue_size']}")
        
        # Restart unhealthy cameras
        for camera_id in unhealthy_cameras:
            logger.info(f"Attempting to restart recording for camera {camera_id}")
            # Get camera config and restart
            cameras = await self.load_camera_configs()
            camera_config = next((c for c in cameras if c['id'] == camera_id), None)
            
            if camera_config:
                self.stop_camera_recording(camera_id)
                await asyncio.sleep(2)  # Brief pause before restart
                await self.start_camera_recording(camera_config)
        
        # Log storage health summary
        try:
            total_stats = await self.storage_manager.get_total_storage_stats()
            logger.debug(f"Storage health: {total_stats.total_segments} segments, "
                        f"{self.storage_manager._format_bytes(total_stats.total_size_bytes)} used")
        except Exception as e:
            logger.error(f"Error getting storage health: {e}")
    
    def get_all_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all recorders
        
        Returns:
            Dictionary mapping camera IDs to their status
        """
        return {
            camera_id: recorder.get_status() 
            for camera_id, recorder in self.recorders.items()
        }
    
    def get_camera_status(self, camera_id: int) -> Optional[Dict[str, Any]]:
        """Get status of a specific camera recorder
        
        Args:
            camera_id: ID of the camera
            
        Returns:
            Camera status dictionary or None if not recording
        """
        if camera_id in self.recorders:
            return self.recorders[camera_id].get_status()
        return None
    
    async def get_storage_report(self) -> Dict[str, Any]:
        """Get comprehensive storage report from storage manager
        
        Returns:
            Storage report dictionary
        """
        return await self.storage_manager.get_storage_report()
    
    async def get_camera_storage_stats(self, camera_id: int):
        """Get storage statistics for a specific camera
        
        Args:
            camera_id: Camera ID
            
        Returns:
            Storage statistics for the camera
        """
        return await self.storage_manager.get_camera_storage_stats(camera_id)
    
    async def cleanup_camera_storage(self, camera_id: int) -> Dict[str, Any]:
        """Force cleanup of a specific camera's storage
        
        Args:
            camera_id: Camera ID to clean up
            
        Returns:
            Cleanup results
        """
        return await self.storage_manager.force_cleanup_camera(camera_id)
    
    def get_storage_manager(self) -> StorageManager:
        """Get the storage manager instance
        
        Returns:
            StorageManager instance
        """
        return self.storage_manager