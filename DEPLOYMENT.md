# LPR System Deployment Guide

## 🚀 Quick Start Checklist

### 1. **Environment Setup**
```bash
# Clone repository
git clone <repository-url>
cd plate_recognition

# Setup Python environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 2. **Configuration**
```bash
# Copy environment template
cp .env.sample .env

# Edit configuration (REQUIRED)
nano .env  # Update JWT_SECRET_KEY, ADMIN_PASSWORD, etc.
```

### 3. **Download AI Models**
```bash
# Download all required YOLO models
python3 scripts/download_models.py

# Verify models downloaded
ls -la *.pt ai_pipeline/train/models/pretrained/*.pt
```

### 4. **Database Setup**
```bash
# Initialize database with migrations
./venv/bin/alembic upgrade head

# Or use migration helper
python3 db_migration_manager.py
```

### 5. **Start Services**
```bash
# Start all services (recommended)
python3 start_lpr.py

# Or start individually
python3 -m api.main                    # Main API (8001)
python3 start_recording_service.py     # Recording API (8002)
cd frontend && python3 -m http.server 8080  # Frontend
```

### 6. **Verify Installation**
```bash
# Check service health
python3 check_services.py

# Run tests
python3 run_tests.py unit
```

## 🔧 Production Configuration

### **Security Settings (CRITICAL)**

**Update `.env` file:**
```bash
# Strong JWT secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-256-bit-secret-key-here

# Secure admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=StrongPasswordHere123!

# Production database URL
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname

# Disable debug features
DEBUG=false
API_RELOAD=false
ENABLE_SWAGGER_UI=false
LOG_SQL_QUERIES=false
```

### **Database Configuration**

**SQLite (Development):**
```bash
DATABASE_URL=sqlite+aiosqlite:///data/license_plates.db
```

**PostgreSQL (Production):**
```bash
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database
```

### **Performance Tuning**
```bash
# API Settings
API_RELOAD=false
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Storage Limits
STORAGE_LIMIT_GB=100
RECORDING_STORAGE_LIMIT_GB=50

# Processing
MAX_CONCURRENT_DETECTIONS=10
BATCH_SIZE=20
```

## 🐳 Docker Deployment

### **Docker Compose**
```yaml
# docker-compose.yml (available in deployment/ directory)
version: '3.8'
services:
  lpr-api:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://...
    volumes:
      - ./data:/app/data
      - ./recordings:/app/recordings
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: lpr_system
      POSTGRES_USER: lpr_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

```bash
# Deploy with Docker
docker-compose up -d --build
```

## 🖥️ System Service (systemd)

### **Create Service File**
```bash
sudo nano /etc/systemd/system/lpr-system.service
```

```ini
[Unit]
Description=License Plate Recognition System
After=network.target

[Service]
Type=simple
User=lpr
Group=lpr
WorkingDirectory=/opt/lpr-system
Environment=PATH=/opt/lpr-system/venv/bin
ExecStart=/opt/lpr-system/venv/bin/python3 start_lpr.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable lpr-system
sudo systemctl start lpr-system
```

## 📊 Monitoring & Maintenance

### **Health Monitoring**
```bash
# Automated health checks
python3 check_services.py -m 60  # Check every 60 seconds

# View logs
tail -f logs/*.log

# System metrics via Prometheus (if enabled)
curl http://localhost:8001/metrics
```

### **Database Maintenance**
```bash
# Database migration
./venv/bin/alembic upgrade head

# Backup database
cp data/license_plates.db data/backup_$(date +%Y%m%d_%H%M%S).db

# Clean old detections (if needed)
# Automatic cleanup runs based on ANALYTICS_DATA_RETENTION_DAYS
```

### **Storage Management**
```bash
# Check storage usage
python3 -c "
from recording_service.services.storage_manager import StorageManager
import asyncio
sm = StorageManager()
print(asyncio.run(sm.get_storage_report()))
"

# Manual cleanup (if needed)
curl -X POST http://localhost:8002/api/v1/storage/cleanup
```

## 🔒 Security Hardening

### **Firewall Configuration**
```bash
# Allow only necessary ports
sudo ufw allow 8001/tcp  # API
sudo ufw allow 8002/tcp  # Recording API  
sudo ufw allow 8080/tcp  # Frontend
sudo ufw enable
```

### **SSL/TLS (Recommended)**
```bash
# Use reverse proxy (nginx/apache) with SSL
# Or configure FastAPI with SSL certificates
```

### **Access Control**
- Change default admin credentials
- Use strong JWT secrets
- Enable CORS only for trusted origins
- Set up rate limiting
- Regular security updates

## 🧪 Testing Deployment

### **Automated Tests**
```bash
# Run full test suite
python3 run_tests.py all

# Performance tests
python3 run_tests.py performance

# Integration tests
python3 run_tests.py integration
```

### **Manual Verification**
```bash
# API endpoints
curl http://localhost:8001/api/system/health
curl http://localhost:8001/api/cameras/

# Frontend access
open http://localhost:8080

# Recording service
curl http://localhost:8002/health
```

## 🚨 Troubleshooting

### **Common Issues**

**Models not found:**
```bash
python3 scripts/download_models.py --force
```

**Database errors:**
```bash
./venv/bin/alembic upgrade head
python3 db_migration_manager.py
```

**Port conflicts:**
```bash
sudo lsof -i :8001  # Check what's using the port
```

**Permission issues:**
```bash
chmod +x start_lpr.py
chmod 755 scripts/download_models.py
```

### **Log Analysis**
```bash
# Service logs
tail -f logs/api_service.log
tail -f logs/recording_service.log

# System logs
sudo journalctl -u lpr-system -f
```

## 📞 Support

- **Documentation**: Check `/docs/` directory
- **Issues**: Create issue in repository
- **Logs**: Include relevant log files when reporting issues
- **Configuration**: Verify `.env` settings match requirements