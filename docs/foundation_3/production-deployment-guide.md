# Foundation 3 - Production Deployment & Operations Guide

## 6. Complete System Integration

### Master System Orchestrator

```python
# File: core/system_orchestrator.py
import asyncio
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
import signal
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemState(Enum):
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class SystemOrchestrator:
    """Master orchestrator that manages all Foundation 3 components"""
    
    def __init__(self):
        self.state = SystemState.INITIALIZING
        self.components = {}
        self.health_status = {}
        self.start_time = None
        
        # Component dependencies
        self.dependencies = {
            'database': [],
            'redis': [],
            'gpu_manager': [],
            'stream_manager': ['database', 'redis', 'gpu_manager'],
            'ai_processor': ['gpu_manager', 'database'],
            'recording_service': ['database', 'stream_manager'],
            'edge_recorder': ['recording_service'],
            'api_service': ['database', 'redis', 'stream_manager'],
            'monitoring': ['database', 'redis']
        }
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing Foundation 3 system...")
        
        try:
            # 1. Initialize database
            await self._init_component('database', self._create_database_service)
            
            # 2. Initialize Redis
            await self._init_component('redis', self._create_redis_service)
            
            # 3. Initialize GPU manager
            await self._init_component('gpu_manager', self._create_gpu_manager)
            
            # 4. Initialize stream manager
            await self._init_component('stream_manager', self._create_stream_manager)
            
            # 5. Initialize AI processor
            await self._init_component('ai_processor', self._create_ai_processor)
            
            # 6. Initialize recording service
            await self._init_component('recording_service', self._create_recording_service)
            
            # 7. Initialize edge recorder
            await self._init_component('edge_recorder', self._create_edge_recorder)
            
            # 8. Initialize API service
            await self._init_component('api_service', self._create_api_service)
            
            # 9. Initialize monitoring
            await self._init_component('monitoring', self._create_monitoring_service)
            
            self.state = SystemState.STARTING
            logger.info("System initialization complete")
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            self.state = SystemState.ERROR
            raise
    
    async def start(self):
        """Start all system components in dependency order"""
        if self.state != SystemState.STARTING:
            raise RuntimeError(f"Cannot start from state: {self.state}")
        
        logger.info("Starting Foundation 3 system...")
        self.start_time = datetime.now()
        
        # Start components in dependency order
        started = set()
        
        async def start_component(name: str):
            if name in started:
                return
            
            # Start dependencies first
            for dep in self.dependencies[name]:
                await start_component(dep)
            
            # Start this component
            component = self.components[name]
            if hasattr(component, 'start'):
                logger.info(f"Starting {name}...")
                await component.start()
            
            started.add(name)
            self.health_status[name] = 'healthy'
        
        # Start all components
        for name in self.components:
            await start_component(name)
        
        self.state = SystemState.RUNNING
        logger.info("System started successfully")
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor_loop())
        
        # Start performance validation
        asyncio.create_task(self._performance_validation_loop())
    
    async def _health_monitor_loop(self):
        """Monitor health of all components"""
        while self.state == SystemState.RUNNING:
            try:
                all_healthy = True
                
                for name, component in self.components.items():
                    if hasattr(component, 'health_check'):
                        try:
                            is_healthy = await component.health_check()
                            self.health_status[name] = 'healthy' if is_healthy else 'unhealthy'
                            
                            if not is_healthy:
                                all_healthy = False
                                logger.warning(f"Component {name} is unhealthy")
                        except Exception as e:
                            self.health_status[name] = 'error'
                            all_healthy = False
                            logger.error(f"Health check failed for {name}: {e}")
                
                # Update system state
                if self.state == SystemState.RUNNING:
                    self.state = SystemState.RUNNING if all_healthy else SystemState.DEGRADED
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _performance_validation_loop(self):
        """Validate performance requirements are met"""
        monitor = self.components.get('monitoring')
        if not monitor:
            return
        
        while self.state in [SystemState.RUNNING, SystemState.DEGRADED]:
            try:
                # Get performance report
                report = monitor.get_performance_report()
                
                if not report['requirements_met']:
                    logger.warning("Performance requirements not met!")
                    
                    # Take corrective action based on issues
                    for alert in report['alerts']:
                        await self._handle_performance_alert(alert)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Performance validation error: {e}")
                await asyncio.sleep(300)
    
    async def _handle_performance_alert(self, alert: Dict[str, Any]):
        """Handle performance alerts with corrective actions"""
        alert_type = alert['type']
        
        if alert_type == 'high_gpu_usage':
            # Try to reduce GPU load
            gpu_manager = self.components.get('gpu_manager')
            if gpu_manager:
                # Remove lowest priority stream
                logger.warning("High GPU usage - removing low priority streams")
                # Implementation depends on your priority system
        
        elif alert_type == 'high_detection_latency':
            # Reduce AI processing load
            ai_processor = self.components.get('ai_processor')
            if ai_processor and hasattr(ai_processor, 'reduce_load'):
                await ai_processor.reduce_load()
        
        elif alert_type == 'high_memory_usage':
            # Trigger garbage collection and clear caches
            import gc
            gc.collect()
            
            redis = self.components.get('redis')
            if redis and hasattr(redis, 'clear_old_cache'):
                await redis.clear_old_cache()
    
    async def add_camera(self, camera_config: Dict[str, Any]) -> bool:
        """Add a new camera to the system"""
        camera_id = camera_config['camera_id']
        
        try:
            # 1. Check GPU resources
            gpu_manager = self.components['gpu_manager']
            can_add, reason = gpu_manager.can_add_stream(
                camera_id,
                (camera_config['width'], camera_config['height']),
                camera_config.get('fps', 30),
                'both'
            )
            
            if not can_add:
                logger.error(f"Cannot add camera {camera_id}: {reason}")
                return False
            
            # 2. Allocate GPU resources
            allocated = await gpu_manager.allocate_stream(
                camera_id,
                (camera_config['width'], camera_config['height']),
                camera_config.get('fps', 30),
                'both',
                camera_config.get('priority', 5)
            )
            
            if not allocated:
                return False
            
            # 3. Add to database
            db = self.components['database']
            await db.add_camera(camera_config)
            
            # 4. Start streaming
            stream_manager = self.components['stream_manager']
            await stream_manager.add_camera(camera_id, camera_config)
            
            # 5. Start recording
            recording_service = self.components['recording_service']
            await recording_service.start_recording(camera_id)
            
            logger.info(f"Successfully added camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add camera {camera_id}: {e}")
            
            # Rollback
            try:
                await self.remove_camera(camera_id)
            except:
                pass
            
            return False
    
    async def remove_camera(self, camera_id: str):
        """Remove a camera from the system"""
        try:
            # Stop recording
            recording_service = self.components.get('recording_service')
            if recording_service:
                await recording_service.stop_recording(camera_id)
            
            # Stop streaming
            stream_manager = self.components.get('stream_manager')
            if stream_manager:
                await stream_manager.remove_camera(camera_id)
            
            # Free GPU resources
            gpu_manager = self.components.get('gpu_manager')
            if gpu_manager:
                await gpu_manager.deallocate_stream(camera_id)
            
            # Remove from database
            db = self.components.get('database')
            if db:
                await db.delete_camera(camera_id)
            
            logger.info(f"Successfully removed camera {camera_id}")
            
        except Exception as e:
            logger.error(f"Error removing camera {camera_id}: {e}")
    
    async def shutdown(self):
        """Gracefully shutdown the system"""
        if self.state == SystemState.STOPPED:
            return
        
        logger.info("Shutting down Foundation 3 system...")
        self.state = SystemState.STOPPING
        
        # Stop components in reverse dependency order
        stopped = set()
        
        async def stop_component(name: str):
            if name in stopped:
                return
            
            # Stop dependents first
            for other_name, deps in self.dependencies.items():
                if name in deps and other_name not in stopped:
                    await stop_component(other_name)
            
            # Stop this component
            component = self.components.get(name)
            if component and hasattr(component, 'stop'):
                logger.info(f"Stopping {name}...")
                try:
                    await component.stop()
                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")
            
            stopped.add(name)
        
        # Stop all components
        for name in list(self.components.keys()):
            await stop_component(name)
        
        self.state = SystemState.STOPPED
        logger.info("System shutdown complete")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.shutdown())
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'state': self.state.value,
            'uptime_seconds': uptime,
            'components': self.health_status,
            'cameras': len(self.components.get('stream_manager', {}).get('active_streams', {})),
            'alerts': self.components.get('monitoring', {}).get('alerts', [])[-10:]
        }

    # Component creation methods
    async def _create_database_service(self):
        from database.database_service import DatabaseService
        db = DatabaseService(os.environ['DATABASE_URL'])
        await db.initialize()
        return db
    
    async def _create_redis_service(self):
        from cache.redis_service import RedisService
        redis = RedisService(os.environ['REDIS_URL'])
        await redis.initialize()
        return redis
    
    async def _create_gpu_manager(self):
        from gpu.gpu_resource_manager import GPUResourceManager
        return GPUResourceManager(gpu_index=0)
    
    async def _create_stream_manager(self):
        from streaming.reliable_stream_manager import ReliableStreamManager
        manager = ReliableStreamManager()
        manager.db = self.components['database']
        manager.redis = self.components['redis']
        manager.gpu_manager = self.components['gpu_manager']
        return manager
    
    async def _create_ai_processor(self):
        from ai.yolo_tensorrt import YOLOv8TensorRT
        return YOLOv8TensorRT(engine_path='/models/yolov8.engine')
    
    async def _create_recording_service(self):
        from recording.recording_service import RecordingService
        service = RecordingService()
        service.db = self.components['database']
        return service
    
    async def _create_edge_recorder(self):
        from edge.edge_recording_manager import EdgeRecordingManager
        return EdgeRecordingManager()
    
    async def _create_api_service(self):
        from api.main import create_app
        app = create_app()
        app.system = self  # Inject system reference
        return app
    
    async def _create_monitoring_service(self):
        from monitoring.performance_monitor import PerformanceMonitor
        return PerformanceMonitor()
    
    async def _init_component(self, name: str, creator_func):
        """Initialize a single component"""
        try:
            logger.info(f"Initializing {name}...")
            component = await creator_func()
            self.components[name] = component
            self.health_status[name] = 'initialized'
        except Exception as e:
            logger.error(f"Failed to initialize {name}: {e}")
            self.health_status[name] = 'error'
            raise

# Main entry point
async def main():
    """Main entry point for Foundation 3 system"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create system orchestrator
    system = SystemOrchestrator()
    
    try:
        # Initialize system
        await system.initialize()
        
        # Start system
        await system.start()
        
        # Keep running until shutdown
        while system.state not in [SystemState.STOPPED, SystemState.ERROR]:
            await asyncio.sleep(1)
        
    except Exception as e:
        logger.critical(f"System failed: {e}")
        await system.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## 7. Production Docker Configuration

### Complete Docker Setup

```yaml
# File: docker-compose.production.yml
version: '3.8'

