# Hexagonal Architecture Implementation Guide

**Version:** 1.0  
**Date:** 2025-01-09  
**Authors:** System Architecture Team  

## Table of Contents

1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [Layer Structure](#layer-structure)
4. [Implementation Patterns](#implementation-patterns)
5. [Code Organization](#code-organization)
6. [Testing Strategy](#testing-strategy)
7. [Migration Path](#migration-path)
8. [Examples](#examples)

## Overview

Hexagonal Architecture, also known as Ports and Adapters architecture, provides a way to create applications that are independent of external concerns. This implementation guide shows how to structure the LPR system following hexagonal principles.

### Key Benefits

- **Testability**: Business logic can be tested in isolation
- **Maintainability**: Clear separation of concerns
- **Flexibility**: Easy to swap external dependencies
- **Independence**: Core business logic is framework-agnostic

### Core Concept

```
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Web UI    │  │  Database   │  │  External   │         │
│  │             │  │             │  │    APIs     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                 │                 │              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Adapter    │  │  Adapter    │  │  Adapter    │         │
│  │             │  │             │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                 │                 │              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    Port     │  │    Port     │  │    Port     │         │
│  │             │  │             │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Application Core                         │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │              Domain Layer                           │ │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │ │ │
│  │  │  │   Entity    │  │ Value Object│  │   Service   │ │ │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │            Application Layer                        │ │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │ │ │
│  │  │  │  Use Case   │  │   Handler   │  │   Service   │ │ │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Architecture Principles

### 1. Dependency Inversion
- High-level modules should not depend on low-level modules
- Both should depend on abstractions (interfaces)
- Abstractions should not depend on details

### 2. Ports and Adapters
- **Ports**: Interfaces that define contracts
- **Adapters**: Implementations that fulfill contracts
- **Primary Ports**: For incoming requests (controllers)
- **Secondary Ports**: For outgoing requests (repositories)

### 3. Domain-Centric Design
- Business logic lives in the domain layer
- External concerns are kept at the edges
- Domain entities are independent of frameworks

## Layer Structure

### Domain Layer (Core)

The innermost layer containing business logic:

```python
# Domain entities
class Camera:
    def __init__(self, camera_id: str, name: str, ip_address: str):
        self.id = camera_id
        self.name = name
        self.ip_address = ip_address
        self.status = CameraStatus.INACTIVE
        self.configuration = CameraConfiguration()
        self.health_metrics = HealthMetrics()
    
    def activate(self) -> None:
        if not self.is_configured():
            raise CameraNotConfiguredException(f"Camera {self.id} not configured")
        
        self.status = CameraStatus.ACTIVE
        self.record_status_change(CameraStatusChanged(self.id, CameraStatus.ACTIVE))
    
    def update_health_metrics(self, metrics: HealthMetrics) -> None:
        self.health_metrics = metrics
        if metrics.is_unhealthy():
            self.record_health_alert(CameraHealthAlert(self.id, metrics))

# Value objects
@dataclass(frozen=True)
class CameraConfiguration:
    resolution: Resolution
    frame_rate: int
    stream_url: str
    authentication: Optional[Authentication] = None
    
    def __post_init__(self):
        if self.frame_rate <= 0:
            raise ValueError("Frame rate must be positive")

# Domain services
class CameraHealthService:
    def __init__(self, health_checker: HealthChecker):
        self._health_checker = health_checker
    
    async def check_camera_health(self, camera: Camera) -> HealthMetrics:
        return await self._health_checker.check_health(camera.stream_url)
    
    def determine_health_status(self, metrics: HealthMetrics) -> HealthStatus:
        if metrics.response_time > 5000:  # 5 seconds
            return HealthStatus.UNHEALTHY
        elif metrics.response_time > 2000:  # 2 seconds
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
```

### Application Layer

Orchestrates domain objects and coordinates business workflows:

```python
# Use cases
class RegisterCameraUseCase:
    def __init__(self, camera_repository: CameraRepository, event_publisher: EventPublisher):
        self._camera_repository = camera_repository
        self._event_publisher = event_publisher
    
    async def execute(self, command: RegisterCameraCommand) -> CameraRegistrationResult:
        # Validate command
        self._validate_command(command)
        
        # Check if camera already exists
        existing_camera = await self._camera_repository.get_by_ip(command.ip_address)
        if existing_camera:
            raise CameraAlreadyExistsException(command.ip_address)
        
        # Create new camera
        camera = Camera(
            camera_id=str(uuid.uuid4()),
            name=command.name,
            ip_address=command.ip_address
        )
        
        # Configure camera
        configuration = CameraConfiguration(
            resolution=command.resolution,
            frame_rate=command.frame_rate,
            stream_url=command.stream_url
        )
        camera.configure(configuration)
        
        # Save camera
        await self._camera_repository.save(camera)
        
        # Publish event
        await self._event_publisher.publish(CameraRegisteredEvent(camera.id, camera.name))
        
        return CameraRegistrationResult(camera.id, camera.name)

# Command handlers
class CameraCommandHandler:
    def __init__(self, camera_repository: CameraRepository):
        self._camera_repository = camera_repository
    
    async def handle_activate_camera(self, command: ActivateCameraCommand) -> None:
        camera = await self._camera_repository.get_by_id(command.camera_id)
        if not camera:
            raise CameraNotFoundException(command.camera_id)
        
        camera.activate()
        await self._camera_repository.save(camera)

# Query handlers
class CameraQueryHandler:
    def __init__(self, camera_repository: CameraRepository):
        self._camera_repository = camera_repository
    
    async def handle_get_camera_details(self, query: GetCameraDetailsQuery) -> CameraDetails:
        camera = await self._camera_repository.get_by_id(query.camera_id)
        if not camera:
            raise CameraNotFoundException(query.camera_id)
        
        return CameraDetails(
            id=camera.id,
            name=camera.name,
            status=camera.status,
            health_metrics=camera.health_metrics,
            configuration=camera.configuration
        )
```

### Infrastructure Layer

Implements ports and provides external integrations:

```python
# Repository implementation
class PostgreSQLCameraRepository(CameraRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, camera: Camera) -> None:
        camera_data = {
            'id': camera.id,
            'name': camera.name,
            'ip_address': camera.ip_address,
            'status': camera.status.value,
            'configuration': camera.configuration.to_dict(),
            'health_metrics': camera.health_metrics.to_dict()
        }
        
        stmt = text("""
            INSERT INTO cameras (id, name, ip_address, status, configuration, health_metrics)
            VALUES (:id, :name, :ip_address, :status, :configuration, :health_metrics)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                ip_address = EXCLUDED.ip_address,
                status = EXCLUDED.status,
                configuration = EXCLUDED.configuration,
                health_metrics = EXCLUDED.health_metrics,
                updated_at = NOW()
        """)
        
        await self._session.execute(stmt, camera_data)
        await self._session.commit()
    
    async def get_by_id(self, camera_id: str) -> Optional[Camera]:
        stmt = text("SELECT * FROM cameras WHERE id = :id")
        result = await self._session.execute(stmt, {'id': camera_id})
        row = result.first()
        
        if not row:
            return None
        
        return self._map_row_to_camera(row)
    
    def _map_row_to_camera(self, row) -> Camera:
        camera = Camera(
            camera_id=row.id,
            name=row.name,
            ip_address=row.ip_address
        )
        camera.status = CameraStatus(row.status)
        camera.configuration = CameraConfiguration.from_dict(row.configuration)
        camera.health_metrics = HealthMetrics.from_dict(row.health_metrics)
        return camera

# External service adapter
class HTTPHealthChecker(HealthChecker):
    def __init__(self, http_client: httpx.AsyncClient):
        self._http_client = http_client
    
    async def check_health(self, stream_url: str) -> HealthMetrics:
        start_time = time.time()
        
        try:
            response = await self._http_client.get(stream_url, timeout=10.0)
            response_time = (time.time() - start_time) * 1000  # milliseconds
            
            return HealthMetrics(
                response_time=response_time,
                status_code=response.status_code,
                is_responsive=response.status_code == 200,
                last_checked=datetime.now()
            )
        except httpx.TimeoutException:
            return HealthMetrics(
                response_time=10000,  # timeout
                status_code=0,
                is_responsive=False,
                last_checked=datetime.now()
            )
```

### Presentation Layer

Handles HTTP requests and responses:

```python
# FastAPI controller
class CameraController:
    def __init__(self, camera_service: CameraService):
        self._camera_service = camera_service
    
    async def register_camera(self, request: RegisterCameraRequest) -> CameraResponse:
        command = RegisterCameraCommand(
            name=request.name,
            ip_address=request.ip_address,
            resolution=request.resolution,
            frame_rate=request.frame_rate,
            stream_url=request.stream_url
        )
        
        result = await self._camera_service.register_camera(command)
        
        return CameraResponse(
            id=result.camera_id,
            name=result.name,
            status="registered"
        )
    
    async def get_camera(self, camera_id: str) -> CameraDetailsResponse:
        query = GetCameraDetailsQuery(camera_id=camera_id)
        camera_details = await self._camera_service.get_camera_details(query)
        
        return CameraDetailsResponse(
            id=camera_details.id,
            name=camera_details.name,
            status=camera_details.status,
            health=HealthResponse(
                response_time=camera_details.health_metrics.response_time,
                is_responsive=camera_details.health_metrics.is_responsive,
                last_checked=camera_details.health_metrics.last_checked
            )
        )

# Router definition
router = APIRouter(prefix="/cameras", tags=["cameras"])

@router.post("/", response_model=CameraResponse)
async def register_camera(
    request: RegisterCameraRequest,
    camera_controller: CameraController = Depends(get_camera_controller)
):
    return await camera_controller.register_camera(request)

@router.get("/{camera_id}", response_model=CameraDetailsResponse)
async def get_camera(
    camera_id: str,
    camera_controller: CameraController = Depends(get_camera_controller)
):
    return await camera_controller.get_camera(camera_id)
```

## Implementation Patterns

### Port Interface Definition

```python
# Primary ports (for incoming requests)
class CameraService(ABC):
    @abstractmethod
    async def register_camera(self, command: RegisterCameraCommand) -> CameraRegistrationResult:
        pass
    
    @abstractmethod
    async def get_camera_details(self, query: GetCameraDetailsQuery) -> CameraDetails:
        pass
    
    @abstractmethod
    async def activate_camera(self, command: ActivateCameraCommand) -> None:
        pass

# Secondary ports (for outgoing requests)
class CameraRepository(ABC):
    @abstractmethod
    async def save(self, camera: Camera) -> None:
        pass
    
    @abstractmethod
    async def get_by_id(self, camera_id: str) -> Optional[Camera]:
        pass
    
    @abstractmethod
    async def get_by_ip(self, ip_address: str) -> Optional[Camera]:
        pass

class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        pass
```

### Dependency Injection

```python
# Service implementation
class CameraServiceImpl(CameraService):
    def __init__(
        self,
        camera_repository: CameraRepository,
        health_service: CameraHealthService,
        event_publisher: EventPublisher
    ):
        self._camera_repository = camera_repository
        self._health_service = health_service
        self._event_publisher = event_publisher
    
    async def register_camera(self, command: RegisterCameraCommand) -> CameraRegistrationResult:
        use_case = RegisterCameraUseCase(self._camera_repository, self._event_publisher)
        return await use_case.execute(command)

# Dependency container
class DIContainer:
    def __init__(self):
        self._services = {}
        self._setup_dependencies()
    
    def _setup_dependencies(self):
        # Infrastructure
        self._services['database_session'] = self._create_database_session()
        self._services['http_client'] = httpx.AsyncClient()
        
        # Repositories
        self._services['camera_repository'] = PostgreSQLCameraRepository(
            self._services['database_session']
        )
        
        # External services
        self._services['health_checker'] = HTTPHealthChecker(
            self._services['http_client']
        )
        
        # Domain services
        self._services['health_service'] = CameraHealthService(
            self._services['health_checker']
        )
        
        # Application services
        self._services['camera_service'] = CameraServiceImpl(
            self._services['camera_repository'],
            self._services['health_service'],
            self._services['event_publisher']
        )
    
    def get(self, service_name: str):
        return self._services[service_name]
```

## Code Organization

### Directory Structure

```
src/
├── domain/
│   ├── entities/
│   │   ├── camera.py
│   │   ├── detection.py
│   │   └── vehicle.py
│   ├── value_objects/
│   │   ├── camera_configuration.py
│   │   ├── health_metrics.py
│   │   └── license_plate.py
│   ├── services/
│   │   ├── camera_health_service.py
│   │   └── detection_service.py
│   ├── events/
│   │   ├── camera_events.py
│   │   └── detection_events.py
│   └── exceptions/
│       └── domain_exceptions.py
├── application/
│   ├── commands/
│   │   ├── camera_commands.py
│   │   └── detection_commands.py
│   ├── queries/
│   │   ├── camera_queries.py
│   │   └── detection_queries.py
│   ├── handlers/
│   │   ├── camera_handlers.py
│   │   └── detection_handlers.py
│   ├── use_cases/
│   │   ├── camera_use_cases.py
│   │   └── detection_use_cases.py
│   └── services/
│       ├── camera_service.py
│       └── detection_service.py
├── infrastructure/
│   ├── repositories/
│   │   ├── postgresql_camera_repository.py
│   │   └── postgresql_detection_repository.py
│   ├── adapters/
│   │   ├── http_health_checker.py
│   │   └── redis_event_publisher.py
│   ├── external_services/
│   │   ├── yolo_detector.py
│   │   └── ocr_service.py
│   └── configuration/
│       └── database_config.py
└── presentation/
    ├── controllers/
    │   ├── camera_controller.py
    │   └── detection_controller.py
    ├── dto/
    │   ├── camera_dto.py
    │   └── detection_dto.py
    ├── routers/
    │   ├── camera_router.py
    │   └── detection_router.py
    └── middleware/
        ├── authentication_middleware.py
        └── error_handling_middleware.py
```

### Package Dependencies

```python
# Domain layer - No external dependencies
from typing import ABC, abstractmethod, Optional, List
from dataclasses import dataclass
from datetime import datetime
import uuid

# Application layer - Only depends on domain
from domain.entities.camera import Camera
from domain.services.camera_health_service import CameraHealthService
from domain.events.camera_events import CameraRegisteredEvent

# Infrastructure layer - Depends on domain and application
from sqlalchemy.ext.asyncio import AsyncSession
from domain.repositories.camera_repository import CameraRepository
from application.services.camera_service import CameraService

# Presentation layer - Depends on application
from fastapi import APIRouter, Depends, HTTPException
from application.services.camera_service import CameraService
from presentation.dto.camera_dto import CameraResponse
```

## Testing Strategy

### Unit Testing Domain Logic

```python
# Test domain entities
class TestCamera:
    def test_camera_activation_when_configured(self):
        # Arrange
        camera = Camera("cam_001", "Test Camera", "192.168.1.100")
        configuration = CameraConfiguration(
            resolution=Resolution(1920, 1080),
            frame_rate=30,
            stream_url="http://192.168.1.100:8080/stream"
        )
        camera.configure(configuration)
        
        # Act
        camera.activate()
        
        # Assert
        assert camera.status == CameraStatus.ACTIVE
        assert len(camera.domain_events) == 1
        assert isinstance(camera.domain_events[0], CameraStatusChanged)
    
    def test_camera_activation_fails_when_not_configured(self):
        # Arrange
        camera = Camera("cam_001", "Test Camera", "192.168.1.100")
        
        # Act & Assert
        with pytest.raises(CameraNotConfiguredException):
            camera.activate()

# Test domain services
class TestCameraHealthService:
    def test_determine_health_status_healthy(self):
        # Arrange
        service = CameraHealthService(Mock())
        metrics = HealthMetrics(response_time=1000, status_code=200, is_responsive=True)
        
        # Act
        status = service.determine_health_status(metrics)
        
        # Assert
        assert status == HealthStatus.HEALTHY
    
    def test_determine_health_status_unhealthy(self):
        # Arrange
        service = CameraHealthService(Mock())
        metrics = HealthMetrics(response_time=6000, status_code=0, is_responsive=False)
        
        # Act
        status = service.determine_health_status(metrics)
        
        # Assert
        assert status == HealthStatus.UNHEALTHY
```

### Integration Testing with Test Doubles

```python
# Test use cases with mock dependencies
class TestRegisterCameraUseCase:
    @pytest.fixture
    def mock_camera_repository(self):
        return Mock(spec=CameraRepository)
    
    @pytest.fixture
    def mock_event_publisher(self):
        return Mock(spec=EventPublisher)
    
    @pytest.fixture
    def use_case(self, mock_camera_repository, mock_event_publisher):
        return RegisterCameraUseCase(mock_camera_repository, mock_event_publisher)
    
    async def test_register_camera_success(self, use_case, mock_camera_repository, mock_event_publisher):
        # Arrange
        command = RegisterCameraCommand(
            name="Test Camera",
            ip_address="192.168.1.100",
            resolution=Resolution(1920, 1080),
            frame_rate=30,
            stream_url="http://192.168.1.100:8080/stream"
        )
        mock_camera_repository.get_by_ip.return_value = None
        
        # Act
        result = await use_case.execute(command)
        
        # Assert
        assert result.name == "Test Camera"
        mock_camera_repository.save.assert_called_once()
        mock_event_publisher.publish.assert_called_once()
    
    async def test_register_camera_fails_when_already_exists(self, use_case, mock_camera_repository):
        # Arrange
        command = RegisterCameraCommand(
            name="Test Camera",
            ip_address="192.168.1.100",
            resolution=Resolution(1920, 1080),
            frame_rate=30,
            stream_url="http://192.168.1.100/stream"
        )
        existing_camera = Camera("existing_id", "Existing Camera", "192.168.1.100")
        mock_camera_repository.get_by_ip.return_value = existing_camera
        
        # Act & Assert
        with pytest.raises(CameraAlreadyExistsException):
            await use_case.execute(command)
```

### End-to-End Testing

```python
# Test complete flow through HTTP API
class TestCameraAPI:
    @pytest.fixture
    async def client(self):
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    async def test_register_camera_endpoint(self, client):
        # Arrange
        camera_data = {
            "name": "Test Camera",
            "ip_address": "192.168.1.100",
            "resolution": {"width": 1920, "height": 1080},
            "frame_rate": 30,
            "stream_url": "http://192.168.1.100:8080/stream"
        }
        
        # Act
        response = await client.post("/cameras", json=camera_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Camera"
        assert "id" in data
    
    async def test_get_camera_endpoint(self, client):
        # Arrange
        # First create a camera
        camera_data = {
            "name": "Test Camera",
            "ip_address": "192.168.1.100",
            "resolution": {"width": 1920, "height": 1080},
            "frame_rate": 30,
            "stream_url": "http://192.168.1.100:8080/stream"
        }
        create_response = await client.post("/cameras", json=camera_data)
        camera_id = create_response.json()["id"]
        
        # Act
        response = await client.get(f"/cameras/{camera_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == camera_id
        assert data["name"] == "Test Camera"
```

## Migration Path

### Step 1: Extract Domain Logic

```python
# Before (monolithic service)
class CameraService:
    def __init__(self, db_session):
        self.db_session = db_session
    
    async def register_camera(self, camera_data):
        # Mix of business logic and database operations
        if not camera_data['name']:
            raise ValueError("Camera name is required")
        
        # Direct database access
        existing = await self.db_session.execute(
            "SELECT * FROM cameras WHERE ip_address = :ip",
            {"ip": camera_data['ip_address']}
        )
        if existing.first():
            raise Exception("Camera already exists")
        
        # Business logic mixed with persistence
        camera_id = str(uuid.uuid4())
        await self.db_session.execute(
            "INSERT INTO cameras (id, name, ip_address) VALUES (:id, :name, :ip)",
            {"id": camera_id, "name": camera_data['name'], "ip": camera_data['ip_address']}
        )
        
        return {"id": camera_id, "name": camera_data['name']}

# After (hexagonal architecture)
class CameraService:
    def __init__(self, camera_repository: CameraRepository, event_publisher: EventPublisher):
        self._camera_repository = camera_repository
        self._event_publisher = event_publisher
    
    async def register_camera(self, command: RegisterCameraCommand) -> CameraRegistrationResult:
        use_case = RegisterCameraUseCase(self._camera_repository, self._event_publisher)
        return await use_case.execute(command)
```

### Step 2: Introduce Ports

```python
# Define repository interface
class CameraRepository(ABC):
    @abstractmethod
    async def save(self, camera: Camera) -> None:
        pass
    
    @abstractmethod
    async def get_by_id(self, camera_id: str) -> Optional[Camera]:
        pass

# Create adapter for existing database code
class LegacyCameraRepository(CameraRepository):
    def __init__(self, db_session):
        self.db_session = db_session
    
    async def save(self, camera: Camera) -> None:
        # Adapt domain entity to database format
        camera_data = {
            'id': camera.id,
            'name': camera.name,
            'ip_address': camera.ip_address,
            'status': camera.status.value
        }
        
        await self.db_session.execute(
            "INSERT INTO cameras (...) VALUES (...) ON CONFLICT (...) DO UPDATE ...",
            camera_data
        )
```

### Step 3: Gradual Migration

```python
# Feature flag for gradual migration
class CameraServiceFacade:
    def __init__(self, legacy_service: LegacyCameraService, new_service: CameraService, feature_flags: FeatureFlags):
        self._legacy_service = legacy_service
        self._new_service = new_service
        self._feature_flags = feature_flags
    
    async def register_camera(self, request):
        if self._feature_flags.is_enabled("hexagonal_architecture"):
            # Use new hexagonal architecture
            command = RegisterCameraCommand(
                name=request.name,
                ip_address=request.ip_address,
                # ... other fields
            )
            result = await self._new_service.register_camera(command)
            return {"id": result.camera_id, "name": result.name}
        else:
            # Use legacy implementation
            return await self._legacy_service.register_camera(request)
```

## Examples

### Complete Camera Management Module

```python
# domain/entities/camera.py
class Camera:
    def __init__(self, camera_id: str, name: str, ip_address: str):
        self.id = camera_id
        self.name = name
        self.ip_address = ip_address
        self.status = CameraStatus.INACTIVE
        self.configuration: Optional[CameraConfiguration] = None
        self.health_metrics: Optional[HealthMetrics] = None
        self.domain_events: List[DomainEvent] = []
    
    def configure(self, configuration: CameraConfiguration) -> None:
        self.configuration = configuration
        self.record_event(CameraConfiguredEvent(self.id, configuration))
    
    def activate(self) -> None:
        if not self.configuration:
            raise CameraNotConfiguredException(f"Camera {self.id} not configured")
        
        self.status = CameraStatus.ACTIVE
        self.record_event(CameraStatusChanged(self.id, CameraStatus.ACTIVE))
    
    def update_health(self, health_metrics: HealthMetrics) -> None:
        self.health_metrics = health_metrics
        if health_metrics.is_unhealthy():
            self.record_event(CameraHealthDegradedEvent(self.id, health_metrics))
    
    def record_event(self, event: DomainEvent) -> None:
        self.domain_events.append(event)
    
    def clear_events(self) -> List[DomainEvent]:
        events = self.domain_events.copy()
        self.domain_events.clear()
        return events

# application/use_cases/register_camera_use_case.py
class RegisterCameraUseCase:
    def __init__(self, camera_repository: CameraRepository, event_publisher: EventPublisher):
        self._camera_repository = camera_repository
        self._event_publisher = event_publisher
    
    async def execute(self, command: RegisterCameraCommand) -> CameraRegistrationResult:
        # Business validation
        if not command.name or not command.name.strip():
            raise InvalidCameraNameException("Camera name cannot be empty")
        
        if not self._is_valid_ip_address(command.ip_address):
            raise InvalidIPAddressException(f"Invalid IP address: {command.ip_address}")
        
        # Check for duplicates
        existing_camera = await self._camera_repository.get_by_ip(command.ip_address)
        if existing_camera:
            raise CameraAlreadyExistsException(f"Camera with IP {command.ip_address} already exists")
        
        # Create camera entity
        camera = Camera(
            camera_id=str(uuid.uuid4()),
            name=command.name.strip(),
            ip_address=command.ip_address
        )
        
        # Configure camera
        configuration = CameraConfiguration(
            resolution=command.resolution,
            frame_rate=command.frame_rate,
            stream_url=command.stream_url
        )
        camera.configure(configuration)
        
        # Save to repository
        await self._camera_repository.save(camera)
        
        # Publish events
        events = camera.clear_events()
        for event in events:
            await self._event_publisher.publish(event)
        
        return CameraRegistrationResult(camera.id, camera.name)
    
    def _is_valid_ip_address(self, ip_address: str) -> bool:
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

# infrastructure/repositories/postgresql_camera_repository.py
class PostgreSQLCameraRepository(CameraRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, camera: Camera) -> None:
        camera_orm = CameraORM(
            id=camera.id,
            name=camera.name,
            ip_address=camera.ip_address,
            status=camera.status.value,
            configuration=camera.configuration.to_dict() if camera.configuration else None,
            health_metrics=camera.health_metrics.to_dict() if camera.health_metrics else None
        )
        
        self._session.add(camera_orm)
        await self._session.commit()
    
    async def get_by_id(self, camera_id: str) -> Optional[Camera]:
        query = select(CameraORM).where(CameraORM.id == camera_id)
        result = await self._session.execute(query)
        camera_orm = result.scalar_one_or_none()
        
        if not camera_orm:
            return None
        
        return self._map_orm_to_domain(camera_orm)
    
    async def get_by_ip(self, ip_address: str) -> Optional[Camera]:
        query = select(CameraORM).where(CameraORM.ip_address == ip_address)
        result = await self._session.execute(query)
        camera_orm = result.scalar_one_or_none()
        
        if not camera_orm:
            return None
        
        return self._map_orm_to_domain(camera_orm)
    
    def _map_orm_to_domain(self, camera_orm: CameraORM) -> Camera:
        camera = Camera(
            camera_id=camera_orm.id,
            name=camera_orm.name,
            ip_address=camera_orm.ip_address
        )
        
        camera.status = CameraStatus(camera_orm.status)
        
        if camera_orm.configuration:
            camera.configuration = CameraConfiguration.from_dict(camera_orm.configuration)
        
        if camera_orm.health_metrics:
            camera.health_metrics = HealthMetrics.from_dict(camera_orm.health_metrics)
        
        return camera

# presentation/controllers/camera_controller.py
class CameraController:
    def __init__(self, camera_service: CameraService):
        self._camera_service = camera_service
    
    async def register_camera(self, request: RegisterCameraRequest) -> CameraResponse:
        try:
            command = RegisterCameraCommand(
                name=request.name,
                ip_address=request.ip_address,
                resolution=Resolution(request.resolution.width, request.resolution.height),
                frame_rate=request.frame_rate,
                stream_url=request.stream_url
            )
            
            result = await self._camera_service.register_camera(command)
            
            return CameraResponse(
                id=result.camera_id,
                name=result.name,
                status="registered",
                message="Camera registered successfully"
            )
        
        except CameraAlreadyExistsException as e:
            raise HTTPException(status_code=409, detail=str(e))
        except (InvalidCameraNameException, InvalidIPAddressException) as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error registering camera: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
```

This implementation provides a complete example of hexagonal architecture with clear separation of concerns, proper dependency injection, and comprehensive testing strategies. The migration path allows for gradual adoption without disrupting existing functionality.

## Conclusion

Hexagonal architecture provides a robust foundation for building maintainable, testable, and flexible applications. By following the patterns and principles outlined in this guide, the LPR system can achieve:

- **Clean separation of concerns** between business logic and technical details
- **High testability** through dependency injection and interface-based design
- **Flexibility** to adapt to changing requirements and technologies
- **Maintainability** through clear architectural boundaries

The migration path allows for gradual adoption, ensuring business continuity while improving the system's architectural quality.