# Backend Modernization & Architecture Implementation - Design

## Overview

This design document outlines the comprehensive backend architecture for the LPR System, implementing a modern microservices architecture based on Domain-Driven Design (DDD) principles and Clean Architecture patterns. The system will transform from a minimal FastAPI structure to a robust, scalable, enterprise-grade backend capable of handling real-time video processing, license plate detection, and multi-tenant operations.

## Architecture

### High-Level Architecture

The system follows a microservices architecture with the following key principles:

- **Domain-Driven Design (DDD)**: Clear bounded contexts for each business domain
- **Hexagonal Architecture**: Clean separation between business logic and infrastructure
- **Event-Driven Architecture**: Asynchronous communication between services
- **Polyglot Persistence**: Different databases optimized for specific use cases
- **API-First Design**: RESTful APIs with comprehensive OpenAPI documentation

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Web Browser  │  Mobile App  │  Desktop App  │  Smart TV  │  API Consumer  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOAD BALANCER (Nginx)                            │
│                        SSL Termination & Routing                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API GATEWAY LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Authentication  │  Rate Limiting  │  Request Routing  │  Circuit Breaker  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MICROSERVICES LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Camera Mgmt  │  Video Proc  │  Detection  │  Analytics  │  User Mgmt  │   │
│   Service     │   Service    │   Service   │   Service   │   Service   │...│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ PostgreSQL │   Redis    │  MongoDB   │ File Storage │ InfluxDB │ ElasticSearch│
│(Relational)│  (Cache)   │(Documents) │   (Videos)   │(Metrics) │   (Logs)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Bounded Contexts

Based on DDD principles, the system is organized into the following bounded contexts:

1. **Camera Management Context**: Camera configuration, health monitoring, ONVIF discovery
2. **Video Processing Context**: Stream transcoding, HLS generation, recording management
3. **Detection Context**: License plate detection, OCR processing, result storage
4. **Analytics Context**: Data analysis, reporting, pattern recognition
5. **User Management Context**: Authentication, authorization, user profiles
6. **Notification Context**: Alerts, notifications, communication channels

## Components and Interfaces

### 1. Camera Management Service

#### Domain Layer
```python
# Domain Entities
class Camera:
    - id: CameraId
    - name: str
    - ip_address: IPAddress
    - location: str
    - status: CameraStatus
    - configuration: CameraConfiguration
    - health_metrics: HealthMetrics
    
    + configure(config: CameraConfiguration)
    + activate()
    + deactivate()
    + update_health_metrics(metrics: HealthMetrics)

# Value Objects
class CameraConfiguration:
    - stream_url: str
    - resolution: Resolution
    - frame_rate: int
    - credentials: Credentials
    
class HealthMetrics:
    - connection_status: ConnectionStatus
    - response_time: int
    - last_seen: datetime
    - error_count: int
```

#### Application Layer
```python
# Use Cases
class CreateCameraUseCase:
    + execute(command: CreateCameraCommand) -> Camera

class ActivateCameraUseCase:
    + execute(camera_id: str) -> Camera

class MonitorCameraHealthUseCase:
    + execute() -> List[HealthStatus]

# Application Services
class CameraApplicationService:
    + create_camera(request: CreateCameraRequest) -> CameraResponse
    + update_camera(id: str, request: UpdateCameraRequest) -> CameraResponse
    + get_camera(id: str) -> CameraResponse
    + list_cameras(filters: CameraFilters) -> CameraListResponse
```

#### Infrastructure Layer
```python
# Repository Implementation
class SQLAlchemyCameraRepository(CameraRepository):
    + save(camera: Camera)
    + find_by_id(id: str) -> Camera
    + find_by_ip_address(ip: str) -> Camera
    + find_all(filters: CameraFilters) -> List[Camera]

# External Services
class ONVIFDiscoveryService:
    + discover_cameras(network_range: str) -> List[CameraInfo]
    + get_camera_profiles(camera: Camera) -> List[Profile]
```

### 2. Video Processing Service

