# 🏗️ Robust 24/7 Security Camera Architecture

**Based on Your Current Microservices System**  
**Date**: 2025-07-25  
**Status**: 🎯 **PRODUCTION-READY RECOMMENDATION**

## 🔍 Current System Analysis

From your documentation, you already have:
- ✅ **Microservices Architecture** (camera_management, video_processing, detection services)
- ✅ **Docker Infrastructure** with proper CI/CD
- ✅ **Event-Driven Architecture** with messaging
- ✅ **Professional Backend** with FastAPI
- ✅ **Database Design** with migrations
- ✅ **Monitoring & Health Checks**

**This is enterprise-grade foundation!**

## 🎯 Recommendation: Extend Your Existing Services

### Don't Start From Scratch - Enhance What You Have

Your current `video_processing` service already exists. We should **extend it** for 24/7 recording rather than build separate systems.

## 🏗️ Robust Architecture (Production-Grade)

### 1. Video Processing Service Enhancement

```python
# src/video_processing/domain/services/recording_service.py
class ContinuousRecordingService:
    """
    Enterprise-grade 24/7 recording service
    Integrates with your existing microservices architecture
    """
    
    def __init__(self, 
                 event_bus: EventBus,
                 storage_service: StorageService,
                 camera_service: CameraService,
                 monitoring: MonitoringService):
        self.event_bus = event_bus
        self.storage_service = storage_service
        self.camera_service = camera_service
        self.monitoring = monitoring
        self.recorders = {}
    
    async def start_continuous_recording(self, camera_id: CameraId):
        """Start 24/7 recording for a camera"""
        camera = await self.camera_service.get_camera(camera_id)
        
        recorder = ContinuousRecorder(
            camera=camera,
            storage=self.storage_service,
            event_bus=self.event_bus
        )
        
        await recorder.start()
        self.recorders[camera_id] = recorder
        
        # Publish event to other services
        await self.event_bus.publish(
            RecordingStartedEvent(camera_id, timestamp=datetime.now())
        )
    
    async def handle_camera_online_event(self, event: CameraOnlineEvent):
        """Auto-start recording when camera comes online"""
        await self.start_continuous_recording(event.camera_id)
    
    async def handle_camera_offline_event(self, event: CameraOfflineEvent):
        """Handle camera disconnection gracefully"""
        if event.camera_id in self.recorders:
            await self.recorders[event.camera_id].stop()
            del self.recorders[event.camera_id]
```

### 2. Integration with Your Event System

```python
# Video processing service listens to camera events
class VideoProcessingService:
    def __init__(self):
        self.recording_service = ContinuousRecordingService(...)
        self.event_handlers = {
            CameraAddedEvent: self._handle_camera_added,
            CameraOnlineEvent: self._handle_camera_online,
            CameraOfflineEvent: self._handle_camera_offline,
            CameraDeletedEvent: self._handle_camera_deleted
        }
    
    async def _handle_camera_added(self, event: CameraAddedEvent):
        """Automatically start recording for new cameras"""
        if event.recording_enabled:
            await self.recording_service.start_continuous_recording(event.camera_id)
    
    async def _handle_camera_online(self, event: CameraOnlineEvent):
        """Resume recording when camera comes back online"""
        await self.recording_service.handle_camera_online_event(event)
```

### 3. Storage Service Integration

```python
# src/shared/infrastructure/storage/video_storage_service.py
class VideoStorageService:
    """
    Robust video storage with multiple backends
    Integrates with your existing infrastructure
    """
    
    def __init__(self, config: StorageConfig):
        self.primary_storage = LocalStorageProvider(config.primary_path)
        self.backup_storage = CloudStorageProvider(config.cloud_config) if config.cloud_enabled else None
        self.database = VideoMetadataRepository()
    
    async def store_video_segment(self, segment: VideoSegment) -> StorageResult:
        """Store video segment with redundancy"""
        try:
            # Store locally first (fast)
            local_path = await self.primary_storage.store(segment)
            
            # Store metadata in database
            metadata = VideoMetadata(
                camera_id=segment.camera_id,
                start_time=segment.start_time,
                duration=segment.duration,
                file_path=local_path,
                file_size=segment.size
            )
            await self.database.save(metadata)
            
            # Async backup to cloud (if configured)
            if self.backup_storage:
                asyncio.create_task(
                    self.backup_storage.store(segment, local_path)
                )
            
            return StorageResult(success=True, path=local_path)
            
        except Exception as e:
            # Log error but don't fail the recording
            logger.error(f"Storage failed for segment {segment.id}: {e}")
            return StorageResult(success=False, error=str(e))
```

## 🚀 Implementation Strategy

### Phase 1: Extend Existing Services (1 week)

#### A. Enhance Video Processing Service
```yaml
# Update your existing docker-compose.yml
services:
  video-processing:
    # Your existing service
    environment:
      - RECORDING_ENABLED=true
      - SEGMENT_DURATION=600  # 10 minutes
      - STORAGE_PATH=/recordings
    volumes:
      - recordings_volume:/recordings
    
volumes:
  recordings_volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/lpr/recordings  # Host path for recordings
```

#### B. Database Migration for Recording Metadata
```sql
-- Add to your existing migrations
CREATE TABLE video_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    quality_level TEXT DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_camera_time (camera_id, start_time),
    INDEX idx_time_range (start_time, end_time)
);
```

### Phase 2: Robust Recording Implementation (1 week)

