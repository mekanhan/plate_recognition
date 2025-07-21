# Design Document

## Overview

The IP Camera Setup feature is a comprehensive 4-step wizard system that enables system administrators to seamlessly add new IP cameras to the License Plate Recognition (LPR) system. The design leverages existing services and infrastructure while introducing new components for camera discovery, manufacturer database integration, and enhanced connection testing.

The system follows a progressive disclosure pattern, guiding users through increasingly technical configuration steps while providing intelligent defaults and auto-configuration capabilities. The design emphasizes user experience, error recovery, and integration with the existing centralized LPR architecture.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web UI Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│  Camera Setup Wizard (4-Step Modal)                            │
│  ├─ Step 1: Basic Information                                  │
│  ├─ Step 2: Network Discovery                                  │
│  ├─ Step 3: Connection Testing                                 │
│  └─ Step 4: Stream Preview & Save                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Layer                                    │
├─────────────────────────────────────────────────────────────────┤
│  Camera Router (/api/cameras)                                  │
│  ├─ POST /test-connection                                      │
│  ├─ POST /test-connection-enhanced                             │
│  ├─ POST /discover                                             │
│  ├─ GET /manufacturers                                         │
│  └─ POST / (create camera)                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Service Layer                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Camera Discovery│  │ Manufacturer DB │  │ Multi-Camera    │ │
│  │ Service         │  │ Service         │  │ Service         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Camera Registry │  │ Location        │  │ Connection Test │ │
│  │ Service         │  │ Service         │  │ Service         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Data Layer                                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Camera Model    │  │ Location Model  │  │ CameraHealth    │ │
│  │ (SQLAlchemy)    │  │ (SQLAlchemy)    │  │ Model           │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Integration

The design integrates with existing system components:

- **MultiCameraService**: Manages camera streams and health monitoring
- **CameraRegistryService**: Handles camera registration and grouping
- **LocationService**: Manages physical locations and site organization
- **ManufacturerDatabaseService**: Provides vendor-specific configurations
- **CameraDiscoveryService**: Performs network scanning and device detection

## Components and Interfaces

### 1. Camera Setup Wizard (Frontend)

**Technology**: HTML5, CSS3, JavaScript (ES6+)
**Framework**: Vanilla JS with existing UI component system

#### Component Structure
```javascript
class CameraSetupWizard {
    constructor(options = {}) {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.formData = new CameraFormData();
        this.validationRules = new ValidationRules();
        this.apiClient = new CameraAPIClient();
    }
    
    // Step management
    async nextStep();
    async previousStep();
    async validateCurrentStep();
    
    // Data management
    updateFormData(field, value);
    preserveFormData();
    restoreFormData();
    
    // API integration
    async testConnection();
    async discoverCameras();
    async saveCamera();
}
```

#### Step Components

**Step 1: Basic Information**
- Camera name input with validation
- Location dropdown (populated from LocationService)
- Manufacturer dropdown with auto-complete
- Model input with suggestions based on manufacturer
- Form validation with real-time feedback

**Step 2: Network Discovery**
- Discovery method selection (Auto/Manual)
- IP address input with validation
- Network scanning interface with progress indicators
- Discovered cameras list with selection capability
- Manual configuration fallback

**Step 3: Connection Configuration**
- Connection type selector (RTSP, HTTP, HTTPS, ONVIF)
- Port and stream path inputs with auto-population
- Authentication credentials (username/password)
- Connection testing with detailed feedback
- Troubleshooting suggestions for failures

**Step 4: Stream Preview**
- Available streams display with technical details
- Live preview player with controls
- Stream quality testing
- Configuration summary
- Save confirmation

### 2. Camera Discovery Service (Backend)

**File**: `app/services/camera_discovery_service.py`
**Status**: Existing (Enhanced)

#### Enhanced Capabilities
```python
class CameraDiscoveryService:
    async def discover_cameras_on_network(
        self, 
        ip_range: str = "192.168.1.0/24",
        methods: List[DiscoveryMethod] = None,
        port_config: Dict[str, List[int]] = None
    ) -> List[DiscoveredCamera]:
        """Enhanced network discovery with multiple methods"""
        
    async def test_camera_connection_enhanced(
        self,
        ip_address: str,
        manufacturer: str,
        connection_type: str,
        credentials: Dict[str, str]
    ) -> ConnectionTestResult:
        """Enhanced connection testing with manufacturer integration"""
        
    async def get_camera_streams(
        self,
        ip_address: str,
        credentials: Dict[str, str]
    ) -> List[StreamInfo]:
        """Discover available video streams"""
```