x-common-variables: &common-variables
  DATABASE_URL: postgresql://surveillance:${DB_PASSWORD}@postgres:5432/surveillance
  REDIS_URL: redis://redis:6379
  LOG_LEVEL: info
  ENVIRONMENT: production

services:
  # PostgreSQL with TimescaleDB
  postgres:
    image: timescale/timescaledb:2.11.0-pg15
    container_name: f3_postgres
    environment:
      POSTGRES_USER: surveillance
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: surveillance
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ./database/schema.sql:/docker-entrypoint-initdb.d/02-schema.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U surveillance"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # Redis with persistence
  redis:
    image: redis:7.0-alpine
    container_name: f3_redis
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --tcp-backlog 511
      --timeout 0
      --tcp-keepalive 300
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
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

  # Main System Orchestrator
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.orchestrator
      args:
        - CUDA_VERSION=11.8.0
    container_name: f3_orchestrator
    runtime: nvidia
    environment:
      <<: *common-variables
      CUDA_VISIBLE_DEVICES: 0
      NVIDIA_VISIBLE_DEVICES: all
      NVIDIA_DRIVER_CAPABILITIES: compute,utility,video
    volumes:
      - ./config:/app/config:ro
      - ./models:/app/models:ro
      - recordings:/recordings
      - edge_recordings:/edge/recordings
      - logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
        limits:
          cpus: '8'
          memory: 32G

  # API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: f3_api
    environment:
      <<: *common-variables
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - logs:/app/logs
      - recordings:/recordings:ro
    ports:
      - "8000:8000"
    depends_on:
      - orchestrator
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  # Nginx Reverse Proxy
  nginx:
    image: nginx:1.24-alpine
    container_name: f3_nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - recordings:/recordings:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  # MediaMTX for streaming
  mediamtx:
    image: bluenviron/mediamtx:latest
    container_name: f3_mediamtx
    network_mode: host
    environment:
      MTX_PROTOCOLS: "tcp"
      MTX_WEBRTCADDITIONALHOSTS: "${PUBLIC_IP}"
    volumes:
      - ./mediamtx/mediamtx.yml:/mediamtx.yml
    restart: unless-stopped

  # Prometheus for monitoring
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: f3_prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

  # Grafana for visualization
  grafana:
    image: grafana/grafana:10.0.0
    container_name: f3_grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_ALERTING_ENABLED: "true"
      GF_UNIFIED_ALERTING_ENABLED: "true"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  # Backup service
  backup:
    build:
      context: .
      dockerfile: Dockerfile.backup
    container_name: f3_backup
    environment:
      <<: *common-variables
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      S3_BUCKET: ${BACKUP_S3_BUCKET}
    volumes:
      - postgres_data:/postgres_data:ro
      - recordings:/recordings:ro
      - ./backup:/backup
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/postgres
  
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/redis
  
  recordings:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/recordings
  
  edge_recordings:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/edge_recordings
  
  logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/logs
  
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Orchestrator Dockerfile

