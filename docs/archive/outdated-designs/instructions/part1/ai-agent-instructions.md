# AI Agent Instructions - LPR System Implementation

## 🎯 Project Context

You are implementing a License Plate Recognition (LPR) system. The frontend exists and works. You need to build the backend and AI pipeline.

**GitHub Repository**: https://github.com/mekanhan/plate_recognition/tree/clean-architecture

**Current State**:
- ✅ Frontend exists (keep it, modify streaming parts)
- ✅ Old backend deleted
- ✅ New folder structure created
- ❌ Need to implement AI pipeline
- ❌ Need to implement new backend
- ❌ Need to update frontend API calls

## ⚠️ CRITICAL RULES - READ FIRST

### NEVER DO THIS:
1. **NEVER stream RTSP video to web browsers** - Browsers cannot handle RTSP
2. **NEVER transcode video in real-time for browsers** - This will fail
3. **NEVER process video over internet** - Process locally only
4. **NEVER try to "fix" browser video streaming** - Use VLC instead

### ALWAYS DO THIS:
1. **Process video on same machine as cameras** - Local processing only
2. **Show snapshots in browser, not video** - Update every 5 seconds
3. **Use VLC or native apps for live video** - Proper tools
4. **Store video clips for playback** - Browsers can play MP4 files

## 📁 Project Structure to Create

```
plate_recognition/
├── ai_pipeline/
│   ├── __init__.py
│   ├── camera_manager.py      # Camera connection and capture
│   ├── processors.py          # AI detection pipeline
│   ├── models.py             # AI model wrappers
│   ├── video_recorder.py     # Video storage service
│   └── config.py             # Configuration
├── database/
│   ├── __init__.py
│   ├── models.py             # SQLAlchemy models
│   ├── service.py            # Database operations
│   └── migrations/           # Alembic migrations
├── api/
│   ├── __init__.py
│   ├── main.py               # FastAPI application
│   ├── routes/               # API endpoints
│   └── dependencies.py       # Shared dependencies
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── scripts/
│       └── deploy.sh
├── config/
│   ├── cameras.yaml          # Camera configurations
│   └── settings.py           # App settings
└── requirements.txt          # Python dependencies
```

## 📋 Phase 2: Core Pipeline Implementation

### Step 1: Create requirements.txt
```python
# requirements.txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
redis==5.0.1

# AI/ML
opencv-python==4.8.1.78
numpy==1.24.3
torch==2.1.1
torchvision==0.16.1
ultralytics==8.0.200
easyocr==1.7.1

# Video processing
av==11.0.0
pillow==10.1.0

# Utilities
pyyaml==6.0.1
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
aiofiles==23.2.1

# Monitoring
prometheus-client==0.19.0
```

### Step 2: Camera Manager Implementation

Create `ai_pipeline/camera_manager.py`:

