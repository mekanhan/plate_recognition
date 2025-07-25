# 🎬 24/7 Continuous Video Recording Architecture

**Date**: 2025-07-25  
**Status**: 🎯 **CRITICAL FOUNDATION**  
**Goal**: Professional-grade continuous recording like Reolink systems

## 🏗️ Industry Standard Architecture

### How Professional Systems Work (Reolink, Hikvision, etc.)

```
Camera → Continuous Recording → Storage Management → Playback System
   ↓                ↓                    ↓              ↓
RTSP Stream    Background Process    Segment Files    Index Database
```

**Key Principles:**
1. **Recording is Primary** - Stream viewing is secondary
2. **Background Operation** - Independent of web UI
3. **Segment-based Storage** - Easy navigation and management
4. **Intelligent Buffering** - Smooth playback experience
5. **Automatic Cleanup** - Storage quota management

## 🎥 Recording Strategy

### Segment-based Recording (Industry Standard)

**Segment Length**: 10-15 minutes per file
- **Why 10-15 minutes?**
  - Fast seeking/navigation
  - Reasonable file sizes (100-500MB)
  - Corruption isolation
  - Network transfer friendly

**File Structure**:
```
/recordings/
├── camera_1/
│   ├── 2025/01/25/
│   │   ├── 00/  # Hour folders
│   │   │   ├── camera_1_20250125_000000_600.mp4   # 10-minute segments
│   │   │   ├── camera_1_20250125_001000_600.mp4
│   │   │   ├── camera_1_20250125_002000_600.mp4
│   │   │   └── ...
│   │   ├── 01/
│   │   └── ...
│   └── index.db  # SQLite index for fast seeking
├── camera_2/
└── camera_3/
```

**Filename Convention**: `camera_{id}_{YYYYMMDD}_{HHMMSS}_{duration}.mp4`

## 🔧 Technical Implementation

### 1. Background Recording Service

