# API Endpoint Organization

## Summary by Category

### System Health & Configuration (5 endpoints)
- Basic health checks and system status
- Feature configuration management
- WebSocket status for real-time updates
- Debug endpoints for development

### Camera Management (16 endpoints) 
**Largest category - core system functionality**
- **CRUD Operations**: Add, update, delete, list cameras
- **Control Operations**: Start, stop, restart individual or all cameras  
- **Health & Diagnostics**: Monitor camera status, run diagnostics
- **Media Operations**: Snapshots, quality control, external viewing

### ONVIF Integration (4 endpoints)
- Network camera discovery
- Brand compatibility checking  
- Automated camera addition from discovery

### Detection Management (11 endpoints)
**Second largest category - core detection functionality**
- **Query Operations**: Recent, search, similar plates, history
- **Analytics**: Statistics and detection metrics
- **Quality Assessment**: Detection quality analysis

### Analytics & Quality (5 endpoints)
- System-wide analytics overview
- Quality metrics and threshold management
- Quality-based filtering capabilities

### Storage Management (3 endpoints)
- Storage usage monitoring
- Routine and emergency cleanup operations

### Video Management (1 endpoint)
- Video clip retrieval and playback

## Functional Groupings

### Real-time Operations (8 endpoints)
```
/ws/status - Live status updates
/api/cameras/{id}/snapshot - Real-time camera frames
/api/detections/recent - Live detection feed
/api/cameras/health/summary - Live health status
/api/cameras/health/detailed - Detailed live health
/api/system/health - System status
/api/cameras/{id}/health - Camera-specific health
/api/cameras/{id}/diagnostics - Real-time diagnostics
```

### Configuration Management (7 endpoints)
```
/api/config/features - Feature toggles
/api/cameras [POST] - Add camera
/api/cameras/{id} [PUT] - Update camera
/api/cameras/{id} [DELETE] - Remove camera
/api/quality/thresholds - Quality settings
/api/cameras/{id}/recording/quality [POST] - Quality config
/api/onvif/add/{ip} - Add discovered camera
```

### Data Retrieval (15 endpoints)
```
/api/cameras - List all cameras
/api/cameras/list - Basic camera list
/api/cameras/{id} - Camera details
/api/detections/search - Search detections
/api/detections/similar/{plate} - Similar plates
/api/detections/history/{plate} - Plate history
/api/detections/stats - Detection statistics
/api/detections/{id} - Detection details
/api/analytics/overview - System analytics
/api/quality/metrics - Quality data
/api/storage/stats - Storage information
/api/onvif/discovered - Discovery results
/api/onvif/brands - Supported brands
/api/detections/object-types - Detection types
/api/video/clip/{id} - Video retrieval
```

### Control Operations (12 endpoints)
```
/api/cameras/{id}/test - Test connection
/api/cameras/{id}/start - Start camera
/api/cameras/{id}/stop - Stop camera
/api/cameras/{id}/restart - Restart camera
/api/cameras/restart/all - Restart all
/api/cameras/test - Test multiple
/api/cameras/test-all-paths - Test all paths
/api/onvif/discover - Discover cameras
/api/storage/cleanup - Cleanup storage
/api/storage/emergency-cleanup - Emergency cleanup
/api/quality/filter - Apply quality filter
/api/cameras/{id}/open-vlc - Open in VLC
```

## Usage Patterns

### Dashboard Endpoints (High Frequency)
- `/api/detections/recent` - Main detection feed
- `/api/cameras` - Camera status overview
- `/api/system/health` - System status
- `/ws/status` - Real-time updates

### Administrative Endpoints (Medium Frequency)
- Camera management CRUD operations
- Storage and quality management
- Analytics and reporting

### Setup/Configuration Endpoints (Low Frequency)
- ONVIF discovery and setup
- Feature configuration
- Quality threshold management

## API Maturity Assessment

### ✅ Mature & Stable
- Camera CRUD operations (consistent patterns)
- Health monitoring (comprehensive coverage)
- Detection queries (multiple access patterns)
- System health (reliable status reporting)

### ⚠️ Functional but Needs Refinement  
- ONVIF integration (newer feature)
- Quality management (evolving metrics)
- Video clip management (single endpoint)

### 🔄 Areas for Enhancement
- Authentication/authorization (currently open)
- Rate limiting (no current limits)
- API versioning (all in v1 implied)
- Batch operations (limited bulk support)

## Performance Considerations

### High-Traffic Endpoints
1. `/api/detections/recent` - Main dashboard feed
2. `/ws/status` - WebSocket real-time updates  
3. `/api/cameras` - Status polling
4. `/api/cameras/{id}/snapshot` - Live image requests

### Resource-Intensive Endpoints
1. `/api/onvif/discover` - Network scanning
2. `/api/cameras/test-all-paths` - Multiple connection tests
3. `/api/storage/cleanup` - File system operations
4. `/api/cameras/{id}/diagnostics` - Comprehensive testing

## Security Considerations

### Public Endpoints (Current State)
All 52 endpoints currently accessible without authentication

### Recommended Security Tiers
1. **Public**: Health checks, basic status
2. **Read-Only**: Detection queries, camera status  
3. **Operator**: Camera control, snapshots
4. **Admin**: Camera CRUD, storage management, system control

Total: **52 endpoints** organized across **7 functional categories** with clear usage patterns and security considerations.