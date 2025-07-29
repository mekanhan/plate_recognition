# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Universal Decision Framework

Before implementing ANY solution, Claude must ask these questions:

1. **Simplicity Check**: Does this make the core functionality simpler or more complex?
   - If more complex, reconsider approach
   - Always prefer simple, direct solutions

2. **Barrier Analysis**: Does this remove barriers or add them?
   - Focus on removing obstacles to core functionality
   - Avoid adding dependencies or complexity layers

3. **Problem Alignment**: Am I solving the user's actual problem or a technical side-effect?
   - Stay focused on the stated user requirement
   - Don't get distracted by technical rabbit holes

### Core System Principles
- **24/7 live streaming in web UI** (no manual start/stop)
- **Simple, straightforward architecture**
- **Cameras auto-connect and auto-reconnect**
- **Real-time status display** (not database status)
- **Remove barriers, don't add them**

## Key Commands

### Development
```bash
# Start backend server (from backend directory)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Start 24/7 recording service (runs independently)
cd backend
source venv/bin/activate
nohup python main_recording_service.py > logs/recording_service.log 2>&1 &

# Start recording API service (REST API for recordings)
cd backend
source venv/bin/activate
python recording_api_service.py

# Start frontend server (from frontend directory)
cd frontend
python3 -m http.server 8080

# Run tests
pytest tests/ -v --tb=short

# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Train YOLO model
cd train && bash train_yolo.sh
```

### Service Access
- **Frontend URL**: http://localhost:8080/
- **Backend API**: http://localhost:8001/
- **API Documentation**: http://localhost:8001/docs
- **24/7 Recording API**: http://localhost:8002/
- **Recording API Documentation**: http://localhost:8002/docs

### Streaming System
```bash
# Check streaming status for camera
curl http://localhost:8001/api/v1/streams/status/3

# Start stream (via API)
curl -X POST http://localhost:8001/api/v1/streams/start/3 \
  -H "Content-Type: application/json" \
  -d '{"quality": "medium", "max_fps": 30, "detection_enabled": false}'

# Stop stream (via API)
curl -X POST http://localhost:8001/api/v1/streams/stop/3

# Access video stream directly
curl http://localhost:8001/stream/video/3
```

### 24/7 Recording System
```bash
# Check recording service health
curl http://localhost:8002/health

# Get recording status for all cameras
curl http://localhost:8002/recordings/status

# Get recording status for specific camera
curl http://localhost:8002/recordings/status/3

# Get recent video segments for a camera
curl http://localhost:8002/recordings/3/segments

# Get comprehensive storage report
curl http://localhost:8002/storage/report

# Check recording service logs
tail -f backend/logs/recording_service.log

# Monitor live recording activity
watch -n 5 "curl -s http://localhost:8002/health | grep -E '(active_cameras|total_segments|total_size_formatted)'"

# Verify recordings are being created
ls -la backend/recordings/camera_3/$(date +%Y/%m/%d/%H)/
```

### Docker
```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f lpr-app

# Stop services
docker-compose down
```

### Script Usage
```bash
# For USB cameras
python scripts/lpr_live.py usb --id 0

# For IP cameras (like Android phone)
python scripts/lpr_live.py ip --ip 192.168.1.100 --port 8080

# For CSI cameras (Jetson/Raspberry Pi)
python scripts/lpr_live.py csi
```

## Architecture Overview

### Core Framework
- **FastAPI** monolithic application with modular services
- **SQLite** database with async support (aiosqlite)
- **YOLO** models for license plate detection (YOLOv11/v8)
- **EasyOCR** for license plate text recognition
- **OpenCV** for image processing and camera handling
- **WebSocket** connections for real-time streaming

### Key Directory Structure
```
app/
├── main.py              # FastAPI application entry point
├── database.py          # SQLAlchemy async database setup
├── models.py            # Pydantic models and SQLAlchemy schemas
├── dependencies/        # FastAPI dependency injection
├── factories/           # Service factory patterns
├── interfaces/          # Abstract base classes
├── repositories/        # Data access layer
├── routers/             # FastAPI route handlers
├── services/            # Business logic services
└── utils/               # Utility functions and helpers
```

### Service Layer Architecture
- **DetectionService**: YOLO model inference and plate detection
- **CameraService**: Camera input management and streaming
- **StorageService**: Database operations and file management
- **EnhancerService**: Image processing and enhancement
- **BackgroundStreamManager**: Real-time video processing
- **PlateProcessor**: License plate recognition pipeline

### Database Schema
- SQLite database at `data/license_plates.db`
- Async SQLAlchemy with aiosqlite driver
- Main tables: detections, license_plates, system_config
- Automatic database initialization on first run

## 24/7 Recording System Architecture

### Recording Components
- **main_recording_service.py**: Continuous recording service (independent process)
- **recording_api_service.py**: REST API for monitoring recordings (port 8002)
- **ContinuousRecorder**: Per-camera recording with segment management
- **StorageManager**: Automated cleanup and retention policies
- **SQLite Index**: Fast video segment retrieval and metadata

