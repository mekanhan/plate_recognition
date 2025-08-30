# Monitoring & Observability System

## Overview

The LPR system now includes a comprehensive monitoring and observability solution with Prometheus metrics, health checks, and real-time system monitoring.

## Features

### 📊 **Prometheus Metrics**
- **System Metrics**: CPU, memory, disk usage, uptime
- **Detection Metrics**: Plate processing, confidence scores, processing times
- **Camera Metrics**: Connection status, FPS, error rates, reconnections
- **Storage Metrics**: Space usage, file counts, cleanup events, deduplication savings
- **API Metrics**: Request counts, response times, status codes
- **Authentication Metrics**: Login attempts, active tokens, permission denials
- **Model Performance**: Loading times, inference duration, memory usage

### 🏥 **Health Monitoring**
- **System Resources**: CPU/memory/disk thresholds with alerting
- **Database Health**: Connectivity, size monitoring, performance checks
- **Camera Status**: Real-time connection testing and diagnostics
- **AI Models**: Model file availability, GPU status, loading validation
- **Storage Health**: Usage monitoring, cleanup verification
- **Authentication System**: User database, JWT configuration validation
- **Recording Service**: External service connectivity and status

### ⚡ **Performance Monitoring**
- **Request Timing**: Automatic slow request detection (>2s threshold)
- **Processing Metrics**: Frame processing times, detection latency
- **Resource Utilization**: Real-time system resource tracking
- **Error Tracking**: Comprehensive error categorization and counting

## API Endpoints

### Public Monitoring Endpoints

#### Prometheus Metrics
```bash
GET /api/monitoring/metrics
Content-Type: text/plain; version=0.0.4; charset=utf-8

# Returns Prometheus-formatted metrics
lpr_cpu_usage_percent 45.2
lpr_detections_total{camera_id="cam_001",vehicle_type="car"} 1847
lpr_camera_status{camera_id="cam_001",name="Entrance",ip_address="192.168.1.100"} 1
```

#### Basic Health Check
```bash
GET /api/monitoring/health

{
  "status": "healthy",
  "timestamp": 1672531200,
  "service": "lpr-system"
}
```

### Authenticated Monitoring Endpoints

#### Detailed Health Information
```bash
GET /api/monitoring/health/detailed
Authorization: Bearer <token>

{
  "overall_status": "healthy",
  "last_check": "2025-08-12T10:30:00Z",
  "checks": {
    "system_resources": {
      "status": "healthy",
      "message": "System resources healthy",
      "duration_ms": 125.4
    },
    "cameras": {
      "status": "warning", 
      "message": "1/3 cameras offline"
    }
  },
  "summary": {
    "total_checks": 7,
    "healthy_checks": 5,
    "warning_checks": 2,
    "critical_checks": 0
  }
}
```

#### System Statistics
```bash
GET /api/monitoring/system/stats
Authorization: Bearer <admin-token>

{
  "system": {
    "uptime_seconds": 86400,
    "cpu_count": 8,
    "cpu_percent": 15.3,
    "load_average": [1.2, 1.5, 1.8]
  },
  "process": {
    "memory_info": {"rss": 536870912, "vms": 1073741824},
    "cpu_percent": 12.1,
    "num_threads": 24
  },
  "memory": {
    "virtual": {"total": 17179869184, "used": 8589934592, "percent": 50.0}
  },
  "disk": {
    ".": {"total": 1000000000000, "used": 500000000000, "percent": 50.0}
  }
}
```

#### Performance Overview
```bash
GET /api/monitoring/performance/overview
Authorization: Bearer <token>

{
  "detection_performance": {
    "total_detections": 15847,
    "detections_last_hour": 142,
    "average_confidence": 0.87
  },
  "camera_performance": {
    "total_cameras": 4,
    "online_cameras": 3,
    "offline_cameras": 1
  },
  "system_performance": {
    "uptime_seconds": 86400,
    "cpu_usage": 15.3,
    "memory_usage": 68.2
  }
}
```

#### System Alerts
```bash
GET /api/monitoring/alerts
Authorization: Bearer <token>

{
  "alerts": [
    {
      "alert_id": "storage_warning",
      "component": "storage",
      "severity": "warning",
      "message": "Storage usage high: 87.3%",
      "timestamp": "2025-08-12T10:25:00Z"
    }
  ],
  "total_alerts": 1,
  "critical_alerts": 0,
  "warning_alerts": 1
}
```

#### Run Specific Health Check
```bash
POST /api/monitoring/health/check/cameras
Authorization: Bearer <token>

{
  "check_name": "cameras",
  "status": "warning",
  "message": "1/3 cameras offline",
  "duration_ms": 234.7,
  "details": {
    "total_cameras": 3,
    "online_cameras": 2,
    "offline_cameras": 1
  }
}
```

## Integration

### Grafana Dashboard

Create Grafana dashboards using the Prometheus metrics:

```yaml
# grafana-dashboard.json
{
  "dashboard": {
    "title": "LPR System Monitoring",
    "panels": [
      {
        "title": "Detection Rate",
        "targets": [{"expr": "rate(lpr_detections_total[5m])"}]
      },
      {
        "title": "Camera Status", 
        "targets": [{"expr": "lpr_camera_status"}]
      },
      {
        "title": "System Resources",
        "targets": [
          {"expr": "lpr_cpu_usage_percent"},
          {"expr": "lpr_memory_usage_bytes{type='physical_used'}/1024/1024/1024"}
        ]
      }
    ]
  }
}
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lpr-system'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/api/monitoring/metrics'
    scrape_interval: 10s
```

### Alertmanager Rules

