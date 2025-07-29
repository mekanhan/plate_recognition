# Troubleshooting Guide

## Common Issues and Solutions

### 1. Backend API Hanging

**Symptoms:**
- `/api/v1/cameras/` takes forever to load
- Backend process shows high CPU usage
- Frontend displays "Loading cameras..." indefinitely

**Root Cause:**
- Circular imports during module initialization
- Frame distribution manager creating global instance at import time

**Solution:**
```python
# Change from:
frame_distribution_manager = FrameDistributionManager()

# To lazy initialization:
_frame_distribution_manager = None

def get_frame_distribution_manager():
    global _frame_distribution_manager
    if _frame_distribution_manager is None:
        _frame_distribution_manager = FrameDistributionManager()
    return _frame_distribution_manager
```

### 2. Import Errors

**Error Message:**
```
ImportError: cannot import name 'frame_distribution_manager' from 'app.services.frame_distribution_service'
```

**Solution:**
Update all imports to use the getter function:
```python
# Old import:
from app.services.frame_distribution_service import frame_distribution_manager

# New import:
from app.services.frame_distribution_service import get_frame_distribution_manager

# Usage:
frame_manager = get_frame_distribution_manager()
```

### 3. Camera Connection Failures

**Symptoms:**
- "Failed to connect to camera" error
- Camera status shows "error" in database
- No frames available for streaming

**Diagnostic Steps:**
```bash
# Check camera connectivity
curl http://localhost:8001/api/v1/streams/diagnostics/3

# Check frame distributor status
curl http://localhost:8001/api/v1/streams/status/3

# Monitor backend logs
tail -f backend/server.log | grep -E "(camera|frame|connection)"
```

### 4. Stream Not Starting

**Symptoms:**
- Start button doesn't work
- Stream shows black screen
- "Too many active streams" error

**Solutions:**
1. Check if frame distributor is running:
   ```python
   distributor = frame_manager.get_distributor(camera_id)
   if not distributor or not distributor.is_running:
       # Restart distributor
   ```

2. Check consumer limits:
   ```python
   max_consumers = 5  # Configured limit
   if len(self.consumers) >= max_consumers:
       # Remove inactive consumers or increase limit
   ```

### 5. Frontend Not Loading Cameras

**Symptoms:**
- Cameras page shows no cameras
- Console shows CORS errors
- API requests timing out

**Solutions:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8001/health
   ```

2. Check port configuration:
   ```javascript
   // frontend/src/config/app.config.js
   API_BASE_URL: 'http://localhost:8001',  // Must match backend port
   ```

3. Test with fallback data:
   ```javascript
   // Frontend includes fallback for testing
   const fallbackCameras = [{
       id: 3,
       name: "Test Camera 1",
       // ... other fields
   }];
   ```

## Debugging Commands

### Check Backend Status
```bash
# Process status
ps aux | grep uvicorn

# Port usage
ss -tlnp | grep :8001

# Kill stuck process
kill -9 $(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')
```

### Monitor Logs
```bash
# Backend startup logs
tail -f backend/server.log

# Recording service logs
tail -f backend/logs/recording_service.log

# Watch for specific errors
tail -f backend/server.log | grep -E "(ERROR|CRITICAL|deadlock|timeout)"
```

### API Testing
```bash
# Test basic health
curl -s -w "Time: %{time_total}s\n" http://localhost:8001/health

# Test cameras endpoint
curl -s -w "Time: %{time_total}s\n" http://localhost:8001/api/v1/cameras/

# Test stream status
curl http://localhost:8001/api/v1/streams/status/3

# Start stream
curl -X POST http://localhost:8001/api/v1/streams/start/3 \
  -H "Content-Type: application/json" \
  -d '{"quality": "medium", "max_fps": 30}'
```

## Performance Monitoring

### Check Response Times
```bash
# Monitor API performance
while true; do
    echo -n "$(date): "
    curl -s -w "%{time_total}s\n" -o /dev/null http://localhost:8001/api/v1/cameras/
    sleep 5
done
```

### Frame Distribution Stats
```bash
# Get detailed stats for camera
curl http://localhost:8001/api/v1/streams/status/3 | jq '.settings'
```

## Recovery Procedures

### 1. Complete Backend Restart
```bash
cd backend
pkill -f uvicorn
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 2. Clear Stuck Connections
```python
# In Python shell
from app.services.frame_distribution_service import get_frame_distribution_manager
manager = get_frame_distribution_manager()
manager.stop_all()  # Stop all distributors
manager.distributors.clear()  # Clear registry
```

### 3. Database Status Reset
```sql
-- Reset all camera statuses
UPDATE cameras SET status = 'offline' WHERE status = 'error';
```

## Prevention Best Practices

1. **Always use lazy initialization** for global services
2. **Avoid circular imports** by using import functions
3. **Monitor resource usage** during development
4. **Test with multiple concurrent users**
5. **Implement proper cleanup** in shutdown handlers

## Known Limitations

1. Maximum 5 consumers per camera (configurable)
2. Frame queues have size limits to prevent memory overflow
3. Reconnection attempts limited to prevent infinite loops
4. CORS must be properly configured for frontend access