### Key Features
- **Continuous Operation**: Runs independently from web UI on dedicated process
- **Segment-based Storage**: 10-minute video segments for efficient storage/retrieval
- **Automatic Reconnection**: Robust handling of camera disconnections
- **Storage Management**: 30-day retention with automated cleanup
- **Health Monitoring**: Automatic restart of failed recordings
- **Directory Structure**: Organized by date/time (YYYY/MM/DD/HH)

### Recording System Flow
1. **Service Startup**: Load camera configurations and initialize storage
2. **Camera Connection**: Establish RTSP connections with reconnection logic
3. **Frame Capture**: Continuous frame capture with queue management
4. **Segment Recording**: Create new video segments every 10 minutes
5. **Database Indexing**: Store segment metadata in SQLite for fast access
6. **Storage Cleanup**: Automated removal of recordings older than retention period
7. **Health Checks**: Monitor recording status and restart failed cameras

### Recording Storage Structure
```
recordings/
└── camera_3/
    ├── index.db                    # SQLite database with segment metadata
    └── 2025/07/27/12/             # Year/Month/Day/Hour structure
        ├── camera_3_20250727_120329_600.avi  # 10-minute segments
        ├── camera_3_20250727_121329_600.avi
        └── camera_3_20250727_122329_600.avi
```

### Recording API Endpoints
- `GET /health` - Service health and recording status
- `GET /recordings/status` - Status for all cameras
- `GET /recordings/status/{camera_id}` - Specific camera status
- `GET /recordings/{camera_id}/segments` - Available video segments
- `GET /storage/report` - Comprehensive storage statistics

## Streaming Integration Architecture

### Frontend Streaming Components
- **LiveVideoPlayer**: Reusable streaming component for camera feeds
- **CamerasPage**: Main interface with external stream control buttons
- **Stream State Management**: Real-time synchronization with backend status
- **Periodic Polling**: Auto-sync every 30 seconds to maintain state consistency

### Key Features
- **Smart Button States**: Start/Stop buttons reflect actual backend streaming status
- **Enhanced Fullscreen**: Loading states, error handling, and timeout management
- **Camera Validation**: Prevents streaming attempts on offline cameras
- **Real-time Duration**: Live stream duration counter with timer management
- **Error Recovery**: Fallback mechanisms and user-friendly error messages

### Stream Control Flow
1. **Page Load**: Check streaming status for all cameras via `/api/v1/streams/status/{id}`
2. **Button Sync**: Initialize button states based on backend response
3. **Stream Operations**: Validate camera status before start/stop operations
4. **Status Polling**: Maintain sync with periodic backend status checks
5. **UI Updates**: Dynamic button states, duration timers, and visual feedback

### Troubleshooting Streaming Issues

**Button Shows Wrong State:**
```bash
# Check backend streaming status
curl http://localhost:8001/api/v1/streams/status/3

# If mismatch, check browser console for sync errors
# Frontend polls every 30 seconds to resync
```

**Fullscreen Shows Black Screen:**
```bash
# Verify stream endpoint is responding
curl -I http://localhost:8001/stream/video/3

# Check if stream is actually active
curl http://localhost:8001/api/v1/streams/status/3

# Look for camera connection issues in backend logs
```

**Stream Won't Start:**
```bash
# Check camera status first
curl http://localhost:8001/api/v1/cameras/

# Verify camera is online before streaming
# Check backend logs for connection errors
```

## Development Guidelines

### Model Management
- YOLO models stored in `app/models/` directory
- Primary model: `yolo11m_best.pt`
- GPU acceleration with CUDA when available
- Model caching to avoid reloading

### Camera Integration
- Supports USB, IP, and CSI cameras
- Android device integration via DroidCam
- Real-time streaming with WebSocket connections
- Camera configuration stored in `config/camera_config.json`

### Testing Framework
- Pytest for unit and integration tests
- Test data in `tests/` directory
- GPU testing utilities in `scripts/unit_tests/`
- End-to-end testing with real camera feeds

### File Storage
- License plate images: `data/license_plates/`
- Enhanced images: `data/enhanced_plates/`
- Video recordings: `data/videos/`
- Configuration backups: `config/backups/`

## Dependencies

### Core Python Packages
- fastapi>=0.95.0
- uvicorn[standard]>=0.22.0
- torch>=2.0.1,<2.6.0
- ultralytics>=8.0.0,<8.4.0
- opencv-python>=4.8.0.74
- easyocr>=1.7.0
- sqlalchemy (async)
- aiosqlite

### Development Tools
- pytest>=7.4.0
- Docker and Docker Compose
- Node.js (for package.json tools)

## Performance Considerations

### GPU Acceleration
- CUDA support for PyTorch models
- GPU memory management for large models
- CPU fallback when GPU unavailable

### Real-time Processing
- Async/await for I/O operations
- WebSocket streaming for low latency
- Background processing for video analysis
- Memory optimization for continuous operation

### Edge Device Optimization
- Designed for NVIDIA Jetson Nano and Raspberry Pi 5
- Minimal resource usage patterns
- Local file storage for speed
- Efficient model loading and caching