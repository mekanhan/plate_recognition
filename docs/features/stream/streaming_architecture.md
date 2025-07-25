# Streaming Architecture

**Date:** 2025-01-24  
**Version:** 1.0  
**Component:** Stream Feature Technical Architecture

## System Architecture Overview

The streaming architecture implements a real-time video processing pipeline that integrates camera feeds, AI detection, and web-based monitoring into a cohesive system.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IP Cameras    │    │   Camera Capture │    │  Detection      │
│                 │────│   Service        │────│  Pipeline       │
│ • Test Camera 1 │    │                  │    │                 │
│ • USB Cameras   │    │ • OpenCV Stream  │    │ • YOLO Models   │
│ • CSI Cameras   │    │ • Connection Mgmt│    │ • EasyOCR       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                     ┌──────────────────┐
                     │   Stream Manager │
                     │                  │
                     │ • Frame Buffer   │
                     │ • Quality Control│
                     │ • Multi-threading│
                     └──────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
    ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
    │   HTTP Stream   │  │   WebSocket      │  │   Database      │
    │   Endpoint      │  │   Real-time      │  │   Storage       │
    │                 │  │   Data           │  │                 │
    │ • /stream/video │  │ • /ws/stream     │  │ • Detections    │
    │ • MJPEG Output  │  │ • Detection Data │  │ • Images        │
    └─────────────────┘  └──────────────────┘  └─────────────────┘
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                     ┌──────────────────┐
                     │   Web Frontend   │
                     │                  │
                     │ • Live Video     │
                     │ • Detection UI   │
                     │ • Controls       │
                     └──────────────────┘
```

## Core Components

### 1. Camera Capture Service

**Responsibility**: Interface with various camera types and manage video stream acquisition.

#### Technical Implementation
```python
class CameraService:
    def __init__(self, camera_config: CameraConfig):
        self.camera_config = camera_config
        self.capture = None
        self.is_streaming = False
        self.frame_queue = asyncio.Queue(maxsize=30)
    
    async def connect(self) -> bool:
        """Establish connection to camera"""
        
    async def capture_frames(self) -> AsyncGenerator[np.ndarray, None]:
        """Continuous frame capture with error handling"""
        
    async def disconnect(self):
        """Clean camera connection shutdown"""
```

#### Camera Type Support
- **IP Cameras**: HTTP/RTSP streams via OpenCV VideoCapture
- **USB Cameras**: Direct device access via OpenCV (device ID)
- **CSI Cameras**: Jetson Nano/Raspberry Pi camera module support

#### Connection Management
- **Health Monitoring**: Continuous connection status validation
- **Auto-reconnect**: Automatic recovery from connection failures
- **Quality Adaptation**: Dynamic resolution/framerate adjustment
- **Error Handling**: Graceful degradation and user notification

### 2. Detection Pipeline

**Responsibility**: Process video frames through YOLO detection and EasyOCR text recognition.

#### Architecture Flow
```
Video Frame → Preprocessing → YOLO Detection → ROI Extraction → EasyOCR → Results
     │              │              │               │              │         │
   640x480      Resize/Norm    Bounding Boxes   Crop Plates   Text Extract  Database
```

#### Technical Implementation
```python
class DetectionPipeline:
    def __init__(self):
        self.yolo_model = self.load_yolo_model()
        self.ocr_reader = easyocr.Reader(['en'])
        self.confidence_threshold = 0.5
    
    async def process_frame(self, frame: np.ndarray) -> List[Detection]:
        """Process single frame through detection pipeline"""
        
    def detect_plates(self, frame: np.ndarray) -> List[BoundingBox]:
        """YOLO license plate detection"""
        
    def extract_text(self, plate_image: np.ndarray) -> str:
        """EasyOCR text recognition"""
```

#### Model Management
- **YOLO Loading**: Efficient model initialization and caching
- **GPU Acceleration**: CUDA support for inference optimization
- **Model Switching**: Runtime model selection (yolo11m vs yolov8m)
- **Batch Processing**: Multiple frame processing for efficiency

### 3. Stream Manager

**Responsibility**: Coordinate video streaming, detection processing, and data distribution.

#### Core Functions
- **Frame Buffering**: Manage video frame queues and timing
- **Processing Coordination**: Balance detection load with streaming performance
- **Multi-threading**: Separate threads for capture, processing, and streaming
- **Quality Control**: Adaptive frame rate and resolution management

#### Technical Implementation
```python
class StreamManager:
    def __init__(self, camera_service: CameraService, detection_pipeline: DetectionPipeline):
        self.camera_service = camera_service
        self.detection_pipeline = detection_pipeline
        self.active_connections = set()
        self.frame_buffer = FrameBuffer(maxsize=60)
    
    async def start_streaming(self):
        """Initialize all streaming components"""
        
    async def process_stream(self):
        """Main processing loop"""
        
    async def broadcast_detection(self, detection: Detection):
        """Send detection data to connected clients"""