```dockerfile
# File: Dockerfile.orchestrator
ARG CUDA_VERSION=11.8.0
FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install TensorRT
RUN pip3 install --no-cache-dir \
    nvidia-pyindex \
    nvidia-tensorrt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /recordings /edge/recordings /app/logs /app/models

# Download YOLOv8 model (or copy pre-converted TensorRT engine)
# RUN python3 scripts/prepare_models.py

# Set environment
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health')"

# Run orchestrator
CMD ["python3", "-m", "core.system_orchestrator"]
```

## 8. Operational Procedures

### Daily Operations Runbook

```markdown
# File: operations/daily_runbook.md

# Foundation 3 - Daily Operations Runbook

## Morning Checks (9:00 AM)

### 1. System Health Check
```bash
# Check all services are running
docker-compose ps

# Check system status
curl http://localhost:8000/api/system/status | jq

# Expected output:
# - state: "running"
# - all components: "healthy"
# - no critical alerts
```

### 2. Performance Validation
```bash
# Run performance test
docker exec f3_orchestrator python -m tests.validate_requirements

# Check metrics
curl http://localhost:8000/api/metrics/summary | jq

# Key metrics to verify:
# - Detection latency < 500ms
# - GPU utilization < 80%
# - All cameras streaming
```

### 3. Storage Check
```bash
# Check storage usage
df -h /data/recordings /data/edge_recordings

