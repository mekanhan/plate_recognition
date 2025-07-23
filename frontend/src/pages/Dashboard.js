/**
 * Dashboard Page Component
 * Main dashboard with metrics, live feeds, and system overview
 */
class Dashboard {
    constructor() {
        this.metrics = {
            activeCameras: 12,
            detectionsToday: 1247,
            activeAlerts: 3,
            accuracyRate: 94.2
        };
        this.liveFeeds = [];
        this.recentDetections = [];
        this.systemHealth = {
            status: 'healthy',
            metrics: []
        };
        this.refreshInterval = null;
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
        this.updateCameraGrid(count);
    }

    renderLiveFeeds() {
        const container = document.getElementById('live-camera-grid');
        if (!container) return;

        // Simulate camera feeds
        const mockFeeds = [
            { id: 'cam1', name: 'Entrance Gate', status: 'online' },
            { id: 'cam2', name: 'Parking Lot A', status: 'online' },
            { id: 'cam3', name: 'Loading Dock', status: 'warning' },
            { id: 'cam4', name: 'Side Entrance', status: 'online' }
        ];

        container.innerHTML = mockFeeds.map(feed => `
            <div class="camera-feed-item ${feed.status}">
                <div class="camera-feed-header">
                    <span class="camera-name">${feed.name}</span>
                    <span class="camera-status ${feed.status}">
                        <i class="fas ${feed.status === 'online' ? 'fa-circle' : 'fa-exclamation-triangle'}"></i>
                    </span>
                </div>
                <div class="camera-feed-video">
                    <div class="video-placeholder">
                        <i class="fas fa-video"></i>
                        <span>Live Feed</span>
                    </div>
                </div>
                <div class="camera-feed-info">
                    <span class="resolution">1920x1080</span>
                    <span class="fps">30 FPS</span>
                </div>
            </div>
        `).join('');
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
            // In a real application, this would make API calls
            // For now, we'll simulate data loading
            await this.simulateDataLoad();
            this.updateMetrics();
            this.renderLiveFeeds();
            this.renderRecentDetections();
            this.renderSystemHealth();
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showAlert('Failed to load dashboard data', 'error');
        }
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

    // Clean up when component is destroyed
    destroy() {
        this.stopAutoRefresh();
        // Remove event listeners if needed
    }
}

export default Dashboard;