```python
"""
Camera Manager - Handles all camera connections
IMPORTANT: This captures from IP cameras locally, does NOT stream to browsers
"""
import cv2
import threading
import queue
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, List
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
        """Build RTSP URL - NEVER send this to browser!"""
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.ip_address}:{self.port}{self.stream_path}"

class CameraStream:
    """
    Handles individual camera connection
    Captures frames for AI processing - NOT for browser streaming!
    """
    
    def __init__(self, config: CameraConfig, buffer_size: int = 30):
        self.config = config
        self.frame_buffer = queue.Queue(maxsize=buffer_size)
        self.is_running = False
        self.capture = None
        self.capture_thread = None
        self.last_frame = None
        self.last_frame_time = 0
        self.logger = logging.getLogger(f"Camera.{config.camera_id}")
        
    def start(self):
        """Start capturing frames for AI processing"""
        if not self.is_running:
            self.is_running = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                name=f"Camera-{self.config.camera_id}"
            )
            self.capture_thread.daemon = True
            self.capture_thread.start()
            self.logger.info(f"Started capture: {self.config.name}")
    
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=5.0)
        if self.capture:
            self.capture.release()
            
    def _capture_loop(self):
        """
        Main capture loop - Gets frames for AI processing
        This is NOT for streaming to browsers!
        """
        while self.is_running:
            try:
                if not self._connect():
                    time.sleep(5)  # Retry connection
                    continue
                
                while self.is_running and self.capture.isOpened():
                    ret, frame = self.capture.read()
                    
                    if not ret or frame is None:
                        self.logger.warning("Failed to read frame")
                        break
                    
                    # Store for AI processing
                    self.last_frame = frame.copy()
                    self.last_frame_time = time.time()
                    
                    # Buffer for processing
                    try:
                        self.frame_buffer.put_nowait(frame)
                    except queue.Full:
                        # Drop old frame
                        try:
                            self.frame_buffer.get_nowait()
                            self.frame_buffer.put_nowait(frame)
                        except queue.Empty:
                            pass
                            
            except Exception as e:
                self.logger.error(f"Capture error: {e}")
                
    def _connect(self) -> bool:
        """Connect to camera via RTSP"""
        try:
            # IMPORTANT: This is local network connection only!
            self.capture = cv2.VideoCapture(self.config.stream_url)
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.capture.isOpened():
                return False
                
            # Test read
            ret, frame = self.capture.read()
            return ret and frame is not None
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get frame for AI processing (not for browser!)"""
        try:
            return self.frame_buffer.get_nowait()
        except queue.Empty:
            return self.last_frame.copy() if self.last_frame is not None else None
    
    def get_snapshot(self) -> Optional[np.ndarray]:
        """Get single snapshot for browser display"""
        return self.last_frame.copy() if self.last_frame is not None else None

class CameraManager:
    """Manages all camera streams for AI processing"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        
    def add_camera(self, config: CameraConfig) -> bool:
        """Add camera for AI processing"""
        if config.camera_id in self.cameras:
            return False
            
        camera = CameraStream(config)
        camera.start()
        self.cameras[config.camera_id] = camera
        return True
        
    def get_camera(self, camera_id: str) -> Optional[CameraStream]:
        return self.cameras.get(camera_id)
        
    def get_all_cameras(self) -> Dict[str, CameraStream]:
        return self.cameras
        
    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()
```

### Step 3: AI Processor Implementation

Create `ai_pipeline/processors.py`:

