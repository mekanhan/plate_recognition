# 🔄 Continuous Streaming Strategy

**Date**: 2025-07-25  
**Status**: 🔄 **IN PROGRESS**  
**Goal**: Always-on camera streaming for optimal user experience

## 🎯 Continuous Streaming Concept

### Current Behavior (Manual)
```
User clicks "Start Stream" → API call → Video appears → User clicks "Stop Stream"
```

### Target Behavior (Automatic)
```
Camera comes online → Stream starts automatically → Video always visible → Auto-reconnect on issues
```

## 🏗️ Technical Architecture

### Stream Lifecycle Management

```javascript
class ContinuousStreamManager {
    constructor() {
        this.streams = new Map();
        this.reconnectAttempts = new Map();
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // Start with 2s, exponential backoff
    }

    async initializeStream(cameraId) {
        const camera = await this.getCameraInfo(cameraId);
        
        if (camera.status !== 'online') {
            this.scheduleStatusCheck(cameraId);
            return;
        }

        await this.startStream(cameraId);
        this.monitorStreamHealth(cameraId);
    }

    async startStream(cameraId) {
        try {
            const response = await fetch(`/api/v1/streams/start/${cameraId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    quality: 'medium',
                    max_fps: 30,
                    auto_reconnect: true
                })
            });

            if (response.ok) {
                this.streams.set(cameraId, 'active');
                this.reconnectAttempts.set(cameraId, 0);
                this.broadcastStreamStatus(cameraId, 'streaming');
            }
        } catch (error) {
            console.error(`Stream start failed for camera ${cameraId}:`, error);
            this.scheduleReconnect(cameraId);
        }
    }

    monitorStreamHealth(cameraId) {
        const healthCheckInterval = setInterval(async () => {
            const isHealthy = await this.checkStreamHealth(cameraId);
            
            if (!isHealthy) {
                clearInterval(healthCheckInterval);
                this.handleStreamFailure(cameraId);
            }
        }, 10000); // Check every 10 seconds

        // Store interval for cleanup
        this.streams.set(`${cameraId}_health`, healthCheckInterval);
    }

    async handleStreamFailure(cameraId) {
        const attempts = this.reconnectAttempts.get(cameraId) || 0;
        
        if (attempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(cameraId);
        } else {
            this.broadcastStreamStatus(cameraId, 'failed');
            console.error(`Stream failed permanently for camera ${cameraId}`);
        }
    }

    scheduleReconnect(cameraId) {
        const attempts = this.reconnectAttempts.get(cameraId) || 0;
        const delay = this.reconnectDelay * Math.pow(2, attempts); // Exponential backoff
        
        this.broadcastStreamStatus(cameraId, 'reconnecting');
        
        setTimeout(async () => {
            this.reconnectAttempts.set(cameraId, attempts + 1);
            await this.startStream(cameraId);
        }, delay);
    }

    broadcastStreamStatus(cameraId, status) {
        // Notify all listening components
        window.dispatchEvent(new CustomEvent('streamStatusChange', {
            detail: { cameraId, status }
        }));
    }
}
```

### Auto-Start on Camera Discovery

```javascript
class CameraDiscoveryService {
    constructor() {
        this.knownCameras = new Set();
        this.streamManager = new ContinuousStreamManager();
    }

    async pollCameraStatus() {
        try {
            const response = await fetch('/api/v1/cameras/');
            const data = await response.json();
            
            data.cameras.forEach(camera => {
                this.processCameraStatus(camera);
            });
        } catch (error) {
            console.error('Camera status poll failed:', error);
        }
    }

    processCameraStatus(camera) {
        const wasKnown = this.knownCameras.has(camera.id);
        const isOnline = camera.status === 'online';
        
        if (isOnline && !wasKnown) {
            // New camera came online - start streaming
            console.log(`Camera ${camera.id} came online, starting stream`);
            this.streamManager.initializeStream(camera.id);
        } else if (!isOnline && wasKnown) {
            // Camera went offline - clean up
            console.log(`Camera ${camera.id} went offline, cleaning up`);
            this.streamManager.cleanup(camera.id);
        }
        
        // Update known cameras set
        if (isOnline) {
            this.knownCameras.add(camera.id);
        } else {
            this.knownCameras.delete(camera.id);
        }
    }

    startPolling() {
        // Initial poll
        this.pollCameraStatus();
        
        // Poll every 30 seconds
        setInterval(() => {
            this.pollCameraStatus();
        }, 30000);
    }
}
```

## 🎮 User Experience

### Visual Indicators

#### Stream States
```css
.camera-card {
    position: relative;
}

.stream-status-indicator {
    position: absolute;
    top: 8px;
    left: 8px;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
}

.stream-status-indicator.streaming {
    background: rgba(40, 167, 69, 0.9);
    color: white;
}

.stream-status-indicator.reconnecting {
    background: rgba(255, 193, 7, 0.9);
    color: black;
    animation: pulse 1.5s infinite;
}

.stream-status-indicator.failed {
    background: rgba(220, 53, 69, 0.9);
    color: white;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}
```

#### Loading States
```html
<!-- During stream initialization -->
<div class="stream-loading-overlay">
    <div class="loading-spinner"></div>
    <span>Connecting to camera...</span>
</div>

<!-- During reconnection -->
<div class="stream-reconnect-overlay">
    <div class="reconnect-spinner"></div>
    <span>Reconnecting... (Attempt 2/5)</span>
</div>

<!-- Stream failed -->
<div class="stream-error-overlay">
    <i class="fas fa-exclamation-triangle"></i>
    <span>Stream unavailable</span>
    <button class="retry-btn">Retry Connection</button>
