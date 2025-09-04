# Streaming Reliability & Remaining Foundation 3 Considerations

## 🚨 Critical Stream Reliability Issues to Address

### 1. **Network Interruption Handling**

Based on the Foundation 3 risk mitigation strategy, network issues are a **system killer**. Here's what we need to implement:

#### **Connection Pool with Health Monitoring**
```python
# Must implement in Phase 2
class ResilientStreamManager:
    """Handles network interruptions gracefully"""
    
    def __init__(self):
        self.reconnect_attempts = {
            'immediate': 0,
            'short': 5,      # 5 attempts with 1s delay
            'medium': 3,     # 3 attempts with 30s delay
            'long': 2        # 2 attempts with 5min delay
        }
        self.dead_cameras = set()  # Cameras that failed all reconnects
        
    async def monitor_stream_health(self, camera_id: str):
        """Continuous health monitoring"""
        consecutive_failures = 0
        
        while camera_id not in self.dead_cameras:
            try:
                # Check if we're getting frames
                last_frame_time = await self.get_last_frame_time(camera_id)
                
                if time.time() - last_frame_time > 5.0:  # No frame in 5 seconds
                    consecutive_failures += 1
                    
                    if consecutive_failures > 3:
                        await self.handle_stream_failure(camera_id)
                else:
                    consecutive_failures = 0  # Reset on success
                    
            except Exception as e:
                logger.error(f"Health check failed for {camera_id}: {e}")
                
            await asyncio.sleep(1)  # Check every second
    
    async def handle_stream_failure(self, camera_id: str):
        """Graduated reconnection strategy"""
        for phase, attempts in self.reconnect_attempts.items():
            for attempt in range(attempts):
                if await self.try_reconnect(camera_id):
                    logger.info(f"Reconnected {camera_id} in {phase} phase")
                    return
                    
                # Wait based on phase
                delays = {'immediate': 0, 'short': 1, 'medium': 30, 'long': 300}
                await asyncio.sleep(delays[phase])
        
        # All attempts failed
        self.dead_cameras.add(camera_id)
        await self.notify_camera_death(camera_id)
```

### 2. **Browser Streaming Reliability Challenges**

#### **Problem Areas:**
1. **WebRTC Connection Drops** - NAT traversal, firewall issues
2. **HLS Latency Accumulation** - Segments pile up during network issues
3. **Browser Memory Leaks** - Long-running video streams
4. **Codec Compatibility** - Different browsers, different support

#### **Solutions We Must Implement:**

```javascript
// Frontend: Robust Stream Manager
class ReliableStreamManager {
    constructor() {
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.reconnectDecay = 1.5;
        this.connectionTimeout = 5000;
        this.healthCheckInterval = 3000;
    }
    
    async connectWithFallback(cameraId) {
        const strategies = [
            { method: 'webrtc', timeout: 5000 },
            { method: 'hls', timeout: 10000 },
            { method: 'websocket', timeout: 5000 },
            { method: 'snapshots', timeout: 3000 }
        ];
        
        for (const strategy of strategies) {
            try {
                const stream = await this.tryConnect(cameraId, strategy);
                this.startHealthMonitoring(stream);
                return stream;
            } catch (e) {
                console.warn(`${strategy.method} failed:`, e);
                continue;
            }
        }
        
        throw new Error('All streaming methods failed');
    }
    
    startHealthMonitoring(stream) {
        let lastFrameTime = Date.now();
        
        setInterval(() => {
            const stats = stream.getStats();
            
            // Detect frozen stream
            if (stats.framesDecoded === this.lastFrameCount) {
                if (Date.now() - lastFrameTime > 5000) {
                    this.handleFrozenStream(stream);
                }
            } else {
                lastFrameTime = Date.now();
                this.lastFrameCount = stats.framesDecoded;
            }
            
            // Detect quality degradation
            if (stats.packetsLost > stats.packetsReceived * 0.05) {
                this.requestQualityReduction(stream);
            }
            
        }, this.healthCheckInterval);
    }
}
```

### 3. **GPU Memory Management Issues**

From Phase 2 requirements: **"GPU memory management - Critical for 4+ cameras"**

```python
# Critical: Prevent GPU OOM with multiple streams
class GPUMemoryManager:
    def __init__(self, gpu_id=0):
        self.gpu_id = gpu_id
        self.reserved_memory = {}
        self.max_memory_gb = 10  # RTX 3080
        self.safety_margin_gb = 2
        
    def can_add_stream(self, camera_id: str, resolution: tuple) -> bool:
        """Check if GPU has memory for new stream"""
        required_mb = self.estimate_memory_usage(resolution)
        used_mb = sum(self.reserved_memory.values())
        available_mb = (self.max_memory_gb - self.safety_margin_gb) * 1024
        
        return (used_mb + required_mb) < available_mb
    
    def estimate_memory_usage(self, resolution: tuple) -> int:
        """Estimate GPU memory for stream processing"""
        width, height = resolution
        # Frame buffer + Model overhead + Working memory
        bytes_per_frame = width * height * 3  # RGB
        frames_in_buffer = 10  # Keep 10 frames
        model_overhead = 500  # 500MB per stream for AI
        
        return (bytes_per_frame * frames_in_buffer / 1024 / 1024) + model_overhead
```

## 📋 Remaining Foundation 3 Critical Items

### 1. **Reolink Camera Compatibility (Test Immediately!)**

