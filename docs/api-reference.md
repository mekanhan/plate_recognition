# License Plate Recognition System - Complete API Reference

This document provides a comprehensive overview of all available APIs in the LPR system.

## Service Overview

The system consists of two main services:
- **Main API Service** (Port 8001) - Core detection, camera management, analytics
- **Recording Service** (Port 8002) - 24/7 video recording and playback

## Main API Service - Port 8001

### 🔐 Authentication & Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | User login |
| `GET` | `/api/auth/me` | Get current user info |
| `GET` | `/api/auth/permissions` | Get current user permissions |
| `POST` | `/api/auth/check-permission` | Check specific permission |
| `GET` | `/api/auth/health` | Auth service health |
| `GET` | `/api/users/` | List all users |
| `POST` | `/api/users/` | Create new user |
| `GET` | `/api/users/{username}` | Get user details |
| `PUT` | `/api/users/{username}` | Update user |
| `DELETE` | `/api/users/{username}` | Delete user |
| `POST` | `/api/users/{username}/change-password` | Change user password |

### 📹 Camera Management (Legacy API)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/cameras` | Get all cameras |
| `POST` | `/api/cameras` | Create new camera |
| `GET` | `/api/cameras/{camera_id}` | Get camera details |
| `PUT` | `/api/cameras/{camera_id}` | Update camera |
| `DELETE` | `/api/cameras/{camera_id}` | Delete camera |
| `POST` | `/api/cameras/{camera_id}/test` | Test camera connection |
| `POST` | `/api/cameras/{camera_id}/start` | Start camera recording |
| `POST` | `/api/cameras/{camera_id}/stop` | Stop camera recording |
| `POST` | `/api/cameras/{camera_id}/restart` | Restart camera |
| `GET` | `/api/cameras/{camera_id}/snapshot` | Get camera snapshot |
| `GET` | `/api/cameras/{camera_id}/health` | Get camera health status |
| `GET` | `/api/cameras/{camera_id}/diagnostics` | Get camera diagnostics |
| `POST` | `/api/cameras/{camera_id}/open-vlc` | Get VLC stream URL |
| `GET` | `/api/cameras/{camera_id}/recording/quality` | Get recording quality |
| `POST` | `/api/cameras/{camera_id}/recording/quality` | Set recording quality |
| `GET` | `/api/cameras/health/summary` | Get all cameras health summary |
| `GET` | `/api/cameras/health/detailed` | Get detailed health status |
| `POST` | `/api/cameras/restart/all` | Restart all cameras |
| `POST` | `/api/cameras/test` | Test camera connection |
| `POST` | `/api/cameras/test-all-paths` | Test all camera stream paths |

### 📹 Camera Management (V2 API)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v2/api/cameras` | Get all cameras |
| `POST` | `/v2/api/cameras` | Create new camera |
| `GET` | `/v2/api/cameras/{camera_id}` | Get camera details |
| `PUT` | `/v2/api/cameras/{camera_id}` | Update camera |
| `DELETE` | `/v2/api/cameras/{camera_id}` | Delete camera |
| `GET` | `/v2/api/cameras/status` | Get all cameras status |
| `GET` | `/v2/api/cameras/{camera_id}/status` | Get camera status |
| `PUT` | `/v2/api/cameras/{camera_id}/status` | Update camera status |
| `POST` | `/v2/api/cameras/{camera_id}/start` | Start recording |
| `POST` | `/v2/api/cameras/{camera_id}/stop` | Stop recording |
| `POST` | `/v2/api/cameras/{camera_id}/restart` | Restart camera connection |
| `GET` | `/v2/api/cameras/{camera_id}/settings` | Get camera settings |
| `PUT` | `/v2/api/cameras/{camera_id}/settings` | Update camera settings |

### 🎯 Detection Management (Legacy)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/detections/recent` | Get recent detections |
| `GET` | `/api/detections/search` | Search detections |
| `GET` | `/api/detections/{detection_id}` | Get detection details |
| `GET` | `/api/detections/similar/{plate_text}` | Get similar plates |
| `GET` | `/api/detections/history/{plate_text}` | Get plate history |
| `GET` | `/api/detections/stats` | Get detection statistics |
| `GET` | `/api/detections/{detection_id}/quality` | Get detection quality details |

### 🎯 Universal Detection Management (V2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v2/object-types` | Get available object types |
| `GET` | `/api/v2/detections` | Search detections |
| `POST` | `/api/v2/detections/search` | Smart search detections |
| `GET` | `/api/v2/detections/{detection_id}` | Get detection details |
| `PUT` | `/api/v2/detections/{detection_id}` | Update detection |
| `GET` | `/api/v2/statistics` | Get detection statistics |

