#### Value Objects
```python
# src/camera_management/domain/value_objects/camera_config.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from shared.utils.validation import validate_url, validate_positive_integer

@dataclass(frozen=True)
class CameraConfiguration:
    """Camera configuration value object"""
    stream_url: str
    resolution_width: int
    resolution_height: int
    frame_rate: int
    username: Optional[str] = None
    password: Optional[str] = None
    stream_path: Optional[str] = None
    quality_settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate configuration values"""
        if not validate_url(self.stream_url):
            raise ValueError(f"Invalid stream URL: {self.stream_url}")
        
        if not validate_positive_integer(self.resolution_width):
            raise ValueError(f"Resolution width must be positive: {self.resolution_width}")
        
        if not validate_positive_integer(self.resolution_height):
            raise ValueError(f"Resolution height must be positive: {self.resolution_height}")
        
        if not (1 <= self.frame_rate <= 120):
            raise ValueError(f"Frame rate must be between 1 and 120: {self.frame_rate}")
    
    @property
    def resolution(self) -> tuple[int, int]:
        """Get resolution as tuple"""
        return (self.resolution_width, self.resolution_height)
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio"""
        return self.resolution_width / self.resolution_height
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "stream_url": self.stream_url,
            "resolution": {
                "width": self.resolution_width,
                "height": self.resolution_height
            },
            "frame_rate": self.frame_rate,
            "authentication": {
                "username": self.username,
                "password": "***" if self.password else None  # Don't expose password
            } if self.username or self.password else None,
            "stream_path": self.stream_path,
            "quality_settings": self.quality_settings
        }

# src/camera_management/domain/value_objects/ip_address.py
import ipaddress
from dataclasses import dataclass

@dataclass(frozen=True)
class IPAddress:
    """IP Address value object"""
    value: str
    
    def __post_init__(self):
        """Validate IP address"""
        try:
            ipaddress.IPv4Address(self.value)
        except ipaddress.AddressValueError:
            raise ValueError(f"Invalid IP address: {self.value}")
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def is_private(self) -> bool:
        """Check if IP is in private range"""
        return ipaddress.IPv4Address(self.value).is_private
    
    @property
    def network_class(self) -> str:
        """Get network class"""
        ip = ipaddress.IPv4Address(self.value)
        first_octet = int(str(ip).split('.')[0])
        
        if 1 <= first_octet <= 126:
            return "A"
        elif 128 <= first_octet <= 191:
            return "B"
        elif 192 <= first_octet <= 223:
            return "C"
        else:
            return "Other"
```

### Application Layer Implementation

#### Use Cases
```python
# src/camera_management/application/use_cases/create_camera.py
from typing import Dict, Any
from dataclasses import dataclass
from camera_management.domain.entities.camera import Camera
from camera_management.domain.value_objects.camera_config import CameraConfiguration
from camera_management.domain.repositories.camera_repository import CameraRepository
from camera_management.application.exceptions import CameraAlreadyExistsError
from shared.core.events import EventBus
import uuid

@dataclass
class CreateCameraCommand:
    """Command to create a new camera"""
    name: str
    ip_address: str
    location: str
    stream_url: str
    resolution_width: int
    resolution_height: int
    frame_rate: int
    username: str = None
    password: str = None
    stream_path: str = None
    quality_settings: Dict[str, Any] = None

class CreateCameraUseCase:
    """Use case for creating a new camera"""
    
    def __init__(self, camera_repository: CameraRepository, event_bus: EventBus):
        self._camera_repository = camera_repository
        self._event_bus = event_bus
    
    async def execute(self, command: CreateCameraCommand) -> Camera:
        """Execute the create camera use case"""
        # Check if camera with same IP already exists
        existing_camera = await self._camera_repository.find_by_ip_address(command.ip_address)
        if existing_camera:
            raise CameraAlreadyExistsError(f"Camera with IP {command.ip_address} already exists")
        
        # Create camera configuration
        configuration = CameraConfiguration(
            stream_url=command.stream_url,
            resolution_width=command.resolution_width,
            resolution_height=command.resolution_height,
            frame_rate=command.frame_rate,
            username=command.username,
            password=command.password,
            stream_path=command.stream_path,
            quality_settings=command.quality_settings or {}
        )
        
        # Create camera entity
        camera = Camera.create(
            id=str(uuid.uuid4()),
            name=command.name,
            ip_address=command.ip_address,
            location=command.location
        )
        
        # Configure camera
        camera.configure(configuration)
        
        # Save camera
        await self._camera_repository.save(camera)
        
        # Publish domain events
        events = camera.get_domain_events()
        for event in events:
            await self._event_bus.publish(event)
        
        # Clear events after publishing
        camera.clear_domain_events()
        
        return camera

# src/camera_management/application/use_cases/monitor_health.py
from typing import List
from camera_management.domain.entities.camera import Camera
from camera_management.domain.repositories.camera_repository import CameraRepository
from camera_management.domain.services.health_monitor import HealthMonitorService
from shared.core.events import EventBus
import asyncio
import logging

logger = logging.getLogger(__name__)

class MonitorCameraHealthUseCase:
    """Use case for monitoring camera health"""
    
    def __init__(
        self, 
        camera_repository: CameraRepository,
        health_monitor: HealthMonitorService,
        event_bus: EventBus
    ):
        self._camera_repository = camera_repository
        self._health_monitor = health_monitor
        self._event_bus = event_bus
    
    async def execute(self) -> None:
        """Monitor health of all active cameras"""
        try:
            # Get all active cameras
            active_cameras = await self._camera_repository.find_by_status("active")
            
            if not active_cameras:
                return
            
            logger.info(f"Monitoring health of {len(active_cameras)} active cameras")
            
            # Monitor cameras concurrently
            tasks = [
                self._monitor_single_camera(camera)
                for camera in active_cameras
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error in health monitoring: {e}")
    
    async def _monitor_single_camera(self, camera: Camera) -> None:
        """Monitor health of a single camera"""
        try:
            # Check camera health
            health_metrics = await self._health_monitor.check_camera_health(camera)
            
            # Update camera health
            camera.update_health_metrics(health_metrics)
            
            # Save updated camera
            await self._camera_repository.save(camera)
            
            # Publish health events
            events = camera.get_domain_events()
            for event in events:
                await self._event_bus.publish(event)
            
            camera.clear_domain_events()
            
        except Exception as e:
            logger.error(f"Error monitoring camera {camera.id}: {e}")
            
            # Mark camera as unhealthy
            camera.update_health_metrics({
                "overall_status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            })
            
            await self._camera_repository.save(camera)
```