#### A. Production-Grade Recorder
```python
class ProductionRecorder:
    """
    Fault-tolerant, production-ready recorder
    Handles all edge cases and failures gracefully
    """
    
    def __init__(self, camera: Camera, config: RecordingConfig):
        self.camera = camera
        self.config = config
        self.health_monitor = HealthMonitor()
        self.connection_manager = ConnectionManager()
        self.segment_manager = SegmentManager()
        
    async def start_recording(self):
        """Start robust recording with health monitoring"""
        while True:
            try:
                async with self.connection_manager.get_connection(self.camera.rtsp_url) as stream:
                    await self._record_continuous_segments(stream)
                    
            except ConnectionLost:
                await self._handle_connection_lost()
            except CameraOffline:
                await self._handle_camera_offline()
            except StorageError:
                await self._handle_storage_error()
            except Exception as e:
                await self._handle_unexpected_error(e)
    
    async def _record_continuous_segments(self, stream):
        """Record in segments with overlap for seamless playback"""
        current_segment = None
        next_segment = None
        
        while True:
            frame = await stream.get_next_frame()
            
            # Start new segment if needed
            if self._should_start_new_segment():
                next_segment = self.segment_manager.create_new_segment()
                
            # Write to current segment
            if current_segment:
                await current_segment.write_frame(frame)
                
            # Write to next segment for overlap
            if next_segment:
                await next_segment.write_frame(frame)
                
            # Finalize completed segment
            if current_segment and current_segment.is_complete():
                await self._finalize_segment(current_segment)
                current_segment = next_segment
                next_segment = None
```

### Phase 3: Playback Integration (3-5 days)

#### A. Add Playback Endpoints to Your API
```python
# Add to your existing routers
@router.get("/cameras/{camera_id}/recordings")
async def get_camera_recordings(
    camera_id: UUID,
    start_time: datetime,
    end_time: datetime,
    db: AsyncSession = Depends(get_db)
) -> RecordingTimelineResponse:
    """Get recording timeline for playback"""
    
    segments = await recording_service.get_segments_for_timerange(
        camera_id, start_time, end_time
    )
    
    return RecordingTimelineResponse(
        camera_id=camera_id,
        segments=segments,
        total_duration=sum(s.duration for s in segments)
    )

@router.get("/recordings/{segment_id}/stream")
async def stream_recording_segment(segment_id: UUID) -> StreamingResponse:
    """Stream recorded video segment for playback"""
    
    segment = await recording_service.get_segment(segment_id)
    
    return StreamingResponse(
        segment.stream_content(),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )
```

## 🛡️ Robust Features for 24/7 Operation

### 1. Health Monitoring & Self-Healing
```python
class RecordingHealthMonitor:
    """Monitor recording health and auto-recover from issues"""
    
    async def monitor_recording_health(self):
        while True:
            for camera_id, recorder in self.active_recorders.items():
                health = await recorder.get_health_status()
                
                if health.status == HealthStatus.DEGRADED:
                    await self._attempt_recovery(recorder)
                elif health.status == HealthStatus.FAILED:
                    await self._restart_recorder(camera_id)
                    
            await asyncio.sleep(30)  # Check every 30 seconds
```

### 2. Storage Management
```python
class StorageManager:
    """Manage storage with automatic cleanup and monitoring"""
    
    async def manage_storage(self):
        """Run storage management tasks"""
        await self._cleanup_old_recordings()
        await self._monitor_disk_space()
        await self._optimize_storage_layout()
        
    async def _cleanup_old_recordings(self):
        """Remove recordings older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        old_segments = await self.db.get_segments_older_than(cutoff_date)
        
        for segment in old_segments:
            await self._safely_delete_segment(segment)
```

### 3. High Availability Setup
```yaml
# docker-compose.prod.yml - Production setup
services:
  video-processing-primary:
    # Primary recording service
    
  video-processing-standby:
    # Standby service for failover
    
  recordings-storage:
    # Redundant storage setup
    volumes:
      - /mnt/raid1/recordings:/recordings  # RAID for redundancy
```

## 📊 Storage Strategy (Production Scale)

### Storage Architecture
```
/var/lpr/recordings/
├── hot/              # Recent recordings (SSD - fast access)
│   ├── camera_1/     # 7 days
│   └── camera_2/
├── warm/             # Older recordings (HDD - cost effective)
│   ├── camera_1/     # 8-30 days
│   └── camera_2/
└── metadata/         # Database files and indexes
    └── segments.db
```

### Capacity Planning
```python
# Production storage calculations
STORAGE_CONFIG = {
    'cameras_count': 10,                    # Your camera count
    'resolution': '640x480',                # Your resolution
    'fps': 30,                             # Frame rate
    'compression_ratio': 0.1,               # H.264 compression
    'retention_days': 30,                   # Keep 30 days
    
    # Results:
    'daily_per_camera': '~15GB',            # Per camera per day
    'total_daily': '~150GB',                # All cameras
    'total_storage_needed': '~4.5TB'        # 30 days retention
}
```

## ✅ Why This Approach is Robust

### 1. **Leverages Your Existing Architecture**
- Uses your microservices infrastructure
- Integrates with existing event system
- Follows your established patterns

### 2. **Production-Ready Features**
- Health monitoring and auto-recovery
- Redundant storage options
- Graceful failure handling
- Performance monitoring

### 3. **Scalable Design**
- Easy to add more cameras
- Horizontal scaling with multiple services
- Cloud storage integration ready

### 4. **Enterprise Operations**
- Proper logging and monitoring
- CI/CD integration
- Database migrations
- Configuration management

## 🎯 Implementation Timeline

- **Week 1**: Extend video processing service for recording
- **Week 2**: Implement robust recording with health monitoring  
- **Week 3**: Add playback APIs and storage management
- **Week 4**: UI integration and testing

This approach builds on your solid foundation rather than creating separate systems. You'll have enterprise-grade 24/7 recording that integrates seamlessly with your existing architecture.

**Would you like me to detail any specific part of this implementation?**