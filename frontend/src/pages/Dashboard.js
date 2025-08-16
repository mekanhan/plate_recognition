/**
 * Dashboard Page Component
 * Main dashboard with metrics, camera status, and system overview
 */
// Removed live streaming imports to eliminate conflicts with Cameras page
import playbackService from '../services/PlaybackService.js';
import config from '../config/app.config.js';
import DetectionConsole from '../components/console/DetectionConsole.js';
import webSocketService from '../services/WebSocketService.js';

class Dashboard {
    constructor() {
        this.metrics = {
            activeCameras: 12,
            detectionsToday: 1247,
            activeAlerts: 3,
            accuracyRate: 94.2
        };
        this.storageStats = {
            totalRecordings: 0,
            storageUsed: '0 B',
            diskUsage: 0,
            retentionDays: 30
        };
        // Removed live feed components to prevent streaming conflicts
        this.recentDetections = [];
        this.systemHealth = {
            status: 'healthy',
            metrics: []
        };
        this.refreshInterval = null;
        this.selectedCameraCount = 4;
        this.currentPage = 0;
        this.detectionConsole = null;
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
        
        // Initialize detection console after DOM is ready
        setTimeout(() => {
            this.initializeDetectionConsole();
        }, 100);
        
        this.loadData();
        this.startAutoRefresh();
    }

    render() {
        const container = document.getElementById('dashboard');
        if (!container) return;

        container.innerHTML = this.getTemplate();
        this.renderRecentDetections();
        this.renderSystemHealth();
        this.renderCameraStatusPlaceholder();
    }

