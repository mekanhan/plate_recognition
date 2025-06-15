# Headless Architecture Documentation

## Overview

The V1 License Plate Recognition system has been enhanced with a comprehensive headless architecture that enables autonomous operation without web UI dependency. This makes the system suitable for:

- **Jetson Nano and embedded deployments**
- **Microservice architectures**
- **Cloud-native deployments**
- **Edge computing environments**
- **Platform integration scenarios**

## Architecture Components

### 1. BackgroundStreamManager

**Purpose**: Autonomous frame processing and detection pipeline management

**Key Features**:
- Continuous frame capture and processing
- Configurable frame skipping for performance optimization
- Detection queue management with overflow protection
- Health monitoring and automatic error recovery
- Performance metrics and statistics tracking

**Configuration Options**:
```python
{
    "frame_skip": 5,                    # Process every Nth frame
    "processing_interval": 0.033,       # Target frame rate (30 FPS)
    "max_queue_size": 100,             # Detection queue limit
    "error_recovery_delay": 5.0,       # Error recovery timeout
    "health_check_interval": 30.0,     # Health monitoring frequency
    "enable_performance_metrics": True  # Performance tracking
}
```

### 2. OutputChannelManager

**Purpose**: Multiple output channel management for microservice integration

**Supported Channels**:
- **Storage**: Local database and file storage
- **API**: Buffer for REST API access
- **WebSocket**: Real-time broadcasting
- **Webhook**: HTTP notifications to external services
- **File**: Export to JSON/CSV formats

**Features**:
- Parallel output to multiple channels
- Automatic retry for webhook failures
- Configurable buffer sizes and timeouts
- Batch processing support
- Dead connection cleanup

### 3. Configuration System

**Purpose**: Environment-driven deployment modes

**Deployment Modes**:
- `headless`: Background processing only, no web UI
- `web_ui`: Traditional web interface with optional background processing
- `hybrid`: Both web UI and background processing enabled

**Key Settings**:
```env
DEPLOYMENT_MODE=headless
ENABLE_BACKGROUND_PROCESSING=true
BACKGROUND_FRAME_SKIP=5
BACKGROUND_PROCESSING_INTERVAL=0.5
ENABLE_WEBHOOK_OUTPUT=true
WEBHOOK_URL=http://external-service.com/api
```

## API Endpoints

### Health and Status Monitoring

```http
GET /api/headless/health
```
Returns comprehensive system health including background processing status, output channel statistics, and recent detection activity.

```http
GET /api/headless/status
```
Returns detailed background processing metrics and configuration.

### Processing Control

```http
POST /api/headless/control/start
POST /api/headless/control/stop
POST /api/headless/control/pause
POST /api/headless/control/resume
```
Complete lifecycle management for background processing.

### Detection Access

```http
GET /api/headless/detections/recent?limit=50
```
Retrieve recent detection results from the API buffer.

```http
DELETE /api/headless/detections/clear
```
Clear the detection buffer.

### Metrics and Configuration

```http
GET /api/headless/metrics
```
Detailed performance metrics for monitoring and analytics.

```http
PUT /api/headless/config
```
Runtime configuration updates.

```http
GET /api/headless/info
```
System information and capability discovery.

## Deployment Scenarios

### 1. Jetson Nano Headless Deployment

**Configuration**:
```env
DEPLOYMENT_MODE=headless
ENABLE_WEB_UI=false
BACKGROUND_FRAME_SKIP=10
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
MODEL_DEVICE=cuda
ENABLE_GPU_ACCELERATION=true
MAX_CONCURRENT_DETECTIONS=2
```

**Startup**:
```bash
# Set environment variables
export DEPLOYMENT_MODE=headless
export ENABLE_BACKGROUND_PROCESSING=true

# Start service
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Health check
curl http://localhost:8001/api/headless/health
```

### 2. Docker Microservice

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Expose port
EXPOSE 8001

