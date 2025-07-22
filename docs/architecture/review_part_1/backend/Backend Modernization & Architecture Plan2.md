##### Week 11-12: User Management & Notification Services
```yaml
tasks:
  - name: "Implement user management"
    duration: 4 days
    deliverable: "User CRUD, authentication, and RBAC"
  
  - name: "Implement notification system"
    duration: 4 days
    deliverable: "Multi-channel notifications with templates"
  
  - name: "API Gateway implementation"
    duration: 3 days
    deliverable: "Centralized routing, authentication, and rate limiting"
  
  - name: "System integration testing"
    duration: 3 days
    deliverable: "End-to-end testing of complete system"

resources:
  - "3 Senior Backend Developers"
  - "1 Security Specialist"
```

#### Phase 4: Production Deployment (Weeks 13-16)

##### Week 13-14: Production Infrastructure
```yaml
tasks:
  - name: "Kubernetes cluster setup"
    duration: 4 days
    deliverable: "Production-ready K8s cluster with monitoring"
  
  - name: "Database clustering and backup"
    duration: 3 days
    deliverable: "HA database setup with automated backups"
  
  - name: "Security hardening"
    duration: 3 days
    deliverable: "WAF, security scanning, and compliance checks"
  
  - name: "Performance testing"
    duration: 4 days
    deliverable: "Load testing results and optimization"

resources:
  - "2 DevOps Engineers"
  - "1 Security Engineer"
  - "1 Performance Engineer"
```

##### Week 15-16: Go-Live
```yaml
tasks:
  - name: "Data migration from legacy"
    duration: 3 days
    deliverable: "Migrated historical data with validation"
  
  - name: "Production deployment"
    duration: 2 days
    deliverable: "All services running in production"
  
  - name: "Monitoring and alerting setup"
    duration: 2 days
    deliverable: "Complete observability stack"
  
  - name: "Documentation and training"
    duration: 3 days
    deliverable: "User manuals, API docs, and team training"
  
  - name: "Post-deployment support"
    duration: 4 days
    deliverable: "24/7 support during initial period"

resources:
  - "All team members"
  - "1 Technical Writer"
```

### Resource Requirements

#### Team Composition
```yaml
core_team:
  senior_backend_developers: 4
  junior_backend_developers: 2
  machine_learning_engineers: 2
  computer_vision_specialists: 1
  devops_engineers: 2
  security_specialists: 1
  data_analysts: 1
  performance_engineers: 1
  technical_writers: 1

total_team_size: 15
estimated_duration: 16_weeks
```

#### Technology Requirements
```yaml
development_tools:
  - "JetBrains PyCharm Professional licenses"
  - "Docker Desktop Pro licenses"
  - "GitHub Enterprise"
  - "Postman Team"

infrastructure:
  - "Cloud computing resources (AWS/Azure/GCP)"
  - "Database hosting (managed services)"
  - "Container registry"
  - "Monitoring and APM tools"

ai_ml_resources:
  - "GPU instances for model training/inference"
  - "Pre-trained YOLO models"
  - "OCR model licenses"
  - "Image processing libraries"
```

### Success Metrics & KPIs

#### Technical Metrics
```yaml
performance_targets:
  api_response_time:
    p95: "< 200ms"
    p99: "< 500ms"
  
  detection_processing:
    average: "< 2 seconds per image"
    throughput: "100+ detections per minute"
  
  system_availability:
    uptime: "> 99.9%"
    recovery_time: "< 5 minutes"

quality_metrics:
  code_coverage: "> 90%"
  security_vulnerabilities: "0 critical, 0 high"
  performance_regression: "< 5%"
  api_breaking_changes: "0"
```

#### Business Metrics
```yaml
operational_improvements:
  deployment_frequency: "Daily deployments"
  lead_time: "< 2 days from commit to production"
  mttr: "< 1 hour"
  change_failure_rate: "< 5%"

cost_optimization:
  infrastructure_costs: "-20% compared to legacy"
  maintenance_effort: "-50% developer hours"
  time_to_market: "+300% faster feature delivery"
```

## Monitoring and Observability

### Comprehensive Monitoring Stack

#### Application Metrics
```python
# src/shared/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from typing import Dict, Any, Optional
from functools import wraps
import time
import logging

# Define application metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint', 'service']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections',
    ['service']
)

DETECTION_PROCESSING_TIME = Histogram(
    'detection_processing_seconds',
    'Time spent processing detections',
    ['model_type', 'image_size']
)

CAMERA_HEALTH_STATUS = Gauge(
    'camera_health_status',
    'Camera health status (1=healthy, 0=unhealthy)',
    ['camera_id', 'location']
)

SERVICE_INFO = Info(
    'service_info',
    'Information about the service'
)

class MetricsCollector:
    """Central metrics collection service"""
    
    def __init__(self, service_name: str, port: int = 9090):
        self.service_name = service_name
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Set service info
        SERVICE_INFO.info({
            'service': service_name,
            'version': '2.0.0',
            'python_version': '3.11'
        })
    
    def start_metrics_server(self):
        """Start Prometheus metrics server"""
        try:
            start_http_server(self.port)
            self.logger.info(f"Metrics server started on port {self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start metrics server: {e}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            service=self.service_name
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint,
            service=self.service_name
        ).observe(duration)
    
    def record_detection_processing(self, model_type: str, image_size: str, processing_time: float):
        """Record detection processing metrics"""
        DETECTION_PROCESSING_TIME.labels(
            model_type=model_type,
            image_size=image_size
        ).observe(processing_time)
    
    def update_camera_health(self, camera_id: str, location: str, is_healthy: bool):
        """Update camera health metrics"""
        CAMERA_HEALTH_STATUS.labels(
            camera_id=camera_id,
            location=location
        ).set(1 if is_healthy else 0)
    
    def set_active_connections(self, count: int):
        """Update active connections count"""
        ACTIVE_CONNECTIONS.labels(service=self.service_name).set(count)

def metrics_middleware():
    """FastAPI middleware for automatic metrics collection"""
    def middleware(request, call_next):
        start_time = time.time()
        
        async def process_request():
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            metrics_collector.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
        
        return process_request()
    
    return middleware

# Initialize metrics collector
metrics_collector = MetricsCollector("camera_management")
```

