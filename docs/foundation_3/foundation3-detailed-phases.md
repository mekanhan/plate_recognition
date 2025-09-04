# Foundation 3 - Detailed Phase Implementation Guide

## Overview
This guide provides granular implementation details for each phase, eliminating assumptions and ensuring AI agents can execute tasks precisely.

## Phase 1: Foundation Stabilization (Week 1-2)

### 1.1 Database & Service Integration

#### Specific Tasks:

**Task 1.1.1: Database Service Consolidation**
```yaml
Current State:
  - recording_service uses hardcoded camera configurations
  - Database exists but is disconnected from recording service
  - Multiple service dependencies are not properly injected

Required Actions:
  1. Create database_service.py with methods:
     - get_all_cameras() -> List[CameraConfig]
     - add_camera(camera: CameraConfig) -> bool
     - update_camera(camera_id: str, updates: dict) -> bool
     - delete_camera(camera_id: str) -> bool
     - get_camera_status(camera_id: str) -> CameraStatus

  2. Modify recording_service.py:
     - Remove hardcoded camera list
     - Import DatabaseService
     - Initialize cameras from database on startup
     - Add database polling for camera changes (every 30 seconds)

  3. Create unified CameraConfig model:
     - id: str (UUID)
     - name: str
     - ip_address: str
     - username: str
     - password: str
     - rtsp_url: str (computed)
     - recording_enabled: bool
     - retention_days: int
     - created_at: datetime
     - updated_at: datetime
```

**Task 1.1.2: Database Migration Scripts**
```sql
-- migrations/001_camera_table.sql
CREATE TABLE IF NOT EXISTS cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    username VARCHAR(255),
    password VARCHAR(255),
    rtsp_port INTEGER DEFAULT 554,
    recording_enabled BOOLEAN DEFAULT true,
    retention_days INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- migrations/002_recording_status.sql
CREATE TABLE IF NOT EXISTS recording_status (
    camera_id UUID REFERENCES cameras(id),
    status VARCHAR(50) NOT NULL,
    ffmpeg_pid INTEGER,
    segments_created INTEGER DEFAULT 0,
    storage_used_mb BIGINT DEFAULT 0,
    last_segment_time TIMESTAMP,
    error_message TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (camera_id)
);
```

### 1.2 API Consolidation

#### Specific Tasks:

**Task 1.2.1: Create Unified API Namespace**
```python
# api/v3/__init__.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v3")

# Standard response format
class APIResponse:
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
        self.timestamp = datetime.utcnow()
```

**Task 1.2.2: Implement Comprehensive Error Handling**
```python
# api/v3/middleware.py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            error="Internal server error",
            request_id=request.headers.get("X-Request-ID")
        ).dict()
    )
```

**Task 1.2.3: Standardize Logging**
```python
# config/logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/surveillance.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    }
}
```

## Phase 2: Stream Management Core (Week 3-4)

### 2.1 Stream Ingestion Service

#### Specific Tasks:

**Task 2.1.1: Connection Pool Implementation**
```python
# stream/connection_pool.py
class StreamConnectionPool:
    def __init__(self, max_connections: int = 100):
        self.pool = {}
        self.max_connections = max_connections
        self.lock = asyncio.Lock()
    
    async def get_connection(self, camera_id: str) -> StreamConnection:
        async with self.lock:
            if camera_id not in self.pool:
                self.pool[camera_id] = await self._create_connection(camera_id)
            return self.pool[camera_id]
    
    async def _create_connection(self, camera_id: str) -> StreamConnection:
        # Implementation with retry logic
        pass
```

**Task 2.1.2: Retry Logic with Exponential Backoff**
```python
# stream/retry_handler.py
class RetryHandler:
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
```

**Task 2.1.3: Stream Health Monitoring**
```python
# stream/health_monitor.py
class StreamHealthMonitor:
    def __init__(self):
        self.metrics = {}
    
    async def check_stream_health(self, camera_id: str) -> HealthStatus:
        # Check: connection alive, frames received, latency
        return HealthStatus(
            connected=True,
            fps=current_fps,
            latency_ms=latency,
            last_frame_time=timestamp,
            error_count=errors
        )
```

### 2.2 GPU-Accelerated Processing

#### Specific Tasks:

**Task 2.2.1: Docker GPU Setup**
```dockerfile
# Dockerfile.gpu
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Install FFmpeg with NVIDIA support
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nvidia-cuda-toolkit

# Set NVIDIA environment variables
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility,video

# docker-compose.gpu.yml
services:
  gpu_processor:
    build:
      context: .
      dockerfile: Dockerfile.gpu
    runtime: nvidia
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Task 2.2.2: FFmpeg NVENC/NVDEC Implementation**
```python
# gpu/ffmpeg_gpu.py
class GPUFFmpegProcessor:
    def __init__(self):
        self.gpu_available = self._check_gpu()
    
    def get_decode_args(self) -> List[str]:
        if self.gpu_available:
            return ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']
        return []
    
    def get_encode_args(self) -> List[str]:
        if self.gpu_available:
            return ['-c:v', 'h264_nvenc', '-preset', 'p4', '-tune', 'hq']
        return ['-c:v', 'libx264', '-preset', 'fast']
