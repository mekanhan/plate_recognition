// Application State
const AppState = {
    currentPage: 'dashboard',
    cameras: [],
    detections: [],
    alerts: [],
    reports: [],
    users: [],
    currentUser: {
        name: 'Security Admin',
        role: 'Administrator',
        email: 'admin@security.com'
    },
    systemHealth: {
        cpu: 45,
        memory: 62,
        storage: 78,
        network: 32
    },
    filters: {
        cameras: {},
        detections: {},
        alerts: {}
    },
    pagination: {
        cameras: { page: 1, limit: 12, total: 24 },
        detections: { page: 1, limit: 50, total: 1247 },
        alerts: { page: 1, limit: 20, total: 15 }
    }
};

// Mock Data
const MockData = {
    cameras: [
        {
            id: 'cam_001',
            name: 'Entrance Gate',
            ip_address: '192.168.1.101',
            location: 'Main Entrance',
            status: 'online',
            resolution: '1920x1080',
            fps: 30,
            last_seen: new Date(),
            detections_today: 156,
            uptime: '15d 4h 23m'
        },
        {
            id: 'cam_002',
            name: 'Parking Lot A',
            ip_address: '192.168.1.102',
            location: 'Parking Area A',
            status: 'online',
            resolution: '1920x1080',
            fps: 25,
            last_seen: new Date(),
            detections_today: 203,
            uptime: '12d 8h 15m'
        },
        {
            id: 'cam_003',
            name: 'Exit Point',
            ip_address: '192.168.1.103',
            location: 'Main Exit',
            status: 'offline',
            resolution: '1920x1080',
            fps: 30,
            last_seen: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
            detections_today: 0,
            uptime: '0d 0h 0m'
        },
        {
            id: 'cam_004',
            name: 'Loading Dock',
            ip_address: '192.168.1.104',
            location: 'Loading Area',
            status: 'online',
            resolution: '1280x720',
            fps: 30,
            last_seen: new Date(),
            detections_today: 89,
            uptime: '8d 12h 45m'
        },
        {
            id: 'cam_005',
            name: 'Side Entrance',
            ip_address: '192.168.1.105',
            location: 'Side Entry',
            status: 'maintenance',
            resolution: '1920x1080',
            fps: 15,
            last_seen: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
            detections_today: 42,
            uptime: '5d 2h 18m'
        },
        {
            id: 'cam_006',
            name: 'Visitor Parking',
            ip_address: '192.168.1.106',
            location: 'Visitor Area',
            status: 'online',
            resolution: '1920x1080',
            fps: 30,
            last_seen: new Date(),
            detections_today: 124,
            uptime: '20d 16h 8m'
        }
    ],

    detections: [
        {
            id: 'det_001',
            plate_number: 'ABC-123',
            camera_id: 'cam_001',
            camera_name: 'Entrance Gate',
            confidence: 98.5,
            timestamp: new Date(),
            vehicle_type: 'Sedan',
            vehicle_color: 'Blue',
            status: 'verified'
        },
        {
            id: 'det_002',
            plate_number: 'XYZ-789',
            camera_id: 'cam_002',
            camera_name: 'Parking Lot A',
            confidence: 95.2,
            timestamp: new Date(Date.now() - 5 * 60 * 1000),
            vehicle_type: 'SUV',
            vehicle_color: 'White',
            status: 'verified'
        },
        {
            id: 'det_003',
            plate_number: 'DEF-456',
            camera_id: 'cam_004',
            camera_name: 'Loading Dock',
            confidence: 92.8,
            timestamp: new Date(Date.now() - 8 * 60 * 1000),
            vehicle_type: 'Truck',
            vehicle_color: 'Red',
            status: 'flagged'
        },
        {
            id: 'det_004',
            plate_number: 'GHI-012',
            camera_id: 'cam_001',
            camera_name: 'Entrance Gate',
            confidence: 89.1,
            timestamp: new Date(Date.now() - 12 * 60 * 1000),
            vehicle_type: 'Sedan',
            vehicle_color: 'Black',
            status: 'verified'
        },
        {
            id: 'det_005',
            plate_number: 'JKL-345',
            camera_id: 'cam_006',
            camera_name: 'Visitor Parking',
            confidence: 96.7,
            timestamp: new Date(Date.now() - 15 * 60 * 1000),
            vehicle_type: 'Hatchback',
            vehicle_color: 'Silver',
            status: 'verified'
        }
    ],

    alerts: [
        {
            id: 'alert_001',
            title: 'Camera Offline',
            description: 'Exit Point camera has been offline for 2 hours',
            severity: 'critical',
            category: 'camera',
            status: 'active',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
            camera_id: 'cam_003'
        },
        {
            id: 'alert_002',
            title: 'Low Detection Confidence',
            description: 'Multiple detections below 70% confidence threshold',
            severity: 'warning',
            category: 'detection',
            status: 'active',
            timestamp: new Date(Date.now() - 30 * 60 * 1000),
            camera_id: 'cam_005'
        },
        {
            id: 'alert_003',
            title: 'High System Load',
            description: 'CPU usage above 80% for extended period',
            severity: 'warning',
            category: 'system',
            status: 'acknowledged',
            timestamp: new Date(Date.now() - 45 * 60 * 1000)
        },
        {
            id: 'alert_004',
            title: 'Storage Space Low',
            description: 'Available storage below 20%',
            severity: 'critical',
            category: 'system',
            status: 'active',
            timestamp: new Date(Date.now() - 60 * 60 * 1000)
        },
        {
            id: 'alert_005',
            title: 'Suspicious Activity',
            description: 'Vehicle detected outside operating hours',
            severity: 'info',
            category: 'security',
            status: 'resolved',
            timestamp: new Date(Date.now() - 90 * 60 * 1000),
            camera_id: 'cam_002'
        }
    ],

    reports: [
        {
            id: 'rep_001',
            name: 'Daily Traffic Report - Jan 9, 2025',
            type: 'traffic',
            status: 'completed',
            generated: new Date(Date.now() - 2 * 60 * 60 * 1000),
            size: '2.4 MB',
            format: 'PDF'
        },
        {
            id: 'rep_002',
            name: 'Weekly Performance Summary',
            type: 'performance',
            status: 'generating',
            generated: new Date(),
            size: '1.8 MB',
            format: 'XLSX'
        },
        {
            id: 'rep_003',
            name: 'Security Incident Report - Week 1',
            type: 'security',
            status: 'completed',
            generated: new Date(Date.now() - 24 * 60 * 60 * 1000),
            size: '856 KB',
            format: 'PDF'
        }
    ],

    users: [
        {
            id: 'user_001',
            name: 'John Smith',
            email: 'john.smith@security.com',
            role: 'Administrator',
            status: 'active',
            last_login: new Date(Date.now() - 30 * 60 * 1000)
        },
        {
            id: 'user_002',
            name: 'Sarah Johnson',
            email: 'sarah.johnson@security.com',
            role: 'Operator',
            status: 'active',
            last_login: new Date(Date.now() - 2 * 60 * 60 * 1000)
        },
        {
            id: 'user_003',
            name: 'Mike Wilson',
            email: 'mike.wilson@security.com',
            role: 'Viewer',
            status: 'inactive',
            last_login: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        }
    ]
};

// Initialize Application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Load mock data
    AppState.cameras = MockData.cameras;
    AppState.detections = MockData.detections;
    AppState.alerts = MockData.alerts;
    AppState.reports = MockData.reports;
    AppState.users = MockData.users;

    // Initialize components
    initNavigation();
    initDashboard();
    initEventListeners();
    initRealtimeUpdates();
    
    // Load initial page
    loadPage('dashboard');
    
    console.log('LPR System initialized successfully');
}

// Navigation Management
function initNavigation() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const menuLinks = document.querySelectorAll('.menu-link');

    // Sidebar toggle for mobile
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // Menu item clicks
    menuLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            if (page) {
                loadPage(page);
                updateActiveMenuItem(link);
                
                // Close sidebar on mobile
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('active');
                }
            }
        });
    });

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });
}

function updateActiveMenuItem(activeLink) {
    // Remove active class from all menu items
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to current menu item
    activeLink.closest('.menu-item').classList.add('active');
}

function loadPage(pageName) {
    // Hide all content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show target section
    const targetSection = document.getElementById(pageName);
    if (targetSection) {
        targetSection.classList.add('active');
        AppState.currentPage = pageName;
        
        // Update page title and breadcrumb
        updatePageTitle(pageName);
        updateBreadcrumb(pageName);
        
        // Load page-specific content
        loadPageContent(pageName);
    }
}

