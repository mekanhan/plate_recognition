# Python FastAPI Implementation Guide

## Overview
This guide provides comprehensive implementation patterns for building production-ready applications using Python with FastAPI. It follows the Universal Software Development Framework principles and includes all necessary components for scalable, maintainable applications.

## Technology Stack

### Core Technologies
- **Python**: 3.11+
- **FastAPI**: 0.104+ (ASGI web framework)
- **Uvicorn**: ASGI server with high performance
- **Pydantic**: Data validation and settings management
- **SQLAlchemy**: Async ORM for database operations
- **Alembic**: Database migration management

### Database Support
- **Primary**: PostgreSQL with asyncpg driver
- **Alternative**: SQLite with aiosqlite (development)
- **Caching**: Redis for session and application caching
- **Search**: Elasticsearch (optional)

### Additional Libraries
- **Authentication**: python-jose, passlib, python-multipart
- **HTTP Requests**: httpx (async HTTP client)
- **Task Queue**: Celery with Redis broker
- **Monitoring**: prometheus-client, structlog
- **Testing**: pytest, pytest-asyncio, httpx (test client)

## Project Structure

```
fastapi_project/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Application configuration
│   │   ├── database.py         # Database connection and sessions
│   │   ├── security.py         # Authentication and authorization
│   │   └── exceptions.py       # Custom exception handlers
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Base SQLAlchemy model
│   │   ├── user.py             # User model
│   │   └── mixins.py           # Model mixins
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── common.py           # Common schemas
│   │   └── responses.py        # API response schemas
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py             # Base repository class
│   │   └── user.py             # User repository
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user.py             # User business logic
│   │   └── auth.py             # Authentication service
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── api.py              # API router aggregator
│   │   ├── auth.py             # Authentication routes
│   │   └── users.py            # User management routes
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication dependencies
│   │   └── database.py         # Database dependencies
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py          # Utility functions
│       └── validators.py       # Custom validators
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest configuration
│   ├── test_main.py            # Main application tests
│   └── test_users.py           # User endpoint tests
├── alembic/                    # Database migrations
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── init_db.py              # Database initialization
│   └── create_superuser.py     # Admin user creation
├── requirements/
│   ├── base.txt                # Base requirements
│   ├── development.txt         # Development requirements
│   └── production.txt          # Production requirements
├── .env.example                # Environment variables example
├── pyproject.toml              # Poetry configuration
└── README.md
```

## Core Implementation

### 1. Application Configuration

```python
# app/core/config.py
from functools import lru_cache
from typing import Optional, List, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "FastAPI Application"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., min_length=32)
    
    # Database
    DATABASE_URL: str = Field(..., description="Database connection URL")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: Optional[str] = "/docs"
    REDOC_URL: Optional[str] = "/redoc"
    
    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'sqlite://')):
            raise ValueError('DATABASE_URL must use postgresql:// or sqlite://')
        return v
    
    @property
    def is_development(self) -> bool:
        return self.DEBUG
    
    @property
    def is_production(self) -> bool:
        return not self.DEBUG
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

### 2. Database Setup

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import asyncio

from app.core.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db() -> None:
    """Close database connection."""
    await engine.dispose()
```

### 3. Base Models

```python
# app/models/base.py
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from app.core.database import Base

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

# app/models/user.py
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class User(BaseModel):
    """User model."""
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

### 4. Pydantic Schemas

```python
# app/schemas/common.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        validate_assignment = True
        arbitrary_types_allowed = True

class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: datetime
    updated_at: Optional[datetime] = None

# app/schemas/user.py
from pydantic import EmailStr, Field, validator
from typing import Optional
from app.schemas.common import BaseSchema, TimestampSchema

class UserBase(BaseSchema):
    """Base user schema."""
    
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    bio: Optional[str] = Field(None, max_length=1000)

class UserCreate(UserBase):
    """Schema for user creation."""
    
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseSchema):
    """Schema for user updates."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None

class UserInDB(UserBase, TimestampSchema):
    """Schema for user in database."""
    
    id: int
    is_superuser: bool = False
    avatar_url: Optional[str] = None

class UserResponse(UserInDB):
    """Schema for user API responses."""
    
    full_name: str
    
    @validator('full_name', always=True)
    def get_full_name(cls, v, values):
        return f"{values.get('first_name', '')} {values.get('last_name', '')}".strip()

class UserListResponse(BaseSchema):
    """Schema for paginated user list."""
    
    users: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int
```

### 5. Repository Pattern

```python
# app/repositories/base.py
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> Optional[ModelType]:
        """Get single record by ID."""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get multiple records with optional filtering."""
        query = select(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create new record."""
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: int, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update existing record."""
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_data)
            .returning(self.model)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one_or_none()
    
    async def delete(self, id: int) -> bool:
        """Delete record by ID."""
        query = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """Count records with optional filtering."""
        query = select(func.count(self.model.id))
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        
        result = await self.db.execute(query)
        return result.scalar()

