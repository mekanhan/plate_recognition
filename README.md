# License Plate Recognition System

A comprehensive License Plate Recognition (LPR) system with 24/7 recording capabilities, real-time detection, and web-based management interface.

## 🚀 Quick Start

The easiest way to start the entire system:

```bash
cd /home/mekanhan/github/learning/plate_recognition
python3 start_lpr.py
```

This single command will:
- ✅ Check database schema
- ✅ Start all three services
- ✅ Show you the access URLs

## 📋 System Components

### 1. **Main API Service** (Port 8001)
- FastAPI backend for camera management
- License plate detection with YOLO
- Camera snapshot serving
- Database operations

### 2. **Recording Service** (Port 8002)
- 24/7 continuous recording
- 10-minute video segments
- Automatic storage management
- Recording playback API

### 3. **Frontend Server** (Port 8080)
- Web dashboard interface
- Camera management UI
- Recording playback interface
- Real-time monitoring

## 🔧 Service Management

### Start All Services
```bash
# Recommended - Simple start
python3 start_lpr.py

# Alternative - Full monitoring
python3 start_all_services.py

# Alternative - Restart everything
python3 restart_services.py
```

### Stop All Services
```bash
python3 stop_all_services.py
```

### Check Service Health
```bash
# Single health check
python3 check_services.py

# Continuous monitoring
python3 check_services.py -m 30
```

### Manual Service Control
If you need to start services individually:

```bash
# Terminal 1 - Main API
python3 -m api.main

# Terminal 2 - Recording Service
python3 start_recording_service.py

# Terminal 3 - Frontend
cd frontend && python3 -m http.server 8080
```

## 🌐 Access URLs

Once services are running:

- **Frontend Dashboard**: http://localhost:8080/
- **Main API Docs**: http://localhost:8001/docs
- **Recording API Docs**: http://localhost:8002/docs

## 📊 System Features

### Camera Management
- Dynamic camera configuration through web UI
- Test camera connections before saving
- Support for RTSP/HTTP/HTTPS streams
- Automatic reconnection on failures

### 24/7 Recording
- Continuous recording to 10-minute segments
- Organized storage: `recordings/camera_id/YYYY/MM/DD/HH/`
- 30-day retention with automatic cleanup
- Segment-based playback with timeline

### License Plate Detection
- Real-time detection using YOLO models
- OCR for plate text recognition
- Detection history and search
- Analytics dashboard

### Web Interface
- Live camera snapshots (not video streaming)
- Recording playback with calendar view
- Camera configuration UI
- System health monitoring

## 🛠️ Troubleshooting

### If Services Won't Start

1. **Check Python Environment**
   ```bash
   # The scripts automatically detect .venv/bin/python3
   # Or ensure you're in the virtual environment:
   source .venv/bin/activate
   ```

2. **Check Port Availability**
   ```bash
   # Check if ports are in use
   lsof -i :8001 -i :8002 -i :8080
   ```

3. **Update Database Schema**
   ```bash
   python3 update_database_schema.py
   ```

4. **Check Logs**
   ```bash
   # All services create timestamped logs
   ls -la logs/
   tail -f logs/main_api_*.log
   tail -f logs/recording_service_*.log
   ```

### Common Issues

**"No module named 'fastapi'"**
- Ensure you're using the virtual environment
- Install dependencies: `pip install -r requirements.txt`

**"Port already in use"**
- Run `python3 stop_all_services.py` first
- Or manually kill processes on the ports

**"Database schema error"**
- Run `python3 update_database_schema.py`
- This safely adds any missing columns

## 📁 Directory Structure

```
plate_recognition/
├── api/                    # Main API service
│   └── main.py            # FastAPI application
├── recording_service/      # 24/7 recording service
│   ├── main.py            # Recording API
│   └── services/          # Recording components
├── frontend/              # Web interface
│   ├── index.html         # Main dashboard
│   └── src/               # JavaScript components
├── database/              # Database models
├── ai_pipeline/           # AI detection pipeline
├── logs/                  # Service log files
├── recordings/            # Video recordings
├── data/                  # SQLite database
└── *.py                   # Service management scripts
```

## 🔒 Security Notes

- Camera passwords are stored in database (consider encryption in production)
- API endpoints are not authenticated (add authentication for production)
- Recording storage is local (consider cloud storage for production)

## 🚧 Development

### Adding New Features
1. Main API changes: Edit `api/main.py`
2. Recording features: Edit `recording_service/main.py`
3. Frontend changes: Edit files in `frontend/src/`

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Test specific component
python test_api.py
python test_camera.py
python test_ai.py
```

## 📌 Important Notes

1. **No Browser Video Streaming**: The system uses snapshots in the browser, not live video streams
2. **Use VLC for Live Video**: Click "Open in VLC" buttons for live RTSP streams
3. **Automatic Camera Loading**: Cameras configured through the UI are automatically used by all services
4. **Continuous Recording**: The recording service runs 24/7 independently of the web UI

## 🆘 Getting Help

1. Check service health: `python3 check_services.py`
2. Review logs in the `logs/` directory
3. Ensure all dependencies are installed
4. Verify camera configurations in the web UI

For more detailed documentation, see:
- `README_SERVICE_MANAGEMENT.md` - Detailed service script documentation
- `CLAUDE.md` - Development guidelines and commands
- `docs/` - Additional documentation