```

### 4. HTTP Streaming Endpoint

**Responsibility**: Serve live video feeds via HTTP for web browser consumption.

#### Endpoint Specification
- **URL**: `/stream/video/{camera_id}`
- **Method**: `GET`
- **Content-Type**: `multipart/x-mixed-replace; boundary=frame`
- **Response**: MJPEG stream

#### Technical Implementation
```python
@app.get("/stream/video/{camera_id}")
async def stream_video(camera_id: int):
    """Stream live video feed as MJPEG"""
    stream_manager = get_stream_manager(camera_id)
    
    async def generate_frames():
        async for frame in stream_manager.get_frames():
            yield frame_to_jpeg(frame)
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
```

### 5. WebSocket Real-time Data

**Responsibility**: Push detection results and metadata to connected web clients.

#### WebSocket Endpoints
- **Connection**: `/ws/stream/{camera_id}`
- **Detection Data**: Real-time detection results
- **System Status**: Stream health and performance metrics
- **Control Commands**: Start/stop streaming, parameter adjustment

#### Message Format
```json
{
  "type": "detection",
  "camera_id": 3,
  "timestamp": "2025-01-24T10:30:45.123Z",
  "detection": {
    "bbox": [100, 50, 200, 120],
    "confidence": 0.87,
    "plate_text": "ABC123",
    "processing_time_ms": 150
  }
}
```

### 6. Database Storage

**Responsibility**: Persist detection results, images, and streaming metadata.

#### Schema Design
```sql
-- Detection results table
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER REFERENCES cameras(id),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    bbox_x1 INTEGER,
    bbox_y1 INTEGER, 
    bbox_x2 INTEGER,
    bbox_y2 INTEGER,
    confidence REAL,
    plate_text TEXT,
    processing_time_ms INTEGER,
    image_path TEXT,
    enhanced_image_path TEXT
);

-- Streaming sessions table
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
```

## Data Flow Architecture

### 1. Video Acquisition Flow
```
Camera → OpenCV Capture → Frame Queue → Stream Manager → HTTP Response
    │
    └─→ Detection Pipeline → Database Storage → WebSocket Broadcast
```

### 2. Detection Processing Flow
```
Video Frame
    │
    ├─→ YOLO Detection ─→ Bounding Boxes
    │                          │
    └─→ ROI Extraction ────────┘
                               │
                    ┌─→ EasyOCR Recognition
                    │           │
                    └─→ Text Confidence Check
                               │
                    ┌─→ Database Storage
                    │           │  
                    └─→ WebSocket Notification
```

### 3. Client Communication Flow
```
Web Browser
    │
    ├─→ HTTP GET /stream/video → MJPEG Stream
    │
    └─→ WebSocket /ws/stream → Real-time Detection Data
                                     │
                              JSON Messages
                                     │
                         ┌─→ Detection Results
                         │
                         ├─→ System Status
                         │
                         └─→ Performance Metrics
```

## Performance Optimization

### 1. Video Processing Optimization
- **GPU Acceleration**: CUDA support for YOLO inference
- **Multi-threading**: Separate threads for capture, processing, streaming
- **Frame Skipping**: Intelligent frame selection for detection processing
- **Memory Management**: Efficient frame buffer management and cleanup

### 2. Network Optimization
- **Adaptive Streaming**: Dynamic quality adjustment based on network conditions
- **Connection Pooling**: Efficient WebSocket connection management
- **Compression**: JPEG compression optimization for HTTP streaming
- **Bandwidth Monitoring**: Real-time network usage tracking

### 3. Database Optimization
- **Indexing**: Optimized indexes for detection queries
- **Batch Inserts**: Efficient bulk detection storage
- **Data Retention**: Automated cleanup of old detection data
- **Connection Pooling**: Async database connection management

## Scalability Considerations

### 1. Multi-Camera Support
- **Camera Pool**: Manage multiple concurrent camera streams
- **Load Balancing**: Distribute processing load across available resources
- **Resource Allocation**: Dynamic CPU/GPU resource allocation per camera
- **Priority Management**: Prioritize high-importance camera streams

### 2. Concurrent Users
- **WebSocket Scaling**: Support multiple simultaneous web clients
- **Resource Sharing**: Efficient sharing of detection results across clients
- **Connection Management**: Graceful handling of client connect/disconnect
- **Rate Limiting**: Prevent resource exhaustion from excessive connections

### 3. Hardware Requirements
- **Minimum**: 4GB RAM, dual-core CPU, 1GB storage
- **Recommended**: 8GB RAM, quad-core CPU, GPU acceleration, 10GB storage
- **Production**: 16GB RAM, 8-core CPU, dedicated GPU, SSD storage

## Security Architecture

### 1. Authentication
- **JWT Tokens**: Secure WebSocket authentication
- **Session Management**: Secure session handling for streaming clients
- **Rate Limiting**: Prevent abuse and DoS attacks
- **IP Filtering**: Optional IP-based access control

### 2. Data Protection
- **Stream Encryption**: Optional SSL/TLS for stream data
- **Database Security**: Encrypted storage of sensitive detection data
- **Access Control**: Role-based access to streaming features
- **Audit Logging**: Track streaming access and detection events

## Error Handling and Recovery

### 1. Camera Connection Failures
- **Auto-reconnect**: Automatic retry with exponential backoff
- **Fallback Modes**: Graceful degradation when cameras unavailable
- **User Notification**: Clear error messaging in web interface
- **Health Monitoring**: Continuous connection status tracking

### 2. Processing Failures
- **Model Loading**: Graceful handling of YOLO model load failures
- **Detection Errors**: Continue streaming even if detection fails
- **Memory Management**: Prevent memory leaks from processing errors
- **Performance Degradation**: Adaptive quality reduction under load

### 3. System Recovery
- **Graceful Shutdown**: Clean resource cleanup on system stop
- **State Persistence**: Resume streaming sessions after restart
- **Data Integrity**: Ensure detection data consistency during failures
- **Monitoring Integration**: Integration with system monitoring tools

This architecture provides a robust, scalable foundation for real-time license plate recognition streaming while maintaining high performance and reliability standards.