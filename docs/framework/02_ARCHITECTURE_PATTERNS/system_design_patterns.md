# Universal System Design Patterns

## Overview
This document provides comprehensive, reusable architecture patterns proven in production environments. These patterns can be applied to any software system, regardless of domain or technology stack.

## Core Architecture Philosophy

### Monolithic with Modular Services (Proven Pattern)
This pattern provides the benefits of microservices (modularity, testability) while maintaining the simplicity of monolithic deployment.

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Router    │  │   Router    │  │   Router    │   ...   │
│  │  (API/Web)  │  │  (API/Web)  │  │  (API/Web)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Service   │  │   Service   │  │   Service   │   ...   │
│  │ (Business)  │  │ (Business)  │  │ (Business)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                   Repository Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Repository  │  │ Repository  │  │ Repository  │   ...   │
│  │   (Data)    │  │   (Data)    │  │   (Data)    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                     Core Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Models    │  │   Config    │  │ Exceptions  │   ...   │
│  │ (Entities)  │  │ (Settings)  │  │  (Errors)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Benefits of This Architecture
- **Single Deployment Unit**: Simplified deployment and debugging
- **Modular Design**: Clear separation of concerns
- **Easy Testing**: Isolated components with dependency injection
- **Performance**: No network overhead between services
- **Gradual Evolution**: Can split into microservices when needed

## Universal Design Patterns

### 1. Repository Pattern (Data Access Abstraction)

**Purpose**: Abstract data access logic from business logic

**Implementation Template**:
```python
# Abstract base repository
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')
ID = TypeVar('ID')

class BaseRepository(ABC, Generic[T, ID]):
    """Abstract base repository interface."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass
    
    @abstractmethod
    async def update(self, entity_id: ID, update_data: dict) -> Optional[T]:
        """Update existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """Delete entity by ID."""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: ID) -> bool:
        """Check if entity exists."""
        pass

# Concrete implementation
class SQLRepository(BaseRepository[T, ID]):
    """SQLAlchemy implementation of repository pattern."""
    
    def __init__(self, db_session, model_class):
        self.db_session = db_session
        self.model_class = model_class
    
    async def create(self, entity: T) -> T:
        """Create new entity in database."""
        db_obj = self.model_class(**entity.dict())
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        return db_obj
    
    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """Get entity by ID from database."""
        result = await self.db_session.get(self.model_class, entity_id)
        return result
    
    # ... implement other methods
```

**Usage Benefits**:
- Database technology can be changed without affecting business logic
- Easy to mock for testing
- Consistent data access patterns across the application
- Support for multiple data sources

### 2. Service Layer Pattern (Business Logic Encapsulation)

**Purpose**: Centralize business logic and coordinate between repositories

**Implementation Template**:
```python
# Abstract service base
from abc import ABC
from typing import Optional, List

class BaseService(ABC):
    """Abstract base service class."""
    
    def __init__(self, repository: BaseRepository):
        self.repository = repository
        self.logger = get_logger(self.__class__.__name__)
    
    async def create_entity(self, create_data: dict) -> T:
        """Create new entity with business logic validation."""
        # Business validation
        await self._validate_create_data(create_data)
        
        # Create entity
        entity = await self.repository.create(create_data)
        
        # Post-creation business logic
        await self._post_create_actions(entity)
        
        return entity
    
    async def get_entity(self, entity_id: ID) -> Optional[T]:
        """Get entity with business logic."""
        entity = await self.repository.get_by_id(entity_id)
        if not entity:
            raise NotFoundError(f"Entity {entity_id} not found")
        
        # Apply business rules
        return await self._apply_business_rules(entity)
    
    # Abstract methods for business logic
    async def _validate_create_data(self, data: dict) -> None:
        """Override to implement creation validation."""
        pass
    
    async def _post_create_actions(self, entity: T) -> None:
        """Override to implement post-creation logic."""
        pass
    
    async def _apply_business_rules(self, entity: T) -> T:
        """Override to implement business rules."""
        return entity

# Concrete service implementation
class UserService(BaseService):
    """User management service with business logic."""
    
    def __init__(self, user_repository: UserRepository, email_service: EmailService):
        super().__init__(user_repository)
        self.email_service = email_service
    
    async def _validate_create_data(self, data: dict) -> None:
        """Validate user creation data."""
        # Check email uniqueness
        if await self.repository.get_by_email(data.get('email')):
            raise ConflictError("Email already exists")
        
        # Validate password strength
        if not self._is_strong_password(data.get('password')):
            raise ValidationError("Password does not meet requirements")
    
    async def _post_create_actions(self, user) -> None:
        """Send welcome email after user creation."""
        await self.email_service.send_welcome_email(user.email)
        self.logger.info(f"User created: {user.id}")
```

**Usage Benefits**:
- Business logic centralized and reusable
- Easy to test business rules in isolation
- Consistent error handling and logging
- Clear transaction boundaries

### 3. Factory Pattern (Service Creation and Management)

**Purpose**: Centralize creation and configuration of services

