# IP Camera Requirements for LPR System

## Overview
This document outlines the requirements and specifications for adding new IP cameras to the License Plate Recognition (LPR) system.

## Camera Hardware Requirements

### Network Connectivity
- **IP Camera**: Must be accessible via network (WiFi or Ethernet)
- **Network Access**: Camera must be on the same network as the LPR system or reachable via routing
- **Static IP**: Recommended to assign static IP address for consistent connectivity
- **Network Ports**: 
  - RTSP port (typically 554)
  - HTTP/HTTPS port (typically 80/443)
  - ONVIF port (typically 80) for discovery

### Video Specifications
- **Resolution**: Minimum 1920x1080 (Full HD) recommended for license plate recognition
- **Frame Rate**: Minimum 15 FPS, recommended 30 FPS
- **Codec Support**: H.264 or H.265 compression
- **Stream Types**: Main stream for recording, sub-stream for preview (optional)

### Camera Features
- **Image Quality**: Good low-light performance for 24/7 operation
- **Focus**: Auto-focus or manual focus with clear license plate visibility
- **Positioning**: Stable mounting with clear view of license plate area
- **Weather Resistance**: IP65 or higher rating for outdoor installation

## Software Requirements

### Camera Firmware
- **RTSP Support**: Must support RTSP streaming protocol
- **Authentication**: Support for username/password authentication
- **ONVIF Compliance**: Recommended for automatic discovery and configuration
- **Streaming Protocols**: Support for standard streaming protocols

### Network Configuration
- **Accessible IP**: Camera must be reachable from LPR system
- **Firewall**: Ensure required ports are open
- **Bandwidth**: Sufficient network bandwidth for video streaming

## System Configuration Requirements

### Database Prerequisites
- **Location**: Camera must be assigned to an existing location in the system
- **Unique IP**: IP address must be unique within the system
- **Database Connection**: System must have access to SQLite database

### Required Camera Information

#### Basic Information
- **Name**: Descriptive name for the camera (e.g., "Front Gate Camera")
- **IP Address**: Camera's network IP address
- **Location**: Must reference existing location in database

#### Authentication
- **Username**: Camera login username (commonly "admin")
- **Password**: Camera login password
- **Port**: RTSP port (default: 554)

#### Video Settings
- **Resolution**: Width x Height (e.g., 1920x1080)
- **FPS**: Frames per second (default: 30)
- **Codec**: Video compression format (default: H.264)
- **Stream Path**: RTSP stream path (if required by camera)

#### Optional Settings
- **Manufacturer**: Camera manufacturer name
- **Model**: Camera model number
- **Installation Location**: Physical installation description
- **Viewing Direction**: Camera viewing direction description

## Installation Process

### 1. Network Setup
```bash
# Test network connectivity
ping [camera_ip_address]

# Test RTSP stream
ffplay rtsp://username:password@[camera_ip_address]:554/stream1
```

### 2. Camera Discovery
- Use the system's camera discovery feature
- Scan network range containing the camera
- Verify camera is detected and accessible

### 3. Test Connection
- Use the "Test Connection" feature in the UI
- Verify authentication credentials
- Confirm video stream accessibility
- Check resolution and frame rate

### 4. Camera Registration
- Fill out camera configuration form
- Assign to appropriate location
- Configure video settings
- Save camera configuration

## API Endpoints

### Camera Management
- `POST /api/cameras/` - Create new camera
- `GET /api/cameras/{camera_id}` - Get camera details
- `PUT /api/cameras/{camera_id}` - Update camera settings
- `DELETE /api/cameras/{camera_id}` - Remove camera

### Camera Testing
- `POST /api/cameras/test-connection` - Test camera connectivity
- `POST /api/cameras/discover` - Discover cameras on network

### Camera Control
- `POST /api/cameras/{camera_id}/start` - Start camera stream
- `POST /api/cameras/{camera_id}/stop` - Stop camera stream
- `GET /api/cameras/{camera_id}/snapshot` - Get camera snapshot

