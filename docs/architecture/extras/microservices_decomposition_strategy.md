# Microservices Decomposition Strategy for LPR System

**Version:** 1.0  
**Date:** 2025-01-09  
**Authors:** System Architecture Team  
**Status:** Active Development  

## Table of Contents

1. [Decomposition Overview](#decomposition-overview)
2. [Service Identification](#service-identification)
3. [Service Boundaries](#service-boundaries)
4. [Communication Patterns](#communication-patterns)
5. [Data Management](#data-management)
6. [Service Definitions](#service-definitions)
7. [Migration Strategy](#migration-strategy)
8. [Deployment Architecture](#deployment-architecture)
9. [Monitoring and Observability](#monitoring-and-observability)
10. [Service Governance](#service-governance)

## Decomposition Overview

The microservices decomposition strategy transforms the monolithic LPR system into a distributed architecture following Domain-Driven Design principles. Each microservice represents a bounded context with clear responsibilities and well-defined interfaces.

### Decomposition Principles

#### 1. Domain-Driven Decomposition
- Services aligned with business capabilities
- Bounded contexts define service boundaries
- Ubiquitous language within each service
- Minimized cross-service dependencies

#### 2. Single Responsibility Principle
- Each service has one reason to change
- Clear and focused business purpose
- Autonomous teams can own entire service
- Independent deployment and scaling

#### 3. Data Ownership
- Each service owns its data
- No shared databases between services
- Service-specific data models
- Eventual consistency across services

#### 4. Failure Isolation
- Service failures don't cascade
- Circuit breakers and bulkheads
- Graceful degradation patterns
- Independent recovery mechanisms

### Service Identification Criteria

#### Business Capability Alignment
- Clear business value proposition
- Distinct user workflows
- Separate organizational responsibilities
- Different change frequencies

#### Technical Characteristics
- Different scalability requirements
- Varying performance needs
- Distinct technology stacks
- Independent deployment cycles

#### Team Structure
- Can be owned by single team
- Clear service boundaries
- Manageable complexity
- Well-defined interfaces

## Service Identification

### Core Services

#### 1. Camera Management Service
**Business Capability**: Manage physical cameras and their configurations
**Key Entities**: Camera, CameraConfiguration, HealthMetrics
**Primary Users**: System administrators, operators
**Change Frequency**: Low to medium

#### 2. Video Processing Service
**Business Capability**: Process video streams and manage recordings
**Key Entities**: VideoStream, Frame, Recording
**Primary Users**: System (automated), operators
**Change Frequency**: Medium

#### 3. Detection Service
**Business Capability**: Detect and recognize license plates
**Key Entities**: Detection, LicensePlate, Vehicle
**Primary Users**: System (automated), security personnel
**Change Frequency**: High (ML model updates)

#### 4. Analytics Service
**Business Capability**: Generate insights and reports from detection data
**Key Entities**: Metric, Insight, Report
**Primary Users**: Business users, managers
**Change Frequency**: Medium to high

#### 5. Notification Service
**Business Capability**: Send alerts and notifications
**Key Entities**: Alert, Notification, Subscription
**Primary Users**: System (automated), all user types
**Change Frequency**: Low

#### 6. User Management Service
**Business Capability**: Manage user accounts and permissions
**Key Entities**: User, Role, Permission
**Primary Users**: Administrators
**Change Frequency**: Low

### Supporting Services

#### 7. Configuration Service
**Business Capability**: Manage system-wide configuration
**Key Entities**: Configuration, Setting, Policy
**Primary Users**: Administrators, other services
**Change Frequency**: Low

#### 8. Audit Service
**Business Capability**: Track system activities and changes
**Key Entities**: AuditLog, Event, Activity
**Primary Users**: Administrators, compliance officers
**Change Frequency**: Low

#### 9. File Storage Service
**Business Capability**: Store and retrieve images and videos
**Key Entities**: File, StorageLocation, Metadata
**Primary Users**: Other services
**Change Frequency**: Low

#### 10. Gateway Service
**Business Capability**: API routing and aggregation
**Key Entities**: Route, Policy, RateLimit
**Primary Users**: External clients, other services
**Change Frequency**: Medium

## Service Boundaries

### Service Interaction Map

```
                    ┌─────────────────────┐
                    │   Gateway Service   │
                    │  (API Routing)      │
                    └─────────┬───────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
    │ Camera Mgmt    │ │ Video Proc  │ │ Detection      │
    │ Service        │ │ Service     │ │ Service        │
    └───────┬────────┘ └──────┬──────┘ └───────┬────────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Analytics Service │
                    │                   │
                    └─────────┬─────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
    │ Notification   │ │ User Mgmt   │ │ Configuration  │
    │ Service        │ │ Service     │ │ Service        │
    └────────────────┘ └─────────────┘ └────────────────┘
```

### Data Flow Patterns

#### 1. Camera to Detection Flow
```
Camera Management → Video Processing → Detection → Analytics
```

#### 2. Configuration Distribution
```
Configuration Service → All Services (via event bus)
```

#### 3. Notification Flow
```
Any Service → Notification Service → External Systems
```

#### 4. Audit Trail
```
All Services → Audit Service → Persistent Storage
```

## Communication Patterns

### Synchronous Communication

#### HTTP/REST APIs
```python
# Camera Management Service API
class CameraManagementAPI:
    @router.get("/cameras/{camera_id}")
    async def get_camera(camera_id: str) -> CameraResponse:
        """Get camera details"""
        pass
    
    @router.post("/cameras")
    async def create_camera(camera: CreateCameraRequest) -> CameraResponse:
        """Create new camera"""
        pass

# Video Processing Service API
class VideoProcessingAPI:
    @router.post("/streams")
    async def start_stream(stream_request: StartStreamRequest) -> StreamResponse:
        """Start video stream processing"""
        pass
    
    @router.get("/streams/{stream_id}/frames")
    async def get_frames(stream_id: str) -> FrameListResponse:
        """Get processed frames"""
        pass
```

#### Internal Service Communication
```python
# Service-to-service communication
class DetectionServiceClient:
    def __init__(self, base_url: str, http_client: httpx.AsyncClient):
        self.base_url = base_url
        self.http_client = http_client
    
    async def detect_plates(self, image_data: bytes) -> DetectionResult:
        """Call detection service"""
        response = await self.http_client.post(
            f"{self.base_url}/detect",
            files={"image": image_data}
        )
        return DetectionResult.parse_obj(response.json())

# Circuit breaker pattern
class CircuitBreakerClient:
    def __init__(self, service_client: DetectionServiceClient):
        self.service_client = service_client
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=httpx.HTTPError
        )
    
    async def detect_plates(self, image_data: bytes) -> DetectionResult:
        return await self.circuit_breaker.call(
            self.service_client.detect_plates,
            image_data
        )
```

### Asynchronous Communication

#### Event-Driven Architecture
```python
# Domain events
@dataclass
class CameraActivatedEvent:
    camera_id: str
    timestamp: datetime
    configuration: CameraConfiguration

@dataclass
class DetectionCompletedEvent:
    detection_id: str
    camera_id: str
    plate_number: Optional[str]
    confidence: float
    timestamp: datetime

# Event publishers
class EventPublisher:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    async def publish(self, event: DomainEvent) -> None:
        await self.event_bus.publish(
            topic=event.__class__.__name__,
            message=event.to_json()
        )

# Event handlers
class DetectionEventHandler:
    def __init__(self, analytics_service: AnalyticsService):
        self.analytics_service = analytics_service
    
    async def handle_detection_completed(self, event: DetectionCompletedEvent) -> None:
        """Handle detection completion event"""
        await self.analytics_service.record_detection_metric(
            camera_id=event.camera_id,
            confidence=event.confidence,
            timestamp=event.timestamp
        )
```

#### Message Queue Integration
```python
# Redis Pub/Sub implementation
class RedisEventBus:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    async def publish(self, topic: str, message: str) -> None:
        await self.redis_client.publish(topic, message)
    
    async def subscribe(self, topic: str, handler: Callable) -> None:
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(topic)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                await handler(message['data'])

# RabbitMQ implementation
class RabbitMQEventBus:
    def __init__(self, connection: aio_pika.Connection):
        self.connection = connection
    
    async def publish(self, topic: str, message: str) -> None:
        channel = await self.connection.channel()
        exchange = await channel.declare_exchange(
            'lpr_events',
            aio_pika.ExchangeType.TOPIC
        )
        
        await exchange.publish(
            aio_pika.Message(message.encode()),
            routing_key=topic
        )
```

### Service Discovery

#### Dynamic Service Discovery
```python
# Service registry
class ServiceRegistry:
    def __init__(self, consul_client: consul.Consul):
        self.consul_client = consul_client
    
    async def register_service(self, service_name: str, host: str, port: int) -> None:
        """Register service with discovery"""
        await self.consul_client.agent.service.register(
            name=service_name,
            service_id=f"{service_name}-{host}-{port}",
            address=host,
            port=port,
            check=consul.Check.http(f"http://{host}:{port}/health", interval="10s")
        )
    
    async def discover_service(self, service_name: str) -> List[ServiceInstance]:
        """Discover service instances"""
        services = await self.consul_client.health.service(service_name, passing=True)
        return [
            ServiceInstance(
                host=service['Service']['Address'],
                port=service['Service']['Port']
            )
            for service in services[1]
        ]

# Service client with discovery
class ServiceClient:
    def __init__(self, service_name: str, registry: ServiceRegistry):
        self.service_name = service_name
        self.registry = registry
        self.load_balancer = RoundRobinLoadBalancer()
    
    async def make_request(self, endpoint: str, **kwargs) -> Any:
        """Make request to service with load balancing"""
        instances = await self.registry.discover_service(self.service_name)
        instance = self.load_balancer.select(instances)
        
        url = f"http://{instance.host}:{instance.port}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, **kwargs)
            return response.json()
```

## Data Management

### Database per Service

#### Service-Specific Databases
```python
# Camera Management Service - PostgreSQL
class CameraRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def save_camera(self, camera: Camera) -> None:
        stmt = insert(CameraTable).values(
            id=camera.id,
            name=camera.name,
            ip_address=camera.ip_address,
            configuration=camera.configuration.to_dict()
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

# Detection Service - MongoDB
class DetectionRepository:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.db = mongo_client.lpr_detection
        self.collection = self.db.detections
    
    async def save_detection(self, detection: Detection) -> None:
        await self.collection.insert_one(detection.to_dict())

# Analytics Service - InfluxDB
class MetricsRepository:
    def __init__(self, influx_client: InfluxDBClient):
        self.client = influx_client
    
    async def save_metric(self, metric: Metric) -> None:
        point = Point("detection_metrics") \
            .tag("camera_id", metric.camera_id) \
            .field("confidence", metric.confidence) \
            .time(metric.timestamp)
        
        await self.client.write_api().write(
            bucket="lpr_metrics",
            record=point
        )
```

### Data Consistency Patterns

#### Saga Pattern
```python
class DetectionProcessingSaga:
    def __init__(self, 
                 video_service: VideoProcessingService,
                 detection_service: DetectionService,
                 analytics_service: AnalyticsService):
        self.video_service = video_service
        self.detection_service = detection_service
        self.analytics_service = analytics_service
        self.compensation_actions = []
    
    async def execute(self, frame_data: FrameData) -> None:
        """Execute detection processing saga"""
        try:
            # Step 1: Process frame
            processed_frame = await self.video_service.process_frame(frame_data)
            self.compensation_actions.append(
                lambda: self.video_service.delete_processed_frame(processed_frame.id)
            )
            
            # Step 2: Detect plates
            detection = await self.detection_service.detect_plates(processed_frame)
            self.compensation_actions.append(
                lambda: self.detection_service.delete_detection(detection.id)
            )
            
            # Step 3: Update analytics
            await self.analytics_service.record_detection(detection)
            
        except Exception as e:
            await self.compensate()
            raise e
    
    async def compensate(self) -> None:
        """Execute compensation actions in reverse order"""
        for action in reversed(self.compensation_actions):
            try:
                await action()
            except Exception as e:
                logger.error(f"Compensation action failed: {e}")
```

#### Event Sourcing
```python
class EventSourcedAggregate:
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self.uncommitted_events = []
    
    def apply_event(self, event: DomainEvent) -> None:
        """Apply event to aggregate"""
        self.version += 1
        self.uncommitted_events.append(event)
        self._handle_event(event)
    
    def mark_events_as_committed(self) -> None:
        """Mark events as committed"""
        self.uncommitted_events.clear()
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get uncommitted events"""
        return self.uncommitted_events.copy()

class CameraAggregate(EventSourcedAggregate):
    def __init__(self, camera_id: str):
        super().__init__(camera_id)
        self.name = ""
        self.status = CameraStatus.INACTIVE
        self.configuration = None
    
    def register_camera(self, name: str, ip_address: str) -> None:
        """Register new camera"""
        event = CameraRegisteredEvent(
            camera_id=self.aggregate_id,
            name=name,
            ip_address=ip_address
        )
        self.apply_event(event)
    
    def _handle_event(self, event: DomainEvent) -> None:
        """Handle domain event"""
        if isinstance(event, CameraRegisteredEvent):
            self.name = event.name
            self.status = CameraStatus.REGISTERED
        elif isinstance(event, CameraActivatedEvent):
            self.status = CameraStatus.ACTIVE
```

## Service Definitions

### 1. Camera Management Service

#### Service Overview
```python
class CameraManagementService:
    """
    Manages physical cameras and their configurations
    
    Responsibilities:
    - Camera registration and deregistration
    - Configuration management
    - Health monitoring
    - Status tracking
    """
    
    def __init__(self, 
                 camera_repository: CameraRepository,
                 health_monitor: HealthMonitor,
                 event_publisher: EventPublisher):
        self.camera_repository = camera_repository
        self.health_monitor = health_monitor
        self.event_publisher = event_publisher
```

#### API Endpoints
```python
@router.post("/cameras")
async def register_camera(camera: RegisterCameraRequest) -> CameraResponse:
    """Register new camera"""
    pass

@router.get("/cameras")
async def list_cameras(filters: CameraFilters) -> CameraListResponse:
    """List cameras with filtering"""
    pass

@router.get("/cameras/{camera_id}")
async def get_camera(camera_id: str) -> CameraResponse:
    """Get camera details"""
    pass

@router.put("/cameras/{camera_id}/configuration")
async def update_configuration(
    camera_id: str, 
    config: ConfigurationRequest
) -> ConfigurationResponse:
    """Update camera configuration"""
    pass

@router.get("/cameras/{camera_id}/health")
async def get_health_status(camera_id: str) -> HealthStatusResponse:
    """Get camera health status"""
    pass
```

#### Database Schema
```sql
-- Camera Management Database
CREATE TABLE cameras (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    ip_address INET NOT NULL UNIQUE,
    location VARCHAR(200),
    status VARCHAR(20) DEFAULT 'inactive',
    configuration JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE camera_health (
    camera_id UUID REFERENCES cameras(id),
    response_time INTEGER,
    connection_status VARCHAR(20),
    error_rate FLOAT,
    last_check TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (camera_id, last_check)
);
```

### 2. Video Processing Service

#### Service Overview
```python
class VideoProcessingService:
    """
    Processes video streams and manages recordings
    
    Responsibilities:
    - Stream ingestion and processing
    - Frame extraction and buffering
    - Video recording management
    - Quality assessment
    """
    
    def __init__(self,
                 stream_manager: StreamManager,
                 frame_processor: FrameProcessor,
                 recording_service: RecordingService):
        self.stream_manager = stream_manager
        self.frame_processor = frame_processor
        self.recording_service = recording_service
```

#### API Endpoints
```python
@router.post("/streams")
async def start_stream(stream_request: StartStreamRequest) -> StreamResponse:
    """Start video stream processing"""
    pass

@router.delete("/streams/{stream_id}")
async def stop_stream(stream_id: str) -> None:
    """Stop video stream processing"""
    pass

@router.get("/streams/{stream_id}/frames")
async def get_frames(stream_id: str, limit: int = 10) -> FrameListResponse:
    """Get processed frames"""
    pass

@router.post("/recordings")
async def start_recording(recording_request: RecordingRequest) -> RecordingResponse:
    """Start video recording"""
    pass

@router.get("/recordings/{recording_id}")
async def get_recording(recording_id: str) -> RecordingResponse:
    """Get recording details"""
    pass
```

### 3. Detection Service

#### Service Overview
```python
class DetectionService:
    """
    Detects and recognizes license plates in images
    
    Responsibilities:
    - License plate detection using YOLO
    - OCR processing for text recognition
    - Confidence scoring and validation
    - Enhancement processing
    """
    
    def __init__(self,
                 detector: LicensePlateDetector,
                 ocr_engine: OCREngine,
                 validator: PlateValidator,
                 enhancer: PlateEnhancer):
        self.detector = detector
        self.ocr_engine = ocr_engine
        self.validator = validator
        self.enhancer = enhancer
```

#### API Endpoints
```python
@router.post("/detect")
async def detect_plates(image: UploadFile) -> DetectionResponse:
    """Detect license plates in image"""
    pass

@router.get("/detections/{detection_id}")
async def get_detection(detection_id: str) -> DetectionResponse:
    """Get detection details"""
    pass

@router.post("/detections/{detection_id}/enhance")
async def enhance_detection(detection_id: str) -> EnhancementResponse:
    """Enhance detection accuracy"""
    pass

@router.get("/models/status")
async def get_model_status() -> ModelStatusResponse:
    """Get AI model status"""
    pass
```

### 4. Analytics Service

#### Service Overview
```python
class AnalyticsService:
    """
    Generates insights and reports from detection data
    
    Responsibilities:
    - Metrics collection and aggregation
    - Pattern analysis and insights
    - Report generation
    - Alert management
    """
    
    def __init__(self,
                 metrics_collector: MetricsCollector,
                 pattern_analyzer: PatternAnalyzer,
                 report_generator: ReportGenerator,
                 alert_manager: AlertManager):
        self.metrics_collector = metrics_collector
        self.pattern_analyzer = pattern_analyzer
        self.report_generator = report_generator
        self.alert_manager = alert_manager
```

#### API Endpoints
```python
@router.get("/metrics/realtime")
async def get_realtime_metrics() -> RealTimeMetricsResponse:
    """Get real-time system metrics"""
    pass

@router.get("/analytics/traffic")
async def get_traffic_analytics(
    location: str,
    time_range: TimeRange
) -> TrafficAnalyticsResponse:
    """Get traffic analytics for location"""
    pass

@router.post("/reports")
async def generate_report(report_request: ReportRequest) -> ReportResponse:
    """Generate analytics report"""
    pass

@router.get("/reports/{report_id}")
async def get_report(report_id: str) -> ReportResponse:
    """Get generated report"""
    pass
```

### 5. Notification Service

#### Service Overview
```python
class NotificationService:
    """
    Sends alerts and notifications
    
    Responsibilities:
    - Alert management and delivery
    - Notification preferences
    - External system integration
    - Delivery tracking
    """
    
    def __init__(self,
                 alert_manager: AlertManager,
                 notification_channels: List[NotificationChannel],
                 subscription_manager: SubscriptionManager):
        self.alert_manager = alert_manager
        self.notification_channels = notification_channels
        self.subscription_manager = subscription_manager
```

#### API Endpoints
```python
@router.post("/alerts")
async def create_alert(alert: CreateAlertRequest) -> AlertResponse:
    """Create new alert"""
    pass

@router.get("/alerts")
async def list_alerts(filters: AlertFilters) -> AlertListResponse:
    """List alerts with filtering"""
    pass

@router.post("/subscriptions")
async def create_subscription(
    subscription: SubscriptionRequest
) -> SubscriptionResponse:
    """Create notification subscription"""
    pass

@router.get("/delivery-status/{notification_id}")
async def get_delivery_status(notification_id: str) -> DeliveryStatusResponse:
    """Get notification delivery status"""
    pass
```

## Migration Strategy

### Phase 1: Extract Core Services (Weeks 1-4)

#### 1.1 Camera Management Service
```python
# Step 1: Extract camera-related code
class CameraManagementService:
    def __init__(self, legacy_service: LegacyService):
        self.legacy_service = legacy_service
    
    async def migrate_cameras(self) -> None:
        """Migrate cameras from legacy system"""
        legacy_cameras = await self.legacy_service.get_all_cameras()
        
        for legacy_camera in legacy_cameras:
            camera = Camera(
                id=legacy_camera.id,
                name=legacy_camera.name,
                ip_address=legacy_camera.ip_address
            )
            await self.camera_repository.save(camera)

# Step 2: Implement dual-write pattern
class DualWriteCameraRepository:
    def __init__(self, 
                 legacy_repo: LegacyCameraRepository,
                 new_repo: NewCameraRepository):
        self.legacy_repo = legacy_repo
        self.new_repo = new_repo
    
    async def save_camera(self, camera: Camera) -> None:
        """Save to both legacy and new systems"""
        await self.legacy_repo.save(camera)
        await self.new_repo.save(camera)
```

#### 1.2 Video Processing Service
```python
# Step 1: Extract video processing logic
class VideoProcessingMigration:
    def __init__(self, legacy_processor: LegacyVideoProcessor):
        self.legacy_processor = legacy_processor
    
    async def migrate_stream_processing(self) -> None:
        """Migrate stream processing to new service"""
        active_streams = await self.legacy_processor.get_active_streams()
        
        for stream in active_streams:
            new_stream = VideoStream(
                id=stream.id,
                camera_id=stream.camera_id,
                configuration=stream.configuration
            )
            await self.start_new_stream_processing(new_stream)
```

### Phase 2: Business Logic Services (Weeks 5-8)

#### 2.1 Detection Service
```python
# Step 1: Extract detection logic
class DetectionServiceMigration:
    def __init__(self, 
                 legacy_detector: LegacyDetector,
                 new_detector: NewDetector):
        self.legacy_detector = legacy_detector
        self.new_detector = new_detector
    
    async def migrate_detection_logic(self) -> None:
        """Migrate detection logic to new service"""
        # Implement feature flag for gradual migration
        if self.feature_flags.is_enabled('new_detection_service'):
            return await self.new_detector.detect_plates(image_data)
        else:
            return await self.legacy_detector.detect_plates(image_data)
```

#### 2.2 Analytics Service
```python
# Step 1: Extract analytics logic
class AnalyticsServiceMigration:
    def __init__(self, legacy_analytics: LegacyAnalytics):
        self.legacy_analytics = legacy_analytics
    
    async def migrate_analytics_data(self) -> None:
        """Migrate historical analytics data"""
        # Batch migration of historical data
        batch_size = 1000
        offset = 0
        
        while True:
            batch = await self.legacy_analytics.get_metrics_batch(
                offset=offset,
                limit=batch_size
            )
            
            if not batch:
                break
            
            for metric in batch:
                new_metric = Metric(
                    name=metric.name,
                    value=metric.value,
                    timestamp=metric.timestamp
                )
                await self.new_analytics.save_metric(new_metric)
            
            offset += batch_size
```

### Phase 3: Supporting Services (Weeks 9-12)

#### 3.1 Notification Service
```python
class NotificationServiceMigration:
    def __init__(self, legacy_notifier: LegacyNotifier):
        self.legacy_notifier = legacy_notifier
    
    async def migrate_notification_rules(self) -> None:
        """Migrate notification rules to new service"""
        legacy_rules = await self.legacy_notifier.get_all_rules()
        
        for rule in legacy_rules:
            new_rule = NotificationRule(
                id=rule.id,
                condition=rule.condition,
                action=rule.action,
                recipients=rule.recipients
            )
            await self.notification_service.save_rule(new_rule)
```

#### 3.2 User Management Service
```python
class UserManagementMigration:
    def __init__(self, legacy_auth: LegacyAuth):
        self.legacy_auth = legacy_auth
    
    async def migrate_users(self) -> None:
        """Migrate user accounts to new service"""
        legacy_users = await self.legacy_auth.get_all_users()
        
        for user in legacy_users:
            new_user = User(
                id=user.id,
                username=user.username,
                email=user.email,
                roles=user.roles
            )
            await self.user_service.save_user(new_user)
```

### Migration Utilities

#### Data Consistency Checker
```python
class DataConsistencyChecker:
    def __init__(self, 
                 legacy_service: LegacyService,
                 new_service: NewService):
        self.legacy_service = legacy_service
        self.new_service = new_service
    
    async def check_camera_consistency(self) -> ConsistencyReport:
        """Check data consistency between legacy and new systems"""
        legacy_cameras = await self.legacy_service.get_all_cameras()
        new_cameras = await self.new_service.get_all_cameras()
        
        inconsistencies = []
        
        for legacy_camera in legacy_cameras:
            new_camera = next(
                (c for c in new_cameras if c.id == legacy_camera.id),
                None
            )
            
            if not new_camera:
                inconsistencies.append(
                    f"Camera {legacy_camera.id} missing in new system"
                )
            elif not self.cameras_match(legacy_camera, new_camera):
                inconsistencies.append(
                    f"Camera {legacy_camera.id} data mismatch"
                )
        
        return ConsistencyReport(
            total_checked=len(legacy_cameras),
            inconsistencies=inconsistencies
        )
```

## Deployment Architecture

### Container Configuration

#### Docker Compose for Development
```yaml
version: '3.8'

services:
  # Core Services
  camera-management:
    build: ./services/camera-management
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/cameras
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    ports:
      - "8001:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  video-processing:
    build: ./services/video-processing
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/video
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    ports:
      - "8002:8000"
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  detection-service:
    build: ./services/detection
    environment:
      - MODEL_PATH=/app/models
      - MONGODB_URL=mongodb://mongo:27017/detections
    depends_on:
      - mongo
    ports:
      - "8003:8000"
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G

  # Supporting Services
  api-gateway:
    image: kong:latest
    environment:
      - KONG_DATABASE=off
      - KONG_DECLARATIVE_CONFIG=/kong/kong.yml
    volumes:
      - ./kong.yml:/kong/kong.yml
    ports:
      - "8000:8000"
      - "8001:8001"
    depends_on:
      - camera-management
      - video-processing
      - detection-service

  # Databases
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=lpr_user
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=lpr_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  mongo:
    image: mongo:6
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  mongo_data:
  redis_data:
```

#### Kubernetes Configuration
```yaml
# Camera Management Service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: camera-management
  namespace: lpr-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: camera-management
  template:
    metadata:
      labels:
        app: camera-management
    spec:
      containers:
      - name: camera-management
        image: lpr/camera-management:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: camera-db-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
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
# Camera Management Service
apiVersion: v1
kind: Service
metadata:
  name: camera-management-service
  namespace: lpr-system
spec:
  selector:
    app: camera-management
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
# Ingress Configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: lpr-ingress
  namespace: lpr-system
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.lpr.company.com
    secretName: lpr-tls-secret
  rules:
  - host: api.lpr.company.com
    http:
      paths:
      - path: /cameras
        pathType: Prefix
        backend:
          service:
            name: camera-management-service
            port:
              number: 80
      - path: /streams
        pathType: Prefix
        backend:
          service:
            name: video-processing-service
            port:
              number: 80
      - path: /detect
        pathType: Prefix
        backend:
          service:
            name: detection-service
            port:
              number: 80
```

## Monitoring and Observability

### Service Metrics

#### Prometheus Configuration
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'lpr-services'
    static_configs:
      - targets: 
        - 'camera-management:8000'
        - 'video-processing:8000'
        - 'detection-service:8000'
        - 'analytics-service:8000'
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### Custom Metrics
```python
from prometheus_client import Counter, Histogram, Gauge, Info

# Service-specific metrics
CAMERA_REQUESTS = Counter('camera_requests_total', 'Total camera requests', ['method', 'endpoint'])
CAMERA_RESPONSE_TIME = Histogram('camera_response_time_seconds', 'Camera response time')
ACTIVE_CAMERAS = Gauge('active_cameras_count', 'Number of active cameras')

DETECTION_REQUESTS = Counter('detection_requests_total', 'Total detection requests')
DETECTION_PROCESSING_TIME = Histogram('detection_processing_time_seconds', 'Detection processing time')
DETECTION_ACCURACY = Gauge('detection_accuracy_score', 'Detection accuracy score')

# Service health metrics
SERVICE_INFO = Info('service_info', 'Service information')
SERVICE_HEALTH = Gauge('service_health_status', 'Service health status')

# Usage in services
class CameraManagementService:
    @CAMERA_RESPONSE_TIME.time()
    async def get_camera(self, camera_id: str) -> Camera:
        CAMERA_REQUESTS.labels(method='GET', endpoint='/cameras').inc()
        
        camera = await self.camera_repository.get_by_id(camera_id)
        
        if camera:
            return camera
        else:
            raise CameraNotFoundException(camera_id)
```

### Distributed Tracing

#### OpenTelemetry Configuration
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument()
RedisInstrumentor().instrument()

# Manual tracing
class CameraService:
    async def get_camera(self, camera_id: str) -> Camera:
        with tracer.start_as_current_span("get_camera") as span:
            span.set_attribute("camera_id", camera_id)
            
            # Database operation
            with tracer.start_as_current_span("database_query") as db_span:
                db_span.set_attribute("query", "SELECT * FROM cameras WHERE id = ?")
                camera = await self.camera_repository.get_by_id(camera_id)
            
            # External service call
            with tracer.start_as_current_span("health_check") as health_span:
                health_status = await self.health_service.check_camera_health(camera_id)
                health_span.set_attribute("health_status", health_status.status)
            
            return camera
```

### Logging Standards

#### Structured Logging
```python
import structlog
from pythonjsonlogger import jsonlogger

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in services
class CameraService:
    async def register_camera(self, camera: Camera) -> None:
        logger.info(
            "Registering camera",
            camera_id=camera.id,
            camera_name=camera.name,
            ip_address=camera.ip_address,
            service="camera-management"
        )
        
        try:
            await self.camera_repository.save(camera)
            
            logger.info(
                "Camera registered successfully",
                camera_id=camera.id,
                processing_time=0.123
            )
            
        except Exception as e:
            logger.error(
                "Camera registration failed",
                camera_id=camera.id,
                error=str(e),
                exc_info=True
            )
            raise
```

## Service Governance

### Service Contracts

#### API Contract Testing
```python
import pytest
from pact import Consumer, Provider
from pact.pact import Pact

# Consumer contract testing
pact = Pact(
    consumer=Consumer('analytics-service'),
    provider=Provider('camera-management-service')
)

def test_get_camera_contract():
    """Test contract for getting camera details"""
    expected = {
        'id': 'cam_001',
        'name': 'Test Camera',
        'status': 'active',
        'ip_address': '192.168.1.100'
    }
    
    (pact
     .given('camera cam_001 exists')
     .upon_receiving('a request for camera details')
     .with_request('GET', '/cameras/cam_001')
     .will_respond_with(200, body=expected))
    
    with pact:
        # Make actual request
        response = requests.get('http://localhost:8001/cameras/cam_001')
        assert response.status_code == 200
        assert response.json() == expected
```

#### Schema Evolution
```python
from pydantic import BaseModel, Field
from typing import Optional

# Version 1 schema
class CameraResponseV1(BaseModel):
    id: str
    name: str
    status: str
    ip_address: str

# Version 2 schema with backward compatibility
class CameraResponseV2(BaseModel):
    id: str
    name: str
    status: str
    ip_address: str
    location: Optional[str] = None  # New optional field
    health_status: Optional[dict] = None  # New optional field
    
    class Config:
        # Allow extra fields for forward compatibility
        extra = "allow"
```

### Service Documentation

#### Service Catalog
```yaml
# service-catalog.yaml
services:
  - name: camera-management
    description: "Manages physical cameras and configurations"
    owner: "platform-team"
    repository: "https://github.com/company/camera-management"
    documentation: "https://docs.company.com/services/camera-management"
    api_endpoint: "https://api.lpr.company.com/cameras"
    health_endpoint: "https://api.lpr.company.com/cameras/health"
    metrics_endpoint: "https://api.lpr.company.com/cameras/metrics"
    dependencies:
      - postgres
      - redis
    consumers:
      - video-processing
      - analytics-service
    sla:
      availability: 99.9%
      response_time: 200ms
    
  - name: video-processing
    description: "Processes video streams and manages recordings"
    owner: "video-team"
    repository: "https://github.com/company/video-processing"
    documentation: "https://docs.company.com/services/video-processing"
    api_endpoint: "https://api.lpr.company.com/streams"
    health_endpoint: "https://api.lpr.company.com/streams/health"
    dependencies:
      - postgres
      - redis
      - camera-management
    consumers:
      - detection-service
    sla:
      availability: 99.5%
      response_time: 500ms
```

### Service Lifecycle Management

#### Deployment Pipeline
```yaml
# .github/workflows/camera-management-deploy.yml
name: Camera Management Service Deploy

on:
  push:
    branches: [main]
    paths: ['services/camera-management/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd services/camera-management
          pytest tests/
          
  contract-test:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - name: Run contract tests
        run: |
          cd services/camera-management
          pytest tests/contracts/
          
  build:
    runs-on: ubuntu-latest
    needs: contract-test
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          cd services/camera-management
          docker build -t camera-management:${{ github.sha }} .
          
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/camera-management \
            camera-management=camera-management:${{ github.sha }} \
            -n lpr-staging
            
  integration-test:
    runs-on: ubuntu-latest
    needs: deploy-staging
    steps:
      - name: Run integration tests
        run: |
          pytest tests/integration/ --env=staging
          
  deploy-production:
    runs-on: ubuntu-latest
    needs: integration-test
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/camera-management \
            camera-management=camera-management:${{ github.sha }} \
            -n lpr-production
```

This comprehensive microservices decomposition strategy provides a clear roadmap for transforming the monolithic LPR system into a scalable, maintainable distributed architecture. Each service has well-defined boundaries, responsibilities, and interfaces, enabling independent development, deployment, and scaling.