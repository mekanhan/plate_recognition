"""
Database Configuration and Connection Management
Provides robust database configuration with connection pooling, 
retry logic, and proper error handling
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, AsyncAdaptedQueuePool
from sqlalchemy import event, text
import aiosqlite

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Centralized database configuration management"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.db_path = os.path.join(self.data_dir, 'license_plates.db')
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Database configuration
        self.config = {
            # Connection settings
            'database_url': f'sqlite+aiosqlite:///{self.db_path}',
            
            # Pool settings
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600,  # Recycle connections after 1 hour
            
            # SQLite specific settings
            'connect_args': {
                'check_same_thread': False,
                'timeout': 30.0,
            },
            
            # Retry settings
            'max_retries': 3,
            'retry_delay': 0.5,
            
            # Performance settings
            'echo': False,  # Set to True for SQL debugging
            'future': True,
            
            # WAL mode for better concurrency
            'pragmas': {
                'journal_mode': 'WAL',
                'cache_size': -64000,  # 64MB cache
                'foreign_keys': 1,
                'synchronous': 'NORMAL',
                'temp_store': 'MEMORY',
                'mmap_size': 268435456,  # 256MB memory map
                'page_size': 4096,
                'optimize': True,
            }
        }
        
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        
    async def init_engine(self) -> AsyncEngine:
        """Initialize the database engine with proper configuration"""
        if self._engine is not None:
            return self._engine
            
        try:
            # Create engine with connection pooling (use StaticPool for SQLite async)
            self._engine = create_async_engine(
                self.config['database_url'],
                echo=self.config['echo'],
                future=self.config['future'],
                poolclass=StaticPool,  # Use StaticPool for SQLite async
                connect_args=self.config['connect_args']
            )
            
            # Configure SQLite pragmas
            await self._configure_pragmas()
            
            # Initialize session factory
            self._session_factory = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )
            
            logger.info(f"Database engine initialized: {self.db_path}")
            return self._engine
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    async def _configure_pragmas(self):
        """Configure SQLite pragmas for optimal performance"""
        if not self._engine:
            return
            
        async with self._engine.begin() as conn:
            for pragma, value in self.config['pragmas'].items():
                if pragma == 'optimize':
                    await conn.execute(text("PRAGMA optimize"))
                else:
                    await conn.execute(text(f"PRAGMA {pragma} = {value}"))
            
            # Verify WAL mode is enabled
            result = await conn.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
            if mode != 'wal':
                logger.warning(f"WAL mode not enabled, current mode: {mode}")
    
    @asynccontextmanager
    async def get_session(self):
        """Get a database session with automatic cleanup"""
        if self._session_factory is None:
            await self.init_engine()
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute a database operation with retry logic"""
        max_retries = self.config['max_retries']
        retry_delay = self.config['retry_delay']
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                    raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        health_status = {
            'status': 'unknown',
            'database_path': self.db_path,
            'database_exists': os.path.exists(self.db_path),
            'database_size': 0,
            'connection_pool': None,
            'wal_enabled': False,
            'tables': [],
            'error': None
        }
        
        try:
            if health_status['database_exists']:
                health_status['database_size'] = os.path.getsize(self.db_path)
            
            if self._engine is None:
                await self.init_engine()
            
            async with self.get_session() as session:
                # Check connection
                result = await session.execute(text("SELECT 1"))
                result.scalar()
                
                # Check WAL mode
                result = await session.execute(text("PRAGMA journal_mode"))
                health_status['wal_enabled'] = result.scalar() == 'wal'
                
                # Get table list
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                health_status['tables'] = [row[0] for row in result.fetchall()]
                
                # Get pool status if available
                if hasattr(self._engine.pool, 'size'):
                    health_status['connection_pool'] = {
                        'size': self._engine.pool.size(),
                        'checked_in': self._engine.pool.checkedin(),
                        'checked_out': self._engine.pool.checkedout(),
                        'overflow': self._engine.pool.overflow(),
                        'total': self._engine.pool.total()
                    }
                
                health_status['status'] = 'healthy'
                
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health_status
    
    async def optimize(self):
        """Optimize database (vacuum, analyze, etc.)"""
        try:
            async with self.get_session() as session:
                # Run VACUUM (requires exclusive access)
                await session.execute(text("VACUUM"))
                
                # Run ANALYZE to update statistics
                await session.execute(text("ANALYZE"))
                
                # Run PRAGMA optimize
                await session.execute(text("PRAGMA optimize"))
                
                logger.info("Database optimization completed")
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise
    
    async def backup(self, backup_path: Optional[str] = None) -> str:
        """Create a database backup"""
        if backup_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.data_dir, f'backup_{timestamp}.db')
        
        try:
            import shutil
            
            # Ensure source exists
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database not found: {self.db_path}")
            
            # Create backup
            shutil.copy2(self.db_path, backup_path)
            
            # Also copy WAL file if it exists
            wal_path = f"{self.db_path}-wal"
            if os.path.exists(wal_path):
                shutil.copy2(wal_path, f"{backup_path}-wal")
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    async def close(self):
        """Close database connections and cleanup"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine closed")

# Global instance
db_config = DatabaseConfig()

# Convenience functions
async def get_session():
    """Get a database session"""
    async with db_config.get_session() as session:
        yield session

async def init_database():
    """Initialize the database"""
    return await db_config.init_engine()

async def close_database():
    """Close the database"""
    return await db_config.close()

async def check_database_health():
    """Check database health"""
    return await db_config.health_check()