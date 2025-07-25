/**
 * LiveVideoPlayer Component
 * Reusable video streaming component for camera feeds
 */

class LiveVideoPlayer {
    constructor(options = {}) {
        this.cameraId = options.cameraId;
        this.camera = options.camera;
        this.autoStart = options.autoStart || false;
        this.showControls = options.showControls !== false; // Default true
        this.className = options.className || '';
        this.onStatusChange = options.onStatusChange || (() => {});
        this.onError = options.onError || (() => {});
        this.onStreamStart = options.onStreamStart || (() => {});
        this.onStreamStop = options.onStreamStop || (() => {});
        
        this.isStreaming = false;
        this.isLoading = false;
        this.streamStartTime = null;
        this.durationTimer = null;
        this.statusCheckInterval = null;
        this.containerId = `live-player-${this.cameraId}-${Date.now()}`;
        
        this.apiBase = 'http://localhost:8001';
    }

    render() {
        const containerClass = `live-video-player ${this.className}`.trim();
        
        return `
            <div class="live-video-container ${containerClass}" id="${this.containerId}" data-camera-id="${this.cameraId}">
                ${this.renderVideoContent()}
                ${this.showControls ? this.renderControls() : ''}
                ${this.renderStatusBar()}
                ${this.renderLoadingOverlay()}
            </div>
        `;
    }

