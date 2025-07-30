// LiveVideoPlayer.js - Fixed version with proper state management and cleanup

export class LiveVideoPlayer {
    constructor(options) {
        this.cameraId = options.cameraId;
        this.camera = options.camera;
        this.autoStart = options.autoStart ?? false;
        this.showControls = options.showControls ?? true;
        this.className = options.className || 'live-video-player';
        this.onStatusChange = options.onStatusChange || (() => {});
        this.onError = options.onError || (() => {});
        this.onStreamStart = options.onStreamStart || (() => {});
        this.onStreamStop = options.onStreamStop || (() => {});
        
        // State management
        this.isStreaming = false;
        this.streamStartTime = null;
        this.durationTimer = null;
        this.container = null;
        this.videoElement = null;
        this.imageLoadTimeout = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.isDestroyed = false;
        
        // Bind methods
        this.handleImageLoad = this.handleImageLoad.bind(this);
        this.handleImageError = this.handleImageError.bind(this);
        this.cleanup = this.cleanup.bind(this);
    }
    
    async init(container) {
        if (this.isDestroyed) return;
        
        this.container = container;
        this.render();
        
        // Check initial status
        await this.checkStreamStatus();
        
        if (this.autoStart && this.camera?.status === 'online') {
            await this.startStream();
        }
    }
    
    render() {
        if (!this.container || this.isDestroyed) return;
        
        const aspectRatio = this.getAspectRatio();
        
        this.container.innerHTML = `
            <div class="${this.className}" data-camera-id="${this.cameraId}" style="position: relative; width: 100%; height: 100%;">
                <div class="video-wrapper" style="position: relative; width: 100%; height: 100%; background: #000; display: flex; align-items: center; justify-content: center;">
                    ${this.renderContent()}
                </div>
                ${this.showControls ? this.renderControls() : ''}
                ${this.renderStatusBar()}
            </div>
        `;
        
        this.attachEventListeners();
    }
    
    getAspectRatio() {
        // Maintain consistent aspect ratio based on container class
        if (this.className.includes('camera-card')) {
            return '16:9'; // Standard widescreen for card view
        }
        return '16:9'; // Default aspect ratio
    }
    
