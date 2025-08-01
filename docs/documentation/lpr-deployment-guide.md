# LPR System Deployment Guide

## 🚀 Quick Deployment

### Simple Production Setup

The easiest way to deploy the LPR system for production:

```bash
# On your production server
git clone <repository-url> lpr-system
cd lpr-system

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Update database schema
python3 update_database_schema.py

# Start all services
python3 start_lpr.py
```

Access the system at:
- **Frontend**: http://your-server:8080/
- **Main API**: http://your-server:8001/docs
- **Recording API**: http://your-server:8002/docs

## 📋 System Architecture

### Current Production Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Main API      │     │   Recording     │
│   (Port 8080)   │────▶│   (Port 8001)   │────▶│   (Port 8002)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         │                       ▼                        ▼
         │              ┌─────────────────┐     ┌─────────────────┐
         └─────────────▶│  SQLite DB      │     │  Video Storage  │
                        │  (Cameras &     │     │  (Recordings)   │
                        │   Detections)   │     │                 │
                        └─────────────────┘     └─────────────────┘
```

### Service Components
- **Main API Service**: FastAPI application handling camera management and detection
- **Recording Service**: Independent 24/7 recording with playback API
- **Frontend Server**: Static file server for web interface
- **SQLite Database**: Persistent storage for cameras, detections, and metadata
- **File Storage**: Video recordings organized by date/time

## 🔧 Service Management

### Production Service Management

#### Start All Services
```bash
# Recommended for production
python3 start_lpr.py

# Alternative with monitoring
python3 start_all_services.py
```

#### Monitor Services
```bash
# Check service health
python3 check_services.py

# Continuous monitoring
python3 check_services.py -m 60  # Check every 60 seconds
```

#### Stop Services
```bash
python3 stop_all_services.py
```

#### Restart Services
```bash
python3 restart_services.py
```

### Service Logs
All services create timestamped logs in the `logs/` directory:
```bash
# Monitor logs
tail -f logs/main_api_*.log
tail -f logs/recording_service_*.log
tail -f logs/frontend_*.log

# Check for errors
grep -i error logs/*.log
```

## 🐳 Docker Deployment (Alternative)

### Docker Compose Setup

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  lpr-system:
    build: .
    container_name: lpr_system
    ports:
      - "8080:8080"   # Frontend
      - "8001:8001"   # Main API
      - "8002:8002"   # Recording API
    volumes:
      - ./data:/app/data           # Database
      - ./recordings:/app/recordings  # Video storage
      - ./logs:/app/logs           # Log files
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data recordings logs detections/frames detections/plates static

# Update database schema
RUN python3 update_database_schema.py

# Expose ports
EXPOSE 8080 8001 8002

# Start all services
CMD ["python3", "start_all_services.py"]
```

### Deploy with Docker
```bash
# Build and start
docker-compose up --build -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔒 Security Configuration

### Basic Security Setup

#### 1. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw enable
sudo ufw allow 22        # SSH
sudo ufw allow 8080      # Frontend
sudo ufw allow 8001      # Main API
sudo ufw allow 8002      # Recording API
```

#### 2. SSL/TLS Setup with Nginx
```nginx
# /etc/nginx/sites-available/lpr-system
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Main API
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Recording API
    location /recordings/ {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. Environment Variables
Create `.env` file for sensitive configuration:
```bash
# Database encryption key (generate with: openssl rand -hex 32)
DATABASE_ENCRYPTION_KEY=your-32-character-hex-key

# API Security
API_SECRET_KEY=your-secret-key-here

# Camera default credentials (optional)
DEFAULT_CAMERA_USERNAME=admin
DEFAULT_CAMERA_PASSWORD=secure-password
```

## 📊 Monitoring and Maintenance

### Health Monitoring
```bash
# Create monitoring script
cat > monitor_lpr.sh << 'EOF'
#!/bin/bash
LOG_FILE="/var/log/lpr_monitor.log"

while true; do
    if ! python3 check_services.py > /dev/null 2>&1; then
        echo "$(date): LPR services unhealthy, restarting..." >> $LOG_FILE
        python3 restart_services.py >> $LOG_FILE 2>&1
    fi
    sleep 300  # Check every 5 minutes
done
EOF

chmod +x monitor_lpr.sh
```

### Systemd Service (Linux)
```bash
# Create systemd service
sudo tee /etc/systemd/system/lpr-system.service << 'EOF'
[Unit]
Description=License Plate Recognition System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/lpr-system
ExecStart=/path/to/lpr-system/.venv/bin/python3 start_all_services.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable lpr-system
sudo systemctl start lpr-system
sudo systemctl status lpr-system
```

### Log Rotation
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/lpr-system << 'EOF'
/path/to/lpr-system/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 your-username your-username
}
EOF
```

## 💾 Backup Strategy

### Database Backup
```bash
# Create backup script
cat > backup_lpr.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/lpr-system"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp data/license_plates.db $BACKUP_DIR/license_plates_$DATE.db

# Backup important configurations
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    *.py \
    requirements.txt \
    .env \
    frontend/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup_lpr.sh
```

### Automated Backups with Cron
```bash
# Add to crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /path/to/lpr-system/backup_lpr.sh >> /var/log/lpr_backup.log 2>&1
```

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check port conflicts
sudo lsof -i :8001 -i :8002 -i :8080

# Check Python environment
which python3
.venv/bin/python3 --version

# Update database schema
python3 update_database_schema.py
```

#### High CPU/Memory Usage
```bash
# Monitor resources
htop
python3 check_services.py

# Check logs for errors
grep -i "error\|warning" logs/*.log | tail -20
```

#### Recording Issues
```bash
# Check storage space
df -h recordings/

# Check recording service
curl http://localhost:8002/health

# Manual cleanup if needed
python3 -c "
from recording_service.services.storage_manager import StorageManager
sm = StorageManager('recordings')
sm.cleanup_old_recordings()
"
```

## 📈 Performance Optimization

### For High-Traffic Deployments

#### 1. Database Optimization
```python
# Add to your configuration
DATABASE_CONNECTION_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
```

#### 2. Video Storage Optimization
```bash
# Mount dedicated storage for recordings
sudo mkdir /mnt/recordings
sudo mount /dev/sdb1 /mnt/recordings
sudo chown your-username:your-username /mnt/recordings

# Update recording path in config
ln -sf /mnt/recordings recordings
```

#### 3. Load Balancing (Multiple Instances)
```nginx
upstream lpr_backend {
    server localhost:8001;
    server localhost:8011;  # Additional instance
    server localhost:8021;  # Additional instance
}

server {
    location /api/ {
        proxy_pass http://lpr_backend;
    }
}
```

## 🎯 Production Checklist

### Pre-Deployment
- [ ] Test all services locally
- [ ] Configure environment variables
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Create backup strategy

### Post-Deployment
- [ ] Verify all services are running
- [ ] Test camera connections
- [ ] Verify recording functionality
- [ ] Set up monitoring
- [ ] Schedule backups
- [ ] Document access credentials

### Ongoing Maintenance
- [ ] Monitor service health daily
- [ ] Review logs weekly
- [ ] Update system monthly
- [ ] Test backups quarterly
- [ ] Security audit annually

The LPR system is now production-ready with comprehensive service management, monitoring, and maintenance capabilities.