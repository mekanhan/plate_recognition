# Before getting started
## The Problem:
    Your cameras are still hardcoded in api/main.py:
    pythoncameras = [
        CameraConfig(
            camera_id="entrance_cam",
            ip_address="10.0.0.181",
            username="admin",
            password="Mekus_1987",  # 😱 Hardcoded password!
            # ...
        )
    ]
    The code loads these hardcoded cameras, then saves them to the database - but it should be the opposite: load FROM the database!
    What needs to change:

    1. Remove hardcoded cameras from load_cameras()
    2. Load cameras from database instead:

    pythonasync def load_cameras():
        cameras = await db.get_all_cameras()
        for camera in cameras:
            # Load from DB, not hardcode

    3. Add API endpoints to manage cameras (create/update/delete)
    4. Create settings UI to add cameras through the web interface


# Camera Configuration Database Schema

## Database Tables for Camera Management

### 1. **cameras** Table
```sql
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., "camera_946701d3"
    name VARCHAR(100) NOT NULL,             -- e.g., "Reolink Main Entrance"
    location VARCHAR(200),                  -- e.g., "Entrance", "Parking Lot"
    status VARCHAR(20) DEFAULT 'active',    -- active, inactive, maintenance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. **camera_connections** Table
```sql
CREATE TABLE camera_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    protocol VARCHAR(10) NOT NULL,          -- RTSP, HTTP, HTTPS
    ip_address INET NOT NULL,               -- 10.0.0.181
    port INTEGER DEFAULT 554,               -- 554 for RTSP
    username VARCHAR(100),                  -- encrypted
    password VARCHAR(100),                  -- encrypted
    stream_path VARCHAR(200),               -- /h264/ch1/main/av_stream
    is_active BOOLEAN DEFAULT true,
    last_connected TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. **camera_recording_config** Table
```sql
CREATE TABLE camera_recording_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT false,
    recording_path VARCHAR(500),            -- /recordings/camera_946701d3/
    segment_duration INTEGER DEFAULT 600,   -- 10 minutes in seconds
    retention_days INTEGER DEFAULT 30,      -- How long to keep recordings
    video_codec VARCHAR(20) DEFAULT 'h264',
    audio_enabled BOOLEAN DEFAULT true,
    motion_detection BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. **camera_settings** Table (Flexible Key-Value)
```sql
CREATE TABLE camera_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,      -- e.g., "resolution", "fps", "quality"
    setting_value TEXT NOT NULL,            -- e.g., "1920x1080", "30", "high"
    setting_type VARCHAR(20),               -- string, integer, boolean, json
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(camera_id, setting_key)
);
```

### 5. **camera_status** Table (Real-time Status)
```sql
CREATE TABLE camera_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    recording_status VARCHAR(20) DEFAULT 'stopped',  -- recording, paused, stopped
    connection_status VARCHAR(20) DEFAULT 'disconnected', -- connected, disconnected, reconnecting
    ffmpeg_pid INTEGER,
    segments_created INTEGER DEFAULT 0,
    last_segment_time TIMESTAMP,
    storage_used_bytes BIGINT DEFAULT 0,
    recording_started_at TIMESTAMP,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(camera_id)
);
```

## Configuration Management Flow

### 1. **Adding a New Camera**
```python
# Backend API endpoint
@app.post("/api/cameras")
async def add_camera(camera_data: CameraCreate):
    # Create camera record
    camera = await db.cameras.create({
        "camera_id": generate_camera_id(),
        "name": camera_data.name,
        "location": camera_data.location
    })
    
    # Create connection config
    await db.camera_connections.create({
        "camera_id": camera.id,
        "protocol": camera_data.protocol,
        "ip_address": camera_data.ip_address,
        "port": camera_data.port,
        "username": encrypt(camera_data.username),
        "password": encrypt(camera_data.password),
        "stream_path": camera_data.stream_path
    })
    
    # Create recording config with defaults
    await db.camera_recording_config.create({
        "camera_id": camera.id,
        "enabled": False,
        "recording_path": f"/recordings/{camera.camera_id}/"
    })
    
    # Initialize status
    await db.camera_status.create({
        "camera_id": camera.id
    })
    
    return camera
```

### 2. **Bulk Status Endpoint Using Database**
```python
@app.get("/api/cameras/status")
async def get_all_cameras_status():
    # Single query with joins for efficiency
    query = """
        SELECT 
            c.camera_id,
            c.name,
            c.location,
            cc.protocol,
            cc.ip_address,
            cs.recording_status,
            cs.connection_status,
            cs.ffmpeg_pid,
            cs.segments_created,
            cs.last_segment_time,
            cs.storage_used_bytes,
            cs.recording_started_at
        FROM cameras c
        LEFT JOIN camera_connections cc ON c.id = cc.camera_id AND cc.is_active = true
        LEFT JOIN camera_status cs ON c.id = cs.camera_id
        WHERE c.status = 'active'
    """
    
    cameras = await db.fetch_all(query)
    
    # Format according to our 8-field standard
    return {
        "cameras": [format_camera_data(cam) for cam in cameras]
    }

