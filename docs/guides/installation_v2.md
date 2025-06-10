# Installation Guide - V2 License Plate Recognition System

**Version:** 2.0  
**Last Updated:** 2025-06-10  
**Authors:** Development Team  

## Overview

This guide provides comprehensive installation instructions for the V2 License Plate Recognition System, including environment setup, dependency installation, configuration, and WSL compatibility considerations.

## System Requirements

### Hardware Requirements
- **CPU**: Intel i5 or AMD Ryzen 5 (minimum), Intel i7 or AMD Ryzen 7 (recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: NVIDIA GPU with CUDA support (optional but recommended)
- **Storage**: 10GB free space minimum, SSD recommended
- **Camera**: USB webcam or IP camera

### Software Requirements
- **Operating System**: Windows 10/11, Ubuntu 18.04+, macOS 10.15+
- **Python**: 3.8 or higher (3.9-3.11 recommended)
- **Git**: Latest version
- **WSL2**: Required for Windows development (recommended)

### Supported Platforms
- ✅ Windows 10/11 with WSL2
- ✅ Ubuntu 18.04 LTS or newer
- ✅ macOS 10.15 (Catalina) or newer
- ✅ Docker (containerized deployment)

## Pre-Installation Setup

### Windows WSL2 Setup (Recommended)

1. **Enable WSL2**:
   ```powershell
   # Run as Administrator in PowerShell
   wsl --install
   wsl --set-default-version 2
   ```

2. **Install Ubuntu Distribution**:
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```

3. **Verify WSL2 Installation**:
   ```bash
   wsl --list --verbose
   # Should show Ubuntu-22.04 with VERSION 2
   ```

### GPU Support (Optional)

#### NVIDIA GPU Setup
1. **Install NVIDIA Drivers** (Windows):
   - Download from [NVIDIA Driver Downloads](https://www.nvidia.com/drivers/)
   - Install latest Game Ready or Studio drivers

2. **Install CUDA Toolkit** (WSL2):
   ```bash
   # Add NVIDIA package repositories
   wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.0-1_all.deb
   sudo dpkg -i cuda-keyring_1.0-1_all.deb
   sudo apt-get update
   sudo apt-get -y install cuda-toolkit-12-0
   ```

3. **Verify GPU Access**:
   ```bash
   nvidia-smi
   # Should display GPU information
   ```

## Installation Steps

### 1. Repository Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-organization/plate_recognition.git
   cd plate_recognition
   ```

2. **Verify Repository Structure**:
   ```bash
   ls -la
   # Should show: app/, docs/, config/, data/, tests/, requirements.txt
   ```

### 2. Python Environment Setup

#### Virtual Environment Creation
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment (WSL/Linux/macOS)
source .venv/bin/activate

# For Windows Command Prompt (if not using WSL)
# .venv\Scripts\activate

# For Windows PowerShell (if not using WSL)  
# .venv\Scripts\Activate.ps1
```

#### Environment Verification
```bash
# Verify Python version
python --version
# Should show: Python 3.8.x or higher

# Verify virtual environment
which python
# Should show: /path/to/plate_recognition/.venv/bin/python
```

### 3. Dependency Installation

#### Core Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

#### Verify Key Packages
```bash
# Test critical imports
python -c "
import torch
import cv2
import ultralytics
import easyocr
import fastapi
print('All critical packages imported successfully')
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"
```

### 4. Configuration Setup

#### Environment Configuration
1. **Create Configuration File**:
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit configuration
   nano .env
   ```

2. **Configure Environment Variables**:
   ```bash
   # Camera settings
   CAMERA_ID=0
   CAMERA_WIDTH=1280
   CAMERA_HEIGHT=720
   
   # Model settings  
   MODEL_PATH=app/models/yolo11m_best.pt
   
   # Directory settings
   LICENSE_PLATES_DIR=data/license_plates
   ENHANCED_PLATES_DIR=data/enhanced_plates
   KNOWN_PLATES_PATH=data/known_plates.json
   ```

#### Directory Structure Creation
```bash
# Create required directories
mkdir -p data/license_plates
mkdir -p data/enhanced_plates
mkdir -p data/videos
mkdir -p logs
mkdir -p tests/unit_tests

# Set proper permissions
chmod 755 data/
chmod 755 logs/
```

### 5. Model Setup

#### Download Pre-trained Models
```bash
# Create models directory
mkdir -p app/models

# Download YOLO models (choose one or more)
cd app/models

# YOLOv11 medium (recommended)
wget https://github.com/ultralytics/assets/releases/download/v8.2.0/yolo11m.pt

# YOLOv8 medium (alternative)
wget https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8m.pt

# Verify downloads
ls -la *.pt
cd ../..
```

#### Custom Model Setup (Optional)
```bash
# If you have a custom trained model
cp /path/to/your/model.pt app/models/yolo11m_best.pt

# Update configuration
echo "MODEL_PATH=app/models/yolo11m_best.pt" >> .env
```

## Configuration

### Database Initialization

The V2 system uses SQLite with automatic initialization:

```bash
# Database will be created automatically on first run
# Location: data/license_plates.db

# Verify database schema (after first run)
sqlite3 data/license_plates.db ".schema"
```

### Camera Configuration

#### USB Camera Setup
```bash
# List available cameras
ls /dev/video*

# Test camera access
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f'Camera accessible: {ret}')
print(f'Frame shape: {frame.shape if ret else \"N/A\"}')
cap.release()
"
```

#### IP Camera Setup
```bash
# For IP cameras, update .env file
echo "CAMERA_ID=rtsp://username:password@ip:port/stream" >> .env
```

### WSL-Specific Configuration

#### File Path Compatibility
```bash
# Ensure WSL paths work correctly
python -c "
import os
test_path = 'data/videos/test'
os.makedirs(test_path, exist_ok=True)
with open(f'{test_path}/test.txt', 'w') as f:
    f.write('WSL path test')
print('WSL file operations working correctly')
os.remove(f'{test_path}/test.txt')
os.rmdir(test_path)
"
```

#### X11 Forwarding (for GUI applications)
```bash
# Install X11 support
sudo apt update
sudo apt install x11-apps

# Test X11 forwarding
echo $DISPLAY
# Should show: localhost:10.0 or similar
```

## Running the Application

### V2 Application Startup

1. **Activate Environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Start V2 Application**:
   ```bash
   python -m app.main_v2
   ```

3. **Verify Startup**:
   ```bash
   # Check logs for successful initialization
   tail -f logs/app.log
   
   # Expected output:
   # INFO - All services initialized successfully
   # INFO - Services assigned to app.state
   # INFO - Application startup complete
   ```

### Access Points

- **Main Application**: http://localhost:8000/
- **V2 Stream**: http://localhost:8000/v2/stream  
- **V2 Results**: http://localhost:8000/v2/results
- **API Documentation**: http://localhost:8000/docs

### V1 Compatibility

The V2 system maintains backward compatibility:

- **V1 Stream**: http://localhost:8000/stream
- **V1 Results**: http://localhost:8000/results/latest
- **V1 Detection**: http://localhost:8000/detection

## Testing Installation

### Automated Tests

```bash
# Run basic functionality tests
cd tests/unit_tests

# Test video recording
python test_annotated_video.py

# Test service integration  
python debug_services.py

# Test storage functionality
python test_troubleshooting.py
```

### Manual Verification

#### 1. Camera Access Test
```bash
# Test camera streaming
curl http://localhost:8000/v2/stream
# Should return MJPEG stream data
```

#### 2. Detection Test
```bash
# Upload test image for detection
curl -X POST "http://localhost:8000/v2/detection/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@images/test_plate.jpg"
```

#### 3. Storage Test
```bash
# Check if JSON files are created
ls -la data/license_plates/
ls -la data/enhanced_plates/

# Check SQLite database
sqlite3 data/license_plates.db "SELECT COUNT(*) FROM detections;"
```

#### 4. Video Recording Test
```bash
# Check video directory after detection
ls -la data/videos/$(date +%Y-%m-%d)/
# Should show .mp4 files after detections
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Problem: ModuleNotFoundError
# Solution: Verify virtual environment activation
source .venv/bin/activate
which python
pip list | grep torch
```

#### 2. CUDA Not Available
```bash
# Problem: GPU not detected
# Solution: Check NVIDIA drivers and CUDA installation
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

#### 3. Camera Access Issues
```bash
# Problem: Cannot access camera
# Solution: Check permissions and device availability
sudo chmod 666 /dev/video0
ls -la /dev/video*
```

#### 4. File Permission Errors
```bash
# Problem: Permission denied on file operations
# Solution: Fix directory permissions
chmod -R 755 data/
chmod -R 755 logs/
```

#### 5. WSL Video Recording Issues
```bash
# Problem: Video files not created
# Solution: Use relative paths and sync filesystem
python -c "
import subprocess
subprocess.run(['sync'], check=False)
print('Filesystem synced')
"
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Create debug configuration
echo "LOG_LEVEL=DEBUG" >> .env

# Run with verbose output
python -m app.main_v2 --log-level DEBUG
```

### Performance Optimization

#### Frame Processing Optimization
```bash
# Adjust processing interval in .env
echo "PROCESS_EVERY_N_FRAMES=5" >> .env

# For slower systems, increase to 10
echo "PROCESS_EVERY_N_FRAMES=10" >> .env
```

#### Memory Optimization
```bash
# Reduce buffer size for lower memory usage
echo "VIDEO_BUFFER_SECONDS=3" >> .env
echo "POST_EVENT_SECONDS=10" >> .env
```

## Production Deployment

### Systemd Service (Linux)

1. **Create Service File**:
   ```bash
   sudo nano /etc/systemd/system/lpr-v2.service
   ```

2. **Service Configuration**:
   ```ini
   [Unit]
   Description=License Plate Recognition V2
   After=network.target
   
   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/plate_recognition
   Environment=PATH=/path/to/plate_recognition/.venv/bin
   ExecStart=/path/to/plate_recognition/.venv/bin/python -m app.main_v2
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable lpr-v2
   sudo systemctl start lpr-v2
   sudo systemctl status lpr-v2
   ```

### Docker Deployment

1. **Build Docker Image**:
   ```bash
   docker build -t lpr-v2:latest .
   ```

2. **Run Container**:
   ```bash
   docker run -d \
     --name lpr-v2 \
     -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     --device /dev/video0:/dev/video0 \
     lpr-v2:latest
   ```

## Maintenance

### Regular Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update models (if needed)
cd app/models
wget -O yolo11m.pt https://github.com/ultralytics/assets/releases/download/v8.2.0/yolo11m.pt

# Restart service
sudo systemctl restart lpr-v2
```

### Log Rotation

```bash
# Setup log rotation
sudo nano /etc/logrotate.d/lpr-v2

# Configuration:
/path/to/plate_recognition/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    postrotate
        systemctl reload lpr-v2
    endscript
}
```

### Database Maintenance

```bash
# Backup database
cp data/license_plates.db data/license_plates.db.backup

# Cleanup old records (optional)
sqlite3 data/license_plates.db "
DELETE FROM detections WHERE timestamp < datetime('now', '-30 days');
VACUUM;
"
```

This installation guide provides comprehensive setup instructions for the V2 License Plate Recognition System with special attention to WSL compatibility and modern development practices.