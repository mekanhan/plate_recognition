// Enhanced Application State with proper data relationships
const AppState = {
    currentPage: 'dashboard',
    systemInfo: {
        name: 'LPR Security System',
        version: '2.1.0',
        uptime: Date.now() - (15 * 24 * 60 * 60 * 1000), // 15 days ago
        status: 'online', // online, degraded, critical, maintenance
        statusMessage: 'All systems operational'
    },
    cameras: [],
    detections: [],
    alerts: [],
    reports: [],
    users: [],
    currentUser: {
        id: 'user_001',
        name: 'Security Admin',
        role: 'Administrator',
        email: 'admin@security.com',
        permissions: ['read', 'write', 'admin']
    },
    systemHealth: {
        cpu: 45,
        memory: 62,
        storage: 78,
        network: 32,
        lastUpdate: new Date()
    },
    statistics: {
        totalDetections: 1247,
        todayDetections: 156,
        uniquePlates: 892,
        avgConfidence: 94.2,
        flaggedDetections: 15
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
    },
    cache: {
        lastRefresh: new Date(),
        data: {}
    },
    settings: {
        autoRefresh: true,
        refreshInterval: 30000,
        notifications: true,
        theme: 'light'
    },
    notifications: [
        {
            id: 'notif_001',
            title: 'Camera Offline',
            message: 'Exit Point camera has been offline for 2 hours',
            type: 'critical',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
            read: false,
            category: 'camera'
        },
        {
            id: 'notif_002',
            title: 'High System Load',
            message: 'CPU usage above 80% for extended period',
            type: 'warning',
            timestamp: new Date(Date.now() - 45 * 60 * 1000),
            read: false,
            category: 'system'
        },
        {
            id: 'notif_003',
            title: 'Detection Processing Complete',
            message: 'Batch processing of 156 images completed successfully',
            type: 'success',
            timestamp: new Date(Date.now() - 15 * 60 * 1000),
            read: true,
            category: 'detection'
        },
        {
            id: 'notif_004',
            title: 'New Vehicle Detected',
            message: 'License plate ABC-123 detected at Entrance Gate',
            type: 'info',
            timestamp: new Date(Date.now() - 5 * 60 * 1000),
            read: false,
            category: 'detection'
        }
    ]
};

