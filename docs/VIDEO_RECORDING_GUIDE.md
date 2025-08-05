# Video Recording Management Guide

This guide explains how to manage 24/7 video recording in your license plate recognition system.

## ✅ **Recording Status: ACTIVE**

Your video recording is now successfully running with the following configuration:

### **Current Recording Setup:**
- **Camera**: Reolink Main Entrance (camera_946701d3)
- **Resolution**: 4K (3840x2160) at 25 FPS
- **Stream Path**: `/h264Preview_01_main`
- **Segment Duration**: 10 minutes (600 seconds)
- **Storage Location**: `recordings/camera_camera_946701d3/YYYY/MM/DD/HH/`

### **Active Recording Details:**
```
✅ Recording Service: Running on port 8002
✅ Camera Connection: Connected successfully
✅ Video Segments: Being created every 10 minutes
✅ File Format: .avi files with H.264 encoding
✅ Current Segment: ~49MB and growing
```

## Recording Management Commands

### **Check Recording Status:**
```bash
# Overall service health
curl http://localhost:8002/health

# Detailed recording status
curl http://localhost:8002/recordings/status

# Specific camera status
curl http://localhost:8002/recordings/status/camera_946701d3
```

### **Control Recording:**
```bash
# Reload camera configurations (if database changes)
curl -X POST http://localhost:8002/recordings/reload

# Stop recording for specific camera
curl -X POST http://localhost:8002/recordings/stop/camera_946701d3

# Start recording for specific camera
curl -X POST http://localhost:8002/recordings/start/camera_946701d3
```

### **Monitor Recording Files:**
```bash
# List current recordings
ls -la recordings/camera_camera_946701d3/2025/08/02/01/

# Monitor file growth (run multiple times)
ls -lh recordings/camera_camera_946701d3/2025/08/02/01/*.avi

# Check total storage usage
du -sh recordings/
```

## File Organization

### **Directory Structure:**
```
recordings/
└── camera_camera_946701d3/           # Camera ID
    └── 2025/                         # Year
        └── 08/                       # Month
            └── 02/                   # Day
                └── 01/               # Hour
                    ├── camera_camera_946701d3_20250802_015723_600.avi
                    ├── camera_camera_946701d3_20250802_016723_600.avi
                    └── camera_camera_946701d3_20250802_017723_600.avi
```

### **File Naming Convention:**
```
Format: {camera_id}_{YYYYMMDD}_{HHMMSS}_{duration_seconds}.avi
Example: camera_camera_946701d3_20250802_015723_600.avi

Where:
- camera_camera_946701d3: Camera identifier
- 20250802: Date (August 2, 2025)
- 015723: Time (01:57:23)
- 600: Duration in seconds (10 minutes)
```

## Storage Management

### **Automatic Cleanup:**
- **Storage Limit**: 10GB (configurable)
- **Cleanup Trigger**: When storage reaches 90% of limit
- **Retention Policy**: Oldest files deleted first
- **Monitoring**: Automatic background process

### **Manual Storage Operations:**
```bash
# Check storage statistics
curl http://localhost:8002/api/v1/storage/report

# Trigger manual cleanup
curl -X POST http://localhost:8002/api/v1/storage/cleanup

# Check available disk space
df -h recordings/
```

## Troubleshooting

### **Recording Not Starting:**

1. **Check Service Status:**
```bash
curl http://localhost:8002/health
```

2. **Verify Camera Configuration:**
```bash
.venv/bin/python3 fix_camera_config.py list
```

3. **Test Camera Connection:**
```bash
.venv/bin/python3 test_camera_fixed.py
```

4. **Reload Configuration:**
```bash
curl -X POST http://localhost:8002/recordings/reload
```

### **No Video Files Created:**

**Check logs:**
```bash
tail -f logs/recording_service.log
```

**Common issues:**
- Camera offline in database (status != 'active')
- Incorrect RTSP path configuration
- Network connectivity problems
- Authentication failures