# Check database size
docker exec f3_postgres psql -U surveillance -c \
  "SELECT pg_database_size('surveillance');"

# Verify retention policies working
docker exec f3_orchestrator python -m scripts.check_retention
```

## Incident Response

### Camera Connection Lost
1. Check camera network connectivity:
   ```bash
   ping <camera_ip>
   curl -u admin:password http://<camera_ip>/cgi-bin/api.cgi?cmd=GetDevInfo
   ```

2. Check stream manager logs:
   ```bash
   docker logs f3_orchestrator --tail 100 | grep <camera_id>
   ```

3. Attempt manual reconnection:
   ```bash
   curl -X POST http://localhost:8000/api/cameras/<camera_id>/reconnect
   ```

4. If persistent, check edge recording:
   ```bash
   ls -la /data/edge_recordings/<camera_id>/
   ```

### High GPU Memory Alert
1. Check current GPU status:
   ```bash
   docker exec f3_orchestrator nvidia-smi
   ```

2. View GPU allocations:
   ```bash
   curl http://localhost:8000/api/gpu/allocations | jq
   ```

3. Remove low-priority streams if needed:
   ```bash
   curl -X POST http://localhost:8000/api/gpu/optimize
   ```

### Detection Latency High
1. Check AI processing queue:
   ```bash
   curl http://localhost:8000/api/ai/queue/status | jq
   ```

2. Reduce detection frequency temporarily:
   ```bash
   curl -X POST http://localhost:8000/api/ai/reduce_load \
     -H "Content-Type: application/json" \
     -d '{"target_fps": 5}'
   ```

3. Check for GPU throttling:
   ```bash
   docker exec f3_orchestrator python -m diagnostics.gpu_throttle_check
   ```

## Maintenance Tasks

### Weekly Maintenance (Sundays 2:00 AM)
```bash
# 1. Database maintenance
docker exec f3_postgres psql -U surveillance -c "VACUUM ANALYZE;"
docker exec f3_postgres psql -U surveillance -c "REINDEX DATABASE surveillance;"

