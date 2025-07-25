# 📹 Camera Card Streaming Integration

**Date**: 2025-01-24  
**Parent Feature**: Streaming UI Integration  
**Target File**: `frontend/src/pages/CamerasPage.js`

## 🎯 Overview

Enhance camera cards with click-to-stream functionality, replacing static preview placeholders with live video streaming capabilities directly within the camera card interface.

## 📍 Current State Analysis

### Existing Preview Implementation (CamerasPage.js:267-278)
```javascript
<div class="camera-card-preview">
    <div class="preview-container">
        ${camera.status === 'online' ? 
            '<div class="video-feed-placeholder"><i class="fas fa-video"></i><span>Live Feed</span></div>' :
            camera.status === 'offline' ? 
            '<div class="offline-indicator"><i class="fas fa-exclamation-triangle"></i><span>No Signal</span></div>' :
            '<div class="warning-indicator"><i class="fas fa-exclamation-circle"></i><span>Degraded</span></div>'
        }
        <div class="preview-overlay">
            <button class="preview-play-btn" data-camera-id="${camera.id}" ${camera.status !== 'online' ? 'disabled' : ''}>
                <i class="fas fa-play"></i>
            </button>
        </div>
    </div>
</div>
```

### Current Issues
- **Static Placeholders**: No actual video content
- **Disabled Play Button**: Currently non-functional (Line 920-923)
- **No Stream Management**: Missing start/stop functionality
- **Limited Status**: Basic online/offline states only

## 🚀 Target State

### Enhanced Camera Card Preview
- **Live Thumbnails**: Show current frame from camera when available
- **Click-to-Stream**: Play button starts live video in card
- **Inline Controls**: Stream management without modal overlay
- **Status Indicators**: Real-time streaming status
- **Smooth Transitions**: Toggle between thumbnail and live stream

## 🔧 Technical Implementation

### 1. Enhanced Preview Rendering

Replace static placeholders with dynamic content:

```javascript
renderCameraCard(camera) {
    const statusClass = camera.status;
    const healthScore = this.calculateHealthScore(camera);
    const isStreaming = this.streamStates.get(camera.id) || false;
    
    return `
        <div class="camera-card" data-camera-id="${camera.id}">
            <!-- Camera Card Header (unchanged) -->
            <div class="camera-card-header">
                <div class="camera-title-row">
                    <div class="camera-checkbox" style="display: ${this.selectedCameras.size > 0 || this.bulkMode ? 'block' : 'none'}">
                        <input type="checkbox" class="camera-select" data-camera-id="${camera.id}" ${this.selectedCameras.has(camera.id) ? 'checked' : ''}>
                    </div>
                    <h4 class="camera-card-title">${camera.name}</h4>
                    <div class="camera-card-status ${statusClass}">
                        <i class="fas ${this.getStatusIcon(camera.status)}"></i>
                        <span>${this.capitalizeFirst(camera.status)}</span>
                        ${isStreaming ? '<span class="streaming-badge">STREAMING</span>' : ''}
                    </div>
                </div>
            </div>
            
            <!-- Enhanced Preview Section -->
            <div class="camera-card-body">
                <div class="camera-card-preview">
                    <div class="preview-container" id="preview-container-${camera.id}">
                        ${this.renderPreviewContent(camera, isStreaming)}
                        <div class="preview-overlay ${isStreaming ? 'streaming' : ''}">
                            ${this.renderPreviewControls(camera, isStreaming)}
                        </div>
                        <div class="preview-status-bar">
                            ${this.renderPreviewStatus(camera, isStreaming)}
                        </div>
                    </div>
                </div>
                
                <!-- Camera Info (unchanged) -->
                <div class="camera-card-info">
                    <!-- Existing info rows -->
                </div>
            </div>
            
            <!-- Camera Actions (unchanged) -->
            <div class="camera-card-actions">
                <!-- Existing action buttons -->
            </div>
        </div>
    `;
}
```

### 2. Dynamic Preview Content

