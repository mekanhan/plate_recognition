# API Test Scenarios - License Plate Recognition System

## Overview

This document contains comprehensive API test scenarios for all backend endpoints of the LPR system. These scenarios are designed to be implemented in the Java automation framework using REST Assured, TestNG, and data-driven testing approaches.

## API Test Categories

### 1. Detection API Tests (Router: `/api/detect`)
### 2. Stream API Tests (Router: `/api/stream`)  
### 3. Results API Tests (Router: `/api/results`)
### 4. System API Tests (Router: `/api/system`)
### 5. Headless API Tests (Router: `/api/headless`)
### 6. Video API Tests (Router: `/api/video`)
### 7. Authentication & Authorization Tests
### 8. Error Handling & Edge Cases

---

## 1. Detection API Tests

### DET-API-001: Live Camera Detection
**Endpoint**: `POST /api/detect/camera`
**Feature**: Real-time camera detection
**Scenario**: Verify live detection from camera source

**Request**:
```json
{
  "camera_id": "camera_001",
  "settings": {
    "confidence_threshold": 0.7,
    "save_results": true
  }
}
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "detections": [
    {
      "license_plate": "ABC123",
      "confidence": 0.85,
      "bbox": [100, 200, 300, 250],
      "timestamp": "2024-01-15T10:30:00Z",
      "camera_id": "camera_001"
    }
  ],
  "processing_time": 0.15,
  "session_id": "session_123"
}
```

**Test Cases**:
- Valid camera ID with default settings
- Valid camera ID with custom confidence threshold
- Invalid camera ID (should return 404)
- Malformed request body (should return 400)
- Camera not available (should return service unavailable)

**Priority**: Critical
**Automation**: Yes

### DET-API-002: Image Upload Detection
**Endpoint**: `POST /api/detect/upload`
**Feature**: Image file detection
**Scenario**: Verify detection from uploaded image files

**Request**: Multipart form with image file
```
Content-Type: multipart/form-data
file: [image file]
settings: {"confidence_threshold": 0.6}
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "filename": "test_image.jpg",
  "detections": [
    {
      "license_plate": "XYZ789",
      "confidence": 0.92,
      "bbox": [50, 75, 200, 125],
      "enhanced_image_path": "/data/enhanced_plates/enhanced_123.jpg"
    }
  ],
  "processing_time": 0.08
}
```

**Test Cases**:
- Valid JPEG image with license plate
- Valid PNG image with multiple plates
- Invalid image format (should return 400)
- Corrupted image file (should return 400)
- Image too large (should return 413)
- Image with no license plates (should return empty detections)

**Priority**: High
**Automation**: Yes

### DET-API-003: Batch Image Detection
**Endpoint**: `POST /api/detect/batch`
**Feature**: Multiple image detection
**Scenario**: Verify batch processing of multiple images

**Request**: Multipart form with multiple files
```
Content-Type: multipart/form-data
files: [image1.jpg, image2.jpg, image3.jpg]
settings: {"confidence_threshold": 0.7, "parallel_processing": true}
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "batch_id": "batch_456",
  "total_files": 3,
  "processed_files": 3,
  "failed_files": 0,
  "results": [
    {
      "filename": "image1.jpg",
      "detections": [...],
      "status": "success"
    }
  ],
  "total_processing_time": 0.45
}
```

**Test Cases**:
- Multiple valid images
- Mix of valid and invalid images
- Empty batch (should return 400)
- Batch size exceeding limit
- Concurrent batch requests

**Priority**: Medium
**Automation**: Yes

### DET-API-004: Detection Status Check
**Endpoint**: `GET /api/detect/status/{session_id}`
**Feature**: Detection status monitoring
**Scenario**: Verify detection status tracking

**Request**: `GET /api/detect/status/session_123`

**Expected Response** (200 OK):
```json
{
  "session_id": "session_123",
  "status": "processing",
  "progress": 0.75,
  "started_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:32:00Z",
  "current_operation": "license_plate_recognition"
}
```

