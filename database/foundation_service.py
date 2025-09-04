"""
Foundation 3 Database Service - Production-ready database service with proper connection management
Implements unified database service as specified in Foundation 3 Phase 1.1.1
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text, select, and_, func, desc
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Camera, Detection, VideoRecording, CameraStatus
from .db_config import DatabaseConfig

logger = logging.getLogger(__name__)

class FoundationDatabaseService:
    """
    Production-ready database service with proper connection pooling and error handling.
    Implements singleton pattern to prevent concurrent initialization issues.
    """
    
    _instance: Optional['FoundationDatabaseService'] = None
    _initialized: bool = False
    _initialization_lock = asyncio.Lock()
    
    def __new__(cls) -> 'FoundationDatabaseService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.logger = logging.getLogger("FoundationDatabaseService")
        self.config = DatabaseConfig()
        
        # Connection state
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._startup_complete = asyncio.Event()
        
        # Service health tracking
        self._connection_errors = 0
        self._last_health_check = None
        self._health_status = "initializing"
        
        # Mark as initialized
        FoundationDatabaseService._initialized = True
        
    async def initialize(self) -> None:
        """Initialize database engine and session factory (idempotent)"""
        if self._engine is not None:
            return
            
        async with self._initialization_lock:
            if self._engine is not None:  # Double-check pattern
                return
                
            try:
                self.logger.info("Initializing Foundation Database Service...")
                
                # Create async engine with proper pooling for SQLite
                self._engine = create_async_engine(
                    self.config.config['database_url'],
                    echo=False,
                    future=True,
                    poolclass=StaticPool,
                    connect_args={
                        'check_same_thread': False,
                        'timeout': 30.0,
                    }
                )
                
                # Configure SQLite for concurrent access
                await self._configure_sqlite()
                
                # Create session factory
                self._session_factory = sessionmaker(
                    bind=self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=True,
                    autocommit=False
                )
                
                # Create tables
                await self._ensure_tables()
                
                self._health_status = "healthy"
                self._startup_complete.set()
                
                self.logger.info("Foundation Database Service initialized successfully")
                
            except Exception as e:
                self._health_status = "error"
                self.logger.error(f"Failed to initialize database service: {e}")
                raise
    
    async def _configure_sqlite(self) -> None:
        """Configure SQLite for production use"""
        async with self._engine.begin() as conn:
            # Enable WAL mode for concurrent access
            await conn.execute(text("PRAGMA journal_mode = WAL"))
            
            # Set cache size (64MB)
            await conn.execute(text("PRAGMA cache_size = -65536"))
            
            # Enable foreign keys
            await conn.execute(text("PRAGMA foreign_keys = ON"))
            
            # Set synchronous mode for performance
            await conn.execute(text("PRAGMA synchronous = NORMAL"))
            
            # Set temp store in memory
            await conn.execute(text("PRAGMA temp_store = MEMORY"))
            
            # Set mmap size (256MB)
            await conn.execute(text("PRAGMA mmap_size = 268435456"))
            
            # Verify WAL mode
            result = await conn.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
            self.logger.info(f"SQLite journal mode: {mode}")
    
    async def _ensure_tables(self) -> None:
        """Ensure all tables exist"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with proper error handling and connection management"""
        if not self._startup_complete.is_set():
            await self.initialize()
            await self._startup_complete.wait()
        
        if self._session_factory is None:
            raise RuntimeError("Database service not initialized")
        
        session = self._session_factory()
        try:
            yield session
            await session.commit()
            self._connection_errors = 0  # Reset error counter on success
        except Exception as e:
            await session.rollback()
            self._connection_errors += 1
            self.logger.error(f"Database session error: {e}")
            
            if self._connection_errors > 5:
                self._health_status = "degraded"
                self.logger.warning("Multiple database errors detected, service health degraded")
            
            raise
        finally:
            await session.close()
    
    async def execute_with_retry(self, operation, max_retries: int = 3) -> Any:
        """Execute database operation with retry logic"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    return await operation(session)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Database operation failed after {max_retries} attempts: {e}")
        
        raise last_exception
    
    # Camera Management Methods (Foundation 3 Phase 1.1.1 specification)
    
    async def get_all_cameras(self) -> List[Dict[str, Any]]:
        """Get all cameras from database as dict format for service compatibility"""
        async def operation(session):
            result = await session.execute(select(Camera))
            cameras = result.scalars().all()
            
            camera_list = []
            for camera in cameras:
                camera_dict = {
                    'id': camera.id,
                    'camera_id': camera.camera_id,
                    'name': camera.name,
                    'ip_address': camera.ip_address,
                    'port': camera.port,
                    'username': camera.username,
                    'password': camera.password,
                    'stream_path': camera.stream_path,
                    'connection_type': camera.connection_type or 'rtsp',
                    'status': camera.status,
                    'enabled': camera.status in ['active', 'online'],
                    'stable_camera_id': getattr(camera, 'stable_camera_id', None),
                    'resolution_width': camera.resolution_width,
                    'resolution_height': camera.resolution_height,
                    'max_fps': camera.max_fps,
                    'video_quality': camera.video_quality,
                    'low_latency': camera.low_latency,
                    'created_at': camera.created_at,
                    'updated_at': camera.updated_at
                }
                camera_list.append(camera_dict)
            
            return camera_list
        
        return await self.execute_with_retry(operation)
    
    async def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get single camera by ID"""
        async def operation(session):
            result = await session.execute(
                select(Camera).where(Camera.camera_id == camera_id)
            )
            camera = result.scalar_one_or_none()
            
            if camera:
                return {
                    'id': camera.id,
                    'camera_id': camera.camera_id,
                    'name': camera.name,
                    'ip_address': camera.ip_address,
                    'port': camera.port,
                    'username': camera.username,
                    'password': camera.password,
                    'stream_path': camera.stream_path,
                    'connection_type': camera.connection_type or 'rtsp',
                    'status': camera.status,
                    'enabled': camera.status in ['active', 'online'],
                    'stable_camera_id': getattr(camera, 'stable_camera_id', None),
                    'resolution_width': camera.resolution_width,
                    'resolution_height': camera.resolution_height,
                    'max_fps': camera.max_fps,
                    'video_quality': camera.video_quality,
                    'low_latency': camera.low_latency,
                    'created_at': camera.created_at,
                    'updated_at': camera.updated_at
                }
            return None
        
        return await self.execute_with_retry(operation)
    
    async def update_camera_status(self, camera_id: str, status: str) -> bool:
        """Update camera status"""
        async def operation(session):
            result = await session.execute(
                select(Camera).where(Camera.camera_id == camera_id)
            )
            camera = result.scalar_one_or_none()
            
            if camera:
                camera.status = status
                camera.updated_at = datetime.utcnow()
                await session.commit()
                return True
            return False
        
        return await self.execute_with_retry(operation)
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        self._last_health_check = datetime.utcnow()
        
        health_info = {
            'status': self._health_status,
            'timestamp': self._last_health_check.isoformat(),
            'connection_errors': self._connection_errors,
            'engine_initialized': self._engine is not None,
            'session_factory_ready': self._session_factory is not None,
            'database_path': self.config.db_path,
            'database_exists': os.path.exists(self.config.db_path)
        }
        
        try:
            # Test database connectivity
            async with self.get_session() as session:
                result = await session.execute(text("SELECT COUNT(*) FROM cameras"))
                camera_count = result.scalar()
                health_info['camera_count'] = camera_count
                health_info['connectivity'] = 'ok'
        except Exception as e:
            health_info['connectivity'] = 'error'
            health_info['error'] = str(e)
            self._health_status = 'error'
        
        return health_info
    
    async def close(self) -> None:
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._health_status = "closed"
            self.logger.info("Database service closed")

# Global instance for backward compatibility
foundation_db_service = FoundationDatabaseService()

async def get_foundation_database_service() -> FoundationDatabaseService:
    """Get initialized database service instance"""
    await foundation_db_service.initialize()
    return foundation_db_service