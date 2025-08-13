/**
 * Updated Dashboard Page Component
 * Integrates camera grid, live events, and proper layout
 */

import playbackService from '../services/PlaybackService.js';
import config from '../config/app.config.js';

class Dashboard {
    constructor() {
        // Component managers
        this.cameraGridManager = null;
        this.liveEventsManager = null;
        
        // State
        this.metrics = {
            activeCameras: 0,
            detectionsToday: 0,
            activeAlerts: 0,
            accuracyRate: 0
        };
        
        this.systemStatus = 'ok'; // ok, degraded, alert
        this.filters = {
            cameras: [],
            location: '',
            status: '',
            features: []
        };
        
        // Initialize
        this.init();
    }
    
    async init() {
        try {
            this.render();
            await this.loadInitialData();
            this.initializeComponents();
            this.attachEventListeners();
            this.startAutoRefresh();
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showAlert('Failed to initialize dashboard', 'error');
        }
    }
    
    render() {
        const container = document.getElementById('dashboard');
        if (!container) return;
        
        container.innerHTML = this.getTemplate();
    }
    
    getTemplate() {
        return `
            <div class="dashboard-container">
                <!-- Global Header -->
                <div class="global-header">
                    <div class="header-left">
                        <div class="app-info">
                            <h2>LPR System</h2>
                            <span class="version">v2.0.1</span>
                        </div>
                        <div class="system-status ${this.systemStatus}">
                            <i class="fas fa-circle"></i>
                            <span>${this.getStatusText()}</span>
                        </div>
                    </div>
                    <div class="header-right">
                        <div class="clock-widget">
                            <span class="time" id="dashboard-clock">--:--:--</span>
                            <button class="utc-toggle" id="utc-toggle">
                                <i class="fas fa-globe"></i>
                                UTC
                            </button>
                        </div>
                        <div class="global-search">
                            <input type="text" placeholder="Search cameras, plates..." 
                                   class="search-input" id="global-search">
                            <i class="fas fa-search"></i>
                        </div>
                        <div class="quick-links">
                            <a href="/cameras.html" class="quick-link">Cameras</a>
                            <a href="/recordings.html" class="quick-link">Recordings</a>
                            <a href="#" class="quick-link" id="health-link">Health</a>
                        </div>
                    </div>
                </div>
                
                <!-- Filters Ribbon -->
                <div class="filters-ribbon">
                    <div class="filter-group">
                        <label class="filter-label">Cameras:</label>
                        <select class="filter-select" id="camera-filter" multiple>
                            <option value="">All Cameras</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">Location:</label>
                        <select class="filter-select" id="location-filter">
                            <option value="">All Locations</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">Status:</label>
                        <select class="filter-select" id="status-filter">
                            <option value="">All</option>
                            <option value="online">Online</option>
                            <option value="degraded">Degraded</option>
                            <option value="offline">Offline</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">Features:</label>
                        <div class="feature-toggles">
                            <label class="feature-toggle">
                                <input type="checkbox" value="lpr" id="feature-lpr">
                                <span>LPR</span>
                            </label>
                            <label class="feature-toggle">
                                <input type="checkbox" value="vehicle_color" id="feature-color">
                                <span>Color</span>
                            </label>
                        </div>
                    </div>
                    <div class="filter-group refresh-controls">
                        <label class="filter-label">Refresh:</label>
                        <select class="filter-select" id="refresh-rate">
                            <option value="auto">Auto</option>
                            <option value="2s">2s</option>
                            <option value="5s">5s</option>
                            <option value="paused">Paused</option>
                        </select>
                    </div>
                </div>
                
                <!-- Key Metrics -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-video text-blue"></i>
                        </div>
                        <div class="metric-content">
                            <h3 id="active-cameras-count">--</h3>
                            <p>Active Cameras</p>
                            <small class="metric-change positive">
                                <i class="fas fa-arrow-up"></i> 2 from yesterday
                            </small>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-car text-green"></i>
                        </div>
                        <div class="metric-content">
                            <h3 id="detections-today">--</h3>
                            <p>Detections Today</p>
                            <small class="metric-change positive">
                                <i class="fas fa-arrow-up"></i> 15% increase
                            </small>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-exclamation-triangle text-orange"></i>
                        </div>
                        <div class="metric-content">
                            <h3 id="active-alerts-count">--</h3>
                            <p>Active Alerts</p>
                            <small class="metric-change neutral">
                                No change
                            </small>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-bullseye text-purple"></i>
                        </div>
                        <div class="metric-content">
                            <h3 id="accuracy-rate">--%</h3>
                            <p>Accuracy Rate</p>
                            <small class="metric-change positive">
                                <i class="fas fa-arrow-up"></i> 0.5%
                            </small>
                        </div>
                    </div>
                </div>
                
                <!-- Main Grid -->
                <div class="dashboard-main-grid">
                    <!-- Camera Grid -->
                    <div class="camera-grid-section">
                        <div class="section-header">
                            <h3>Camera Feeds</h3>
                            <div class="section-actions">
                                <button class="icon-btn" id="grid-fullscreen">
                                    <i class="fas fa-expand"></i>
                                </button>
                            </div>
                        </div>
                        <div class="camera-grid" id="camera-grid">
                            <!-- Camera tiles will be rendered here -->
                            <div class="loading-state">
                                <i class="fas fa-spinner fa-spin"></i>
                                <span>Loading cameras...</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Right Sidebar -->
                    <div class="dashboard-sidebar">
                        <!-- Recent Events -->
                        <div class="recent-events-card">
                            <div id="recent-events-container">
                                <!-- Live events will be rendered here -->
                            </div>
                        </div>
                        
                        <!-- System Health -->
                        <div class="system-health-widget">
                            <div class="widget-header">
                                <h3>System Health</h3>
                                <button class="icon-btn" id="health-details">
                                    <i class="fas fa-info-circle"></i>
                                </button>
                            </div>
                            <div class="health-metrics-grid">
                                <div class="health-metric-item">
                                    <div class="metric-label">CPU</div>
                                    <div class="metric-value" id="cpu-usage">--%</div>
                                    <div class="metric-bar">
                                        <div class="metric-fill" id="cpu-bar"></div>
                                    </div>
                                </div>
                                <div class="health-metric-item">
                                    <div class="metric-label">Memory</div>
                                    <div class="metric-value" id="memory-usage">--%</div>
                                    <div class="metric-bar">
                                        <div class="metric-fill" id="memory-bar"></div>
                                    </div>
                                </div>
                                <div class="health-metric-item">
                                    <div class="metric-label">GPU</div>
                                    <div class="metric-value" id="gpu-usage">--%</div>
                                    <div class="metric-bar">
                                        <div class="metric-fill" id="gpu-bar"></div>
                                    </div>
                                </div>
                                <div class="health-metric-item">
                                    <div class="metric-label">Network</div>
                                    <div class="metric-value" id="network-usage">--%</div>
                                    <div class="metric-bar">
                                        <div class="metric-fill" id="network-bar"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="health-footer">
                                <span class="ml-fps">ML: <span id="ml-fps">-- FPS</span></span>
                                <span class="event-rate">Events: <span id="event-rate">--/min</span></span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="dashboard-footer">
                    <div class="footer-left">
                        <span class="last-refresh">Last refresh: <span id="last-refresh-time">--:--:--</span></span>
                    </div>
                    <div class="footer-center">
                        <span class="backend-status">API: <span class="status-indicator" id="api-status">●</span></span>
                        <span class="storage-status">Storage: <span id="storage-usage">-- GB / -- GB</span></span>
                    </div>
                    <div class="footer-right">
                        <button class="text-btn" id="refresh-now">
                            <i class="fas fa-sync"></i> Refresh Now
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    async loadInitialData() {
        // Load cameras for filters
        const cameras = await this.fetchCameras();
        this.populateCameraFilter(cameras);
        this.populateLocationFilter(cameras);
        
        // Load metrics
        await this.loadMetrics();
        
        // Load system health
        await this.loadSystemHealth();
    }
    
    initializeComponents() {
        // Initialize camera grid
        const gridContainer = document.getElementById('camera-grid');
        this.cameraGridManager = new CameraGridManager(gridContainer);
        this.cameraGridManager.init();
        
        // Initialize live events
        const eventsContainer = document.getElementById('recent-events-container');
        this.liveEventsManager = new LiveEventsManager(eventsContainer);
        
        // Start clock
        this.startClock();
    }
    
    attachEventListeners() {
        // Filter changes
        document.getElementById('camera-filter')?.addEventListener('change', (e) => {
            this.updateFilters();
        });
        
        document.getElementById('location-filter')?.addEventListener('change', (e) => {
            this.updateFilters();
        });
        
        document.getElementById('status-filter')?.addEventListener('change', (e) => {
            this.updateFilters();
        });
        
        document.getElementById('feature-lpr')?.addEventListener('change', (e) => {
            this.updateFilters();
        });
        
        document.getElementById('feature-color')?.addEventListener('change', (e) => {
            this.updateFilters();
        });
        
        // Refresh rate
        document.getElementById('refresh-rate')?.addEventListener('change', (e) => {
            this.cameraGridManager?.setGlobalRefreshRate(e.target.value);
        });
        
        // Manual refresh
        document.getElementById('refresh-now')?.addEventListener('click', () => {
            this.refreshAll();
        });
        
        // Clock toggle
        document.getElementById('utc-toggle')?.addEventListener('click', (e) => {
            e.target.classList.toggle('active');
            this.updateClock();
        });
        
        // Global search
        document.getElementById('global-search')?.addEventListener('input', (e) => {
            this.handleGlobalSearch(e.target.value);
        });
        
        // Custom events
        window.addEventListener('camera-details', (e) => {
            this.showCameraDetails(e.detail.camera);
        });
        
        window.addEventListener('roi-editor', (e) => {
            this.openROIEditor(e.detail.camera);
        });
        
        window.addEventListener('show-toast', (e) => {
            this.showToast(e.detail.message, e.detail.type);
        });
    }
    
    updateFilters() {
        const filters = {
            cameras: Array.from(document.getElementById('camera-filter').selectedOptions)
                .map(opt => opt.value).filter(v => v),
            location: document.getElementById('location-filter').value,
            status: document.getElementById('status-filter').value,
            features: []
        };
        
        if (document.getElementById('feature-lpr').checked) {
            filters.features.push('lpr');
        }
        if (document.getElementById('feature-color').checked) {
            filters.features.push('vehicle_color');
        }
        
        this.cameraGridManager?.updateFilters(filters);
    }
    
    async fetchCameras() {
        try {
            const response = await fetch('/api/cameras');
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch cameras:', error);
            return [];
        }
    }
    
    populateCameraFilter(cameras) {
        const select = document.getElementById('camera-filter');
        cameras.forEach(camera => {
            const option = document.createElement('option');
            option.value = camera.id;
            option.textContent = camera.alias;
            select.appendChild(option);
        });
    }
    
    populateLocationFilter(cameras) {
        const locations = [...new Set(cameras.map(c => c.location).filter(Boolean))];
        const select = document.getElementById('location-filter');
        locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location;
            option.textContent = location;
            select.appendChild(option);
        });
    }
    
    async loadMetrics() {
        try {
            const response = await fetch('/api/metrics/dashboard');
            const metrics = await response.json();
            
            this.metrics = metrics;
            this.updateMetricsDisplay();
        } catch (error) {
            console.error('Failed to load metrics:', error);
        }
    }
    
    updateMetricsDisplay() {
        document.getElementById('active-cameras-count').textContent = 
            this.metrics.activeCameras || '--';
        document.getElementById('detections-today').textContent = 
            (this.metrics.detectionsToday || 0).toLocaleString();
        document.getElementById('active-alerts-count').textContent = 
            this.metrics.activeAlerts || '--';
        document.getElementById('accuracy-rate').textContent = 
            `${this.metrics.accuracyRate || '--'}%`;
    }
    
    async loadSystemHealth() {
        try {
            const response = await fetch('/api/health/detailed');
            const health = await response.json();
            
            this.updateHealthDisplay(health);
        } catch (error) {
            console.error('Failed to load system health:', error);
        }
    }
    
    updateHealthDisplay(health) {
        // Update health metrics
        const updateMetric = (id, value, barId) => {
            const element = document.getElementById(id);
            const bar = document.getElementById(barId);
            if (element && bar) {
                element.textContent = `${value}%`;
                bar.style.width = `${value}%`;
                
                // Color coding
                if (value > 80) {
                    bar.classList.add('high');
                } else if (value > 60) {
                    bar.classList.add('medium');
                } else {
                    bar.classList.add('low');
                }
            }
        };
        
        