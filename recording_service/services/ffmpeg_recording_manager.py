"""
FFmpeg Recording Manager - Handles 24/7 continuous camera recording
Replaces OpenCV VideoWriter with FFmpeg for browser-compatible MP4 recording
"""
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import time
import json
import signal
from database.models import VideoRecording, Camera

logger = logging.getLogger(__name__)

class FFmpegCameraRecorder:
    """Handles FFmpeg-based recording for a single camera"""
    
    def __init__(self, camera_config: dict, storage_path: str, db_service):
        self.camera_config = camera_config
        self.camera_id = camera_config['camera_id']
        self.name = camera_config['name']
        self.rtsp_url = self._build_rtsp_url()
        self.storage_path = Path(storage_path) / f"camera_{self.camera_id}"
        self.db_service = db_service
        
        # Recording state
        self.is_recording = False
        self.ffmpeg_process: Optional[asyncio.subprocess.Process] = None
        self.current_output_dir = None
        self.segment_duration = 600  # 10 minutes in seconds
        
        # Statistics tracking
        self.total_segments = 0
        self.total_size_bytes = 0
        self.last_segment_time = None
        self.error_count = 0
        self.start_time = None
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FFmpeg camera recorder initialized: {self.name} ({self.camera_id})")
    
    def _build_rtsp_url(self) -> str:
        """Build RTSP URL from camera configuration"""
        config = self.camera_config
        username = config.get('username', '')
        password = config.get('password', '')
        ip_address = config.get('ip_address')
        port = config.get('port', 554)
        stream_path = config.get('stream_path', '/stream')
        
        # Handle different URL formats
        if username and password:
            return f"rtsp://{username}:{password}@{ip_address}:{port}{stream_path}"
        else:
            return f"rtsp://{ip_address}:{port}{stream_path}"
    
    async def start_recording(self) -> bool:
        """Start FFmpeg recording process"""
        if self.is_recording:
            logger.warning(f"Recording already active for {self.name}")
            return False
        
        try:
            # Create date-based directory structure
            now = datetime.now()
            self.current_output_dir = (
                self.storage_path / 
                str(now.year) / 
                f"{now.month:02d}" / 
                f"{now.day:02d}" / 
                f"{now.hour:02d}"
            )
            self.current_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename pattern with strftime support
            output_pattern = str(self.current_output_dir / f"camera_{self.camera_id}_%Y%m%d_%H%M%S.mp4")
            
            # FFmpeg command for segmented recording (simplified to match working test)
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output files
                '-rtsp_transport', 'tcp',  # Use TCP for RTSP (more reliable)
                '-i', self.rtsp_url,       # Input RTSP stream
                
                # Video settings - convert H.265 to H.264 for browser compatibility
                '-c:v', 'libx264',         # Encode to H.264 (universal browser support)
                '-preset', 'ultrafast',    # Ultrafast preset for real-time transcoding
                '-crf', '28',              # Higher CRF for faster encoding
                '-r', '15',                # Reduce frame rate to 15fps for stability
                '-vf', 'scale=1920:1080',  # Scale down from 4K to 1080p
                '-c:a', 'aac',             # Encode audio to AAC (browser compatible)
                '-err_detect', 'ignore_err', # Ignore stream errors to prevent crashes
                
                # Segmentation settings (simplified)
                '-f', 'segment',           # Use segment muxer
                '-segment_time', str(self.segment_duration),  # 10-minute segments  
                '-segment_format', 'mp4',  # MP4 format for segments
                '-reset_timestamps', '1',   # Reset timestamps for each segment
                '-strftime', '1',          # Enable strftime in output pattern
                
                # Output pattern
                output_pattern
            ]
            
            logger.info(f"Starting FFmpeg recording for {self.name}")
            logger.debug(f"RTSP URL: {self.rtsp_url.split('@')[0]}@***")  # Hide credentials
            logger.debug(f"Output pattern: {output_pattern}")
            
            # Start FFmpeg process
            self.ffmpeg_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )
            
            self.is_recording = True
            self.start_time = datetime.now()
            self.error_count = 0
            
            # Start monitoring tasks
            asyncio.create_task(self._monitor_process())
            asyncio.create_task(self._monitor_files())
            
            logger.info(f"FFmpeg recording started for {self.name} (PID: {self.ffmpeg_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start FFmpeg recording for {self.name}: {e}")
            self.is_recording = False
            return False
    
    async def stop_recording(self) -> bool:
        """Stop FFmpeg recording process gracefully"""
        if not self.is_recording or not self.ffmpeg_process:
            return True
        
        try:
            logger.info(f"Stopping FFmpeg recording for {self.name}")
            
            # Send SIGTERM for graceful shutdown
            self.ffmpeg_process.terminate()
            
            # Wait for process to exit (with timeout)
            try:
                await asyncio.wait_for(self.ffmpeg_process.wait(), timeout=10.0)
                logger.info(f"FFmpeg process stopped gracefully for {self.name}")
            except asyncio.TimeoutError:
                logger.warning(f"FFmpeg process didn't stop gracefully, killing it for {self.name}")
                self.ffmpeg_process.kill()
                await self.ffmpeg_process.wait()
            
            self.is_recording = False
            self.ffmpeg_process = None
            
            # Update final statistics
            await self._update_statistics()
            
            logger.info(f"FFmpeg recording stopped for {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping FFmpeg recording for {self.name}: {e}")
            return False
    
    async def _monitor_process(self):
        """Monitor FFmpeg process for errors and status updates"""
        if not self.ffmpeg_process:
            return
        
        try:
            # Read stderr for FFmpeg output
            async for line in self.ffmpeg_process.stderr:
                line_str = line.decode('utf-8', errors='ignore').strip()
                
                # Log important messages
                if any(keyword in line_str.lower() for keyword in ['error', 'failed', 'connection']):
                    if 'error' in line_str.lower():
                        logger.error(f"FFmpeg error for {self.name}: {line_str}")
                        self.error_count += 1
                    else:
                        logger.warning(f"FFmpeg warning for {self.name}: {line_str}")
                        
                elif 'frame=' in line_str and 'fps=' in line_str:
                    # Periodic status update (every 100 frames to avoid spam)
                    if 'frame= 1000' in line_str or 'frame= 5000' in line_str:
                        logger.info(f"FFmpeg status for {self.name}: {line_str}")
                        self.last_segment_time = datetime.now()
                
            # Process ended
            return_code = await self.ffmpeg_process.wait()
            
            if return_code != 0:
                logger.error(f"FFmpeg process for {self.name} exited with code {return_code}")
                self.error_count += 1
            else:
                logger.info(f"FFmpeg process for {self.name} completed normally")
            
            self.is_recording = False
            
        except Exception as e:
            logger.error(f"Error monitoring FFmpeg process for {self.name}: {e}")
            self.is_recording = False
    
    async def _monitor_files(self):
        """Monitor file creation and update database records"""
        last_file_count = 0
        
        while self.is_recording:
            try:
                # Check for new MP4 files
                mp4_files = list(self.storage_path.rglob("*.mp4"))
                current_file_count = len(mp4_files)
                
                if current_file_count > last_file_count:
                    # New files created, update statistics and database
                    new_files = current_file_count - last_file_count
                    logger.info(f"New segments created for {self.name}: {new_files}")
                    
                    # Update database with new recordings
                    await self._update_database_records()
                    
                    last_file_count = current_file_count
                    self.total_segments = current_file_count
                
                # Sleep for a bit before checking again
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring files for {self.name}: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _update_database_records(self):
        """Update database with new recording segments"""
        try:
            # Find MP4 files that aren't in database yet
            mp4_files = list(self.storage_path.rglob("*.mp4"))
            
            async with self.db_service.async_session() as session:
                for mp4_file in mp4_files:
                    # Parse filename to extract metadata
                    metadata = self._parse_filename(mp4_file.name)
                    if not metadata:
                        continue
                    
                    # Check if already in database
                    existing = await session.execute(
                        VideoRecording.__table__.select().where(
                            VideoRecording.filename == mp4_file.name
                        )
                    )
                    if existing.fetchone():
                        continue  # Already exists
                    
                    # Create new database record
                    file_stats = mp4_file.stat()
                    
                    recording = VideoRecording(
                        camera_id=self.camera_id,
                        filename=mp4_file.name,
                        file_path=str(mp4_file),
                        start_time=metadata['start_time'],
                        end_time=metadata['end_time'],
                        duration_seconds=metadata['duration'],
                        file_size_bytes=file_stats.st_size,
                        video_codec='h264',  # Converted to H.264 for browser compatibility
                        video_width=1920,    # 1080p width (scaled down)
                        video_height=1080,   # 1080p height (scaled down)
                        video_fps=15,        # 15 FPS (reduced for stability)
                        is_compressed=True,
                        has_audio=True,      # FFmpeg records audio
                        has_detections=False,
                        detection_count=0,
                        created_at=datetime.fromtimestamp(file_stats.st_ctime)
                    )
                    
                    session.add(recording)
                    
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating database records for {self.name}: {e}")
    
    def _parse_filename(self, filename: str) -> Optional[Dict]:
        """Parse filename to extract recording metadata"""
        # Expected format: camera_camera_946701d3_20250802_142500.mp4
        import re
        
        pattern = r'camera_(.+)_(\d{8})_(\d{6})\.mp4'
        match = re.match(pattern, filename)
        
        if not match:
            return None
        
        camera_id, date_str, time_str = match.groups()
        
        # Parse date and time
        try:
            date_time_str = f"{date_str}_{time_str}"
            start_time = datetime.strptime(date_time_str, "%Y%m%d_%H%M%S")
            end_time = start_time + timedelta(seconds=self.segment_duration)
            
            return {
                'camera_id': camera_id,
                'start_time': start_time,
                'end_time': end_time,
                'duration': self.segment_duration
            }
        except ValueError:
            return None
    
    async def _update_statistics(self):
        """Update recording statistics"""
        try:
            mp4_files = list(self.storage_path.rglob("*.mp4"))
            self.total_segments = len(mp4_files)
            self.total_size_bytes = sum(f.stat().st_size for f in mp4_files)
            
        except Exception as e:
            logger.error(f"Error updating statistics for {self.name}: {e}")
    
    def get_status(self) -> Dict:
        """Get current recording status"""
        return {
            'camera_id': self.camera_id,
            'name': self.name,
            'is_recording': self.is_recording,
            'process_pid': self.ffmpeg_process.pid if self.ffmpeg_process else None,
            'total_segments': self.total_segments,
            'total_size_mb': round(self.total_size_bytes / (1024 * 1024), 2),
            'error_count': self.error_count,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'last_segment_time': self.last_segment_time.isoformat() if self.last_segment_time else None
        }