### Infrastructure Layer Implementation

#### Repository Implementation
```python
# src/camera_management/infrastructure/persistence/repositories.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from camera_management.domain.entities.camera import Camera
from camera_management.domain.repositories.camera_repository import CameraRepository
from camera_management.domain.value_objects.ip_address import IPAddress
from camera_management.domain.value_objects.camera_config import CameraConfiguration
from camera_management.infrastructure.persistence.models import CameraModel
import json

class SQLAlchemyCameraRepository(CameraRepository):
    """SQLAlchemy implementation of camera repository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, camera: Camera) -> None:
        """Save camera to database"""
        # Check if camera exists
        stmt = select(CameraModel).where(CameraModel.id == camera.id)
        result = await self._session.execute(stmt)
        existing_camera = result.scalar_one_or_none()
        
        if existing_camera:
            # Update existing camera
            existing_camera.name = camera.name
            existing_camera.ip_address = str(camera.ip_address)
            existing_camera.location = camera.location
            existing_camera.status = camera.status
            existing_camera.configuration = json.dumps(
                camera.configuration.to_dict() if camera.configuration else {}
            )
            existing_camera.health_metrics = json.dumps(camera.health_metrics)
            existing_camera.updated_at = camera.updated_at
        else:
            # Create new camera
            camera_model = CameraModel(
                id=camera.id,
                name=camera.name,
                ip_address=str(camera.ip_address),
                location=camera.location,
                status=camera.status,
                configuration=json.dumps(
                    camera.configuration.to_dict() if camera.configuration else {}
                ),
                health_metrics=json.dumps(camera.health_metrics),
                created_at=camera.created_at,
                updated_at=camera.updated_at
            )
            self._session.add(camera_model)
        
        await self._session.commit()
    
    async def find_by_id(self, camera_id: str) -> Optional[Camera]:
        """Find camera by ID"""
        stmt = select(CameraModel).where(CameraModel.id == camera_id)
        result = await self._session.execute(stmt)
        camera_model = result.scalar_one_or_none()
        
        if not camera_model:
            return None
        
        return self._model_to_entity(camera_model)
    
    async def find_by_ip_address(self, ip_address: str) -> Optional[Camera]:
        """Find camera by IP address"""
        stmt = select(CameraModel).where(CameraModel.ip_address == ip_address)
        result = await self._session.execute(stmt)
        camera_model = result.scalar_one_or_none()
        
        if not camera_model:
            return None
        
        return self._model_to_entity(camera_model)
    
    async def find_by_status(self, status: str) -> List[Camera]:
        """Find cameras by status"""
        stmt = select(CameraModel).where(CameraModel.status == status)
        result = await self._session.execute(stmt)
        camera_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in camera_models]
    
    async def find_all(self, 
                      status: Optional[str] = None,
                      location: Optional[str] = None,
                      limit: int = 100,
                      offset: int = 0) -> List[Camera]:
        """Find cameras with optional filters"""
        stmt = select(CameraModel)
        
        # Apply filters
        conditions = []
        if status:
            conditions.append(CameraModel.status == status)
        if location:
            conditions.append(CameraModel.location.ilike(f"%{location}%"))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self._session.execute(stmt)
        camera_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in camera_models]
    
    async def delete(self, camera_id: str) -> bool:
        """Delete camera by ID"""
        stmt = select(CameraModel).where(CameraModel.id == camera_id)
        result = await self._session.execute(stmt)
        camera_model = result.scalar_one_or_none()
        
        if not camera_model:
            return False
        
        await self._session.delete(camera_model)
        await self._session.commit()
        return True
    
    async def count(self, status: Optional[str] = None) -> int:
        """Count cameras with optional status filter"""
        from sqlalchemy import func
        
        stmt = select(func.count(CameraModel.id))
        if status:
            stmt = stmt.where(CameraModel.status == status)
        
        result = await self._session.execute(stmt)
        return result.scalar()
    
    def _model_to_entity(self, model: CameraModel) -> Camera:
        """Convert database model to domain entity"""
        # Parse configuration
        configuration = None
        if model.configuration:
            config_dict = json.loads(model.configuration)
            if config_dict:
                configuration = CameraConfiguration(
                    stream_url=config_dict["stream_url"],
                    resolution_width=config_dict["resolution"]["width"],
                    resolution_height=config_dict["resolution"]["height"],
                    frame_rate=config_dict["frame_rate"],
                    username=config_dict.get("authentication", {}).get("username"),
                    password=config_dict.get("authentication", {}).get("password"),
                    stream_path=config_dict.get("stream_path"),
                    quality_settings=config_dict.get("quality_settings", {})
                )
        
        # Parse health metrics
        health_metrics = {}
        if model.health_metrics:
            health_metrics = json.loads(model.health_metrics)
        
        # Create entity
        camera = Camera(
            id=model.id,
            name=model.name,
            ip_address=IPAddress(model.ip_address),
            location=model.location,
            status=model.status,
            configuration=configuration,
            health_metrics=health_metrics,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        
        return camera
```