// Enhanced Mock Data with realistic relationships
const MockData = {
    cameras: [
        {
            id: 'cam_001',
            name: 'Entrance Gate',
            ip_address: '192.168.1.101',
            location: 'Main Entrance',
            zone: 'entrance',
            status: 'online',
            resolution: '1920x1080',
            fps: 30,
            last_seen: new Date(),
            detections_today: 156,
            uptime: '15d 4h 23m',
            health_score: 98,
            stream_url: 'rtsp://192.168.1.101/stream',
            recording: true,
            motion_detection: true,
            night_vision: true
        },
        {
            id: 'cam_002',
            name: 'Parking Lot A',
            ip_address: '192.168.1.102',
            location: 'Parking Area A',
            zone: 'parking',
            status: 'online',
            resolution: '1920x1080',
            fps: 25,
            last_seen: new Date(),
            detections_today: 203,
            uptime: '12d 8h 15m',
            health_score: 95,
            stream_url: 'rtsp://192.168.1.102/stream',
            recording: true,
            motion_detection: true,
            night_vision: false
        },
        {
            id: 'cam_003',
            name: 'Exit Point',
            ip_address: '192.168.1.103',
            location: 'Main Exit',
            zone: 'exit',
            status: 'offline',
            resolution: '1920x1080',
            fps: 30,
            last_seen: new Date(Date.now() - 2 * 60 * 60 * 1000),
            detections_today: 0,
            uptime: '0d 0h 0m',
            health_score: 0,
            stream_url: 'rtsp://192.168.1.103/stream',
            recording: false,
            motion_detection: false,
            night_vision: true,
            error: 'Connection timeout'
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
            vehicle_make: 'Toyota',
            vehicle_model: 'Camry',
            status: 'verified',
            flagged: false,
            direction: 'entering',
            speed: 25,
            image_path: '/images/det_001.jpg',
            processing_time: 234,
            coordinates: { x: 120, y: 45, width: 150, height: 80 }
        },
        {
            id: 'det_002',
            plate_number: 'XYZ-789',
            camera_id: 'cam_002',
            camera_name: 'Parking Lot A',
            confidence: 87.2,
            timestamp: new Date(Date.now() - 5 * 60 * 1000),
            vehicle_type: 'SUV',
            vehicle_color: 'White',
            vehicle_make: 'Honda',
            vehicle_model: 'CR-V',
            status: 'flagged',
            flagged: true,
            direction: 'parking',
            speed: 12,
            image_path: '/images/det_002.jpg',
            processing_time: 187,
            coordinates: { x: 85, y: 32, width: 140, height: 75 }
        },
        {
            id: 'det_003',
            plate_number: 'DEF-456',
            camera_id: 'cam_003',
            camera_name: 'Loading Dock',
            confidence: 92.8,
            timestamp: new Date(Date.now() - 15 * 60 * 1000),
            vehicle_type: 'Truck',
            vehicle_color: 'Red',
            vehicle_make: 'Ford',
            vehicle_model: 'F-150',
            status: 'verified',
            flagged: false,
            direction: 'exiting',
            speed: 18,
            image_path: '/images/det_003.jpg',
            processing_time: 312,
            coordinates: { x: 95, y: 28, width: 165, height: 85 }
        },
        {
            id: 'det_004',
            plate_number: 'GHI-789',
            camera_id: 'cam_001',
            camera_name: 'Entrance Gate',
            confidence: 65.3,
            timestamp: new Date(Date.now() - 30 * 60 * 1000),
            vehicle_type: 'Sedan',
            vehicle_color: 'Black',
            vehicle_make: 'BMW',
            vehicle_model: '3 Series',
            status: 'pending',
            flagged: false,
            direction: 'entering',
            speed: 22,
            image_path: '/images/det_004.jpg',
            processing_time: 445,
            coordinates: { x: 110, y: 40, width: 135, height: 70 }
        },
        {
            id: 'det_005',
            plate_number: 'JKL-012',
            camera_id: 'cam_002',
            camera_name: 'Parking Lot A',
            confidence: 94.7,
            timestamp: new Date(Date.now() - 45 * 60 * 1000),
            vehicle_type: 'SUV',
            vehicle_color: 'Silver',
            vehicle_make: 'Audi',
            vehicle_model: 'Q5',
            status: 'verified',
            flagged: false,
            direction: 'parking',
            speed: 8,
            image_path: '/images/det_005.jpg',
            processing_time: 198,
            coordinates: { x: 75, y: 35, width: 155, height: 80 }
        },
        {
            id: 'det_006',
            plate_number: 'MNO-345',
            camera_id: 'cam_004',
            camera_name: 'Side Entrance',
            confidence: 89.1,
            timestamp: new Date(Date.now() - 60 * 60 * 1000),
            vehicle_type: 'Hatchback',
            vehicle_color: 'Green',
            vehicle_make: 'Volkswagen',
            vehicle_model: 'Golf',
            status: 'flagged',
            flagged: true,
            direction: 'entering',
            speed: 35,
            image_path: '/images/det_006.jpg',
            processing_time: 267,
            coordinates: { x: 88, y: 42, width: 145, height: 72 }
        },
        {
            id: 'det_007',
            plate_number: 'PQR-678',
            camera_id: 'cam_001',
            camera_name: 'Entrance Gate',
            confidence: 96.4,
            timestamp: new Date(Date.now() - 90 * 60 * 1000),
            vehicle_type: 'Motorcycle',
            vehicle_color: 'Blue',
            vehicle_make: 'Yamaha',
            vehicle_model: 'R1',
            status: 'verified',
            flagged: false,
            direction: 'entering',
            speed: 28,
            image_path: '/images/det_007.jpg',
            processing_time: 156,
            coordinates: { x: 102, y: 55, width: 95, height: 45 }
        },
        {
            id: 'det_008',
            plate_number: 'STU-901',
            camera_id: 'cam_003',
            camera_name: 'Loading Dock',
            confidence: 78.9,
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
            vehicle_type: 'Van',
            vehicle_color: 'White',
            vehicle_make: 'Mercedes',
            vehicle_model: 'Sprinter',
            status: 'pending',
            flagged: false,
            direction: 'loading',
            speed: 15,
            image_path: '/images/det_008.jpg',
            processing_time: 389,
            coordinates: { x: 65, y: 25, width: 180, height: 95 }
        },
        {
            id: 'det_009',
            plate_number: 'VWX-234',
            camera_id: 'cam_002',
            camera_name: 'Parking Lot A',
            confidence: 91.6,
            timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
            vehicle_type: 'Sedan',
            vehicle_color: 'Gray',
            vehicle_make: 'Nissan',
            vehicle_model: 'Altima',
            status: 'verified',
            flagged: false,
            direction: 'parking',
            speed: 10,
            image_path: '/images/det_009.jpg',
            processing_time: 203,
            coordinates: { x: 125, y: 38, width: 142, height: 78 }
        },
        {
            id: 'det_010',
            plate_number: 'YZA-567',
            camera_id: 'cam_005',
            camera_name: 'Rear Exit',
            confidence: 85.3,
            timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
            vehicle_type: 'SUV',
            vehicle_color: 'Black',
            vehicle_make: 'Jeep',
            vehicle_model: 'Cherokee',
            status: 'flagged',
            flagged: true,
            direction: 'exiting',
            speed: 30,
            image_path: '/images/det_010.jpg',
            processing_time: 278,
            coordinates: { x: 98, y: 30, width: 160, height: 85 }
        },
        {
            id: 'det_011',
            plate_number: 'BCD-890',
            camera_id: 'cam_001',
            camera_name: 'Entrance Gate',
            confidence: 99.2,
            timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
            vehicle_type: 'Luxury',
            vehicle_color: 'White',
            vehicle_make: 'Tesla',
            vehicle_model: 'Model S',
            status: 'verified',
            flagged: false,
            direction: 'entering',
            speed: 20,
            image_path: '/images/det_011.jpg',
            processing_time: 145,
            coordinates: { x: 115, y: 43, width: 148, height: 76 }
        },
        {
            id: 'det_012',
            plate_number: 'EFG-123',
            camera_id: 'cam_006',
            camera_name: 'Visitor Parking',
            confidence: 73.8,
            timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000),
            vehicle_type: 'Convertible',
            vehicle_color: 'Red',
            vehicle_make: 'Mazda',
            vehicle_model: 'MX-5',
            status: 'pending',
            flagged: false,
            direction: 'parking',
            speed: 12,
            image_path: '/images/det_012.jpg',
            processing_time: 456,
            coordinates: { x: 92, y: 48, width: 128, height: 68 }
        },
        {
            id: 'det_013',
            plate_number: 'HIJ-456',
            camera_id: 'cam_002',
            camera_name: 'Parking Lot A',
            confidence: 88.7,
            timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000),
            vehicle_type: 'Pickup',
            vehicle_color: 'Blue',
            vehicle_make: 'Chevrolet',
            vehicle_model: 'Silverado',
            status: 'verified',
            flagged: false,
            direction: 'parking',
            speed: 14,
            image_path: '/images/det_013.jpg',
            processing_time: 234,
            coordinates: { x: 78, y: 33, width: 172, height: 88 }
        },
        {
            id: 'det_014',
            plate_number: 'KLM-789',
            camera_id: 'cam_003',
            camera_name: 'Loading Dock',
            confidence: 67.5,
            timestamp: new Date(Date.now() - 18 * 60 * 60 * 1000),
            vehicle_type: 'Bus',
            vehicle_color: 'Yellow',
            vehicle_make: 'Ford',
            vehicle_model: 'Transit',
            status: 'flagged',
            flagged: true,
            direction: 'loading',
            speed: 8,
            image_path: '/images/det_014.jpg',
            processing_time: 567,
            coordinates: { x: 45, y: 15, width: 220, height: 110 }
        },
        {
            id: 'det_015',
            plate_number: 'NOP-012',
            camera_id: 'cam_001',
            camera_name: 'Entrance Gate',
            confidence: 93.9,
            timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
            vehicle_type: 'Sedan',
            vehicle_color: 'Silver',
            vehicle_make: 'Hyundai',
            vehicle_model: 'Elantra',
            status: 'verified',
            flagged: false,
            direction: 'entering',
            speed: 26,
            image_path: '/images/det_015.jpg',
            processing_time: 189,
            coordinates: { x: 105, y: 41, width: 138, height: 74 }
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
            camera_id: 'cam_003',
            acknowledged: false,
            assigned_to: null,
            resolution_notes: '',
            auto_resolve: false
        },
        {
            id: 'alert_002',
            title: 'High System Load',
            description: 'CPU usage above 80% for extended period',
            severity: 'warning',
            category: 'system',
            status: 'acknowledged',
            timestamp: new Date(Date.now() - 45 * 60 * 1000),
            acknowledged: true,
            acknowledged_by: 'user_001',
            acknowledged_at: new Date(Date.now() - 30 * 60 * 1000),
            assigned_to: 'user_001',
            resolution_notes: 'Monitoring system performance',
            auto_resolve: true
        }
    ],

    reports: [
        {
            id: 'rep_001',
            name: 'Daily Traffic Report - Jan 9, 2025',
            type: 'traffic',
            status: 'completed',
            generated: new Date(Date.now() - 2 * 60 * 60 * 1000),
            generated_by: 'user_001',
            size: '2.4 MB',
            format: 'PDF',
            download_count: 3,
            expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
            parameters: {
                date_range: { from: '2025-01-09', to: '2025-01-09' },
                cameras: ['cam_001', 'cam_002'],
                include_charts: true
            }
        }
    ]
};

// Enhanced Application Controller
class LPRSystemController {
    constructor() {
        this.initializeState();
        this.initializeDarkMode();
        this.bindEvents();
        this.startRealTimeUpdates();
        this.loadInitialData();
        
        // Initialize detection filters
        this.currentDetectionFilters = {
            search: '',
            camera: '',
            confidence: '',
            dateFrom: '',
            dateTo: '',
            status: '',
            direction: '',
            speedMin: '',
            speedMax: ''
        };
        
        // Initialize sorting state
        this.currentSortState = {
            column: null,
            direction: null // null, 'asc', 'desc'
        };
        this.updateLastUpdateTime();
    }

    initializeState() {
        AppState.cameras = MockData.cameras;
        AppState.detections = MockData.detections;
        AppState.alerts = MockData.alerts;
        AppState.reports = MockData.reports;
        
        // Initialize cache
        this.updateCache('cameras', AppState.cameras);
        this.updateCache('detections', AppState.detections);
    }

    updateCache(key, data) {
        AppState.cache.data[key] = {
            data: data,
            timestamp: new Date(),
            ttl: 5 * 60 * 1000 // 5 minutes
        };
    }

    getCachedData(key) {
        const cached = AppState.cache.data[key];
        if (cached && (new Date() - cached.timestamp) < cached.ttl) {
            return cached.data;
        }
        return null;
    }

    bindEvents() {
        this.bindNavigationEvents();
        this.bindHeaderEvents();
        this.bindQuickActionEvents();
        this.bindKeyboardShortcuts();
        this.bindModalEvents();
    }