function updatePageTitle(pageName) {
    const pageTitle = document.querySelector('.page-title');
    const titles = {
        dashboard: 'Security Dashboard',
        cameras: 'Camera Management',
        detections: 'Detection Results',
        analytics: 'Analytics & Insights',
        alerts: 'System Alerts',
        reports: 'Reports',
        settings: 'System Settings'
    };
    
    if (pageTitle) {
        pageTitle.textContent = titles[pageName] || 'Dashboard';
    }
}

function updateBreadcrumb(pageName) {
    const breadcrumb = document.querySelector('.breadcrumb');
    const breadcrumbs = {
        dashboard: ['Dashboard'],
        cameras: ['Cameras', 'Management'],
        detections: ['Detections', 'Results'],
        analytics: ['Analytics', 'Insights'],
        alerts: ['System', 'Alerts'],
        reports: ['Reports'],
        settings: ['System', 'Settings']
    };
    
    if (breadcrumb) {
        const items = breadcrumbs[pageName] || ['Dashboard'];
        breadcrumb.innerHTML = items.map((item, index) => 
            `<span class="breadcrumb-item ${index === items.length - 1 ? 'active' : ''}">${item}</span>`
        ).join(' <i class="fas fa-chevron-right"></i> ');
    }
}

function loadPageContent(pageName) {
    switch (pageName) {
        case 'dashboard':
            loadDashboardContent();
            break;
        case 'cameras':
            loadCamerasContent();
            break;
        case 'detections':
            loadDetectionsContent();
            break;
        case 'analytics':
            loadAnalyticsContent();
            break;
        case 'alerts':
            loadAlertsContent();
            break;
        case 'reports':
            loadReportsContent();
            break;
        case 'settings':
            loadSettingsContent();
            break;
    }
}

// Dashboard Implementation
function initDashboard() {
    initMetricsAnimation();
    initQuickActions();
    initHeaderActions();
}

function loadDashboardContent() {
    updateMetrics();
    loadLiveCameraFeeds();
    loadRecentDetections();
    loadSystemHealth();
    loadAnalyticsChart();
}

function updateMetrics() {
    const onlineCameras = AppState.cameras.filter(cam => cam.status === 'online').length;
    const totalDetections = AppState.detections.length;
    const activeAlerts = AppState.alerts.filter(alert => alert.status === 'active').length;
    
    // Update metric values
    updateElement('active-cameras-count', onlineCameras);
    updateElement('detections-today', totalDetections.toLocaleString());
    updateElement('active-alerts-count', activeAlerts);
    updateElement('accuracy-rate', '94.2%');
    
    // Update badges in sidebar
    updateElement('camera-count', AppState.cameras.length);
    updateElement('detection-alerts', AppState.detections.filter(d => d.status === 'flagged').length);
    updateElement('alert-count', activeAlerts);
}

function loadLiveCameraFeeds() {
    const cameraGrid = document.getElementById('live-camera-grid');
    if (!cameraGrid) return;
    
    const onlineCameras = AppState.cameras.filter(cam => cam.status === 'online').slice(0, 4);
    
    cameraGrid.innerHTML = onlineCameras.map(camera => `
        <div class="camera-feed" data-camera-id="${camera.id}">
            <div class="feed-container">
                <div class="feed-placeholder">
                    <i class="fas fa-video"></i>
                </div>
                <div class="feed-overlay">
                    <span class="camera-name">${camera.name}</span>
                    <span class="feed-status ${camera.status}">${camera.status.toUpperCase()}</span>
                </div>
            </div>
        </div>
    `).join('');
    
    // Add click handlers for camera feeds
    cameraGrid.querySelectorAll('.camera-feed').forEach(feed => {
        feed.addEventListener('click', () => {
            const cameraId = feed.getAttribute('data-camera-id');
            openCameraModal(cameraId);
        });
    });
}

function loadRecentDetections() {
    const detectionsList = document.getElementById('recent-detections-list');
    if (!detectionsList) return;
    
    const recentDetections = AppState.detections.slice(0, 5);
    
    detectionsList.innerHTML = recentDetections.map(detection => `
        <div class="detection-item" data-detection-id="${detection.id}">
            <div class="detection-image">
                <div class="plate-preview">${detection.plate_number}</div>
            </div>
            <div class="detection-info">
                <span class="plate-number">${detection.plate_number}</span>
                <span class="camera-location">${detection.camera_name}</span>
                <span class="detection-time">${formatTimeAgo(detection.timestamp)}</span>
            </div>
            <div class="detection-confidence">
                <span class="confidence-score ${getConfidenceClass(detection.confidence)}">${detection.confidence}%</span>
            </div>
        </div>
    `).join('');
    
    // Add click handlers for detections
    detectionsList.querySelectorAll('.detection-item').forEach(item => {
        item.addEventListener('click', () => {
            const detectionId = item.getAttribute('data-detection-id');
            openDetectionModal(detectionId);
        });
    });
}

function loadSystemHealth() {
    const healthMetrics = document.getElementById('health-metrics');
    if (!healthMetrics) return;
    
    const metrics = [
        { label: 'CPU Usage', value: AppState.systemHealth.cpu, key: 'cpu' },
        { label: 'Memory', value: AppState.systemHealth.memory, key: 'memory' },
        { label: 'Storage', value: AppState.systemHealth.storage, key: 'storage' },
        { label: 'Network', value: AppState.systemHealth.network, key: 'network' }
    ];
    
    healthMetrics.innerHTML = metrics.map(metric => `
        <div class="health-item">
            <span class="health-label">${metric.label}</span>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${metric.value}%; background: ${getHealthColor(metric.value)}"></div>
            </div>
            <span class="health-value">${metric.value}%</span>
        </div>
    `).join('');
}

function loadAnalyticsChart() {
    const chartCanvas = document.getElementById('detectionChart');
    if (!chartCanvas) return;
    
    // Simulate chart with placeholder
    const chartContainer = chartCanvas.parentElement;
    chartContainer.innerHTML = `
        <div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #718096;">
            <div style="text-align: center;">
                <i class="fas fa-chart-line" style="font-size: 3rem; margin-bottom: 1rem; display: block;"></i>
                <p>Detection Analytics Chart</p>
                <small>Real chart would be implemented with Chart.js</small>
            </div>
        </div>
    `;
}

// Camera Management Implementation
function loadCamerasContent() {
    setupCameraFilters();
    loadCamerasGrid();
    setupCameraPagination();
}

function setupCameraFilters() {
    const statusFilter = document.getElementById('camera-status-filter');
    const locationFilter = document.getElementById('camera-location-filter');
    const searchInput = document.getElementById('camera-search');
    const sortSelect = document.getElementById('camera-sort');
    
    // Status filter
    if (statusFilter) {
        statusFilter.addEventListener('change', (e) => {
            AppState.filters.cameras.status = e.target.value;
            loadCamerasGrid();
        });
    }
    
    // Location filter
    if (locationFilter) {
        locationFilter.addEventListener('change', (e) => {
            AppState.filters.cameras.location = e.target.value;
            loadCamerasGrid();
        });
    }
    
    // Search input
    if (searchInput) {
        searchInput.addEventListener('input', debounce((e) => {
            AppState.filters.cameras.search = e.target.value;
            loadCamerasGrid();
        }, 300));
    }
    
    // Sort select
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            AppState.filters.cameras.sort = e.target.value;
            loadCamerasGrid();
        });
    }
    
    // Reset filters
    const resetBtn = document.getElementById('reset-filters');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            AppState.filters.cameras = {};
            if (statusFilter) statusFilter.value = '';
            if (locationFilter) locationFilter.value = '';
            if (searchInput) searchInput.value = '';
            if (sortSelect) sortSelect.value = 'name';
            loadCamerasGrid();
        });
    }
}