```yaml
# alert-rules.yml
groups:
  - name: lpr-system
    rules:
      - alert: HighCPUUsage
        expr: lpr_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"

      - alert: CameraOffline
        expr: lpr_camera_status == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Camera {{ $labels.camera_id }} is offline"

      - alert: StorageFull
        expr: lpr_storage_usage_bytes{type="total"} / (10 * 1024 * 1024 * 1024) > 0.9
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Storage is 90% full"
```

## Monitoring Middleware

The system automatically collects metrics via middleware:

### API Request Metrics
- Automatic request/response time tracking
- Status code distribution
- Endpoint normalization to prevent cardinality explosion
- Slow request detection and logging

### Authentication Metrics
- Login success/failure rates
- Permission denial tracking
- Active token monitoring

### Performance Monitoring
- Response time headers (`X-Process-Time`, `X-Response-Time-ms`)
- Slow request logging (>2s threshold)
- Server timing information

## Health Check Types

### 1. System Resources
- **CPU Usage**: Warning >70%, Critical >90%
- **Memory Usage**: Warning >80%, Critical >90%  
- **Disk Usage**: Warning >85%, Critical >95%
- **Load Average**: System load monitoring

### 2. Database Health
- **Connectivity**: Basic database operations
- **Size Monitoring**: Database growth tracking
- **Performance**: Query response times

### 3. Camera Status
- **Connection Testing**: Real-time connectivity
- **Status Aggregation**: Overall camera health
- **Error Tracking**: Connection failure rates

### 4. AI Models
- **File Availability**: YOLO model file checks
- **GPU Status**: CUDA availability
- **Memory Usage**: Model memory consumption

### 5. Storage Health
- **Usage Monitoring**: Space utilization tracking
- **Cleanup Verification**: Automatic cleanup effectiveness
- **Threshold Alerts**: Configurable storage limits

### 6. Authentication System
- **User Database**: User system integrity
- **JWT Configuration**: Token system health
- **Security Checks**: Default password detection

### 7. Recording Service
- **Service Connectivity**: External service health
- **API Responsiveness**: Service response validation

## Configuration

### Environment Variables
```env
# Monitoring Configuration
PROMETHEUS_METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=60
SLOW_REQUEST_THRESHOLD=2.0
METRICS_UPDATE_INTERVAL=30
```

### Health Check Intervals
```python
check_intervals = {
    'system_resources': 30,  # seconds
    'database': 60,
    'cameras': 45, 
    'ai_models': 120,
    'storage': 90,
    'auth_system': 300,
    'recording_service': 60
}
```

## Usage Examples

### Basic Monitoring Setup

```bash
# 1. Start the LPR system with monitoring
python3 start_lpr.py

# 2. Check basic health
curl http://localhost:8001/api/monitoring/health

# 3. Get Prometheus metrics
curl http://localhost:8001/api/monitoring/metrics

# 4. Check detailed health (requires auth)
TOKEN=$(curl -X POST http://localhost:8001/api/auth/login \
  -d '{"username":"admin","password":"admin123"}' \
  -H "Content-Type: application/json" | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/monitoring/health/detailed
```

### Custom Metrics Integration

```python
# In your code, record custom metrics
from monitoring.metrics import metrics

# Record detection
metrics.record_detection(
    camera_id="cam_001",
    vehicle_type="car", 
    confidence=0.92,
    ocr_confidence=0.87,
    processing_time=0.145
)

# Record camera error
metrics.record_camera_error("cam_001", "connection_timeout")

# Update storage metrics
metrics.update_storage_metrics({
    'detections_size': 1024*1024*500,  # 500MB
    'recordings_size': 1024*1024*1024*5,  # 5GB
    'total_size': 1024*1024*1024*5.5  # 5.5GB
})
```

### Monitoring Integration

```python
# Custom health check
async def custom_health_check():
    # Your custom logic
    return HealthCheck(
        name="custom_component",
        status=HealthStatus.HEALTHY,
        message="Component is working",
        details={"metric": "value"}
    )

# Add to health monitor
health_monitor.check_methods['custom_component'] = custom_health_check
```

## Troubleshooting

### Common Issues

**Metrics Not Updating**
```bash
# Check if metrics endpoint is accessible
curl http://localhost:8001/api/monitoring/metrics

# Verify middleware is loaded
# Look for "Monitoring middleware configured" in logs
```

**Health Checks Failing**
```bash
# Run individual health check
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/monitoring/health/check/system_resources

# Check health monitor logs
tail -f logs/api_*.log | grep -i health
```

**High Resource Usage**
```bash
# Check system stats
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/monitoring/system/stats

# Monitor resource trends in Grafana
# Review slow request logs
```

### Performance Optimization

**Reduce Metrics Cardinality**
- Endpoint normalization prevents label explosion
- Camera IDs are normalized for metrics grouping
- Time-series data is automatically pruned

**Health Check Optimization** 
- Configurable check intervals
- Cached results for frequent requests
- Asynchronous check execution

**Resource Management**
- Metrics collection runs in background
- Health checks are non-blocking
- Automatic cleanup of old metric data

## Future Enhancements

### Planned Features
1. **Custom Alerting**: Email/SMS notifications for critical issues
2. **Trend Analysis**: Historical performance analysis and predictions
3. **Automated Remediation**: Self-healing capabilities for common issues
4. **Mobile Dashboard**: Real-time monitoring on mobile devices
5. **Integration APIs**: Webhook support for external monitoring systems

### Advanced Monitoring
- **Distributed Tracing**: Request flow tracking across services
- **Log Aggregation**: Centralized log collection and analysis
- **Anomaly Detection**: ML-based anomaly detection for unusual patterns
- **Capacity Planning**: Predictive scaling recommendations

The monitoring system provides comprehensive visibility into your LPR system, enabling proactive issue detection, performance optimization, and reliable production operations.