#### Core Components
```python
# FFmpeg Process Manager
class FFmpegProcessManager:
    + start_transcoding(camera: Camera, output_config: OutputConfig)
    + stop_transcoding(camera_id: str)
    + get_process_status(camera_id: str) -> ProcessStatus
    + restart_process(camera_id: str)

# HLS Stream Manager
class HLSStreamManager:
    + create_stream(camera_id: str, quality_levels: List[QualityLevel])
    + update_playlist(camera_id: str, segments: List[Segment])
    + cleanup_old_segments(retention_policy: RetentionPolicy)

# Quality Controller
class AdaptiveBitrateController:
    + adjust_quality(camera_id: str, network_conditions: NetworkConditions)
    + get_optimal_bitrate(resolution: Resolution, frame_rate: int) -> int
```

### 3. Detection Service

#### AI/ML Components
```python
# License Plate Detection
class YOLODetector:
    + detect_plates(image: np.ndarray) -> List[Detection]
    + load_model(model_path: str)
    + preprocess_image(image: np.ndarray) -> np.ndarray

# OCR Processing
class OCRProcessor:
    + extract_text(plate_image: np.ndarray) -> OCRResult
    + enhance_image(image: np.ndarray) -> np.ndarray
    + validate_plate_format(text: str, country: str) -> bool

# Detection Pipeline
class DetectionPipeline:
    + process_frame(frame: VideoFrame) -> List[PlateDetection]
    + batch_process(frames: List[VideoFrame]) -> List[PlateDetection]
```

### 4. Analytics Service

#### Analytics Engine
```python
# Data Aggregation
class AnalyticsAggregator:
    + aggregate_detections(time_range: TimeRange) -> AggregatedData
    + calculate_traffic_patterns(location: str) -> TrafficPattern
    + generate_reports(report_type: ReportType) -> Report

# Pattern Recognition
class PatternAnalyzer:
    + identify_frequent_vehicles(time_range: TimeRange) -> List[Vehicle]
    + detect_anomalies(baseline: Baseline, current: CurrentData) -> List[Anomaly]
    + predict_traffic_trends(historical_data: HistoricalData) -> Prediction
```

### 5. API Gateway

#### Gateway Components
```python
# Request Router
class APIGateway:
    + route_request(request: HTTPRequest) -> HTTPResponse
    + authenticate_request(request: HTTPRequest) -> AuthResult
    + apply_rate_limiting(user_id: str, endpoint: str) -> bool
    + log_request(request: HTTPRequest, response: HTTPResponse)

# Circuit Breaker
class CircuitBreaker:
    + call_service(service_name: str, request: Request) -> Response
    + handle_failure(service_name: str, error: Exception)
    + get_service_health(service_name: str) -> HealthStatus
```

## Data Models

### PostgreSQL Schema (Transactional Data)

```sql
-- Cameras table
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    ip_address INET NOT NULL UNIQUE,
    location VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    configuration JSONB,
    health_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    roles TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System configuration
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### MongoDB Schema (Document Data)

```javascript
// Detection results collection
{
  _id: ObjectId,
  camera_id: String,
  timestamp: Date,
  image_data: {
    original_url: String,
    processed_url: String,
    thumbnail_url: String
  },
  license_plates: [{
    text: String,
    confidence: Number,
    bounding_box: {
      x: Number, y: Number,
      width: Number, height: Number
    },
    ocr_confidence: Number
  }],
  metadata: {
    processing_time: Number,
    model_version: String,
    frame_number: Number
  }
}

// Analytics data collection
{
  _id: ObjectId,
  type: String, // "traffic_count", "vehicle_frequency", etc.
  location: String,
  time_period: {
    start: Date,
    end: Date
  },
  data: Object, // Flexible analytics data
  created_at: Date
}
```

### Redis Schema (Cache & Sessions)

```
# Session storage
session:{user_id} -> {
  "user_id": "uuid",
  "username": "string",
  "roles": ["admin", "operator"],
  "expires_at": "timestamp"
}

# Camera health cache
camera:health:{camera_id} -> {
  "status": "active|inactive|error",
  "last_seen": "timestamp",
  "response_time": 150,
  "error_count": 0
}

