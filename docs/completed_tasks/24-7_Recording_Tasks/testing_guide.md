# 24/7 Recording System - Testing Guide

This document provides comprehensive testing procedures to validate the 24/7 recording system functionality, reliability, and performance.

## 🧪 Testing Overview

### Test Categories
1. **Functional Testing** - Core recording functionality
2. **Integration Testing** - API and service interaction
3. **Reliability Testing** - Long-term operation and error recovery
4. **Performance Testing** - Resource usage and throughput
5. **Security Testing** - API security and data protection

## ✅ Pre-Test Setup

### Environment Requirements
```bash
# Ensure services are running
cd backend
source venv/bin/activate

# Check recording service status
ps aux | grep main_recording_service
ps aux | grep recording_api_service

# Verify network connectivity to camera
ping 10.0.0.181

# Check disk space
df -h
```

### Test Data Validation
```bash
# Verify existing recordings
ls -la recordings/camera_3/
sqlite3 recordings/camera_3/index.db "SELECT COUNT(*) FROM segments;"

# Check log files
tail -f logs/recording_service.log
```

## 🔧 1. Functional Testing

### 1.1 Recording Service Health Check
**Objective:** Verify recording service is operational and healthy

```bash
# Test 1: Service health endpoint
curl -v http://localhost:8002/health

# Expected Response:
# - HTTP 200 status
# - JSON with "status": "healthy"
# - active_cameras > 0
# - total_segments > 0
```

**Validation Criteria:**
- ✅ Service responds within 2 seconds
- ✅ Returns valid JSON structure
- ✅ Reports active camera recordings
- ✅ Storage statistics are accurate

### 1.2 Continuous Recording Validation
**Objective:** Confirm continuous video recording is working

```bash
# Test 2: Check recent recordings
CURRENT_HOUR=$(date +%Y/%m/%d/%H)
ls -la recordings/camera_3/$CURRENT_HOUR/

# Test 3: Monitor new segment creation
watch -n 30 "ls -la recordings/camera_3/$CURRENT_HOUR/ | tail -3"

# Test 4: Verify segment duration (should be ~600 seconds)
curl -s http://localhost:8002/recordings/3/segments | grep duration
```

**Validation Criteria:**
- ✅ New segments created every 10 minutes
- ✅ Segment files are valid video format
- ✅ File sizes are reasonable (15-25MB typical)
- ✅ Database entries match file system

### 1.3 Database Integrity
**Objective:** Ensure SQLite index database is accurate

```bash
# Test 5: Database consistency check
sqlite3 recordings/camera_3/index.db << EOF
SELECT 
    COUNT(*) as total_segments,
    MIN(start_time) as oldest,
    MAX(start_time) as newest,
    SUM(file_size) as total_size
FROM segments;
EOF

# Test 6: Verify file system matches database
SEGMENT_COUNT=$(find recordings/camera_3/ -name "*.avi" | wc -l)
DB_COUNT=$(sqlite3 recordings/camera_3/index.db "SELECT COUNT(*) FROM segments;")
echo "File system: $SEGMENT_COUNT, Database: $DB_COUNT"
```

**Validation Criteria:**
- ✅ File count matches database count
- ✅ Total file size matches database sum
- ✅ No orphaned files or database entries
- ✅ Timestamps are sequential and valid

## 🔗 2. Integration Testing

### 2.1 API Endpoint Testing
**Objective:** Validate all REST API endpoints

```bash
# Test 7: Root endpoint
curl -s http://localhost:8002/ | jq '.status'

# Test 8: All recordings status
curl -s http://localhost:8002/recordings/status | jq '.total_cameras'

# Test 9: Specific camera status
curl -s http://localhost:8002/recordings/status/3 | jq '.is_active'

# Test 10: Storage report
curl -s http://localhost:8002/storage/report | jq '.system_stats.total_segments'

# Test 11: Segment listing with time range
START_TIME=$(date -d "1 hour ago" -Iseconds)
curl -s "http://localhost:8002/recordings/3/segments?start_time=$START_TIME" | jq '.total_segments'
```

**Validation Criteria:**
- ✅ All endpoints return HTTP 200
- ✅ JSON responses are well-formed
- ✅ Data values are realistic and consistent
- ✅ Time range filtering works correctly

### 2.2 CORS and Headers Testing
**Objective:** Verify API can be accessed from web applications

```bash
# Test 12: CORS headers
curl -s -H "Origin: http://localhost:8080" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS http://localhost:8002/health

# Test 13: Content-Type headers
curl -s -I http://localhost:8002/health | grep -i content-type
```

**Validation Criteria:**
- ✅ CORS headers present and permissive
- ✅ Content-Type is application/json
- ✅ No authentication errors
- ✅ Headers allow cross-origin requests

## 🔄 3. Reliability Testing

### 3.1 Service Restart Testing
**Objective:** Verify graceful shutdown and restart

