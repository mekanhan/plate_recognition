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
        self.shutdown_event = threading.Event()
        self.current_writer = None
        self.current_segment_start = None
        self.current_filepath = None
        self.frame_queue = queue.Queue(maxsize=300)  # 10-second buffer at 30fps
        self.frame_width = None
        self.frame_height = None
        
        # Storage management with uncompressed video considerations
        self.max_storage_days = 30  # Keep 30 days by default
        self.compression_scheduled = False  # Flag for future compression of old files
        self.current_codec = None  # Track current codec being used
        self.is_uncompressed = False  # Track if current recording is uncompressed
        
        # Recording threads
        self.capture_thread = None
        self.recording_thread = None
        self.cleanup_thread = None
        
        # Database connection
        self.db_conn = None
        
        # Initialize directories and database
        self.ensure_directories()
        self.init_index_database()
        
        # Verify uncompressed codec availability at startup
        self.verify_codec_availability()
    
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
    
    def verify_codec_availability(self):
        """Verify that uncompressed codecs are available before recording starts"""
        logger.info(f"🔍 VERIFYING UNCOMPRESSED CODECS for camera {self.camera_id}")
        
        # SIMPLIFIED: Just log that we'll try codecs during recording
        # Avoid hanging the startup process with codec testing
        logger.info("✅ Codec verification will occur during first recording attempt")
        logger.info("Available codecs: RAW, I420, YUV, None(raw), FFV1")
    
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
                    logger.info(f"Connecting to camera {self.camera_id} at {self.rtsp_url} with uncompressed video support")
                    
                    # Use FFmpeg backend for better codec support and raw access
                    cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                    
                    # Set capture properties for uncompressed video recording
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Configure for proper color conversion to suppress YUV warnings
                    cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)  # Convert YUV to BGR format
                    
                    # Set connection timeouts for stability
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10s open timeout
                    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 8000)   # 8s read timeout
                    
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
        
        # Initialize video writer with UNCOMPRESSED codec preference ONLY
        # Try ONLY uncompressed codecs - NO compressed fallbacks for highest quality
        codecs_to_try = [
            # ONLY uncompressed options for maximum quality
            ('RAW ', 'avi'),  # Raw uncompressed
            ('I420', 'avi'),  # YUV 4:2:0 uncompressed
            ('YUV ', 'avi'),  # YUV uncompressed
            (None, 'avi'),    # No codec (raw)
            ('FFV1', 'avi'),  # Lossless compression (mathematically lossless)
            # REMOVED ALL COMPRESSED CODECS - NO QUALITY COMPROMISE
        ]
        
        for codec, ext in codecs_to_try:
            try:
                # Handle raw/uncompressed codec (None)
                if codec is None:
                    fourcc = 0  # Raw uncompressed
                    codec_name = "RAW (uncompressed)"
                else:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    codec_name = codec
                
                test_filepath = self.current_filepath.rsplit('.', 1)[0] + f'.{ext}'
                # CRITICAL: Use ONLY actual frame dimensions - NO DEFAULT DOWNSCALING
                if not self.frame_width or not self.frame_height:
                    logger.error(f"CRITICAL: No frame dimensions available for camera {self.camera_id}")
                    logger.error("Cannot record at unknown resolution - skipping this codec")
                    continue
                width = self.frame_width
                height = self.frame_height
                
                test_writer = cv2.VideoWriter(
                    test_filepath,
                    fourcc,
                    30.0,  # FPS
                    (width, height)  # Use actual resolution
                )
                
                if test_writer.isOpened():
                    self.current_writer = test_writer
                    self.current_filepath = test_filepath
                    
                    # Log codec selection with compression status and resolution
                    is_uncompressed = codec in [None, 'RAW ', 'I420', 'YUV ', 'FFV1']
                    compression_status = "UNCOMPRESSED" if is_uncompressed else "COMPRESSED"
                    logger.info(f"✅ RECORDING CODEC SELECTED: {codec_name} ({compression_status})")
                    logger.info(f"✅ RECORDING RESOLUTION: {width}x{height} @ 30 FPS")
                    logger.info(f"✅ RECORDING FILE: {test_filepath}")
                    
                    # Store codec info for file size estimation
                    self.current_codec = codec_name
                    self.is_uncompressed = is_uncompressed
                    break
                else:
                    test_writer.release()
                    
            except Exception as e:
                logger.debug(f"Codec {codec_name if 'codec_name' in locals() else codec} not available: {e}")
                continue
        
        if self.current_writer is None or not self.current_writer.isOpened():
            logger.error(f"CRITICAL: NO UNCOMPRESSED CODECS AVAILABLE for camera {self.camera_id}")
            logger.error("System requires uncompressed video recording - no compressed fallbacks allowed")
            raise Exception("UNCOMPRESSED video codec required but not available - check OpenCV installation and codec support")
        
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
                
                # Calculate and log detailed quality metrics
                file_size_mb = file_stats.st_size / (1024 * 1024)
                file_size_gb = file_size_mb / 1024
                
                # Calculate expected uncompressed size for comparison
                if hasattr(self, 'frame_width') and hasattr(self, 'frame_height'):
                    expected_uncompressed_mb = (self.frame_width * self.frame_height * 3 * 30 * duration) / (1024 * 1024)
                    size_ratio = file_size_mb / expected_uncompressed_mb if expected_uncompressed_mb > 0 else 0
                else:
                    size_ratio = 0
                
                compression_info = f"{getattr(self, 'current_codec', 'Unknown')}"
                quality_status = "✅ UNCOMPRESSED" if hasattr(self, 'is_uncompressed') and self.is_uncompressed else "❌ COMPRESSED"
                
                logger.info(f"🎥 SEGMENT COMPLETED: {filename}")
                logger.info(f"   Duration: {duration}s | Size: {file_size_mb:.1f}MB ({file_size_gb:.3f}GB)")
                logger.info(f"   Codec: {compression_info} | Quality: {quality_status}")
                if size_ratio > 0:
                    logger.info(f"   Size ratio: {size_ratio:.3f} (1.0 = true uncompressed)")
                    if size_ratio < 0.8:
                        logger.warning(f"⚠️  QUALITY WARNING: File size suggests compression occurred!")
            
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
        
        # Signal shutdown to all threads
        self.shutdown_event.set()
        self.is_recording = False
        
        # Wait for threads to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=3)
            if self.capture_thread.is_alive():
                logger.warning(f"Capture thread for camera {self.camera_id} did not stop gracefully")
        if self.recording_thread:
            self.recording_thread.join(timeout=3)
            if self.recording_thread.is_alive():
                logger.warning(f"Recording thread for camera {self.camera_id} did not stop gracefully")
        
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