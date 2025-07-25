# 🚀 Implementation & Deployment Guide

**Date**: 2025-07-25  
**Status**: 📋 **READY TO IMPLEMENT**  
**Goal**: Step-by-step deployment of 24/7 recording system

## 🎯 Implementation Order

### Phase 1: Core Recording Service (Priority 1)
**Goal**: Get continuous recording working independently
**Time**: 2-3 days

### Phase 2: Storage & Playback (Priority 2)  
**Goal**: Implement efficient storage and video playback
**Time**: 2 days

### Phase 3: Web Integration (Priority 3)
**Goal**: Connect recording system to web UI
**Time**: 1-2 days

## 📁 Directory Structure

```
project/
├── core/
│   ├── recording/
│   │   ├── __init__.py
│   │   ├── continuous_recorder.py
│   │   ├── recording_manager.py
│   │   └── config.py
│   ├── playback/
│   │   ├── __init__.py
│   │   ├── video_playback.py
│   │   └── timeline_generator.py
│   └── storage/
│       ├── __init__.py
│       ├── storage_manager.py
│       └── cleanup_service.py
├── config/
│   ├── cameras.json
│   └── recording_settings.json
├── recordings/           # Video storage directory
│   ├── camera_1/
│   ├── camera_2/
│   └── ...
├── main_recording_service.py
├── requirements.txt
└── docker-compose.yml
```

## ⚙️ Configuration Files

### cameras.json
```json
{
  "cameras": [
    {
      "id": 1,
      "name": "Test Camera 1",
      "rtsp_url": "rtsp://admin:Mekus_1987@10.0.0.181:554/h264Preview_01_sub",
      "recording_enabled": true,
      "live_streaming_enabled": true,
      "resolution": {
        "width": 640,
        "height": 480
      },
      "fps": 30,
      "recording_quality": "medium"
    }
  ]
}
```

### recording_settings.json
```json
{
  "recording": {
    "segment_duration_seconds": 600,
    "buffer_size_frames": 300,
    "reconnect_delay_seconds": 2,
    "max_reconnect_delay_seconds": 30
  },
  "storage": {
    "base_path": "/recordings",
    "retention_days": 30,
    "hot_storage_days": 7,
    "max_storage_gb_per_camera": 500,
    "cleanup_interval_hours": 1
  },
  "video": {
    "codec": "mp4v",
    "quality": "medium",
    "enable_audio": false
  }
}
```

## 🐳 Docker Deployment

### docker-compose.yml
```yaml
version: '3.8'

services:
  recording-service:
    build: .
    container_name: lpr-recording
    restart: unless-stopped
    volumes:
      - ./recordings:/recordings
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - PYTHONPATH=/app
    networks:
      - lpr-network
    depends_on:
      - redis
    
  web-backend:
    build: ./backend
    container_name: lpr-backend
    restart: unless-stopped
    ports:
      - "8001:8001"
    volumes:
      - ./recordings:/recordings:ro  # Read-only access to recordings
    networks:
      - lpr-network
    depends_on:
      - recording-service
      
  redis:
    image: redis:7-alpine
    container_name: lpr-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - lpr-network

networks:
  lpr-network:
    driver: bridge

volumes:
  redis_data:
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    python3-opencv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create recordings directory
RUN mkdir -p /recordings

# Run the recording service
CMD ["python", "main_recording_service.py"]
```

### requirements.txt
```
opencv-python==4.8.1.78
fastapi==0.104.1
uvicorn==0.24.0
redis==5.0.1
pydantic==2.5.0
python-multipart==0.0.6
aiofiles==23.2.1
```

## 🔧 Implementation Steps

### Step 1: Core Recording Service

Create the main service file:

```python
# main_recording_service.py
import asyncio
import json
import logging
import signal
import sys
from pathlib import Path

from core.recording.recording_manager import RecordingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/recording.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class RecordingService:
    def __init__(self):
        self.recording_manager = RecordingManager()
        self.running = True
        
    async def start(self):
        """Start the recording service"""
        logger.info("Starting 24/7 Recording Service...")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Start all camera recordings
            await self.recording_manager.start_all_recordings()
            logger.info("All recordings started successfully")
            
            # Main service loop
            while self.running:
                await asyncio.sleep(30)  # Health check every 30 seconds
                await self._health_check()
                
        except Exception as e:
            logger.error(f"Service error: {e}")
        finally:
            await self._shutdown()
    
    async def _health_check(self):
        """Perform health checks and restart failed recordings"""
        try:
            await self.recording_manager.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
    
    async def _shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down recording service...")
        await self.recording_manager.stop_all_recordings()
        logger.info("Recording service stopped")

async def main():
    # Ensure directories exist
    Path("logs").mkdir(exist_ok=True)
    Path("recordings").mkdir(exist_ok=True)
    
    # Start the service
    service = RecordingService()
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Enhanced Recording Manager

```python
# core/recording/recording_manager.py
import json
import logging
from typing import Dict, List
from .continuous_recorder import Contin