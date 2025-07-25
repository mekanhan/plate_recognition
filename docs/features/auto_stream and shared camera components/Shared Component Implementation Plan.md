# 🧩 Shared Component Implementation Plan

**Date**: 2025-07-25  
**Status**: 🔨 **IMPLEMENTATION READY**  
**Goal**: Create reusable components for consistent camera streaming

## 🎯 Component Architecture

### Core Components Structure
```
src/components/camera/
├── CameraCard.js                 # Main adaptive component
├── CameraVideo.js                # Video streaming logic
├── CameraInfo.js                 # Information display
├── CameraControls.js             # Stream controls
├── CameraStatus.js               # Status indicators
├── StreamManager.js              # Stream state management
└── styles/
    ├── CameraCard.css            # Component styles
    └── CameraVariants.css        # Context-specific styles
```

## 🔧 Implementation Details

### 1. CameraCard Component (Main)

```javascript
// src/components/camera/CameraCard.js
class CameraCard {
    constructor(container, camera, options = {}) {
        this.container = container;
        this.camera = camera;
        this.options = {
            context: 'dashboard', // or 'management'
            autoStream: true,
            showControls: true,
            showInfo: true,
            ...options
        };
        
        this.streamManager = window.globalStreamManager || new StreamManager();
        this.isInitialized = false;
        this.streamState = 'disconnected';
        
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
        
        if (this.options.autoStream && this.camera.status === 'online') {
            this.startAutoStream();
        }
        
        this.isInitialized = true;
    }

    render() {
        const config = this.getContextConfig();
        
        this.container.innerHTML = `
            <div class="camera-card camera-card--${this.options.context}" 
                 data-camera-id="${this.camera.id}">
                ${config.showHeader ? this.renderHeader() : ''}
                ${this.renderVideo()}
                ${config.showInfo ? this.renderInfo() : ''}
                ${config.showActions ? this.renderActions() : ''}
            </div>
        `;
    }

    getContextConfig() {
        const configs = {
            dashboard: {
                showHeader: false,
                showInfo: true,
                showActions: false,
                videoHeight: '160px',
                infoType: 'compact',
                controls: ['fullscreen', 'capture']
            },
            management: {
                showHeader: true,
                showInfo: true,
                showActions: true,
                videoHeight: '200px',
                infoType: 'detailed',
                controls: ['fullscreen', 'capture', 'record', 'settings']
            }
        };
        
        return configs[this.options.context] || configs.dashboard;
    }

    renderHeader() {
        return `
            <div class="camera-header">
                <div class="camera-title">
                    <h4 class="camera-name">${this.camera.name}</h4>
                    <span class="camera-id">ID: ${this.camera.id}</span>
                </div>
                <div class="camera-actions">
                    <button class="action-btn" data-action="configure" title="Configure">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="action-btn" data-action="diagnostics" title="Diagnostics">
                        <i class="fas fa-stethoscope"></i>
                    </button>
                </div>
            </div>
        `;
    }

    renderVideo() {
        const config = this.getContextConfig();
        
        return `
            <div class="camera-video" style="height: ${config.videoHeight}">
                <div class="video-container" id="video-${this.camera.id}">
                    ${this.renderVideoContent()}
                </div>
                ${this.renderStreamOverlay()}
                ${this.renderStreamStatus()}
            </div>
        `;
    }

    renderVideoContent() {
        if (this.camera.status !== 'online') {
            return this.renderOfflineState();
        }

        if (this.streamState === 'streaming') {
            return `
                <img src="/stream/video/${this.camera.id}?t=${Date.now()}" 
                     class="live-stream" 
                     alt="Live feed from ${this.camera.name}"
                     onload="this.classList.add('loaded')"
                     onerror="this.classList.add('error')">
            `;
        }

        return `
            <div class="stream-placeholder">
                <i class="fas fa-video"></i>
                <span>Starting stream...</span>
            </div>
        `;
    }

    renderOfflineState() {
        const stateConfigs = {
            offline: {
                icon: 'fa-exclamation-triangle',
                message: 'Camera Offline',
                class: 'offline'
            },
            warning: {
                icon: 'fa-exclamation-circle', 
                message: 'Connection Issues',
                class: 'warning'
            }
        };

        const config = stateConfigs[this.camera.status] || stateConfigs.offline;

        return `
            <div class="camera-offline ${config.class}">
                <i class="fas ${config.icon}"></i>
                <span>${config.message}</span>
            </div>
        `;
    }

    renderStreamOverlay() {
        if (this.camera.status !== 'online') return '';

        const config = this.getContextConfig();
        const controls = config.controls.map(control => 
            `<button class="control-btn" data-action="${control}" title="${control}">
                <i class="fas ${this.getControlIcon(control)}"></i>
            </button>`
        ).join('');

        return `
            <div class="stream-overlay">
                <div class="stream-info">
                    <div class="live-indicator ${this.streamState === 'streaming' ? 'active' : 'inactive'}">
                        <span class="live-dot"></span>
                        ${this.streamState === 'streaming' ? 'LIVE' : 'OFFLINE'}
                    </div>
                    ${this.options.context === 'management' ? 
                        `<div class="stream-quality">${this.camera.resolution || '640×480'}</div>` : 
                        ''
                    }
                </div>
                <div class="stream-controls">
                    ${controls}
                </div>
            </div>
        `;
    }

    renderStreamStatus() {
        return `
            <div class="stream-status-bar">
                <span class="stream-status-text" id="status-${this.camera.id}">
                    ${this.getStatusText()}
                </span>
                ${this.streamState === 'streaming' ? 
                    `<span class="stream-duration" id="duration-${this.camera.id}">00:00</span>` : 
                    ''
                }
            </div>
        `;
    }

    renderInfo() {
        const config = this.getContextConfig();
        
        if (config.infoType === 'compact') {
            return this.renderCompactInfo();
        } else {
            return this.renderDetailedInfo();
        }
    }

    renderCompactInfo() {
        return `
            <div class="camera-info camera-info--compact">
                <div class="camera-identity">
                    <span class="camera-name">${this.camera.name}</span>
                    <span class="camera-location">${this.camera.location || 'Unknown'}</span>
                </div>
                <div class="camera-status">
                    <div class="status-indicator ${this.camera.status}">
                        <i class="fas fa-circle"></i>
                    </div>
                </div>
            </div>
        `;
    }

    renderDetailedInfo() {
        return `
            <div class="camera-info camera-info--detailed">
                <div class="info-grid">
                    <div class="info-row">
                        <span class="info-label">Location:</span>
                        <span class="info-value">${this.camera.location || 'Not specified'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Status:</span>
                        <span class="info-value status-${this.camera.status}">
                            ${this.capitalizeFirst(this.camera.status)}
                        </span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">IP Address:</span>
                        <span class="info-value">${this.camera.ip_address}:${this.camera.port}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Resolution:</span>
                        <span class="info-value">${this.camera.resolution || '640×480'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Health:</span>
                        <span class="info-value">
                            <div class="health-bar">
                                <div class="health-fill" style="width: ${this.getHealthScore()}%"></div>
                            </div>
                            ${this.getHealthScore()}%
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    renderActions() {
        return `
            <div class="camera-actions-bar">
                <button class="btn btn-primary" data-action="configure">
                    <i class="fas fa-cog"></i>
                    Configure
                </button>
                <button class="btn btn-secondary" data-action="test-connection">
                    <i class="fas fa-network-wired"></i>
                    Test
                </button>
                <button class="btn btn-danger" data-action="delete">
                    <i class="fas fa-trash"></i>
                    Delete
                </button>
            </div>
        `;
    }

    // Event handling and stream management methods
    attachEventListeners() {
        const card = this.container.querySelector('.camera-card');
        
        // Control button handlers
        card.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]') || e.target.parentElement.matches('[data-action]')) {
                const action = e.target.dataset.action || e.target.parentElement.dataset.action;
                this.handleAction(action, e);
            }
        });

        // Stream status updates
        window.addEventListener('streamStatusUpdate', (e) => {
            if (e.detail.cameraId === this.camera.id) {
                this.updateStreamState(e.detail.status);
            }
        });
    }

    async handleAction(action, event) {
        event.preventDefault();
        event.stopPropagation();

        switch (action) {
            case 'fullscreen':
                this.openFullscreen();
                break;
            case 'capture':
                await this.captureFrame();
                break;
            case 'configure':
                this.openConfigModal();
                break;
            case 'diagnostics':
                this.openDiagnostics();
                break;
            case 'test-connection':
                await this.testConnection();
                break;
            case 'delete':
                this.confirmDelete();
                break;
            default:
                console.warn(`Unknown action: ${action}`);
        }
    }

    async startAutoStream() {
        if (this.camera.status !== 'online') return;

        try {
            this.updateStreamState('connecting');
            
            await this.streamManager.startStream(this.camera.id, {
                quality: 'medium',
                autoReconnect: true
            });
            
            this.updateStreamState('streaming');
            this.startStreamTimer();
            
        } catch (error) {
            console.error('Auto-stream failed:', error);
            this.updateStreamState('error');
        }
    }

    updateStreamState(newState) {
        this.streamState = newState;
        
        // Update video content
        const videoContainer = this.container.querySelector(`#video-${this.camera.id}`);
        if (videoContainer) {
            videoContainer.innerHTML = this.renderVideoContent();
        }

        // Update overlay
        const overlay = this.container.querySelector('.stream-overlay');
        if (overlay) {
            overlay.innerHTML = this.renderStreamOverlay().replace(/<div class="stream-overlay">|<\/div>$/g, '');
        }

        // Update status bar
        const statusBar = this.container.querySelector('.stream-status-bar');
        if (statusBar) {
            statusBar.innerHTML = this.renderStreamStatus().replace(/<div class="stream-status-bar">|<\/div>$/g, '');
        }
    }

    startStreamTimer() {
        const startTime = Date.now();
        const durationElement = this.container.querySelector(`#duration-${this.camera.id}`);
        
        if (!durationElement) return;

        const timer = setInterval(() => {
            if (this.streamState !== 'streaming') {
                clearInterval(timer);
                return;
            }

            const elapsed = Date.now() - startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            durationElement.textContent = display;
        }, 1000);
    }

    // Utility methods
    getControlIcon(control) {
        const icons = {
            fullscreen: 'fa-expand',
            capture: 'fa-camera',
            record: 'fa-record-vinyl',
            settings: 'fa-cog'
        };
        return icons[control] || 'fa-circle';
    }

    getStatusText() {
        const statusTexts = {
            streaming: 'Live streaming',
            connecting: 'Connecting...',
            error: 'Connection failed',
            disconnected: 'Not streaming'
        };
        return statusTexts[this.streamState] || 'Unknown status';
    }

    getHealthScore() {
        // Calculate health score based on status, uptime, etc.
        const baseScore = this.camera.status === 'online' ? 85 : 
                         this.camera.status === 'warning' ? 60 : 25;
        return baseScore + Math.floor(Math.random() * 15);
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    // Action implementations
    openFullscreen() {
        // Implementation for fullscreen view
        console.log(`Opening fullscreen for camera ${this.camera.id}`);
    }

    async captureFrame() {
        // Implementation for frame capture
        console.log(`Capturing frame from camera ${this.camera.id}`);
    }

    openConfigModal() {
        // Implementation for configuration modal
        console.log(`Opening config for camera ${this.camera.id}`);
    }

    openDiagnostics() {
        // Implementation for diagnostics
        console.log(`Opening diagnostics for camera ${this.camera.id}`);
    }

    async testConnection() {
        // Implementation for connection testing
        console.log(`Testing connection for camera ${this.camera.id}`);
    }

    confirmDelete() {
        // Implementation for delete confirmation
        console.log(`Delete requested for camera ${this.camera.id}`);
    }

    // Cleanup
    destroy() {
        if (this.streamState === 'streaming') {
            this.streamManager.stopStream(this.camera.id);
        }
        
        // Remove event listeners
        const card = this.container.querySelector('.camera-card');
        if (card) {
            card.remove();
        }
    }
}