### 📊 Analytics & Reporting

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics/overview` | Get analytics overview |
| `GET` | `/api/analytics/dashboard` | Get dashboard data |
| `GET` | `/api/analytics/cameras` | Get camera analytics |
| `GET` | `/api/analytics/plates` | Get plate analytics |
| `GET` | `/api/analytics/trends` | Get temporal trends |
| `GET` | `/api/analytics/insights` | Get automated insights |
| `GET` | `/api/analytics/performance` | Get system performance |
| `GET` | `/api/analytics/comprehensive-report` | Generate comprehensive report |
| `GET` | `/api/analytics/charts/{chart_type}` | Generate charts |
| `POST` | `/api/analytics/reports/generate` | Generate custom report |
| `GET` | `/api/analytics/export/csv` | Export analytics to CSV |

### 🖥️ System Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Basic health check |
| `GET` | `/api/system/health` | Get system health |
| `GET` | `/api/monitoring/health` | Basic health monitoring |
| `GET` | `/api/monitoring/health/detailed` | Detailed health monitoring |
| `GET` | `/api/monitoring/health/summary` | Health summary |
| `POST` | `/api/monitoring/health/check/{check_name}` | Run specific health check |
| `GET` | `/api/monitoring/alerts` | Get system alerts |
| `GET` | `/api/monitoring/metrics` | Get Prometheus metrics |
| `POST` | `/api/monitoring/metrics/update` | Update metrics |
| `GET` | `/api/monitoring/performance/overview` | Performance overview |
| `GET` | `/api/monitoring/system/stats` | System statistics |

### 💾 Storage Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/storage/stats` | Get storage statistics |
| `POST` | `/api/storage/cleanup` | Trigger storage cleanup |
| `POST` | `/api/storage/emergency-cleanup` | Emergency cleanup |

### 🎛️ Quality Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/quality/metrics` | Get quality metrics |
| `GET` | `/api/quality/thresholds` | Get quality thresholds |
| `POST` | `/api/quality/filter` | Filter detections by quality |

### ⚙️ Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config/features` | Get feature configuration |

### 🎬 Video Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/video/clip/{clip_id}` | Get video clip |

### 🌐 WebSocket

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ws/status` | WebSocket status |

---

## Recording Service - Port 8002

### 🎥 Recording Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check |
| `GET` | `/health/detailed` | Detailed health check |
| `GET` | `/recordings/status` | Get all recording status |
| `GET` | `/recordings/status/{camera_id}` | Get camera recording status |
| `POST` | `/recordings/cameras/{camera_id}/start` | Start camera recording |
| `POST` | `/recordings/cameras/{camera_id}/stop` | Stop camera recording |
| `POST` | `/recordings/reload` | Reload all cameras |
| `POST` | `/shutdown` | Graceful shutdown |

### 📅 Playback & Timeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/recordings/cameras/{camera_id}/calendar` | Get calendar data |
| `GET` | `/api/v1/recordings/cameras/{camera_id}/timeline` | Get timeline segments |
| `GET` | `/api/v1/recordings/cameras/{camera_id}/details` | Get recording details |
| `POST` | `/api/v1/recordings/cameras/{camera_id}/search` | Search segments |

### 🎞️ Video Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/recordings/stream/{segment_filename}` | Stream video segment |
| `OPTIONS` | `/api/v1/recordings/stream/{segment_filename}` | Stream video options |

### 💾 Recording Storage

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/storage/report` | Get storage report |
| `POST` | `/api/v1/storage/cleanup` | Trigger storage cleanup |

---

## API Examples

### Camera Management

#### Get All Cameras
```bash
curl http://localhost:8001/api/cameras
```

#### Create New Camera
```bash
curl -X POST http://localhost:8001/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Front Gate Camera",
    "ip_address": "192.168.1.100",
    "port": 80,
    "connection_type": "http",
    "stream_path": "/mjpeg"
  }'
```

#### Get Camera Snapshot
```bash
curl http://localhost:8001/api/cameras/entrance_cam/snapshot
```

### Detection Management

#### Get Recent Detections
```bash
curl "http://localhost:8001/api/detections/recent?limit=10"
```

#### Search Detections
```bash
curl "http://localhost:8001/api/detections/search?plate_text=ABC123&camera_id=entrance_cam"
```

#### Get Detection Statistics
```bash
curl http://localhost:8001/api/detections/stats
```

### Universal Detection API (V2)

#### Get Object Types
```bash
curl http://localhost:8001/api/v2/object-types
```

#### Get Detection Statistics
```bash
curl http://localhost:8001/api/v2/statistics
```

#### Search Universal Detections
```bash
curl "http://localhost:8001/api/v2/detections?object_types=vehicle&confidence=0.8"
```

### Recording Management

#### Get Recording Status
```bash
curl http://localhost:8002/recordings/status
```

#### Get Camera Calendar
```bash
curl http://localhost:8002/api/v1/recordings/cameras/entrance_cam/calendar?year=2025&month=8
```

#### Get Timeline Segments
```bash
curl http://localhost:8002/api/v1/recordings/cameras/entrance_cam/timeline?date=2025-08-15
```

#### Stream Video Segment
```bash
curl http://localhost:8002/api/v1/recordings/stream/camera_entrance_cam_20250815_120000_600.avi
```

### System Monitoring

#### System Health
```bash
curl http://localhost:8001/api/system/health
```

#### Storage Statistics
```bash
curl http://localhost:8001/api/storage/stats
```

#### Performance Metrics
```bash
curl http://localhost:8001/api/monitoring/performance/overview
```

---

## Feature Flags

The system uses feature flags to control API availability:

```json
{
  "api_features": {
    "universal_detection_endpoints": true,
    "legacy_detection_endpoints": true
  }
}
```

- **universal_detection_endpoints**: Controls `/api/v2/*` detection endpoints
- **legacy_detection_endpoints**: Controls `/api/detections/*` endpoints

---

## Authentication

Most endpoints require authentication. Include JWT token in headers:

```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" http://localhost:8001/api/cameras
```

Get token via login:
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

---

## Service URLs

- **Frontend**: http://localhost:8080/
- **Main API Docs**: http://localhost:8001/docs
- **Recording API Docs**: http://localhost:8002/docs

---

## Total API Count

- **Main API Service**: 81 endpoints
- **Recording Service**: 16 endpoints
- **Total**: **97 API endpoints**

This comprehensive API set provides complete control over the license plate recognition system, from camera management to analytics and reporting.