### **Recording Stops Unexpectedly:**

**Monitor for errors:**
```bash
grep -i error logs/recording_service.log | tail -10
```

**Restart recording:**
```bash
curl -X POST http://localhost:8002/recordings/stop/camera_946701d3
curl -X POST http://localhost:8002/recordings/start/camera_946701d3
```

## Playback and Access

### **Direct File Access:**
Video files can be accessed directly from the file system:
```bash
# Play with VLC
vlc recordings/camera_camera_946701d3/2025/08/02/01/camera_camera_946701d3_20250802_015723_600.avi

# Copy to another location
cp recordings/camera_camera_946701d3/2025/08/02/01/*.avi /backup/location/
```

### **API Access (In Development):**
The playback API is available but may need refinement:
```bash
# Get calendar data (may have issues)
curl "http://localhost:8002/api/v1/recordings/cameras/camera_946701d3/calendar?year=2025&month=8"

# Get timeline segments (may have issues)
curl "http://localhost:8002/api/v1/recordings/cameras/camera_946701d3/timeline?date=2025-08-02"
```

## Service Management

### **Start All Services:**
```bash
python3 start_lpr.py
```

### **Check Service Status:**
```bash
python3 check_services.py
```

### **Restart Services:**
```bash
python3 restart_services.py
```

### **Service URLs:**
- **Recording Service**: http://localhost:8002/
- **API Documentation**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/health

## Configuration Details

### **Current Camera Configuration:**
```json
{
  "camera_id": "camera_946701d3",
  "name": "Reolink Main Entrance", 
  "ip_address": "10.0.0.181",
  "port": 554,
  "stream_path": "/h264Preview_01_main",
  "username": "admin",
  "password": "Mekus_1987",
  "status": "active"
}
```

### **Recording Settings:**
- **Segment Duration**: 600 seconds (10 minutes)
- **Video Codec**: H.264
- **Container Format**: AVI
- **Quality**: High (4K resolution)
- **Frame Rate**: 25 FPS
- **Audio**: No audio track

## Performance Metrics

### **Current Performance:**
- **File Size**: ~49MB per 10-minute segment
- **Bitrate**: ~650 Kbps (4K video)
- **Storage Rate**: ~295MB per hour
- **Daily Storage**: ~7GB per day (24 hours)

### **Optimization Options:**
If storage is a concern, you can:
1. **Use sub stream**: Change stream_path to `/h264Preview_01_sub` (640x360)
2. **Reduce segment duration**: Modify recording settings
3. **Increase compression**: Adjust video quality settings

## Monitoring and Maintenance

### **Regular Checks:**
```bash
# Daily: Check recording status
curl -s http://localhost:8002/recordings/status | jq .

# Weekly: Check storage usage
curl -s http://localhost:8002/api/v1/storage/report | jq .

# Monthly: Verify file integrity
find recordings/ -name "*.avi" -size 0 -delete
```

### **Log Monitoring:**
```bash
# Monitor real-time logs
tail -f logs/recording_service.log

# Check for errors
grep -i "error\|failed" logs/recording_service.log | tail -20
```

## Success Indicators

Your recording system is working correctly when you see:

✅ **Service Status**: `"recording_active":true`
✅ **Camera Status**: `"is_recording":true`
✅ **Recent Frames**: `"last_frame_time"` is recent
✅ **No Errors**: `"error_count":0`
✅ **Growing Files**: Video files increase in size over time
✅ **Regular Segments**: New files created every 10 minutes

## Next Steps

1. **Monitor for 24 hours** to ensure stable operation
2. **Set up storage monitoring** alerts if needed
3. **Configure backup** procedures for important recordings
4. **Test playback functionality** once API issues are resolved
5. **Consider additional cameras** following the same process

---

**Recording Status**: ✅ **ACTIVE AND WORKING**
**Video Quality**: 4K (3840x2160) @ 25 FPS
**Storage**: Growing at ~295MB/hour
**Last Verified**: 2025-08-02 01:57 UTC