```javascript
renderPreviewContent(camera, isStreaming) {
    if (camera.status === 'offline') {
        return `
            <div class="offline-indicator">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Camera Offline</span>
                <small>Last seen: ${this.getRelativeTime(camera.lastSeen)}</small>
            </div>
        `;
    }
    
    if (camera.status === 'warning') {
        return `
            <div class="warning-indicator">
                <i class="fas fa-exclamation-circle"></i>
                <span>Connection Issues</span>
                <small>Reduced functionality</small>
            </div>
        `;
    }
    
    if (isStreaming) {
        return `
            <div class="live-video-container">
                <img src="http://localhost:8001/stream/video/${camera.id}" 
                     alt="Live stream from ${camera.name}"
                     class="live-stream-preview"
                     onload="this.parentElement.classList.add('stream-active')"
                     onerror="this.parentElement.classList.add('stream-error')">
                <div class="stream-info-overlay">
                    <div class="live-indicator">
                        <span class="live-dot"></span>
                        LIVE
                    </div>
                    <div class="stream-quality">
                        <span class="quality-text">720p</span>
                    </div>
                </div>
                <div class="stream-loading" style="display: none;">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Connecting...</span>
                </div>
            </div>
        `;
    }
    
    // Default: Show thumbnail/preview
    return `
        <div class="camera-thumbnail">
            <img src="http://localhost:8001/stream/thumbnail/${camera.id}" 
                 alt="Preview from ${camera.name}"
                 class="thumbnail-image"
                 onload="this.parentElement.classList.add('thumbnail-loaded')"
                 onerror="this.src='/images/camera-placeholder.jpg'">
            <div class="thumbnail-overlay">
                <div class="thumbnail-info">
                    <span class="capture-time" id="capture-time-${camera.id}">
                        ${new Date().toLocaleTimeString()}
                    </span>
                </div>
            </div>
        </div>
    `;
}
```

### 3. Interactive Preview Controls

```javascript
renderPreviewControls(camera, isStreaming) {
    if (camera.status !== 'online') {
        return `
            <div class="preview-controls disabled">
                <button class="preview-control-btn" disabled title="Camera offline">
                    <i class="fas fa-ban"></i>
                </button>
            </div>
        `;
    }
    
    if (isStreaming) {
        return `
            <div class="preview-controls streaming">
                <button class="preview-control-btn stop-stream" 
                        data-action="stop-stream" 
                        data-camera-id="${camera.id}"
                        title="Stop streaming">
                    <i class="fas fa-stop"></i>
                </button>
                <button class="preview-control-btn fullscreen" 
                        data-action="fullscreen" 
                        data-camera-id="${camera.id}"
                        title="Fullscreen">
                    <i class="fas fa-expand"></i>
                </button>
                <button class="preview-control-btn capture" 
                        data-action="capture" 
                        data-camera-id="${camera.id}"
                        title="Capture frame">
                    <i class="fas fa-camera"></i>
                </button>
            </div>
        `;
    }
    
    return `
        <div class="preview-controls">
            <button class="preview-control-btn start-stream" 
                    data-action="start-stream" 
                    data-camera-id="${camera.id}"
                    title="Start live stream">
                <i class="fas fa-play"></i>
            </button>
            <button class="preview-control-btn refresh" 
                    data-action="refresh-thumbnail" 
                    data-camera-id="${camera.id}"
                    title="Refresh thumbnail">
                <i class="fas fa-sync-alt"></i>
            </button>
        </div>
    `;
}

renderPreviewStatus(camera, isStreaming) {
    if (isStreaming) {
        return `
            <div class="status-indicator streaming">
                <span class="status-text">Streaming</span>
                <span class="stream-duration" id="duration-${camera.id}">00:00</span>
                <span class="stream-fps">30 FPS</span>
            </div>
        `;
    }
    
    return `
        <div class="status-indicator">
            <span class="status-text">${this.capitalizeFirst(camera.status)}</span>
            <span class="last-update">Updated: ${this.getRelativeTime(camera.lastSeen)}</span>
        </div>
    `;
}
```

### 4. Stream State Management

