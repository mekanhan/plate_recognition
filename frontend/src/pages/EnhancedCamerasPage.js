/**
 * EnhancedCamerasPage.js - Professional Auto-Recording Camera Management
 * 
 * Features:
 * - Professional auto-recording monitoring (no manual start/stop buttons)
 * - Working snapshots with correct camera manager IDs
 * - Search and filter functionality
 * - Camera details (IP, location, model)
 * - Settings and kebab menu actions
 * - Real-time health monitoring
 */

import config from '../config/app.config.js';
import SimpleCameraModal from '../components/cameras/SimpleCameraModal.js';

class EnhancedCamerasPage {
    constructor() {
        this.cameras = [];
        this.filteredCameras = [];
        this.filters = { status: '', location: '', search: '' };
        this.currentView = 'grid';
        this.refreshInterval = null;
        
        // Initialize camera modal for settings
        this.simpleCameraModal = new SimpleCameraModal();
        
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
                <!-- Page Header -->
                <div class="page-header">
                    <h1 class="page-title">Camera Management</h1>
                    <p class="page-subtitle">Professional 24/7 Auto-Recording Surveillance System</p>
                    <div class="system-status">
                        <div class="status-badge auto-recording">
                            <i class="fas fa-circle recording-pulse"></i>
                            Auto-Recording Active
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="quick-actions">
                    <button class="quick-action-btn" id="add-camera-btn">
                        <i class="fas fa-plus"></i>
                        <span>Add Camera</span>
                    </button>
                    <button class="quick-action-btn" id="discover-cameras-btn">
                        <i class="fas fa-search"></i>
                        <span>Discover Cameras</span>
                    </button>
                    <button class="quick-action-btn" id="refresh-cameras-btn">
                        <i class="fas fa-sync-alt"></i>
                        <span>Refresh All</span>
                    </button>
                    <div class="view-toggle">
                        <button class="view-btn active" data-view="grid">
                            <i class="fas fa-th"></i>
                        </button>
                        <button class="view-btn" data-view="list">
                            <i class="fas fa-list"></i>
                        </button>
                    </div>
                </div>

                <!-- Search and Filters -->
                <div class="camera-filters">
                    <div class="filter-group">
                        <label for="camera-status-filter">Status:</label>
                        <select id="camera-status-filter" class="filter-select">
                            <option value="">All Status</option>
                            <option value="online">Online</option>
                            <option value="offline">Offline</option>
                            <option value="warning">Warning</option>
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
                        </select>
                    </div>
                    <div class="filter-group">
                        <label for="camera-search-filter">Search:</label>
                        <input type="text" id="camera-search-filter" class="filter-input" 
                               placeholder="Search by name or IP...">
                    </div>
                    <div class="filter-actions">
                        <button class="btn btn-primary" id="apply-camera-filters">Apply Filters</button>
                        <button class="btn btn-secondary" id="clear-camera-filters">Clear</button>
                    </div>
                </div>

                <!-- Camera Grid -->
                <div class="cameras-grid grid" id="cameras-grid">
                    <div class="loading-state">
                        <i class="fas fa-spinner fa-spin"></i>
                        Loading cameras...
                    </div>
                </div>
            </div>

            <style>
                .cameras-page {
                    padding: 20px;
                    max-width: 1400px;
                    margin: 0 auto;
                    background: linear-gradient(135deg, #0f1419 0%, #1a2332 50%, #0f1419 100%);
                    min-height: 100vh;
                    color: #e8eaed;
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
                    font-size: 2.2rem;
                }
                
                .page-subtitle {
                    color: #9ca3af;
                    margin-bottom: 15px;
                    font-size: 1.1rem;
                }
                
                .system-status {
                    display: flex;
                    justify-content: center;
                }
                
                .status-badge {
                    padding: 8px 16px;
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.9rem;
                    font-weight: 600;
                }
                
                .status-badge.auto-recording {
                    background: rgba(34, 197, 94, 0.15);
                    color: #22c55e;
                    border: 1px solid rgba(34, 197, 94, 0.3);
                }
                
                .recording-pulse {
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                
                /* Quick Actions */
                .quick-actions {
                    display: flex;
                    gap: 15px;
                    margin-bottom: 20px;
                    align-items: center;
                    flex-wrap: wrap;
                }
                
                .quick-action-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 16px;
                    background: rgba(99, 102, 241, 0.1);
                    color: #6366f1;
                    border: 1px solid rgba(99, 102, 241, 0.3);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .quick-action-btn:hover {
                    background: rgba(99, 102, 241, 0.2);
                    transform: translateY(-1px);
                }
                
                .view-toggle {
                    margin-left: auto;
                    display: flex;
                    gap: 5px;
                }
                
                .view-btn {
                    padding: 8px 12px;
                    background: rgba(55, 65, 81, 0.8);
                    border: 1px solid rgba(75, 85, 99, 0.5);
                    border-radius: 6px;
                    color: #9ca3af;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .view-btn.active,
                .view-btn:hover {
                    background: rgba(99, 102, 241, 0.2);
                    color: #6366f1;
                    border-color: rgba(99, 102, 241, 0.3);
                }
                
                /* Filters */
                .camera-filters {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: rgba(26, 35, 50, 0.6);
                    border-radius: 10px;
                    border: 1px solid rgba(55, 65, 81, 0.3);
                    flex-wrap: wrap;
                    align-items: end;
                }
                
                .filter-group {
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                }
                
                .filter-group label {
                    font-size: 0.9rem;
                    color: #9ca3af;
                    font-weight: 500;
                }
                
                .filter-select,
                .filter-input {
                    padding: 8px 12px;
                    background: rgba(15, 20, 25, 0.8);
                    border: 1px solid rgba(55, 65, 81, 0.5);
                    border-radius: 6px;
                    color: #e8eaed;
                    min-width: 120px;
                }
                
                .filter-input {
                    min-width: 200px;
                }
                
                .filter-actions {
                    display: flex;
                    gap: 10px;
                    margin-left: auto;
                }
                
                .btn {
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.9rem;
                    font-weight: 500;
                    transition: all 0.2s ease;
                }
                
                .btn.btn-primary {
                    background: #3b82f6;
                    color: white;
                    border: 1px solid #2563eb;
                }
                
                .btn.btn-secondary {
                    background: rgba(55, 65, 81, 0.8);
                    color: #e8eaed;
                    border: 1px solid rgba(75, 85, 99, 0.5);
                }
                
                .btn:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                }
                
                /* Camera Grid */
                .cameras-grid {
                    display: grid;
                    gap: 20px;
                }
                
                .cameras-grid.grid {
                    grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
                }
                
                .cameras-grid.list {
                    grid-template-columns: 1fr;
                }
                
                /* Camera Cards */
                .camera-card {
                    background: rgba(26, 35, 50, 0.9);
                    border-radius: 16px;
                    padding: 20px;
                    border: 1px solid rgba(99, 102, 241, 0.2);
                    transition: all 0.3s ease;
                    position: relative;
                }
                
                .camera-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #6366f1, #8b5cf6);
                    border-radius: 16px 16px 0 0;
                }
                
                .camera-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
                    border-color: rgba(99, 102, 241, 0.4);
                }
                
                .camera-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }
                