```python
"""
AI Processing Pipeline
Processes frames from cameras, detects license plates
"""
import asyncio
from typing import List, Dict, Optional
import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import logging
from datetime import datetime
import uuid

class LicensePlateDetector:
    """Detects and reads license plates"""
    
    def __init__(self):
        self.logger = logging.getLogger("LPDetector")
        
        # Load models
        self.vehicle_model = YOLO('yolov8m.pt')
        self.plate_model = YOLO('license_plate_detector.pt')  # You need to train/download this
        self.ocr_reader = easyocr.Reader(['en'])
        
        # Vehicle classes in COCO
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        
    def detect_vehicles(self, frame: np.ndarray) -> List[Dict]:
        """Detect vehicles in frame"""
        results = self.vehicle_model(frame)
        
        vehicles = []
        for r in results:
            if r.boxes is None:
                continue
                
            for box in r.boxes:
                class_id = int(box.cls)
                if class_id in self.vehicle_classes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    vehicles.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(box.conf),
                        'class': r.names[class_id]
                    })
        
        return vehicles
    
    def detect_plates(self, frame: np.ndarray, vehicles: List[Dict]) -> List[Dict]:
        """Detect license plates in vehicles"""
        plates = []
        
        for vehicle in vehicles:
            x1, y1, x2, y2 = vehicle['bbox']
            vehicle_roi = frame[y1:y2, x1:x2]
            
            if vehicle_roi.size == 0:
                continue
            
            # Detect plates in vehicle region
            # NOTE: You need a trained license plate model
            # For testing, you can use vehicle detection as placeholder
            # In production, train a specific plate detector
            
            # Placeholder - assumes plate in lower 1/3 of vehicle
            plate_y1 = int(y1 + (y2-y1) * 0.6)
            plate_bbox = [x1, plate_y1, x2, y2]
            
            plates.append({
                'vehicle_bbox': vehicle['bbox'],
                'plate_bbox': plate_bbox,
                'confidence': vehicle['confidence'] * 0.8,  # Placeholder
                'vehicle_type': vehicle['class']
            })
        
        return plates
    
    def read_plate(self, frame: np.ndarray, plate_bbox: List[int]) -> tuple[str, float]:
        """Read license plate text"""
        x1, y1, x2, y2 = plate_bbox
        plate_roi = frame[y1:y2, x1:x2]
        
        if plate_roi.size == 0:
            return "", 0.0
        
        # Preprocess
        plate_roi = self._preprocess_plate(plate_roi)
        
        # OCR
        results = self.ocr_reader.readtext(plate_roi)
        
        if not results:
            return "", 0.0
        
        # Combine text
        text = "".join([r[1] for r in results])
        confidence = sum([r[2] for r in results]) / len(results)
        
        return text.upper().replace(" ", ""), confidence
    
    def _preprocess_plate(self, plate_img: np.ndarray) -> np.ndarray:
        """Enhance plate image for OCR"""
        # Resize if too small
        h, w = plate_img.shape[:2]
        if w < 200:
            scale = 200 / w
            new_w = int(w * scale)
            new_h = int(h * scale)
            plate_img = cv2.resize(plate_img, (new_w, new_h))
        
        # Convert to grayscale
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img
            
        return gray

class ProcessingPipeline:
    """Main processing pipeline"""
    
    def __init__(self, detector: LicensePlateDetector):
        self.detector = detector
        self.logger = logging.getLogger("Pipeline")
        
    async def process_frame(self, camera_id: str, frame: np.ndarray) -> List[Dict]:
        """Process single frame"""
        detections = []
        
        # Detect vehicles
        vehicles = self.detector.detect_vehicles(frame)
        
        if not vehicles:
            return detections
        
        # Detect plates
        plates = self.detector.detect_plates(frame, vehicles)
        
        # Read plates
        for plate_info in plates:
            plate_text, confidence = self.detector.read_plate(frame, plate_info['plate_bbox'])
            
            if confidence > 0.5 and len(plate_text) >= 4:
                detection = {
                    'detection_id': str(uuid.uuid4()),
                    'camera_id': camera_id,
                    'timestamp': datetime.now(),
                    'plate_text': plate_text,
                    'confidence': confidence,
                    'vehicle_type': plate_info['vehicle_type'],
                    'vehicle_bbox': plate_info['vehicle_bbox'],
                    'plate_bbox': plate_info['plate_bbox']
                }
                detections.append(detection)
                
        return detections
```

### Step 4: Database Models

Create `database/models.py`:

