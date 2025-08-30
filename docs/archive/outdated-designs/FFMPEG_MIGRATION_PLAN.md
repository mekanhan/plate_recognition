# FFmpeg Migration Plan: Fix Video Playback Once and For All

## **The Problem (Root Cause Analysis)**

OpenCV VideoWriter is fundamentally incompatible with web browsers:
- Creates malformed MP4 containers 
- No proper audio/video track structure
- Browser error: `NS_ERROR_DOM_MEDIA_DEMUXER_ERR: No MP4 audio () or video () tracks`
- **NO amount of codec tweaking will fix this - it's the wrong tool**

## **The Solution: Complete FFmpeg Migration**

### **Phase 1: Validation (MANDATORY FIRST STEP)**
```bash
# Install FFmpeg
sudo apt install ffmpeg

# Create test video
ffmpeg -f lavfi -i testsrc2=duration=10:size=640x480:rate=30 \
  -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p test.mp4

# Verify in browser - drag test.mp4 into browser
# MUST play without errors before proceeding
```

### **Phase 2: Replace Recording Service**

#### A. Stop OpenCV Recording
```python
# In recording_service/services/recording_manager.py
# REMOVE all cv2.VideoWriter code
# REPLACE with FFmpegRecorder
```

#### B. Implement FFmpeg Recording
```python
from .ffmpeg_recorder import FFmpegRecorder

class CameraRecorder:
    def __init__(self, camera_id, camera_config):
        # OLD: self.current_writer = cv2.VideoWriter(...)
        # NEW: 
        self.ffmpeg_recorder = FFmpegRecorder(
            camera_id=camera_id,
            rtsp_url=camera_config['rtsp_url'],
            output_dir=Path("recordings")
        )
    
    async def start_recording(self):
        # OLD: OpenCV frame-by-frame writing
        # NEW: FFmpeg handles everything
        return await self.ffmpeg_recorder.start_recording()
```

### **Phase 3: Update Playback Service**

No changes needed! FFmpeg creates proper MP4 files that work with existing playback endpoints.

### **Phase 4: Migration Steps**

#### Day 1: Parallel Recording
1. Keep OpenCV running (backup)
2. Start FFmpeg recording in parallel
3. Compare file outputs
4. Verify FFmpeg files play in browser

#### Day 2: Switch Playback
1. Update playback service to serve FFmpeg files
2. Test timeline, seeking, calendar
3. Verify no browser errors

#### Day 3: Complete Migration
1. Stop OpenCV recording
2. Remove all cv2.VideoWriter code
3. Clean up old AVI/broken MP4 files

## **Key Benefits of FFmpeg Approach**

1. **✅ Browser Compatibility**: Creates standard H.264/MP4 files
2. **✅ No Re-encoding**: Uses `-c:v copy` to preserve camera quality  
3. **✅ Industry Standard**: Used by YouTube, Netflix, professional systems
4. **✅ Better Error Recovery**: Handles network issues gracefully
5. **✅ Lower CPU Usage**: No Python frame processing overhead
6. **✅ Proper Timestamps**: Correct seeking behavior

## **Files to Modify**

### Delete/Replace:
- `recording_service/services/recording_manager.py` (OpenCV parts)
- All `cv2.VideoWriter` references

### Add:
- `recording_service/services/ffmpeg_recorder.py` ✅ Created
- Validation scripts ✅ Created

### Update:
- `recording_service/main.py` - Use FFmpegRecorder
- Database models (if needed for new file patterns)

## **Testing Checklist**

- [ ] FFmpeg test video plays in browser
- [ ] RTSP recording works with FFmpeg
- [ ] Segmented recording creates playable files
- [ ] Timeline/calendar still work
- [ ] Video seeking works properly
- [ ] No "demuxer error" messages
- [ ] File sizes reasonable
- [ ] Recording survives network glitches

## **Success Criteria**

### Before (Current Broken State):
```
Browser Console:
❌ NS_ERROR_DOM_MEDIA_DEMUXER_ERR: No MP4 audio () or video () tracks
❌ Video playback error
❌ Failed to load video segment
```

### After (Target Success State):
```
Browser Console:
✅ Video loaded successfully! Duration: 600.00s, 1920x1080
✅ Can play: video/mp4; codecs="avc1.42E01E"
✅ Seeking works, timeline updates properly
```

## **Why This Will Work (vs. Previous Attempts)**

1. **Right Tool**: FFmpeg is designed for video processing, OpenCV is for computer vision
2. **Proven Standard**: Same approach used by all major video platforms
3. **Test-First**: Validation before implementation prevents wasted effort
4. **Complete Replacement**: Not trying to "fix" broken OpenCV output

This migration will permanently solve the video playback issues by using the correct tool for the job.