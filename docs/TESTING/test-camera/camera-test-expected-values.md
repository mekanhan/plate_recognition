# Camera System Expected Test Values & Behaviors

## 1. Database Expected Values

### 1.1 Camera Table Structure
```sql
-- After creating a new camera
SELECT * FROM cameras WHERE camera_id = 'camera_abc123';

Expected Result:
├─ id: (UUID - auto-generated)
├─ camera_id: 'camera_abc123' (unique, generated)
├─ name: 'Main Entrance Camera'
├─ ip_address: '10.0.0.181'
├─ port: 554
├─ protocol: 'RTSP'
├─ stream_path: '/h264Preview_01_main'
├─ location: 'Main Entrance'
├─ status: 'active'
├─ created_at: '2024-01-XX 10:30:00'
├─ updated_at: '2024-01-XX 10:30:00'
└─ config: (JSON - see below)
```

### 1.2 Camera Config JSON Structure
```json
{
  "username": "encrypted_string_here",
  "password": "encrypted_string_here",
  "encryption_version": 1,
  "network": {
    "timeout": 10,
    "retry_count": 3
  },
  "stream": {
    "main_stream": "/h264Preview_01_main",
    "sub_stream": "/h264Preview_01_sub",
    "codec": "H264"
  },
  "recording": {
    "enabled": false,
    "segment_duration": 600,
    "retention_days": 30
  }
}
```

### 1.3 Camera Status Table (When Implemented)
```sql
Expected Values:
├─ camera_id: 'camera_abc123'
├─ recording_status: 'stopped' | 'recording' | 'paused'
├─ connection_status: 'connected' | 'disconnected' | 'error'
├─ ffmpeg_pid: NULL | 12345 (when recording)
├─ segments_created: 0 | 47 (increments during recording)
├─ last_segment_time: NULL | '2024-01-XX 11:47:30'
├─ storage_used_bytes: 0 | 1073741824 (in bytes)
├─ recording_started_at: NULL | '2024-01-XX 10:00:00'
├─ last_heartbeat: '2024-01-XX 10:35:00' (updates every 30s)
└─ error_message: NULL | 'Connection timeout'
```

## 2. Backend API Expected Responses

### 2.1 GET /v2/api/cameras/status
```json
{
  "cameras": [
    {
      "id": "camera_abc123",
      "location": "Main Entrance",          // Never null, defaults to "Unknown"
      "connection": "RTSP (10.0.0.181)",   // Format: "protocol (ip)"
      "recording_status": "⏹️ Stopped",     // With emoji indicator
      "connection_status": "✅ Connected",  // With status indicator
      "ffmpeg_pid": "None",                // "None" when not recording
      "segments_created": "None",          // "None" or "47 (last: 11:47:30 PM)"
      "storage_used": "0 B",               // Human readable: "0 B", "1.5 GB"
      "recording_uptime": "None"           // "None" or "2h 15m"
    }
  ],
  "timestamp": "2024-01-XX 10:35:00"
}
```

### 2.2 POST /v2/api/cameras (Create)
```json
// Request
{
  "name": "New Test Camera",
  "ip_address": "192.168.1.100",
  "port": 554,
  "protocol": "RTSP",
  "stream_path": "/stream1",
  "location": "Parking Lot",
  "username": "admin",
  "password": "secure123",
  "recording_enabled": true
}

// Expected Response (201 Created)
{
  "success": true,
  "camera": {
    "id": "camera_def456",
    "camera_id": "camera_def456",
    "name": "New Test Camera",
    "ip_address": "192.168.1.100",
    "location": "Parking Lot",
    "status": "active",
    "created_at": "2024-01-XX 10:40:00"
  }
}

// Expected Errors
400 Bad Request: {"detail": "Camera with this IP already exists"}
422 Validation Error: {"detail": [{"loc": ["body", "name"], "msg": "field required"}]}
500 Server Error: {"detail": "Failed to create camera: Connection test failed"}
```

