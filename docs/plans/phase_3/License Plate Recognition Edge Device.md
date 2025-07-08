# License Plate Recognition Edge Device
## Implementation Guide & Technical Documentation

**Version:** 2.0.0  
**Last Updated:** July 2025  
**Classification:** Technical Implementation Document

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Implementation Roadmap](#3-implementation-roadmap)
4. [Technical Requirements](#4-technical-requirements)
5. [Core Components Implementation](#5-core-components-implementation)
6. [Data Models & Storage](#6-data-models--storage)
7. [Sync Service Implementation](#7-sync-service-implementation)
8. [Security Implementation](#8-security-implementation)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment Guide](#10-deployment-guide)
11. [Monitoring & Maintenance](#11-monitoring--maintenance)
12. [API Reference](#12-api-reference)

---

## 1. Executive Summary

The License Plate Recognition (LPR) Edge Device is a local-first system designed for real-time vehicle identification with cloud synchronization capabilities. This document outlines the implementation steps for transforming the current standalone detection system into a production-ready edge device with enterprise features.

### Key Objectives
- Implement local SQLite storage for offline operation
- Add device registration and authentication
- Build asynchronous cloud synchronization
- Ensure data integrity and security
- Maintain sub-100ms detection latency

### Success Metrics
- 99.9% uptime for local detection
- <100ms detection latency
- 100% data synchronization when connected
- Zero data loss during offline periods

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Edge Device (Local)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Camera    │  │ LPR Service  │  │  Sync Service    │  │
│  │  Interface  │──│  (Detection) │──│ (Cloud Upload)   │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│         │                 │                    │            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Local SQLite Database                   │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │ Detections │  │ Sync Queue │  │ Device Config│  │  │
│  │  └────────────┘  └────────────┘  └──────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/TLS
                              ▼
                    ┌─────────────────┐
                    │  Cloud Platform  │
                    └─────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility | Priority |
|-----------|---------------|----------|
| LPR Service | Real-time detection and recognition | P0 |
| Local Storage | SQLite database for offline operation | P0 |
| Sync Service | Asynchronous cloud synchronization | P1 |
| Device Manager | Registration and authentication | P1 |
| Health Monitor | System health and diagnostics | P2 |

---

## 3. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Implement SQLite data models
- [ ] Add local storage service
- [ ] Create device configuration system
- [ ] Update detection service for local persistence

### Phase 2: Synchronization (Week 3-4)
- [ ] Build sync queue mechanism
- [ ] Implement retry logic with exponential backoff
- [ ] Add batch upload capabilities
- [ ] Create conflict resolution strategy

### Phase 3: Security & Auth (Week 5)
- [ ] Implement device registration flow
- [ ] Add API key management
- [ ] Encrypt sensitive local data
- [ ] Set up secure cloud communication

### Phase 4: Production Hardening (Week 6)
- [ ] Add comprehensive error handling
- [ ] Implement health monitoring
- [ ] Create deployment automation
- [ ] Performance optimization

---

## 4. Technical Requirements

### 4.1 Hardware Requirements

**Minimum Specifications:**
- CPU: ARM Cortex-A53 (4 cores) or equivalent
- RAM: 4GB
- Storage: 32GB (with 16GB available)
- Camera: 1080p capable
- Network: Ethernet or WiFi

**Recommended Specifications:**
- Platform: NVIDIA Jetson Nano or Raspberry Pi 4
- RAM: 8GB
- Storage: 64GB SSD
- Camera: 1080p with infrared capability

### 4.2 Software Dependencies

```toml
# requirements.txt additions
sqlalchemy==2.0.23
alembic==1.13.0
aiosqlite==0.19.0
cryptography==41.0.7
aiohttp==3.9.1
asyncio-mqtt==0.16.2
psutil==5.9.6
netifaces==0.11.0
```

---

## 5. Core Components Implementation

### 5.1 Project Structure Update

```
plate_recognition/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── detection.py      # NEW: Detection model
│   │   ├── sync_queue.py     # NEW: Sync queue model
│   │   └── device.py         # NEW: Device config model
│   ├── services/
│   │   ├── storage_service.py    # UPDATE: Add SQLite support
│   │   ├── sync_service.py       # NEW: Cloud sync service
│   │   └── device_service.py     # NEW: Device management
│   ├── db/
│   │   ├── __init__.py          # NEW: Database setup
│   │   └── migrations/          # NEW: Alembic migrations
│   └── config/
│       └── settings.py          # UPDATE: Add sync settings
├── data/
│   ├── local_lpr.db            # SQLite database
│   └── device_config.json      # Device configuration
└── scripts/
    ├── init_db.py              # NEW: Database initialization
    └── device_setup.py         # NEW: Device setup script
```

### 5.2 Database Models

```python
# app/models/detection.py
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Detection(Base):
    __tablename__ = 'detections'
    
    id = Column(String, primary_key=True)
    plate_text = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    state = Column(String(2))
    
    # Bounding box coordinates
    box_x1 = Column(Integer)
    box_y1 = Column(Integer)
    box_x2 = Column(Integer)
    box_y2 = Column(Integer)
    
    # Metadata
    camera_id = Column(String, default='main')
    frame_id = Column(Integer)
    detection_time = Column(DateTime, default=datetime.utcnow, index=True)
    processing_time_ms = Column(Float)
    
    # Raw data for debugging
    raw_text = Column(String)
    ocr_results = Column(JSON)
    
    # Sync status
    synced = Column(Boolean, default=False, index=True)
    sync_attempts = Column(Integer, default=0)
    last_sync_attempt = Column(DateTime)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_detection_time_synced', 'detection_time', 'synced'),
        Index('idx_plate_text_time', 'plate_text', 'detection_time'),
    )
```

```python
# app/models/sync_queue.py
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum
import enum

class SyncStatus(enum.Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"
    RETRY = "retry"

class SyncQueue(Base):
    __tablename__ = 'sync_queue'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(String, nullable=False)
    item_type = Column(String, nullable=False)  # 'detection', 'health', 'logs'
    
    # Sync metadata
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING, index=True)
    priority = Column(Integer, default=0)  # Higher = more important
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    
    # Payload
    data = Column(JSON, nullable=False)
    compressed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    next_retry_at = Column(DateTime)
    synced_at = Column(DateTime)
    
    # Error tracking
    last_error = Column(String)
    error_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_sync_status_priority', 'status', 'priority'),
        Index('idx_next_retry', 'next_retry_at', 'status'),
    )
```

### 5.3 Updated Storage Service

```python
# app/services/storage_service.py
import asyncio
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """Local SQLite storage service with sync queue integration"""
    
    def __init__(self, config):
        self.config = config
        self.engine = None
        self.async_session = None
        
    async def initialize(self):
        """Initialize database connection"""
        # Create async engine
        self.engine = create_async_engine(
            self.config.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5
        )
        
        # Create session factory
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables if they don't exist
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Storage service initialized")
    
    async def save_detection(self, detection_data: Dict) -> str:
        """Save detection to local database and add to sync queue"""
        async with self.async_session() as session:
            try:
                # Create detection record
                detection = Detection(
                    id=detection_data['detection_id'],
                    plate_text=detection_data['plate_text'],
                    confidence=detection_data['confidence'],
                    state=detection_data.get('state'),
                    box_x1=detection_data['box'][0],
                    box_y1=detection_data['box'][1],
                    box_x2=detection_data['box'][2],
                    box_y2=detection_data['box'][3],
                    camera_id=detection_data.get('camera_id', 'main'),
                    frame_id=detection_data.get('frame_id'),
                    processing_time_ms=detection_data.get('processing_time_ms'),
                    raw_text=detection_data.get('raw_text'),
                    ocr_results=detection_data.get('ocr_results'),
                    detection_time=datetime.utcnow()
                )
                
                session.add(detection)
                
                # Add to sync queue if sync is enabled
                if self.config.sync_enabled:
                    sync_item = SyncQueue(
                        item_id=detection.id,
                        item_type='detection',
                        data=detection_data,
                        priority=self._calculate_priority(detection_data)
                    )
                    session.add(sync_item)
                
                await session.commit()
                logger.info(f"Saved detection {detection.id} to local storage")
                
                return detection.id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save detection: {e}")
                raise
    
    def _calculate_priority(self, detection_data: Dict) -> int:
        """Calculate sync priority based on detection attributes"""
        priority = 0
        
        # High confidence detections get higher priority
        if detection_data['confidence'] > 0.9:
            priority += 2
        elif detection_data['confidence'] > 0.7:
            priority += 1
            
        # Known plates (if implementing allowlist/blocklist)
        if detection_data.get('is_known_plate'):
            priority += 3
            
        return priority
    
    async def get_pending_sync_items(self, limit: int = 50) -> List[SyncQueue]:
        """Get items pending synchronization"""
        async with self.async_session() as session:
            result = await session.execute(
                select(SyncQueue)
                .where(
                    and_(
                        SyncQueue.status.in_([SyncStatus.PENDING, SyncStatus.RETRY]),
                        or_(
                            SyncQueue.next_retry_at.is_(None),
                            SyncQueue.next_retry_at <= datetime.utcnow()
                        )
                    )
                )
                .order_by(SyncQueue.priority.desc(), SyncQueue.created_at)
                .limit(limit)
            )
            return result.scalars().all()
    
    async def update_sync_status(self, sync_id: int, status: SyncStatus, 
                                error: Optional[str] = None):
        """Update sync queue item status"""
        async with self.async_session() as session:
            item = await session.get(SyncQueue, sync_id)
            if item:
                item.status = status
                item.updated_at = datetime.utcnow()
                
                if status == SyncStatus.SYNCED:
                    item.synced_at = datetime.utcnow()
                elif status == SyncStatus.FAILED:
                    item.attempts += 1
                    item.error_count += 1
                    item.last_error = error
                    # Exponential backoff for retries
                    item.next_retry_at = datetime.utcnow() + timedelta(
                        minutes=2 ** item.attempts
                    )
                    
                await session.commit()
    
    async def cleanup_old_data(self, days_to_keep: int = 7):
        """Clean up old synced data to save storage"""
        async with self.async_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old synced detections
            await session.execute(
                delete(Detection).where(
                    and_(
                        Detection.synced == True,
                        Detection.detection_time < cutoff_date
                    )
                )
            )
            
            # Delete old sync queue items
            await session.execute(
                delete(SyncQueue).where(
                    and_(
                        SyncQueue.status == SyncStatus.SYNCED,
                        SyncQueue.synced_at < cutoff_date
                    )
                )
            )
            
            await session.commit()
            logger.info(f"Cleaned up data older than {days_to_keep} days")
```

---

## 6. Data Models & Storage

### 6.1 SQLite Schema Design

The database schema is optimized for:
- Fast local queries (indexed on common fields)
- Efficient sync queue processing
- Data integrity with constraints
- Storage efficiency with cleanup policies

### 6.2 Migration Strategy

```python
# alembic.ini configuration
[alembic]
script_location = app/db/migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = sqlite:///data/local_lpr.db

# Migration command
alembic upgrade head
```

### 6.3 Data Retention Policy

| Data Type | Retention Period | Condition |
|-----------|-----------------|-----------|
| Unsynced detections | Indefinite | Until synced |
| Synced detections | 7 days | After successful sync |
| Failed sync items | 30 days | After max attempts |
| Device logs | 3 days | Rolling window |

---

## 7. Sync Service Implementation

### 7.1 Sync Strategy

```python
# app/services/sync_service.py
import asyncio
import aiohttp
import gzip
import json
from typing import List, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SyncService:
    """Handles local to cloud data synchronization"""
    
    def __init__(self, storage_service, device_service, config):
        self.storage = storage_service
        self.device = device_service
        self.config = config
        self.running = False
        self._sync_lock = asyncio.Lock()
        
    async def start(self):
        """Start sync service workers"""
        self.running = True
        
        # Start different sync strategies based on config
        if self.config.sync_mode == 'immediate':
            asyncio.create_task(self._immediate_sync_worker())
        else:
            asyncio.create_task(self._batch_sync_worker())
            
        # Always run retry worker
        asyncio.create_task(self._retry_worker())
        
        # Cleanup worker
        asyncio.create_task(self._cleanup_worker())
        
        logger.info(f"Sync service started in {self.config.sync_mode} mode")
    
    async def _immediate_sync_worker(self):
        """Process items immediately as they arrive"""
        while self.running:
            try:
                # Get one pending item
                items = await self.storage.get_pending_sync_items(limit=1)
                
                if items:
                    await self._sync_items(items)
                else:
                    # No items, wait briefly
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Immediate sync error: {e}")
                await asyncio.sleep(5)
    
    async def _batch_sync_worker(self):
        """Process items in batches at intervals"""
        while self.running:
            try:
                # Wait for batch interval
                await asyncio.sleep(self.config.sync_interval)
                
                # Get batch of items
                items = await self.storage.get_pending_sync_items(
                    limit=self.config.sync_batch_size
                )
                
                if items:
                    await self._sync_items(items)
                    
            except Exception as e:
                logger.error(f"Batch sync error: {e}")
                await asyncio.sleep(30)
    
    async def _sync_items(self, items: List[SyncQueue]):
        """Sync a list of items to cloud"""
        async with self._sync_lock:
            # Group items by type for efficient upload
            grouped_items = self._group_items_by_type(items)
            
            for item_type, type_items in grouped_items.items():
                await self._upload_items(item_type, type_items)
    
    def _group_items_by_type(self, items: List[SyncQueue]) -> Dict[str, List]:
        """Group sync items by type"""
        groups = {}
        for item in items:
            if item.item_type not in groups:
                groups[item.item_type] = []
            groups[item.item_type].append(item)
        return groups
    
    async def _upload_items(self, item_type: str, items: List[SyncQueue]):
        """Upload items to cloud API"""
        # Prepare payload
        payload = {
            'device_id': self.device.device_id,
            'timestamp': datetime.utcnow().isoformat(),
            'item_type': item_type,
            'items': [item.data for item in items]
        }
        
        # Compress if large
        data = json.dumps(payload).encode('utf-8')
        if len(data) > 1024 * 10:  # 10KB threshold
            data = gzip.compress(data)
            headers = {
                'Content-Encoding': 'gzip',
                'Content-Type': 'application/json'
            }
        else:
            headers = {'Content-Type': 'application/json'}
            
        # Add auth headers
        headers.update(self.device.get_auth_headers())
        
        # Upload with retry logic
        success = await self._upload_with_retry(
            url=f"{self.config.cloud_api_url}/api/v1/sync/{item_type}",
            data=data,
            headers=headers
        )
        
        # Update sync status
        for item in items:
            if success:
                await self.storage.update_sync_status(
                    item.id, SyncStatus.SYNCED
                )
            else:
                await self.storage.update_sync_status(
                    item.id, SyncStatus.FAILED, 
                    error="Upload failed"
                )
    
    async def _upload_with_retry(self, url: str, data: bytes, 
                                headers: Dict, max_retries: int = 3) -> bool:
        """Upload with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        url, data=data, headers=headers
                    ) as response:
                        if response.status == 200:
                            logger.info(f"Successfully uploaded to {url}")
                            return True
                        elif response.status == 401:
                            # Re-authenticate
                            await self.device.refresh_auth()
                            headers.update(self.device.get_auth_headers())
                        else:
                            logger.warning(
                                f"Upload failed with status {response.status}"
                            )
                            
            except asyncio.TimeoutError:
                logger.warning(f"Upload timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Upload error: {e}")
                
            # Exponential backoff
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                
        return False
    
    async def _retry_worker(self):
        """Handle failed items with exponential backoff"""
        while self.running:
            try:
                # Check every minute
                await asyncio.sleep(60)
                
                # Get items ready for retry
                items = await self.storage.get_pending_sync_items(limit=10)
                retry_items = [
                    item for item in items 
                    if item.status == SyncStatus.RETRY
                ]
                
                if retry_items:
                    logger.info(f"Retrying {len(retry_items)} failed items")
                    await self._sync_items(retry_items)
                    
            except Exception as e:
                logger.error(f"Retry worker error: {e}")
    
    async def _cleanup_worker(self):
        """Clean up old synced data"""
        while self.running:
            try:
                # Run cleanup daily
                await asyncio.sleep(86400)  # 24 hours
                
                await self.storage.cleanup_old_data(
                    days_to_keep=self.config.data_retention_days
                )
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
```

### 7.2 Network Resilience

The sync service implements:
- Exponential backoff for retries
- Connection pooling
- Timeout handling
- Automatic compression for large payloads
- Graceful degradation during network issues

---

## 8. Security Implementation

### 8.1 Device Authentication

```python
# app/services/device_service.py
import os
import uuid
import hashlib
import jwt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import aiohttp

class DeviceService:
    """Manages device identity and authentication"""
    
    def __init__(self, config):
        self.config = config
        self.device_id = None
        self.api_key = None
        self.jwt_token = None
        self.fernet = None
        
    async def initialize(self):
        """Initialize device identity"""
        config_path = "data/device_config.json"
        
        if os.path.exists(config_path):
            # Load existing configuration
            self._load_config(config_path)
            
            # Validate with cloud
            if not await self._validate_device():
                await self._register_device()
        else:
            # Register new device
            await self._register_device()
            
    def _generate_device_id(self) -> str:
        """Generate unique device ID"""
        # Collect hardware identifiers
        identifiers = []
        
        # MAC address
        try:
            import netifaces
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_LINK in addrs:
                    mac = addrs[netifaces.AF_LINK][0]['addr']
                    if mac != '00:00:00:00:00:00':
                        identifiers.append(mac)
                        break
        except:
            pass
            
        # CPU serial (Raspberry Pi)
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        identifiers.append(line.split(':')[1].strip())
                        break
        except:
            pass
            
        # Add randomness
        identifiers.append(str(uuid.uuid4()))
        
        # Generate device ID
        combined = '-'.join(identifiers)
        device_hash = hashlib.sha256(combined.encode()).hexdigest()[:12]
        
        return f"LPR-{device_hash.upper()}"
    
    async def _register_device(self):
        """Register device with cloud platform"""
        self.device_id = self._generate_device_id()
        
        # Generate encryption key for local data
        self.fernet = Fernet.generate_key()
        
        # Prepare registration request
        registration_data = {
            'device_id': self.device_id,
            'device_type': 'edge_lpr',
            'capabilities': {
                'model_version': '2.0.0',
                'has_gpu': torch.cuda.is_available(),
                'camera_resolution': '1920x1080'
            },
            'registration_token': self.config.registration_token
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.cloud_api_url}/api/v1/devices/register",
                    json=registration_data
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        self.api_key = result['api_key']
                        
                        # Save configuration
                        self._save_config()
                        
                        logger.info(f"Device registered: {self.device_id}")
                    else:
                        raise Exception(f"Registration failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Device registration failed: {e}")
            raise
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API calls"""
        # Generate JWT if needed
        if not self.jwt_token or self._jwt_expired():
            self.jwt_token = self._generate_jwt()
            
        return {
            'X-Device-ID': self.device_id,
            'X-API-Key': self.api_key,
            'Authorization': f'Bearer {self.jwt_token}'
        }
    
    def _generate_jwt(self) -> str:
        """Generate JWT token for API authentication"""
        payload = {
            'device_id': self.device_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        return jwt.encode(payload, self.api_key, algorithm='HS256')
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for local storage"""
        if not self.fernet:
            raise RuntimeError("Encryption not initialized")
            
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted: str) -> str:
        """Decrypt sensitive data from local storage"""
        if not self.fernet:
            raise RuntimeError("Encryption not initialized")
            
        return self.fernet.decrypt(encrypted.encode()).decode()
```

### 8.2 Data Security

| Security Measure | Implementation | Purpose |
|-----------------|----------------|---------|
| Device Authentication | JWT + API Key | Secure API access |
| Local Encryption | Fernet (AES-128) | Protect sensitive data at rest |
| TLS Communication | HTTPS only | Protect data in transit |
| Input Validation | Pydantic models | Prevent injection attacks |
| Rate Limiting | Token bucket | Prevent DoS |

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/test_sync_service.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from app.services.sync_service import SyncService

@pytest.mark.asyncio
async def test_sync_service_immediate_mode():
    """Test immediate sync mode"""
    # Mock dependencies
    storage_mock = Mock()
    device_mock = Mock()
    config = {
        'sync_mode': 'immediate',
        'cloud_api_url': 'http://test.api'
    }
    
    # Create service
    sync_service = SyncService(storage_mock, device_mock, config)
    
    # Test immediate sync
    test_item = Mock(id=1, item_type='detection', data={'test': 'data'})
    storage_mock.get_pending_sync_items.return_value = [test_item]
    
    # Run sync
    await sync_service._sync_items([test_item])
    
    # Verify
    assert storage_mock.update_sync_status.called

@pytest.mark.asyncio
async def test_network_resilience