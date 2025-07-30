# Video Processing Architecture - Raw vs Compressed Data Flow

## The Core Question

**How does video flow from camera through AI to storage?**

## 🎯 Best Approach: Decode Once, Use Everywhere

```
Camera (H.264/H.265) → Network → Your PC → Decode to Raw → Everything else
      [Compressed]                         [Uncompressed]
```

### Why This Matters:

**Camera Sends Compressed Video:**
- Cameras compress video using H.264/H.265 codecs
- This reduces bandwidth (4K raw = 6 Gbps, compressed = 8-25 Mbps)
- Camera does hardware encoding efficiently

**You Decode ONCE:**
```python
# This is what happens in OpenCV
capture = cv2.VideoCapture("rtsp://camera/stream")
ret, frame = capture.read()  # ← OpenCV decodes H.264 to raw pixels here
```

## Complete Data Flow

```python
class HighQualityVideoProcessor:
    def __init__(self, camera_config):
        # Connect to camera's HIGHEST quality stream
        self.main_stream = cv2.VideoCapture(camera_config['main_stream_url'])
        
        # Configure for quality
        self.main_stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffering
        
        # Get actual resolution from camera
        self.width = int(self.main_stream.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.main_stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.main_stream.get(cv2.CAP_PROP_FPS))
        
        print(f"Camera stream: {self.width}x{self.height} @ {self.fps} FPS")
        
        # Setup high-quality recording
        self.setup_recording()
        
    def setup_recording(self):
        # Use H.264 codec for recording (same as camera uses)
        fourcc = cv2.VideoWriter_fourcc(*'h264')
        
        # Record at FULL camera resolution
        self.recorder = cv2.VideoWriter(
            'output.mp4',
            fourcc,
            self.fps,
            (self.width, self.height),
            isColor=True
        )
        
    def process_frame(self):
        # 1. Read frame from camera (OpenCV decodes H.264 → raw pixels)
        ret, raw_frame = self.main_stream.read()
        
        if not ret:
            return
            
        # Now we have RAW PIXELS (uncompressed)
        # Shape: (height, width, 3) in BGR format
        # Size: 1920×1080×3 = 6.2 MB per frame uncompressed
        
        # 2. Send SAME raw frame to AI (no quality loss)
        detections = self.ai_detector.detect(raw_frame)
        
        # 3. Record SAME raw frame (re-encoded to H.264)
        self.recorder.write(raw_frame)
        
        # 4. If detection found, save high-quality snapshot
        if detections:
            # Save full quality frame
            cv2.imwrite(f"detection_{timestamp}.png", raw_frame, 
                       [cv2.IMWRITE_PNG_COMPRESSION, 0])  # Lossless
            
            # Extract plate region at full quality
            for detection in detections:
                x1, y1, x2, y2 = detection['plate_bbox']
                plate_roi = raw_frame[y1:y2, x1:x2]
                
                # Save plate at high quality for OCR
                cv2.imwrite(f"plate_{detection['id']}.png", plate_roi)
```

## Quality Considerations

### 1. Camera Configuration
```python
# Most IP cameras have multiple streams
CAMERA_STREAMS = {
    "main_stream": {
        "url": "rtsp://admin:pass@192.168.1.100:554/Streaming/Channels/101",
        "resolution": "3840x2160",  # 4K
        "bitrate": "8192 kbps",     # High bitrate
        "fps": 30,
        "codec": "H.265"            # Better compression
    },
    "sub_stream": {
        "url": "rtsp://admin:pass@192.168.1.100:554/Streaming/Channels/102", 
        "resolution": "640x480",     # Low res
        "bitrate": "512 kbps",       # Low bitrate
        "fps": 15,
        "codec": "H.264"
    }
}

# ALWAYS use main_stream for AI processing!
```

### 2. Bandwidth Requirements
```
4K Stream (3840×2160):
- Raw: 3840 × 2160 × 3 bytes × 30 fps = 747 MB/s (6 Gbps!)
- H.265 compressed: 8-15 Mbps (0.06% of raw!)
- H.264 compressed: 15-25 Mbps

1080p Stream (1920×1080):
- Raw: 1920 × 1080 × 3 bytes × 30 fps = 187 MB/s (1.5 Gbps)
- H.264 compressed: 4-8 Mbps (0.5% of raw!)
```

### 3. Processing Pipeline Quality Settings

