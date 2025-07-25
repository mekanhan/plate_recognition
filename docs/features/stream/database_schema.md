# Database Schema

**Date:** 2025-01-24  
**Version:** 1.0  
**Component:** Stream Feature Database Design

## Schema Overview

The streaming feature extends the existing SQLite database with new tables for detection results, streaming sessions, and related metadata while maintaining compatibility with the current camera management schema.

## Current Schema Analysis

### Existing Tables

#### cameras (Existing)
```sql
CREATE TABLE cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    ip_address VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL DEFAULT 80,
    connection_type VARCHAR(50) NOT NULL DEFAULT 'http',
    stream_path VARCHAR(255),
    location VARCHAR(100),
    username VARCHAR(100),
    password VARCHAR(255),
    status VARCHAR(50) DEFAULT 'offline',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    enabled BOOLEAN DEFAULT true
);

-- Existing indexes
CREATE INDEX idx_cameras_ip_address ON cameras(ip_address);
CREATE INDEX idx_cameras_status ON cameras(status);
CREATE INDEX idx_cameras_location ON cameras(location);
```

**Current Data**:
- Test Camera 1: ID=3, IP=10.0.0.181, Location=entrance
- Parking Camera: ID=4, IP=192.168.1.205, Location=parking

## New Tables for Streaming Feature

### 1. detections

**Purpose**: Store license plate detection results from video streams.

```sql
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    session_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Bounding box coordinates (original frame coordinates)
    bbox_x1 INTEGER NOT NULL,
    bbox_y1 INTEGER NOT NULL,
    bbox_x2 INTEGER NOT NULL,
    bbox_y2 INTEGER NOT NULL,
    
    -- Detection confidence scores
    yolo_confidence REAL NOT NULL,
    ocr_confidence REAL,
    combined_confidence REAL,
    quality_score REAL,
    
    -- OCR Results
    plate_text VARCHAR(20),
    raw_ocr_text VARCHAR(50),
    text_validated BOOLEAN DEFAULT false,
    
    -- Processing metadata
    processing_time_ms INTEGER,
    model_version VARCHAR(50),
    
    -- Image storage
    original_image_path VARCHAR(500),
    enhanced_image_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    
    -- Additional metadata
    frame_number INTEGER,
    stream_timestamp DATETIME,
    
    FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES stream_sessions(id) ON DELETE SET NULL
);
```

### 2. stream_sessions

**Purpose**: Track streaming sessions and their metadata.

```sql
CREATE TABLE stream_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    
    -- Session timing
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    duration_seconds INTEGER,
    
    -- Session configuration
    quality_setting VARCHAR(20) DEFAULT 'medium',
    detection_enabled BOOLEAN DEFAULT true,
    confidence_threshold REAL DEFAULT 0.5,
    max_fps INTEGER DEFAULT 30,
    
    -- Performance statistics
    total_frames INTEGER DEFAULT 0,
    processed_frames INTEGER DEFAULT 0,
    total_detections INTEGER DEFAULT 0,
    avg_fps REAL,
    avg_processing_time_ms REAL,
    
    -- Session status
    status VARCHAR(20) DEFAULT 'active',  -- active, stopped, error, interrupted
    error_message TEXT,
    
    -- Resource usage
    peak_cpu_usage REAL,
    peak_memory_mb REAL,
    
    FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE
);
```

### 3. detection_images

**Purpose**: Manage detection image files and metadata.

```sql
CREATE TABLE detection_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_id INTEGER NOT NULL,
    
    -- Image types
    image_type VARCHAR(20) NOT NULL,  -- 'original', 'enhanced', 'thumbnail'
    
    -- File information
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(50) DEFAULT 'image/jpeg',
    
    -- Image properties
    width INTEGER,
    height INTEGER,
    
    -- Processing information
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_applied TEXT,  -- JSON string of applied enhancements
    
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE
);
```

### 4. system_metrics

**Purpose**: Store system performance and health metrics.

```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_type VARCHAR(50) NOT NULL,
    
    -- Performance metrics
    cpu_usage_percent REAL,
    memory_usage_mb REAL,
    gpu_usage_percent REAL,
    gpu_memory_mb REAL,
    disk_usage_percent REAL,
    
    -- Streaming metrics
    active_streams INTEGER DEFAULT 0,
    total_fps REAL,
    processing_queue_size INTEGER,
    
    -- Detection metrics
    detections_per_minute REAL,
    avg_detection_time_ms REAL,
    detection_accuracy_percent REAL,
    
    -- Network metrics
    bandwidth_usage_mbps REAL,
    websocket_connections INTEGER DEFAULT 0,
    
    -- Additional data (JSON format for flexibility)
    additional_data TEXT
);
```

### 5. plate_text_validation

**Purpose**: Store validation rules and patterns for license plate text.