```python
"""
Database models
Uses SQLAlchemy for async PostgreSQL
"""
from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Camera(Base):
    __tablename__ = 'cameras'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)
    location = Column(String(200))
    status = Column(String(20), default='active')
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Detection(Base):
    __tablename__ = 'detections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(50), nullable=False)
    plate_text = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    vehicle_type = Column(String(50))
    detected_at = Column(DateTime, nullable=False)
    vehicle_bbox = Column(JSON)
    plate_bbox = Column(JSON)
    snapshot_path = Column(String(500))
    video_clip_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

class VideoRecording(Base):
    __tablename__ = 'video_recordings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    has_detections = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Step 5: FastAPI Backend

Create `api/main.py`:

```python
"""
FastAPI Backend
IMPORTANT: This serves data and snapshots, NOT video streams!
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import io
from datetime import datetime
import asyncio

app = FastAPI(title="LPR System API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import your services
from ai_pipeline.camera_manager import CameraManager, CameraConfig
from ai_pipeline.processors import LicensePlateDetector, ProcessingPipeline

# Initialize services
camera_manager = CameraManager()
detector = LicensePlateDetector()
pipeline = ProcessingPipeline(detector)

@app.on_event("startup")
async def startup():
    """Initialize cameras on startup"""
    # Load camera configs (from file or database)
    cameras = [
        CameraConfig(
            camera_id="cam1",
            name="Entrance Camera",
            ip_address="10.0.0.181",
            username="admin",
            password="password"
        )
    ]
    
    for config in cameras:
        camera_manager.add_camera(config)
    
    # Start processing loop
    asyncio.create_task(processing_loop())

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    camera_manager.stop_all()

async def processing_loop():
    """Main processing loop - runs continuously"""
    while True:
        for camera_id, camera in camera_manager.get_all_cameras().items():
            frame = camera.get_frame()
            if frame is not None:
                # Process for detections
                detections = await pipeline.process_frame(camera_id, frame)
                
                # Save detections to database
                for detection in detections:
                    # TODO: Save to database
                    print(f"Detected: {detection['plate_text']}")
        
        await asyncio.sleep(0.1)  # Process at 10 FPS

# API ENDPOINTS - NO VIDEO STREAMING!

@app.get("/api/cameras")
async def get_cameras():
    """Get all cameras with status"""
    cameras = []
    for camera_id, camera in camera_manager.get_all_cameras().items():
        cameras.append({
            "id": camera.config.camera_id,
            "name": camera.config.name,
            "status": "online" if camera.last_frame_time > 0 else "offline",
            "location": camera.config.location
        })
    return cameras

@app.get("/api/cameras/{camera_id}/snapshot")
async def get_snapshot(camera_id: str):
    """
    Get current snapshot from camera
    This is for browser display - NOT video streaming!
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    frame = camera.get_snapshot()
    if frame is None:
        # Return placeholder image
        return FileResponse("static/camera_offline.jpg")
    
    # Convert to JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    
    return StreamingResponse(
        io.BytesIO(buffer.tobytes()),
        media_type="image/jpeg"
    )

@app.get("/api/detections/recent")
async def get_recent_detections(limit: int = 100):
    """Get recent license plate detections"""
    # TODO: Get from database
    return []

