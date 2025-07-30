// CamerasPage.js - Stream management fixes

// Add these methods to your CamerasPage class:

class CamerasPage {
    constructor() {
        // ... existing constructor code ...
        
        // Enhanced state management for streaming
        this.streamStates = new Map();
        this.videoPlayers = new Map();
        this.streamTimers = new Map();
        this.navigationCleanupHandlers = new Map();
        
        // Make instance available globally for onclick handlers
        window.camerasPage = this;
        
        // Page visibility API for handling tab switching
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
    }
    
    // Initialize camera player with proper cleanup tracking
    initializeCameraPlayer(camera) {
        const container = document.getElementById(`preview-container-${camera.id}`);
        if (!container) return;
        
        // Clean up existing player first
        this.cleanupCameraPlayer(camera.id);
        
        // Create new player instance
        const player = new LiveVideoPlayer({
            cameraId: camera.id,
            camera: camera,
            autoStart: false,
            showControls: false,  // External controls used
            className: 'camera-card-player',
            onStatusChange: (status) => this.handleStreamStatusChange(camera.id, status),
            onError: (error) => this.handleStreamError(camera.id, error),
            onStreamStart: () => this.handleStreamStart(camera.id),
            onStreamStop: () => this.handleStreamStop(camera.id)
        });
        
        // Initialize the player
        player.init(container);
        
        // Store reference
        this.videoPlayers.set(camera.id, player);
        
        // Set up navigation cleanup
        this.setupNavigationCleanup(camera.id);
    }
    
    // Clean up individual camera player
    cleanupCameraPlayer(cameraId) {
        const player = this.videoPlayers.get(cameraId);
        if (player) {
            player.destroy();
            this.videoPlayers.delete(cameraId);
        }
        
        // Clean up timer
        const timer = this.streamTimers.get(cameraId);
        if (timer) {
            clearInterval(timer);
            this.streamTimers.delete(cameraId);
        }
        
        // Clean up navigation handler
        const cleanup = this.navigationCleanupHandlers.get(cameraId);
        if (cleanup) {
            cleanup();
            this.navigationCleanupHandlers.delete(cameraId);
        }
    }
    
    // Set up navigation cleanup to prevent black screens
    setupNavigationCleanup(cameraId) {
        // Listen for page navigation
        const beforeUnloadHandler = () => {
            this.cleanupCameraPlayer(cameraId);
        };
        
        window.addEventListener('beforeunload', beforeUnloadHandler);
        
        // Store cleanup function
        this.navigationCleanupHandlers.set(cameraId, () => {
            window.removeEventListener('beforeunload', beforeUnloadHandler);
        });
    }
    