#### Database Models
```python
# src/camera_management/infrastructure/persistence/models.py
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class CameraModel(Base):
    """Camera database model"""
    __tablename__ = "cameras"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    ip_address = Column(String(15), nullable=False, unique=True)
    location = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="inactive")
    configuration = Column(JSONB, nullable=True)
    health_metrics = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Camera(id='{self.id}', name='{self.name}', ip='{self.ip_address}')>"

# Create indexes for performance
from sqlalchemy import Index
Index('idx_cameras_status', CameraModel.status)
Index('idx_cameras_location', CameraModel.location)
Index('idx_cameras_ip_address', CameraModel.ip_address)
```

### API Layer Implementation

#### FastAPI Routers
```python
# src/camera_management/presentation/api/routers/cameras.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from camera_management.presentation.api.schemas.requests import (
    CreateCameraRequest,
    UpdateCameraRequest,
    CameraFiltersRequest
)
from camera_management.presentation.api.schemas.responses import (
    CameraResponse,
    CameraListResponse,
    HealthResponse
)
from camera_management.presentation.api.dependencies import (
    get_camera_app_service,
    get_current_user
)
from camera_management.application.services.camera_app_service import CameraAppService
from camera_management.application.exceptions import (
    CameraNotFoundError,
    CameraAlreadyExistsError
)
from shared.utils.security import User
import logging

logger = logging.getLogger(__name__)
camera_router = APIRouter()

@camera_router.post("/", 
                   response_model=CameraResponse,
                   status_code=status.HTTP_201_CREATED,
                   summary="Create a new camera",
                   description="Create a new camera with configuration")
async def create_camera(
    camera_request: CreateCameraRequest,
    camera_service: CameraAppService = Depends(get_camera_app_service),
    current_user: User = Depends(get_current_user)
) -> CameraResponse:
    """Create a new camera"""
    try:
        camera = await camera_service.create_camera(camera_request.to_command())
        return CameraResponse.from_entity(camera)
    
    except CameraAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating camera: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@camera_router.get("/",
                  response_model=CameraListResponse,
                  summary="List cameras",
                  description="Get list of cameras with optional filtering")
async def list_cameras(
    status_filter: Optional[str] = Query(None, description="Filter by camera status"),
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(20, ge=1, le=100, description="Number of cameras to return"),
    offset: int = Query(0, ge=0, description="Number of cameras to skip"),
    camera_service: CameraAppService = Depends(get_camera_app_service),
    current_user: User = Depends(get_current_user)
) -> CameraListResponse:
    """List cameras with optional filtering"""
    try:
        cameras = await camera_service.list_cameras(
            status=status_filter,
            location=location,
            limit=limit,
            offset=offset
        )
        
        total_count = await camera_service.count_cameras(status=status_filter)
        
        camera_responses = [CameraResponse.from_entity(camera) for camera in cameras]
        
        return CameraListResponse(
            data=camera_responses,
            total=total_count,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total_count,
            has_previous=offset > 0
        )
    
    except Exception as e:
        logger.error(f"Error listing cameras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@camera_router.get("/{camera_id}",
                  response_model=CameraResponse,
                  summary="Get camera by ID",
                  description="Get detailed information about a specific camera")
async def get_camera(
    camera_id: str,
    camera_service: CameraAppService = Depends(get_camera_app_service),
    current_user: User = Depends(get_current_user)
) -> CameraResponse:
    """Get camera by ID"""
    try:
        camera = await camera_service.get_camera_by_id(camera_id)
        return CameraResponse.from_entity(camera)
    
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found"
        )
    except Exception as e:
        logger.error(f"Error getting camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@camera_router.put("/{camera_id}",
                  response_model=CameraResponse,
                  summary="Update camera",
                  description="Update camera information and configuration")
async def update_camera(
    camera_id: str,
    update_request: UpdateCameraRequest,
    camera_service: CameraAppService = Depends(get_camera_app_service),
    current_user: User = Depends(get_current_user)
) -> CameraResponse:
    """Update camera"""
    try:
        camera = await camera_service.update_camera(camera_id, update_request.to_command())
        return CameraResponse.from_entity(camera)
    
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@camera_router.delete("/{camera_id}",
                     status_code=status.HTTP_204_NO_CONTENT,
                     summary="Delete camera",
                     description="Delete a camera from the system")
async def delete_camera(
    camera_id: str,
    camera_service: CameraAppService = Depends(get_camera_app_service),
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete camera"""
    try:
        await camera_service.delete_camera(camera_id)
    
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found"
        )
    except Exception as e:
        logger.error(f"Error deleting camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@camera_router.post("/{camera_id}/activate",
                   response_model=CameraResponse,
                   summary="Activate camera",
                   description="Activate camera for processing")
async def activate_camera(
    camera_id: str,
    camera_service: CameraAppService = Depends(get_camera_app_service),
    current_user: User = Depends(get_current_user)
) -> CameraResponse:
    """Activate camera"""
    try:
        camera = await camera_service.activate_camera(camera_id)
        return CameraResponse.from_entity(camera)
    
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error activating camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@camera_router.get("/{camera_id}/health",
                  response_model=HealthResponse,
                  summary="Get camera health",
                  description="Get current health status of the camera")
async def get_camera_health(
    camera_id: str,
    camera_service: CameraAppService = Depends(get_camera_app_service),
    current_user: User = Depends(get_current_user)
) -> HealthResponse:
    """Get camera health status"""
    try:
        health_status = await camera_service.get_camera_health(camera_id)
        return HealthResponse.from_dict(health_status)
    
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID {camera_id} not found"
        )
    except Exception as e:
        logger.error(f"Error getting camera health {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@camera_router.post("/test-connection",
                   summary="Test camera connection",
                   description="Test connection to a camera without saving it")
async def test_camera_connection(
    connection_test: CreateCameraRequest,
    camera_service: CameraAppService = Depends(get_camera_app_service),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Test camera connection"""
    try:
        result = await camera_service.test_camera_connection(connection_test.to_command())
        return {"success": True, "message": "Connection successful", "details": result}
    
    except Exception as e:
        logger.error(f"Camera connection test failed: {e}")
        return {"success": False, "message": str(e)}
```