                .camera-info h3 {
                    margin: 0;
                    font-size: 1.3rem;
                    color: #e8eaed;
                    font-weight: 600;
                }
                
                .camera-location {
                    color: #9ca3af;
                    font-size: 0.9rem;
                    margin-top: 2px;
                }
                
                .camera-actions {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .camera-status {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.9rem;
                    font-weight: 600;
                    padding: 4px 8px;
                    border-radius: 12px;
                    border: 1px solid currentColor;
                }
                
                .camera-status.online {
                    color: #22c55e;
                    background: rgba(34, 197, 94, 0.1);
                }
                
                .camera-status.offline {
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.1);
                }
                
                .camera-status.warning {
                    color: #fbbf24;
                    background: rgba(251, 191, 36, 0.1);
                }
                
                /* Settings Button */
                .settings-btn {
                    padding: 6px;
                    background: rgba(55, 65, 81, 0.8);
                    border: 1px solid rgba(75, 85, 99, 0.5);
                    border-radius: 6px;
                    color: #9ca3af;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .settings-btn:hover {
                    background: rgba(99, 102, 241, 0.2);
                    color: #6366f1;
                    border-color: rgba(99, 102, 241, 0.3);
                }
                
                /* Kebab Menu */
                .kebab-wrapper {
                    position: relative;
                }
                
                .kebab-btn {
                    padding: 6px;
                    background: rgba(55, 65, 81, 0.8);
                    border: 1px solid rgba(75, 85, 99, 0.5);
                    border-radius: 6px;
                    color: #9ca3af;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .kebab-btn:hover {
                    background: rgba(99, 102, 241, 0.2);
                    color: #6366f1;
                    border-color: rgba(99, 102, 241, 0.3);
                }
                
                .kebab-dots {
                    display: flex;
                    gap: 2px;
                }
                
                .kebab-dot {
                    width: 3px;
                    height: 3px;
                    background: currentColor;
                    border-radius: 50%;
                }
                
                .kebab-menu {
                    position: absolute;
                    top: 100%;
                    right: 0;
                    background: rgba(26, 35, 50, 0.95);
                    border: 1px solid rgba(75, 85, 99, 0.5);
                    border-radius: 8px;
                    padding: 8px 0;
                    min-width: 180px;
                    z-index: 1000;
                    display: none;
                    backdrop-filter: blur(10px);
                }
                
                .kebab-menu.show {
                    display: block;
                }
                
                .menu-item {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 8px 16px;
                    color: #e8eaed;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    border: none;
                    background: none;
                    width: 100%;
                    text-align: left;
                }
                
                .menu-item:hover {
                    background: rgba(99, 102, 241, 0.1);
                    color: #6366f1;
                }
                
                .menu-item.danger:hover {
                    background: rgba(239, 68, 68, 0.1);
                    color: #ef4444;
                }
                
                .menu-divider {
                    height: 1px;
                    background: rgba(75, 85, 99, 0.5);
                    margin: 4px 0;
                }
                
                /* Camera Preview */
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
                
                .snapshot-overlay.hidden {
                    display: none;
                }
                
                /* Camera Details */
                .camera-details {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin-bottom: 15px;
                }
                
                .detail-section {
                    background: rgba(15, 20, 25, 0.6);
                    padding: 12px;
                    border-radius: 8px;
                    border: 1px solid rgba(55, 65, 81, 0.3);
                }
                
                .detail-section h4 {
                    margin: 0 0 8px 0;
                    font-size: 0.9rem;
                    color: #9ca3af;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .detail-item {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                    font-size: 0.9rem;
                }
                
                .detail-label {
                    color: #9ca3af;
                }
                
                .detail-value {
                    color: #e8eaed;
                    font-weight: 500;
                }
                
                .detail-value.link {
                    color: #3b82f6;
                    text-decoration: none;
                }
                
                .detail-value.link:hover {
                    text-decoration: underline;
                }
                
                /* Recording Status */
                .recording-status {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 12px 15px;
                    background: rgba(15, 20, 25, 0.6);
                    border-radius: 8px;
                    border: 1px solid rgba(55, 65, 81, 0.3);
                }
                
                .recording-info {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .recording-dot {
                    width: 12px;
                    height: 12px;
                    background: #ef4444;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }
                
                .recording-text {
                    color: #22c55e;
                    font-weight: 600;
                }
                
                .recording-stats {
                    color: #9ca3af;
                    font-size: 0.85rem;
                }
                
                /* Loading State */
                .loading-state {
                    grid-column: 1 / -1;
                    text-align: center;
                    padding: 60px 20px;
                    color: #9ca3af;
                }
                
                .loading-state i {
                    font-size: 3rem;
                    margin-bottom: 20px;
                    color: #6366f1;
                }
                
                /* Responsive */
                @media (max-width: 768px) {
                    .cameras-grid.grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .camera-filters {
                        flex-direction: column;
                        gap: 15px;
                    }
                    
                    .filter-actions {
                        margin-left: 0;
                        justify-content: center;
                    }
                    
                    .quick-actions {
                        justify-content: center;
                    }
                    
                    .view-toggle {
                        margin-left: 0;
                    }
                }
            </style>
        `;
    }

    async loadCameras() {
        try {
            const [dbCameras, healthData] = await Promise.all([
                this.fetchDatabaseCameras(),
                this.fetchCameraManagerHealth()
            ]);

            this.cameras = this.mergeCameraData(dbCameras, healthData);
            this.applyFilters();

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
        const usedDbCameras = new Set();
        
        // First, try to merge cameras from camera manager with database records
        Object.entries(healthData.cameras || {}).forEach(([managerId, health]) => {
            let dbCamera = null;
            
            // Enhanced connection info extraction
            const connectionInfo = this.extractConnectionInfo(health.connection_url);
            const extractedIp = connectionInfo.ip;
            const extractedPort = connectionInfo.port;
            
            // Strategy 1: Match by IP address
            if (extractedIp) {
                dbCamera = dbCameras.find(db => db.ip_address === extractedIp);
            }
            
            // Strategy 2: If no match and we have database cameras, try to match by being the only unused one
            if (!dbCamera && dbCameras.length === 1 && usedDbCameras.size === 0) {
                dbCamera = dbCameras[0];
            }
            
            // Strategy 3: Match by name similarity (if available)
            if (!dbCamera && health.camera_name) {
                dbCamera = dbCameras.find(db => 
                    db.name && db.name.toLowerCase().includes(health.camera_name.toLowerCase())
                );
            }
            
            if (dbCamera) {
                usedDbCameras.add(dbCamera);
            }
            
            // Database-first priority: Use database values as primary, health data for status/metrics only
            cameras.push({
                id: managerId,
                manager_id: managerId,
                database_id: dbCamera?.camera_id || dbCamera?.id || null,
                
                // Display Information (Database First)
                name: dbCamera?.name || (health.camera_name || `Camera ${managerId.substring(0, 8)}`),
                location: dbCamera?.location || 'Unknown',
                
                // Connection Information (Database First, Health Secondary)
                ip_address: dbCamera?.ip_address || extractedIp || 'Unknown',
                port: dbCamera?.port || extractedPort || 554,
                connection_type: dbCamera?.connection_type || 'RTSP',
                stream_path: dbCamera?.stream_path || health.stream_path || '/h264Preview_01_main',
                username: dbCamera?.username || 'admin',
                password: dbCamera?.password || '',
                
                // Hardware Information (Database Only)
                model: dbCamera?.model || 'Unknown',
                brand: dbCamera?.brand || 'Unknown',
                
                // Resolution & Quality (Database First, Health Secondary)
                resolution: dbCamera?.resolution_width && dbCamera?.resolution_height ? 
                    `${dbCamera.resolution_width}x${dbCamera.resolution_height}` : 
                    (health.resolution || '1920x1080'),
                resolution_width: dbCamera?.resolution_width || 1920,
                resolution_height: dbCamera?.resolution_height || 1080,
                fps: dbCamera?.max_fps || health.fps || 30,
                
                // Settings (Database Only)
                video_quality: dbCamera?.video_quality || 'medium',
                low_latency: dbCamera?.low_latency !== undefined ? dbCamera.low_latency : true,
                enabled: dbCamera?.enabled !== undefined ? dbCamera.enabled : true,
                
                // Health & Status Information (Health Data Only)
                status: health.is_healthy ? 'online' : 'offline',
                is_recording: health.capture_active || false,
                last_frame_age: health.last_frame_age || 0,
                error_count: health.error_count || 0,
                buffer_size: health.buffer_size || 0,
                max_buffer_size: health.max_buffer_size || 30,
                
                // Keep original records for complete access
                _dbRecord: dbCamera,
                _healthRecord: health
            });
        });

        // Add any unused database cameras that don't have health data (offline cameras)
        dbCameras.forEach(dbCamera => {
            if (!usedDbCameras.has(dbCamera)) {
                cameras.push({
                    id: dbCamera.camera_id || dbCamera.id,
                    manager_id: null, // No manager ID for offline cameras
                    database_id: dbCamera.camera_id || dbCamera.id,
                    name: dbCamera.name || 'Camera',
                    location: dbCamera.location || 'Unknown',
                    ip_address: dbCamera.ip_address || 'Unknown',
                    port: dbCamera.port || 554,
                    model: dbCamera.model || 'Unknown',
                    brand: dbCamera.brand || 'Unknown',
                    connection_type: dbCamera.connection_type || 'rtsp',
                    stream_path: dbCamera.stream_path || '/h264Preview_01_main',
                    username: dbCamera.username || 'admin',
                    password: dbCamera.password || '',
                    resolution: `${dbCamera.resolution_width || 1920}x${dbCamera.resolution_height || 1080}`,
                    resolution_width: dbCamera.resolution_width || 1920,
                    resolution_height: dbCamera.resolution_height || 1080,
                    fps: dbCamera.max_fps || 30,
                    video_quality: dbCamera.video_quality || 'medium',
                    low_latency: dbCamera.low_latency !== undefined ? dbCamera.low_latency : true,
                    enabled: dbCamera.enabled !== undefined ? dbCamera.enabled : true,
                    status: 'offline', // No health data means offline
                    is_recording: false,
                    last_frame_age: null,
                    error_count: 0,
                    buffer_size: 0,
                    _dbRecord: dbCamera
                });
            }
        });

        return cameras;
    }

    extractConnectionInfo(connectionUrl) {
        if (!connectionUrl) return { ip: null, port: null };
        try {
            // Handle different RTSP URL formats: rtsp://user:pass@IP:port/path
            const patterns = [
                /\/\/[^:]*:[^@]*@([^:]+):(\d+)/,  // rtsp://user:pass@IP:port
                /\/\/[^@]*@([^:]+):(\d+)/,        // rtsp://user@IP:port  
                /\/\/([^:]+):(\d+)/,               // rtsp://IP:port
                /\/\/[^:]*:[^@]*@([^:\/]+)/,      // rtsp://user:pass@IP (no port)
                /\/\/[^@]*@([^:\/]+)/,            // rtsp://user@IP (no port)
                /\/\/([^:\/]+)/                   // rtsp://IP (no port)
            ];
            
            for (const pattern of patterns) {
                const match = connectionUrl.match(pattern);
                if (match) {
                    return {
                        ip: match[1],
                        port: match[2] ? parseInt(match[2]) : 554  // Default RTSP port
                    };
                }
            }
            
            return { ip: null, port: null };
        } catch {
            return { ip: null, port: null };
        }
    }

    // Backward compatibility
    extractIpFromHealth(connectionUrl) {
        return this.extractConnectionInfo(connectionUrl).ip;
    }

    applyFilters() {
        this.filteredCameras = this.cameras.filter(camera => {
            const matchesStatus = !this.filters.status || camera.status === this.filters.status;
            const matchesLocation = !this.filters.location || camera.location === this.filters.location;
            const matchesSearch = !this.filters.search || 
                camera.name.toLowerCase().includes(this.filters.search) ||
                camera.ip_address.includes(this.filters.search);
            
            return matchesStatus && matchesLocation && matchesSearch;
        });

        this.renderCameras();
    }

    renderCameras() {
        const container = document.getElementById('cameras-grid');
        if (!container) return;

        if (this.filteredCameras.length === 0) {
            container.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-video-slash"></i>
                    <h3>No cameras found</h3>
                    <p>Professional monitoring system ready</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.filteredCameras.map(camera => 
            this.currentView === 'grid' ? this.renderCameraCard(camera) : this.renderCameraRow(camera)
        ).join('');
        
        // Initialize snapshots
        this.filteredCameras.forEach(camera => {
            this.loadCameraSnapshot(camera);
        });
    }

    renderCameraCard(camera) {
        // Format model/brand properly (avoid "Unknown Unknown")
        const modelDisplay = camera.model !== 'Unknown' ? 
            (camera.brand !== 'Unknown' ? `${camera.brand} ${camera.model}` : camera.model) : 
            (camera.brand !== 'Unknown' ? camera.brand : 'Unknown');
        
        // Format IP display - handle cases where IP might be "Unknown"  
        const ipDisplay = camera.ip_address !== 'Unknown' ? camera.ip_address : 'Unknown';
        const portDisplay = camera.port && camera.port !== 554 ? `:${camera.port}` : ':554';
        const connectionDisplay = ipDisplay !== 'Unknown' ? `${ipDisplay}${portDisplay}` : 'Unknown:554';
        
        // Health status for overlay
        const healthStatus = camera.status === 'online' ? 'REC' : 'OFF';
        const errorCount = camera.error_count || 0;
        const bufferSize = camera.buffer_size || 0;
        const maxBuffer = camera.max_buffer_size || 30;
        
        return `
            <div class="camera-card" data-camera-id="${camera.id}">
                <!-- Camera Header - Demo Style -->
                <div class="camera-header">
                    <div class="camera-title">
                        <span class="recording-dot ${camera.status === 'online' ? 'pulsing' : ''}"></span>
                        <h3 class="camera-name">${camera.name}</h3>
                    </div>
                    <div class="header-actions">
                        <button class="action-btn settings" data-action="settings" data-camera-id="${camera.id}" title="Settings">
                            <i class="fas fa-cog"></i>
                        </button>
                        <div class="kebab-wrapper">
                            <button class="action-btn kebab-btn" data-camera-id="${camera.id}" title="More actions">
                                <span class="kebab-dots">•••</span>
                            </button>
                            <div class="kebab-menu" id="kebab-menu-${camera.id}">
                                <button class="menu-item" data-action="snapshot" data-camera-id="${camera.id}">
                                    <i class="fas fa-camera"></i>
                                    <span>Take Snapshot</span>
                                </button>
                                <button class="menu-item" data-action="test" data-camera-id="${camera.id}">
                                    <i class="fas fa-network-wired"></i>
                                    <span>Test Connection</span>
                                </button>
                                <button class="menu-item" data-action="restart" data-camera-id="${camera.id}">
                                    <i class="fas fa-redo"></i>
                                    <span>Restart Camera</span>
                                </button>
                                <div class="menu-divider"></div>
                                <button class="menu-item danger" data-action="delete" data-camera-id="${camera.id}">
                                    <i class="fas fa-trash"></i>
                                    <span>Remove Camera</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Camera Preview with Health Overlay -->
                <div class="camera-preview">
                    <img class="camera-snapshot" 
                         id="snapshot-${camera.id}" 
                         alt="${camera.name} preview"
                         style="display: none;">
                    <div class="preview-loading" id="loading-${camera.id}">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Loading...</span>
                    </div>
                    <!-- Professional Health Overlay -->
                    <div class="health-overlay" id="health-${camera.id}">
                        <span class="health-status">●${healthStatus} E:${errorCount} B:${bufferSize}/${maxBuffer}</span>
                    </div>
                </div>

                <!-- Demo-Style Information List -->
                <div class="camera-info-list">
                    <div class="info-row">
                        <span class="info-label">IP ADDRESS</span>
                        <span class="info-value">${connectionDisplay}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">CONNECTION</span>
                        <span class="info-value ${camera.status}">${camera.status === 'online' ? 'Online' : 'Offline'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">RECORDING</span>
                        <span class="info-value">${camera.is_recording ? 'Recording' : 'Not Recording'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">LOCATION</span>
                        <span class="info-value">${camera.location || 'Unknown'}</span>
                    </div>
                    
                    <!-- Expandable More Details -->
                    <div class="more-details" data-camera-id="${camera.id}">
                        <div class="details-toggle">
                            <span class="toggle-label">MORE DETAILS</span>
                            <span class="toggle-icon">▶</span>
                        </div>
                        <div class="details-content">
                            <div class="info-row">
                                <span class="info-label">MODEL</span>
                                <span class="info-value">${modelDisplay}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">RESOLUTION</span>
                                <span class="info-value">${camera.resolution_width || 1920}x${camera.resolution_height || 1080}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">FPS</span>
                                <span class="info-value">${camera.fps || 30}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">BITRATE</span>
                                <span class="info-value">${camera._healthRecord?.bitrate || '--'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">PROTOCOL</span>
                                <span class="info-value">${camera.connection_type.toUpperCase()}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">LAST SEEN</span>
                                <span class="info-value">${this.formatLastSeen(camera)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderCameraRow(camera) {
        // List view implementation
        return `
            <div class="camera-row" data-camera-id="${camera.id}">
                <div class="row-content">
                    <div class="row-info">
                        <h4>${camera.name}</h4>
                        <span>${camera.ip_address} • ${camera.location}</span>
                    </div>
                    <div class="row-status ${camera.status}">
                        ${camera.status.toUpperCase()}
                    </div>
                </div>
            </div>
        `;
    }

    loadCameraSnapshot(camera) {
        const img = document.getElementById(`snapshot-${camera.id}`);
        const loading = document.getElementById(`loading-${camera.id}`);
        const healthOverlay = document.getElementById(`health-${camera.id}`);
        
        if (!img || !loading) return;

        // Only try to load snapshot if camera has manager_id (is online in camera manager)
        if (!camera.manager_id) {
            loading.innerHTML = `
                <i class="fas fa-camera-slash"></i>
                <span>Camera offline</span>
            `;
            // Hide health overlay for offline cameras
            if (healthOverlay) healthOverlay.style.display = 'none';
            return;
        }

        const snapshotUrl = config.buildApiUrl(`/api/cameras/${camera.manager_id}/snapshot`);
        
        img.onload = () => {
            img.style.display = 'block';
            loading.style.display = 'none';
            // Show health overlay when snapshot loads
            if (healthOverlay) healthOverlay.style.display = 'block';
        };
        
        img.onerror = () => {
            loading.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <span>Snapshot failed</span>
            `;
            // Hide health overlay on error
            if (healthOverlay) healthOverlay.style.display = 'none';
        };
        
        img.src = snapshotUrl;
    }

    formatLastSeen(camera) {
        if (camera.status === 'online') {
            return 'Just now';
        }
        
        if (camera.last_frame_age && camera.last_frame_age > 0) {
            const hours = Math.floor(camera.last_frame_age / 3600);
            const minutes = Math.floor((camera.last_frame_age % 3600) / 60);
            
            if (hours > 0) {
                return `${hours} hour${hours > 1 ? 's' : ''} ago`;
            } else if (minutes > 0) {
                return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
            } else {
                return 'Just now';
            }
        }
        
        return camera._healthRecord?.last_seen || 'Unknown';
    }

    attachEventListeners() {
        // Filter controls
        document.getElementById('apply-camera-filters')?.addEventListener('click', () => {
            this.updateFilters();
            this.applyFilters();
        });

        document.getElementById('clear-camera-filters')?.addEventListener('click', () => {
            this.clearFilters();
        });

        document.getElementById('camera-search-filter')?.addEventListener('input', (e) => {
            this.filters.search = e.target.value.toLowerCase();
            this.applyFilters();
        });

        // View toggle
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.changeView(e.target.dataset.view);
            });
        });

        // Quick action buttons
        document.getElementById('add-camera-btn')?.addEventListener('click', () => {
            this.showAddCameraModal();
        });

        document.getElementById('discover-cameras-btn')?.addEventListener('click', () => {
            this.showDiscoverCamerasModal();
        });

        document.getElementById('refresh-cameras-btn')?.addEventListener('click', () => {
            this.refreshCameras();
        });

        // Camera actions with improved event delegation
        document.addEventListener('click', (e) => {
            // Check for kebab button click (including child elements)
            const kebabBtn = e.target.closest('.kebab-btn');
            if (kebabBtn) {
                this.toggleKebabMenu(e);
                return;
            }
            
            // Check for details toggle click (including child elements)
            const detailsToggle = e.target.closest('.details-toggle');
            if (detailsToggle) {
                this.toggleMoreDetails(e);
                return;
            }
            
            // Check for menu item actions
            const actionElement = e.target.closest('[data-action]');
            if (actionElement) {
                this.handleCameraAction(e);
                return;
            }
            
            // Close all kebab menus when clicking outside
            document.querySelectorAll('.kebab-menu').forEach(menu => {
                menu.classList.remove('show');
            });
        });
    }

    updateFilters() {
        this.filters.status = document.getElementById('camera-status-filter').value;
        this.filters.location = document.getElementById('camera-location-filter').value;
        this.filters.search = document.getElementById('camera-search-filter').value.toLowerCase();
    }

    clearFilters() {
        document.getElementById('camera-status-filter').value = '';
        document.getElementById('camera-location-filter').value = '';
        document.getElementById('camera-search-filter').value = '';
        this.filters = { status: '', location: '', search: '' };
        this.applyFilters();
    }

    changeView(view) {
        this.currentView = view;
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        
        const grid = document.getElementById('cameras-grid');
        grid.className = `cameras-grid ${view}`;
        this.renderCameras();
    }

    toggleKebabMenu(e) {
        e.stopPropagation();
        e.preventDefault();
        const kebabBtn = e.target.closest('.kebab-btn');
        const cameraId = kebabBtn.dataset.cameraId;
        const menu = document.getElementById(`kebab-menu-${cameraId}`);
        if (!menu) return;
        
        // Close other menus
        document.querySelectorAll('.kebab-menu').forEach(m => {
            if (m !== menu) m.classList.remove('show');
        });
        
        menu.classList.toggle('show');
    }

    toggleMoreDetails(e) {
        e.stopPropagation();
        e.preventDefault();
        
        const detailsToggle = e.target.closest('.details-toggle');
        if (!detailsToggle) return;
        
        const moreDetails = detailsToggle.closest('.more-details');
        if (!moreDetails) return;
        
        const toggleIcon = moreDetails.querySelector('.toggle-icon');
        const detailsContent = moreDetails.querySelector('.details-content');
        
        if (!toggleIcon || !detailsContent) return;
        
        const isExpanded = moreDetails.classList.contains('expanded');
        
        if (isExpanded) {
            // Collapse
            moreDetails.classList.remove('expanded');
            toggleIcon.textContent = '▶';
            detailsContent.style.display = 'none';
        } else {
            // Expand
            moreDetails.classList.add('expanded');
            toggleIcon.textContent = '▼';
            detailsContent.style.display = 'block';
        }
    }

    handleCameraAction(e) {
        const action = e.target.closest('[data-action]').dataset.action;
        const cameraId = e.target.closest('[data-action]').dataset.cameraId;
        
        // Close kebab menu
        document.querySelectorAll('.kebab-menu').forEach(menu => {
            menu.classList.remove('show');
        });

        switch (action) {
            case 'settings':
                this.showCameraSettings(cameraId);
                break;
            case 'snapshot':
                this.takeSnapshot(cameraId);
                break;
            case 'test':
                this.testCamera(cameraId);
                break;
            case 'restart':
                this.restartCamera(cameraId);
                break;
            case 'delete':
                this.deleteCamera(cameraId);
                break;
        }
    }

    async takeSnapshot(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;

        if (!camera.manager_id) {
            this.showToast('❌ Cannot take snapshot: Camera not connected to camera manager', 'error');
            return;
        }

        try {
            const snapshotUrl = config.buildApiUrl(`/api/cameras/${camera.manager_id}/snapshot`);
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            
            const link = document.createElement('a');
            link.href = snapshotUrl;
            link.download = `${camera.name.replace(/\s+/g, '_')}_snapshot_${timestamp}.jpg`;
            link.click();
            
            this.showToast('📸 Snapshot saved!', 'success');
        } catch (error) {
            console.error('Snapshot error:', error);
            this.showToast('❌ Failed to take snapshot', 'error');
        }
    }

    async testCamera(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;

        if (camera.ip_address === 'Unknown') {
            this.showToast('❌ Cannot test: No IP address configured', 'error');
            return;
        }

        this.showToast(`🔍 Testing ${camera.name} connection...`, 'info');

        try {
            const response = await fetch(config.buildApiUrl('/api/cameras/test'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ip_address: camera.ip_address,
                    port: camera.port,
                    connection_type: camera.connection_type,
                    stream_path: camera.stream_path,
                    username: camera.username,
                    password: camera.password,
                    timeout: 10
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showToast(`✅ ${camera.name}: Connection successful (${result.resolution || 'Unknown resolution'})`, 'success');
            } else {
                this.showToast(`❌ ${camera.name}: ${result.message || 'Connection failed'}`, 'error');
            }
        } catch (error) {
            console.error('Test error:', error);
            this.showToast(`❌ ${camera.name}: Test failed - ${error.message}`, 'error');
        }
    }

    async showCameraSettings(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) {
            this.showToast('Camera not found', 'error');
            return;
        }

        try {
            // If we have a database_id, fetch the complete camera data from the API
            if (camera.database_id) {
                try {
                    const response = await fetch(config.buildApiUrl(`/api/cameras/${camera.database_id}`));
                    if (response.ok) {
                        const fullCameraData = await response.json();
                        // Use the complete data from the database
                        await this.simpleCameraModal.show(fullCameraData);
                    } else {
                        // Fallback to merged data if API call fails
                        await this.showCameraSettingsWithMergedData(camera);
                    }
                } catch (apiError) {
                    console.warn('Failed to fetch complete camera data:', apiError);
                    // Fallback to merged data
                    await this.showCameraSettingsWithMergedData(camera);
                }
            } else {
                // No database record, use merged data
                await this.showCameraSettingsWithMergedData(camera);
            }
            
            // Refresh cameras after modal closes
            this.simpleCameraModal.onClose = () => {
                this.loadCameras();
            };
            
        } catch (error) {
            console.error('Error opening camera settings:', error);
            this.showToast('Failed to open camera settings', 'error');
        }
    }

    async showCameraSettingsWithMergedData(camera) {
        // Use the enhanced merged camera data with all network values
        const modalCamera = {
            id: camera.database_id || camera.id,
            camera_id: camera.database_id || camera.id,
            name: camera.name || 'Camera',
            ip_address: camera.ip_address || '',
            port: camera.port || 554,
            connection_type: camera.connection_type || 'rtsp',
            stream_path: camera.stream_path || '/h264Preview_01_main',
            username: camera.username || 'admin',
            password: camera.password || '', // Will need to be entered if not saved
            brand: camera.brand || '',
            model: camera.model || '',
            location: camera.location || '',
            resolution_width: camera.resolution_width || 1920,
            resolution_height: camera.resolution_height || 1080,
            max_fps: camera.fps || 30,
            video_quality: camera.video_quality || 'medium',
            low_latency: camera.low_latency !== undefined ? camera.low_latency : true,
            enabled: camera.enabled !== undefined ? camera.enabled : camera.status === 'online'
        };

        await this.simpleCameraModal.show(modalCamera);
    }

    async restartCamera(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;

        this.showToast(`🔄 Restarting ${camera.name}...`, 'info');

        try {
            // Use database ID for restart API call
            const restartId = camera.database_id || camera.id;
            const response = await fetch(config.buildApiUrl(`/api/cameras/${restartId}/restart`), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const result = await response.json();
                this.showToast(`✅ ${camera.name}: ${result.message || 'Restart successful'}`, 'success');
                
                // Refresh camera data after a brief delay
                setTimeout(() => this.loadCameras(), 2000);
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Restart failed');
            }
        } catch (error) {
            console.error('Restart camera error:', error);
            this.showToast(`❌ ${camera.name}: Restart failed - ${error.message}`, 'error');
        }
    }

    async deleteCamera(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;

        if (!confirm(`Are you sure you want to delete "${camera.name}"?\n\nThis action cannot be undone.`)) {
            return;
        }

        try {
            // Use database ID for deletion
            const deleteId = camera.database_id || camera.id;
            const response = await fetch(config.buildApiUrl(`/api/cameras/${deleteId}`), {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                this.showToast(`✅ ${camera.name} deleted successfully`, 'success');
                // Refresh camera list
                await this.loadCameras();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Deletion failed');
            }
        } catch (error) {
            console.error('Delete camera error:', error);
            this.showToast(`❌ Failed to delete ${camera.name}: ${error.message}`, 'error');
        }
    }

    async refreshCameras() {
        const btn = document.getElementById('refresh-cameras-btn');
        const icon = btn.querySelector('i');
        
        icon.classList.add('fa-spin');
        btn.disabled = true;
        
        try {
            await this.loadCameras();
            this.showToast('Cameras refreshed successfully', 'success');
        } catch (error) {
            this.showToast('Failed to refresh cameras', 'error');
        } finally {
            icon.classList.remove('fa-spin');
            btn.disabled = false;
        }
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.loadCameras();
            
            // Refresh snapshots
            this.filteredCameras.forEach(camera => {
                const img = document.getElementById(`snapshot-${camera.id}`);
                if (img && img.style.display !== 'none') {
                    const snapshotUrl = config.buildApiUrl(`/api/cameras/${camera.manager_id}/snapshot`);
                    img.src = `${snapshotUrl}?t=${Date.now()}`;
                }
            });
        }, 30000);
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    showError(message) {
        const container = document.getElementById('cameras-grid');
        if (container) {
            container.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    showToast(message, type = 'info') {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            z-index: 10000;
            font-weight: 500;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    showAddCameraModal() {
        try {
            // Show modal in add mode (no camera data)
            this.simpleCameraModal.show();
            
            // Refresh cameras after modal closes
            this.simpleCameraModal.onClose = () => {
                this.loadCameras();
            };
            
        } catch (error) {
            console.error('Error opening add camera modal:', error);
            this.showToast('Failed to open camera setup', 'error');
        }
    }

    showDiscoverCamerasModal() {
        // For now, show a simple info message
        // This could be enhanced with actual ONVIF discovery integration
        this.showToast('🔍 Camera discovery: Check network settings in Add Camera modal', 'info');
        this.showAddCameraModal();
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Clean up modal
        if (this.simpleCameraModal) {
            this.simpleCameraModal.destroy?.();
        }
    }
}

export default EnhancedCamerasPage;