```javascript
class Cameras {
    constructor() {
        // Existing properties...
        this.streamStates = new Map(); // Track streaming state per camera
        this.streamTimers = new Map(); // Track stream duration timers
        this.refreshIntervals = new Map(); // Track thumbnail refresh intervals
    }

    attachCameraEventListeners() {
        // Existing listeners...
        
        // Enhanced preview controls
        document.querySelectorAll('.preview-control-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handlePreviewControl(e));
        });
    }

    async handlePreviewControl(e) {
        e.stopPropagation();
        const action = e.target.dataset.action || e.target.parentElement.dataset.action;
        const cameraId = e.target.dataset.cameraId || e.target.parentElement.dataset.cameraId;
        
        switch (action) {
            case 'start-stream':
                await this.startCameraStream(cameraId);
                break;
            case 'stop-stream':
                await this.stopCameraStream(cameraId);
                break;
            case 'fullscreen':
                this.openFullscreenPreview(cameraId);
                break;
            case 'capture':
                await this.captureFrame(cameraId);
                break;
            case 'refresh-thumbnail':
                await this.refreshThumbnail(cameraId);
                break;
        }
    }
```

### 5. Stream Control Implementation

```javascript
async startCameraStream(cameraId) {
    const camera = this.cameras.find(c => c.id === cameraId);
    if (!camera || camera.status !== 'online') return;

    const btn = document.querySelector(`[data-action="start-stream"][data-camera-id="${cameraId}"]`);
    const icon = btn?.querySelector('i');
    
    try {
        // Show loading state
        if (btn) {
            btn.disabled = true;
            if (icon) icon.className = 'fas fa-spinner fa-spin';
        }

        // Start stream via API
        const response = await fetch(`http://localhost:8001/api/v1/streams/start/${cameraId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                quality: 'medium',
                max_fps: 30,
                detection_enabled: false
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        
        // Update state
        this.streamStates.set(cameraId, true);
        
        // Update UI
        this.updatePreviewContainer(cameraId);
        this.startStreamTimer(cameraId);
        
        this.showToast(`Stream started for ${camera.name}`, 'success');
        
    } catch (error) {
        console.error('Failed to start stream:', error);
        this.showToast(`Failed to start stream for ${camera.name}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            if (icon) icon.className = 'fas fa-play';
        }
    }
}

async stopCameraStream(cameraId) {
    const camera = this.cameras.find(c => c.id === cameraId);
    if (!camera) return;

    const btn = document.querySelector(`[data-action="stop-stream"][data-camera-id="${cameraId}"]`);
    const icon = btn?.querySelector('i');
    
    try {
        // Show loading state
        if (btn) {
            btn.disabled = true;
            if (icon) icon.className = 'fas fa-spinner fa-spin';
        }

        // Stop stream via API
        const response = await fetch(`http://localhost:8001/api/v1/streams/stop/${cameraId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        // Update state
        this.streamStates.set(cameraId, false);
        
        // Cleanup timers
        this.stopStreamTimer(cameraId);
        
        // Update UI
        this.updatePreviewContainer(cameraId);
        
        this.showToast(`Stream stopped for ${camera.name}`, 'info');
        
    } catch (error) {
        console.error('Failed to stop stream:', error);
        this.showToast(`Failed to stop stream for ${camera.name}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            if (icon) icon.className = 'fas fa-stop';
        }
    }
}

updatePreviewContainer(cameraId) {
    const container = document.getElementById(`preview-container-${cameraId}`);
    if (!container) return;
    
    const camera = this.cameras.find(c => c.id === cameraId);
    const isStreaming = this.streamStates.get(cameraId) || false;
    
    container.innerHTML = `
        ${this.renderPreviewContent(camera, isStreaming)}
        <div class="preview-overlay ${isStreaming ? 'streaming' : ''}">
            ${this.renderPreviewControls(camera, isStreaming)}
        </div>
        <div class="preview-status-bar">
            ${this.renderPreviewStatus(camera, isStreaming)}
        </div>
    `;
    
    // Reattach event listeners
    container.querySelectorAll('.preview-control-btn').forEach(btn => {
        btn.addEventListener('click', (e) => this.handlePreviewControl(e));
    });
}
```

### 6. Stream Duration Timer

```javascript
startStreamTimer(cameraId) {
    const startTime = Date.now();
    
    const timer = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        const durationElement = document.getElementById(`duration-${cameraId}`);
        if (durationElement) {
            durationElement.textContent = display;
        }
    }, 1000);
    
    this.streamTimers.set(cameraId, timer);
}

stopStreamTimer(cameraId) {
    const timer = this.streamTimers.get(cameraId);
    if (timer) {
        clearInterval(timer);
        this.streamTimers.delete(cameraId);
    }
}
```

### 7. Additional Features

```javascript
async refreshThumbnail(cameraId) {
    const camera = this.cameras.find(c => c.id === cameraId);
    if (!camera) return;

    const btn = document.querySelector(`[data-action="refresh-thumbnail"][data-camera-id="${cameraId}"]`);
    const icon = btn?.querySelector('i');
    
    if (btn && icon) {
        btn.disabled = true;
        icon.classList.add('fa-spin');
    }

    try {
        // Force thumbnail refresh by adding timestamp
        const thumbnailImg = document.querySelector(`#preview-container-${cameraId} .thumbnail-image`);
        if (thumbnailImg) {
            const baseUrl = `http://localhost:8001/stream/thumbnail/${cameraId}`;
            thumbnailImg.src = `${baseUrl}?t=${Date.now()}`;
        }

        this.showToast(`Thumbnail refreshed for ${camera.name}`, 'success');
    } catch (error) {
        this.showToast(`Failed to refresh thumbnail`, 'error');
    } finally {
        setTimeout(() => {
            if (btn && icon) {
                btn.disabled = false;
                icon.classList.remove('fa-spin');
            }
        }, 1000);
    }
}

async captureFrame(cameraId) {
    const camera = this.cameras.find(c => c.id === cameraId);
    if (!camera) return;

    try {
        // Create download link for current frame
        const captureUrl = `http://localhost:8001/stream/thumbnail/${cameraId}?t=${Date.now()}`;
        
        const link = document.createElement('a');
        link.href = captureUrl;
        link.download = `${camera.name.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.showToast(`Frame captured from ${camera.name}`, 'success');
    } catch (error) {
        this.showToast(`Failed to capture frame`, 'error');
    }
}

openFullscreenPreview(cameraId) {
    const camera = this.cameras.find(c => c.id === cameraId);
    if (!camera) return;

    // Create fullscreen modal
    const modal = document.createElement('div');
    modal.className = 'fullscreen-preview-modal';
    modal.innerHTML = `
        <div class="fullscreen-content">
            <div class="fullscreen-header">
                <h3>${camera.name} - Live Stream</h3>
                <button class="close-fullscreen">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="fullscreen-video">
                <img src="http://localhost:8001/stream/video/${cameraId}" 
                     alt="Fullscreen view of ${camera.name}" 
                     class="fullscreen-stream">
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = 'flex';

    // Close handlers
    modal.querySelector('.close-fullscreen').addEventListener('click', () => {
        modal.remove();
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });

    // Escape key handler
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
}
```

## 🎨 Enhanced Styling

### CSS for Camera Card Streaming

```css
/* Enhanced Camera Card Preview */
.camera-card-preview {
    position: relative;
    height: 200px;
    background: #000;
    border-radius: 6px;
    overflow: hidden;
}

.preview-container {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Live Video Streaming */
.live-video-container {
    position: relative;
    width: 100%;
    height: 100%;
}

.live-stream-preview {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 6px;
}

.stream-info-overlay {
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
    font-size: 10px;
    font-weight: bold;
    display: flex;
    align-items: center;
    gap: 4px;
}

.live-dot {
    width: 4px;
    height: 4px;
    background: white;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

.stream-quality {
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 9px;
}

/* Thumbnail Display */
.camera-thumbnail {
    position: relative;
    width: 100%;
    height: 100%;
}

.thumbnail-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 6px;
}

.thumbnail-overlay {
    position: absolute;
    bottom: 8px;
    left: 8px;
    right: 8px;
}

.capture-time {
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 9px;
}

/* Preview Controls */
.preview-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s;
}

.preview-container:hover .preview-overlay {
    opacity: 1;
}

.preview-overlay.streaming {
    background: rgba(0, 0, 0, 0.1);
}

.preview-controls {
    display: flex;
    gap: 8px;
}

.preview-control-btn {
    width: 40px;
    height: 40px;
    background: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 14px;
    color: #333;
}

.preview-control-btn:hover:not(:disabled) {
    background: white;
    transform: scale(1.1);
}

.preview-control-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.preview-control-btn.stop-stream {
    background: rgba(220, 53, 69, 0.9);
    color: white;
}

.preview-control-btn.stop-stream:hover {
    background: #dc3545;
}

/* Status Bar */
.preview-status-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
    padding: 8px 12px 12px;
}

.status-indicator {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: white;
}

.status-indicator.streaming .status-text {
    color: #28a745;
    font-weight: bold;
}

.streaming-badge {
    background: #dc3545;
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 9px;
    font-weight: bold;
    margin-left: 8px;
}

/* Offline/Warning States */
.offline-indicator,
.warning-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: white;
    text-align: center;
}

