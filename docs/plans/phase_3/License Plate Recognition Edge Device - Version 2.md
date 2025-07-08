# License Plate Recognition Edge Device
## Implementation Guide & Technical Documentation

**Version:** 2.0.0  
**Last Updated:** January 2025  
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
async def test_network_resilience():
    """Test sync behavior during network failures"""
    storage_mock = Mock()
    device_mock = Mock()
    config = {'sync_mode': 'batch', 'cloud_api_url': 'http://test.api'}
    
    sync_service = SyncService(storage_mock, device_mock, config)
    
    # Simulate network failure
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.side_effect = asyncio.TimeoutError()
        
        result = await sync_service._upload_with_retry(
            url='http://test.api/sync',
            data=b'test',
            headers={},
            max_retries=2
        )
        
        assert result is False
        assert mock_post.call_count == 2  # Should retry

@pytest.mark.asyncio
async def test_data_compression():
    """Test automatic data compression for large payloads"""
    sync_service = SyncService(Mock(), Mock(), {})
    
    # Create large payload
    large_data = {'items': ['x' * 1000 for _ in range(20)]}
    
    # Test compression logic
    compressed = await sync_service._prepare_payload(large_data)
    
    assert len(compressed) < len(json.dumps(large_data).encode())
```

### 9.2 Integration Tests

```python
# tests/test_integration.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from app.services.storage_service import StorageService
from app.services.detection_service import DetectionService

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.mark.asyncio
async def test_detection_to_sync_flow(test_db):
    """Test complete flow from detection to sync queue"""
    # Setup services
    storage = StorageService({'database_url': 'sqlite+aiosqlite:///:memory:'})
    await storage.initialize()
    
    # Create test detection
    detection_data = {
        'detection_id': 'test-001',
        'plate_text': 'ABC123',
        'confidence': 0.95,
        'box': [100, 100, 200, 150]
    }
    
    # Save detection
    await storage.save_detection(detection_data)
    
    # Verify sync queue entry
    sync_items = await storage.get_pending_sync_items()
    assert len(sync_items) == 1
    assert sync_items[0].item_id == 'test-001'
```

### 9.3 Performance Tests

```python
# tests/test_performance.py
import time
import asyncio
import statistics

@pytest.mark.asyncio
async def test_detection_latency():
    """Ensure detection meets latency requirements"""
    detection_service = DetectionService()
    await detection_service.initialize()
    
    # Load test image
    test_image = cv2.imread('tests/fixtures/test_plate.jpg')
    
    # Measure latencies
    latencies = []
    for _ in range(100):
        start = time.time()
        await detection_service.process_frame(test_image)
        latencies.append((time.time() - start) * 1000)
    
    # Assert performance requirements
    assert statistics.mean(latencies) < 100  # Average < 100ms
    assert statistics.quantiles(latencies, n=100)[94] < 150  # 95th percentile < 150ms
```

### 9.4 Test Coverage Requirements

| Component | Required Coverage | Priority |
|-----------|------------------|----------|
| Core Detection | 90% | P0 |
| Storage Service | 85% | P0 |
| Sync Service | 80% | P1 |
| Device Service | 85% | P1 |
| API Endpoints | 75% | P2 |

---

## 10. Deployment Guide

### 10.1 Pre-deployment Checklist

```bash
#!/bin/bash
# scripts/pre-deployment-check.sh

echo "=== LPR Edge Device Pre-deployment Check ==="

# 1. System requirements
check_system() {
    echo -n "Checking system requirements... "
    
    # Check CPU cores
    cores=$(nproc)
    if [ $cores -lt 4 ]; then
        echo "FAIL: Need at least 4 CPU cores (found $cores)"
        return 1
    fi
    
    # Check RAM
    ram_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [ $ram_gb -lt 4 ]; then
        echo "FAIL: Need at least 4GB RAM (found ${ram_gb}GB)"
        return 1
    fi
    
    # Check storage
    storage_gb=$(df -BG /opt/lpr | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ $storage_gb -lt 16 ]; then
        echo "FAIL: Need at least 16GB free storage (found ${storage_gb}GB)"
        return 1
    fi
    
    echo "PASS"
    return 0
}

# 2. Camera check
check_camera() {
    echo -n "Checking camera... "
    if [ -e /dev/video0 ]; then
        echo "PASS"
        return 0
    else
        echo "FAIL: No camera detected at /dev/video0"
        return 1
    fi
}