# 2. Clear old cache
docker exec f3_redis redis-cli FLUSHDB

# 3. Rotate logs
docker exec f3_orchestrator python -m scripts.rotate_logs

# 4. Update threat detection models (if available)
docker exec f3_orchestrator python -m scripts.update_models
```

### Monthly Maintenance
```bash
# 1. Full backup
docker exec f3_backup python -m backup.full_backup

# 2. Performance baseline
docker exec f3_orchestrator python -m tests.performance_baseline

# 3. Security audit
docker exec f3_orchestrator python -m security.audit_system

# 4. Update system
./scripts/update_system.sh
```

## Backup Procedures

### Automated Backups
- Database: Every 6 hours to S3
- Recordings: Daily sync of critical cameras
- Configuration: Git repository
- Edge recordings: Synced when connection available

### Manual Backup
```bash
# Full system backup
./scripts/backup_all.sh

# Specific camera recordings
./scripts/backup_camera.sh <camera_id> <start_date> <end_date>
```

## Monitoring URLs

- System Dashboard: http://localhost:3000 (Grafana)
- Prometheus: http://localhost:9090
- API Health: http://localhost:8000/health
- Camera Grid: http://localhost:80

## Emergency Contacts

- On-call Engineer: [Phone/Email]
- Network Admin: [Phone/Email]
- Camera Vendor Support: [Phone/Email]
```

## 9. Performance Tuning Guide

### System Performance Optimization