.offline-indicator {
    background: linear-gradient(135deg, #6c757d, #495057);
}

.warning-indicator {
    background: linear-gradient(135deg, #ffc107, #e0a800);
    color: #333;
}

.offline-indicator i,
.warning-indicator i {
    font-size: 24px;
}

.offline-indicator small,
.warning-indicator small {
    font-size: 10px;
    opacity: 0.8;
}

/* Fullscreen Modal */
.fullscreen-preview-modal {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.95);
    display: flex;
    flex-direction: column;
    z-index: 10000;
}

.fullscreen-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    margin: 20px;
}

.fullscreen-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: white;
    margin-bottom: 20px;
}

.close-fullscreen {
    background: none;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    padding: 8px;
}

.fullscreen-video {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}

.fullscreen-stream {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}

/* Loading States */
.stream-loading {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: white;
}

.stream-loading i {
    font-size: 24px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .preview-controls {
        gap: 12px;
    }
    
    .preview-control-btn {
        width: 44px;
        height: 44px;
        font-size: 16px;
    }
    
    .fullscreen-content {
        margin: 10px;
    }
}
```

## 📱 State Persistence

### Local Storage Integration

```javascript
// Save stream states to localStorage
saveStreamStates() {
    const states = {};
    this.streamStates.forEach((value, key) => {
        states[key] = value;
    });
    localStorage.setItem('cameraStreamStates', JSON.stringify(states));
}