function loadCamerasGrid() {
    const camerasGrid = document.getElementById('cameras-grid');
    if (!camerasGrid) return;
    
    let filteredCameras = [...AppState.cameras];
    
    // Apply filters
    if (AppState.filters.cameras.status) {
        filteredCameras = filteredCameras.filter(cam => 
            cam.status === AppState.filters.cameras.status);
    }
    
    if (AppState.filters.cameras.location) {
        filteredCameras = filteredCameras.filter(cam => 
            cam.location.toLowerCase().includes(AppState.filters.cameras.location.toLowerCase()));
    }
    
    if (AppState.filters.cameras.search) {
        const search = AppState.filters.cameras.search.toLowerCase();
        filteredCameras = filteredCameras.filter(cam => 
            cam.name.toLowerCase().includes(search) || 
            cam.location.toLowerCase().includes(search) ||
            cam.ip_address.includes(search));
    }
    
    // Apply sorting
    const sortBy = AppState.filters.cameras.sort || 'name';
    filteredCameras.sort((a, b) => {
        switch (sortBy) {
            case 'status':
                return a.status.localeCompare(b.status);
            case 'location':
                return a.location.localeCompare(b.location);
            case 'added':
                return new Date(b.last_seen) - new Date(a.last_seen);
            default:
                return a.name.localeCompare(b.name);
        }
    });
    
    camerasGrid.innerHTML = filteredCameras.map(camera => `
        <div class="camera-card" data-camera-id="${camera.id}">
            <div class="camera-header">
                <h4>${camera.name}</h4>
                <div class="camera-status ${camera.status}">
                    <i class="fas fa-circle"></i>
                    ${camera.status.charAt(0).toUpperCase() + camera.status.slice(1)}
                </div>
            </div>
            <div class="camera-preview">
                <div class="preview-placeholder ${camera.status === 'offline' ? 'error' : ''}">
                    <i class="fas fa-${camera.status === 'offline' ? 'exclamation-triangle' : 'video'}"></i>
                </div>
            </div>
            <div class="camera-info">
                <div class="info-row">
                    <span class="label">IP Address:</span>
                    <span class="value">${camera.ip_address}</span>
                </div>
                <div class="info-row">
                    <span class="label">Resolution:</span>
                    <span class="value">${camera.resolution}</span>
                </div>
                <div class="info-row">
                    <span class="label">FPS:</span>
                    <span class="value">${camera.fps}</span>
                </div>
                <div class="info-row">
                    <span class="label">Location:</span>
                    <span class="value">${camera.location}</span>
                </div>
                ${camera.status === 'offline' ? `
                    <div class="info-row">
                        <span class="label">Last Seen:</span>
                        <span class="value error">${formatTimeAgo(camera.last_seen)}</span>
                    </div>
                ` : `
                    <div class="info-row">
                        <span class="label">Uptime:</span>
                        <span class="value">${camera.uptime}</span>
                    </div>
                `}
            </div>
            <div class="camera-actions">
                ${camera.status === 'offline' ? 
                    `<button class="btn btn-small btn-warning" onclick="reconnectCamera('${camera.id}')">Reconnect</button>` :
                    `<button class="btn btn-small" onclick="configureCamera('${camera.id}')">Configure</button>`
                }
                <button class="btn btn-small btn-secondary" onclick="viewLiveCamera('${camera.id}')">View Live</button>
                <button class="btn btn-small btn-secondary" onclick="openCameraMenu('${camera.id}')">
                    <i class="fas fa-ellipsis-v"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function setupCameraPagination() {
    // Implementation for camera pagination
    const prevBtn = document.getElementById('cameras-prev-page');
    const nextBtn = document.getElementById('cameras-next-page');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (AppState.pagination.cameras.page > 1) {
                AppState.pagination.cameras.page--;
                loadCamerasGrid();
                updateCamerasPagination();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            const maxPages = Math.ceil(AppState.pagination.cameras.total / AppState.pagination.cameras.limit);
            if (AppState.pagination.cameras.page < maxPages) {
                AppState.pagination.cameras.page++;
                loadCamerasGrid();
                updateCamerasPagination();
            }
        });
    }
}

function updateCamerasPagination() {
    const { page, limit, total } = AppState.pagination.cameras;
    const maxPages = Math.ceil(total / limit);
    
    // Update pagination info
    const showingElement = document.getElementById('cameras-showing');
    const totalElement = document.getElementById('cameras-total');
    
    if (showingElement) {
        const start = (page - 1) * limit + 1;
        const end = Math.min(page * limit, total);
        showingElement.textContent = `${start}-${end}`;
    }
    
    if (totalElement) {
        totalElement.textContent = total;
    }
    
    // Update pagination buttons
    const prevBtn = document.getElementById('cameras-prev-page');
    const nextBtn = document.getElementById('cameras-next-page');
    
    if (prevBtn) {
        prevBtn.disabled = page === 1;
    }
    
    if (nextBtn) {
        nextBtn.disabled = page === maxPages;
    }
}

// Detection Results Implementation
function loadDetectionsContent() {
    setupDetectionFilters();
    loadDetectionsTable();
    updateDetectionStats();
    setupDetectionPagination();
}

function setupDetectionFilters() {
    const dateFromInput = document.getElementById('detection-date-from');
    const dateToInput = document.getElementById('detection-date-to');
    const cameraFilter = document.getElementById('detection-camera-filter');
    const confidenceFilter = document.getElementById('detection-confidence-filter');
    const plateSearch = document.getElementById('plate-search');
    
    // Set default date range (last 30 days)
    if (dateFromInput && dateToInput) {
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
        
        dateFromInput.value = thirtyDaysAgo.toISOString().split('T')[0];
        dateToInput.value = today.toISOString().split('T')[0];
    }
    
    // Populate camera filter
    if (cameraFilter) {
        cameraFilter.innerHTML = '<option value="">All Cameras</option>' +
            AppState.cameras.map(camera => 
                `<option value="${camera.id}">${camera.name}</option>`
            ).join('');
    }
    
    // Add event listeners
    [dateFromInput, dateToInput, cameraFilter, confidenceFilter].forEach(element => {
        if (element) {
            element.addEventListener('change', () => {
                updateDetectionFilters();
                loadDetectionsTable();
            });
        }
    });
    
    if (plateSearch) {
        plateSearch.addEventListener('input', debounce(() => {
            updateDetectionFilters();
            loadDetectionsTable();
        }, 300));
    }
}

function updateDetectionFilters() {
    const dateFrom = document.getElementById('detection-date-from')?.value;
    const dateTo = document.getElementById('detection-date-to')?.value;
    const camera = document.getElementById('detection-camera-filter')?.value;
    const confidence = document.getElementById('detection-confidence-filter')?.value;
    const plateSearch = document.getElementById('plate-search')?.value;
    
    AppState.filters.detections = {
        dateFrom,
        dateTo,
        camera,
        confidence,
        plateSearch
    };
}

function loadDetectionsTable() {
    const tableBody = document.getElementById('detections-table-body');
    if (!tableBody) return;
    
    let filteredDetections = [...AppState.detections];
    
    // Apply filters
    const filters = AppState.filters.detections;
    
    if (filters.camera) {
        filteredDetections = filteredDetections.filter(det => det.camera_id === filters.camera);
    }
    
    if (filters.confidence) {
        filteredDetections = filteredDetections.filter(det => {
            switch (filters.confidence) {
                case 'high': return det.confidence >= 90;
                case 'medium': return det.confidence >= 70 && det.confidence < 90;
                case 'low': return det.confidence < 70;
                default: return true;
            }
        });
    }
    
    if (filters.plateSearch) {
        const search = filters.plateSearch.toLowerCase();
        filteredDetections = filteredDetections.filter(det => 
            det.plate_number.toLowerCase().includes(search));
    }
    
    tableBody.innerHTML = filteredDetections.map(detection => `
        <tr data-detection-id="${detection.id}">
            <td>
                <input type="checkbox" class="detection-checkbox" value="${detection.id}">
            </td>
            <td>${formatDateTime(detection.timestamp)}</td>
            <td>
                <span class="plate-number">${detection.plate_number}</span>
            </td>
            <td>${detection.camera_name}</td>
            <td>
                <span class="confidence-score ${getConfidenceClass(detection.confidence)}">
                    ${detection.confidence}%
                </span>
            </td>
            <td>
                <div class="vehicle-info">
                    <span>${detection.vehicle_type}</span>
                    <small>${detection.vehicle_color}</small>
                </div>
            </td>
            <td>
                <span class="status-badge ${detection.status}">${detection.status}</span>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-small" onclick="viewDetectionDetails('${detection.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="downloadDetectionImage('${detection.id}')">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn btn-small ${detection.status === 'flagged' ? 'btn-warning' : ''}" 
                            onclick="toggleDetectionFlag('${detection.id}')">
                        <i class="fas fa-flag"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    // Setup table interactions
    setupTableSorting();
    setupSelectAll();
}

function updateDetectionStats() {
    const totalDetections = AppState.detections.length;
    const uniquePlates = new Set(AppState.detections.map(d => d.plate_number)).size;
    const avgConfidence = (AppState.detections.reduce((sum, d) => sum + d.confidence, 0) / totalDetections).toFixed(1);
    const flaggedDetections = AppState.detections.filter(d => d.status === 'flagged').length;
    
    updateElement('total-detections', totalDetections.toLocaleString());
    updateElement('unique-plates', uniquePlates.toLocaleString());
    updateElement('avg-confidence', avgConfidence + '%');
    updateElement('flagged-detections', flaggedDetections);
}

function setupDetectionPagination() {
    // Similar to camera pagination but for detections
    const prevBtn = document.getElementById('detections-prev-page');
    const nextBtn = document.getElementById('detections-next-page');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (AppState.pagination.detections.page > 1) {
                AppState.pagination.detections.page--;
                loadDetectionsTable();
                updateDetectionsPagination();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            const maxPages = Math.ceil(AppState.pagination.detections.total / AppState.pagination.detections.limit);
            if (AppState.pagination.detections.page < maxPages) {
                AppState.pagination.detections.page++;
                loadDetectionsTable();
                updateDetectionsPagination();
            }
        });
    }
}