// Export for use in other modules
window.CameraCard = CameraCard;
```

### 2. StreamManager Service

```javascript
// src/components/camera/StreamManager.js
class StreamManager {
    constructor() {
        this.activeStreams = new Map();
        this.streamStates = new Map();
        this.reconnectAttempts = new Map();
        this.maxReconnectAttempts = 5;
        this.healthCheckInterval = 10000; // 10 seconds
    }

    async startStream(cameraId, options = {}) {
        try {
            const response = await fetch(`/api/v1/streams/start/${cameraId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    quality: options.quality || 'medium',
                    max_fps: options.maxFps || 30,
                    auto_reconnect: options.autoReconnect || true
                })
            });

            if (!response.ok) {
                throw new Error(`Stream start failed: ${response.status}`);
            }

            const result = await response.json();
            
            this.streamStates.set(cameraId, 'streaming');
            this.activeStreams.set(cameraId, Date.now());
            this.reconnectAttempts.set(cameraId, 0);
            
            if (options.autoReconnect) {
                this.startHealthMonitoring(cameraId);
            }

            this.broadcastUpdate(cameraId, 'streaming');
            return result;

        } catch (error) {
            this.streamStates.set(cameraId, 'error');
            this.broadcastUpdate(cameraId, 'error');
            throw error;
        }
    }

    async stopStream(cameraId) {
        try {
            const response = await fetch(`/api/v1/streams/stop/${cameraId}`, {
                method: 'POST'
            });

            if (response.ok) {
                this.cleanup(cameraId);
                this.broadcastUpdate(cameraId, 'disconnected');
            }

        } catch (error) {
            console.error(`Failed to stop stream ${cameraId}:`, error);
        }
    }

    startHealthMonitoring(cameraId) {
        const healthTimer = setInterval(async () => {
            const isHealthy = await this.checkStreamHealth(cameraId);
            
            if (!isHealthy) {
                clearInterval(healthTimer);
                await this.handleStreamFailure(cameraId);
            }
        }, this.healthCheckInterval);

        this.activeStreams.set(`${cameraId}_health`, healthTimer);
    }

    async checkStreamHealth(cameraId) {
        try {
            const response = await fetch(`/api/v1/streams/status/${cameraId}`);
            const data = await response.json();
            return data.status === 'active';
        } catch (error) {
            return false;
        }
    }

    async handleStreamFailure(cameraId) {
        const attempts = this.reconnectAttempts.get(cameraId) || 0;
        
        if (attempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(cameraId);
        } else {
            this.streamStates.set(cameraId, 'failed');
            this.broadcastUpdate(cameraId, 'failed');
            console.error(`Stream permanently failed for camera ${cameraId}`);
        }
    }

    scheduleReconnect(cameraId) {
        const attempts = this.reconnectAttempts.get(cameraId) || 0;
        const delay = 2000 * Math.pow(2, attempts); // Exponential backoff
        
        this.streamStates.set(cameraId, 'reconnecting');
        this.broadcastUpdate(cameraId, 'reconnecting');
        
        setTimeout(async () => {
            this.reconnectAttempts.set(cameraId, attempts + 1);
            try {
                await this.startStream(cameraId, { autoReconnect: true });
            } catch (error) {
                console.error(`Reconnect failed for camera ${cameraId}:`, error);
            }
        }, delay);
    }

    broadcastUpdate(cameraId, status) {
        window.dispatchEvent(new CustomEvent('streamStatusUpdate', {
            detail: { cameraId, status }
        }));
    }

    cleanup(cameraId) {
        // Clear health monitoring
        const healthTimer = this.activeStreams.get(`${cameraId}_health`);
        if (healthTimer) {
            clearInterval(healthTimer);
            this.activeStreams.delete(`${cameraId}_health`);
        }

        // Clear stream data
        this.activeStreams.delete(cameraId);
        this.streamStates.delete(cameraId);
        this.reconnectAttempts.delete(cameraId);
    }

    getStreamState(cameraId) {
        return this.streamStates.get(cameraId) || 'disconnected';
    }

    isStreaming(cameraId) {
        return this.streamStates.get(cameraId) === 'streaming';
    }
}

// Global instance
window.globalStreamManager = new StreamManager();
```

## 📱 Usage Examples

### Dashboard Implementation

```javascript
// In Dashboard.js
class Dashboard {
    constructor() {
        this.cameraCards = new Map();
    }

    async loadLiveCameraFeeds() {
        try {
            const response = await fetch('/api/v1/cameras/');
            const data = await response.json();
            
            const onlineCameras = data.cameras
                .filter(camera => camera.status === 'online')
                .slice(0, 4); // Dashboard shows max 4 cameras

            this.renderCameraGrid(onlineCameras);
            
        } catch (error) {
            console.error('Failed to load cameras:', error);
        }
    }

    renderCameraGrid(cameras) {
        const container = document.getElementById('live-camera-grid');
        container.innerHTML = '';

        cameras.forEach(camera => {
            const cardContainer = document.createElement('div');
            cardContainer.className = 'camera-card-container';
            container.appendChild(cardContainer);

            const cameraCard = new CameraCard(cardContainer, camera, {
                context: 'dashboard',
                autoStream: true,
                showControls: true,
                showInfo: true
            });

            this.cameraCards.set(camera.id, cameraCard);
        });
    }

    destroy() {
        this.cameraCards.forEach(card => card.destroy());
        this.cameraCards.clear();
    }
}
```

### Cameras Page Implementation

```javascript
// In CamerasPage.js
class CamerasPage {
    constructor() {
        this.cameraCards = new Map();
        this.cameras = [];
    }

    async loadCameras() {
        try {
            const response = await fetch('/api/v1/cameras/');
            const data = await response.json();
            
            this.cameras = data.cameras;
            this.renderCameraGrid();
            
        } catch (error) {
            console.error('Failed to load cameras:', error);
        }
    }

    renderCameraGrid() {
        const container = document.getElementById('cameras-grid');
        container.innerHTML = '';

        this.cameras.forEach(camera => {
            const cardContainer = document.createElement('div');
            cardContainer.className = 'camera-card-container';
            container.appendChild(cardContainer);

            const cameraCard = new CameraCard(cardContainer, camera, {
                context: 'management',
                autoStream: true,
                showControls: true,
                showInfo: true
            });

            this.cameraCards.set(camera.id, cameraCard);
        });
    }

    destroy() {
        this.cameraCards.forEach(card => card.destroy());
        this.cameraCards.clear();
    }
}
```

## 🎨 CSS Styling Structure

### Base Camera Card Styles

```css
/* src/components/camera/styles/CameraCard.css */

.camera-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    overflow: hidden;
    transition: all 0.3s ease;
    position: relative;
}

.camera-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

/* Header */
.camera-header {
    padding: 16px 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.camera-title h4 {
    margin: 0;
    font-size: 16px;
    color: #212529;
}

.camera-id {
    font-size: 12px;
    color: #6c757d;
}

.camera-actions {
    display: flex;
    gap: 8px;
}

.action-btn {
    width: 32px;
    height: 32px;
    border: none;
    background: #f8f9fa;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.action-btn:hover {
    background: #e9ecef;
    color: #007bff;
}

/* Video Container */
.camera-video {
    position: relative;
    background: #000;
    overflow: hidden;
}

.video-container {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.live-stream {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: opacity 0.3s;
}

.live-stream.loaded {
    opacity: 1;
}

.live-stream.error {
    opacity: 0.5;
}

.stream-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    color: #6c757d;
}

.stream-placeholder i {
    font-size: 32px;
}

/* Camera Offline States */
.camera-offline {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    color: white;
    height: 100%;
    justify-content: center;
}

.camera-offline.offline {
    background: linear-gradient(135deg, #6c757d, #495057);
}

.camera-offline.warning {
    background: linear-gradient(135deg, #ffc107, #e0a800);
    color: #212529;
}

.camera-offline i {
    font-size: 32px;
}

/* Stream Overlay */
.stream-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.3);
    opacity: 0;
    transition: opacity 0.2s;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 12px;
}

.camera-video:hover .stream-overlay {
    opacity: 1;
}

.stream-info {
    display: flex;
    flex-direction: column;
    gap: 6px;
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

.live-indicator.inactive {
    background: rgba(108, 117, 125, 0.9);
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

.stream-quality {
    background: rgba(0,0,0,0.7);
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
}

.stream-controls {
    display: flex;
    gap: 8px;
}

.control-btn {
    width: 36px;
    height: 36px;
    background: rgba(255,255,255,0.9);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.control-btn:hover {
    background: white;
    transform: scale(1.1);
}

/* Stream Status Bar */
.stream-status-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.8));
    padding: 8px 12px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: white;
}

/* Info Sections */
.camera-info {
    padding: 16px 20px;
}

.camera-info--compact {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.camera-identity {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.camera-name {
    font-weight: 600;
    color: #212529;
}

.camera-location {
    font-size: 12px;
    color: #6c757d;
}

.camera-status {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
}

.status-indicator.online { color: #28a745; }
.status-indicator.offline { color: #dc3545; }
.status-indicator.warning { color: #ffc107; }

/* Detailed Info */
.camera-info--detailed .info-grid {
    display: grid;
    gap: 12px;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f1f3f4;
}

.info-row:last-child {
    border-bottom: none;
}

.info-label {
    font-weight: 500;
    color: #495057;
}

.info-value {
    color: #212529;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Health Bar */
.health-bar {
    width: 60px;
    height: 6px;
    background: #e9ecef;
    border-radius: 3px;
    overflow: hidden;
}

.health-fill {
    height: 100%;
    background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
    transition: width 0.3s;
}

/* Actions Bar */
.camera-actions-bar {
    padding: 16px 20px;
    background: #f8f9fa;
    border-top: 1px solid #e9ecef;
    display: flex;
    gap: 12px;
}

.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-primary:hover {
    background: #0056b3;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-secondary:hover {
    background: #545b62;
}

.btn-danger {
    background: #dc3545;
    color: white;
}

.btn-danger:hover {
    background: #c82333;
}
```

### Context-Specific Variants

```css
/* src/components/camera/styles/CameraVariants.css */

/* Dashboard Variants */
.camera-card--dashboard {
    height: 240px;
}

.camera-card--dashboard .camera-video {
    height: 180px;
}

.camera-card--dashboard .camera-info {
    height: 60px;
    padding: 12px 16px;
}

/* Management Variants */
.camera-card--management {
    min-height: 420px;
}

.camera-card--management .camera-video {
    height: 200px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .camera-card--dashboard {
        height: 200px;
    }
    
    .camera-card--dashboard .camera-video {
        height: 140px;
    }
    
    .camera-card--management {
        min-height: 360px;
    }
    
    .stream-controls {
        gap: 6px;
    }
    
    .control-btn {
        width: 32px;
        height: 32px;
    }
}
```

## ✅ Integration Checklist

### Phase 1: Component Creation
- [ ] Create CameraCard main component
- [ ] Implement StreamManager service
- [ ] Add context-aware rendering
- [ ] Create base CSS styling

### Phase 2: Dashboard Integration  
- [ ] Replace existing dashboard feeds
- [ ] Test auto-streaming functionality
- [ ] Verify responsive grid layout
- [ ] Test multiple camera performance

### Phase 3: Cameras Page Integration
- [ ] Update cameras page implementation
- [ ] Test detailed info display
- [ ] Verify management actions work
- [ ] Test configuration modal integration

### Phase 4: Testing & Polish
- [ ] Cross-browser compatibility testing
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Documentation updates

This shared component approach ensures consistency while allowing each page to serve its specific purpose effectively.