@app.post("/api/cameras/{camera_id}/open-vlc")
async def open_vlc(camera_id: str):
    """
    Provide RTSP URL for VLC
    Frontend should open VLC with this URL
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    return {
        "rtsp_url": camera.config.stream_url,
        "instructions": "Open VLC and use Media -> Open Network Stream with this URL"
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Step 6: Docker Configuration

Create `deployment/docker/Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p logs recordings detections

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `deployment/docker/docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: lpr_user
      POSTGRES_PASSWORD: lpr_password
      POSTGRES_DB: lpr_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://lpr_user:lpr_password@postgres:5432/lpr_db
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./recordings:/app/recordings
      - ./detections:/app/detections

volumes:
  postgres_data:
```

## 📋 Phase 3: Frontend Updates

### Update Frontend API Calls

1. **Remove ALL video streaming code**
2. **Replace with snapshot refreshing**

Update `frontend/src/components/CameraCard.js`:

```javascript
import React, { useState, useEffect } from 'react';

function CameraCard({ camera }) {
  const [snapshotUrl, setSnapshotUrl] = useState('');
  
  useEffect(() => {
    // Refresh snapshot every 5 seconds
    const updateSnapshot = () => {
      setSnapshotUrl(`/api/cameras/${camera.id}/snapshot?t=${Date.now()}`);
    };
    
    updateSnapshot();
    const interval = setInterval(updateSnapshot, 5000);
    
    return () => clearInterval(interval);
  }, [camera.id]);
  
  const openInVLC = async () => {
    // Get RTSP URL from backend
    const response = await fetch(`/api/cameras/${camera.id}/open-vlc`, {
      method: 'POST'
    });
    const data = await response.json();
    
    // Show instructions to user
    alert(`Open VLC and go to Media > Open Network Stream\n\nURL: ${data.rtsp_url}`);
    
    // Or try to open VLC directly (may not work in all browsers)
    window.location.href = `vlc://${data.rtsp_url}`;
  };
  
  return (
    <div className="camera-card">
      <h3>{camera.name}</h3>
      
      {/* Snapshot instead of video */}
      <img 
        src={snapshotUrl} 
        alt={camera.name}
        style={{ width: '100%', height: 'auto' }}
      />
      
      <div className="camera-controls">
        <span className={`status ${camera.status}`}>
          {camera.status}
        </span>
        
        <button onClick={openInVLC}>
          View Live in VLC
        </button>
      </div>
    </div>
  );
}

export default CameraCard;
```

## 🚀 Running the System

### Development Mode:

```bash
# Terminal 1: Start database
docker-compose up postgres redis

# Terminal 2: Start backend
cd /path/to/project
python -m uvicorn api.main:app --reload

# Terminal 3: Start frontend
cd frontend
npm start
```

### Production Mode:

```bash
# Build and run everything
docker-compose up --build
```

## ✅ Verification Checklist

1. **Camera Connection**: Can you see snapshots updating?
2. **AI Detection**: Are license plates being detected?
3. **Database**: Are detections being saved?
4. **VLC Integration**: Can you open streams in VLC?
5. **No Browser Streaming**: Confirm NO video elements in HTML

## ⚠️ Common Mistakes to Avoid

1. **DON'T** add `<video>` tags to frontend
2. **DON'T** try to convert RTSP to WebRTC
3. **DON'T** use FFmpeg to transcode for browsers
4. **DON'T** process video over the internet
5. **DO** use snapshots for browser display
6. **DO** use VLC for live viewing
7. **DO** process everything locally

## 📚 IMPORTANT: Read Documentation First!

**CRITICAL**: Complete documentation exists in `docs/documentation/` directory. READ THESE BEFORE CODING:

### Required Reading (in this order):
1. `docs/documentation/01-overview-architecture.md` - **READ FIRST!** Explains why no browser streaming
2. `docs/documentation/02-camera-integration.md` - Complete camera capture implementation
3. `docs/documentation/03-ai-processing-pipeline.md` - Full AI detection pipeline with code
4. `docs/documentation/04-database-design.md` - Complete database schema and video storage
5. `docs/documentation/05-web-dashboard.md` - Frontend implementation (data only, no video!)
6. `docs/documentation/06-live-view-solutions.md` - VLC and native app integration
7. `docs/documentation/07-deployment-guide.md` - Docker and production deployment
8. `docs/documentation/08-troubleshooting-faq.md` - Common issues and solutions

### Additional Advanced Documentation:
- `docs/documentation/video-processing-architecture.md` - How to handle video quality
- `docs/documentation/multi-model-architecture.md` - Adding more AI features
- `docs/documentation/innovative-ai-features.md` - Advanced features to stand out

**DO NOT START CODING WITHOUT READING THE DOCUMENTATION!**

The documentation contains:
- Complete working code examples
- Detailed explanations of what works and what doesn't
- Common pitfalls to avoid
- Best practices from industry

### Why This Documentation Matters:
1. **Avoids all common mistakes** - Especially browser streaming attempts
2. **Provides tested code** - Copy and adapt from documentation
3. **Explains the "why"** - Understanding prevents bad decisions
4. **Industry best practices** - Based on how companies actually do this

Remember: The system processes video locally and displays DATA in the browser, not video!

---

**Final Note for AI Agents**: This architecture is proven and works. Do not try to "improve" it by adding browser video streaming - it will fail. Follow these instructions exactly.