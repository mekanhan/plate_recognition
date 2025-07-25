# 📊 Dashboard Live Camera Feeds Integration

**Date**: 2025-01-24  
**Parent Feature**: Streaming UI Integration  
**Target File**: `frontend/src/pages/Dashboard.js`

## 🎯 Overview

Transform the Dashboard's Live Camera Feeds section from static placeholders to real-time video streams using the working RTSP streaming backend.

## 📍 Current State Analysis

### Existing Implementation (Dashboard.js:297-329)
```javascript
renderLiveFeeds() {
    // Mock camera feeds with placeholders
    const mockFeeds = [
        { id: 'cam1', name: 'Entrance Gate', status: 'online' },
        { id: 'cam2', name: 'Parking Lot A', status: 'online' },
        { id: 'cam3', name: 'Loading Dock', status: 'warning' },
        { id: 'cam4', name: 'Side Entrance', status: 'online' }
    ];

    container.innerHTML = mockFeeds.map(feed => `
        <div class="camera-feed-item ${feed.status}">
            <div class="video-placeholder">
                <i class="fas fa-video"></i>
                <span>Live Feed</span>
            </div>
        </div>
    `).join('');
}
```

### Issues with Current Implementation
- **Static Mock Data**: No real camera integration
- **Placeholder Videos**: No actual streaming capability
- **No API Integration**: Not connected to backend camera list
- **Limited Controls**: No stream management functionality

## 🚀 Target State

### Real-time Live Feeds
- **Dynamic Camera List**: Fetch cameras from API `/api/v1/cameras/`
- **Live Video Streams**: Display actual RTSP streams via `/stream/video/{camera_id}`
- **Status Indicators**: Real-time online/offline/streaming status
- **Grid Controls**: 1-4 camera layout with pagination
- **Stream Management**: Start/stop individual feeds

## 🔧 Technical Implementation

### 1. API Integration

Replace mock data with real camera data:

```javascript
async loadLiveCameras() {
    try {
        const response = await fetch('http://localhost:8001/api/v1/cameras/');
        const data = await response.json();
        
        // Filter for enabled cameras and add streaming status
        this.liveCameras = data.cameras
            .filter(camera => camera.enabled)
            .map(camera => ({
                id: camera.id,
                name: camera.name,
                location: camera.location,
                status: camera.status,
                ipAddress: camera.ip_address,
                streamUrl: `/stream/video/${camera.id}`,
                thumbnailUrl: `/stream/thumbnail/${camera.id}`,
                isStreaming: false
            }));
            
        this.renderLiveFeeds();
    } catch (error) {
        console.error('Failed to load cameras:', error);
        this.showAlert('Failed to load camera feeds', 'error');
    }
}
```

### 2. LiveVideoPlayer Integration

Replace video placeholders with actual streaming:

```javascript
renderLiveFeeds() {
    const container = document.getElementById('live-camera-grid');
    if (!container || !this.liveCameras.length) {
        container.innerHTML = this.getNoFeedsMessage();
        return;
    }

    // Apply camera count filter
    const selectedCount = parseInt(document.getElementById('camera-count-select')?.value || 4);
    const displayCameras = this.liveCameras.slice(0, selectedCount);

    container.innerHTML = displayCameras.map(camera => `
        <div class="camera-feed-item ${camera.status}" data-camera-id="${camera.id}">
            <div class="camera-feed-header">
                <span class="camera-name">${camera.name}</span>
                <div class="camera-status-indicator ${camera.status}">
                    <i class="fas ${this.getStatusIcon(camera.status)}"></i>
                    <span class="status-text">${this.getStatusText(camera.status)}</span>
                </div>
            </div>
            
            <div class="camera-feed-video" id="video-container-${camera.id}">
                ${camera.status === 'online' ? 
                    this.renderVideoPlayer(camera) : 
                    this.renderOfflinePlaceholder(camera)
                }
            </div>
            
            <div class="camera-feed-controls">
                <button class="feed-control-btn" data-action="stream" data-camera-id="${camera.id}" 
                        ${camera.status !== 'online' ? 'disabled' : ''}>
                    <i class="fas ${camera.isStreaming ? 'fa-stop' : 'fa-play'}"></i>
                    ${camera.isStreaming ? 'Stop' : 'Start'}
                </button>
                <button class="feed-control-btn" data-action="fullscreen" data-camera-id="${camera.id}">
                    <i class="fas fa-expand"></i>
                </button>
                <button class="feed-control-btn" data-action="settings" data-camera-id="${camera.id}">
                    <i class="fas fa-cog"></i>
                </button>
            </div>
            
            <div class="camera-feed-info">
                <span class="resolution">Res: ${camera.resolution || '640x360'}</span>
                <span class="fps">FPS: ${camera.fps || 'Auto'}</span>
                <span class="quality">Quality: Medium</span>
            </div>
        </div>
    `).join('');

    // Attach event listeners for controls
    this.attachFeedControlListeners();
}
```

### 3. Video Player Component

