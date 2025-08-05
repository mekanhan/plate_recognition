"""
FFmpeg-based Recording Service
Replaces OpenCV VideoWriter with FFmpeg for browser-compatible video recording
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

class FFmpegRecorder:
    """
    FFmpeg-based video recorder that creates browser-compatible MP4 files
    """
    
    def __init__(self, camera_id: str, rtsp_url: str, output_dir: Path):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.output_dir = output_dir
        self.process: Optional[asyncio.subprocess.Process] = None
        self.is_recording = False
        self.current_segment_path: Optional[Path] = None
        
        # Create output directory structure
        self.camera_dir = output_dir / f"camera_{camera_id}"
        self.camera_dir.mkdir(parents=True, exist_ok=True)
        
    async def start_recording(self) -> bool:
        """Start FFmpeg recording process"""
        if self.is_recording:
            logger.warning(f"Recording already active for {self.camera_id}")
            return False
            
        try:
            # Create date-based directory structure
            now = datetime.now()
            date_dir = self.camera_dir / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}" / f"{now.hour:02d}"
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename pattern with strftime support
            output_pattern = str(date_dir / f"camera_{self.camera_id}_%Y%m%d_%H%M%S.mp4")
            
            # FFmpeg command for segmented MP4 recording
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output files
                '-rtsp_transport', 'tcp',  # Use TCP for RTSP (more reliable)
                '-i', self.rtsp_url,
                
                # Video settings
                '-c:v', 'copy',  # Copy video stream (no re-encoding)
                '-c:a', 'aac',   # Encode audio to AAC (browser compatible)
                
                # Segmentation settings  
                '-f', 'segment',           # Use segment muxer
                '-segment_time', '600',    # 10-minute segments (600 seconds)
                '-segment_format', 'mp4',  # MP4 format for segments
                '-reset_timestamps', '1',   # Reset timestamps for each segment
                '-strftime', '1',          # Enable strftime in output pattern
                
                # Error recovery
                '-reconnect', '1',           # Auto-reconnect on failure
                '-reconnect_at_eof', '1',    # Reconnect at end of file
                '-reconnect_streamed', '1',  # Reconnect for streamed content
                
                # Output pattern
                output_pattern
            ]
            
            logger.info(f"Starting FFmpeg recording for {self.camera_id}")
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # Start FFmpeg process
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )
            
            self.is_recording = True
            
            # Start monitoring task
            asyncio.create_task(self._monitor_process())
            
            logger.info(f"FFmpeg recording started for {self.camera_id} (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start FFmpeg recording for {self.camera_id}: {e}")
            self.is_recording = False
            return False
    
    async def stop_recording(self) -> bool:
        """Stop FFmpeg recording process"""
        if not self.is_recording or not self.process:
            return True
            
        try:
            logger.info(f"Stopping FFmpeg recording for {self.camera_id}")
            
            # Send SIGTERM to FFmpeg for graceful shutdown
            self.process.terminate()
            
            # Wait for process to exit (with timeout)
            try:
                await asyncio.wait_for(self.process.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning(f"FFmpeg process didn't stop gracefully, killing it")
                self.process.kill()
                await self.process.wait()
            
            self.is_recording = False
            self.process = None
            
            logger.info(f"FFmpeg recording stopped for {self.camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping FFmpeg recording for {self.camera_id}: {e}")
            return False
    
    async def _monitor_process(self):
        """Monitor FFmpeg process for errors and output"""
        if not self.process:
            return
            
        try:
            # Read stderr for FFmpeg output/errors
            async for line in self.process.stderr:
                line_str = line.decode('utf-8', errors='ignore').strip()
                
                if 'error' in line_str.lower() or 'failed' in line_str.lower():
                    logger.error(f"FFmpeg error for {self.camera_id}: {line_str}")
                elif 'frame=' in line_str:
                    # Periodic status update (every 1000th frame logged)
                    if 'frame=1000' in line_str or 'frame=5000' in line_str:
                        logger.debug(f"FFmpeg status for {self.camera_id}: {line_str}")
                
            # Process ended
            return_code = await self.process.wait()
            
            if return_code != 0:
                logger.error(f"FFmpeg process for {self.camera_id} exited with code {return_code}")
            else:
                logger.info(f"FFmpeg process for {self.camera_id} completed normally")
                
            self.is_recording = False
            
        except Exception as e:
            logger.error(f"Error monitoring FFmpeg process for {self.camera_id}: {e}")
            self.is_recording = False
    
    def get_recording_status(self) -> Dict[str, Any]:
        """Get current recording status"""
        status = {
            'camera_id': self.camera_id,
            'is_recording': self.is_recording,
            'rtsp_url': self.rtsp_url,
            'process_pid': self.process.pid if self.process else None,
            'output_directory': str(self.camera_dir)
        }
        
        # Add latest recording info
        latest_files = self._get_latest_recordings(limit=1)
        if latest_files:
            latest = latest_files[0]
            status['latest_recording'] = {
                'filename': latest.name,
                'path': str(latest),
                'size_mb': round(latest.stat().st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(latest.stat().st_ctime).isoformat()
            }
        
        return status
    
    def _get_latest_recordings(self, limit: int = 10) -> list[Path]:
        """Get list of latest recording files"""
        try:
            # Find all MP4 files in camera directory
            mp4_files = list(self.camera_dir.rglob("*.mp4"))
            
            # Sort by creation time (newest first)
            mp4_files.sort(key=lambda f: f.stat().st_ctime, reverse=True)
            
            return mp4_files[:limit]
            
        except Exception as e:
            logger.error(f"Error getting latest recordings for {self.camera_id}: {e}")
            return []

    async def validate_recording(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate a recorded file using ffprobe
        Returns format and stream information
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return json.loads(stdout.decode('utf-8'))
            else:
                logger.error(f"ffprobe failed for {file_path}: {stderr.decode('utf-8')}")
                return {}
                
        except Exception as e:
            logger.error(f"Error validating recording {file_path}: {e}")
            return {}

# Test function for validation
async def test_ffmpeg_recording():
    """
    Test function to validate FFmpeg recording without camera
    Creates a test pattern video for browser compatibility testing
    """
    output_file = Path("test_ffmpeg_output.mp4")
    
    # Create test pattern video (no camera required)
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite
        '-f', 'lavfi',  # Use libavfilter virtual input
        '-i', 'testsrc2=duration=10:size=640x480:rate=30',  # 10-second test pattern
        '-c:v', 'libx264',  # H.264 encoding
        '-preset', 'fast',   # Fast encoding
        '-crf', '23',        # Good quality
        '-pix_fmt', 'yuv420p',  # Browser-compatible pixel format
        str(output_file)
    ]
    
    try:
        logger.info("Creating test video with FFmpeg...")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info(f"✅ Test video created: {output_file}")
            logger.info(f"File size: {output_file.stat().st_size / (1024*1024):.2f} MB")
            
            # Validate with ffprobe
            recorder = FFmpegRecorder("test", "", Path("."))
            validation = await recorder.validate_recording(output_file)
            
            if validation:
                format_info = validation.get('format', {})
                video_streams = [s for s in validation.get('streams', []) if s.get('codec_type') == 'video']
                
                logger.info("✅ Video validation successful:")
                logger.info(f"   Format: {format_info.get('format_name')}")
                logger.info(f"   Duration: {format_info.get('duration')} seconds")
                
                if video_streams:
                    stream = video_streams[0]
                    logger.info(f"   Video codec: {stream.get('codec_name')}")
                    logger.info(f"   Resolution: {stream.get('width')}x{stream.get('height')}")
                    logger.info(f"   Frame rate: {stream.get('r_frame_rate')}")
                
                return True
            else:
                logger.error("❌ Video validation failed")
                return False
        else:
            logger.error(f"❌ FFmpeg test failed: {stderr.decode('utf-8')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test recording failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_ffmpeg_recording())