```bash
# Test 14: Graceful shutdown
pkill -TERM -f main_recording_service
sleep 5

# Check final segment was properly closed
tail -n 10 logs/recording_service.log | grep "Finalized segment"

# Test 15: Service restart
nohup python main_recording_service.py > logs/recording_service.log 2>&1 &
sleep 30

# Verify recording resumed
curl -s http://localhost:8002/health | jq '.active_cameras'
```

**Validation Criteria:**
- ✅ Service shuts down cleanly within 10 seconds
- ✅ Current segment is properly finalized
- ✅ Database connections are closed
- ✅ Service restarts and resumes recording

### 3.2 Network Disconnection Testing
**Objective:** Test camera reconnection handling

```bash
# Test 16: Simulate network disconnection
# (This requires network control or camera power cycling)

# Monitor logs during disconnection
tail -f logs/recording_service.log | grep -E "(Lost connection|Successfully connected)"

# Check reconnection behavior
# - Should see "Lost connection" messages
# - Should see exponential backoff delays
# - Should eventually reconnect
```

**Validation Criteria:**
- ✅ Disconnection is detected within 30 seconds
- ✅ Reconnection attempts use exponential backoff
- ✅ Recording resumes after reconnection
- ✅ No data corruption during interruption

### 3.3 Storage Cleanup Testing
**Objective:** Verify automated storage management

```bash
# Test 17: Create old test segments (simulate)
# Note: This test should be run in a test environment

# Check current retention policy
grep -r "retention_days" config/

# Monitor cleanup process
tail -f logs/recording_service.log | grep -E "(Cleanup|Delete|removed)"

# Test 18: Verify cleanup removes old files
# (This test requires waiting for cleanup cycle or manual trigger)
```

**Validation Criteria:**
- ✅ Old segments are automatically deleted
- ✅ Database entries are properly removed
- ✅ Empty directories are cleaned up
- ✅ Storage statistics are updated

## ⚡ 4. Performance Testing

### 4.1 Resource Usage Monitoring
**Objective:** Validate system resource consumption

```bash
# Test 19: CPU and memory monitoring
top -p $(pgrep -f main_recording_service) -n 1

# Test 20: Disk I/O monitoring
iostat -x 1 5

# Test 21: Network usage
netstat -i

# Test 22: API response time testing
for i in {1..10}; do
  time curl -s http://localhost:8002/health > /dev/null
done
```

**Performance Benchmarks:**
- ✅ CPU usage < 20% per camera
- ✅ Memory usage < 200MB per camera
- ✅ Disk write rate ~2MB/s per camera
- ✅ API response time < 200ms

### 4.2 Concurrent Access Testing
**Objective:** Test API under load

```bash
# Test 23: Concurrent API requests
for i in {1..20}; do
  curl -s http://localhost:8002/health &
done
wait

# Test 24: Database locking test
for i in {1..5}; do
  curl -s http://localhost:8002/recordings/3/segments &
done
wait
```

**Validation Criteria:**
- ✅ No request timeouts or errors
- ✅ Database remains responsive
- ✅ No SQL locking issues
- ✅ Response times remain stable

## 🔒 5. Security Testing

### 5.1 API Security Validation
**Objective:** Ensure API security best practices

```bash
# Test 25: Check for sensitive data exposure
curl -s http://localhost:8002/health | grep -E "(password|secret|key)"

# Test 26: Validate error handling
curl -s http://localhost:8002/recordings/999/segments
curl -s http://localhost:8002/invalid-endpoint

# Test 27: Input validation testing
curl -s "http://localhost:8002/recordings/3/segments?start_time=invalid-date"
```

**Security Criteria:**
- ✅ No sensitive information in responses
- ✅ Proper error messages without stack traces
- ✅ Input validation prevents injection
- ✅ No directory traversal vulnerabilities

### 5.2 File System Security
**Objective:** Verify file permissions and access controls

```bash
# Test 28: Check file permissions
find recordings/ -type f -exec ls -la {} + | head -10
find recordings/ -type d -exec ls -ld {} + | head -5

# Test 29: Database file security
ls -la recordings/camera_3/index.db
```

**Security Criteria:**
- ✅ Recording files have appropriate permissions
- ✅ Database files are not world-readable
- ✅ No temporary files with sensitive data
- ✅ Log files don't contain credentials

## 📊 6. Data Validation Testing

### 6.1 Video File Integrity
**Objective:** Verify recorded video files are valid

```bash
# Test 30: Video file validation using FFmpeg/OpenCV
python << EOF
import cv2
import os

# Test a recent video file
video_files = []
for root, dirs, files in os.walk('recordings/camera_3'):
    for file in files:
        if file.endswith('.avi'):
            video_files.append(os.path.join(root, file))

if video_files:
    latest_video = max(video_files, key=os.path.getctime)
    print(f"Testing video: {latest_video}")
    
    cap = cv2.VideoCapture(latest_video)
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        if frame_count >= 100:  # Sample first 100 frames
            break
    
    cap.release()
    print(f"Video is valid. Tested {frame_count} frames.")
else:
    print("No video files found")
EOF
```