# 3. Network connectivity
check_network() {
    echo -n "Checking network connectivity... "
    if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
        echo "PASS"
        return 0
    else
        echo "FAIL: No internet connectivity"
        return 1
    fi
}

# 4. Docker installation
check_docker() {
    echo -n "Checking Docker... "
    if command -v docker > /dev/null 2>&1; then
        version=$(docker --version | awk '{print $3}' | sed 's/,//')
        echo "PASS (version $version)"
        return 0
    else
        echo "FAIL: Docker not installed"
        return 1
    fi
}

# Run all checks
all_passed=true
check_system || all_passed=false
check_camera || all_passed=false
check_network || all_passed=false
check_docker || all_passed=false

if $all_passed; then
    echo -e "\n✓ All checks passed! Ready for deployment."
    exit 0
else
    echo -e "\n✗ Some checks failed. Please fix issues before deployment."
    exit 1
fi
```

### 10.2 Deployment Script

```bash
#!/bin/bash
# scripts/deploy-device.sh

set -e

DEPLOYMENT_DIR="/opt/lpr"
CONFIG_FILE="$DEPLOYMENT_DIR/config/device.env"
LOG_DIR="$DEPLOYMENT_DIR/logs"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "Error: Configuration file not found at $CONFIG_FILE"
    exit 1
fi

echo "=== Deploying LPR Edge Device ==="
echo "Device ID: $DEVICE_ID"
echo "Customer: $CUSTOMER_ID"
echo "Location: $LOCATION"
echo

# 1. Stop existing service
echo "1. Stopping existing service..."
sudo systemctl stop lpr-device || true

# 2. Pull latest image
echo "2. Pulling latest Docker image..."
docker pull "${DOCKER_REGISTRY}/lpr-service:${VERSION:-latest}"

# 3. Database migration
echo "3. Running database migrations..."
docker run --rm \
    -v "$DEPLOYMENT_DIR/data:/app/data" \
    -e DATABASE_URL="sqlite:///app/data/local_lpr.db" \
    "${DOCKER_REGISTRY}/lpr-service:${VERSION:-latest}" \
    alembic upgrade head

# 4. Start service
echo "4. Starting LPR service..."
sudo systemctl start lpr-device
sleep 5

# 5. Health check
echo "5. Performing health check..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8001/health | grep -q "healthy"; then
        echo "✓ Service is healthy"
        break
    fi
    
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "✗ Health check failed"
    sudo journalctl -u lpr-device -n 50
    exit 1
fi

