# Camera Database Implementation Documentation

## Overview

This document describes the successful implementation of a database-driven camera management system that replaces hardcoded camera configurations. The new architecture provides dynamic camera management, encrypted credential storage, and real-time status updates through a comprehensive API.

**Implementation Date**: August 6, 2025  
**Status**: ✅ Completed and Tested

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Key Components](#key-components)
4. [API Endpoints](#api-endpoints)
5. [Implementation Details](#implementation-details)
6. [Testing Results](#testing-results)
7. [Security Features](#security-features)
8. [Migration Guide](#migration-guide)
9. [Integration Instructions](#integration-instructions)
10. [Next Steps](#next-steps)

## Architecture Overview

The database-driven camera system consists of:

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Frontend UI   │────▶│  v2 API Endpoints │────▶│ Camera Service│
└─────────────────┘     └──────────────────┘     └───────────────┘
                                                           │
                                                           ▼
                                                  ┌────────────────┐
                                                  │ SQLite Database│
                                                  │  (Async ORM)   │
                                                  └────────────────┘
```

### Key Benefits:
- **Dynamic Configuration**: Add/remove cameras without code changes
- **Centralized Management**: Single source of truth for all services
- **Real-time Updates**: Status changes reflected immediately
- **Secure Storage**: Encrypted credentials using Fernet encryption
- **Scalable Design**: Efficient queries with proper indexing

## Database Schema

### 1. **cameras_new** Table
Primary table for camera entities with unique identifiers and basic metadata.

```sql
CREATE TABLE cameras_new (
    id VARCHAR(36) PRIMARY KEY,              -- UUID format
    camera_id VARCHAR(50) UNIQUE NOT NULL,   -- e.g., "camera_946701d3"
    name VARCHAR(100) NOT NULL,              -- Display name
    location VARCHAR(200),                   -- Physical location
    status VARCHAR(20) DEFAULT 'active',     -- active/inactive/maintenance
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 2. **camera_connections** Table
Stores connection details with encrypted credentials.

```sql
CREATE TABLE camera_connections (
    id VARCHAR(36) PRIMARY KEY,
    camera_id VARCHAR(36) REFERENCES cameras_new(id),
    protocol VARCHAR(10) NOT NULL,           -- RTSP/HTTP/HTTPS
    ip_address VARCHAR(45) NOT NULL,         
    port INTEGER DEFAULT 554,
    username VARCHAR(100),                   -- Encrypted
    password VARCHAR(100),                   -- Encrypted
    stream_path VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    last_connected TIMESTAMP,
    created_at TIMESTAMP
);
```

### 3. **camera_recording_config** Table
Recording configuration per camera.

```sql
CREATE TABLE camera_recording_config (
    id VARCHAR(36) PRIMARY KEY,
    camera_id VARCHAR(36) REFERENCES cameras_new(id),
    enabled BOOLEAN DEFAULT false,
    recording_path VARCHAR(500),
    segment_duration INTEGER DEFAULT 600,    -- 10 minutes
    retention_days INTEGER DEFAULT 30,
    video_codec VARCHAR(20) DEFAULT 'h264',
    audio_enabled BOOLEAN DEFAULT true,
    motion_detection BOOLEAN DEFAULT false,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 4. **camera_settings** Table
Flexible key-value storage for camera-specific settings.

```sql
CREATE TABLE camera_settings (
    id VARCHAR(36) PRIMARY KEY,
    camera_id VARCHAR(36) REFERENCES cameras_new(id),
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20),                -- string/int/bool/json
    created_at TIMESTAMP,
    UNIQUE(camera_id, setting_key)
);
```

### 5. **camera_status** Table
Real-time status tracking for the 8-field standard display.

```sql
CREATE TABLE camera_status (
    id VARCHAR(36) PRIMARY KEY,
    camera_id VARCHAR(36) REFERENCES cameras_new(id) UNIQUE,
    recording_status VARCHAR(20) DEFAULT 'stopped',
    connection_status VARCHAR(20) DEFAULT 'disconnected',
    ffmpeg_pid INTEGER,
    segments_created INTEGER DEFAULT 0,
    last_segment_time TIMESTAMP,
    storage_used_bytes BIGINT DEFAULT 0,
    recording_started_at TIMESTAMP,
    last_heartbeat TIMESTAMP,
    error_message TEXT,
    updated_at TIMESTAMP
);
```

### Database Indexes
Optimized for performance with strategic indexes:
```sql
CREATE INDEX idx_cameras_new_camera_id ON cameras_new(camera_id);
CREATE INDEX idx_camera_connections_camera_id ON camera_connections(camera_id);
CREATE INDEX idx_camera_connections_active ON camera_connections(is_active);
CREATE INDEX idx_camera_status_camera_id ON camera_status(camera_id);
CREATE INDEX idx_camera_settings_key ON camera_settings(camera_id, setting_key);
```

## Key Components

### 1. Database Models (`/database/models.py`)
- **CameraNew**: Main camera entity with relationships
- **CameraConnection**: Connection details with encryption
- **CameraRecordingConfig**: Recording preferences
- **CameraSetting**: Flexible key-value settings
- **CameraStatus**: Real-time status tracking

### 2. Camera Service (`/database/camera_service.py`)
Core service providing:
- **CRUD Operations**: Create, Read, Update, Delete cameras
- **Encryption**: Fernet-based credential encryption/decryption
- **Status Management**: Real-time status updates
- **Bulk Operations**: Efficient bulk status queries
- **8-Field Formatting**: Standardized data formatting

Key methods:
```python
async def create_camera(camera_data: Dict) -> Dict
async def get_camera(camera_id: str) -> Optional[Dict]
async def get_all_cameras() -> List[Dict]
async def get_cameras_status() -> Dict  # Bulk status for UI
async def update_camera_status(camera_id: str, status_data: Dict) -> bool
async def delete_camera(camera_id: str) -> bool
```

### 3. API Endpoints (`/api/camera_endpoints.py`)
FastAPI router implementing RESTful endpoints:
- Pydantic models for request/response validation
- Comprehensive error handling
- Async/await pattern throughout
- Automatic API documentation

### 4. Migration Script (`/migrate_to_new_camera_schema.py`)
- Initializes database schema
- Seeds default cameras from existing system
- Encrypts credentials during migration
- Provides migration status and verification

## API Endpoints

All endpoints are prefixed with `/v2/api/cameras` to distinguish from legacy API.

### Camera Management

#### 1. Get All Cameras Status (8-field standard)
```http
GET /v2/api/cameras/status

Response:
{
    "cameras": [
        {
            "id": "camera_entrance_cam",
            "name": "Entrance Security Camera",
            "location": "Front Entrance",
            "connection": "RTSP (10.0.0.182)",
            "recording_status": "⏹️ Stopped",
            "connection_status": "❌ Disconnected",
            "ffmpeg_pid": "None",
            "segments_created": "0",
            "storage_used": "0 B",
            "recording_uptime": "None",
            "last_heartbeat": "2025-08-06T15:38:39.695571",
            "error_message": null
        }
    ],
    "count": 3,
    "timestamp": "2025-08-06T15:38:39.695571"
}
```

#### 2. Get All Cameras (Full Details)
```http
GET /v2/api/cameras

Response: Array of camera objects with complete configuration
```

#### 3. Get Single Camera
```http
GET /v2/api/cameras/{camera_id}

Response:
{
    "id": "camera_entrance_cam",
    "name": "Entrance Security Camera",
    "location": "Front Entrance",
    "status": "active",
    "protocol": "RTSP",
    "ip_address": "10.0.0.182",
    "port": 554,
    "stream_path": "/stream1",
    "recording_config": {
        "enabled": true,
        "segment_duration": 600,
        "retention_days": 30,
        "video_codec": "h264"
    },
    "current_status": { /* 8-field standard */ },
    "settings": {
        "resolution": "1080p",
        "fps": 25,
        "quality": "medium"
    }
}
```

#### 4. Create Camera
```http
POST /v2/api/cameras
Content-Type: application/json

{
    "name": "New Camera",
    "ip_address": "192.168.1.100",
    "port": 554,
    "protocol": "RTSP",
    "stream_path": "/stream1",
    "location": "Parking Lot",
    "username": "admin",
    "password": "secure_password",
    "recording_enabled": true,
    "settings": {
        "resolution": "4K",
        "fps": 30
    }
}
```

### Camera Control

#### 5. Start Recording
```http
POST /v2/api/cameras/{camera_id}/start

Response:
{
    "message": "Recording started for camera camera_entrance_cam",
    "status": "success"
}
```

#### 6. Stop Recording
```http
POST /v2/api/cameras/{camera_id}/stop

Response:
{
    "message": "Recording stopped for camera camera_entrance_cam",
    "status": "success"
}
```

#### 7. Update Camera Status
```http
PUT /v2/api/cameras/{camera_id}/status
Content-Type: application/json

{
    "recording_status": "recording",
    "connection_status": "connected",
    "ffmpeg_pid": 12345,
    "segments_created": 10
}
```

#### 8. Update Camera Settings
```http
PUT /v2/api/cameras/{camera_id}/settings
Content-Type: application/json

{
    "settings": {
        "resolution": "4K",
        "fps": 60,
        "quality": "high"
    }
}
```

### System Endpoints

#### 9. Health Check
```http
GET /health

Response:
{
    "status": "healthy",
    "database": "connected",
    "cameras_count": 3,
    "timestamp": "2025-08-06T15:40:02.196754"
}
```

## Implementation Details

### 1. SQLAlchemy Async ORM
- Uses `aiosqlite` for async SQLite operations
- Session management with context managers
- Proper relationship handling with `selectinload`
- Transaction support with rollback on errors

### 2. Encryption System
```python
# Initialization
cipher_suite = Fernet(encryption_key)

# Encrypting credentials
encrypted_password = cipher_suite.encrypt(password.encode()).decode()

# Decrypting for use
decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode()
```

### 3. Status Formatting (8-field standard)
The system formats camera data according to the standardized 8-field display:

1. **Location**: Physical location or "Unknown"
2. **Connection**: Protocol and IP address
3. **Recording Status**: Emoji-prefixed status (⏹️/▶️/⏸️)
4. **Connection Status**: Emoji-prefixed status (✅/❌/🔄/⚠️)
5. **FFmpeg PID**: Process ID or "None"
6. **Segments Created**: Count with last segment time
7. **Storage Used**: Human-readable bytes (B/KB/MB/GB)
8. **Recording Uptime**: Formatted duration (e.g., "2h 45m")

### 4. Frontend Integration
```javascript
// Frontend configuration (app.config.js)
API_ENDPOINTS: {
    // Database-driven v2 endpoints
    CAMERAS_V2: '/v2/api/cameras',
    CAMERAS_V2_STATUS: '/v2/api/cameras/status',
    CAMERA_V2_START: (id) => `/v2/api/cameras/${id}/start`,
    CAMERA_V2_STOP: (id) => `/v2/api/cameras/${id}/stop`,
    // ... other endpoints
}

// Usage with fallback
async startRecording(cameraId) {
    try {
        // Try new v2 API first
        const response = await fetch(config.buildApiUrl(
            config.API_ENDPOINTS.CAMERA_V2_START(cameraId)
        ), { method: 'POST' });
        
        if (!response.ok) {
            // Fallback to legacy API
            await this.startRecordingLegacy(cameraId);
        }
    } catch (error) {
        // Handle error with legacy fallback
    }
}
```

## Testing Results

### Test Environment
- **Test Server**: Port 8003 (to avoid conflicts)
- **Database**: SQLite with async support
- **Encryption**: Fernet with auto-generated keys

### Successful Tests
1. ✅ **Database Initialization**: Tables created with proper relationships
2. ✅ **Migration Script**: 3 cameras migrated successfully
3. ✅ **Status API**: Returns all cameras with 8-field format
4. ✅ **Individual Camera**: Detailed camera data retrieval
5. ✅ **Recording Control**: Start/stop updates status correctly
6. ✅ **Status Updates**: Real-time status changes persisted
7. ✅ **Health Check**: Database connectivity verified
8. ✅ **Encryption**: Credentials encrypted/decrypted properly

### Test Output Examples
```json
// Camera Status Response
{
    "id": "camera_entrance_cam",
    "recording_status": "▶️ Recording",
    "connection_status": "✅ Connected"
}

// Health Check Response
{
    "status": "healthy",
    "database": "connected",
    "cameras_count": 3
}
```

## Security Features

### 1. Credential Encryption
- **Algorithm**: Fernet (symmetric encryption)
- **Key Storage**: Environment variable `CAMERA_ENCRYPTION_KEY`
- **Scope**: Username and password fields
- **Auto-generation**: Development key generated if not set

### 2. API Security
- **CORS**: Configured for frontend access
- **Validation**: Pydantic models for input validation
- **Error Handling**: Sensitive information not exposed
- **SQL Injection**: Protected by SQLAlchemy ORM

### 3. Best Practices
- Passwords never returned in API responses
- Encryption keys stored securely (production)
- Database credentials separate from camera credentials
- Audit trail through timestamps

## Migration Guide

### From Hardcoded to Database

1. **Run Migration Script**:
```bash
./venv/bin/python3 migrate_to_new_camera_schema.py
```

2. **Update API Server**:
```python
# In api/main.py lifespan function
await init_camera_api()  # Initialize database
```

3. **Include v2 Router**:
```python
# In api/main.py
from api.camera_endpoints import router as camera_router
app.include_router(camera_router, prefix="/v2")
```

### Default Cameras Migrated
- `camera_946701d3`: Reolink Main Entrance (10.0.0.181)
- `camera_entrance_cam`: Entrance Security Camera (10.0.0.182)
- `camera_parking_cam`: Parking Lot Camera (192.168.1.100)

## Integration Instructions

### 1. Backend Integration
```python
# Import camera service
from database.camera_service import CameraService
from database.service import DatabaseService

# Initialize
db_service = DatabaseService()
await db_service.init_db()
camera_service = CameraService(db_service)

# Use in your code
cameras = await camera_service.get_all_cameras()
status = await camera_service.get_cameras_status()
```

### 2. Frontend Integration
The frontend is already configured with:
- v2 API endpoints in `app.config.js`
- Fallback logic in `CamerasPage.js`
- 8-field standard formatting

### 3. Recording Service Integration (Pending)
```python
# Replace hardcoded cameras with database query
async def load_cameras():
    cameras = await camera_service.get_all_cameras()
    for camera in cameras:
        # Initialize camera from database
        connection = camera['current_connection']
        rtsp_url = build_rtsp_url(connection)
        # ... initialize recording
```

## Next Steps

### High Priority
1. **Update Recording Service** (`recording_service/main.py`)
   - Replace hardcoded camera loading
   - Use database for camera configuration
   - Update status in real-time

### Medium Priority
2. **Camera Management UI**
   - Add camera form in settings page
   - Edit/delete functionality
   - Connection testing UI

3. **Advanced Features**
   - Batch camera import
   - Camera templates
   - Group management

### Low Priority
4. **Monitoring & Analytics**
   - Connection history tracking
   - Recording statistics
   - Performance metrics

## Troubleshooting

### Common Issues

1. **Encryption Key Error**
   - Set `CAMERA_ENCRYPTION_KEY` environment variable
   - Or let system generate one (development only)

2. **Database Connection Error**
   - Ensure SQLite file permissions
   - Check `data/` directory exists

3. **API Not Found (404)**
   - Verify v2 router is included
   - Check API server initialization

4. **Status Not Updating**
   - Verify camera_id matches database
   - Check last_heartbeat timestamp

## Conclusion

The database-driven camera management system successfully replaces hardcoded configurations with a flexible, secure, and scalable architecture. The implementation provides:

- ✅ Dynamic camera management without code changes
- ✅ Encrypted credential storage
- ✅ Real-time status updates
- ✅ RESTful API with comprehensive endpoints
- ✅ 8-field standardized display format
- ✅ Frontend integration with fallback support

The system is production-ready and awaits integration with the recording service to complete the migration from hardcoded to database-driven architecture.