class FFmpegRecordingManager:
    """Manages FFmpeg recording for all cameras"""
    
    def __init__(self, db_service, storage_path: str = "recordings"):
        self.db_service = db_service
        self.storage_path = storage_path
        self.recorders: Dict[str, FFmpegCameraRecorder] = {}
        self.is_running = False
        
        logger.info("FFmpeg Recording Manager initialized")
    
    async def start(self):
        """Start recording for all enabled cameras"""
        self.is_running = True
        
        try:
            # Get enabled cameras from database
            cameras = await self._get_enabled_cameras()
            
            if not cameras:
                logger.warning("No enabled cameras found for recording")
                return
            
            # Start recording for each camera
            for camera_config in cameras:
                recorder = FFmpegCameraRecorder(camera_config, self.storage_path, self.db_service)
                success = await recorder.start_recording()
                
                if success:
                    self.recorders[camera_config['camera_id']] = recorder
                    logger.info(f"Started recording for {camera_config['name']}")
                else:
                    logger.error(f"Failed to start recording for {camera_config['name']}")
            
            logger.info(f"FFmpeg Recording Manager started with {len(self.recorders)} active recorders")
            
        except Exception as e:
            logger.error(f"Error starting recording manager: {e}")
    
    async def stop(self):
        """Stop all recording processes"""
        self.is_running = False
        
        logger.info("Stopping all FFmpeg recorders...")
        
        # Stop all recorders
        for camera_id, recorder in self.recorders.items():
            try:
                await recorder.stop_recording()
                logger.info(f"Stopped recording for {camera_id}")
            except Exception as e:
                logger.error(f"Error stopping recorder for {camera_id}: {e}")
        
        self.recorders.clear()
        logger.info("All FFmpeg recorders stopped")
    
    async def _get_enabled_cameras(self) -> List[Dict]:
        """Get enabled cameras from database"""
        cameras = []
        
        try:
            async with self.db_service.async_session() as session:
                result = await session.execute(
                    Camera.__table__.select().where(Camera.status == 'active')
                )
                
                for row in result.fetchall():
                    camera_config = {
                        'camera_id': row.camera_id,  # Use the simpler camera_id field, not the UUID
                        'name': row.name,
                        'ip_address': row.ip_address,
                        'port': row.port,
                        'username': row.username,
                        'password': row.password,
                        'stream_path': row.stream_path,
                    }
                    cameras.append(camera_config)
                    
        except Exception as e:
            logger.error(f"Error loading cameras from database: {e}")
        
        return cameras
    
    def get_status(self) -> Dict:
        """Get status of all recorders"""
        return {
            'is_running': self.is_running,
            'active_recorders': len(self.recorders),
            'recorders': {
                camera_id: recorder.get_status() 
                for camera_id, recorder in self.recorders.items()
            }
        }