#### Discovery Methods
1. **ONVIF Discovery**: Standards-based device discovery
2. **HTTP Probing**: Web interface detection
3. **RTSP Probing**: Stream endpoint testing
4. **Vendor API**: Manufacturer-specific protocols
5. **UPnP Discovery**: Universal Plug and Play detection

### 3. Manufacturer Database Service (Backend)

**File**: `app/services/manufacturer_database_service.py`
**Status**: Existing (Enhanced)

#### Enhanced Features
```python
class ManufacturerDatabaseService:
    def get_manufacturer_suggestions(self, query: str) -> List[Dict]:
        """Get manufacturer suggestions based on search query"""
        
    def auto_configure_camera(
        self, 
        manufacturer: str, 
        model: str,
        connection_type: str
    ) -> CameraConfiguration:
        """Auto-configure camera based on manufacturer database"""
        
    def validate_configuration(
        self,
        manufacturer: str,
        connection_type: str,
        stream_path: str
    ) -> ValidationResult:
        """Validate camera configuration against known specifications"""
```

#### Manufacturer Database Schema
```python
@dataclass
class ManufacturerConfig:
    name: str
    common_models: List[str]
    default_ports: Dict[str, int]
    stream_paths: Dict[str, str]
    default_auth: str
    default_username: str
    supported_codecs: List[str]
    capabilities: List[str]
```

### 4. Connection Testing Service (New)

**File**: `app/services/connection_test_service.py`
**Status**: New Component

```python
class ConnectionTestService:
    async def test_basic_connectivity(self, ip_address: str) -> ConnectivityResult:
        """Test basic network connectivity (ping, port scan)"""
        
    async def test_authentication(
        self, 
        url: str, 
        credentials: Dict[str, str]
    ) -> AuthResult:
        """Test camera authentication"""
        
    async def test_stream_access(
        self, 
        stream_url: str,
        timeout: int = 10
    ) -> StreamTestResult:
        """Test stream accessibility and quality"""
        
    async def get_stream_capabilities(
        self,
        stream_url: str
    ) -> StreamCapabilities:
        """Analyze stream capabilities (codecs, resolution, fps)"""
```

### 5. Stream Preview Service (New)

**File**: `app/services/stream_preview_service.py`
**Status**: New Component

```python
class StreamPreviewService:
    async def start_preview_session(
        self,
        camera_config: Dict[str, Any]
    ) -> PreviewSession:
        """Start a temporary preview session"""
        
    async def capture_snapshot(
        self,
        session_id: str
    ) -> SnapshotResult:
        """Capture a snapshot from preview stream"""
        
    async def test_stream_stability(
        self,
        session_id: str,
        duration: int = 30
    ) -> StabilityResult:
        """Test stream stability and quality metrics"""
        
    async def stop_preview_session(self, session_id: str) -> bool:
        """Stop and cleanup preview session"""
```

## Data Models

### Enhanced Camera Model

The existing `Camera` model in `app/models.py` already supports the required fields:

```python
class Camera(Base):
    # Basic identification
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location_id = Column(String, ForeignKey("locations.id"))
    
    # Network configuration
    ip_address = Column(String, unique=True)
    port = Column(Integer, default=554)
    connection_type = Column(String, default="rtsp")
    stream_path = Column(String)
    username = Column(String)
    password_hash = Column(String)
    
    # Manufacturer integration
    manufacturer = Column(String)
    model = Column(String)
    manufacturer_config = Column(JSON)
    
    # Connection test results
    connection_test_results = Column(JSON)
    last_tested_at = Column(DateTime)
    last_successful_connection = Column(DateTime)
    
    # Stream configuration
    main_stream_url = Column(String)
    sub_stream_url = Column(String)
    snapshot_url = Column(String)
```

### New Data Transfer Objects

```python
@dataclass
class CameraSetupRequest:
    """Request object for camera setup wizard"""
    step: int
    name: str
    location_id: str
    manufacturer: str
    model: str
    ip_address: str
    connection_type: str
    port: int
    stream_path: str
    username: str
    password: str
    discovery_method: str

@dataclass
class ConnectionTestResult:
    """Result of connection testing"""
    success: bool
    response_time_ms: float
    error_message: Optional[str]
    capabilities: List[str]
    suggested_streams: List[Dict[str, Any]]
    warnings: List[str]

@dataclass
class DiscoveredCamera:
    """Discovered camera information"""
    ip_address: str
    manufacturer: str
    model: str
    supported_protocols: List[str]
    confidence_score: float
    discovery_method: str
```

## Error Handling

### Error Categories