// Restore stream states from localStorage
restoreStreamStates() {
    try {
        const saved = localStorage.getItem('cameraStreamStates');
        if (saved) {
            const states = JSON.parse(saved);
            Object.entries(states).forEach(([key, value]) => {
                this.streamStates.set(key, value);
            });
        }
    } catch (error) {
        console.error('Failed to restore stream states:', error);
    }
}

// Auto-save states on changes
async startCameraStream(cameraId) {
    // ... existing implementation ...
    
    // Save state after successful start
    this.saveStreamStates();
}

async stopCameraStream(cameraId) {
    // ... existing implementation ...
    
    // Save state after successful stop
    this.saveStreamStates();
}
```

## ✅ Testing Checklist

### Functional Testing
- [ ] Play button starts live stream in camera card
- [ ] Stop button stops streaming and returns to thumbnail
- [ ] Fullscreen mode works correctly
- [ ] Frame capture downloads current image
- [ ] Thumbnail refresh updates preview
- [ ] Stream duration timer counts accurately
- [ ] Status indicators update properly

### Error Handling
- [ ] Graceful handling of offline cameras
- [ ] Network error recovery
- [ ] Invalid camera ID handling
- [ ] Stream timeout handling
- [ ] Memory cleanup on errors

### Performance Testing
- [ ] Multiple concurrent streams don't slow UI
- [ ] Memory usage remains stable
- [ ] Stream startup time < 3 seconds
- [ ] Smooth transitions between states

### User Experience
- [ ] Intuitive control placement
- [ ] Clear visual feedback
- [ ] Responsive design on mobile
- [ ] Accessibility compliance
- [ ] Consistent with existing design

---

## 🚀 Implementation Priority

1. **High Priority**: Basic click-to-stream functionality
2. **High Priority**: Stream start/stop controls
3. **Medium Priority**: Status indicators and duration timer
4. **Medium Priority**: Fullscreen and capture features
5. **Low Priority**: State persistence and advanced features

**This implementation transforms static camera cards into dynamic, interactive streaming interfaces while maintaining the existing card layout and design consistency.**