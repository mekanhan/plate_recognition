class ONVIFDiscoveryModal {
    constructor() {
        this.isVisible = false;
        this.discoveredCameras = [];
        this.selectedCameras = new Set();
        this.isDiscovering = false;
        this.discoveryMethod = 'both';
        this.customSubnet = '';
        this.init();
    }

    init() {
        this.createModal();
        this.attachEventListeners();
    }

    createModal() {
        const modalHTML = `
            <div class="modal" id="onvif-discovery-modal">
                <div class="modal-overlay"></div>
                <div class="modal-content modal-large">
                    <div class="modal-header">
                        <h2>
                            <i class="fas fa-search"></i>
                            Discover ONVIF Cameras
                        </h2>
                        <button class="modal-close" id="onvif-modal-close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>

                    <div class="modal-body">
                        <!-- Discovery Options -->
                        <div class="discovery-options">
                            <div class="option-group">
                                <label>Discovery Method:</label>
                                <select id="discovery-method" class="form-select">
                                    <option value="both">Both (Recommended)</option>
                                    <option value="multicast">Multicast Only (Fast)</option>
                                    <option value="unicast">Network Scan (Thorough)</option>
                                </select>
                            </div>

                            <div class="option-group">
                                <label>Custom Subnet (Optional):</label>
                                <input type="text" id="custom-subnet" class="form-input" placeholder="e.g., 192.168.1.0/24">
                                <small class="help-text">Leave empty to use local subnet</small>
                            </div>

                            <div class="option-group">
                                <label>ONVIF Credentials (Optional - for camera details):</label>
                                <div class="credentials-row" style="display:flex;gap:8px;">
                                    <input type="text" id="onvif-username-bulk" class="form-input" placeholder="Username" style="flex:1;">
                                    <input type="password" id="onvif-password-bulk" class="form-input" placeholder="Password" style="flex:1;">
                                </div>
                                <small class="help-text">
                                    <i class="fas fa-info-circle"></i>
                                    Provide credentials to see camera manufacturer, model, and other details
                                </small>
                            </div>

                            <button id="start-discovery" class="btn btn-primary">
                                <i class="fas fa-search"></i>
                                Start Discovery
                            </button>
                        </div>

                        <!-- Discovery Progress -->
                        <div id="discovery-progress" class="discovery-progress" style="display:none;">
                            <div class="progress-spinner">
                                <i class="fas fa-spinner fa-spin"></i>
                            </div>
                            <p>Discovering cameras on the network...</p>
                            <small>This may take up to 30 seconds</small>
                        </div>

                        <!-- Discovered Cameras List -->
                        <div id="discovered-cameras" class="discovered-cameras" style="display:none;">
                            <div class="cameras-header">
                                <h3>Discovered Cameras</h3>
                                <button id="select-all-cameras" class="btn btn-sm">
                                    <i class="fas fa-check-square"></i>
                                    Select All
                                </button>
                            </div>

                            <div id="cameras-list" class="cameras-list">
                                <!-- Cameras will be populated here -->
                            </div>

                            <div class="bulk-actions">
                                <button id="add-selected-cameras" class="btn btn-success" disabled>
                                    <i class="fas fa-plus"></i>
                                    Add Selected Cameras
                                </button>
                            </div>
                        </div>

                        <!-- No Cameras Found Message -->
                        <div id="no-cameras-message" class="no-cameras-message" style="display:none;">
                            <i class="fas fa-exclamation-circle"></i>
                            <h3>No ONVIF Cameras Found</h3>
                            <p>Possible reasons:</p>
                            <ul>
                                <li>Cameras are not ONVIF compliant</li>
                                <li>Cameras are on a different network segment</li>
                                <li>Firewall is blocking UDP port 3702</li>
                                <li>ONVIF is disabled on the cameras</li>
                            </ul>
                            <button id="retry-discovery" class="btn btn-primary">
                                <i class="fas fa-redo"></i>
                                Try Again
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (!document.getElementById('onvif-discovery-modal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }

        this.addStyles();
    }

    addStyles() {
        const styleId = 'onvif-discovery-modal-styles';
        if (document.getElementById(styleId)) return;

        const styles = `
            <style id="${styleId}">
            #onvif-discovery-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10000;
                display: none;
                align-items: center;
                justify-content: center;
            }

            #onvif-discovery-modal.show {
                display: flex;
            }

            #onvif-discovery-modal .modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
            }

            #onvif-discovery-modal .modal-content {
                position: relative;
                z-index: 10001;
            }

            .modal-large {
                max-width: 800px;
                width: 90%;
            }

            .discovery-options {
                background: var(--bg-secondary);
                padding: var(--spacing-lg);
                border-radius: var(--radius-lg);
                margin-bottom: var(--spacing-xl);
            }

            .option-group {
                margin-bottom: var(--spacing-md);
            }

            .option-group label {
                display: block;
                margin-bottom: var(--spacing-sm);
                font-weight: 600;
            }

            .discovery-progress {
                text-align: center;
                padding: var(--spacing-xl);
            }

            .progress-spinner {
                font-size: 3rem;
                color: var(--primary-color);
                margin-bottom: var(--spacing-lg);
            }

            .discovered-cameras {
                margin-top: var(--spacing-lg);
            }

            .cameras-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: var(--spacing-lg);
            }

            .cameras-list {
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: var(--spacing-md);
            }

            .camera-item {
                display: flex;
                align-items: center;
                padding: var(--spacing-md);
                margin-bottom: var(--spacing-sm);
                background: var(--bg-secondary);
                border-radius: var(--radius-md);
                transition: all var(--transition-fast);
            }

            .camera-item:hover {
                background: var(--bg-hover);
            }

            .camera-item.selected {
                background: var(--primary-color-light);
                border: 2px solid var(--primary-color);
            }

            .camera-checkbox {
                margin-right: var(--spacing-md);
            }

            .camera-info {
                flex: 1;
            }

            .camera-name {
                font-weight: 600;
                margin-bottom: var(--spacing-xs);
            }

            .camera-details {
                font-size: var(--font-size-sm);
                color: var(--text-secondary);
            }

            .camera-credentials {
                display: flex;
                gap: var(--spacing-sm);
                margin-left: auto;
            }

            .camera-credentials input {
                width: 120px;
            }

            .bulk-actions {
                margin-top: var(--spacing-lg);
                text-align: right;
            }

            .no-cameras-message {
                text-align: center;
                padding: var(--spacing-xl);
                color: var(--text-secondary);
            }

            .no-cameras-message i {
                font-size: 3rem;
                color: var(--warning-color);
                margin-bottom: var(--spacing-md);
            }

            .no-cameras-message ul {
                text-align: left;
                max-width: 400px;
                margin: var(--spacing-lg) auto;
            }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    attachEventListeners() {
        document.getElementById('onvif-modal-close')?.addEventListener('click', () => this.hide());
        document.querySelector('#onvif-discovery-modal .modal-overlay')?.addEventListener('click', () => this.hide());
        document.getElementById('start-discovery')?.addEventListener('click', () => this.startDiscovery());
        document.getElementById('retry-discovery')?.addEventListener('click', () => this.startDiscovery());
        document.getElementById('select-all-cameras')?.addEventListener('click', () => this.toggleSelectAll());
        document.getElementById('add-selected-cameras')?.addEventListener('click', () => this.addSelectedCameras());

        document.getElementById('discovery-method')?.addEventListener('change', (e) => {
            this.discoveryMethod = e.target.value;
        });

        document.getElementById('custom-subnet')?.addEventListener('input', (e) => {
            this.customSubnet = e.target.value;
        });
    }

    show() {
        const modal = document.getElementById('onvif-discovery-modal');
        if (modal) {
            modal.classList.add('show');
            this.isVisible = true;
            this.resetModal();
        }
    }

    hide() {
        const modal = document.getElementById('onvif-discovery-modal');
        if (modal) {
            modal.classList.remove('show');
            this.isVisible = false;
        }
    }

    resetModal() {
        document.getElementById('discovery-progress').style.display = 'none';
        document.getElementById('discovered-cameras').style.display = 'none';
        document.getElementById('no-cameras-message').style.display = 'none';
        
        this.discoveredCameras = [];
        this.selectedCameras.clear();
        
        document.getElementById('discovery-method').value = 'both';
        document.getElementById('custom-subnet').value = '';
        document.getElementById('start-discovery').disabled = false;
    }

    async startDiscovery() {
        if (this.isDiscovering) return;

        this.isDiscovering = true;
        document.getElementById('discovery-progress').style.display = 'block';
        document.getElementById('discovered-cameras').style.display = 'none';
        document.getElementById('no-cameras-message').style.display = 'none';
        document.getElementById('start-discovery').disabled = true;

        try {
            const onvifUsername = document.getElementById('onvif-username-bulk')?.value?.trim() || '';
            const onvifPassword = document.getElementById('onvif-password-bulk')?.value || '';
            const customSubnet = document.getElementById('custom-subnet')?.value?.trim() || '';

            let url = `/api/onvif/discover?method=${this.discoveryMethod}`;
            
            if (customSubnet) {
                url += `&subnets=${encodeURIComponent(customSubnet)}`;
            }
            
            if (onvifUsername || onvifPassword) {
                url += `&username=${encodeURIComponent(onvifUsername)}&password=${encodeURIComponent(onvifPassword)}`;
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success && result.cameras && result.cameras.length > 0) {
                this.discoveredCameras = result.cameras;
                this.displayDiscoveredCameras();
            } else {
                this.showNoCamerasMessage();
            }
        } catch (error) {
            console.error('Discovery failed:', error);
            this.showError('Discovery failed. Please check your network connection.');
        } finally {
            this.isDiscovering = false;
            document.getElementById('discovery-progress').style.display = 'none';
            document.getElementById('start-discovery').disabled = false;
        }
    }

    displayDiscoveredCameras() {
        const camerasList = document.getElementById('cameras-list');
        const discoveredSection = document.getElementById('discovered-cameras');

        camerasList.innerHTML = '';

        this.discoveredCameras.forEach((camera, index) => {
            const cameraHTML = `
                <div class="camera-item" data-camera-index="${index}">
                    <input type="checkbox" class="camera-checkbox" id="camera-${index}" data-camera-ip="${camera.ip_address}">
                    <div class="camera-info">
                        <div class="camera-name">${camera.name}</div>
                        <div class="camera-details">
                            IP: ${camera.ip_address} | ${camera.manufacturer || 'Unknown'} ${camera.model || ''} | Brand: ${camera.detected_brand || 'Generic'}
                        </div>
                    </div>
                    <div class="camera-credentials">
                        <input type="text" class="form-input" placeholder="Username" id="username-${index}" value="${camera.username || 'admin'}">
                        <input type="password" class="form-input" placeholder="Password" id="password-${index}">
                    </div>
                </div>
            `;
            camerasList.insertAdjacentHTML('beforeend', cameraHTML);
        });

        camerasList.querySelectorAll('.camera-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleCameraSelection(e));
        });

        discoveredSection.style.display = 'block';
    }

    handleCameraSelection(event) {
        const checkbox = event.target;
        const cameraIp = checkbox.dataset.cameraIp;
        const cameraItem = checkbox.closest('.camera-item');

        if (checkbox.checked) {
            this.selectedCameras.add(cameraIp);
            cameraItem.classList.add('selected');
        } else {
            this.selectedCameras.delete(cameraIp);
            cameraItem.classList.remove('selected');
        }

        const addButton = document.getElementById('add-selected-cameras');
        addButton.disabled = this.selectedCameras.size === 0;
    }

    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.camera-checkbox');
        const allSelected = this.selectedCameras.size === this.discoveredCameras.length;

        checkboxes.forEach(checkbox => {
            checkbox.checked = !allSelected;
            const event = new Event('change');
            checkbox.dispatchEvent(event);
        });
    }

    async addSelectedCameras() {
        if (this.selectedCameras.size === 0) return;

        const addButton = document.getElementById('add-selected-cameras');
        addButton.disabled = true;
        addButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding Cameras...';

        const results = [];

        for (const cameraIp of this.selectedCameras) {
            const index = this.discoveredCameras.findIndex(cam => cam.ip_address === cameraIp);
            if (index === -1) continue;

            const camera = this.discoveredCameras[index];
            const username = document.getElementById(`username-${index}`).value;
            const password = document.getElementById(`password-${index}`).value;

            try {
                const response = await fetch(`/api/onvif/add/${cameraIp}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });

                const result = await response.json();
                results.push({
                    camera: camera.name,
                    success: result.success,
                    message: result.message || result.error
                });
            } catch (error) {
                results.push({
                    camera: camera.name,
                    success: false,
                    message: error.message
                });
            }
        }

        this.showAddResults(results);

        addButton.disabled = false;
        addButton.innerHTML = '<i class="fas fa-plus"></i> Add Selected Cameras';

        if (results.some(r => r.success)) {
            window.dispatchEvent(new CustomEvent('camerasAdded'));
            setTimeout(() => this.hide(), 2000);
        }
    }

    showAddResults(results) {
        const successCount = results.filter(r => r.success).length;
        const failCount = results.filter(r => !r.success).length;

        let message = `Added ${successCount} camera(s) successfully.`;
        if (failCount > 0) {
            message += ` ${failCount} camera(s) failed.`;
        }

        this.showToast(message, successCount > 0 ? 'success' : 'error');

        results.forEach(result => {
            console.log(`${result.camera}: ${result.success ? '✅' : '❌'} ${result.message}`);
        });
    }

    showNoCamerasMessage() {
        document.getElementById('no-cameras-message').style.display = 'block';
        document.getElementById('discovered-cameras').style.display = 'none';
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        if (window.lprApp && window.lprApp.showToast) {
            window.lprApp.showToast(message, type);
        } else {
            alert(message);
        }
    }
}

export default ONVIFDiscoveryModal;