#### Structured Logging
```python
# src/shared/core/logging_config.py
import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['service'] = getattr(record, 'service', 'unknown')
        
        # Add correlation ID if available
        log_record['correlation_id'] = getattr(record, 'correlation_id', None)
        
        # Add user context if available
        log_record['user_id'] = getattr(record, 'user_id', None)
        
        # Add request context if available
        log_record['request_id'] = getattr(record, 'request_id', None)
        log_record['endpoint'] = getattr(record, 'endpoint', None)

def setup_logging(service_name: str, log_level: str = "INFO") -> None:
    """Set up structured logging configuration"""
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
                "format": "%(timestamp)s %(level)s %(logger)s %(message)s"
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "structured",
                "filename": f"/var/log/{service_name}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(config)

class ContextLogger:
    """Logger with context support"""
    
    def __init__(self, name: str, service_name: str):
        self.logger = logging.getLogger(name)
        self.service_name = service_name
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """Set context fields for all subsequent log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context fields"""
        self.context.clear()
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with context"""
        extra = {
            'service': self.service_name,
            **self.context,
            **kwargs
        }
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, **kwargs)

def get_logger(name: str, service_name: str) -> ContextLogger:
    """Get context-aware logger"""
    return ContextLogger(name, service_name)
```

#### Health Monitoring
```python
# src/shared/core/health.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aioredis
import asyncpg
from sqlalchemy.ext.asyncio import AsyncEngine

@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: str  # 'healthy', 'unhealthy', 'degraded'
    message: Optional[str] = None
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class HealthMonitor:
    """System health monitoring"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: Dict[str, callable] = {}
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check"""
        self.checks[name] = check_func
    
    async def check_all(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks"""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                if isinstance(result, HealthCheck):
                    results[name] = result
                else:
                    results[name] = HealthCheck(
                        name=name,
                        status='healthy',
                        details=result
                    )
            except Exception as e:
                results[name] = HealthCheck(
                    name=name,
                    status='unhealthy',
                    message=str(e)
                )
        
        return results
    
    async def get_overall_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        checks = await self.check_all()
        
        # Determine overall status
        if all(check.status == 'healthy' for check in checks.values()):
            overall_status = 'healthy'
        elif any(check.status == 'unhealthy' for check in checks.values()):
            overall_status = 'unhealthy'
        else:
            overall_status = 'degraded'
        
        return {
            'service': self.service_name,
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {name: {
                'status': check.status,
                'message': check.message,
                'response_time': check.response_time,
                'details': check.details
            } for name, check in checks.items()}
        }

# Database health checks
async def check_postgres_health(engine: AsyncEngine) -> HealthCheck:
    """Check PostgreSQL database health"""
    start_time = datetime.utcnow()
    
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return HealthCheck(
            name="postgres",
            status="healthy",
            message="Database connection successful",
            response_time=response_time
        )
    except Exception as e:
        return HealthCheck(
            name="postgres",
            status="unhealthy",
            message=f"Database connection failed: {str(e)}"
        )

async def check_redis_health(redis_url: str) -> HealthCheck:
    """Check Redis health"""
    start_time = datetime.utcnow()
    
    try:
        redis = await aioredis.from_url(redis_url)
        await redis.ping()
        await redis.close()
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return HealthCheck(
            name="redis",
            status="healthy",
            message="Redis connection successful",
            response_time=response_time
        )
    except Exception as e:
        return HealthCheck(
            name="redis",
            status="unhealthy",
            message=f"Redis connection failed: {str(e)}"
        )

async def check_external_service_health(service_url: str, service_name: str) -> HealthCheck:
    """Check external service health"""
    import aiohttp
    
    start_time = datetime.utcnow()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{service_url}/health", timeout=5) as response:
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if response.status == 200:
                    return HealthCheck(
                        name=service_name,
                        status="healthy",
                        message="Service responding",
                        response_time=response_time
                    )
                else:
                    return HealthCheck(
                        name=service_name,
                        status="unhealthy",
                        message=f"Service returned status {response.status}"
                    )
    except Exception as e:
        return HealthCheck(
            name=service_name,
            status="unhealthy",
            message=f"Service check failed: {str(e)}"
        )
```

### Performance Optimization Strategies

#### Connection Pooling
```python
# src/shared/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
import asyncio
from typing import Optional

class DatabaseManager:
    """Database connection manager with pooling"""
    
    def __init__(self, database_url: str, service_name: str):
        self.database_url = database_url
        self.service_name = service_name
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
    
    async def initialize(self):
        """Initialize database engine and session factory"""
        self.engine = create_async_engine(
            self.database_url,
            # Connection pool settings
            poolclass=QueuePool,
            pool_size=20,  # Number of connections to maintain
            max_overflow=30,  # Additional connections beyond pool_size
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Validate connections before use
            
            # Performance settings
            echo=False,  # Set to True for SQL debugging
            future=True,
            
            # Connection settings
            connect_args={
                "command_timeout": 30,
                "server_settings": {
                    "application_name": f"lpr_{self.service_name}",
                    "jit": "off"  # Disable JIT for faster connection
                }
            }
        )
        
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            await self.initialize()
        
        return self.session_factory()
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
    
    async def health_check(self):
        """Check database health"""
        async with self.get_session() as session:
            await session.execute("SELECT 1")
```