```sql
CREATE TABLE plate_text_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    region VARCHAR(50),  -- US, EU, etc.
    is_active BOOLEAN DEFAULT true,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Default validation patterns
INSERT INTO plate_text_validation (pattern, description, region) VALUES
('^[A-Z0-9]{2,3}[- ]?[A-Z0-9]{3,4}$', 'Standard US format', 'US'),
('^[A-Z]{3}[- ]?[0-9]{3,4}$', 'Letter-Number format', 'US'),
('^[0-9]{3}[- ]?[A-Z]{3}$', 'Number-Letter format', 'US'),
('^[A-Z]{2}[0-9]{2}[A-Z]{3}$', 'European format', 'EU');
```

## Database Indexes

### Performance Indexes

```sql
-- Detection queries (most common)
CREATE INDEX idx_detections_camera_timestamp 
    ON detections(camera_id, timestamp DESC);

CREATE INDEX idx_detections_plate_text 
    ON detections(plate_text);

CREATE INDEX idx_detections_timestamp 
    ON detections(timestamp DESC);

CREATE INDEX idx_detections_confidence 
    ON detections(yolo_confidence, ocr_confidence);

-- Session queries
CREATE INDEX idx_stream_sessions_camera 
    ON stream_sessions(camera_id, started_at DESC);

CREATE INDEX idx_stream_sessions_status 
    ON stream_sessions(status, started_at DESC);

-- Image queries
CREATE INDEX idx_detection_images_detection 
    ON detection_images(detection_id, image_type);

-- Metrics queries
CREATE INDEX idx_system_metrics_timestamp 
    ON system_metrics(timestamp DESC, metric_type);

-- Validation queries
CREATE INDEX idx_plate_validation_region 
    ON plate_text_validation(region, is_active);
```

### Composite Indexes for Complex Queries

```sql
-- Recent detections with camera info
CREATE INDEX idx_detections_recent 
    ON detections(timestamp DESC, camera_id, yolo_confidence);

-- Detection search and filtering
CREATE INDEX idx_detections_search 
    ON detections(camera_id, timestamp DESC, plate_text, yolo_confidence);

-- Session analytics
CREATE INDEX idx_sessions_analytics 
    ON stream_sessions(camera_id, started_at DESC, status, total_detections);
```

## Data Relationships

### Entity Relationship Diagram

```
cameras (existing)
    |
    ├── stream_sessions (1:many)
    │   └── detections (1:many)
    │       └── detection_images (1:many)
    │
    └── detections (1:many) [direct relationship for non-session detections]

system_metrics (independent)
plate_text_validation (reference data)
```

### Foreign Key Constraints

```sql
-- Enable foreign key enforcement
PRAGMA foreign_keys = ON;

-- Verify constraints
SELECT * FROM pragma_foreign_key_check;
```

## Data Migration Strategy

### Migration Scripts

#### Migration 001: Create streaming tables
```sql
-- File: migrations/001_create_streaming_tables.sql
BEGIN TRANSACTION;

-- Create new tables
-- [Include all CREATE TABLE statements above]

-- Verify migration
SELECT name FROM sqlite_master WHERE type='table' 
    AND name IN ('detections', 'stream_sessions', 'detection_images', 'system_metrics', 'plate_text_validation');

COMMIT;
```

#### Migration 002: Add indexes
```sql
-- File: migrations/002_add_performance_indexes.sql
BEGIN TRANSACTION;

-- [Include all CREATE INDEX statements above]

-- Verify indexes
SELECT name FROM sqlite_master WHERE type='index' 
    AND name LIKE 'idx_%';

COMMIT;
```

### Migration Execution

```python
# backend/app/database_migrations.py
async def run_migrations(db_path: str):
    """Execute database migrations"""
    migration_files = [
        "migrations/001_create_streaming_tables.sql",
        "migrations/002_add_performance_indexes.sql"
    ]
    
    for migration_file in migration_files:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        async with aiosqlite.connect(db_path) as db:
            await db.executescript(migration_sql)
            await db.commit()
```

## Query Patterns and Performance

### Common Queries

#### Recent Detections
```sql
-- Get recent detections with camera info (most common query)
SELECT 
    d.id,
    d.timestamp,
    d.plate_text,
    d.yolo_confidence,
    d.ocr_confidence,
    d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2,
    c.name as camera_name,
    c.location
FROM detections d
JOIN cameras c ON d.camera_id = c.id
WHERE d.timestamp >= datetime('now', '-1 hour')
ORDER BY d.timestamp DESC
LIMIT 50;

-- Expected execution time: <50ms with proper indexes
```

#### Detection Search and Filtering
```sql
-- Search detections by plate text and date range
SELECT 
    d.*,
    c.name as camera_name
FROM detections d
JOIN cameras c ON d.camera_id = c.id
WHERE d.plate_text LIKE '%ABC%'
    AND d.timestamp BETWEEN '2025-01-24 00:00:00' AND '2025-01-24 23:59:59'
    AND d.yolo_confidence >= 0.7
ORDER BY d.timestamp DESC;

-- Expected execution time: <100ms with composite index
```