```python
# core/recording/continuous_recorder.py
import asyncio
import cv2
import os
from datetime import datetime, timedelta
from pathlib import Path
import threading
import queue
import sqlite3

class ContinuousRecorder:
    def __init__(self, camera_config):
        self.camera_id = camera_config['id']
        self.rtsp_url = camera_config['rtsp_url']
        self.storage_path = f"/recordings/camera_{self.camera_id}"
        self.segment_duration = 600  # 10 minutes in seconds
        
        # Recording state
        self.is_recording = False
        self.current_writer = None
        self.current_segment_start = None
        self.frame_queue = queue.Queue(maxsize=300)  # 10-second buffer at 30fps
        
        # Storage management
        self.max_storage_days = 30  # Keep 30 days by default
        
        self.ensure_directories()
        self.init_index_database()
    
    def ensure_directories(self):
        """Create directory structure"""
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
    
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
    
    async def start_recording(self):
        """Start continuous recording"""
        if self.is_recording:
            return
        
        self.is_recording = True
        
        # Start capture thread
        capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        capture_thread.start()
        
        # Start recording thread
        recording_thread = threading.Thread(target=self._process_frames, daemon=True)
        recording_thread.start()
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_old_recordings, daemon=True)
        cleanup_thread.start()
        
        print(f"Started continuous recording for camera {self.camera_id}")
    
    def _capture_frames(self):
        """Capture frames from RTSP stream"""
        cap = None
        reconnect_delay = 1
        
        while self.is_recording:
            try:
                if cap is None:
                    cap = cv2.VideoCapture(self.rtsp_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
                    reconnect_delay = 1
                
                ret, frame = cap.read()
                if ret:
                    timestamp = datetime.now()
                    
                    # Add to queue (drop oldest if full)
                    try:
                        self.frame_queue.put((frame, timestamp), timeout=0.1)
                    except queue.Full:
                        # Drop oldest frame to maintain real-time processing
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put((frame, timestamp), timeout=0.1)
                        except queue.Empty:
                            pass
                else:
                    # Lost connection - reconnect
                    print(f"Lost connection to camera {self.camera_id}, reconnecting...")
                    if cap:
                        cap.release()
                        cap = None
                    
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 30)  # Exponential backoff, max 30s
                    
            except Exception as e:
                print(f"Capture error for camera {self.camera_id}: {e}")
                if cap:
                    cap.release()
                    cap = None
                time.sleep(5)
        
        if cap:
            cap.release()
    
    def _process_frames(self):
        """Process frames and write to video files"""
        while self.is_recording:
            try:
                # Get frame from queue
                frame, timestamp = self.frame_queue.get(timeout=1.0)
                
                # Check if we need to start a new segment
                if (self.current_writer is None or 
                    self._should_start_new_segment(timestamp)):
                    self._start_new_segment(timestamp)
                
                # Write frame to current segment
                if self.current_writer:
                    self.current_writer.write(frame)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error for camera {self.camera_id}: {e}")
    
    def _should_start_new_segment(self, timestamp):
        """Check if we should start a new video segment"""
        if self.current_segment_start is None:
            return True
        
        elapsed = (timestamp - self.current_segment_start).total_seconds()
        return elapsed >= self.segment_duration
    
    def _start_new_segment(self, timestamp):
        """Start a new video segment"""
        # Close current writer
        if self.current_writer:
            self._finalize_current_segment()
        
        # Create new segment
        self.current_segment_start = timestamp
        
        # Generate filename
        date_path = timestamp.strftime("%Y/%m/%d/%H")
        segment_dir = f"{self.storage_path}/{date_path}"
        Path(segment_dir).mkdir(parents=True, exist_ok=True)
        
        filename = f"camera_{self.camera_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{self.segment_duration}.mp4"
        self.current_filepath = f"{segment_dir}/{filename}"
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.current_writer = cv2.VideoWriter(
            self.current_filepath,
            fourcc,
            30.0,  # FPS
            (640, 480)  # Resolution - adjust based on camera
        )
        
        print(f"Started new segment: {filename}")
    
    def _finalize_current_segment(self):
        """Finalize current video segment"""
        if self.current_writer:
            self.current_writer.release()
            
            # Get file info
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
                self.current_segment_start,
                end_time,
                duration,
                file_stats.st_size
            ))
            self.db_conn.commit()
            
            self.current_writer = None
            print(f"Finalized segment: {filename} ({duration}s, {file_stats.st_size} bytes)")
    
    def _cleanup_old_recordings(self):
        """Cleanup old recordings based on retention policy"""
        while self.is_recording:
            try:
                cutoff_date = datetime.now() - timedelta(days=self.max_storage_days)
                
                # Find old segments
                cursor = self.db_conn.execute('''
                    SELECT filename, start_time FROM segments 
                    WHERE start_time < ?
                ''', (cutoff_date,))
                
                old_segments = cursor.fetchall()
                
                for filename, start_time in old_segments:
                    # Delete file
                    start_dt = datetime.fromisoformat(start_time)
                    date_path = start_dt.strftime("%Y/%m/%d/%H")
                    file_path = f"{self.storage_path}/{date_path}/{filename}"
                    
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Deleted old recording: {filename}")
                    
                    # Remove from database
                    self.db_conn.execute('DELETE FROM segments WHERE filename = ?', (filename,))
                
                self.db_conn.commit()
                
                # Sleep for 1 hour before next cleanup
                time.sleep(3600)
                
            except Exception as e:
                print(f"Cleanup error for camera {self.camera_id}: {e}")
                time.sleep(3600)
    
    def stop_recording(self):
        """Stop continuous recording"""
        self.is_recording = False
        
        if self.current_writer:
            self._finalize_current_segment()
        
        self.db_conn.close()
        print(f"Stopped recording for camera {self.camera_id}")
```

### 2. Recording Manager

```python
# core/recording/recording_manager.py
class RecordingManager:
    def __init__(self):
        self.recorders = {}
        self.config_file = "config/cameras.json"
    
    async def start_all_recordings(self):
        """Start recording for all configured cameras"""
        cameras = self.load_camera_configs()
        
        for camera in cameras:
            if camera.get('recording_enabled', True):
                await self.start_camera_recording(camera)
    
    async def start_camera_recording(self, camera_config):
        """Start recording for a specific camera"""
        camera_id = camera_config['id']
        
        if camera_id not in self.recorders:
            recorder = ContinuousRecorder(camera_config)
            self.recorders[camera_id] = recorder
            await recorder.start_recording()
    
    def stop_camera_recording(self, camera_id):
        """Stop recording for a specific camera"""
        if camera_id in self.recorders:
            self.recorders[camera_id].stop_recording()
            del self.recorders[camera_id]
    
    def load_camera_configs(self):
        """Load camera configurations"""
        # Implementation to load from database or config file
        return [
            {
                'id': 1,
                'name': 'Test Camera 1',
                'rtsp_url': 'rtsp://admin:Mekus_1987@10.0.0.181:554/h264Preview_01_sub',
                'recording_enabled': True
            }
        ]
```

