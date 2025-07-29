Core Concept
One camera connection → Internal distribution → Multiple consumers

Architecture Diagram
                    SINGLE CONNECTION POINT
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    CAMERA THREAD                         │
│  while True:                                             │
│      frame = camera.read()  # Only connection to camera │
│      distribute(frame)      # Send to all consumers     │
└─────────────────────────────────────────────────────────┘
                            ↓
              ┌─────────────┴─────────────┐
              │   FRAME DISTRIBUTOR       │
              │   • Makes frame copies    │
              │   • Manages queues        │
              │   • Thread-safe          │
              └─────────────┬─────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   RECORDING   │   │   DETECTION   │   │ WEB STREAMING │
│               │   │               │   │     (NEW)     │
│ Records 24/7  │   │ YOLO + OCR    │   │ Live viewing  │
│ Full quality  │   │ Full quality  │   │ Full quality  │
└───────────────┘   └───────────────┘   └───────────────┘

Implementation Details
1. Frame Distribution Code
python# camera.py - Modified capture method
class Camera:
    def __init__(self):
        # Existing queues
        self.recording_queue = Queue(maxsize=30)
        self.detection_queue = Queue(maxsize=10)
        
        # NEW: For web streaming
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
    def capture_frames(self):
        """Single thread that reads from camera"""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.reconnect()
                continue
            
            # DISTRIBUTE TO ALL CONSUMERS
            self.distribute_frame(frame)
    
    def distribute_frame(self, frame):
        """Send frame to all consumers"""
        
        # 1. Recording (existing)
        try:
            self.recording_queue.put_nowait(frame.copy())
        except queue.Full:
            pass  # Skip if full
        
        # 2. Detection (existing) 
        if self.should_process_frame():
            try:
                self.detection_queue.put_nowait(frame.copy())
            except queue.Full:
                pass
        
        # 3. Web Streaming (NEW)
        with self.frame_lock:
            self.latest_frame = frame.copy()
2. Consumer Architecture
RECORDING CONSUMER
├── Input: recording_queue
├── Process: Compress & save to MP4
├── Output: Video files on disk
└── Runs in: separate thread

DETECTION CONSUMER  
├── Input: detection_queue
├── Process: YOLO detect → OCR read plates
├── Output: Events to database
└── Runs in: separate thread

WEB STREAMING CONSUMER (NEW)
├── Input: latest_frame (shared memory)
├── Process: JPEG encode on-demand
├── Output: HTTP response
└── Runs in: FastAPI async
3. Memory Management
python# Frame sizes at different qualities
1080p frame = 1920 x 1080 x 3 bytes = ~6 MB
4K frame = 3840 x 2160 x 3 bytes = ~25 MB

# Memory usage per camera
Recording queue (30 frames) = 30 x 6 MB = 180 MB
Detection queue (10 frames) = 10 x 6 MB = 60 MB  
Latest frame buffer = 6 MB
Total per camera ≈ 250 MB (1080p) or 1 GB (4K)
4. Thread Safety
python# Each consumer is independent
Recording Thread → Reads from recording_queue only
Detection Thread → Reads from detection_queue only
Web Requests → Read from latest_frame with lock

# No conflicts, no shared state between consumers

API Integration
New Streaming Endpoints
python# routers/streaming.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response

router = APIRouter(prefix="/api/streaming")

@router.get("/snapshot/{camera_id}")
async def get_snapshot(camera_id: str):
    """Single frame snapshot"""
    camera = camera_manager.get_camera(camera_id)
    frame = camera.get_latest_frame()
    
    if frame is None:
        return Response(status_code=503)
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame, 
        [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    return Response(
        content=buffer.tobytes(),
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache"}
    )

@router.get("/video_feed/{camera_id}")
async def video_feed(camera_id: str):
    """MJPEG video stream"""
    def generate():
        camera = camera_manager.get_camera(camera_id)
        while True:
            frame = camera.get_latest_frame()
            if frame is None:
                continue
                
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   buffer.tobytes() + b'\r\n')
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

Benefits of This Architecture
✅ Solves Connection Limit

Only ONE connection to camera
Camera sees single client
No connection rejections

✅ Maintains Quality

Each consumer gets full resolution
No quality degradation
No re-encoding between stages

✅ Independent Scaling

Recording can run at 30 FPS
Detection can process at 10 FPS
Web can stream at variable FPS
Each consumer works at its own pace

✅ Minimal Code Changes

Existing recording code: unchanged
Existing detection code: unchanged
Just add distribution logic
Add streaming endpoints

✅ Fault Isolation

If web streaming fails → recording continues
If detection backs up → streaming unaffected
Each part fails independently


Performance Considerations
Network bandwidth (camera → server):
- 1080p @ 30 FPS = ~10 Mbps (single stream)
- 4K @ 30 FPS = ~40 Mbps (single stream)

Processing overhead:
- Frame copy: ~1ms per copy
- JPEG encoding: ~10ms per frame
- Total overhead: <5% CPU per camera