**Implementation Template**:
```python
# Service factory for dependency injection
from typing import Dict, Any
from functools import lru_cache

class ServiceFactory:
    """Factory for creating and managing service instances."""
    
    def __init__(self, db_session, config: Settings):
        self.db_session = db_session
        self.config = config
        self._services: Dict[str, Any] = {}
    
    @lru_cache()
    def get_user_service(self) -> UserService:
        """Get or create user service instance."""
        if 'user_service' not in self._services:
            user_repo = self.get_user_repository()
            email_service = self.get_email_service()
            self._services['user_service'] = UserService(user_repo, email_service)
        return self._services['user_service']
    
    @lru_cache()
    def get_user_repository(self) -> UserRepository:
        """Get or create user repository instance."""
        if 'user_repository' not in self._services:
            self._services['user_repository'] = UserRepository(self.db_session)
        return self._services['user_repository']
    
    @lru_cache()
    def get_email_service(self) -> EmailService:
        """Get or create email service instance."""
        if 'email_service' not in self._services:
            self._services['email_service'] = EmailService(
                smtp_server=self.config.SMTP_SERVER,
                smtp_port=self.config.SMTP_PORT,
                username=self.config.SMTP_USERNAME,
                password=self.config.SMTP_PASSWORD,
            )
        return self._services['email_service']

# FastAPI dependency provider
@lru_cache()
def get_service_factory() -> ServiceFactory:
    """Get service factory instance."""
    return ServiceFactory(get_db(), get_settings())

# Usage in FastAPI routes
@router.post("/users")
async def create_user(
    user_data: UserCreateSchema,
    factory: ServiceFactory = Depends(get_service_factory)
):
    user_service = factory.get_user_service()
    return await user_service.create_entity(user_data.dict())
```

**Usage Benefits**:
- Centralized dependency management
- Easy to mock services for testing
- Consistent service configuration
- Lazy loading of services

### 4. Interface-Based Design (Extensibility and Testing)

**Purpose**: Define clear contracts for components to enable easy testing and extension

**Implementation Template**:
```python
# Abstract interfaces
from abc import ABC, abstractmethod

class CacheInterface(ABC):
    """Abstract interface for caching services."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

class NotificationInterface(ABC):
    """Abstract interface for notification services."""
    
    @abstractmethod
    async def send_notification(self, recipient: str, message: str, type: str) -> bool:
        """Send notification to recipient."""
        pass

# Concrete implementations
class RedisCache(CacheInterface):
    """Redis implementation of cache interface."""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        value = await self.redis_client.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in Redis with expiration."""
        json_value = json.dumps(value)
        return await self.redis_client.setex(key, expire, json_value)

class EmailNotification(NotificationInterface):
    """Email implementation of notification interface."""
    
    def __init__(self, smtp_config):
        self.smtp_config = smtp_config
    
    async def send_notification(self, recipient: str, message: str, type: str) -> bool:
        """Send email notification."""
        # Implementation for sending email
        pass

# Mock implementations for testing
class MockCache(CacheInterface):
    """Mock cache for testing."""
    
    def __init__(self):
        self.data = {}
    
    async def get(self, key: str) -> Optional[Any]:
        return self.data.get(key)
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        self.data[key] = value
        return True
```

**Usage Benefits**:
- Easy to swap implementations (Redis vs Memory cache)
- Simplified testing with mock implementations
- Clear contracts between components
- Support for multiple implementations

### 5. Event-Driven Architecture (Scalability and Decoupling)

**Purpose**: Decouple components through event publishing and subscription

**Implementation Template**:
```python
# Event system
from typing import Callable, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    """Base event class."""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str

class EventBus:
    """Simple event bus for intra-application communication."""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]):
        """Subscribe to event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: Event):
        """Publish event to all subscribers."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_type}: {e}")

# Event handlers
class UserEventHandler:
    """Handler for user-related events."""
    
    def __init__(self, email_service: EmailService, analytics_service: AnalyticsService):
        self.email_service = email_service
        self.analytics_service = analytics_service
    
    async def handle_user_created(self, event: Event):
        """Handle user creation event."""
        user_data = event.data
        
        # Send welcome email
        await self.email_service.send_welcome_email(user_data['email'])
        
        # Track analytics
        await self.analytics_service.track_user_registration(user_data['id'])
    
    async def handle_user_updated(self, event: Event):
        """Handle user update event."""
        user_data = event.data
        
        # Track profile update
        await self.analytics_service.track_profile_update(user_data['id'])

# Service integration with events
class UserService(BaseService):
    """User service with event publishing."""
    
    def __init__(self, repository: UserRepository, event_bus: EventBus):
        super().__init__(repository)
        self.event_bus = event_bus
    
    async def create_entity(self, create_data: dict) -> User:
        """Create user and publish event."""
        user = await super().create_entity(create_data)
        
        # Publish user created event
        event = Event(
            event_type="user.created",
            data=user.dict(),
            timestamp=datetime.utcnow(),
            source="user_service"
        )
        await self.event_bus.publish(event)
        
        return user
```

