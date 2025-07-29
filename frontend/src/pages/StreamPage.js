/**
 * StreamPage - Live video streaming with license plate detection
 * Integrates with backend streaming API
 */
import config from '../config/app.config.js';

class StreamPage {
    constructor() {
        this.isStreaming = false;
        this.isDetectionEnabled = true;
        this.showLabels = true;
        this.streamWebSocket = null;
        this.canvas = null;
        this.ctx = null;
        this.videoFeed = null;
        this.detections = [];
        this.lastFrameTime = 0;
        this.frameCount = 0;
        this.cameraId = 3; // Test Camera 1
        this.apiBaseUrl = config.API_BASE_URL;
        this.streamUrl = `${this.apiBaseUrl}${config.API_ENDPOINTS.STREAM_VIDEO(this.cameraId)}`;
        
        this.recentConfidences = [];
    }

    init() {
        this.setupEventListeners();
        this.setupWebSocket();
        this.setupFullscreenListeners();
        this.initializeButtonStates();
        this.loadInitialStats();
    }
    
    initializeButtonStates() {
        // Initialize button states to match current settings
        const detectionBtn = document.getElementById('toggle-detection');
        const labelsBtn = document.getElementById('toggle-labels');
        
        if (detectionBtn) {
            detectionBtn.classList.toggle('active', this.isDetectionEnabled);
            detectionBtn.style.backgroundColor = this.isDetectionEnabled ? 'var(--primary)' : 'rgba(255, 255, 255, 0.2)';
        }
        
        if (labelsBtn) {
            labelsBtn.classList.toggle('active', this.showLabels);
            labelsBtn.style.backgroundColor = this.showLabels ? 'var(--primary)' : 'rgba(255, 255, 255, 0.2)';
        }
        
        // Update stream button
        this.updateStreamButton();
    }