#### Session Analytics
```sql
-- Get streaming session statistics
SELECT 
    s.id,
    c.name,
    s.started_at,
    s.ended_at,
    s.duration_seconds,
    s.total_frames,
    s.total_detections,
    s.avg_fps,
    ROUND(s.total_detections * 1.0 / (s.duration_seconds / 60.0), 2) as detections_per_minute
FROM stream_sessions s
JOIN cameras c ON s.camera_id = c.id
WHERE s.started_at >= datetime('now', '-7 days')
ORDER BY s.started_at DESC;
```

### Performance Optimization

#### Query Optimization Rules
1. **Always use indexes**: Ensure WHERE clauses match available indexes
2. **Limit result sets**: Use LIMIT and pagination for large datasets
3. **Avoid SELECT ***: Select only needed columns
4. **Use EXPLAIN QUERY PLAN**: Analyze query execution plans

#### Example Query Plan Analysis
```sql
EXPLAIN QUERY PLAN
SELECT d.id, d.plate_text, c.name
FROM detections d
JOIN cameras c ON d.camera_id = c.id
WHERE d.timestamp >= datetime('now', '-1 hour')
ORDER BY d.timestamp DESC
LIMIT 20;

-- Expected plan: Uses idx_detections_timestamp for efficient filtering
```

## Data Retention and Cleanup

### Retention Policies

```sql
-- Cleanup policies configuration
CREATE TABLE data_retention_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name VARCHAR(50) NOT NULL,
    retention_days INTEGER NOT NULL,
    cleanup_enabled BOOLEAN DEFAULT true,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Default retention policies
INSERT INTO data_retention_policies (table_name, retention_days) VALUES
('detections', 90),          -- Keep detections for 90 days
('detection_images', 30),    -- Keep images for 30 days
('stream_sessions', 365),    -- Keep session data for 1 year
('system_metrics', 30);      -- Keep metrics for 30 days
```

### Automated Cleanup

```python
# backend/app/services/data_cleanup.py
class DataCleanupService:
    async def cleanup_old_data(self):
        """Execute automated data cleanup based on retention policies"""
        
        # Delete old detections
        await self.cleanup_detections()
        
        # Delete old images
        await self.cleanup_detection_images()
        
        # Delete old sessions
        await self.cleanup_stream_sessions()
        
        # Delete old metrics
        await self.cleanup_system_metrics()
    
    async def cleanup_detections(self):
        """Remove detections older than retention period"""
        retention_days = await self.get_retention_days('detections')
        
        query = """
        DELETE FROM detections 
        WHERE timestamp < datetime('now', '-{} days')
        """.format(retention_days)
        
        # Execute cleanup with logging
```

## Backup and Recovery

### Backup Strategy

```python
# backend/app/services/database_backup.py
class DatabaseBackupService:
    async def create_backup(self):
        """Create full database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"backups/database_{timestamp}.db"
        
        # Create backup using SQLite backup API
        shutil.copy2(self.db_path, backup_path)
        
        # Compress backup
        with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
            with open(backup_path, 'rb') as f_in:
                shutil.copyfileobj(f_in, f_out)
        
        os.remove(backup_path)  # Remove uncompressed backup
```

### Recovery Procedures

```bash
# Restore from backup
gunzip database_20250124_120000.db.gz
cp database_20250124_120000.db backend/data/cameras.db

# Verify database integrity
sqlite3 backend/data/cameras.db "PRAGMA integrity_check;"
```

## Security Considerations

### Data Protection

```sql
-- Sensitive data handling
-- Note: Passwords in cameras table should be encrypted
-- Detection images should be stored with appropriate file permissions

-- Audit logging for sensitive operations
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100),
    action VARCHAR(50),
    table_name VARCHAR(50),
    record_id INTEGER,
    old_values TEXT,
    new_values TEXT
);
```

### Access Control

```python
# Row-level security for multi-tenant scenarios
class DatabaseSecurity:
    async def filter_camera_access(self, user_id: str, query: str) -> str:
        """Add camera access filtering to queries"""
        # Add WHERE clause to limit access based on user permissions
        pass
```

## Monitoring and Health Checks

### Database Health Monitoring

```sql
-- Database size monitoring
SELECT 
    page_count * page_size as database_size_bytes,
    page_count,
    page_size
FROM pragma_page_count(), pragma_page_size();

-- Table size analysis
SELECT 
    name,
    COUNT(*) as row_count
FROM (
    SELECT 'cameras' as name UNION ALL
    SELECT 'detections' UNION ALL
    SELECT 'stream_sessions' UNION ALL
    SELECT 'detection_images' UNION ALL
    SELECT 'system_metrics'
) tables,
sqlite_master
WHERE sqlite_master.name = tables.name;
```

### Performance Monitoring

```python
# Database performance monitoring
class DatabaseMonitor:
    async def collect_performance_metrics(self):
        """Collect database performance metrics"""
        metrics = {
            'database_size_mb': await self.get_database_size(),
            'total_detections': await self.count_detections(),
            'avg_query_time_ms': await self.measure_query_performance(),
            'active_connections': await self.count_connections()
        }
        
        # Store metrics in system_metrics table
        await self.store_metrics(metrics)
```

This database schema provides a robust foundation for the streaming feature while maintaining compatibility with the existing camera management system and ensuring optimal performance for real-time detection operations.