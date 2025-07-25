# Implementation Roadmap

**Date:** 2025-01-24  
**Version:** 1.0  
**Component:** Stream Feature Development Plan

## Implementation Overview

The Stream feature implementation follows a three-phase approach, building from basic video streaming to full real-time license plate recognition with production-ready features.

## Phase 1: Basic Video Streaming (3-4 days)

### Objective
Establish live video streaming from Test Camera 1 with basic web interface integration.

### 1.1 Backend Video Streaming Service (Day 1-2)

#### Camera Service Implementation
```python
# backend/app/services/camera_streaming_service.py
class CameraStreamingService:
    def __init__(self, camera_config: CameraConfig):
        self.camera_config = camera_config
        self.capture = None
        self.is_streaming = False
        self.frame_queue = asyncio.Queue(maxsize=30)
        
    async def connect_camera(self) -> bool:
        """Establish connection to IP camera"""
        
    async def start_streaming(self) -> AsyncGenerator[bytes, None]:
        """Start video frame capture and streaming"""
        
    async def stop_streaming(self):
        """Stop streaming and cleanup resources"""
```

**Key Components:**
- **OpenCV Integration**: Camera capture via `cv2.VideoCapture`
- **Async Frame Processing**: Non-blocking frame acquisition
- **MJPEG Encoding**: Convert frames to JPEG for HTTP streaming
- **Connection Management**: Handle camera disconnections and reconnections

#### HTTP Streaming Endpoint
```python
# backend/app/api/v1/endpoints/streaming.py
@router.get("/stream/video/{camera_id}")
async def stream_video(camera_id: int):
    """Stream live video as MJPEG"""
    camera = await get_camera_by_id(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    streaming_service = CameraStreamingService(camera)
    
    async def generate_frames():
        async for frame in streaming_service.start_streaming():
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
```

**Implementation Tasks:**
- [ ] Create `CameraStreamingService` class
- [ ] Implement OpenCV camera connection for IP cameras
- [ ] Add MJPEG frame encoding
- [ ] Create `/stream/video/{camera_id}` endpoint
- [ ] Add error handling for camera failures
- [ ] Test with Test Camera 1 (10.0.0.181:80/mjpeg)

### 1.2 Frontend Integration (Day 2-3)

#### Integrate Existing Streaming UI
**Target**: Leverage existing sophisticated UI in `frontend/drafts/templates/stream.html`

**Integration Tasks:**
- [ ] Move stream.html to main application templates
- [ ] Update video source URL to `/stream/video/3` (Test Camera 1)
- [ ] Integrate with existing navigation and authentication
- [ ] Test responsive design and controls
- [ ] Ensure compatibility with current theme system

#### Stream Controls Implementation
```javascript
// Enhanced integration with existing StreamPage class
class StreamPageIntegrated extends StreamPage {
    constructor() {
        super();
        this.apiBaseUrl = '/api/v1';
        this.streamUrl = `/stream/video/${this.cameraId}`;
    }
    
    async startStream() {
        // Integration with backend streaming service
        const response = await fetch(`${this.apiBaseUrl}/streams/${this.cameraId}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quality: 'high', detection_enabled: false })
        });
        
        if (response.ok) {
            this.videoFeed.src = this.streamUrl;
            this.updateStreamStatus('connected');
        }
    }
}
```

### 1.3 Testing and Validation (Day 3-4)

**Test Scenarios:**
- [ ] Stream Test Camera 1 successfully
- [ ] Verify 30 FPS streaming performance
- [ ] Test stream controls (start/stop/fullscreen)
- [ ] Validate browser compatibility (Chrome, Firefox, Safari)
- [ ] Test network interruption recovery
- [ ] Load testing with multiple concurrent viewers

**Success Criteria:**
- [ ] Test Camera 1 streams reliably for 1+ hours
- [ ] Web interface displays video without artifacts
- [ ] Stream controls function correctly
- [ ] CPU usage remains below 50% during streaming

## Phase 2: Real-time Detection Pipeline (4-5 days)

### Objective
Integrate YOLO license plate detection with live video streams and provide real-time detection results via WebSocket.

### 2.1 YOLO Model Integration (Day 1-2)

#### Detection Service Implementation
```python
# backend/app/services/detection_service.py
class DetectionService:
    def __init__(self):
        self.yolo_model = self.load_yolo_model()
        self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
        self.confidence_threshold = 0.5
        
    def load_yolo_model(self):
        """Load YOLO model from train/models/pretrained/"""
        model_path = "train/models/pretrained/yolo11m_best.pt"
        return YOLO(model_path)
        
    async def process_frame(self, frame: np.ndarray) -> List[Detection]:
        """Process frame through detection pipeline"""
