# Foundation 3 Complete Implementation Guide

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Phase-by-Phase Implementation](#phase-by-phase-implementation)
3. [Critical Integration Points](#critical-integration-points)
4. [Prompt Engineering Templates](#prompt-engineering-templates)
5. [Testing & Validation](#testing--validation)
6. [Performance Optimization](#performance-optimization)
7. [Security Considerations](#security-considerations)
8. [Deployment Strategy](#deployment-strategy)

---

## System Architecture Overview

### Core Components Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Camera Layer                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐   │
│  │Camera 1 │  │Camera 2 │  │Camera N │  │Edge Processing  │   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘   │
└───────┼────────────┼────────────┼────────────────┼─────────────┘
        │            │            │                │
┌───────▼────────────▼────────────▼────────────────▼─────────────┐
│                    Network Infrastructure                        │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │VLAN Segment │  │Load Balancer │  │Security/Firewall    │   │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘   │
└─────────┼────────────────┼──────────────────────┼──────────────┘
          │                │                      │
┌─────────▼────────────────▼──────────────────────▼──────────────┐
│                      Core Services Layer                         │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │Stream Ingest  │  │Recording    │  │AI Processing     │     │
│  │Service        │  │Service      │  │Service           │     │
│  └───────────────┘  └─────────────┘  └──────────────────┘     │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │Event Process  │  │API Service  │  │Analytics Service │     │
│  └───────────────┘  └─────────────┘  └──────────────────┘     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                       Data Storage Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │PostgreSQL/   │  │Object Store  │  │Redis Cache/Queue   │   │
│  │TimescaleDB   │  │(S3/MinIO)    │  │                    │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Patterns

1. **Video Stream Flow**: Camera → Ingestion → Recording/AI → Storage
2. **Event Flow**: AI/Detection → Event Processing → Message Queue → Notifications
3. **API Flow**: Frontend → API Gateway → Services → Database
4. **Analytics Flow**: Raw Data → Processing → Aggregation → Visualization

---

## Phase-by-Phase Implementation

### Phase 1: Foundation Stabilization (Week 1-2)

#### Day 1-2: Database Schema Implementation

```sql
-- Complete database schema
-- File: migrations/001_complete_schema.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cameras table
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id VARCHAR(255) UNIQUE NOT NULL, -- Stable ID for recording service
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) DEFAULT 'Unknown',
    ip_address VARCHAR(45) NOT NULL,
    port INTEGER DEFAULT 554,
    username VARCHAR(255),
    password VARCHAR(255), -- Should be encrypted in production
    connection_type VARCHAR(50) DEFAULT 'rtsp',
    stream_path VARCHAR(255) DEFAULT '/stream',
    status VARCHAR(50) DEFAULT 'inactive',
    recording_enabled BOOLEAN DEFAULT true,
    retention_days INTEGER DEFAULT 30,
    resolution_width INTEGER DEFAULT 1920,
    resolution_height INTEGER DEFAULT 1080,
    max_fps INTEGER DEFAULT 30,
    video_quality VARCHAR(50) DEFAULT 'high',
    low_latency BOOLEAN DEFAULT false,
    last_test_result VARCHAR(50),
    last_test_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Recording status table
CREATE TABLE recording_status (
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'stopped',
    ffmpeg_pid INTEGER,
    segments_created INTEGER DEFAULT 0,
    storage_used_mb BIGINT DEFAULT 0,
    recording_started_at TIMESTAMP,
    last_segment_time TIMESTAMP,
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (camera_id)
);

-- Detection events table with TimescaleDB
CREATE TABLE detection_events (
    id UUID DEFAULT uuid_generate_v4(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,
    object_class VARCHAR(100),
    license_plate VARCHAR(50),
    bounding_box JSONB,
    metadata JSONB,
    snapshot_path VARCHAR(500),
    video_segment_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE detection_events_2025_01 PARTITION OF detection_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE detection_events_2025_02 PARTITION OF detection_events
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- Continue for all months...

-- Indexes for performance
CREATE INDEX idx_cameras_status ON cameras(status);
CREATE INDEX idx_cameras_camera_id ON cameras(camera_id);
CREATE INDEX idx_detection_camera_time ON detection_events(camera_id, created_at DESC);
CREATE INDEX idx_detection_type ON detection_events(event_type);
CREATE INDEX idx_detection_plate ON detection_events(license_plate) WHERE license_plate IS NOT NULL;

-- Update trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cameras_updated_at BEFORE UPDATE ON cameras
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_recording_status_updated_at BEFORE UPDATE ON recording_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

#### Day 3-4: Database Service Implementation

```python
# File: database/database_service.py
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)

class DatabaseService:
    """Production-ready database service with connection pooling"""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[Pool] = None
        self._retry_count = 3
        self._retry_delay = 1.0
    
    async def initialize(self):
        """Initialize connection pool with retry logic"""
        for attempt in range(self._retry_count):
            try:
                self.pool = await asyncpg.create_pool(
                    self.dsn,
                    min_size=5,
                    max_size=20,
                    max_queries=50000,
                    max_inactive_connection_lifetime=300,
                    command_timeout=60
                )
                logger.info("Database connection pool initialized")
                return
            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))
                else:
                    raise
    
    async def close(self):
        """Close connection pool gracefully"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    # Camera operations
    async def get_all_cameras(self) -> List[Dict[str, Any]]:
        """Get all cameras with recording status"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    c.*,
                    rs.status as recording_status,
                    rs.ffmpeg_pid,
                    rs.segments_created,
                    rs.storage_used_mb,
                    rs.recording_started_at,
                    rs.error_message
                FROM cameras c
                LEFT JOIN recording_status rs ON c.id = rs.camera_id
                ORDER BY c.name
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    async def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get single camera by ID or camera_id"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT c.*, rs.*
                FROM cameras c
                LEFT JOIN recording_status rs ON c.id = rs.camera_id
                WHERE c.id::text = $1 OR c.camera_id = $1
            """
            row = await conn.fetchrow(query, camera_id)
            return dict(row) if row else None
    
    async def add_camera(self, camera_data: Dict[str, Any]) -> str:
        """Add new camera with recording status initialization"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Insert camera
                camera_query = """
                    INSERT INTO cameras (
                        camera_id, name, location, ip_address, port,
                        username, password, connection_type, stream_path,
                        status, recording_enabled, retention_days,
                        resolution_width, resolution_height, max_fps,
                        video_quality, low_latency
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17
                    ) RETURNING id, camera_id
                """
                result = await conn.fetchrow(
                    camera_query,
                    camera_data['camera_id'],
                    camera_data['name'],
                    camera_data.get('location', 'Unknown'),
                    camera_data['ip_address'],
                    camera_data.get('port', 554),
                    camera_data.get('username'),
                    camera_data.get('password'),
                    camera_data.get('connection_type', 'rtsp'),
                    camera_data.get('stream_path', '/stream'),
                    camera_data.get('status', 'inactive'),
                    camera_data.get('recording_enabled', True),
                    camera_data.get('retention_days', 30),
                    camera_data.get('resolution_width', 1920),
                    camera_data.get('resolution_height', 1080),
                    camera_data.get('max_fps', 30),
                    camera_data.get('video_quality', 'high'),
                    camera_data.get('low_latency', False)
                )
                
                # Initialize recording status
                status_query = """
                    INSERT INTO recording_status (camera_id, status)
                    VALUES ($1, 'stopped')
                """
                await conn.execute(status_query, result['id'])
                
                return result['camera_id']
    
    async def update_camera(self, camera_id: str, updates: Dict[str, Any]) -> bool:
        """Update camera configuration"""
        async with self.pool.acquire() as conn:
            # Build dynamic update query
            set_clauses = []
            values = []
            for i, (key, value) in enumerate(updates.items(), 1):
                set_clauses.append(f"{key} = ${i + 1}")
                values.append(value)
            
            if not set_clauses:
                return False
            
            query = f"""
                UPDATE cameras
                SET {', '.join(set_clauses)}
                WHERE id::text = $1 OR camera_id = $1
            """
            values.insert(0, camera_id)
            
            result = await conn.execute(query, *values)
            return result.split()[-1] != '0'
    
    async def delete_camera(self, camera_id: str) -> bool:
        """Delete camera and all related data"""
        async with self.pool.acquire() as conn:
            query = "DELETE FROM cameras WHERE id::text = $1 OR camera_id = $1"
            result = await conn.execute(query, camera_id)
            return result.split()[-1] != '0'
    
    # Recording status operations
    async def update_recording_status(self, camera_id: str, status_data: Dict[str, Any]):
        """Update recording status for a camera"""
        async with self.pool.acquire() as conn:
            # Get camera UUID
            cam_query = "SELECT id FROM cameras WHERE camera_id = $1"
            cam_result = await conn.fetchrow(cam_query, camera_id)
            if not cam_result:
                return
            
            query = """
                INSERT INTO recording_status (camera_id, status, ffmpeg_pid)
                VALUES ($1, $2, $3)
                ON CONFLICT (camera_id) DO UPDATE SET
                    status = $2,
                    ffmpeg_pid = $3,
                    updated_at = NOW()
            """
            await conn.execute(
                query,
                cam_result['id'],
                status_data.get('status', 'stopped'),
                status_data.get('ffmpeg_pid')
            )
    
    # Detection operations
    async def add_detection(self, detection_data: Dict[str, Any]) -> str:
        """Add detection event"""
        async with self.pool.acquire() as conn:
            # Get camera UUID
            cam_query = "SELECT id FROM cameras WHERE camera_id = $1"
            cam_result = await conn.fetchrow(cam_query, detection_data['camera_id'])
            if not cam_result:
                return None
            
            query = """
                INSERT INTO detection_events (
                    camera_id, event_type, confidence, object_class,
                    license_plate, bounding_box, metadata,
                    snapshot_path, video_segment_path
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """
            
            result = await conn.fetchrow(
                query,
                cam_result['id'],
                detection_data['event_type'],
                detection_data['confidence'],
                detection_data.get('object_class'),
                detection_data.get('license_plate'),
                detection_data.get('bounding_box'),
                detection_data.get('metadata'),
                detection_data.get('snapshot_path'),
                detection_data.get('video_segment_path')
            )
            return str(result['id'])
    
    async def get_detections(self, camera_id: str = None, 
                           start_time: datetime = None,
                           end_time: datetime = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Get detection events with filters"""
        async with self.pool.acquire() as conn:
            query_parts = ["SELECT * FROM detection_events WHERE 1=1"]
            params = []
            param_count = 0
            
            if camera_id:
                param_count += 1
                query_parts.append(f"AND camera_id = (SELECT id FROM cameras WHERE camera_id = ${param_count})")
                params.append(camera_id)
            
            if start_time:
                param_count += 1
                query_parts.append(f"AND created_at >= ${param_count}")
                params.append(start_time)
            
            if end_time:
                param_count += 1
                query_parts.append(f"AND created_at <= ${param_count}")
                params.append(end_time)
            
            query_parts.append("ORDER BY created_at DESC")
            
            if limit:
                param_count += 1
                query_parts.append(f"LIMIT ${param_count}")
                params.append(limit)
            
            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    # Health check
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
```

#### Day 5-6: Service Integration Layer

```python
# File: services/service_integration.py
import asyncio
import aiohttp
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ServiceIntegrator:
    """Handles communication between services"""
    
    def __init__(self):
        self.service_urls = {
            'recording': 'http://localhost:8002',
            'ai_processing': 'http://localhost:8003',
            'event_processing': 'http://localhost:8004',
            'analytics': 'http://localhost:8005'
        }
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100),
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def notify_recording_service(self, event_type: str, camera_id: str, data: Dict[str, Any] = None):
        """Notify recording service of camera events"""
        try:
            url = f"{self.service_urls['recording']}/api/events"
            payload = {
                'event_type': event_type,
                'camera_id': camera_id,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data or {}
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Recording service notification failed: {response.status}")
                    return False
                return True
                
        except Exception as e:
            logger.error(f"Failed to notify recording service: {e}")
            return False
    
    async def get_service_health(self) -> Dict[str, bool]:
        """Check health of all services"""
        health_status = {}
        
        for service_name, url in self.service_urls.items():
            try:
                async with self.session.get(f"{url}/health", timeout=5) as response:
                    health_status[service_name] = response.status == 200
            except:
                health_status[service_name] = False
        
        return health_status
```

### Phase 2: Stream Management Core (Week 3-4)

#### Stream Connection Pool Implementation

```python
# File: stream/connection_pool.py
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import cv2
import numpy as np
from dataclasses import dataclass, field
from asyncio import Lock

logger = logging.getLogger(__name__)

@dataclass
class StreamConnection:
    """Represents a single camera stream connection"""
    camera_id: str
    url: str
    cap: Optional[cv2.VideoCapture] = None
    last_frame_time: datetime = field(default_factory=datetime.utcnow)
    frame_count: int = 0
    error_count: int = 0
    is_healthy: bool = True
    lock: Lock = field(default_factory=Lock)

class StreamConnectionPool:
    """Thread-safe connection pool for camera streams"""
    
    def __init__(self, max_connections: int = 100, health_check_interval: int = 30):
        self.max_connections = max_connections
        self.health_check_interval = health_check_interval
        self.connections: Dict[str, StreamConnection] = {}
        self.global_lock = asyncio.Lock()
        self._health_check_task = None
        self._retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
    
    async def start(self):
        """Start the connection pool and health monitoring"""
        self._health_check_task = asyncio.create_task(self._health_monitor())
        logger.info(f"Stream connection pool started with max {self.max_connections} connections")
    
    async def stop(self):
        """Stop the connection pool and cleanup"""
        if self._health_check_task:
            self._health_check_task.cancel()
        
        async with self.global_lock:
            for conn in self.connections.values():
                await self._close_connection(conn)
            self.connections.clear()
    
    async def get_connection(self, camera_id: str, url: str) -> StreamConnection:
        """Get or create a connection for a camera"""
        async with self.global_lock:
            if camera_id in self.connections:
                conn = self.connections[camera_id]
                if conn.is_healthy:
                    return conn
                else:
                    # Unhealthy connection, recreate
                    await self._close_connection(conn)
                    del self.connections[camera_id]
            
            # Check pool limit
            if len(self.connections) >= self.max_connections:
                # Remove least recently used connection
                lru_id = min(self.connections.keys(), 
                           key=lambda k: self.connections[k].last_frame_time)
                await self._close_connection(self.connections[lru_id])
                del self.connections[lru_id]
            
            # Create new connection
            conn = await self._create_connection(camera_id, url)
            if conn:
                self.connections[camera_id] = conn
                return conn
            else:
                raise ConnectionError(f"Failed to connect to camera {camera_id}")
    
    async def _create_connection(self, camera_id: str, url: str) -> Optional[StreamConnection]:
        """Create a new stream connection with retry logic"""
        conn = StreamConnection(camera_id=camera_id, url=url)
        
        for attempt, delay in enumerate(self._retry_delays):
            try:
                # Create VideoCapture in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                cap = await loop.run_in_executor(
                    None,
                    lambda: cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                )
                
                # Configure capture properties
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
                cap.set(cv2.CAP_PROP_FPS, 30)
                
                # Test connection
                ret, frame = cap.read()
                if ret and frame is not None:
                    conn.cap = cap
                    conn.is_healthy = True
                    logger.info(f"Connected to camera {camera_id} on attempt {attempt + 1}")
                    return conn
                else:
                    cap.release()
                    
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed for {camera_id}: {e}")
            
            if attempt < len(self._retry_delays) - 1:
                await asyncio.sleep(delay)
        
        logger.error(f"Failed to connect to camera {camera_id} after {len(self._retry_delays)} attempts")
        return None
    
    async def _close_connection(self, conn: StreamConnection):
        """Close a stream connection"""
        async with conn.lock:
            if conn.cap:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, conn.cap.release)
                conn.cap = None
            conn.is_healthy = False
    
    async def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get a frame from a camera stream"""
        if camera_id not in self.connections:
            raise ValueError(f"No connection for camera {camera_id}")
        
        conn = self.connections[camera_id]
        async with conn.lock:
            if not conn.cap or not conn.is_healthy:
                return None
            
            try:
                loop = asyncio.get_event_loop()
                ret, frame = await loop.run_in_executor(
                    None, conn.cap.read
                )
                
                if ret and frame is not None:
                    conn.last_frame_time = datetime.utcnow()
                    conn.frame_count += 1
                    conn.error_count = 0
                    return frame
                else:
                    conn.error_count += 1
                    if conn.error_count > 5:
                        conn.is_healthy = False
                    return None
                    
            except Exception as e:
                logger.error(f"Error reading frame from {camera_id}: {e}")
                conn.error_count += 1
                conn.is_healthy = False
                return None
    
    async def _health_monitor(self):
        """Monitor connection health periodically"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                async with self.global_lock:
                    for camera_id, conn in list(self.connections.items()):
                        # Check if connection is stale
                        time_since_last_frame = datetime.utcnow() - conn.last_frame_time
                        if time_since_last_frame > timedelta(seconds=60):
                            logger.warning(f"Connection {camera_id} is stale, marking unhealthy")
                            conn.is_healthy = False
                        
                        # Remove unhealthy connections with too many errors
                        if not conn.is_healthy and conn.error_count > 10:
                            await self._close_connection(conn)
                            del self.connections[camera_id]
                            logger.info(f"Removed unhealthy connection {camera_id}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        stats = {
            'total_connections': len(self.connections),
            'healthy_connections': sum(1 for c in self.connections.values() if c.is_healthy),
            'total_frames': sum(c.frame_count for c in self.connections.values()),
            'connections': {}
        }
        
        for camera_id, conn in self.connections.items():
            stats['connections'][camera_id] = {
                'is_healthy': conn.is_healthy,
                'frame_count': conn.frame_count,
                'error_count': conn.error_count,
                'last_frame_time': conn.last_frame_time.isoformat()
            }
        
        return stats
```

#### GPU Processing Pipeline

```python
# File: gpu/gpu_processor.py
import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import torch
import pynvml
from queue import Queue
import threading

logger = logging.getLogger(__name__)

@dataclass
class GPUConfig:
    device_id: int = 0
    max_batch_size: int = 4
    memory_fraction: float = 0.8
    enable_tensorrt: bool = True
    precision: str = 'fp16'  # fp32, fp16, int8

class GPUProcessor:
    """GPU-accelerated video processing pipeline"""
    
    def __init__(self, config: GPUConfig):
        self.config = config
        self.device = None
        self.processing_queue = Queue(maxsize=100)
        self.result_queue = Queue(maxsize=100)
        self.worker_thread = None
        self.running = False
        self._initialize_gpu()
    
    def _initialize_gpu(self):
        """Initialize GPU and monitoring"""
        try:
            # Initialize NVML for GPU monitoring
            pynvml.nvmlInit()
            self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(self.config.device_id)
            
            # Set CUDA device
            torch.cuda.set_device(self.config.device_id)
            self.device = torch.device(f'cuda:{self.config.device_id}')
            
            # Configure memory
            if self.config.memory_fraction < 1.0:
                torch.cuda.set_per_process_memory_fraction(
                    self.config.memory_fraction, 
                    self.config.device_id
                )
            
            logger.info(f"GPU {self.config.device_id} initialized successfully")
            
        except Exception as e:
            logger.error(f"GPU initialization failed: {e}")
            raise
    
    def start(self):
        """Start GPU processing thread"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_loop)
        self.worker_thread.start()
        logger.info("GPU processor started")
    
    def stop(self):
        """Stop GPU processing"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        logger.info("GPU processor stopped")
    
    async def process_frame_async(self, camera_id: str, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Queue frame for processing and get result asynchronously"""
        # Add to processing queue
        self.processing_queue.put({
            'camera_id': camera_id,
            'frame': frame,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        # Wait for result (non-blocking)
        while True:
            if not self.result_queue.empty():
                result = self.result_queue.get()
                if result['camera_id'] == camera_id:
                    return result
                else:
                    # Not our result, put it back
                    self.result_queue.put(result)
            await asyncio.sleep(0.01)
    
    def _process_loop(self):
        """Main GPU processing loop"""
        batch = []
        
        while self.running:
            try:
                # Collect batch
                while len(batch) < self.config.max_batch_size:
                    try:
                        item = self.processing_queue.get(timeout=0.1)
                        batch.append(item)
                    except:
                        break
                
                if batch:
                    # Process batch on GPU
                    results = self._process_batch_gpu(batch)
                    
                    # Queue results
                    for result in results:
                        self.result_queue.put(result)
                    
                    batch.clear()
                    
            except Exception as e:
                logger.error(f"GPU processing error: {e}")
                batch.clear()
    
    def _process_batch_gpu(self, batch: List[Dict]) -> List[Dict]:
        """Process a batch of frames on GPU"""
        results = []
        
        try:
            # Convert frames to tensor
            frames = [item['frame'] for item in batch]
            tensor_batch = self._frames_to_tensor(frames)
            
            # Move to GPU
            tensor_batch = tensor_batch.to(self.device)
            
            # Run inference (placeholder - implement your model here)
            with torch.no_grad():
                detections = self._run_inference(tensor_batch)
            
            # Process results
            for i, item in enumerate(batch):
                results.append({
                    'camera_id': item['camera_id'],
                    'detections': detections[i],
                    'processing_time': asyncio.get_event_loop().time() - item['timestamp']
                })
                
        except Exception as e:
            logger.error(f"Batch GPU processing failed: {e}")
            # Return empty results on error
            for item in batch:
                results.append({
                    'camera_id': item['camera_id'],
                    'detections': [],
                    'error': str(e)
                })
        
        return results
    
    def _frames_to_tensor(self, frames: List[np.ndarray]) -> torch.Tensor:
        """Convert numpy frames to PyTorch tensor"""
        # Assuming frames are BGR, convert to RGB and normalize
        tensors = []
        for frame in frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (640, 640))
            frame_normalized = frame_resized.astype(np.float32) / 255.0
            tensor = torch.from_numpy(frame_normalized).permute(2, 0, 1)
            tensors.append(tensor)
        
        return torch.stack(tensors)
    
    def _run_inference(self, tensor_batch: torch.Tensor) -> List[List[Dict]]:
        """Run model inference on GPU (placeholder)"""
        # This is where you'd run your actual model
        # For now, return dummy detections
        batch_size = tensor_batch.shape[0]
        return [[] for _ in range(batch_size)]
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """Get current GPU statistics"""
        try:
            memory = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            temperature = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
            
            return {
                'device_id': self.config.device_id,
                'memory_used_mb': memory.used // (1024 * 1024),
                'memory_total_mb': memory.total // (1024 * 1024),
                'memory_percent': (memory.used / memory.total) * 100,
                'gpu_utilization': utilization.gpu,
                'memory_utilization': utilization.memory,
                'temperature': temperature,
                'queue_size': self.processing_queue.qsize()
            }
        except Exception as e:
            logger.error(f"Failed to get GPU stats: {e}")
            return {}
```

### Phase 3: AI Pipeline (Week 5-6)

#### YOLOv8 TensorRT Integration

```python
# File: ai/yolo_tensorrt.py
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import numpy as np
import cv2
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class YOLOv8TensorRT:
    """YOLOv8 with TensorRT optimization for production inference"""
    
    def __init__(self, engine_path: str, conf_threshold: float = 0.5, nms_threshold: float = 0.4):
        self.engine_path = engine_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.input_shape = (640, 640)
        self.batch_size = 4
        
        # Load TensorRT engine
        self._load_engine()
        
        # Allocate buffers
        self._allocate_buffers()
        
        logger.info(f"YOLOv8 TensorRT engine loaded from {engine_path}")
    
    def _load_engine(self):
        """Load TensorRT engine"""
        # Create runtime
        self.trt_logger = trt.Logger(trt.Logger.WARNING)
        self.runtime = trt.Runtime(self.trt_logger)
        
        # Load engine
        with open(self.engine_path, 'rb') as f:
            self.engine = self.runtime.deserialize_cuda_engine(f.read())
        
        # Create execution context
        self.context = self.engine.create_execution_context()
        
        # Get input/output info
        self.input_idx = self.engine.get_binding_index("images")
        self.output_idx = self.engine.get_binding_index("output")
        
        # Get shapes
        self.input_shape = self.engine.get_binding_shape(self.input_idx)
        self.output_shape = self.engine.get_binding_shape(self.output_idx)
    
    def _allocate_buffers(self):
        """Allocate GPU memory for inputs and outputs"""
        # Calculate sizes
        self.input_size = trt.volume(self.input_shape) * self.batch_size * np.float32().itemsize
        self.output_size = trt.volume(self.output_shape) * self.batch_size * np.float32().itemsize
        
        # Allocate device memory
        self.d_input = cuda.mem_alloc(self.input_size)
        self.d_output = cuda.mem_alloc(self.output_size)
        
        # Create stream
        self.stream = cuda.Stream()
        
        # Allocate host memory
        self.h_input = cuda.pagelocked_empty(
            (self.batch_size, 3, self.input_shape[2], self.input_shape[3]), 
            dtype=np.float32
        )
        self.h_output = cuda.pagelocked_empty(
            (self.batch_size, self.output_shape[1], self.output_shape[2]), 
            dtype=np.float32
        )
    
    def preprocess_batch(self, images: List[np.ndarray]) -> np.ndarray:
        """Preprocess batch of images for YOLOv8"""
        batch = np.zeros((len(images), 3, *self.input_shape), dtype=np.float32)
        
        for i, image in enumerate(images):
            # Resize with aspect ratio preservation
            resized = self._letterbox_resize(image, self.input_shape)
            
            # BGR to RGB
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # Normalize to [0, 1]
            normalized = rgb.astype(np.float32) / 255.0
            
            # HWC to CHW
            batch[i] = normalized.transpose(2, 0, 1)
        
        return batch
    
    def _letterbox_resize(self, image: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        """Resize image with aspect ratio preservation"""
        h, w = image.shape[:2]
        target_h, target_w = target_shape
        
        # Calculate scale
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Resize
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Pad to target size
        pad_w = (target_w - new_w) // 2
        pad_h = (target_h - new_h) // 2
        
        padded = cv2.copyMakeBorder(
            resized, pad_h, target_h - new_h - pad_h, 
            pad_w, target_w - new_w - pad_w,
            cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )
        
        return padded
    
    def detect_batch(self, images: List[np.ndarray]) -> List[List[Dict[str, Any]]]:
        """Run detection on batch of images"""
        # Preprocess
        batch = self.preprocess_batch(images)
        
        # Copy to host memory
        self.h_input[:len(images)] = batch
        
        # Copy to device
        cuda.memcpy_htod_async(self.d_input, self.h_input, self.stream)
        
        # Run inference
        bindings = [int(self.d_input), int(self.d_output)]
        self.context.execute_async_v2(bindings, self.stream.handle)
        
        # Copy output to host
        cuda.memcpy_dtoh_async(self.h_output, self.d_output, self.stream)
        
        # Synchronize
        self.stream.synchronize()
        
        # Process outputs
        results = []
        for i in range(len(images)):
            detections = self._process_output(self.h_output[i], images[i].shape[:2])
            results.append(detections)
        
        return results
    
    def _process_output(self, output: np.ndarray, original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Process YOLOv8 output to get detections"""
        detections = []
        
        # YOLOv8 output format: [x, y, w, h, conf, class_probs...]
        # Transpose to get [num_detections, features]
        predictions = output.T
        
        # Filter by confidence
        mask = predictions[:, 4] > self.conf_threshold
        predictions = predictions[mask]
        
        if len(predictions) == 0:
            return detections
        
        # Get boxes, scores, and classes
        boxes = predictions[:, :4]
        scores = predictions[:, 4]
        class_ids = np.argmax(predictions[:, 5:], axis=1)
        
        # Convert from xywh to xyxy
        boxes = self._xywh_to_xyxy(boxes)
        
        # Apply NMS
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(), scores.tolist(), 
            self.conf_threshold, self.nms_threshold
        )
        
        if len(indices) > 0:
            indices = indices.flatten()
            
            for idx in indices:
                x1, y1, x2, y2 = boxes[idx]
                
                # Scale to original image size
                h_scale = original_shape[0] / self.input_shape[0]
                w_scale = original_shape[1] / self.input_shape[1]
                
                detection = {
                    'bbox': [
                        int(x1 * w_scale),
                        int(y1 * h_scale),
                        int(x2 * w_scale),
                        int(y2 * h_scale)
                    ],
                    'confidence': float(scores[idx]),
                    'class_id': int(class_ids[idx]),
                    'class_name': self._get_class_name(class_ids[idx])
                }
                detections.append(detection)
        
        return detections
    
    def _xywh_to_xyxy(self, boxes: np.ndarray) -> np.ndarray:
        """Convert bounding boxes from xywh to xyxy format"""
        xyxy = np.copy(boxes)
        xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2  # x1
        xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2  # y1
        xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2  # x2
        xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2  # y2
        return xyxy
    
    def _get_class_name(self, class_id: int) -> str:
        """Get class name from ID (customize for your model)"""
        # COCO classes for default YOLOv8
        coco_classes = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
            'toothbrush'
        ]
        
        if 0 <= class_id < len(coco_classes):
            return coco_classes[class_id]
        return f'class_{class_id}'
    
    def cleanup(self):
        """Cleanup GPU resources"""
        del self.d_input
        del self.d_output
        del self.stream
        del self.context
        del self.engine
        logger.info("YOLOv8 TensorRT cleanup completed")
```

### Phase 4: Storage & Performance (Week 7-8)

#### TimescaleDB Integration

```python
# File: storage/timescale_service.py
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TimescaleService:
    """Service for handling time-series data with TimescaleDB"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize TimescaleDB connection and setup"""
        # Create connection pool
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Setup TimescaleDB
        await self._setup_timescale()
        
        logger.info("TimescaleDB service initialized")
    
    async def _setup_timescale(self):
        """Setup TimescaleDB extensions and hypertables"""
        async with self.pool.acquire() as conn:
            # Enable TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            
            # Convert detection_events to hypertable if not already
            try:
                await conn.execute("""
                    SELECT create_hypertable(
                        'detection_events',
                        'created_at',
                        chunk_time_interval => interval '1 day',
                        if_not_exists => TRUE
                    );
                """)
            except:
                pass  # Already a hypertable
            
            # Create continuous aggregates for analytics
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS detection_stats_hourly
                WITH (timescaledb.continuous) AS
                SELECT
                    camera_id,
                    time_bucket('1 hour', created_at) AS hour,
                    event_type,
                    COUNT(*) as event_count,
                    AVG(confidence) as avg_confidence,
                    MAX(confidence) as max_confidence
                FROM detection_events
                GROUP BY camera_id, hour, event_type
                WITH NO DATA;
            """)
            
            # Create retention policy (keep raw data for 90 days)
            await conn.execute("""
                SELECT add_retention_policy(
                    'detection_events',
                    interval '90 days',
                    if_not_exists => TRUE
                );
            """)
            
            # Create compression policy (compress data older than 7 days)
            await conn.execute("""
                SELECT add_compression_policy(
                    'detection_events',
                    interval '7 days',
                    if_not_exists => TRUE
                );
            """)
    
    async def insert_detection_batch(self, detections: List[Dict[str, Any]]):
        """Efficiently insert batch of detections"""
        if not detections:
            return
        
        async with self.pool.acquire() as conn:
            # Prepare data for COPY
            records = []
            for det in detections:
                records.append((
                    det['camera_id'],
                    det['event_type'],
                    det['confidence'],
                    det.get('object_class'),
                    det.get('license_plate'),
                    det.get('bounding_box'),
                    det.get('metadata'),
                    det.get('snapshot_path'),
                    det.get('video_segment_path'),
                    det.get('created_at', datetime.utcnow())
                ))
            
            # Use COPY for efficient bulk insert
            await conn.copy_records_to_table(
                'detection_events',
                records=records,
                columns=[
                    'camera_id', 'event_type', 'confidence', 'object_class',
                    'license_plate', 'bounding_box', 'metadata',
                    'snapshot_path', 'video_segment_path', 'created_at'
                ]
            )
    
    async def get_camera_analytics(self, camera_id: str, 
                                 start_time: datetime,
                                 end_time: datetime,
                                 granularity: str = 'hour') -> List[Dict[str, Any]]:
        """Get analytics for a camera over time period"""
        async with self.pool.acquire() as conn:
            # Determine time bucket based on granularity
            time_bucket_map = {
                'minute': '1 minute',
                'hour': '1 hour',
                'day': '1 day',
                'week': '1 week',
                'month': '1 month'
            }
            bucket = time_bucket_map.get(granularity, '1 hour')
            
            query = """
                SELECT
                    time_bucket($1::interval, created_at) AS time_bucket,
                    event_type,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY confidence) as median_confidence,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY confidence) as p95_confidence
                FROM detection_events
                WHERE camera_id = $2
                    AND created_at >= $3
                    AND created_at <= $4
                GROUP BY time_bucket, event_type
                ORDER BY time_bucket, event_type;
            """
            
            rows = await conn.fetch(query, bucket, camera_id, start_time, end_time)
            return [dict(row) for row in rows]
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        async with self.pool.acquire() as conn:
            # Total detections
            total_query = "SELECT COUNT(*) FROM detection_events;"
            total_count = await conn.fetchval(total_query)
            
            # Detections in last hour
            hour_query = """
                SELECT COUNT(*) FROM detection_events 
                WHERE created_at > NOW() - INTERVAL '1 hour';
            """
            hour_count = await conn.fetchval(hour_query)
            
            # Storage size
            size_query = """
                SELECT 
                    hypertable_size('detection_events') as total_size,
                    hypertable_compression_stats('detection_events') as compression_stats;
            """
            size_info = await conn.fetchrow(size_query)
            
            # Active cameras
            cameras_query = """
                SELECT COUNT(DISTINCT camera_id) FROM detection_events 
                WHERE created_at > NOW() - INTERVAL '5 minutes';
            """
            active_cameras = await conn.fetchval(cameras_query)
            
            return {
                'total_detections': total_count,
                'detections_last_hour': hour_count,
                'active_cameras': active_cameras,
                'storage_size_mb': size_info['total_size'] // (1024 * 1024) if size_info else 0,
                'compression_ratio': size_info['compression_stats'].get('compression_ratio', 1.0) if size_info and size_info['compression_stats'] else 1.0
            }
```

#### Redis Caching Layer

```python
# File: cache/redis_service.py
import asyncio
import aioredis
import json
import pickle
from typing import Any, Optional, List, Dict
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class RedisService:
    """Redis caching and pub/sub service"""
    
    def __init__(self, url: str = "redis://localhost"):
        self.url = url
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.subscribers = {}
    
    async def initialize(self):
        """Initialize Redis connections"""
        self.redis = await aioredis.from_url(
            self.url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )
        
        # Test connection
        await self.redis.ping()
        logger.info("Redis service initialized")
    
    async def close(self):
        """Close Redis connections"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
    
    # Caching operations
    async def set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Set cache value with TTL"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = pickle.dumps(value).hex()
            
            await self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON first
            try:
                return json.loads(value)
            except:
                # Try to unpickle
                try:
                    return pickle.loads(bytes.fromhex(value))
                except:
                    return value
                    
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    async def delete_cache(self, pattern: str):
        """Delete cache keys matching pattern"""
        try:
            keys = []
            async for key in self.redis.scan_iter(pattern):
                keys.append(key)
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Deleted {len(keys)} cache keys matching {pattern}")
                
        except Exception as e:
            logger.error(f"Cache delete error for {pattern}: {e}")
    
    # Camera status caching
    async def set_camera_status(self, camera_id: str, status: Dict[str, Any]):
        """Cache camera status"""
        key = f"camera:status:{camera_id}"
        await self.set_cache(key, status, ttl=60)  # 1 minute TTL
    
    async def get_camera_status(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get cached camera status"""
        key = f"camera:status:{camera_id}"
        return await self.get_cache(key)
    
    async def get_all_camera_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get all camera statuses"""
        statuses = {}
        async for key in self.redis.scan_iter("camera:status:*"):
            camera_id = key.split(":")[-1]
            status = await self.get_cache(key)
            if status:
                statuses[camera_id] = status
        return statuses
    
    # Detection caching
    async def cache_recent_detections(self, camera_id: str, detections: List[Dict[str, Any]]):
        """Cache recent detections for a camera"""
        key = f"detections:recent:{camera_id}"
        # Keep only last 100 detections
        if len(detections) > 100:
            detections = detections[-100:]
        await self.set_cache(key, detections, ttl=300)  # 5 minutes
    
    async def get_recent_detections(self, camera_id: str) -> List[Dict[str, Any]]:
        """Get recent detections from cache"""
        key = f"detections:recent:{camera_id}"
        return await self.get_cache(key) or []
    
    # Pub/Sub operations
    async def subscribe(self, channel: str, callback):
        """Subscribe to a channel"""
        if not self.pubsub:
            self.pubsub = self.redis.pubsub()
            asyncio.create_task(self._pubsub_listener())
        
        await self.pubsub.subscribe(channel)
        self.subscribers[channel] = callback
        logger.info(f"Subscribed to channel: {channel}")
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to channel"""
        try:
            msg = json.dumps(message)
            await self.redis.publish(channel, msg)
        except Exception as e:
            logger.error(f"Publish error to {channel}: {e}")
    
    async def _pubsub_listener(self):
        """Listen for pub/sub messages"""
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel']
                if channel in self.subscribers:
                    try:
                        data = json.loads(message['data'])
                        callback = self.subscribers[channel]
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        logger.error(f"Pubsub callback error: {e}")
    
    # Event publishing helpers
    async def publish_camera_event(self, camera_id: str, event_type: str, data: Dict[str, Any]):
        """Publish camera-specific event"""
        await self.publish(f"camera:{camera_id}:events", {
            'event_type': event_type,
            'camera_id': camera_id,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        })
    
    async def publish_detection(self, detection: Dict[str, Any]):
        """Publish detection event"""
        await self.publish("detections:live", detection)
        await self.publish(f"camera:{detection['camera_id']}:detections", detection)
    
    # Distributed locking
    async def acquire_lock(self, resource: str, timeout: int = 10) -> bool:
        """Acquire distributed lock"""
        lock_key = f"lock:{resource}"
        identifier = str(uuid.uuid4())
        
        acquired = await self.redis.set(
            lock_key, identifier, 
            ex=timeout, nx=True
        )
        
        if acquired:
            return identifier
        return None
    
    async def release_lock(self, resource: str, identifier: str) -> bool:
        """Release distributed lock"""
        lock_key = f"lock:{resource}"
        
        # Lua script to ensure we only delete our own lock
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = await self.redis.eval(script, 1, lock_key, identifier)
        return bool(result)
```

---

## Critical Integration Points

### Service Communication Matrix

| Source Service | Target Service | Communication Method | Data Format | Frequency |
|---------------|----------------|---------------------|-------------|-----------|
| Camera | Stream Ingestion | RTSP/HTTP | H.264/H.265 | Continuous |
| Stream Ingestion | Recording | Internal Queue | Raw Frames | 30 FPS |
| Stream Ingestion | AI Processing | Shared Memory | NumPy Arrays | 5-10 FPS |
| AI Processing | Event Processing | Message Queue | JSON | On Detection |
| Event Processing | Database | Direct Write | Structured Data | Batch/Stream |
| All Services | Redis | TCP | JSON/Binary | As Needed |
| Frontend | API Gateway | HTTP/WebSocket | JSON | On Demand |

### Data Consistency Requirements

1. **Camera Configuration**: Single source of truth in PostgreSQL
2. **Recording Status**: Eventually consistent, cached in Redis
3. **Detection Events**: Write-once, immutable in TimescaleDB
4. **Analytics Data**: Aggregated, eventually consistent
5. **Live Status**: Real-time via Redis pub/sub

### Error Recovery Patterns

```python
# File: services/recovery_patterns.py
import asyncio
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Circuit breaker pattern for service resilience"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half_open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = 'closed'
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

class RetryWithBackoff:
    """Retry pattern with exponential backoff"""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    break
                
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception

class ServiceHealthMonitor:
    """Monitor and manage service health"""
    
    def __init__(self):
        self.services = {}
        self.health_checks = {}
        self.monitor_task = None
    
    def register_service(self, name: str, health_check: Callable):
        """Register a service with its health check"""
        self.services[name] = {
            'status': 'unknown',
            'last_check': None,
            'consecutive_failures': 0
        }
        self.health_checks[name] = health_check
    
    async def start_monitoring(self, interval: int = 30):
        """Start health monitoring loop"""
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval))
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        if self.monitor_task:
            self.monitor_task.cancel()
    
    async def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while True:
            try:
                await self._check_all_services()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    async def _check_all_services(self):
        """Check health of all registered services"""
        tasks = []
        for name, health_check in self.health_checks.items():
            tasks.append(self._check_service(name, health_check))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service(self, name: str, health_check: Callable):
        """Check individual service health"""
        try:
            is_healthy = await health_check()
            
            if is_healthy:
                self.services[name]['status'] = 'healthy'
                self.services[name]['consecutive_failures'] = 0
            else:
                self.services[name]['status'] = 'unhealthy'
                self.services[name]['consecutive_failures'] += 1
                
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            self.services[name]['status'] = 'error'
            self.services[name]['consecutive_failures'] += 1
        
        self.services[name]['last_check'] = datetime.utcnow()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current status of all services"""
        return {
            name: {
                **info,
                'last_check': info['last_check'].isoformat() if info['last_check'] else None
            }
            for name, info in self.services.items()
        }
```

---

## Prompt Engineering Templates

### Template Collection for AI Agents

#### 1. Component Implementation Template
```markdown
Role: Senior Software Engineer with 10+ years in distributed systems, video processing, and Python/FastAPI development.

Context: Building component [COMPONENT_NAME] for a production video surveillance system with these specifications:
- Architecture: Microservices with PostgreSQL, Redis, TimescaleDB
- Scale: 4-20 cameras initially, scaling to 1000+
- Performance: <500ms detection latency, 99.9% uptime
- Current Phase: [PHASE_NUMBER] - [PHASE_NAME]

Component Requirements:
[PASTE EXACT REQUIREMENTS FROM PHASE GUIDE]

Integration Points:
- Upstream: [LIST SERVICES THAT FEED DATA]
- Downstream: [LIST SERVICES THAT CONSUME DATA]
- Shared Resources: [DATABASE/CACHE/QUEUE DETAILS]

Task: Implement [SPECIFIC_COMPONENT] with:
1. Complete error handling and recovery
2. Comprehensive logging
3. Performance monitoring hooks
4. Unit and integration tests
5. Documentation

Constraints:
- Must handle network interruptions gracefully
- Support concurrent operations (specify number)
- Memory usage must stay under [LIMIT]
- Follow provided coding standards exactly

Output Format:
1. **Implementation Code** (production-ready with all imports)
2. **Test Suite** (pytest with async support)
3. **Integration Guide** (how to connect with other services)
4. **Configuration Schema** (environment variables, settings)
5. **Deployment Notes** (Docker, dependencies, startup order)
```

#### 2. Debugging Complex Issues Template
```markdown
Role: Senior DevOps Engineer specializing in distributed systems debugging and Python/video streaming applications.

Context: Production surveillance system experiencing [ISSUE_DESCRIPTION]
System Architecture:
- Services: [LIST AFFECTED SERVICES]
- Infrastructure: Docker containers, RTX 3080 GPU, Ubuntu 22.04
- Current Load: [NUMBER] cameras, [NUMBER] detections/hour

Symptoms:
[DETAILED SYMPTOMS WITH TIMESTAMPS]

Error Logs:
```
[PASTE RELEVANT ERROR LOGS]
```

Metrics at Time of Issue:
- CPU Usage: [VALUE]
- Memory Usage: [VALUE]
- GPU Utilization: [VALUE]
- Network I/O: [VALUE]
- Database Connections: [VALUE]

Recent Changes:
[LIST ANY RECENT DEPLOYMENTS OR CHANGES]

Task: Diagnose root cause and provide fix that:
1. Resolves immediate issue
2. Prevents recurrence
3. Maintains system stability
4. Can be deployed without downtime

Constraints:
- Cannot interrupt active recordings
- Must maintain data integrity
- Fix must be reversible
- Solution must be monitoring-friendly

Output Format:
1. **Root Cause Analysis** (technical deep dive)
2. **Immediate Mitigation** (stop the bleeding)
3. **Permanent Fix** (code changes required)
4. **Verification Tests** (how to confirm fix works)
5. **Monitoring Additions** (prevent future occurrences)
6. **Rollback Plan** (if fix causes issues)
```

#### 3. Performance Optimization Template
```markdown
Role: Performance Engineer with expertise in video processing, GPU optimization, and Python async programming.

Context: Surveillance system component [COMPONENT] showing performance degradation
Current Performance Metrics:
- Latency: [CURRENT] (target: [TARGET])
- Throughput: [CURRENT] (target: [TARGET])
- Resource Usage: [CPU/MEM/GPU STATS]

Bottleneck Analysis Results:
[PROFILING DATA OR ASSUMPTIONS]

Code Section Under Review:
```python
[PASTE CURRENT IMPLEMENTATION]
```

Task: Optimize for:
1. Reduced latency (target: [SPECIFIC_MS])
2. Increased throughput (target: [SPECIFIC_FPS/QPS])
3. Better resource utilization
4. Maintained code readability

Constraints:
- Cannot change external interfaces
- Must maintain backward compatibility
- GPU memory limited to [AMOUNT]
- Must support [NUMBER] concurrent streams

Output Format:
1. **Performance Analysis** (where time/resources spent)
2. **Optimization Strategy** (approach and reasoning)
3. **Optimized Code** (with performance comments)
4. **Benchmark Comparison** (before/after metrics)
5. **Trade-offs** (what we're sacrificing, if anything)
6. **Further Opportunities** (additional optimizations possible)
```

#### 4. Integration Testing Template
```markdown
Role: QA Automation Engineer specializing in distributed systems testing and video streaming applications.

Context: Need comprehensive integration tests for [COMPONENT/FEATURE]
System Components:
- Component Under Test: [COMPONENT]
- Dependencies: [LIST ALL DEPENDENCIES]
- External Services: [LIST EXTERNAL SERVICES]

Test Scenarios Required:
1. Happy path workflows
2. Error conditions
3. Edge cases
4. Performance boundaries
5. Concurrent operations

Current Test Coverage:
- Unit Tests: [PERCENTAGE]
- Integration Tests: [PERCENTAGE]
- E2E Tests: [PERCENTAGE]

Task: Create integration test suite that:
1. Tests all integration points
2. Simulates real-world conditions
3. Includes negative test cases
4. Measures performance
5. Can run in CI/CD pipeline

Constraints:
- Tests must complete in under [TIME]
- Cannot require actual cameras
- Must clean up all test data
- Should use Docker compose for dependencies

Output Format:
1. **Test Plan** (what we're testing and why)
2. **Test Implementation** (pytest code with fixtures)
3. **Mock Services** (how we simulate dependencies)
4. **Test Data** (realistic test scenarios)
5. **CI/CD Integration** (how to run in pipeline)
6. **Coverage Report** (what's tested, what's not)
```

#### 5. Security Hardening Template
```markdown
Role: Security Engineer with expertise in video surveillance systems and API security.

Context: Security audit required for [COMPONENT/SERVICE]
Current Security Measures:
- Authentication: [CURRENT_METHOD]
- Authorization: [CURRENT_METHOD]
- Encryption: [CURRENT_METHOD]
- Input Validation: [CURRENT_METHOD]

Potential Threat Vectors:
1. Unauthorized camera access
2. Stream interception
3. API abuse
4. Data tampering
5. Resource exhaustion

Compliance Requirements:
- GDPR compliance for video data
- SOC2 requirements
- Industry best practices

Task: Implement security hardening:
1. Identify vulnerabilities
2. Implement fixes
3. Add security monitoring
4. Create security tests
5. Document security measures

Constraints:
- Cannot impact performance significantly
- Must maintain backward compatibility
- Should not complicate deployment
- Must be auditable

Output Format:
1. **Vulnerability Assessment** (what could go wrong)
2. **Security Implementations** (code fixes)
3. **Authentication/Authorization** (improved controls)
4. **Monitoring and Alerting** (security events)
5. **Security Test Suite** (penetration tests)
6. **Compliance Checklist** (what we meet/don't meet)
```

---

## Testing & Validation

### Comprehensive Test Strategy

#### Unit Testing Framework
```python
# File: tests/test_framework.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from datetime import datetime

# Fixtures for common test objects
@pytest.fixture
def mock_camera_config():
    """Standard camera configuration for tests"""
    return {
        'camera_id': 'test_cam_001',
        'name': 'Test Camera',
        'ip_address': '192.168.1.100',
        'port': 554,
        'username': 'admin',
        'password': 'password',
        'stream_path': '/stream'
    }

@pytest.fixture
def mock_frame():
    """Generate mock video frame"""
    return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

@pytest.fixture
async def mock_database():
    """Mock database service"""
    db = AsyncMock()
    db.get_all_cameras.return_value = []
    db.health_check.return_value = True
    return db

@pytest.fixture
async def redis_mock():
    """Mock Redis service"""
    redis = AsyncMock()
    redis.get_cache.return_value = None
    redis.set_cache.return_value = True
    return redis

# Base test class with common functionality
class BaseIntegrationTest:
    """Base class for integration tests"""
    
    @pytest.fixture(autouse=True)
    async def setup_services(self, mock_database, redis_mock):
        """Setup common services for tests"""
        self.db = mock_database
        self.redis = redis_mock
        
        # Setup service mocks
        self.services = {
            'database': self.db,
            'redis': self.redis
        }
    
    async def simulate_camera_stream(self, camera_id: str, frame_count: int = 10):
        """Simulate camera stream for testing"""
        frames = []
        for i in range(frame_count):
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            frames.append(frame)
            await asyncio.sleep(0.033)  # ~30 FPS
        return frames
```

#### Integration Test Suite
```python
# File: tests/integration/test_camera_lifecycle.py
import pytest
from tests.test_framework import BaseIntegrationTest

class TestCameraLifecycle(BaseIntegrationTest):
    """Test complete camera lifecycle"""
    
    @pytest.mark.asyncio
    async def test_camera_add_to_recording(self, mock_camera_config):
        """Test adding camera and starting recording"""
        # 1. Add camera via API
        camera_id = await self.db.add_camera(mock_camera_config)
        assert camera_id == mock_camera_config['camera_id']
        
        # 2. Verify camera in database
        camera = await self.db.get_camera(camera_id)
        assert camera is not None
        assert camera['name'] == mock_camera_config['name']
        
        # 3. Simulate recording service picking up camera
        # Mock recording service behavior
        recording_status = {
            'status': 'recording',
            'ffmpeg_pid': 12345,
            'started_at': datetime.utcnow()
        }
        await self.db.update_recording_status(camera_id, recording_status)
        
        # 4. Verify recording status
        camera_with_status = await self.db.get_camera(camera_id)
        assert camera_with_status['recording_status'] == 'recording'
        
        # 5. Simulate detection
        detection = {
            'camera_id': camera_id,
            'event_type': 'vehicle_detected',
            'confidence': 0.95,
            'object_class': 'car'
        }
        detection_id = await self.db.add_detection(detection)
        assert detection_id is not None
        
        # 6. Clean up
        await self.db.delete_camera(camera_id)
    
    @pytest.mark.asyncio
    async def test_multi_camera_concurrent_operations(self):
        """Test concurrent operations on multiple cameras"""
        camera_count = 10
        cameras = []
        
        # Add multiple cameras concurrently
        tasks = []
        for i in range(camera_count):
            config = {
                'camera_id': f'test_cam_{i:03d}',
                'name': f'Test Camera {i}',
                'ip_address': f'192.168.1.{100 + i}',
                'port': 554
            }
            tasks.append(self.db.add_camera(config))
            cameras.append(config)
        
        camera_ids = await asyncio.gather(*tasks)
        assert len(camera_ids) == camera_count
        
        # Simulate concurrent recording starts
        recording_tasks = []
        for camera_id in camera_ids:
            status = {
                'status': 'recording',
                'ffmpeg_pid': 12345 + i
            }
            recording_tasks.append(
                self.db.update_recording_status(camera_id, status)
            )
        
        await asyncio.gather(*recording_tasks)
        
        # Verify all cameras recording
        all_cameras = await self.db.get_all_cameras()
        recording_count = sum(
            1 for cam in all_cameras 
            if cam.get('recording_status') == 'recording'
        )
        assert recording_count == camera_count
```

#### Performance Testing
```python
# File: tests/performance/test_stream_performance.py
import time
import asyncio
import statistics
from tests.test_framework import BaseIntegrationTest

class TestStreamPerformance(BaseIntegrationTest):
    """Performance tests for stream processing"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_frame_processing_latency(self):
        """Test frame processing stays under 500ms"""
        latencies = []
        frame_count = 100
        
        for i in range(frame_count):
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            
            start_time = time.time()
            
            # Simulate processing pipeline
            # 1. Frame capture
            await asyncio.sleep(0.01)  # Simulate capture time
            
            # 2. Preprocessing
            await asyncio.sleep(0.02)  # Simulate preprocessing
            
            # 3. AI inference
            await asyncio.sleep(0.05)  # Simulate inference
            
            # 4. Post-processing
            await asyncio.sleep(0.01)  # Simulate post-processing
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to ms
            latencies.append(latency)
        
        # Analyze results
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        max_latency = max(latencies)
        
        print(f"\nLatency Stats:")
        print(f"Average: {avg_latency:.2f}ms")
        print(f"P95: {p95_latency:.2f}ms")
        print(f"Max: {max_latency:.2f}ms")
        
        # Assertions
        assert avg_latency < 200, f"Average latency {avg_latency}ms exceeds 200ms"
        assert p95_latency < 500, f"P95 latency {p95_latency}ms exceeds 500ms"
        assert max_latency < 1000, f"Max latency {max_latency}ms exceeds 1000ms"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_stream_handling(self):
        """Test handling multiple concurrent streams"""
        stream_count = 20
        frames_per_stream = 30
        
        async def process_stream(stream_id: int):
            """Simulate processing a single stream"""
            processing_times = []
            
            for frame_num in range(frames_per_stream):
                start_time = time.time()
                
                # Simulate frame processing
                await asyncio.sleep(0.033)  # ~30 FPS
                
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
            
            return {
                'stream_id': stream_id,
                'avg_time': statistics.mean(processing_times),
                'max_time': max(processing_times)
            }
        
        # Process all streams concurrently
        start_time = time.time()
        results = await asyncio.gather(*[
            process_stream(i) for i in range(stream_count)
        ])
        total_time = time.time() - start_time
        
        # Analyze results
        avg_times = [r['avg_time'] for r in results]
        overall_avg = statistics.mean(avg_times)
        
        print(f"\nConcurrent Stream Processing:")
        print(f"Streams: {stream_count}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Avg per frame: {overall_avg*1000:.2f}ms")
        
        # Should process 20 streams at 30 FPS
        expected_time = frames_per_stream / 30.0
        assert total_time < expected_time * 1.5  # Allow 50% overhead
```

### Validation Checkpoints

#### Phase Completion Criteria

##### Phase 1: Foundation Stabilization ✓
- [ ] Database schema deployed and tested
- [ ] All services use centralized database
- [ ] API v3 endpoints functional
- [ ] Service integration layer operational
- [ ] No hardcoded camera configurations

##### Phase 2: Stream Management ✓
- [ ] Connection pool handles 20+ cameras
- [ ] Retry logic prevents stream drops
- [ ] GPU acceleration operational
- [ ] Stream health monitoring active
- [ ] <100ms frame acquisition time

##### Phase 3: AI Pipeline ✓
- [ ] YOLOv8 TensorRT optimized
- [ ] Batch processing functional
- [ ] Detection latency <500ms
- [ ] 30+ FPS processing capability
- [ ] License plate detection accuracy >90%

##### Phase 4: Storage & Performance ✓
- [ ] TimescaleDB handling 10k events/sec
- [ ] Redis caching reduces DB load by >50%
- [ ] Data retention policies active
- [ ] Query response time <100ms
- [ ] Compression achieving >3:1 ratio

---

## Performance Optimization

### System-Wide Optimizations

#### 1. Database Query Optimization
```sql
-- Optimized queries with proper indexing
-- File: database/optimized_queries.sql

-- Fast camera status query
CREATE OR REPLACE VIEW camera_status_view AS
SELECT 
    c.camera_id,
    c.name,
    c.status,
    rs.recording_status,
    rs.ffmpeg_pid,
    rs.storage_used_mb,
    COUNT(DISTINCT DATE(d.created_at)) as days_with_detections,
    MAX(d.created_at) as last_detection
FROM cameras c
LEFT JOIN recording_status rs ON c.id = rs.camera_id
LEFT JOIN detection_events d ON c.id = d.camera_id 
    AND d.created_at > NOW() - INTERVAL '7 days'
GROUP BY c.camera_id, c.name, c.status, rs.recording_status, 
         rs.ffmpeg_pid, rs.storage_used_mb;

-- Materialized view for dashboard stats
CREATE MATERIALIZED VIEW dashboard_stats AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    camera_id,
    event_type,
    COUNT(*) as event_count,
    AVG(confidence) as avg_confidence
FROM detection_events
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour, camera_id, event_type;

-- Refresh every hour
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS void AS $
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_stats;
END;
$ LANGUAGE plpgsql;

-- Schedule refresh
SELECT cron.schedule('refresh-dashboard-stats', '0 * * * *', 'SELECT refresh_dashboard_stats();');
```

#### 2. Memory Management
```python
# File: optimization/memory_manager.py
import gc
import psutil
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    """System-wide memory management"""
    
    def __init__(self, max_memory_percent: float = 80.0):
        self.max_memory_percent = max_memory_percent
        self.monitoring = False
        self._monitor_task = None
    
    async def start_monitoring(self, interval: int = 60):
        """Start memory monitoring"""
        self.monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(interval)
        )
        logger.info("Memory monitoring started")
    
    async def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
    
    async def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                stats = self.get_memory_stats()
                
                if stats['percent'] > self.max_memory_percent:
                    logger.warning(
                        f"Memory usage high: {stats['percent']:.1f}%"
                    )
                    await self._reduce_memory_usage()
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        memory = psutil.virtual_memory()
        return {
            'total_mb': memory.total // (1024 * 1024),
            'available_mb': memory.available // (1024 * 1024),
            'used_mb': memory.used // (1024 * 1024),
            'percent': memory.percent,
            'swap_percent': psutil.swap_memory().percent
        }
    
    async def _reduce_memory_usage(self):
        """Attempt to reduce memory usage"""
        # Force garbage collection
        gc.collect()
        
        # Clear caches (implement cache clearing logic)
        # await self.clear_caches()
        
        # Log memory stats after cleanup
        stats_after = self.get_memory_stats()
        logger.info(
            f"Memory cleanup completed. Usage: {stats_after['percent']:.1f}%"
        )
    
    @staticmethod
    def optimize_numpy_arrays(array: np.ndarray) -> np.ndarray:
        """Optimize numpy array memory usage"""
        # Use smallest dtype that fits the data
        if array.dtype == np.float64:
            return array.astype(np.float32)
        elif array.dtype == np.int64:
            if array.max() < 2**31:
                return array.astype(np.int32)
            elif array.max() < 2**15:
                return array.astype(np.int16)
        return array
```

#### 3. Connection Pooling
```python
# File: optimization/connection_pools.py
from contextlib import asynccontextmanager
import aiohttp
import asyncpg
import aioredis
from typing import Optional

class ConnectionPools:
    """Centralized connection pool management"""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis_pool: Optional[aioredis.Redis] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self, config: Dict[str, Any]):
        """Initialize all connection pools"""
        # Database pool
        self.db_pool = await asyncpg.create_pool(
            config['database_url'],
            min_size=5,
            max_size=20,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
        
        # Redis pool
        self.redis_pool = await aioredis.from_url(
            config['redis_url'],
            max_connections=50,
            decode_responses=True
        )
        
        # HTTP session
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300
        )
        timeout = aiohttp.ClientTimeout(total=30)
        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
    
    async def close(self):
        """Close all connections"""
        if self.db_pool:
            await self.db_pool.close()
        
        if self.redis_pool:
            await self.redis_pool.close()
        
        if self.http_session:
            await self.http_session.close()
    
    @asynccontextmanager
    async def database(self):
        """Get database connection from pool"""
        async with self.db_pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def redis(self):
        """Get redis connection"""
        yield self.redis_pool
    
    @asynccontextmanager
    async def http(self):
        """Get HTTP session"""
        yield self.http_session
```

---

## Security Considerations

### Security Implementation Checklist

#### 1. Authentication & Authorization
```python
# File: security/auth_handler.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets

class AuthHandler:
    """Handle authentication and authorization"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, subject: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        
        to_encode = {
            "exp": expire,
            "sub": subject,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user"""
        token = credentials.credentials
        payload = self.decode_token(token)
        
        # Check if token is revoked (implement revocation check)
        # if await self.is_token_revoked(payload['jti']):
        #     raise HTTPException(status_code=401, detail="Token revoked")
        
        return payload['sub']

# Role-based access control
class RBACHandler:
    """Role-based access control"""
    
    def __init__(self):
        self.permissions = {
            'admin': ['*'],
            'operator': ['cameras.view', 'cameras.control', 'detections.view'],
            'viewer': ['cameras.view', 'detections.view']
        }
    
    def has_permission(self, role: str, permission: str) -> bool:
        """Check if role has permission"""
        if role not in self.permissions:
            return False
        
        role_perms = self.permissions[role]
        if '*' in role_perms:
            return True
        
        return permission in role_perms
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        def decorator(func):
            async def wrapper(*args, current_user: str = Depends(get_current_user), **kwargs):
                # Get user role (implement user role lookup)
                user_role = await get_user_role(current_user)
                
                if not self.has_permission(user_role, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator
```

#### 2. Input Validation & Sanitization
```python
# File: security/validators.py
from pydantic import BaseModel, validator, Field
from typing import Optional
import re
import ipaddress

class CameraInputValidator(BaseModel):
    """Validate camera input data"""
    
    name: str = Field(..., min_length=1, max_length=255)
    ip_address: str
    port: int = Field(..., ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=50)
    stream_path: str = Field(..., max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        """Validate camera name"""
        # Allow only alphanumeric, spaces, and basic punctuation
        if not re.match(r'^[\w\s\-\.]+, v):
            raise ValueError('Invalid camera name format')
        return v.strip()
    
    @validator('ip_address')
    def validate_ip(cls, v):
        """Validate IP address"""
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address')
        
        # Check for private IP ranges (security consideration)
        ip = ipaddress.ip_address(v)
        if not ip.is_private:
            # Log attempt to add public IP camera
            logger.warning(f"Attempt to add public IP camera: {v}")
        
        return v
    
    @validator('stream_path')
    def validate_stream_path(cls, v):
        """Validate stream path"""
        # Prevent path traversal
        if '..' in v or v.count('/') > 5:
            raise ValueError('Invalid stream path')
        
        # Must start with /
        if not v.startswith('/'):
            v = '/' + v
        
        return v

class DetectionFilterValidator(BaseModel):
    """Validate detection query parameters"""
    
    camera_id: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    event_type: Optional[str]
    min_confidence: float = Field(0.0, ge=0.0, le=1.0)
    limit: int = Field(100, ge=1, le=1000)
    
    @validator('camera_id')
    def validate_camera_id(cls, v):
        """Validate camera ID format"""
        if v and not re.match(r'^[a-zA-Z0-9_\-]+, v):
            raise ValueError('Invalid camera ID format')
        return v
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        """Validate time range"""
        if v and 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError('End time must be after start time')
            
            # Limit query range to prevent DoS
            max_range = timedelta(days=30)
            if v - values['start_time'] > max_range:
                raise ValueError('Time range cannot exceed 30 days')
        
        return v
```

#### 3. Secure Communication
```python
# File: security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionHandler:
    """Handle encryption for sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        if master_key:
            self.key = self._derive_key(master_key)
        else:
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt',  # Use proper salt in production
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_camera_credentials(self, username: str, password: str) -> Dict[str, str]:
        """Encrypt camera credentials"""
        return {
            'username': username,  # Username often needed in plain text
            'password': self.encrypt(password)
        }
    
    def decrypt_camera_credentials(self, encrypted_creds: Dict[str, str]) -> Dict[str, str]:
        """Decrypt camera credentials"""
        return {
            'username': encrypted_creds['username'],
            'password': self.decrypt(encrypted_creds['password'])
        }

# Stream encryption for video data
class StreamEncryption:
    """Handle video stream encryption"""
    
    @staticmethod
    def generate_stream_key() -> bytes:
        """Generate key for stream encryption"""
        return os.urandom(32)
    
    @staticmethod
    def encrypt_frame(frame: np.ndarray, key: bytes) -> bytes:
        """Encrypt video frame (simplified example)"""
        # In production, use proper video encryption like SRTP
        # This is a simplified example
        frame_bytes = frame.tobytes()
        # Implement actual encryption here
        return frame_bytes
```

---

## Deployment Strategy

### Production Deployment Guide

#### Docker Configuration
```yaml
# File: docker-compose.production.yml
version: '3.8'

services:
  # PostgreSQL with TimescaleDB
  postgres:
    image: timescale/timescaledb:latest-pg14
    container_name: surveillance_db
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: surveillance
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  # Redis
  redis:
    image: redis:7-alpine
    container_name: surveillance_redis
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  # API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: surveillance_api
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/surveillance
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
    volumes:
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
  
  # Stream Ingestion Service
  stream_ingestion:
    build:
      context: .
      dockerfile: Dockerfile.stream
    container_name: surveillance_stream
    runtime: nvidia
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/surveillance
      REDIS_URL: redis://redis:6379
      CUDA_VISIBLE_DEVICES: 0
    volumes:
      - ./recordings:/recordings
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  # AI Processing Service
  ai_processor:
    build:
      context: .
      dockerfile: Dockerfile.ai
    container_name: surveillance_ai
    runtime: nvidia
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/surveillance
      REDIS_URL: redis://redis:6379
      MODEL_PATH: /models/yolov8_tensorrt.engine
      CUDA_VISIBLE_DEVICES: 0
    volumes:
      - ./models:/models:ro
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: surveillance_nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
    restart: unless-stopped
  
  # Monitoring - Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: surveillance_prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped
  
  # Monitoring - Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: surveillance_grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### Kubernetes Deployment
```yaml
# File: kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: surveillance-api
  namespace: surveillance
spec:
  replicas: 3
  selector:
    matchLabels:
      app: surveillance-api
  template:
    metadata:
      labels:
        app: surveillance-api
    spec:
      containers:
      - name: api
        image: surveillance/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: surveillance-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: surveillance-config
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: surveillance-api
  namespace: surveillance
spec:
  selector:
    app: surveillance-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
# GPU-enabled AI processor
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: surveillance-ai-processor
  namespace: surveillance
spec:
  selector:
    matchLabels:
      app: surveillance-ai-processor
  template:
    metadata:
      labels:
        app: surveillance-ai-processor
    spec:
      nodeSelector:
        nvidia.com/gpu: "true"
      containers:
      - name: ai-processor
        image: surveillance/ai-processor:latest
        resources:
          limits:
            nvidia.com/gpu: 1
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: ai-models-pvc
```

#### CI/CD Pipeline
```yaml
# File: .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=./ --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ secrets.REGISTRY_URL }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    
    - name: Build and push API
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.api
        push: true
        tags: |
          ${{ secrets.REGISTRY_URL }}/surveillance/api:latest
          ${{ secrets.REGISTRY_URL }}/surveillance/api:${{ github.sha }}
        cache-from: type=registry,ref=${{ secrets.REGISTRY_URL }}/surveillance/api:buildcache
        cache-to: type=registry,ref=${{ secrets.REGISTRY_URL }}/surveillance/api:buildcache,mode=max
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v4
      with:
        manifests: |
          kubernetes/deployment.yaml
          kubernetes/service.yaml
        images: |
          ${{ secrets.REGISTRY_URL }}/surveillance/api:${{ github.sha }}
        namespace: surveillance
```

---

## Discussion Points & Recommendations

### 1. Camera Hardware Selection

For your Reolink cameras and scaling to 20+:

**Recommended Models:**
- **Reolink RLC-811A**: 4K, PoE, good night vision
- **Reolink RLC-822A**: 4K, 3x optical zoom, person/vehicle detection
- **Reolink RLC-1212A**: 12MP, wide angle, excellent for large areas

**Network Architecture:**
- Use VLANs to isolate camera traffic
- Implement QoS for video streams
- Plan for 100Mbps per 4K camera

### 2. Scaling Considerations

**4 Camera Setup (Initial)**
- Single server with RTX 3080 sufficient
- 32GB RAM minimum
- 10TB storage for 30-day retention

**20 Camera Setup (Growth)**
- Consider distributed architecture
- Add second GPU or upgrade to RTX 4090
- 64GB RAM recommended
- 50TB+ storage with NAS

**100+ Camera Setup (Future)**
- Kubernetes cluster with 3+ nodes
- Multiple GPU nodes
- Distributed storage (Ceph/GlusterFS)
- Load balancer for API traffic

### 3. Business Feature Priorities

Based on SMB needs, prioritize:

1. **Theft Detection** (Week 5-6)
   - Loitering detection
   - After-hours activity
   - Removed object detection

2. **Customer Analytics** (Week 11-12)
   - Foot traffic patterns
   - Queue management
   - Heat mapping

3. **Vehicle Analytics** (Week 11-12)
   - License plate logging
   - Parking duration
   - Repeat visitor tracking

### 4. Cost Optimization

**Hardware Costs:**
- Start with single server: ~$5,000
- Scale horizontally vs. vertically
- Use consumer GPUs (RTX) vs. datacenter (A100)

**Operational Costs:**
- Implement efficient video retention
- Use motion-triggered recording
- Compress older footage

### 5. Maintenance & Support

**Monitoring Setup:**
- Implement comprehensive logging
- Set up alerting for critical issues
- Create runbooks for common problems

**Update Strategy:**
- Blue-green deployments
- Scheduled maintenance windows
- Automatic backup before updates

### 6. Next Steps

1. **Week 1-2**: Complete Phase 1, test with your cameras
2. **Week 3-4**: Implement streaming, validate with 4 cameras
3. **Week 5-6**: Get basic AI detection working
4. **Week 7-8**: Focus on stability and performance
5. **Week 9-10**: Add monitoring and recovery
6. **Week 11-12**: Implement business-specific features
7. **Week 13-14**: Polish frontend
8. **Week 15-16**: Production deployment

This comprehensive guide provides everything needed to build a production-ready AI video surveillance system. The modular approach allows you to start small and scale as needed, while the detailed implementation examples eliminate guesswork for AI agents or developers implementing the system.