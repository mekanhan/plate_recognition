# Camera Diagnostic Issues and Fixes

This document explains the camera connection issues you encountered and how they were resolved.

## Issue Summary

**Error Messages:**
```
[rtsp @ 0x2a0d7440] method DESCRIBE failed: 404 Stream Not Found
[rtsp @ 0x2a0d7440] method DESCRIBE failed: 401 Unauthorized
```

**Root Cause:** Missing or incorrect RTSP stream path configuration in test scripts.

## Problem Analysis

### 1. **Missing Stream Path**
Your test scripts were not specifying the correct RTSP stream path:

**Before (Incorrect):**
```python
config = CameraConfig(
    camera_id="1",
    name="Test Camera", 
    ip_address="10.0.0.181",
    username="admin",
    password="Mekus_1987",
    # stream_path missing! This caused 404 errors
)
```

### 2. **Generic vs Brand-Specific Paths**
Different camera brands use different RTSP path formats:

- **Generic paths** (often fail): `/stream`, `/live`, `/video`
- **Reolink-specific paths** (work): `/h264Preview_01_main`, `/Preview_01_main`

## Solution Applied

### 1. **Comprehensive Diagnostics**
Used the enhanced diagnostic tool to find working paths:

```bash
.venv/bin/python3 diagnose_camera.py 10.0.0.181 -u admin -P Mekus_1987 -b reolink
```

**Results:**
```
✅ Found 5 working RTSP path(s):
   - /h264Preview_01_main (3840x2160) ← RECOMMENDED
   - /Preview_01_main (3840x2160)
   - /h264Preview_01_sub (640x360)
   - /Preview_01_sub (640x360)
   - / (3840x2160)
```

### 2. **Fixed Test Scripts**
Updated test configurations with correct stream path:

**After (Correct):**
```python
config = CameraConfig(
    camera_id="1",
    name="Test Camera",
    ip_address="10.0.0.181", 
    username="admin",
    password="Mekus_1987",
    port=554,
    stream_path="/h264Preview_01_main",  # ← ADDED THIS
    protocol="rtsp"
)
```

### 3. **Database Configuration**
Verified and updated camera configuration in database:

```bash
.venv/bin/python3 fix_camera_config.py fix camera_946701d3 /h264Preview_01_main
```

**Result:**
```
📷 Updating camera: Reolink Main Entrance
   Current path: /
   New path: /h264Preview_01_main
✅ Successfully updated stream path
```

### 4. **Created Working Test Script**
Created `test_camera_fixed.py` with correct configuration that successfully connects:

```
✅ Camera stream opened successfully
📸 Reading test frames...
   Frame 1: 3840x2160 ✅
   Frame 2: 3840x2160 ✅
   Frame 3: 3840x2160 ✅
   Frame 4: 3840x2160 ✅
   Frame 5: 3840x2160 ✅
📊 Stream Properties:
   Resolution: 3840x2160
   FPS: 25.0
✅ Camera test PASSED
```

## Files Updated

### **Fixed Files:**
- `scripts/test_camera.py` - Added correct stream path
- `camera_configs.json` - Created with working configuration
- `test_camera_fixed.py` - New working test script (NEW)

### **Database:**
- Camera `camera_946701d3` updated with `/h264Preview_01_main` path
- Test result marked as 'success'

## Key Learnings

### 1. **Always Specify Stream Path**
Never leave `stream_path` empty for RTSP connections. Use brand-specific paths.

### 2. **Use Diagnostic Tools First**
Before troubleshooting connection issues:
```bash
# Run comprehensive diagnostics
.venv/bin/python3 diagnose_camera.py <IP> -u <USER> -P <PASS> -b <BRAND>

# Or use RTSP builder for interactive testing
.venv/bin/python3 rtsp_builder.py test <IP> -u <USER> -P <PASS> -b <BRAND>
```

### 3. **Brand-Specific Optimization**
Different camera brands have different URL patterns:

**Reolink:**
- Main: `/h264Preview_01_main` (4K quality)
- Sub: `/h264Preview_01_sub` (low bandwidth)

**Hikvision:**
- Main: `/Streaming/Channels/101`
- Sub: `/Streaming/Channels/102`

**Dahua:**
- Main: `/cam/realmonitor?channel=1&subtype=0`
- Sub: `/cam/realmonitor?channel=1&subtype=1`

### 4. **Error Message Interpretation**
- `404 Stream Not Found` = Wrong stream path
- `401 Unauthorized` = Authentication issue
- `Timeout` = Network/connectivity problem

## Testing Workflow

### **For New Cameras:**
1. **Run diagnostics** to find working paths
2. **Update configuration** with correct path
3. **Test connection** with simple script
4. **Update database** if needed

### **For Existing Cameras:**
1. **Check current configuration**: `fix_camera_config.py list`
2. **Test current path**: Use diagnostic tools
3. **Update if needed**: `fix_camera_config.py fix <ID> <NEW_PATH>`

## Scripts Reference

### **Diagnostic Tools:**
```bash
# Comprehensive diagnostics
.venv/bin/python3 diagnose_camera.py <IP> -u <USER> -P <PASS> -b <BRAND>

# RTSP path testing
.venv/bin/python3 rtsp_builder.py test <IP> -u <USER> -P <PASS> -b <BRAND>

# Simple connection test
.venv/bin/python3 test_camera_fixed.py
```

### **Configuration Management:**
```bash  
# List cameras
.venv/bin/python3 fix_camera_config.py list

# Update camera path
.venv/bin/python3 fix_camera_config.py fix <CAMERA_ID> <NEW_PATH>
```

## Status: RESOLVED ✅

- ✅ **Camera connection working** with 4K resolution (3840x2160)
- ✅ **Database updated** with correct stream path
- ✅ **Test scripts fixed** with proper configuration
- ✅ **Diagnostic tools** available for future troubleshooting

The camera is now properly configured and should work correctly with all services in your license plate recognition system.