# Headless startup
ENV DEPLOYMENT_MODE=headless
ENV ENABLE_BACKGROUND_PROCESSING=true

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 3. Kubernetes Deployment

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lpr-headless
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lpr-headless
  template:
    metadata:
      labels:
        app: lpr-headless
    spec:
      containers:
      - name: lpr
        image: lpr-system:latest
        ports:
        - containerPort: 8001
        env:
        - name: DEPLOYMENT_MODE
          value: "headless"
        - name: ENABLE_BACKGROUND_PROCESSING
          value: "true"
        - name: ENABLE_WEBHOOK_OUTPUT
          value: "true"
        - name: WEBHOOK_URL
          value: "http://analytics-service/api/detections"
        livenessProbe:
          httpGet:
            path: /api/headless/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/headless/status
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 4. Platform Integration

**External Service Integration**:
```python
# External service receiving webhook notifications
@app.post("/api/detections")
async def receive_detection(detection_data: dict):
    plate_text = detection_data["detection"]["plate_text"]
    confidence = detection_data["detection"]["confidence"]
    timestamp = detection_data["timestamp"]
    
    # Process detection in external system
    await process_license_plate(plate_text, confidence, timestamp)
    
    return {"status": "received"}
```

**API Polling Integration**:
```python
# External service polling for detections
async def poll_lpr_service():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://lpr-service:8001/api/headless/detections/recent") as response:
            data = await response.json()
            
            for detection in data["detections"]:
                await process_detection(detection)
```

## Performance Optimization

### Resource Management

**CPU Optimization**:
- Configurable frame skipping (`BACKGROUND_FRAME_SKIP`)
- Adaptive processing intervals
- Efficient queue management

**Memory Optimization**:
- Bounded detection queues
- Automatic buffer cleanup
- Configurable buffer sizes

**GPU Acceleration**:
- CUDA support for model inference
- Automatic device selection
- Memory pool management

### Monitoring and Alerting

**Health Checks**:
```bash
# Basic health check
curl http://localhost:8001/api/headless/health

# Detailed metrics
curl http://localhost:8001/api/headless/metrics

# Processing status
curl http://localhost:8001/api/headless/status
```

**Key Metrics**:
- Frames per second
- Detection rate
- Processing time
- Error count
- Queue size
- Memory usage

## Troubleshooting

### Common Issues

1. **Background processing not starting**:
   - Check `ENABLE_BACKGROUND_PROCESSING=true`
   - Verify camera access permissions
   - Check model file availability

2. **High memory usage**:
   - Reduce `BACKGROUND_MAX_QUEUE_SIZE`
   - Increase `BACKGROUND_FRAME_SKIP`
   - Enable batch processing

3. **Webhook failures**:
   - Check webhook URL accessibility
   - Verify timeout settings
   - Monitor retry counts

### Debug Commands

```bash
# Check system health
curl http://localhost:8001/api/headless/health

# Get processing status
curl http://localhost:8001/api/headless/status

# Pause processing for debugging
curl -X POST http://localhost:8001/api/headless/control/pause

# Resume processing
curl -X POST http://localhost:8001/api/headless/control/resume

# Get recent detections
curl http://localhost:8001/api/headless/detections/recent?limit=10
```

## Migration from Web-Only Mode

### Step 1: Update Configuration
```bash
# Copy example configuration
cp .env.headless.example .env

# Edit configuration
nano .env
```

### Step 2: Test Headless Mode
```bash
# Start in headless mode
DEPLOYMENT_MODE=headless uvicorn app.main:app --host 0.0.0.0 --port 8001

# Verify API access
curl http://localhost:8001/api/headless/info
```

### Step 3: Production Deployment
```bash
# Production startup with environment file
uvicorn app.main:app --host 0.0.0.0 --port 8001 --env-file .env
```

## Future Enhancements

### Planned Features
- Message queue integration (RabbitMQ, Kafka)
- Advanced analytics and ML insights
- Multi-camera support
- Edge AI optimizations
- Cloud storage integration

### Extension Points
- Custom output channel implementations
- External model integration
- Advanced filtering and validation
- Real-time streaming protocols

This headless architecture transforms the V1 system into a production-ready, microservice-compatible solution suitable for any deployment scenario while maintaining full backward compatibility with existing web UI functionality.