## Database Design

### Multi-Database Strategy

#### PostgreSQL Schema (Transactional Data)
```sql
-- Camera Management Database Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cameras table
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    ip_address INET NOT NULL UNIQUE,
    location VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    configuration JSONB,
    health_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_camera_status CHECK (status IN ('active', 'inactive', 'error', 'maintenance'))
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    roles TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System configuration
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_cameras_status ON cameras(status);
CREATE INDEX idx_cameras_location ON cameras(location);
CREATE INDEX idx_cameras_created_at ON cameras(created_at);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- Function to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_cameras_updated_at BEFORE UPDATE ON cameras
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### MongoDB Schema (Document Data)
```javascript
// Detection results collection
db.createCollection("detections", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["id", "camera_id", "timestamp", "image_data"],
            properties: {
                id: { bsonType: "string" },
                camera_id: { bsonType: "string" },
                timestamp: { bsonType: "date" },
                image_data: {
                    bsonType: "object",
                    properties: {
                        original_url: { bsonType: "string" },
                        processed_url: { bsonType: "string" },
                        thumbnail_url: { bsonType: "string" }
                    }
                },
                license_plates: {
                    bsonType: "array",
                    items: {
                        bsonType: "object",
                        properties: {
                            text: { bsonType: "string" },
                            confidence: { bsonType: "double" },
                            bounding_box: {
                                bsonType: "object",
                                properties: {
                                    x: { bsonType: "int" },
                                    y: { bsonType: "int" },
                                    width: { bsonType: "int" },
                                    height: { bsonType: "int" }
                                }
                            }
                        }
                    }
                },
                vehicle_info: {
                    bsonType: "object",
                    properties: {
                        type: { bsonType: "string" },
                        color: { bsonType: "string" },
                        make: { bsonType: "string" },
                        model: { bsonType: "string" }
                    }
                },
                metadata: { bsonType: "object" }
            }
        }
    }
});

