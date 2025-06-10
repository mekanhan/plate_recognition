# Technology Stack - V2 License Plate Recognition System

**Version:** 2.0  
**Last Updated:** 2025-06-10  
**Authors:** Development Team  

## Overview

This document provides a comprehensive overview of the technology stack used in the V2 License Plate Recognition System, including versions, configurations, and integration details.

## Core Technology Stack

### Programming Language

#### **Python 3.8+**
- **Primary Language**: Python 3.8.x - 3.11.x (3.9-3.11 recommended)
- **Async Support**: Full async/await pattern implementation
- **Type Hints**: Comprehensive type annotations for better code quality
- **Package Management**: pip with requirements.txt

```python
# Example of V2 async patterns
async def process_detection(self, detection_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    async with self.detection_lock:
        result = await self.detector.detect_and_recognize(detection_data)
        return result
```

## Web Framework & API

### **FastAPI 0.95.0+**
- **Modern Framework**: Latest FastAPI with automatic OpenAPI documentation
- **Async Support**: Native async/await support for high performance
- **Dependency Injection**: Advanced DI system for service management
- **API Versioning**: Support for both V1 and V2 API endpoints
- **Validation**: Pydantic integration for request/response validation

#### Key Features Used:
- **Router-based Architecture**: Modular endpoint organization
- **Background Tasks**: Async task management
- **WebSocket Support**: Real-time communication capabilities
- **Middleware**: Custom middleware for logging and error handling

```python
# V2 API endpoint example
@router.get("/v2/results/detections")
async def get_detections(
    limit: int = Query(10, description="Maximum number of detections"),
    detection_repository: DetectionRepository = Depends(get_detection_repository)
):
    return await detection_repository.get_detections()
```

### **Uvicorn 0.22.0+**
- **ASGI Server**: High-performance async server
- **Auto-reload**: Development mode with hot reloading
- **SSL Support**: HTTPS deployment capabilities
- **Worker Processes**: Multi-worker production deployment

## Computer Vision & Machine Learning

### **OpenCV 4.8.0+**
- **Video Processing**: Camera capture and video recording
- **Image Processing**: Frame manipulation and enhancement
- **Codec Support**: MP4V, H.264 video encoding
- **WSL Compatibility**: Optimized for Windows Subsystem for Linux

#### V2 Enhancements:
- **Enhanced Overlays**: Confidence-based color coding
- **Performance Optimization**: Efficient frame processing
- **Memory Management**: Optimized buffer handling

```python
# Enhanced overlay implementation
def add_enhanced_overlay(frame, detection):
    confidence = detection.get('confidence', 0) * 100
    color = (0, 255, 0) if confidence >= 80 else (0, 255, 255) if confidence >= 60 else (0, 0, 255)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(frame, f"TX: ABC123 ({confidence:.0f}%)", (x1, y1-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
```

### **YOLO (Ultralytics 8.0+)**
- **Model Architecture**: YOLOv8/YOLOv11 for object detection
- **Custom Training**: Support for custom license plate models
- **GPU Acceleration**: CUDA optimization for NVIDIA GPUs
- **Model Formats**: Support for .pt, .onnx formats

#### Supported Models:
- **YOLOv11m**: Medium model (recommended)
- **YOLOv8m**: Alternative medium model
- **Custom Models**: Trained on license plate datasets

### **EasyOCR 1.7.0+**
- **Text Recognition**: Optical Character Recognition for license plates
- **Multi-language**: English language optimization
- **GPU Support**: CUDA acceleration available
- **Confidence Scoring**: Per-character confidence metrics

#### V2 OCR Enhancements:
- **Bounding Box Analysis**: Spatial text element scoring
- **Character Correction**: Confusion matrix-based corrections
- **State-specific Logic**: Texas plate improvements

### **PyTorch 2.0.1+**
- **Deep Learning Framework**: Backend for YOLO models
- **CUDA Support**: GPU acceleration (when available)
- **Model Optimization**: FP16 precision for faster inference
- **Version Constraints**: <2.6.0 for compatibility

## Data Storage & Management

### **SQLite with SQLAlchemy**
- **Primary Database**: SQLite for structured data storage
- **ORM**: SQLAlchemy with async support
- **Migrations**: Automatic schema creation and updates
- **Performance**: Optimized for single-user applications

