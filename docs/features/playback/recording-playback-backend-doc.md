# Recording Playback Backend Implementation Guide

## Overview
This document provides comprehensive implementation requirements for backend support of the Recording Playback UI. The system handles 4K 30fps compressed video recordings stored in 10-minute segments with a 10GB development storage limit.

## Project Context & Guidelines

### System Architecture
- **Recording Service**: Runs independently on port 8002
- **Storage Path**: `recordings/camera_{id}/YYYY/MM/DD/HH/`
- **Video Format**: 4K resolution (3840x2160) at 30fps, compressed
- **Segment Duration**: 10 minutes per file
- **Storage Limit**: 10GB (development phase)
- **Database**: SQLite index per camera for metadata

### Core Principles (from CLAUDE.md)
1. **Simplicity First**: Keep implementations straightforward
2. **Remove Barriers**: Focus on accessibility and ease of use
3. **24/7 Operation**: Continuous recording without manual intervention
4. **Real-time Status**: Live updates, not database-cached states

## Required API Endpoints

### 1. Calendar Data Endpoint
Provides recording availability for calendar widget display.

```python
@router.get("/api/v1/recordings/cameras/{camera_id}/calendar")
async def get_calendar_data(
    camera_id: str,
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12)
):
    """
    Get recording availability for calendar display
    
    Returns:
    {
        "year": 2025,
        "month": 7,
        "days": {
            "1": {
                "has_recordings": true,
                "total_duration": 86400,
                "total_size": 12884901888,
                "recording_percentage": 100.0
            },
            "31": {
                "has_recordings": true,
                "total_duration": 82800,
                "total_size": 12345678900,
                "recording_percentage": 95.8
            }
        },
        "total_size": 398876543210,
        "total_duration": 2678400
    }
    """
```

### 2. Timeline Segments Endpoint
Returns detailed segment information for timeline visualization.

```python
@router.get("/api/v1/recordings/cameras/{camera_id}/timeline")
async def get_timeline_segments(
    camera_id: str,
    date: str = Query(..., regex="^\d{4}-\d{2}-\d{2}$"),
    start_hour: Optional[int] = Query(None, ge=0, le=23),
    end_hour: Optional[int] = Query(None, ge=0, le=23)
):
    """
    Get timeline segments for a specific date
    
    Returns:
    {
        "camera_id": "3",
        "date": "2025-07-31",
        "segments": [
            {
                "filename": "camera_3_20250731_000329_600.avi",
                "start_time": "2025-07-31T00:03:29Z",
                "end_time": "2025-07-31T00:13:29Z",
                "duration_seconds": 600,
                "file_size": 536870912,
                "file_path": "recordings/camera_3/2025/07/31/00/camera_3_20250731_000329_600.avi",
                "type": "continuous",
                "has_gap_before": false,
                "gap_duration": 0
            }
        ],
        "total_segments": 144,
        "total_duration": 86400,
        "total_size": 77309411328,
        "coverage_percentage": 100.0
    }
    """
```

### 3. Video Streaming Endpoint
Streams video segments with HTTP 206 Partial Content support for seeking.

```python
@router.get("/api/v1/recordings/stream/{segment_filename}")
async def stream_video_segment(
    segment_filename: str,
    range: Optional[str] = Header(None)
):
    """
    Stream video segment with seek support
    
    Headers:
        Range: bytes=0-1024000
    
    Returns:
        Binary video stream with appropriate headers
        Supports HTTP 206 Partial Content for video seeking
    """
```

Implementation requirements:
- Parse Range header for byte-range requests
- Return 206 Partial Content with Content-Range header
- Support full file streaming if no range specified
- Handle invalid range requests gracefully

### 4. Recording Details Endpoint
Provides comprehensive statistics for a specific date.

```python
@router.get("/api/v1/recordings/cameras/{camera_id}/details")
async def get_recording_details(
    camera_id: str,
    date: str = Query(..., regex="^\d{4}-\d{2}-\d{2}$")
):
    """
    Get detailed recording statistics
    
    Returns:
    {
        "camera_id": "3",
        "date": "2025-07-31",
        "stats": {
            "total_duration": 86400,
            "total_size": 77309411328,
            "total_size_formatted": "72.0 GB",
            "segment_count": 144,
            "average_segment_size": 536870912,
            "recording_percentage": 100.0,
            "gaps_count": 0,
            "gaps_duration": 0,
            "video_codec": "h264",
            "video_quality": "4K (3840x2160) @ 30fps",
            "average_bitrate": 7153778,
            "compression_ratio": "10:1"
        },
        "hourly_breakdown": {
            "0": {"segments": 6, "duration": 3600, "size": 3221225472},
            "1": {"segments": 6, "duration": 3600, "size": 3221225472},
            // ... all 24 hours
        }
    }
    """
```

