"""
Test script for the recording service
"""
import asyncio
import logging
import sys
from app.core.recording.recording_manager import RecordingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def test_recording():
    """Test the recording functionality"""
    logger.info("Starting recording test...")
    
    # Create recording manager
    manager = RecordingManager()
    
    try:
        # Start recordings
        await manager.start_all_recordings()
        
        # Run for 30 seconds
        logger.info("Recording for 30 seconds...")
        for i in range(6):
            await asyncio.sleep(5)
            status = manager.get_all_status()
            for camera_id, cam_status in status.items():
                logger.info(f"Camera {camera_id}: Recording={cam_status['is_recording']}, Queue={cam_status['queue_size']}")
        
        # Stop recordings
        await manager.stop_all_recordings()
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        await manager.stop_all_recordings()


if __name__ == "__main__":
    asyncio.run(test_recording())