    setupEventListeners() {
        // Stream controls
        document.getElementById('toggle-stream')?.addEventListener('click', () => this.toggleStream());
        document.getElementById('toggle-fullscreen')?.addEventListener('click', () => this.toggleFullscreen());
        document.getElementById('capture-frame')?.addEventListener('click', () => this.captureFrame());
        
        // Video controls
        document.getElementById('play-pause')?.addEventListener('click', () => this.togglePlayPause());
        document.getElementById('toggle-detection')?.addEventListener('click', () => this.toggleDetection());
        document.getElementById('toggle-labels')?.addEventListener('click', () => this.toggleLabels());
        document.getElementById('settings')?.addEventListener('click', () => this.openSettings());
        
        // Settings
        document.getElementById('save-settings')?.addEventListener('click', () => this.saveSettings());
        document.getElementById('clear-detections')?.addEventListener('click', () => this.clearDetections());
        
        // Modal close functionality
        document.querySelectorAll('[data-modal-close]').forEach(btn => {
            btn.addEventListener('click', () => {
                const modal = btn.closest('.modal');
                if (modal) modal.classList.remove('show');
            });
        });
        
        // Close modal on backdrop click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                }
            });
        });
        
        // Get video feed element
        this.videoFeed = document.getElementById('video-feed');
        if (this.videoFeed) {
            this.videoFeed.addEventListener('load', () => this.onVideoLoad());
            this.videoFeed.addEventListener('error', () => this.onVideoError());
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                this.togglePlayPause();
            } else if (e.code === 'KeyF') {
                e.preventDefault();
                this.toggleFullscreen();
            }
        });
    }

    setupWebSocket() {
        // Future implementation for Phase 2 - real-time detection data
        if (window.location.protocol === 'http:') {
            const wsUrl = config.buildWsUrl(config.WS_ENDPOINTS.STREAM)(this.cameraId);
            try {
                this.streamWebSocket = new WebSocket(wsUrl);
                this.streamWebSocket.onopen = () => this.onStreamConnected();
                this.streamWebSocket.onclose = () => this.onStreamDisconnected();
                this.streamWebSocket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleStreamData(data);
                };
            } catch (error) {
                console.debug('WebSocket not available yet:', error);
            }
        }
    }

    async loadInitialStats() {
        // Check initial stream status
        await this.checkStreamStatus();
        
        // Load today's detection count
        await this.fetchTodayDetectionCount();
        
        // Load recent detections for display
        await this.loadRecentDetections();
        
        // Update stream quality
        this.updateSystemStats();
        
        // Start periodic stats update
        this.statsInterval = setInterval(() => {
            this.fetchTodayDetectionCount();
            this.updateProcessingSpeed();
            this.checkStreamStatus();
            this.loadRecentDetections();
        }, 10000); // Update every 10 seconds
    }

    async checkStreamStatus() {
        try {
            // Check backend stream status
            const response = await fetch(`${this.apiBaseUrl}/api/v1/streams/status/${this.cameraId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'active') {
                    this.updateStreamStatus('connected');
                    this.isStreaming = true;
                } else {
                    this.updateStreamStatus('disconnected');
                    this.isStreaming = false;
                }
            } else {
                this.updateStreamStatus('disconnected');
                this.isStreaming = false;
            }
        } catch (error) {
            console.debug('Could not check stream status:', error);
            this.updateStreamStatus('disconnected');
            this.isStreaming = false;
        }
        
        this.updateStreamButton();
    }

    updateStreamButton() {
        const btn = document.getElementById('toggle-stream');
        if (btn) {
            btn.innerHTML = this.isStreaming ? `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16"></rect>
                    <rect x="14" y="4" width="4" height="16"></rect>
                </svg>
                Stop Stream
            ` : `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5,3 19,12 5,21 5,3"></polygon>
                </svg>
                Start Stream
            `;
        }
    }

    async toggleStream() {
        try {
            const btn = document.getElementById('toggle-stream');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M8 12l2 2 4-4"></path>
                    </svg>
                    Processing...
                `;
            }

            if (this.isStreaming) {
                // Stop stream
                const response = await fetch(`${this.apiBaseUrl}/api/v1/streams/stop/${this.cameraId}`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    // Hide video feed
                    if (this.videoFeed) {
                        this.videoFeed.style.display = 'none';
                    }
                    this.isStreaming = false;
                    this.updateStreamStatus('disconnected');
                } else {
                    throw new Error('Failed to stop stream');
                }
            } else {
                // Start stream
                const response = await fetch(`${this.apiBaseUrl}/api/v1/streams/start/${this.cameraId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        quality: 'high',
                        max_fps: 30,
                        detection_enabled: this.isDetectionEnabled,
                        confidence_threshold: 0.7
                    })
                });
                
                if (response.ok) {
                    // Show video feed and set source
                    if (this.videoFeed) {
                        this.videoFeed.style.display = 'block';
                        this.videoFeed.src = this.streamUrl;
                        this.setupCanvas();
                    }
                    this.isStreaming = true;
                    this.updateStreamStatus('connected');
                } else {
                    throw new Error('Failed to start stream');
                }
            }
        } catch (error) {
            console.error('Error toggling stream:', error);
            this.updateStreamStatus('error');
            if (window.lprApp) {
                window.lprApp.showNotification(`Stream error: ${error.message}`, 'error');
            }
        } finally {
            // Update button
            this.updateStreamButton();
            const btn = document.getElementById('toggle-stream');
            if (btn) {
                btn.disabled = false;
            }
        }
    }

    setupCanvas() {
        this.canvas = document.getElementById('detection-canvas');
        if (!this.canvas || !this.videoFeed) return;
        
        this.ctx = this.canvas.getContext('2d');
        
        // Make canvas overlay the video
        const updateCanvasSize = () => {
            const rect = this.videoFeed.getBoundingClientRect();
            this.canvas.width = rect.width;
            this.canvas.height = rect.height;
            this.canvas.style.position = 'absolute';
            this.canvas.style.top = '0';
            this.canvas.style.left = '0';
            this.canvas.style.pointerEvents = 'none';
        };
        
        updateCanvasSize();
        window.addEventListener('resize', updateCanvasSize);
        
        // Start detection overlay rendering
        this.startDetectionOverlay();
    }

    startDetectionOverlay() {
        const renderLoop = () => {
            if (this.ctx && this.isDetectionEnabled) {
                // Clear canvas
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                
                // Draw detections
                this.drawDetections();
            }
            
            requestAnimationFrame(renderLoop);
        };
        
        renderLoop();
    }

    drawDetections() {
        if (!this.ctx || !this.detections.length) return;
        
        this.detections.forEach(detection => {
            const { bbox, confidence, plate_text } = detection;
            if (!bbox || bbox.length < 4) return;
            
            const [x1, y1, x2, y2] = bbox;
            const width = x2 - x1;
            const height = y2 - y1;
            
            // Scale coordinates to canvas size
            const scaleX = this.canvas.width / 1280;
            const scaleY = this.canvas.height / 720;
            
            const scaledX = x1 * scaleX;
            const scaledY = y1 * scaleY;
            const scaledWidth = width * scaleX;
            const scaledHeight = height * scaleY;
            
            // Draw bounding box
            this.ctx.strokeStyle = confidence > 0.7 ? '#10b981' : confidence > 0.4 ? '#f59e0b' : '#ef4444';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);
            
            // Draw label if enabled
            if (this.showLabels && plate_text) {
                const label = `${plate_text} (${(confidence * 100).toFixed(1)}%)`;
                
                this.ctx.fillStyle = this.ctx.strokeStyle;
                this.ctx.fillRect(scaledX, scaledY - 25, this.ctx.measureText(label).width + 10, 20);
                
                this.ctx.fillStyle = 'white';
                this.ctx.font = '12px Arial';
                this.ctx.fillText(label, scaledX + 5, scaledY - 10);
            }
        });
    }

    onVideoLoad() {
        this.updateStreamStatus('connected');
        console.log('Video stream loaded successfully');
        
        // Update resolution display
        const resElement = document.getElementById('resolution');
        if (resElement && this.videoFeed) {
            resElement.textContent = `${this.videoFeed.naturalWidth || 1280}x${this.videoFeed.naturalHeight || 720}`;
        }
    }

    onVideoError() {
        this.updateStreamStatus('error');
        console.error('Video stream failed to load');
    }

    updateStreamStatus(status) {
        const statusEl = document.getElementById('stream-status');
        if (statusEl) {
            statusEl.className = `status status-${status}`;
            const statusText = {
                connected: 'Connected',
                disconnected: 'Disconnected',
                error: 'Error',
                loading: 'Connecting...'
            };
            statusEl.querySelector('.status-text').textContent = statusText[status] || status;
        }
    }

    // Placeholder methods for future Phase 2 implementation
    handleStreamData(data) {
        if (data.type === 'detection') {
            this.addDetection(data.detection || data);
            this.updateStats(data.detection || data);
        }
    }

    addDetection(detection) {
        // Add to detections array for overlay
        this.detections.unshift(detection);
        if (this.detections.length > 10) {
            this.detections.pop();
        }
        
        // Add to recent detections list
        this.addDetectionToList(detection);
        
        // Clear detection after 3 seconds
        setTimeout(() => {
            const index = this.detections.indexOf(detection);
            if (index > -1) {
                this.detections.splice(index, 1);
            }
        }, 3000);
    }

    addDetectionToList(detection) {
        const list = document.getElementById('recent-detections');
        if (!list) return;
        
        const item = document.createElement('div');
        item.className = 'detection-item';
        
        const confidence = detection.confidence || 0;
        const confidenceClass = confidence > 0.7 ? 'confidence-high' : 
                                 confidence > 0.4 ? 'confidence-medium' : 'confidence-low';
        
        item.innerHTML = `
            <div class="detection-thumbnail">
                ${detection.plate_text ? detection.plate_text.substring(0, 3) : 'IMG'}
            </div>
            <div class="detection-info">
                <div class="detection-plate">${detection.plate_text || 'Unknown'}</div>
                <div class="detection-meta">
                    <span class="confidence-badge ${confidenceClass}">${(confidence * 100).toFixed(1)}%</span>
                    <span style="margin-left: 8px;">Just now</span>
                </div>
            </div>
        `;
        
        list.insertBefore(item, list.firstChild);
        
        // Remove old items
        while (list.children.length > 20) {
            list.removeChild(list.lastChild);
        }
    }

    async fetchTodayDetectionCount() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/detections/recent?limit=1`);
            if (response.ok) {
                const data = await response.json();
                const countEl = document.getElementById('detections-count');
                if (countEl) {
                    countEl.textContent = data.total || 0;
                }
            }
        } catch (error) {
            console.debug('Could not fetch detection count:', error);
        }
    }

    async loadRecentDetections() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/detections/recent?limit=10`);
            if (response.ok) {
                const data = await response.json();
                const container = document.getElementById('recent-detections');
                if (container && data.detections && data.detections.length > 0) {
                    // Clear existing content
                    container.innerHTML = '';
                    
                    // Add each detection
                    data.detections.forEach(detection => {
                        this.addDetectionToList(detection);
                    });
                } else if (container) {
                    // Show placeholder
                    container.innerHTML = `
                        <div class="detection-item">
                            <div class="detection-thumbnail">IMG</div>
                            <div class="detection-info">
                                <div class="detection-plate">No recent detections</div>
                                <div class="detection-meta">Start streaming to see live results</div>
                            </div>
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.debug('Could not load recent detections:', error);
        }
    }

    updateProcessingSpeed() {
        const processingEl = document.getElementById('processing-speed');
        if (processingEl) {
            processingEl.textContent = '150ms'; // Placeholder for Phase 1
        }
    }

    updateSystemStats() {
        const qualityEl = document.getElementById('stream-quality');
        if (qualityEl && this.videoFeed) {
            const width = this.videoFeed.naturalWidth || 1280;
            
            if (width >= 1920) {
                qualityEl.textContent = 'Full HD';
            } else if (width >= 1280) {
                qualityEl.textContent = 'HD';
            } else {
                qualityEl.textContent = 'SD';
            }
        }
        
        // Update FPS counter
        const fpsElement = document.getElementById('fps-counter');
        if (fpsElement) {
            fpsElement.textContent = '30';
        }
        
        // Update accuracy rate placeholder
        const accuracyEl = document.getElementById('accuracy-rate');
        if (accuracyEl) {
            accuracyEl.textContent = '0%'; // Will be updated when detections come in
        }
    }

    // Additional UI control methods
    toggleFullscreen() {
        const container = document.getElementById('stream-container');
        if (!container) return;
        
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            container.requestFullscreen();
        }
    }

    setupFullscreenListeners() {
        document.addEventListener('fullscreenchange', () => {
            const container = document.getElementById('stream-container');
            if (!container) return;
            
            if (document.fullscreenElement) {
                container.classList.add('fullscreen-mode');
            } else {
                container.classList.remove('fullscreen-mode');
            }
        });
    }

    captureFrame() {
        if (!this.videoFeed) return;
        
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = this.videoFeed.naturalWidth || 1280;
        tempCanvas.height = this.videoFeed.naturalHeight || 720;
        
        tempCtx.drawImage(this.videoFeed, 0, 0);
        
        const link = document.createElement('a');
        link.download = `capture_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.png`;
        link.href = tempCanvas.toDataURL();
        link.click();
        
        if (window.lprApp) {
            window.lprApp.showNotification('Frame captured successfully', 'success');
        }
    }

    togglePlayPause() {
        this.toggleStream();
    }

    toggleDetection() {
        this.isDetectionEnabled = !this.isDetectionEnabled;
        const btn = document.getElementById('toggle-detection');
        if (btn) {
            btn.classList.toggle('active', this.isDetectionEnabled);
            btn.style.backgroundColor = this.isDetectionEnabled ? 'var(--primary)' : 'rgba(255, 255, 255, 0.2)';
        }
        
        if (!this.isDetectionEnabled && this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    toggleLabels() {
        this.showLabels = !this.showLabels;
        const btn = document.getElementById('toggle-labels');
        if (btn) {
            btn.classList.toggle('active', this.showLabels);
            btn.style.backgroundColor = this.showLabels ? 'var(--primary)' : 'rgba(255, 255, 255, 0.2)';
        }
    }

    openSettings() {
        const modal = document.getElementById('settings-modal');
        if (modal) {
            modal.classList.add('show');
        }
    }

    saveSettings() {
        const confidence = document.getElementById('confidence-slider')?.value;
        const frequency = document.getElementById('detection-frequency')?.value;
        const autoEnhance = document.getElementById('auto-enhance')?.checked;
        const saveDetections = document.getElementById('save-detections')?.checked;
        
        console.log('Settings saved:', { confidence, frequency, autoEnhance, saveDetections });
        
        const modal = document.getElementById('settings-modal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    clearDetections() {
        const list = document.getElementById('recent-detections');
        if (list) {
            list.innerHTML = `
                <div class="detection-item">
                    <div class="detection-thumbnail">IMG</div>
                    <div class="detection-info">
                        <div class="detection-plate">No recent detections</div>
                        <div class="detection-meta">Cleared by user</div>
                    </div>
                </div>
            `;
        }
        this.detections = [];
    }

    onStreamConnected() {
        this.updateStreamStatus('connected');
        console.log('Stream WebSocket connected');
    }

    onStreamDisconnected() {
        this.updateStreamStatus('disconnected');
        console.log('Stream WebSocket disconnected');
    }

    // Cleanup method
    destroy() {
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
        }
        
        if (this.streamWebSocket) {
            this.streamWebSocket.close();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamPage;
}

// Global initialization if included as script
if (typeof window !== 'undefined') {
    window.StreamPage = StreamPage;
}