### 5. Segment Search Endpoint
Advanced search functionality for finding specific recordings.

```python
@router.post("/api/v1/recordings/cameras/{camera_id}/search")
async def search_segments(
    camera_id: str,
    search_params: SegmentSearchParams
):
    """
    Search recordings with filters
    
    Request Body:
    {
        "start_date": "2025-07-01",
        "end_date": "2025-07-31",
        "start_time": "18:00:00",  # Optional
        "end_time": "06:00:00",    # Optional
        "min_duration": 300,        # Optional (seconds)
        "max_duration": 1200,       # Optional (seconds)
        "include_gaps": false       # Optional
    }
    
    Returns:
    {
        "total_results": 248,
        "total_duration": 148800,
        "total_size": 133143986176,
        "segments": [
            {
                "filename": "camera_3_20250731_180329_600.avi",
                "date": "2025-07-31",
                "start_time": "2025-07-31T18:03:29Z",
                "end_time": "2025-07-31T18:13:29Z",
                "duration_seconds": 600,
                "file_size": 536870912
            }
        ]
    }
    """
```

### 6. Storage Management Endpoints

#### Storage Report
```python
@router.get("/api/v1/storage/report")
async def get_storage_report():
    """
    Get comprehensive storage statistics
    
    Returns:
    {
        "storage_limit_gb": 10,
        "storage_limit_bytes": 10737418240,
        "total_used_bytes": 8589934592,
        "total_used_gb": 8.0,
        "percentage_used": 80.0,
        "available_bytes": 2147483648,
        "available_gb": 2.0,
        "cameras": {
            "3": {
                "total_size": 8589934592,
                "total_segments": 144,
                "oldest_recording": "2025-07-01T00:03:29Z",
                "newest_recording": "2025-07-31T23:53:29Z"
            }
        },
        "cleanup_required": false,
        "estimated_days_remaining": 2.5
    }
    """
```

#### Manual Cleanup Trigger
```python
@router.post("/api/v1/storage/cleanup")
async def trigger_storage_cleanup(
    target_size_gb: Optional[float] = Query(None, le=10),
    delete_before_date: Optional[str] = Query(None)
):
    """Manually trigger storage cleanup"""
```

## Database Schema

### SQLite Index Tables

```sql
-- Segment metadata table
CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    camera_id TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds INTEGER NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    video_codec TEXT DEFAULT 'h264',
    video_width INTEGER DEFAULT 3840,
    video_height INTEGER DEFAULT 2160,
    video_fps INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_compressed BOOLEAN DEFAULT TRUE,
    compression_ratio REAL,
    has_audio BOOLEAN DEFAULT FALSE
);

-- Indexes for efficient queries
CREATE INDEX idx_camera_time ON segments(camera_id, start_time);
CREATE INDEX idx_filename ON segments(filename);
CREATE INDEX idx_date ON segments(date(start_time));

-- Daily summary cache
CREATE TABLE IF NOT EXISTS daily_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT NOT NULL,
    date DATE NOT NULL,
    total_segments INTEGER DEFAULT 0,
    total_duration_seconds INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    first_segment_time TIMESTAMP,
    last_segment_time TIMESTAMP,
    coverage_percentage REAL DEFAULT 0.0,
    gaps_count INTEGER DEFAULT 0,
    gaps_duration_seconds INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(camera_id, date)
);

-- Storage tracking
CREATE TABLE IF NOT EXISTS storage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_size_bytes INTEGER NOT NULL,
    segment_count INTEGER NOT NULL,
    camera_count INTEGER NOT NULL,
    oldest_segment_date DATE,
    newest_segment_date DATE
);
```

## Service Implementation

### Recording Index Service

