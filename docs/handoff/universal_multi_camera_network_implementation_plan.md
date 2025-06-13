Universal Multi-Camera Network Implementation Plan                                 │ │
│ │                                                                                    │ │
│ │ Project Context & Current State                                                    │ │
│ │                                                                                    │ │
│ │ Current System: License Plate Recognition (LPR) system built with FastAPI, YOLO    │ │
│ │ models, and SQLite. Successfully completed Phase 1 with enhanced web UI, search    │ │
│ │ capabilities, and headless architecture.                                           │ │
│ │                                                                                    │ │
│ │ Next Goal: Implement universal multi-camera network that supports ANY video source │ │
│ │  (Android devices, IP cameras, USB cameras, RTSP streams) through dynamic          │ │
│ │ discovery and registration.                                                        │ │
│ │                                                                                    │ │
│ │ Implementation Plan (1-2 weeks)                                                    │ │
│ │                                                                                    │ │
│ │ Week 1: Backend Infrastructure                                                     │ │
│ │                                                                                    │ │
│ │ Day 1-2: Camera Management System                                                  │ │
│ │ - Create app/services/camera_manager.py - Universal camera registration and        │ │
│ │ management                                                                         │ │
│ │ - Create app/services/stream_processor.py - Universal stream processing for all    │ │
│ │ camera types                                                                       │ │
│ │ - Add camera management API endpoints to app/routers/cameras.py                    │ │
│ │                                                                                    │ │
│ │ Day 3-4: Database Enhancement                                                      │ │
│ │ - Add cameras table to database schema                                             │ │
│ │ - Enhance detections table with camera_id foreign key                              │ │
│ │ - Create migration scripts for existing data                                       │ │
│ │                                                                                    │ │
│ │ Day 5-7: Stream Processing                                                         │ │
│ │ - Implement RTSP stream handling for IP cameras                                    │ │
│ │ - Add HTTP stream processing for various camera types                              │ │
│ │ - Create frame processing pipeline that handles multiple simultaneous streams      │ │
│ │                                                                                    │ │
│ │ Week 2: Frontend & Discovery                                                       │ │
│ │                                                                                    │ │
│ │ Day 8-10: Progressive Web App (PWA)                                                │ │
│ │ - Create templates/camera_client.html - Universal mobile camera interface          │ │
│ │ - Implement WebRTC camera capture for Android/mobile devices                       │ │
│ │ - Add QR code generation for easy mobile setup                                     │ │
│ │                                                                                    │ │
│ │ Day 11-12: Auto-Discovery                                                          │ │
│ │ - Implement network scanning for IP cameras (RTSP, UPnP)                           │ │
│ │ - Add manual camera registration interface                                         │ │
│ │ - Create camera management UI in existing web interface                            │ │
│ │                                                                                    │ │
│ │ Day 13-14: Integration & Testing                                                   │ │
│ │ - Test with multiple camera types (Android, IP camera, USB)                        │ │
│ │ - Performance optimization for multiple simultaneous streams                       │ │
│ │ - Documentation and deployment testing                                             │ │
│ │                                                                                    │ │
│ │ Technical Specifications                                                           │ │
│ │                                                                                    │ │
│ │ Database Schema Changes                                                            │ │
│ │                                                                                    │ │
│ │ -- New cameras table                                                               │ │
│ │ CREATE TABLE cameras (                                                             │ │
│ │     id TEXT PRIMARY KEY,                                                           │ │
│ │     name TEXT NOT NULL,                                                            │ │
│ │     type TEXT NOT NULL,  -- 'android', 'ip_camera', 'usb', 'rtsp'                  │ │
│ │     source_config JSON,                                                            │ │
│ │     location TEXT,                                                                 │ │
│ │     capabilities JSON,                                                             │ │
│ │     auto_discovered BOOLEAN DEFAULT FALSE,                                         │ │
│ │     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                                │ │
│ │     last_seen TIMESTAMP,                                                           │ │
│ │     status TEXT DEFAULT 'offline'                                                  │ │
│ │ );                                                                                 │ │
│ │                                                                                    │ │
│ │ -- Enhance existing detections table                                               │ │
│ │ ALTER TABLE detections ADD COLUMN camera_id TEXT REFERENCES cameras(id);           │ │
│ │                                                                                    │ │
│ │ New API Endpoints                                                                  │ │
│ │                                                                                    │ │
│ │ POST /api/cameras/register       - Register new camera source                      │ │
│ │ GET  /api/cameras/discover       - Auto-discover network cameras                   │ │
│ │ GET  /api/cameras               - List all registered cameras                      │ │
│ │ PUT  /api/cameras/{id}          - Update camera configuration                      │ │
│ │ DELETE /api/cameras/{id}        - Remove camera                                    │ │
│ │ POST /api/cameras/{id}/stream   - Handle incoming frames from camera               │ │
│ │ GET  /api/cameras/qr/{ip}       - Generate QR code for mobile setup                │ │
│ │                                                                                    │ │
│ │ File Structure Changes                                                             │ │
│ │                                                                                    │ │
│ │ app/                                                                               │ │
│ │ ├── services/                                                                      │ │
│ │ │   ├── camera_manager.py      # NEW: Universal camera management                  │ │
│ │ │   ├── stream_processor.py    # NEW: Multi-stream processing                      │ │
│ │ │   └── network_discovery.py   # NEW: Auto-discovery service                       │ │
│ │ ├── routers/                                                                       │ │
│ │ │   └── cameras.py            # NEW: Camera management API                         │ │
│ │ └── models/                                                                        │ │
│ │     └── camera_models.py       # NEW: Camera-related Pydantic models               │ │
│ │                                                                                    │ │
│ │ templates/                                                                         │ │
│ │ ├── camera_client.html         # NEW: PWA for mobile devices                       │ │
│ │ ├── camera_management.html     # NEW: Camera admin interface                       │ │
│ │ └── multi_camera_view.html     # NEW: Multi-camera dashboard                       │ │
│ │                                                                                    │ │
│ │ static/                                                                            │ │
│ │ ├── js/                                                                            │ │
│ │ │   ├── camera_client.js       # NEW: Mobile camera functionality                  │ │
│ │ │   └── camera_manager.js      # NEW: Admin camera management                      │ │
│ │ └── css/                                                                           │ │
│ │     └── camera_interface.css   # NEW: Camera-specific styling                      │ │
│ │                                                                                    │ │
│ │ Key Implementation Classes                                                         │ │
│ │                                                                                    │ │
│ │ # Camera Management                                                                │ │
│ │ class CameraManager:                                                               │ │
│ │     async def register_camera(source_config: dict) -> str                          │ │
│ │     async def discover_cameras() -> List[dict]                                     │ │
│ │     async def get_camera_status(camera_id: str) -> dict                            │ │
│ │                                                                                    │ │
│ │ # Stream Processing                                                                │ │
│ │ class UniversalStreamProcessor:                                                    │ │
│ │     async def add_camera_source(config: dict) -> str                               │ │
│ │     async def process_frame(camera_id: str, frame: bytes)                          │ │
│ │     async def handle_rtsp_stream(url: str)                                         │ │
│ │     async def handle_pwa_frames(session_id: str, frame: bytes)                     │ │
│ │                                                                                    │ │
│ │ # Network Discovery                                                                │ │
│ │ class NetworkDiscovery:                                                            │ │
│ │     async def scan_rtsp_cameras() -> List[dict]                                    │ │
│ │     async def discover_upnp_devices() -> List[dict]                                │ │
│ │     def generate_setup_qr(ip: str) -> bytes                                        │ │
│ │                                                                                    │ │
│ │ Configuration Updates                                                              │ │
│ │                                                                                    │ │
│ │ # Add to settings.py                                                               │ │
│ │ class Settings:                                                                    │ │
│ │     # Camera network settings                                                      │ │
│ │     CAMERA_DISCOVERY_ENABLED: bool = True                                          │ │
│ │     CAMERA_NETWORK_RANGE: str = "192.168.1.0/24"                                   │ │
│ │     MAX_CONCURRENT_CAMERAS: int = 10                                               │ │
│ │     CAMERA_FRAME_BUFFER_SIZE: int = 30                                             │ │
│ │                                                                                    │ │
│ │     # PWA settings                                                                 │ │
│ │     ENABLE_PWA_CAMERAS: bool = True                                                │ │
│ │     PWA_CAMERA_QUALITY: str = "720p"  # 480p, 720p, 1080p                          │ │
│ │                                                                                    │ │
│ │ Testing Strategy                                                                   │ │
│ │                                                                                    │ │
│ │ Test Cases to Implement                                                            │ │
│ │                                                                                    │ │
│ │ 1. Android PWA Camera - Test with real Android device                              │ │
│ │ 2. IP Camera Integration - Test RTSP stream processing                             │ │
│ │ 3. Multiple Simultaneous Cameras - Performance testing                             │ │
│ │ 4. Auto-Discovery - Network scanning functionality                                 │ │
│ │ 5. Database Migration - Existing data compatibility                                │ │
│ │                                                                                    │ │
│ │ Performance Requirements                                                           │ │
│ │                                                                                    │ │
│ │ - Support 5+ simultaneous camera streams                                           │ │
│ │ - < 500ms latency for mobile camera frames                                         │ │
│ │ - Auto-discovery completes within 30 seconds                                       │ │
│ │ - Memory usage scales linearly with camera count                                   │ │
│ │                                                                                    │ │
│ │ Integration Points                                                                 │ │
│ │                                                                                    │ │
│ │ Existing Code Integration                                                          │ │
│ │                                                                                    │ │
│ │ - Extend current DetectionService to handle camera_id parameter                    │ │
│ │ - Modify StorageService to include camera source information                       │ │
│ │ - Update web UI templates to show camera source in results                         │ │
│ │ - Enhance search functionality to filter by camera                                 │ │
│ │                                                                                    │ │
│ │ Backward Compatibility                                                             │ │
│ │                                                                                    │ │
│ │ - Existing single-camera functionality must remain unchanged                       │ │
│ │ - Current database records get default camera_id                                   │ │
│ │ - Web UI gracefully handles single vs multi-camera modes                           │ │
│ │                                                                                    │ │
│ │ Deployment Considerations                                                          │ │
│ │                                                                                    │ │
│ │ Environment Variables                                                              │ │
│ │                                                                                    │ │
│ │ # Add to .env                                                                      │ │
│ │ CAMERA_DISCOVERY_ENABLED=true                                                      │ │
│ │ CAMERA_NETWORK_RANGE=192.168.1.0/24                                                │ │
│ │ MAX_CONCURRENT_CAMERAS=10                                                          │ │
│ │ PWA_CAMERA_QUALITY=720p                                                            │ │
│ │                                                                                    │ │
│ │ Docker Considerations                                                              │ │
│ │                                                                                    │ │
│ │ - Ensure container can access host network for discovery                           │ │
│ │ - Volume mounts for camera configuration persistence                               │ │
│ │ - Network policies for camera access                                               │ │
│ │                                                                                    │ │
│ │ Success Criteria                                                                   │ │
│ │                                                                                    │ │
│ │ 1. ✅ Android device can connect as camera via browser PWA                          │ │
│ │ 2. ✅ System auto-discovers IP cameras on network                                   │ │
│ │ 3. ✅ Multiple cameras stream simultaneously without performance issues             │ │
│ │ 4. ✅ All detection results include camera source information                       │ │
│ │ 5. ✅ Web UI shows multi-camera view with camera switching                          │ │
│ │ 6. ✅ QR code setup works for easy mobile camera addition                           │ │
│ │                                                                                    │ │
│ │ Handoff Notes for Next AI Agent                                                    │ │
│ │                                                                                    │ │
│ │ Priority Order:                                                                    │ │
│ │ 1. Start with camera_manager.py and basic registration                             │ │
│ │ 2. Implement PWA camera client for immediate testing                               │ │
│ │ 3. Add database schema and migration                                               │ │
│ │ 4. Implement multi-camera web UI                                                   │ │
│ │ 5. Add auto-discovery as final enhancement                                         │ │
│ │                                                                                    │ │
│ │ Key Dependencies:                                                                  │ │
│ │ - Current FastAPI app structure in app/main.py                                     │ │
│ │ - Existing detection service in app/services/detection_service.py                  │ │
│ │ - Database setup in app/database.py                                                │ │
│ │ - Web templates in templates/ directory                                            │ │
│ │                                                                                    │ │
│ │ Testing Approach:                                                                  │ │
│ │ - Use Android device browser for PWA testing                                       │ │
│ │ - Can simulate IP camera with simple HTTP server                                   │ │
│ │ - Test database migration with existing detection data                             │ │
│ │                                                                                    │ │
│ │ This plan maintains full backward compatibility while adding powerful multi-camera │ │
│ │  capabilities that work with any video source.  