### 2.3 PUT /v2/api/cameras/{camera_id} (Update)
```json
// Request (Partial Update)
{
  "name": "Updated Camera Name",
  "location": "New Location"
}

// Expected Response (200 OK)
{
  "success": true,
  "camera": {
    "id": "camera_abc123",
    "name": "Updated Camera Name",
    "location": "New Location",
    "updated_at": "2024-01-XX 11:00:00"
    // Other fields unchanged
  }
}

// Expected Errors
404 Not Found: {"detail": "Camera camera_xyz999 not found"}
400 Bad Request: {"detail": "No valid update fields provided"}
```

### 2.4 POST /v2/api/cameras/{camera_id}/start
```json
// Expected Response (200 OK)
{
  "success": true,
  "message": "Recording started for camera camera_abc123",
  "timestamp": "2024-01-XX 11:00:00"
}

// Database Side Effect: recording_status → "recording"
// Expected Errors
404 Not Found: {"detail": "Camera not found"}
400 Bad Request: {"detail": "Camera is offline"}
409 Conflict: {"detail": "Recording already in progress"}
```

### 2.5 Connection Test Response
```json
// POST /v2/api/cameras/test-connection
{
  "ip_address": "10.0.0.181",
  "port": 554,
  "username": "admin",
  "password": "password",
  "stream_path": "/h264Preview_01_main"
}

// Success Response (200 OK)
{
  "success": true,
  "message": "Connection successful",
  "details": {
    "rtsp_url": "rtsp://10.0.0.181:554/h264Preview_01_main",
    "frame_captured": true,
    "latency_ms": 145
  }
}

// Failure Response (200 OK - not 400)
{
  "success": false,
  "message": "Connection failed",
  "error": "Authentication failed",
  "details": {
    "attempted_url": "rtsp://10.0.0.181:554/h264Preview_01_main",
    "error_code": "AUTH_FAILED"
  }
}
```

## 3. Frontend Expected Behaviors

### 3.1 Camera List Display
```javascript
// Expected DOM Structure for Each Camera
<div class="camera-card" data-camera-id="camera_abc123">
  <div class="camera-status-indicator connected"></div>
  <h3>Main Entrance Camera</h3>
  
  <div class="camera-info">
    <div class="info-row">
      <span class="label">Location:</span>
      <span class="value">Main Entrance</span>
    </div>
    <div class="info-row">
      <span class="label">Connection:</span>
      <span class="value">RTSP (10.0.0.181)</span>
    </div>
    <!-- All 8 fields displayed -->
  </div>
</div>

// Expected Status Classes
.connected { background: #4CAF50; }    // Green
.disconnected { background: #f44336; } // Red
.recording { background: #2196F3; }    // Blue
.error { background: #ff9800; }        // Orange
```

### 3.2 Add Camera Modal Behavior
```javascript
// Form Validation Expected Results
{
  name: {
    required: true,
    minLength: 3,
    maxLength: 100,
    error: "Camera name is required (3-100 characters)"
  },
  ip_address: {
    required: true,
    pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/,
    error: "Invalid IP address format"
  },
  port: {
    required: true,
    min: 1,
    max: 65535,
    default: 554,
    error: "Port must be between 1-65535"
  }
}

// Connection Test Button States
1. Initial: "Test Connection" (enabled)
2. Testing: "Testing..." (disabled, spinner)
3. Success: "✓ Connected" (green, enabled)
4. Failed: "✗ Failed" (red, enabled)

// Save Button Behavior
- Disabled until all required fields filled
- Disabled during connection test
- Shows spinner during save
- Closes modal on success
- Shows error message on failure
```