```

**Implementation Tasks:**
- [ ] Create DetectionService class
- [ ] Integrate existing YOLO models (yolo11m_best.pt)
- [ ] Add EasyOCR integration for text recognition
- [ ] Implement detection pipeline from documentation
- [ ] Add GPU acceleration support
- [ ] Create detection result data structures

### 2.2 Database Schema Extension (Day 2)

#### Detection Tables
```sql
-- Add to existing database schema
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER REFERENCES cameras(id),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    bbox_x1 INTEGER,
    bbox_y1 INTEGER,
    bbox_x2 INTEGER,
    bbox_y2 INTEGER,
    confidence REAL,
    ocr_confidence REAL,
    plate_text TEXT,
    processing_time_ms INTEGER,
    image_path TEXT,
    enhanced_image_path TEXT,
    quality_score REAL
);

CREATE TABLE stream_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER REFERENCES cameras(id),
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    total_frames INTEGER DEFAULT 0,
    total_detections INTEGER DEFAULT 0,
    avg_fps REAL,
    status TEXT DEFAULT 'active'
);

-- Indexes for performance
CREATE INDEX idx_detections_camera_timestamp 
ON detections(camera_id, timestamp);

CREATE INDEX idx_detections_plate_text 
ON detections(plate_text);
```

**Implementation Tasks:**
- [ ] Extend database models with detection tables
- [ ] Add database migration scripts
- [ ] Create detection CRUD operations
- [ ] Add image storage management
- [ ] Test database performance with detection data

### 2.3 WebSocket Real-time Streaming (Day 3-4)

#### WebSocket Implementation
```python
# backend/app/api/v1/endpoints/websockets.py
@router.websocket("/ws/stream/{camera_id}")
async def websocket_stream(websocket: WebSocket, camera_id: int):
    """WebSocket endpoint for real-time detection data"""
    await websocket.accept()
    
    # Get streaming service for camera
    streaming_service = get_streaming_service(camera_id)
    
    try:
        async for detection in streaming_service.get_detections():
            await websocket.send_json({
                "type": "detection",
                "timestamp": detection.timestamp.isoformat(),
                "detection": {
                    "bbox": detection.bbox,
                    "confidence": detection.confidence,
                    "plate_text": detection.plate_text,
                    "processing_time_ms": detection.processing_time_ms
                }
            })
    except WebSocketDisconnect:
        pass
```

**Implementation Tasks:**
- [ ] Create WebSocket streaming endpoints
- [ ] Integrate detection results broadcasting
- [ ] Add connection management for multiple clients
- [ ] Implement message queuing and rate limiting
- [ ] Add error handling and reconnection logic
- [ ] Test WebSocket performance and stability

### 2.4 Detection Integration Testing (Day 4-5)

**Test Scenarios:**
- [ ] Real-time detection on Test Camera 1 stream
- [ ] Verify YOLO model accuracy on live video
- [ ] Test EasyOCR text recognition performance
- [ ] Validate WebSocket data streaming
- [ ] Test detection storage and retrieval
- [ ] Performance testing under continuous operation

**Success Criteria:**
- [ ] Detection accuracy >85% on clear license plates
- [ ] Detection processing time <200ms per frame
- [ ] WebSocket latency <500ms end-to-end
- [ ] System stability during 4+ hour operation
- [ ] Detection data correctly stored in database

## Phase 3: Production Features (2-3 days)

### Objective
Add production-ready features including multi-camera support, monitoring, and performance optimization.

### 3.1 Multi-Camera Support (Day 1)

#### Stream Manager Enhancement
```python
# backend/app/services/stream_manager.py
class StreamManager:
    def __init__(self):
        self.active_streams = {}  # camera_id -> StreamingService
        self.detection_services = {}  # camera_id -> DetectionService
        self.websocket_connections = defaultdict(set)
        
    async def start_camera_stream(self, camera_id: int):
        """Start streaming for specific camera"""
        
    async def stop_camera_stream(self, camera_id: int):
        """Stop streaming for specific camera"""
        
    async def broadcast_detection(self, camera_id: int, detection: Detection):
        """Broadcast detection to all connected clients"""
```

**Implementation Tasks:**
- [ ] Create centralized StreamManager
- [ ] Support concurrent camera streaming
- [ ] Add resource allocation and load balancing
- [ ] Implement camera priority management
- [ ] Test multi-camera streaming performance

### 3.2 Health Monitoring and Analytics (Day 1-2)

#### System Health Service
```python
# backend/app/services/health_service.py
class HealthService:
    def __init__(self):
        self.metrics = defaultdict(list)
        
    async def collect_stream_metrics(self):
        """Collect performance metrics from active streams"""
        
    async def get_system_health(self) -> Dict:
        """Return current system health status"""
        
    async def check_camera_health(self, camera_id: int) -> bool:
        """Check individual camera health"""
