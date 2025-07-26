# 🚀 Phase 2 Deployment Guide

## Quick Start

### 1. Restart the Backend (to load new endpoints)
```bash
# Stop current backend
pkill -f "uvicorn app.main:app"

# Start with new Phase 2 endpoints
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 2. Restart Recording Service (with storage management)
```bash
# Stop current recording service
pkill -f "main_recording_service"

# Start with Phase 2 storage management
cd backend
source venv/bin/activate
python main_recording_service.py
```

## 🔧 Available APIs

### **Playback Endpoints**
```bash
# Health check
curl http://localhost:8001/api/v1/playback/health

# Get timeline for camera 3 (last 24 hours)
START_TIME=$(date -d "1 day ago" --iso-8601)T00:00:00
END_TIME=$(date --iso-8601)T23:59:59
curl "http://localhost:8001/api/v1/playback/cameras/3/timeline?start_time=${START_TIME}&end_time=${END_TIME}"

# Get storage report
curl http://localhost:8001/api/v1/playback/storage/report | python3 -m json.tool

# Search recordings for camera 3
curl "http://localhost:8001/api/v1/playback/cameras/3/search?start_date=${START_TIME}&end_date=${END_TIME}" | python3 -m json.tool
```

### **Video Streaming**
```bash
# Stream a video segment (replace with actual segment ID)
curl "http://localhost:8001/api/v1/playback/segments/3_camera_3_20250725_182548_600.avi/stream" --output test_video.avi

# Get segment information
curl "http://localhost:8001/api/v1/playback/segments/3_camera_3_20250725_182548_600.avi/info" | python3 -m json.tool
```

## 📊 Storage Management

### **Automatic Features** (No action needed)
- ✅ **Daily cleanup**: Removes recordings older than 30 days
- ✅ **Hourly monitoring**: Checks disk space and logs health
- ✅ **Background tasks**: Runs automatically with recording service

### **Manual Operations**
```bash
# Force cleanup for camera 3
curl -X POST "http://localhost:8001/api/v1/playback/storage/cleanup?camera_id=3" | python3 -m json.tool

# Get camera 3 storage stats
curl "http://localhost:8001/api/v1/playback/storage/cameras/3/stats" | python3 -m json.tool

# Trigger full system cleanup
curl -X POST "http://localhost:8001/api/v1/playback/storage/cleanup" | python3 -m json.tool
```

## ⚙️ Configuration

### **Storage Settings** (`config/storage_settings.json`)
```json
{
  "storage": {
    "retention_days": 30,              // Keep recordings for 30 days
    "hot_storage_days": 7,             // Keep recent 7 days for fast access
    "max_storage_gb_per_camera": 500,  // Limit per camera (500GB)
    "warning_threshold_percent": 80,   // Warn when disk 80% full
    "critical_threshold_percent": 90,  // Alert when disk 90% full
    "cleanup_interval_hours": 1,       // Clean up every hour
    "monitoring_interval_minutes": 30  // Monitor every 30 minutes
  }
}
```

## 📁 File Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── storage_manager.py          ✨ NEW
│   │   ├── playback/
│   │   │   ├── __init__.py                 ✨ NEW
│   │   │   └── video_playback.py           ✨ NEW
│   │   └── recording/
│   │       ├── recording_manager.py        📝 ENHANCED 
│   │       └── continuous_recorder.py
│   └── api/v1/endpoints/
│       ├── playback.py                     ✨ NEW
│       ├── streaming.py
│       └── cameras.py
├── config/
│   ├── storage_settings.json              ✨ NEW
│   └── cameras.json
├── main_recording_service.py               📝 ENHANCED
└── recordings/                             📁 AUTO-MANAGED
    └── camera_3/
        ├── index.db
        └── 2025/07/25/18/
            └── camera_3_20250725_182548_600.avi
```

## 🎯 What Changed

### **Zero Breaking Changes**
- ✅ All existing streaming endpoints work unchanged
- ✅ Current recording continues without interruption  
- ✅ Database schema and file structure preserved
- ✅ Frontend compatibility maintained

### **New Capabilities**
- ✅ **Storage Management**: Automatic cleanup and monitoring
- ✅ **Video Playback**: Timeline-based access to recordings
- ✅ **HTTP Streaming**: Range request support for seeking
- ✅ **Storage Analytics**: Comprehensive reporting APIs
- ✅ **Health Monitoring**: Storage health integrated into service

## 🚨 Monitoring

### **Logs to Watch**
```bash
# Recording service with storage management
tail -f logs/recording.log

# Backend API with playback endpoints  
tail -f server.log
```

### **Key Log Messages**
```
✅ "Storage manager started" - Storage management active
✅ "Started recording for X cameras with storage management" - Integration working
✅ "Storage Health: X segments, Y GB used, Z% disk free" - Health monitoring
✅ "Cleanup complete: Removed X segments, freed Y GB" - Automatic cleanup
```

## 🎉 Success Verification

### **1. Check Storage Management**
```bash
# Should show storage stats
curl http://localhost:8001/api/v1/playback/storage/report | grep -E "total_segments|total_size"
```

### **2. Check Video Playback**
```bash
# Should return camera timeline
curl "http://localhost:8001/api/v1/playback/cameras/3/timeline?start_time=2025-07-25T00:00:00&end_time=2025-07-26T00:00:00" | grep -E "total_segments"
```

### **3. Check Recording Integration**
```bash
# Should show storage management in logs
grep "storage management" logs/recording.log
```

## 🔧 Troubleshooting

### **API Not Working**
```bash
# Check if backend includes new endpoints
curl http://localhost:8001/docs | grep playback
```

### **Storage Not Cleaning**
```bash
# Check storage manager is running
grep "Storage manager started" logs/recording.log

# Manually trigger cleanup
curl -X POST http://localhost:8001/api/v1/playback/storage/cleanup
```

### **Playback Not Working**
```bash
# Check recordings directory exists
ls -la recordings/

# Check segment index database
ls -la recordings/camera_*/index.db
```

---

## ✅ **Phase 2 is Ready for Production!**

Your 24/7 recording system now includes:
- 🏪 **Enterprise storage management** with automatic cleanup
- 🎬 **Professional video playback** with timeline scrubbing  
- 📊 **Comprehensive monitoring** and health reporting
- 🚀 **Production-ready APIs** for all functionality