#### Caching Strategy
```python
# src/shared/core/cache.py
import aioredis
import json
import pickle
from typing import Any, Optional, Union, Dict
from datetime import timedelta
import asyncio
import hashlib

class CacheManager:
    """Redis-based cache manager with multiple serialization strategies"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis: Optional[aioredis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False,  # Handle binary data
            max_connections=20,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={}
        )
    
    def _make_key(self, key: str, namespace: str = "lpr") -> str:
        """Create namespaced cache key"""
        return f"{namespace}:{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode()
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize stored value"""
        try:
            return json.loads(data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return pickle.loads(data)
    
    async def get(self, key: str, namespace: str = "lpr") -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            await self.initialize()
        
        cache_key = self._make_key(key, namespace)
        
        try:
            data = await self.redis.get(cache_key)
            if data:
                return self._deserialize(data)
        except Exception as e:
            # Log error but don't raise - cache miss is acceptable
            logging.warning(f"Cache get error for key {cache_key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = "lpr") -> bool:
        """Set value in cache"""
        if not self.redis:
            await self.initialize()
        
        cache_key = self._make_key(key, namespace)
        ttl = ttl or self.default_ttl
        
        try:
            serialized = self._serialize(value)
            await self.redis.setex(cache_key, ttl, serialized)
            return True
        except Exception as e:
            logging.warning(f"Cache set error for key {cache_key}: {e}")
            return False
    
    async def delete(self, key: str, namespace: str = "lpr") -> bool:
        """Delete key from cache"""
        if not self.redis:
            await self.initialize()
        
        cache_key = self._make_key(key, namespace)
        
        try:
            result = await self.redis.delete(cache_key)
            return result > 0
        except Exception as e:
            logging.warning(f"Cache delete error for key {cache_key}: {e}")
            return False
    
    async def exists(self, key: str, namespace: str = "lpr") -> bool:
        """Check if key exists in cache"""
        if not self.redis:
            await self.initialize()
        
        cache_key = self._make_key(key, namespace)
        
        try:
            result = await self.redis.exists(cache_key)
            return result > 0
        except Exception as e:
            logging.warning(f"Cache exists error for key {cache_key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str, namespace: str = "lpr") -> int:
        """Invalidate keys matching pattern"""
        if not self.redis:
            await self.initialize()
        
        search_pattern = self._make_key(pattern, namespace)
        
        try:
            keys = await self.redis.keys(search_pattern)
            if keys:
                return await self.redis.delete(*keys)
        except Exception as e:
            logging.warning(f"Cache invalidate error for pattern {search_pattern}: {e}")
        
        return 0

# Cache decorators
def cached(ttl: int = 3600, namespace: str = "lpr", key_func: Optional[callable] = None):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cache = CacheManager("redis://localhost:6379")
            cached_result = await cache.get(cache_key, namespace)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl, namespace)
            
            return result
        
        return wrapper
    return decorator

# Usage example
@cached(ttl=300, namespace="cameras")
async def get_camera_health(camera_id: str):
    """Get camera health with 5-minute cache"""
    # Expensive operation here
    return await fetch_camera_health(camera_id)
```

This completes the comprehensive Backend Modernization & Architecture Plan - Part 2, covering security implementation, development workflows, containerization, CI/CD pipelines, detailed implementation roadmap, monitoring and observability, and performance optimization strategies. The plan provides a complete blueprint for building a modern, scalable, and maintainable backend system for the LPR application.#### FastAPI Dependencies
```python
# src/shared/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from shared.utils.security import jwt_manager, User, TokenData
from shared.utils.rbac import RBACService, Permission
from user_management.application.services.user_service import UserService

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends()
) -> User:
    """Get current authenticated user"""
    try:
        # Verify token
        token_data = jwt_manager.verify_token(credentials.credentials)
        
        # Get user from database
        user = await user_service.get_user_by_id(token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def require_permission(permission: Permission):
    """Create dependency that requires specific permission"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not RBACService.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
        return current_user
    
    return permission_checker

def require_any_permission(*permissions: Permission):
    """Create dependency that requires any of the specified permissions"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not RBACService.has_any_permission(current_user, list(permissions)):
            required_perms = [p.value for p in permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of the following permissions required: {required_perms}"
            )
        return current_user
    
    return permission_checker

# Service-specific dependencies
async def get_camera_app_service() -> 'CameraAppService':
    """Get camera application service"""
    from camera_management.application.services.camera_app_service import CameraAppService
    # In real implementation, this would use dependency injection container
    return CameraAppService()

async def get_detection_app_service() -> 'DetectionAppService':
    """Get detection application service"""
    from detection.application.services.detection_app_service import DetectionAppService
    return DetectionAppService()
```

### Data Encryption & Security

#### Encryption Service
```python
# src/shared/utils/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import os
import secrets
from typing import Dict, Any, Optional

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption service with master key"""
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = os.environ.get("MASTER_KEY", "default-key-change-in-production").encode()
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())
    
    def encrypt_data(self, data: str, context: str = "default") -> Dict[str, str]:
        """Encrypt data with context-specific key"""
        # Generate random salt
        salt = secrets.token_bytes(16)
        
        # Derive key from master key and context
        key = self._derive_key(f"{self.master_key.decode()}-{context}", salt)
        
        # Create Fernet cipher
        fernet = Fernet(base64.urlsafe_b64encode(key))
        
        # Encrypt data
        encrypted_data = fernet.encrypt(data.encode())
        
        return {
            "encrypted_data": base64.urlsafe_b64encode(encrypted_data).decode(),
            "salt": base64.urlsafe_b64encode(salt).decode(),
            "context": context
        }
    
    def decrypt_data(self, encrypted_info: Dict[str, str]) -> str:
        """Decrypt data using stored salt and context"""
        encrypted_data = base64.urlsafe_b64decode(encrypted_info["encrypted_data"])
        salt = base64.urlsafe_b64decode(encrypted_info["salt"])
        context = encrypted_info["context"]
        
        # Derive key
        key = self._derive_key(f"{self.master_key.decode()}-{context}", salt)
        
        # Create Fernet cipher
        fernet = Fernet(base64.urlsafe_b64encode(key))
        
        # Decrypt data
        decrypted_data = fernet.decrypt(encrypted_data)
        
        return decrypted_data.decode()
    
    def encrypt_camera_credentials(self, username: str, password: str, camera_id: str) -> Dict[str, Any]:
        """Encrypt camera credentials with camera-specific context"""
        credentials = {
            "username": username,
            "password": password
        }
        
        return self.encrypt_data(
            data=f"{username}:{password}",
            context=f"camera-{camera_id}"
        )
    
    def decrypt_camera_credentials(self, encrypted_credentials: Dict[str, str]) -> Dict[str, str]:
        """Decrypt camera credentials"""
        decrypted = self.decrypt_data(encrypted_credentials)
        username, password = decrypted.split(":", 1)
        
        return {
            "username": username,
            "password": password
        }

# Initialize encryption service
encryption_service = EncryptionService()
```

## Development Workflow

### Containerization Strategy