**Test Cases**:
- Valid session ID in different states (processing, completed, failed)
- Invalid session ID (should return 404)
- Expired session ID (should return 410)

**Priority**: Medium
**Automation**: Yes

---

## 2. Stream API Tests

### STREAM-API-001: WebSocket Connection Test
**Endpoint**: `WebSocket /ws/stream`
**Feature**: Real-time streaming connection
**Scenario**: Verify WebSocket connection and message handling

**Connection**: `ws://localhost:8001/ws/stream`

**Expected Messages**:
```json
{
  "type": "detection_update",
  "data": {
    "detections": [...],
    "timestamp": "2024-01-15T10:30:00Z",
    "camera_id": "camera_001"
  }
}
```

**Test Cases**:
- Successful WebSocket connection
- Message reception and parsing
- Connection handling with multiple clients
- Automatic reconnection on disconnect
- Message rate limiting

**Priority**: High
**Automation**: Partial (connection testing)

### STREAM-API-002: Stream Configuration
**Endpoint**: `POST /api/stream/config`
**Feature**: Stream configuration management
**Scenario**: Verify stream settings configuration

**Request**:
```json
{
  "camera_id": "camera_001",
  "stream_settings": {
    "resolution": "1920x1080",
    "fps": 30,
    "quality": "high",
    "detection_overlay": true
  }
}
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "camera_id": "camera_001",
  "applied_settings": {
    "resolution": "1920x1080",
    "fps": 30,
    "quality": "high",
    "detection_overlay": true
  },
  "message": "Stream configuration updated successfully"
}
```

**Test Cases**:
- Valid configuration parameters
- Invalid resolution format
- Unsupported FPS values
- Missing required parameters
- Camera not available

**Priority**: High
**Automation**: Yes

---

## 3. Results API Tests

### RESULTS-API-001: Get Detection Results
**Endpoint**: `GET /api/results`
**Feature**: Detection results retrieval
**Scenario**: Verify results retrieval with pagination and filtering

**Request**: `GET /api/results?page=1&limit=10&start_date=2024-01-01&end_date=2024-01-31`

**Expected Response** (200 OK):
```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "license_plate": "ABC123",
      "confidence": 0.85,
      "timestamp": "2024-01-15T10:30:00Z",
      "camera_id": "camera_001",
      "image_path": "/data/license_plates/plate_001.jpg",
      "bbox": [100, 200, 300, 250]
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_results": 47,
    "per_page": 10
  },
  "filters_applied": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
```

**Test Cases**:
- Default results retrieval (no filters)
- Date range filtering
- License plate text search (exact match)
- License plate text search (fuzzy match)
- Camera ID filtering
- Confidence threshold filtering
- Pagination with different page sizes
- Invalid date formats
- Page number out of range

**Priority**: High
**Automation**: Yes

### RESULTS-API-002: Search Results
**Endpoint**: `POST /api/results/search`
**Feature**: Advanced search functionality
**Scenario**: Verify advanced search capabilities

**Request**:
```json
{
  "query": {
    "license_plate": "ABC*",
    "confidence_min": 0.7,
    "date_range": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "camera_ids": ["camera_001", "camera_002"],
    "fuzzy_search": true
  },
  "sort": {
    "field": "timestamp",
    "order": "desc"
  },
  "pagination": {
    "page": 1,
    "limit": 20
  }
}
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "results": [...],
  "search_metadata": {
    "query_time": 0.15,
    "total_matches": 23,
    "fuzzy_matches": 5
  },
  "pagination": {...}
}
```

**Test Cases**:
- Complex search queries with multiple filters
- Wildcard search patterns
- Fuzzy search with similarity thresholds
- Empty search results
- Invalid search parameters
- Search performance with large datasets

**Priority**: High
**Automation**: Yes