```

## Phase 3: AI Pipeline (Week 5-6)

### 3.1 Real-time Detection Framework

#### Specific Tasks:

**Task 3.1.1: YOLOv8 TensorRT Integration**
```python
# ai/yolo_tensorrt.py
class YOLOv8TensorRT:
    def __init__(self, model_path: str):
        self.model = self._load_tensorrt_model(model_path)
        self.input_shape = (640, 640)
        self.batch_size = 4
    
    def _load_tensorrt_model(self, path: str):
        # TensorRT model loading
        pass
    
    def detect_batch(self, frames: List[np.ndarray]) -> List[Detection]:
        # Batch processing implementation
        preprocessed = self._preprocess_batch(frames)
        results = self.model.predict(preprocessed)
        return self._postprocess_results(results)
```

**Task 3.1.2: Detection Queue System**
```python
# ai/detection_queue.py
class DetectionQueue:
    def __init__(self, max_queue_size: int = 100):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.processing = False
    
    async def add_frame(self, camera_id: str, frame: np.ndarray):
        await self.queue.put({
            'camera_id': camera_id,
            'frame': frame,
            'timestamp': time.time()
        })
    
    async def process_queue(self):
        batch = []
        while len(batch) < self.batch_size:
            try:
                item = await asyncio.wait_for(
                    self.queue.get(), 
                    timeout=0.1
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break
        
        if batch:
            await self._process_batch(batch)
```

## Prompt Engineering Templates

### For AI Agent Implementation

#### Template 1: Service Implementation
```markdown
Role: Senior Backend Developer with 10 years experience in Python, FastAPI, and video processing systems.

Context: Building a production video surveillance system with the following architecture:
- FastAPI backend with PostgreSQL database
- FFmpeg-based video recording
- GPU-accelerated AI processing
- Multiple camera support with real-time monitoring

Current State: [Describe specific phase and component]

Task: Implement [specific component] following these exact specifications:
[Copy relevant task details from above]

Constraints:
- Must handle network interruptions gracefully
- Support concurrent processing of 4+ cameras
- Maintain <500ms processing latency
- Use proper error handling and logging

Output Format:
1. Complete implementation code with detailed comments
2. Unit tests for critical functions
3. Integration points with other services
4. Error handling strategies
5. Performance optimization notes
```

#### Template 2: Debugging and Troubleshooting
```markdown
Role: DevOps Engineer specializing in video streaming systems and GPU optimization.

Context: Surveillance system experiencing [specific issue] in [component].
System specs: RTX 3080, 32GB RAM, Ubuntu 22.04, Docker containers.
Current symptoms: [detailed symptoms]

Available logs:
[Include relevant log snippets]

Task: Diagnose and fix the issue with minimal downtime.

Constraints:
- Cannot interrupt ongoing recordings
- Must maintain data integrity
- Solution should be reversible

Output Format:
1. Root cause analysis
2. Step-by-step fix procedure
3. Validation tests
4. Monitoring recommendations
5. Prevention strategies
```

#### Template 3: Code Review and Optimization
```markdown
Role: Senior Software Architect with expertise in high-performance video systems.

Context: Review and optimize [component] for production deployment.
Performance requirements:
- Handle 10+ cameras concurrently
- Process 30 FPS per camera
- <100ms detection latency
- 99.9% uptime

Current implementation:
[Include code snippet]

Task: Review code for performance, reliability, and maintainability.

Focus areas:
- Memory leaks
- GPU utilization
- Error recovery
- Scalability bottlenecks

Output Format:
1. Critical issues (must fix)
2. Performance improvements
3. Code quality suggestions
4. Refactoring recommendations
5. Benchmark comparisons
```

## Gap Prevention Strategies

### 1. Explicit State Definitions
Always define:
- Current state (what exists)
- Target state (what should exist)
- Exact transformation steps
- Validation criteria

### 2. Zero Assumption Policy
- Specify exact file paths
- Define all imports
- Include version numbers
- Document all dependencies

### 3. Incremental Validation
After each sub-task:
- Run specific tests
- Check integration points
- Verify performance metrics
- Document completion

### 4. Error Handling Matrix
For each component, define:
- Expected errors
- Recovery strategies
- Fallback behaviors
- Monitoring alerts

### 5. Integration Checklists
Between phases:
- [ ] All services communicate
- [ ] Data flows correctly
- [ ] Error propagation works
- [ ] Monitoring is active
- [ ] Documentation updated

## Implementation Order Summary

1. **Week 1-2**: Foundation (Database + API)
   - Focus: Stability and integration
   - Validation: All services use unified database

2. **Week 3-4**: Streaming Core
   - Focus: Reliable video ingestion
   - Validation: 4+ cameras streaming stable

3. **Week 5-6**: AI Pipeline
   - Focus: Real-time processing
   - Validation: <500ms detection latency

4. **Week 7-8**: Storage & Performance
   - Focus: Scalability and optimization
   - Validation: 30-day retention working

5. **Week 9-10**: Reliability
   - Focus: Production hardening
   - Validation: Auto-recovery functional

6. **Week 11-12**: Advanced Features
   - Focus: Differentiation
   - Validation: Business value metrics

7. **Week 13-14**: Frontend Polish
   - Focus: User experience
   - Validation: 10-minute setup achieved

8. **Week 15-16**: Production Deployment
   - Focus: Single-command deployment
   - Validation: Full system operational