#### Multi-stage Dockerfile Template
```dockerfile
# src/camera_management/Dockerfile
# Multi-stage build for Python microservice
ARG PYTHON_VERSION=3.11-slim

# Build stage
FROM python:${PYTHON_VERSION} as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run tests in build stage
RUN python -m pytest tests/ --cov=src --cov-report=term-missing

# Production stage
FROM python:${PYTHON_VERSION}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "src.camera_management.main:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose for Development
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  # Database services
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: lpr_user
      POSTGRES_PASSWORD: lpr_password
      POSTGRES_DB: lpr_db
      POSTGRES_MULTIPLE_DATABASES: "camera_db,detection_db,user_db"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-databases.sh:/docker-entrypoint-initdb.d/init-databases.sh
    ports:
      - "5432:5432"
    networks:
      - lpr_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lpr_user -d lpr_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:6-focal
    environment:
      MONGO_INITDB_ROOT_USERNAME: lpr_user
      MONGO_INITDB_ROOT_PASSWORD: lpr_password
    volumes:
      - mongodb_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js
    ports:
      - "27017:27017"
    networks:
      - lpr_network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - lpr_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Message queue
  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: lpr_user
      RABBITMQ_DEFAULT_PASS: lpr_password
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"  # Management UI
    networks:
      - lpr_network
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Core services
  camera_management:
    build:
      context: ./src/camera_management
      dockerfile: Dockerfile
      target: development
    environment:
      - DATABASE_URL=postgresql://lpr_user:lpr_password@postgres:5432/camera_db
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://lpr_user:lpr_password@rabbitmq:5672/
      - JWT_SECRET_KEY=dev-secret-key-change-in-production
      - LOG_LEVEL=DEBUG
    volumes:
      - ./src/camera_management:/app/src/camera_management
      - ./src/shared:/app/src/shared
    ports:
      - "8001:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    networks:
      - lpr_network
    restart: unless-stopped

  video_processing:
    build:
      context: ./src/video_processing
      dockerfile: Dockerfile
      target: development
    environment:
      - DATABASE_URL=postgresql://lpr_user:lpr_password@postgres:5432/video_db
      - REDIS_URL=redis://redis:6379/1
      - RABBITMQ_URL=amqp://lpr_user:lpr_password@rabbitmq:5672/
      - OPENCV_THREADS=4
    volumes:
      - ./src/video_processing:/app/src/video_processing
      - ./src/shared:/app/src/shared
      - video_data:/app/data/videos
    ports:
      - "8002:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    networks:
      - lpr_network
    restart: unless-stopped

  detection:
    build:
      context: ./src/detection
      dockerfile: Dockerfile
      target: development
    environment:
      - MONGODB_URL=mongodb://lpr_user:lpr_password@mongodb:27017/detection_db
      - REDIS_URL=redis://redis:6379/2
      - RABBITMQ_URL=amqp://lpr_user:lpr_password@rabbitmq:5672/
      - MODEL_PATH=/app/models
      - CUDA_VISIBLE_DEVICES=0  # If GPU available
    volumes:
      - ./src/detection:/app/src/detection
      - ./src/shared:/app/src/shared
      - ./models:/app/models
      - detection_data:/app/data/detections
    ports:
      - "8003:8000"
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    networks:
      - lpr_network
    restart: unless-stopped

  analytics:
    build:
      context: ./src/analytics
      dockerfile: Dockerfile
      target: development
    environment:
      - MONGODB_URL=mongodb://lpr_user:lpr_password@mongodb:27017/analytics_db
      - REDIS_URL=redis://redis:6379/3
      - RABBITMQ_URL=amqp://lpr_user:lpr_password@rabbitmq:5672/
    volumes:
      - ./src/analytics:/app/src/analytics
      - ./src/shared:/app/src/shared
    ports:
      - "8004:8000"
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    networks:
      - lpr_network
    restart: unless-stopped

  user_management:
    build:
      context: ./src/user_management
      dockerfile: Dockerfile
      target: development
    environment:
      - DATABASE_URL=postgresql://lpr_user:lpr_password@postgres:5432/user_db
      - REDIS_URL=redis://redis:6379/4
      - JWT_SECRET_KEY=dev-secret-key-change-in-production
      - BCRYPT_ROUNDS=12
    volumes:
      - ./src/user_management:/app/src/user_management
      - ./src/shared:/app/src/shared
    ports:
      - "8005:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - lpr_network
    restart: unless-stopped

  # API Gateway
  api_gateway:
    build:
      context: ./src/api_gateway
      dockerfile: Dockerfile
      target: development
    environment:
      - CAMERA_SERVICE_URL=http://camera_management:8000
      - VIDEO_SERVICE_URL=http://video_processing:8000
      - DETECTION_SERVICE_URL=http://detection:8000
      - ANALYTICS_SERVICE_URL=http://analytics:8000
      - USER_SERVICE_URL=http://user_management:8000
      - JWT_SECRET_KEY=dev-secret-key-change-in-production
    volumes:
      - ./src/api_gateway:/app/src/api_gateway
      - ./src/shared:/app/src/shared
    ports:
      - "8000:8000"
    depends_on:
      - camera_management
      - video_processing
      - detection
      - analytics
      - user_management
    networks:
      - lpr_network
    restart: unless-stopped

  # Monitoring and observability
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - lpr_network

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - lpr_network

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  rabbitmq_data:
  video_data:
  detection_data:
  prometheus_data:
  grafana_data:

networks:
  lpr_network:
    driver: bridge
```

### CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/backend-ci-cd.yml
name: Backend CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths: ['src/**', 'requirements/**', 'tests/**', 'docker-compose*.yml']
  pull_request:
    branches: [main, develop]
    paths: ['src/**', 'requirements/**', 'tests/**']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Code Quality and Testing
  quality-checks:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [camera_management, video_processing, detection, analytics, user_management]
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/base.txt
        pip install -r requirements/dev.txt
    
    - name: Code formatting check
      run: |
        black --check src/${{ matrix.service }}
        isort --check-only src/${{ matrix.service }}
    
    - name: Linting
      run: |
        flake8 src/${{ matrix.service }}
        pylint src/${{ matrix.service }}
    
    - name: Type checking
      run: |
        mypy src/${{ matrix.service }}
    
    - name: Security scan
      run: |
        bandit -r src/${{ matrix.service }}
        safety check
    
    - name: Run unit tests
      run: |
        pytest tests/unit/${{ matrix.service }} \
          --cov=src/${{ matrix.service }} \
          --cov-report=xml \
          --cov-report=html \
          --junit-xml=test-results-${{ matrix.service }}.xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: ${{ matrix.service }}

  # Integration Testing
  integration-tests:
    runs-on: ubuntu-latest
    needs: quality-checks
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      mongodb:
        image: mongo:6
        env:
          MONGO_INITDB_ROOT_USERNAME: test_user
          MONGO_INITDB_ROOT_PASSWORD: test_password
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/base.txt
        pip install -r requirements/test.txt
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
        MONGODB_URL: mongodb://test_user:test_password@localhost:27017/test_db
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/integration/ \
          --cov=src \
          --cov-report=xml \
          --junit-xml=integration-test-results.xml

  # Container Build and Push
  build-and-push:
    runs-on: ubuntu-latest
    needs: [quality-checks, integration-tests]
    if: github.ref == 'refs/heads/main'
    
    strategy:
      matrix:
        service: [camera_management, video_processing, detection, analytics, user_management, api_gateway]
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./src/${{ matrix.service }}
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        platforms: linux/amd64,linux/arm64

  # End-to-End Testing
  e2e-tests:
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Start services with Docker Compose
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 60  # Wait for services to be ready
    
    - name: Install test dependencies
      run: |
        pip install -r requirements/test.txt
    
    - name: Run E2E tests
      run: |
        pytest tests/e2e/ \
          --base-url=http://localhost:8000 \
          --junit-xml=e2e-test-results.xml
    
    - name: Collect service logs
      if: failure()
      run: |
        docker-compose -f docker-compose.test.yml logs > service-logs.txt
    
    - name: Upload logs
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: service-logs
        path: service-logs.txt
    
    - name: Cleanup
      if: always()
      run: |
        docker-compose -f docker-compose.test.yml down -v

  # Deployment to Staging
  deploy-staging:
    runs-on: ubuntu-latest
    needs: e2e-tests
    if: github.ref == 'refs/heads/main'
    environment: staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment..."
        # Add deployment scripts here
    
    - name: Run smoke tests
      run: |
        echo "Running smoke tests..."
        # Add smoke test scripts here

  # Production Deployment (Manual Approval)
  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Deploy to production
      run: |
        echo "Deploying to production environment..."
        # Add production deployment scripts here
    
    - name: Post-deployment verification
      run: |
        echo "Running post-deployment verification..."
        # Add verification scripts here
```

## Implementation Roadmap

### Detailed Implementation Timeline

#### Phase 1: Foundation & Core Services (Weeks 1-4)

##### Week 1-2: Infrastructure Setup
```yaml
tasks:
  - name: "Set up project structure"
    duration: 2 days
    deliverable: "Complete directory structure with all service folders"
  
  - name: "Configure development environment"
    duration: 2 days
    deliverable: "Docker Compose setup with all databases and message queues"
  
  - name: "Implement shared utilities"
    duration: 3 days
    deliverable: "Authentication, encryption, logging, and base classes"
  
  - name: "Set up CI/CD pipeline"
    duration: 3 days
    deliverable: "GitHub Actions workflow with testing and deployment"

resources:
  - "2 Senior Backend Developers"
  - "1 DevOps Engineer"
```

##### Week 3-4: Camera Management Service
```yaml
tasks:
  - name: "Implement domain layer"
    duration: 3 days
    deliverable: "Camera entity, value objects, and domain services"
  
  - name: "Implement application layer"
    duration: 3 days
    deliverable: "Use cases and command/query handlers"
  
  - name: "Implement infrastructure layer"
    duration: 3 days
    deliverable: "Repository implementations and external service adapters"
  
  - name: "Implement API layer"
    duration: 2 days
    deliverable: "REST endpoints with OpenAPI documentation"
  
  - name: "Write comprehensive tests"
    duration: 3 days
    deliverable: "Unit, integration, and API tests with 90%+ coverage"

resources:
  - "2 Senior Backend Developers"
  - "1 Junior Backend Developer"
```

#### Phase 2: Processing Services (Weeks 5-8)

##### Week 5-6: Video Processing Service
```yaml
tasks:
  - name: "Implement video stream handling"
    duration: 4 days
    deliverable: "RTSP stream ingestion and frame extraction"
  
  - name: "Implement frame processing pipeline"
    duration: 4 days
    deliverable: "Frame buffering, quality assessment, and processing queue"
  
  - name: "Implement recording management"
    duration: 3 days
    deliverable: "Video recording with pre/post event buffers"
  
  - name: "Integration with camera service"
    duration: 3 days
    deliverable: "Event-driven communication and health monitoring"

resources:
  - "2 Senior Backend Developers with video processing experience"
  - "1 Computer Vision Specialist"
```

##### Week 7-8: Detection Service
```yaml
tasks:
  - name: "Integrate YOLO models"
    duration: 4 days
    deliverable: "License plate detection with configurable models"
  
  - name: "Implement OCR processing"
    duration: 4 days
    deliverable: "Text recognition with confidence scoring"
  
  - name: "Implement validation and enhancement"
    duration: 3 days
    deliverable: "Plate format validation and image enhancement"
  
  - name: "Performance optimization"
    duration: 3 days
    deliverable: "GPU acceleration and batch processing"

resources:
  - "2 Senior Backend Developers"
  - "1 Machine Learning Engineer"
  - "1 Computer Vision Specialist"
```

#### Phase 3: Supporting Services (Weeks 9-12)

##### Week 9-10: Analytics Service
```yaml
tasks:
  - name: "Implement metrics collection"
    duration: 3 days
    deliverable: "Real-time metrics processing and storage"
  
  - name: "Implement pattern analysis"
    duration: 4 days
    deliverable: "Traffic pattern detection and trend analysis"
  
  - name: "Implement reporting system"
    duration: 4 days
    deliverable: "Report generation with multiple formats"
  
  - name: "Dashboard data APIs"
    duration: 3 days
    deliverable: "Real-time dashboard data endpoints"

resources:
  - "2 Senior Backend Developers"
  - "1 Data Analyst"
