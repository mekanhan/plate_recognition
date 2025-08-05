# Video Recording Validation Steps

## **CRITICAL: Complete This Validation Before Any Implementation**

### Step 1: Install FFmpeg
```bash
sudo apt update && sudo apt install -y ffmpeg
```

### Step 2: Test Basic FFmpeg Recording
```bash
# Create a 10-second test video (no camera needed)
ffmpeg -f lavfi -i testsrc2=duration=10:size=640x480:rate=30 \
  -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
  test_basic.mp4

# Verify file was created
ls -la test_basic.mp4
file test_basic.mp4
```

### Step 3: Validate with ffprobe
```bash
# Check video properties
ffprobe -v error -show_format -show_streams test_basic.mp4

# Should show:
# - format_name=mov,mp4,m4a,3gp,3g2,mj2
# - codec_name=h264
# - pix_fmt=yuv420p
```

### Step 4: Test Browser Playback
```bash
# Start simple HTTP server
python3 -m http.server 8000

# Open browser to: http://localhost:8000/test_basic.mp4
# Video MUST play without errors
```

### Step 5: Test RTSP Recording (With Real Camera)
```bash
# Record 30 seconds from actual camera
timeout 30 ffmpeg -rtsp_transport tcp \
  -i rtsp://admin:password@camera/stream \
  -c:v copy -c:a aac \
  test_camera.mp4

# Verify browser playback again
```

### Step 6: Test Segmented Recording
```bash
# Test 10-minute segments (like production)
ffmpeg -f lavfi -i testsrc2=duration=30:size=640x480:rate=30 \
  -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
  -f segment -segment_time 10 -segment_format mp4 \
  -reset_timestamps 1 \
  "test_segment_%03d.mp4"

# Should create: test_segment_000.mp4, test_segment_001.mp4, test_segment_002.mp4
# Each should play in browser
```

## **Validation Checklist**

- [ ] FFmpeg installed and working
- [ ] Basic test video created successfully
- [ ] ffprobe shows correct format (H.264, yuv420p)
- [ ] Test video plays in browser without errors
- [ ] RTSP recording works with real camera
- [ ] Browser plays RTSP-recorded video
- [ ] Segmented recording creates multiple files
- [ ] All segments play in browser
- [ ] No "No MP4 audio/video tracks" errors

## **Only After 100% Validation Success:**

1. Replace OpenCV recording with FFmpeg recording
2. Update recording service to use FFmpegRecorder class
3. Test with actual cameras
4. Remove all OpenCV VideoWriter code

## **Expected Browser Test Results**

### ✅ SUCCESS (What You Should See):
```
Video loaded successfully!
Duration: 10.00s, 640x480
✅ Can play: video/mp4; codecs="avc1.42E01E"
```

### ❌ FAILURE (What We're Fixing):
```
Video error: NS_ERROR_DOM_MEDIA_DEMUXER_ERR
No MP4 audio () or video () tracks
```

## **Critical Notes**

1. **DO NOT** implement recording service until validation passes
2. **DO NOT** try to "fix" OpenCV - it cannot create browser-compatible files
3. **EVERY** video file must be tested in browser before considering it successful
4. If ANY validation step fails, debug that step before proceeding

This validation process will prove definitively whether FFmpeg can solve the browser compatibility issue that OpenCV cannot.