```python
class QualityOptimizedPipeline:
    def __init__(self):
        # For AI: Process at full resolution
        self.ai_scale = 1.0  # No downscaling
        
        # For Recording: Match camera quality
        self.recording_bitrate = 8000  # 8 Mbps
        self.recording_codec = 'h264'
        
        # For Snapshots: Lossless when possible
        self.snapshot_quality = 100  # JPEG quality
        self.use_png_for_plates = True  # PNG is lossless
        
    def process_for_ai(self, frame):
        # DO NOT resize for AI if you want best accuracy
        # Modern AI models handle full resolution well
        return frame  # Full quality!
        
    def save_detection_evidence(self, frame, detection):
        # Save full frame as high-quality JPEG
        cv2.imwrite(
            f"evidence/frame_{detection.id}.jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 95]  # 95% quality
        )
        
        # Save plate region as PNG (lossless)
        x1, y1, x2, y2 = detection.plate_bbox
        plate = frame[y1:y2, x1:x2]
        
        # Upscale small plates for better OCR
        if plate.shape[1] < 200:  # If width < 200px
            scale = 200 / plate.shape[1]
            width = int(plate.shape[1] * scale)
            height = int(plate.shape[0] * scale)
            plate = cv2.resize(plate, (width, height), 
                             interpolation=cv2.INTER_CUBIC)
        
        cv2.imwrite(f"evidence/plate_{detection.id}.png", plate)
```

## The Complete Flow Visualized

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Camera    │     │  Network    │     │   Your PC    │
│             │────▶│             │────▶│              │
│ H.265 @8Mbps│     │ RTSP Stream │     │ OpenCV Decode│
└─────────────┘     └─────────────┘     └──────┬───────┘
                                                │
                                         Raw Frame (6MB)
                    ┌───────────────────────────┼───────────────────────────┐
                    ▼                           ▼                           ▼
            ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
            │ AI Processing│           │  Recording   │           │  Snapshots   │
            │              │           │              │           │              │
            │ YOLO on raw  │           │ Encode→H.264 │           │ PNG/JPEG     │
            │ Full quality │           │ High bitrate │           │ Full quality │
            └──────────────┘           └──────────────┘           └──────────────┘
```

## Best Practices for Quality

### 1. Camera Setup
```yaml
# Configure camera for maximum quality
camera_settings:
  main_stream:
    resolution: "highest_available"  # 4K if possible
    bitrate: "maximum"              # 8-20 Mbps
    i_frame_interval: 30            # Every 1 second
    encoding: "H.265"               # Better than H.264
    
  # DON'T use sub-stream for AI!
```

### 2. Network Considerations
```python
# Ensure stable connection
def setup_camera_connection(url):
    cap = cv2.VideoCapture(url)
    
    # Force TCP for reliability (not UDP)
    cap.open(url + "?tcp")
    
    # Set buffer size small to get latest frames
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Don't limit FPS
    # Let camera send at its configured rate
    
    return cap
```

### 3. Storage Strategy
```python
# Different quality for different purposes
STORAGE_STRATEGY = {
    "continuous_recording": {
        "codec": "h264",      # Good compression
        "bitrate": "4000k",   # 4 Mbps
        "format": "mp4"
    },
    "detection_clips": {
        "codec": "h264",      
        "bitrate": "8000k",   # Higher quality for evidence
        "format": "mp4"
    },
    "plate_images": {
        "format": "png",      # Lossless
        "preprocessing": "enhance_contrast"
    }
}
```

## Summary

**What happens to video quality:**

1. **Camera → Network**: Compressed (H.264/H.265) - Some quality loss but minimal
2. **Network → Your PC**: No additional loss (just transport)
3. **OpenCV Decode**: Get raw pixels - Original captured quality
4. **AI Processing**: Uses raw pixels - Best possible quality
5. **Recording**: Re-encode to H.264 - Small quality loss (configure bitrate!)
6. **Snapshots**: Can be lossless (PNG) or high-quality JPEG

**Key Point**: You decode ONCE when reading from camera, then that same raw frame goes everywhere - AI, recording, snapshots. No quality is lost between these steps!

The only quality loss happens at:
- Camera's initial encoding (unavoidable)
- Your re-encoding for storage (controllable via bitrate)

---

*AI Agent Note: Always use the camera's highest quality stream for AI processing. The bandwidth cost is worth the accuracy improvement.*