# Troubleshooting & FAQ

## Overview
Common issues, solutions, and frequently asked questions about the LPR system.

## 🚨 Critical Understanding

### Why No Browser Video Streaming?

**The Problem:**
```
RTSP (Camera Protocol) ←→ HTTP (Browser Protocol)
       Oil                    Water
   (Won't mix without major effort)
```

**The Solution:**
- Process video locally (where cameras are)
- Display data in browser (detections, analytics)
- Use proper tools for live video (VLC, native apps)

## Common Issues & Solutions

### 1. Camera Connection Issues

#### Problem: "Failed to connect to camera"
```python
# Error: [Errno 113] No route to host
# Or: [WinError 10060] Connection timed out
```

**Solutions:**
```bash
# 1. Check network connectivity
ping 10.0.0.181

# 2. Verify RTSP port is open
nmap -p 554 10.0.0.181

# 3. Test with VLC first
vlc rtsp://admin:password@10.0.0.181:554/stream

# 4. Check firewall rules
sudo ufw status
```

**Common Causes:**
- Wrong IP address or port
- Camera on different network/VLAN
- Firewall blocking connection
- Wrong credentials
- Camera offline

#### Problem: "Stream URL not found"
```python
# Error: Server returned 404 Not Found
```

**Solutions:**
```python
# Common stream paths by manufacturer
STREAM_PATHS = {
    "hikvision": [
        "/Streaming/Channels/101",  # Main stream
        "/Streaming/Channels/102",  # Sub stream
    ],
    "dahua": [
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
    ],
    "axis": [
        "/axis-cgi/mjpg/video.cgi",
        "/mjpg/video.mjpg",
    ],
    "generic": [
        "/stream",
        "/video",
        "/live",
        "/h264",
    ]
}

# Test each path
for path in STREAM_PATHS[camera_type]:
    url = f"rtsp://{username}:{password}@{ip}:554{path}"
    if test_connection(url):
        print(f"Working path: {path}")
        break
```

### 2. AI Processing Issues

#### Problem: "CUDA out of memory"
```python
# torch.cuda.OutOfMemoryError: CUDA out of memory
```

**Solutions:**
```python
# 1. Reduce batch size
detector = YOLO('yolov8m.pt')
detector.predict(frame, batch=1)  # Process one at a time

# 2. Use smaller model
models = {
    'nano': 'yolov8n.pt',    # 3.2M params, fastest
    'small': 'yolov8s.pt',   # 11.2M params
    'medium': 'yolov8m.pt',  # 25.9M params
    'large': 'yolov8l.pt',   # 43.7M params
}

# 3. Clear GPU cache periodically
import torch
torch.cuda.empty_cache()

# 4. Monitor GPU usage
nvidia-smi -l 1  # Watch every second
```

#### Problem: "Poor OCR accuracy"
```python
# Detected: "AB0 I23" instead of "ABC 123"
```

**Solutions:**
```python
# 1. Preprocess image better
def enhance_plate_image(plate_img):
    # Resize if too small
    if plate_img.shape[1] < 200:
        scale = 200 / plate_img.shape[1]
        width = int(plate_img.shape[1] * scale)
        height = int(plate_img.shape[0] * scale)
        plate_img = cv2.resize(plate_img, (width, height), 
                              interpolation=cv2.INTER_CUBIC)
    
    # Convert to grayscale
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(enhanced)
    
    # Threshold
    _, binary = cv2.threshold(denoised, 0, 255, 
                             cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

# 2. Use multiple OCR attempts
def robust_ocr(plate_img):
    results = []
    
    # Try original
    results.append(ocr_reader.readtext(plate_img))
    
    # Try enhanced
    enhanced = enhance_plate_image(plate_img)
    results.append(ocr_reader.readtext(enhanced))
    
    # Try inverted
    inverted = cv2.bitwise_not(enhanced)
    results.append(ocr_reader.readtext(inverted))
    
    # Vote on best result
    return get_most_confident_result(results)
```

### 3. Performance Issues

#### Problem: "System running slowly"
```bash
# Symptoms: Low FPS, high CPU, laggy dashboard
```

