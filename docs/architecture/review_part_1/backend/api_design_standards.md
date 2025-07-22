# API Design Standards for LPR System

**Version:** 1.0  
**Date:** 2025-01-09  
**Authors:** System Architecture Team  
**Status:** Active Development  

## Table of Contents

1. [API Design Principles](#api-design-principles)
2. [RESTful API Standards](#restful-api-standards)
3. [HTTP Status Codes](#http-status-codes)
4. [Request/Response Formats](#request-response-formats)
5. [Error Handling](#error-handling)
6. [Authentication & Authorization](#authentication--authorization)
7. [API Versioning](#api-versioning)
8. [Rate Limiting](#rate-limiting)
9. [Documentation Standards](#documentation-standards)
10. [Testing Standards](#testing-standards)
11. [Performance Guidelines](#performance-guidelines)
12. [Security Standards](#security-standards)

## API Design Principles

### 1. Consistency
- Uniform naming conventions across all endpoints
- Consistent response formats and structures
- Standardized error handling patterns
- Common authentication mechanisms

### 2. Simplicity
- Intuitive endpoint URLs and parameter names
- Minimal number of required parameters
- Clear and concise response structures
- Self-documenting API behavior

### 3. Reliability
- Idempotent operations where appropriate
- Graceful error handling and recovery
- Comprehensive input validation
- Proper transaction handling

### 4. Scalability
- Efficient resource utilization
- Pagination for large datasets
- Caching strategies
- Rate limiting and throttling

### 5. Security
- Authentication and authorization
- Input sanitization and validation
- Secure communication protocols
- Data privacy protection

## RESTful API Standards

### Resource Naming Conventions

#### URL Structure
```
https://api.lpr.company.com/v1/{resource-collection}/{resource-id}/{sub-resource}
```

#### Resource Collections (Plural Nouns)
```
GET    /cameras              # List all cameras
POST   /cameras              # Create new camera
GET    /cameras/{id}         # Get specific camera
PUT    /cameras/{id}         # Update camera
DELETE /cameras/{id}         # Delete camera
```

#### Sub-resources
```
GET    /cameras/{id}/detections     # Get camera detections
POST   /cameras/{id}/detections     # Create detection for camera
GET    /cameras/{id}/health         # Get camera health status
PUT    /cameras/{id}/configuration  # Update camera configuration
```

#### Query Parameters
```
GET /cameras?status=active&location=parking-lot-1&limit=20&offset=0
GET /detections?camera_id=cam_001&from=2025-01-01&to=2025-01-31
GET /analytics/reports?type=daily&date=2025-01-09&format=json
```

### HTTP Methods

#### GET (Retrieve Resources)
```python
@router.get("/cameras")
async def list_cameras(
    status: Optional[CameraStatus] = None,
    location: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> CameraListResponse:
    """List cameras with optional filtering and pagination"""
    pass

@router.get("/cameras/{camera_id}")
async def get_camera(
    camera_id: str = Path(..., description="Camera identifier")
) -> CameraResponse:
    """Get specific camera details"""
    pass
```

#### POST (Create Resources)
```python
@router.post("/cameras", status_code=201)
async def create_camera(
    camera: CreateCameraRequest
) -> CameraResponse:
    """Create new camera"""
    pass

@router.post("/cameras/{camera_id}/detections")
async def create_detection(
    camera_id: str,
    detection: CreateDetectionRequest
) -> DetectionResponse:
    """Create detection for specific camera"""
    pass
```

#### PUT (Update Resources)
```python
@router.put("/cameras/{camera_id}")
async def update_camera(
    camera_id: str,
    camera: UpdateCameraRequest
) -> CameraResponse:
    """Update camera (full replacement)"""
    pass

@router.put("/cameras/{camera_id}/configuration")
async def update_camera_configuration(
    camera_id: str,
    config: CameraConfigurationRequest
) -> CameraConfigurationResponse:
    """Update camera configuration"""
    pass
```

#### PATCH (Partial Updates)
```python
@router.patch("/cameras/{camera_id}")
async def patch_camera(
    camera_id: str,
    camera: PatchCameraRequest
) -> CameraResponse:
    """Partially update camera"""
    pass
```

#### DELETE (Remove Resources)
```python
@router.delete("/cameras/{camera_id}", status_code=204)
async def delete_camera(
    camera_id: str
) -> None:
    """Delete camera"""
    pass
```

### Resource Relationships

#### Parent-Child Relationships
```python
# Cameras and their detections
GET /cameras/{camera_id}/detections
POST /cameras/{camera_id}/detections

# Detections and their enhancements
GET /detections/{detection_id}/enhancements
POST /detections/{detection_id}/enhancements
```

#### Related Resources
```python
# Camera health status
GET /cameras/{camera_id}/health
GET /health/cameras/{camera_id}  # Alternative approach

# System analytics
GET /analytics/cameras/{camera_id}
GET /analytics/detections?camera_id={camera_id}
```

## HTTP Status Codes

### Success Codes (2xx)

#### 200 OK
```python
@router.get("/cameras/{camera_id}")
async def get_camera(camera_id: str) -> CameraResponse:
    """Returns existing resource"""
    camera = await camera_service.get_camera(camera_id)
    return CameraResponse.from_domain(camera)
```

#### 201 Created
```python
@router.post("/cameras", status_code=201)
async def create_camera(camera: CreateCameraRequest) -> CameraResponse:
    """Returns newly created resource"""
    created_camera = await camera_service.create_camera(camera)
    return CameraResponse.from_domain(created_camera)
```

#### 204 No Content
```python
@router.delete("/cameras/{camera_id}", status_code=204)
async def delete_camera(camera_id: str) -> None:
    """Successful deletion with no response body"""
    await camera_service.delete_camera(camera_id)
```

### Client Error Codes (4xx)

#### 400 Bad Request
```python
# Invalid request format or validation errors
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request data",
        "details": [
            {
                "field": "frame_rate",
                "message": "Frame rate must be between 1 and 60"
            }
        ]
    }
}
```

#### 401 Unauthorized
```python
# Missing or invalid authentication
{
    "error": {
        "code": "AUTHENTICATION_REQUIRED",
        "message": "Authentication credentials are required"
    }
}
```

#### 403 Forbidden
```python
# Insufficient permissions
{
    "error": {
        "code": "INSUFFICIENT_PERMISSIONS",
        "message": "User does not have permission to access this resource"
    }
}
```

#### 404 Not Found
```python
# Resource not found
{
    "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Camera with ID 'cam_001' not found"
    }
}
```

#### 409 Conflict
```python
# Resource conflict
{
    "error": {
        "code": "RESOURCE_CONFLICT",
        "message": "Camera with IP address '192.168.1.100' already exists"
    }
}
```

#### 422 Unprocessable Entity
```python
# Semantic validation errors
{
    "error": {
        "code": "BUSINESS_RULE_VIOLATION",
        "message": "Camera cannot be activated without valid configuration"
    }
}
```

#### 429 Too Many Requests
```python
# Rate limiting exceeded
{
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Rate limit exceeded. Try again in 60 seconds.",
        "retry_after": 60
    }
}
```

### Server Error Codes (5xx)

#### 500 Internal Server Error
```python
# Unexpected server errors
{
    "error": {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
        "request_id": "req_123456789"
    }
}
```

#### 503 Service Unavailable
```python
# Service temporarily unavailable
{
    "error": {
        "code": "SERVICE_UNAVAILABLE",
        "message": "Detection service is temporarily unavailable",
        "retry_after": 30
    }
}
```

## Request/Response Formats

### Request Format Standards

#### JSON Request Body
```python
class CreateCameraRequest(BaseModel):
    """Standard request format for creating cameras"""
    name: str = Field(..., min_length=1, max_length=100, description="Camera name")
    ip_address: str = Field(..., regex=r'^(\d{1,3}\.){3}\d{1,3}$', description="Camera IP address")
    location: str = Field(..., min_length=1, max_length=200, description="Camera location")
    configuration: CameraConfigurationRequest = Field(..., description="Camera configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Parking Lot Camera 1",
                "ip_address": "192.168.1.100",
                "location": "Main entrance parking lot",
                "configuration": {
                    "stream_url": "rtsp://192.168.1.100:554/stream",
                    "resolution": {
                        "width": 1920,
                        "height": 1080
                    },
                    "frame_rate": 30,
                    "quality_settings": {
                        "compression": "h264",
                        "bitrate": 2000000
                    }
                }
            }
        }

class CameraConfigurationRequest(BaseModel):
    """Camera configuration request format"""
    stream_url: str = Field(..., description="Camera stream URL")
    resolution: ResolutionRequest = Field(..., description="Video resolution")
    frame_rate: int = Field(..., ge=1, le=60, description="Frames per second")
    quality_settings: QualitySettingsRequest = Field(..., description="Quality settings")
    
    @validator('stream_url')
    def validate_stream_url(cls, v):
        if not v.startswith(('rtsp://', 'http://', 'https://')):
            raise ValueError('Stream URL must start with rtsp://, http://, or https://')
        return v
```

#### Query Parameters
```python
class CameraListQueryParams(BaseModel):
    """Query parameters for listing cameras"""
    status: Optional[CameraStatus] = Field(None, description="Filter by camera status")
    location: Optional[str] = Field(None, description="Filter by location")
    limit: int = Field(20, ge=1, le=100, description="Number of results per page")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[SortOrder] = Field(SortOrder.DESC, description="Sort order")
    
    class Config:
        use_enum_values = True
```

### Response Format Standards

#### Success Response Format
```python
class CameraResponse(BaseModel):
    """Standard response format for camera resources"""
    id: str = Field(..., description="Camera identifier")
    name: str = Field(..., description="Camera name")
    ip_address: str = Field(..., description="Camera IP address")
    location: str = Field(..., description="Camera location")
    status: CameraStatus = Field(..., description="Camera status")
    configuration: CameraConfigurationResponse = Field(..., description="Camera configuration")
    health_status: HealthStatusResponse = Field(..., description="Camera health status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "cam_001",
                "name": "Parking Lot Camera 1",
                "ip_address": "192.168.1.100",
                "location": "Main entrance parking lot",
                "status": "active",
                "configuration": {
                    "stream_url": "rtsp://192.168.1.100:554/stream",
                    "resolution": {
                        "width": 1920,
                        "height": 1080
                    },
                    "frame_rate": 30
                },
                "health_status": {
                    "overall_status": "healthy",
                    "response_time": 150,
                    "connection_status": "connected",
                    "last_updated": "2025-01-09T10:30:00Z"
                },
                "created_at": "2025-01-09T09:00:00Z",
                "updated_at": "2025-01-09T10:30:00Z"
            }
        }

class CameraListResponse(BaseModel):
    """Standard response format for camera lists"""
    data: List[CameraResponse] = Field(..., description="List of cameras")
    pagination: PaginationResponse = Field(..., description="Pagination information")
    
    class Config:
        schema_extra = {
            "example": {
                "data": [
                    # Camera objects here
                ],
                "pagination": {
                    "total": 150,
                    "limit": 20,
                    "offset": 0,
                    "has_next": True,
                    "has_previous": False
                }
            }
        }

class PaginationResponse(BaseModel):
    """Standard pagination response format"""
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_next: bool = Field(..., description="Whether there are more items")
    has_previous: bool = Field(..., description="Whether there are previous items")
```

### Content Types

#### Supported Content Types
- `application/json` - Default for all API requests/responses
- `application/xml` - Alternative format for specific endpoints
- `multipart/form-data` - For file uploads (images, videos)
- `application/octet-stream` - For binary data

#### Content Negotiation
```python
@router.get("/cameras/{camera_id}")
async def get_camera(
    camera_id: str,
    accept: Optional[str] = Header("application/json")
) -> Union[CameraResponse, str]:
    """Support multiple response formats"""
    camera = await camera_service.get_camera(camera_id)
    
    if accept == "application/xml":
        return camera.to_xml()
    else:
        return CameraResponse.from_domain(camera)
```

## Error Handling

### Standard Error Response Format

#### Error Response Schema
```python
class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: ErrorDetail = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: str = Field(..., description="Request identifier for tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "details": [
                        {
                            "field": "ip_address",
                            "message": "Invalid IP address format"
                        }
                    ]
                },
                "timestamp": "2025-01-09T10:30:00Z",
                "request_id": "req_123456789"
            }
        }

class ErrorDetail(BaseModel):
    """Error detail information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[FieldError]] = Field(None, description="Detailed error information")

class FieldError(BaseModel):
    """Field-specific error information"""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Field error message")
    value: Optional[Any] = Field(None, description="Invalid value")
```

### Error Handling Implementation

#### Global Exception Handler
```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid request data",
                details=[
                    FieldError(
                        field=error["loc"][-1],
                        message=error["msg"],
                        value=error.get("input")
                    )
                    for error in exc.errors()
                ]
            ),
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4()))
        ).dict()
    )

@app.exception_handler(BusinessRuleViolationException)
async def business_rule_exception_handler(request: Request, exc: BusinessRuleViolationException):
    """Handle business rule violations"""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code="BUSINESS_RULE_VIOLATION",
                message=str(exc)
            ),
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4()))
        ).dict()
    )

@app.exception_handler(ResourceNotFoundException)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundException):
    """Handle resource not found errors"""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error=ErrorDetail(
                code="RESOURCE_NOT_FOUND",
                message=str(exc)
            ),
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4()))
        ).dict()
    )
```

### Error Codes Reference

#### Camera Management Errors
- `CAMERA_NOT_FOUND` - Camera with specified ID not found
- `CAMERA_ALREADY_EXISTS` - Camera with IP address already exists
- `CAMERA_NOT_CONFIGURED` - Camera not properly configured
- `CAMERA_ACTIVATION_FAILED` - Camera activation failed
- `CAMERA_HEALTH_CHECK_FAILED` - Camera health check failed

#### Detection Errors
- `DETECTION_NOT_FOUND` - Detection with specified ID not found
- `DETECTION_PROCESSING_FAILED` - Detection processing failed
- `INVALID_IMAGE_FORMAT` - Invalid image format provided
- `IMAGE_TOO_LARGE` - Image exceeds size limits
- `DETECTION_TIMEOUT` - Detection processing timed out

#### Configuration Errors
- `INVALID_CONFIGURATION` - Configuration validation failed
- `CONFIGURATION_NOT_FOUND` - Configuration not found
- `CONFIGURATION_LOCKED` - Configuration is locked for editing
- `PERMISSION_DENIED` - Insufficient permissions for operation

## Authentication & Authorization

### Authentication Methods

#### JWT Bearer Token Authentication
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Extract and validate JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = await user_service.get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user
```

#### API Key Authentication
```python
from fastapi import Header, HTTPException

async def validate_api_key(x_api_key: str = Header(...)) -> str:
    """Validate API key"""
    if not await api_key_service.is_valid(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key
```

### Authorization

#### Role-Based Access Control
```python
from functools import wraps
from typing import List

def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not user.has_permissions(permissions):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@router.post("/cameras")
@require_permissions(["camera:create"])
async def create_camera(
    camera: CreateCameraRequest,
    current_user: User = Depends(get_current_user)
) -> CameraResponse:
    """Create camera with permission check"""
    pass
```

#### Resource-Based Access Control
```python
async def check_camera_access(camera_id: str, user: User, action: str) -> bool:
    """Check if user has access to specific camera"""
    camera = await camera_service.get_camera(camera_id)
    if not camera:
        return False
    
    # Check if user has access to this camera's location
    if not user.has_location_access(camera.location):
        return False
    
    # Check if user has permission for this action
    permission = f"camera:{action}"
    return user.has_permission(permission)

@router.get("/cameras/{camera_id}")
async def get_camera(
    camera_id: str,
    current_user: User = Depends(get_current_user)
) -> CameraResponse:
    """Get camera with access control"""
    if not await check_camera_access(camera_id, current_user, "read"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    camera = await camera_service.get_camera(camera_id)
    return CameraResponse.from_domain(camera)
```

## API Versioning

### Versioning Strategy

#### URL Versioning (Recommended)
```python
# Version in URL path
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")

# Version-specific endpoints
@v1_router.get("/cameras")
async def list_cameras_v1() -> CameraListResponseV1:
    """Version 1 of camera list endpoint"""
    pass

@v2_router.get("/cameras")
async def list_cameras_v2() -> CameraListResponseV2:
    """Version 2 of camera list endpoint"""
    pass
```

#### Header Versioning (Alternative)
```python
from fastapi import Header

@router.get("/cameras")
async def list_cameras(
    api_version: str = Header("v1", alias="API-Version")
) -> Union[CameraListResponseV1, CameraListResponseV2]:
    """Version-aware camera list endpoint"""
    if api_version == "v1":
        return await list_cameras_v1()
    elif api_version == "v2":
        return await list_cameras_v2()
    else:
        raise HTTPException(status_code=400, detail="Unsupported API version")
```

### Version Migration

#### Backward Compatibility
```python
class CameraResponseV1(BaseModel):
    """Version 1 camera response format"""
    id: str
    name: str
    ip_address: str
    status: str

class CameraResponseV2(BaseModel):
    """Version 2 camera response format"""
    id: str
    name: str
    ip_address: str
    location: str  # New field
    status: CameraStatus  # Changed from string to enum
    health_status: HealthStatusResponse  # New field
    
    @classmethod
    def from_v1(cls, v1_response: CameraResponseV1) -> 'CameraResponseV2':
        """Convert V1 response to V2 format"""
        return cls(
            id=v1_response.id,
            name=v1_response.name,
            ip_address=v1_response.ip_address,
            location="Unknown",  # Default value for new field
            status=CameraStatus(v1_response.status),
            health_status=HealthStatusResponse(overall_status="unknown")
        )
```

#### Deprecation Strategy
```python
@router.get("/cameras", deprecated=True)
async def list_cameras_deprecated() -> CameraListResponseV1:
    """Deprecated endpoint - use /api/v2/cameras instead"""
    response = await list_cameras_v2()
    
    # Add deprecation warning header
    headers = {
        "Deprecation": "true",
        "Sunset": "2025-12-31",
        "Link": '</api/v2/cameras>; rel="successor-version"'
    }
    
    return JSONResponse(
        content=response.dict(),
        headers=headers
    )
```

## Rate Limiting

### Rate Limiting Implementation

#### Token Bucket Algorithm
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/detections")
@limiter.limit("100/minute")
async def create_detection(
    request: Request,
    detection: CreateDetectionRequest
) -> DetectionResponse:
    """Create detection with rate limiting"""
    pass
```

#### User-Based Rate Limiting
```python
def get_user_id(request: Request) -> str:
    """Extract user ID from request for rate limiting"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub", "anonymous")
    except JWTError:
        return "anonymous"

user_limiter = Limiter(key_func=get_user_id)

@router.post("/analytics/reports")
@user_limiter.limit("10/hour")
async def generate_report(
    request: Request,
    report_request: ReportRequest
) -> ReportResponse:
    """Generate report with user-based rate limiting"""
    pass
```

### Rate Limit Headers

#### Standard Rate Limit Headers
```python
from fastapi import Response

@router.get("/cameras")
@limiter.limit("1000/hour")
async def list_cameras(
    request: Request,
    response: Response
) -> CameraListResponse:
    """List cameras with rate limit headers"""
    # Rate limit headers are automatically added by slowapi
    # X-RateLimit-Limit: 1000
    # X-RateLimit-Remaining: 999
    # X-RateLimit-Reset: 1641768000
    
    cameras = await camera_service.list_cameras()
    return CameraListResponse(data=cameras)
```

## Documentation Standards

### OpenAPI Specification

#### Complete OpenAPI Schema
```yaml
openapi: 3.0.0
info:
  title: License Plate Recognition API
  version: 2.0.0
  description: |
    Enterprise License Plate Recognition System API
    
    This API provides comprehensive license plate recognition capabilities including:
    - Camera management and monitoring
    - Video processing and recording
    - License plate detection and recognition
    - Analytics and reporting
    
    ## Authentication
    
    All API endpoints require authentication using JWT Bearer tokens.
    
    ## Rate Limiting
    
    API requests are rate limited to prevent abuse. Rate limits vary by endpoint
    and user type. Rate limit information is included in response headers.
    
    ## Error Handling
    
    All errors follow a consistent format with error codes, messages, and
    detailed information where applicable.
  
  contact:
    name: API Support Team
    email: api-support@company.com
    url: https://support.company.com
  
  license:
    name: Commercial License
    url: https://company.com/license

servers:
  - url: https://api.lpr.company.com/v2
    description: Production server
  - url: https://api-staging.lpr.company.com/v2
    description: Staging server
  - url: https://api-dev.lpr.company.com/v2
    description: Development server

security:
  - bearerAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Camera:
      type: object
      required:
        - id
        - name
        - ip_address
        - location
        - status
      properties:
        id:
          type: string
          description: Unique camera identifier
          example: "cam_001"
        name:
          type: string
          description: Human-readable camera name
          example: "Parking Lot Camera 1"
        ip_address:
          type: string
          format: ipv4
          description: Camera IP address
          example: "192.168.1.100"
        location:
          type: string
          description: Camera physical location
          example: "Main entrance parking lot"
        status:
          $ref: '#/components/schemas/CameraStatus'
        configuration:
          $ref: '#/components/schemas/CameraConfiguration'
        health_status:
          $ref: '#/components/schemas/HealthStatus'
        created_at:
          type: string
          format: date-time
          description: Camera creation timestamp
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp

    CameraStatus:
      type: string
      enum:
        - active
        - inactive
        - error
        - maintenance
      description: Camera operational status

    Error:
      type: object
      required:
        - error
        - timestamp
        - request_id
      properties:
        error:
          type: object
          required:
            - code
            - message
          properties:
            code:
              type: string
              description: Error code
            message:
              type: string
              description: Human-readable error message
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  message:
                    type: string
        timestamp:
          type: string
          format: date-time
        request_id:
          type: string
          description: Request identifier for tracking

paths:
  /cameras:
    get:
      summary: List cameras
      description: Retrieve a list of cameras with optional filtering and pagination
      operationId: listCameras
      parameters:
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/CameraStatus'
          description: Filter by camera status
        - name: location
          in: query
          schema:
            type: string
          description: Filter by camera location
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
          description: Number of results per page
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
          description: Number of results to skip
      responses:
        '200':
          description: List of cameras
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Camera'
                  pagination:
                    type: object
                    properties:
                      total:
                        type: integer
                      limit:
                        type: integer
                      offset:
                        type: integer
                      has_next:
                        type: boolean
                      has_previous:
                        type: boolean
        '401':
          description: Authentication required
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Insufficient permissions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security:
        - bearerAuth: []
      tags:
        - Cameras
```

### Endpoint Documentation

#### Comprehensive Endpoint Documentation
```python
@router.post("/cameras/{camera_id}/detections")
async def create_detection(
    camera_id: str = Path(
        ...,
        description="Camera identifier",
        example="cam_001"
    ),
    detection: CreateDetectionRequest = Body(
        ...,
        description="Detection request data"
    ),
    current_user: User = Depends(get_current_user)
) -> DetectionResponse:
    """
    Create a new detection for a specific camera.
    
    This endpoint processes an image from a camera and attempts to detect
    license plates. The detection process includes:
    
    1. Image validation and preprocessing
    2. License plate detection using YOLO models
    3. OCR processing for text recognition
    4. Confidence scoring and validation
    5. Storage of results and metadata
    
    ## Request Format
    
    The request must include:
    - `image_data`: Base64-encoded image data
    - `timestamp`: When the image was captured
    - `metadata`: Additional image metadata (optional)
    
    ## Response Format
    
    The response includes:
    - `detection_id`: Unique identifier for the detection
    - `results`: List of detected license plates
    - `processing_time`: Time taken for processing
    - `confidence`: Overall confidence score
    
    ## Error Handling
    
    Common errors include:
    - `400`: Invalid image format or size
    - `404`: Camera not found
    - `422`: Detection processing failed
    - `429`: Rate limit exceeded
    
    ## Rate Limiting
    
    This endpoint is rate limited to 100 requests per minute per user.
    
    ## Example
    
    ```json
    {
        "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
        "timestamp": "2025-01-09T10:30:00Z",
        "metadata": {
            "camera_resolution": "1920x1080",
            "weather_conditions": "clear"
        }
    }
    ```
    """
    pass
```

## Testing Standards

### Unit Testing

#### API Endpoint Testing
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

@pytest.fixture
def mock_camera_service():
    with patch('app.services.camera_service.CameraService') as mock:
        yield mock

class TestCameraEndpoints:
    def test_list_cameras_success(self, client, mock_camera_service):
        """Test successful camera list retrieval"""
        # Arrange
        mock_cameras = [
            Camera(id="cam_001", name="Test Camera 1"),
            Camera(id="cam_002", name="Test Camera 2")
        ]
        mock_camera_service.list_cameras.return_value = mock_cameras
        
        # Act
        response = client.get("/api/v1/cameras")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "cam_001"
    
    def test_list_cameras_with_filters(self, client, mock_camera_service):
        """Test camera list with filters"""
        # Arrange
        mock_camera_service.list_cameras.return_value = []
        
        # Act
        response = client.get("/api/v1/cameras?status=active&location=parking")
        
        # Assert
        assert response.status_code == 200
        mock_camera_service.list_cameras.assert_called_once_with(
            status="active",
            location="parking",
            limit=20,
            offset=0
        )
    
    def test_create_camera_success(self, client, mock_camera_service):
        """Test successful camera creation"""
        # Arrange
        camera_data = {
            "name": "New Camera",
            "ip_address": "192.168.1.100",
            "location": "Test Location",
            "configuration": {
                "stream_url": "rtsp://192.168.1.100:554/stream",
                "resolution": {"width": 1920, "height": 1080},
                "frame_rate": 30
            }
        }
        mock_camera = Camera(id="cam_003", name="New Camera")
        mock_camera_service.create_camera.return_value = mock_camera
        
        # Act
        response = client.post("/api/v1/cameras", json=camera_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "cam_003"
        assert data["name"] == "New Camera"
    
    def test_create_camera_validation_error(self, client):
        """Test camera creation with validation error"""
        # Arrange
        invalid_data = {
            "name": "",  # Invalid: empty name
            "ip_address": "invalid_ip",  # Invalid: not an IP address
            "location": "Test Location"
        }
        
        # Act
        response = client.post("/api/v1/cameras", json=invalid_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert len(data["error"]["details"]) >= 2
```

### Integration Testing

#### Database Integration Tests
```python
@pytest.mark.asyncio
async def test_camera_creation_integration():
    """Test camera creation with database integration"""
    # Arrange
    async with AsyncTestClient(app) as client:
        camera_data = {
            "name": "Integration Test Camera",
            "ip_address": "192.168.1.200",
            "location": "Test Location",
            "configuration": {
                "stream_url": "rtsp://192.168.1.200:554/stream",
                "resolution": {"width": 1920, "height": 1080},
                "frame_rate": 30
            }
        }
        
        # Act
        response = await client.post("/api/v1/cameras", json=camera_data)
        
        # Assert
        assert response.status_code == 201
        camera_id = response.json()["id"]
        
        # Verify camera was created in database
        get_response = await client.get(f"/api/v1/cameras/{camera_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Integration Test Camera"
```

### Load Testing

#### Performance Testing with Locust
```python
from locust import HttpUser, task, between

class LPRAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get authentication token"""
        response = self.client.post("/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        self.token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(3)
    def list_cameras(self):
        """Test camera listing endpoint"""
        self.client.get("/api/v1/cameras")
    
    @task(1)
    def get_camera_details(self):
        """Test camera details endpoint"""
        self.client.get("/api/v1/cameras/cam_001")
    
    @task(1)
    def create_detection(self):
        """Test detection creation endpoint"""
        detection_data = {
            "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
            "timestamp": "2025-01-09T10:30:00Z"
        }
        self.client.post("/api/v1/cameras/cam_001/detections", json=detection_data)
```

## Performance Guidelines

### Response Time Standards

#### Target Response Times
- **List endpoints**: < 200ms
- **Detail endpoints**: < 100ms
- **Create/Update endpoints**: < 500ms
- **Detection endpoints**: < 2000ms
- **Analytics endpoints**: < 5000ms

#### Performance Monitoring
```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor endpoint performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            processing_time = time.time() - start_time
            
            # Log performance metrics
            logger.info(f"Endpoint {func.__name__} completed in {processing_time:.3f}s")
            
            # Add performance headers
            if hasattr(result, 'headers'):
                result.headers['X-Processing-Time'] = f"{processing_time:.3f}"
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Endpoint {func.__name__} failed after {processing_time:.3f}s: {e}")
            raise
    
    return wrapper

@router.get("/cameras")
@monitor_performance
async def list_cameras() -> CameraListResponse:
    """List cameras with performance monitoring"""
    pass
```

### Caching Strategies

#### Response Caching
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/cameras/{camera_id}")
@cache(expire=300)  # Cache for 5 minutes
async def get_camera(camera_id: str) -> CameraResponse:
    """Get camera with response caching"""
    camera = await camera_service.get_camera(camera_id)
    return CameraResponse.from_domain(camera)

@router.get("/analytics/daily-stats")
@cache(expire=3600)  # Cache for 1 hour
async def get_daily_stats(date: str) -> DailyStatsResponse:
    """Get daily statistics with caching"""
    stats = await analytics_service.get_daily_stats(date)
    return DailyStatsResponse.from_domain(stats)
```

#### Conditional Requests
```python
from fastapi import Header

@router.get("/cameras/{camera_id}")
async def get_camera(
    camera_id: str,
    if_none_match: Optional[str] = Header(None)
) -> CameraResponse:
    """Get camera with conditional requests"""
    camera = await camera_service.get_camera(camera_id)
    
    # Generate ETag based on camera data
    etag = hashlib.md5(camera.to_json().encode()).hexdigest()
    
    # Check if client has current version
    if if_none_match == etag:
        return Response(status_code=304)
    
    response = CameraResponse.from_domain(camera)
    response.headers["ETag"] = etag
    return response
```

### Pagination

#### Cursor-Based Pagination
```python
class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters"""
    cursor: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    direction: str = Field("forward", regex="^(forward|backward)$")

@router.get("/detections")
async def list_detections(
    pagination: CursorPaginationParams = Depends()
) -> DetectionListResponse:
    """List detections with cursor-based pagination"""
    detections, next_cursor = await detection_service.list_detections(
        cursor=pagination.cursor,
        limit=pagination.limit,
        direction=pagination.direction
    )
    
    return DetectionListResponse(
        data=detections,
        pagination=CursorPaginationResponse(
            next_cursor=next_cursor,
            limit=pagination.limit,
            has_next=next_cursor is not None
        )
    )
```

## Security Standards

### Input Validation

#### Request Validation
```python
from pydantic import validator, Field
import re

class CreateCameraRequest(BaseModel):
    """Validated camera creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    ip_address: str = Field(..., regex=r'^(\d{1,3}\.){3}\d{1,3}$')
    location: str = Field(..., min_length=1, max_length=200)
    
    @validator('name')
    def validate_name(cls, v):
        # Sanitize name to prevent XSS
        if re.search(r'[<>"\']', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        # Validate IP address format and range
        octets = v.split('.')
        for octet in octets:
            if not (0 <= int(octet) <= 255):
                raise ValueError('Invalid IP address')
        return v
```

#### SQL Injection Prevention
```python
from sqlalchemy import text

# Good: Using parameterized queries
async def get_cameras_by_location(location: str) -> List[Camera]:
    """Get cameras by location using parameterized query"""
    query = text("SELECT * FROM cameras WHERE location = :location")
    result = await session.execute(query, {"location": location})
    return result.fetchall()

# Bad: String concatenation (vulnerable to SQL injection)
async def get_cameras_by_location_bad(location: str) -> List[Camera]:
    """DON'T DO THIS - vulnerable to SQL injection"""
    query = f"SELECT * FROM cameras WHERE location = '{location}'"
    result = await session.execute(query)
    return result.fetchall()
```

### Output Sanitization

#### Response Sanitization
```python
import html
from typing import Any

def sanitize_response(data: Any) -> Any:
    """Sanitize response data to prevent XSS"""
    if isinstance(data, str):
        return html.escape(data)
    elif isinstance(data, dict):
        return {k: sanitize_response(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_response(item) for item in data]
    else:
        return data

@router.get("/cameras/{camera_id}")
async def get_camera(camera_id: str) -> CameraResponse:
    """Get camera with sanitized response"""
    camera = await camera_service.get_camera(camera_id)
    response = CameraResponse.from_domain(camera)
    
    # Sanitize response data
    response.name = html.escape(response.name)
    response.location = html.escape(response.location)
    
    return response
```

### Security Headers

#### Standard Security Headers
```python
from fastapi import Response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

This comprehensive API Design Standards document provides a solid foundation for building consistent, secure, and maintainable APIs for the LPR system. The standards cover all aspects of API design from basic RESTful principles to advanced security and performance considerations.