</div>
```

### Smart Stream Management

#### Viewport Optimization
```javascript
class ViewportStreamManager {
    constructor() {
        this.observer = new IntersectionObserver(
            this.handleVisibilityChange.bind(this),
            { threshold: 0.1 }
        );
    }

    observeCamera(cameraElement, cameraId) {
        cameraElement.dataset.cameraId = cameraId;
        this.observer.observe(cameraElement);
    }

    handleVisibilityChange(entries) {
        entries.forEach(entry => {
            const cameraId = entry.target.dataset.cameraId;
            
            if (entry.isIntersecting) {
                // Camera is visible - ensure high quality stream
                this.upgradeStreamQuality(cameraId, 'high');
            } else {
                // Camera not visible - reduce to low quality to save bandwidth
                this.upgradeStreamQuality(cameraId, 'low');
            }
        });
    }

    async upgradeStreamQuality(cameraId, quality) {
        try {
            await fetch(`/api/v1/streams/quality/${cameraId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quality })
            });
        } catch (error) {
            console.error('Quality adjustment failed:', error);
        }
    }
}
```

## 📊 Performance Considerations

### Resource Management

#### Memory Optimization
```javascript
class StreamResourceManager {
    constructor() {
        this.maxConcurrentStreams = 8;
        this.activeStreams = new Map();
        this.streamPriority = new Map();
    }

    async requestStream(cameraId, priority = 'normal') {
        if (this.activeStreams.size >= this.maxConcurrentStreams) {
            await this.evictLowestPriorityStream();
        }

        this.streamPriority.set(cameraId, priority);
        this.activeStreams.set(cameraId, Date.now());
        
        return this.initializeStream(cameraId);
    }

    async evictLowestPriorityStream() {
        let lowestPriority = 'high';
        let oldestStream = null;
        let oldestTime = Date.now();

        this.activeStreams.forEach((timestamp, cameraId) => {
            const priority = this.streamPriority.get(cameraId);
            
            if (priority < lowestPriority || 
                (priority === lowestPriority && timestamp < oldestTime)) {
                lowestPriority = priority;
                oldestStream = cameraId;
                oldestTime = timestamp;
            }
        });

        if (oldestStream) {
            await this.stopStream(oldestStream);
        }
    }
}
```

#### Bandwidth Management
```javascript
class BandwidthManager {
    constructor() {
        this.totalBandwidth = 0;
        this.maxBandwidth = 50 * 1024 * 1024; // 50 Mbps
        this.streamBandwidth = new Map();
    }

    async adjustStreamQuality() {
        if (this.totalBandwidth > this.maxBandwidth * 0.8) {
            // Reduce quality of non-priority streams
            const streams = Array.from(this.streamBandwidth.entries())
                .sort(([,a], [,b]) => b - a); // Sort by bandwidth usage

            for (const [cameraId, bandwidth] of streams) {
                if (this.totalBandwidth <= this.maxBandwidth * 0.7) break;
                
                await this.reduceStreamQuality(cameraId);
                this.totalBandwidth -= bandwidth * 0.3; // Estimate 30% reduction
            }
        }
    }
}
```

## 🛡️ Error Handling

### Resilient Connection Management
```javascript
class ResilientStreamConnection {
    constructor(cameraId) {
        this.cameraId = cameraId;
        this.connectionState = 'disconnected';
        this.lastError = null;
        this.consecutiveFailures = 0;
    }

    async connect() {
        try {
            this.connectionState = 'connecting';
            
            const stream = await this.establishConnection();
            
            this.connectionState = 'connected';
            this.consecutiveFailures = 0;
            this.lastError = null;
            
            return stream;
        } catch (error) {
            this.consecutiveFailures++;
            this.lastError = error;
            this.connectionState = 'failed';
            
            if (this.shouldRetry()) {
                setTimeout(() => this.connect(), this.getRetryDelay());
            } else {
                this.connectionState = 'permanently_failed';
            }
            
            throw error;
        }
    }

    shouldRetry() {
        return this.consecutiveFailures < 5 && 
               !this.isPermanentError(this.lastError);
    }

    isPermanentError(error) {
        const permanentErrors = [
            'CAMERA_NOT_FOUND',
            'UNAUTHORIZED',
            'INVALID_RTSP_URL'
        ];
        
        return permanentErrors.some(code => 
            error.message.includes(code)
        );
    }

    getRetryDelay() {
        // Exponential backoff with jitter
        const baseDelay = 1000;
        const exponentialDelay = baseDelay * Math.pow(2, this.consecutiveFailures);
        const jitter = Math.random() * 1000;
        
        return Math.min(exponentialDelay + jitter, 30000); // Max 30 seconds
    }
}
```

## ✅ Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create ContinuousStreamManager
- [ ] Implement auto-start on camera online
- [ ] Add health monitoring and auto-reconnect
- [ ] Create visual status indicators

### Phase 2: Optimization
- [ ] Implement viewport-based quality adjustment
- [ ] Add bandwidth management
- [ ] Create resource manager for concurrent streams
- [ ] Add performance monitoring

### Phase 3: User Experience
- [ ] Smooth loading and error states
- [ ] Manual override controls (pause/resume)
- [ ] Stream quality indicators
- [ ] Connection diagnostics

### Phase 4: Monitoring
- [ ] Stream analytics dashboard
- [ ] Performance metrics collection
- [ ] Alert system for stream failures
- [ ] Bandwidth usage reporting

This continuous streaming approach will provide users with an always-live security monitoring experience, similar to professional CCTV systems.