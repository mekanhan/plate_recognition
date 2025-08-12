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

## Documentation-First Implementation Protocol

Before implementing ANY code changes, Claude MUST:

1. **Search Documentation**: Use Glob and Read tools to find relevant documentation in:
   - `/docs/` - Architecture and implementation guides
   - `/docs/features/` - Feature specifications
   - `/docs/fixes/` - Previous fix implementations
   - `/docs/TESTING/` - Test scenarios and expected values
   - Project README files

2. **Review Existing Solutions**: Check if the issue was previously addressed:
   - Look for similar fixes in `/docs/fixes/`
   - Check implementation reports for lessons learned
   - Review architecture decisions and constraints

3. **Follow Documented Patterns**: Ensure new code follows:
   - Established architectural patterns
   - Coding conventions from existing documentation
   - Database schema standards
   - API endpoint patterns

4. **Update Documentation**: After implementation:
   - Create or update relevant documentation
   - Document any architectural decisions
   - Add troubleshooting notes if applicable

**MANDATORY**: If no relevant documentation exists, Claude must ask the user whether to proceed or create documentation first.

## Breaking Changes Prevention Protocol

Before implementing ANY code changes that modify existing functionality, Claude MUST ask these critical questions:

### 1. **Impact Assessment Questions**
- **Will this break existing imports?** Check all files that import from the modules being changed
- **What APIs/interfaces will be affected?** Identify all public methods, classes, and endpoints
- **Are there existing tests that might fail?** Review test files that depend on current behavior
- **How will database changes impact existing data?** Analyze schema modifications and data migration needs
- **Will frontend/API consumers be affected?** Check for endpoint signature changes

### 2. **Backward Compatibility Requirements**
- **Maintain Existing Interfaces**: Keep all public class names, method signatures, and return types unchanged
- **Use Facade Pattern**: When refactoring, create thin wrapper classes that delegate to new implementation
- **Optional New Fields**: Add database columns and dataclass fields with defaults to avoid breaking existing records
- **API Versioning**: Add new endpoints rather than modifying existing ones when possible
- **Gradual Migration**: Support both old and new systems during transition periods

### 3. **Migration Strategy Framework**
- **Document Migration Path**: Clearly explain how existing code will continue working
- **Provide Compatibility Layer**: Create adapters/wrappers to bridge old and new implementations
- **Test Thoroughly**: Verify all existing functionality continues working with new changes
- **Version Support**: Plan how long to maintain backward compatibility
- **Rollback Plan**: Ensure changes can be safely reverted if issues arise

### 4. **Specific Check Points**

**Database Changes:**
- Use `ALTER TABLE ADD COLUMN` with defaults, never `ALTER COLUMN` existing fields
- Ensure new columns are nullable or have sensible defaults
- Test with existing data records

**Code Refactoring:**
- Keep original files as facade/wrapper layers
- Move implementation to new organized structure
- Maintain exact same public APIs

**Import Dependencies:**
- Check all files using `grep -r "from module_being_changed"`
- Ensure import statements continue working unchanged
- Test import compatibility

**API Endpoints:**
- Never change existing endpoint signatures
- Add new endpoints for new features
- Maintain response format compatibility

### 5. **Required Questions Before Implementation**

Claude MUST ask the user:

1. **"Will this change break any existing imports or code that depends on [specific module/class]?"**
2. **"Should I maintain backward compatibility by keeping the existing [class/API/endpoint] as a wrapper?"**
3. **"How do you want to handle existing [database records/API consumers/test cases] during this change?"**
4. **"Would you prefer I add new functionality alongside existing code rather than modifying it?"**

### 6. **Implementation Safety Pattern**

**✅ SAFE APPROACH:**
```python
# Keep existing interface working
class ExistingClass:
    def __init__(self, *args, **kwargs):
        # Delegate to new implementation
        self._impl = NewImplementation(*args, **kwargs)
    
    def existing_method(self, param):
        # Maintain exact same signature and behavior
        return self._impl.new_method(param)
```

**❌ UNSAFE APPROACH:**
```python
# This breaks existing code!
class ExistingClass:  # Changed constructor parameters
    def __init__(self, new_required_param, *args, **kwargs):
        ...
    
    def existing_method(self, param, new_param):  # Changed signature
        ...
```

**MANDATORY**: If there's any doubt about breaking changes, Claude must ask the user for clarification and approval before proceeding.

## Key Commands

### Quick Start (NEW - Recommended)
```bash
# Start ALL services with one command
python3 start_lpr.py

# Or use the restart script
python3 restart_services.py

# Stop all services
python3 stop_all_services.py

# Check service health
python3 check_services.py
```

### Manual Start (if needed)
```bash
# Start backend API server (Main API on port 8001)
python3 -m api.main

# Start 24/7 recording service (port 8002)
python3 start_recording_service.py

# Start frontend server (port 8080)
cd frontend && python3 -m http.server 8080

# Run tests
pytest tests/ -v --tb=short

# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Train YOLO model
cd ai_pipeline/train && bash train_yolo.sh
```