**Solutions:**
```python
# 1. Profile your code
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your processing code here
process_frame(frame)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 time consumers

# 2. Optimize frame processing
class OptimizedProcessor:
    def __init__(self):
        self.frame_skip = 3  # Process every 3rd frame
        self.frame_count = 0
        
    def should_process(self):
        self.frame_count += 1
        return self.frame_count % self.frame_skip == 0
        
    def process_cameras(self):
        for camera in cameras:
            frame = camera.get_frame()
            
            if self.should_process():
                # Full AI processing
                detections = self.detect_plates(frame)
            else:
                # Just record video
                self.video_recorder.add_frame(frame)

# 3. Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### 4. Storage Issues

#### Problem: "Disk space running out"
```bash
# df -h shows 95% full
```

**Solutions:**
```python
# 1. Implement retention policy
class StorageManager:
    def __init__(self, max_days=30, max_size_gb=500):
        self.max_days = max_days
        self.max_size_gb = max_size_gb
        
    async def cleanup_old_files(self):
        """Remove files older than max_days"""
        cutoff = datetime.now() - timedelta(days=self.max_days)
        
        # Clean detection images
        for file in Path("detections").rglob("*.jpg"):
            if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                file.unlink()
                
        # Clean video recordings
        async with db.session() as session:
            old_recordings = await session.query(VideoRecording).filter(
                VideoRecording.created_at < cutoff
            ).all()
            
            for recording in old_recordings:
                Path(recording.file_path).unlink(missing_ok=True)
                await session.delete(recording)
                
            await session.commit()
    
    async def check_disk_usage(self):
        """Alert if disk usage too high"""
        usage = shutil.disk_usage("/")
        used_percent = (usage.used / usage.total) * 100
        
        if used_percent > 90:
            await send_alert("Disk space critical", f"Usage: {used_percent:.1f}%")
        elif used_percent > 80:
            await send_alert("Disk space warning", f"Usage: {used_percent:.1f}%")

# 2. Compress old recordings
def compress_old_videos():
    for video in Path("recordings").glob("*.mp4"):
        age_days = (time.time() - video.stat().st_mtime) / 86400
        
        if age_days > 7:  # Compress week-old videos
            compressed = video.with_suffix(".compressed.mp4")
            cmd = [
                "ffmpeg", "-i", str(video),
                "-c:v", "libx265",  # Better compression
                "-crf", "28",       # Higher = smaller file
                "-preset", "medium",
                str(compressed)
            ]
            subprocess.run(cmd)
            
            # Replace if successful
            if compressed.exists():
                video.unlink()
                compressed.rename(video)
```

### 5. Database Issues

#### Problem: "Database connection pool exhausted"
```python
# sqlalchemy.exc.TimeoutError: QueuePool limit exceeded
```

**Solutions:**
```python
# 1. Increase pool size
engine = create_engine(
    DATABASE_URL,
    pool_size=50,        # Increase from default 5
    max_overflow=100,    # Increase from default 10
    pool_timeout=30,     # Wait longer for connection
    pool_recycle=3600    # Recycle connections hourly
)

# 2. Use connection context manager
class DatabaseService:
    @contextmanager
    async def get_db(self):
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

# 3. Monitor connections
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change
FROM pg_stat_activity
WHERE datname = 'lpr_db';
```

## Frequently Asked Questions

### General Questions

**Q: Why can't I see live video in my browser?**

A: Browsers don't natively support RTSP protocol that IP cameras use. Converting RTSP to browser-compatible formats in real-time is resource-intensive and introduces delays. Use VLC or our native app for live viewing.

**Q: Can I use this with my existing cameras?**

A: Yes, if your cameras support:
- RTSP streaming
- H.264 or H.265 video codec
- Network accessibility
- Known credentials

**Q: How many cameras can one server handle?**

A: Depends on:
- Server specs (CPU, GPU, RAM)
- Camera resolution
- Processing frequency
- AI model complexity

Rough estimates:
- Basic server (4 core, 8GB RAM, GTX 1060): 4-6 cameras
- Good server (8 core, 16GB RAM, RTX 3060): 10-15 cameras
- Powerful server (16 core, 32GB RAM, RTX 4090): 20-30 cameras

### Technical Questions

**Q: How do I find my camera's RTSP URL?**

A: Methods:
1. **Camera manual/website**
2. **ONVIF Device Manager** (Windows tool)
3. **Common patterns**:
   ```
   rtsp://[username]:[password]@[ip]:[port]/[path]
   
   Examples:
   rtsp://admin:12345@192.168.1.100:554/stream
   rtsp://admin:12345@192.168.1.100:554/Streaming/Channels/101
   ```
4. **Python ONVIF discovery**:
   ```python
   from onvif import ONVIFCamera
   
   cam = ONVIFCamera('192.168.1.100', 80, 'admin', 'password')
   media = cam.create_media_service()
   profiles = media.GetProfiles()
   
   for profile in profiles:
       stream = media.GetStreamUri({
           'StreamSetup': {
               'Stream': 'RTP-Unicast',
               'Transport': {'Protocol': 'RTSP'}
           },
           'ProfileToken': profile.token
       })
       print(f"Stream URL: {stream.Uri}")
   ```

**Q: Can I process 4K cameras?**

A: Yes, but consider:
- Higher GPU requirements
- More network bandwidth
- Larger storage needs
- Possible frame rate reduction

Optimization:
```python
# Use camera's sub-stream for detection
main_stream = "rtsp://camera/stream1"  # 4K for recording
sub_stream = "rtsp://camera/stream2"   # 720p for AI

