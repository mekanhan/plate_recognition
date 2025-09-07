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

            webSocketService.connect();
            console.log('WebSocket service connected');
            console.log('Detection console initialization complete');
        } catch (error) {
            console.error('Error initializing detection console:', error);
        }
    }getTemplate() {
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
                <div class="metric-card clickable" data-action="view-cameras" style="animation-delay:0.1s">
                    <div class="metric-icon">
                        <i class="fas fa-video text-blue"></i>
                    </div>
                    <div class="metric-content">
                        <h3 id="active-cameras-count">${this.metrics.activeCameras}</h3>
                        <p>Active Cameras</p>
                        <span class="metric-change" id="orphaned-cameras-info">
                            ${this.metrics.orphanedCameras || 0} orphaned
                        </span>
                    </div>
                    <div class="metric-trend">
                        <i class="fas fa-database"></i>
                    </div>
                </div>

                <div class="metric-card clickable" data-action="view-detections" style="animation-delay:0.2s">
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

                <div class="metric-card clickable" data-action="view-alerts" style="animation-delay:0.3s">
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

                <div class="metric-card clickable" data-action="view-analytics" style="animation-delay:0.4s">
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
                            <i class="fas fa-film"></i> View Recordings
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
                                <i class="fas fa-video"></i> View Cameras
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
                        <div style="text-align:center;">
                            <i class="fas fa-chart-line" style="font-size:3rem;margin-bottom:1rem;display:block;"></i>
                            <p>Detection Analytics Chart</p>
                            <small>Real-time detection trends and patterns</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Alert Banner -->
            <div class="alert-banner" id="alert-banner" style="display:none;">
                <div class="alert-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span class="alert-message"></span>
                </div>
                <button class="alert-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    }attachEventListeners() {
        document.getElementById('add-camera-quick')?.addEventListener('click', () => this.handleAddCamera());
        document.getElementById('export-data')?.addEventListener('click', () => this.handleExportData());
        document.getElementById('system-health')?.addEventListener('click', () => this.handleSystemHealth());

        document.querySelectorAll('.metric-card[data-action]').forEach(card => {
            card.addEventListener('click', (e) => this.handleMetricClick(e));
        });

        document.getElementById('view-cameras-btn')?.addEventListener('click', () => this.navigateToCameras());
        document.getElementById('filter-detections')?.addEventListener('click', () => this.showDetectionFilters());
        document.getElementById('view-all-detections')?.addEventListener('click', () => this.navigateToDetections());
        document.getElementById('run-diagnostics')?.addEventListener('click', () => this.runDiagnostics());
        document.getElementById('view-logs')?.addEventListener('click', () => this.viewSystemLogs());
        document.getElementById('chart-time-filter')?.addEventListener('change', (e) => this.updateChart(e.target.value));
        document.querySelector('.alert-close')?.addEventListener('click', () => this.closeAlertBanner());
        window.addEventListener('dataRefresh', () => this.loadData());
    }handleAddCamera() {
        window.dispatchEvent(new CustomEvent('navigate', {
            detail: { page: 'cameras', action: 'add' }
        }));
    }

    navigateToCameras() {
        window.dispatchEvent(new CustomEvent('navigate', {
            detail: { page: 'cameras' }
        }));
    }

    handleExportData() {
        this.showExportModal();
    }

    handleSystemHealth() {
        window.dispatchEvent(new CustomEvent('navigate', {
            detail: { page: 'settings', section: 'system' }
        }));
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
            window.dispatchEvent(new CustomEvent('navigate', {
                detail: { page: pageMap[action] }
            }));
        }
    }async loadCameraStatus() {
        try {
            const [dbResponse, recordingResponse] = await Promise.all([
                fetch(config.buildApiUrl(config.API_ENDPOINTS.CAMERAS))
                    .catch(err => {
                        console.warn('Failed to load database cameras:', err);
                        return null;
                    }),
                fetch('http://localhost:8002/api/v1/recordings/sources')
                    .catch(err => {
                        console.warn('Failed to load recording sources:', err);
                        return null;
                    })
            ]);

            let dbCameras = [];
            if (dbResponse && dbResponse.ok) {
                const data = await dbResponse.json();
                if (Array.isArray(data)) {
                    dbCameras = data;
                } else if (data.cameras && Array.isArray(data.cameras)) {
                    dbCameras = data.cameras;
                }
            }

            let recordingSources = [];
            if (recordingResponse && recordingResponse.ok) {
                const data = await recordingResponse.json();
                recordingSources = data.sources || [];
            }

            const cameras = this.mergeCameraDataForDashboard(dbCameras, recordingSources);
            this.metrics.activeCameras = cameras.filter(c => c.status === 'online').length;
            this.metrics.orphanedCameras = cameras.filter(c => c.status === 'orphaned').length;
            this.metrics.totalRecordings = cameras.reduce((sum, c) => sum + (c.recordingCount || 0), 0);
            this.metrics.totalStorageGB = cameras.reduce((sum, c) => sum + (c.storageUsedMb || 0), 0) / 1024;

            this.renderCameraStatus(cameras);
        } catch (error) {
            console.error('Failed to load camera status:', error);
            this.renderCameraStatusError();
        }
    }mergeCameraDataForDashboard(dbCameras, recordingSources) {
        const sourceMap = new Map();
        recordingSources.forEach(source => {
            sourceMap.set(source.camera_id, source);
        });

        const cameras = dbCameras.map(camera => {
            const source = sourceMap.get(camera.camera_id) || 
                          sourceMap.get(`camera_${camera.camera_id}`);
            
            if (source) {
                sourceMap.delete(source.camera_id);
                return {
                    ...camera,
                    enabled: true,
                    recordingCount: source.recording_count || 0,
                    storageUsedMb: source.storage_used_mb || 0,
                    hasRecordings: true
                };
            }
            
            return {
                ...camera,
                enabled: true,
                recordingCount: 0,
                storageUsedMb: 0,
                hasRecordings: false
            };
        });

        sourceMap.forEach(source => {
            if (source.has_recordings) {
                cameras.push({
                    id: source.camera_id,
                    name: source.display_name || `Camera ${source.camera_id}`,
                    status: 'orphaned',
                    enabled: false,
                    recordingCount: source.recording_count || 0,
                    storageUsedMb: source.storage_used_mb || 0,
                    hasRecordings: true,
                    isOrphaned: true
                });
            }
        });

        return cameras;
    }renderCameraStatus(cameras){const container=document.getElementById('camera-status-grid');if(!container)return;if(!cameras.length){this.renderNoCamerasMessage();return;}container.innerHTML=cameras.map(camera=> this.renderCameraStatusItem(camera)).join('');}renderCameraStatusItem(camera){const statusClass=camera.status==='orphaned' ? 'orphaned':camera.status;const recordingInfo=camera.hasRecordings ? `<span class="recording-info">${camera.recordingCount}clips • ${(camera.storageUsedMb/1024).toFixed(1)}GB</span>`:'<span class="recording-info">No recordings</span>';return ` <div class="camera-status-item ${statusClass}" data-camera-id="${camera.id}"> <div class="camera-status-header"> <span class="camera-name">${camera.name}</span> <div class="camera-status-indicator ${statusClass}"> <i class="fas ${this.getStatusIcon(camera.status)}"></i> <span class="status-text">${this.capitalizeFirst(camera.status)}</span> </div> </div> <div class="camera-info"> <div class="camera-detail"> <span class="label">Location:</span> <span class="value">${camera.location || 'Unknown'}</span> </div> <div class="camera-detail"> <span class="label">Recordings:</span> ${recordingInfo}</div> </div> </div> `;}renderNoCamerasMessage(){const container=document.getElementById('camera-status-grid');if(!container)return;container.innerHTML=` <div class="no-cameras-message"> <div class="no-cameras-content"> <i class="fas fa-video-slash"></i> <h3>No Cameras Configured</h3> <p>Add cameras to monitor system status</p> <button class="btn btn-primary" onclick="window.dispatchEvent(new CustomEvent('navigate',{detail:{page:'cameras',action:'add'}}))"> <i class="fas fa-plus"></i> Add Camera </button> </div> </div> `;}renderCameraStatusError(){const container=document.getElementById('camera-status-grid');if(!container)return;container.innerHTML=` <div class="camera-status-error"> <i class="fas fa-exclamation-triangle"></i> <span>Failed to load camera status</span> </div> `;}renderCameraStatusPlaceholder(){const container=document.getElementById('camera-status-grid');if(!container)return;container.innerHTML=` <div class="camera-status-loading"> <i class="fas fa-spinner fa-spin"></i> <span>Loading camera status...</span> </div> `;}renderRecentDetections(){const container=document.getElementById('recent-detections-list');if(!container)return;const mockDetections=[{plate:'ABC-123',camera:'Entrance Gate',time:'2 min ago',confidence:98.5},{plate:'XYZ-789',camera:'Parking Lot A',time:'5 min ago',confidence:92.1},{plate:'DEF-456',camera:'Loading Dock',time:'8 min ago',confidence:87.3},{plate:'GHI-321',camera:'Side Entrance',time:'12 min ago',confidence:95.7}];container.innerHTML=mockDetections.map(detection=> ` <div class="detection-item"> <div class="detection-plate">${detection.plate}</div> <div class="detection-details"> <span class="detection-camera">${detection.camera}</span> <span class="detection-time">${detection.time}</span> </div> <div class="detection-confidence"> <span class="confidence-value">${detection.confidence}%</span> <div class="confidence-bar"> <div class="confidence-fill" style="width:${detection.confidence}%"></div> </div> </div> </div> `).join('');}renderSystemHealth(){const container=document.getElementById('health-metrics');if(!container)return;const healthMetrics=[{name:'CPU Usage',value:34,unit:'%',status:'good'},{name:'Memory Usage',value:67,unit:'%',status:'warning'},{name:'Disk Usage',value:23,unit:'%',status:'good'},{name:'Network',value:98,unit:'%',status:'good'}];container.innerHTML=healthMetrics.map(metric=> ` <div class="health-metric"> <div class="metric-label">${metric.name}</div> <div class="metric-value ${metric.status}">${metric.value}${metric.unit}</div> <div class="metric-bar"> <div class="metric-fill ${metric.status}" style="width:${metric.value}%"></div> </div> </div> `).join('');}async loadData() {
        try {
            await this.simulateDataLoad();
            await this.loadCameraStatus();
            await this.loadStorageData();
            this.updateMetrics();
            this.renderRecentDetections();
            this.renderSystemHealth();
            this.updateStorageMetrics();
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showAlert('Failed to load dashboard data', 'error');
        }
    }

    async simulateDataLoad() {
        return new Promise(resolve => setTimeout(resolve, 500));
    }

    updateMetrics() {
        document.getElementById('active-cameras-count').textContent = this.metrics.activeCameras;
        document.getElementById('detections-today').textContent = this.metrics.detectionsToday.toLocaleString();
        document.getElementById('active-alerts-count').textContent = this.metrics.activeAlerts;
        document.getElementById('accuracy-rate').textContent = `${this.metrics.accuracyRate}%`;
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.loadData();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }showAlert(message,type='info'){const alertBanner=document.getElementById('alert-banner');const alertMessage=alertBanner?.querySelector('.alert-message');if(alertBanner && alertMessage){alertMessage.textContent=message;alertBanner.className=`alert-banner alert-${type}`;alertBanner.style.display='flex';}}closeAlertBanner(){const alertBanner=document.getElementById('alert-banner');if(alertBanner){alertBanner.style.display='none';}}capitalizeFirst(str) {
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

    destroy() {
        this.stopAutoRefresh();
        if (this.detectionConsole) {
            this.detectionConsole.destroy();
            this.detectionConsole = null;
        }
    }async loadStorageData(){try{const storageReport=await playbackService.getStorageReport();if(storageReport && storageReport.system_stats){this.storageStats={totalRecordings:storageReport.system_stats.total_segments || 0,storageUsed:storageReport.system_stats.total_size_formatted || '0 B',diskUsage:Math.round(storageReport.system_stats.disk_used_percent || 0),retentionDays:storageReport.retention_days || 30};}await this.checkRecordingStatus();}catch(error){console.warn('Recording service unavailable-using default values:',error.message);this.storageStats={totalRecordings:0,storageUsed:'Service offline',diskUsage:0,retentionDays:30};this.updateRecordingStatusOffline();}}async checkRecordingStatus(){try{const health=await playbackService.getHealth();const recordingStatusEl=document.getElementById('recording-status');if(recordingStatusEl){const isRecording=health.status==='healthy' && health.storage_status==='healthy';const statusIcon=recordingStatusEl.querySelector('i');const statusText=recordingStatusEl.querySelector('span');if(isRecording){statusIcon.className='fas fa-circle text-green';statusText.textContent='Recording:Active';}else{statusIcon.className='fas fa-circle text-red';statusText.textContent='Recording:Inactive';}}}catch(error){console.warn('Recording service health check failed:',error.message);this.updateRecordingStatusOffline();}}updateRecordingStatusOffline(){const recordingStatusEl=document.getElementById('recording-status');if(recordingStatusEl){const statusIcon=recordingStatusEl.querySelector('i');const statusText=recordingStatusEl.querySelector('span');if(statusIcon && statusText){statusIcon.className='fas fa-circle text-gray';statusText.textContent='Recording:Service Offline';}}}updateStorageMetrics(){const totalRecordingsEl=document.getElementById('total-recordings');const storageUsedEl=document.getElementById('storage-used');const diskUsageEl=document.getElementById('disk-usage');const retentionDaysEl=document.getElementById('retention-days');if(totalRecordingsEl)totalRecordingsEl.textContent=this.storageStats.totalRecordings;if(storageUsedEl)storageUsedEl.textContent=this.storageStats.storageUsed;if(diskUsageEl)diskUsageEl.textContent=`${this.storageStats.diskUsage}%`;if(retentionDaysEl)retentionDaysEl.textContent=this.storageStats.retentionDays;if(diskUsageEl && diskUsageEl.parentElement){const card=diskUsageEl.closest('.storage-metric-card');if(card){const icon=card.querySelector('.metric-icon i');if(this.storageStats.diskUsage >=90){icon.className='fas fa-chart-pie text-red';}else if(this.storageStats.diskUsage >=80){icon.className='fas fa-chart-pie text-orange';}else{icon.className='fas fa-chart-pie text-green';}}}}}export default Dashboard;