# LPR Edge Device Setup Guide

## Phase 1: Enhanced Data Models & Sync Queue ✅ COMPLETED

This guide covers setting up the License Plate Recognition Edge Device with offline-first capability and cloud synchronization.

## Overview

The Edge Device implementation provides:
- **Offline-first operation** - Works without internet connection
- **Automatic cloud sync** - Syncs data when connection available  
- **Device registration** - Secure device identity management
- **Priority sync queue** - High-confidence detections sync first
- **Retry logic** - Exponential backoff for failed syncs
- **Data encryption** - Sensitive data encrypted locally

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.edge.example .env
# Edit .env with your settings
```

### 3. Test Implementation

```bash
python test_edge_implementation.py
```

### 4. Start the Application

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Configuration

### Device Settings
```env
DEVICE_NAME=LPR-Edge-001
DEVICE_LOCATION=Main Entrance
REGISTRATION_TOKEN=your-registration-token
```

### Sync Settings
```env
CLOUD_API_URL=https://api.lprcloud.com
SYNC_MODE=batch  # immediate, batch, manual
SYNC_INTERVAL=300  # seconds
SYNC_BATCH_SIZE=50
```

### Deployment Modes
- **web_ui**: Full web interface (default)
- **headless**: Background processing only
- **hybrid**: Both web UI and background

## API Endpoints

### Sync Management
- `GET /api/sync/status` - Get sync queue status
- `POST /api/sync/force` - Force immediate sync
- `DELETE /api/sync/failed` - Clear failed items
- `GET /api/sync/config` - Get sync configuration

### Device Management  
- `GET /api/sync/device/info` - Get device information
- `POST /api/sync/device/heartbeat` - Update device heartbeat
- `POST /api/sync/test-connection` - Test cloud connection

## Database Schema

### New Tables Added

**sync_queue** - Manages cloud synchronization
```sql
- id (primary key)
- item_type (detection, health, logs)  
- item_id (reference to actual record)
- data (JSON payload to sync)
- status (pending, synced, failed, retry)
- priority (low, normal, high, critical)
- created_at, updated_at, synced_at
- attempts, error_count, last_error
```

**device_config** - Device identity and configuration
```sql
- device_id (unique identifier)
- api_key_hash (encrypted API key)
- cloud_endpoint
- capabilities (JSON)
- registration info
```

### Enhanced Existing Tables
- Added `synced`, `sync_attempts`, `sync_error` fields to `detections`
- Added sync-related indexes for performance

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Detection     │───▶│   Sync Queue    │───▶│   Cloud API     │
│   Service       │    │   Manager       │    │   (Optional)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local         │    │   SQLite        │    │   PostgreSQL    │
│   JSON Files    │    │   Database      │    │   Cloud DB      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Sync Modes

### Batch Mode (Recommended)
- Syncs data in batches every 5 minutes
- Efficient for high-volume scenarios
- Lower bandwidth usage

### Immediate Mode  
- Syncs each detection immediately
- Real-time cloud updates
- Higher bandwidth usage

### Manual Mode
- No automatic sync
- Use API endpoints to trigger sync
- Full offline operation

## Monitoring

### Sync Status
```bash
curl http://localhost:8001/api/sync/status
```

Response:
```json
{
  "pending": 15,
  "retry": 2,
  "failed": 0,
  "sync_mode": "batch",
  "device_id": "LPR-ABC123DEF456",
  "last_sync": "2025-01-20T10:30:00Z"
}
```

### Device Info
```bash
curl http://localhost:8001/api/sync/device/info
```

### Force Sync
```bash
curl -X POST http://localhost:8001/api/sync/force
```

## Troubleshooting

### Common Issues

**1. Sync Queue Not Processing**
- Check internet connection
- Verify cloud endpoint URL
- Check device registration status

**2. High Failed Sync Count**
- Verify API credentials
- Check cloud platform status
- Review error logs

**3. Database Errors** 
- Ensure data directory is writable
- Check SQLite file permissions
- Verify disk space

### Logs
```bash
tail -f logs/app.log
```

### Debug Mode
Set `LOG_LEVEL=DEBUG` in .env for detailed logging.

## Security

### Data Encryption
- API keys encrypted with Fernet
- Sensitive local data encrypted
- Secure device ID generation

### Authentication
- Device registration with tokens
- API key validation
- JWT tokens for cloud communication

## Hardware Requirements

### Minimum
- ARM Cortex-A53 (4 cores)
- 4GB RAM
- 32GB storage
- 1080p camera

### Recommended  
- NVIDIA Jetson Nano or Raspberry Pi 4
- 8GB RAM
- 64GB SSD storage
- 1080p camera with IR

## Next Steps

### Phase 2: Device Management & Authentication
- Enhanced device registration
- Cloud device validation
- API key rotation
- Device health monitoring

### Phase 3: Cloud Sync Service  
- Batch compression
- Conflict resolution
- Real-time status updates
- Sync analytics

### Phase 4: Production Features
- Health monitoring system
- Performance metrics
- Comprehensive testing
- Deployment automation

## Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. Test connection: `curl http://localhost:8001/api/sync/test-connection`
3. Review configuration: `cat .env`
4. Run diagnostics: `python test_edge_implementation.py`