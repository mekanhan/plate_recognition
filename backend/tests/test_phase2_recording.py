#!/usr/bin/env python3
"""
Test script for Phase 2 24/7 Recording System
Tests storage management and playback functionality
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from app.core.storage.storage_manager import StorageManager, StorageConfig
from app.core.playback.video_playback import VideoPlayback
from app.core.recording.recording_manager import RecordingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_storage_manager():
    """Test storage manager functionality"""
    logger.info("=" * 50)
    logger.info("Testing Storage Manager")
    logger.info("=" * 50)
    
    # Create storage manager with test config
    config = StorageConfig({
        'retention_days': 30,
        'hot_storage_days': 7,
        'max_storage_gb_per_camera': 100,
        'cleanup_interval_hours': 1
    })
    
    storage_manager = StorageManager(config)
    
    try:
        # Test storage stats
        logger.info("Getting total storage statistics...")
        total_stats = await storage_manager.get_total_storage_stats()
        logger.info(f"Total segments: {total_stats.total_segments}")
        logger.info(f"Total size: {storage_manager._format_bytes(total_stats.total_size_bytes)}")
        
        # Test camera-specific stats
        logger.info("Getting camera 3 storage statistics...")
        camera_stats = await storage_manager.get_camera_storage_stats(3)
        logger.info(f"Camera 3 segments: {camera_stats.total_segments}")
        logger.info(f"Camera 3 size: {storage_manager._format_bytes(camera_stats.total_size_bytes)}")
        
        # Test storage report
        logger.info("Generating storage report...")
        report = await storage_manager.get_storage_report()
        if "error" not in report:
            logger.info(f"Report generated successfully at {report['generated_at']}")
            logger.info(f"System has {report['system_stats']['total_segments']} total segments")
        else:
            logger.error(f"Storage report error: {report['error']}")
        
        logger.info("✅ Storage Manager tests completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Storage Manager test failed: {e}")


async def test_video_playback():
    """Test video playback functionality"""
    logger.info("=" * 50)
    logger.info("Testing Video Playback")
    logger.info("=" * 50)
    
    playback = VideoPlayback()
    
    try:
        # Test timeline retrieval
        logger.info("Testing timeline retrieval...")
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()
        
        segments = await playback.get_camera_timeline(3, start_time, end_time)
        logger.info(f"Found {len(segments)} segments for camera 3")
        
        if segments:
            # Test segment details
            first_segment = segments[0]
            logger.info(f"First segment: {first_segment.filename}")
            logger.info(f"Duration: {first_segment.duration_seconds} seconds")
            logger.info(f"File exists: {first_segment.exists}")
            
            # Test segment retrieval by ID
            logger.info("Testing segment retrieval by ID...")
            segment = await playback.get_segment_by_id(first_segment.id)
            if segment:
                logger.info(f"Retrieved segment: {segment.filename}")
            
            # Test playback info
            logger.info("Testing playback info...")
            target_time = first_segment.start_time + timedelta(minutes=5)
            playback_info = await playback.get_playback_info(3, target_time)
            if playback_info:
                logger.info(f"Playback info found for {target_time}")
                logger.info(f"Offset: {playback_info['offset_seconds']} seconds")
        
        # Test available time ranges
        logger.info("Testing available time ranges...")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ranges = await playback.get_available_time_ranges(3, today)
        logger.info(f"Found {len(ranges)} time ranges for today")
        
        # Test recording search
        logger.info("Testing recording search...")
        search_start = datetime.now() - timedelta(days=2)
        search_end = datetime.now()
        recordings = await playback.search_recordings(3, search_start, search_end)
        logger.info(f"Found {len(recordings)} recordings in search")
        
        logger.info("✅ Video Playback tests completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Video Playback test failed: {e}")


async def test_integrated_system():
    """Test integrated recording system with Phase 2 features"""
    logger.info("=" * 50)
    logger.info("Testing Integrated System")
    logger.info("=" * 50)
    
    try:
        # Create storage config
        storage_config = StorageConfig({
            'retention_days': 30,
            'cleanup_interval_hours': 24,  # Daily cleanup for test
            'monitoring_interval_minutes': 60  # Hourly monitoring for test
        })
        
        # Create recording manager with storage integration
        recording_manager = RecordingManager(storage_config=storage_config)
        
        # Test storage integration
        logger.info("Testing storage integration...")
        storage_report = await recording_manager.get_storage_report()
        if "error" not in storage_report:
            logger.info("Storage integration working correctly")
            logger.info(f"Total storage: {storage_report['system_stats']['total_size_formatted']}")
        
        # Test camera storage stats
        logger.info("Testing camera storage stats...")
        camera_stats = await recording_manager.get_camera_storage_stats(3)
        logger.info(f"Camera 3 storage: {recording_manager.storage_manager._format_bytes(camera_stats.total_size_bytes)}")
        
        logger.info("✅ Integrated System tests completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Integrated System test failed: {e}")


async def test_api_compatibility():
    """Test that our new components work with the existing system"""
    logger.info("=" * 50)
    logger.info("Testing API Compatibility")
    logger.info("=" * 50)
    
    try:
        # Test that recordings directory exists and has expected structure
        recordings_path = Path("recordings")
        if recordings_path.exists():
            logger.info(f"Recordings directory exists: {recordings_path}")
            
            # Check for camera directories
            camera_dirs = [d for d in recordings_path.iterdir() if d.is_dir() and d.name.startswith('camera_')]
            logger.info(f"Found {len(camera_dirs)} camera directories")
            
            for camera_dir in camera_dirs:
                # Check for index database
                index_db = camera_dir / "index.db"
                if index_db.exists():
                    logger.info(f"✅ Index database exists for {camera_dir.name}")
                else:
                    logger.warning(f"⚠️ No index database for {camera_dir.name}")
                
                # Check for video files
                video_files = list(camera_dir.rglob("*.avi")) + list(camera_dir.rglob("*.mp4"))
                logger.info(f"Found {len(video_files)} video files in {camera_dir.name}")
        else:
            logger.warning("No recordings directory found - this is expected for a fresh install")
        
        logger.info("✅ API Compatibility tests completed")
        
    except Exception as e:
        logger.error(f"❌ API Compatibility test failed: {e}")


async def main():
    """Run all Phase 2 tests"""
    logger.info("🚀 Starting Phase 2 Recording System Tests")
    logger.info(f"Test started at: {datetime.now().isoformat()}")
    
    # Ensure required directories exist
    Path("recordings").mkdir(exist_ok=True)
    Path("config").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Run all tests
    await test_storage_manager()
    await test_video_playback()
    await test_integrated_system()
    await test_api_compatibility()
    
    logger.info("=" * 50)
    logger.info("🎉 Phase 2 Recording System Tests Completed")
    logger.info(f"Test completed at: {datetime.now().isoformat()}")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        exit(1)