# Camera Integration Guide

## Prerequisites
- Python 3.9+ installed
- IP camera on network with known credentials
- OpenCV installed (`pip install opencv-python`)
- Network access to camera

## Overview
This guide covers connecting to IP cameras, capturing frames reliably, and handling common camera issues without attempting browser streaming.

## Step-by-Step Implementation

### 1. Camera Connection Manager

```python
# camera_manager.py
import cv2
import threading
import queue
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np

@dataclass
class CameraConfig:
    """Camera configuration"""
    camera_id: str
    name: str
    ip_address: str
    username: str
    password: str
    port: int = 554
    stream_path: str = "/stream"
    protocol: str = "rtsp"
    
    @property
    def stream_url(self) -> str:
        """Build complete stream URL"""
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.ip_address}:{self.port}{self.stream_path}"

class CameraStream:
    """Handles individual camera connection and frame capture"""
    
    def __init__(self, config: CameraConfig, buffer_size: int = 30):
        self.config = config
        self.buffer_size = buffer_size
        self.frame_buffer = queue.Queue(maxsize=buffer_size)
        self.is_running = False
        self.capture = None
        self.capture_thread = None
        self.last_frame = None
        self.last_frame_time = 0
        self.error_count = 0
        self.logger = logging.getLogger(f"Camera.{config.camera_id}")
        
    def start(self):
        """Start camera capture thread"""
        if not self.is_running:
            self.is_running = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                name=f"Camera-{self.config.camera_id}"
            )
            self.capture_thread.daemon = True
            self.capture_thread.start()
            self.logger.info(f"Started camera stream: {self.config.name}")
    
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=5.0)
        if self.capture:
            self.capture.release()
        self.logger.info(f"Stopped camera stream: {self.config.name}")
    
    def _capture_loop(self):
        """Main capture loop - runs in separate thread"""
        reconnect_delay = 5
        
        while self.is_running:
            try:
                # Connect to camera
                if not self._connect():
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 1.5, 60)
                    continue
                
                reconnect_delay = 5  # Reset on successful connect
                self.error_count = 0
                
                # Capture frames
                while self.is_running and self.capture.isOpened():
                    ret, frame = self.capture.read()
                    
                    if not ret or frame is None:
                        self.logger.warning("Failed to read frame")
                        break
                    
                    # Update last frame
                    self.last_frame = frame.copy()
                    self.last_frame_time = time.time()
                    
                    # Add to buffer (drop old frames if full)
                    try:
                        self.frame_buffer.put_nowait(frame)
                    except queue.Full:
                        try:
                            self.frame_buffer.get_nowait()
                            self.frame_buffer.put_nowait(frame)
                        except queue.Empty:
                            pass
                
            except Exception as e:
                self.logger.error(f"Capture error: {e}")
                self.error_count += 1
                
            finally:
                if self.capture:
                    self.capture.release()
                    self.capture = None
    
    def _connect(self) -> bool:
        """Connect to camera"""
        try:
            self.logger.info(f"Connecting to {self.config.stream_url}")
            
            # Create capture with optimal settings
            self.capture = cv2.VideoCapture(self.config.stream_url)
            
            # Set capture properties
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
            
            # For RTSP, try TCP transport
            if self.config.protocol == "rtsp":
                self.capture.release()
                self.capture = cv2.VideoCapture(self.config.stream_url + "?tcp")
            
            # Test connection
            if not self.capture.isOpened():
                raise Exception("Failed to open stream")
            
            ret, frame = self.capture.read()
            if not ret or frame is None:
                raise Exception("Failed to read test frame")
            
            self.logger.info("Successfully connected to camera")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            if self.capture:
                self.capture.release()
                self.capture = None
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame from buffer"""
        try:
            # Try to get from buffer first
            return self.frame_buffer.get_nowait()
        except queue.Empty:
            # Return last known frame if buffer empty
            return self.last_frame.copy() if self.last_frame is not None else None
    
    def get_snapshot(self) -> Optional[np.ndarray]:
        """Get single snapshot (latest frame)"""
        return self.last_frame.copy() if self.last_frame is not None else None
    
    def is_healthy(self) -> bool:
        """Check if camera stream is healthy"""
        if not self.is_running or not self.capture:
            return False
        
        # Check if we've received frames recently
        if time.time() - self.last_frame_time > 10:
            return False
        
        return self.error_count < 5

class CameraManager:
    """Manages multiple camera streams"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        self.logger = logging.getLogger("CameraManager")
    
    def add_camera(self, config: CameraConfig) -> bool:
        """Add and start a new camera"""
        if config.camera_id in self.cameras:
            self.logger.warning(f"Camera {config.camera_id} already exists")
            return False
        
        camera = CameraStream(config)
        camera.start()
        self.cameras[config.camera_id] = camera
        return True
    
    def remove_camera(self, camera_id: str):
        """Stop and remove a camera"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
    
    def get_camera(self, camera_id: str) -> Optional[CameraStream]:
        """Get camera by ID"""
        return self.cameras.get(camera_id)
    
    def get_all_cameras(self) -> Dict[str, CameraStream]:
        """Get all cameras"""
        return self.cameras
    
    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()
```