```python
import aiosqlite
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import os

class RecordingIndexService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    async def get_calendar_data(self, camera_id: str, year: int, month: int) -> Dict:
        """Get calendar data with recording availability"""
        async with aiosqlite.connect(self.db_path) as db:
            # Query daily summaries for the month
            query = """
                SELECT 
                    date,
                    total_duration_seconds,
                    total_size_bytes,
                    coverage_percentage
                FROM daily_summaries
                WHERE camera_id = ? 
                AND strftime('%Y', date) = ?
                AND strftime('%m', date) = ?
            """
            
            cursor = await db.execute(
                query, 
                (camera_id, str(year), str(month).zfill(2))
            )
            rows = await cursor.fetchall()
            
            days = {}
            total_size = 0
            total_duration = 0
            
            for row in rows:
                day = int(row[0].split('-')[2])
                days[str(day)] = {
                    "has_recordings": True,
                    "total_duration": row[1],
                    "total_size": row[2],
                    "recording_percentage": row[3]
                }
                total_size += row[2]
                total_duration += row[1]
            
            return {
                "year": year,
                "month": month,
                "days": days,
                "total_size": total_size,
                "total_duration": total_duration
            }
    
    async def get_timeline_segments(
        self, 
        camera_id: str, 
        date_str: str,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None
    ) -> Dict:
        """Get detailed segment list for timeline"""
        async with aiosqlite.connect(self.db_path) as db:
            # Build query with optional hour filtering
            query = """
                SELECT 
                    filename,
                    start_time,
                    end_time,
                    duration_seconds,
                    file_size_bytes,
                    file_path
                FROM segments
                WHERE camera_id = ?
                AND date(start_time) = ?
            """
            params = [camera_id, date_str]
            
            if start_hour is not None:
                query += " AND cast(strftime('%H', start_time) as integer) >= ?"
                params.append(start_hour)
            
            if end_hour is not None:
                query += " AND cast(strftime('%H', start_time) as integer) <= ?"
                params.append(end_hour)
                
            query += " ORDER BY start_time"
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            segments = []
            prev_end_time = None
            
            for row in rows:
                segment = {
                    "filename": row[0],
                    "start_time": row[1],
                    "end_time": row[2],
                    "duration_seconds": row[3],
                    "file_size": row[4],
                    "file_path": row[5],
                    "type": "continuous",
                    "has_gap_before": False,
                    "gap_duration": 0
                }
                
                # Check for gaps
                if prev_end_time:
                    gap = (datetime.fromisoformat(row[1]) - 
                          datetime.fromisoformat(prev_end_time)).total_seconds()
                    if gap > 60:  # More than 1 minute gap
                        segment["has_gap_before"] = True
                        segment["gap_duration"] = int(gap)
                
                segments.append(segment)
                prev_end_time = row[2]
            
            # Calculate totals
            total_duration = sum(s["duration_seconds"] for s in segments)
            total_size = sum(s["file_size"] for s in segments)
            coverage = (total_duration / 86400) * 100 if segments else 0
            
            return {
                "camera_id": camera_id,
                "date": date_str,
                "segments": segments,
                "total_segments": len(segments),
                "total_duration": total_duration,
                "total_size": total_size,
                "coverage_percentage": round(coverage, 1)
            }
```

### Video Streaming Service

```python
from fastapi import Response, HTTPException
from fastapi.responses import StreamingResponse
import aiofiles
import os
from typing import Optional, Tuple

class VideoStreamingService:
    def __init__(self, recordings_base_path: str):
        self.base_path = recordings_base_path
    
    async def stream_segment(
        self, 
        segment_path: str, 
        range_header: Optional[str] = None
    ) -> StreamingResponse:
        """Stream video with HTTP 206 Partial Content support"""
        
        file_path = os.path.join(self.base_path, segment_path)
        
        if not os.path.exists(file_path):
            raise HTTPException(404, "Video segment not found")
        
        file_size = os.path.getsize(file_path)
        
        # Parse range header
        start = 0
        end = file_size - 1
        
        if range_header:
            try:
                range_str = range_header.replace("bytes=", "")
                range_parts = range_str.split("-")
                start = int(range_parts[0]) if range_parts[0] else 0
                end = int(range_parts[1]) if range_parts[1] else file_size - 1
            except:
                raise HTTPException(400, "Invalid range header")
        
        # Validate range
        if start >= file_size or end >= file_size or start > end:
            raise HTTPException(416, "Requested range not satisfiable")
        
        # Create response headers
        headers = {
            "Content-Type": "video/mp4",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Range": f"bytes {start}-{end}/{file_size}",
        }
        
        async def stream_file():
            async with aiofiles.open(file_path, 'rb') as file:
                await file.seek(start)
                chunk_size = 1024 * 1024  # 1MB chunks
                current = start
                
                while current <= end:
                    remaining = end - current + 1
                    size = min(chunk_size, remaining)
                    data = await file.read(size)
                    if not data:
                        break
                    current += len(data)
                    yield data
        
        return StreamingResponse(
            stream_file(),
            status_code=206 if range_header else 200,
            headers=headers,
            media_type="video/mp4"
        )
```

### Background Tasks