### RESULTS-API-003: Export Results
**Endpoint**: `POST /api/results/export`
**Feature**: Results export functionality
**Scenario**: Verify CSV export of detection results

**Request**:
```json
{
  "format": "csv",
  "filters": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "include_images": false
}
```

**Expected Response** (200 OK):
```
Content-Type: text/csv
Content-Disposition: attachment; filename="detection_results_20240115.csv"

id,license_plate,confidence,timestamp,camera_id,image_path
1,ABC123,0.85,2024-01-15T10:30:00Z,camera_001,/data/license_plates/plate_001.jpg
```

**Test Cases**:
- CSV export with different date ranges
- JSON export format
- Export with image inclusion
- Export with no results
- Large dataset export (performance test)
- Invalid export format

**Priority**: Medium
**Automation**: Yes

### RESULTS-API-004: Delete Results
**Endpoint**: `DELETE /api/results/{result_id}`
**Feature**: Result deletion
**Scenario**: Verify individual result deletion

**Request**: `DELETE /api/results/123`

**Expected Response** (200 OK):
```json
{
  "success": true,
  "message": "Detection result deleted successfully",
  "deleted_id": 123
}
```

**Test Cases**:
- Valid result ID deletion
- Invalid result ID (should return 404)
- Already deleted result (should return 410)
- Bulk deletion endpoint testing

**Priority**: Medium
**Automation**: Yes

---

## 4. System API Tests

### SYS-API-001: Health Check
**Endpoint**: `GET /api/system/health`
**Feature**: System health monitoring
**Scenario**: Verify system health status reporting

**Request**: `GET /api/system/health`

**Expected Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "response_time": 0.05
    },
    "camera_service": {
      "status": "healthy",
      "active_cameras": 2
    },
    "detection_service": {
      "status": "healthy",
      "model_loaded": true
    }
  },
  "system_info": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

**Test Cases**:
- Healthy system status
- System with service failures
- High resource usage scenarios
- Health check during high load

**Priority**: High
**Automation**: Yes

### SYS-API-002: System Metrics
**Endpoint**: `GET /api/system/metrics`
**Feature**: Performance metrics
**Scenario**: Verify system performance metrics

**Request**: `GET /api/system/metrics?period=1h`

**Expected Response** (200 OK):
```json
{
  "success": true,
  "period": "1h",
  "metrics": {
    "detections_processed": 1250,
    "average_processing_time": 0.12,
    "detection_accuracy": 0.94,
    "system_uptime": 86400,
    "error_rate": 0.001
  },
  "performance_data": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "detections_per_minute": 25,
      "cpu_usage": 45.2,
      "memory_usage": 67.8
    }
  ]
}
```

**Test Cases**:
- Different time periods (1h, 6h, 24h, 7d)
- Metrics during high load
- Metrics with no data
- Invalid time period format

**Priority**: Medium
**Automation**: Yes

### SYS-API-003: Configuration Management
**Endpoint**: `GET/PUT /api/system/config`
**Feature**: System configuration
**Scenario**: Verify configuration retrieval and updates

**GET Request**: `GET /api/system/config`

**Expected Response** (200 OK):
```json
{
  "success": true,
  "configuration": {
    "detection": {
      "confidence_threshold": 0.7,
      "model_path": "/app/models/yolo11m_best.pt"
    },
    "camera": {
      "default_resolution": "1920x1080",
      "frame_rate": 30
    },
    "storage": {
      "save_images": true,
      "max_storage_gb": 100
    }
  }
}
```

**PUT Request**:
```json
{
  "detection": {
    "confidence_threshold": 0.8
  }
}
```

**Test Cases**:
- Get current configuration
- Update individual configuration values
- Update multiple configuration sections
- Invalid configuration values
- Configuration validation
- Configuration rollback on failure

**Priority**: High
**Automation**: Yes

---

## 5. Headless API Tests

### HEADLESS-API-001: Background Processing Control
**Endpoint**: `POST /api/headless/start`
**Feature**: Background processing management
**Scenario**: Verify headless processing control