**Usage Benefits**:
- Loose coupling between components
- Easy to add new functionality without modifying existing code
- Scalable event processing
- Clear audit trail of system events

## Real-Time Communication Patterns

### WebSocket Integration Pattern

**Purpose**: Provide real-time updates to clients

**Implementation Template**:
```python
# WebSocket manager
from typing import Dict, List
from fastapi import WebSocket
import json

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all clients."""
        for client_connections in self.active_connections.values():
            for connection in client_connections:
                await connection.send_text(json.dumps(message))

# WebSocket integration with services
class RealtimeService:
    """Service for real-time updates."""
    
    def __init__(self, connection_manager: ConnectionManager, event_bus: EventBus):
        self.connection_manager = connection_manager
        self.event_bus = event_bus
        
        # Subscribe to events for real-time updates
        self.event_bus.subscribe("user.created", self.handle_user_created)
        self.event_bus.subscribe("data.updated", self.handle_data_updated)
    
    async def handle_user_created(self, event: Event):
        """Send real-time update for new user."""
        message = {
            "type": "user_created",
            "data": event.data,
            "timestamp": event.timestamp.isoformat()
        }
        await self.connection_manager.broadcast(message)
    
    async def handle_data_updated(self, event: Event):
        """Send real-time update for data changes."""
        message = {
            "type": "data_updated",
            "data": event.data,
            "timestamp": event.timestamp.isoformat()
        }
        # Send to specific client if available in event data
        client_id = event.data.get('client_id')
        if client_id:
            await self.connection_manager.send_personal_message(message, client_id)
        else:
            await self.connection_manager.broadcast(message)
```

## Error Handling Patterns

### Comprehensive Error Management

**Implementation Template**:
```python
# Custom exception hierarchy
class AppException(Exception):
    """Base application exception."""
    
    def __init__(self, message: str, status_code: int = 500, detail: dict = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)

class ValidationError(AppException):
    """Validation error exception."""
    def __init__(self, message: str, detail: dict = None):
        super().__init__(message, status_code=422, detail=detail)

class NotFoundError(AppException):
    """Resource not found exception."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class UnauthorizedError(AppException):
    """Unauthorized access exception."""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

# Global exception handler
from fastapi import Request
from fastapi.responses import JSONResponse

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Global exception handler for custom exceptions."""
    logger.error(f"Application error: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code,
        "detail": exc.detail
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

# Service-level error handling
class BaseService:
    """Base service with error handling patterns."""
    
    async def safe_execute(self, operation: Callable, *args, **kwargs):
        """Execute operation with error handling."""
        try:
            return await operation(*args, **kwargs)
        except ValidationError:
            # Re-raise validation errors
            raise
        except NotFoundError:
            # Re-raise not found errors
            raise
        except Exception as e:
            # Log unexpected errors and raise generic error
            self.logger.error(f"Unexpected error in {operation.__name__}: {e}")
            raise AppException("Internal server error occurred")
```

## Data Validation Patterns

### Pydantic Schema Design

**Implementation Template**:
```python
# Base schema classes
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        validate_assignment = True
        use_enum_values = True

class CreateSchema(BaseSchema):
    """Base schema for creation operations."""
    pass

class UpdateSchema(BaseSchema):
    """Base schema for update operations."""
    pass

class ResponseSchema(BaseSchema):
    """Base schema for response operations."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# Specific schema implementations
class UserCreateSchema(CreateSchema):
    """Schema for user creation."""
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

class UserUpdateSchema(UpdateSchema):
    """Schema for user updates."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    
class UserResponseSchema(ResponseSchema):
    """Schema for user responses."""
    email: str
    first_name: str
    last_name: str
    is_active: bool
    last_login: Optional[datetime] = None
```

## Configuration Management Patterns

### Environment-Based Configuration

**Implementation Template**:
```python
# Configuration management
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment support."""
    
    # Application settings
    APP_NAME: str = "Application"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    
    # Database settings
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Feature flags
    FEATURE_REGISTRATION: bool = True
    FEATURE_EMAIL_VERIFICATION: bool = True
    
    # External service settings
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

## Summary

These universal design patterns provide:

1. **Scalable Architecture**: Monolithic with modular services approach
2. **Clean Code**: Repository, Service, and Factory patterns
3. **Testability**: Interface-based design with dependency injection
4. **Real-time Capability**: WebSocket integration patterns
5. **Robust Error Handling**: Comprehensive exception management
6. **Data Validation**: Pydantic schema patterns
7. **Configuration Management**: Environment-based settings

**Implementation Benefits**:
- **Rapid Development**: Proven patterns accelerate development
- **High Quality**: Built-in best practices and error handling
- **Easy Testing**: Mockable interfaces and dependency injection
- **Scalability**: Patterns support growth and complexity
- **Maintainability**: Clear separation of concerns and responsibilities

**AI Agent Usage**:
Any AI agent can use these patterns by:
1. Copying the template code
2. Adapting to specific domain requirements
3. Implementing domain-specific business logic
4. Following the established patterns for consistency

These patterns have been proven in production environments and provide a solid foundation for any software system.