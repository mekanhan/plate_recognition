/**
 * Cameras Page Component
 * Manages camera list, configuration, and snapshot monitoring
 */
import SimpleCameraModal from '../components/cameras/SimpleCameraModal.js';
import config from '../config/app.config.js';

class Cameras {
    constructor() {
        this.cameras = [];
        this.filteredCameras = [];
        this.filters = {
            status: '',
            location: '',
            search: ''
        };
        this.selectedCameras = new Set();
        this.currentView = 'grid'; // grid or list
        this.bulkMode = false;
        
        // Make instance available globally for onclick handlers
        window.camerasPage = this;
        
        // Page visibility API for handling tab switching
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
        
        console.log('SimpleCameraModal class:', SimpleCameraModal);
        this.simpleCameraModal = new SimpleCameraModal();
        console.log('SimpleCameraModal instance:', this.simpleCameraModal);
        
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
        this.loadCameras();
    }

    render() {
        const container = document.getElementById('cameras');
        if (!container) return;

        container.innerHTML = this.getTemplate();
        this.renderCameraGrid();
    }

    getTemplate() {
        return `
            <div class="page-header">
                <h1 class="page-title">Cameras</h1>
                <p class="page-subtitle">Manage and monitor all security cameras</p>
            </div>
            
            <!-- Camera Management Controls -->
            <div class="quick-actions">
                <button class="quick-action-btn" id="add-camera-btn">
                    <i class="fas fa-plus"></i>
                    <span>Add Camera</span>
                </button>
                <button class="quick-action-btn" id="bulk-actions-btn">
                    <i class="fas fa-cog"></i>
                    <span>Bulk Actions</span>
                </button>
                <button class="quick-action-btn" id="refresh-cameras-btn">
                    <i class="fas fa-sync-alt"></i>
                    <span>Refresh All</span>
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
            
            <!-- Camera Quick Filters -->
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
                    <input type="text" id="camera-search-filter" class="filter-input" placeholder="Search by name or IP...">
                </div>
                <div class="filter-actions">
                    <button class="btn btn-primary" id="apply-camera-filters">Apply Filters</button>
                    <button class="btn btn-secondary" id="clear-camera-filters">Clear</button>
                </div>
            </div>
            
            <!-- Bulk Actions Bar (hidden by default) -->
            <div class="bulk-actions-bar" id="bulk-actions-bar" style="display: none;">
                <div class="bulk-selection-info">
                    <span id="selected-count">0</span> cameras selected
                </div>
                <div class="bulk-actions">
                    <button class="btn btn-small btn-success" id="bulk-enable">Enable</button>
                    <button class="btn btn-small btn-warning" id="bulk-disable">Disable</button>
                    <button class="btn btn-small btn-secondary" id="bulk-test">Test Connection</button>
                    <button class="btn btn-small btn-danger" id="bulk-delete">Delete</button>
                </div>
                <button class="bulk-close" id="bulk-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <!-- Camera Grid -->
            <div class="cameras-grid ${this.currentView}" id="cameras-grid">
                <!-- Camera cards will be dynamically loaded -->
            </div>

            <!-- Pagination -->
            <div class="camera-pagination" id="camera-pagination">
                <!-- Pagination will be added if needed -->
            </div>
        `;
    }

    attachEventListeners() {
        // Add camera button
        const addCameraBtn = document.getElementById('add-camera-btn');
        console.log('Add camera button found:', addCameraBtn);
        addCameraBtn?.addEventListener('click', () => {
            console.log('Add camera button clicked');
            this.showAddCameraModal();
        });

        // Bulk actions
        document.getElementById('bulk-actions-btn')?.addEventListener('click', () => this.toggleBulkMode());
        document.getElementById('bulk-close')?.addEventListener('click', () => this.closeBulkMode());

        // Refresh cameras
        document.getElementById('refresh-cameras-btn')?.addEventListener('click', () => this.refreshCameras());

        // View toggle
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.changeView(e.target.dataset.view));
        });

        // Filters
        document.getElementById('apply-camera-filters')?.addEventListener('click', () => this.applyFilters());
        document.getElementById('clear-camera-filters')?.addEventListener('click', () => this.clearFilters());
        document.getElementById('camera-search-filter')?.addEventListener('input', (e) => this.handleSearchInput(e));

        // Bulk actions
        document.getElementById('bulk-enable')?.addEventListener('click', () => this.bulkAction('enable'));
        document.getElementById('bulk-disable')?.addEventListener('click', () => this.bulkAction('disable'));
        document.getElementById('bulk-test')?.addEventListener('click', () => this.bulkAction('test'));
        document.getElementById('bulk-delete')?.addEventListener('click', () => this.bulkAction('delete'));

        // Global refresh listener
        window.addEventListener('dataRefresh', () => this.loadCameras());
        
        // Camera update listeners
        window.addEventListener('cameraAdded', () => this.loadCameras());
        window.addEventListener('cameraUpdated', () => this.loadCameras());
    }

    async loadCameras() {
        try {
            // In a real application, this would be an API call
            this.cameras = await this.fetchCameras();
            this.filteredCameras = [...this.cameras];
            
            this.renderCameraGrid();
        } catch (error) {
            console.error('Error loading cameras:', error);
            this.showError('Failed to load cameras');
        }
    }

    async fetchCameras() {
        try {
            // Load cameras from API using config
            const url = config.buildApiUrl(config.API_ENDPOINTS.CAMERAS);
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch cameras');
            }
            const cameras = await response.json();
            
            // Transform API response to match frontend expectations
            return cameras.map(camera => ({
                id: camera.camera_id || camera.id, // Use camera_id as primary identifier
                camera_id: camera.camera_id || camera.id,
                name: camera.name,
                location: camera.location || 'unknown',
                ipAddress: camera.ip_address,
                port: camera.port,
                connectionType: camera.connection_type,
                streamPath: camera.stream_path,
                status: this.mapBackendStatus(camera.status),
                manufacturer: camera.brand || 'Unknown',
                model: camera.model || 'Unknown',
                resolution: `${camera.resolution_width || 1920}x${camera.resolution_height || 1080}`,
                fps: camera.max_fps || 30,
                lastSeen: new Date(camera.updated_at || camera.created_at),
                uptime: this.calculateUptime(new Date(camera.created_at)),
                username: camera.username,
                enabled: camera.enabled
            }));
        } catch (error) {
            console.error('Error fetching cameras:', error);
            // Return empty array if API fails
            return [];
        }
    }

    calculateUptime(createdAt) {
        const now = new Date();
        const diff = now - createdAt;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        return `${days}d ${hours}h ${minutes}m`;
    }

    mapBackendStatus(backendStatus) {
        // Map backend status values to frontend expected values
        const statusMap = {
            'active': 'online',
            'inactive': 'offline', 
            'error': 'error',
            'offline': 'offline',
            'online': 'online',
            'warning': 'warning',
            'connecting': 'warning',
            'unknown': 'offline'
        };
        return statusMap[backendStatus] || 'offline';
    }



    updateAllCameraStates() {
        // Update camera status indicators and information
        this.cameras.forEach(camera => {
            this.updateCameraStatusIndicator(camera.id);
            this.updateCameraInfo(camera.id);
        });
    }

    renderCameraGrid() {
        const container = document.getElementById('cameras-grid');
        if (!container) return;

        container.className = `cameras-grid ${this.currentView}`;

        if (this.filteredCameras.length === 0) {
            container.innerHTML = this.getEmptyState();
            return;
        }

        container.innerHTML = this.filteredCameras.map(camera => 
            this.currentView === 'grid' ? this.renderCameraCard(camera) : this.renderCameraRow(camera)
        ).join('');

        // Initialize video players for grid view
        if (this.currentView === 'grid') {
            this.filteredCameras.forEach(camera => {
                this.initializeCameraPlayer(camera);
            });
        }

        // Attach camera-specific event listeners
        this.attachCameraEventListeners();
    }

    renderCameraCard(camera) {
        const statusClass = camera.status;
        const healthScore = this.calculateHealthScore(camera);
        // Removed streaming state
        
        return `
            <div class="camera-card" data-camera-id="${camera.id}">
                <div class="camera-card-header">
                    <div class="camera-title-row">
                        <div class="camera-checkbox" style="display: ${this.selectedCameras.size > 0 || this.bulkMode ? 'block' : 'none'}">
                            <input type="checkbox" class="camera-select" data-camera-id="${camera.id}" ${this.selectedCameras.has(camera.id) ? 'checked' : ''}>
                        </div>
                        <h4 class="camera-card-title">${camera.display_name || camera.name}</h4>
                        ${camera.short_id ? `<span class="camera-short-id">#${camera.short_id}</span>` : ''}
                        <div class="camera-card-status ${statusClass}">
                            <i class="fas ${this.getStatusIcon(camera.status)}"></i>
                            <span>${this.capitalizeFirst(camera.status)}</span>
                        </div>
                        <div class="action-dropdown">
                            <button class="btn btn-secondary btn-small dropdown-toggle" data-camera-id="${camera.id}">
                                <i class="fas fa-ellipsis-h"></i>
                            </button>
                            <div class="dropdown-menu dropdown-menu-right">
                                <button class="dropdown-item" data-action="edit" data-camera-id="${camera.id}">
                                    <i class="fas fa-cog"></i>
                                    Configure
                                </button>
                                <button class="dropdown-item" data-action="test" data-camera-id="${camera.id}">
                                    <i class="fas fa-plug"></i>
                                    Test Connection
                                </button>
                                <button class="dropdown-item" data-action="details" data-camera-id="${camera.id}">
                                    <i class="fas fa-info-circle"></i>
                                    View Details
                                </button>
                                <button class="dropdown-item" data-action="reboot" data-camera-id="${camera.id}">
                                    <i class="fas fa-redo"></i>
                                    Reboot Camera
                                </button>
                                <div class="dropdown-divider"></div>
                                <button class="dropdown-item text-danger" data-action="delete" data-camera-id="${camera.id}">
                                    <i class="fas fa-trash"></i>
                                    Delete Camera
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="camera-card-body">
                    <div class="camera-card-preview">
                        <div class="preview-container" id="preview-container-${camera.id}">
                            <!-- LiveVideoPlayer will be inserted here -->
                        </div>
                    </div>
                    
                    <div class="camera-card-info">
                        <div class="info-row">
                            <span class="info-label">Location:</span>
                            <span class="info-value">${this.capitalizeFirst(camera.location)}</span>
                        </div>
                        ${camera.status === 'offline' ? `
                        <div class="info-row error">
                            <span class="info-label">Last Seen:</span>
                            <span class="info-value">${this.getRelativeTime(camera.lastSeen)}</span>
                        </div>
                        ` : ''}
                        <div class="info-row">
                            <span class="info-label">Connection:</span>
                            <span class="info-value">${camera.connectionType?.toUpperCase() || 'HTTP'} (${camera.ipAddress})</span>
                        </div>
                    </div>
                </div>
                
                <!-- Snapshot-only interface, no streaming controls -->
            </div>
        `;
    }

    initializeCameraPlayer(camera) {
        const container = document.getElementById(`preview-container-${camera.id}`);
        if (!container) return;
        
        // Clean up existing player first
        // Display snapshot instead of video player
        container.innerHTML = `
            <img src="/api/cameras/${camera.id}/snapshot" 
                 alt="${camera.display_name || camera.name} snapshot" 
                 class="camera-snapshot"
                 onerror="this.src='/images/camera-placeholder.jpg'"
                 style="width: 100%; height: 100%; object-fit: cover;">
        `;
        
        // Set up navigation cleanup
        this.setupNavigationCleanup(camera.id);
    }

    // Clean up camera snapshot refresh
    cleanupCameraPlayer(cameraId) {
        // No cleanup needed for snapshot-only interface
    }
    
    // Set up snapshot refresh
    setupNavigationCleanup(cameraId) {
        // No navigation cleanup needed for snapshot-only interface
    }
    
    // Handle page visibility changes (tab switching)
    handleVisibilityChange() {
        // Page visibility handling - refresh snapshots when page becomes visible
        if (!document.hidden) {
            this.refreshSnapshots();
        }
    }
    
    // Refresh all camera snapshots
    refreshSnapshots() {
        document.querySelectorAll('.camera-snapshot').forEach(img => {
            // Force reload snapshot by updating src with timestamp
            const baseSrc = img.src.split('?')[0];
            img.src = `${baseSrc}?t=${Date.now()}`;
        });
    }

    // Camera event handlers
    handleSnapshotError(cameraId, error) {
        console.error(`Camera ${cameraId} snapshot error:`, error);
        this.showToast(`Camera snapshot error: ${error}`, 'error');
    }

    updateCameraStatusIndicator(cameraId) {
        const statusElement = document.querySelector(`[data-camera-id="${cameraId}"] .camera-card-status`);
        if (!statusElement) return;

        // Status indicator updated without streaming badge - cleaner interface
    }

    updateCameraInfo(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;

        const cameraCard = document.querySelector(`[data-camera-id="${cameraId}"]`);
        const infoSection = cameraCard?.querySelector('.camera-card-info');
        if (!infoSection) return;

        const healthScore = this.calculateHealthScore(camera);

        // Rebuild the camera info section
        infoSection.innerHTML = `
            <div class="info-row">
                <span class="info-label">Location:</span>
                <span class="info-value">${this.capitalizeFirst(camera.location)}</span>
            </div>
            ${camera.status === 'offline' ? `
            <div class="info-row error">
                <span class="info-label">Last Seen:</span>
                <span class="info-value">${this.getRelativeTime(camera.lastSeen)}</span>
            </div>
            ` : ''}
            <div class="info-row">
                <span class="info-label">Connection:</span>
                <span class="info-value">${camera.connectionType?.toUpperCase() || 'HTTP'} (${camera.ipAddress})</span>
            </div>
        `;
    }

    // Removed stream timer methods - snapshot-only interface

    renderCameraRow(camera) {
        const statusIcon = this.getStatusIcon(camera.status);
        const statusClass = camera.status;

        return `
            <div class="camera-row ${statusClass}" data-camera-id="${camera.id}">
                <div class="row-checkbox">
                    <input type="checkbox" class="camera-select" data-camera-id="${camera.id}">
                </div>
                <div class="row-status ${statusClass}">
                    <i class="fas ${statusIcon}"></i>
                </div>
                <div class="row-info">
                    <div class="row-primary">
                        <span class="camera-name">${camera.display_name || camera.name}</span>
                        ${camera.short_id ? `<span class="camera-short-id-inline">#${camera.short_id}</span>` : ''}
                        <span class="camera-ip">${camera.ipAddress}</span>
                    </div>
                    <div class="row-secondary">
                        <span class="camera-location">${this.capitalizeFirst(camera.location)}</span>
                        <span class="camera-specs">${camera.resolution} @ ${camera.fps}fps</span>
                        <span class="camera-manufacturer">${camera.manufacturer} ${camera.model}</span>
                    </div>
                </div>
                <div class="row-metadata">
                    <div class="uptime">${camera.uptime}</div>
                    <div class="last-seen">${this.getRelativeTime(camera.lastSeen)}</div>
                </div>
                <div class="row-actions">
                    <button class="action-btn" title="Edit" data-action="edit" data-camera-id="${camera.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-btn" title="Test" data-action="test" data-camera-id="${camera.id}">
                        <i class="fas fa-plug"></i>
                    </button>
                    <button class="action-btn" title="Details" data-action="details" data-camera-id="${camera.id}">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button class="action-btn danger" title="Delete" data-action="delete" data-camera-id="${camera.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }

    getEmptyState() {
        return `
            <div class="empty-state">
                <i class="fas fa-video-slash"></i>
                <h3>No cameras found</h3>
                <p>Add your first camera to start monitoring</p>
                <button class="btn btn-primary" id="add-first-camera">
                    <i class="fas fa-plus"></i>
                    Add Camera
                </button>
            </div>
        `;
    }

    attachCameraEventListeners() {
        // Camera selection checkboxes
        document.querySelectorAll('.camera-select').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleCameraSelection(e));
        });

        // Camera action buttons
        document.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleCameraAction(e));
        });

        // Preview buttons - removed as they're now handled by LiveVideoPlayer

        // Dropdown toggles
        document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => this.toggleDropdown(e));
        });

        // Add first camera button
        document.getElementById('add-first-camera')?.addEventListener('click', () => this.showAddCameraModal());

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => this.handleOutsideClick(e));
    }

    handleCameraSelection(e) {
        const cameraId = e.target.dataset.cameraId;
        const isChecked = e.target.checked;

        if (isChecked) {
            this.selectedCameras.add(cameraId);
        } else {
            this.selectedCameras.delete(cameraId);
        }

        this.updateBulkActionsBar();
    }

    updateBulkActionsBar() {
        const bulkBar = document.getElementById('bulk-actions-bar');
        const selectedCount = document.getElementById('selected-count');
        
        if (this.selectedCameras.size > 0) {
            bulkBar.style.display = 'flex';
            selectedCount.textContent = this.selectedCameras.size;
        } else {
            bulkBar.style.display = 'none';
        }
    }

    handleCameraAction(e) {
        e.stopPropagation();
        const action = e.target.dataset.action || e.target.parentElement.dataset.action;
        const cameraId = e.target.dataset.cameraId || e.target.parentElement.dataset.cameraId;
        
        // Close any open dropdowns
        this.closeAllDropdowns();
        
        switch (action) {
            case 'edit':
                this.editCamera(cameraId);
                break;
            case 'live':
                this.openCameraLiveView(cameraId);
                break;
            case 'capture':
                this.handleCapture(cameraId);
                break;
            case 'fullscreen':
                this.handleFullscreen(cameraId);
                break;
            case 'test':
                this.testCamera(cameraId);
                break;
            case 'details':
                this.showCameraDetails(cameraId);
                break;
            case 'reboot':
                this.rebootCamera(cameraId);
                break;
            case 'delete':
                this.deleteCamera(cameraId);
                break;
        }
    }

    toggleDropdown(e) {
        e.stopPropagation();
        const toggle = e.target.closest('.dropdown-toggle');
        const dropdown = toggle.parentElement;
        const menu = dropdown.querySelector('.dropdown-menu');
        
        // Close all other dropdowns first
        this.closeAllDropdowns();
        
        // Toggle this dropdown
        menu.classList.toggle('show');
    }

    closeAllDropdowns() {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    }

    handleOutsideClick(e) {
        if (!e.target.closest('.action-dropdown')) {
            this.closeAllDropdowns();
        }
    }

    // Camera action methods
    editCamera(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (camera) {
            // Show edit camera modal with pre-filled data
            this.simpleCameraModal.show(camera);
        }
    }

    async testCamera(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;

        // Show loading state
        const testBtn = document.querySelector(`[data-action="test"][data-camera-id="${cameraId}"]`);
        const originalContent = testBtn.innerHTML;
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        testBtn.disabled = true;

        try {
            // Perform actual connection test
            const result = await this.performConnectionTest(camera);
            
            if (result.success) {
                const responseTime = result.response_time ? ` (${Math.round(result.response_time)}ms)` : '';
                this.showToast(`✅ ${camera.name}: ${result.message}${responseTime}`, 'success');
            } else {
                this.showToast(`❌ ${camera.name}: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Connection test error:', error);
            this.showToast(`❌ ${camera.name}: Connection test failed`, 'error');
        } finally {
            testBtn.innerHTML = originalContent;
            testBtn.disabled = false;
        }
    }

    showCameraDetails(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (camera) {
            // Create and show camera details modal
            this.showCameraDetailsModal(camera);
        }
    }

    showCameraDetailsModal(camera) {
        // Create modal HTML - compact version matching SimpleCameraModal size
        const modalHtml = `
            <div class="modal-overlay simple-camera-modal" id="camera-details-modal">
                <div class="modal-container">
                    <div class="modal-header">
                        <h3>
                            <i class="fas fa-info-circle"></i>
                            Camera Details
                        </h3>
                        <button class="modal-close" id="close-details-modal">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="camera-details-compact">
                            <!-- Basic Information -->
                            <div class="details-section">
                                <h4 class="section-title">Basic Information</h4>
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>Camera Name</label>
                                        <div class="detail-value">${camera.name}</div>
                                    </div>
                                    <div class="form-group">
                                        <label>Location</label>
                                        <div class="detail-value">${this.capitalizeFirst(camera.location)}</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Connection Details -->
                            <div class="details-section">
                                <h4 class="section-title">Connection</h4>
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>IP Address</label>
                                        <div class="detail-value">${camera.ipAddress}</div>
                                    </div>
                                    <div class="form-group">
                                        <label>Port</label>
                                        <div class="detail-value">${camera.port}</div>
                                    </div>
                                </div>
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>Connection Type</label>
                                        <div class="detail-value">${camera.connectionType?.toUpperCase()}</div>
                                    </div>
                                    <div class="form-group">
                                        <label>Stream Path</label>
                                        <div class="detail-value">${camera.streamPath || 'N/A'}</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Status & Performance -->
                            <div class="details-section">
                                <h4 class="section-title">Status & Performance</h4>
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>Current Status</label>
                                        <div class="detail-value status-${camera.status}">
                                            <i class="fas ${this.getStatusIcon(camera.status)}"></i>
                                            ${this.capitalizeFirst(camera.status)}
                                        </div>
                                    </div>
                                </div>
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>Last Seen</label>
                                        <div class="detail-value">${this.getRelativeTime(camera.lastSeen)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="close-details-btn">Close</button>
                        <button class="btn btn-primary" id="edit-from-details-btn" data-camera-id="${camera.id}">
                            <i class="fas fa-cog"></i>
                            Configure
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('camera-details-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = document.getElementById('camera-details-modal');
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('show'), 10);

        // Add event listeners
        document.getElementById('close-details-modal')?.addEventListener('click', () => this.closeCameraDetailsModal());
        document.getElementById('close-details-btn')?.addEventListener('click', () => this.closeCameraDetailsModal());
        document.getElementById('edit-from-details-btn')?.addEventListener('click', (e) => {
            this.closeCameraDetailsModal();
            this.editCamera(e.target.dataset.cameraId);
        });
        
        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeCameraDetailsModal();
            }
        });
    }

    closeCameraDetailsModal() {
        const modal = document.getElementById('camera-details-modal');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        }
    }

    async rebootCamera(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;

        if (confirm(`Are you sure you want to reboot "${camera.name}"? This may take a few minutes.`)) {
            try {
                // Simulate reboot operation
                await this.performRebootCamera(cameraId);
                this.showToast(`Camera "${camera.name}" is rebooting`, 'info');
                
                // Update camera status to show it's rebooting
                camera.status = 'warning';
                this.renderCameraGrid();
                
                // Simulate completion after delay
                setTimeout(() => {
                    camera.status = 'online';
                    this.renderCameraGrid();
                    this.showToast(`Camera "${camera.name}" rebooted successfully`, 'success');
                }, 3000);
            } catch (error) {
                this.showToast(`Failed to reboot camera "${camera.name}"`, 'error');
            }
        }
    }

    async deleteCamera(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;

        if (confirm(`Are you sure you want to delete "${camera.name}"?`)) {
            try {
                // Use camera_id directly - no conversion needed
                const apiUrl = config.buildApiUrl(config.API_ENDPOINTS.CAMERA_BY_ID(cameraId));
                const response = await fetch(apiUrl, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to delete camera');
                }

                // Remove from local array and re-render
                this.cameras = this.cameras.filter(c => c.id !== cameraId);
                this.applyFilters();
                this.showToast(`Camera "${camera.name}" deleted successfully`, 'success');
            } catch (error) {
                console.error('Error deleting camera:', error);
                this.showToast(`Failed to delete camera "${camera.name}"`, 'error');
            }
        }
    }

    // Utility methods
    getStatusIcon(status) {
        const icons = {
            online: 'fa-circle',
            offline: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-exclamation-circle'
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

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    calculateHealthScore(camera) {
        let score = 100;
        
        // Status impact
        if (camera.status === 'offline' || camera.status === 'error') {
            score -= 50;
        } else if (camera.status === 'warning') {
            score -= 20;
        }
        
        // Uptime calculation (assume 100% if online, 0% if offline)
        const uptimeParts = camera.uptime.split(' ');
        let uptimeScore = 0;
        
        if (camera.status === 'online') {
            // Parse uptime string like "15d 4h 23m"
            const days = parseInt(uptimeParts[0]) || 0;
            const hours = parseInt(uptimeParts[1]) || 0;
            
            // Calculate uptime percentage (assuming target is 30 days)
            const totalHours = (days * 24) + hours;
            const targetHours = 30 * 24; // 30 days
            uptimeScore = Math.min((totalHours / targetHours) * 100, 100);
        }
        
        // Adjust score based on uptime
        if (uptimeScore < 95) {
            score -= (95 - uptimeScore);
        }
        
        // Last seen impact
        if (camera.lastSeen) {
            const lastSeenMinutes = (new Date() - camera.lastSeen) / (1000 * 60);
            if (lastSeenMinutes > 60) { // More than 1 hour
                score -= Math.min(lastSeenMinutes / 60, 20); // Max 20 point penalty
            }
        }
        
        return Math.max(Math.round(score), 0);
    }

    showToast(message, type = 'info', duration = 3000) {
        // Create enhanced toast notification with better styling
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle', 
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        const colorMap = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
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
        
        // Enhanced styling
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            minWidth: '300px',
            maxWidth: '500px',
            padding: '16px 20px',
            backgroundColor: colorMap[type] || colorMap.info,
            color: 'white',
            borderRadius: '8px',
            zIndex: '10001',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.15)',
            fontSize: '14px',
            lineHeight: '1.4',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        // Toast close button styling
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            Object.assign(closeBtn.style, {
                background: 'rgba(255, 255, 255, 0.2)',
                border: 'none',
                borderRadius: '4px',
                color: 'white',
                cursor: 'pointer',
                padding: '4px 6px',
                fontSize: '12px',
                marginLeft: 'auto'
            });
        }
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Auto remove
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

    async performConnectionTest(camera) {
        try {
            const response = await fetch(config.buildApiUrl(config.API_ENDPOINTS.CAMERA_TEST_CONNECTION), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip_address: camera.ipAddress || camera.ip_address,
                    port: camera.port || 80,
                    connection_type: camera.connectionType || camera.connection_type || 'http',
                    stream_path: camera.streamPath || camera.stream_path || '/mjpeg',
                    username: camera.username || 'admin',
                    password: camera.password || '',
                    timeout: 10
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                return {
                    success: false,
                    message: errorData.detail || `HTTP ${response.status}: ${response.statusText}`
                };
            }
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('Connection test failed:', error);
            return {
                success: false,
                message: `Network error: ${error.message}`
            };
        }
    }

    async performRebootCamera(cameraId) {
        return new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Filter and search methods
    applyFilters() {
        this.filters.status = document.getElementById('camera-status-filter').value;
        this.filters.location = document.getElementById('camera-location-filter').value;
        this.filters.search = document.getElementById('camera-search-filter').value.toLowerCase();

        this.filteredCameras = this.cameras.filter(camera => {
            const matchesStatus = !this.filters.status || camera.status === this.filters.status;
            const matchesLocation = !this.filters.location || camera.location === this.filters.location;
            const matchesSearch = !this.filters.search || 
                camera.name.toLowerCase().includes(this.filters.search) ||
                camera.ipAddress.includes(this.filters.search);

            return matchesStatus && matchesLocation && matchesSearch;
        });

        this.renderCameraGrid();
    }

    clearFilters() {
        document.getElementById('camera-status-filter').value = '';
        document.getElementById('camera-location-filter').value = '';
        document.getElementById('camera-search-filter').value = '';
        
        this.filters = { status: '', location: '', search: '' };
        this.filteredCameras = [...this.cameras];
        this.renderCameraGrid();
    }

    handleSearchInput(e) {
        // Debounced search
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.applyFilters();
        }, 300);
    }

    // View management
    changeView(view) {
        this.currentView = view;
        
        // Update button states
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        
        this.renderCameraGrid();
    }

    // Modal methods
    showAddCameraModal() {
        this.simpleCameraModal.show();
    }

    openCameraLiveView(cameraId) {
        // Snapshot-only interface - show snapshot in modal
        this.showSnapshotModal(cameraId);
    }
    
    showSnapshotModal(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (!camera) return;
        
        // Create snapshot modal (simple implementation)
        const modal = document.createElement('div');
        modal.className = 'snapshot-modal';
        modal.innerHTML = `
            <div class="snapshot-modal-content">
                <div class="snapshot-modal-header">
                    <h3>${camera.display_name || camera.name} - Live Snapshot</h3>
                    <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
                </div>
                <div class="snapshot-modal-body">
                    <img src="/api/cameras/${cameraId}/snapshot?t=${Date.now()}" 
                         alt="${camera.display_name || camera.name} snapshot" 
                         style="max-width: 100%; height: auto;">
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Auto-refresh snapshot every 5 seconds
        const img = modal.querySelector('img');
        const refreshInterval = setInterval(() => {
            img.src = `/api/cameras/${cameraId}/snapshot?t=${Date.now()}`;
        }, 5000);
        
        // Clean up interval when modal is closed
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                clearInterval(refreshInterval);
                modal.remove();
            }
        });
    }

    // Snapshot control handlers
    async handleRefreshSnapshot(cameraId) {
        const snapshotImg = document.querySelector(`[data-camera-id="${cameraId}"] .camera-snapshot`);
        if (snapshotImg) {
            try {
                snapshotImg.src = `/api/cameras/${cameraId}/snapshot?t=${Date.now()}`;
                this.showToast('Snapshot refreshed', 'success');
            } catch (error) {
                this.showToast(`Failed to refresh snapshot: ${error.message}`, 'error');
            }
        }
    }

    async handleCapture(cameraId) {
        try {
            // Capture current snapshot
            const response = await fetch(config.buildApiUrl(`/api/cameras/${cameraId}/snapshot`));
            if (response.ok) {
                this.showToast('Snapshot captured successfully', 'success');
            } else {
                throw new Error('Failed to capture snapshot');
            }
        } catch (error) {
            this.showToast(`Failed to capture snapshot: ${error.message}`, 'error');
        }
    }

    async handleFullscreen(cameraId) {
        this.openCameraLiveView(cameraId);
    }

    // Bulk actions
    toggleBulkMode() {
        this.bulkMode = !this.bulkMode;
        const checkboxes = document.querySelectorAll('.camera-checkbox');
        
        if (this.bulkMode) {
            checkboxes.forEach(cb => cb.style.display = 'block');
        } else {
            checkboxes.forEach(cb => cb.style.display = 'none');
            this.selectedCameras.clear();
            document.querySelectorAll('.camera-select').forEach(cb => cb.checked = false);
            this.updateBulkActionsBar();
        }
    }

    closeBulkMode() {
        this.bulkMode = false;
        this.selectedCameras.clear();
        document.querySelectorAll('.camera-select').forEach(cb => cb.checked = false);
        document.querySelectorAll('.camera-checkbox').forEach(cb => cb.style.display = 'none');
        this.updateBulkActionsBar();
    }

    async bulkAction(action) {
        const selectedIds = Array.from(this.selectedCameras);
        if (selectedIds.length === 0) return;

        const confirmMessage = `Are you sure you want to ${action} ${selectedIds.length} camera(s)?`;
        if (!confirm(confirmMessage)) return;

        try {
            // Simulate bulk operation
            await this.performBulkAction(action, selectedIds);
            this.showToast(`Bulk ${action} completed successfully`, 'success');
            this.closeBulkMode();
            this.loadCameras();
        } catch (error) {
            this.showToast(`Bulk ${action} failed`, 'error');
        }
    }

    async performBulkAction(action, cameraIds) {
        return new Promise(resolve => setTimeout(resolve, 1000));
    }

    async refreshCameras() {
        const refreshBtn = document.getElementById('refresh-cameras-btn');
        const icon = refreshBtn.querySelector('i');
        
        icon.classList.add('fa-spin');
        refreshBtn.disabled = true;

        try {
            await this.loadCameras();
            this.showToast('Cameras refreshed successfully', 'success');
        } catch (error) {
            this.showToast('Failed to refresh cameras', 'error');
        } finally {
            icon.classList.remove('fa-spin');
            refreshBtn.disabled = false;
        }
    }

    // Enhanced cleanup on page destroy
    destroy() {
        // Remove visibility change listener
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Stop all polling
        this.stopStatusPolling();
        
        // Clean up camera components
        this.cameras.forEach(camera => {
            this.cleanupCameraPlayer(camera.id);
        });
        
        // Remove global reference
        if (window.camerasPage === this) {
            delete window.camerasPage;
        }
        
        console.log('CamerasPage cleaned up with enhanced cleanup');
    }
}

export default Cameras;