### Database Migrations
```bash
# Check migration status
python3 migrate.py current

# Apply pending migrations
python3 migrate.py upgrade

# Create new migration (after model changes)
python3 migrate.py create "Description of changes"

# Show migration history
python3 migrate.py history

# Rollback to previous version
python3 migrate.py downgrade -1
```

### Service Access
- **Frontend URL**: http://localhost:8080/
- **Main API**: http://localhost:8001/
- **Main API Documentation**: http://localhost:8001/docs
- **Recording API**: http://localhost:8002/
- **Recording API Documentation**: http://localhost:8002/docs

### Snapshot System (No Browser Streaming)
```bash
# Get camera snapshot (JPEG)
curl http://localhost:8001/api/cameras/entrance_cam/snapshot

# Get camera snapshot with quality setting
curl "http://localhost:8001/api/cameras/entrance_cam/snapshot?quality=high"

# Get camera health status
curl http://localhost:8001/api/cameras/entrance_cam/health

# List all cameras
curl http://localhost:8001/api/cameras/
```

### System Health
```bash
# Check overall system health
curl http://localhost:8001/api/system/health

# Get camera detection status
curl http://localhost:8001/api/cameras/entrance_cam/detections

# Check license plate processing
curl http://localhost:8001/api/detections/

# Check recording service health
curl http://localhost:8002/health
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
- **FastAPI** dual-service architecture: Main API (8001) + Recording Service (8002)
- **SQLite** database with async support (aiosqlite) and dynamic schema updates
- **YOLO** models for license plate detection (YOLOv11/v8)
- **EasyOCR** for license plate text recognition
- **OpenCV** for image processing and camera handling
- **Dynamic Camera Management** with real-time database synchronization

### Key Directory Structure
```
plate_recognition/
├── api/
│   └── main.py              # Main API service (port 8001)
├── recording_service/
│   ├── main.py              # Recording API service (port 8002)
│   └── services/            # Recording components
├── database/
│   ├── models.py            # SQLAlchemy models with Camera schema
│   └── service.py           # Database operations
├── frontend/
│   ├── index.html           # Main dashboard
│   ├── cameras.html         # Camera management
│   ├── recordings.html      # Recording playback
│   └── src/                 # Component architecture
├── ai_pipeline/             # YOLO detection pipeline
├── logs/                    # Service log files
├── recordings/              # Video storage
├── data/                    # SQLite database
└── *.py                     # Service management scripts
```

### Service Layer Architecture

#### Main API Service (Port 8001)
- **CameraManager**: Dynamic camera loading from database
- **LicensePlateDetector**: YOLO model inference and plate detection
- **ProcessingPipeline**: Detection workflow coordination
- **DatabaseService**: Async database operations with CRUD for cameras
- **Camera CRUD API**: REST endpoints for camera management
- **Snapshot Service**: Camera image serving (not video streaming)

#### Recording Service (Port 8002)
- **RecordingManager**: 24/7 continuous recording coordination
- **CameraRecorder**: Individual camera recording with 10-minute segments
- **PlaybackService**: Video timeline and streaming API
- **StorageManager**: Automated cleanup and retention policies
- **Recording API**: Complete REST API for playback functionality

### Database Schema
- SQLite database at `data/license_plates.db`
- Async SQLAlchemy with aiosqlite driver
- **Enhanced Camera Table**: Includes all connection details (IP, port, credentials, stream paths)
- **Dynamic Schema Updates**: `update_database_schema.py` adds missing columns
- Main tables: cameras, detections, video_recordings, daily_summaries
- **Service Integration**: Cameras configured via UI are automatically used by all services

## 24/7 Recording System Architecture ✅ IMPLEMENTED

### Recording Components
- **start_recording_service.py**: Service startup script for port 8002
- **recording_service/main.py**: FastAPI application with complete playback API
- **RecordingManager**: Manages 24/7 recording for all active cameras
- **CameraRecorder**: Per-camera recording with 10-minute segments
- **PlaybackService**: Complete video playback and timeline API
- **StorageManager**: Automated cleanup and storage monitoring (10GB limit)

### Key Features ✅ IMPLEMENTED
- **Continuous Operation**: Runs independently on port 8002 with database integration
- **Segment-based Storage**: 10-minute video segments (600 seconds) in organized directories
- **Automatic Reconnection**: Robust RTSP connection handling with exponential backoff
- **Storage Management**: Automated cleanup at 90% usage with configurable retention
- **Health Monitoring**: Real-time status monitoring and error recovery
- **Directory Structure**: `recordings/camera_id/YYYY/MM/DD/HH/` organization
- **Complete Playback API**: Calendar data, timeline segments, HTTP 206 video streaming

### Recording System Implementation Status
✅ **Database Models**: VideoRecording, DailySummary, StorageStats with indexes
✅ **Recording Service**: Full FastAPI service with startup/shutdown lifecycle
✅ **Camera Management**: Dynamic loading from database with JSON config parsing
✅ **Storage Management**: Size monitoring, cleanup, and comprehensive reporting
✅ **Playback API**: All endpoints from documentation implemented
✅ **Health Monitoring**: Service status, camera status, and error tracking

### Recording Storage Structure
```
recordings/
└── camera_entrance_cam/
    └── 2025/08/01/01/             # Year/Month/Day/Hour structure
        ├── camera_entrance_cam_20250801_010000_600.avi  # 10-minute segments
        ├── camera_entrance_cam_20250801_011000_600.avi
        └── camera_entrance_cam_20250801_012000_600.avi