**Request**:
```json
{
  "cameras": ["camera_001", "camera_002"],
  "processing_mode": "continuous",
  "settings": {
    "confidence_threshold": 0.7,
    "save_results": true,
    "output_channels": ["storage", "webhook"]
  }
}
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "session_id": "headless_session_789",
  "status": "started",
  "cameras_active": 2,
  "started_at": "2024-01-15T10:30:00Z"
}
```

**Test Cases**:
- Start background processing with single camera
- Start with multiple cameras
- Start with invalid camera IDs
- Stop background processing
- Get processing status
- Processing with different output channels

**Priority**: High
**Automation**: Yes

### HEADLESS-API-002: API Buffer Management
**Endpoint**: `GET /api/headless/buffer`
**Feature**: Detection buffer management
**Scenario**: Verify API buffer operations

**Request**: `GET /api/headless/buffer?limit=100`

**Expected Response** (200 OK):
```json
{
  "success": true,
  "buffer_size": 50,
  "detections": [
    {
      "detection_id": "det_001",
      "license_plate": "ABC123",
      "confidence": 0.85,
      "timestamp": "2024-01-15T10:30:00Z",
      "camera_id": "camera_001",
      "processed": false
    }
  ],
  "buffer_stats": {
    "total_detections": 50,
    "processed_detections": 30,
    "pending_detections": 20
  }
}
```

**Test Cases**:
- Get buffer contents with different limits
- Clear buffer
- Buffer overflow handling
- Buffer with no detections
- Mark detections as processed

**Priority**: Medium
**Automation**: Yes

---

## 6. Video API Tests

### VIDEO-API-001: Video Segment Management
**Endpoint**: `GET /api/video/segments`
**Feature**: Video segment listing
**Scenario**: Verify video segment retrieval

**Request**: `GET /api/video/segments?camera_id=camera_001&date=2024-01-15`

**Expected Response** (200 OK):
```json
{
  "success": true,
  "segments": [
    {
      "segment_id": "seg_001",
      "camera_id": "camera_001",
      "start_time": "2024-01-15T10:00:00Z",
      "end_time": "2024-01-15T10:05:00Z",
      "duration": 300,
      "file_path": "/data/videos/camera_001_20240115_100000.mp4",
      "file_size": 52428800,
      "detection_count": 5
    }
  ],
  "total_segments": 1,
  "total_duration": 300
}
```

**Test Cases**:
- Get segments for specific camera and date
- Get segments with no filters
- Get segments for invalid camera ID
- Get segments for date with no recordings
- Pagination for large number of segments

**Priority**: Medium
**Automation**: Yes

### VIDEO-API-002: Video Download
**Endpoint**: `GET /api/video/download/{segment_id}`
**Feature**: Video file download
**Scenario**: Verify video file download

**Request**: `GET /api/video/download/seg_001`

**Expected Response** (200 OK):
```
Content-Type: video/mp4
Content-Disposition: attachment; filename="camera_001_20240115_100000.mp4"
Content-Length: 52428800

[Binary video data]
```

**Test Cases**:
- Download valid video segment
- Download non-existent segment (should return 404)
- Download corrupted video file
- Concurrent download requests
- Download with range requests (partial content)

**Priority**: Low
**Automation**: Yes

---

## 7. Authentication & Authorization Tests

### AUTH-API-001: API Key Authentication
**Endpoint**: All protected endpoints
**Feature**: API key authentication
**Scenario**: Verify API key-based authentication

**Request Header**: `X-API-Key: your-api-key-here`

**Test Cases**:
- Valid API key (should return 200)
- Invalid API key (should return 401)
- Missing API key (should return 401)
- Expired API key (should return 401)
- Rate limiting with API keys

**Priority**: High
**Automation**: Yes

