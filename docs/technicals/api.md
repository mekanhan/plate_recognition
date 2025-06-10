# API Reference

**Version:** 1.0
**Last Updated:** 2023-07-20

## Overview

This document provides a reference for the License Plate Recognition System API endpoints. The API is organized into several functional areas, with the newer v2 endpoints providing access to the improved architecture including video recording functionality.

## API Conventions

### Base URL

For example: `http://localhost:8001/`

### Authentication

The API currently does not require authentication. Access control should be implemented at the network level.

### Response Format

All API responses are in JSON format with the following general structure for successful responses:

```json
{
  "field1": "value1",
  "field2": "value2",
  // ...
}

Error responses follow this structure:
{
  "detail": "Error message describing what went wrong"
}

HTTP Status Codes
200 OK: Request succeeded
400 Bad Request: Invalid request parameters
404 Not Found: Resource not found
500 Internal Server Error: Server error
API Endpoints
Video Management
List Video Segments
Run
GET /v2/video/segments
Returns a paginated list of video segments.

Query Parameters:

Name	Type	Required	Description
limit	integer	No	Maximum number of results (default 20)
offset	integer	No	Number of results to skip (default 0)

Response:

Json

Apply
{
  "count": 2,
  "segments": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "file_path": "data/videos/2023-07-19/ABC123_1689765432.mp4",
      "start_time": 1689765432.567,
      "end_time": 1689765452.123,
      "duration_seconds": 19.556,
      "file_size_bytes": 3145728,
      "resolution": "1280x720",
      "archived": false,
      "detection_ids": ["7f4e6c2b-1a2b-3c4d-5e6f-7a8b9c0d1e2f"]
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "file_path": "data/videos/2023-07-19/XYZ789_1689764321.mp4",
      "start_time": 1689764321.123,
      "end_time": 1689764341.789,
      "duration_seconds": 20.666,
      "file_size_bytes": 3355443,
      "resolution": "1280x720",
      "archived": false,
      "detection_ids": ["8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d"]
    }
  ]
}
Get Video Segment
Run
GET /v2/video/segments/{segment_id}
Returns information about a specific video segment.

Path Parameters:

Name	Type	Required	Description
segment_id	string	Yes	ID of the video segment

Response:

Json

Apply
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_path": "data/videos/2023-07-19/ABC123_1689765432.mp4",
  "start_time": 1689765432.567,
  "end_time": 1689765452.123,
  "duration_seconds": 19.556,
  "file_size_bytes": 3145728,
  "resolution": "1280x720",
  "archived": false,
  "detection_ids": ["7f4e6c2b-1a2b-3c4d-5e6f-7a8b9c0d1e2f"]
}
Download Video Segment
Run
GET /v2/video/segments/{segment_id}/download
Downloads the video file for a specific segment.

Path Parameters:

Name	Type	Required	Description
segment_id	string	Yes	ID of the video segment

Response:

The video file as a binary stream with Content-Type: video/mp4

Get Videos by Detection
Run
GET /v2/video/by-detection/{detection_id}
Returns videos containing a specific detection.

Path Parameters:

Name	Type	Required	Description
detection_id	string	Yes	ID of the detection

Response:

Json

Apply
{
  "count": 1,
  "videos": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "file_path": "data/videos/2023-07-19/ABC123_1689765432.mp4",
      "start_time": 1689765432.567,
      "end_time": 1689765452.123,
      "duration_seconds": 19.556,
      "file_size_bytes": 3145728,
      "resolution": "1280x720",
      "archived": false,
      "detection_ids": ["7f4e6c2b-1a2b-3c4d-5e6f-7a8b9c0d1e2f"]
    }
  ]
}
Clean Up Old Videos
Run
POST /v2/video/cleanup
Archives and optionally deletes videos older than the specified retention period.

Query Parameters:

Name	Type	Required	Description
retention_days	integer	No	Number of days to keep videos (default 30)

Response:

Json

Apply
{
  "status": "success",
  "message": "Archived 5 old videos",
  "archived_count": 5
}
Get Video Statistics
Run
GET /v2/video/stats
Returns statistics about video recordings.

Response:

Json

Apply
{
  "total_count": 120,
  "total_size_mb": 3500.25,
  "total_duration_minutes": 1240.5,
  "average_duration_seconds": 20.5,
  "average_size_mb": 29.17,
  "videos_by_date": {
    "2023-07-19": 42,
    "2023-07-18": 38,
    "2023-07-17": 40
  }
}
Detection Management
Get Latest Detections
Run
GET /v2/detection/latest
Returns the most recent license plate detections.

Response:

Json

Apply
{
  "detections": [
    {
      "detection_id": "7f4e6c2b-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
      "plate_text": "ABC123",
      "confidence": 0.95,
      "timestamp": 1689765432.567,
      "box": [100, 200, 300, 250],
      "state": "CA",
      "status": "active",
      "image_path": "data/images/ABC123_1689765432.jpg",
      "video_path": "data/videos/2023-07-19/ABC123_1689765432.mp4"
    }
  ]
}
Detect From Camera
Run
POST /v2/detection/detect-from-camera
Detects license plates from the current camera frame.

Response:

Json

Apply
{
  "detection_id": "7f4e6c2b-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
  "plate_text": "ABC123",
  "confidence": 0.95,
  "timestamp": 1689765432.567
}
Detect From Image
Run
POST /v2/detection/detect-from-image
Detects license plates from an uploaded image.

Request Body:

Form data with file field named "file"

Response:

Json

Apply
{
  "detection_id": "7f4e6c2b-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
  "plate_text": "ABC123",
  "confidence": 0.95,
  "timestamp": 1689765432.567
}
Results Management
Get Detections
Run
GET /v2/results/detections
Returns license plate detections with pagination and filtering.

Query Parameters:

Name	Type	Required	Description
limit	integer	No	Maximum number of results (default 10)
skip	integer	No	Number of results to skip (default 0)
min_confidence	float	No	Minimum confidence threshold (default 0.0)

Response:

Json

Apply
{
  "total": 120,
  "limit": 10,
  "skip": 0,
  "detections": [
    {
      "detection_id": "7f4e6c2b-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
      "plate_text": "ABC123",
      "confidence": 0.95,
      "timestamp": 1689765432.567,
      "box": [100, 200, 300, 250],
      "state": "CA",
      "status": "active",
      "image_path": "data/images/ABC123_1689765432.jpg",
      "video_path": "data/videos/2023-07-19/ABC123_1689765432.mp4"
    }
  ]
}
Get Enhanced Results
Run
GET /v2/results/enhanced-results
Returns enhanced license plate results with pagination and filtering.

Query Parameters:

Name	Type	Required	Description
limit	integer	No	Maximum number of results (default 10)
skip	integer	No	Number of results to skip (default 0)
min_confidence	float	No	Minimum confidence threshold (default 0.0)

Response:

Json

Apply
{
  "total": 120,
  "limit": 10,
  "skip": 0,
  "enhanced_results": [
    {
      "enhanced_id": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
      "original_detection_id": "7f4e6c2b-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
      "plate_text": "ABC123",
      "confidence": 0.98,
      "timestamp": 1689765433.123,
      "match_type": "known_plate",
      "confidence_category": "HIGH"
    }
  ]
}
Stream Management
Video Feed
Run
GET /v2/stream/video-feed
Streams the video feed with license plate detection overlays.

Response:

Multipart MJPEG stream

Snapshot
Run
GET /v2/stream/snapshot
Returns a single snapshot from the camera.

Response:

JPEG image

Annotated Snapshot
Run
GET /v2/stream/annotated-snapshot
Returns a single snapshot with license plate detection overlays.

Response:

JPEG image with detection overlays and custom headers:

X-Detections-Count: Number of detections in the image
X-Timestamp: Timestamp when the image was captured
Web Interfaces
The system also provides web interfaces for the API:

/video-browser: Web UI for browsing and viewing recorded videos
/detection-test: Web UI for testing license plate detection
/v2: Enhanced UI for v2 API features
Code Examples
JavaScript Example - Fetching Videos

async function fetchVideos() {
  const response = await fetch('/v2/video/segments?limit=10');
  const data = await response.json();
  
  console.log(`Found ${data.count} videos`);
  data.segments.forEach(video => {
    console.log(`Video: ${video.file_path}, Duration: ${video.duration_seconds}s`);
  });
}
Python Example - Detecting from Camera

import requests

response = requests.post('http://localhost:8001/v2/detection/detect-from-camera')
if response.status_code == 200:
    detection = response.json()
    print(f"Detected plate: {detection['plate_text']} with confidence {detection['confidence']}")
else:
    print(f"Error: {response.json()['detail']}")