#### Database Schema:
```sql
-- Detections table
CREATE TABLE detections (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    plate_text TEXT NOT NULL,
    confidence REAL NOT NULL,
    state TEXT,
    box TEXT,
    frame_id INTEGER,
    video_path TEXT
);

-- Enhanced results table  
CREATE TABLE enhanced_results (
    id TEXT PRIMARY KEY,
    original_detection_id TEXT,
    plate_text TEXT NOT NULL,
    confidence REAL NOT NULL,
    match_type TEXT,
    timestamp DATETIME NOT NULL
);

-- Video segments table
CREATE TABLE video_segments (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_seconds REAL,
    file_size_bytes INTEGER,
    resolution TEXT,
    detection_ids TEXT
);
```

### **JSON File Storage**
- **Secondary Storage**: Human-readable data format
- **Backup & Export**: Easy data export and debugging
- **Session Management**: Organized by detection sessions
- **Atomic Writes**: Temporary file + rename for data integrity

#### JSON Structure:
```json
{
  "session_info": {
    "session_id": "session_20250610_023456", 
    "start_time": 1733881496.123,
    "version": "2.0",
    "enhanced_features": true
  },
  "detections": [
    {
      "detection_id": "det_abc123",
      "timestamp": 1733881500.456,
      "plate_text": "ABC123",
      "confidence": 0.87,
      "state": "TX",
      "enhanced": true
    }
  ]
}
```

## Architecture Patterns

### **Repository Pattern**
- **Data Abstraction**: Interface-based data access
- **Multiple Implementations**: SQL and JSON repositories
- **Composite Pattern**: Dual storage with automatic failover
- **Async Operations**: Non-blocking database operations

```python
class CompositeDetectionRepository(DetectionRepository):
    def __init__(self, sql_repo: DetectionRepository, json_repo: DetectionRepository):
        self.sql_repository = sql_repo
        self.json_repository = json_repo
    
    async def add_detections(self, detections: List[Dict]):
        # Write to both repositories
        await asyncio.gather(
            self.sql_repository.add_detections(detections),
            self.json_repository.add_detections(detections)
        )
```

### **Dependency Injection**
- **Service Factory**: Centralized service creation and management
- **Interface-based**: Services depend on interfaces, not implementations
- **Configuration-driven**: Service configuration through factory
- **Lifecycle Management**: Automatic service initialization and cleanup

### **Interface-based Design**
- **Contracts**: Clear interfaces define service contracts
- **Testability**: Easy mocking and unit testing
- **Flexibility**: Swap implementations without code changes
- **Maintainability**: Clear separation of concerns

## Development Tools & Libraries

### **Data Processing**
- **NumPy 1.25.2+**: Numerical computing and array operations
- **Pandas 2.0.3+**: Data analysis and manipulation
- **Scikit-image 0.21.0+**: Image processing algorithms
- **Scipy 1.11.1+**: Scientific computing utilities

### **Machine Learning Support**
- **Scikit-learn 1.3.0+**: Machine learning utilities
- **ONNX 1.14.0+**: Model interchange format
- **ONNX Runtime 1.15.1+**: Optimized inference engine

### **Utilities**
- **Pydantic 2.0.0+**: Data validation and settings management
- **Python-multipart 0.0.6+**: File upload handling
- **Jinja2 3.1.2+**: Template engine for web interface
- **Python-dotenv 1.0.0+**: Environment variable management

### **Testing Framework**
- **Pytest 7.4.0+**: Testing framework with async support
- **Pytest-mock 3.11.1+**: Mocking utilities for testing
- **Custom Test Utilities**: Domain-specific test helpers

```python
# Example test with dependency injection
@pytest.mark.asyncio
async def test_detection_service():
    mock_camera = Mock(spec=Camera)
    mock_detector = Mock(spec=LicensePlateDetector)
    mock_repository = Mock(spec=DetectionRepository)
    
    service = DetectionServiceV2()
    await service.initialize(
        camera=mock_camera,
        detector=mock_detector,
        detection_repository=mock_repository
    )
    
    # Test service functionality
    assert service.camera == mock_camera
```

## Performance & Monitoring

### **Logging**
- **Structured Logging**: JSON-formatted logs for analysis
- **Multiple Levels**: DEBUG, INFO, WARNING, ERROR levels
- **Component-specific**: Per-service logging configuration
- **Coloredlogs 15.0.1+**: Enhanced console output

### **System Monitoring**
- **psutil 5.9.5+**: System resource monitoring
- **Performance Metrics**: CPU, memory, disk usage tracking
- **Custom Metrics**: Application-specific performance indicators

### **Asynchronous Processing**
- **asyncio**: Native Python async/await support
- **Task Management**: Background task coordination
- **Timeout Handling**: Prevent blocking operations
- **Resource Pooling**: Efficient resource utilization

## Video Processing Stack