    initializeDetectionConsole() {
        try {
            console.log('Initializing detection console...');
            
            // Initialize detection console
            this.detectionConsole = new DetectionConsole();
            console.log('DetectionConsole instance created');
            
            const consoleContainer = document.getElementById('detection-console-container');
            console.log('Console container found:', !!consoleContainer);
            
            if (consoleContainer) {
                const consoleElement = this.detectionConsole.getElement();
                console.log('Console element created:', !!consoleElement);
                consoleContainer.appendChild(consoleElement);
                console.log('Console element appended to container');
            } else {
                console.error('detection-console-container not found in DOM');
            }
            
            // Connect WebSocket service for real-time updates
            webSocketService.connect();
            console.log('WebSocket service connected');
            
            console.log('Detection console initialization complete');
        } catch (error) {
            console.error('Error initializing detection console:', error);
        }
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

            <!-- Storage & Recording Metrics -->
            <div class="storage-metrics-section">
                <div class="section-header">
                    <h2>Recording & Storage</h2>
                    <div class="section-actions">
                        <button class="btn btn-secondary" id="view-recordings-btn">
                            <i class="fas fa-film"></i>
                            View Recordings
                        </button>
                        <span class="recording-status" id="recording-status">
                            <i class="fas fa-circle text-red"></i>
                            <span>Recording: Unknown</span>
                        </span>
                    </div>
                </div>
                
                <div class="storage-metrics-grid">
                    <div class="storage-metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-video text-blue"></i>
                        </div>
                        <div class="metric-content">
                            <h3 id="total-recordings">${this.storageStats.totalRecordings}</h3>
                            <p>Total Recordings</p>
                            <small class="metric-detail">Across all cameras</small>
                        </div>
                    </div>
                    
                    <div class="storage-metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-hdd text-green"></i>
                        </div>
                        <div class="metric-content">
                            <h3 id="storage-used">${this.storageStats.storageUsed}</h3>
                            <p>Storage Used</p>
                            <small class="metric-detail">Video files</small>
                        </div>
                    </div>
                    
                    <div class="storage-metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-chart-pie text-orange"></i>
                        </div>
                        <div class="metric-content">
                            <h3 id="disk-usage">${this.storageStats.diskUsage}%</h3>
                            <p>Disk Usage</p>
                            <small class="metric-detail">Overall system</small>
                        </div>
                    </div>
                    
                    <div class="storage-metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-calendar-alt text-purple"></i>
                        </div>
                        <div class="metric-content">
                            <h3 id="retention-days">${this.storageStats.retentionDays}</h3>
                            <p>Retention Days</p>
                            <small class="metric-detail">Auto cleanup</small>
                        </div>
                    </div>
                </div>
                
                <!-- Detection Console Section -->
                <div class="detection-console-section-full">
                    <div id="detection-console-container">
                        <!-- Detection console will be rendered here by JavaScript -->
                    </div>
                </div>
            </div>

            <!-- Real-time Section -->
            <div class="dashboard-grid">
                <!-- Camera Status Summary -->
                <div class="camera-status-overview">
                    <div class="card-header">
                        <h3>Camera Status Overview</h3>
                        <div class="card-actions">
                            <button class="card-action" id="view-cameras-btn">
                                <i class="fas fa-video"></i>
                                View Cameras
                            </button>
                        </div>
                    </div>
                    <div class="camera-status-grid" id="camera-status-grid">
                        <!-- Camera status will be dynamically loaded -->
                    </div>
                </div>

                <!-- Recent Detections -->
                <div class="recent-detections">
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
                <div class="system-health">
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
                <div class="analytics-chart">
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
        document.getElementById('export-data')?.addEventListener('click', () => this.handleExportData());
        document.getElementById('system-health')?.addEventListener('click', () => this.handleSystemHealth());

        // Metric cards navigation
        document.querySelectorAll('.metric-card[data-action]').forEach(card => {
            card.addEventListener('click', (e) => this.handleMetricClick(e));
        });

        // Camera status controls
        document.getElementById('view-cameras-btn')?.addEventListener('click', () => this.navigateToCameras());

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

    navigateToCameras() {
        // Navigate to cameras page for live streaming
        window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'cameras' } }));
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

    // Removed camera count handling - streaming moved to Cameras page

    // Removed feed control methods - streaming moved to Cameras page

    // Removed streaming control methods - moved to Cameras page

    // Removed UI update methods - no longer needed without streaming

    // Removed pagination methods - no longer needed

    // Removed player event handlers - no longer needed

    async loadCameraStatus() {
        try {
            // Simplified camera status loading without streaming
            const url = config.buildApiUrl(config.API_ENDPOINTS.CAMERAS);
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Handle different response formats
            let cameras = [];
            if (Array.isArray(data)) {
                cameras = data;
            } else if (data.cameras && Array.isArray(data.cameras)) {
                cameras = data.cameras;
            } else if (data.data && Array.isArray(data.data)) {
                cameras = data.data;
            } else {
                console.warn('Unexpected API response format:', data);
                cameras = [];
            }
            
            this.renderCameraStatus(cameras.filter(camera => camera.enabled));
        } catch (error) {
            console.error('Failed to load camera status:', error);
            this.renderCameraStatusError();
        }
    }

    renderCameraStatus(cameras) {
        const container = document.getElementById('camera-status-grid');
        if (!container) return;

        if (!cameras.length) {
            this.renderNoCamerasMessage();
            return;
        }

        container.innerHTML = cameras.map(camera => this.renderCameraStatusItem(camera)).join('');
    }

    renderCameraStatusItem(camera) {
        return `
            <div class="camera-status-item ${camera.status}" data-camera-id="${camera.id}">
                <div class="camera-status-header">
                    <span class="camera-name">${camera.name}</span>
                    <div class="camera-status-indicator ${camera.status}">
                        <i class="fas ${this.getStatusIcon(camera.status)}"></i>
                        <span class="status-text">${this.capitalizeFirst(camera.status)}</span>
                    </div>
                </div>
                
                <div class="camera-info">
                    <div class="camera-detail">
                        <span class="label">Location:</span>
                        <span class="value">${camera.location || 'Unknown'}</span>
                    </div>
                    <div class="camera-detail">
                        <span class="label">IP:</span>
                        <span class="value">${camera.ip_address}:${camera.port}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Removed player initialization - no longer needed

    renderNoCamerasMessage() {
        const container = document.getElementById('camera-status-grid');
        if (!container) return;

        container.innerHTML = `
            <div class="no-cameras-message">
                <div class="no-cameras-content">
                    <i class="fas fa-video-slash"></i>
                    <h3>No Cameras Configured</h3>
                    <p>Add cameras to monitor system status</p>
                    <button class="btn btn-primary" onclick="window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'cameras', action: 'add' } }))">
                        <i class="fas fa-plus"></i>
                        Add Camera
                    </button>
                </div>
            </div>
        `;
    }

    renderCameraStatusError() {
        const container = document.getElementById('camera-status-grid');
        if (!container) return;

        container.innerHTML = `
            <div class="camera-status-error">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Failed to load camera status</span>
            </div>
        `;
    }

    renderCameraStatusPlaceholder() {
        const container = document.getElementById('camera-status-grid');
        if (!container) return;

        container.innerHTML = `
            <div class="camera-status-loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading camera status...</span>
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
            
            // Load camera status overview
            await this.loadCameraStatus();
            
            // Load storage and recording data
            await this.loadStorageData();
            
            // Update other sections
            this.updateMetrics();
            this.renderRecentDetections();
            this.renderSystemHealth();
            this.updateStorageMetrics();
            
            // Removed streaming service setup
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showAlert('Failed to load dashboard data', 'error');
        }
    }

    // Removed streaming service event listeners

    // Removed camera status update method

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
        
        // Cleanup detection console
        if (this.detectionConsole) {
            this.detectionConsole.destroy();
            this.detectionConsole = null;
        }
        
        // Note: Don't disconnect WebSocket as other components might use it
    }

    // Storage and Recording Methods
    async loadStorageData() {
        try {
            // Get storage report
            const storageReport = await playbackService.getStorageReport();
            
            if (storageReport && storageReport.system_stats) {
                this.storageStats = {
                    totalRecordings: storageReport.system_stats.total_segments || 0,
                    storageUsed: storageReport.system_stats.total_size_formatted || '0 B',
                    diskUsage: Math.round(storageReport.system_stats.disk_used_percent || 0),
                    retentionDays: storageReport.retention_days || 30
                };
            }

            // Check recording status
            await this.checkRecordingStatus();

        } catch (error) {
            console.warn('Recording service unavailable - using default values:', error.message);
            // Use default values when recording service is stopped
            this.storageStats = {
                totalRecordings: 0,
                storageUsed: 'Service offline',
                diskUsage: 0,
                retentionDays: 30
            };
            this.updateRecordingStatusOffline();
        }
    }

    async checkRecordingStatus() {
        try {
            const health = await playbackService.getHealth();
            const recordingStatusEl = document.getElementById('recording-status');
            
            if (recordingStatusEl) {
                const isRecording = health.status === 'healthy' && health.storage_status === 'healthy';
                const statusIcon = recordingStatusEl.querySelector('i');
                const statusText = recordingStatusEl.querySelector('span');
                
                if (isRecording) {
                    statusIcon.className = 'fas fa-circle text-green';
                    statusText.textContent = 'Recording: Active';
                } else {
                    statusIcon.className = 'fas fa-circle text-red';
                    statusText.textContent = 'Recording: Inactive';
                }
            }
        } catch (error) {
            console.warn('Recording service health check failed:', error.message);
            this.updateRecordingStatusOffline();
        }
    }

    updateRecordingStatusOffline() {
        const recordingStatusEl = document.getElementById('recording-status');
        if (recordingStatusEl) {
            const statusIcon = recordingStatusEl.querySelector('i');
            const statusText = recordingStatusEl.querySelector('span');
            
            if (statusIcon && statusText) {
                statusIcon.className = 'fas fa-circle text-gray';
                statusText.textContent = 'Recording: Service Offline';
            }
        }
    }

    updateStorageMetrics() {
        // Update storage metric values
        const totalRecordingsEl = document.getElementById('total-recordings');
        const storageUsedEl = document.getElementById('storage-used');
        const diskUsageEl = document.getElementById('disk-usage');
        const retentionDaysEl = document.getElementById('retention-days');

        if (totalRecordingsEl) totalRecordingsEl.textContent = this.storageStats.totalRecordings;
        if (storageUsedEl) storageUsedEl.textContent = this.storageStats.storageUsed;
        if (diskUsageEl) diskUsageEl.textContent = `${this.storageStats.diskUsage}%`;
        if (retentionDaysEl) retentionDaysEl.textContent = this.storageStats.retentionDays;

        // Update disk usage color based on percentage
        if (diskUsageEl && diskUsageEl.parentElement) {
            const card = diskUsageEl.closest('.storage-metric-card');
            if (card) {
                const icon = card.querySelector('.metric-icon i');
                if (this.storageStats.diskUsage >= 90) {
                    icon.className = 'fas fa-chart-pie text-red';
                } else if (this.storageStats.diskUsage >= 80) {
                    icon.className = 'fas fa-chart-pie text-orange';
                } else {
                    icon.className = 'fas fa-chart-pie text-green';
                }
            }
        }
    }


}


export default Dashboard;