```

**Implementation Tasks:**
- [ ] Create health monitoring service
- [ ] Add performance metrics collection
- [ ] Implement camera health checks
- [ ] Create system status dashboard endpoints
- [ ] Add alerting for system issues

### 3.3 Performance Optimization (Day 2-3)

#### Optimization Areas
1. **GPU Memory Management**
   - Efficient CUDA memory allocation
   - Batch processing for multiple cameras
   - Memory cleanup and garbage collection

2. **Network Optimization**
   - Adaptive streaming quality
   - Connection pooling for WebSockets
   - Bandwidth monitoring and adjustment

3. **Database Performance**
   - Query optimization with proper indexing
   - Batch insertion for detection data
   - Data retention and cleanup policies

**Implementation Tasks:**
- [ ] Implement GPU memory optimization
- [ ] Add adaptive streaming quality
- [ ] Optimize database queries and indexes
- [ ] Add data retention policies
- [ ] Performance testing and benchmarking

### 3.4 Production Deployment (Day 3)

#### Docker Configuration Updates
```dockerfile
# Add GPU support and OpenCV dependencies
FROM nvidia/cuda:11.8-runtime-ubuntu20.04

# Install OpenCV and AI dependencies
RUN apt-get update && apt-get install -y \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0

# Copy models and application
COPY train/models/pretrained/ /app/models/
COPY backend/ /app/
```

**Implementation Tasks:**
- [ ] Update Docker configuration for GPU support
- [ ] Add production environment variables
- [ ] Configure model paths and GPU settings
- [ ] Test production deployment
- [ ] Add monitoring and logging configuration

## Risk Assessment and Mitigation

### Technical Risks

#### High Priority Risks
1. **GPU Memory Limitations**
   - **Risk**: CUDA out of memory errors with multiple cameras
   - **Mitigation**: Implement dynamic batch sizing and memory monitoring
   - **Timeline Impact**: +1 day for optimization

2. **Camera Connection Stability**
   - **Risk**: IP camera disconnections affecting streaming
   - **Mitigation**: Robust reconnection logic and health monitoring
   - **Timeline Impact**: Already accounted for in Phase 1

3. **Detection Accuracy Variations**
   - **Risk**: YOLO model performance on different lighting/angles
   - **Mitigation**: Model validation and confidence thresholding
   - **Timeline Impact**: +0.5 days for tuning

#### Medium Priority Risks
1. **WebSocket Connection Scaling**
   - **Risk**: Performance degradation with many concurrent users
   - **Mitigation**: Connection pooling and rate limiting
   - **Timeline Impact**: +0.5 days

2. **Database Performance**
   - **Risk**: Slow queries with large detection datasets
   - **Mitigation**: Proper indexing and query optimization
   - **Timeline Impact**: Already accounted for in Phase 3

### Dependencies

#### External Dependencies
- **Hardware**: GPU availability for YOLO inference
- **Network**: Stable connection to Test Camera 1
- **Storage**: Sufficient disk space for detection images

#### Internal Dependencies
- **Camera Management**: Existing camera configuration system
- **Database**: Current SQLite database structure
- **Frontend**: Existing streaming UI components

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1** | 3-4 days | Basic video streaming from Test Camera 1 |
| **Phase 2** | 4-5 days | Real-time detection with WebSocket streaming |
| **Phase 3** | 2-3 days | Multi-camera support and production features |
| **Buffer** | 1-2 days | Testing, optimization, and documentation |

**Total Duration**: 10-14 days

## Success Metrics

### Phase 1 Success Criteria
- [ ] Test Camera 1 streaming at 30 FPS consistently
- [ ] Web interface displays video without interruption
- [ ] Stream controls functional (play/pause/fullscreen)
- [ ] System stable for 2+ hours continuous operation

### Phase 2 Success Criteria
- [ ] License plate detection accuracy >85%
- [ ] Detection processing time <200ms average
- [ ] WebSocket latency <500ms end-to-end
- [ ] Detection data stored correctly in database

### Phase 3 Success Criteria
- [ ] Support for up to 4 concurrent camera streams
- [ ] System health monitoring dashboard functional
- [ ] Performance optimized for production deployment
- [ ] Complete documentation and deployment guide

## Next Steps

1. **Environment Setup** (Prerequisites)
   - Install OpenCV and YOLO dependencies
   - Configure GPU support (if available)
   - Test connection to Test Camera 1

2. **Phase 1 Kickoff**
   - Create camera streaming service skeleton
   - Set up development database with test data
   - Begin OpenCV integration for IP camera capture

3. **Continuous Integration**
   - Set up automated testing for streaming endpoints
   - Configure performance monitoring
   - Establish code review process for AI components

This roadmap provides a structured approach to implementing the Stream feature with clear milestones, risk mitigation, and success criteria for each phase.