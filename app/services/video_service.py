# app/services/video_service.py
import os
import cv2
import time
import asyncio
import datetime
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from app.repositories.sql_repository import SQLiteDetectionRepository, SQLiteVideoRepository

logger = logging.getLogger(__name__)

class VideoRecorder:
    """Low-level class for recording video frames"""
    
    def __init__(self, buffer_seconds: int = 5, post_event_seconds: int = 15, fps: int = 15, max_segment_minutes: int = 5):
        self.frame_buffer = []
        self.buffer_seconds = buffer_seconds
        self.post_event_seconds = post_event_seconds
        self.fps = fps
        self.buffer_frames = self.buffer_seconds * self.fps
        self.max_segment_seconds = max_segment_minutes * 60  # Convert to seconds
        
        # Recording state
        self.recording = False
        self.current_output = None
        self.current_video_path = None
        self.post_event_frames = 0
        
        # Performance monitoring
        self.frames_written = 0
        self.recording_start_time = None
    
    def add_frame(self, frame: np.ndarray, timestamp: float) -> bool:
        """
        Add a frame to the rolling buffer and recording if active
        
        Args:
            frame: Video frame as numpy array
            timestamp: Frame timestamp in seconds
            
        Returns:
            bool: True if recording should stop, False otherwise
        """
        # Add to rolling buffer
        self.frame_buffer.append((frame.copy(), timestamp))
        
        # Keep buffer at desired size
        while len(self.frame_buffer) > self.buffer_frames:
            self.frame_buffer.pop(0)
        
        # If currently recording, write frame to video
        if self.recording and self.current_output:
            self.current_output.write(frame)
            self.frames_written += 1
            
            # Increment post-event counter
            self.post_event_frames += 1
            
            # Check if segment should be closed due to time limit
            recording_duration = time.time() - self.recording_start_time if self.recording_start_time else 0
            segment_time_exceeded = recording_duration >= self.max_segment_seconds
            
            # Check if we've recorded enough frames after the event
            post_event_complete = self.post_event_frames >= self.post_event_seconds * self.fps
            
            # Return True if either condition is met (time limit or post-event complete)
            return segment_time_exceeded or post_event_complete
        
        return False
    
    def start_recording(self, video_path: str) -> Tuple[float, List]:
        """
        Start recording to the specified path
        
        Args:
            video_path: Path to save the video file
            
        Returns:
            Tuple of (start_timestamp, buffer_frames)
        """
        if self.recording:
            # Already recording
            return None, []
        
        # Set recording state
        self.recording = True
        self.current_video_path = video_path
        self.post_event_frames = 0
        self.frames_written = 0
        self.recording_start_time = time.time()
        
        # Get buffer frames to write
        buffer_frames = list(self.frame_buffer)
        buffer_start_time = buffer_frames[0][1] if buffer_frames else time.time()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        
        # Initialize video writer
        if buffer_frames:
            height, width = buffer_frames[0][0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or 'avc1' for H.264
            self.current_output = cv2.VideoWriter(
                video_path, fourcc, self.fps, (width, height))
            
            # Write buffered frames
            for buffered_frame, _ in buffer_frames:
                self.current_output.write(buffered_frame)
                self.frames_written += 1
        
        return buffer_start_time, buffer_frames
    
    def stop_recording(self) -> Tuple[str, int, float]:
        """
        Stop the current recording
        
        Returns:
            Tuple of (video_path, frames_written, duration)
        """
        if not self.recording:
            return None, 0, 0
        
        # Update recording state
        self.recording = False
        video_path = self.current_video_path
        frames_written = self.frames_written
        
        # Calculate duration
        duration = time.time() - self.recording_start_time if self.recording_start_time else 0
        
        # Release video writer
        if self.current_output:
            self.current_output.release()
            self.current_output = None
            
            # Force filesystem sync for WSL compatibility
            import subprocess
            try:
                subprocess.run(['sync'], check=False)
            except:
                pass
        
        # Reset recording state
        self.current_video_path = None
        self.post_event_frames = 0
        self.frames_written = 0
        self.recording_start_time = None
        
        return video_path, frames_written, duration

class VideoRecordingService:
    """Service for managing video recording of license plate detections"""
    
    def __init__(self, detection_repository: SQLiteDetectionRepository, 
                video_repository: SQLiteVideoRepository):
        self.detection_repository = detection_repository
        self.video_repository = video_repository
        
        # Create recorder
        self.recorder = VideoRecorder(buffer_seconds=5, post_event_seconds=15, fps=15)
        
        # Recording state
        self.current_segment_id = None
        self.current_detection_ids = []
        self.last_frame_time = None
        
        # Ensure video directory exists (use relative path for WSL compatibility)
        self.base_video_dir = "data/videos"
        os.makedirs(self.base_video_dir, exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize the video recording service"""
        logger.info("Initializing video recording service")
        
        # Create date-based directories
        await self._ensure_date_directory()
    
    async def shutdown(self) -> None:
        """Shutdown the video recording service"""
        logger.info("Shutting down video recording service")
        
        # Stop any active recording
        if self.recorder.recording:
            await self.stop_recording()
    
    async def add_frame(self, frame: np.ndarray, timestamp: float) -> None:
        """
        Add a frame to the rolling buffer and recording if active
        
        Args:
            frame: Video frame as numpy array
            timestamp: Frame timestamp in seconds
        """
        # Update last frame time
        self.last_frame_time = timestamp
        
        # Add frame to recorder
        should_stop = self.recorder.add_frame(frame, timestamp)
        
        # Check if we should stop recording
        if should_stop:
            await self.stop_recording()
    
    async def trigger_recording(self, detection_id: str) -> None:
        """
        Start recording on detection event
        
        Args:
            detection_id: ID of the detection triggering the recording
        """
        if self.recorder.recording:
            # Already recording, just extend the post-event duration and add detection ID
            self.recorder.post_event_frames = 0
            if detection_id not in self.current_detection_ids:
                self.current_detection_ids.append(detection_id)
                # Update video segment with new detection ID
                await self._update_segment_detections()
            return
        
        logger.info(f"Starting video recording for detection {detection_id}")
        
        # Create output directory and file
        await self._ensure_date_directory()
        date_dir = datetime.datetime.now().strftime("%Y-%m-%d")
        video_filename = f"{detection_id}_{int(time.time())}.mp4"
        video_path = os.path.join(self.base_video_dir, date_dir, video_filename)
        
        # Set current detection
        self.current_detection_ids = [detection_id]
        
        # Start recording
        buffer_start_time, buffer_frames = self.recorder.start_recording(video_path)
        
        if buffer_start_time is None:
            logger.warning("Failed to start recording")
            return
        
        # Get video properties
        if buffer_frames:
            height, width = buffer_frames[0][0].shape[:2]
            resolution = f"{width}x{height}"
        else:
            resolution = "unknown"
        
        # Create video segment in database
        video_start_time = datetime.datetime.fromtimestamp(buffer_start_time)
        self.current_segment_id = await self.video_repository.add_video_segment(
            file_path=video_path,
            start_time=video_start_time,
            end_time=video_start_time,  # Will update when finished
            duration_seconds=0,  # Will update when finished
            file_size_bytes=0,  # Will update when finished
            resolution=resolution,
            detection_ids=detection_id
        )
        
        # Update detection record with video reference
        await self.detection_repository.update_detection_video(
            detection_id=detection_id,
            video_path=video_path,
            video_start_time=video_start_time
        )
        
        logger.info(f"Started recording to {video_path}")
    
    async def stop_recording(self) -> None:
        """Stop the current recording"""
        if not self.recorder.recording:
            return
        
        logger.info("Stopping video recording")
        
        # Stop recording
        video_path, frames_written, duration = self.recorder.stop_recording()
        
        if not video_path or not os.path.exists(video_path):
            logger.warning(f"Video file not found at {video_path}")
            return
        
        # Get video file size
        file_size = os.path.getsize(video_path)
        
        # Get end time
        video_end_time = datetime.datetime.fromtimestamp(
            self.last_frame_time if self.last_frame_time else time.time())
        
        # Update video segment with final information
        if self.current_segment_id:
            await self.video_repository.update_video_segment(
                segment_id=self.current_segment_id,
                end_time=video_end_time,
                duration_seconds=duration,
                file_size_bytes=file_size
            )
        
        # Update all detection records with video end time
        for detection_id in self.current_detection_ids:
            await self.detection_repository.update_detection_video(
                detection_id=detection_id,
                video_path=video_path,
                video_start_time=None,  # Don't change start time
                video_end_time=video_end_time
            )
        
        logger.info(f"Finished recording {video_path} ({file_size/1024/1024:.2f} MB, {duration:.2f}s, {frames_written} frames)")
        
        # Reset recording state
        self.current_segment_id = None
        self.current_detection_ids = []
    
    async def _ensure_date_directory(self) -> None:
        """Ensure the date-based directory exists"""
        date_dir = datetime.datetime.now().strftime("%Y-%m-%d")
        os.makedirs(os.path.join(self.base_video_dir, date_dir), exist_ok=True)
    
    async def _update_segment_detections(self) -> None:
        """Update the video segment with current detection IDs"""
        if not self.current_segment_id:
            return
            
        detection_ids_str = ",".join(self.current_detection_ids)
        
        # Update video segment with new detection IDs
        async with self.video_repository.session_factory() as session:
            from sqlalchemy import update
            from app.models import VideoSegment
            
            await session.execute(
                update(VideoSegment)
                .where(VideoSegment.id == self.current_segment_id)
                .values(detection_ids=detection_ids_str)
            )
            await session.commit()
    
    async def cleanup_old_videos(self, retention_days: int = 30) -> int:
        """
        Clean up old video recordings
        
        Args:
            retention_days: Number of days to keep videos
            
        Returns:
            Number of archived videos
        """
        # Mark old videos as archived in database
        archived_count = await self.video_repository.cleanup_old_videos(days=retention_days)
        
        # Get list of archived videos
        async with self.video_repository.session_factory() as session:
            from sqlalchemy import select
            from app.models import VideoSegment
            
            result = await session.execute(
                select(VideoSegment)
                .where(VideoSegment.archived == True)
            )
            archived_segments = result.scalars().all()
            
            # Delete physical files for archived videos
            deleted_count = 0
            for segment in archived_segments:
                if os.path.exists(segment.file_path):
                    try:
                        os.remove(segment.file_path)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting video file {segment.file_path}: {e}")
            
            logger.info(f"Cleaned up {archived_count} old videos, deleted {deleted_count} files")
            
        return archived_count
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a video
        
        Args:
            video_id: ID of the video segment
            
        Returns:
            Dict with video information or None if not found
        """
        return await self.video_repository.get_video_segment_by_id(video_id)
    
    async def get_videos_for_detection(self, detection_id: str) -> List[Dict[str, Any]]:
        """
        Get videos containing a specific detection
        
        Args:
            detection_id: ID of the detection
            
        Returns:
            List of video information dicts
        """
        video = await self.video_repository.get_video_segment_by_detection_id(detection_id)
        return [video] if video else []