## Common Camera Configurations

### Generic IP Camera
```json
{
    "name": "Front Door Camera",
    "ip_address": "192.168.1.100",
    "location_id": "location_uuid",
    "username": "admin",
    "password": "password123",
    "port": 554,
    "resolution_width": 1920,
    "resolution_height": 1080,
    "fps": 30,
    "codec": "H.264",
    "stream_path": "/stream1"
}
```

### Hikvision Camera
```json
{
    "name": "Parking Lot Camera",
    "ip_address": "192.168.1.101",
    "location_id": "location_uuid",
    "manufacturer": "Hikvision",
    "model": "DS-2CD2085FWD-I",
    "username": "admin",
    "password": "password123",
    "port": 554,
    "resolution_width": 1920,
    "resolution_height": 1080,
    "fps": 25,
    "codec": "H.264",
    "stream_path": "/Streaming/Channels/101"
}
```

### Dahua Camera
```json
{
    "name": "Exit Gate Camera",
    "ip_address": "192.168.1.102",
    "location_id": "location_uuid",
    "manufacturer": "Dahua",
    "model": "IPC-HFW4431R-Z",
    "username": "admin",
    "password": "password123",
    "port": 554,
    "resolution_width": 1920,
    "resolution_height": 1080,
    "fps": 30,
    "codec": "H.264",
    "stream_path": "/cam/realmonitor?channel=1&subtype=0"
}
```

## Troubleshooting

### Common Issues

#### Connection Failed
- Verify IP address is correct and reachable
- Check username/password credentials
- Ensure camera is powered on and network connected
- Verify firewall settings allow camera ports

#### Stream Not Available
- Check RTSP port (typically 554)
- Verify stream path format for camera brand
- Ensure camera supports RTSP streaming
- Check network bandwidth and stability

#### Poor Video Quality
- Increase resolution settings
- Adjust FPS settings
- Check network bandwidth
- Verify camera focus and positioning

#### Authentication Errors
- Verify username/password are correct
- Check if camera requires specific authentication method
- Ensure camera user has streaming permissions

### Network Requirements
- **Minimum Bandwidth**: 2 Mbps per 1080p stream
- **Recommended Bandwidth**: 5 Mbps per 1080p stream
- **Latency**: Less than 100ms for optimal performance
- **Packet Loss**: Less than 1% for stable streaming

## Security Considerations

### Camera Security
- Change default passwords immediately
- Use strong passwords
- Enable firmware updates
- Disable unnecessary services

### Network Security
- Use VLANs to isolate camera network
- Implement firewall rules
- Monitor network traffic
- Regular security audits

### System Security
- Encrypt database connections
- Secure API endpoints
- Regular system updates
- Monitor system logs

## Performance Optimization

### Camera Settings
- Use appropriate resolution for license plate recognition
- Balance frame rate with storage requirements
- Configure compression settings for bandwidth optimization
- Set appropriate bit rate for quality vs. bandwidth

### System Configuration
- Limit concurrent camera streams based on system resources
- Configure appropriate buffer sizes
- Monitor system performance metrics
- Scale system resources as needed

## Supported Camera Brands

### Tested Brands
- Hikvision
- Dahua
- Axis
- Bosch
- Uniview
- Reolink

### Generic Support
- Any IP camera supporting RTSP streaming
- ONVIF compliant cameras
- Cameras with HTTP/HTTPS access
- Standard authentication methods

## Future Enhancements

### Planned Features
- Automatic camera discovery via ONVIF
- PTZ (Pan-Tilt-Zoom) camera support
- Advanced analytics configuration
- Multi-stream support per camera
- Camera health monitoring
- Automated camera configuration backup

### Integration Possibilities
- Video Management Systems (VMS)
- Access Control Systems
- Alarm Systems
- Cloud storage integration
- Mobile app connectivity

---

**Note**: This document should be updated as new camera models are tested and system capabilities are expanded.