```

### Recording API Endpoints ✅ WORKING
- `GET /health` - Service health and recording status
- `GET /recordings/status` - Status for all cameras  
- `GET /recordings/status/{camera_id}` - Specific camera status
- `GET /api/v1/recordings/cameras/{camera_id}/calendar` - Calendar data for month
- `GET /api/v1/recordings/cameras/{camera_id}/timeline` - Timeline segments for date
- `GET /api/v1/recordings/stream/{segment_filename}` - Video streaming with HTTP 206
- `GET /api/v1/recordings/cameras/{camera_id}/details` - Recording statistics
- `POST /api/v1/recordings/cameras/{camera_id}/search` - Search recordings
- `GET /api/v1/storage/report` - Comprehensive storage statistics
- `POST /api/v1/storage/cleanup` - Manual storage cleanup

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

### Camera Integration ✅ DYNAMIC SYSTEM
- **Web-based Configuration**: Full camera CRUD through web UI
- **Connection Testing**: Test camera connections before saving
- **Database-driven**: All services load cameras from database dynamically
- **Real-time Sync**: Camera changes automatically propagate to recording service
- **Support**: RTSP, HTTP, HTTPS camera protocols
- **Auto-reconnection**: Robust handling of camera disconnections
- **No Hardcoding**: Complete removal of hardcoded camera configurations

### Testing Framework
- Pytest for unit and integration tests
- Test data in `tests/` directory
- GPU testing utilities in `scripts/unit_tests/`
- End-to-end testing with real camera feeds

### File Storage
- **Detection Images**: `detections/frames/` and `detections/plates/`
- **Video Recordings**: `recordings/camera_id/YYYY/MM/DD/HH/` (organized by date/hour)
- **Service Logs**: `logs/` with timestamped service logs
- **Database**: `data/license_plates.db` with automatic schema updates
- **Static Assets**: `static/` for web interface resources

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

## Service Management System ✅ COMPLETE

### Comprehensive Service Scripts
A complete set of Python scripts for managing all system services with process management, health monitoring, and graceful shutdown capabilities.

#### Primary Scripts
- **`start_lpr.py`**: Simplest way to start everything (recommended)
- **`start_all_services.py`**: Full-featured startup with monitoring and Ctrl+C handling
- **`stop_all_services.py`**: Graceful shutdown using lsof (no external dependencies)
- **`check_services.py`**: Health monitoring with continuous mode option
- **`restart_services.py`**: Complete restart sequence with verification

#### Management Features
- **Auto venv Detection**: Scripts automatically use `.venv/bin/python3` when available
- **Process Management**: Proper signal handling (SIGTERM → SIGKILL)
- **Health Monitoring**: Real-time service validation with response time measurement
- **Comprehensive Logging**: Timestamped logs for all services in `logs/` directory
- **Port Conflict Resolution**: Automatic detection and cleanup of port conflicts
- **Database Migration**: Automatic schema updates for camera table

#### Service Orchestration
```bash
# Complete system startup
python3 start_lpr.py
# → Checks database schema
# → Starts Main API (8001)
# → Starts Recording Service (8002) 
# → Starts Frontend (8080)
# → Shows access URLs

# Health monitoring
python3 check_services.py -m 30
# → Checks all endpoints every 30 seconds
# → Measures response times
# → Validates API responses
```

#### Architecture Benefits
- **No Manual venv Activation**: Scripts handle virtual environment automatically
- **Robust Error Handling**: Comprehensive error recovery and user feedback
- **Service Dependencies**: Proper startup order and dependency management  
- **Resource Cleanup**: Automatic cleanup of processes and resources
- **Production Ready**: Suitable for deployment with proper logging and monitoring

### Integration with Development Workflow
The service management system integrates seamlessly with the existing development commands while providing enhanced functionality:

**Before**: Manual terminal management
```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8001

# Terminal 2  
cd backend && source venv/bin/activate && python main_recording_service.py

# Terminal 3
cd frontend && python3 -m http.server 8080
```

**Now**: One-command startup
```bash
python3 start_lpr.py
# All services started, monitored, and accessible
```

This represents a significant improvement in developer experience and system reliability.