function updateDetectionsPagination() {
    const { page, limit, total } = AppState.pagination.detections;
    const maxPages = Math.ceil(total / limit);
    
    // Update pagination info
    const showingElement = document.getElementById('detections-showing');
    const totalElement = document.getElementById('detections-total');
    
    if (showingElement) {
        const start = (page - 1) * limit + 1;
        const end = Math.min(page * limit, total);
        showingElement.textContent = `${start}-${end}`;
    }
    
    if (totalElement) {
        totalElement.textContent = total;
    }
    
    // Update pagination buttons
    const prevBtn = document.getElementById('detections-prev-page');
    const nextBtn = document.getElementById('detections-next-page');
    
    if (prevBtn) {
        prevBtn.disabled = page === 1;
    }
    
    if (nextBtn) {
        nextBtn.disabled = page === maxPages;
    }
}

// Analytics Implementation
function loadAnalyticsContent() {
    setupTimeRangeSelector();
    loadAnalyticsCharts();
    loadPerformanceMetrics();
    loadTopVehicles();
    loadAlertsummary();
}

function setupTimeRangeSelector() {
    const rangeButtons = document.querySelectorAll('.range-btn');
    const customRange = document.getElementById('custom-range');
    
    rangeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            rangeButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            btn.classList.add('active');
            
            const range = btn.getAttribute('data-range');
            if (range === 'custom') {
                customRange.style.display = 'flex';
            } else {
                customRange.style.display = 'none';
                // Load data for selected range
                loadAnalyticsData(range);
            }
        });
    });
}

function loadAnalyticsCharts() {
    // Traffic Overview Chart
    const trafficChart = document.getElementById('trafficChart');
    if (trafficChart) {
        const container = trafficChart.parentElement;
        container.innerHTML = `
            <div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #718096;">
                <div style="text-align: center;">
                    <i class="fas fa-chart-line" style="font-size: 3rem; margin-bottom: 1rem; display: block;"></i>
                    <p>Traffic Overview Chart</p>
                    <small>Chart.js implementation would go here</small>
                </div>
            </div>
        `;
    }
    
    // Peak Hours Chart
    const peakHoursChart = document.getElementById('peakHoursChart');
    if (peakHoursChart) {
        const container = peakHoursChart.parentElement;
        container.innerHTML = `
            <div style="height: 200px; display: flex; align-items: center; justify-content: center; color: #718096;">
                <div style="text-align: center;">
                    <i class="fas fa-clock" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
                    <p>Peak Hours Distribution</p>
                    <small>Real chart would show hourly traffic patterns</small>
                </div>
            </div>
        `;
    }
    
    // Accuracy Chart
    const accuracyChart = document.getElementById('accuracyChart');
    if (accuracyChart) {
        const container = accuracyChart.parentElement;
        container.innerHTML = `
            <div style="height: 200px; display: flex; align-items: center; justify-content: center; color: #718096;">
                <div style="text-align: center;">
                    <i class="fas fa-bullseye" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
                    <p>Detection Accuracy Trends</p>
                    <small>Accuracy over time visualization</small>
                </div>
            </div>
        `;
    }
}

function loadPerformanceMetrics() {
    const performanceContainer = document.querySelector('.performance-metrics');
    if (!performanceContainer) return;
    
    const performanceData = AppState.cameras.map(camera => ({
        name: camera.name,
        performance: Math.floor(Math.random() * 40) + 60 // Random performance 60-100%
    }));
    
    performanceContainer.innerHTML = performanceData.map(item => `
        <div class="performance-item">
            <span class="camera-name">${item.name}</span>
            <div class="performance-bar">
                <div class="performance-fill" style="width: ${item.performance}%; background: ${getPerformanceColor(item.performance)}"></div>
            </div>
            <span class="performance-value">${item.performance}%</span>
        </div>
    `).join('');
}

function loadTopVehicles() {
    const topVehiclesList = document.querySelector('.top-vehicles-list');
    if (!topVehiclesList) return;
    
    // Generate mock top vehicles data
    const plateFrequency = {};
    AppState.detections.forEach(detection => {
        plateFrequency[detection.plate_number] = (plateFrequency[detection.plate_number] || 0) + 1;
    });
    
    const topVehicles = Object.entries(plateFrequency)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10);
    
    topVehiclesList.innerHTML = topVehicles.map(([plate, count]) => `
        <div class="top-vehicle-item">
            <span class="plate-number">${plate}</span>
            <span class="visit-count">${count} visits</span>
        </div>
    `).join('');
}

function loadAlertsummary() {
    const alertsSummary = document.querySelector('.alerts-summary');
    if (!alertsSummary) return;
    
    const alertCounts = AppState.alerts.reduce((acc, alert) => {
        const category = alert.category;
        acc[category] = (acc[category] || 0) + 1;
        return acc;
    }, {});
    
    alertsSummary.innerHTML = Object.entries(alertCounts).map(([category, count]) => `
        <div class="alert-type">
            <span class="alert-type-name">${category.charAt(0).toUpperCase() + category.slice(1)} Alerts</span>
            <span class="alert-count">${count}</span>
        </div>
    `).join('');
}

// Alerts Implementation
function loadAlertsContent() {
    setupAlertFilters();
    loadAlertsSummary();
    loadAlertsList();
}

function setupAlertFilters() {
    const severityFilter = document.getElementById('alert-severity-filter');
    const statusFilter = document.getElementById('alert-status-filter');
    const categoryFilter = document.getElementById('alert-category-filter');
    
    [severityFilter, statusFilter, categoryFilter].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', () => {
                updateAlertFilters();
                loadAlertsList();
            });
        }
    });
}

function updateAlertFilters() {
    const severity = document.getElementById('alert-severity-filter')?.value;
    const status = document.getElementById('alert-status-filter')?.value;
    const category = document.getElementById('alert-category-filter')?.value;
    
    AppState.filters.alerts = { severity, status, category };
}

function loadAlertsSummary() {
    const criticalCount = AppState.alerts.filter(a => a.severity === 'critical' && a.status === 'active').length;
    const warningCount = AppState.alerts.filter(a => a.severity === 'warning' && a.status === 'active').length;
    const infoCount = AppState.alerts.filter(a => a.severity === 'info' && a.status === 'active').length;
    const resolvedCount = AppState.alerts.filter(a => a.status === 'resolved').length;
    
    updateElement('critical-alerts', criticalCount);
    updateElement('warning-alerts', warningCount);
    updateElement('info-alerts', infoCount);
    updateElement('resolved-alerts', resolvedCount);
}