```python
import asyncio
from datetime import datetime, timedelta

class RecordingMaintenanceService:
    def __init__(self, index_service: RecordingIndexService, storage_limit_gb: int = 10):
        self.index_service = index_service
        self.storage_limit_bytes = storage_limit_gb * 1024 * 1024 * 1024
        
    async def update_daily_summaries(self):
        """Update daily summary cache - run hourly"""
        # Implementation to aggregate segment data into daily summaries
        pass
    
    async def check_storage_limit(self) -> Dict:
        """Check if storage limit is exceeded"""
        async with aiosqlite.connect(self.index_service.db_path) as db:
            cursor = await db.execute(
                "SELECT SUM(file_size_bytes) FROM segments"
            )
            total_size = (await cursor.fetchone())[0] or 0
            
            return {
                "total_size": total_size,
                "limit": self.storage_limit_bytes,
                "percentage_used": (total_size / self.storage_limit_bytes) * 100,
                "cleanup_required": total_size > self.storage_limit_bytes * 0.9
            }
    
    async def cleanup_old_recordings(self, target_size_bytes: Optional[int] = None):
        """Remove oldest recordings to stay within storage limit"""
        if target_size_bytes is None:
            target_size_bytes = int(self.storage_limit_bytes * 0.8)  # 80% of limit
        
        # Get current size
        storage_info = await self.check_storage_limit()
        current_size = storage_info["total_size"]
        
        if current_size <= target_size_bytes:
            return {"cleaned": False, "reason": "Within storage limit"}
        
        # Delete oldest segments until within limit
        async with aiosqlite.connect(self.index_service.db_path) as db:
            cursor = await db.execute(
                """
                SELECT filename, file_path, file_size_bytes
                FROM segments
                ORDER BY start_time ASC
                """
            )
            
            deleted_count = 0
            deleted_size = 0
            
            async for row in cursor:
                if current_size - deleted_size <= target_size_bytes:
                    break
                
                # Delete file
                file_path = row[1]
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_size += row[2]
                    deleted_count += 1
                
                # Remove from database
                await db.execute(
                    "DELETE FROM segments WHERE filename = ?",
                    (row[0],)
                )
            
            await db.commit()
        
        return {
            "cleaned": True,
            "deleted_count": deleted_count,
            "deleted_size": deleted_size,
            "new_total_size": current_size - deleted_size
        }
```

## Performance Optimizations

### 1. Caching Strategy
```python
from functools import lru_cache
import asyncio

class CachedRecordingService:
    def __init__(self, index_service: RecordingIndexService):
        self.index_service = index_service
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    @lru_cache(maxsize=100)
    async def get_cached_calendar_data(self, camera_id: str, year: int, month: int):
        """Cache calendar data for 5 minutes"""
        cache_key = f"calendar_{camera_id}_{year}_{month}"
        
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                return cached_data
        
        data = await self.index_service.get_calendar_data(camera_id, year, month)
        self._cache[cache_key] = (data, datetime.now())
        return data
```

### 2. Database Optimization
- Add composite indexes for common queries
- Use prepared statements for repeated queries
- Implement connection pooling for concurrent requests
- Regular VACUUM operations on SQLite database

### 3. Video Streaming Optimization
- Implement adaptive bitrate based on client bandwidth
- Pre-cache segment metadata for faster access
- Use sendfile() for efficient file streaming
- Consider HLS conversion for better browser compatibility

## Error Handling

### Standard Error Responses
```python
class RecordingError(Exception):
    """Base exception for recording errors"""
    pass

class SegmentNotFoundError(RecordingError):
    """Segment file not found"""
    pass

class StorageLimitExceededError(RecordingError):
    """Storage limit exceeded"""
    pass

# Error handler
@app.exception_handler(RecordingError)
async def recording_error_handler(request: Request, exc: RecordingError):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Integration Points

### 1. Main Recording Service
- Subscribe to segment creation events
- Update index database when new segments are created
- Trigger daily summary updates

### 2. Camera Service
- Validate camera exists before serving recordings
- Check camera recording status
- Sync camera configuration changes

### 3. Frontend Integration
- CORS configuration for cross-origin requests
- WebSocket notifications for real-time updates
- Progress events for large file downloads

## Testing Checklist

- [ ] Calendar data returns correct recording days
- [ ] Timeline segments are properly ordered
- [ ] Video streaming supports seeking (range requests)
- [ ] Storage cleanup removes oldest files first
- [ ] Database indexes improve query performance
- [ ] Error handling covers all edge cases
- [ ] API responses match documented schemas
- [ ] 10GB storage limit is enforced
- [ ] Concurrent requests are handled properly
- [ ] Memory usage remains stable during streaming

## Deployment Notes

1. Ensure recording directory has proper permissions
2. Configure systemd service for background tasks
3. Set up log rotation for service logs
4. Monitor disk space usage
5. Configure CORS for frontend access
6. Set appropriate nginx proxy timeouts for video streaming
7. Enable HTTP/2 for better streaming performance