# API Reference

**Version:** 1.0
**Last Updated:** 2023-07-20
**Authors:** [Your Name]

## Overview

This document provides a comprehensive reference for the License Plate Recognition System API endpoints.

## API Specification

The API follows OpenAPI 3.0 specification. Full API documentation is available at `/docs` when the server is running.

## Authentication

API endpoints currently do not require authentication. This may change in future versions.

## Endpoints

### Video Management

#### List Video Segments

GET /v2/video/segments


**Parameters:**

| Name   | In    | Type    | Required | Description                          |
|--------|-------|---------|----------|--------------------------------------|
| limit  | query | integer | No       | Maximum number of results (default 20) |
| offset | query | integer | No       | Number of results to skip (default 0) |

**Responses:**

| Status | Description           | Schema                        |
|--------|-----------------------|-------------------------------|
| 200    | Successful operation  | VideoSegmentList              |
| 500    | Server error          | Error                         |

**Example Response:**

```json
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
```
Get Video Segment

GET /v2/video/segments/{segment_id}

[Additional endpoint documentation...]

Schemas
VideoSegment
Property	Type	Description
id	string	Unique identifier (UUID format)
file_path	string	Path to video file
start_time	number	Recording start timestamp (epoch)
end_time	number	Recording end timestamp (epoch)
duration_seconds	number	Duration in seconds
file_size_bytes	integer	File size in bytes
resolution	string	Video resolution (e.g., "1280x720")
archived	boolean	Whether video is archived
detection_ids	array	List of associated detection IDs

[Additional schema documentation...]

Error Handling
All API endpoints use standard HTTP status codes and return error details in a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```
Rate Limiting
The API currently does not implement rate limiting.

Versioning
API versioning is reflected in the URL path (/v2/...) and will be incremented for breaking changes.


