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
        
        // Check if we need to restore a page first
        const savedPage = localStorage.getItem('currentPage');
        if (savedPage && savedPage !== 'dashboard') {
            // Defer initial data loading until after page restoration
            setTimeout(() => {
                this.restoreCurrentPage();
                this.loadInitialData();
            }, 200);
        } else {
            // Load dashboard immediately
            this.loadInitialData();
        }
        
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

    restoreCurrentPage() {
        // Restore the last active page from localStorage
        const savedPage = localStorage.getItem('currentPage');
        console.log('Restoring page:', savedPage);
        
        if (savedPage && savedPage !== 'dashboard') {
            // Check if the target page element exists
            const targetElement = document.getElementById(savedPage);
            if (targetElement) {
                console.log('Navigating to saved page:', savedPage);
                this.navigateToPage(savedPage);
            } else {
                console.warn('Target page element not found:', savedPage);
                // Clear invalid page from localStorage
                localStorage.removeItem('currentPage');
            }
        }
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
            
            // Save current page to localStorage
            localStorage.setItem('currentPage', pageName);

            // Re-initialize camera management when navigating to cameras page
            if (pageName === 'cameras' && window.cameraManager) {
                console.log('Re-initializing camera manager for cameras page');
                window.cameraManager.setupAddCameraModal();
                window.cameraManager.loadCameras();
            }

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
                // Camera rendering is now handled by CameraManager
                // this.loadCamerasContent();
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

    // WebSocket Integration Methods
    updateConnectionStatus(connected) {
        const statusElements = document.querySelectorAll('.status-indicator');
        statusElements.forEach(element => {
            if (connected) {
                element.classList.remove('offline');
                element.classList.add('online');
            } else {
                element.classList.remove('online');
                element.classList.add('offline');
            }
        });
        
        // Update system status text
        const systemStatusText = document.querySelector('.system-status span:nth-child(2)');
        if (systemStatusText && !connected) {
            systemStatusText.textContent = 'Connection Lost';
        } else if (connected) {
            this.updateSystemStatus();
        }
    }

    updateCameraList(cameras) {
        console.log('Updating camera list:', cameras);
        AppState.cameras = cameras;
        this.updateCache('cameras', cameras);
        
        // Update camera count in UI
        const cameraCount = document.getElementById('camera-count');
        if (cameraCount) {
            cameraCount.textContent = cameras.length;
        }
        
        const activeCamerasCount = document.getElementById('active-cameras-count');
        if (activeCamerasCount) {
            activeCamerasCount.textContent = cameras.filter(cam => cam.status === 'online').length;
        }
        
        // Refresh current page if on cameras page
        if (AppState.currentPage === 'cameras') {
            this.renderCamerasPage();
        }
        
        // Update dashboard camera feeds
        if (AppState.currentPage === 'dashboard') {
            this.updateDashboardCameraFeeds();
        }
    }

    updateCameraFrame(cameraId, frameData) {
        console.log('Updating camera frame:', cameraId, frameData);
        
        // Find camera feed element
        const cameraFeedElement = document.querySelector(`[data-camera-id="${cameraId}"]`);
        if (cameraFeedElement) {
            const imgElement = cameraFeedElement.querySelector('img') || cameraFeedElement.querySelector('.camera-preview');
            
            if (imgElement && frameData.image) {
                // Update with base64 image data
                imgElement.src = `data:image/jpeg;base64,${frameData.image}`;
                imgElement.style.display = 'block';
                
                // Hide placeholder if present
                const placeholder = cameraFeedElement.querySelector('.camera-placeholder');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
            }
        }
        
        // Update frame timestamp
        const timestampElement = document.querySelector(`[data-camera-id="${cameraId}"] .frame-timestamp`);
        if (timestampElement && frameData.timestamp) {
            timestampElement.textContent = new Date(frameData.timestamp * 1000).toLocaleTimeString();
        }
    }

    updateCameraStatus(cameraId, statusData) {
        console.log('Updating camera status:', cameraId, statusData);
        
        // Find and update camera in AppState
        const camera = AppState.cameras.find(cam => cam.id === cameraId);
        if (camera) {
            camera.status = statusData.status;
            camera.last_seen = statusData.last_seen;
            
            // Update UI elements
            const statusElements = document.querySelectorAll(`[data-camera-id="${cameraId}"] .camera-status`);
            statusElements.forEach(element => {
                element.className = `camera-status ${statusData.status}`;
                element.textContent = statusData.status.toUpperCase();
            });
            
            // Update system status
            this.updateSystemStatus();
        }
    }

    addDetectionResult(detection) {
        console.log('Adding detection result:', detection);
        
        // Add to AppState
        AppState.detections.unshift(detection);
        AppState.statistics.totalDetections++;
        AppState.statistics.todayDetections++;
        
        // Update detection count in UI
        const detectionsToday = document.getElementById('detections-today');
        if (detectionsToday) {
            detectionsToday.textContent = AppState.statistics.todayDetections.toLocaleString();
        }
        
        // Refresh detections page if currently viewing
        if (AppState.currentPage === 'detections') {
            this.renderDetectionsPage();
        }
        
        // Update recent detections on dashboard
        if (AppState.currentPage === 'dashboard') {
            this.updateDashboardRecentDetections();
        }
        
        // Show notification
        this.showToast(`New detection: ${detection.plate_text} (${detection.confidence}% confidence)`, 'success');
    }

    updateSystemStats(stats) {
        console.log('Updating system stats:', stats);
        
        // Update system health metrics
        if (stats.cpu !== undefined) {
            AppState.systemHealth.cpu = stats.cpu;
        }
        if (stats.memory !== undefined) {
            AppState.systemHealth.memory = stats.memory;
        }
        if (stats.storage !== undefined) {
            AppState.systemHealth.storage = stats.storage;
        }
        if (stats.network !== undefined) {
            AppState.systemHealth.network = stats.network;
        }
        
        AppState.systemHealth.lastUpdate = new Date();
        
        // Update dashboard system health display
        if (AppState.currentPage === 'dashboard') {
            this.updateDashboardSystemHealth();
        }
    }

    updateDashboardCameraFeeds() {
        const cameraGrid = document.getElementById('live-camera-grid');
        if (!cameraGrid) return;
        
        const cameraCountSelect = document.getElementById('camera-count-select');
        const maxCameras = cameraCountSelect ? parseInt(cameraCountSelect.value) : 4;
        
        const onlineCameras = AppState.cameras.filter(cam => cam.status === 'online').slice(0, maxCameras);
        
        cameraGrid.innerHTML = onlineCameras.map(camera => `
            <div class="camera-feed-item" data-camera-id="${camera.id}">
                <div class="camera-header">
                    <span class="camera-name">${camera.name}</span>
                    <span class="camera-status ${camera.status}">${camera.status.toUpperCase()}</span>
                </div>
                <div class="camera-preview-container">
                    <img class="camera-preview" style="display: none;" alt="${camera.name}">
                    <div class="camera-placeholder">
                        <i class="fas fa-video"></i>
                        <span>Connecting...</span>
                    </div>
                </div>
                <div class="camera-info">
                    <span class="camera-location">${camera.location}</span>
                    <span class="frame-timestamp">--:--:--</span>
                </div>
            </div>
        `).join('');
        
        if (onlineCameras.length === 0) {
            cameraGrid.innerHTML = '<div class="no-cameras">No cameras available</div>';
        }
    }

    updateDashboardRecentDetections() {
        const recentDetectionsList = document.getElementById('recent-detections-list');
        if (!recentDetectionsList) return;
        
        const recentDetections = AppState.detections.slice(0, 10);
        
        recentDetectionsList.innerHTML = recentDetections.map(detection => `
            <div class="detection-item" data-detection-id="${detection.id}">
                <div class="detection-plate">${detection.plate_text}</div>
                <div class="detection-info">
                    <div class="detection-camera">${detection.camera_name}</div>
                    <div class="detection-time">${this.formatTimeAgo(detection.timestamp)}</div>
                </div>
                <div class="detection-confidence ${this.getConfidenceClass(detection.confidence)}">
                    ${detection.confidence}%
                </div>
            </div>
        `).join('');
    }

    updateDashboardSystemHealth() {
        const healthMetrics = document.getElementById('health-metrics');
        if (!healthMetrics) return;
        
        const health = AppState.systemHealth;
        
        healthMetrics.innerHTML = `
            <div class="health-metric">
                <div class="metric-label">CPU Usage</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${health.cpu}%; background-color: ${this.getHealthColor(health.cpu)}"></div>
                </div>
                <div class="metric-value">${health.cpu}%</div>
            </div>
            <div class="health-metric">
                <div class="metric-label">Memory Usage</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${health.memory}%; background-color: ${this.getHealthColor(health.memory)}"></div>
                </div>
                <div class="metric-value">${health.memory}%</div>
            </div>
            <div class="health-metric">
                <div class="metric-label">Storage Usage</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${health.storage}%; background-color: ${this.getHealthColor(health.storage)}"></div>
                </div>
                <div class="metric-value">${health.storage}%</div>
            </div>
            <div class="health-metric">
                <div class="metric-label">Network Usage</div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: ${health.network}%; background-color: ${this.getHealthColor(health.network)}"></div>
                </div>
                <div class="metric-value">${health.network}%</div>
            </div>
        `;
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

        // Update the cameras grid with filtered results - DISABLED: Now handled by camera_modal.js
        // this.loadCamerasContent(filteredCameras);
        
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
        
        // Reload all cameras - DISABLED: Now handled by camera_modal.js
        // this.loadCamerasContent();
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

// WebSocket Integration for Real-time Updates
class WebSocketManager {
    constructor(controller) {
        this.controller = controller;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000; // 3 seconds
        this.connected = false;
        this.subscriptions = new Set();
    }

    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/ws/ws/dashboard`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected successfully');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.controller.updateConnectionStatus(true);
                
                // Subscribe to real-time updates
                this.subscribeToUpdates();
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket connection closed:', event.code, event.reason);
                this.connected = false;
                this.controller.updateConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.connected = false;
                this.controller.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Error connecting to WebSocket:', error);
            this.attemptReconnect();
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
        this.controller.updateConnectionStatus(false);
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.controller.showToast('Connection lost. Please refresh the page.', 'error');
        }
    }

    subscribeToUpdates() {
        if (!this.connected) return;

        // Subscribe to camera frames for live feeds
        this.sendMessage({
            type: 'subscribe',
            subscription: 'camera_frames',
            camera_ids: [] // Subscribe to all cameras
        });

        // Subscribe to detection results
        this.sendMessage({
            type: 'subscribe',
            subscription: 'detection_results',
            camera_ids: [] // Subscribe to all cameras
        });

        // Subscribe to system stats
        this.sendMessage({
            type: 'subscribe',
            subscription: 'system_stats',
            camera_ids: []
        });

        // Subscribe to camera status updates
        this.sendMessage({
            type: 'subscribe',
            subscription: 'camera_status',
            camera_ids: []
        });
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, message not sent:', message);
        }
    }

    handleMessage(data) {
        console.log('Received WebSocket message:', data);
        
        switch (data.type) {
            case 'camera_list':
                this.controller.updateCameraList(data.data.cameras || []);
                break;
                
            case 'camera_frame':
                this.controller.updateCameraFrame(data.camera_id, data.data);
                break;
                
            case 'detection_result':
                this.controller.addDetectionResult(data.data);
                break;
                
            case 'camera_status':
                this.controller.updateCameraStatus(data.camera_id, data.data);
                break;
                
            case 'system_stats':
                this.controller.updateSystemStats(data.data);
                break;
                
            case 'subscribe':
                console.log('Subscription confirmed:', data.data);
                break;
                
            case 'error':
                console.error('WebSocket error:', data.data.error);
                this.controller.showToast(data.data.error, 'error');
                break;
                
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    ping() {
        if (this.connected) {
            this.sendMessage({ type: 'ping' });
        }
    }
}

// Simplified Camera Management
// Simplified Camera Management
class CameraManager {
    constructor() {
        console.log('CameraManager initialized');
        this.cameras = [];
        this.editingCameraId = null; // Track camera being edited
        this.isSubmitting = false; // Prevent double submissions
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Connect to existing Add Camera functionality from HTML
        this.setupAddCameraModal();
        this.setupCameraGrid();
    }
    
    setupAddCameraModal() {
        console.log('Setting up Add Camera modal functionality');
        
        // Setup Add Camera button and modal functionality
        const addCameraBtn = document.getElementById('add-camera-btn');
        const addCameraQuickBtn = document.getElementById('add-camera-quick');
        const addCameraModal = document.getElementById('add-camera-modal');
        const closeAddCameraModal = document.getElementById('close-add-camera-modal');
        const addCameraForm = document.getElementById('add-camera-form');
        const testConnectionBtn = document.getElementById('test-camera-connection');
        
        // Modal open function - Updated to use Camera Wizard
        const openModal = () => {
            console.log('Opening Camera Wizard');
            if (window.cameraWizard) {
                window.cameraWizard.show();
            } else {
                console.error('Camera Wizard not initialized!');
                // Fallback to old modal if wizard is not available
                if (addCameraModal) {
                    addCameraModal.style.display = 'flex';
                    addCameraModal.style.visibility = 'visible';
                    addCameraModal.style.opacity = '1';
                    addCameraModal.classList.add('active');
                    this.resetAddCameraForm();
                }
            }
        };
        
        // Modal close function
        const closeModal = () => {
            console.log('Closing Add Camera modal');
            if (addCameraModal) {
                addCameraModal.style.display = 'none';
                addCameraModal.style.visibility = 'hidden';
                addCameraModal.style.opacity = '0';
                addCameraModal.classList.remove('active');
            }
        };
        
        // Setup event listeners with proper duplicate prevention
        if (addCameraBtn) {
            if (!addCameraBtn.hasAttribute('data-initialized')) {
                console.log('Setting up add-camera-btn event listener');
                addCameraBtn.addEventListener('click', openModal);
                addCameraBtn.setAttribute('data-initialized', 'true');
            }
        } else {
            console.warn('add-camera-btn not found');
        }
        
        if (addCameraQuickBtn) {
            if (!addCameraQuickBtn.hasAttribute('data-initialized')) {
                console.log('Setting up add-camera-quick event listener');
                addCameraQuickBtn.addEventListener('click', openModal);
                addCameraQuickBtn.setAttribute('data-initialized', 'true');
            }
        } else {
            console.warn('add-camera-quick not found');
        }
        
        // Modal close button
        if (closeAddCameraModal) {
            if (!closeAddCameraModal.hasAttribute('data-initialized')) {
                closeAddCameraModal.addEventListener('click', closeModal);
                closeAddCameraModal.setAttribute('data-initialized', 'true');
            }
        } else {
            console.warn('close-add-camera-modal not found');
        }
        
        // Close on backdrop click (replace modal to remove old listeners)
        if (addCameraModal) {
            // Don't replace the entire modal, just update the backdrop listener
            addCameraModal.onclick = (e) => {
                if (e.target === addCameraModal) {
                    closeModal();
                }
            };
        }
        
        // Connection type handling
        const connectionTypeSelect = document.getElementById('connection-type');
        if (connectionTypeSelect) {
            connectionTypeSelect.addEventListener('change', (e) => {
                this.updateConnectionFields(e.target.value);
            });
            // Initialize with default
            this.updateConnectionFields(connectionTypeSelect.value);
        }
        
        // Form submission
        if (addCameraForm) {
            if (!addCameraForm.hasAttribute('data-initialized')) {
                addCameraForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleAddCameraSubmit();
                });
                addCameraForm.setAttribute('data-initialized', 'true');
            }
        }
        
        // Test connection
        if (testConnectionBtn) {
            if (!testConnectionBtn.hasAttribute('data-initialized')) {
                testConnectionBtn.addEventListener('click', () => {
                    this.testCameraConnection();
                });
                testConnectionBtn.setAttribute('data-initialized', 'true');
            }
        }
        
        // Cancel button
        const cancelBtn = document.getElementById('cancel-add-camera');
        if (cancelBtn) {
            if (!cancelBtn.hasAttribute('data-initialized')) {
                cancelBtn.addEventListener('click', () => {
                    if (addCameraModal) {
                        addCameraModal.style.display = 'none';
                        addCameraModal.classList.remove('active');
                    }
                });
                cancelBtn.setAttribute('data-initialized', 'true');
            }
        }
        
        // Resolution change handler
        const resolutionSelect = document.getElementById('camera-resolution');
        if (resolutionSelect) {
            resolutionSelect.addEventListener('change', (e) => {
                this.updateResolutionFields(e.target.value);
            });
        }
        
        // Connection type change handler already set up above
    }
    
    resetAddCameraForm() {
        // Use the shared resetForm method
        this.resetForm();
    }
    
    async handleAddCameraSubmit() {
        // Prevent double submission
        if (this.isSubmitting) {
            console.log('Form submission already in progress, ignoring');
            return;
        }
        
        this.isSubmitting = true;
        
        const status = document.getElementById('add-camera-status');
        if (status) {
            status.textContent = 'Submitting...';
            status.className = 'form-status info';
        }
        
        try {
            // Debug: Log current state
            console.log('Form submission started');
            console.log('Editing camera ID:', this.editingCameraId);
            console.log('Current IP address:', document.getElementById('camera-ip').value);
            
            // Route to appropriate method based on mode
            if (this.editingCameraId) {
                await this.updateCamera();
            } else {
                await this.createCamera();
            }
        } finally {
            this.isSubmitting = false;
        }
        
        // Get or create location
        const locationName = document.getElementById('camera-location').value;
        let locationId;
        
        try {
            locationId = await this.getOrCreateLocation(locationName);
        } catch (error) {
            if (status) {
                status.textContent = 'Error: ' + error.message;
                status.className = 'form-status error';
            }
            this.showToast('Failed to create location: ' + error.message, 'error');
            return;
        }
        
        const data = {
            name: document.getElementById('camera-name').value,
            ip_address: document.getElementById('camera-ip').value,
            location_id: locationId,
            port: parseInt(document.getElementById('camera-port').value) || 554,
            username: document.getElementById('camera-username').value || 'admin',
            password: document.getElementById('camera-password').value || '',
            manufacturer: document.getElementById('camera-manufacturer').value || null,
            model: document.getElementById('camera-model').value || null,
            resolution_width: width,
            resolution_height: height,
            fps: parseInt(document.getElementById('camera-fps').value) || 30,
            stream_path: document.getElementById('stream-path').value || '/live.sdp',
            camera_type: 'ip_camera'
        };
        
        try {
            const response = await fetch('/api/cameras/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                const result = await response.json();
                if (status) {
                    status.textContent = 'Camera added successfully!';
                    status.className = 'form-status success';
                }
                this.showToast('Camera added successfully!', 'success');
                
                // Refresh camera grid
                this.loadCameras();
                
                // Close modal after delay
                setTimeout(() => {
                    const modal = document.getElementById('add-camera-modal');
                    if (modal) {
                        modal.style.display = 'none';
                        modal.classList.remove('active');
                    }
                }, 1500);
            } else {
                let errorMsg = 'Failed to add camera';
                try {
                    const error = await response.json();
                    if (error.detail) {
                        if (typeof error.detail === 'string') {
                            errorMsg = error.detail;
                            // Handle specific constraint errors
                            if (errorMsg.includes('UNIQUE constraint failed: cameras.ip_address')) {
                                errorMsg = 'A camera with this IP address already exists. Please use a different IP address or update the existing camera.';
                            }
                        } else if (Array.isArray(error.detail)) {
                            errorMsg = error.detail.map(e => e.msg || e.message || e).join(', ');
                        } else {
                            errorMsg = JSON.stringify(error.detail);
                        }
                    }
                } catch (e) {
                    errorMsg = `HTTP ${response.status}: ${response.statusText}`;
                }
                if (status) {
                    status.textContent = 'Error: ' + errorMsg;
                    status.className = 'form-status error';
                }
                this.showToast(errorMsg, 'error');
            }
        } catch (err) {
            const errorMsg = 'Network error: ' + err.message;
            if (status) {
                status.textContent = errorMsg;
                status.className = 'form-status error';
            }
            this.showToast('Network error occurred', 'error');
        }
    }
    
    async createCamera() {
        const status = document.getElementById('add-camera-status');
        
        try {
            const cameraData = await this.collectFormData();
            
            const response = await fetch('/api/cameras/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(cameraData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.handleSubmissionSuccess('Camera added successfully!', status);
            } else {
                await this.handleSubmissionError(response, status);
            }
        } catch (error) {
            this.handleNetworkError(error, status);
        }
    }
    
    async collectFormData() {
        const resolution = document.getElementById('camera-resolution').value;
        let width = 1920, height = 1080;
        
        if (resolution === 'custom') {
            width = parseInt(document.getElementById('resolution-width').value) || 1920;
            height = parseInt(document.getElementById('resolution-height').value) || 1080;
        } else if (resolution && resolution !== 'custom') {
            [width, height] = resolution.split('x').map(Number);
        }
        
        // Get or create location
        const locationName = document.getElementById('camera-location').value;
        const locationId = await this.getOrCreateLocation(locationName);
        
        return {
            name: document.getElementById('camera-name').value,
            ip_address: document.getElementById('camera-ip').value,
            location_id: locationId,
            port: parseInt(document.getElementById('camera-port').value) || 554,
            username: document.getElementById('camera-username').value || 'admin',
            password: document.getElementById('camera-password').value || '',
            manufacturer: document.getElementById('camera-manufacturer').value || null,
            model: document.getElementById('camera-model').value || null,
            resolution_width: width,
            resolution_height: height,
            fps: parseInt(document.getElementById('camera-fps').value) || 30,
            stream_path: document.getElementById('stream-path').value || '/live.sdp',
            camera_type: 'ip_camera'
        };
    }
    
    async handleSubmissionError(response, status) {
        if (response.status === 409) {
            const conflictData = await response.json();
            this.handleConflictResolution(conflictData, status);
        } else {
            let errorMsg = 'Failed to process camera';
            try {
                const error = await response.json();
                if (error.detail) {
                    errorMsg = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
                }
            } catch (parseError) {
                errorMsg = `HTTP ${response.status}: ${response.statusText}`;
            }
            
            if (status) {
                status.textContent = 'Error: ' + errorMsg;
                status.className = 'form-status error';
            }
            this.showToast(errorMsg, 'error');
        }
    }
    
    async handleConflictResolution(conflictData, status) {
        const existingCamera = conflictData.detail.existing_camera;
        const confirmMessage = `A camera with IP address ${existingCamera.ip_address} already exists:\n\n` +
                              `Name: ${existingCamera.name}\n` +
                              `ID: ${existingCamera.id}\n\n` +
                              `Would you like to update the existing camera instead?`;
        
        if (confirm(confirmMessage)) {
            this.editingCameraId = existingCamera.id;
            
            try {
                const response = await fetch(`/api/cameras/${existingCamera.id}`);
                if (response.ok) {
                    const camera = await response.json();
                    this.populateAddCameraForm(camera);
                    
                    if (status) {
                        status.textContent = 'Switched to edit mode for existing camera';
                        status.className = 'form-status info';
                    }
                } else {
                    throw new Error('Failed to load existing camera data');
                }
            } catch (error) {
                if (status) {
                    status.textContent = 'Error loading existing camera: ' + error.message;
                    status.className = 'form-status error';
                }
            }
        } else {
            if (status) {
                status.textContent = 'Camera with this IP address already exists';
                status.className = 'form-status error';
            }
        }
    }
    
    handleSubmissionSuccess(message, status) {
        if (status) {
            status.textContent = message;
            status.className = 'form-status success';
        }
        this.showToast(message, 'success');
        
        this.loadCameras();
        
        setTimeout(() => {
            const modal = document.getElementById('add-camera-modal');
            if (modal) {
                modal.style.display = 'none';
                modal.classList.remove('active');
            }
            this.resetForm();
        }, 1500);
    }
    
    handleNetworkError(error, status) {
        const errorMsg = 'Network error: ' + error.message;
        if (status) {
            status.textContent = errorMsg;
            status.className = 'form-status error';
        }
        this.showToast('Network error occurred', 'error');
    }
    
    async testCameraConnection() {
        const status = document.getElementById('add-camera-status');
        const testResultsSection = document.getElementById('test-results-section');
        const testResultsContent = document.getElementById('test-results-content');
        const testButton = document.getElementById('test-camera-connection');
        const addButton = document.getElementById('add-camera-submit-btn');
        
        // Update button state
        if (testButton) {
            testButton.disabled = true;
            testButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        }
        
        // Hide previous results
        if (testResultsSection) testResultsSection.style.display = 'none';
        if (addButton) addButton.style.display = 'none';
        
        // Show testing status
        if (status) {
            status.textContent = 'Testing connection...';
            status.className = 'form-status info';
        }
        
        // Collect form data
        const resolution = document.getElementById('camera-resolution').value;
        let width = 1920, height = 1080;
        
        if (resolution === 'custom') {
            width = parseInt(document.getElementById('resolution-width').value) || 1920;
            height = parseInt(document.getElementById('resolution-height').value) || 1080;
        } else if (resolution && resolution !== 'custom') {
            [width, height] = resolution.split('x').map(Number);
        }
        
        const data = {
            ip_address: document.getElementById('camera-ip').value,
            port: document.getElementById('camera-port').value || '554',
            connection_type: document.getElementById('connection-type').value,
            stream_path: document.getElementById('stream-path').value,
            username: document.getElementById('camera-username').value,
            password: document.getElementById('camera-password').value,
            auth_method: document.getElementById('auth-method').value,
            resolution_width: width,
            resolution_height: height,
            fps: parseInt(document.getElementById('camera-fps').value) || 30
        };
        
        try {
            const response = await fetch('/api/cameras/test-connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayTestResults(result);
                
                if (result.success) {
                    if (status) {
                        status.textContent = 'Connection test successful!';
                        status.className = 'form-status success';
                    }
                    if (addButton) addButton.style.display = 'inline-block';
                    this.showToast('Camera connection successful!', 'success');
                } else {
                    if (status) {
                        status.textContent = 'Connection test failed: ' + (result.error || 'Unknown error');
                        status.className = 'form-status error';
                    }
                    this.showToast('Connection test failed', 'error');
                }
            } else {
                const errorData = await response.json();
                const errorMsg = errorData.detail || 'Connection test failed';
                if (status) {
                    status.textContent = 'Error: ' + errorMsg;
                    status.className = 'form-status error';
                }
                this.showToast(errorMsg, 'error');
            }
        } catch (err) {
            const errorMsg = 'Network error: ' + err.message;
            if (status) {
                status.textContent = errorMsg;
                status.className = 'form-status error';
            }
            this.showToast('Network error occurred', 'error');
        } finally {
            // Reset button state
            if (testButton) {
                testButton.disabled = false;
                testButton.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
            }
        }
    }
    
    displayTestResults(result) {
        const testResultsSection = document.getElementById('test-results-section');
        const testResultsContent = document.getElementById('test-results-content');
        
        if (!testResultsSection || !testResultsContent) return;
        
        let resultsHTML = '<div class="test-results">';
        
        if (result.success) {
            resultsHTML += `
                <div class="test-result-item">
                    <div class="test-result-icon success">
                        <i class="fas fa-check"></i>
                    </div>
                    <span class="test-result-label">Connection Status</span>
                    <span class="test-result-value">Test Successful</span>
                </div>
            `;
            
            if (result.stream_url) {
                resultsHTML += `
                    <div class="test-result-item">
                        <div class="test-result-icon success">
                            <i class="fas fa-video"></i>
                        </div>
                        <span class="test-result-label">Stream URL</span>
                        <span class="test-result-value">${result.stream_url}</span>
                    </div>
                `;
            }
            
            if (result.manufacturer) {
                resultsHTML += `
                    <div class="test-result-item">
                        <div class="test-result-icon success">
                            <i class="fas fa-industry"></i>
                        </div>
                        <span class="test-result-label">Manufacturer</span>
                        <span class="test-result-value">${result.manufacturer}</span>
                    </div>
                `;
            }
            
            if (result.model) {
                resultsHTML += `
                    <div class="test-result-item">
                        <div class="test-result-icon success">
                            <i class="fas fa-camera"></i>
                        </div>
                        <span class="test-result-label">Model</span>
                        <span class="test-result-value">${result.model}</span>
                    </div>
                `;
            }
            
            if (result.resolution) {
                resultsHTML += `
                    <div class="test-result-item">
                        <div class="test-result-icon success">
                            <i class="fas fa-expand-arrows-alt"></i>
                        </div>
                        <span class="test-result-label">Resolution</span>
                        <span class="test-result-value">${result.resolution}</span>
                    </div>
                `;
            }
            
            if (result.fps) {
                resultsHTML += `
                    <div class="test-result-item">
                        <div class="test-result-icon success">
                            <i class="fas fa-tachometer-alt"></i>
                        </div>
                        <span class="test-result-label">Frame Rate</span>
                        <span class="test-result-value">${result.fps} FPS</span>
                    </div>
                `;
            }
            
            if (result.response_time) {
                resultsHTML += `
                    <div class="test-result-item">
                        <div class="test-result-icon success">
                            <i class="fas fa-clock"></i>
                        </div>
                        <span class="test-result-label">Response Time</span>
                        <span class="test-result-value">${result.response_time}ms</span>
                    </div>
                `;
            }
            
            if (result.snapshot_url) {
                resultsHTML += `
                    <div class="camera-preview">
                        <img src="${result.snapshot_url}" alt="Camera Preview" onerror="this.style.display='none'">
                    </div>
                `;
            }
        } else {
            resultsHTML += `
                <div class="test-result-item">
                    <div class="test-result-icon error">
                        <i class="fas fa-times"></i>
                    </div>
                    <span class="test-result-label">Connection Status</span>
                    <span class="test-result-value">Failed</span>
                </div>
            `;
            
            if (result.error) {
                resultsHTML += `
                    <div class="test-result-item">
                        <div class="test-result-icon error">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <span class="test-result-label">Error</span>
                        <span class="test-result-value">${result.error}</span>
                    </div>
                `;
            }
            
            // Add retry button for failed connections
            resultsHTML += `
                <div class="test-result-actions">
                    <button type="button" class="btn btn-outline-primary btn-small" id="retry-connection-btn">
                        <i class="fas fa-redo"></i> Retry Connection
                    </button>
                </div>
            `;
        }
        
        resultsHTML += '</div>';
        
        testResultsContent.innerHTML = resultsHTML;
        testResultsSection.style.display = 'block';
        
        // Add event listener for retry button
        const retryBtn = document.getElementById('retry-connection-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                this.testCameraConnection();
            });
        }
    }
    
    updateResolutionFields(resolution) {
        const customResolutionGroup = document.getElementById('custom-resolution-group');
        const widthField = document.getElementById('resolution-width');
        const heightField = document.getElementById('resolution-height');
        
        if (resolution === 'custom') {
            if (customResolutionGroup) customResolutionGroup.style.display = 'block';
        } else {
            if (customResolutionGroup) customResolutionGroup.style.display = 'none';
            
            // Set default values based on selected resolution
            if (resolution && resolution !== 'custom') {
                const [width, height] = resolution.split('x');
                if (widthField) widthField.value = width;
                if (heightField) heightField.value = height;
            }
        }
    }
    
    // Removed checkCameraByIP - IP conflicts are now handled by the backend with 409 status codes
    
    async getOrCreateLocation(locationName) {
        if (!locationName || locationName.trim() === '') {
            throw new Error('Location name is required');
        }
        
        try {
            // First, get all locations to check for exact match
            const allLocationsResponse = await fetch('/api/locations/', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (allLocationsResponse.ok) {
                const allLocations = await allLocationsResponse.json();
                const existingLocation = allLocations.find(loc => 
                    loc.name.toLowerCase() === locationName.trim().toLowerCase()
                );
                
                if (existingLocation) {
                    console.log(`Found existing location: ${existingLocation.name} (ID: ${existingLocation.id})`);
                    return existingLocation.id;
                }
            }
            
            // Location not found, create new one
            const createResponse = await fetch('/api/locations/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: locationName.trim(),
                    description: `Auto-created location for ${locationName.trim()}`,
                    country: 'USA',
                    timezone: 'UTC'
                })
            });
            
            if (createResponse.ok) {
                const result = await createResponse.json();
                console.log(`Created new location: ${locationName.trim()} (ID: ${result.location_id})`);
                return result.location_id;
            } else {
                const error = await createResponse.json();
                // If creation fails due to existing location, try to find it again
                if (error.detail && error.detail.includes('already exists')) {
                    console.log('Location creation failed due to existing location, searching again...');
                    const retryResponse = await fetch('/api/locations/', {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (retryResponse.ok) {
                        const retryLocations = await retryResponse.json();
                        const foundLocation = retryLocations.find(loc => 
                            loc.name.toLowerCase() === locationName.trim().toLowerCase()
                        );
                        
                        if (foundLocation) {
                            console.log(`Found existing location on retry: ${foundLocation.name} (ID: ${foundLocation.id})`);
                            return foundLocation.id;
                        }
                    }
                }
                
                throw new Error(error.detail || 'Failed to create location');
            }
            
        } catch (error) {
            throw new Error(`Failed to get or create location: ${error.message}`);
        }
    }
    
    updateConnectionFields(connectionType) {
        const portField = document.getElementById('camera-port');
        const portGroup = portField.closest('.form-group');
        const streamPathGroup = document.getElementById('stream-path-group');
        const streamPathField = document.getElementById('stream-path');
        
        // Set default ports and show/hide fields based on connection type
        switch (connectionType) {
            case 'rtsp':
                if (portField) portField.value = '554';
                if (portGroup) portGroup.style.display = 'block';
                if (streamPathGroup) streamPathGroup.style.display = 'block';
                if (streamPathField) streamPathField.placeholder = '/live.sdp';
                break;
            case 'http':
                if (portField) portField.value = '80';
                if (portGroup) portGroup.style.display = 'block';
                if (streamPathGroup) streamPathGroup.style.display = 'block';
                if (streamPathField) streamPathField.placeholder = '/cgi-bin/mjpg/video.cgi';
                break;
            case 'https':
                if (portField) portField.value = '443';
                if (portGroup) portGroup.style.display = 'block';
                if (streamPathGroup) streamPathGroup.style.display = 'block';
                if (streamPathField) streamPathField.placeholder = '/cgi-bin/mjpg/video.cgi';
                break;
            case 'onvif':
                if (portField) portField.value = '80';
                if (portGroup) portGroup.style.display = 'block';
                if (streamPathGroup) streamPathGroup.style.display = 'none';
                break;
            default:
                if (portField) portField.value = '554';
                if (portGroup) portGroup.style.display = 'block';
                if (streamPathGroup) streamPathGroup.style.display = 'block';
                if (streamPathField) streamPathField.placeholder = '/mjpeg';
                break;
        }
    }
    
    setupCameraGrid() {
        // Load and display cameras
        this.loadCameras();
    }
    
    async loadCameras() {
        try {
            const response = await fetch('/api/cameras/?include_inactive=true');
            if (response.ok) {
                this.cameras = await response.json();
                this.renderCameraGrid();
            }
        } catch (error) {
            console.error('Failed to load cameras:', error);
            this.renderCameraGrid(); // Render with empty array
        }
    }
    
    renderCameraGrid() {
        const grid = document.getElementById('cameras-grid');
        if (!grid) return;
        
        if (this.cameras.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-video"></i>
                    </div>
                    <h3>No cameras configured</h3>
                    <p>Add cameras to start monitoring</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = this.cameras.map(camera => this.createCameraCard(camera)).join('');
    }
    
    createCameraCard(camera) {
        const statusClass = camera.status ? camera.status.toLowerCase() : 'offline';
        const resolution = camera.resolution || `${camera.resolution_width || 1920}x${camera.resolution_height || 1080}`;
        
        return `
            <div class="camera-card" data-camera-id="${camera.id}">
                <div class="camera-card-header">
                    <div class="camera-card-title">${camera.name}</div>
                    <div class="camera-card-status ${statusClass}">${statusClass.toUpperCase()}</div>
                </div>
                <div class="camera-card-body">
                    <div class="camera-card-preview">
                        <i class="fas fa-video"></i>
                    </div>
                    <div class="camera-card-info">
                        <div><strong>Location:</strong> ${camera.location || 'No location'}</div>
                        <div><strong>IP:</strong> ${camera.ip_address}</div>
                        <div><strong>Resolution:</strong> ${resolution}</div>
                        <div><strong>FPS:</strong> ${camera.fps}</div>
                        <div><strong>Detections:</strong> ${camera.detections_today || 0}</div>
                        <div><strong>Health:</strong> ${camera.health_score || 0}%</div>
                    </div>
                </div>
                <div class="camera-card-actions">
                    <button class="btn btn-small btn-primary" onclick="cameraManager.editCamera('${camera.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="cameraManager.viewLive('${camera.id}')">
                        <i class="fas fa-play"></i> Live
                    </button>
                    <button class="btn btn-small btn-danger" onclick="cameraManager.deleteCamera('${camera.id}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `;
    }
    
    // Camera management methods
    async editCamera(cameraId) {
        try {
            const response = await fetch(`/api/cameras/${cameraId}`);
            if (response.ok) {
                const camera = await response.json();
                this.editingCameraId = cameraId; // Set editing mode
                
                // Initialize the IP camera wizard with edit data if it exists
                if (window.ipCameraWizard) {
                    window.ipCameraWizard.populateForEdit(camera);
                    window.ipCameraWizard.showModal();
                } else {
                    // Fallback to old form
                    this.populateAddCameraForm(camera);
                    const modal = document.getElementById('add-camera-modal');
                    if (modal) {
                        modal.style.display = 'flex';
                    }
                }
            } else {
                this.showToast('Failed to load camera details', 'error');
            }
        } catch (error) {
            console.error('Failed to load camera details:', error);
            this.showToast('Failed to load camera details', 'error');
        }
    }
    
    populateAddCameraForm(camera) {
        console.log('Populating form with camera data:', camera);
        
        // Basic info
        document.getElementById('camera-name').value = camera.name || '';
        document.getElementById('camera-location').value = camera.location || '';
        document.getElementById('camera-ip').value = camera.ip_address || '';
        document.getElementById('camera-port').value = camera.port || '554';
        document.getElementById('camera-username').value = camera.username || '';
        document.getElementById('camera-password').value = camera.password || '';
        
        // Additional fields
        document.getElementById('camera-manufacturer').value = camera.manufacturer || '';
        document.getElementById('camera-model').value = camera.model || '';
        document.getElementById('camera-fps').value = camera.fps || '30';
        document.getElementById('codec').value = camera.codec || 'H.264';
        document.getElementById('stream-path').value = camera.stream_path || '/live.sdp';
        
        // Set resolution
        const resolutionSelect = document.getElementById('camera-resolution');
        const resolution = `${camera.resolution_width || 1920}x${camera.resolution_height || 1080}`;
        if (resolutionSelect) {
            resolutionSelect.value = resolution;
            this.updateResolutionFields(resolution);
        }
        
        // Update modal title to indicate editing
        const modalTitle = document.querySelector('#add-camera-modal .modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Camera';
        }
        
        // Update button text
        const submitBtn = document.getElementById('add-camera-submit-btn');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Camera';
        }
        
        console.log('Form populated with camera data');
    }
    
    async updateCamera() {
        const status = document.getElementById('add-camera-status');
        if (status) {
            status.textContent = 'Updating camera...';
            status.className = 'form-status info';
        }
        
        try {
            const cameraData = await this.collectFormData();
            
            const response = await fetch(`/api/cameras/${this.editingCameraId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cameraData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.handleSubmissionSuccess('Camera updated successfully!', status);
            } else {
                await this.handleSubmissionError(response, status);
            }
        } catch (error) {
            this.handleNetworkError(error, status);
        }
    }
    
    async deleteCamera(cameraId) {
        if (!confirm('Are you sure you want to delete this camera?')) return;
        
        try {
            const response = await fetch(`/api/cameras/${cameraId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.loadCameras(); // Refresh the grid
                this.showToast('Camera deleted successfully', 'success');
            } else {
                this.showToast('Failed to delete camera', 'error');
            }
        } catch (error) {
            console.error('Delete failed:', error);
            this.showToast('Network error occurred', 'error');
        }
    }
    
    viewLive(cameraId) {
        console.log('Viewing live stream for camera:', cameraId);
        // Show live stream in modal instead of new tab
        this.showLiveStreamModal(cameraId);
    }
    
    showLiveStreamModal(cameraId) {
        // Create modal HTML
        const modalHTML = `
            <div id="live-stream-modal" class="modal-overlay" style="display: flex;">
                <div class="modal-container" style="max-width: 800px; width: 90vw;">
                    <div class="modal-header">
                        <h2>Live Stream - Camera ${cameraId}</h2>
                        <button class="modal-close" onclick="closeLiveStreamModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="stream-container">
                            <img id="live-stream-image" 
                                 src="/api/cameras/${cameraId}/live" 
                                 alt="Live Camera Stream"
                                 style="width: 100%; height: auto; background: #000;">
                        </div>
                        <div class="stream-controls" style="margin-top: 15px; text-align: center;">
                            <button class="btn btn-secondary" onclick="refreshLiveStream('${cameraId}')">
                                <i class="fas fa-refresh"></i> Refresh
                            </button>
                            <button class="btn btn-primary" onclick="captureSnapshot('${cameraId}')">
                                <i class="fas fa-camera"></i> Capture
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('live-stream-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add global functions for modal controls
        window.closeLiveStreamModal = function() {
            const modal = document.getElementById('live-stream-modal');
            if (modal) {
                modal.remove();
            }
        };
        
        window.refreshLiveStream = function(cameraId) {
            const img = document.getElementById('live-stream-image');
            if (img) {
                img.src = `/api/cameras/${cameraId}/live?t=${Date.now()}`;
            }
        };
        
        window.captureSnapshot = function(cameraId) {
            // Download snapshot
            const link = document.createElement('a');
            link.href = `/api/cameras/${cameraId}/snapshot`;
            link.download = `camera_${cameraId}_snapshot_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.jpg`;
            link.click();
        };
    }
    
    resetForm() {
        // Reset editing state
        this.editingCameraId = null;
        
        // Reset form fields
        const form = document.getElementById('add-camera-form');
        if (form) form.reset();
        
        // Reset visibility and status
        const testResultsSection = document.getElementById('test-results-section');
        const addButton = document.getElementById('add-camera-submit-btn');
        const status = document.getElementById('add-camera-status');
        const modalTitle = document.querySelector('#add-camera-modal .modal-title');
        
        // Reset visibility
        if (status) {
            status.textContent = '';
            status.className = 'form-status';
        }
        if (modalTitle) modalTitle.textContent = 'Add New IP Camera';
        if (testResultsSection) testResultsSection.style.display = 'none';
        if (addButton) addButton.style.display = 'none';
        
        // Reset button text
        if (addButton) {
            addButton.innerHTML = '<i class="fas fa-save"></i> Save Camera';
        }
        
        // Reset form state
        this.updateConnectionFields('IP');
        
        // Reset resolution fields
        const resolutionSelect = document.getElementById('camera-resolution');
        if (resolutionSelect) {
            this.updateResolutionFields(resolutionSelect.value);
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
            <span>${message}</span>
        `;
        
        const container = document.getElementById('toast-container') || document.body;
        container.appendChild(toast);
        
        setTimeout(() => toast.remove(), 3000);
    }
    
    openAddCameraModal() {
        // Use the new wizard system instead of old modal
        if (window.showAddCameraModal) {
            window.showAddCameraModal();
        } else {
            // Fallback to direct modal show
            const modal = document.getElementById('add-camera-modal');
            if (modal) {
                modal.style.display = 'flex';
                modal.style.visibility = 'visible';
                modal.style.opacity = '1';
                modal.classList.add('active');
            }
        }
    }
    
    async discoverCameras() {
        try {
            this.showToast('Discovering cameras on network...', 'info');
            const response = await fetch('/api/cameras/discover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip_range: "192.168.1.0/24"
                })
            });
            
            if (response.ok) {
                const discoveredCameras = await response.json();
                this.showToast(`Found ${discoveredCameras.length} cameras`, 'success');
                
                // You can extend this to show a discovery modal
                console.log('Discovered cameras:', discoveredCameras);
            } else {
                this.showToast('Camera discovery failed', 'error');
            }
        } catch (error) {
            console.error('Discovery failed:', error);
            this.showToast('Network error during discovery', 'error');
        }
    }
}
// Initialize Application
let app;
let wsManager;
let cameraManager;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing application');
    app = new LPRSystemController();
    wsManager = new WebSocketManager(app);
    // cameraManager = new CameraManager(); // DISABLED: Conflicts with camera_modal.js
    console.log('Core managers initialized');
    
    // Make app globally available for inline event handlers
    window.app = app;
    window.wsManager = wsManager;
    window.cameraManager = cameraManager;
    
    // Connect to WebSocket
    wsManager.connect();
    
    // Set up periodic ping
    setInterval(() => {
        if (wsManager) {
            wsManager.ping();
        }
    }, 30000); // Ping every 30 seconds
    
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

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (wsManager) {
        wsManager.disconnect();
    }
});