def format_camera_data(cam):
    """Format camera data according to standardized fields"""
    return {
        "id": cam["camera_id"],
        "location": cam["location"] or "Unknown",
        "connection": f"{cam['protocol']} ({cam['ip_address']})" if cam["protocol"] else "Unknown",
        "recording_status": format_recording_status(cam["recording_status"]),
        "connection_status": format_connection_status(cam["connection_status"]),
        "ffmpeg_pid": str(cam["ffmpeg_pid"]) if cam["ffmpeg_pid"] else "None",
        "segments_created": format_segments(cam["segments_created"], cam["last_segment_time"]),
        "storage_used": format_bytes(cam["storage_used_bytes"]),
        "recording_uptime": format_uptime(cam["recording_started_at"])
    }
```

### 3. **Settings Management**
```python
# Store flexible settings
async def update_camera_setting(camera_id: str, key: str, value: Any):
    await db.camera_settings.upsert({
        "camera_id": camera_id,
        "setting_key": key,
        "setting_value": str(value),
        "setting_type": type(value).__name__
    })

# Retrieve all settings for a camera
async def get_camera_settings(camera_id: str):
    settings = await db.camera_settings.find_all(camera_id=camera_id)
    return {s.setting_key: parse_value(s.setting_value, s.setting_type) for s in settings}
```

## Migration Strategy

### Phase 1: Database Setup
```sql
-- Create all tables
-- Add indexes for performance
CREATE INDEX idx_camera_status_camera_id ON camera_status(camera_id);
CREATE INDEX idx_camera_connections_camera_id ON camera_connections(camera_id);
CREATE INDEX idx_cameras_camera_id ON cameras(camera_id);
```

### Phase 2: Seed Initial Data
```python
# Migrate existing hardcoded data
default_cameras = [
    {
        "camera_id": "camera_946701d3",
        "name": "Reolink Main Entrance",
        "location": "Entrance",
        "ip_address": "10.0.0.181",
        "protocol": "RTSP"
    },
    # ... other cameras
]

for cam in default_cameras:
    await migrate_camera_to_database(cam)
```

### Phase 3: Update Backend Services
- Recording Service reads from database
- Main API uses database for all camera data
- Remove all hardcoded camera configurations

## Benefits of Database Approach

### 1. **Dynamic Configuration**
- Add/remove cameras without code changes
- Update settings through UI
- No service restarts needed

### 2. **Centralized Management**
- Single source of truth
- Consistent data across services
- Easy backup and restore

### 3. **Scalability**
- Handles 10, 100, or 1000 cameras
- Efficient queries with indexes
- Distributed database options

### 4. **Security**
- Encrypted credentials
- Role-based access control
- Audit trails

### 5. **Real-time Updates**
- Status changes reflected immediately
- No cache invalidation issues
- Consistent across all clients

## API Endpoints for Camera Management

```yaml
Camera CRUD:
  POST   /api/cameras                 - Create new camera
  GET    /api/cameras                 - List all cameras
  GET    /api/cameras/{id}            - Get camera details
  PUT    /api/cameras/{id}            - Update camera
  DELETE /api/cameras/{id}            - Delete camera

Settings:
  GET    /api/cameras/{id}/settings   - Get all settings
  PUT    /api/cameras/{id}/settings   - Update settings
  
Status:
  GET    /api/cameras/status          - Bulk status (all cameras)
  GET    /api/cameras/{id}/status     - Single camera status
  
Actions:
  POST   /api/cameras/{id}/start      - Start recording
  POST   /api/cameras/{id}/stop       - Stop recording
  POST   /api/cameras/{id}/restart    - Restart camera connection
```

## Frontend Integration

```javascript
// Camera management service
class CameraService {
    async getAllCameras() {
        const response = await fetch('/api/cameras');
        return response.json();
    }
    
    async addCamera(cameraData) {
        const response = await fetch('/api/cameras', {
            method: 'POST',
            body: JSON.stringify(cameraData)
        });
        return response.json();
    }
    
    async updateCameraSettings(cameraId, settings) {
        const response = await fetch(`/api/cameras/${cameraId}/settings`, {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
        return response.json();
    }
}
```

This database-driven approach ensures your system is flexible, scalable, and maintainable!