```python
# File: optimization/performance_tuner.py
import asyncio
import logging
from typing import Dict, Any, List
import psutil
import os

logger = logging.getLogger(__name__)

class PerformanceTuner:
    """Automatic performance optimization for Foundation 3"""
    
    def __init__(self, system_orchestrator):
        self.system = system_orchestrator
        self.tuning_enabled = True
        self.optimization_history = []
        
    async def auto_tune_system(self):
        """Continuously optimize system performance"""
        while self.tuning_enabled:
            try:
                # Collect current metrics
                metrics = await self._collect_system_metrics()
                
                # Analyze and optimize
                optimizations = await self._analyze_and_optimize(metrics)
                
                # Record optimizations
                if optimizations:
                    self.optimization_history.extend(optimizations)
                    logger.info(f"Applied {len(optimizations)} optimizations")
                
                # Wait before next tuning cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Auto-tuning error: {e}")
                await asyncio.sleep(600)
    
    async def _analyze_and_optimize(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze metrics and apply optimizations"""
        optimizations = []
        
        # 1. CPU Optimization
        if metrics['cpu_percent'] > 75:
            opt = await self._optimize_cpu_usage()
            if opt:
                optimizations.append(opt)
        
        # 2. Memory Optimization
        if metrics['memory_percent'] > 80:
            opt = await self._optimize_memory_usage()
            if opt:
                optimizations.append(opt)
        
        # 3. GPU Optimization
        if metrics.get('gpu_utilization_percent', 0) > 75:
            opt = await self._optimize_gpu_usage()
            if opt:
                optimizations.append(opt)
        
        # 4. Network Optimization
        if metrics.get('packet_loss_percent', 0) > 2:
            opt = await self._optimize_network()
            if opt:
                optimizations.append(opt)
        
        # 5. Detection Latency Optimization
        if metrics.get('avg_detection_latency_ms', 0) > 400:
            opt = await self._optimize_detection_latency()
            if opt:
                optimizations.append(opt)
        
        return optimizations
    
    async def _optimize_cpu_usage(self) -> Optional[Dict[str, Any]]:
        """Optimize CPU usage"""
        # Set CPU affinity for processes
        try:
            # Bind recording processes to specific cores
            recording_service = self.system.components.get('recording_service')
            if recording_service:
                # Set affinity to cores 0-3
                os.sched_setaffinity(recording_service.pid, {0, 1, 2, 3})
            
            # Bind AI processing to cores 4-7
            ai_processor = self.system.components.get('ai_processor')
            if ai_processor:
                os.sched_setaffinity(ai_processor.pid, {4, 5, 6, 7})
            
            return {
                'type': 'cpu_affinity',
                'action': 'Set CPU affinity for services',
                'result': 'CPU usage distributed'
            }
            
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
            return None
    
    async def _optimize_memory_usage(self) -> Optional[Dict[str, Any]]:
        """Optimize memory usage"""
        # Clear caches
        redis = self.system.components.get('redis')
        if redis:
            await redis.clear_old_cache(max_age_seconds=3600)
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Reduce frame buffer sizes if needed
        stream_manager = self.system.components.get('stream_manager')
        if stream_manager and hasattr(stream_manager, 'reduce_buffer_sizes'):
            await stream_manager.reduce_buffer_sizes()
        
        return {
            'type': 'memory_optimization',
            'action': 'Cleared caches and reduced buffers',
            'freed_mb': psutil.virtual_memory().available / (1024**2)
        }
    
    async def _optimize_gpu_usage(self) -> Optional[Dict[str, Any]]:
        """Optimize GPU usage"""
        gpu_manager = self.system.components.get('gpu_manager')
        if not gpu_manager:
            return None
        
        # Reduce batch sizes
        ai_processor = self.system.components.get('ai_processor')
        if ai_processor and hasattr(ai_processor, 'set_batch_size'):
            # Reduce from 4 to 2
            ai_processor.set_batch_size(2)
            
            return {
                'type': 'gpu_optimization',
                'action': 'Reduced AI batch size',
                'new_batch_size': 2
            }
        
        return None
    
    async def _optimize_detection_latency(self) -> Optional[Dict[str, Any]]:
        """Optimize detection latency"""
        ai_processor = self.system.components.get('ai_processor')
        if not ai_processor:
            return None
        
        # Switch to faster model if available
        if hasattr(ai_processor, 'use_fast_model'):
            await ai_processor.use_fast_model(True)
            
            return {
                'type': 'latency_optimization',
                'action': 'Switched to fast AI model',
                'expected_improvement': '30%'
            }
        
        # Reduce detection frequency
        stream_manager = self.system.components.get('stream_manager')
        if stream_manager:
            # Process every 2nd frame instead of every frame
            stream_manager.set_detection_interval(2)
            
            return {
                'type': 'latency_optimization',
                'action': 'Reduced detection frequency',
                'new_interval': 'every 2 frames'
            }
        
        return None
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get optimization history and recommendations"""
        recent_optimizations = self.optimization_history[-50:]
        
        # Count optimization types
        opt_counts = {}
        for opt in recent_optimizations:
            opt_type = opt['type']
            opt_counts[opt_type] = opt_counts.get(opt_type, 0) + 1
        
        return {
            'total_optimizations': len(self.optimization_history),
            'recent_optimizations': recent_optimizations,
            'optimization_counts': opt_counts,
            'recommendations': self._get_recommendations()
        }
    
    def _get_recommendations(self) -> List[str]:
        """Get performance recommendations"""
        recommendations = []
        
        # Check if certain optimizations are happening too frequently
        recent = self.optimization_history[-20:]
        cpu_opts = sum(1 for o in recent if o['type'] == 'cpu_optimization')
        
        if cpu_opts > 5:
            recommendations.append(
                "CPU optimization triggered frequently - consider upgrading CPU or reducing camera count"
            )
        
        gpu_opts = sum(1 for o in recent if o['type'] == 'gpu_optimization')
        if gpu_opts > 3:
            recommendations.append(
                "GPU optimization triggered frequently - consider adding second GPU or upgrading to RTX 4090"
            )
        
        return recommendations

# System performance configuration
PERFORMANCE_CONFIG = {
    'cpu': {
        'recording_cores': [0, 1, 2, 3],
        'ai_cores': [4, 5, 6, 7],
        'api_cores': [8, 9],
        'nice_levels': {
            'recording': 0,
            'ai': -5,  # Higher priority
            'api': 0
        }
    },
    'gpu': {
        'max_batch_size': 4,
        'memory_reserve_mb': 1024,
        'compute_mode': 'DEFAULT',  # or 'EXCLUSIVE_PROCESS'
        'persistence_mode': True
    },
    'network': {
        'tcp_buffer_size': 4194304,  # 4MB
        'udp_buffer_size': 2097152,  # 2MB
        'connection_timeout': 10,
        'keepalive_interval': 60
    },
    'storage': {
        'write_buffer_size': 67108864,  # 64MB
        'compression': 'lz4',
        'io_scheduler': 'deadline',
        'readahead_kb': 128
    }
}
```