### 3. Playback System

```python
# core/playback/video_playback.py
class VideoPlayback:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.storage_path = f"/recordings/camera_{camera_id}"
        self.db_path = f"{self.storage_path}/index.db"
    
    def get_recordings_for_timerange(self, start_time, end_time):
        """Get list of recordings for a time range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT filename, start_time, end_time, duration, file_size
            FROM segments 
            WHERE start_time <= ? AND end_time >= ?
            ORDER BY start_time
        ''', (end_time, start_time))
        
        recordings = cursor.fetchall()
        conn.close()
        
        return [
            {
                'filename': row[0],
                'start_time': row[1],
                'end_time': row[2],
                'duration': row[3],
                'file_size': row[4],
                'url': f'/api/v1/playback/{self.camera_id}/{row[0]}'
            }
            for row in recordings
        ]
    
    def get_recording_url(self, filename):
        """Get direct URL to video file"""
        # Find the file path
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            'SELECT start_time FROM segments WHERE filename = ?', 
            (filename,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            start_time = datetime.fromisoformat(result[0])
            date_path = start_time.strftime("%Y/%m/%d/%H")
            return f"{self.storage_path}/{date_path}/{filename}"
        
        return None
```

## 🚀 System Integration

### 1. Service Startup (Independent of Web UI)

```python
# main_recording_service.py
import asyncio
from core.recording.recording_manager import RecordingManager

async def main():
    """Main recording service - runs independently"""
    print("Starting 24/7 Recording Service...")
    
    recording_manager = RecordingManager()
    
    # Start all recordings
    await recording_manager.start_all_recordings()
    
    print("All recordings started. Service running...")
    
    # Keep service running
    try:
        while True:
            await asyncio.sleep(60)  # Check every minute
            # Health checks, restart failed recordings, etc.
    except KeyboardInterrupt:
        print("Shutting down recording service...")
        # Cleanup
    
if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Web API Integration

```python
# API endpoints for accessing recordings
@app.get("/api/v1/cameras/{camera_id}/recordings")
async def get_recordings(
    camera_id: int,
    start_time: datetime,
    end_time: datetime
):
    """Get recordings for time range"""
    playback = VideoPlayback(camera_id)
    recordings = playback.get_recordings_for_timerange(start_time, end_time)
    return {"recordings": recordings}

@app.get("/api/v1/playback/{camera_id}/{filename}")
async def stream_recording(camera_id: int, filename: str):
    """Stream recorded video file"""
    playback = VideoPlayback(camera_id)
    file_path = playback.get_recording_url(filename)
    
    if file_path and os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="video/mp4",
            headers={"Accept-Ranges": "bytes"}  # Enable seeking
        )
    
    raise HTTPException(status_code=404, detail="Recording not found")
```

## 📊 Storage Management Strategy

### Storage Calculations
```
Camera Resolution: 640x480 @ 30fps
Compression: H.264 (good quality)
Estimated bitrate: 1-2 Mbps

Per day per camera: ~10-20 GB
Per month per camera: ~300-600 GB
Per year per camera: ~3.6-7.2 TB
```

### Storage Tiers
1. **Hot Storage** (0-7 days): SSD for fast access
2. **Warm Storage** (8-30 days): Fast HDD
3. **Cold Storage** (30+ days): Archive or cloud storage

### Auto-cleanup Rules
```python
# Storage policies
STORAGE_POLICIES = {
    'default': {
        'retention_days': 30,
        'hot_storage_days': 7,
        'max_storage_gb': 1000
    },
    'critical_camera': {
        'retention_days': 90,
        'hot_storage_days': 14,
        'max_storage_gb': 2000
    }
}
```

## 🔥 Key Benefits

### 1. **Reliability Like Reolink**
- Independent background service
- Automatic reconnection
- Corruption isolation via segments
- Fast seeking and navigation

### 2. **Performance**
- Minimal latency buffering
- Efficient storage utilization
- Fast playback startup
- Smooth timeline scrubbing

### 3. **Scalability**
- Per-camera recording processes
- Configurable storage policies
- Easy to add new cameras
- Horizontal scaling possible

### 4. **Web UI Integration**
- Live streaming works independently
- Recording continues regardless of UI
- Timeline-based playback interface
- Seamless switching between live and recorded

This architecture provides the professional foundation you need - recordings happen 24/7 regardless of the web interface, with efficient storage and fast playback capabilities matching commercial systems like Reolink.