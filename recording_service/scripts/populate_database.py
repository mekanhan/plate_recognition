#!/usr/bin/env python3
"""
Populate Database Script
Scans existing recording files and populates database with metadata
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import re
import logging

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from database.models import VideoRecording, DailySummary
from database.service import DatabaseService
from recording_service.services.storage_manager import StorageManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePopulator:
    def __init__(self, recordings_path: str):
        self.recordings_path = Path(recordings_path)
        self.db_service = DatabaseService()
        
    async def populate_all(self):
        """Populate database with all existing recordings"""
        logger.info("Starting database population...")
        
        # Initialize database
        await self.db_service.init_db()
        
        # Find all video files (both AVI and MP4 formats)
        video_files = list(self.recordings_path.glob("**/*.avi")) + list(self.recordings_path.glob("**/*.mp4"))
        logger.info(f"Found {len(video_files)} video files")
        
        # Process each file
        processed = 0
        skipped = 0
        
        async with self.db_service.async_session() as session:
            for video_file in video_files:
                try:
                    # Check if already in database
                    existing = await session.execute(
                        text("SELECT id FROM video_recordings WHERE filename = :filename"),
                        {"filename": video_file.name}
                    )
                    if existing.fetchone():
                        skipped += 1
                        continue
                    
                    # Parse filename to get metadata
                    metadata = self.parse_filename(video_file)
                    if not metadata:
                        logger.warning(f"Could not parse filename: {video_file.name}")
                        continue
                    
                    # Get file stats
                    file_stats = video_file.stat()
                    
                    # Create database record
                    record = VideoRecording(
                        filename=video_file.name,
                        camera_id=metadata['camera_id'],
                        file_path=str(video_file),
                        start_time=metadata['start_time'],
                        end_time=metadata['start_time'] + timedelta(seconds=metadata['duration']),
                        duration_seconds=metadata['duration'],
                        file_size_bytes=file_stats.st_size,
                        video_codec='xvid',
                        video_width=640,  # Default for current recordings
                        video_height=360,  # Default for current recordings
                        video_fps=30,
                        is_compressed=True,
                        has_audio=False
                    )
                    
                    session.add(record)
                    processed += 1
                    
                    if processed % 100 == 0:
                        await session.commit()
                        logger.info(f"Processed {processed} files...")
                
                except Exception as e:
                    logger.error(f"Error processing {video_file}: {e}")
            
            # Final commit
            await session.commit()
        
        logger.info(f"Database population complete: {processed} processed, {skipped} skipped")
        
        # Generate daily summaries
        await self.generate_daily_summaries()
        
    def parse_filename(self, video_file: Path) -> dict:
        """Parse filename to extract metadata"""
        # Expected format: camera_camera_946701d3_20250802_022919_600.avi or .mp4
        pattern = r'camera_(.+)_(\d{8})_(\d{6})_(\d+)\.(avi|mp4)'
        match = re.match(pattern, video_file.name)
        
        if not match:
            return None
        
        camera_id, date_str, time_str, duration_str, file_ext = match.groups()
        
        # Parse date and time
        date_time_str = f"{date_str}_{time_str}"
        start_time = datetime.strptime(date_time_str, "%Y%m%d_%H%M%S")
        duration = int(duration_str)
        
        return {
            'camera_id': camera_id,
            'start_time': start_time,
            'duration': duration
        }
    
    async def generate_daily_summaries(self):
        """Generate daily summary records"""
        logger.info("Generating daily summaries...")
        
        async with self.db_service.async_session() as session:
            # Get all recording dates grouped by camera and date
            query = """
                SELECT 
                    camera_id,
                    date(start_time) as recording_date,
                    COUNT(*) as segment_count,
                    SUM(duration_seconds) as total_duration,
                    SUM(file_size_bytes) as total_size,
                    MIN(start_time) as first_segment,
                    MAX(start_time) as last_segment
                FROM video_recordings
                GROUP BY camera_id, date(start_time)
            """
            
            result = await session.execute(text(query))
            rows = result.fetchall()
            
            for row in rows:
                camera_id, date_str, count, total_duration, total_size, first_time, last_time = row
                
                # Calculate coverage percentage (assuming 24 hours = 86400 seconds)
                coverage_percentage = min(100.0, (total_duration / 86400.0) * 100.0)
                
                # Create daily summary record
                summary = DailySummary(
                    camera_id=camera_id,
                    date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                    total_segments=count,
                    total_duration_seconds=total_duration,
                    total_size_bytes=total_size,
                    first_segment_time=datetime.fromisoformat(first_time.replace('Z', '+00:00')) if first_time else None,
                    last_segment_time=datetime.fromisoformat(last_time.replace('Z', '+00:00')) if last_time else None,
                    coverage_percentage=round(coverage_percentage, 1),
                    gaps_count=0,  # Would need more complex calculation
                    gaps_duration_seconds=0
                )
                
                session.add(summary)
            
            await session.commit()
            logger.info(f"Generated {len(rows)} daily summaries")

async def main():
    """Main entry point"""
    recordings_path = "recordings"
    
    if not Path(recordings_path).exists():
        logger.error(f"Recordings path does not exist: {recordings_path}")
        return
    
    populator = DatabasePopulator(recordings_path)
    await populator.populate_all()
    
    logger.info("Database population complete!")

if __name__ == "__main__":
    asyncio.run(main())