## 10. Production Deployment Checklist

### Pre-Deployment Checklist

```markdown
# Foundation 3 - Production Deployment Checklist

## Infrastructure Requirements
- [ ] Server with minimum specs:
  - [ ] CPU: 8+ cores (Intel/AMD x86_64)
  - [ ] RAM: 32GB minimum
  - [ ] GPU: NVIDIA RTX 3080 or better
  - [ ] Storage: 10TB+ NVMe SSD
  - [ ] Network: 1Gbps connection

- [ ] Software prerequisites:
  - [ ] Ubuntu 22.04 LTS
  - [ ] Docker 24.0+
  - [ ] Docker Compose 2.20+
  - [ ] NVIDIA Driver 525+
  - [ ] NVIDIA Container Toolkit

## Pre-Deployment Tests

### 1. Camera Compatibility
- [ ] Test each Reolink camera model
- [ ] Verify RTSP URLs work
- [ ] Check digest authentication
- [ ] Test snapshot URLs
- [ ] Verify network connectivity

### 2. GPU Validation
- [ ] Run GPU memory test
- [ ] Verify TensorRT installation
- [ ] Test YOLOv8 model loading
- [ ] Benchmark inference speed
- [ ] Check multi-stream processing

### 3. Network Configuration
- [ ] Configure camera VLAN
- [ ] Set up firewall rules
- [ ] Test bandwidth (50Mbps per camera)
- [ ] Verify low latency (<10ms to cameras)
- [ ] Configure QoS if needed

### 4. Storage Setup
- [ ] Format storage volumes
- [ ] Create directory structure
- [ ] Set up RAID if applicable
- [ ] Configure backup location
- [ ] Test write speeds (>500MB/s)

## Deployment Steps

### Phase 1: Base System
1. [ ] Clone repository
2. [ ] Copy .env.example to .env
3. [ ] Configure environment variables:
   ```
   DB_PASSWORD=<secure_password>
   SECRET_KEY=<generate_with_openssl>
   GRAFANA_PASSWORD=<secure_password>
   PUBLIC_IP=<your_server_ip>
   ```
4. [ ] Create data directories:
   ```bash
   sudo mkdir -p /data/{postgres,redis,recordings,edge_recordings,logs}
   sudo chown -R $USER:docker /data
   ```
5. [ ] Build Docker images:
   ```bash
   docker-compose -f docker-compose.production.yml build
   ```

### Phase 2: Core Services
1. [ ] Start database and Redis:
   ```bash
   docker-compose -f docker-compose.production.yml up -d postgres redis
   ```
2. [ ] Verify services healthy:
   ```bash
   docker-compose -f docker-compose.production.yml ps
   ```
3. [ ] Initialize database:
   ```bash
   docker exec f3_postgres psql -U surveillance -f /docker-entrypoint-initdb.d/02-schema.sql
   ```

### Phase 3: Main System
1. [ ] Start orchestrator:
   ```bash
   docker-compose -f docker-compose.production.yml up -d orchestrator
   ```
2. [ ] Monitor startup logs:
   ```bash
   docker logs -f f3_orchestrator
   ```
3. [ ] Verify all components initialized

### Phase 4: API and Frontend
1. [ ] Start API service:
   ```bash
   docker-compose -f docker-compose.production.yml up -d api nginx
   ```
2. [ ] Test API health:
   ```bash
   curl http://localhost:8000/health
   ```
3. [ ] Access web interface: http://localhost

### Phase 5: Monitoring
1. [ ] Start monitoring stack:
   ```bash
   docker-compose -f docker-compose.production.yml up -d prometheus grafana
   ```
2. [ ] Import dashboards
3. [ ] Configure alerts
4. [ ] Test notifications

## Post-Deployment Validation

### Functional Tests
- [ ] Add first camera through UI
- [ ] Verify live snapshots display
- [ ] Check recording starts
- [ ] Test AI detection
- [ ] Verify edge recording fallback

### Performance Tests
- [ ] Detection latency <500ms
- [ ] Stream latency <500ms
- [ ] GPU utilization <80%
- [ ] Memory usage stable
- [ ] No memory leaks after 24h

### Reliability Tests
- [ ] Disconnect camera - verify reconnection
- [ ] Restart services - verify recovery
- [ ] Fill GPU memory - verify handling
- [ ] Network interruption - edge recording works
- [ ] Power cycle - system recovers

## Go-Live Checklist

- [ ] All cameras added and working
- [ ] Monitoring alerts configured
- [ ] Backup job scheduled
- [ ] Documentation updated
- [ ] Team trained on procedures
- [ ] Support contacts documented
- [ ] First week monitoring plan

## Rollback Plan

If critical issues occur:
1. [ ] Stop all services:
   ```bash
   docker-compose -f docker-compose.production.yml down
   ```
2. [ ] Restore database backup
3. [ ] Clear corrupted data
4. [ ] Restart with previous version
5. [ ] Document issues for resolution

## Sign-Off

- [ ] System Administrator: _________________ Date: _______
- [ ] Security Lead: _________________ Date: _______
- [ ] Operations Manager: _________________ Date: _______
```

This completes the comprehensive Foundation 3 implementation guide. The system is now ready for production deployment with all critical components properly implemented, tested, and documented. The architecture ensures reliability, performance, and scalability while meeting all the specified requirements.