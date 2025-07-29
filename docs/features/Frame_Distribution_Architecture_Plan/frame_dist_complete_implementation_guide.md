Complete Implementation Guide
File Structure Changes
plate_recognition/
├── routers/
│   ├── streaming.py (NEW FILE - create this)
│   └── ... (existing files)
├── camera.py (MODIFY)
├── main.py (MODIFY - add router)
└── ... (other files unchanged)

Step 1: Modify camera.py
Add these imports at the top:
pythonimport threading
import queue
Add these methods to Camera class:
pythonclass Camera:
    def __init__(self, camera_info, recording_queue, detection_queue):
        # ... existing init code ...
        
        # ADD THESE LINES:
        self.latest_frame = None
        self.frame_lock = threading.Lock()
    
    # ADD THIS NEW METHOD:
    def get_latest_frame(self):
        """Get the most recent frame for web streaming"""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    # MODIFY capture_frames method:
    def capture_frames(self):
        """Capture frames from the camera."""
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                logger.warning(f"Camera {self.camera_info['name']} not connected. Attempting to reconnect...")
                self.connect()
                time.sleep(5)
                continue
            
            ret, frame = self.cap.read()
            if not ret:
                logger.error(f"Failed to read frame from camera {self.camera_info['name']}")
                self.cap.release()
                self.cap = None
                continue
            
            # ADD THIS SECTION - Update latest frame for web streaming
            with self.frame_lock:
                self.latest_frame = frame.copy()
            
            # EXISTING CODE - Recording queue
            try:
                self.recording_queue.put(frame, timeout=0.1)
            except queue.Full:
                logger.warning(f"Recording queue full for camera {self.camera_info['name']}")
            
            # EXISTING CODE - Detection queue  
            self.frame_count += 1
            if self.frame_count % self.detection_interval == 0:
                try:
                    self.detection_queue.put((frame, self.camera_info['id']), timeout=0.1)
                except queue.Full:
                    logger.warning(f"Detection queue full for camera {self.camera_info['name']}")

Step 2: Create routers/streaming.py
Complete new file:
pythonfrom fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
import cv2
import asyncio
from typing import Generator
import logging

from camera_manager import camera_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/streaming", tags=["streaming"])

def generate_mjpeg(camera_id: str) -> Generator:
    """Generate MJPEG stream for a camera"""
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        logger.error(f"Camera {camera_id} not found")
        return
    
    while True:
        frame = camera.get_latest_frame()
        if frame is None:
            # If no frame available, wait a bit
            asyncio.run(asyncio.sleep(0.1))
            continue
        
        # Encode frame as JPEG
        try:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # Yield in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   buffer.tobytes() + b'\r\n')
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            break

@router.get("/video_feed/{camera_id}")
async def video_feed(camera_id: str):
    """
    Stream video feed from a camera as MJPEG
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    return StreamingResponse(
        generate_mjpeg(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@router.get("/snapshot/{camera_id}")
async def get_snapshot(camera_id: str):
    """
    Get a single snapshot from a camera
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    frame = camera.get_latest_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="No frame available")
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    return Response(
        content=buffer.tobytes(),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@router.get("/cameras")
async def list_cameras():
    """
    List all available cameras
    """
    cameras = camera_manager.get_all_cameras()
    return {
        "cameras": [
            {
                "id": cam_id,
                "name": camera.camera_info.get('name', cam_id),
                "status": "online" if camera.cap and camera.cap.isOpened() else "offline"
            }
            for cam_id, camera in cameras.items()
        ]
    }

Step 3: Update main.py
Add import:
pythonfrom routers import plates, cameras, events, dashboard, streaming
Add router:
python# After existing routers
app.include_router(streaming.router)

Step 4: Update camera_manager.py
Add method to get camera:
pythonclass CameraManager:
    # ... existing code ...
    
    def get_camera(self, camera_id: str):
        """Get a specific camera by ID"""
        return self.cameras.get(camera_id)
    
    def get_all_cameras(self):
        """Get all cameras"""
        return self.cameras

Step 5: Frontend HTML Example
Create test_streaming.html:
html<!DOCTYPE html>
<html>
<head>
    <title>Camera Streaming Test</title>
    <style>
        .camera-container {
            display: inline-block;
            margin: 10px;
            border: 1px solid #ccc;
            padding: 10px;
        }
        .camera-title {
            font-weight: bold;
            margin-bottom: 10px;
        }
        img {
            max-width: 640px;
            height: auto;
        }
    </style>
</head>
<body>
    <h1>Camera Streaming Test</h1>
    
    <div id="cameras"></div>
    
    <script>
        // Fetch available cameras
        fetch('/api/streaming/cameras')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('cameras');
                
                data.cameras.forEach(camera => {
                    const div = document.createElement('div');
                    div.className = 'camera-container';
                    
                    div.innerHTML = `
                        <div class="camera-title">${camera.name} (${camera.id})</div>
                        <div>Status: ${camera.status}</div>
                        <div style="margin-top: 10px;">
                            <button onclick="showMJPEG('${camera.id}')">MJPEG Stream</button>
                            <button onclick="showSnapshot('${camera.id}')">Snapshot Mode</button>
                        </div>
                        <img id="camera-${camera.id}" src="/api/streaming/snapshot/${camera.id}" />
                    `;
                    
                    container.appendChild(div);
                });
            });
        
        function showMJPEG(cameraId) {
            document.getElementById(`camera-${cameraId}`).src = 
                `/api/streaming/video_feed/${cameraId}`;
        }
        
        function showSnapshot(cameraId) {
            const img = document.getElementById(`camera-${cameraId}`);
            
            function updateSnapshot() {
                img.src = `/api/streaming/snapshot/${cameraId}?t=${Date.now()}`;
            }
            
            updateSnapshot();
            setInterval(updateSnapshot, 500); // 2 FPS
        }
    </script>
</body>
</html>

Testing Steps

Start your application
bashpython main.py

Test endpoints
bash# Test snapshot
curl http://localhost:8000/api/streaming/snapshot/camera1 --output test.jpg

# Test camera list
curl http://localhost:8000/api/streaming/cameras

Open browser

Go to http://localhost:8000/test_streaming.html
Or directly view stream: http://localhost:8000/api/streaming/video_feed/camera1




Troubleshooting
If no image appears:

Check camera is connected: Look at logs
Verify camera ID is correct
Check latest_frame is being updated in camera.py

If image is frozen:

Check capture_frames thread is running
Verify frame_lock isn't deadlocked
Look for "queue full" warnings in logs

This should be complete enough for implementation. The AI agent needs to:

Create the new streaming.py file
Modify specific methods in camera.py
Add one line to main.py
Test with the provided HTML