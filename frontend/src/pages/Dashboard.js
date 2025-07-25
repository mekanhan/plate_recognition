/**
 * Dashboard Page Component
 * Main dashboard with metrics, live feeds, and system overview
 */
import LiveVideoPlayer from '../components/streaming/LiveVideoPlayer.js';
import streamingService from '../services/StreamingService.js';

class Dashboard {
    constructor() {
        this.metrics = {
            activeCameras: 12,
            detectionsToday: 1247,
            activeAlerts: 3,
            accuracyRate: 94.2
        };
        this.liveFeeds = [];
        this.liveCameras = [];
        this.videoPlayers = new Map();
        this.recentDetections = [];
        this.systemHealth = {
            status: 'healthy',
            metrics: []
        };
        this.refreshInterval = null;
        this.selectedCameraCount = 4;
        this.currentPage = 0;
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
        this.loadData();
        this.startAutoRefresh();
    }

    render() {
        const container = document.getElementById('dashboard');
        if (!container) return;

        container.innerHTML = this.getTemplate();
        this.renderLiveFeeds();
        this.renderRecentDetections();
        this.renderSystemHealth();
    }

    getTemplate() {
        return `
            <div class="page-header">
                <h1 class="page-title">Dashboard</h1>
                <p class="page-subtitle">Real-time monitoring and system overview</p>
            </div>

            <!-- Quick Actions Bar -->
            <div class="quick-actions">
                <button class="quick-action-btn" id="add-camera-quick">
                    <i class="fas fa-plus"></i>
                    <span>Add Camera</span>
                </button>
                <button class="quick-action-btn" id="view-live-feeds">
                    <i class="fas fa-play"></i>
                    <span>Live Feeds</span>
                </button>
                <button class="quick-action-btn" id="export-data">
                    <i class="fas fa-download"></i>
                    <span>Export Data</span>
                </button>
                <button class="quick-action-btn" id="system-health">
                    <i class="fas fa-heartbeat"></i>
                    <span>System Health</span>
                </button>
            </div>

            <!-- Key Metrics -->
            <div class="metrics-grid">
                <div class="metric-card clickable" data-action="view-cameras" style="animation-delay: 0.1s">
                    <div class="metric-icon">
                        <i class="fas fa-video text-blue"></i>
                    </div>
                    <div class="metric-content">
                        <h3 id="active-cameras-count">${this.metrics.activeCameras}</h3>
                        <p>Active Cameras</p>
                        <span class="metric-change positive">+2 this week</span>
                    </div>
                    <div class="metric-trend">
                        <i class="fas fa-arrow-up"></i>
                    </div>
                </div>
                
                <div class="metric-card clickable" data-action="view-detections" style="animation-delay: 0.2s">
                    <div class="metric-icon">
                        <i class="fas fa-car text-green"></i>
                    </div>
                    <div class="metric-content">
                        <h3 id="detections-today">${this.metrics.detectionsToday.toLocaleString()}</h3>
                        <p>Detections Today</p>
                        <span class="metric-change positive">+8.5%</span>
                    </div>
                    <div class="metric-trend">
                        <i class="fas fa-arrow-up"></i>
                    </div>
                </div>
                
                <div class="metric-card clickable" data-action="view-alerts" style="animation-delay: 0.3s">
                    <div class="metric-icon">
                        <i class="fas fa-exclamation-triangle text-orange"></i>
                    </div>
                    <div class="metric-content">
                        <h3 id="active-alerts-count">${this.metrics.activeAlerts}</h3>
                        <p>Active Alerts</p>
                        <span class="metric-change neutral">2 resolved</span>
                    </div>
                    <div class="metric-trend">
                        <i class="fas fa-minus"></i>
                    </div>
                </div>
                
                <div class="metric-card clickable" data-action="view-analytics" style="animation-delay: 0.4s">
                    <div class="metric-icon">
                        <i class="fas fa-percentage text-purple"></i>
                    </div>
                    <div class="metric-content">
                        <h3 id="accuracy-rate">${this.metrics.accuracyRate}%</h3>
                        <p>Detection Accuracy</p>
                        <span class="metric-change positive">+1.2%</span>
                    </div>
                    <div class="metric-trend">
                        <i class="fas fa-arrow-up"></i>
                    </div>
                </div>
            </div>

            <!-- Real-time Section -->
            <div class="dashboard-grid">
                <!-- Live Camera Feeds -->
                <div class="dashboard-card camera-feeds">
                    <div class="card-header">
                        <h3>Live Camera Feeds</h3>
                        <div class="card-actions">
                            <select id="camera-count-select" class="camera-count-select">
                                <option value="1">1 Camera</option>
                                <option value="2">2 Cameras</option>
                                <option value="3">3 Cameras</option>
                                <option value="4" selected>4 Cameras</option>
                            </select>
                            <button class="card-action" id="camera-layout-btn">
                                <i class="fas fa-th"></i>
                            </button>
                            <button class="card-action" id="fullscreen-feeds">
                                <i class="fas fa-expand"></i>
                            </button>
                        </div>
                    </div>
                    <div class="camera-grid" id="live-camera-grid">
                        <!-- Live feeds will be dynamically loaded -->
                    </div>
                    <div class="camera-pagination" id="camera-pagination">
                        <!-- Pagination will be dynamically added if needed -->
                    </div>
                </div>

                <!-- Recent Detections -->
                <div class="dashboard-card recent-detections">
                    <div class="card-header">
                        <h3>Recent Detections</h3>
                        <div class="card-actions">
                            <button class="card-action" id="filter-detections">
                                <i class="fas fa-filter"></i>
                            </button>
                            <button class="card-action" id="view-all-detections">View All</button>
                        </div>
                    </div>
                    <div class="detections-list" id="recent-detections-list">
                        <!-- Recent detections will be dynamically loaded -->
                    </div>
                </div>

                <!-- System Health -->
                <div class="dashboard-card system-health">
                    <div class="card-header">
                        <h3>System Health</h3>
                        <div class="health-indicator ${this.systemHealth.status}">
                            <i class="fas fa-check-circle"></i>
                            <span id="system-status-text">${this.capitalizeFirst(this.systemHealth.status)}</span>
                        </div>
                    </div>
                    <div class="health-metrics" id="health-metrics">
                        <!-- Health metrics will be dynamically loaded -->
                    </div>
                    <div class="health-actions">
                        <button class="btn btn-small" id="run-diagnostics">Run Diagnostics</button>
                        <button class="btn btn-small btn-secondary" id="view-logs">View Logs</button>
                    </div>
                </div>

                <!-- Analytics Chart -->
                <div class="dashboard-card analytics-chart">
                    <div class="card-header">
                        <h3>Detection Analytics</h3>
                        <select class="chart-filter" id="chart-time-filter">
                            <option value="24h">Last 24 Hours</option>
                            <option value="7d">Last 7 Days</option>
                            <option value="30d">Last 30 Days</option>
                            <option value="90d">Last 90 Days</option>
                        </select>
                    </div>
                    <div class="chart-container">
                        <div style="text-align: center;">
                            <i class="fas fa-chart-line" style="font-size: 3rem; margin-bottom: 1rem; display: block;"></i>
                            <p>Detection Analytics Chart</p>
                            <small>Real-time detection trends and patterns</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Alert Banner -->
            <div class="alert-banner" id="alert-banner" style="display: none;">
                <div class="alert-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span class="alert-message"></span>
                </div>
                <button class="alert-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    }

    attachEventListeners() {
        // Quick action buttons
        document.getElementById('add-camera-quick')?.addEventListener('click', () => this.handleAddCamera());
        document.getElementById('view-live-feeds')?.addEventListener('click', () => this.handleViewLiveFeeds());
        document.getElementById('export-data')?.addEventListener('click', () => this.handleExportData());
        document.getElementById('system-health')?.addEventListener('click', () => this.handleSystemHealth());

        // Metric cards navigation
        document.querySelectorAll('.metric-card[data-action]').forEach(card => {
            card.addEventListener('click', (e) => this.handleMetricClick(e));
        });

        // Camera feed controls
        document.getElementById('camera-count-select')?.addEventListener('change', (e) => this.handleCameraCountChange(e));
        document.getElementById('camera-layout-btn')?.addEventListener('click', () => this.toggleCameraLayout());
        document.getElementById('fullscreen-feeds')?.addEventListener('click', () => this.toggleFullscreenFeeds());

        // Detection controls
        document.getElementById('filter-detections')?.addEventListener('click', () => this.showDetectionFilters());
        document.getElementById('view-all-detections')?.addEventListener('click', () => this.navigateToDetections());

        // System health controls
        document.getElementById('run-diagnostics')?.addEventListener('click', () => this.runDiagnostics());
        document.getElementById('view-logs')?.addEventListener('click', () => this.viewSystemLogs());

        // Chart controls
        document.getElementById('chart-time-filter')?.addEventListener('change', (e) => this.updateChart(e.target.value));

        // Alert banner close
        document.querySelector('.alert-close')?.addEventListener('click', () => this.closeAlertBanner());

        // Global data refresh listener
        window.addEventListener('dataRefresh', () => this.loadData());
    }

    handleAddCamera() {
        // Navigate to cameras page and trigger add camera modal
        window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'cameras', action: 'add' } }));
    }

    handleViewLiveFeeds() {
        // Show fullscreen live feeds
        this.toggleFullscreenFeeds();
    }

    handleExportData() {
        // Show export options modal
        this.showExportModal();
    }

    handleSystemHealth() {
        // Navigate to system health section
        window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'settings', section: 'system' } }));
    }

    handleMetricClick(e) {
        const action = e.currentTarget.dataset.action;
        const pageMap = {
            'view-cameras': 'cameras',
            'view-detections': 'detections',
            'view-alerts': 'alerts',
            'view-analytics': 'analytics'
        };
        
        if (pageMap[action]) {
            window.dispatchEvent(new CustomEvent('navigate', { detail: { page: pageMap[action] } }));
        }
    }

    handleCameraCountChange(e) {
        const count = parseInt(e.target.value);
        this.selectedCameraCount = count;
        this.currentPage = 0; // Reset to first page
        this.renderLiveFeeds();
    }

    attachFeedControlListeners() {
        document.querySelectorAll('.feed-control-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFeedControl(e));
        });
    }

    async handleFeedControl(e) {
        e.preventDefault();
        const action = e.target.dataset.action || e.target.parentElement.dataset.action;
        const cameraId = e.target.dataset.cameraId || e.target.parentElement.dataset.cameraId;
        
        if (!cameraId) return;
        
        const camera = this.liveCameras.find(c => c.id.toString() === cameraId);
        if (!camera) return;

        switch (action) {
            case 'stream':
                await this.toggleCameraStream(cameraId);
                break;
            case 'fullscreen':
                this.openFullscreenFeed(cameraId);
                break;
            case 'refresh':
                await this.refreshCameraFeed(cameraId);
                break;
        }
    }

    async toggleCameraStream(cameraId) {
        const player = this.videoPlayers.get(cameraId);
        if (!player) return;

        const isStreaming = streamingService.isStreamActive(cameraId);
        
        try {
            if (isStreaming) {
                await player.stopStream();
            } else {
                await player.startStream();
            }
            
            // Update UI
            this.updateFeedControlButton(cameraId);
            this.updateCameraStatusIndicator(cameraId);
            
        } catch (error) {
            console.error('Failed to toggle stream:', error);
            this.showAlert(`Failed to ${isStreaming ? 'stop' : 'start'} stream for camera`, 'error');
        }
    }

    openFullscreenFeed(cameraId) {
        const player = this.videoPlayers.get(cameraId);
        if (player && streamingService.isStreamActive(cameraId)) {
            player.openFullscreen();
        } else {
            this.showAlert('Start streaming to view in fullscreen', 'info');
        }
    }

    async refreshCameraFeed(cameraId) {
        const player = this.videoPlayers.get(cameraId);
        if (player) {
            await player.refreshThumbnail();
        }
    }

    updateFeedControlButton(cameraId) {
        const btn = document.querySelector(`[data-action="stream"][data-camera-id="${cameraId}"]`);
        if (!btn) return;

        const isStreaming = streamingService.isStreamActive(cameraId);
        const icon = btn.querySelector('i');
        const text = btn.childNodes[btn.childNodes.length - 1];

        if (icon) {
            icon.className = `fas ${isStreaming ? 'fa-stop' : 'fa-play'}`;
        }
        if (text && text.textContent) {
            text.textContent = isStreaming ? 'Stop' : 'Start';
        }
    }

    updateCameraStatusIndicator(cameraId) {
        const indicator = document.querySelector(`[data-camera-id="${cameraId}"] .camera-status-indicator`);
        if (!indicator) return;

        const isStreaming = streamingService.isStreamActive(cameraId);
        const existingBadge = indicator.querySelector('.streaming-badge');
        
        if (isStreaming && !existingBadge) {
            indicator.insertAdjacentHTML('beforeend', '<span class="streaming-badge">LIVE</span>');
        } else if (!isStreaming && existingBadge) {
            existingBadge.remove();
        }
    }

    updateFeedPagination() {
        const paginationContainer = document.getElementById('camera-pagination');
        if (!paginationContainer) return;

        const totalPages = Math.ceil(this.liveCameras.length / this.selectedCameraCount);
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        const pagination = [];
        
        // Previous button
        pagination.push(`
            <button class="pagination-btn ${this.currentPage === 0 ? 'disabled' : ''}" 
                    data-page="${this.currentPage - 1}" ${this.currentPage === 0 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i>
            </button>
        `);

        // Page numbers
        for (let i = 0; i < totalPages; i++) {
            pagination.push(`
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                        data-page="${i}">
                    ${i + 1}
                </button>
            `);
        }

        // Next button
        pagination.push(`
            <button class="pagination-btn ${this.currentPage === totalPages - 1 ? 'disabled' : ''}" 
                    data-page="${this.currentPage + 1}" ${this.currentPage === totalPages - 1 ? 'disabled' : ''}>
                <i class="fas fa-chevron-right"></i>
            </button>
        `);

        paginationContainer.innerHTML = pagination.join('');

        // Attach pagination event listeners
        paginationContainer.querySelectorAll('.pagination-btn:not(.disabled)').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt(e.target.dataset.page);
                if (!isNaN(page) && page !== this.currentPage) {
                    this.currentPage = page;
                    this.renderLiveFeeds();
                }
            });
        });
    }

    // Player event handlers
    handlePlayerStatusChange(cameraId, status) {
        console.log(`Camera ${cameraId} status changed to: ${status}`);
        this.updateCameraStatusIndicator(cameraId);
    }

    handlePlayerError(cameraId, error) {
        console.error(`Camera ${cameraId} error:`, error);
        this.showAlert(`Camera error: ${error}`, 'error');
    }

    handleStreamStart(cameraId) {
        console.log(`Stream started for camera ${cameraId}`);
        this.updateFeedControlButton(cameraId);
        this.updateCameraStatusIndicator(cameraId);
    }

    handleStreamStop(cameraId) {
        console.log(`Stream stopped for camera ${cameraId}`);
        this.updateFeedControlButton(cameraId);
        this.updateCameraStatusIndicator(cameraId);
    }

    async loadLiveCameras() {
        try {
            const cameras = await streamingService.getCameras();
            
            // Filter for enabled cameras and transform data
            this.liveCameras = cameras
                .filter(camera => camera.enabled)
                .map(camera => ({
                    id: camera.id,
                    name: camera.name,
                    location: camera.location || 'unknown',
                    status: camera.status || 'offline',
                    ipAddress: camera.ip_address,
                    port: camera.port,
                    connectionType: camera.connection_type,
                    streamPath: camera.stream_path,
                    lastSeen: camera.updated_at ? new Date(camera.updated_at) : new Date(),
                    enabled: camera.enabled,
                    isStreaming: streamingService.isStreamActive(camera.id)
                }));
                
            this.renderLiveFeeds();
        } catch (error) {
            console.error('Failed to load cameras:', error);
            this.showAlert('Failed to load camera feeds', 'error');
            this.renderNoFeedsMessage();
        }
    }

    renderLiveFeeds() {
        const container = document.getElementById('live-camera-grid');
        if (!container) return;

        if (!this.liveCameras.length) {
            this.renderNoFeedsMessage();
            return;
        }

        // Apply camera count filter and pagination
        const startIndex = this.currentPage * this.selectedCameraCount;
        const displayCameras = this.liveCameras.slice(startIndex, startIndex + this.selectedCameraCount);

        // Update grid layout class
        container.className = `camera-grid layout-${Math.min(displayCameras.length, this.selectedCameraCount)}`;

        container.innerHTML = displayCameras.map(camera => this.renderCameraFeedItem(camera)).join('');

        // Initialize video players for each camera
        displayCameras.forEach(camera => {
            this.initializeCameraPlayer(camera);
        });

        // Attach event listeners
        this.attachFeedControlListeners();

        // Update pagination if needed
        this.updateFeedPagination();
    }

    renderCameraFeedItem(camera) {
        const isStreaming = streamingService.isStreamActive(camera.id);
        
        return `
            <div class="camera-feed-item ${camera.status}" data-camera-id="${camera.id}">
                <div class="camera-feed-header">
                    <span class="camera-name">${camera.name}</span>
                    <div class="camera-status-indicator ${camera.status}">
                        <i class="fas ${this.getStatusIcon(camera.status)}"></i>
                        <span class="status-text">${this.capitalizeFirst(camera.status)}</span>
                        ${isStreaming ? '<span class="streaming-badge">LIVE</span>' : ''}
                    </div>
                </div>
                
                <div class="camera-feed-video" id="feed-video-${camera.id}">
                    <!-- LiveVideoPlayer will be inserted here -->
                </div>
                
                <div class="camera-feed-controls">
                    <button class="feed-control-btn" data-action="stream" data-camera-id="${camera.id}" 
                            ${camera.status !== 'online' ? 'disabled' : ''}>
                        <i class="fas ${isStreaming ? 'fa-stop' : 'fa-play'}"></i>
                        ${isStreaming ? 'Stop' : 'Start'}
                    </button>
                    <button class="feed-control-btn" data-action="fullscreen" data-camera-id="${camera.id}">
                        <i class="fas fa-expand"></i>
                        Fullscreen
                    </button>
                    <button class="feed-control-btn" data-action="refresh" data-camera-id="${camera.id}">
                        <i class="fas fa-sync-alt"></i>
                        Refresh
                    </button>
                </div>
            </div>
        `;
    }

    initializeCameraPlayer(camera) {
        const videoContainer = document.getElementById(`feed-video-${camera.id}`);
        if (!videoContainer) return;

        // Create LiveVideoPlayer instance
        const player = new LiveVideoPlayer({
            cameraId: camera.id,
            camera: camera,
            autoStart: false,
            showControls: false, // We'll use external controls
            className: 'dashboard-feed-player',
            onStatusChange: (status) => this.handlePlayerStatusChange(camera.id, status),
            onError: (error) => this.handlePlayerError(camera.id, error),
            onStreamStart: () => this.handleStreamStart(camera.id),
            onStreamStop: () => this.handleStreamStop(camera.id)
        });

        // Render and initialize player
        videoContainer.innerHTML = player.render();
        player.init();

        // Store player reference
        this.videoPlayers.set(camera.id, player);
    }

    renderNoFeedsMessage() {
        const container = document.getElementById('live-camera-grid');
        if (!container) return;

        container.innerHTML = `
            <div class="no-feeds-message">
                <div class="no-feeds-content">
                    <i class="fas fa-video-slash"></i>
                    <h3>No Camera Feeds Available</h3>
                    <p>Add cameras to start monitoring live feeds</p>
                    <button class="btn btn-primary" onclick="window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'cameras', action: 'add' } }))">
                        <i class="fas fa-plus"></i>
                        Add Camera
                    </button>
                </div>
            </div>
        `;
    }

    renderRecentDetections() {
        const container = document.getElementById('recent-detections-list');
        if (!container) return;

        // Simulate recent detections
        const mockDetections = [
            { plate: 'ABC-123', camera: 'Entrance Gate', time: '2 min ago', confidence: 98.5 },
            { plate: 'XYZ-789', camera: 'Parking Lot A', time: '5 min ago', confidence: 92.1 },
            { plate: 'DEF-456', camera: 'Loading Dock', time: '8 min ago', confidence: 87.3 },
            { plate: 'GHI-321', camera: 'Side Entrance', time: '12 min ago', confidence: 95.7 }
        ];

        container.innerHTML = mockDetections.map(detection => `
            <div class="detection-item">
                <div class="detection-plate">${detection.plate}</div>
                <div class="detection-details">
                    <span class="detection-camera">${detection.camera}</span>
                    <span class="detection-time">${detection.time}</span>
                </div>
                <div class="detection-confidence">
                    <span class="confidence-value">${detection.confidence}%</span>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${detection.confidence}%"></div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderSystemHealth() {
        const container = document.getElementById('health-metrics');
        if (!container) return;

        const healthMetrics = [
            { name: 'CPU Usage', value: 34, unit: '%', status: 'good' },
            { name: 'Memory Usage', value: 67, unit: '%', status: 'warning' },
            { name: 'Disk Usage', value: 23, unit: '%', status: 'good' },
            { name: 'Network', value: 98, unit: '%', status: 'good' }
        ];

        container.innerHTML = healthMetrics.map(metric => `
            <div class="health-metric">
                <div class="metric-label">${metric.name}</div>
                <div class="metric-value ${metric.status}">${metric.value}${metric.unit}</div>
                <div class="metric-bar">
                    <div class="metric-fill ${metric.status}" style="width: ${metric.value}%"></div>
                </div>
            </div>
        `).join('');
    }

    async loadData() {
        try {
            // Load basic dashboard data
            await this.simulateDataLoad();
            
            // Load live cameras with streaming integration
            await this.loadLiveCameras();
            
            // Update other sections
            this.updateMetrics();
            this.renderRecentDetections();
            this.renderSystemHealth();
            
            // Setup streaming service event listeners
            this.setupStreamingEventListeners();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showAlert('Failed to load dashboard data', 'error');
        }
    }

    setupStreamingEventListeners() {
        // Listen for streaming service events
        streamingService.on('streamStarted', (data) => {
            this.handleStreamStart(data.cameraId);
        });

        streamingService.on('streamStopped', (data) => {
            this.handleStreamStop(data.cameraId);
        });

        streamingService.on('streamError', (data) => {
            this.handlePlayerError(data.cameraId, data.error);
        });

        streamingService.on('statusUpdate', (data) => {
            // Update camera statuses based on server data
            this.updateCameraStatuses(data);
        });
    }

    updateCameraStatuses(statusData) {
        if (!statusData.activeStreams) return;

        const activeStreamIds = new Set(statusData.activeStreams.map(s => s.cameraId));
        
        // Update local camera data
        this.liveCameras.forEach(camera => {
            const wasStreaming = camera.isStreaming;
            camera.isStreaming = activeStreamIds.has(camera.id);
            
            // Update UI if status changed
            if (wasStreaming !== camera.isStreaming) {
                this.updateFeedControlButton(camera.id);
                this.updateCameraStatusIndicator(camera.id);
            }
        });
    }

    async simulateDataLoad() {
        return new Promise(resolve => setTimeout(resolve, 500));
    }

    updateMetrics() {
        // Update metric values in DOM
        document.getElementById('active-cameras-count').textContent = this.metrics.activeCameras;
        document.getElementById('detections-today').textContent = this.metrics.detectionsToday.toLocaleString();
        document.getElementById('active-alerts-count').textContent = this.metrics.activeAlerts;
        document.getElementById('accuracy-rate').textContent = `${this.metrics.accuracyRate}%`;
    }

    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadData();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    showAlert(message, type = 'info') {
        const alertBanner = document.getElementById('alert-banner');
        const alertMessage = alertBanner?.querySelector('.alert-message');
        
        if (alertBanner && alertMessage) {
            alertMessage.textContent = message;
            alertBanner.className = `alert-banner alert-${type}`;
            alertBanner.style.display = 'flex';
        }
    }

    closeAlertBanner() {
        const alertBanner = document.getElementById('alert-banner');
        if (alertBanner) {
            alertBanner.style.display = 'none';
        }
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    getStatusIcon(status) {
        const icons = {
            online: 'fa-circle',
            offline: 'fa-times-circle',
            warning: 'fa-exclamation-triangle'
        };
        return icons[status] || 'fa-question-circle';
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

    // Clean up when component is destroyed
    destroy() {
        this.stopAutoRefresh();
        
        // Cleanup video players
        this.videoPlayers.forEach(player => {
            player.destroy();
        });
        this.videoPlayers.clear();
        
        // Remove streaming service event listeners
        streamingService.off('streamStarted');
        streamingService.off('streamStopped');
        streamingService.off('streamError');
        streamingService.off('statusUpdate');
        
        // Stop any active streams
        this.liveCameras.forEach(camera => {
            if (camera.isStreaming) {
                streamingService.stopStream(camera.id).catch(console.error);
            }
        });
    }
}

export default Dashboard;