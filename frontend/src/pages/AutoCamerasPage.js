/**
 * Professional Auto-Recording Camera Management System
 * Implements industry-standard surveillance monitoring with automatic recording lifecycle management
 */
import SimpleCameraModal from '../components/cameras/SimpleCameraModal.js';
import VLCStreamModal from '../components/modals/VLCStreamModal.js';
import ONVIFDiscoveryModal from '../components/modals/ONVIFDiscoveryModal.js';
import WebSocketService from '../services/WebSocketService.js';
import config from '../config/app.config.js';

class AutoCamerasPage {
    constructor() {
        this.cameras = [];
        this.filteredCameras = [];
        this.filters = { status: '', location: '', search: '' };
        this.currentView = 'grid';
        
        // Health monitoring state
        this.healthMonitor = null;
        this.cameraHealthData = new Map();
        this.recordingHealthData = new Map();
        this.systemAlerts = new Map();
        
        // Auto-refresh intervals
        this.refreshInterval = null;
        this.healthCheckInterval = null;
        this.isPageActive = true;
        
        // Modal instances
        this.simpleCameraModal = new SimpleCameraModal();
        this.onvifDiscoveryModal = new ONVIFDiscoveryModal();
        
        if (config.FEATURES.VLC_INTEGRATION) {
            this.vlcModal = new VLCStreamModal();
        }
        
        // WebSocket subscriptions
        this.webSocketSubscriptions = [];
        
        // Bind methods
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
        
        // Global reference
        window.autoCamerasPage = this;
        
        this.init();
    }
    
    init() {
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
        
        this.render();
        this.attachEventListeners();
        this.loadCameras();
        this.startHealthMonitoring();
        this.setupWebSocketUpdates();
        
        console.log('🎥 Professional Auto-Recording Camera System Initialized');
    }
    
    render() {
        const container = document.getElementById('cameras');
        if (!container) return;
        
        container.innerHTML = this.getTemplate();
        this.renderCameraGrid();
    }
    
    getTemplate() {
        const systemHealth = this.getSystemHealthSummary();
        
        return `
            <div class="page-header">
                <div class="header-main">
                    <h1 class="page-title">
                        <i class="fas fa-video"></i>
                        Camera Management System
                    </h1>
                    <p class="page-subtitle">Professional Auto-Recording Surveillance Platform</p>
                </div>
                
                <!-- System Health Dashboard -->
                <div class="system-health-bar">
                    <div class="health-indicator ${systemHealth.status}">
                        <div class="health-icon">
                            <i class="fas ${systemHealth.icon}"></i>
                        </div>
                        <div class="health-info">
                            <div class="health-status">${systemHealth.message}</div>
                            <div class="health-details">
                                <span class="metric">
                                    <i class="fas fa-video"></i>
                                    ${systemHealth.camerasOnline}/${systemHealth.totalCameras} Cameras
                                </span>
                                <span class="metric">
                                    <i class="fas fa-record-vinyl"></i>
                                    ${systemHealth.recordingActive} Recording
                                </span>
                                <span class="metric">
                                    <i class="fas fa-hdd"></i>
                                    ${systemHealth.storageUsage}% Storage
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Camera Management Controls -->
            <div class="quick-actions">
                <button class="quick-action-btn primary" id="add-camera-btn">
                    <i class="fas fa-plus"></i>
                    <span>Add Camera</span>
                </button>
                
                <button class="quick-action-btn" id="discover-cameras-btn">
                    <i class="fas fa-search"></i>
                    <span>Auto-Discover</span>
                </button>
                
                <button class="quick-action-btn" id="system-health-btn">
                    <i class="fas fa-heartbeat"></i>
                    <span>System Health</span>
                </button>
                
                <button class="quick-action-btn" id="refresh-cameras-btn">
                    <i class="fas fa-sync-alt"></i>
                    <span>Refresh</span>
                </button>
                
                <div class="view-toggle">
                    <button class="view-btn ${this.currentView === 'grid' ? 'active' : ''}" data-view="grid">
                        <i class="fas fa-th"></i>
                    </button>
                    <button class="view-btn ${this.currentView === 'list' ? 'active' : ''}" data-view="list">
                        <i class="fas fa-list"></i>
                    </button>
                </div>
            </div>
            
            <!-- Advanced Filters -->
            <div class="camera-filters">
                <div class="filter-group">
                    <label for="camera-status-filter">System Status:</label>
                    <select id="camera-status-filter" class="filter-select">
                        <option value="">All Status</option>
                        <option value="healthy">Healthy</option>
                        <option value="warning">Warning</option>
                        <option value="critical">Critical</option>
                        <option value="offline">Offline</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="recording-filter">Recording Status:</label>
                    <select id="recording-filter" class="filter-select">
                        <option value="">All Recording</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="error">Error</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="camera-location-filter">Location:</label>
                    <select id="camera-location-filter" class="filter-select">
                        <option value="">All Locations</option>
                        <option value="entrance">Entrance</option>
                        <option value="parking">Parking</option>
                        <option value="exit">Exit</option>
                        <option value="loading">Loading Dock</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="camera-search-filter">Search:</label>
                    <input type="text" id="camera-search-filter" class="filter-input" 
                           placeholder="Camera name, IP, or location...">
                </div>
                
                <div class="filter-actions">
                    <button class="btn btn-primary" id="apply-camera-filters">Apply</button>
                    <button class="btn btn-secondary" id="clear-camera-filters">Clear</button>
                </div>
            </div>
            
            <!-- Active Alerts Banner -->
            <div class="alerts-banner" id="alerts-banner" style="display: none;">
                <div class="alerts-content" id="alerts-content">
                    <!-- Dynamic alerts will be inserted here -->
                </div>
                <button class="alerts-dismiss" id="dismiss-alerts">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <!-- Camera Grid/List -->
            <div class="cameras-container">
                <div class="cameras-grid ${this.currentView}" id="cameras-grid">
                    <!-- Camera cards will be dynamically loaded -->
                </div>
            </div>
            
            <!-- System Statistics Footer -->
            <div class="system-stats-footer" id="system-stats">
                <div class="stat-group">
                    <span class="stat-label">System Uptime:</span>
                    <span class="stat-value" id="system-uptime">--</span>
                </div>
                <div class="stat-group">
                    <span class="stat-label">Recording Sessions:</span>
                    <span class="stat-value" id="recording-sessions">--</span>
                </div>
                <div class="stat-group">
                    <span class="stat-label">Data Processed:</span>
                    <span class="stat-value" id="data-processed">--</span>
                </div>
                <div class="stat-group">
                    <span class="stat-label">Last Health Check:</span>
                    <span class="stat-value" id="last-health-check">--</span>
                </div>
            </div>
        `;
    }
    