1. **Network Errors**: Connection timeouts, unreachable hosts
2. **Authentication Errors**: Invalid credentials, authorization failures
3. **Protocol Errors**: Unsupported formats, malformed responses
4. **Configuration Errors**: Invalid parameters, conflicting settings
5. **System Errors**: Database failures, service unavailability

### Error Response Format

```python
class ErrorResponse(BaseModel):
    error_type: str
    message: str
    details: Optional[Dict[str, Any]]
    suggestions: List[str]
    retry_possible: bool
    timestamp: datetime
```

### Error Recovery Strategies

1. **Automatic Retry**: For transient network issues
2. **Fallback Methods**: Alternative discovery/connection methods
3. **User Guidance**: Clear instructions for manual resolution
4. **Graceful Degradation**: Partial functionality when possible

### User-Friendly Error Messages

```python
ERROR_MESSAGES = {
    "connection_timeout": {
        "message": "Unable to connect to camera",
        "suggestions": [
            "Check if camera is powered on",
            "Verify IP address is correct",
            "Ensure camera is on same network"
        ]
    },
    "authentication_failed": {
        "message": "Camera credentials are incorrect",
        "suggestions": [
            "Verify username and password",
            "Try default credentials for manufacturer",
            "Check if camera requires admin setup"
        ]
    },
    "stream_not_accessible": {
        "message": "Camera stream is not accessible",
        "suggestions": [
            "Check stream path configuration",
            "Verify camera supports selected protocol",
            "Try alternative stream paths"
        ]
    }
}
```

## Testing Strategy

### Unit Testing

1. **Service Layer Tests**
   - Camera discovery methods
   - Manufacturer database queries
   - Connection testing logic
   - Stream preview functionality

2. **API Endpoint Tests**
   - Request/response validation
   - Error handling scenarios
   - Authentication and authorization

3. **Frontend Component Tests**
   - Wizard step navigation
   - Form validation
   - API integration
   - Error state handling

### Integration Testing

1. **End-to-End Wizard Flow**
   - Complete camera setup process
   - Data persistence verification
   - Service integration validation

2. **Network Discovery Testing**
   - Mock camera responses
   - Various network configurations
   - Error scenario simulation

3. **Connection Testing**
   - Multiple camera manufacturers
   - Different protocol combinations
   - Authentication methods

### Performance Testing

1. **Network Scanning Performance**
   - Large IP range scanning
   - Concurrent discovery operations
   - Timeout handling

2. **Stream Preview Performance**
   - Multiple simultaneous previews
   - Memory usage monitoring
   - Resource cleanup verification

### Security Testing

1. **Credential Handling**
   - Password encryption/decryption
   - Secure transmission
   - Storage security

2. **Network Security**
   - Input validation
   - Injection attack prevention
   - Rate limiting

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- Enhanced connection testing service
- Stream preview service implementation
- API endpoint development
- Basic wizard UI structure

### Phase 2: Discovery & Configuration (Week 3-4)
- Network discovery integration
- Manufacturer database enhancements
- Auto-configuration logic
- Advanced error handling

### Phase 3: User Experience (Week 5-6)
- Complete wizard UI implementation
- Real-time validation
- Progress indicators
- Responsive design

### Phase 4: Testing & Polish (Week 7-8)
- Comprehensive testing suite
- Performance optimization
- Documentation
- User acceptance testing

## Security Considerations

### Data Protection
- Camera credentials encrypted at rest
- Secure transmission using HTTPS/WSS
- Session-based authentication for preview streams

### Network Security
- Input validation for all network parameters
- Rate limiting for discovery operations
- Timeout controls for all network operations

### Access Control
- Role-based access to camera setup
- Audit logging for configuration changes
- Secure credential storage and retrieval

## Performance Considerations

### Scalability
- Concurrent camera discovery (max 50 simultaneous)
- Efficient database queries with proper indexing
- Connection pooling for API requests

### Resource Management
- Preview session cleanup and timeouts
- Memory management for stream buffers
- CPU usage optimization for discovery operations

### Caching Strategy
- Manufacturer database caching
- Discovery results caching (1-hour TTL)
- Stream capability caching

## Monitoring and Observability

### Metrics Collection
- Discovery success/failure rates
- Connection test performance
- Setup completion rates
- Error frequency by type

### Logging Strategy
- Structured logging with correlation IDs
- Debug logs for troubleshooting
- Audit logs for security events

### Health Checks
- Service availability monitoring
- Database connectivity checks
- External dependency health

This design provides a comprehensive foundation for implementing the IP Camera Setup feature while leveraging existing system architecture and ensuring scalability, security, and maintainability.