# app/repositories/user.py
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    """User-specific repository operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users only."""
        return await self.get_multi(skip=skip, limit=limit, is_active=True)
    
    async def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by name or email."""
        search = f"%{search_term}%"
        query = (
            select(User)
            .where(
                (User.first_name.ilike(search)) |
                (User.last_name.ilike(search)) |
                (User.email.ilike(search))
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
```

### 6. Service Layer

```python
# app/services/user.py
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.core.exceptions import ConflictError, NotFoundError, ValidationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """User business logic service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create new user with validation."""
        
        # Check if email already exists
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ConflictError("Email address already registered")
        
        # Hash password
        hashed_password = self._hash_password(user_data.password)
        
        # Prepare user data
        user_dict = user_data.dict(exclude={'password', 'confirm_password'})
        user_dict['hashed_password'] = hashed_password
        
        # Create user
        user = await self.repository.create(user_dict)
        
        # Send welcome email (if email service is configured)
        await self._send_welcome_email(user.email)
        
        return user
    
    async def get_user(self, user_id: int) -> User:
        """Get user by ID."""
        user = await self.repository.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.repository.get_by_email(email)
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information."""
        
        # Check if user exists
        existing_user = await self.repository.get(user_id)
        if not existing_user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Update user
        update_data = user_data.dict(exclude_unset=True)
        updated_user = await self.repository.update(user_id, update_data)
        
        return updated_user
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete by deactivating)."""
        
        # Check if user exists
        existing_user = await self.repository.get(user_id)
        if not existing_user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Deactivate instead of hard delete
        await self.repository.update(user_id, {"is_active": False})
        return True
    
    async def list_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> tuple[List[User], int]:
        """List users with pagination and filtering."""
        
        if search:
            users = await self.repository.search_users(search, skip, limit)
            total = len(users)  # Simplified count for search
        elif active_only:
            users = await self.repository.get_active_users(skip, limit)
            total = await self.repository.count(is_active=True)
        else:
            users = await self.repository.get_multi(skip=skip, limit=limit)
            total = await self.repository.count()
        
        return users, total
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        
        user = await self.repository.get_by_email(email)
        if not user or not user.is_active:
            return None
        
        if not self._verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    async def _send_welcome_email(self, email: str) -> None:
        """Send welcome email to new user."""
        # Implementation depends on email service
        # This is a placeholder
        pass
```

### 7. API Routes

```python
# app/routers/users.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.user import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.core.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/users", tags=["users"])

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency to get user service."""
    return UserService(db)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user."""
    try:
        user = await user_service.create_user(user_data)
        return user
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID."""
    try:
        user = await user_service.get_user(user_id)
        return user
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """Update user information."""
    try:
        user = await user_service.update_user(user_id, user_data)
        return user
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Delete user."""
    try:
        await user_service.delete_user(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    user_service: UserService = Depends(get_user_service)
):
    """List users with pagination and filtering."""
    
    users, total = await user_service.list_users(
        skip=skip, 
        limit=limit, 
        search=search, 
        active_only=active_only
    )
    
    return UserListResponse(
        users=users,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )
```

### 8. Main Application

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.core.exceptions import setup_exception_handlers
from app.routers.api import api_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    logging.info("Database initialized")
    yield
    # Shutdown
    await close_db()
    logging.info("Database closed")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready FastAPI application",
    docs_url=settings.DOCS_URL if settings.DEBUG else None,
    redoc_url=settings.REDOC_URL if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }
```

## Testing Implementation

### Pytest Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.core.config import get_settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        
        async with TestingSessionLocal() as session:
            yield session
            
        await connection.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }
```

### Test Examples

```python
# tests/test_users.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import UserService
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, test_user_data):
    """Test user creation endpoint."""
    response = await client.post("/api/v1/users/", json=test_user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["first_name"] == test_user_data["first_name"]
    assert "id" in data
    assert "hashed_password" not in data  # Password should not be returned

@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, db_session: AsyncSession, test_user_data):
    """Test get user endpoint."""
    # Create user first
    user_service = UserService(db_session)
    user_create = UserCreate(**test_user_data)
    created_user = await user_service.create_user(user_create)
    
    # Get user
    response = await client.get(f"/api/v1/users/{created_user.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["id"] == created_user.id

@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, db_session: AsyncSession, test_user_data):
    """Test list users endpoint."""
    # Create multiple users
    user_service = UserService(db_session)
    for i in range(3):
        user_data = test_user_data.copy()
        user_data["email"] = f"user{i}@example.com"
        user_create = UserCreate(**user_data)
        await user_service.create_user(user_create)
    
    # List users
    response = await client.get("/api/v1/users/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["users"]) == 3
```

## Deployment Configuration

### Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Development stage
FROM base as development
RUN poetry install --with dev
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
RUN poetry install --only main
COPY . .
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      target: development
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/fastapi_db
      - REDIS_URL=redis://redis:6379
    volumes:
      - .:/app
      - /app/.venv
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=fastapi_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Best Practices and Performance

### 1. Database Optimization
- Use connection pooling with appropriate pool sizes
- Implement database indexes for frequently queried fields
- Use async operations throughout the application
- Implement proper error handling and rollback strategies

### 2. Security Best Practices
- Use environment variables for sensitive configuration
- Implement proper password hashing with bcrypt
- Add rate limiting for API endpoints
- Use HTTPS in production
- Implement proper CORS configuration

### 3. Performance Optimization
- Use async/await throughout the application
- Implement caching with Redis for frequently accessed data
- Use pagination for list endpoints
- Implement proper logging and monitoring
- Use database query optimization techniques

### 4. Error Handling
- Implement custom exception classes
- Use consistent error response formats
- Log errors appropriately with proper log levels
- Implement graceful degradation for external service failures

This FastAPI implementation provides a solid foundation for building scalable, maintainable web applications following the Universal Software Development Framework principles.