### AUTH-API-002: Role-Based Access Control
**Endpoint**: All endpoints
**Feature**: Role-based permissions
**Scenario**: Verify different user roles have appropriate access

**Test Cases**:
- Admin role (full access)
- Operator role (read/write access)
- Viewer role (read-only access)
- Unauthorized role access attempts

**Priority**: Medium
**Automation**: Yes

---

## 8. Error Handling & Edge Cases

### ERROR-API-001: Rate Limiting
**Endpoint**: All endpoints
**Feature**: API rate limiting
**Scenario**: Verify rate limiting behavior

**Test Cases**:
- Normal request rate (should succeed)
- Exceeding rate limit (should return 429)
- Rate limit reset behavior
- Different rate limits for different endpoints

**Priority**: Medium
**Automation**: Yes

### ERROR-API-002: Malformed Requests
**Endpoint**: All POST/PUT endpoints
**Feature**: Request validation
**Scenario**: Verify handling of malformed requests

**Test Cases**:
- Invalid JSON format (should return 400)
- Missing required fields (should return 400)
- Invalid data types (should return 400)
- Oversized request bodies (should return 413)

**Priority**: High
**Automation**: Yes

### ERROR-API-003: Server Error Handling
**Endpoint**: All endpoints
**Feature**: Server error responses
**Scenario**: Verify proper error responses

**Test Cases**:
- Database connection failure (should return 503)
- Service unavailable (should return 503)
- Internal server error (should return 500)
- Timeout scenarios (should return 504)

**Priority**: High
**Automation**: Yes

---

## Test Data Requirements

### Sample Request Payloads
```json
// Detection request with various confidence levels
{
  "test_detection_requests": [
    {"confidence_threshold": 0.5},
    {"confidence_threshold": 0.7},
    {"confidence_threshold": 0.9}
  ]
}

// Search query variations
{
  "test_search_queries": [
    {"license_plate": "ABC123"},
    {"license_plate": "ABC*"},
    {"confidence_min": 0.8},
    {"date_range": {"start": "2024-01-01", "end": "2024-01-31"}}
  ]
}
```

### Test Images
- Valid license plate images (JPEG, PNG)
- Invalid image formats
- Corrupted image files
- Images with multiple license plates
- Images with no license plates
- Large image files (>10MB)

### Mock Data
- Sample detection results (JSON)
- Camera configuration data
- System metrics data
- User authentication data

## Performance Benchmarks

### Response Time Targets
- Health check: < 100ms
- Image detection: < 500ms
- Results retrieval: < 200ms
- Search queries: < 300ms
- Export operations: < 2000ms

### Throughput Targets
- Concurrent API requests: 100/second
- Image processing: 10 images/second
- WebSocket connections: 50 concurrent

## Test Execution Guidelines

### Test Environment Setup
- Use Docker containers for consistent testing
- Mock external dependencies (cameras, file systems)
- Use test databases with known data sets
- Implement proper test data cleanup

### API Testing Best Practices
- Test positive and negative scenarios
- Validate response schemas
- Test error handling and edge cases
- Implement proper authentication in tests
- Use meaningful test data
- Validate response times
- Test concurrent access scenarios

### Automation Framework Integration
- Use REST Assured for API testing
- Implement request/response logging
- Use TestNG for test organization
- Implement data-driven testing
- Generate comprehensive test reports
- Integrate with CI/CD pipeline

## Traceability Matrix

| Test Category | Endpoint Count | Priority | Automation Coverage |
|---------------|----------------|----------|-------------------|
| Detection API | 4 | Critical | 100% |
| Stream API | 2 | High | 75% |
| Results API | 4 | High | 100% |
| System API | 3 | High | 100% |
| Headless API | 2 | Medium | 100% |
| Video API | 2 | Low | 100% |
| Auth API | 2 | High | 100% |
| Error Handling | 3 | High | 100% |

**Total API Endpoints**: 22  
**Total Test Scenarios**: 65+  
**Automation Coverage**: 95%