# Detection cache (recent detections)
detections:recent:{camera_id} -> [
  {
    "plate": "ABC123",
    "confidence": 0.95,
    "timestamp": "2025-01-09T10:30:00Z"
  }
]
```

## Error Handling

### Error Classification

1. **Domain Errors**: Business rule violations, validation errors
2. **Infrastructure Errors**: Database connection failures, external service errors
3. **Application Errors**: Use case execution failures, authorization errors
4. **System Errors**: Unexpected exceptions, resource exhaustion

### Error Response Format

```python
class ErrorResponse:
    error: ErrorDetail
    timestamp: datetime
    request_id: str
    trace_id: str  # For distributed tracing

class ErrorDetail:
    code: str
    message: str
    details: Optional[List[FieldError]]
    
class FieldError:
    field: str
    message: str
    value: Optional[Any]
```

### Global Exception Handling

```python
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.error_code,
                message=str(exc)
            ),
            request_id=request.headers.get("X-Request-ID"),
            trace_id=request.headers.get("X-Trace-ID")
        ).dict()
    )
```

## Testing Strategy

### Testing Pyramid

1. **Unit Tests (70%)**
   - Domain entity tests
   - Use case tests
   - Service tests
   - Utility function tests

2. **Integration Tests (20%)**
   - Repository tests with real database
   - External service integration tests
   - API endpoint tests

3. **End-to-End Tests (10%)**
   - Complete user workflow tests
   - Cross-service integration tests
   - Performance tests

### Test Implementation

```python
# Unit Test Example
class TestCameraEntity:
    def test_camera_activation_success(self):
        camera = Camera.create(name="Test Camera", ip="192.168.1.100")
        camera.configure(valid_configuration)
        
        camera.activate()
        
        assert camera.status == CameraStatus.ACTIVE
        assert len(camera.domain_events) == 1
        assert isinstance(camera.domain_events[0], CameraActivatedEvent)

# Integration Test Example
class TestCameraRepository:
    async def test_save_and_retrieve_camera(self, db_session):
        repository = SQLAlchemyCameraRepository(db_session)
        camera = Camera.create(name="Test Camera", ip="192.168.1.100")
        
        await repository.save(camera)
        retrieved = await repository.find_by_id(camera.id)
        
        assert retrieved.name == camera.name
        assert retrieved.ip_address == camera.ip_address
```

### Performance Testing

```python
# Load Testing Configuration
class LoadTestConfig:
    concurrent_users: int = 100
    test_duration: int = 300  # 5 minutes
    ramp_up_time: int = 60    # 1 minute
    
    endpoints_to_test = [
        {"path": "/api/v2/cameras", "weight": 40},
        {"path": "/api/v2/detections", "weight": 30},
        {"path": "/api/v2/analytics/reports", "weight": 20},
        {"path": "/api/v2/streams/{camera_id}", "weight": 10}
    ]
```

## Security Architecture

### Authentication & Authorization

```python
# JWT Token Structure
{
  "sub": "user_id",
  "username": "admin",
  "roles": ["admin", "operator"],
  "permissions": ["camera:read", "camera:write", "detection:read"],
  "exp": 1641768000,
  "iat": 1641764400,
  "jti": "token_id"
}

# Permission-based Authorization
class PermissionChecker:
    def has_permission(self, user: User, resource: str, action: str) -> bool:
        required_permission = f"{resource}:{action}"
        return required_permission in user.permissions
```

### Data Encryption

```python
# Sensitive Data Encryption
class EncryptionService:
    def encrypt_sensitive_data(self, data: str) -> str:
        # AES-256 encryption for passwords, API keys
        pass
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        # Decryption with proper key management
        pass
```

### Security Headers

```python
# Security Middleware
class SecurityMiddleware:
    def add_security_headers(self, response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
```

## Deployment Architecture

### Containerization

```dockerfile
# Dockerfile for microservices
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
# Camera Management Service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: camera-management-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: camera-management
  template:
    metadata:
      labels:
        app: camera-management
    spec:
      containers:
      - name: camera-management
        image: lpr/camera-management:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Service Mesh (Istio)

```yaml
# Service Mesh Configuration
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: camera-management-vs
spec:
  http:
  - match:
    - uri:
        prefix: /api/v2/cameras
    route:
    - destination:
        host: camera-management-service
        port:
          number: 8000
    fault:
      delay:
        percentage:
          value: 0.1
        fixedDelay: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
```

This comprehensive design provides a solid foundation for implementing a modern, scalable backend architecture that meets all the requirements while following industry best practices and patterns.