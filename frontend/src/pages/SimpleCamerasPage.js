/**
 * SimpleCamerasPage.js - Professional Auto-Recording Camera Monitoring
 * 
 * This replaces manual recording controls with professional monitoring interface.
 * - Automatic recording lifecycle management
 * - Real-time health monitoring  
 * - Professional status indicators (no manual start/stop)
 * - Working snapshots with correct camera manager IDs
 */

import config from '../config/app.config.js';

class SimpleCamerasPage {
    constructor() {
        this.cameras = [];
        this.activeCamera = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        this.render();
        await this.loadCameras();
        this.startAutoRefresh();
        this.attachEventListeners();
    }

    render() {
        const container = document.getElementById('cameras');
        if (!container) return;

        container.innerHTML = `
            <div class="cameras-page">
                <div class="page-header">
                    <h1 class="page-title">
                        <i class="fas fa-video"></i>
                        Camera Monitoring
                    </h1>
                    <p class="page-subtitle">Professional 24/7 Surveillance System</p>
                    <div class="system-status">
                        <div class="status-badge" id="system-status">
                            <i class="fas fa-circle"></i>
                            Auto-Recording Active
                        </div>
                    </div>
                </div>

                <div class="cameras-grid" id="cameras-grid">
                    <div class="loading-state">
                        <i class="fas fa-spinner fa-spin"></i>
                        Loading cameras...
                    </div>
                </div>
            </div>

            <style>
                .cameras-page {
                    padding: 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                .page-header {
                    text-align: left;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: rgba(26, 35, 50, 0.8);
                    border-radius: 12px;
                    border: 1px solid rgba(99, 102, 241, 0.2);
                }
                
                .page-title {
                    color: #e8eaed;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 15px;
                }
                
                .page-subtitle {
                    color: #9ca3af;
                    margin-bottom: 15px;
                }
                
                .system-status {
                    display: flex;
                    justify-content: center;
                    gap: 15px;
                }
                
                .status-badge {
                    padding: 8px 16px;
                    background: rgba(34, 197, 94, 0.15);
                    color: #22c55e;
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.9rem;
                    font-weight: 600;
                }
                
                .cameras-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
                    gap: 20px;
                }
                
                .camera-card {
                    background: rgba(26, 35, 50, 0.9);
                    border-radius: 16px;
                    padding: 20px;
                    border: 1px solid rgba(99, 102, 241, 0.2);
                    transition: all 0.3s ease;
                }
                
                .camera-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
                }
                
                .camera-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }
                
                .camera-name {
                    font-size: 1.3rem;
                    color: #e8eaed;
                    font-weight: 600;
                }
                
                .camera-status {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.9rem;
                    font-weight: 600;
                }
                
                .camera-status.online {
                    color: #22c55e;
                }
                
                .camera-status.offline {
                    color: #ef4444;
                }
                
                .camera-preview {
                    position: relative;
                    aspect-ratio: 16/9;
                    background: #1f2937;
                    border-radius: 10px;
                    overflow: hidden;
                    margin-bottom: 15px;
                    border: 1px solid rgba(55, 65, 81, 0.5);
                }
                
                .camera-snapshot {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                
                .snapshot-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-direction: column;
                    gap: 10px;
                    color: #9ca3af;
                }
                
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 12px;
                    margin-bottom: 15px;
                }
                
                .metric-item {
                    background: rgba(15, 20, 25, 0.6);
                    padding: 12px;
                    border-radius: 8px;
                    text-align: center;
                    border: 1px solid rgba(55, 65, 81, 0.3);
                }
                
                .metric-value {
                    font-size: 1.2rem;
                    font-weight: 700;
                    margin-bottom: 2px;
                    color: #22c55e;
                }
                
                .metric-label {
                    font-size: 0.8rem;
                    color: #9ca3af;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .recording-status {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 12px 15px;
                    background: rgba(15, 20, 25, 0.6);
                    border-radius: 8px;
                    border: 1px solid rgba(55, 65, 81, 0.3);
                }
                
                .recording-indicator {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    color: #22c55e;
                    font-weight: 600;
                }
                
                .recording-dot {
                    width: 12px;
                    height: 12px;
                    background: #ef4444;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                
                .loading-state {
                    text-align: center;
                    padding: 40px;
                    color: #9ca3af;
                }
                
                .loading-state i {
                    font-size: 2rem;
                    margin-bottom: 15px;
                }
                
                .error-state {
                    text-align: center;
                    padding: 40px;
                    color: #ef4444;
                }
            </style>
        `;
    }

    async loadCameras() {
        try {
            // Get cameras from both database and camera manager
            const [dbCameras, healthData] = await Promise.all([
                this.fetchDatabaseCameras(),
                this.fetchCameraManagerHealth()
            ]);

            // Merge data from both sources
            this.cameras = this.mergeCameraData(dbCameras, healthData);
            this.renderCameras();

        } catch (error) {
            console.error('Error loading cameras:', error);
            this.showError('Failed to load cameras');
        }
    }