    renderCameraGrid() {
        const container = document.getElementById('cameras-grid');
        if (!container) return;
        
        container.className = `cameras-grid ${this.currentView}`;
        
        if (this.filteredCameras.length === 0) {
            container.innerHTML = this.getEmptyState();
            return;
        }
        
        container.innerHTML = this.filteredCameras
            .map(camera => this.currentView === 'grid' 
                ? this.renderCameraCard(camera) 
                : this.renderCameraRow(camera))
            .join('');
        
        // Initialize camera monitoring after rendering
        this.filteredCameras.forEach(camera => {
            this.initializeCameraMonitoring(camera);
        });
        
        this.attachCameraEventListeners();
    }
    
    renderCameraCard(camera) {
        const health = this.cameraHealthData.get(camera.id) || this.getDefaultHealthData();
        const recording = this.recordingHealthData.get(camera.id) || this.getDefaultRecordingData();
        
        const statusClass = this.getSystemHealthClass(health, recording);
        const healthScore = this.calculateCameraHealthScore(health, recording);
        
        return `
            <div class="professional-camera-card ${statusClass}" data-camera-id="${camera.id}">
                <!-- Camera Header -->
                <div class="camera-header">
                    <div class="camera-title-section">
                        <div class="camera-status-indicator ${statusClass}">
                            <div class="status-dot"></div>
                            <div class="status-pulse ${recording.isRecording ? 'active' : ''}"></div>
                        </div>
                        
                        <div class="camera-title-info">
                            <h4 class="camera-name">${camera.name}</h4>
                            <div class="camera-location">
                                <i class="fas fa-map-marker-alt"></i>
                                ${this.capitalizeFirst(camera.location || 'Unknown')}
                            </div>
                        </div>
                    </div>
                    
                    <div class="camera-actions">
                        <div class="health-score">
                            <div class="health-circle ${this.getHealthScoreClass(healthScore)}">
                                <span class="health-percentage">${healthScore}%</span>
                            </div>
                        </div>
                        
                        <div class="action-buttons">
                            <button class="icon-btn" title="Settings" 
                                    onclick="autoCamerasPage.editCamera('${camera.id}')">
                                <i class="fas fa-cog"></i>
                            </button>
                            <button class="icon-btn" title="Diagnostics" 
                                    onclick="autoCamerasPage.showDiagnostics('${camera.id}')">
                                <i class="fas fa-stethoscope"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Live Preview -->
                <div class="camera-preview-section">
                    <div class="preview-container" id="preview-${camera.id}">
                        <img src="${config.buildApiUrl(config.API_ENDPOINTS.CAMERA_SNAPSHOT(camera.id))}?t=${Date.now()}" 
                             alt="${camera.name} Preview"
                             class="camera-snapshot"
                             onerror="this.src='/images/camera-placeholder.jpg'"
                             loading="lazy" />
                        
                        <div class="preview-overlay">
                            <div class="live-indicator ${camera.status === 'online' ? 'active' : ''}">
                                <span class="live-dot"></span>
                                LIVE
                            </div>
                            
                            <div class="preview-controls">
                                <button class="preview-btn" title="Refresh" 
                                        onclick="autoCamerasPage.refreshSnapshot('${camera.id}')">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="preview-btn" title="Fullscreen"
                                        onclick="autoCamerasPage.openFullscreen('${camera.id}')">
                                    <i class="fas fa-expand"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Status Dashboard -->
                <div class="camera-status-dashboard">
                    <!-- Recording Status -->
                    <div class="status-section recording-status">
                        <div class="status-header">
                            <div class="status-icon ${recording.isRecording ? 'recording' : 'stopped'}">
                                <i class="fas ${recording.isRecording ? 'fa-record-vinyl fa-spin' : 'fa-stop-circle'}"></i>
                            </div>
                            <div class="status-info">
                                <div class="status-title">Auto-Recording</div>
                                <div class="status-value ${recording.status}">
                                    ${this.getRecordingStatusText(recording)}
                                </div>
                            </div>
                        </div>
                        
                        ${recording.isRecording ? `
                        <div class="recording-details">
                            <div class="detail-item">
                                <span class="detail-label">Duration:</span>
                                <span class="detail-value">${this.formatUptime(recording.duration)}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Segments:</span>
                                <span class="detail-value">${recording.segments || 0}</span>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    
                    <!-- Connection Health -->
                    <div class="status-section connection-health">
                        <div class="status-header">
                            <div class="status-icon ${health.connectionStatus}">
                                <i class="fas ${this.getConnectionIcon(health.connectionStatus)}"></i>
                            </div>
                            <div class="status-info">
                                <div class="status-title">Connection Health</div>
                                <div class="status-value ${health.connectionStatus}">
                                    ${this.capitalizeFirst(health.connectionStatus)}
                                </div>
                            </div>
                        </div>
                        
                        <div class="health-metrics">
                            <div class="metric-item">
                                <span class="metric-label">Latency:</span>
                                <span class="metric-value ${this.getLatencyClass(health.latency)}">
                                    ${health.latency ? health.latency + 'ms' : '--'}
                                </span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Uptime:</span>
                                <span class="metric-value">${this.formatUptime(health.uptime)}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Storage and Performance -->
                    <div class="status-section storage-performance">
                        <div class="storage-info">
                            <div class="info-item">
                                <span class="info-icon"><i class="fas fa-hdd"></i></span>
                                <div class="info-content">
                                    <span class="info-label">Storage Used</span>
                                    <span class="info-value" id="storage-${camera.id}">
                                        ${this.formatFileSize(recording.storageUsed || 0)}
                                    </span>
                                </div>
                            </div>
                            
                            <div class="info-item">
                                <span class="info-icon"><i class="fas fa-tachometer-alt"></i></span>
                                <div class="info-content">
                                    <span class="info-label">Frame Rate</span>
                                    <span class="info-value">
                                        ${health.currentFps || '--'} / ${camera.max_fps || 30} fps
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Quick Info -->
                <div class="camera-quick-info">
                    <div class="info-row">
                        <span class="info-label">IP Address:</span>
                        <span class="info-value">
                            <a href="http://${camera.ip_address}:${camera.port}" target="_blank" class="ip-link">
                                ${camera.ip_address}:${camera.port}
                            </a>
                        </span>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">Model:</span>
                        <span class="info-value">
                            ${[camera.brand, camera.model].filter(Boolean).join(' ') || 'Unknown'}
                        </span>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">Resolution:</span>
                        <span class="info-value">
                            ${camera.resolution_width || 1920}×${camera.resolution_height || 1080}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderCameraRow(camera) {
        const health = this.cameraHealthData.get(camera.id) || this.getDefaultHealthData();
        const recording = this.recordingHealthData.get(camera.id) || this.getDefaultRecordingData();
        const statusClass = this.getSystemHealthClass(health, recording);
        const healthScore = this.calculateCameraHealthScore(health, recording);
        
        return `
            <div class="professional-camera-row ${statusClass}" data-camera-id="${camera.id}">
                <div class="row-status">
                    <div class="status-indicator ${statusClass}">
                        <div class="status-dot"></div>
                    </div>
                </div>
                
                <div class="row-camera-info">
                    <div class="camera-primary">
                        <span class="camera-name">${camera.name}</span>
                        <span class="camera-location">${this.capitalizeFirst(camera.location || 'Unknown')}</span>
                    </div>
                    <div class="camera-secondary">
                        <span class="camera-ip">${camera.ip_address}:${camera.port}</span>
                        <span class="camera-model">
                            ${[camera.brand, camera.model].filter(Boolean).join(' ') || 'Unknown'}
                        </span>
                    </div>
                </div>
                
                <div class="row-recording">
                    <div class="recording-indicator ${recording.isRecording ? 'active' : 'inactive'}">
                        <i class="fas ${recording.isRecording ? 'fa-record-vinyl' : 'fa-stop-circle'}"></i>
                        <span>${recording.isRecording ? 'Recording' : 'Stopped'}</span>
                    </div>
                </div>
                
                <div class="row-health">
                    <div class="health-score ${this.getHealthScoreClass(healthScore)}">
                        <span class="score-percentage">${healthScore}%</span>
                        <span class="score-label">Health</span>
                    </div>
                </div>
                
                <div class="row-storage">
                    <div class="storage-info">
                        <span class="storage-amount">${this.formatFileSize(recording.storageUsed || 0)}</span>
                        <span class="storage-label">Used</span>
                    </div>
                </div>
                
                <div class="row-actions">
                    <button class="action-btn primary" title="Settings" 
                            onclick="autoCamerasPage.editCamera('${camera.id}')">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="action-btn" title="Diagnostics"
                            onclick="autoCamerasPage.showDiagnostics('${camera.id}')">
                        <i class="fas fa-stethoscope"></i>
                    </button>
                    <button class="action-btn" title="Playback"
                            onclick="autoCamerasPage.openPlayback('${camera.id}')">
                        <i class="fas fa-play"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    getEmptyState() {
        return `
            <div class="empty-state professional">
                <div class="empty-icon">
                    <i class="fas fa-video-slash"></i>
                </div>
                <h3>No Cameras Configured</h3>
                <p>Add your first surveillance camera to begin automated monitoring</p>
                <div class="empty-actions">
                    <button class="btn btn-primary" onclick="autoCamerasPage.showAddCameraModal()">
                        <i class="fas fa-plus"></i>
                        Add Camera
                    </button>
                    <button class="btn btn-secondary" onclick="autoCamerasPage.showDiscoveryModal()">
                        <i class="fas fa-search"></i>
                        Auto-Discover
                    </button>
                </div>
            </div>
        `;
    }
    
    // === HEALTH MONITORING SYSTEM ===
    
    startHealthMonitoring() {
        if (!config.FEATURES.HEALTH_MONITORING) return;
        
        console.log('🔍 Starting professional health monitoring system');
        
        // Initial health check
        this.performHealthCheck();
        
        // Set up continuous monitoring
        this.healthCheckInterval = setInterval(() => {
            if (this.isPageActive) {
                this.performHealthCheck();
            }
        }, config.TIMEOUTS.HEALTH_MONITOR);
        
        // Set up camera refresh
        this.refreshInterval = setInterval(() => {
            if (this.isPageActive) {
                this.refreshCameraData();
            }
        }, config.TIMEOUTS.STATUS_POLLING);
        
        console.log('✅ Health monitoring system active');
    }
    
    async performHealthCheck() {
        try {
            // Check each camera's health
            const healthPromises = this.cameras.map(camera => 
                this.checkCameraHealth(camera.id)
            );
            
            await Promise.allSettled(healthPromises);
            
            // Update system health summary
            this.updateSystemHealthDisplay();
            
            // Process alerts
            this.processHealthAlerts();
            
            // Update last check time
            const lastCheckEl = document.getElementById('last-health-check');
            if (lastCheckEl) {
                lastCheckEl.textContent = new Date().toLocaleTimeString();
            }
            
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }
    
    async checkCameraHealth(cameraId) {
        try {
            const camera = this.cameras.find(c => c.id === cameraId);
            if (!camera) return;
            
            // Parallel health checks
            const [connectionHealth, recordingHealth, storageHealth] = await Promise.allSettled([
                this.checkConnectionHealth(camera),
                this.checkRecordingHealth(camera),
                this.checkStorageHealth(camera)
            ]);
            
            // Combine health data
            const healthData = {
                timestamp: Date.now(),
                connectionStatus: connectionHealth.status === 'fulfilled' ? 
                    connectionHealth.value.status : 'error',
                latency: connectionHealth.status === 'fulfilled' ? 
                    connectionHealth.value.latency : null,
                uptime: connectionHealth.status === 'fulfilled' ? 
                    connectionHealth.value.uptime : 0,
                currentFps: connectionHealth.status === 'fulfilled' ? 
                    connectionHealth.value.fps : null,
                errors: []
            };
            
            const recordingData = recordingHealth.status === 'fulfilled' ? 
                recordingHealth.value : this.getDefaultRecordingData();
            
            // Store health data
            this.cameraHealthData.set(cameraId, healthData);
            this.recordingHealthData.set(cameraId, recordingData);
            
            // Update UI if camera is visible
            this.updateCameraHealthDisplay(cameraId, healthData, recordingData);
            
        } catch (error) {
            console.error(`Health check failed for camera ${cameraId}:`, error);
        }
    }
    
    async checkConnectionHealth(camera) {
        try {
            const startTime = Date.now();
            const response = await fetch(
                config.buildApiUrl(config.API_ENDPOINTS.CAMERA_HEALTH(camera.id)),
                { timeout: config.TIMEOUTS.CONNECTION_TIMEOUT }
            );
            
            const latency = Date.now() - startTime;
            
            if (response.ok) {
                const healthData = await response.json();
                return {
                    status: 'connected',
                    latency,
                    uptime: healthData.uptime || 0,
                    fps: healthData.current_fps || null
                };
            } else {
                return {
                    status: 'error',
                    latency,
                    uptime: 0,
                    fps: null
                };
            }
            
        } catch (error) {
            return {
                status: 'offline',
                latency: null,
                uptime: 0,
                fps: null
            };
        }
    }
    
    async checkRecordingHealth(camera) {
        try {
            const response = await fetch(
                config.buildRecordingUrl(config.API_ENDPOINTS.RECORDING_STATUS(camera.id)),
                { timeout: config.TIMEOUTS.CONNECTION_TIMEOUT }
            );
            
            if (response.ok) {
                const recordingData = await response.json();
                return {
                    isRecording: recordingData.is_recording || false,
                    status: recordingData.is_recording ? 'active' : 'stopped',
                    duration: recordingData.duration || 0,
                    segments: recordingData.segments || 0,
                    storageUsed: recordingData.storage_used || 0,
                    errors: recordingData.errors || [],
                    lastSegment: recordingData.last_segment_time
                };
            } else {
                return this.getDefaultRecordingData();
            }
            
        } catch (error) {
            return {
                ...this.getDefaultRecordingData(),
                status: 'error',
                errors: [error.message]
            };
        }
    }
    
    async checkStorageHealth(camera) {
        try {
            const response = await fetch(
                config.buildRecordingUrl('/api/v1/storage/report'),
                { timeout: config.TIMEOUTS.CONNECTION_TIMEOUT }
            );
            
            if (response.ok) {
                const storageData = await response.json();
                const cameraStorage = storageData.cameras?.[camera.id];
                
                return {
                    used: cameraStorage?.total_size || 0,
                    percentage: cameraStorage?.usage_percentage || 0,
                    available: cameraStorage?.available_space || 0
                };
            } else {
                return { used: 0, percentage: 0, available: 0 };
            }
            
        } catch (error) {
            return { used: 0, percentage: 0, available: 0 };
        }
    }
    
    // === UTILITY METHODS ===
    
    getDefaultHealthData() {
        return {
            timestamp: Date.now(),
            connectionStatus: 'unknown',
            latency: null,
            uptime: 0,
            currentFps: null,
            errors: []
        };
    }
    
    getDefaultRecordingData() {
        return {
            isRecording: false,
            status: 'stopped',
            duration: 0,
            segments: 0,
            storageUsed: 0,
            errors: [],
            lastSegment: null
        };
    }
    
    getSystemHealthSummary() {
        const totalCameras = this.cameras.length;
        const onlineCameras = this.cameras.filter(c => c.status === 'online').length;
        const recordingCameras = Array.from(this.recordingHealthData.values())
            .filter(r => r.isRecording).length;
        
        // Calculate overall system health
        let status = 'healthy';
        let icon = 'fa-check-circle';
        let message = 'All Systems Operational';
        
        const healthPercentage = totalCameras > 0 ? (onlineCameras / totalCameras) : 1;
        
        if (healthPercentage < 0.5) {
            status = 'critical';
            icon = 'fa-exclamation-circle';
            message = 'Critical System Issues';
        } else if (healthPercentage < 0.8) {
            status = 'warning';
            icon = 'fa-exclamation-triangle';
            message = 'System Warnings Detected';
        }
        
        return {
            status,
            icon,
            message,
            totalCameras,
            camerasOnline: onlineCameras,
            recordingActive: recordingCameras,
            storageUsage: 0 // Will be calculated from actual storage data
        };
    }
    
    calculateCameraHealthScore(health, recording) {
        let score = 100;
        
        // Connection health (40% weight)
        if (health.connectionStatus === 'offline') score -= 40;
        else if (health.connectionStatus === 'error') score -= 30;
        else if (health.connectionStatus === 'warning') score -= 15;
        
        // Recording health (30% weight)  
        if (recording.status === 'error') score -= 30;
        else if (recording.status === 'stopped' && config.FEATURES.AUTO_RECORDING) score -= 20;
        
        // Performance metrics (30% weight)
        if (health.latency > 5000) score -= 20;
        else if (health.latency > 2000) score -= 10;
        
        if (recording.errors && recording.errors.length > 0) {
            score -= Math.min(recording.errors.length * 5, 15);
        }
        
        return Math.max(0, Math.min(100, Math.round(score)));
    }
    
    getSystemHealthClass(health, recording) {
        const score = this.calculateCameraHealthScore(health, recording);
        
        if (score >= 90) return 'healthy';
        if (score >= 70) return 'warning';
        return 'critical';
    }
    
    getHealthScoreClass(score) {
        if (score >= 90) return 'excellent';
        if (score >= 80) return 'good';
        if (score >= 60) return 'warning';
        return 'critical';
    }
    
    getRecordingStatusText(recording) {
        if (recording.isRecording) {
            return `Recording (${this.formatUptime(recording.duration)})`;
        }
        
        switch (recording.status) {
            case 'stopped': return 'Auto-Start Pending';
            case 'error': return 'Recovery Required';
            case 'inactive': return 'System Inactive';
            default: return 'Initializing';
        }
    }
    
    getConnectionIcon(status) {
        const icons = {
            'connected': 'fa-wifi',
            'connecting': 'fa-circle-notch fa-spin',
            'error': 'fa-exclamation-triangle',
            'offline': 'fa-times-circle'
        };
        return icons[status] || 'fa-question-circle';
    }
    
    getLatencyClass(latency) {
        if (!latency) return 'unknown';
        if (latency < 100) return 'excellent';
        if (latency < 500) return 'good';
        if (latency < 2000) return 'warning';
        return 'critical';
    }
    
    formatUptime(seconds) {
        if (!seconds || seconds <= 0) return '0m';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (hours > 24) {
            const days = Math.floor(hours / 24);
            return `${days}d ${hours % 24}h`;
        }
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        
        return `${minutes}m`;
    }
    
    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    // === EVENT HANDLERS & UI UPDATES ===
    
    updateCameraHealthDisplay(cameraId, health, recording) {
        // This will be called to update individual camera health displays
        // Implementation will update specific camera card elements
    }
    
    updateSystemHealthDisplay() {
        // Update the system health bar at the top
        const systemHealth = this.getSystemHealthSummary();
        // Implementation will update the health bar elements
    }
    
    processHealthAlerts() {
        // Process and display system alerts based on health data
        // Implementation will manage the alerts banner
    }
    
    // === CAMERA ACTIONS ===
    
    editCamera(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (camera) {
            this.simpleCameraModal.show(camera);
        }
    }
    
    showDiagnostics(cameraId) {
        // Show detailed diagnostic information
        console.log('Showing diagnostics for camera:', cameraId);
    }
    
    refreshSnapshot(cameraId) {
        const img = document.querySelector(`#preview-${cameraId} .camera-snapshot`);
        if (img) {
            const baseUrl = config.buildApiUrl(config.API_ENDPOINTS.CAMERA_SNAPSHOT(cameraId));
            img.src = `${baseUrl}?t=${Date.now()}`;
        }
    }
    
    openFullscreen(cameraId) {
        // Open camera in fullscreen mode
        console.log('Opening fullscreen for camera:', cameraId);
    }
    
    openPlayback(cameraId) {
        window.location.href = `/recordings.html?camera=${cameraId}`;
    }
    
    // === INITIALIZATION & DATA LOADING ===
    
    async loadCameras() {
        try {
            console.log('🔄 Loading cameras with professional monitoring');
            
            const response = await fetch(config.buildApiUrl(config.API_ENDPOINTS.CAMERAS));
            
            if (!response.ok) {
                throw new Error(`Failed to load cameras: ${response.status}`);
            }
            
            const camerasData = await response.json();
            
            this.cameras = camerasData.map(camera => ({
                id: camera.camera_id || camera.id,
                camera_id: camera.camera_id || camera.id,
                name: camera.name,
                location: camera.location,
                ip_address: camera.ip_address,
                port: camera.port,
                connection_type: camera.connection_type,
                stream_path: camera.stream_path,
                status: this.mapBackendStatus(camera.status),
                brand: camera.brand,
                model: camera.model,
                resolution_width: camera.resolution_width || 1920,
                resolution_height: camera.resolution_height || 1080,
                max_fps: camera.max_fps || 30,
                username: camera.username,
                password: camera.password,
                enabled: camera.enabled
            }));
            
            this.filteredCameras = [...this.cameras];
            this.renderCameraGrid();
            
            console.log(`✅ Loaded ${this.cameras.length} cameras successfully`);
            
        } catch (error) {
            console.error('Failed to load cameras:', error);
            this.showToast(`Failed to load cameras: ${error.message}`, 'error');
        }
    }
    
    mapBackendStatus(backendStatus) {
        const statusMap = {
            'active': 'online',
            'inactive': 'offline', 
            'error': 'critical',
            'offline': 'offline',
            'online': 'online',
            'warning': 'warning'
        };
        return statusMap[backendStatus] || 'offline';
    }
    
    // === INITIALIZATION METHODS ===
    
    initializeCameraMonitoring(camera) {
        // Initialize monitoring for a specific camera
        this.checkCameraHealth(camera.id);
    }
    
    attachEventListeners() {
        // Main action buttons
        document.getElementById('add-camera-btn')?.addEventListener('click', () => 
            this.showAddCameraModal());
        
        document.getElementById('discover-cameras-btn')?.addEventListener('click', () => 
            this.showDiscoveryModal());
        
        document.getElementById('system-health-btn')?.addEventListener('click', () => 
            this.showSystemHealthModal());
        
        document.getElementById('refresh-cameras-btn')?.addEventListener('click', () => 
            this.refreshCameras());
        
        // View toggle
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.changeView(e.target.dataset.view));
        });
        
        // Filters
        document.getElementById('apply-camera-filters')?.addEventListener('click', () => 
            this.applyFilters());
        
        document.getElementById('clear-camera-filters')?.addEventListener('click', () => 
            this.clearFilters());
        
        // Search input with debounce
        document.getElementById('camera-search-filter')?.addEventListener('input', (e) => 
            this.handleSearchInput(e));
        
        // Alerts dismiss
        document.getElementById('dismiss-alerts')?.addEventListener('click', () => 
            this.dismissAlerts());
    }
    
    attachCameraEventListeners() {
        // These will be attached after camera cards are rendered
        // Most actions are handled via onclick attributes in the templates
    }
    
    // === MODAL METHODS ===
    
    showAddCameraModal() {
        this.simpleCameraModal.show();
    }
    
    showDiscoveryModal() {
        this.onvifDiscoveryModal.show();
    }
    
    showSystemHealthModal() {
        // Implementation for system health modal
        console.log('🏥 Opening System Health Dashboard');
    }
    
    // === FILTER AND SEARCH ===
    
    applyFilters() {
        const statusFilter = document.getElementById('camera-status-filter')?.value;
        const recordingFilter = document.getElementById('recording-filter')?.value;
        const locationFilter = document.getElementById('camera-location-filter')?.value;
        const searchFilter = document.getElementById('camera-search-filter')?.value?.toLowerCase();
        
        this.filteredCameras = this.cameras.filter(camera => {
            // Status filter
            if (statusFilter) {
                const health = this.cameraHealthData.get(camera.id) || this.getDefaultHealthData();
                const recording = this.recordingHealthData.get(camera.id) || this.getDefaultRecordingData();
                const systemHealth = this.getSystemHealthClass(health, recording);
                
                if (statusFilter !== systemHealth) return false;
            }
            
            // Recording filter
            if (recordingFilter) {
                const recording = this.recordingHealthData.get(camera.id) || this.getDefaultRecordingData();
                const recordingStatus = recording.isRecording ? 'active' : 
                    recording.status === 'error' ? 'error' : 'inactive';
                
                if (recordingFilter !== recordingStatus) return false;
            }
            
            // Location filter
            if (locationFilter && camera.location !== locationFilter) return false;
            
            // Search filter
            if (searchFilter) {
                const searchableText = [
                    camera.name,
                    camera.location,
                    camera.ip_address,
                    camera.brand,
                    camera.model
                ].filter(Boolean).join(' ').toLowerCase();
                
                if (!searchableText.includes(searchFilter)) return false;
            }
            
            return true;
        });
        
        this.renderCameraGrid();
    }
    
    clearFilters() {
        document.getElementById('camera-status-filter').value = '';
        document.getElementById('recording-filter').value = '';
        document.getElementById('camera-location-filter').value = '';
        document.getElementById('camera-search-filter').value = '';
        
        this.filteredCameras = [...this.cameras];
        this.renderCameraGrid();
    }
    
    handleSearchInput(e) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.applyFilters();
        }, 300);
    }
    
    changeView(view) {
        this.currentView = view;
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        this.renderCameraGrid();
    }
    
    // === REFRESH AND AUTO-UPDATE ===
    
    async refreshCameras() {
        const refreshBtn = document.getElementById('refresh-cameras-btn');
        const icon = refreshBtn?.querySelector('i');
        
        if (icon) {
            icon.classList.add('fa-spin');
        }
        if (refreshBtn) {
            refreshBtn.disabled = true;
        }
        
        try {
            await this.loadCameras();
            await this.performHealthCheck();
            this.showToast('System refreshed successfully', 'success');
        } catch (error) {
            this.showToast('Failed to refresh system', 'error');
        } finally {
            if (icon) {
                icon.classList.remove('fa-spin');
            }
            if (refreshBtn) {
                refreshBtn.disabled = false;
            }
        }
    }
    
    async refreshCameraData() {
        // Refresh camera snapshots
        this.cameras.forEach(camera => {
            this.refreshSnapshot(camera.id);
        });
    }
    
    handleVisibilityChange() {
        this.isPageActive = !document.hidden;
        
        if (this.isPageActive) {
            console.log('👁️ Page active - resuming monitoring');
            this.refreshCameraData();
        } else {
            console.log('👁️ Page inactive - monitoring continues in background');
        }
    }
    
    // === WEBSOCKET UPDATES ===
    
    setupWebSocketUpdates() {
        if (!config.FEATURES.WEBSOCKET_UPDATES) {
            console.log('WebSocket updates disabled');
            return;
        }
        
        console.log('🔌 Setting up WebSocket real-time updates');
        
        WebSocketService.connect();
        
        // Subscribe to relevant events
        const subscriptions = [
            WebSocketService.subscribe('camera_health', data => this.handleCameraHealthUpdate(data)),
            WebSocketService.subscribe('recording_status', data => this.handleRecordingStatusUpdate(data)),
            WebSocketService.subscribe('system_alert', data => this.handleSystemAlert(data))
        ];
        
        this.webSocketSubscriptions = subscriptions;
        
        console.log('✅ WebSocket subscriptions established');
    }
    
    handleCameraHealthUpdate(data) {
        const { cameraId, health } = data;
        this.cameraHealthData.set(cameraId, health);
        this.updateCameraHealthDisplay(cameraId, health, this.recordingHealthData.get(cameraId));
    }
    
    handleRecordingStatusUpdate(data) {
        const { cameraId, recording } = data;
        this.recordingHealthData.set(cameraId, recording);
        this.updateCameraHealthDisplay(cameraId, this.cameraHealthData.get(cameraId), recording);
    }
    
    handleSystemAlert(data) {
        this.systemAlerts.set(data.id, data);
        this.showSystemAlert(data);
    }
    
    // === ALERT SYSTEM ===
    
    showSystemAlert(alert) {
        // Show system-wide alerts
        this.showToast(alert.message, alert.type);
    }
    
    dismissAlerts() {
        const alertsBanner = document.getElementById('alerts-banner');
        if (alertsBanner) {
            alertsBanner.style.display = 'none';
        }
        this.systemAlerts.clear();
    }
    
    // === TOAST NOTIFICATIONS ===
    
    showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `professional-toast toast-${type}`;
        
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${iconMap[type] || iconMap.info}"></i>
            </div>
            <div class="toast-content">
                <span class="toast-message">${message}</span>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Toast styling
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            minWidth: '350px',
            maxWidth: '500px',
            padding: '16px 20px',
            backgroundColor: type === 'success' ? '#10b981' : 
                            type === 'error' ? '#ef4444' : 
                            type === 'warning' ? '#f59e0b' : '#3b82f6',
            color: 'white',
            borderRadius: '8px',
            zIndex: '10001',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
            fontSize: '14px',
            lineHeight: '1.4',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        });
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Auto-dismiss
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }
        }, duration);
    }
    
    // === CLEANUP ===
    
    destroy() {
        console.log('🧹 Cleaning up Professional Camera System');
        
        // Clear intervals
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }
        
        // Cleanup WebSocket subscriptions
        this.webSocketSubscriptions.forEach(unsubscribe => {
            if (typeof unsubscribe === 'function') {
                unsubscribe();
            }
        });
        
        if (config.FEATURES.WEBSOCKET_UPDATES) {
            WebSocketService.disconnect();
        }
        
        // Remove event listeners
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Clear references
        delete window.autoCamerasPage;
        
        console.log('✅ Professional Camera System cleaned up');
    }
}

export default AutoCamerasPage;