# Process sub-stream, record main stream
ai_capture = cv2.VideoCapture(sub_stream)
record_capture = cv2.VideoCapture(main_stream)
```

**Q: How do I add custom AI models?**

A: Follow the pattern:
```python
# 1. Create model class
class CustomModel(AIModel):
    async def load_model(self):
        # Load your model
        self.model = load_your_model()
        
    async def process_frame(self, frame):
        # Process and return detections
        results = self.model.predict(frame)
        return format_results(results)

# 2. Register in config
models:
  custom_model:
    enabled: true
    class: "CustomModel"
    confidence_threshold: 0.7

# 3. Add to pipeline
model_manager.register_model(CustomModel())
```

### Deployment Questions

**Q: Can I run this on a Raspberry Pi?**

A: Limited support:
- Pi 4 (8GB): 1-2 cameras at low resolution
- Use lighter models (YOLOv8n)
- Consider frame skipping
- Better to use as edge device, not main server

**Q: How do I setup HTTPS?**

A: Use Let's Encrypt:
```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx.conf
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

**Q: Can I run this in the cloud?**

A: Not recommended because:
- Cameras need local network access
- Bandwidth costs would be huge
- Latency affects real-time processing

Better approach:
- Edge devices at camera locations
- Cloud for dashboard/storage only

## Debug Commands Cheatsheet

```bash
# Check system resources
htop
nvidia-smi
df -h
free -h

# Docker debugging
docker-compose logs -f app
docker-compose exec app bash
docker stats

# Test camera connection
ffplay rtsp://camera_url
curl -v http://camera_ip

# Database queries
docker-compose exec postgres psql -U lpr_user -d lpr_db
\dt  # List tables
SELECT COUNT(*) FROM detections;

# Network debugging
netstat -tuln | grep LISTEN
tcpdump -i any port 554
iptables -L -n

# Python debugging
python -m pdb script.py
import ipdb; ipdb.set_trace()

# Performance monitoring
iostat -x 1
sar -u 1
```

## Getting Help

### Before Asking for Help

1. **Check logs**: `docker-compose logs app`
2. **Verify basics**: Network, credentials, camera online
3. **Test with VLC**: Ensure camera stream works
4. **Read error messages**: They usually tell you what's wrong
5. **Search this FAQ**: Your issue might be covered

### Information to Provide

When asking for help, include:
```markdown
**Environment:**
- OS: Ubuntu 20.04
- Python: 3.9.5
- GPU: RTX 3060 (12GB)
- Docker: 20.10.12

**Issue:**
Brief description of the problem

**Error Message:**
```
Paste full error here
```

**What I've Tried:**
1. Checked network connectivity
2. Tested with VLC
3. ...

**Relevant Config:**
```yaml
camera_config:
  ip: 192.168.1.100
  ...
```
```

## Final Tips

1. **Start simple**: Get one camera working before adding more
2. **Monitor resources**: Watch CPU, GPU, RAM, disk usage
3. **Keep logs**: They're invaluable for debugging
4. **Test incrementally**: Add features one at a time
5. **Read the docs**: Most answers are already here

---

*AI Agent Note: Remember the golden rule - process video locally, display data remotely. Don't fight the architecture, work with it!*