    renderVideoContent() {
        if (this.isStreaming) {
            return `
                <div class="video-stream-wrapper">
                    <img src="${this.apiBase}/stream/video/${this.cameraId}?t=${Date.now()}" 
                         alt="Live stream from ${this.camera?.name || 'Camera'}"
                         class="live-stream-video"
                         onload="window.liveVideoPlayers?.get('${this.containerId}')?.handleStreamLoad()"
                         onerror="window.liveVideoPlayers?.get('${this.containerId}')?.handleStreamError()">
                    <div class="stream-overlay">
                        <div class="live-indicator">
                            <span class="live-dot"></span>
                            LIVE
                        </div>
                        <div class="stream-info">
                            <span class="stream-duration" id="duration-${this.containerId}">00:00</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // Show thumbnail when not streaming
        return `
            <div class="video-thumbnail-wrapper">
                <img src="${this.apiBase}/stream/thumbnail/${this.cameraId}?t=${Date.now()}" 
                     alt="Preview from ${this.camera?.name || 'Camera'}"
                     class="thumbnail-image"
                     onload="this.parentElement.classList.add('loaded'); this.parentElement.classList.remove('no-thumbnail')"
                     onerror="this.style.display='none'; this.parentElement.classList.add('no-thumbnail')">
                <div class="thumbnail-placeholder">
                    <i class="fas fa-camera"></i>
                    <span>No Preview Available</span>
                    <small>Click to start streaming</small>
                </div>
                <div class="thumbnail-overlay">
                    <div class="play-indicator">
                        <i class="fas fa-play"></i>
                    </div>
                    <div class="thumbnail-info">
                        <span class="capture-time">
                            Updated: ${new Date().toLocaleTimeString()}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    renderControls() {
        // Only render controls when explicitly enabled
        if (!this.showControls) return '';

        const isOnline = this.camera?.status === 'online';
        
        return `
            <div class="video-controls" style="display: none;">
                <div class="control-buttons">
                    ${this.isStreaming ? `
                        <button class="control-btn stop-btn" data-action="stop" title="Stop Stream">
                            <i class="fas fa-stop"></i>
                        </button>
                        <button class="control-btn fullscreen-btn" data-action="fullscreen" title="Fullscreen">
                            <i class="fas fa-expand"></i>
                        </button>
                        <button class="control-btn capture-btn" data-action="capture" title="Capture Frame">
                            <i class="fas fa-camera"></i>
                        </button>
                    ` : `
                        <button class="control-btn play-btn" data-action="start" title="Start Stream" ${!isOnline ? 'disabled' : ''}>
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="control-btn refresh-btn" data-action="refresh" title="Refresh Thumbnail">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    `}
                </div>
            </div>
        `;
    }

    renderStatusBar() {
        const statusClass = this.isStreaming ? 'streaming' : (this.camera?.status || 'unknown');
        
        return `
            <div class="video-status-bar ${statusClass}">
                <div class="status-left">
                    <span class="status-indicator">
                        <i class="fas ${this.getStatusIcon()}"></i>
                        ${this.getStatusText()}
                    </span>
                </div>
                <div class="status-right">
                    ${this.isStreaming ? `
                        <span class="stream-quality">720p</span>
                        <span class="stream-fps">30 FPS</span>
                    ` : `
                        <span class="last-update">
                            ${this.camera?.lastSeen ? this.getRelativeTime(new Date(this.camera.lastSeen)) : 'Unknown'}
                        </span>
                    `}
                </div>
            </div>
        `;
    }

    renderLoadingOverlay() {
        return `
            <div class="loading-overlay" style="display: none;">
                <div class="loading-content">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span class="loading-text">Connecting...</span>
                </div>
            </div>
        `;
    }

    // Initialization and Event Handling
    init() {
        // Store instance reference for global access
        if (!window.liveVideoPlayers) {
            window.liveVideoPlayers = new Map();
        }
        window.liveVideoPlayers.set(this.containerId, this);

        // Attach event listeners
        this.attachEventListeners();

        // Auto-start if requested
        if (this.autoStart && this.camera?.status === 'online') {
            setTimeout(() => this.startStream(), 500);
        }

        // Show controls on hover
        this.setupHoverEffects();

        return this;
    }

    attachEventListeners() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // Control button handlers
        container.addEventListener('click', (e) => {
            const action = e.target.dataset.action || e.target.parentElement?.dataset.action;
            if (action) {
                e.stopPropagation();
                this.handleControlAction(action);
            }
        });

        // Play overlay click handler
        const playIndicator = container.querySelector('.play-indicator');
        if (playIndicator) {
            playIndicator.addEventListener('click', () => this.startStream());
        }
    }

    setupHoverEffects() {
        const container = document.getElementById(this.containerId);
        
        // Skip hover effects completely when controls are disabled
        if (!container || !this.showControls) return;

        const controls = container.querySelector('.video-controls');
        if (!controls) return;

        container.addEventListener('mouseenter', () => {
            controls.style.display = 'block';
        });

        container.addEventListener('mouseleave', () => {
            controls.style.display = 'none';
        });
    }

    // Stream Control Methods
    async startStream() {
        if (this.isStreaming || this.isLoading) {
            return;
        }

        // Validate camera is online before starting stream
        if (this.camera?.status !== 'online') {
            this.onError(`Cannot start stream: Camera is ${this.camera?.status || 'offline'}`);
            return;
        }

        this.isLoading = true;
        this.showLoading('Starting stream...');
        this.onStatusChange('starting');

        try {
            // Check if backend is available before attempting stream
            const healthCheck = await this.checkBackendConnection();
            if (!healthCheck) {
                throw new Error('Backend service unavailable');
            }

            // Check if stream is already active on backend
            const statusResponse = await fetch(`${this.apiBase}/api/v1/streams/status/${this.cameraId}`);
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                if (statusData.status === 'active') {
                    console.log(`Stream already active for camera ${this.cameraId}, updating local state`);
                    this.isStreaming = true;
                    this.streamStartTime = Date.now();
                    this.updateVideoContent();
                    this.updateControls();
                    this.updateStatusBar();
                    this.startDurationTimer();
                    this.hideLoading();
                    this.onStatusChange('streaming');
                    this.onStreamStart({ message: 'Stream was already active' });
                    return;
                }
            }

            const response = await fetch(`${this.apiBase}/api/v1/streams/start/${this.cameraId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    quality: 'medium',
                    max_fps: 30,
                    detection_enabled: false
                }),
                timeout: 15000 // 15 second timeout
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Connection failed' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            
            // Update state
            this.isStreaming = true;
            this.streamStartTime = Date.now();
            
            // Update UI
            this.updateVideoContent();
            this.updateControls();
            this.updateStatusBar();
            this.startDurationTimer();
            
            // Start status monitoring
            this.startStatusMonitoring();
            
            this.hideLoading();
            this.onStatusChange('streaming');
            this.onStreamStart(result);
            
        } catch (error) {
            console.error('Failed to start stream:', error);
            this.hideLoading();
            this.onError('Failed to start stream: ' + error.message);
            this.onStatusChange('error');
        } finally {
            this.isLoading = false;
        }
    }

    async stopStream() {
        if (!this.isStreaming || this.isLoading) {
            return;
        }

        this.isLoading = true;
        this.showLoading('Stopping stream...');
        this.onStatusChange('stopping');

        try {
            const response = await fetch(`${this.apiBase}/api/v1/streams/stop/${this.cameraId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout: 10000 // 10 second timeout
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            
            // Update state
            this.isStreaming = false;
            this.streamStartTime = null;
            
            // Cleanup timers
            this.stopDurationTimer();
            this.stopStatusMonitoring();
            
            // Update UI
            this.updateVideoContent();
            this.updateControls();
            this.updateStatusBar();
            
            this.hideLoading();
            this.onStatusChange('stopped');
            this.onStreamStop(result);
            
        } catch (error) {
            console.error('Failed to stop stream:', error);
            this.hideLoading();
            this.onError('Failed to stop stream: ' + error.message);
            this.onStatusChange('error');
        } finally {
            this.isLoading = false;
        }
    }

    async refreshThumbnail() {
        const thumbnail = document.querySelector(`#${this.containerId} .thumbnail-image`);
        if (thumbnail) {
            const refreshBtn = document.querySelector(`#${this.containerId} .refresh-btn i`);
            if (refreshBtn) {
                refreshBtn.classList.add('fa-spin');
                setTimeout(() => refreshBtn.classList.remove('fa-spin'), 1000);
            }
            
            thumbnail.src = `${this.apiBase}/stream/thumbnail/${this.cameraId}?t=${Date.now()}`;
        }
    }

    async captureFrame() {
        try {
            const captureUrl = `${this.apiBase}/stream/thumbnail/${this.cameraId}?t=${Date.now()}`;
            
            const link = document.createElement('a');
            link.href = captureUrl;
            link.download = `${this.camera?.name?.replace(/\s+/g, '_') || 'camera'}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.jpg`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
        } catch (error) {
            console.error('Failed to capture frame:', error);
            this.onError('Failed to capture frame');
        }
    }

    async openFullscreen() {
        // Start streaming if not already active
        if (!this.isStreaming) {
            try {
                await this.startStream();
                // Wait a moment for stream to initialize
                await new Promise(resolve => setTimeout(resolve, 1500));
            } catch (error) {
                this.onError('Failed to start stream for fullscreen view');
                return;
            }
        }

        const modal = document.createElement('div');
        modal.className = 'fullscreen-video-modal';
        modal.innerHTML = `
            <div class="fullscreen-content">
                <div class="fullscreen-header">
                    <h3>${this.camera?.name || 'Camera'} - Live Stream</h3>
                    <button class="close-fullscreen">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="fullscreen-video">
                    <div class="fullscreen-loading" id="fullscreen-loading-${this.cameraId}">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Loading stream...</span>
                    </div>
                    <img src="${this.apiBase}/stream/video/${this.cameraId}?t=${Date.now()}" 
                         alt="Fullscreen view" 
                         class="fullscreen-stream"
                         style="display: none;"
                         onload="this.style.display='block'; document.getElementById('fullscreen-loading-${this.cameraId}')?.remove();"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="fullscreen-error" style="display: none; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: white;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 16px; color: #ffc107;"></i>
                        <h4>Stream Not Available</h4>
                        <p>Unable to load video stream. The camera may be offline or the stream endpoint is not responding.</p>
                        <button class="btn btn-primary" onclick="location.reload()" style="margin-top: 16px;">
                            <i class="fas fa-refresh"></i>
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'flex';

        // Event handlers
        modal.querySelector('.close-fullscreen').addEventListener('click', () => modal.remove());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Add timeout for loading state
        setTimeout(() => {
            const loadingElement = document.getElementById(`fullscreen-loading-${this.cameraId}`);
            if (loadingElement) {
                loadingElement.remove();
                const errorElement = modal.querySelector('.fullscreen-error');
                if (errorElement) {
                    errorElement.style.display = 'flex';
                }
            }
        }, 10000); // 10 second timeout
    }

    // Control Action Handler
    handleControlAction(action) {
        switch (action) {
            case 'start':
                this.startStream();
                break;
            case 'stop':
                this.stopStream();
                break;
            case 'refresh':
                this.refreshThumbnail();
                break;
            case 'capture':
                this.captureFrame();
                break;
            case 'fullscreen':
                this.openFullscreen();
                break;
        }
    }

    // UI Update Methods
    updateVideoContent() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const wrapper = container.querySelector('.video-stream-wrapper, .video-thumbnail-wrapper');
        if (wrapper) {
            wrapper.outerHTML = this.renderVideoContent();
        }
    }

    updateControls() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // If controls are disabled, ensure no controls are present
        if (!this.showControls) {
            const controls = container.querySelector('.video-controls');
            if (controls) {
                controls.remove();
            }
            return;
        }

        const controls = container.querySelector('.video-controls');
        if (controls) {
            controls.innerHTML = this.renderControls().match(/<div class="video-controls"[^>]*>(.*?)<\/div>/s)?.[1] || '';
        }
    }

    updateStatusBar() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const statusBar = container.querySelector('.video-status-bar');
        if (statusBar) {
            statusBar.outerHTML = this.renderStatusBar();
        }
    }

    // Timer and Monitoring
    startDurationTimer() {
        if (this.durationTimer) {
            clearInterval(this.durationTimer);
        }

        this.durationTimer = setInterval(() => {
            if (this.streamStartTime) {
                const elapsed = Date.now() - this.streamStartTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                const durationElement = document.getElementById(`duration-${this.containerId}`);
                if (durationElement) {
                    durationElement.textContent = display;
                }
            }
        }, 1000);
    }

    stopDurationTimer() {
        if (this.durationTimer) {
            clearInterval(this.durationTimer);
            this.durationTimer = null;
        }
    }

    startStatusMonitoring() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }

        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBase}/api/v1/streams/status/${this.cameraId}`);
                const data = await response.json();
                
                if (data.status !== 'active' && this.isStreaming) {
                    // Stream was stopped externally
                    this.isStreaming = false;
                    this.streamStartTime = null;
                    this.stopDurationTimer();
                    this.updateVideoContent();
                    this.updateControls();
                    this.updateStatusBar();
                    this.onStatusChange('stopped');
                }
            } catch (error) {
                console.error('Status check failed:', error);
            }
        }, 10000); // Check every 10 seconds
    }

    stopStatusMonitoring() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    // Loading Overlay
    showLoading(text = 'Loading...') {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const overlay = container.querySelector('.loading-overlay');
        const loadingText = container.querySelector('.loading-text');
        
        if (overlay) {
            overlay.style.display = 'flex';
        }
        if (loadingText) {
            loadingText.textContent = text;
        }
    }

    hideLoading() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const overlay = container.querySelector('.loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    // Stream Event Handlers
    handleStreamLoad() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.classList.add('stream-active');
        }
    }

    handleStreamError() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.classList.add('stream-error');
        }
        this.onError('Stream connection lost');
    }

    // Backend Connection Check
    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.apiBase}/health`, {
                method: 'GET',
                timeout: 5000 // Quick health check
            });
            return response.ok;
        } catch (error) {
            console.warn('Backend health check failed:', error.message);
            return false;
        }
    }

    // Utility Methods
    getStatusIcon() {
        if (this.isStreaming) return 'fa-circle text-success';
        
        const statusIcons = {
            online: 'fa-circle text-success',
            offline: 'fa-times-circle text-danger',
            warning: 'fa-exclamation-triangle text-warning'
        };
        return statusIcons[this.camera?.status] || 'fa-question-circle text-muted';
    }

    getStatusText() {
        if (this.isStreaming) return 'Streaming';
        return this.camera?.status ? this.capitalizeFirst(this.camera.status) : 'Unknown';
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    getRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
        return `${Math.floor(minutes / 1440)}d ago`;
    }

    // Cleanup
    destroy() {
        // Stop streaming if active
        if (this.isStreaming) {
            this.stopStream();
        }

        // Clear timers
        this.stopDurationTimer();
        this.stopStatusMonitoring();

        // Remove from global registry
        if (window.liveVideoPlayers) {
            window.liveVideoPlayers.delete(this.containerId);
        }

        // Remove event listeners
        const container = document.getElementById(this.containerId);
        if (container) {
            container.replaceWith(container.cloneNode(true));
        }
    }

    // Static factory method
    static create(options) {
        const player = new LiveVideoPlayer(options);
        return player;
    }

    // Static method to get player instance
    static getInstance(containerId) {
        return window.liveVideoPlayers?.get(containerId);
    }
}

export default LiveVideoPlayer;