```python
# Phase 1, Day 1 - Test with your actual cameras
REOLINK_TEST_CONFIGS = {
    'RLC-811A': {
        'rtsp_path': '/h264Preview_01_main',
        'http_snapshot': '/cgi-bin/api.cgi?cmd=Snap&channel=0',
        'username': 'admin',
        'auth_method': 'digest',  # Reolink uses digest auth
        'special_headers': {'User-Agent': 'Surveillance/1.0'}
    },
    'RLC-822A': {
        'rtsp_path': '/h265Preview_01_main',  # H.265 stream
        'supports_ptz': True,
        'ptz_commands': {
            'left': '/cgi-bin/api.cgi?cmd=PtzCtrl&op=Left',
            'right': '/cgi-bin/api.cgi?cmd=PtzCtrl&op=Right'
        }
    }
}

async def test_reolink_compatibility():
    """Must run on Day 1 to verify camera compatibility"""
    for model, config in REOLINK_TEST_CONFIGS.items():
        # Test RTSP
        rtsp_url = f"rtsp://{config['username']}:password@camera_ip{config['rtsp_path']}"
        
        # Test with digest authentication
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_FFMPEG_RTSP_FLAG_TCP)
        
        if not cap.isOpened():
            logger.error(f"Failed to connect to {model}")
            # Try alternative authentication methods
```

### 2. **Edge Recording Fallback (Phase 6)**

Critical for reliability when network/server fails:

```python
class EdgeRecordingFallback:
    """Records locally when server unreachable"""
    
    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.edge_storage = Path(f"/edge/recordings/{camera_id}")
        self.sync_queue = []
        
    async def start_edge_recording(self):
        """Fallback recording when server offline"""
        self.edge_storage.mkdir(exist_ok=True)
        
        # Record to local disk
        output_file = self.edge_storage / f"{int(time.time())}.mp4"
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', self.camera_rtsp_url,
            '-c:v', 'copy',  # Don't re-encode
            '-c:a', 'copy',
            '-f', 'segment',
            '-segment_time', '600',  # 10-minute segments
            '-reset_timestamps', '1',
            str(output_file)
        ]
        
        # Add to sync queue for later upload
        self.sync_queue.append(output_file)
    
    async def sync_when_online(self):
        """Upload edge recordings when connection restored"""
        while self.sync_queue:
            file_path = self.sync_queue.pop(0)
            try:
                await self.upload_to_server(file_path)
                file_path.unlink()  # Delete after successful upload
            except:
                self.sync_queue.insert(0, file_path)  # Re-queue
                break
```

### 3. **Performance Testing Benchmarks**

You MUST hit these targets for production:

```python
# Performance requirements from Foundation 3
PERFORMANCE_REQUIREMENTS = {
    'detection_latency': 500,  # ms - HARD REQUIREMENT
    'stream_latency': 500,     # ms for WebRTC
    'gpu_utilization': 80,     # % max for stability
    'memory_per_camera': 2048, # MB RAM
    'cpu_per_camera': 0.5,     # cores
    'storage_per_camera': 500, # GB/month at 1080p
}

async def performance_validation():
    """Run after each phase to ensure targets met"""
    results = {}
    
    # Test detection latency
    frame = get_test_frame()
    start = time.time()
    detections = await ai_processor.detect(frame)
    results['detection_latency'] = (time.time() - start) * 1000
    
    assert results['detection_latency'] < PERFORMANCE_REQUIREMENTS['detection_latency'], \
        f"Detection too slow: {results['detection_latency']}ms"
```

### 4. **Security Hardening for Streams**

```python
# Must implement before production
class StreamSecurity:
    """Secure streaming implementation"""
    
    def generate_stream_token(self, camera_id: str, user_id: str) -> str:
        """Time-limited token for stream access"""
        payload = {
            'camera_id': camera_id,
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(minutes=30),
            'permissions': ['view_live', 'view_recording']
        }
        return jwt.encode(payload, SECRET_KEY)
    
    def validate_stream_access(self, token: str, camera_id: str) -> bool:
        """Validate before allowing stream access"""
        try:
            payload = jwt.decode(token, SECRET_KEY)
            return (
                payload['camera_id'] == camera_id and
                payload['exp'] > datetime.utcnow() and
                'view_live' in payload['permissions']
            )
        except:
            return False
```

## 🎯 Stream Reliability Answer

### **Will the streams be reliable?**

**YES, BUT** only if you implement ALL of these:

1. ✅ **Connection pooling with retry logic** (Phase 2)
2. ✅ **Multiple streaming methods with fallback** (WebRTC → HLS → Snapshots)
3. ✅ **Continuous health monitoring** (Both server and client side)
4. ✅ **Edge recording fallback** (Phase 6)
5. ✅ **GPU memory management** (Phase 2)
6. ✅ **Graduated reconnection strategy**

### **Expected Reliability Metrics:**

- **Stream Uptime**: 99.5% with all mitigations
- **Recovery Time**: <5 seconds for temporary network issues
- **Fallback Time**: <2 seconds to switch streaming methods
- **Data Loss**: Zero with edge recording
- **User Experience**: Seamless with proper error handling

## 📊 Final Foundation 3 Checklist

### **Before Starting Development:**
- [ ] Test ALL Reolink camera models you'll use
- [ ] Verify network can handle bandwidth (50Mbps per 4K camera)
- [ ] Confirm GPU memory calculations
- [ ] Plan edge storage requirements
- [ ] Set up monitoring from Day 1

### **Critical Success Factors:**
1. **Don't skip Phase 1** - Database integration is BLOCKING
2. **Test with real cameras early** - Not simulators
3. **Monitor everything** - You can't fix what you can't see
4. **Build reliability in** - Not as an afterthought
5. **Have fallback for everything** - Assume failure

The architecture is solid, but streaming reliability requires implementing ALL the safety mechanisms. Skip any, and you'll have angry users with frozen streams!