    renderContent() {
        if (!this.camera || this.camera.status === 'offline') {
            return `
                <div class="offline-indicator" style="text-align: center; color: #6c757d;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 10px; display: block;"></i>
                    <span style="font-size: 14px;">Camera Offline</span>
                </div>
            `;
        }
        
        if (this.isStreaming) {
            // Use a wrapper div to maintain aspect ratio
            return `
                <div class="stream-container" style="width: 100%; height: 100%; position: relative; overflow: hidden;">
                    <img id="stream-${this.cameraId}" 
                         src="/stream/video/${this.cameraId}?t=${Date.now()}" 
                         alt="Live stream"
                         style="width: 100%; height: 100%; object-fit: contain; display: block;"
                         crossorigin="anonymous">
                    <div class="stream-loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: none;">
                        <i class="fas fa-spinner fa-spin" style="font-size: 24px; color: white;"></i>
                    </div>
                </div>
            `;
        }
        
        // Thumbnail view
        return `
            <div class="thumbnail-container" style="width: 100%; height: 100%; position: relative;">
                <img src="/stream/thumbnail/${this.cameraId}?t=${Date.now()}" 
                     alt="Camera preview"
                     style="width: 100%; height: 100%; object-fit: contain;"
                     onerror="this.src='/images/camera-placeholder.jpg'">
                <div class="play-overlay" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                    <button class="play-btn" style="width: 60px; height: 60px; border-radius: 50%; background: rgba(0,0,0,0.7); border: 2px solid white; color: white; cursor: pointer;">
                        <i class="fas fa-play" style="font-size: 20px; margin-left: 3px;"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    renderControls() {
        return `
            <div class="video-controls" style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); display: flex; gap: 10px;">
                ${this.isStreaming ? `
                    <button class="control-btn stop-btn" title="Stop Stream">
                        <i class="fas fa-stop"></i>
                    </button>
                ` : `
                    <button class="control-btn play-btn" title="Start Stream">
                        <i class="fas fa-play"></i>
                    </button>
                `}
                <button class="control-btn fullscreen-btn" title="Fullscreen">
                    <i class="fas fa-expand"></i>
                </button>
            </div>
        `;
    }
    
    renderStatusBar() {
        return `
            <div class="status-bar" style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); padding: 5px 10px; border-radius: 4px; color: white; font-size: 12px;">
                ${this.isStreaming ? `
                    <span class="live-indicator" style="display: inline-flex; align-items: center; gap: 5px;">
                        <span style="width: 8px; height: 8px; background: #dc3545; border-radius: 50%; display: inline-block;"></span>
                        LIVE
                    </span>
                    <span class="duration" style="margin-left: 10px;">00:00</span>
                ` : ''}
            </div>
        `;
    }
    
    attachEventListeners() {
        if (this.isDestroyed) return;
        
        const player = this.container.querySelector(`.${this.className}`);
        if (!player) return;
        
        // Play button listeners
        const playBtn = player.querySelector('.play-btn');
        const playOverlay = player.querySelector('.play-overlay');
        
        if (playBtn) {
            playBtn.addEventListener('click', () => this.startStream());
        }
        if (playOverlay) {
            playOverlay.addEventListener('click', () => this.startStream());
        }
        
        // Control button listeners
        const stopBtn = player.querySelector('.stop-btn');
        const fullscreenBtn = player.querySelector('.fullscreen-btn');
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopStream());
        }
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }
        
        // Image load handlers for streaming
        if (this.isStreaming) {
            this.videoElement = player.querySelector(`#stream-${this.cameraId}`);
            if (this.videoElement) {
                this.videoElement.addEventListener('load', this.handleImageLoad);
                this.videoElement.addEventListener('error', this.handleImageError);
                
                // Set initial loading state
                this.setLoadingState(true);
            }
        }
    }
    
    handleImageLoad() {
        if (this.isDestroyed || !this.isStreaming) return;
        
        this.reconnectAttempts = 0;
        this.setLoadingState(false);
        
        // Clear any existing timeout
        if (this.imageLoadTimeout) {
            clearTimeout(this.imageLoadTimeout);
        }
        
        // Set up next frame load with slight delay to prevent overwhelming
        this.imageLoadTimeout = setTimeout(() => {
            if (this.isStreaming && this.videoElement && !this.isDestroyed) {
                this.videoElement.src = `/stream/video/${this.cameraId}?t=${Date.now()}`;
            }
        }, 100); // 10 FPS
    }
    
    handleImageError() {
        if (this.isDestroyed || !this.isStreaming) return;
        
        this.reconnectAttempts++;
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.onError(new Error('Failed to connect to stream'));
            this.stopStream();
            return;
        }
        
        // Retry with exponential backoff
        const retryDelay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 5000);
        setTimeout(() => {
            if (this.isStreaming && this.videoElement && !this.isDestroyed) {
                this.videoElement.src = `/stream/video/${this.cameraId}?t=${Date.now()}`;
            }
        }, retryDelay);
    }
    
    setLoadingState(loading) {
        const loadingEl = this.container?.querySelector('.stream-loading');
        if (loadingEl) {
            loadingEl.style.display = loading ? 'block' : 'none';
        }
    }
    
    async checkStreamStatus() {
        try {
            const response = await fetch(`/api/v1/streams/status/${this.cameraId}`);
            if (response.ok) {
                const data = await response.json();
                this.isStreaming = data.status === 'active';
                this.onStatusChange(data.status);
            }
        } catch (error) {
            console.error('Failed to check stream status:', error);
        }
    }
    
    async startStream() {
        if (this.isStreaming || this.isDestroyed) return;
        
        try {
            const response = await fetch(`/api/v1/streams/start/${this.cameraId}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to start stream');
            }
            
            this.isStreaming = true;
            this.streamStartTime = Date.now();
            this.startDurationTimer();
            this.render();
            this.onStreamStart();
            this.onStatusChange('active');
            
        } catch (error) {
            this.onError(error);
            console.error('Failed to start stream:', error);
        }
    }
    
    async stopStream() {
        if (!this.isStreaming || this.isDestroyed) return;
        
        // Clean up image loading first
        this.cleanup();
        
        try {
            const response = await fetch(`/api/v1/streams/stop/${this.cameraId}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to stop stream');
            }
            
            this.isStreaming = false;
            this.streamStartTime = null;
            this.stopDurationTimer();
            this.render();
            this.onStreamStop();
            this.onStatusChange('stopped');
            
        } catch (error) {
            this.onError(error);
            console.error('Failed to stop stream:', error);
        }
    }
    
    startDurationTimer() {
        this.stopDurationTimer();
        
        this.durationTimer = setInterval(() => {
            if (this.isDestroyed) {
                this.stopDurationTimer();
                return;
            }
            
            const duration = Math.floor((Date.now() - this.streamStartTime) / 1000);
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            const formatted = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            
            const durationEl = this.container?.querySelector('.duration');
            if (durationEl) {
                durationEl.textContent = formatted;
            }
        }, 1000);
    }
    
    stopDurationTimer() {
        if (this.durationTimer) {
            clearInterval(this.durationTimer);
            this.durationTimer = null;
        }
    }
    
    toggleFullscreen() {
        // Implementation for fullscreen
        const streamImg = this.container?.querySelector(`#stream-${this.cameraId}`);
        if (streamImg) {
            if (streamImg.requestFullscreen) {
                streamImg.requestFullscreen();
            }
        }
    }
    
    cleanup() {
        // Clear timeouts
        if (this.imageLoadTimeout) {
            clearTimeout(this.imageLoadTimeout);
            this.imageLoadTimeout = null;
        }
        
        // Remove event listeners
        if (this.videoElement) {
            this.videoElement.removeEventListener('load', this.handleImageLoad);
            this.videoElement.removeEventListener('error', this.handleImageError);
            this.videoElement = null;
        }
    }
    
    destroy() {
        this.isDestroyed = true;
        
        // Stop streaming if active
        if (this.isStreaming) {
            this.stopStream();
        }
        
        // Clean up
        this.cleanup();
        this.stopDurationTimer();
        
        // Clear container
        if (this.container) {
            this.container.innerHTML = '';
            this.container = null;
        }
    }
}