function loadAlertsList() {
    const alertsList = document.getElementById('alerts-list');
    if (!alertsList) return;
    
    let filteredAlerts = [...AppState.alerts];
    
    // Apply filters
    const filters = AppState.filters.alerts;
    if (filters.severity) {
        filteredAlerts = filteredAlerts.filter(alert => alert.severity === filters.severity);
    }
    if (filters.status) {
        filteredAlerts = filteredAlerts.filter(alert => alert.status === filters.status);
    }
    if (filters.category) {
        filteredAlerts = filteredAlerts.filter(alert => alert.category === filters.category);
    }
    
    // Sort by timestamp (newest first)
    filteredAlerts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    alertsList.innerHTML = filteredAlerts.map(alert => `
        <div class="alert-item ${alert.severity}" data-alert-id="${alert.id}">
            <div class="alert-icon">
                <i class="fas fa-${getAlertIcon(alert.severity)}"></i>
            </div>
            <div class="alert-content">
                <div class="alert-title">${alert.title}</div>
                <div class="alert-description">${alert.description}</div>
                <div class="alert-time">${formatTimeAgo(alert.timestamp)}</div>
            </div>
            <div class="alert-actions">
                ${alert.status === 'active' ? `
                    <button class="btn btn-small" onclick="acknowledgeAlert('${alert.id}')">Acknowledge</button>
                    <button class="btn btn-small btn-primary" onclick="resolveAlert('${alert.id}')">Resolve</button>
                ` : `
                    <span class="status-badge ${alert.status}">${alert.status}</span>
                `}
            </div>
        </div>
    `).join('');
}

// Reports Implementation
function loadReportsContent() {
    loadReportTypes();
    loadRecentReports();
}

function loadReportTypes() {
    const reportTypes = document.querySelectorAll('.report-type-card');
    reportTypes.forEach(card => {
        const generateBtn = card.querySelector('.btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                const reportType = card.getAttribute('data-type');
                generateReport(reportType);
            });
        }
    });
}

function loadRecentReports() {
    const reportsTableBody = document.getElementById('reports-table-body');
    if (!reportsTableBody) return;
    
    reportsTableBody.innerHTML = AppState.reports.map(report => `
        <tr data-report-id="${report.id}">
            <td>${report.name}</td>
            <td>
                <span class="report-type-badge ${report.type}">${report.type}</span>
            </td>
            <td>${formatDateTime(report.generated)}</td>
            <td>
                <span class="status-badge ${report.status}">${report.status}</span>
            </td>
            <td>${report.size}</td>
            <td>
                <div class="action-buttons">
                    ${report.status === 'completed' ? `
                        <button class="btn btn-small" onclick="downloadReport('${report.id}')">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-small btn-secondary" onclick="shareReport('${report.id}')">
                            <i class="fas fa-share"></i>
                        </button>
                    ` : `
                        <button class="btn btn-small" disabled>
                            <i class="fas fa-spinner fa-spin"></i>
                        </button>
                    `}
                    <button class="btn btn-small btn-danger" onclick="deleteReport('${report.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Settings Implementation
function loadSettingsContent() {
    setupSettingsNavigation();
    loadSettingsData();
}

function setupSettingsNavigation() {
    const settingsNavBtns = document.querySelectorAll('.settings-nav-btn');
    const settingsSections = document.querySelectorAll('.settings-section');
    
    settingsNavBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.getAttribute('data-section');
            
            // Update active nav button
            settingsNavBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show target section
            settingsSections.forEach(s => s.classList.remove('active'));
            const targetSection = document.getElementById(`settings-${section}`);
            if (targetSection) {
                targetSection.classList.add('active');
            }
        });
    });
}

function loadSettingsData() {
    loadUsersTable();
    setupRangeInputs();
    setupFormValidation();
}

function loadUsersTable() {
    const usersTableBody = document.getElementById('users-table-body');
    if (!usersTableBody) return;
    
    usersTableBody.innerHTML = AppState.users.map(user => `
        <tr data-user-id="${user.id}">
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>
                <span class="role-badge ${user.role.toLowerCase()}">${user.role}</span>
            </td>
            <td>
                <span class="status-badge ${user.status}">${user.status}</span>
            </td>
            <td>${formatTimeAgo(user.last_login)}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-small" onclick="editUser('${user.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="resetUserPassword('${user.id}')">
                        <i class="fas fa-key"></i>
                    </button>
                    <button class="btn btn-small btn-danger" onclick="deleteUser('${user.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function setupRangeInputs() {
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    rangeInputs.forEach(range => {
        const valueDisplay = range.parentElement.querySelector('.range-value');
        if (valueDisplay) {
            range.addEventListener('input', () => {
                valueDisplay.textContent = range.value + '%';
            });
        }
    });
}

function setupFormValidation() {
    const forms = document.querySelectorAll('.settings-form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                // Mark form as modified
                form.classList.add('modified');
                showSaveNotification();
            });
        });
    });
}

// Event Listeners and Interactions
function initEventListeners() {
    initQuickActions();
    initHeaderActions();
    initModalHandlers();
    initTableInteractions();
    initFormHandlers();
    initKeyboardShortcuts();
}

function initQuickActions() {
    // Add Camera Quick Action
    const addCameraQuick = document.getElementById('add-camera-quick');
    if (addCameraQuick) {
        addCameraQuick.addEventListener('click', () => openAddCameraModal());
    }
    
    // View Live Feeds
    const viewLiveFeeds = document.getElementById('view-live-feeds');
    if (viewLiveFeeds) {
        viewLiveFeeds.addEventListener('click', () => openLiveFeedsModal());
    }
    
    // Export Data
    const exportData = document.getElementById('export-data');
    if (exportData) {
        exportData.addEventListener('click', () => openExportModal());
    }
    
    // System Health
    const systemHealth = document.getElementById('system-health');
    if (systemHealth) {
        systemHealth.addEventListener('click', () => openSystemHealthModal());
    }
}

function initHeaderActions() {
    // Refresh Button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            showLoadingOverlay();
            setTimeout(() => {
                refreshCurrentPage();
                hideLoadingOverlay();
                showToast('Data refreshed successfully', 'success');
            }, 1000);
        });
    }
    
    // Notifications Button
    const notificationsBtn = document.getElementById('notifications-btn');
    if (notificationsBtn) {
        notificationsBtn.addEventListener('click', () => openNotificationsPanel());
    }
    
    // Fullscreen Button
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', toggleFullscreen);
    }
    
    // User Menu
    const userAvatar = document.querySelector('.user-avatar');
    if (userAvatar) {
        userAvatar.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleUserMenu();
        });
    }
}

function initModalHandlers() {
    // Close modals when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            closeModal();
        }
    });
    
    // Close modals with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function initTableInteractions() {
    setupTableSorting();
    setupSelectAll();
    setupBulkActions();
}

function setupTableSorting() {
    const sortableHeaders = document.querySelectorAll('th.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const sortKey = header.getAttribute('data-sort');
            const table = header.closest('table');
            const tableId = table.id;
            
            // Toggle sort direction
            const currentDirection = header.getAttribute('data-direction') || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            
            // Update all headers
            sortableHeaders.forEach(h => {
                h.setAttribute('data-direction', '');
                h.querySelector('i').className = 'fas fa-sort';
            });
            
            // Update current header
            header.setAttribute('data-direction', newDirection);
            header.querySelector('i').className = `fas fa-sort-${newDirection === 'asc' ? 'up' : 'down'}`;
            
            // Sort table data
            sortTable(tableId, sortKey, newDirection);
        });
    });
}

function setupSelectAll() {
    const selectAllCheckboxes = document.querySelectorAll('#select-all-detections');
    selectAllCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            const table = e.target.closest('table');
            const checkboxes = table.querySelectorAll('tbody input[type="checkbox"]');
            
            checkboxes.forEach(cb => {
                cb.checked = isChecked;
            });
            
            updateBulkActionButtons();
        });
    });
}

function setupBulkActions() {
    // Implementation for bulk actions
    const bulkActionBtns = document.querySelectorAll('[id*="bulk"]');
    bulkActionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const selectedItems = getSelectedTableItems();
            if (selectedItems.length === 0) {
                showToast('No items selected', 'warning');
                return;
            }
            openBulkActionModal(selectedItems);
        });
    });
}

function initFormHandlers() {
    // Form submission handlers
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            handleFormSubmission(form);
        });
    });
}

function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            focusSearch();
        }
        
        // Ctrl/Cmd + R for refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshCurrentPage();
        }
        
        // F11 for fullscreen
        if (e.key === 'F11') {
            e.preventDefault();
            toggleFullscreen();
        }
    });
}

// Real-time Updates
function initRealtimeUpdates() {
    // Simulate real-time updates
    setInterval(updateMetrics, 30000); // Every 30 seconds
    setInterval(updateSystemHealth, 10000); // Every 10 seconds
    setInterval(addNewDetection, 45000); // Every 45 seconds
    setInterval(updateCameraStatuses, 60000); // Every minute
    setInterval(checkForNewAlerts, 20000); // Every 20 seconds
}

