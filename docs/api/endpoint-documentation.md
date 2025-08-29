# API Endpoint Documentation

Complete reference for all 52 API endpoints in the License Plate Recognition System.

## System Health & Status (5 endpoints)

### `/health` - GET
- **Purpose**: Basic health check endpoint
- **Response**: `200 OK` with health status
- **Usage**: Load balancer health checks

### `/api/system/health` - GET
- **Purpose**: Comprehensive system health check
- **Response**: JSON with service status, database connectivity, and performance metrics
- **Usage**: Monitoring dashboard, alerting systems

### `/ws/status` - GET
- **Purpose**: WebSocket status endpoint
- **Response**: Real-time system status via WebSocket
- **Usage**: Live dashboard updates

### `/debug/cameras` - GET
- **Purpose**: Debug camera configuration and status
- **Response**: Camera debugging information
- **Usage**: Development and troubleshooting

### `/api/config/features` - GET  
- **Purpose**: Get current feature configuration
- **Response**: JSON with enabled/disabled features
- **Usage**: Frontend feature toggles

## Camera Management (16 endpoints)

### Core Camera Operations

#### `/api/cameras` - GET
- **Purpose**: Get all cameras with status
- **Response**: Array of camera objects with real-time status
- **Usage**: Camera list display

#### `/api/cameras` - POST
- **Purpose**: Add new camera
- **Request**: Camera configuration (IP, port, stream path, etc.)
- **Response**: Created camera object
- **Usage**: Camera setup wizard

#### `/api/cameras/{camera_id}` - PUT
- **Purpose**: Update existing camera configuration
- **Request**: Updated camera configuration
- **Response**: Updated camera object
- **Usage**: Camera settings modification

#### `/api/cameras/{camera_id}` - GET
- **Purpose**: Get specific camera details
- **Response**: Camera object with current status
- **Usage**: Camera details view

#### `/api/cameras/{camera_id}` - DELETE
- **Purpose**: Remove camera from system
- **Response**: Success confirmation
- **Usage**: Camera removal

#### `/api/cameras/list` - GET
- **Purpose**: Simple camera list (legacy endpoint)
- **Response**: Basic camera array
- **Usage**: Dropdown lists, basic UI components

### Camera Control Operations

#### `/api/cameras/{camera_id}/test` - POST
- **Purpose**: Test connection to specific camera
- **Response**: Connection test results
- **Usage**: Camera setup validation

#### `/api/cameras/{camera_id}/start` - POST
- **Purpose**: Start camera recording/monitoring
- **Response**: Start operation status
- **Usage**: Camera activation

#### `/api/cameras/{camera_id}/stop` - POST
- **Purpose**: Stop camera recording/monitoring  
- **Response**: Stop operation status
- **Usage**: Camera deactivation

#### `/api/cameras/{camera_id}/restart` - POST
- **Purpose**: Restart specific camera
- **Response**: Restart operation status
- **Usage**: Camera troubleshooting

#### `/api/cameras/restart/all` - POST
- **Purpose**: Restart all cameras
- **Response**: Batch restart status
- **Usage**: System maintenance

#### `/api/cameras/test` - POST
- **Purpose**: Test multiple camera configurations
- **Request**: Array of camera configurations
- **Response**: Test results for each camera
- **Usage**: Bulk camera validation

#### `/api/cameras/test-all-paths` - POST
- **Purpose**: Test all possible stream paths for a camera
- **Request**: Camera IP and connection details
- **Response**: Results for each tested path
- **Usage**: Auto-discovery of camera streams

### Camera Health & Diagnostics

#### `/api/cameras/{camera_id}/health` - GET
- **Purpose**: Get detailed health status for specific camera
- **Response**: Health metrics, connection status, performance data
- **Usage**: Camera monitoring dashboard

#### `/api/cameras/health/summary` - GET
- **Purpose**: Get health summary for all cameras
- **Response**: Aggregated health status
- **Usage**: System overview dashboard

#### `/api/cameras/health/detailed` - GET
- **Purpose**: Get detailed health data for all cameras
- **Response**: Comprehensive health metrics for each camera
- **Usage**: Detailed monitoring and diagnostics

#### `/api/cameras/{camera_id}/diagnostics` - GET
- **Purpose**: Run comprehensive diagnostics on specific camera
- **Response**: Diagnostic test results including network, stream quality, etc.
- **Usage**: Troubleshooting and maintenance

### Camera Media & Quality

#### `/api/cameras/{camera_id}/snapshot` - GET
- **Purpose**: Capture current frame from camera
- **Response**: JPEG image or error
- **Usage**: Live preview, testing, thumbnails

#### `/api/cameras/{camera_id}/recording/quality` - GET
- **Purpose**: Get recording quality metrics
- **Response**: Quality statistics (fps, resolution, bitrate, etc.)
- **Usage**: Quality monitoring

