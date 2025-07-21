# Camera API Testing - Postman Collection Guide

**Version:** 2.0  
**Date:** 2025-01-20  
**API Base URL:** `http://localhost:8002/api`  
**Authentication:** None (for development)  

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Camera Management Endpoints](#camera-management-endpoints)
3. [Connection Testing Endpoints](#connection-testing-endpoints)
4. [Stream Management Endpoints](#stream-management-endpoints)
5. [Health & Monitoring Endpoints](#health--monitoring-endpoints)
6. [Error Scenarios](#error-scenarios)
7. [Complete Test Scenarios](#complete-test-scenarios)

## Environment Setup

### Postman Environment Variables
Create a new environment in Postman with these variables:

```json
{
  "base_url": "http://localhost:8002/api",
  "camera_id": "",
  "location_id": "",
  "test_ip": "10.0.0.181",
  "test_username": "admin",
  "test_password": "Mekus_1987"
}
```

### Global Headers
Set these headers for all requests:
- `Content-Type: application/json`
- `Accept: application/json`

---

## Camera Management Endpoints

### 1. **GET /cameras** - List All Cameras

**Purpose:** Retrieve all cameras in the system  
**Method:** `GET`  
**URL:** `{{base_url}}/cameras/`  

#### Query Parameters (Optional)
- `status` (string): Filter by camera status (`active`, `inactive`, `offline`)
- `location` (string): Filter by location name
- `limit` (integer): Number of results (default: 20, max: 100)
- `offset` (integer): Pagination offset (default: 0)

#### Test Cases

**Test 1.1: Get All Cameras**
```
GET {{base_url}}/cameras/
```

**Expected Response (200):**
```json
[
  {
    "id": "065d0400-90ca-4f15-a25e-7adb001c2c18",
    "name": "Front Gate Camera",
    "ip_address": "10.0.0.181",
    "port": 554,
    "username": "admin",
    "manufacturer": "generic",
    "camera_type": "ip_camera",
    "stream_path": "/stream1",
    "location_id": "6d882a8a-2ad8-46d9-b254-987c5e5d5eba",
    "location_name": "Front Door",
    "status": "offline",
    "created_at": "2025-01-20T10:30:00Z",
    "updated_at": "2025-01-20T10:30:00Z"
  }
]
```

**Test 1.2: Get Cameras with Filters**
```
GET {{base_url}}/cameras/?status=active&limit=10
```

**Test 1.3: Get Cameras with Pagination**
```
GET {{base_url}}/cameras/?limit=5&offset=0
```

---

### 2. **GET /cameras/{id}** - Get Specific Camera

**Purpose:** Retrieve details of a specific camera  
**Method:** `GET`  
**URL:** `{{base_url}}/cameras/{{camera_id}}`  

#### Test Cases

**Test 2.1: Get Valid Camera**
```
GET {{base_url}}/cameras/065d0400-90ca-4f15-a25e-7adb001c2c18
```

**Test 2.2: Get Non-existent Camera**
```
GET {{base_url}}/cameras/invalid-camera-id
```

**Expected Response (404):**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Camera with ID 'invalid-camera-id' not found"
  },
  "timestamp": "2025-01-20T10:30:00Z",
  "request_id": "req_123456789"
}
```

---

### 3. **POST /cameras/** - Create New Camera

**Purpose:** Add a new camera to the system  
**Method:** `POST`  
**URL:** `{{base_url}}/cameras/`  

#### Request Body Schema
```json
{
  "name": "string (required)",
  "ip_address": "string (required, valid IP)",
  "port": "integer (optional, default: 554)",
  "username": "string (optional, default: admin)",
  "password": "string (optional)",
  "stream_path": "string (optional, default: /stream1)",
  "location_id": "string (required, valid UUID)",
  "manufacturer": "string (optional, default: generic)",
  "camera_type": "string (optional, default: ip_camera)",
  "connection_type": "string (optional, default: rtsp)",
  "model": "string (optional)",
  "auth_type": "string (optional, default: basic)",
  "resolution_width": "integer (optional, default: 1920)",
  "resolution_height": "integer (optional, default: 1080)",
  "fps": "integer (optional, default: 30)"
}
```

#### Test Cases

**Test 3.1: Create Valid Camera**
```json
POST {{base_url}}/cameras/

{
  "name": "Parking Lot Camera",
  "ip_address": "192.168.1.100",
  "port": 554,
  "username": "admin",
  "password": "password123",
  "stream_path": "/stream1",
  "location_id": "6d882a8a-2ad8-46d9-b254-987c5e5d5eba",
  "manufacturer": "hikvision",
  "camera_type": "ip_camera",
  "connection_type": "rtsp"
}
```

**Expected Response (201):**
```json
{
  "id": "new-camera-uuid",
  "name": "Parking Lot Camera",
  "ip_address": "192.168.1.100",
  "status": "offline",
  "created_at": "2025-01-20T10:30:00Z"
}
```

**Test 3.2: Create Camera with Minimum Required Fields**
```json
POST {{base_url}}/cameras/

{
  "name": "Minimal Camera",
  "ip_address": "192.168.1.101",
  "location_id": "6d882a8a-2ad8-46d9-b254-987c5e5d5eba"
}
```

**Test 3.3: Create Camera with Invalid Data**
```json
POST {{base_url}}/cameras/

{
  "name": "",
  "ip_address": "invalid_ip",
  "location_id": "invalid_uuid"
}
```

**Expected Response (400):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "name",
        "message": "Name cannot be empty"
      },
      {
        "field": "ip_address", 
        "message": "Invalid IP address format"
      }
    ]
  }
}
```

**Test 3.4: Create Camera with Duplicate IP**
```json
POST {{base_url}}/cameras/

{
  "name": "Duplicate Camera",
  "ip_address": "10.0.0.181",
  "location_id": "6d882a8a-2ad8-46d9-b254-987c5e5d5eba"
}
```

**Expected Response (409):**
```json
{
  "error": {
    "code": "RESOURCE_CONFLICT",
    "message": "Camera with IP address '10.0.0.181' already exists"
  }
}
```

---

### 4. **PUT /cameras/{id}** - Update Camera

**Purpose:** Update an existing camera  
**Method:** `PUT`  
**URL:** `{{base_url}}/cameras/{{camera_id}}`  

#### Test Cases

**Test 4.1: Update Camera Successfully**
```json
PUT {{base_url}}/cameras/065d0400-90ca-4f15-a25e-7adb001c2c18

{
  "name": "Updated Front Gate Camera",
  "ip_address": "10.0.0.181",
  "port": 554,
  "username": "admin",
  "password": "Mekus_1987",
  "stream_path": "/h264Preview_01_main",
  "location_id": "6d882a8a-2ad8-46d9-b254-987c5e5d5eba",
  "manufacturer": "reolink"
}
```

**Test 4.2: Update Non-existent Camera**
```json
PUT {{base_url}}/cameras/invalid-camera-id

{
  "name": "Updated Camera"
}
```

**Test 4.3: Update Camera with Invalid Data**
```json
PUT {{base_url}}/cameras/065d0400-90ca-4f15-a25e-7adb001c2c18

{
  "ip_address": "invalid_ip"
}
```

---

### 5. **DELETE /cameras/{id}** - Delete Camera

**Purpose:** Remove a camera from the system  
**Method:** `DELETE`  
**URL:** `{{base_url}}/cameras/{{camera_id}}`  

#### Test Cases

**Test 5.1: Delete Valid Camera**
```
DELETE {{base_url}}/cameras/065d0400-90ca-4f15-a25e-7adb001c2c18
```

**Expected Response (204):** No content

**Test 5.2: Delete Non-existent Camera**
```
DELETE {{base_url}}/cameras/invalid-camera-id
```

**Expected Response (404):**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Camera not found"
  }
}
```

---

## Connection Testing Endpoints

### 6. **POST /cameras/test-connection** - Test Camera Connection

**Purpose:** Test connectivity to a camera before adding it  
**Method:** `POST`  
**URL:** `{{base_url}}/cameras/test-connection`  

#### Request Body Schema
```json
{
  "connection_type": "string (default: rtsp)",
  "ip_address": "string (required)",
  "port": "string (optional, default: 554)",
  "username": "string (optional, default: admin)",
  "password": "string (optional)",
  "stream_path": "string (optional, default: /stream1)"
}
```

#### Test Cases

**Test 6.1: Test Valid RTSP Connection**
```json
POST {{base_url}}/cameras/test-connection

{
  "connection_type": "rtsp",
  "ip_address": "{{test_ip}}",
  "port": "554",
  "username": "{{test_username}}",
  "password": "{{test_password}}",
  "stream_path": "/stream1"
}
```

**Expected Response (200) - Success:**
```json
{
  "success": true,
  "detail": "Connection successful",
  "url": "rtsp://admin:Mekus_1987@10.0.0.181:554/stream1",
  "details": {
    "response_time": 150,
    "stream_info": "H.264",
    "resolution": "1920x1080"
  },
  "connection_info": {
    "protocol": "RTSP",
    "timeout_used": "10 seconds"
  }
}
```

**Expected Response (200) - Failure:**
```json
{
  "success": false,
  "detail": "Connection test timed out after 15 seconds",
  "url": "rtsp://admin:wrong@10.0.0.181:554/stream1",
  "details": {
    "timeout": true,
    "timeout_seconds": 15
  }
}
```

**Test 6.2: Test Different Stream Paths**
```json
POST {{base_url}}/cameras/test-connection

{
  "ip_address": "{{test_ip}}",
  "username": "{{test_username}}",
  "password": "{{test_password}}",
  "stream_path": "/h264Preview_01_main"
}
```

**Test 6.3: Test HTTP Connection**
```json
POST {{base_url}}/cameras/test-connection

{
  "connection_type": "http",
  "ip_address": "{{test_ip}}",
  "port": "80",
  "username": "{{test_username}}",
  "password": "{{test_password}}"
}
```

**Test 6.4: Test with Invalid Credentials**
```json
POST {{base_url}}/cameras/test-connection

{
  "ip_address": "{{test_ip}}",
  "username": "wrong_user",
  "password": "wrong_pass",
  "stream_path": "/stream1"
}
```

**Test 6.5: Test Unreachable IP**
```json
POST {{base_url}}/cameras/test-connection

{
  "ip_address": "192.168.99.99",
  "username": "admin",
  "password": "password"
}
```

---

### 7. **POST /cameras/test-connection-enhanced** - Enhanced Connection Test

**Purpose:** Advanced connection testing with multiple protocols  
**Method:** `POST`  
**URL:** `{{base_url}}/cameras/test-connection-enhanced`  

#### Test Cases

**Test 7.1: Enhanced Connection Test**
```json
POST {{base_url}}/cameras/test-connection-enhanced

{
  "ip_address": "{{test_ip}}",
  "username": "{{test_username}}",
  "password": "{{test_password}}",
  "test_multiple_paths": true,
  "include_onvif": true
}
```

---

## Stream Management Endpoints

### 8. **GET /cameras/{id}/snapshot** - Get Camera Snapshot

**Purpose:** Retrieve a snapshot image from the camera  
**Method:** `GET`  
**URL:** `{{base_url}}/cameras/{{camera_id}}/snapshot`  

#### Test Cases

**Test 8.1: Get Snapshot from Active Camera**
```
GET {{base_url}}/cameras/065d0400-90ca-4f15-a25e-7adb001c2c18/snapshot
```

**Expected Response:** Binary image data or JSON error

**Test 8.2: Get Snapshot from Offline Camera**
```
GET {{base_url}}/cameras/offline-camera-id/snapshot
```

---

### 9. **GET /cameras/{id}/stream** - Get Live Stream

**Purpose:** Get live stream URL or stream data  
**Method:** `GET`  
**URL:** `{{base_url}}/cameras/{{camera_id}}/stream`  

#### Test Cases

**Test 9.1: Get Stream URL**
```
GET {{base_url}}/cameras/065d0400-90ca-4f15-a25e-7adb001c2c18/stream
```

---

## Health & Monitoring Endpoints

### 10. **GET /cameras/{id}/health** - Camera Health Check

**Purpose:** Get camera health status and diagnostics  
**Method:** `GET`  
**URL:** `{{base_url}}/cameras/{{camera_id}}/health`  

#### Test Cases

**Test 10.1: Get Camera Health**
```
GET {{base_url}}/cameras/065d0400-90ca-4f15-a25e-7adb001c2c18/health
```

**Expected Response (200):**
```json
{
  "camera_id": "065d0400-90ca-4f15-a25e-7adb001c2c18",
  "status": "offline",
  "last_ping": null,
  "response_time": null,
  "stream_active": false,
  "error_count": 0,
  "uptime_percentage": 95.5,
  "last_error": null,
  "health_score": 100.0
}
```

---

### 11. **GET /locations/** - Get Available Locations

**Purpose:** Retrieve all available locations for camera assignment  
**Method:** `GET`  
**URL:** `{{base_url}}/locations/`  

#### Test Cases

**Test 11.1: Get All Locations**
```
GET {{base_url}}/locations/
```

**Expected Response (200):**
```json
[
  {
    "id": "6d882a8a-2ad8-46d9-b254-987c5e5d5eba",
    "name": "Front Door",
    "description": "Main entrance area",
    "active": true
  },
  {
    "id": "4b0dc614-b7fc-445a-8835-d6b54fbd19d3",
    "name": "Main Site",
    "description": "Primary location",
    "active": true
  }
]
```

---

## Error Scenarios

### Authentication Errors
**Test 12.1: Missing Authentication (if required)**
```
GET {{base_url}}/cameras/
Authorization: (remove header)
```

### Rate Limiting
**Test 12.2: Rate Limit Exceeded**
```
// Send 100+ requests rapidly to trigger rate limiting
POST {{base_url}}/cameras/test-connection
```

### Server Errors
**Test 12.3: Invalid JSON**
```json
POST {{base_url}}/cameras/

{
  "name": "Invalid JSON"
  // Missing closing brace
```

---

## Complete Test Scenarios

### Scenario 1: Full Camera Lifecycle

1. **Get all locations** to find valid location_id
2. **Test connection** before adding camera
3. **Create camera** with test connection data
4. **Verify camera creation** by getting camera details
5. **Update camera** with different stream path
6. **Test camera health** 
7. **Get camera snapshot** (if available)
8. **Delete camera** when done

### Scenario 2: Connection Testing Workflow

1. **Test basic RTSP connection** with `/stream1`
2. **Test alternative stream paths** (`/h264Preview_01_main`, `/Streaming/Channels/101/`)
3. **Test HTTP connection** as fallback
4. **Test ONVIF discovery** if supported
5. **Use successful connection data** to create camera

### Scenario 3: Error Handling Validation

1. **Test all validation errors** (empty name, invalid IP, etc.)
2. **Test duplicate IP address** conflict
3. **Test non-existent camera operations**
4. **Test invalid connection parameters**
5. **Test network timeout scenarios**

### Scenario 4: Real Camera Integration (Your Camera)

1. **Test connection** to 10.0.0.181 with various stream paths:
   - `/stream1`
   - `/stream2` 
   - `/h264Preview_01_main`
   - `/live1.sdp`
   - `/axis-media/media.amp`

2. **Create camera** with working stream path
3. **Update stream path** if initial doesn't work
4. **Monitor health status**

---

## Postman Collection Structure

```
Camera API Tests/
├── 📁 Environment Setup
├── 📁 Camera Management
│   ├── GET List Cameras
│   ├── GET Camera Details  
│   ├── POST Create Camera
│   ├── PUT Update Camera
│   └── DELETE Camera
├── 📁 Connection Testing
│   ├── POST Test Connection Basic
│   ├── POST Test Connection Enhanced
│   └── POST Test Different Protocols
├── 📁 Stream Management
│   ├── GET Camera Snapshot
│   └── GET Stream Info
├── 📁 Health & Monitoring
│   ├── GET Camera Health
│   └── GET Locations
├── 📁 Error Scenarios
│   ├── Validation Errors
│   ├── Not Found Errors
│   └── Conflict Errors
└── 📁 Complete Workflows
    ├── Full Camera Lifecycle
    ├── Connection Testing Flow
    └── Real Camera Setup
```

## Usage Instructions

1. **Import Environment:** Create Postman environment with the variables above
2. **Set Base URL:** Update `{{base_url}}` to your server
3. **Update Credentials:** Set your real camera IP, username, password
4. **Run Tests:** Execute requests in suggested order
5. **Check Responses:** Validate status codes and response structure
6. **Save Results:** Store working camera configurations

## Success Criteria

- ✅ All 2xx responses return expected JSON structure
- ✅ All 4xx/5xx errors return consistent error format
- ✅ Connection tests correctly identify reachable cameras
- ✅ CRUD operations work end-to-end
- ✅ Real camera (10.0.0.181) connects successfully
- ✅ Stream paths are discovered and functional

---

**Next Steps:**
1. Test your real camera with different stream paths
2. Document working configuration
3. Set up automated health monitoring
4. Implement camera preview functionality