function addNewDetection() {
    if (AppState.currentPage !== 'dashboard') return;
    
    const plateNumbers = ['ABC-123', 'XYZ-789', 'DEF-456', 'GHI-012', 'JKL-345', 'MNO-678', 'PQR-901'];
    const vehicleTypes = ['Sedan', 'SUV', 'Truck', 'Hatchback', 'Van'];
    const vehicleColors = ['Blue', 'White', 'Black', 'Silver', 'Red', 'Gray'];
    const onlineCameras = AppState.cameras.filter(cam => cam.status === 'online');
    
    if (onlineCameras.length === 0) return;
    
    const randomCamera = onlineCameras[Math.floor(Math.random() * onlineCameras.length)];
    const randomPlate = plateNumbers[Math.floor(Math.random() * plateNumbers.length)];
    const randomType = vehicleTypes[Math.floor(Math.random() * vehicleTypes.length)];
    const randomColor = vehicleColors[Math.floor(Math.random() * vehicleColors.length)];
    const randomConfidence = Math.floor(Math.random() * 30) + 70; // 70-100%
    
    const newDetection = {
        id: 'det_' + Date.now(),
        plate_number: randomPlate,
        camera_id: randomCamera.id,
        camera_name: randomCamera.name,
        confidence: randomConfidence,
        timestamp: new Date(),
        vehicle_type: randomType,
        vehicle_color: randomColor,
        status: randomConfidence >= 85 ? 'verified' : 'flagged'
    };
    
    // Add to beginning of detections array
    AppState.detections.unshift(newDetection);
    
    // Keep only last 100 detections
    if (AppState.detections.length > 100) {
        AppState.detections = AppState.detections.slice(0, 100);
    }
    
    // Update UI
    loadRecentDetections();
    updateMetrics();
    
    // Show notification for high-confidence detections
    if (randomConfidence >= 95) {
        showToast(`High confidence detection: ${randomPlate}`, 'success');
    }
}

function updateSystemHealth() {
    // Simulate system health fluctuations
    AppState.systemHealth.cpu = Math.max(20, Math.min(90, AppState.systemHealth.cpu + (Math.random() - 0.5) * 10));
    AppState.systemHealth.memory = Math.max(30, Math.min(95, AppState.systemHealth.memory + (Math.random() - 0.5) * 8));
    AppState.systemHealth.storage = Math.max(50, Math.min(95, AppState.systemHealth.storage + (Math.random() - 0.5) * 2));
    AppState.systemHealth.network = Math.max(10, Math.min(80, AppState.systemHealth.network + (Math.random() - 0.5) * 15));
    
    // Update health display if on dashboard
    if (AppState.currentPage === 'dashboard') {
        loadSystemHealth();
        updateSystemStatus();
    }
}

function updateCameraStatuses() {
    // Randomly update camera statuses
    AppState.cameras.forEach(camera => {
        if (Math.random() < 0.05) { // 5% chance of status change
            if (camera.status === 'online' && Math.random() < 0.3) {
                camera.status = 'offline';
                camera.last_seen = new Date();
                
                // Create offline alert
                const newAlert = {
                    id: 'alert_' + Date.now(),
                    title: 'Camera Offline',
                    description: `${camera.name} has gone offline`,
                    severity: 'critical',
                    category: 'camera',
                    status: 'active',
                    timestamp: new Date(),
                    camera_id: camera.id
                };
                AppState.alerts.unshift(newAlert);
                
                showToast(`Camera ${camera.name} went offline`, 'error');
            } else if (camera.status === 'offline' && Math.random() < 0.7) {
                camera.status = 'online';
                camera.last_seen = new Date();
                
                showToast(`Camera ${camera.name} is back online`, 'success');
            }
        }
    });
    
    // Update UI if on relevant pages
    if (AppState.currentPage === 'cameras') {
        loadCamerasGrid();
    }
    if (AppState.currentPage === 'dashboard') {
        loadLiveCameraFeeds();
        updateMetrics();
    }
}

function checkForNewAlerts() {
    // Check system thresholds and create alerts
    const { cpu, memory, storage, network } = AppState.systemHealth;
    
    // CPU alert
    if (cpu > 85) {
        const existingAlert = AppState.alerts.find(a => 
            a.category === 'system' && 
            a.description.includes('CPU') && 
            a.status === 'active'
        );
        
        if (!existingAlert) {
            const newAlert = {
                id: 'alert_' + Date.now(),
                title: 'High CPU Usage',
                description: `CPU usage is at ${cpu.toFixed(1)}%`,
                severity: 'warning',
                category: 'system',
                status: 'active',
                timestamp: new Date()
            };
            AppState.alerts.unshift(newAlert);
            
            showAlertBanner(newAlert);
        }
    }
    
    // Storage alert
    if (storage > 90) {
        const existingAlert = AppState.alerts.find(a => 
            a.category === 'system' && 
            a.description.includes('storage') && 
            a.status === 'active'
        );
        
        if (!existingAlert) {
            const newAlert = {
                id: 'alert_' + Date.now(),
                title: 'Storage Space Critical',
                description: `Storage usage is at ${storage.toFixed(1)}%`,
                severity: 'critical',
                category: 'system',
                status: 'active',
                timestamp: new Date()
            };
            AppState.alerts.unshift(newAlert);
            
            showAlertBanner(newAlert);
        }
    }
}

function updateSystemStatus() {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.getElementById('system-status-text');
    const systemStatusText = document.querySelector('.system-status span:last-child');
    
    const { cpu, memory, storage } = AppState.systemHealth;
    const maxUsage = Math.max(cpu, memory, storage);
    
    let status = 'online';
    let statusLabel = 'System Online';
    let healthLabel = 'Healthy';
    
    if (maxUsage > 90) {
        status = 'critical';
        statusLabel = 'System Critical';
        healthLabel = 'Critical';
    } else if (maxUsage > 80) {
        status = 'warning';
        statusLabel = 'System Warning';
        healthLabel = 'Warning';
    }
    
    if (statusIndicator) {
        statusIndicator.className = `status-indicator ${status === 'online' ? 'online' : 'offline'}`;
    }
    
    if (systemStatusText) {
        systemStatusText.textContent = statusLabel;
    }
    
    if (statusText) {
        statusText.textContent = healthLabel;
        statusText.parentElement.className = `health-indicator ${status === 'online' ? 'good' : status}`;
    }
}

// Utility Functions
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function formatTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - new Date(date)) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} mins ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
}

function formatDateTime(date) {
    return new Date(date).toLocaleString();
}

function getConfidenceClass(confidence) {
    if (confidence >= 90) return 'high';
    if (confidence >= 70) return 'medium';
    return 'low';
}

function getHealthColor(value) {
    if (value > 80) return '#e53e3e'; // Red
    if (value > 60) return '#ed8936'; // Orange
    return '#48bb78'; // Green
}

function getPerformanceColor(value) {
    if (value >= 90) return '#48bb78'; // Green
    if (value >= 70) return '#ed8936'; // Orange
    return '#e53e3e'; // Red
}