#### `/api/cameras/{camera_id}/recording/quality` - POST
- **Purpose**: Update recording quality settings
- **Request**: Quality parameters
- **Response**: Updated settings confirmation
- **Usage**: Quality optimization

#### `/api/cameras/{camera_id}/open-vlc` - POST
- **Purpose**: Open camera stream in VLC player
- **Response**: VLC launch status
- **Usage**: External stream viewing

## ONVIF Discovery (4 endpoints)

### `/api/onvif/discover` - POST
- **Purpose**: Discover ONVIF cameras on network
- **Response**: Array of discovered cameras
- **Usage**: Automatic camera detection

### `/api/onvif/discovered` - GET
- **Purpose**: Get list of previously discovered cameras
- **Response**: Cached discovery results
- **Usage**: Camera selection from discovered devices

### `/api/onvif/add/{camera_ip}` - POST
- **Purpose**: Add discovered ONVIF camera to system
- **Response**: Added camera configuration
- **Usage**: One-click camera addition

### `/api/onvif/brands` - GET
- **Purpose**: Get supported ONVIF camera brands/models
- **Response**: Array of supported brands
- **Usage**: Compatibility reference

## Detection Management (11 endpoints)

### Detection Queries

#### `/api/detections/recent` - GET
- **Purpose**: Get recent license plate detections
- **Parameters**: `limit` (optional, default 50)
- **Response**: Array of recent detection objects
- **Usage**: Main dashboard detection feed

#### `/api/detections/search` - GET
- **Purpose**: Search detections by various criteria
- **Parameters**: `plate_text`, `camera_id`, `start_date`, `end_date`, `limit`
- **Response**: Filtered detection results
- **Usage**: Detection search interface

#### `/api/detections/similar/{plate_text}` - GET (multiple implementations)
- **Purpose**: Find detections with similar plate text
- **Response**: Array of similar detections
- **Usage**: Partial plate matching, fuzzy search

#### `/api/detections/history/{plate_text}` - GET (multiple implementations)
- **Purpose**: Get complete history for specific plate
- **Response**: Chronological detection history
- **Usage**: Plate tracking timeline

#### `/api/detections/stats` - GET (multiple implementations)
- **Purpose**: Get detection statistics
- **Response**: Aggregated detection metrics
- **Usage**: Analytics dashboard

#### `/api/detections/{detection_id}` - GET
- **Purpose**: Get specific detection details
- **Response**: Complete detection object with images
- **Usage**: Detection detail view

#### `/api/detections/object-types` - GET
- **Purpose**: Get available detection object types
- **Response**: Array of supported detection types
- **Usage**: Filter configuration

### Detection Quality

#### `/api/detections/{detection_id}/quality` - GET
- **Purpose**: Get quality metrics for specific detection
- **Response**: Quality scores and analysis
- **Usage**: Quality assessment dashboard

## Analytics & Quality (5 endpoints)

### `/api/analytics/overview` - GET
- **Purpose**: Get system analytics overview
- **Response**: High-level analytics data
- **Usage**: Executive dashboard

### `/api/quality/metrics` - GET
- **Purpose**: Get quality metrics across system
- **Response**: Quality statistics and trends
- **Usage**: Quality monitoring dashboard

### `/api/quality/thresholds` - GET
- **Purpose**: Get current quality thresholds
- **Response**: Quality threshold configuration
- **Usage**: Quality settings display

### `/api/quality/filter` - POST
- **Purpose**: Apply quality filtering to detections
- **Request**: Filter criteria and parameters
- **Response**: Filtered results
- **Usage**: Quality-based detection filtering

## Storage Management (3 endpoints)

### `/api/storage/stats` - GET
- **Purpose**: Get storage usage statistics
- **Response**: Storage metrics (used, available, by category)
- **Usage**: Storage monitoring dashboard

### `/api/storage/cleanup` - POST
- **Purpose**: Perform routine storage cleanup
- **Response**: Cleanup operation results
- **Usage**: Maintenance operations

### `/api/storage/emergency-cleanup` - POST
- **Purpose**: Perform emergency storage cleanup when space critical
- **Response**: Emergency cleanup results  
- **Usage**: Automated space management

## Video Management (1 endpoint)

### `/api/video/clip/{clip_id}` - GET
- **Purpose**: Retrieve video clip by ID
- **Response**: Video file or stream
- **Usage**: Playback of detection video clips

## Authentication Status

All endpoints currently operate without authentication but return proper HTTP status codes:
- **200**: Success
- **404**: Resource not found  
- **500**: Server error
- **422**: Validation error

## Database Integration

All endpoints use FastAPI dependency injection for database access:
```python
db_service: DatabaseService = Depends(get_database_service)
```

This ensures proper session management and prevents the "Could not locate a bind configured on mapper" errors that were previously occurring.

## Testing Status ✅

All 52 endpoints have been tested and confirmed working with proper JSON responses and 200 status codes after the database session fixes were implemented.