# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Key Commands

### Development
```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
pytest tests/ -v --tb=short

# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Train YOLO model
cd train && bash train_yolo.sh
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