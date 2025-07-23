/**
 * Cameras Page Component
 * Manages camera list, configuration, and monitoring
 */
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
        document.getElementById('add-camera-btn')?.addEventListener('click', () => this.showAddCameraModal());

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
        // Simulate API call with mock data
        return new Promise(resolve => {
            setTimeout(() => {
                resolve([
                    {
                        id: '1',
                        name: 'Entrance Gate',
                        location: 'entrance',
                        ipAddress: '192.168.1.101',
                        status: 'online',
                        manufacturer: 'Hikvision',
                        model: 'DS-2CD2T85FWD-I8',
                        resolution: '3840x2160',
                        fps: 30,
                        lastSeen: new Date(Date.now() - 5 * 60 * 1000),
                        uptime: '15d 4h 23m'
                    },
                    {
                        id: '2',
                        name: 'Parking Lot A',
                        location: 'parking',
                        ipAddress: '192.168.1.102',
                        status: 'online',
                        manufacturer: 'Dahua',
                        model: 'IPC-HFW4831E-SE',
                        resolution: '3840x2160',
                        fps: 25,
                        lastSeen: new Date(Date.now() - 2 * 60 * 1000),
                        uptime: '12d 8h 15m'
                    },
                    {
                        id: '3',
                        name: 'Loading Dock',
                        location: 'exit',
                        ipAddress: '192.168.1.103',
                        status: 'warning',
                        manufacturer: 'Axis',
                        model: 'M3046-V',
                        resolution: '1920x1080',
                        fps: 30,
                        lastSeen: new Date(Date.now() - 45 * 60 * 1000),
                        uptime: '8d 12h 45m'
                    },
                    {
                        id: '4',
                        name: 'Side Entrance',
                        location: 'entrance',
                        ipAddress: '192.168.1.104',
                        status: 'offline',
                        manufacturer: 'Reolink',
                        model: 'RLC-810A',
                        resolution: '3840x2160',
                        fps: 25,
                        lastSeen: new Date(Date.now() - 2 * 60 * 60 * 1000),
                        uptime: '0d 0h 0m'
                    }
                ]);
            }, 500);
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

        // Attach camera-specific event listeners
        this.attachCameraEventListeners();
    }

    renderCameraCard(camera) {
        const statusClass = camera.status;
        const healthScore = this.calculateHealthScore(camera);
        
        return `
            <div class="camera-card" data-camera-id="${camera.id}">
                <div class="camera-card-header">
                    <div class="camera-title-row">
                        <div class="camera-checkbox" style="display: ${this.selectedCameras.size > 0 || this.bulkMode ? 'block' : 'none'}">
                            <input type="checkbox" class="camera-select" data-camera-id="${camera.id}" ${this.selectedCameras.has(camera.id) ? 'checked' : ''}>
                        </div>
                        <h4 class="camera-card-title">${camera.name}</h4>
                        <div class="camera-card-status ${statusClass}">
                            <i class="fas ${this.getStatusIcon(camera.status)}"></i>
                            <span>${this.capitalizeFirst(camera.status)}</span>
                        </div>
                    </div>
                </div>
                
                <div class="camera-card-body">
                    <div class="camera-card-preview">
                        <div class="preview-container">
                            ${camera.status === 'online' ? 
                                '<div class="video-feed-placeholder"><i class="fas fa-video"></i><span>Live Feed</span></div>' :
                                camera.status === 'offline' ? 
                                '<div class="offline-indicator"><i class="fas fa-exclamation-triangle"></i><span>No Signal</span></div>' :
                                '<div class="warning-indicator"><i class="fas fa-exclamation-circle"></i><span>Degraded</span></div>'
                            }
                            <div class="preview-overlay">
                                <button class="preview-play-btn" data-camera-id="${camera.id}" ${camera.status !== 'online' ? 'disabled' : ''}>
                                    <i class="fas fa-play"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="camera-card-info">
                        <div class="info-row">
                            <span class="info-label">Location:</span>
                            <span class="info-value">${this.capitalizeFirst(camera.location)}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">IP Address:</span>
                            <span class="info-value">${camera.ipAddress}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Resolution:</span>
                            <span class="info-value">${camera.resolution}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Frame Rate:</span>
                            <span class="info-value">${camera.fps} FPS</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Manufacturer:</span>
                            <span class="info-value">${camera.manufacturer}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Model:</span>
                            <span class="info-value">${camera.model}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Uptime:</span>
                            <span class="info-value">${camera.uptime}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Health Score:</span>
                            <span class="info-value health-score ${healthScore >= 90 ? 'excellent' : healthScore >= 75 ? 'good' : healthScore >= 50 ? 'fair' : 'poor'}">${healthScore}%</span>
                        </div>
                        ${camera.status === 'offline' ? `
                        <div class="info-row error">
                            <span class="info-label">Last Seen:</span>
                            <span class="info-value">${this.getRelativeTime(camera.lastSeen)}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="camera-card-actions">
                    <button class="btn btn-secondary btn-small" title="Edit Camera" data-action="edit" data-camera-id="${camera.id}">
                        <i class="fas fa-edit"></i>
                        Configure
                    </button>
                    <button class="btn btn-secondary btn-small" title="View Live" data-action="live" data-camera-id="${camera.id}" ${camera.status !== 'online' ? 'disabled' : ''}>
                        <i class="fas fa-eye"></i>
                        View Live
                    </button>
                    <div class="action-dropdown">
                        <button class="btn btn-secondary btn-small dropdown-toggle" data-camera-id="${camera.id}">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <div class="dropdown-menu">
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
                            <button class="dropdown-item danger" data-action="delete" data-camera-id="${camera.id}">
                                <i class="fas fa-trash"></i>
                                Delete Camera
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

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
                        <span class="camera-name">${camera.name}</span>
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
        document.querySelectorAll('.action-btn[data-action], .dropdown-item[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleCameraAction(e));
        });

        // Preview buttons
        document.querySelectorAll('.preview-play-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.showCameraPreview(e.target.dataset.cameraId));
        });

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
                this.showCameraPreview(cameraId);
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
            console.log('Edit camera:', camera);
            // This would open the camera edit modal
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
            // Simulate connection test
            await this.performConnectionTest(camera);
            this.showToast(`Connection test successful for ${camera.name}`, 'success');
        } catch (error) {
            this.showToast(`Connection test failed for ${camera.name}`, 'error');
        } finally {
            testBtn.innerHTML = originalContent;
            testBtn.disabled = false;
        }
    }

    showCameraDetails(cameraId) {
        const camera = this.cameras.find(c => c.id === cameraId);
        if (camera) {
            // Show camera details modal
            console.log('Show camera details:', camera);
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
                // Simulate API call
                await this.performDeleteCamera(cameraId);
                this.cameras = this.cameras.filter(c => c.id !== cameraId);
                this.applyFilters();
                this.showToast(`Camera "${camera.name}" deleted successfully`, 'success');
            } catch (error) {
                this.showToast(`Failed to delete camera "${camera.name}"`, 'error');
            }
        }
    }

    // Utility methods
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

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    calculateHealthScore(camera) {
        let score = 100;
        
        // Status impact
        if (camera.status === 'offline') {
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

    showToast(message, type = 'info') {
        // Create and show toast notification
        console.log(`Toast ${type}: ${message}`);
    }

    async performConnectionTest(camera) {
        return new Promise(resolve => setTimeout(resolve, 1500));
    }

    async performDeleteCamera(cameraId) {
        return new Promise(resolve => setTimeout(resolve, 500));
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
        // This would trigger the camera setup wizard
        console.log('Show add camera modal');
    }

    showCameraPreview(cameraId) {
        // Show live preview modal
        console.log('Show camera preview for:', cameraId);
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
}

export default Cameras;