// Create indexes
db.detections.createIndex({ camera_id: 1, timestamp: -1 });
db.detections.createIndex({ timestamp: -1 });
db.detections.createIndex({ "license_plates.text": 1 });
db.detections.createIndex({ "vehicle_info# Backend Modernization & Architecture Plan

**Version:** 1.0  
**Date:** 2025-01-09  
**Authors:** Backend Architecture Team  
**Status:** Active Development  

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Target Architecture](#target-architecture)
4. [Technology Stack Selection](#technology-stack-selection)
5. [Project Structure](#project-structure)
6. [Service Architecture](#service-architecture)
7. [Database Design](#database-design)
8. [API Design](#api-design)
9. [Security Implementation](#security-implementation)
10. [Development Workflow](#development-workflow)
11. [Implementation Roadmap](#implementation-roadmap)

## Executive Summary

This document outlines the complete backend modernization strategy for the LPR system, transitioning from legacy architecture to a modern, cloud-native microservices-based system built from scratch following Domain-Driven Design principles and industry best practices.

### Key Objectives

- **Clean Architecture**: Start fresh with modern architectural patterns
- **Microservices**: Modular, independently deployable services
- **Scalability**: Horizontal scaling capabilities with cloud-native design
- **Maintainability**: Clear separation of concerns and testable code
- **Performance**: Optimized for real-time processing requirements
- **Security**: Enterprise-grade security from the ground up

### Business Impact

- **50% reduction** in response times through optimized architecture
- **99.9% uptime** with resilient microservices design
- **10x faster** development cycles with modern tooling
- **Enhanced security** with zero-trust architecture
- **Cost optimization** through efficient resource utilization

## Current State Analysis

### Legacy System Issues

#### Architectural Problems
```python
# Current issues identified:
LEGACY_ISSUES = {
    "monolithic_structure": {
        "problem": "Single large application",
        "impact": "Difficult to scale, maintain, and deploy",
        "solution": "Microservices architecture"
    },
    "tight_coupling": {
        "problem": "Components heavily interdependent",
        "impact": "Changes affect entire system",
        "solution": "Loose coupling with event-driven architecture"
    },
    "mixed_concerns": {
        "problem": "Business logic mixed with infrastructure",
        "impact": "Hard to test and maintain",
        "solution": "Clean architecture with clear boundaries"
    },
    "limited_scalability": {
        "problem": "Vertical scaling only",
        "impact": "Performance bottlenecks",
        "solution": "Horizontal scaling with microservices"
    }
}
```

#### Technical Debt
- **Outdated Dependencies**: Legacy versions causing security vulnerabilities
- **No Testing Strategy**: Limited automated testing coverage
- **Poor Error Handling**: Inconsistent error responses and logging
- **Performance Issues**: Synchronous processing causing bottlenecks
- **Security Gaps**: Basic authentication without modern security practices

## Target Architecture

### Microservices Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
│                    (Kong/Traefik)                              │
│              Authentication & Rate Limiting                     │
└─────────────────┬───────────────────┬───────────────────┬──────┘
                  │                   │                   │
    ┌─────────────▼─────────────┐   ┌──▼──────────────┐  ┌─▼─────────────┐
    │    Camera Management      │   │  Video Processing│  │   Detection   │
    │       Service            │   │     Service      │  │    Service    │
    │                         │   │                  │  │               │
    │ • Camera CRUD           │   │ • Stream ingestion│  │ • YOLO models │
    │ • Health monitoring     │   │ • Frame processing│  │ • OCR processing│
    │ • Configuration         │   │ • Recording mgmt  │  │ • Validation  │
    └─────────────┬───────────┘   └──┬───────────────┘  └─┬─────────────┘
                  │                  │                    │
                  └──────────────────┼────────────────────┘
                                     │
              ┌─────────────────────▼─────────────────────┐
              │             Event Bus                     │
              │         (Redis/RabbitMQ)                  │
              └─────────────────────┬─────────────────────┘
                                    │
    ┌─────────────────────────────▼─────────────────────────────┐
    │                    Supporting Services                     │
    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
    │  │ Analytics   │ │Notification │ │    User     │         │
    │  │   Service   │ │   Service   │ │ Management  │         │
    │  └─────────────┘ └─────────────┘ └─────────────┘         │
    └───────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────▼─────────────────────┐
              │              Data Layer                   │
              │ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
              │ │PostgreSQL│ │ MongoDB  │ │  Redis   │   │
              │ │(Metadata)│ │(Documents)│ │(Cache)   │   │
              │ └──────────┘ └──────────┘ └──────────┘   │
              └───────────────────────────────────────────┘
```

### Domain-Driven Design Bounded Contexts

#### Core Domains

1. **Camera Management Domain**
   - Camera registration and lifecycle
   - Health monitoring and diagnostics
   - Configuration management
   - Stream connection management

2. **Video Processing Domain**
   - Stream ingestion and buffering
   - Frame extraction and preprocessing
   - Recording management
   - Quality assessment

3. **Detection Domain**
   - License plate detection (YOLO)
   - OCR text recognition
   - Confidence scoring and validation
   - Enhancement processing

4. **Analytics Domain**
   - Real-time metrics collection
   - Pattern analysis and insights
   - Reporting and visualization
   - Performance monitoring

#### Supporting Domains

5. **User Management Domain**
   - Authentication and authorization
   - Role-based access control
   - User preferences and settings
   - Audit logging

6. **Notification Domain**
   - Alert management
   - Multi-channel notifications
   - Subscription management
   - Delivery tracking

## Technology Stack Selection

### Core Backend Technologies

#### Runtime & Framework
```python
TECHNOLOGY_STACK = {
    "runtime": {
        "language": "Python 3.11+",
        "framework": "FastAPI 0.104+",
        "async_support": "asyncio with full async/await",
        "performance": "uvicorn with gunicorn for production"
    },
    "validation": {
        "primary": "Pydantic v2",
        "features": ["automatic validation", "serialization", "OpenAPI generation"]
    },
    "orm": {
        "primary": "SQLAlchemy 2.0 (async)",
        "drivers": ["asyncpg for PostgreSQL", "motor for MongoDB"],
        "migrations": "Alembic"
    }
}
```

#### Database Selection Strategy
```python
DATABASE_STRATEGY = {
    "transactional_data": {
        "technology": "PostgreSQL 15+",
        "use_cases": ["cameras", "users", "system_config", "relationships"],
        "benefits": ["ACID compliance", "advanced indexing", "JSON support"]
    },
    "document_data": {
        "technology": "MongoDB 6+",
        "use_cases": ["detections", "analytics_data", "logs", "flexible_schemas"],
        "benefits": ["horizontal scaling", "flexible schema", "geospatial queries"]
    },
    "cache_layer": {
        "technology": "Redis 7+ Cluster",
        "use_cases": ["session_storage", "real_time_data", "pub_sub", "rate_limiting"],
        "benefits": ["in-memory performance", "persistence", "clustering"]
    },
    "search_engine": {
        "technology": "Elasticsearch 8+",
        "use_cases": ["full_text_search", "log_analysis", "complex_queries"],
        "benefits": ["powerful search", "analytics", "scalability"]
    }
}
```

#### Message Queue & Events
```python
MESSAGING_STACK = {
    "event_bus": {
        "development": "Redis Pub/Sub",
        "production": "RabbitMQ 3.12+",
        "cloud": "AWS SQS/SNS or Azure Service Bus"
    },
    "task_queue": {
        "technology": "Celery with Redis backend",
        "use_cases": ["background tasks", "scheduled jobs", "long-running processes"]
    },
    "real_time": {
        "technology": "WebSocket with FastAPI",
        "use_cases": ["live camera feeds", "real-time notifications", "system status"]
    }
}
```

## Project Structure

### Clean Architecture Project Layout

```
lpr-backend/
├── README.md
├── docker-compose.yml              # Development environment
├── docker-compose.prod.yml         # Production environment
├── pyproject.toml                  # Python project configuration
├── requirements/                   # Dependency management
│   ├── base.txt                   # Core dependencies
│   ├── dev.txt                    # Development dependencies
│   ├── prod.txt                   # Production dependencies
│   └── test.txt                   # Testing dependencies
├── scripts/                       # Deployment and utility scripts
│   ├── start-dev.sh              # Development startup
│   ├── start-prod.sh             # Production startup
│   ├── run-tests.sh              # Test execution
│   └── db-migrate.sh             # Database migrations
├── tests/                         # Test files
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── e2e/                      # End-to-end tests
│   └── conftest.py               # Test configuration
├── docs/                         # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture docs
│   └── deployment/               # Deployment guides
├── migrations/                   # Database migrations
│   └── versions/                 # Migration versions
└── src/                          # Source code
    ├── shared/                   # Shared components across services
    │   ├── __init__.py
    │   ├── core/                 # Core shared functionality
    │   │   ├── __init__.py
    │   │   ├── config.py         # Configuration management
    │   │   ├── database.py       # Database connections
    │   │   ├── events.py         # Event system
    │   │   ├── exceptions.py     # Custom exceptions
    │   │   ├── logging.py        # Logging configuration
    │   │   └── middleware.py     # Shared middleware
    │   ├── infrastructure/       # Infrastructure concerns
    │   │   ├── __init__.py
    │   │   ├── cache/           # Caching implementations
    │   │   ├── messaging/       # Message queue implementations
    │   │   ├── storage/         # File storage implementations
    │   │   └── monitoring/      # Monitoring and health checks
    │   └── utils/               # Utility functions
    │       ├── __init__.py
    │       ├── datetime.py      # Date/time utilities
    │       ├── validation.py    # Validation helpers
    │       └── security.py      # Security utilities
    ├── api_gateway/             # API Gateway service
    │   ├── __init__.py
    │   ├── main.py             # Gateway entry point
    │   ├── routing/            # Route configuration
    │   ├── middleware/         # Gateway middleware
    │   └── config/             # Gateway configuration
    ├── camera_management/       # Camera Management Service
    │   ├── __init__.py
    │   ├── main.py             # Service entry point
    │   ├── domain/             # Domain layer
    │   │   ├── __init__.py
    │   │   ├── entities/       # Domain entities
    │   │   │   ├── __init__.py
    │   │   │   ├── camera.py   # Camera entity
    │   │   │   └── health_metrics.py
    │   │   ├── value_objects/  # Value objects
    │   │   │   ├── __init__.py
    │   │   │   ├── camera_config.py
    │   │   │   └── ip_address.py
    │   │   ├── services/       # Domain services
    │   │   │   ├── __init__.py
    │   │   │   ├── camera_service.py
    │   │   │   └── health_monitor.py
    │   │   ├── events/         # Domain events
    │   │   │   ├── __init__.py
    │   │   │   └── camera_events.py
    │   │   └── repositories/   # Repository interfaces
    │   │       ├── __init__.py
    │   │       └── camera_repository.py
    │   ├── application/        # Application layer
    │   │   ├── __init__.py
    │   │   ├── use_cases/      # Use case implementations
    │   │   │   ├── __init__.py
    │   │   │   ├── create_camera.py
    │   │   │   ├── update_camera.py
    │   │   │   └── monitor_health.py
    │   │   ├── handlers/       # Command/Query handlers
    │   │   │   ├── __init__.py
    │   │   │   ├── command_handlers.py
    │   │   │   └── query_handlers.py
    │   │   └── services/       # Application services
    │   │       ├── __init__.py
    │   │       └── camera_app_service.py
    │   ├── infrastructure/     # Infrastructure layer
    │   │   ├── __init__.py
    │   │   ├── persistence/    # Data persistence
    │   │   │   ├── __init__.py
    │   │   │   ├── models.py   # SQLAlchemy models
    │   │   │   └── repositories.py # Repository implementations
    │   │   ├── external/       # External services
    │   │   │   ├── __init__.py
    │   │   │   └── camera_client.py
    │   │   └── messaging/      # Message handling
    │   │       ├── __init__.py
    │   │       └── event_handlers.py
    │   └── presentation/       # Presentation layer
    │       ├── __init__.py
    │       ├── api/            # REST API
    │       │   ├── __init__.py
    │       │   ├── routers/    # API routers
    │       │   │   ├── __init__.py
    │       │   │   └── cameras.py
    │       │   ├── schemas/    # Pydantic schemas
    │       │   │   ├── __init__.py
    │       │   │   ├── requests.py
    │       │   │   └── responses.py
    │       │   └── dependencies.py # FastAPI dependencies
    │       └── websocket/      # WebSocket handlers
    │           ├── __init__.py
    │           └── camera_ws.py
    ├── video_processing/        # Video Processing Service
    │   ├── __init__.py
    │   ├── main.py
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   ├── video_stream.py
    │   │   │   ├── frame.py
    │   │   │   └── recording.py
    │   │   ├── value_objects/
    │   │   │   ├── stream_config.py
    │   │   │   └── quality_metrics.py
    │   │   └── services/
    │   │       ├── stream_processor.py
    │   │       └── frame_extractor.py
    │   ├── application/
    │   │   ├── use_cases/
    │   │   │   ├── start_stream.py
    │   │   │   ├── process_frame.py
    │   │   │   └── manage_recording.py
    │   │   └── handlers/
    │   ├── infrastructure/
    │   │   ├── persistence/
    │   │   ├── streaming/      # Video streaming implementations
    │   │   │   ├── rtsp_client.py
    │   │   │   └── frame_buffer.py
    │   │   └── processing/     # Frame processing
    │   │       └── opencv_processor.py
    │   └── presentation/
    │       └── api/
    │           └── routers/
    │               └── streams.py
    ├── detection/               # Detection Service
    │   ├── __init__.py
    │   ├── main.py
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   ├── detection.py
    │   │   │   ├── license_plate.py
    │   │   │   └── vehicle.py
    │   │   ├── value_objects/
    │   │   │   ├── bounding_box.py
    │   │   │   ├── confidence_score.py
    │   │   │   └── plate_format.py
    │   │   └── services/
    │   │       ├── yolo_detector.py
    │   │       ├── ocr_processor.py
    │   │       └── plate_validator.py
    │   ├── application/
    │   │   ├── use_cases/
    │   │   │   ├── detect_plates.py
    │   │   │   ├── enhance_detection.py
    │   │   │   └── validate_results.py
    │   │   └── handlers/
    │   ├── infrastructure/
    │   │   ├── ai_models/      # AI model implementations
    │   │   │   ├── yolo_model.py
    │   │   │   ├── ocr_model.py
    │   │   │   └── model_manager.py
    │   │   ├── persistence/
    │   │   └── image_processing/
    │   │       └── opencv_utils.py
    │   └── presentation/
    │       └── api/
    │           └── routers/
    │               └── detections.py
    ├── analytics/               # Analytics Service
    │   ├── __init__.py
    │   ├── main.py
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   ├── metric.py
    │   │   │   ├── report.py
    │   │   │   └── dashboard.py
    │   │   ├── value_objects/
    │   │   │   ├── time_period.py
    │   │   │   └── metric_value.py
    │   │   └── services/
    │   │       ├── metrics_collector.py
    │   │       ├── pattern_analyzer.py
    │   │       └── report_generator.py
    │   ├── application/
    │   │   ├── use_cases/
    │   │   │   ├── collect_metrics.py
    │   │   │   ├── analyze_patterns.py
    │   │   │   └── generate_report.py
    │   │   └── handlers/
    │   ├── infrastructure/
    │   │   ├── persistence/
    │   │   ├── analytics_engine/
    │   │   │   └── pandas_processor.py
    │   │   └── visualization/
    │   │       └── chart_generator.py
    │   └── presentation/
    │       └── api/
    │           └── routers/
    │               └── analytics.py
    ├── user_management/         # User Management Service
    │   ├── __init__.py
    │   ├── main.py
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   ├── user.py
    │   │   │   ├── role.py
    │   │   │   └── permission.py
    │   │   ├── value_objects/
    │   │   │   ├── email.py
    │   │   │   └── password.py
    │   │   └── services/
    │   │       ├── auth_service.py
    │   │       └── permission_service.py
    │   ├── application/
    │   │   ├── use_cases/
    │   │   │   ├── authenticate_user.py
    │   │   │   ├── authorize_action.py
    │   │   │   └── manage_roles.py
    │   │   └── handlers/
    │   ├── infrastructure/
    │   │   ├── persistence/
    │   │   ├── security/
    │   │   │   ├── jwt_handler.py
    │   │   │   ├── password_hasher.py
    │   │   │   └── token_validator.py
    │   │   └── external/
    │   │       └── ldap_client.py
    │   └── presentation/
    │       └── api/
    │           └── routers/
    │               ├── auth.py
    │               └── users.py
    └── notification/            # Notification Service
        ├── __init__.py
        ├── main.py
        ├── domain/
        │   ├── entities/
        │   │   ├── notification.py
        │   │   ├── alert.py
        │   │   └── subscription.py
        │   ├── value_objects/
        │   │   ├── channel.py
        │   │   └── template.py
        │   └── services/
        │       ├── notification_service.py
        │       └── template_service.py
        ├── application/
        │   ├── use_cases/
        │   │   ├── send_notification.py
        │   │   ├── manage_alerts.py
        │   │   └── handle_subscriptions.py
        │   └── handlers/
        ├── infrastructure/
        │   ├── persistence/
        │   ├── channels/        # Notification channels
        │   │   ├── email_channel.py
        │   │   ├── sms_channel.py
        │   │   ├── webhook_channel.py
        │   │   └── websocket_channel.py
        │   └── templates/
        │       └── template_engine.py
        └── presentation/
            └── api/
                └── routers/
                    └── notifications.py
```

## Service Architecture

### Core Service Implementation

#### Base Service Architecture
```python
# src/shared/core/base_service.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from fastapi import FastAPI
from contextlib import asynccontextmanager

class BaseService(ABC):
    """Base class for all microservices"""
    
    def __init__(self, service_name: str, version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self.app: Optional[FastAPI] = None
        self._initialized = False
    
    async def create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.startup()
            yield
            # Shutdown
            await self.shutdown()
        
        self.app = FastAPI(
            title=f"LPR {self.service_name}",
            version=self.version,
            description=f"LPR System - {self.service_name} Service",
            lifespan=lifespan
        )
        
        await self.configure_app()
        return self.app
    
    async def configure_app(self) -> None:
        """Configure FastAPI application with middleware, routes, etc."""
        # Add common middleware
        from shared.core.middleware import (
            CORSMiddleware,
            LoggingMiddleware,
            ErrorHandlingMiddleware,
            RequestIDMiddleware
        )
        
        self.app.add_middleware(RequestIDMiddleware)
        self.app.add_middleware(LoggingMiddleware)
        self.app.add_middleware(ErrorHandlingMiddleware)
        self.app.add_middleware(CORSMiddleware)
        
        # Add health check endpoints
        self.app.get("/health")(self.health_check)
        self.app.get("/ready")(self.readiness_check)
        
        # Configure service-specific routes
        await self.configure_routes()
    
    @abstractmethod
    async def configure_routes(self) -> None:
        """Configure service-specific routes"""
        pass
    
    @abstractmethod
    async def startup(self) -> None:
        """Service startup logic"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Service shutdown logic"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": self.service_name,
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def readiness_check(self) -> Dict[str, Any]:
        """Readiness check endpoint"""
        # Check dependencies
        checks = await self.check_dependencies()
        
        is_ready = all(check["status"] == "healthy" for check in checks.values())
        
        return {
            "status": "ready" if is_ready else "not_ready",
            "service": self.service_name,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @abstractmethod
    async def check_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """Check service dependencies"""
        pass
```

#### Camera Management Service Implementation
```python
# src/camera_management/main.py
from shared.core.base_service import BaseService
from shared.core.database import DatabaseManager
from shared.core.events import EventBus
from camera_management.infrastructure.persistence.models import CameraModel
from camera_management.presentation.api.routers.cameras import camera_router
from camera_management.application.services.camera_app_service import CameraAppService

class CameraManagementService(BaseService):
    """Camera Management microservice"""
    
    def __init__(self):
        super().__init__("Camera Management", "2.0.0")
        self.db_manager: Optional[DatabaseManager] = None
        self.event_bus: Optional[EventBus] = None
        self.camera_service: Optional[CameraAppService] = None
    
    async def startup(self) -> None:
        """Initialize service dependencies"""
        # Initialize database
        self.db_manager = DatabaseManager()
        await self.db_manager.initialize()
        
        # Initialize event bus
        self.event_bus = EventBus()
        await self.event_bus.initialize()
        
        # Initialize application service
        self.camera_service = CameraAppService(
            db_session=self.db_manager.get_session(),
            event_bus=self.event_bus
        )
        
        # Start background tasks
        await self.start_health_monitoring()
        
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Cleanup service resources"""
        if self.event_bus:
            await self.event_bus.close()
        
        if self.db_manager:
            await self.db_manager.close()
    
    async def configure_routes(self) -> None:
        """Configure API routes"""
        self.app.include_router(
            camera_router,
            prefix="/api/v2/cameras",
            tags=["cameras"]
        )
    
    async def check_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """Check service dependencies"""
        checks = {}
        
        # Database check
        try:
            await self.db_manager.health_check()
            checks["database"] = {"status": "healthy", "response_time": "5ms"}
        except Exception as e:
            checks["database"] = {"status": "unhealthy", "error": str(e)}
        
        # Event bus check
        try:
            await self.event_bus.health_check()
            checks["event_bus"] = {"status": "healthy"}
        except Exception as e:
            checks["event_bus"] = {"status": "unhealthy", "error": str(e)}
        
        return checks
    
    async def start_health_monitoring(self) -> None:
        """Start background health monitoring tasks"""
        import asyncio
        from camera_management.application.use_cases.monitor_health import MonitorCameraHealthUseCase
        
        async def health_monitor_task():
            monitor_use_case = MonitorCameraHealthUseCase(self.camera_service)
            while True:
                try:
                    await monitor_use_case.execute()
                    await asyncio.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
        
        asyncio.create_task(health_monitor_task())

# Entry point
async def create_app() -> FastAPI:
    service = CameraManagementService()
    return await service.create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:create_app", host="0.0.0.0", port=8001, factory=True)
```

### Domain Layer Implementation

#### Camera Entity
```python
# src/camera_management/domain/entities/camera.py
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
from shared.core.events import DomainEvent
from camera_management.domain.value_objects.camera_config import CameraConfiguration
from camera_management.domain.value_objects.ip_address import IPAddress
from camera_management.domain.events.camera_events import (
    CameraCreatedEvent,
    CameraActivatedEvent,
    CameraHealthChangedEvent
)

@dataclass
class Camera:
    """Camera domain entity"""
    id: str
    name: str
    ip_address: IPAddress
    location: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    configuration: Optional[CameraConfiguration] = None
    status: str = "inactive"
    health_metrics: dict = field(default_factory=dict)
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def configure(self, configuration: CameraConfiguration) -> None:
        """Configure camera settings"""
        self.configuration = configuration
        self.updated_at = datetime.utcnow()
        
        # Record domain event
        self._add_domain_event(
            CameraConfiguredEvent(
                camera_id=self.id,
                configuration=configuration.to_dict(),
                timestamp=self.updated_at
            )
        )
    
    def activate(self) -> None:
        """Activate camera for processing"""
        if not self.configuration:
            raise ValueError(f"Camera {self.id} must be configured before activation")
        
        if self.status == "active":
            return  # Already active
        
        self.status = "active"
        self.updated_at = datetime.utcnow()
        
        # Record domain event
        self._add_domain_event(
            CameraActivatedEvent(
                camera_id=self.id,
                ip_address=str(self.ip_address),
                timestamp=self.updated_at
            )
        )
    
    def deactivate(self) -> None:
        """Deactivate camera"""
        if self.status != "active":
            return  # Already inactive
        
        self.status = "inactive"
        self.updated_at = datetime.utcnow()
        
        # Record domain event
        self._add_domain_event(
            CameraDeactivatedEvent(
                camera_id=self.id,
                timestamp=self.updated_at
            )
        )
    
    def update_health_metrics(self, metrics: dict) -> None:
        """Update camera health metrics"""
        previous_health = self.health_metrics.get("overall_status", "unknown")
        self.health_metrics = metrics
        self.updated_at = datetime.utcnow()
        
        current_health = metrics.get("overall_status", "unknown")
        
        # Record domain event if health status changed
        if previous_health != current_health:
            self._add_domain_event(
                CameraHealthChangedEvent(
                    camera_id=self.id,
                    previous_status=previous_health,
                    current_status=current_health,
                    metrics=metrics,
                    timestamp=self.updated_at
                )
            )
    
    def is_healthy(self) -> bool:
        """Check if camera is healthy"""
        return self.health_metrics.get("overall_status") == "healthy"
    
    def is_active(self) -> bool:
        """Check if camera is active"""
        return self.status == "active"
    
    def get_stream_url(self) -> Optional[str]:
        """Get camera stream URL"""
        if not self.configuration:
            return None
        return self.configuration.stream_url
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event to be published"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get all domain events"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear all domain events"""
        self._domain_events.clear()
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "ip_address": str(self.ip_address),
            "location": self.location,
            "status": self.status,
            "configuration": self.configuration.to_dict() if self.configuration else None,
            "health_metrics": self.health_metrics,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def create(cls, id: str, name: str, ip_address: str, location: str) -> 'Camera':
        """Factory method to create new camera"""
        camera = cls(
            id=id,
            name=name,
            ip_address=IPAddress(ip_address),
            location=location
        )
        
        # Record creation event
        camera._add_domain_event(
            CameraCreatedEvent(
                camera_id=id,
                name=name,
                ip_address=ip_address,
                location=location,
                timestamp=camera.created_at
            )
        )
        
        return camera
```

#### Value Objects