**Validation Criteria:**
- ✅ Video files can be opened by standard players
- ✅ Frame data is not corrupted
- ✅ Audio/video sync is maintained
- ✅ File headers are properly formatted

### 6.2 Metadata Accuracy
**Objective:** Ensure database metadata matches actual files

```bash
# Test 31: Cross-validate file sizes
python << EOF
import sqlite3
import os
from pathlib import Path

db_path = 'recordings/camera_3/index.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT filename, file_size, start_time FROM segments LIMIT 10")
for filename, db_size, start_time in cursor.fetchall():
    # Construct file path from start_time
    from datetime import datetime
    dt = datetime.fromisoformat(start_time)
    date_path = dt.strftime("%Y/%m/%d/%H")
    file_path = f"recordings/camera_3/{date_path}/{filename}"
    
    if os.path.exists(file_path):
        actual_size = os.path.getsize(file_path)
        if actual_size == db_size:
            print(f"✅ {filename}: Size matches ({actual_size} bytes)")
        else:
            print(f"❌ {filename}: Size mismatch (DB: {db_size}, Actual: {actual_size})")
    else:
        print(f"❌ {filename}: File not found")

conn.close()
EOF
```

**Validation Criteria:**
- ✅ Database file sizes match actual files
- ✅ Timestamps are accurate
- ✅ Duration calculations are correct
- ✅ No missing or orphaned entries

## 🎯 7. End-to-End Testing

### 7.1 Complete System Workflow
**Objective:** Test entire recording pipeline

```bash
# Test 32: End-to-end recording workflow
echo "Starting E2E test at $(date)"

# 1. Check initial state
INITIAL_COUNT=$(curl -s http://localhost:8002/recordings/status/3 | jq '.total_segments')
echo "Initial segment count: $INITIAL_COUNT"

# 2. Wait for new segment creation (up to 15 minutes)
echo "Waiting for new segment creation..."
START_TIME=$(date +%s)
while true; do
    CURRENT_COUNT=$(curl -s http://localhost:8002/recordings/status/3 | jq '.total_segments')
    if [ "$CURRENT_COUNT" -gt "$INITIAL_COUNT" ]; then
        echo "New segment created! Count: $CURRENT_COUNT"
        break
    fi
    
    ELAPSED=$(($(date +%s) - START_TIME))
    if [ $ELAPSED -gt 900 ]; then  # 15 minutes timeout
        echo "Timeout waiting for new segment"
        exit 1
    fi
    
    sleep 30
done

# 3. Validate the new segment
NEW_SEGMENTS=$(curl -s http://localhost:8002/recordings/3/segments?limit=1)
echo "Latest segment: $NEW_SEGMENTS"

echo "E2E test completed successfully at $(date)"
```

**E2E Validation Criteria:**
- ✅ New segment is created within expected timeframe
- ✅ Segment appears in both file system and database
- ✅ API returns updated statistics
- ✅ Complete workflow operates without manual intervention

## 📋 Test Report Template

### Test Execution Checklist

```markdown
## 24/7 Recording System Test Report

**Test Date:** _______________
**Tester:** _______________
**System Version:** _______________

### Functional Testing
- [ ] Recording service health check
- [ ] Continuous recording validation
- [ ] Database integrity verification

### Integration Testing  
- [ ] API endpoint testing
- [ ] CORS and headers validation

### Reliability Testing
- [ ] Service restart testing
- [ ] Network disconnection handling
- [ ] Storage cleanup verification

### Performance Testing
- [ ] Resource usage monitoring
- [ ] Concurrent access testing

### Security Testing
- [ ] API security validation
- [ ] File system security check

### Data Validation
- [ ] Video file integrity
- [ ] Metadata accuracy

### End-to-End Testing
- [ ] Complete system workflow

### Issues Found
1. _______________
2. _______________
3. _______________

### Overall Status: PASS / FAIL / PARTIAL

### Recommendations
1. _______________
2. _______________
3. _______________
```

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

**Issue:** API service not responding
```bash
# Check if service is running
ps aux | grep recording_api_service

# Check port binding
ss -tulpn | grep 8002

# Restart API service
python recording_api_service.py
```

**Issue:** Recording service stopped
```bash
# Check logs for errors
tail -50 logs/recording_service.log

# Check disk space
df -h

# Restart recording service
nohup python main_recording_service.py > logs/recording_service.log 2>&1 &
```

**Issue:** Database corruption
```bash
# Check database integrity
sqlite3 recordings/camera_3/index.db "PRAGMA integrity_check;"

# Backup and recreate if needed
cp recordings/camera_3/index.db recordings/camera_3/index.db.backup
# Restart recording service to recreate database
```

---

**Note:** This testing guide should be executed in a test environment first, then gradually applied to production systems. Always backup critical data before running destructive tests.