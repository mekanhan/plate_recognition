# Deployment Guide

## Prerequisites
- All components developed and tested locally
- Ubuntu 20.04+ or similar Linux server
- Docker and Docker Compose installed
- NVIDIA drivers for GPU (if using GPU)

## Overview
Deploy the complete LPR system for production use with proper monitoring, backups, and security.

## System Architecture for Deployment

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Load Balancer │     │   Web Server    │     │   Database      │
│   (Nginx)       │────▶│   (FastAPI)     │────▶│   (PostgreSQL)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         │              ┌─────────────────┐              │
         │              │ Processing Node │              │
         └─────────────▶│ (AI + Cameras)  │──────────────┘
                        └─────────────────┘
```

## Docker Deployment

### 1. Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: lpr_postgres
    environment:
      POSTGRES_USER: ${DB_USER:-lpr_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secure_password}
      POSTGRES_DB: ${DB_NAME:-lpr_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init_db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-lpr_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for Queuing
  redis:
    image: redis:7-alpine
    container_name: lpr_redis
    command: redis-server --appendonly yes
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

  # Main Application
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: lpr_app
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER:-lpr_user}:${DB_PASSWORD:-secure_password}@postgres:5432/${DB_NAME:-lpr_db}
      REDIS_URL: redis://redis:6379
      PYTHONUNBUFFERED: 1
    volumes:
      - ./detections:/app/detections
      - ./recordings:/app/recordings
      - ./config:/app/config
      - ./models:/app/models
    ports:
      - "8000:8000"
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

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: lpr_nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/build:/usr/share/nginx/html:ro
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
    restart: unless-stopped

  # Monitoring - Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: lpr_prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    restart: unless-stopped

  # Monitoring - Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: lpr_grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
      GF_USERS_ALLOW_SIGN_UP: false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana/datasources:/etc/grafana/provisioning/datasources:ro
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### 2. Application Dockerfile

```dockerfile
# Dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libglfw3-dev \
    libgles2-mesa-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install additional AI models
RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p detections recordings logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### 3. Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=snapshots:10m rate=1r/s;

    # Upstream servers
    upstream app {
        server app:8000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API endpoints
        location /api {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://app;
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Camera snapshots (rate limited)
        location /api/cameras {
            limit_req zone=snapshots burst=5 nodelay;
            proxy_pass http://app;
        }

        # Video clips
        location /api/video {
            proxy_pass http://app;
            proxy_buffering off;
            
            # Large files support
            client_max_body_size 0;
            proxy_max_temp_file_size 0;
        }

        # Static files
        location /images {
            alias /app/detections;
            expires 1h;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## Production Environment Setup

### 1. Environment Variables

```bash
# .env.production
# Database
DB_USER=lpr_user
DB_PASSWORD=your_secure_password_here
DB_NAME=lpr_production
DB_HOST=postgres
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your_secret_key_here
API_KEY=your_api_key_here

# Camera defaults
DEFAULT_CAMERA_USERNAME=admin
DEFAULT_CAMERA_PASSWORD=camera_password

# Storage
DETECTION_STORAGE_PATH=/app/detections
RECORDING_STORAGE_PATH=/app/recordings
MAX_STORAGE_GB=500

# AI Models
MODEL_CACHE_DIR=/app/models
YOLO_MODEL=yolov8m.pt
OCR_LANGUAGES=en

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Grafana
GRAFANA_PASSWORD=secure_admin_password
```

### 2. System Requirements

```yaml
# Minimum Requirements
minimum:
  cpu: 4 cores
  ram: 8 GB
  gpu: NVIDIA GTX 1060 (6GB)
  storage: 100 GB SSD
  network: 100 Mbps

# Recommended Requirements  
recommended:
  cpu: 8+ cores
  ram: 16-32 GB
  gpu: NVIDIA RTX 3060 or better
  storage: 1 TB NVMe SSD
  network: 1 Gbps

# Per Camera Requirements
per_camera:
  cpu: 0.5-1 core
  ram: 1-2 GB
  bandwidth: 8-15 Mbps
  storage: 10-50 GB/day
```

### 3. Pre-deployment Checklist

```bash
#!/bin/bash
# deployment/pre-deploy-check.sh

echo "🔍 Pre-deployment Check"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed"
    exit 1
fi
echo "✅ Docker installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not installed"
    exit 1
fi
echo "✅ Docker Compose installed"

# Check NVIDIA Docker (if GPU)
if nvidia-smi &> /dev/null; then
    if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo "❌ NVIDIA Docker runtime not configured"
        exit 1
    fi
    echo "✅ NVIDIA Docker runtime configured"
fi

# Check required ports
for port in 80 443 8000 5432 6379; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $port already in use"
        exit 1
    fi
done
echo "✅ Required ports available"

# Check disk space
available=$(df -BG /var/lib/docker | awk 'NR==2 {print $4}' | sed 's/G//')
if [ $available -lt 50 ]; then
    echo "❌ Insufficient disk space (need 50GB, have ${available}GB)"
    exit 1
fi
echo "✅ Sufficient disk space"

# Check environment file
if [ ! -f .env.production ]; then
    echo "❌ .env.production file missing"
    exit 1
fi
echo "✅ Environment file present"

echo "✨ System ready for deployment!"
```

## Deployment Steps

### 1. Initial Deployment

```bash
# Clone repository
git clone https://github.com/yourorg/lpr-system.git
cd lpr-system

# Copy production environment
cp .env.example .env.production
# Edit .env.production with your values

# Create SSL certificates
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem

# Build and start services
docker-compose up -d --build

# Check service health
docker-compose ps
docker-compose logs -f app

# Initialize database
docker-compose exec app python scripts/init_db.py

# Create admin user
docker-compose exec app python scripts/create_admin.py
```

### 2. Camera Configuration

```python
# scripts/configure_cameras.py
import asyncio
from database.service import DatabaseService
from camera_manager import CameraConfig

async def add_production_cameras():
    db = DatabaseService("postgresql+asyncpg://...")
    
    cameras = [
        {
            "camera_id": "entrance_main",
            "name": "Main Entrance",
            "ip_address": "10.0.0.181",
            "username": "admin",
            "password": "secure_password",
            "location": "Building A - Main Entrance",
            "stream_path": "/Streaming/Channels/101"
        },
        # Add more cameras
    ]
    
    for cam_data in cameras:
        config = CameraConfig(**cam_data)
        await db.add_camera(config)
        print(f"Added camera: {config.name}")

if __name__ == "__main__":
    asyncio.run(add_production_cameras())
```

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'lpr-app'
    static_configs:
      - targets: ['app:9090']
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
      
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### 2. Grafana Dashboard

```json
{
  "dashboard": {
    "title": "LPR System Monitoring",
    "panels": [
      {
        "title": "Detection Rate",
        "targets": [
          {
            "expr": "rate(lpr_detections_total[5m])"
          }
        ]
      },
      {
        "title": "Camera Health",
        "targets": [
          {
            "expr": "lpr_camera_health_status"
          }
        ]
      },
      {
        "title": "AI Processing Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, lpr_ai_processing_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

## Backup Strategy

### 1. Automated Backups

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/lpr"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T postgres pg_dump -U lpr_user lpr_db | \
  gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Backup detection images (last 7 days)
find /app/detections -mtime -7 -type f | \
  tar -czf "$BACKUP_DIR/detections_$DATE.tar.gz" -T -

# Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /app/config

# Keep only last 30 days of backups
find "$BACKUP_DIR" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 sync "$BACKUP_DIR" s3://your-backup-bucket/lpr/
```

### 2. Backup Cron Job

```cron
# /etc/cron.d/lpr-backup
0 2 * * * root /opt/lpr/scripts/backup.sh >> /var/log/lpr-backup.log 2>&1
```

## Security Hardening

### 1. Firewall Rules

```bash
# UFW firewall configuration
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (restrict source IP)
ufw allow from 192.168.1.0/24 to any port 22

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow camera network only
ufw allow from 10.0.0.0/24 to any port 8000

# Enable firewall
ufw enable
```

### 2. SSL/TLS with Let's Encrypt

```bash
# Install certbot
apt-get install certbot

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Auto-renewal
echo "0 0 * * 0 root certbot renew --quiet" > /etc/cron.d/certbot-renew
```

## Troubleshooting Deployment

### Common Issues

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f app
docker-compose logs -f postgres

# Restart service
docker-compose restart app

# Check resource usage
docker stats

# Enter container for debugging
docker-compose exec app bash

# Test camera connection
docker-compose exec app python -c "
import cv2
cap = cv2.VideoCapture('rtsp://...')
print('Connected:', cap.isOpened())
"
```

## Performance Tuning

### 1. PostgreSQL Optimization

```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 200
```

### 2. Application Optimization

```python
# Optimize frame processing
PROCESSING_CONFIG = {
    "frame_skip": 3,  # Process every 3rd frame
    "max_queue_size": 100,
    "batch_size": 10,
    "worker_threads": 4
}
```

## Next Steps

Continue to: **[08 - Troubleshooting & FAQ](./08-troubleshooting-faq.md)**

---

*AI Agent Note: This deployment uses Docker for consistency and scalability. The architecture separates concerns properly - cameras connect to processing nodes, not the web server.*