"""
Continuous video recorder for 24/7 camera recording
"""
import asyncio
import cv2
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import threading
import queue
import sqlite3
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ContinuousRecorder:
    """Handles continuous recording for a single camera"""
    
    def __init__(self, camera_config: Dict[str, Any]):
        """Initialize the continuous recorder
        
        Args:
            camera_config: Camera configuration dictionary containing:
                - id: Camera ID
                - rtsp_url: RTSP URL for the camera stream
                - name: Camera name
                - recording_enabled: Whether recording is enabled
        """
        self.camera_id = camera_config['id']
        self.camera_name = camera_config.get('name', f'Camera {self.camera_id}')
        self.rtsp_url = camera_config['rtsp_url']
        self.storage_path = f"recordings/camera_{self.camera_id}"
        self.segment_duration = 600  # 10 minutes in seconds
        
        # Recording state
        self.is_recording = False
        self.current_writer = None
        self.current_segment_start = None
        self.current_filepath = None
        self.frame_queue = queue.Queue(maxsize=300)  # 10-second buffer at 30fps
        self.frame_width = None
        self.frame_height = None
        
        # Storage management
        self.max_storage_days = 30  # Keep 30 days by default
        
        # Recording threads
        self.capture_thread = None
        self.recording_thread = None
        self.cleanup_thread = None
        
        # Database connection
        self.db_conn = None
        
        # Initialize directories and database
        self.ensure_directories()
        self.init_index_database()
    
    def ensure_directories(self):
        """Create directory structure for recordings"""
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created recording directory: {self.storage_path}")
    
    def init_index_database(self):
        """Initialize SQLite index for fast seeking"""
        db_path = f"{self.storage_path}/index.db"
        self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
        
        self.db_conn.execute('''
            CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER,
                frame_count INTEGER,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db_conn.commit()
        logger.info(f"Initialized recording database for camera {self.camera_id}")
    
    async def start_recording(self):
        """Start continuous recording"""
        if self.is_recording:
            logger.warning(f"Recording already active for camera {self.camera_id}")
            return
        
        self.is_recording = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(
            target=self._capture_frames, 
            daemon=True,
            name=f"capture-{self.camera_id}"
        )
        self.capture_thread.start()
        
        # Start recording thread
        self.recording_thread = threading.Thread(
            target=self._process_frames, 
            daemon=True,
            name=f"recording-{self.camera_id}"
        )
        self.recording_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_old_recordings, 
            daemon=True,
            name=f"cleanup-{self.camera_id}"
        )
        self.cleanup_thread.start()
        
        logger.info(f"Started continuous recording for camera {self.camera_id} ({self.camera_name})")
    
    def _capture_frames(self):
        """Capture frames from RTSP stream"""
        cap = None
        reconnect_delay = 1
        frame_count = 0
        
        while self.is_recording:
            try:
                if cap is None:
                    logger.info(f"Connecting to camera {self.camera_id} at {self.rtsp_url}")
                    cap = cv2.VideoCapture(self.rtsp_url)
                    
                    # Set capture properties for better performance
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Verify connection
                    if not cap.isOpened():
                        raise Exception("Failed to open camera stream")
                    
                    reconnect_delay = 1
                    logger.info(f"Successfully connected to camera {self.camera_id}")
                
                ret, frame = cap.read()
                if ret and frame is not None:
                    timestamp = datetime.now()
                    frame_count += 1
                    
                    # Get frame dimensions on first frame
                    if self.frame_width is None or self.frame_height is None:
                        self.frame_height, self.frame_width = frame.shape[:2]
                        logger.info(f"Camera {self.camera_id} frame dimensions: {self.frame_width}x{self.frame_height}")
                    
                    # Add to queue (drop oldest if full)
                    try:
                        self.frame_queue.put((frame, timestamp), timeout=0.1)
                        
                        # Log progress every 1000 frames
                        if frame_count % 1000 == 0:
                            logger.debug(f"Camera {self.camera_id}: Captured {frame_count} frames")
                            
                    except queue.Full:
                        # Drop oldest frame to maintain real-time processing
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put((frame, timestamp), timeout=0.1)
                        except queue.Empty:
                            pass
                else:
                    # Lost connection - reconnect
                    logger.warning(f"Lost connection to camera {self.camera_id}, reconnecting...")
                    if cap:
                        cap.release()
                        cap = None
                    
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 30)  # Exponential backoff, max 30s
                    
            except Exception as e:
                logger.error(f"Capture error for camera {self.camera_id}: {e}")
                if cap:
                    cap.release()
                    cap = None
                time.sleep(5)
        
        if cap:
            cap.release()
        logger.info(f"Stopped capturing frames for camera {self.camera_id}")
    
    def _process_frames(self):
        """Process frames and write to video files"""
        frame_count = 0
        
        while self.is_recording:
            try:
                # Get frame from queue
                frame, timestamp = self.frame_queue.get(timeout=1.0)
                
                # Check if we need to start a new segment
                if (self.current_writer is None or 
                    self._should_start_new_segment(timestamp)):
                    self._start_new_segment(timestamp)
                
                # Write frame to current segment
                if self.current_writer and frame is not None:
                    self.current_writer.write(frame)
                    frame_count += 1
                    
                    # Log progress
                    if frame_count % 300 == 0:  # Every 10 seconds at 30fps
                        logger.debug(f"Camera {self.camera_id}: Written {frame_count} frames to current segment")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing error for camera {self.camera_id}: {e}")
        
        # Finalize any open segment
        if self.current_writer:
            self._finalize_current_segment()
        
        logger.info(f"Stopped processing frames for camera {self.camera_id}")
    
    def _should_start_new_segment(self, timestamp: datetime) -> bool:
        """Check if we should start a new video segment"""
        if self.current_segment_start is None:
            return True
        
        elapsed = (timestamp - self.current_segment_start).total_seconds()
        return elapsed >= self.segment_duration
    
    def _start_new_segment(self, timestamp: datetime):
        """Start a new video segment"""
        # Close current writer
        if self.current_writer:
            self._finalize_current_segment()
        
        # Create new segment
        self.current_segment_start = timestamp
        
        # Generate filename with proper directory structure
        date_path = timestamp.strftime("%Y/%m/%d/%H")
        segment_dir = f"{self.storage_path}/{date_path}"
        Path(segment_dir).mkdir(parents=True, exist_ok=True)
        
        filename = f"camera_{self.camera_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{self.segment_duration}.mp4"
        self.current_filepath = f"{segment_dir}/{filename}"
        
        # Initialize video writer with H264 codec
        # Try different codecs in order of preference
        codecs_to_try = [
            ('H264', 'mp4'),
            ('XVID', 'avi'),
            ('MJPG', 'avi'),
            ('mp4v', 'mp4')
        ]
        
        for codec, ext in codecs_to_try:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                test_filepath = self.current_filepath.rsplit('.', 1)[0] + f'.{ext}'
                # Use actual frame dimensions if available, otherwise default
                width = self.frame_width if self.frame_width else 640
                height = self.frame_height if self.frame_height else 480
                
                test_writer = cv2.VideoWriter(
                    test_filepath,
                    fourcc,
                    30.0,  # FPS
                    (width, height)  # Use actual resolution
                )
                
                if test_writer.isOpened():
                    self.current_writer = test_writer
                    self.current_filepath = test_filepath
                    logger.info(f"Using codec {codec} for recording")
                    break
                else:
                    test_writer.release()
                    
            except Exception as e:
                logger.debug(f"Codec {codec} not available: {e}")
                continue
        
        if self.current_writer is None or not self.current_writer.isOpened():
            logger.error(f"Failed to initialize video writer for camera {self.camera_id}")
            raise Exception("No suitable video codec found")
        
        logger.info(f"Started new segment for camera {self.camera_id}: {filename}")
    
    def _finalize_current_segment(self):
        """Finalize current video segment"""
        if not self.current_writer:
            return
            
        try:
            self.current_writer.release()
            
            # Get file info
            if os.path.exists(self.current_filepath):
                file_stats = os.stat(self.current_filepath)
                end_time = datetime.now()
                duration = int((end_time - self.current_segment_start).total_seconds())
                
                # Add to index database
                filename = os.path.basename(self.current_filepath)
                self.db_conn.execute('''
                    INSERT INTO segments 
                    (filename, start_time, end_time, duration, file_size)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    filename,
                    self.current_segment_start.isoformat(),
                    end_time.isoformat(),
                    duration,
                    file_stats.st_size
                ))
                self.db_conn.commit()
                
                logger.info(f"Finalized segment for camera {self.camera_id}: {filename} ({duration}s, {file_stats.st_size} bytes)")
            
        except Exception as e:
            logger.error(f"Error finalizing segment for camera {self.camera_id}: {e}")
        finally:
            self.current_writer = None
            self.current_filepath = None
    
    def _cleanup_old_recordings(self):
        """Cleanup old recordings based on retention policy"""
        while self.is_recording:
            try:
                cutoff_date = datetime.now() - timedelta(days=self.max_storage_days)
                
                # Find old segments
                cursor = self.db_conn.execute('''
                    SELECT filename, start_time FROM segments 
                    WHERE datetime(start_time) < datetime(?)
                ''', (cutoff_date.isoformat(),))
                
                old_segments = cursor.fetchall()
                
                for filename, start_time in old_segments:
                    # Delete file
                    start_dt = datetime.fromisoformat(start_time)
                    date_path = start_dt.strftime("%Y/%m/%d/%H")
                    file_path = f"{self.storage_path}/{date_path}/{filename}"
                    
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Deleted old recording for camera {self.camera_id}: {filename}")
                    
                    # Remove from database
                    self.db_conn.execute('DELETE FROM segments WHERE filename = ?', (filename,))
                
                self.db_conn.commit()
                
                # Sleep for 1 hour before next cleanup
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Cleanup error for camera {self.camera_id}: {e}")
                time.sleep(3600)
    
    def stop_recording(self):
        """Stop continuous recording"""
        logger.info(f"Stopping recording for camera {self.camera_id}")
        self.is_recording = False
        
        # Wait for threads to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
        if self.recording_thread:
            self.recording_thread.join(timeout=5)
        
        # Finalize any open segment
        if self.current_writer:
            self._finalize_current_segment()
        
        # Close database connection
        if self.db_conn:
            self.db_conn.close()
        
        logger.info(f"Stopped recording for camera {self.camera_id}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current recording status"""
        return {
            'camera_id': self.camera_id,
            'camera_name': self.camera_name,
            'is_recording': self.is_recording,
            'current_segment': self.current_filepath if self.current_writer else None,
            'segment_start': self.current_segment_start.isoformat() if self.current_segment_start else None,
            'queue_size': self.frame_queue.qsize(),
            'storage_path': self.storage_path
        }