    async fetchDatabaseCameras() {
        try {
            const response = await fetch(config.buildApiUrl(config.API_ENDPOINTS.CAMERAS));
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('Failed to load database cameras:', error);
            return [];
        }
    }

    async fetchCameraManagerHealth() {
        try {
            const response = await fetch(config.buildApiUrl('/api/cameras/health/summary'));
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('Failed to load camera manager health:', error);
            return { cameras: {} };
        }
    }

    mergeCameraData(dbCameras, healthData) {
        const cameras = [];
        
        // Add cameras from camera manager (these have working snapshots)
        Object.entries(healthData.cameras || {}).forEach(([managerId, health]) => {
            // Try to find matching database camera
            const dbCamera = dbCameras.find(db => 
                db.ip_address === this.extractIpFromHealth(health.connection_url)
            ) || {};

            cameras.push({
                id: managerId,
                manager_id: managerId,
                database_id: dbCamera.camera_id,
                name: dbCamera.name || 'Camera',
                location: dbCamera.location || 'Unknown',
                ip_address: this.extractIpFromHealth(health.connection_url),
                status: health.is_healthy ? 'online' : 'offline',
                is_recording: health.capture_active,
                last_frame_age: health.last_frame_age,
                error_count: health.error_count,
                buffer_size: health.buffer_size
            });
        });

        return cameras;
    }

    extractIpFromHealth(connectionUrl) {
        if (!connectionUrl) return 'Unknown';
        try {
            const match = connectionUrl.match(/\/\/[^:]*@([^:]+):/);
            return match ? match[1] : 'Unknown';
        } catch {
            return 'Unknown';
        }
    }

    renderCameras() {
        const container = document.getElementById('cameras-grid');
        if (!container) return;

        if (this.cameras.length === 0) {
            container.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-video-slash"></i>
                    <h3>No cameras found</h3>
                    <p>Professional monitoring system ready</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.cameras.map(camera => this.renderCameraCard(camera)).join('');
        
        // Initialize snapshots
        this.cameras.forEach(camera => {
            this.loadCameraSnapshot(camera);
        });
    }

    renderCameraCard(camera) {
        return `
            <div class="camera-card" data-camera-id="${camera.id}">
                <div class="camera-header">
                    <div class="camera-name">${camera.name}</div>
                    <div class="camera-status ${camera.status}">
                        <i class="fas ${camera.status === 'online' ? 'fa-circle' : 'fa-times-circle'}"></i>
                        ${camera.status.toUpperCase()}
                    </div>
                </div>

                <div class="camera-preview">
                    <img class="camera-snapshot" 
                         id="snapshot-${camera.id}" 
                         alt="${camera.name} snapshot"
                         style="display: none;">
                    <div class="snapshot-overlay" id="overlay-${camera.id}">
                        <i class="fas fa-spinner fa-spin"></i>
                        <div>Loading preview...</div>
                    </div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">${camera.last_frame_age?.toFixed(2) || '0.00'}s</div>
                        <div class="metric-label">Frame Age</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">${camera.buffer_size || 0}/30</div>
                        <div class="metric-label">Buffer</div>
                    </div>
                </div>

                <div class="recording-status">
                    <div class="recording-indicator">
                        <div class="recording-dot"></div>
                        <span>Auto-Recording Active</span>
                    </div>
                    <div class="recording-stats">
                        Errors: ${camera.error_count || 0}
                    </div>
                </div>
            </div>
        `;
    }

    loadCameraSnapshot(camera) {
        const img = document.getElementById(`snapshot-${camera.id}`);
        const overlay = document.getElementById(`overlay-${camera.id}`);
        
        if (!img || !overlay) return;

        // Use camera manager ID for snapshots (this works!)
        const snapshotUrl = config.buildApiUrl(`/api/cameras/${camera.manager_id}/snapshot`);
        
        img.onload = () => {
            img.style.display = 'block';
            overlay.style.display = 'none';
        };
        
        img.onerror = () => {
            overlay.innerHTML = `
                <i class="fas fa-camera"></i>
                <div>Camera offline</div>
            `;
        };
        
        img.src = snapshotUrl;
    }

    startAutoRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadCameras();
            
            // Refresh snapshots
            this.cameras.forEach(camera => {
                const img = document.getElementById(`snapshot-${camera.id}`);
                if (img && img.style.display !== 'none') {
                    const snapshotUrl = config.buildApiUrl(`/api/cameras/${camera.manager_id}/snapshot`);
                    img.src = `${snapshotUrl}?t=${Date.now()}`;
                }
            });
        }, 30000);
    }

    attachEventListeners() {
        // No manual controls - this is a monitoring interface only
        console.log('Professional monitoring interface active - no manual controls');
    }

    showError(message) {
        const container = document.getElementById('cameras-grid');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

export default SimpleCamerasPage;