function getAlertIcon(severity) {
    switch (severity) {
        case 'critical': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        case 'info': return 'info-circle';
        default: return 'bell';
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Modal Functions
function openModal(modalContent) {
    const modalContainer = document.getElementById('modal-container');
    modalContainer.innerHTML = `
        <div class="modal-overlay active">
            <div class="modal">
                ${modalContent}
            </div>
        </div>
    `;
    
    // Add close handlers
    const closeBtn = modalContainer.querySelector('.modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
}

function closeModal() {
    const modalContainer = document.getElementById('modal-container');
    const overlay = modalContainer.querySelector('.modal-overlay');
    if (overlay) {
        overlay.classList.remove('active');
        setTimeout(() => {
            modalContainer.innerHTML = '';
        }, 300);
    }
}

function openAddCameraModal() {
    const modalContent = `
        <div class="modal-header">
            <h3 class="modal-title">Add New Camera</h3>
            <button class="modal-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-content">
            <form id="add-camera-form" class="settings-form">
                <div class="form-group">
                    <label for="camera-name">Camera Name</label>
                    <input type="text" id="camera-name" required>
                </div>
                <div class="form-group">
                    <label for="camera-ip">IP Address</label>
                    <input type="text" id="camera-ip" placeholder="192.168.1.100" required>
                </div>
                <div class="form-group">
                    <label for="camera-location">Location</label>
                    <input type="text" id="camera-location" required>
                </div>
                <div class="form-group">
                    <label for="camera-resolution">Resolution</label>
                    <select id="camera-resolution">
                        <option value="1920x1080">1920x1080 (Full HD)</option>
                        <option value="1280x720">1280x720 (HD)</option>
                        <option value="640x480">640x480 (VGA)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="camera-fps">Frame Rate (FPS)</label>
                    <select id="camera-fps">
                        <option value="30">30 FPS</option>
                        <option value="25">25 FPS</option>
                        <option value="15">15 FPS</option>
                    </select>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary" onclick="addCamera()">Add Camera</button>
        </div>
    `;
    openModal(modalContent);
}

function openCameraModal(cameraId) {
    const camera = AppState.cameras.find(cam => cam.id === cameraId);
    if (!camera) return;
    
    const modalContent = `
        <div class="modal-header">
            <h3 class="modal-title">${camera.name} - Live Feed</h3>
            <button class="modal-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-content">
            <div class="camera-live-view">
                <div class="live-feed-container">
                    <div class="live-feed-placeholder">
                        <i class="fas fa-video"></i>
                        <p>Live feed from ${camera.name}</p>
                        <small>Real stream would be displayed here</small>
                    </div>
                </div>
                <div class="camera-details">
                    <div class="detail-row">
                        <span>Status:</span>
                        <span class="camera-status ${camera.status}">
                            <i class="fas fa-circle"></i>
                            ${camera.status.toUpperCase()}
                        </span>
                    </div>
                    <div class="detail-row">
                        <span>IP Address:</span>
                        <span>${camera.ip_address}</span>
                    </div>
                    <div class="detail-row">
                        <span>Resolution:</span>
                        <span>${camera.resolution}</span>
                    </div>
                    <div class="detail-row">
                        <span>Frame Rate:</span>
                        <span>${camera.fps} FPS</span>
                    </div>
                    <div class="detail-row">
                        <span>Detections Today:</span>
                        <span>${camera.detections_today}</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            <button class="btn btn-primary" onclick="configureCamera('${camera.id}')">Configure</button>
        </div>
    `;
    openModal(modalContent);
}

function openDetectionModal(detectionId) {
    const detection = AppState.detections.find(det => det.id === detectionId);
    if (!detection) return;
    
    const modalContent = `
        <div class="modal-header">
            <h3 class="modal-title">Detection Details - ${detection.plate_number}</h3>
            <button class="modal-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-content">
            <div class="detection-details">
                <div class="detection-image-large">
                    <div class="image-placeholder">
                        <i class="fas fa-image"></i>
                        <p>Vehicle Image</p>
                        <small>Original detection image would be displayed here</small>
                    </div>
                    <div class="plate-highlight">
                        <div class="plate-number-large">${detection.plate_number}</div>
                        <div class="confidence-large ${getConfidenceClass(detection.confidence)}">
                            ${detection.confidence}% Confidence
                        </div>
                    </div>
                </div>
                <div class="detection-metadata">
                    <div class="metadata-section">
                        <h4>Detection Information</h4>
                        <div class="metadata-row">
                            <span>Timestamp:</span>
                            <span>${formatDateTime(detection.timestamp)}</span>
                        </div>
                        <div class="metadata-row">
                            <span>Camera:</span>
                            <span>${detection.camera_name}</span>
                        </div>
                        <div class="metadata-row">
                            <span>Status:</span>
                            <span class="status-badge ${detection.status}">${detection.status}</span>
                        </div>
                    </div>
                    <div class="metadata-section">
                        <h4>Vehicle Information</h4>
                        <div class="metadata-row">
                            <span>Type:</span>
                            <span>${detection.vehicle_type}</span>
                        </div>
                        <div class="metadata-row">
                            <span>Color:</span>
                            <span>${detection.vehicle_color}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            <button class="btn btn-warning" onclick="toggleDetectionFlag('${detection.id}')">
                ${detection.status === 'flagged' ? 'Unflag' : 'Flag'}
            </button>
            <button class="btn btn-primary" onclick="downloadDetectionImage('${detection.id}')">
                Download Image
            </button>
        </div>
    `;
    openModal(modalContent);
}

// Action Functions
function addCamera() {
    const form = document.getElementById('add-camera-form');
    const formData = new FormData(form);
    
    const newCamera = {
        id: 'cam_' + Date.now(),
        name: document.getElementById('camera-name').value,
        ip_address: document.getElementById('camera-ip').value,
        location: document.getElementById('camera-location').value,
        status: 'online',
        resolution: document.getElementById('camera-resolution').value,
        fps: parseInt(document.getElementById('camera-fps').value),
        last_seen: new Date(),
        detections_today: 0,
        uptime: '0d 0h 0m'
    };
    
    AppState.cameras.push(newCamera);
    
    closeModal();
    showToast(`Camera "${newCamera.name}" added successfully`, 'success');
    
    if (AppState.currentPage === 'cameras') {
        loadCamerasGrid();
    }
    
    updateMetrics();
}

function configureCamera(cameraId) {
    showToast('Camera configuration panel would open here', 'info');
    closeModal();
}

function viewLiveCamera(cameraId) {
    openCameraModal(cameraId);
}

function reconnectCamera(cameraId) {
    const camera = AppState.cameras.find(cam => cam.id === cameraId);
    if (!camera) return;
    
    showLoadingOverlay();
    
    setTimeout(() => {
        camera.status = 'online';
        camera.last_seen = new Date();
        
        hideLoadingOverlay();
        showToast(`${camera.name} reconnected successfully`, 'success');
        
        if (AppState.currentPage === 'cameras') {
            loadCamerasGrid();
        }
        
        updateMetrics();
    }, 2000);
}

function toggleDetectionFlag(detectionId) {
    const detection = AppState.detections.find(det => det.id === detectionId);
    if (!detection) return;
    
    detection.status = detection.status === 'flagged' ? 'verified' : 'flagged';
    
    showToast(`Detection ${detection.status}`, 'success');
    
    if (AppState.currentPage === 'detections') {
        loadDetectionsTable();
    }
    
    closeModal();
}

function downloadDetectionImage(detectionId) {
    showToast('Detection image download started', 'success');
}

function acknowledgeAlert(alertId) {
    const alert = AppState.alerts.find(a => a.id === alertId);
    if (!alert) return;
    
    alert.status = 'acknowledged';
    
    showToast('Alert acknowledged', 'success');
    loadAlertsList();
    updateMetrics();
}

function resolveAlert(alertId) {
    const alert = AppState.alerts.find(a => a.id === alertId);
    if (!alert) return;
    
    alert.status = 'resolved';
    
    showToast('Alert resolved', 'success');
    loadAlertsList();
    updateMetrics();
}

function generateReport(reportType) {
    showLoadingOverlay();
    
    const newReport = {
        id: 'rep_' + Date.now(),
        name: `${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report - ${new Date().toLocaleDateString()}`,
        type: reportType,
        status: 'generating',
        generated: new Date(),
        size: 'Calculating...',
        format: 'PDF'
    };
    
    AppState.reports.unshift(newReport);
    
    setTimeout(() => {
        newReport.status = 'completed';
        newReport.size = (Math.random() * 5 + 1).toFixed(1) + ' MB';
        
        hideLoadingOverlay();
        showToast(`${newReport.name} generated successfully`, 'success');
        
        if (AppState.currentPage === 'reports') {
            loadRecentReports();
        }
    }, 3000);
}

function downloadReport(reportId) {
    showToast('Report download started', 'success');
}

function deleteReport(reportId) {
    const reportIndex = AppState.reports.findIndex(r => r.id === reportId);
    if (reportIndex === -1) return;
    
    AppState.reports.splice(reportIndex, 1);
    
    showToast('Report deleted', 'success');
    loadRecentReports();
}

// UI Helper Functions
function showLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('active');
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${getToastIcon(type)}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Auto hide
    setTimeout(() => {
        hideToast(toast);
    }, duration);
    
    // Close button
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => hideToast(toast));
}

function hideToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => {
        if (toast.parentElement) {
            toast.parentElement.removeChild(toast);
        }
    }, 300);
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'warning': return 'exclamation-triangle';
        case 'error': return 'exclamation-circle';
        default: return 'info-circle';
    }
}