# 6. Verify sync connectivity
echo "6. Verifying cloud connectivity..."
sync_status=$(curl -s http://localhost:8001/api/sync/status | jq -r '.connected')

if [ "$sync_status" = "true" ]; then
    echo "✓ Cloud sync connected"
else
    echo "⚠ Cloud sync not connected (will retry automatically)"
fi

# 7. Create deployment report
report_file="$LOG_DIR/deployment_$(date +%Y%m%d_%H%M%S).log"
cat > "$report_file" <<EOF
=== LPR Edge Device Deployment Report ===
Date: $(date)
Device ID: $DEVICE_ID
Customer: $CUSTOMER_ID
Location: $LOCATION
Version: ${VERSION:-latest}

System Info:
- CPU: $(nproc) cores
- RAM: $(free -h | awk '/^Mem:/{print $2}')
- Storage: $(df -h $DEPLOYMENT_DIR | awk 'NR==2 {print $4}' | sed 's/G//') GB free
- OS: $(lsb_release -d | cut -f2)

Service Status: $(systemctl is-active lpr-device)
Cloud Connected: $sync_status

Deployment completed successfully.
=========================================
EOF

echo
echo "=== Deployment Complete ==="
echo "Report saved to: $report_file"
echo
echo "Monitor logs with: sudo journalctl -u lpr-device -f"
echo "View UI at: http://localhost:8001"
```

### 10.3 Post-deployment Verification

```python
# scripts/verify_deployment.py
import asyncio
import aiohttp
import sys
from datetime import datetime

async def verify_deployment(base_url="http://localhost:8001"):
    """Verify edge device deployment"""
    
    tests = {
        "health": {"url": f"{base_url}/health", "expected_status": 200},
        "api_docs": {"url": f"{base_url}/docs", "expected_status": 200},
        "detection_status": {"url": f"{base_url}/api/detection/status", "expected_status": 200},
        "sync_status": {"url": f"{base_url}/api/sync/status", "expected_status": 200},
    }
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for test_name, test_config in tests.items():
            try:
                async with session.get(test_config["url"]) as response:
                    results[test_name] = {
                        "status": response.status,
                        "passed": response.status == test_config["expected_status"]
                    }
            except Exception as e:
                results[test_name] = {
                    "status": "error",
                    "passed": False,
                    "error": str(e)
                }
    
    # Print results
    print("=== Deployment Verification Results ===")
    print(f"Timestamp: {datetime.now()}")
    print(f"Base URL: {base_url}")
    print()
    
    all_passed = True
    for test_name, result in results.items():
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        print(f"{test_name}: {status} (status: {result['status']})")
        if not result["passed"]:
            all_passed = False
            if "error" in result:
                print(f"  Error: {result['error']}")
    
    print()
    if all_passed:
        print("✓ All verification tests passed!")
        return 0
    else:
        print("✗ Some tests failed. Check service logs.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(verify_deployment()))
```

---

## 11. Monitoring & Maintenance

### 11.1 Health Monitoring

```python
# app/services/health_monitor.py
import psutil
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HealthMonitor:
    """System health monitoring"""
    
    def __init__(self, config):
        self.config = config
        self.metrics = {}
        
    async def start(self):
        """Start health monitoring"""
        asyncio.create_task(self._monitor_system())
        asyncio.create_task(self._monitor_services())
        
    async def _monitor_system(self):
        """Monitor system resources"""
        while True:
            try:
                self.metrics['system'] = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'temperature': self._get_cpu_temperature(),
                    'network_up': await self._check_network()
                }
                
                # Alert on critical conditions
                if self.metrics['system']['cpu_percent'] > 90:
                    logger.warning(f"High CPU usage: {self.metrics['system']['cpu_percent']}%")
                    
                if self.metrics['system']['memory_percent'] > 85:
                    logger.warning(f"High memory usage: {self.metrics['system']['memory_percent']}%")
                    
                if self.metrics['system']['disk_percent'] > 80:
                    logger.warning(f"Low disk space: {self.metrics['system']['disk_percent']}% used")
                    
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                
            await asyncio.sleep(60)  # Check every minute
    
    def _get_cpu_temperature(self):
        """Get CPU temperature (platform specific)"""
        try:
            # Raspberry Pi
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                return temp
        except:
            return None
    
    async def _check_network(self):
        """Check network connectivity"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection('8.8.8.8', 53),
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    async def get_health_status(self):
        """Get current health status"""
        return {
            'healthy': self._is_healthy(),
            'metrics': self.metrics,
            'alerts': self._get_active_alerts()
        }
    
    def _is_healthy(self):
        """Determine if system is healthy"""
        if not self.metrics.get('system'):
            return False
            
        system = self.metrics['system']
        
        # Health criteria
        return all([
            system.get('cpu_percent', 100) < 95,
            system.get('memory_percent', 100) < 90,
            system.get('disk_percent', 100) < 90,
            system.get('network_up', False),
            system.get('temperature', 100) < 80  # 80°C threshold
        ])
```

### 11.2 Maintenance Tasks

```bash
#!/bin/bash
# scripts/maintenance.sh

# Daily maintenance script
# Add to cron: 0 2 * * * /opt/lpr/scripts/maintenance.sh

LOG_FILE="/opt/lpr/logs/maintenance_$(date +%Y%m%d).log"

echo "=== LPR Maintenance Started: $(date) ===" >> "$LOG_FILE"

# 1. Clean old logs
echo "Cleaning old logs..." >> "$LOG_FILE"
find /opt/lpr/logs -name "*.log" -mtime +7 -delete

# 2. Database optimization
echo "Optimizing database..." >> "$LOG_FILE"
docker exec lpr-device python -c "
from app.db import get_session
async def optimize():
    async with get_session() as session:
        await session.execute('VACUUM;')
        await session.execute('ANALYZE;')
import asyncio
asyncio.run(optimize())
"

# 3. Docker cleanup
echo "Cleaning Docker resources..." >> "$LOG_FILE"
docker system prune -f

# 4. Check for updates (optional)
echo "Checking for updates..." >> "$LOG_FILE"
# Add update check logic here

echo "=== Maintenance Completed: $(date) ===" >> "$LOG_FILE"
```

### 11.3 Troubleshooting Guide

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| No detections | Camera feed ok, no plates detected | 1. Check lighting conditions<br>2. Verify camera focus<br>3. Check detection confidence threshold |
| Sync failures | Detections work, cloud sync fails | 1. Check network connectivity<br>2. Verify device authentication<br>3. Check cloud API status |
| High CPU usage | System sluggish, high temperature | 1. Check for memory leaks<br>2. Reduce frame rate<br>3. Enable frame skipping |
| Storage full | Sync stopped, errors in logs | 1. Run cleanup script<br>2. Check data retention settings<br>3. Verify old data deletion |

---

## 12. API Reference

### 12.1 Local API Endpoints

```yaml
# OpenAPI specification excerpt
paths:
  /health:
    get:
      summary: Health check endpoint
      responses:
        200:
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: 
                    type: string
                    example: "healthy"
                  uptime:
                    type: number
                    example: 3600
                  version:
                    type: string
                    example: "2.0.0"
  
  /api/detection/detect:
    post:
      summary: Detect license plate in uploaded image
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
      responses:
        200:
          description: Detection result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DetectionResult'
  
  /api/sync/status:
    get:
      summary: Get sync queue status
      responses:
        200:
          description: Sync status
          content:
            application/json:
              schema:
                type: object
                properties:
                  pending:
                    type: integer
                  synced:
                    type: integer
                  failed:
                    type: integer
                  connected:
                    type: boolean

components:
  schemas:
    DetectionResult:
      type: object
      properties:
        detection_id:
          type: string
        plate_text:
          type: string
        confidence:
          type: number
        state:
          type: string
        timestamp:
          type: string
          format: date-time
```

### 12.2 Configuration Reference

```toml
# config/settings.toml

[database]
url = "sqlite:///data/local_lpr.db"
pool_size = 5
echo = false

[sync]
enabled = true
mode = "immediate"  # immediate | batch
batch_size = 50
interval = 300  # seconds (for batch mode)
retry_max_attempts = 5
retry_backoff_base = 2  # exponential backoff base
compression_threshold = 10240  # bytes

[detection]
confidence_threshold = 0.5
save_images = true
image_retention_days = 7

[device]
registration_token = ""  # Set during deployment
cloud_api_url = "https://api.lprcloud.com"
health_check_interval = 60

[security]
encrypt_local_data = true
api_timeout = 30  # seconds
max_request_size = 10485760  # 10MB

[maintenance]
data_retention_days = 7
cleanup_hour = 2  # 2 AM local time
vacuum_on_startup = true
```

---

## Appendix A: Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| E001 | Database connection failed | Check database file permissions |
| E002 | Camera not found | Verify camera connection |
| E003 | Cloud API unreachable | Check network and firewall |
| E004 | Authentication failed | Re-register device |
| E005 | Storage full | Run cleanup or expand storage |
| E006 | Invalid configuration | Check config file syntax |

## Appendix B: Performance Tuning

### B.1 Edge Device Optimization

```python
# config/performance.py

# Frame processing optimization
FRAME_SKIP = 2  # Process every Nth frame
MAX_QUEUE_SIZE = 10  # Limit processing queue
DETECTION_THREADS = 2  # Parallel detection threads

# Memory optimization
IMAGE_CACHE_SIZE = 50  # Number of images to keep in memory
CLEANUP_INTERVAL = 3600  # Cleanup every hour

# Network optimization
SYNC_COMPRESSION = True  # Enable compression
BATCH_UPLOAD_SIZE = 100  # Max items per upload
CONNECTION_POOL_SIZE = 5  # Concurrent connections
```

### B.2 Database Optimization

```sql
-- Indexes for common queries
CREATE INDEX idx_detection_sync ON detections(synced, detection_time);
CREATE INDEX idx_sync_queue_status ON sync_queue(status, priority);

-- Periodic maintenance
PRAGMA optimize;
PRAGMA integrity_check;
```

---

This completes the Plate Recognition Edge Device documentation. The document provides a comprehensive guide for implementing all necessary features to transform your current system into a production-ready edge device with cloud synchronization capabilities.