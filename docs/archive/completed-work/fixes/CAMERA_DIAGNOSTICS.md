# Camera Connection Diagnostics Tools

This document describes the enhanced camera diagnostic tools available in your license plate recognition system.

## Overview

The diagnostic tools help troubleshoot camera connection issues, test RTSP streams, and optimize camera configurations. These tools were created to address the connection failures seen in the system logs.

## Available Tools

### 1. 📊 `diagnose_camera.py` - Comprehensive Diagnostics

**Purpose**: Complete diagnostic suite for troubleshooting camera connections

**Usage:**
```bash
# Basic diagnostics
.venv/bin/python3 diagnose_camera.py <IP_ADDRESS>

# Full diagnostics with credentials and brand
.venv/bin/python3 diagnose_camera.py 10.0.0.181 -u admin -P password -b reolink

# Save results to file
.venv/bin/python3 diagnose_camera.py 10.0.0.181 -u admin -P password -o results.json
```

**Features:**
- ✅ Network connectivity testing (ping, socket connection)
- ✅ Port scanning for common camera ports
- ✅ RTSP path discovery and testing
- ✅ Network quality assessment (packet loss, jitter)
- ✅ Brand-specific optimizations
- ✅ Detailed recommendations for fixes

**Example Output:**
```
============================================================
Camera Connection Diagnostics
============================================================
Target: 10.0.0.181:554
Brand: reolink
Type: RTSP

✅ Ping successful (avg: 2.1ms)
✅ Port 554 is open (connected in 1.4ms)
✅ Found 5 working RTSP path(s):
   - /h264Preview_01_main (3840x2160)
   - /Preview_01_main (3840x2160)
   - /h264Preview_01_sub (640x360)
```

### 2. 🔧 `rtsp_builder.py` - RTSP URL Builder and Validator

**Purpose**: Interactive tool for building and testing RTSP URLs

**Usage:**
```bash
# Interactive mode
.venv/bin/python3 rtsp_builder.py interactive

# Build URL with parameters
.venv/bin/python3 rtsp_builder.py build 10.0.0.181 -u admin -P password -b reolink

# Test all paths for a brand
.venv/bin/python3 rtsp_builder.py test 10.0.0.181 -u admin -P password -b reolink

# Show brand information
.venv/bin/python3 rtsp_builder.py info -b reolink
```

**Supported Brands:**
- **Reolink**: `/h264Preview_01_main`, `/Preview_01_main`, etc.
- **Hikvision**: `/Streaming/Channels/101`, `/h264/ch1/main/av_stream`
- **Dahua**: `/cam/realmonitor?channel=1&subtype=0`
- **Axis**: `/axis-media/media.amp`
- **Foscam**: `/videoMain`, `/videoSub`
- **Generic**: `/stream`, `/live`, `/video`

### 3. 🔄 `fix_camera_config.py` - Configuration Fixer

**Purpose**: Update camera configurations based on diagnostic results

**Usage:**
```bash
# List all cameras
.venv/bin/python3 fix_camera_config.py list

# Fix camera stream path
.venv/bin/python3 fix_camera_config.py fix camera_946701d3 /h264Preview_01_main
```

### 4. 🌐 API Endpoint - Real-time Diagnostics

**Purpose**: Web API for running diagnostics from the frontend

**Endpoint:** `GET /api/cameras/{camera_id}/diagnostics`

**Example:**
```bash
curl http://localhost:8001/api/cameras/camera_946701d3/diagnostics
```

**Response includes:**
- Complete diagnostic results
- Current stream status
- Quick fix recommendations
- Suggested configuration changes

## Troubleshooting Workflow

### Step 1: Identify the Problem
Check the recording service logs for connection errors:
```bash
grep -i "error\|failed" recording_service/logs/recording_service.log
```

### Step 2: Run Comprehensive Diagnostics
```bash
.venv/bin/python3 diagnose_camera.py <CAMERA_IP> -u <USERNAME> -P <PASSWORD> -b <BRAND>
```

### Step 3: Analyze Results
The diagnostic tool will provide:
- ✅ Working RTSP paths
- ❌ Failed connection attempts  
- 🔧 Specific recommendations
- 📊 Network quality metrics

### Step 4: Apply Fixes
Based on diagnostics, apply fixes:

**For Stream Path Issues:**
```bash
.venv/bin/python3 fix_camera_config.py fix <CAMERA_ID> <NEW_PATH>
```

**For Port Issues:**
Update camera configuration through the web UI or API

**For Network Issues:**
- Check physical connections
- Verify firewall rules
- Test with different network settings

### Step 5: Verify Fix
- Check that recording service connects successfully
- Monitor logs for continued errors
- Test camera functionality in web UI

## Common Issues and Solutions

### Issue: "Failed to read test frame"
**Cause:** Wrong RTSP path or authentication failure  
**Solution:** Run diagnostics to find working paths
```bash
.venv/bin/python3 diagnose_camera.py <IP> -u <USER> -P <PASS> -b <BRAND>
```

### Issue: "Connection timeout"
**Cause:** Network connectivity or firewall blocking  
**Solution:** Check network connectivity and port access
```bash
# Test network connectivity
ping <CAMERA_IP>
nc -zv <CAMERA_IP> 554
```

### Issue: "Authentication failed"
**Cause:** Incorrect credentials  
**Solution:** Verify username/password, try defaults
- Common defaults: admin/admin, admin/password, admin/blank

### Issue: "Port closed or filtered"
**Cause:** RTSP port not accessible  
**Solution:** Check camera settings, enable RTSP, check firewall

## Brand-Specific Notes

### Reolink Cameras
- **Best paths**: `/h264Preview_01_main` (4K), `/h264Preview_01_sub` (lower res)
- **Default port**: 554
- **Authentication**: Usually required
- **Note**: Some models use `/Preview_01_main` instead

### Hikvision Cameras  
- **Best paths**: `/Streaming/Channels/101` (main), `/Streaming/Channels/102` (sub)
- **Default port**: 554
- **Authentication**: Usually required
- **Note**: Channel numbers may vary (1, 101, 201, etc.)

### Dahua Cameras
- **Best paths**: `/cam/realmonitor?channel=1&subtype=0` (main)
- **Default port**: 554  
- **Authentication**: Usually required
- **Note**: Query parameters are important

## Performance Optimization

### High-Quality Streams
- Use main stream paths (e.g., `/h264Preview_01_main`)
- Results in 4K resolution (3840x2160)
- Higher bandwidth requirements

### Low-Bandwidth Streams  
- Use sub stream paths (e.g., `/h264Preview_01_sub`)
- Lower resolution (e.g., 640x360)
- Reduced network usage

### Network Quality Requirements
- **Excellent (90-100)**: Suitable for 4K streaming
- **Good (70-89)**: Suitable for 1080p streaming  
- **Fair (50-69)**: Use sub streams only
- **Poor (<50)**: Connection issues likely

## Integration with Main System

The diagnostic tools integrate with your existing system:

1. **Database Integration**: Camera configurations are updated in SQLite database
2. **Service Synchronization**: Recording service automatically uses updated configurations
3. **Web UI Compatibility**: Diagnostics API can be called from frontend
4. **Logging Integration**: Results are logged for troubleshooting

## Example: Fixing the Reolink Camera Issue

Based on the logs showing connection failures for the Reolink camera at 10.0.0.181:

```bash
# 1. Run diagnostics
.venv/bin/python3 diagnose_camera.py 10.0.0.181 -u admin -P Mekus_1987 -b reolink

# 2. Results showed working paths:
#    - /h264Preview_01_main (3840x2160) ✅
#    - /Preview_01_main (3840x2160) ✅  
#    - /h264Preview_01_sub (640x360) ✅

# 3. Update camera configuration
.venv/bin/python3 fix_camera_config.py fix camera_946701d3 /h264Preview_01_main

# 4. Restart services to apply changes
python3 restart_services.py
```

**Result**: Camera now connects successfully with 4K video quality.

## Files Created/Modified

- ✅ `diagnose_camera.py` - Main diagnostic tool
- ✅ `rtsp_builder.py` - RTSP URL builder and validator
- ✅ `fix_camera_config.py` - Configuration update tool  
- ✅ `api/main.py` - Added `/api/cameras/{camera_id}/diagnostics` endpoint
- ✅ `CAMERA_DIAGNOSTICS.md` - This documentation

All tools are production-ready and integrate seamlessly with your existing license plate recognition system.