"""
Main 24/7 Recording Service
Runs independently to handle continuous camera recording
"""
import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

from app.core.recording.recording_manager import RecordingManager
from app.core.storage.storage_manager import StorageConfig
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/recording.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class RecordingService:
    """Main recording service that manages 24/7 recording"""
    
    def __init__(self):
        # Load storage configuration
        storage_config = self._load_storage_config()
        
        # Initialize recording manager with storage management
        self.recording_manager = RecordingManager(storage_config=storage_config)
        self.running = True
        
    async def start(self):
        """Start the recording service"""
        logger.info("=" * 60)
        logger.info("Starting 24/7 Recording Service")
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Start all camera recordings
            await self.recording_manager.start_all_recordings()
            logger.info("All recordings started successfully")
            
            # Main service loop
            while self.running:
                # Perform health check every 30 seconds
                await asyncio.sleep(30)
                
                if self.running:
                    await self._health_check()
                
        except Exception as e:
            logger.error(f"Service error: {e}", exc_info=True)
        finally:
            await self._shutdown()
    
    async def _health_check(self):
        """Perform health checks and restart failed recordings"""
        try:
            logger.debug("Performing health check...")
            await self.recording_manager.health_check()
            
            # Log current status
            all_status = self.recording_manager.get_all_status()
            logger.info(f"Health check complete. Active recordings: {len(all_status)}")
            
            for camera_id, status in all_status.items():
                logger.debug(f"Camera {camera_id}: Recording={status['is_recording']}, Queue={status['queue_size']}")
            
            # Log storage summary every 10th health check (5 minutes)
            if hasattr(self, '_health_check_count'):
                self._health_check_count += 1
            else:
                self._health_check_count = 1
            
            if self._health_check_count % 10 == 0:
                try:
                    total_stats = await self.recording_manager.storage_manager.get_total_storage_stats()
                    logger.info(f"Storage summary: {total_stats.total_segments} segments, "
                              f"{self.recording_manager.storage_manager._format_bytes(total_stats.total_size_bytes)} used")
                except Exception as e:
                    logger.debug(f"Could not get storage summary: {e}")
                
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def _shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down recording service...")
        
        try:
            await self.recording_manager.stop_all_recordings()
            logger.info("Recording service stopped successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
        
        logger.info("=" * 60)
        logger.info("24/7 Recording Service Stopped")
        logger.info(f"Stopped at: {datetime.now().isoformat()}")
        logger.info("=" * 60)
    
    def _load_storage_config(self) -> StorageConfig:
        """Load storage configuration from file
        
        Returns:
            StorageConfig object
        """
        config_path = Path("config/storage_settings.json")
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                storage_config = config_data.get('storage', {})
                logger.info(f"Loaded storage configuration from {config_path}")
                logger.info(f"Retention: {storage_config.get('retention_days', 30)} days")
                logger.info(f"Cleanup interval: {storage_config.get('cleanup_interval_hours', 1)} hours")
                
                return StorageConfig(storage_config)
                
            except Exception as e:
                logger.warning(f"Error loading storage config: {e}, using defaults")
                return StorageConfig()
        else:
            logger.info("No storage config file found, using default settings")
            return StorageConfig()


async def main():
    """Main entry point"""
    # Ensure directories exist
    Path("logs").mkdir(exist_ok=True)
    Path("recordings").mkdir(exist_ok=True)
    Path("config").mkdir(exist_ok=True)
    
    # Start the service
    service = RecordingService()
    await service.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)