### **Video Recording**
- **Codec**: MP4V for broad compatibility
- **Frame Rate**: 15 FPS for optimal file size/quality
- **Resolution**: Configurable (default 1280x720)
- **Buffer Management**: 5-second pre-event buffer

### **Streaming**
- **Format**: MJPEG over HTTP
- **Real-time**: Low-latency streaming
- **Adaptive Quality**: Dynamic quality adjustment
- **Multi-client**: Support for multiple concurrent viewers

## Configuration Management

### **Environment-based Configuration**
```bash
# Core Configuration
CAMERA_ID=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720

# Model Configuration
MODEL_PATH=app/models/yolo11m_best.pt

# Storage Configuration  
LICENSE_PLATES_DIR=data/license_plates
ENHANCED_PLATES_DIR=data/enhanced_plates

# Performance Configuration
PROCESS_EVERY_N_FRAMES=5
FRAME_PROCESSING_TIMEOUT=0.5
VIDEO_BUFFER_SECONDS=5
POST_EVENT_SECONDS=15

# Feature Flags
DUAL_STORAGE_ENABLED=true
VIDEO_OVERLAYS_ENABLED=true
ENHANCED_RECOGNITION_ENABLED=true
```

### **Pydantic Settings**
```python
class Config(BaseSettings):
    camera_id: str = "0"
    camera_width: str = "1280"
    camera_height: str = "720"
    model_path: str = "app/models/yolo11m_best.pt"
    license_plates_dir: str = "data/license_plates"
    enhanced_plates_dir: str = "data/enhanced_plates"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
```

## Deployment Technologies

### **Production Deployment**
- **Systemd**: Linux service management
- **Docker**: Containerized deployment option
- **Nginx**: Reverse proxy for production
- **SSL/TLS**: HTTPS support for secure communication

### **Development Tools**
- **Virtual Environments**: Isolated Python environments
- **Git**: Version control with branching strategy
- **WSL2**: Windows development environment
- **Hot Reload**: Development mode with auto-restart

## Security Considerations

### **Input Validation**
- **Pydantic Validation**: Automatic request validation
- **File Upload Security**: Safe file handling
- **Parameter Sanitization**: SQL injection prevention
- **Rate Limiting**: Request throttling capabilities

### **Data Protection**
- **Local Storage**: Data remains on local system
- **No External APIs**: Self-contained processing
- **Access Control**: Configuration-based security
- **Audit Logging**: Comprehensive operation logging

## Platform Compatibility

### **Operating Systems**
| Platform | Support Level | Notes |
|----------|---------------|-------|
| **Ubuntu 18.04+** | ✅ Full | Primary development platform |
| **Windows 10/11 + WSL2** | ✅ Full | Recommended Windows setup |
| **macOS 10.15+** | ✅ Full | Compatible with Apple Silicon |
| **Docker** | ✅ Full | Cross-platform deployment |
| **Windows Native** | ⚠️ Limited | Some video features may be limited |

### **Hardware Requirements**
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| **RAM** | 8GB | 16GB+ |
| **GPU** | Integrated graphics | NVIDIA GTX 1060+ |
| **Storage** | 10GB free (HDD) | 20GB+ free (SSD) |
| **Camera** | USB 2.0 webcam | USB 3.0 or IP camera |

## Version Compatibility Matrix

| Component | V1 Version | V2 Version | Breaking Changes |
|-----------|------------|------------|------------------|
| **FastAPI** | 0.85.0+ | 0.95.0+ | Enhanced dependency injection |
| **OpenCV** | 4.5.0+ | 4.8.0+ | Improved codec support |
| **PyTorch** | 1.12.0+ | 2.0.1+ | Model compatibility updates |
| **EasyOCR** | 1.6.0+ | 1.7.0+ | Enhanced language support |
| **SQLAlchemy** | 1.4.0+ | 2.0.0+ | Async support improvements |
| **Pydantic** | 1.10.0+ | 2.0.0+ | Major API changes |

## Future Technology Roadmap

### **Planned Upgrades**
- **Python 3.12**: Migration to latest Python version
- **FastAPI 0.100+**: Latest framework features
- **YOLOv12**: Next-generation detection models
- **PostgreSQL**: Optional enterprise database support
- **Redis**: Caching and session management
- **WebRTC**: Advanced streaming capabilities

### **Research Areas**
- **Edge Computing**: Deployment on edge devices
- **Cloud Integration**: Optional cloud storage and processing
- **Mobile Applications**: iOS/Android companion apps
- **Kubernetes**: Container orchestration for scaling

This comprehensive technology stack provides a solid foundation for the V2 License Plate Recognition System while maintaining flexibility for future enhancements and optimizations.