```javascript
renderVideoPlayer(camera) {
    if (!camera.isStreaming) {
        return `
            <div class="video-thumbnail">
                <img src="${camera.thumbnailUrl}" alt="${camera.name}" 
                     onerror="this.src='data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100\" height=\"75\" viewBox=\"0 0 100 75\"><rect width=\"100\" height=\"75\" fill=\"%23f0f0f0\"/><text x=\"50\" y=\"40\" text-anchor=\"middle\" fill=\"%23999\">No Image</text></svg>'">
                <div class="play-overlay">
                    <i class="fas fa-play"></i>
                </div>
            </div>
        `;
    }

    return `
        <div class="live-video-player">
            <img src="${camera.streamUrl}" alt="Live feed from ${camera.name}" 
                 class="live-stream" 
                 onload="this.parentElement.classList.add('streaming')"
                 onerror="this.parentElement.classList.add('error')">
            <div class="stream-overlay">
                <div class="live-indicator">
                    <span class="live-dot"></span>
                    LIVE
                </div>
                <div class="stream-info">
                    <span class="stream-time" id="stream-time-${camera.id}">00:00</span>
                </div>
            </div>
            <div class="stream-loading" style="display: none;">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Connecting...</span>
            </div>
        </div>
    `;
}
```

### 4. Stream Controls Handler