```

##### Week 11-12: User Management & Notification Services
```yaml
tasks:
  - name: "Implement user management"
    duration: 4 days
    deliverable: "User CRUD, authentication, and RBAC"
  
  - name: "Implement notification system"
    duration: 4 days
    deliverable: "Multi-channel notifications with templates"
  
  - name: "API Gateway implementation"
    duration: # Backend Modernization & Architecture Plan - Part 2

**Version:** 3.0  
**Date:** 2025-01-09  
**Authors:** Backend Architecture Team  
**Status:** Active Development  

## Continued from Part 1...

### MongoDB Schema (Document Data) - Continued
```javascript
// Create indexes (continued)
db.detections.createIndex({ "vehicle_info.type": 1 });
db.detections.createIndex({ "metadata.location": 1 });
db.detections.createIndex({ created_at: -1 });

// Analytics data collection
db.createCollection("analytics_metrics", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["metric_name", "value", "timestamp"],
            properties: {
                metric_name: { bsonType: "string" },
                value: { bsonType: ["double", "int"] },
                timestamp: { bsonType: "date" },
                dimensions: { bsonType: "object" },
                tags: { bsonType: "array" }
            }
        }
    }
});

// Time-series indexes for analytics
db.analytics_metrics.createIndex({ metric_name: 1, timestamp: -1 });
db.analytics_metrics.createIndex({ timestamp: -1 });
db.analytics_metrics.createIndex({ "dimensions.camera_id": 1 });

// System logs collection
db.createCollection("system_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["level", "message", "timestamp", "service"],
            properties: {
                level: { 
                    bsonType: "string",
                    enum: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                },
                message: { bsonType: "string" },
                timestamp: { bsonType: "date" },
                service: { bsonType: "string" },
                context: { bsonType: "object" }
            }
        }
    }
});

db.system_logs.createIndex({ timestamp: -1 });
db.system_logs.createIndex({ level: 1, timestamp: -1 });
db.system_logs.createIndex({ service: 1, timestamp: -1 });
```

## API Design

### RESTful API Standards

#### API Versioning Strategy
```python
# src/shared/core/versioning.py
from enum import Enum
from fastapi import Request
from typing import Optional

class APIVersion(Enum):
    V1 = "v1"
    V2 = "v2"

class APIVersioning:
    """Handle API versioning across services"""
    
    @staticmethod
    def get_version_from_path(request: Request) -> APIVersion:
        """Extract API version from URL path"""
        path_parts = request.url.path.split('/')
        for part in path_parts:
            if part.startswith('v'):
                try:
                    return APIVersion(part)
                except ValueError:
                    pass
        return APIVersion.V2  # Default to latest
    
    @staticmethod
    def get_version_from_header(request: Request) -> Optional[APIVersion]:
        """Extract API version from header"""
        version_header = request.headers.get('API-Version')
        if version_header:
            try:
                return APIVersion(version_header)
            except ValueError:
                pass
        return None

# Example usage in routers
from fastapi import APIRouter, Depends, Request

router = APIRouter()

@router.get("/cameras")
async def list_cameras_versioned(
    request: Request,
    version: APIVersion = Depends(APIVersioning.get_version_from_path)
):
    if version == APIVersion.V1:
        return await list_cameras_v1()
    else:  # V2
        return await list_cameras_v2()
```

#### Comprehensive Request/Response Schemas
```python
# src/camera_management/presentation/api/schemas/requests.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
import re

class CreateCameraRequest(BaseModel):
    """Request schema for creating a camera"""
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Camera name for identification"
    )
    ip_address: str = Field(
        ...,
        description="Camera IP address",
        regex=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    )
    location: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Physical location of the camera"
    )
    stream_url: str = Field(
        ...,
        description="RTSP or HTTP stream URL"
    )
    resolution_width: int = Field(
        ...,
        ge=320,
        le=3840,
        description="Video resolution width"
    )
    resolution_height: int = Field(
        ...,
        ge=240,
        le=2160,
        description="Video resolution height"
    )
    frame_rate: int = Field(
        30,
        ge=1,
        le=120,
        description="Frames per second"
    )
    username: Optional[str] = Field(
        None,
        max_length=50,
        description="Authentication username"
    )
    password: Optional[str] = Field(
        None,
        max_length=100,
        description="Authentication password"
    )
    stream_path: Optional[str] = Field(
        None,
        max_length=200,
        description="Stream path for RTSP"
    )
    quality_settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional quality settings"
    )
    
    @validator('stream_url')
    def validate_stream_url(cls, v):
        """Validate stream URL format"""
        if not (v.startswith('rtsp://') or v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Stream URL must start with rtsp://, http://, or https://')
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format and range"""
        octets = v.split('.')
        for octet in octets:
            if not (0 <= int(octet) <= 255):
                raise ValueError('Invalid IP address')
        return v
    
    @root_validator
    def validate_authentication(cls, values):
        """Validate authentication credentials"""
        username = values.get('username')
        password = values.get('password')
        
        if username and not password:
            raise ValueError('Password is required when username is provided')
        if password and not username:
            raise ValueError('Username is required when password is provided')
        
        return values
    
    def to_command(self):
        """Convert to application command"""
        from camera_management.application.use_cases.create_camera import CreateCameraCommand
        return CreateCameraCommand(
            name=self.name,
            ip_address=self.ip_address,
            location=self.location,
            stream_url=self.stream_url,
            resolution_width=self.resolution_width,
            resolution_height=self.resolution_height,
            frame_rate=self.frame_rate,
            username=self.username,
            password=self.password,
            stream_path=self.stream_path,
            quality_settings=self.quality_settings or {}
        )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Entrance Gate Camera",
                "ip_address": "192.168.1.100",
                "location": "Main Entrance",
                "stream_url": "rtsp://192.168.1.100:554/stream1",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "frame_rate": 30,
                "username": "admin",
                "password": "password123",
                "stream_path": "/stream1",
                "quality_settings": {
                    "bitrate": 2000000,
                    "compression": "h264"
                }
            }
        }

class UpdateCameraRequest(BaseModel):
    """Request schema for updating a camera"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    stream_url: Optional[str] = None
    resolution_width: Optional[int] = Field(None, ge=320, le=3840)
    resolution_height: Optional[int] = Field(None, ge=240, le=2160)
    frame_rate: Optional[int] = Field(None, ge=1, le=120)
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=100)
    stream_path: Optional[str] = Field(None, max_length=200)
    quality_settings: Optional[Dict[str, Any]] = None
    
    def to_command(self):
        """Convert to application command"""
        from camera_management.application.use_cases.update_camera import UpdateCameraCommand
        return UpdateCameraCommand(**self.dict(exclude_none=True))

# Detection request schemas
class DetectionRequest(BaseModel):
    """Request schema for license plate detection"""
    image_data: str = Field(
        ...,
        description="Base64 encoded image data or image URL"
    )
    camera_id: Optional[str] = Field(
        None,
        description="Source camera ID"
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="Detection timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )
    
    @validator('image_data')
    def validate_image_data(cls, v):
        """Validate image data format"""
        if v.startswith('data:image/'):
            # Base64 encoded image
            if ';base64,' not in v:
                raise ValueError('Invalid base64 image format')
        elif v.startswith(('http://', 'https://')):
            # Image URL
            if not v.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                raise ValueError('Invalid image URL format')
        else:
            raise ValueError('Image data must be base64 encoded or valid URL')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
                "camera_id": "cam_001",
                "timestamp": "2025-01-09T14:32:15Z",
                "metadata": {
                    "weather": "clear",
                    "lighting": "daylight"
                }
            }
        }
```