function showAlertBanner(alert) {
    const alertBanner = document.getElementById('alert-banner');
    if (!alertBanner) return;
    
    const alertMessage = alertBanner.querySelector('.alert-message');
    alertMessage.textContent = alert.description;
    
    alertBanner.classList.add('show');
    
    // Auto hide after 10 seconds
    setTimeout(() => {
        alertBanner.classList.remove('show');
    }, 10000);
    
    // Close button
    const closeBtn = alertBanner.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => {
        alertBanner.classList.remove('show');
    });
}

function refreshCurrentPage() {
    loadPageContent(AppState.currentPage);
    showToast('Page refreshed', 'success');
}

function toggleFullscreen() {
    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        document.documentElement.requestFullscreen();
    }
}

function initMetricsAnimation() {
    const metricCards = document.querySelectorAll('.metric-card');
    
    // Animate metrics on load
    metricCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Add click handlers for metric cards
    metricCards.forEach(card => {
        if (card.classList.contains('clickable')) {
            card.addEventListener('click', () => {
                const action = card.getAttribute('data-action');
                switch (action) {
                    case 'view-cameras':
                        loadPage('cameras');
                        break;
                    case 'view-detections':
                        loadPage('detections');
                        break;
                    case 'view-alerts':
                        loadPage('alerts');
                        break;
                    case 'view-analytics':
                        loadPage('analytics');
                        break;
                }
            });
        }
    });
}

// Additional Modal Functions
function openLiveFeedsModal() {
    const modalContent = `
        <div class="modal-header">
            <h3 class="modal-title">Live Camera Feeds</h3>
            <button class="modal-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-content">
            <div class="live-feeds-grid">
                ${AppState.cameras.filter(cam => cam.status === 'online').map(camera => `
                    <div class="live-feed-item">
                        <div class="feed-container">
                            <div class="feed-placeholder">
                                <i class="fas fa-video"></i>
                            </div>
                            <div class="feed-overlay">
                                <span class="camera-name">${camera.name}</span>
                                <span class="feed-status online">LIVE</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            <button class="btn btn-primary" onclick="openFullscreenFeeds()">Fullscreen View</button>
        </div>
    `;
    openModal(modalContent);
}

function openExportModal() {
    const modalContent = `
        <div class="modal-header">
            <h3 class="modal-title">Export Data</h3>
            <button class="modal-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-content">
            <form class="export-form">
                <div class="form-group">
                    <label>Data Type</label>
                    <select id="export-type">
                        <option value="detections">Detection Results</option>
                        <option value="cameras">Camera Information</option>
                        <option value="alerts">System Alerts</option>
                        <option value="all">All Data</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Date Range</label>
                    <div style="display: flex; gap: 1rem;">
                        <input type="date" id="export-date-from">
                        <input type="date" id="export-date-to">
                    </div>
                </div>
                <div class="form-group">
                    <label>Format</label>
                    <select id="export-format">
                        <option value="csv">CSV</option>
                        <option value="xlsx">Excel (XLSX)</option>
                        <option value="json">JSON</option>
                        <option value="pdf">PDF Report</option>
                    </select>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary" onclick="startExport()">Export Data</button>
        </div>
    `;
    openModal(modalContent);
}

function openSystemHealthModal() {
    const modalContent = `
        <div class="modal-header">
            <h3 class="modal-title">System Health Details</h3>
            <button class="modal-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-content">
            <div class="health-details">
                <div class="health-section">
                    <h4>Resource Usage</h4>
                    <div class="health-metrics">
                        <div class="health-item">
                            <span class="health-label">CPU Usage</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${AppState.systemHealth.cpu}%; background: ${getHealthColor(AppState.systemHealth.cpu)}"></div>
                            </div>
                            <span class="health-value">${AppState.systemHealth.cpu.toFixed(1)}%</span>
                        </div>
                        <div class="health-item">
                            <span class="health-label">Memory</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${AppState.systemHealth.memory}%; background: ${getHealthColor(AppState.systemHealth.memory)}"></div>
                            </div>
                            <span class="health-value">${AppState.systemHealth.memory.toFixed(1)}%</span>
                        </div>
                        <div class="health-item">
                            <span class="health-label">Storage</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${AppState.systemHealth.storage}%; background: ${getHealthColor(AppState.systemHealth.storage)}"></div>
                            </div>
                            <span class="health-value">${AppState.systemHealth.storage.toFixed(1)}%</span>
                        </div>
                        <div class="health-item">
                            <span class="health-label">Network</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${AppState.systemHealth.network}%; background: ${getHealthColor(AppState.systemHealth.network)}"></div>
                            </div>
                            <span class="health-value">${AppState.systemHealth.network.toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                <div class="health-section">
                    <h4>System Information</h4>
                    <div class="system-info">
                        <div class="info-row">
                            <span>Uptime:</span>
                            <span>15 days, 4 hours, 23 minutes</span>
                        </div>
                        <div class="info-row">
                            <span>Active Cameras:</span>
                            <span>${AppState.cameras.filter(cam => cam.status === 'online').length} of ${AppState.cameras.length}</span>
                        </div>
                        <div class="info-row">
                            <span>Processing Queue:</span>
                            <span>12 frames</span>
                        </div>
                        <div class="info-row">
                            <span>Database Size:</span>
                            <span>2.4 GB</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            <button class="btn btn-warning" onclick="runDiagnostics()">Run Diagnostics</button>
            <button class="btn btn-primary" onclick="optimizeSystem()">Optimize System</button>
        </div>
    `;
    openModal(modalContent);
}

function startExport() {
    const exportType = document.getElementById('export-type').value;
    const format = document.getElementById('export-format').value;
    
    showLoadingOverlay();
    closeModal();
    
    setTimeout(() => {
        hideLoadingOverlay();
        showToast(`${exportType} export started (${format.toUpperCase()})`, 'success');
    }, 2000);
}

function runDiagnostics() {
    showLoadingOverlay();
    closeModal();
    
    setTimeout(() => {
        hideLoadingOverlay();
        showToast('System diagnostics completed - No issues found', 'success');
    }, 3000);
}

function optimizeSystem() {
    showLoadingOverlay();
    closeModal();
    
    setTimeout(() => {
        // Slightly improve system health
        AppState.systemHealth.cpu = Math.max(20, AppState.systemHealth.cpu - 10);
        AppState.systemHealth.memory = Math.max(30, AppState.systemHealth.memory - 15);
        
        hideLoadingOverlay();
        showToast('System optimization completed', 'success');
        
        if (AppState.currentPage === 'dashboard') {
            loadSystemHealth();
        }
    }, 4000);
}

// Handle window resize
window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.remove('active');
        }
    }
});

// Handle page visibility change
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, reduce update frequency
        console.log('Page hidden - reducing update frequency');
    } else {
        // Page is visible, resume normal updates
        console.log('Page visible - resuming normal updates');
        refreshCurrentPage();
    }
});

// Error handling
window.addEventListener('error', function(e) {
    console.error('Application error:', e.error);
    showToast('An error occurred. Please refresh the page.', 'error');
});

// Show save notification for settings
function showSaveNotification() {
    const existingNotification = document.querySelector('.save-notification');
    if (existingNotification) return;
    
    const notification = document.createElement('div');
    notification.className = 'save-notification';
    notification.innerHTML = `
        <span>You have unsaved changes</span>
        <button class="btn btn-small btn-primary" onclick="saveSettings()">Save</button>
        <button class="btn btn-small btn-secondary" onclick="discardChanges()">Discard</button>
    `;
    
    document.querySelector('.settings-content').appendChild(notification);
}

function saveSettings() {
    showLoadingOverlay();
    
    setTimeout(() => {
        hideLoadingOverlay();
        showToast('Settings saved successfully', 'success');
        
        // Remove save notification
        const notification = document.querySelector('.save-notification');
        if (notification) {
            notification.remove();
        }
        
        // Remove modified class from forms
        document.querySelectorAll('.settings-form.modified').forEach(form => {
            form.classList.remove('modified');
        });
    }, 1000);
}

function discardChanges() {
    // Reload settings content to discard changes
    loadSettingsContent();
    
    // Remove save notification
    const notification = document.querySelector('.save-notification');
    if (notification) {
        notification.remove();
    }
    
    showToast('Changes discarded', 'info');
}

// Initialize service worker for offline functionality (if available)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js').then(function(registration) {
            console.log('ServiceWorker registration successful');
        }, function(err) {
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}