### 2. Configuration File

```yaml
# config/cameras.yaml
cameras:
  - camera_id: "entrance_cam"
    name: "Entrance Camera"
    ip_address: "10.0.0.181"
    username: "admin"
    password: "your_password"
    port: 554
    stream_path: "/stream"
    protocol: "rtsp"
    
  - camera_id: "exit_cam"
    name: "Exit Camera"  
    ip_address: "10.0.0.182"
    username: "admin"
    password: "your_password"
    port: 554
    stream_path: "/stream"
    protocol: "rtsp"
```

### 3. Usage Example

```python
# main.py
import yaml
import logging
from camera_manager import CameraManager, CameraConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load configuration
with open('config/cameras.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create camera manager
manager = CameraManager()

# Add cameras from config
for cam_config in config['cameras']:
    camera_config = CameraConfig(**cam_config)
    manager.add_camera(camera_config)

# Example: Get frames for processing
def process_cameras():
    while True:
        for camera_id, camera in manager.get_all_cameras().items():
            if camera.is_healthy():
                frame = camera.get_frame()
                if frame is not None:
                    # Process frame (send to AI pipeline)
                    process_frame(camera_id, frame)
            else:
                logging.warning(f"Camera {camera_id} is unhealthy")
        
        time.sleep(0.1)  # Process at ~10 FPS
```

## Common Pitfalls

### ❌ DON'T Do This:
```python
# Don't try to stream to browser
@app.get("/video_feed/{camera_id}")
async def video_feed(camera_id: str):
    # This will cause pain and suffering
    return StreamingResponse(generate_frames())
```

### ✅ DO This Instead:
```python
# Provide snapshots for web display
@app.get("/camera/{camera_id}/snapshot")
async def get_snapshot(camera_id: str):
    camera = manager.get_camera(camera_id)
    if camera and camera.is_healthy():
        frame = camera.get_snapshot()
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            return Response(content=buffer.tobytes(), media_type="image/jpeg")
    
    # Return placeholder image
    return FileResponse("static/camera_offline.jpg")
```

## Network Camera URLs

### Common Formats by Manufacturer:
```python
CAMERA_URLS = {
    "hikvision": {
        "main": "/Streaming/Channels/101",
        "sub": "/Streaming/Channels/102"
    },
    "dahua": {
        "main": "/cam/realmonitor?channel=1&subtype=0",
        "sub": "/cam/realmonitor?channel=1&subtype=1"  
    },
    "axis": {
        "main": "/axis-cgi/mjpg/video.cgi",
        "h264": "/axis-media/media.amp"
    },
    "generic": {
        "main": "/stream",
        "onvif": "/onvif/device_service"
    }
}
```

## Verification

### Test Camera Connection:
```python
# test_camera.py
def test_camera_connection(config: CameraConfig):
    """Test if camera is accessible"""
    print(f"Testing camera: {config.name}")
    print(f"URL: {config.stream_url}")
    
    cap = cv2.VideoCapture(config.stream_url)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print("✅ Connection successful!")
            print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
            cv2.imwrite(f"test_{config.camera_id}.jpg", frame)
            print(f"   Saved test image")
        else:
            print("❌ Could not read frame")
    else:
        print("❌ Could not connect to camera")
    
    cap.release()
```

### Expected Output:
```
2024-01-24 10:30:45 - CameraManager - INFO - Started camera stream: Entrance Camera
2024-01-24 10:30:46 - Camera.entrance_cam - INFO - Connecting to rtsp://admin:***@10.0.0.181:554/stream
2024-01-24 10:30:47 - Camera.entrance_cam - INFO - Successfully connected to camera
```

## Performance Tips

1. **Use Threading**: Each camera gets its own thread
2. **Buffer Frames**: Don't process every frame
3. **Handle Errors**: Cameras disconnect, networks fail
4. **Monitor Health**: Track connection status
5. **Limit FPS**: Process at reasonable rate (5-10 FPS usually enough)

## Next Steps

Continue to: **[03 - AI Processing Pipeline](./03-ai-processing-pipeline.md)**

---

*AI Agent Note: This approach captures frames locally without any browser streaming. The frame buffer ensures smooth processing even with network hiccups.*