#### Response Schemas
```python
# src/camera_management/presentation/api/schemas/responses.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from camera_management.domain.entities.camera import Camera

class CameraResponse(BaseModel):
    """Response schema for camera data"""
    id: str = Field(..., description="Camera unique identifier")
    name: str = Field(..., description="Camera name")
    ip_address: str = Field(..., description="Camera IP address")
    location: str = Field(..., description="Camera location")
    status: str = Field(..., description="Camera status")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Camera configuration")
    health_metrics: Optional[Dict[str, Any]] = Field(None, description="Health metrics")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    @classmethod
    def from_entity(cls, camera: Camera) -> 'CameraResponse':
        """Create response from domain entity"""
        return cls(
            id=camera.id,
            name=camera.name,
            ip_address=str(camera.ip_address),
            location=camera.location,
            status=camera.status,
            configuration=camera.configuration.to_dict() if camera.configuration else None,
            health_metrics=camera.health_metrics,
            created_at=camera.created_at,
            updated_at=camera.updated_at
        )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Entrance Gate Camera",
                "ip_address": "192.168.1.100",
                "location": "Main Entrance",
                "status": "active",
                "configuration": {
                    "stream_url": "rtsp://192.168.1.100:554/stream1",
                    "resolution": {"width": 1920, "height": 1080},
                    "frame_rate": 30
                },
                "health_metrics": {
                    "overall_status": "healthy",
                    "response_time": 150,
                    "connection_status": "connected",
                    "last_check": "2025-01-09T14:32:15Z"
                },
                "created_at": "2025-01-09T10:00:00Z",
                "updated_at": "2025-01-09T14:32:15Z"
            }
        }

class CameraListResponse(BaseModel):
    """Response schema for camera list"""
    data: List[CameraResponse] = Field(..., description="List of cameras")
    total: int = Field(..., description="Total number of cameras")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_next: bool = Field(..., description="Whether there are more items")
    has_previous: bool = Field(..., description="Whether there are previous items")
    
    class Config:
        schema_extra = {
            "example": {
                "data": [
                    # Camera objects here
                ],
                "total": 150,
                "limit": 20,
                "offset": 0,
                "has_next": True,
                "has_previous": False
            }
        }

class HealthResponse(BaseModel):
    """Response schema for camera health status"""
    overall_status: str = Field(..., description="Overall health status")
    response_time: Optional[int] = Field(None, description="Response time in milliseconds")
    connection_status: str = Field(..., description="Connection status")
    error_rate: Optional[float] = Field(None, description="Error rate percentage")
    last_check: datetime = Field(..., description="Last health check timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")
    
    @classmethod
    def from_dict(cls, health_data: Dict[str, Any]) -> 'HealthResponse':
        """Create response from health data dictionary"""
        return cls(
            overall_status=health_data.get("overall_status", "unknown"),
            response_time=health_data.get("response_time"),
            connection_status=health_data.get("connection_status", "unknown"),
            error_rate=health_data.get("error_rate"),
            last_check=health_data.get("last_check", datetime.utcnow()),
            details=health_data.get("details")
        )

# Detection response schemas
class LicensePlateResponse(BaseModel):
    """Response schema for detected license plate"""
    text: str = Field(..., description="License plate text")
    confidence: float = Field(..., description="Detection confidence (0-1)")
    bounding_box: Dict[str, int] = Field(..., description="Plate bounding box")
    format_type: Optional[str] = Field(None, description="Plate format type")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "ABC-123",
                "confidence": 0.95,
                "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 80},
                "format_type": "US_STANDARD"
            }
        }

class VehicleResponse(BaseModel):
    """Response schema for detected vehicle"""
    type: Optional[str] = Field(None, description="Vehicle type")
    color: Optional[str] = Field(None, description="Vehicle color")
    make: Optional[str] = Field(None, description="Vehicle make")
    model: Optional[str] = Field(None, description="Vehicle model")
    confidence: Optional[float] = Field(None, description="Classification confidence")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "sedan",
                "color": "blue",
                "make": "Honda",
                "model": "Civic",
                "confidence": 0.85
            }
        }

class DetectionResponse(BaseModel):
    """Response schema for detection results"""
    id: str = Field(..., description="Detection unique identifier")
    camera_id: Optional[str] = Field(None, description="Source camera ID")
    timestamp: datetime = Field(..., description="Detection timestamp")
    license_plates: List[LicensePlateResponse] = Field(..., description="Detected license plates")
    vehicle: Optional[VehicleResponse] = Field(None, description="Vehicle information")
    confidence: float = Field(..., description="Overall detection confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    status: str = Field(..., description="Detection status")
    image_urls: Optional[Dict[str, str]] = Field(None, description="Image URLs")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "det_550e8400-e29b-41d4-a716-446655440000",
                "camera_id": "cam_001",
                "timestamp": "2025-01-09T14:32:15Z",
                "license_plates": [
                    {
                        "text": "ABC-123",
                        "confidence": 0.95,
                        "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 80},
                        "format_type": "US_STANDARD"
                    }
                ],
                "vehicle": {
                    "type": "sedan",
                    "color": "blue",
                    "confidence": 0.85
                },
                "confidence": 0.92,
                "processing_time": 0.234,
                "status": "completed",
                "image_urls": {
                    "original": "/images/detections/det_123_original.jpg",
                    "processed": "/images/detections/det_123_processed.jpg",
                    "thumbnail": "/images/detections/det_123_thumb.jpg"
                }
            }
        }

# Error response schemas
class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error: bool = Field(True, description="Error flag")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "error": True,
                "code": "CAMERA_NOT_FOUND",
                "message": "Camera with ID 'cam_001' not found",
                "details": {
                    "camera_id": "cam_001",
                    "requested_at": "2025-01-09T14:32:15Z"
                },
                "timestamp": "2025-01-09T14:32:15Z",
                "request_id": "req_550e8400-e29b-41d4-a716-446655440000"
            }
        }
```

