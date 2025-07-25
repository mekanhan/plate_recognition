# API Specifications

**Date:** 2025-01-24  
**Version:** 1.0  
**Component:** Stream Feature API Documentation

## API Overview

The streaming API provides RESTful endpoints for stream management and WebSocket connections for real-time data streaming. All endpoints maintain consistency with the existing camera management API structure.

## REST API Endpoints

### 1. Video Streaming Endpoints

#### Get Camera Video Stream
```http
GET /stream/video/{camera_id}
```

**Description**: Serves live video stream from specified camera as MJPEG.

**Parameters**:
- `camera_id` (path, required): Integer ID of the configured camera

**Headers**:
- `Accept`: `multipart/x-mixed-replace` (optional, for explicit MJPEG support)

**Response**:
- **Content-Type**: `multipart/x-mixed-replace; boundary=frame`
- **Status**: `200 OK` for successful stream
- **Body**: Continuous MJPEG stream

**Example**:
```bash
curl -X GET "http://localhost:8000/stream/video/3" \
  -H "Accept: multipart/x-mixed-replace"
```

**Error Responses**:
```json
# Camera not found
{
  "status_code": 404,
  "detail": "Camera with ID 3 not found"
}

# Camera offline
{
  "status_code": 503,
  "detail": "Camera is currently offline"
}

# Stream initialization failed
{
  "status_code": 500,
  "detail": "Failed to initialize video stream"
}
```

#### Get Stream Thumbnail
```http
GET /stream/thumbnail/{camera_id}
```

**Description**: Returns current frame from camera as static JPEG image.

**Parameters**:
- `camera_id` (path, required): Integer ID of the configured camera
- `width` (query, optional): Thumbnail width in pixels (default: 320)
- `height` (query, optional): Thumbnail height in pixels (default: 240)

**Response**:
- **Content-Type**: `image/jpeg`
- **Status**: `200 OK`

**Example**:
```bash
curl -X GET "http://localhost:8000/stream/thumbnail/3?width=640&height=480" \
  --output camera_thumbnail.jpg
```

### 2. Stream Management Endpoints

#### Start Camera Stream
```http
POST /api/v1/streams/{camera_id}/start
```

**Description**: Initialize streaming session for specified camera.

**Parameters**:
- `camera_id` (path, required): Integer ID of the configured camera

**Request Body**:
```json
{
  "quality": "high",           // "low", "medium", "high"
  "detection_enabled": true,   // Enable/disable detection processing
  "confidence_threshold": 0.7, // Detection confidence threshold (0.1-0.9)
  "max_fps": 30               // Maximum frames per second
}
```

**Response**:
```json
{
  "session_id": "stream_3_20250124_103045",
  "camera_id": 3,
  "status": "active",
  "started_at": "2025-01-24T10:30:45.123Z",
  "settings": {
    "quality": "high",
    "detection_enabled": true,
    "confidence_threshold": 0.7,
    "max_fps": 30
  }
}
```

#### Stop Camera Stream
```http
POST /api/v1/streams/{camera_id}/stop
```

**Description**: Terminate active streaming session.

**Response**:
```json
{
  "session_id": "stream_3_20250124_103045",
  "camera_id": 3,
  "status": "stopped",
  "started_at": "2025-01-24T10:30:45.123Z",
  "ended_at": "2025-01-24T10:45:22.456Z",
  "statistics": {
    "total_frames": 27000,
    "total_detections": 15,
    "avg_fps": 29.8,
    "duration_seconds": 922
  }
}
```

#### Get Stream Status
```http
GET /api/v1/streams/{camera_id}/status
```

**Description**: Retrieve current streaming session information.

**Response**:
```json
{
  "camera_id": 3,
  "camera_name": "Test Camera 1",
  "status": "active",           // "active", "stopped", "error", "connecting"
  "session_id": "stream_3_20250124_103045",
  "started_at": "2025-01-24T10:30:45.123Z",
  "current_fps": 29.5,
  "total_frames": 15420,
  "total_detections": 8,
  "last_detection_at": "2025-01-24T10:42:15.789Z",
  "settings": {
    "quality": "high",
    "detection_enabled": true,
    "confidence_threshold": 0.7,
    "max_fps": 30
  },
  "performance": {
    "cpu_usage_percent": 25.4,
    "memory_usage_mb": 156.7,
    "detection_avg_time_ms": 145
  }
}
```

#### List Active Streams
```http
GET /api/v1/streams/
```

**Description**: Get list of all active streaming sessions.

**Query Parameters**:
- `status` (optional): Filter by status ("active", "stopped", "error")
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "streams": [
    {
      "camera_id": 3,
      "camera_name": "Test Camera 1",
      "status": "active",
      "session_id": "stream_3_20250124_103045",
      "started_at": "2025-01-24T10:30:45.123Z",
      "current_fps": 29.5,
      "total_detections": 8
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### 3. Detection Data Endpoints

#### Get Recent Detections
```http
GET /api/v1/detections/recent
```

**Description**: Retrieve recent license plate detections across all cameras.

**Query Parameters**:
- `camera_id` (optional): Filter by specific camera
- `limit` (optional): Number of results (default: 20, max: 100)
- `since` (optional): ISO timestamp to filter results after
- `confidence_min` (optional): Minimum confidence threshold (0.0-1.0)

**Response**:
```json
{
  "detections": [
    {
      "id": 1547,
      "camera_id": 3,
      "camera_name": "Test Camera 1",
      "timestamp": "2025-01-24T10:42:15.789Z",
      "bbox": [125, 200, 275, 240],
      "confidence": 0.87,
      "plate_text": "ABC123",
      "processing_time_ms": 145,
      "image_url": "/api/v1/detections/1547/image",
      "enhanced_image_url": "/api/v1/detections/1547/enhanced"
    }
  ],
  "total": 1,
  "camera_filters": ["Test Camera 1"],
  "timestamp_range": {
    "earliest": "2025-01-24T10:42:15.789Z",
    "latest": "2025-01-24T10:42:15.789Z"
  }
}
```

#### Get Detection Image
```http
GET /api/v1/detections/{detection_id}/image
```

**Description**: Retrieve original detection image.

**Parameters**:
- `detection_id` (path, required): Integer ID of the detection

**Response**:
- **Content-Type**: `image/jpeg`
- **Status**: `200 OK`
- **Headers**: `Content-Disposition: attachment; filename="detection_1547.jpg"`

#### Get Enhanced Detection Image
```http
GET /api/v1/detections/{detection_id}/enhanced
```

**Description**: Retrieve enhanced/cropped license plate image.

**Parameters**:
- `detection_id` (path, required): Integer ID of the detection

**Response**:
- **Content-Type**: `image/jpeg`
- **Status**: `200 OK`

## WebSocket API

### Connection Endpoint
```
ws://localhost:8000/ws/stream/{camera_id}
```

**Authentication**: JWT token via query parameter or header
```
ws://localhost:8000/ws/stream/3?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Message Types

#### 1. Client → Server Messages

##### Subscribe to Detection Events
```json
{
  "type": "subscribe",
  "events": ["detection", "system_status", "stream_stats"]
}
```

##### Update Stream Settings
```json
{
  "type": "update_settings",
  "settings": {
    "confidence_threshold": 0.8,
    "detection_enabled": false
  }
}
```

##### Request Current Status
```json
{
  "type": "get_status"
}
```

#### 2. Server → Client Messages

##### Detection Event
```json
{
  "type": "detection",
  "timestamp": "2025-01-24T10:42:15.789Z",
  "camera_id": 3,
  "detection": {
    "id": 1547,
    "bbox": [125, 200, 275, 240],
    "confidence": 0.87,
    "plate_text": "ABC123",
    "processing_time_ms": 145,
    "image_url": "/api/v1/detections/1547/image"
  }
}
```

##### System Status Update
```json
{
  "type": "system_status",
  "timestamp": "2025-01-24T10:42:20.123Z",
  "camera_id": 3,
  "status": {
    "streaming": true,
    "fps": 29.8,
    "cpu_usage": 24.5,
    "memory_usage_mb": 158.2,
    "detection_queue_size": 2,
    "last_frame_at": "2025-01-24T10:42:19.987Z"
  }
}
```

##### Stream Statistics
```json
{
  "type": "stream_stats",
  "timestamp": "2025-01-24T10:42:25.456Z",
  "camera_id": 3,
  "stats": {
    "session_duration_seconds": 715,
    "total_frames": 21447,
    "total_detections": 12,
    "avg_fps": 29.9,
    "detections_per_minute": 1.0,
    "avg_detection_confidence": 0.79
  }
}
```

##### Error Message
```json
{
  "type": "error",
  "timestamp": "2025-01-24T10:42:30.123Z",
  "error": {
    "code": "CAMERA_DISCONNECTED",
    "message": "Camera connection lost",
    "details": "Network timeout after 5 seconds",
    "recovery_action": "Attempting automatic reconnection"
  }
}
```

##### Connection Acknowledgment
```json
{
  "type": "connected",
  "timestamp": "2025-01-24T10:30:45.123Z",
  "camera_id": 3,
  "session_id": "ws_3_20250124_103045",
  "message": "WebSocket connection established"
}
```

## Error Handling

### HTTP Error Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 400 | Bad Request | Invalid parameters, malformed JSON |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Camera or detection not found |
| 409 | Conflict | Stream already active |
| 422 | Unprocessable Entity | Invalid configuration values |
| 503 | Service Unavailable | Camera offline, system overloaded |
| 500 | Internal Server Error | Unexpected system error |

### Error Response Format
```json
{
  "status_code": 404,
  "detail": "Camera with ID 3 not found",
  "error_code": "CAMERA_NOT_FOUND",
  "timestamp": "2025-01-24T10:42:35.789Z",
  "request_id": "req_abc123def456"
}
```

### WebSocket Error Handling
```json
{
  "type": "error",
  "error": {
    "code": "INVALID_MESSAGE",
    "message": "Unknown message type: invalid_type",
    "timestamp": "2025-01-24T10:42:40.123Z"
  }
}
```

## Rate Limiting

### HTTP Endpoints
- **Stream endpoints**: 10 requests per minute per IP
- **Detection queries**: 100 requests per minute per user
- **Management operations**: 20 requests per minute per user

### WebSocket Connections
- **Max connections per IP**: 5 concurrent connections
- **Message rate limit**: 50 messages per minute per connection
- **Bandwidth limit**: 10MB per minute per connection

## Authentication & Authorization

### JWT Token Structure
```json
{
  "sub": "user123",
  "username": "admin",
  "permissions": ["stream:view", "stream:manage", "detection:view"],
  "camera_access": [3, 4],  // Accessible camera IDs
  "exp": 1706097600,
  "iat": 1706094000
}
```

### Required Permissions
- **stream:view**: Access video streams and detection data
- **stream:manage**: Start/stop streams, modify settings
- **detection:view**: Access detection history and images
- **camera:admin**: Full camera management access

## API Versioning

### Version Strategy
- **Current Version**: `v1`
- **Backward Compatibility**: Maintained for at least 2 versions
- **Deprecation Notice**: 6 months advance notice for breaking changes

### Version Headers
```http
Accept: application/json; version=1
API-Version: 1
```

## SDK Examples

### Python Client Example
```python
import asyncio
import websockets
import json

async def stream_client():
    uri = "ws://localhost:8000/ws/stream/3?token=your_jwt_token"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to detection events
        await websocket.send(json.dumps({
            "type": "subscribe",
            "events": ["detection", "system_status"]
        }))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data['type']}")
            
            if data['type'] == 'detection':
                print(f"License plate: {data['detection']['plate_text']}")

asyncio.run(stream_client())
```

### JavaScript Client Example
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream/3?token=your_jwt_token');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'subscribe',
        events: ['detection', 'system_status']
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'detection') {
        console.log('New detection:', data.detection.plate_text);
        updateDetectionUI(data.detection);
    }
};
```

This API specification provides a comprehensive foundation for implementing robust, scalable streaming functionality with real-time detection capabilities.