    bindNavigationEvents() {
        const menuLinks = document.querySelectorAll('.menu-link');
        console.log(`Found ${menuLinks.length} menu links`);
        
        menuLinks.forEach(link => {
            const page = link.getAttribute('data-page');
            console.log(`Binding navigation for: ${page}`);
            
            link.addEventListener('click', (e) => {
                e.preventDefault();
                console.log(`Menu link clicked: ${page}`);
                this.navigateToPage(page);
            });
        });

        // Sidebar collapse/expand functionality
        const sidebarCollapseBtn = document.getElementById('sidebar-collapse-btn');
        const sidebar = document.querySelector('.sidebar');
        
        if (sidebarCollapseBtn) {
            sidebarCollapseBtn.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                // Save collapse state to localStorage
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            });
        }

        // Restore sidebar state from localStorage
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed) {
            sidebar.classList.add('collapsed');
        }

        // Sidebar toggle for mobile
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('active');
            });
        }

        // Close sidebar on outside click (mobile)
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('active');
                }
            }
        });
    }

    bindHeaderEvents() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshCurrentPage());
        }

        // Notification button
        const notificationsBtn = document.getElementById('notifications-btn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', () => this.toggleNotificationDropdown());
        }

        // Mark all notifications as read
        const markAllReadBtn = document.getElementById('mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllNotificationsRead());
        }

        // Dark mode toggle button
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            darkModeToggle.addEventListener('click', () => this.toggleDarkMode());
        }

        // Fullscreen button
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }
    }

    bindQuickActionEvents() {
        // Metric card clicks
        document.querySelectorAll('.metric-card.clickable').forEach(card => {
            card.addEventListener('click', () => {
                const action = card.getAttribute('data-action');
                this.handleMetricCardClick(action);
            });
        });

        // Camera count selector
        const cameraCountSelect = document.getElementById('camera-count-select');
        if (cameraCountSelect) {
            cameraCountSelect.addEventListener('change', (e) => {
                const count = parseInt(e.target.value);
                this.updateCameraFeedCount(count);
            });
        }

        // View All Detections button
        const viewAllDetectionsBtn = document.getElementById('view-all-detections');
        if (viewAllDetectionsBtn) {
            viewAllDetectionsBtn.addEventListener('click', () => {
                this.navigateToPage('detections');
            });
        }

        // Camera filters
        const applyCameraFiltersBtn = document.getElementById('apply-camera-filters');
        if (applyCameraFiltersBtn) {
            applyCameraFiltersBtn.addEventListener('click', () => {
                this.applyCameraFilters();
            });
        }

        const clearCameraFiltersBtn = document.getElementById('clear-camera-filters');
        if (clearCameraFiltersBtn) {
            clearCameraFiltersBtn.addEventListener('click', () => {
                this.clearCameraFilters();
            });
        }

        // Real-time search for cameras
        const cameraSearchInput = document.getElementById('camera-search-filter');
        if (cameraSearchInput) {
            cameraSearchInput.addEventListener('input', (e) => {
                this.applyCameraFilters();
            });
        }

        // Settings navigation
        document.querySelectorAll('.settings-nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const settingsType = e.target.getAttribute('data-settings');
                this.navigateToSettings(settingsType);
            });
        });
    }

    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R for refresh
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.refreshCurrentPage();
            }

            // F11 for fullscreen
            if (e.key === 'F11') {
                e.preventDefault();
                this.toggleFullscreen();
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    bindModalEvents() {
        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeModal();
            }
        });
    }

    navigateToPage(pageName) {
        console.log(`Navigating to: ${pageName}`);
        
        // Hide all content sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Show target section
        const targetSection = document.getElementById(pageName);
        if (targetSection) {
            console.log(`Found target section: ${pageName}`);
            targetSection.classList.add('active');
            AppState.currentPage = pageName;

            // Update active menu item
            this.updateActiveMenuItem(pageName);
            this.updateBreadcrumb(pageName);
            this.loadPageContent(pageName);

            // Close sidebar on mobile
            if (window.innerWidth <= 768) {
                document.querySelector('.sidebar').classList.remove('active');
            }
        } else {
            console.error(`Target section not found: ${pageName}`);
        }
    }

    updateActiveMenuItem(pageName) {
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });

        const activeLink = document.querySelector(`[data-page="${pageName}"]`);
        if (activeLink) {
            activeLink.closest('.menu-item').classList.add('active');
        }
    }

    updateBreadcrumb(pageName) {
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

    loadPageContent(pageName) {
        switch (pageName) {
            case 'dashboard':
                this.loadDashboardContent();
                break;
            case 'cameras':
                this.loadCamerasContent();
                break;
            case 'detections':
                this.loadDetectionsContent();
                break;
            case 'analytics':
                this.loadAnalyticsContent();
                break;
            case 'alerts':
                this.loadAlertsContent();
                break;
            case 'reports':
                this.loadReportsContent();
                break;
            case 'settings':
                this.loadSettingsContent();
                break;
            default:
                console.warn(`Unknown page: ${pageName}`);
        }
    }

    loadInitialData() {
        this.loadDashboardContent();
        this.animateMetrics();
        this.loadNotifications();
        this.updateSystemStatus();
    }

    loadDashboardContent() {
        this.updateMetrics();
        this.loadLiveCameraFeeds();
        this.loadRecentDetections();
        this.loadSystemHealth();
    }

    animateMetrics() {
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.animationDelay = `${index * 0.1}s`;
                card.classList.add('animate');
            }, index * 100);
        });
    }

    updateMetrics() {
        const onlineCameras = AppState.cameras.filter(cam => cam.status === 'online').length;
        const totalDetections = AppState.statistics.todayDetections;
        const activeAlerts = AppState.alerts.filter(alert => alert.status === 'active').length;

        this.updateElement('active-cameras-count', onlineCameras);
        this.updateElement('detections-today', totalDetections.toLocaleString());
        this.updateElement('active-alerts-count', activeAlerts);
        this.updateElement('accuracy-rate', AppState.statistics.avgConfidence + '%');

        // Update sidebar badges
        this.updateElement('camera-count', AppState.cameras.length);
        this.updateElement('detection-alerts', AppState.detections.filter(d => d.flagged).length);
        this.updateElement('alert-count', activeAlerts);
    }

    loadLiveCameraFeeds() {
        const cameraGrid = document.getElementById('live-camera-grid');
        if (!cameraGrid) return;

        const cameraCountSelect = document.getElementById('camera-count-select');
        const maxCameras = cameraCountSelect ? parseInt(cameraCountSelect.value) : 4;
        const onlineCameras = AppState.cameras.filter(cam => cam.status === 'online').slice(0, maxCameras);

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

        // Update camera grid layout based on count
        this.updateCameraGridLayout(maxCameras);
    }

    updateCameraFeedCount(count) {
        AppState.settings.cameraFeedCount = count;
        this.loadLiveCameraFeeds();
    }

    updateCameraGridLayout(count) {
        const cameraGrid = document.getElementById('live-camera-grid');
        if (!cameraGrid) return;

        // Update grid layout based on camera count
        switch (count) {
            case 1:
                cameraGrid.style.gridTemplateColumns = '1fr';
                break;
            case 2:
                cameraGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
                break;
            case 3:
                cameraGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
                break;
            case 4:
            default:
                cameraGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
                break;
        }
    }

    loadRecentDetections() {
        const detectionsList = document.getElementById('recent-detections-list');
        if (!detectionsList) return;

        const recentDetections = AppState.detections.slice(0, 10);

        detectionsList.innerHTML = recentDetections.map(detection => `
            <div class="detection-item clickable" data-detection-id="${detection.id}">
                <div class="detection-image">
                    <div class="plate-preview">${detection.plate_number}</div>
                </div>
                <div class="detection-info">
                    <span class="plate-number">${detection.plate_number}</span>
                    <span class="camera-location">${detection.camera_name}</span>
                    <span class="detection-time">${this.formatTimeAgo(detection.timestamp)}</span>
                </div>
                <div class="detection-confidence">
                    <span class="confidence-score ${this.getConfidenceClass(detection.confidence)}">${detection.confidence}%</span>
                </div>
            </div>
        `).join('');

        // Add click event listeners to detection items
        document.querySelectorAll('.detection-item.clickable').forEach(item => {
            item.addEventListener('click', (e) => {
                const detectionId = e.currentTarget.getAttribute('data-detection-id');
                this.showDetectionDetails(detectionId);
            });
        });
    }

    loadSystemHealth() {
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
                    <div class="progress-fill" style="width: ${metric.value}%; background: ${this.getHealthColor(metric.value)}"></div>
                </div>
                <span class="health-value">${metric.value}%</span>
            </div>
        `).join('');
    }

    startRealTimeUpdates() {
        // Update metrics every 30 seconds
        setInterval(() => {
            this.updateMetrics();
            this.updateLastUpdateTime();
            this.updateSystemStatus();
        }, 30000);
        
        // Update system health every 10 seconds
        setInterval(() => this.updateSystemHealthData(), 10000);
        
        // Update last update time every 5 seconds
        setInterval(() => this.updateLastUpdateTime(), 5000);
    }

    updateSystemHealthData() {
        // Simulate system health fluctuations
        AppState.systemHealth.cpu = Math.max(20, Math.min(90, 
            AppState.systemHealth.cpu + (Math.random() - 0.5) * 10));
        AppState.systemHealth.memory = Math.max(30, Math.min(95, 
            AppState.systemHealth.memory + (Math.random() - 0.5) * 8));
        AppState.systemHealth.storage = Math.max(50, Math.min(95, 
            AppState.systemHealth.storage + (Math.random() - 0.5) * 2));
        AppState.systemHealth.network = Math.max(10, Math.min(80, 
            AppState.systemHealth.network + (Math.random() - 0.5) * 15));

        AppState.systemHealth.lastUpdate = new Date();

        if (AppState.currentPage === 'dashboard') {
            this.loadSystemHealth();
        }
    }

    // Action handlers
    handleMetricCardClick(action) {
        switch (action) {
            case 'view-cameras':
                this.navigateToPage('cameras');
                break;
            case 'view-detections':
                this.navigateToPage('detections');
                break;
            case 'view-alerts':
                this.navigateToPage('alerts');
                break;
            case 'view-analytics':
                this.navigateToPage('analytics');
                break;
        }
    }

    refreshCurrentPage() {
        // Add loading animation to refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            const icon = refreshBtn.querySelector('i');
            icon.classList.add('fa-spin');
        }

        // Simulate loading delay
        setTimeout(() => {
            this.loadPageContent(AppState.currentPage);
            this.updateLastUpdateTime();
            this.showToast('Data refreshed successfully', 'success');
            
            // Remove loading animation
            if (refreshBtn) {
                const icon = refreshBtn.querySelector('i');
                icon.classList.remove('fa-spin');
            }
        }, 500);
    }

    updateLastUpdateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        const lastUpdateElement = document.getElementById('last-update-time');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = timeString;
        }
    }

    updateSystemStatus() {
        // Determine system status based on alerts and camera status
        const criticalAlerts = AppState.alerts.filter(alert => alert.severity === 'critical' && alert.status === 'active');
        const offlineCameras = AppState.cameras.filter(cam => cam.status === 'offline');
        const warningAlerts = AppState.alerts.filter(alert => alert.severity === 'warning' && alert.status === 'active');

        let status = 'online';
        let statusMessage = 'All systems operational';
        let statusClass = 'online';

        if (criticalAlerts.length > 0) {
            status = 'critical';
            statusMessage = `Critical Issues (${criticalAlerts.length})`;
            statusClass = 'critical';
        } else if (offlineCameras.length > 0) {
            status = 'degraded';
            statusMessage = `${offlineCameras.length} Camera(s) Offline`;
            statusClass = 'degraded';
        } else if (warningAlerts.length > 0) {
            status = 'degraded';
            statusMessage = `${warningAlerts.length} Warning(s)`;
            statusClass = 'degraded';
        }

        AppState.systemInfo.status = status;
        AppState.systemInfo.statusMessage = statusMessage;

        // Update the UI
        const statusIndicator = document.querySelector('.status-indicator');
        const systemStatusText = document.querySelector('.system-status span:nth-child(2)');
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${statusClass}`;
        }
        
        if (systemStatusText) {
            systemStatusText.textContent = statusMessage;
        }
    }

    toggleFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            document.documentElement.requestFullscreen();
        }
    }

    // Dark Mode Methods
    initializeDarkMode() {
        // Check for saved theme preference or default to light mode
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            this.enableDarkMode();
        } else {
            this.enableLightMode();
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                if (e.matches) {
                    this.enableDarkMode();
                } else {
                    this.enableLightMode();
                }
            }
        });
    }

    toggleDarkMode() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        
        if (currentTheme === 'dark') {
            this.enableLightMode();
        } else {
            this.enableDarkMode();
        }
    }

    enableDarkMode() {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        AppState.settings.theme = 'dark';
        
        // Update dark mode toggle icon
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            const icon = darkModeToggle.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-sun';
            }
            darkModeToggle.title = 'Switch to Light Mode';
        }
    }

    enableLightMode() {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        AppState.settings.theme = 'light';
        
        // Update dark mode toggle icon
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            const icon = darkModeToggle.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-moon';
            }
            darkModeToggle.title = 'Switch to Dark Mode';
        }
    }

    closeModal() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.remove();
            }, 300);
        }
    }

    showDetectionDetails(detectionId) {
        const detection = AppState.detections.find(d => d.id === detectionId);
        if (!detection) return;

        const modalHtml = `
            <div class="modal-overlay show">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Detection Details</h3>
                        <button class="modal-close" onclick="app.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="detection-details-grid">
                            <div class="detail-section">
                                <h4>License Plate Information</h4>
                                <div class="detail-item">
                                    <span class="detail-label">Plate Number:</span>
                                    <span class="detail-value">${detection.plate_number}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Confidence:</span>
                                    <span class="detail-value confidence-score ${this.getConfidenceClass(detection.confidence)}">${detection.confidence}%</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Status:</span>
                                    <span class="detail-value badge ${detection.flagged ? 'warning' : 'success'}">${detection.status}</span>
                                </div>
                            </div>
                            <div class="detail-section">
                                <h4>Vehicle Information</h4>
                                <div class="detail-item">
                                    <span class="detail-label">Type:</span>
                                    <span class="detail-value">${detection.vehicle_type}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Color:</span>
                                    <span class="detail-value">${detection.vehicle_color}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Make:</span>
                                    <span class="detail-value">${detection.vehicle_make}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Model:</span>
                                    <span class="detail-value">${detection.vehicle_model}</span>
                                </div>
                            </div>
                            <div class="detail-section">
                                <h4>Detection Information</h4>
                                <div class="detail-item">
                                    <span class="detail-label">Camera:</span>
                                    <span class="detail-value">${detection.camera_name}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Timestamp:</span>
                                    <span class="detail-value">${new Date(detection.timestamp).toLocaleString()}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Direction:</span>
                                    <span class="detail-value">${detection.direction}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Speed:</span>
                                    <span class="detail-value">${detection.speed} mph</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Processing Time:</span>
                                    <span class="detail-value">${detection.processing_time} ms</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="app.closeModal()">Close</button>
                        <button class="btn btn-primary" onclick="app.flagDetection('${detection.id}')">
                            ${detection.flagged ? 'Unflag' : 'Flag'} Detection
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    flagDetection(detectionId) {
        const detection = AppState.detections.find(d => d.id === detectionId);
        if (detection) {
            detection.flagged = !detection.flagged;
            this.showToast(`Detection ${detection.flagged ? 'flagged' : 'unflagged'} successfully`, 'success');
            this.closeModal();
            this.loadRecentDetections();
        }
    }

    // Camera Filtering Methods
    applyCameraFilters() {
        const statusFilter = document.getElementById('camera-status-filter').value;
        const locationFilter = document.getElementById('camera-location-filter').value;
        const searchFilter = document.getElementById('camera-search-filter').value.toLowerCase();

        let filteredCameras = AppState.cameras;

        // Apply status filter
        if (statusFilter) {
            filteredCameras = filteredCameras.filter(camera => camera.status === statusFilter);
        }

        // Apply location filter
        if (locationFilter) {
            filteredCameras = filteredCameras.filter(camera => camera.zone === locationFilter);
        }

        // Apply search filter
        if (searchFilter) {
            filteredCameras = filteredCameras.filter(camera => 
                camera.name.toLowerCase().includes(searchFilter) || 
                camera.ip_address.toLowerCase().includes(searchFilter) ||
                camera.location.toLowerCase().includes(searchFilter)
            );
        }

        // Update the cameras grid with filtered results
        this.loadCamerasContent(filteredCameras);
        
        // Show filter results message
        const totalCameras = AppState.cameras.length;
        const filteredCount = filteredCameras.length;
        
        if (filteredCount !== totalCameras) {
            this.showToast(`Showing ${filteredCount} of ${totalCameras} cameras`, 'info');
        }
    }

    clearCameraFilters() {
        document.getElementById('camera-status-filter').value = '';
        document.getElementById('camera-location-filter').value = '';
        document.getElementById('camera-search-filter').value = '';
        
        // Reload all cameras
        this.loadCamerasContent();
        this.showToast('Camera filters cleared', 'success');
    }

    // Notification Methods
    toggleNotificationDropdown() {
        const dropdown = document.getElementById('notification-dropdown');
        const isVisible = dropdown.classList.contains('show');
        
        if (isVisible) {
            dropdown.classList.remove('show');
        } else {
            dropdown.classList.add('show');
            this.loadNotifications();
        }
        
        // Close dropdown when clicking outside
        if (!isVisible) {
            document.addEventListener('click', this.handleOutsideClick.bind(this));
        }
    }

    handleOutsideClick(event) {
        const dropdown = document.getElementById('notification-dropdown');
        const notificationMenu = event.target.closest('.notification-menu');
        
        if (!notificationMenu && dropdown.classList.contains('show')) {
            dropdown.classList.remove('show');
            document.removeEventListener('click', this.handleOutsideClick);
        }
    }

    loadNotifications() {
        const notificationList = document.getElementById('notification-list');
        if (!notificationList) return;

        const unreadNotifications = AppState.notifications.filter(n => !n.read);
        const recentNotifications = AppState.notifications.slice(0, 5);

        notificationList.innerHTML = recentNotifications.map(notification => `
            <div class="notification-item ${notification.read ? 'read' : 'unread'}" data-notification-id="${notification.id}">
                <div class="notification-icon ${notification.type}">
                    <i class="fas fa-${this.getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${this.formatTimeAgo(notification.timestamp)}</div>
                </div>
            </div>
        `).join('');

        // Update notification dot visibility
        const notificationDot = document.querySelector('.notification-dot');
        if (notificationDot) {
            notificationDot.style.display = unreadNotifications.length > 0 ? 'block' : 'none';
        }

        // Add click handlers to notification items
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const notificationId = e.currentTarget.getAttribute('data-notification-id');
                this.handleNotificationClick(notificationId);
            });
        });
    }

    handleNotificationClick(notificationId) {
        const notification = AppState.notifications.find(n => n.id === notificationId);
        if (notification && !notification.read) {
            notification.read = true;
            this.loadNotifications();
        }

        // Navigate based on notification category
        if (notification.category === 'camera') {
            this.navigateToPage('cameras');
        } else if (notification.category === 'detection') {
            this.navigateToPage('detections');
        } else if (notification.category === 'system') {
            this.navigateToPage('settings');
        }

        // Close dropdown
        document.getElementById('notification-dropdown').classList.remove('show');
    }

    markAllNotificationsRead() {
        AppState.notifications.forEach(notification => {
            notification.read = true;
        });
        this.loadNotifications();
        this.showToast('All notifications marked as read', 'success');
    }

    getNotificationIcon(type) {
        switch (type) {
            case 'critical': return 'exclamation-triangle';
            case 'warning': return 'exclamation-circle';
            case 'success': return 'check-circle';
            case 'info': return 'info-circle';
            default: return 'bell';
        }
    }

    // Content loading methods
    loadCamerasContent(filteredCameras = null) {
        const camerasGrid = document.getElementById('cameras-grid');
        if (!camerasGrid) return;

        const camerasToDisplay = filteredCameras || AppState.cameras;

        camerasGrid.innerHTML = camerasToDisplay.map(camera => `
            <div class="camera-card">
                <div class="camera-card-header">
                    <div class="camera-card-title">${camera.name}</div>
                    <div class="camera-card-status ${camera.status}">${camera.status.toUpperCase()}</div>
                </div>
                <div class="camera-card-body">
                    <div class="camera-card-preview">
                        <i class="fas fa-video"></i>
                    </div>
                    <div class="camera-card-info">
                        <div><strong>Location:</strong> ${camera.location}</div>
                        <div><strong>IP:</strong> ${camera.ip_address}</div>
                        <div><strong>Resolution:</strong> ${camera.resolution}</div>
                        <div><strong>FPS:</strong> ${camera.fps}</div>
                        <div><strong>Detections:</strong> ${camera.detections_today}</div>
                        <div><strong>Health:</strong> ${camera.health_score}%</div>
                    </div>
                </div>
                <div class="camera-card-actions">
                    <button class="btn btn-small btn-primary">Configure</button>
                    <button class="btn btn-small btn-secondary">View Live</button>
                </div>
            </div>
        `).join('');

        // Show message if no cameras found
        if (camerasToDisplay.length === 0) {
            camerasGrid.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <h3>No cameras found</h3>
                    <p>Try adjusting your filters or search criteria</p>
                </div>
            `;
        }
    }

    loadDetectionsContent() {
        // Load sample data into AppState if empty
        if (AppState.detections.length === 0) {
            AppState.detections = MockData.detections;
        }

        this.renderDetectionTable();
        this.initializeDetectionFilters();
        this.initializeDetectionModal();
    }

    initializeDetectionFilters() {
        // Smart search functionality
        const smartSearch = document.getElementById('smart-search');
        if (smartSearch) {
            smartSearch.addEventListener('input', (e) => {
                this.currentDetectionFilters.search = e.target.value.toLowerCase();
                this.renderDetectionTable();
            });
        }

        // Quick filter buttons
        const quickFilterButtons = document.querySelectorAll('.quick-filter-btn');
        quickFilterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active class from all buttons
                quickFilterButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const period = e.target.dataset.period;
                this.applyTimeFilter(period);
            });
        });

        // Date range filters
        const dateFrom = document.getElementById('date-from');
        const dateTo = document.getElementById('date-to');
        if (dateFrom) {
            dateFrom.addEventListener('change', () => {
                this.currentDetectionFilters.dateFrom = dateFrom.value;
                this.renderDetectionTable();
            });
        }
        if (dateTo) {
            dateTo.addEventListener('change', () => {
                this.currentDetectionFilters.dateTo = dateTo.value;
                this.renderDetectionTable();
            });
        }

        // Camera filter
        const cameraFilter = document.getElementById('camera-filter');
        if (cameraFilter) {
            cameraFilter.addEventListener('change', (e) => {
                this.currentDetectionFilters.camera = e.target.value;
                this.renderDetectionTable();
            });
        }

        // Confidence filter
        const confidenceFilter = document.getElementById('confidence-filter');
        if (confidenceFilter) {
            confidenceFilter.addEventListener('change', (e) => {
                this.currentDetectionFilters.confidence = e.target.value;
                this.renderDetectionTable();
            });
        }

        // Status filter
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentDetectionFilters.status = e.target.value;
                this.renderDetectionTable();
            });
        }

        // Direction filter
        const directionFilter = document.getElementById('direction-filter');
        if (directionFilter) {
            directionFilter.addEventListener('change', (e) => {
                this.currentDetectionFilters.direction = e.target.value;
                this.renderDetectionTable();
            });
        }

        // Speed range filters
        const speedMin = document.getElementById('speed-min');
        const speedMax = document.getElementById('speed-max');
        if (speedMin) {
            speedMin.addEventListener('input', (e) => {
                this.currentDetectionFilters.speedMin = e.target.value;
                this.renderDetectionTable();
            });
        }
        if (speedMax) {
            speedMax.addEventListener('input', (e) => {
                this.currentDetectionFilters.speedMax = e.target.value;
                this.renderDetectionTable();
            });
        }

        // Apply filters button
        const applyFiltersBtn = document.getElementById('apply-filters-btn');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => {
                this.renderDetectionTable();
            });
        }

        // Clear All filters button
        const clearAllFiltersBtn = document.getElementById('clear-all-filters-btn');
        if (clearAllFiltersBtn) {
            clearAllFiltersBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }

        // Select all checkbox
        const selectAllCheckbox = document.getElementById('select-all-detections');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                this.toggleAllDetectionSelection(e.target.checked);
            });
        }

        // Export buttons
        const exportCsvBtn = document.getElementById('export-csv-btn');
        const exportPdfBtn = document.getElementById('export-pdf-btn');
        
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportDetections('csv'));
        }
        if (exportPdfBtn) {
            exportPdfBtn.addEventListener('click', () => this.exportDetections('pdf'));
        }

        // Sortable headers
        const sortableHeaders = document.querySelectorAll('.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', (e) => {
                e.preventDefault();
                const column = header.getAttribute('data-sort');
                this.toggleSort(column);
            });
        });
    }

    applyTimeFilter(period) {
        const now = new Date();
        let startTime, endTime;
        
        switch (period) {
            case '1h':
                startTime = new Date(now.getTime() - 60 * 60 * 1000);
                endTime = now;
                break;
            case '24h':
                startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                endTime = now;
                break;
            case 'today':
                startTime = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                endTime = now;
                break;
            case 'yesterday':
                startTime = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
                endTime = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                break;
            case 'this-week':
                const startOfWeek = new Date(now);
                startOfWeek.setDate(now.getDate() - now.getDay());
                startOfWeek.setHours(0, 0, 0, 0);
                startTime = startOfWeek;
                endTime = now;
                break;
            case 'last-week':
                const lastWeekStart = new Date(now);
                lastWeekStart.setDate(now.getDate() - now.getDay() - 7);
                lastWeekStart.setHours(0, 0, 0, 0);
                const lastWeekEnd = new Date(lastWeekStart);
                lastWeekEnd.setDate(lastWeekStart.getDate() + 6);
                lastWeekEnd.setHours(23, 59, 59, 999);
                startTime = lastWeekStart;
                endTime = lastWeekEnd;
                break;
            case '30d':
                startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                endTime = now;
                break;
            case 'custom':
                // Custom date range - don't set any dates, let user pick
                this.showToast('Please select custom date range', 'info');
                return;
            default:
                startTime = null;
                endTime = null;
        }
        
        if (startTime && endTime) {
            this.currentDetectionFilters.dateFrom = startTime.toISOString().split('T')[0];
            this.currentDetectionFilters.dateTo = endTime.toISOString().split('T')[0];
            
            // Update the date inputs
            const dateFromInput = document.getElementById('date-from');
            const dateToInput = document.getElementById('date-to');
            if (dateFromInput) dateFromInput.value = this.currentDetectionFilters.dateFrom;
            if (dateToInput) dateToInput.value = this.currentDetectionFilters.dateTo;
        }
        
        this.renderDetectionTable();
    }

    clearAllFilters() {
        // Reset all filter values
        this.currentDetectionFilters = {
            search: '',
            camera: '',
            confidence: '',
            dateFrom: '',
            dateTo: '',
            status: '',
            direction: '',
            speedMin: '',
            speedMax: ''
        };

        // Clear all form inputs
        const smartSearch = document.getElementById('smart-search');
        const dateFrom = document.getElementById('date-from');
        const dateTo = document.getElementById('date-to');
        const cameraFilter = document.getElementById('camera-filter');
        const confidenceFilter = document.getElementById('confidence-filter');
        const statusFilter = document.getElementById('status-filter');
        const directionFilter = document.getElementById('direction-filter');
        const speedMin = document.getElementById('speed-min');
        const speedMax = document.getElementById('speed-max');

        if (smartSearch) smartSearch.value = '';
        if (dateFrom) dateFrom.value = '';
        if (dateTo) dateTo.value = '';
        if (cameraFilter) cameraFilter.value = '';
        if (confidenceFilter) confidenceFilter.value = '';
        if (statusFilter) statusFilter.value = '';
        if (directionFilter) directionFilter.value = '';
        if (speedMin) speedMin.value = '';
        if (speedMax) speedMax.value = '';

        // Remove active class from quick filter buttons
        const quickFilterButtons = document.querySelectorAll('.quick-filter-btn');
        quickFilterButtons.forEach(btn => btn.classList.remove('active'));

        // Re-render the table with no filters
        this.renderDetectionTable();
        
        this.showToast('All filters cleared', 'success');
    }

    toggleSort(column) {
        // Determine new sort direction
        if (this.currentSortState.column === column) {
            // Same column clicked - cycle through: asc -> desc -> null
            switch (this.currentSortState.direction) {
                case null:
                    this.currentSortState.direction = 'asc';
                    break;
                case 'asc':
                    this.currentSortState.direction = 'desc';
                    break;
                case 'desc':
                    this.currentSortState.direction = null;
                    this.currentSortState.column = null;
                    break;
            }
        } else {
            // New column clicked - start with ascending
            this.currentSortState.column = column;
            this.currentSortState.direction = 'asc';
        }

        // Update sort icons
        this.updateSortIcons();
        
        // Re-render table with new sort
        this.renderDetectionTable();
    }

    updateSortIcons() {
        // Reset all sort icons
        document.querySelectorAll('.sortable .sort-icon').forEach(icon => {
            icon.className = 'fas fa-sort sort-icon';
        });

        // Update active sort icon
        if (this.currentSortState.column && this.currentSortState.direction) {
            const activeHeader = document.querySelector(`[data-sort="${this.currentSortState.column}"] .sort-icon`);
            if (activeHeader) {
                if (this.currentSortState.direction === 'asc') {
                    activeHeader.className = 'fas fa-sort-up sort-icon';
                } else if (this.currentSortState.direction === 'desc') {
                    activeHeader.className = 'fas fa-sort-down sort-icon';
                }
            }
        }
    }

    sortDetections(detections) {
        if (!this.currentSortState.column || !this.currentSortState.direction) {
            return detections;
        }

        const column = this.currentSortState.column;
        const isAscending = this.currentSortState.direction === 'asc';

        return [...detections].sort((a, b) => {
            let valueA, valueB;

            switch (column) {
                case 'timestamp':
                    valueA = new Date(a.timestamp);
                    valueB = new Date(b.timestamp);
                    break;
                case 'plate':
                    valueA = a.plate_number.toLowerCase();
                    valueB = b.plate_number.toLowerCase();
                    break;
                case 'camera':
                    valueA = a.camera_name.toLowerCase();
                    valueB = b.camera_name.toLowerCase();
                    break;
                case 'confidence':
                    valueA = parseFloat(a.confidence);
                    valueB = parseFloat(b.confidence);
                    break;
                case 'vehicle':
                    valueA = `${a.vehicle_color} ${a.vehicle_make} ${a.vehicle_type}`.toLowerCase();
                    valueB = `${b.vehicle_color} ${b.vehicle_make} ${b.vehicle_type}`.toLowerCase();
                    break;
                case 'status':
                    valueA = a.status.toLowerCase();
                    valueB = b.status.toLowerCase();
                    break;
                default:
                    return 0;
            }

            if (valueA < valueB) {
                return isAscending ? -1 : 1;
            }
            if (valueA > valueB) {
                return isAscending ? 1 : -1;
            }
            return 0;
        });
    }

    renderDetectionTable() {
        const tableBody = document.getElementById('detection-table-body');
        if (!tableBody) return;

        const filteredDetections = this.filterDetections();
        const sortedDetections = this.sortDetections(filteredDetections);
        
        tableBody.innerHTML = sortedDetections.map(detection => `
            <tr data-detection-id="${detection.id}">
                <td class="checkbox-column">
                    <input type="checkbox" class="detection-checkbox" value="${detection.id}">
                </td>
                <td>${this.formatDateTime(detection.timestamp)}</td>
                <td class="plate-number">${detection.plate_number}</td>
                <td>${detection.camera_name}</td>
                <td>
                    <span class="confidence-badge ${this.getConfidenceClass(detection.confidence)}">
                        ${detection.confidence}%
                    </span>
                </td>
                <td class="vehicle-info">
                    ${detection.vehicle_color} ${detection.vehicle_make} ${detection.vehicle_type}
                </td>
                <td>
                    <span class="status-badge ${detection.status}">
                        ${detection.status}
                    </span>
                </td>
                <td class="actions-column">
                    <div class="row-actions">
                        <button class="row-action-btn view" onclick="app.openDetectionModal('${detection.id}')" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="row-action-btn download" onclick="app.downloadDetection('${detection.id}')" title="Download">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="row-action-btn flag" onclick="app.toggleDetectionFlag('${detection.id}')" title="Flag">
                            <i class="fas fa-flag"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Add event listeners for checkboxes
        this.initializeDetectionCheckboxes();
        this.updateBulkActions();
    }

    filterDetections() {
        let detections = [...AppState.detections];

        // Apply search filter
        if (this.currentDetectionFilters.search) {
            const searchTerm = this.currentDetectionFilters.search;
            detections = detections.filter(detection => 
                detection.plate_number.toLowerCase().includes(searchTerm) ||
                detection.vehicle_color.toLowerCase().includes(searchTerm) ||
                detection.vehicle_make.toLowerCase().includes(searchTerm) ||
                detection.vehicle_model.toLowerCase().includes(searchTerm) ||
                detection.vehicle_type.toLowerCase().includes(searchTerm) ||
                detection.camera_name.toLowerCase().includes(searchTerm)
            );
        }

        // Apply camera filter
        if (this.currentDetectionFilters.camera) {
            detections = detections.filter(detection => 
                detection.camera_id === this.currentDetectionFilters.camera
            );
        }

        // Apply confidence filter
        if (this.currentDetectionFilters.confidence) {
            const confidenceFilter = this.currentDetectionFilters.confidence;
            detections = detections.filter(detection => {
                switch (confidenceFilter) {
                    case 'high':
                        return detection.confidence >= 90;
                    case 'medium':
                        return detection.confidence >= 70 && detection.confidence < 90;
                    case 'low':
                        return detection.confidence < 70;
                    default:
                        return true;
                }
            });
        }

        // Apply date filters
        if (this.currentDetectionFilters.dateFrom || this.currentDetectionFilters.dateTo) {
            detections = detections.filter(detection => {
                const detectionDate = new Date(detection.timestamp).toISOString().split('T')[0];
                
                if (this.currentDetectionFilters.dateFrom && detectionDate < this.currentDetectionFilters.dateFrom) {
                    return false;
                }
                if (this.currentDetectionFilters.dateTo && detectionDate > this.currentDetectionFilters.dateTo) {
                    return false;
                }
                return true;
            });
        }

        // Apply status filter
        if (this.currentDetectionFilters.status) {
            detections = detections.filter(detection => 
                detection.status === this.currentDetectionFilters.status
            );
        }

        // Apply direction filter
        if (this.currentDetectionFilters.direction) {
            detections = detections.filter(detection => 
                detection.direction === this.currentDetectionFilters.direction
            );
        }

        // Apply speed range filter
        if (this.currentDetectionFilters.speedMin || this.currentDetectionFilters.speedMax) {
            detections = detections.filter(detection => {
                const speed = parseFloat(detection.speed) || 0;
                const minSpeed = parseFloat(this.currentDetectionFilters.speedMin) || 0;
                const maxSpeed = parseFloat(this.currentDetectionFilters.speedMax) || Number.MAX_VALUE;
                
                return speed >= minSpeed && speed <= maxSpeed;
            });
        }

        return detections;
    }

    initializeDetectionCheckboxes() {
        const checkboxes = document.querySelectorAll('.detection-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkActions();
            });
        });
    }

    toggleAllDetectionSelection(checked) {
        const checkboxes = document.querySelectorAll('.detection-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
        this.updateBulkActions();
    }

    updateBulkActions() {
        const selectedCount = document.querySelectorAll('.detection-checkbox:checked').length;
        const bulkActions = document.getElementById('bulk-actions');
        
        if (bulkActions) {
            bulkActions.style.display = selectedCount > 0 ? 'flex' : 'none';
        }
    }

    initializeDetectionModal() {
        // Initialize detection modal tabs
        const detectionTabs = document.querySelectorAll('.detection-tab');
        detectionTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const targetTab = e.target.dataset.tab;
                this.switchDetectionTab(targetTab);
            });
        });

        // Modal close buttons
        const closeButtons = document.querySelectorAll('#close-detection-modal, #close-modal-btn');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeDetectionModal();
            });
        });

        // Modal overlay click to close
        const modalOverlay = document.getElementById('detection-details-modal');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.closeDetectionModal();
                }
            });
        }
    }

    openDetectionModal(detectionId) {
        const detection = AppState.detections.find(d => d.id === detectionId);
        if (!detection) return;

        // Populate modal with detection data
        document.getElementById('modal-plate-number').textContent = detection.plate_number;
        document.getElementById('modal-plate-overlay').textContent = detection.plate_number;
        document.getElementById('modal-timestamp').textContent = this.formatDateTime(detection.timestamp);
        document.getElementById('modal-camera').textContent = detection.camera_name;
        document.getElementById('modal-location').textContent = detection.camera_name;
        document.getElementById('modal-confidence').textContent = `${detection.confidence}%`;
        document.getElementById('modal-confidence').className = `confidence-badge ${this.getConfidenceClass(detection.confidence)}`;
        document.getElementById('modal-status').textContent = detection.status;
        document.getElementById('modal-status').className = `status-badge ${detection.status}`;
        document.getElementById('modal-processing-time').textContent = `${detection.processing_time}ms`;
        
        // Vehicle details
        document.getElementById('modal-vehicle-type').textContent = detection.vehicle_type;
        document.getElementById('modal-vehicle-color').textContent = detection.vehicle_color;
        document.getElementById('modal-vehicle-model').textContent = `${detection.vehicle_make} ${detection.vehicle_model}`;
        document.getElementById('modal-direction').textContent = detection.direction;
        document.getElementById('modal-speed').textContent = `${detection.speed} mph`;

        // Show modal
        document.getElementById('detection-details-modal').style.display = 'flex';
    }

    closeDetectionModal() {
        document.getElementById('detection-details-modal').style.display = 'none';
    }

    switchDetectionTab(tabName) {
        // Remove active class from all tabs and panels
        document.querySelectorAll('.detection-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        
        // Add active class to selected tab and panel
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    downloadDetection(detectionId) {
        const detection = AppState.detections.find(d => d.id === detectionId);
        if (!detection) return;

        // Create mock download
        const data = JSON.stringify(detection, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `detection_${detection.plate_number}_${detection.id}.json`;
        a.click();
        URL.revokeObjectURL(url);

        this.showToast(`Downloaded detection data for ${detection.plate_number}`, 'success');
    }

    toggleDetectionFlag(detectionId) {
        const detection = AppState.detections.find(d => d.id === detectionId);
        if (!detection) return;

        detection.flagged = !detection.flagged;
        detection.status = detection.flagged ? 'flagged' : 'verified';
        
        this.renderDetectionTable();
        this.showToast(`Detection ${detection.plate_number} ${detection.flagged ? 'flagged' : 'unflagged'}`, 'info');
    }

    exportDetections(format) {
        const filteredDetections = this.filterDetections();
        
        if (format === 'csv') {
            this.exportToCSV(filteredDetections);
        } else if (format === 'pdf') {
            this.exportToPDF(filteredDetections);
        }
    }

    exportToCSV(detections) {
        const headers = ['Timestamp', 'Plate Number', 'Camera', 'Confidence', 'Vehicle Type', 'Vehicle Color', 'Vehicle Make', 'Status'];
        const csvContent = [
            headers.join(','),
            ...detections.map(d => [
                this.formatDateTime(d.timestamp),
                d.plate_number,
                d.camera_name,
                `${d.confidence}%`,
                d.vehicle_type,
                d.vehicle_color,
                d.vehicle_make,
                d.status
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `detections_export_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);

        this.showToast(`Exported ${detections.length} detections to CSV`, 'success');
    }

    exportToPDF(detections) {
        // Mock PDF export
        this.showToast(`PDF export functionality would be implemented here. ${detections.length} detections selected.`, 'info');
    }

    getConfidenceClass(confidence) {
        if (confidence >= 90) return 'high';
        if (confidence >= 70) return 'medium';
        return 'low';
    }

    formatDateTime(date) {
        return new Date(date).toLocaleString();
    }

    loadAnalyticsContent() {
        const analyticsGrid = document.getElementById('analytics-grid');
        if (!analyticsGrid) return;

        analyticsGrid.innerHTML = `
            <div class="analytics-card">
                <div class="analytics-card-header">
                    <div class="analytics-card-title">Detection Trends</div>
                </div>
                <div class="analytics-card-body">
                    <i class="fas fa-chart-line" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <h4>Detection Trends Chart</h4>
                    <p>Real-time detection analytics over time</p>
                </div>
            </div>
            <div class="analytics-card">
                <div class="analytics-card-header">
                    <div class="analytics-card-title">Camera Performance</div>
                </div>
                <div class="analytics-card-body">
                    <i class="fas fa-chart-bar" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <h4>Camera Performance</h4>
                    <p>Individual camera detection rates</p>
                </div>
            </div>
            <div class="analytics-card">
                <div class="analytics-card-header">
                    <div class="analytics-card-title">Traffic Flow</div>
                </div>
                <div class="analytics-card-body">
                    <i class="fas fa-chart-area" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <h4>Traffic Flow Analysis</h4>
                    <p>Peak hours and traffic patterns</p>
                </div>
            </div>
            <div class="analytics-card">
                <div class="analytics-card-header">
                    <div class="analytics-card-title">System Health</div>
                </div>
                <div class="analytics-card-body">
                    <i class="fas fa-chart-pie" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <h4>System Health Metrics</h4>
                    <p>Overall system performance</p>
                </div>
            </div>
        `;
    }

    loadAlertsContent() {
        const alertsList = document.getElementById('alerts-list');
        if (!alertsList) return;

        alertsList.innerHTML = AppState.alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-icon ${alert.severity}">
                    <i class="fas fa-${alert.severity === 'critical' ? 'exclamation-triangle' : alert.severity === 'warning' ? 'exclamation-circle' : 'info-circle'}"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-title">${alert.title}</div>
                    <div class="alert-description">${alert.description}</div>
                    <div class="alert-meta">
                        <span>Category: ${alert.category}</span>
                        <span>Time: ${this.formatTimeAgo(alert.timestamp)}</span>
                        <span>Status: ${alert.status}</span>
                    </div>
                </div>
                <div class="alert-actions-btn">
                    <button class="btn btn-small btn-primary">Acknowledge</button>
                    <button class="btn btn-small btn-secondary">Details</button>
                </div>
            </div>
        `).join('');
    }

    loadReportsContent() {
        const reportsList = document.getElementById('reports-list');
        if (!reportsList) return;

        reportsList.innerHTML = AppState.reports.map(report => `
            <div class="report-item">
                <div class="report-icon">
                    <i class="fas fa-file-alt"></i>
                </div>
                <div class="report-content">
                    <div class="report-title">${report.name}</div>
                    <div class="report-meta">
                        <span>Type: ${report.type}</span>
                        <span>Size: ${report.size}</span>
                        <span>Status: ${report.status}</span>
                        <span>Generated: ${this.formatTimeAgo(report.generated)}</span>
                    </div>
                </div>
                <div class="report-actions-btn">
                    <button class="btn btn-small btn-primary">Download</button>
                    <button class="btn btn-small btn-secondary">View</button>
                </div>
            </div>
        `).join('');
    }

    loadSettingsContent() {
        const settingsContent = document.getElementById('settings-content');
        if (!settingsContent) return;

        settingsContent.innerHTML = `
            <div class="settings-panel active" id="settings-general">
                <div class="settings-group">
                    <div class="settings-group-title">General Settings</div>
                    <div class="settings-item">
                        <div class="settings-item-info">
                            <div class="settings-item-title">Auto Refresh</div>
                            <div class="settings-item-description">Automatically refresh data every 30 seconds</div>
                        </div>
                        <div class="settings-item-control">
                            <div class="toggle-switch active" onclick="this.classList.toggle('active')"></div>
                        </div>
                    </div>
                    <div class="settings-item">
                        <div class="settings-item-info">
                            <div class="settings-item-title">Notifications</div>
                            <div class="settings-item-description">Enable desktop notifications for alerts</div>
                        </div>
                        <div class="settings-item-control">
                            <div class="toggle-switch active" onclick="this.classList.toggle('active')"></div>
                        </div>
                    </div>
                </div>
                <div class="settings-group">
                    <div class="settings-group-title">Display Settings</div>
                    <div class="settings-item">
                        <div class="settings-item-info">
                            <div class="settings-item-title">Dark Mode</div>
                            <div class="settings-item-description">Use dark theme for better visibility in low light</div>
                        </div>
                        <div class="settings-item-control">
                            <div class="toggle-switch" onclick="this.classList.toggle('active')"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    navigateToSettings(settingsType) {
        // Remove active class from all settings nav buttons
        document.querySelectorAll('.settings-nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Add active class to clicked button
        document.querySelector(`[data-settings="${settingsType}"]`).classList.add('active');

        // Show appropriate settings panel
        this.showSettingsPanel(settingsType);
    }

    showSettingsPanel(settingsType) {
        // For now, just show the general settings
        // In a full implementation, you would have different panels for each setting type
        this.showToast(`${settingsType} settings selected`, 'info');
    }

    // UI Helper Methods
    showToast(message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
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
            this.hideToast(toast);
        }, duration);

        // Close button
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.hideToast(toast));
    }

    hideToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }

    // Utility Methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - new Date(date)) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} mins ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        return `${Math.floor(diffInSeconds / 86400)} days ago`;
    }

    getConfidenceClass(confidence) {
        if (confidence >= 90) return 'high';
        if (confidence >= 70) return 'medium';
        return 'low';
    }

    getHealthColor(value) {
        if (value > 80) return '#e53e3e'; // Red
        if (value > 60) return '#ed8936'; // Orange
        return '#48bb78'; // Green
    }

    getToastIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'warning': return 'exclamation-triangle';
            case 'error': return 'exclamation-circle';
            default: return 'info-circle';
        }
    }
}

// Initialize Application
let app;

document.addEventListener('DOMContentLoaded', function() {
    app = new LPRSystemController();
    
    // Make app globally available for inline event handlers
    window.app = app;
    
    console.log('Enhanced LPR System initialized successfully');
});

// Handle visibility change for performance optimization
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('Page hidden - reducing update frequency');
    } else {
        console.log('Page visible - resuming normal updates');
        if (app) {
            app.refreshCurrentPage();
        }
    }
});