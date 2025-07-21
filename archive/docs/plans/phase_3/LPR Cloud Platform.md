# LPR Cloud Platform
## Architecture & Implementation Guide

**Version:** 1.0.0  
**Last Updated:** July 2025  
**Classification:** Cloud Platform Technical Documentation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Platform Architecture](#2-platform-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Design](#4-database-design)
5. [API Design & Implementation](#5-api-design--implementation)
6. [Device Management System](#6-device-management-system)
7. [Data Ingestion Pipeline](#7-data-ingestion-pipeline)
8. [Web Portal Implementation](#8-web-portal-implementation)
9. [Security Architecture](#9-security-architecture)
10. [Scalability & Performance](#10-scalability--performance)
11. [Deployment Strategy](#11-deployment-strategy)
12. [Monitoring & Analytics](#12-monitoring--analytics)

---

## 1. Executive Summary

The LPR Cloud Platform serves as the central hub for managing edge devices, collecting detection data, and providing analytics. Built with scalability and reliability in mind, it supports thousands of edge devices with millions of daily detections.

### Core Functions
- Device registration and management
- Real-time data ingestion from edge devices
- Analytics and reporting
- User management and access control
- API for third-party integrations

### Design Principles
- **API-First**: All functionality exposed via RESTful APIs
- **Scalable**: Horizontal scaling for all components
- **Secure**: Zero-trust security model
- **Resilient**: No single point of failure
- **Observable**: Comprehensive monitoring and logging

---

## 2. Platform Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Load Balancer                              │
│                        (AWS ALB / Nginx)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────────────┐         ┌─────────────────┐         ┌───────────────┐
│   API Gateway │         │   Web Portal    │         │  Static Assets│
│  (Kong/FastAPI)│         │    (Next.js)    │         │  (CloudFront) │
└───────────────┘         └─────────────────┘         └───────────────┘
        │                           │                           
        │     ┌─────────────────────┴─────────────────────┐
        │     │                                           │
┌───────────────────────────────────────────────────────────────────┐
│                        Service Layer                                │
├─────────────────┬─────────────────┬─────────────────┬────────────┤
│ Device Service  │  Sync Service   │ Analytics Service│ Auth Service│
└─────────────────┴─────────────────┴─────────────────┴────────────┘
        │                           │                    
┌───────────────────────────────────────────────────────────────────┐
│                         Data Layer                                  │
├─────────────────┬─────────────────┬─────────────────┬────────────┤
│   PostgreSQL    │     Redis       │   TimescaleDB   │     S3      │
│   (Primary DB)  │    (Cache)      │  (Time Series)  │  (Storage)  │
└─────────────────┴─────────────────┴─────────────────┴────────────┘
```

### 2.2 Component Overview

| Component | Purpose | Technology |
|-----------|---------|------------|
| API Gateway | Request routing, rate limiting | Kong or AWS API Gateway |
| Device Service | Device registration & management | FastAPI + PostgreSQL |
| Sync Service | Data ingestion from devices | FastAPI + Redis Queue |
| Analytics Service | Data processing & reporting | FastAPI + TimescaleDB |
| Auth Service | Authentication & authorization | FastAPI + JWT |
| Web Portal | User interface | Next.js + React |

---

## 3. Technology Stack

### 3.1 Backend Stack

```yaml
# Backend Technologies
language: Python 3.11+
framework: FastAPI
orm: SQLAlchemy 2.0
async: asyncio + aiohttp
validation: Pydantic
testing: pytest + pytest-asyncio

# Databases
primary: PostgreSQL 15
cache: Redis 7
timeseries: TimescaleDB
search: Elasticsearch (optional)

# Message Queue
queue: Redis + RQ or Celery
streaming: Apache Kafka (for scale)

# Infrastructure
container: Docker
orchestration: Kubernetes
ci/cd: GitHub Actions + ArgoCD
monitoring: Prometheus + Grafana
logging: ELK Stack or Loki
```

### 3.2 Frontend Stack

```yaml
# Frontend Technologies
framework: Next.js 14
ui_library: React 18
styling: Tailwind CSS
components: shadcn/ui
state: Zustand or Redux Toolkit
charts: Recharts
maps: Mapbox GL
forms: React Hook Form + Zod
```

---

## 4. Database Design

### 4.1 PostgreSQL Schema

```sql
-- Organizations (customers)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    organization_id UUID REFERENCES organizations(id),
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Devices
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(50) UNIQUE NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    location_name VARCHAR(255),
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    device_type VARCHAR(50),
    firmware_version VARCHAR(50),
    capabilities JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    api_key VARCHAR(255) UNIQUE,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    metadata JSONB
);

-- Detections (partitioned by month)
CREATE TABLE detections (
    id UUID DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id),
    detection_id VARCHAR(100),
    plate_text VARCHAR(20) NOT NULL,
    confidence DECIMAL(3, 2),
    state VARCHAR(2),
    detection_time TIMESTAMP NOT NULL,
    sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    camera_id VARCHAR(50),
    bbox JSONB,
    metadata JSONB,
    PRIMARY KEY (id, detection_time)
) PARTITION BY RANGE (detection_time);

-- Create monthly partitions
CREATE TABLE detections_2025_01 PARTITION OF detections
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Indexes
CREATE INDEX idx_detections_device_time ON detections(device_id, detection_time DESC);
CREATE INDEX idx_detections_plate_text ON detections(plate_text);
CREATE INDEX idx_detections_sync_time ON detections(sync_time);

-- Allowlist/Blocklist
CREATE TABLE plate_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    plate_text VARCHAR(20) NOT NULL,
    list_type VARCHAR(20) CHECK (list_type IN ('allow', 'block')),
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(organization_id, plate_text, list_type)
);

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    device_id UUID REFERENCES devices(id),
    detection_id UUID,
    alert_type VARCHAR(50),
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(255),
    description TEXT,
    metadata JSONB
);

-- API Keys for third-party integrations
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    permissions JSONB,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### 4.2 TimescaleDB Schema (Analytics)

```sql
-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Device metrics
CREATE TABLE device_metrics (
    time TIMESTAMPTZ NOT NULL,
    device_id UUID NOT NULL,
    cpu_percent DECIMAL(5,2),
    memory_percent DECIMAL(5,2),
    disk_percent DECIMAL(5,2),
    temperature DECIMAL(5,2),
    detections_count INTEGER,
    sync_queue_size INTEGER,
    network_latency_ms INTEGER
);

-- Convert to hypertable
SELECT create_hypertable('device_metrics', 'time');

-- Detection analytics
CREATE TABLE detection_analytics (
    time TIMESTAMPTZ NOT NULL,
    organization_id UUID NOT NULL,
    device_id UUID NOT NULL,
    hour_bucket TIMESTAMPTZ NOT NULL,
    total_detections INTEGER,
    unique_plates INTEGER,
    avg_confidence DECIMAL(3,2),
    processing_time_p50 DECIMAL(6,2),
    processing_time_p95 DECIMAL(6,2),
    processing_time_p99 DECIMAL(6,2)
);

SELECT create_hypertable('detection_analytics', 'time');

-- Continuous aggregates for real-time analytics
CREATE MATERIALIZED VIEW hourly_detection_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS hour,
    device_id,
    COUNT(*) as detection_count,
    AVG(confidence) as avg_confidence,
    COUNT(DISTINCT plate_text) as unique_plates
FROM detections
GROUP BY hour, device_id;
```

---

## 5. API Design & Implementation

### 5.1 API Structure

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, devices, sync, analytics, organizations

app = FastAPI(
    title="LPR Cloud Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
```

### 5.2 Device Registration API

```python
# app/api/devices.py
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Device
from app.schemas import DeviceRegistration, DeviceResponse
from app.services.device_service import DeviceService
from app.dependencies import get_db, get_current_organization

router = APIRouter()

@router.post("/register", response_model=DeviceResponse, status_code=201)
async def register_device(
    registration: DeviceRegistration,
    organization_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Register a new edge device"""
    device_service = DeviceService(db)
    
    # Validate registration token
    if not await device_service.validate_registration_token(
        registration.registration_token, organization_id
    ):
        raise HTTPException(status_code=403, detail="Invalid registration token")
    
    # Check if device already exists
    existing = await device_service.get_device_by_id(registration.device_id)
    if existing:
        raise HTTPException(status_code=409, detail="Device already registered")
    
    # Create device
    device = await device_service.create_device(
        device_id=registration.device_id,
        organization_id=organization_id,
        device_type=registration.device_type,
        capabilities=registration.capabilities,
        location=registration.location
    )
    
    # Generate API key
    api_key = await device_service.generate_api_key(device.id)
    
    return DeviceResponse(
        device_id=device.device_id,
        api_key=api_key,
        endpoint=f"https://api.lprcloud.com/api/v1/sync",
        sync_interval=300,
        features={
            "immediate_sync": True,
            "batch_sync": True,
            "compression": True
        }
    )

@router.get("/validate", status_code=200)
async def validate_device(
    x_device_id: str = Header(...),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """Validate device credentials"""
    device_service = DeviceService(db)
    
    if not await device_service.validate_api_key(x_device_id, x_api_key):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last seen
    await device_service.update_last_seen(x_device_id)
    
    return {"status": "valid", "device_id": x_device_id}

@router.get("/{device_id}/status")
async def get_device_status(
    device_id: str,
    organization_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get device status and health metrics"""
    device_service = DeviceService(db)
    
    device = await device_service.get_device_with_metrics(device_id, organization_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "device_id": device.device_id,
        "status": device.status,
        "last_seen": device.last_seen,
        "location": device.location_name,
        "health": {
            "cpu_usage": device.latest_cpu_percent,
            "memory_usage": device.latest_memory_percent,
            "disk_usage": device.latest_disk_percent,
            "temperature": device.latest_temperature
        },
        "statistics": {
            "total_detections_today": device.detections_today,
            "sync_queue_size": device.sync_queue_size,
            "last_sync": device.last_sync_time
        }
    }
```

### 5.3 Data Sync API

```python
# app/api/sync.py
from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from app.schemas import SyncPayload, SyncResponse
from app.services.sync_service import SyncService
from app.dependencies import get_db, validate_device_auth
import gzip
import json

router = APIRouter()

@router.post("/detection", response_model=SyncResponse)
async def sync_detections(
    payload: SyncPayload,
    background_tasks: BackgroundTasks,
    device_id: str = Depends(validate_device_auth),
    db: AsyncSession = Depends(get_db)
):
    """Receive detection data from edge devices"""
    sync_service = SyncService(db)
    
    # Process sync payload
    result = await sync_service.process_detection_sync(
        device_id=device_id,
        items=payload.items
    )
    
    # Queue background processing
    for item in payload.items:
        background_tasks.add_task(
            process_detection_analytics,
            device_id,
            item
        )
    
    return SyncResponse(
        accepted=result.accepted_count,
        rejected=result.rejected_count,
        errors=result.errors
    )

@router.post("/batch")
async def sync_batch(
    background_tasks: BackgroundTasks,
    device_id: str = Depends(validate_device_auth),
    content_encoding: str = Header(None),
    db: AsyncSession = Depends(get_db),
    request: Request
):
    """Handle batch sync with optional compression"""
    sync_service = SyncService(db)
    
    # Read body
    body = await request.body()
    
    # Decompress if needed
    if content_encoding == "gzip":
        body = gzip.decompress(body)
    
    # Parse payload
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Process each item type
    results = {}
    for item_type, items in data.items():
        if item_type == "detections":
            result = await sync_service.process_detection_sync(device_id, items)
        elif item_type == "health":
            result = await sync_service.process_health_sync(device_id, items)
        elif item_type == "logs":
            result = await sync_service.process_log_sync(device_id, items)
        else:
            continue
            
        results[item_type] = {
            "accepted": result.accepted_count,
            "rejected": result.rejected_count
        }
        
        # Queue analytics processing
        background_tasks.add_task(
            process_batch_analytics,
            device_id,
            item_type,
            items
        )
    
    return results
```

---

## 6. Device Management System

### 6.1 Device Service Implementation

```python
# app/services/device_service.py
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Device, Organization

class DeviceService:
    """Manages device lifecycle and operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_device(
        self,
        device_id: str,
        organization_id: str,
        device_type: str,
        capabilities: dict,
        location: dict
    ) -> Device:
        """Create a new device"""
        device = Device(
            device_id=device_id,
            organization_id=organization_id,
            device_type=device_type,
            capabilities=capabilities,
            location_name=location.get("name"),
            location_lat=location.get("lat"),
            location_lng=location.get("lng"),
            status="pending"
        )
        
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        
        return device
    
    async def generate_api_key(self, device_id: str) -> str:
        """Generate API key for device"""
        # Generate secure random key
        raw_key = secrets.token_urlsafe(32)
        
        # Hash for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Update device with key hash
        await self.db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(
                api_key=key_hash,
                status="active",
                activated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Return raw key (only shown once)
        return raw_key
    
    async def validate_api_key(self, device_id: str, api_key: str) -> bool:
        """Validate device API key"""
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Check against database
        result = await self.db.execute(
            select(Device)
            .where(
                Device.device_id == device_id,
                Device.api_key == key_hash,
                Device.status == "active"
            )
        )
        
        device = result.scalar_one_or_none()
        return device is not None
    
    async def get_organization_devices(
        self,
        organization_id: str,
        status: Optional[str] = None
    ) -> List[Device]:
        """Get all devices for an organization"""
        query = select(Device).where(Device.organization_id == organization_id)
        
        if status:
            query = query.where(Device.status == status)
            
        result = await self.db.execute(query.order_by(Device.created_at.desc()))
        return result.scalars().all()
    
    async def update_device_status(
        self,
        device_id: str,
        status: str,
        metadata: Optional[dict] = None
    ):
        """Update device status"""
        values = {"status": status, "updated_at": datetime.utcnow()}
        
        if metadata:
            values["metadata"] = metadata
            
        await self.db.execute(
            update(Device)
            .where(Device.device_id == device_id)
            .values(**values)
        )
        await self.db.commit()
    
    async def deactivate_device(self, device_id: str, organization_id: str):
        """Deactivate a device"""
        await self.db.execute(
            update(Device)
            .where(
                Device.device_id == device_id,
                Device.organization_id == organization_id
            )
            .values(
                status="inactive",
                api_key=None,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
```

### 6.2 Device Monitoring

```python
# app/services/device_monitor.py
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from app.models import Device, DeviceMetrics
import logging

logger = logging.getLogger(__name__)

class DeviceMonitor:
    """Monitors device health and connectivity"""
    
    def __init__(self, db_session_factory):
        self.db_factory = db_session_factory
        self.running = False
        
    async def start(self):
        """Start monitoring tasks"""
        self.running = True
        asyncio.create_task(self._monitor_device_health())
        asyncio.create_task(self._check_offline_devices())
        logger.info("Device monitor started")
    
    async def _monitor_device_health(self):
        """Monitor device health metrics"""
        while self.running:
            try:
                async with self.db_factory() as db:
                    # Get active devices
                    result = await db.execute(
                        select(Device).where(Device.status == "active")
                    )
                    devices = result.scalars().all()
                    
                    for device in devices:
                        # Check last metrics
                        metrics = await self._get_latest_metrics(db, device.id)
                        
                        if metrics:
                            # Check for anomalies
                            await self._check_anomalies(db, device, metrics)
                            
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def _check_offline_devices(self):
        """Check for devices that haven't reported"""
        while self.running:
            try:
                async with self.db_factory() as db:
                    # Find devices offline for >10 minutes
                    cutoff = datetime.utcnow() - timedelta(minutes=10)
                    
                    result = await db.execute(
                        select(Device).where(
                            Device.status == "active",
                            Device.last_seen < cutoff
                        )
                    )
                    
                    offline_devices = result.scalars().all()
                    
                    for device in offline_devices:
                        await self._handle_offline_device(db, device)
                        
            except Exception as e:
                logger.error(f"Offline check error: {e}")
                
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_anomalies(self, db, device, metrics):
        """Check for anomalous metrics"""
        alerts = []
        
        # High CPU usage
        if metrics.cpu_percent > 90:
            alerts.append({
                "type": "high_cpu",
                "severity": "high",
                "value": metrics.cpu_percent
            })
            
        # High memory usage
        if metrics.memory_percent > 85:
            alerts.append({
                "type": "high_memory",
                "severity": "medium",
                "value": metrics.memory_percent
            })
            
        # High temperature
        if metrics.temperature and metrics.temperature > 75:
            alerts.append({
                "type": "high_temperature",
                "severity": "critical",
                "value": metrics.temperature
            })
            
        # Create alerts
        for alert_data in alerts:
            await self._create_alert(db, device, alert_data)
    
    async def _handle_offline_device(self, db, device):
        """Handle offline device"""
        # Update status
        device.status = "offline"
        
        # Create alert
        await self._create_alert(db, device, {
            "type": "device_offline",
            "severity": "high",
            "description": f"Device has been offline since {device.last_seen}"
        })
        
        await db.commit()
        logger.warning(f"Device {device.device_id} marked as offline")
```

---

## 7. Data Ingestion Pipeline

### 7.1 High-Performance Ingestion

```python
# app/services/ingestion_service.py
import asyncio
from typing import List, Dict
import aiokafka
from app.models import Detection
from app.services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)

class IngestionService:
    """High-performance data ingestion pipeline"""
    
    def __init__(self, config):
        self.config = config
        self.kafka_producer = None
        self.batch_queue = asyncio.Queue(maxsize=1000)
        self.workers = []
        
    async def start(self):
        """Start ingestion pipeline"""
        # Initialize Kafka producer for high volume
        if self.config.use_kafka:
            self.kafka_producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=self.config.kafka_brokers,
                value_serializer=lambda v: json.dumps(v).encode()
            )
            await self.kafka_producer.start()
        
        # Start worker pool
        for i in range(self.config.worker_count):
            worker = asyncio.create_task(self._process_worker(i))
            self.workers.append(worker)
            
        logger.info(f"Ingestion pipeline started with {self.config.worker_count} workers")
    
    async def ingest_detection(self, device_id: str, detection_data: Dict):
        """Ingest a single detection"""
        # Add to processing queue
        await self.batch_queue.put({
            "device_id": device_id,
            "data": detection_data,
            "timestamp": datetime.utcnow()
        })
        
        # Send to Kafka for stream processing if enabled
        if self.kafka_producer:
            await self.kafka_producer.send(
                "detections",
                value={
                    "device_id": device_id,
                    "detection": detection_data
                }
            )
    
    async def _process_worker(self, worker_id: int):
        """Worker to process detection queue"""
        batch = []
        
        while True:
            try:
                # Collect batch
                while len(batch) < self.config.batch_size:
                    try:
                        item = await asyncio.wait_for(
                            self.batch_queue.get(),
                            timeout=1.0
                        )
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break
                
                # Process batch if we have items
                if batch:
                    await self._process_batch(batch)
                    batch = []
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, batch: List[Dict]):
        """Process a batch of detections"""
        async with self.db_factory() as db:
            # Bulk insert detections
            detections = []
            for item in batch:
                detection = Detection(
                    device_id=item["device_id"],
                    detection_id=item["data"]["detection_id"],
                    plate_text=item["data"]["plate_text"],
                    confidence=item["data"]["confidence"],
                    state=item["data"].get("state"),
                    detection_time=item["data"]["timestamp"],
                    sync_time=item["timestamp"],
                    bbox=item["data"].get("box"),
                    metadata=item["data"].get("metadata", {})
                )
                detections.append(detection)
            
            db.add_all(detections)
            await db.commit()
            
            # Update analytics
            analytics = AnalyticsService(db)
            await analytics.update_detection_stats(detections)
            
            logger.info(f"Processed batch of {len(batch)} detections")
```

### 7.2 Stream Processing (Optional)

```python
# app/services/stream_processor.py
import faust
from datetime import timedelta

app = faust.App(
    'lpr-stream-processor',
    broker='kafka://localhost:9092',
    store='rocksdb://',
    topic_partitions=8
)

# Detection topic
detection_topic = app.topic('detections', value_type=Detection)

# Tables for aggregation
device_stats = app.Table(
    'device_stats',
    default=lambda: {"count": 0, "plates": set()},
    on_window_close=lambda key, value: print(f"Window closed for {key}: {value}")
)

# Tumbling window for hourly stats
@app.agent(detection_topic)
async def process_detections(detections):
    async for detection in detections.group_by(
        Detection.device_id,
        window=timedelta(hours=1)
    ):
        # Update device statistics
        device_stats[detection.device_id]["count"] += 1
        device_stats[detection.device_id]["plates"].add(detection.plate_text)
        
        # Check for alerts
        if detection.confidence < 0.5:
            await low_confidence_alert.send(value=detection)
        
        # Update real-time dashboard
        await update_dashboard(detection)

# Alert topics
low_confidence_alert = app.topic('alerts.low_confidence')
repeated_plate_alert = app.topic('alerts.repeated_plate')

@app.timer(interval=60.0)  # Every minute
async def report_stats():
    """Report aggregated statistics"""
    for device_id, stats in device_stats.items():
        print(f"Device {device_id}: {stats['count']} detections, "
              f"{len(stats['plates'])} unique plates")
```

---

## 8. Web Portal Implementation

### 8.1 Next.js Application Structure

```typescript
// Frontend structure
app/
├── (auth)/
│   ├── login/
│   ├── register/
│   └── layout.tsx
├── (dashboard)/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── devices/
│   │   ├── page.tsx
│   │   └── [id]/
│   │       └── page.tsx
│   ├── detections/
│   │   └── page.tsx
│   ├── analytics/
│   │   └── page.tsx
│   └── settings/
│       └── page.tsx
├── api/
│   └── [...route].ts
└── components/
    ├── ui/
    ├── dashboard/
    └── devices/
```

### 8.2 Dashboard Component

```typescript
// app/components/dashboard/Dashboard.tsx
'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DeviceMap } from '@/components/devices/DeviceMap';
import { DetectionChart } from '@/components/analytics/DetectionChart';
import { RealtimeDetections } from '@/components/detections/RealtimeDetections';
import { useWebSocket } from '@/hooks/useWebSocket';
import { api } from '@/lib/api';

export function Dashboard() {
  const [stats, setStats] = useState({
    totalDevices: 0,
    activeDevices: 0,
    todayDetections: 0,
    uniquePlates: 0
  });
  
  const [devices, setDevices] = useState([]);
  
  // WebSocket for real-time updates
  const { data: realtimeData } = useWebSocket('/ws/dashboard');
  
  useEffect(() => {
    // Load initial data
    loadDashboardData();
  }, []);
  
  useEffect(() => {
    // Handle real-time updates
    if (realtimeData) {
      if (realtimeData.type === 'detection') {
        // Update detection count
        setStats(prev => ({
          ...prev,
          todayDetections: prev.todayDetections + 1
        }));
      }
    }
  }, [realtimeData]);
  
  async function loadDashboardData() {
    try {
      const [statsRes, devicesRes] = await Promise.all([
        api.get('/analytics/summary'),
        api.get('/devices')
      ]);
      
      setStats(statsRes.data);
      setDevices(devicesRes.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Total Devices
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalDevices}</div>
            <p className="text-xs text-muted-foreground">
              {stats.activeDevices} active
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Today's Detections
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.todayDetections.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.uniquePlates} unique plates
            </p>
          </CardContent>
        </Card>
        
        {/* More stat cards... */}
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Map */}
        <Card>
          <CardHeader>
            <CardTitle>Device Locations</CardTitle>
          </CardHeader>
          <CardContent>
            <DeviceMap devices={devices} className="h-[400px]" />
          </CardContent>
        </Card>
        
        {/* Detection Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>Detection Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <DetectionChart className="h-[400px]" />
          </CardContent>
        </Card>
      </div>
      
      {/* Real-time Feed */}
      <Card>
        <CardHeader>
          <CardTitle>Live Detections</CardTitle>
        </CardHeader>
        <CardContent>
          <RealtimeDetections />
        </CardContent>
      </Card>
    </div>
  );
}
```

### 8.3 Device Management Interface

```typescript
// app/components/devices/DeviceList.tsx
'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MoreVertical, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { api } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

export function DeviceList() {
  const { data: devices, isLoading, refetch } = useQuery({
    queryKey: ['devices'],
    queryFn: () => api.get('/devices').then(res => res.data)
  });
  
  const deactivateMutation = useMutation({
    mutation# LPR Cloud Platform
## Architecture & Implementation Guide

**Version:** 1.0.0  
**Last Updated:** January 2025  
**Classification:** Cloud Platform Technical Documentation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Platform Architecture](#2-platform-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Design](#4-database-design)
5. [API Design & Implementation](#5-api-design--implementation)
6. [Device Management System](#6-device-management-system)
7. [Data Ingestion Pipeline](#7-data-ingestion-pipeline)
8. [Web Portal Implementation](#8-web-portal-implementation)
9. [Security Architecture](#9-security-architecture)
10. [Scalability & Performance](#10-scalability--performance)
11. [Deployment Strategy](#11-deployment-strategy)
12. [Monitoring & Analytics](#12-monitoring--analytics)

---

## 1. Executive Summary

The LPR Cloud Platform serves as the central hub for managing edge devices, collecting detection data, and providing analytics. Built with scalability and reliability in mind, it supports thousands of edge devices with millions of daily detections.

### Core Functions
- Device registration and management
- Real-time data ingestion from edge devices
- Analytics and reporting
- User management and access control
- API for third-party integrations

### Design Principles
- **API-First**: All functionality exposed via RESTful APIs
- **Scalable**: Horizontal scaling for all components
- **Secure**: Zero-trust security model
- **Resilient**: No single point of failure
- **Observable**: Comprehensive monitoring and logging

---

## 2. Platform Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Load Balancer                              │
│                        (AWS ALB / Nginx)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────────────┐         ┌─────────────────┐         ┌───────────────┐
│   API Gateway │         │   Web Portal    │         │  Static Assets│
│  (Kong/FastAPI)│         │    (Next.js)    │         │  (CloudFront) │
└───────────────┘         └─────────────────┘         └───────────────┘
        │                           │                           
        │     ┌─────────────────────┴─────────────────────┐
        │     │                                           │
┌───────────────────────────────────────────────────────────────────┐
│                        Service Layer                                │
├─────────────────┬─────────────────┬─────────────────┬────────────┤
│ Device Service  │  Sync Service   │ Analytics Service│ Auth Service│
└─────────────────┴─────────────────┴─────────────────┴────────────┘
        │                           │                    
┌───────────────────────────────────────────────────────────────────┐
│                         Data Layer                                  │
├─────────────────┬─────────────────┬─────────────────┬────────────┤
│   PostgreSQL    │     Redis       │   TimescaleDB   │     S3      │
│   (Primary DB)  │    (Cache)      │  (Time Series)  │  (Storage)  │
└─────────────────┴─────────────────┴─────────────────┴────────────┘
```

### 2.2 Component Overview

| Component | Purpose | Technology |
|-----------|---------|------------|
| API Gateway | Request routing, rate limiting | Kong or AWS API Gateway |
| Device Service | Device registration & management | FastAPI + PostgreSQL |
| Sync Service | Data ingestion from devices | FastAPI + Redis Queue |
| Analytics Service | Data processing & reporting | FastAPI + TimescaleDB |
| Auth Service | Authentication & authorization | FastAPI + JWT |
| Web Portal | User interface | Next.js + React |

---

## 3. Technology Stack

### 3.1 Backend Stack

```yaml
# Backend Technologies
language: Python 3.11+
framework: FastAPI
orm: SQLAlchemy 2.0
async: asyncio + aiohttp
validation: Pydantic
testing: pytest + pytest-asyncio

# Databases
primary: PostgreSQL 15
cache: Redis 7
timeseries: TimescaleDB
search: Elasticsearch (optional)

# Message Queue
queue: Redis + RQ or Celery
streaming: Apache Kafka (for scale)

# Infrastructure
container: Docker
orchestration: Kubernetes
ci/cd: GitHub Actions + ArgoCD
monitoring: Prometheus + Grafana
logging: ELK Stack or Loki
```

### 3.2 Frontend Stack

```yaml
# Frontend Technologies
framework: Next.js 14
ui_library: React 18
styling: Tailwind CSS
components: shadcn/ui
state: Zustand or Redux Toolkit
charts: Recharts
maps: Mapbox GL
forms: React Hook Form + Zod
```

---

## 4. Database Design

### 4.1 PostgreSQL Schema

```sql
-- Organizations (customers)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    organization_id UUID REFERENCES organizations(id),
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Devices
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(50) UNIQUE NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    location_name VARCHAR(255),
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    device_type VARCHAR(50),
    firmware_version VARCHAR(50),
    capabilities JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    api_key VARCHAR(255) UNIQUE,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    metadata JSONB
);

-- Detections (partitioned by month)
CREATE TABLE detections (
    id UUID DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id),
    detection_id VARCHAR(100),
    plate_text VARCHAR(20) NOT NULL,
    confidence DECIMAL(3, 2),
    state VARCHAR(2),
    detection_time TIMESTAMP NOT NULL,
    sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    camera_id VARCHAR(50),
    bbox JSONB,
    metadata JSONB,
    PRIMARY KEY (id, detection_time)
) PARTITION BY RANGE (detection_time);

-- Create monthly partitions
CREATE TABLE detections_2025_01 PARTITION OF detections
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Indexes
CREATE INDEX idx_detections_device_time ON detections(device_id, detection_time DESC);
CREATE INDEX idx_detections_plate_text ON detections(plate_text);
CREATE INDEX idx_detections_sync_time ON detections(sync_time);

-- Allowlist/Blocklist
CREATE TABLE plate_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    plate_text VARCHAR(20) NOT NULL,
    list_type VARCHAR(20) CHECK (list_type IN ('allow', 'block')),
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(organization_id, plate_text, list_type)
);

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    device_id UUID REFERENCES devices(id),
    detection_id UUID,
    alert_type VARCHAR(50),
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(255),
    description TEXT,
    metadata JSONB,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys for third-party integrations
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    permissions JSONB,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);