```javascript
attachFeedControlListeners() {
    document.querySelectorAll('.feed-control-btn').forEach(btn => {
        btn.addEventListener('click', (e) => this.handleFeedControl(e));
    });
}

async handleFeedControl(e) {
    const action = e.target.dataset.action || e.target.parentElement.dataset.action;
    const cameraId = e.target.dataset.cameraId || e.target.parentElement.dataset.cameraId;
    
    switch (action) {
        case 'stream':
            await this.toggleStream(cameraId);
            break;
        case 'fullscreen':
            this.openFullscreenFeed(cameraId);
            break;
        case 'settings':
            this.openFeedSettings(cameraId);
            break;
    }
}

async toggleStream(cameraId) {
    const camera = this.liveCameras.find(c => c.id.toString() === cameraId);
    if (!camera) return;

    const btn = document.querySelector(`[data-action="stream"][data-camera-id="${cameraId}"]`);
    const icon = btn.querySelector('i');
    const text = btn.querySelector('span') || btn.childNodes[btn.childNodes.length - 1];

    try {
        if (camera.isStreaming) {
            // Stop stream
            btn.disabled = true;
            icon.className = 'fas fa-spinner fa-spin';
            
            const response = await fetch(`http://localhost:8001/api/v1/streams/stop/${cameraId}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                camera.isStreaming = false;
                icon.className = 'fas fa-play';
                text.textContent = 'Start';
                this.updateVideoContainer(cameraId, camera);
            }
        } else {
            // Start stream
            btn.disabled = true;
            icon.className = 'fas fa-spinner fa-spin';
            
            const response = await fetch(`http://localhost:8001/api/v1/streams/start/${cameraId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    quality: 'medium',
                    max_fps: 30
                })
            });
            
            if (response.ok) {
                camera.isStreaming = true;
                icon.className = 'fas fa-stop';
                text.textContent = 'Stop';
                this.updateVideoContainer(cameraId, camera);
                this.startStreamTimer(cameraId);
            }
        }
    } catch (error) {
        console.error('Stream control error:', error);
        this.showAlert(`Failed to ${camera.isStreaming ? 'stop' : 'start'} stream`, 'error');
    } finally {
        btn.disabled = false;
    }
}
```

### 5. Real-time Status Updates

```javascript
startStatusPolling() {
    // Poll camera status every 30 seconds
    this.statusInterval = setInterval(async () => {
        await this.updateCameraStatuses();
    }, 30000);
}

async updateCameraStatuses() {
    try {
        const response = await fetch('http://localhost:8001/api/v1/streams/');
        const streamsData = await response.json();
        
        // Update streaming status for each camera
        this.liveCameras.forEach(camera => {
            const streamInfo = streamsData.streams.find(s => s.camera_id === camera.id);
            camera.isStreaming = streamInfo?.status === 'active';
            
            // Update UI
            this.updateCameraStatusIndicator(camera.id, camera);
        });
    } catch (error) {
        console.error('Status update failed:', error);
    }
}

updateCameraStatusIndicator(cameraId, camera) {
    const statusIndicator = document.querySelector(`[data-camera-id="${cameraId}"] .camera-status-indicator`);
    if (statusIndicator) {
        statusIndicator.className = `camera-status-indicator ${camera.status}`;
        statusIndicator.querySelector('.status-text').textContent = this.getStatusText(camera.status);
        statusIndicator.querySelector('i').className = `fas ${this.getStatusIcon(camera.status)}`;
    }
}
```

## 🎨 Styling Updates

### CSS Enhancements for Live Feeds

```css
/* Live Camera Feeds Styling */
.camera-feed-item {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}

.camera-feed-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.camera-feed-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
}

.camera-status-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
}

.camera-status-indicator.online { color: #28a745; }
.camera-status-indicator.offline { color: #dc3545; }
.camera-status-indicator.warning { color: #ffc107; }

.camera-feed-video {
    position: relative;
    height: 200px;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.live-video-player {
    position: relative;
    width: 100%;
    height: 100%;
}

.live-stream {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.stream-overlay {
    position: absolute;
    top: 8px;
    left: 8px;
    right: 8px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.live-indicator {
    background: rgba(220, 53, 69, 0.9);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    display: flex;
    align-items: center;
    gap: 4px;
}

.live-dot {
    width: 6px;
    height: 6px;
    background: white;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

.camera-feed-controls {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    background: white;
}

.feed-control-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 12px;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s;
}

.feed-control-btn:hover:not(:disabled) {
    background: #e9ecef;
    border-color: #adb5bd;
}

.feed-control-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.camera-feed-info {
    display: flex;
    gap: 16px;
    padding: 8px 16px;
    background: #f8f9fa;
    font-size: 11px;
    color: #6c757d;
}
```

## 📱 Responsive Design

### Grid Layout Adaptation

```css
/* Responsive Grid Layouts */
.camera-grid {
    display: grid;
    gap: 20px;
    margin-top: 20px;
}

/* 1 Camera Layout */
.camera-grid.layout-1 {
    grid-template-columns: 1fr;
}

/* 2 Camera Layout */
.camera-grid.layout-2 {
    grid-template-columns: repeat(2, 1fr);
}

/* 3 Camera Layout */
.camera-grid.layout-3 {
    grid-template-columns: repeat(2, 1fr);
}

.camera-grid.layout-3 .camera-feed-item:first-child {
    grid-column: 1 / -1;
}

/* 4 Camera Layout */
.camera-grid.layout-4 {
    grid-template-columns: repeat(2, 1fr);
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .camera-grid.layout-2,
    .camera-grid.layout-3,
    .camera-grid.layout-4 {
        grid-template-columns: 1fr;
    }
    
    .camera-grid.layout-3 .camera-feed-item:first-child {
        grid-column: auto;
    }
}
```

## 🔄 Real-time Updates

### Auto-refresh Mechanism

```javascript
// Enhanced data loading with live feed support
async loadData() {
    try {
        // Load basic dashboard data
        await this.simulateDataLoad();
        
        // Load live cameras
        await this.loadLiveCameras();
        
        // Update metrics and other sections
        this.updateMetrics();
        this.renderRecentDetections();
        this.renderSystemHealth();
        
        // Start status polling
        if (!this.statusInterval) {
            this.startStatusPolling();
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        this.showAlert('Failed to load dashboard data', 'error');
    }
}

// Cleanup on component destroy
destroy() {
    this.stopAutoRefresh();
    if (this.statusInterval) {
        clearInterval(this.statusInterval);
        this.statusInterval = null;
    }
    
    // Stop all active streams
    this.liveCameras.forEach(camera => {
        if (camera.isStreaming) {
            this.toggleStream(camera.id);
        }
    });
}
```

## 📊 Performance Optimization

### Lazy Loading and Resource Management

```javascript
// Optimize video loading
renderVideoPlayer(camera) {
    if (!camera.isStreaming) {
        return this.renderThumbnail(camera);
    }

    return `
        <div class="live-video-player" data-camera-id="${camera.id}">
            <img src="${camera.streamUrl}" 
                 alt="Live feed from ${camera.name}"
                 class="live-stream"
                 loading="lazy"
                 onload="this.parentElement.classList.add('loaded')"
                 onerror="this.parentElement.classList.add('error')">
            <!-- Stream overlay and controls -->
        </div>
    `;
}

// Resource cleanup
updateVideoContainer(cameraId, camera) {
    const container = document.getElementById(`video-container-${cameraId}`);
    if (container) {
        // Clean up existing video element
        const existingVideo = container.querySelector('.live-stream');
        if (existingVideo) {
            existingVideo.onload = null;
            existingVideo.onerror = null;
            existingVideo.src = '';
        }
        
        // Update container content
        container.innerHTML = this.renderVideoPlayer(camera);
    }
}
```

## ✅ Testing Checklist

### Functional Testing
- [ ] Camera list loads from API correctly
- [ ] Live feeds display for online cameras
- [ ] Stream start/stop controls work
- [ ] Status indicators update in real-time
- [ ] Grid layout controls function properly
- [ ] Fullscreen mode works
- [ ] Error handling for offline cameras

### Performance Testing
- [ ] Multiple streams don't impact UI responsiveness
- [ ] Memory usage remains stable
- [ ] Network bandwidth usage is reasonable
- [ ] Stream startup time < 3 seconds

### Compatibility Testing
- [ ] Works in Chrome, Firefox, Safari, Edge
- [ ] Mobile responsive design functions correctly
- [ ] Touch controls work on mobile devices
- [ ] Accessibility features work properly

---

## 🚀 Implementation Priority

1. **High Priority**: Basic live feed integration with API
2. **High Priority**: Stream start/stop controls
3. **Medium Priority**: Real-time status updates
4. **Medium Priority**: Grid layout controls
5. **Low Priority**: Advanced features (fullscreen, settings)

**This implementation will transform the Dashboard into a powerful live monitoring interface, leveraging the fully working RTSP streaming backend.**