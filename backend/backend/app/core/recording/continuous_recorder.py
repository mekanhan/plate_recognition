"""
Continuous Recorder for 24/7 Recording System
Handles continuous video recording with segment management
"""
import asyncio
import cv2
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, Event
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ContinuousRecorder:
    """Records video continuously from a camera source"""
    
    def __init__(
        self,
        camera_id: int,
        camera_url: str,
        output_dir: str = "recordings",
        segment_duration: int = 600,
        buffer_size: int = 300
    ):
        self.camera_id = camera_id
        self.camera_url = camera_url
        self.output_dir = Path(output_dir) / f"camera_{camera_id}"
        self.segment_duration = segment_duration
        self.buffer_size = buffer_size
        
        # Recording state
        self.is_recording = False
        self._stop_event = Event()
        self._recording_thread = None
        self._frame_queue = Queue(maxsize=buffer_size)
        
        # Video capture
        self.cap = None
        self.writer = None
        self.current_segment_path = None
        self.segment_start_time = None
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Initialized recorder for camera {camera_id}")
    
    def _init_database(self):
        """Initialize SQLite database for segment indexing"""
        db_path = self.output_dir / "index.db"
        
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for fast lookup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_start_time 
                ON video_segments(start_time)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_camera_time 
                ON video_segments(camera_id, start_time)
            """)
            
            conn.commit()
    
    def start(self):
        """Start continuous recording"""
        if self.is_recording:
            logger.warning(f"Camera {self.camera_id} is already recording")
            return
        
        self.is_recording = True
        self._stop_event.clear()
        
        # Start recording thread
        self._recording_thread = Thread(
            target=self._recording_loop,
            name=f"Recorder-Camera-{self.camera_id}"
        )
        self._recording_thread.start()
        
        logger.info(f"Started recording for camera {self.camera_id}")
    
    def stop(self):
        """Stop continuous recording"""
        if not self.is_recording:
            return
        
        logger.info(f"Stopping recording for camera {self.camera_id}")
        
        self.is_recording = False
        self._stop_event.set()
        
        # Wait for thread to finish
        if self._recording_thread:
            self._recording_thread.join(timeout=5)
        
        # Cleanup
        self._cleanup()
        
        logger.info(f"Stopped recording for camera {self.camera_id}")
    
    def _recording_loop(self):
        """Main recording loop"""
        try:
            # Initialize capture
            self.cap = cv2.VideoCapture(self.camera_url)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id} at {self.camera_url}")
                return
            
            # Get video properties
            fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Camera {self.camera_id} properties: {width}x{height} @ {fps} fps")
            
            frame_count = 0
            segment_frames = fps * self.segment_duration
            
            while not self._stop_event.is_set():
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from camera {self.camera_id}")
                    # Try to reconnect
                    self._reconnect()
                    continue
                
                # Start new segment if needed
                if self.writer is None or frame_count >= segment_frames:
                    self._start_new_segment(width, height, fps)
                    frame_count = 0
                
                # Write frame
                if self.writer:
                    self.writer.write(frame)
                    frame_count += 1
                
                # Also queue frame for streaming if needed
                try:
                    self._frame_queue.put_nowait(frame)
                except:
                    # Queue full, drop oldest frame
                    try:
                        self._frame_queue.get_nowait()
                        self._frame_queue.put_nowait(frame)
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"Recording error for camera {self.camera_id}: {e}", exc_info=True)
        finally:
            self._cleanup()
    
    def _start_new_segment(self, width: int, height: int, fps: int):
        """Start a new video segment"""
        # Close current segment
        if self.writer:
            self._close_current_segment()
        
        # Generate new segment filename
        self.segment_start_time = datetime.now()
        timestamp = self.segment_start_time.strftime("%Y%m%d_%H%M%S")
        
        # Create date-based subdirectory
        date_dir = self.output_dir / self.segment_start_time.strftime("%Y/%m/%d/%H")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"camera_{self.camera_id}_{timestamp}_{self.segment_duration}.avi"
        self.current_segment_path = date_dir / filename
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.writer = cv2.VideoWriter(
            str(self.current_segment_path),
            fourcc,
            fps,
            (width, height)
        )
        
        logger.info(f"Started new segment: {filename}")
    
    def _close_current_segment(self):
        """Close current segment and update database"""
        if not self.writer or not self.current_segment_path:
            return
        
        self.writer.release()
        self.writer = None
        
        # Get file info
        if self.current_segment_path.exists():
            file_size = self.current_segment_path.stat().st_size
            end_time = datetime.now()
            
            # Update database
            db_path = self.output_dir / "index.db"
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO video_segments 
                    (camera_id, filename, file_path, start_time, end_time, duration_seconds, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.camera_id,
                    self.current_segment_path.name,
                    str(self.current_segment_path),
                    self.segment_start_time.isoformat(),
                    end_time.isoformat(),
                    int((end_time - self.segment_start_time).total_seconds()),
                    file_size
                ))
                conn.commit()
            
            logger.info(f"Closed segment: {self.current_segment_path.name} ({file_size} bytes)")
    
    def _reconnect(self):
        """Attempt to reconnect to camera"""
        logger.info(f"Attempting to reconnect to camera {self.camera_id}")
        
        if self.cap:
            self.cap.release()
        
        # Wait before reconnecting
        self._stop_event.wait(5)
        
        if not self._stop_event.is_set():
            self.cap = cv2.VideoCapture(self.camera_url)
            if self.cap.isOpened():
                logger.info(f"Reconnected to camera {self.camera_id}")
            else:
                logger.error(f"Failed to reconnect to camera {self.camera_id}")
    
    def _cleanup(self):
        """Clean up resources"""
        # Close current segment
        if self.writer:
            self._close_current_segment()
        
        # Release capture
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Clear queue
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except:
                break
    
    def get_latest_frame(self) -> Optional[Any]:
        """Get the latest frame from the buffer"""
        try:
            # Get most recent frame
            frame = None
            while not self._frame_queue.empty():
                frame = self._frame_queue.get_nowait()
            return frame
        except:
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get recorder status"""
        return {
            'camera_id': self.camera_id,
            'is_recording': self.is_recording,
            'current_segment': self.current_segment_path.name if self.current_segment_path else None,
            'segment_start_time': self.segment_start_time.isoformat() if self.segment_start_time else None,
            'queue_size': self._frame_queue.qsize()
        }