    // Handle page visibility changes (tab switching)
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden - pause all streams
            this.pauseAllStreams();
        } else {
            // Page is visible - resume streams
            this.resumeActiveStreams();
        }
    }
    
    // Pause all active streams when page is hidden
    pauseAllStreams() {
        this.videoPlayers.forEach((player, cameraId) => {
            if (player.isStreaming) {
                // Store state before pausing
                this.streamStates.set(cameraId, 'paused');
                player.cleanup(); // Just cleanup connections, don't stop stream
            }
        });
    }
    
    // Resume streams that were active
    resumeActiveStreams() {
        this.streamStates.forEach((state, cameraId) => {
            if (state === 'paused') {
                const player = this.videoPlayers.get(cameraId);
                if (player) {
                    // Re-render to restart image loading
                    player.render();
                    this.streamStates.set(cameraId, true);
                }
            }
        });
    }
    
    // Enhanced render method with fixed 800x600 sizing
    renderCameraCard(camera) {
        const statusClass = camera.status;
        const healthScore = this.calculateHealthScore(camera);
        const isStreaming = this.streamStates.get(camera.id) || false;
        
        return `
            <div class="camera-card" data-camera-id="${camera.id}">
                <div class="camera-card-header">
                    <!-- Header content unchanged -->
                </div>
                
                <div class="camera-card-body">
                    <div class="camera-card-preview" style="position: relative; width: 100%; min-height: 600px; background: #f5f5f5; display: flex; align-items: center; justify-content: center;">
                        <div class="preview-container" id="preview-container-${camera.id}" style="width: 100%;">
                            <!-- LiveVideoPlayer will be inserted here with 800x600 size -->
                        </div>
                    </div>
                    
                    <div class="camera-card-info">
                        <!-- Info content unchanged -->
                    </div>
                </div>
                
                <div class="camera-card-actions">
                    <div class="camera-card-stream-controls">
                        <button class="btn ${isStreaming ? 'btn-danger' : 'btn-success'} btn-small stream-control-btn" 
                                data-action="${isStreaming ? 'stop-stream' : 'start-stream'}" 
                                data-camera-id="${camera.id}">
                            <i class="fas fa-${isStreaming ? 'stop' : 'play'}"></i>
                            ${isStreaming ? 'Stop' : 'Start'}
                        </button>
                        <button class="btn btn-info btn-small" 
                                data-action="capture" 
                                data-camera-id="${camera.id}">
                            <i class="fas fa-camera"></i>
                            Capture
                        </button>
                        <button class="btn btn-primary btn-small" 
                                data-action="fullscreen" 
                                data-camera-id="${camera.id}">
                            <i class="fas fa-expand"></i>
                            Full Screen
                        </button>
                    </div>
                    <!-- Other action buttons unchanged -->
                </div>
            </div>
        `;
    }
    
    // Stream control button handler
    attachCameraEventListeners() {
        // ... existing event listeners ...
        
        // Stream control buttons
        document.querySelectorAll('.stream-control-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const cameraId = parseInt(e.currentTarget.dataset.cameraId);
                const action = e.currentTarget.dataset.action;
                const player = this.videoPlayers.get(cameraId);
                
                if (!player) return;
                
                // Disable button during operation
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                
                try {
                    if (action === 'start-stream') {
                        await player.startStream();
                    } else if (action === 'stop-stream') {
                        await player.stopStream();
                    }
                } catch (error) {
                    console.error(`Failed to ${action}:`, error);
                    this.showToast(`Failed to ${action}`, 'error');
                } finally {
                    // Re-render to update button state
                    this.updateStreamControlButton(cameraId);
                }
            });
        });
        
        // Fullscreen button
        document.querySelectorAll('[data-action="fullscreen"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cameraId = parseInt(e.currentTarget.dataset.cameraId);
                const player = this.videoPlayers.get(cameraId);
                if (player) {
                    player.toggleFullscreen();
                }
            });
        });
    }
    
    // Update individual stream control button
    updateStreamControlButton(cameraId) {
        const btn = document.querySelector(`.stream-control-btn[data-camera-id="${cameraId}"]`);
        if (!btn) return;
        
        const isStreaming = this.streamStates.get(cameraId) || false;
        
        btn.disabled = false;
        btn.className = `btn ${isStreaming ? 'btn-danger' : 'btn-success'} btn-small stream-control-btn`;
        btn.dataset.action = isStreaming ? 'stop-stream' : 'start-stream';
        btn.innerHTML = `<i class="fas fa-${isStreaming ? 'stop' : 'play'}"></i> ${isStreaming ? 'Stop' : 'Start'}`;
    }
    
    // Stream event handlers
    handleStreamStatusChange(cameraId, status) {
        console.log(`Camera ${cameraId} stream status: ${status}`);
    }
    
    handleStreamError(cameraId, error) {
        console.error(`Camera ${cameraId} stream error:`, error);
        this.showToast(`Stream error for camera ${cameraId}`, 'error');
    }
    
    handleStreamStart(cameraId) {
        this.streamStates.set(cameraId, true);
        this.updateStreamControlButton(cameraId);
        
        // Update camera info to show streaming status
        const cameraCard = document.querySelector(`.camera-card[data-camera-id="${cameraId}"]`);
        if (cameraCard) {
            const statusEl = cameraCard.querySelector('.camera-card-status');
            if (statusEl && !statusEl.querySelector('.streaming-badge')) {
                statusEl.innerHTML += '<span class="streaming-badge" style="margin-left: 8px; background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">LIVE</span>';
            }
        }
    }
    
    handleStreamStop(cameraId) {
        this.streamStates.set(cameraId, false);
        this.updateStreamControlButton(cameraId);
        
        // Remove streaming badge
        const cameraCard = document.querySelector(`.camera-card[data-camera-id="${cameraId}"]`);
        if (cameraCard) {
            const badge = cameraCard.querySelector('.streaming-badge');
            if (badge) {
                badge.remove();
            }
        }
    }
    
    // Enhanced cleanup on page destroy
    destroy() {
        // Remove visibility change listener
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Stop all polling
        this.stopStatusPolling();
        
        // Clean up all video players
        this.videoPlayers.forEach((player, cameraId) => {
            this.cleanupCameraPlayer(cameraId);
        });
        
        // Clear all maps
        this.streamStates.clear();
        this.videoPlayers.clear();
        this.streamTimers.clear();
        this.navigationCleanupHandlers.clear();
        
        // Call parent destroy if exists
        if (super.destroy) {
            super.destroy();
        }
    }
}