## Security Implementation

### Authentication & Authorization

#### JWT Token Management
```python
# src/shared/utils/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import HTTPException, status
import secrets
import hashlib

class TokenData(BaseModel):
    """JWT token data"""
    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    exp: datetime
    iat: datetime

class User(BaseModel):
    """User model for authentication"""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []
    is_active: bool = True

class JWTManager:
    """JWT token management"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(self, user: User, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "permissions": user.permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access_token"
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=30)
        
        to_encode = {
            "sub": user.id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh_token"
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            token_type = payload.get("type", "access_token")
            if token_type != "access_token":
                raise JWTError("Invalid token type")
            
            # Extract user data
            user_id = payload.get("sub")
            if user_id is None:
                raise JWTError("Invalid token: missing subject")
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
                raise JWTError("Token expired")
            
            return TokenData(
                user_id=user_id,
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(exp),
                iat=datetime.fromtimestamp(payload.get("iat", 0))
            )
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_api_key(self, length: int = 32) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(length)

# Initialize JWT manager
import os
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
jwt_manager = JWTManager(SECRET_KEY)
```

#### Role-Based Access Control (RBAC)
```python
# src/shared/utils/rbac.py
from enum import Enum
from typing import List, Set
from functools import wraps
from fastapi import HTTPException, status, Depends
from shared.utils.security import User, TokenData

class Permission(Enum):
    """System permissions"""
    # Camera permissions
    CAMERA_READ = "camera:read"
    CAMERA_WRITE = "camera:write"
    CAMERA_DELETE = "camera:delete"
    CAMERA_CONTROL = "camera:control"
    
    # Detection permissions
    DETECTION_READ = "detection:read"
    DETECTION_WRITE = "detection:write"
    DETECTION_DELETE = "detection:delete"
    
    # Analytics permissions
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_WRITE = "analytics:write"
    
    # User management permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # System administration
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"

class Role(Enum):
    """System roles"""
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMINISTRATOR = "administrator"
    SUPER_ADMIN = "super_admin"

# Role-permission mapping
ROLE_PERMISSIONS = {
    Role.VIEWER: {
        Permission.CAMERA_READ,
        Permission.DETECTION_READ,
        Permission.ANALYTICS_READ,
    },
    Role.OPERATOR: {
        Permission.CAMERA_READ,
        Permission.CAMERA_WRITE,
        Permission.CAMERA_CONTROL,
        Permission.DETECTION_READ,
        Permission.DETECTION_WRITE,
        Permission.ANALYTICS_READ,
        Permission.SYSTEM_READ,
    },
    Role.ADMINISTRATOR: {
        Permission.CAMERA_READ,
        Permission.CAMERA_WRITE,
        Permission.CAMERA_DELETE,
        Permission.CAMERA_CONTROL,
        Permission.DETECTION_READ,
        Permission.DETECTION_WRITE,
        Permission.DETECTION_DELETE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_WRITE,
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.SYSTEM_READ,
        Permission.SYSTEM_WRITE,
    },
    Role.SUPER_ADMIN: set(Permission)  # All permissions
}

class RBACService:
    """Role-Based Access Control service"""
    
    @staticmethod
    def get_role_permissions(role: Role) -> Set[Permission]:
        """Get permissions for a role"""
        return ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def get_user_permissions(user: User) -> Set[Permission]:
        """Get all permissions for a user based on their roles"""
        permissions = set()
        for role_name in user.roles:
            try:
                role = Role(role_name)
                permissions.update(RBACService.get_role_permissions(role))
            except ValueError:
                # Invalid role, skip
                continue
        
        # Add explicit permissions
        for perm_name in user.permissions:
            try:
                permission = Permission(perm_name)
                permissions.add(permission)
            except ValueError:
                # Invalid permission, skip
                continue
        
        return permissions
    
    @staticmethod
    def has_permission(user: User, required_permission: Permission) -> bool:
        """Check if user has required permission"""
        user_permissions = RBACService.get_user_permissions(user)
        return required_permission in user_permissions
    
    @staticmethod
    def has_any_permission(user: User, required_permissions: List[Permission]) -> bool:
        """Check if user has any of the required permissions"""
        user_permissions = RBACService.get_user_permissions(user)
        return any(perm in user_permissions for perm in required_permissions)
    
    @staticmethod
    def has_all_permissions(user: User, required_permissions: List[Permission]) -> bool:
        """Check if user has all required permissions"""
        user_permissions = RBACService.get_user_permissions(user)
        return all(perm in user_permissions for perm in required_permissions)

# Permission decorators
def require_permissions(*permissions: Permission):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (injected by dependency)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permissions
            if not RBACService.has_all_permissions(current_user, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(*permissions: Permission):
    """Decorator to require any of the specified permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not RBACService.has_any_permission(current_user, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(*roles: Role):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_roles = {Role(role_name) for role_name in current_user.roles if role_name in [r.value for r in Role]}
            required_roles = set(roles)
            
            if not user_roles.intersection(required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient role privileges"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

#### FastAPI Dependencies
```python
# src/shared/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTP