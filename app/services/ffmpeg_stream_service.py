# app/services/ffmpeg_stream_service.py
# Alternative streaming service using FFmpeg subprocess for better IP camera compatibility
import asyncio
import subprocess
import logging
import os
import tempfile
import time
import numpy as np
import cv2
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FFmpegStreamService:
    """Alternative streaming service using FFmpeg for IP camera compatibility"""
    
    def __init__(self):
        self.active_streams = {}
        self.frame_cache = {}
        
    async def start_ffmpeg_stream(self, camera_id: str, rtsp_url: str) -> bool:
        """Start FFmpeg stream for a camera"""
        try:
            if camera_id in self.active_streams:
                await self.stop_ffmpeg_stream(camera_id)
            
            # Create named pipe for frame data
            temp_dir = tempfile.gettempdir()
            pipe_path = os.path.join(temp_dir, f"camera_stream_{camera_id}.pipe")
            
            # Remove existing pipe if it exists
            if os.path.exists(pipe_path):
                os.unlink(pipe_path)
            
            # Create named pipe
            os.mkfifo(pipe_path)
            
            # FFmpeg command to convert RTSP to raw frames
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', rtsp_url,
                '-f', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', '640x480',  # Resize for better performance
                '-r', '10',        # 10 FPS to reduce load
                '-an',             # No audio
                '-y',              # Overwrite output
                pipe_path
            ]
            
            # Start FFmpeg process
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            self.active_streams[camera_id] = {
                'process': process,
                'pipe_path': pipe_path,
                'frame_size': 640 * 480 * 3,  # BGR24 format
                'width': 640,
                'height': 480,
                'last_frame_time': 0,
                'frame_count': 0
            }
            
            # Start frame reader task
            asyncio.create_task(self._read_ffmpeg_frames(camera_id))
            
            logger.info(f"Started FFmpeg stream for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start FFmpeg stream for camera {camera_id}: {e}")
            return False
    
    async def stop_ffmpeg_stream(self, camera_id: str) -> bool:
        """Stop FFmpeg stream for a camera"""
        try:
            if camera_id not in self.active_streams:
                return True
            
            stream_info = self.active_streams[camera_id]
            
            # Terminate FFmpeg process
            if stream_info['process']:
                stream_info['process'].terminate()
                try:
                    stream_info['process'].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    stream_info['process'].kill()
            
            # Clean up pipe
            if os.path.exists(stream_info['pipe_path']):
                os.unlink(stream_info['pipe_path'])
            
            # Clean up cache
            if camera_id in self.frame_cache:
                del self.frame_cache[camera_id]
            
            del self.active_streams[camera_id]
            
            logger.info(f"Stopped FFmpeg stream for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop FFmpeg stream for camera {camera_id}: {e}")
            return False
    
    async def _read_ffmpeg_frames(self, camera_id: str):
        """Read frames from FFmpeg pipe"""
        stream_info = self.active_streams[camera_id]
        pipe_path = stream_info['pipe_path']
        frame_size = stream_info['frame_size']
        width = stream_info['width']
        height = stream_info['height']
        
        try:
            # Wait a moment for FFmpeg to start
            await asyncio.sleep(2)
            
            with open(pipe_path, 'rb') as pipe:
                while camera_id in self.active_streams:
                    try:
                        # Read one frame worth of data
                        frame_data = pipe.read(frame_size)
                        
                        if len(frame_data) == frame_size:
                            # Convert to numpy array
                            frame = np.frombuffer(frame_data, dtype=np.uint8)
                            frame = frame.reshape((height, width, 3))
                            
                            # Cache the frame
                            self.frame_cache[camera_id] = {
                                'frame': frame.copy(),
                                'timestamp': time.time()
                            }
                            
                            stream_info['frame_count'] += 1
                            stream_info['last_frame_time'] = time.time()
                            
                            if stream_info['frame_count'] == 1:
                                logger.info(f"🎉 First FFmpeg frame received for camera {camera_id}")
                        
                        else:
                            # End of stream or incomplete frame
                            break
                            
                        await asyncio.sleep(0.1)  # Control frame rate
                        
                    except Exception as e:
                        logger.error(f"Error reading frame for camera {camera_id}: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"FFmpeg frame reader error for camera {camera_id}: {e}")
    
    def get_latest_frame(self, camera_id: str) -> Tuple[Optional[np.ndarray], float]:
        """Get latest frame for a camera"""
        if camera_id not in self.frame_cache:
            return None, 0
        
        cache_entry = self.frame_cache[camera_id]
        return cache_entry['frame'], cache_entry['timestamp']
    
    def get_frame_as_jpeg(self, camera_id: str) -> Tuple[Optional[bytes], float]:
        """Get latest frame as JPEG bytes"""
        frame, timestamp = self.get_latest_frame(camera_id)
        if frame is None:
            return None, 0
        
        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes(), timestamp
    
    def get_stream_stats(self, camera_id: str) -> dict:
        """Get stream statistics"""
        if camera_id not in self.active_streams:
            return {}
        
        stream_info = self.active_streams[camera_id]
        return {
            'frame_count': stream_info['frame_count'],
            'last_frame_time': stream_info['last_frame_time'],
            'is_active': stream_info['process'].poll() is None,
            'width': stream_info['width'],
            'height': stream_info['height']
        }