### 3.3 Camera Actions Expected Results
```javascript
// Start Recording
Expected Flow:
1. Button clicked → Disabled + Loading state
2. API call to /v2/api/cameras/{id}/start
3. Success → Button changes to "Stop Recording"
4. Status updates → Recording indicator appears
5. Recording time starts incrementing

// Edit Camera
Expected Flow:
1. Edit icon clicked → Modal opens with pre-filled data
2. Fields editable except camera_id
3. Save → Updates database and refreshes list
4. Camera card updates without page reload

// Delete Camera
Expected Flow:
1. Delete icon clicked → Confirmation modal
2. "Are you sure?" with camera name
3. Confirm → API DELETE call
4. Success → Camera removed from DOM
5. If recording → Stop recording first
```

### 3.4 Real-time Updates
```javascript
// Expected Update Intervals
- Camera list refresh: Every 30 seconds
- Recording status: Every 5 seconds (when recording)
- Connection status: Every 30 seconds
- After user action: Immediate (within 1 second)

// Expected Loading States
1. Initial page load: Skeleton cards
2. Refresh: Subtle spinner, no layout shift
3. Action processing: Button disabled + spinner
4. Error state: Red banner with retry button
```

## 4. Integration Expected Behaviors

### 4.1 Service Communication Flow
```
User adds camera → Frontend → v2 API → Database
                                    ↓
                              Camera Service
                                    ↓
                            Recording Service (TODO)
                                    ↓
                              Status Updates
                                    ↓
                              Frontend Display
```

### 4.2 Error Recovery Behaviors
```javascript
// Network Error
Expected: Automatic retry after 5 seconds, max 3 attempts
Display: "Connection error. Retrying... (attempt 2/3)"

// Service Unavailable
Expected: Fallback to cached data if available
Display: "Some features unavailable. Last updated: 5 min ago"

// Database Error
Expected: Read operations continue from cache
Display: "Unable to save changes. Please try again."
```

### 4.3 Data Consistency Rules
```
1. Camera ID: Once created, never changes
2. Status Updates: Last write wins
3. Recording State: Must match FFmpeg process
4. Storage Calculation: Updated every segment
5. Connection Status: Based on last successful frame
```

## 5. Performance Expected Values

### 5.1 Response Times
```
API Endpoints:
- GET /cameras/status: < 200ms
- POST /cameras: < 1000ms (includes connection test)
- Connection test: < 5000ms timeout
- Start recording: < 2000ms

Frontend Actions:
- Page load: < 2 seconds
- Modal open: < 100ms
- List refresh: < 500ms
- Status update: < 300ms
```

### 5.2 Resource Usage
```
With 10 cameras:
- Database size: < 10 MB
- API memory: < 500 MB
- CPU usage: < 20% average
- Network bandwidth: < 1 Mbps (status updates)
```

## 6. Security Expected Behaviors

### 6.1 Credential Handling
```
Storage: Encrypted with Fernet
Transit: HTTPS only (production)
Display: Never show passwords
Logs: No credentials in logs
Errors: No credentials in error messages
```

### 6.2 Input Validation
```
SQL Injection: Prevented by ORM
XSS: HTML escaped in frontend
Path Traversal: Validated file paths
Rate Limiting: 100 requests/minute (TODO)
```

## 7. Edge Cases Expected Behaviors

### 7.1 Boundary Conditions
```
Empty Database:
- Show "No cameras configured" message
- Display "Add Camera" button prominently

Maximum Cameras (100+):
- Pagination appears after 20 cameras
- Search/filter becomes available
- Performance remains acceptable

Long Names/Locations:
- Truncate with ellipsis after 50 chars
- Show full text on hover

Invalid Data:
- Skip invalid records
- Log errors but continue operation
- Show partial data with error indicator
```

### 7.2 Concurrent Operations
```
Same Camera Modified by Multiple Users:
- Last update wins
- No locking mechanism
- Frontend refreshes show latest

Recording Started While Deleting:
- Delete blocked with message
- Must stop recording first

Service Restart During Operation:
- Operations may fail
- Frontend retries automatically
- User notified of temporary issue
```