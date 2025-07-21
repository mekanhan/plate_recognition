/**
 * Modern IP Camera Modal
 * Industry-standard implementation with validation, auto-discovery, and accessibility
 */

class IPCameraModal {
    constructor() {
        this.isTestingConnection = false;
        this.isDiscovering = false;
        this.connectionTest = null;
        this.manufacturers = [];
        this.locations = [];
        this.validationRules = {
            name: { required: true, minLength: 1, maxLength: 100 },
            ip_address: { required: true, pattern: /^(\d{1,3}\.){3}\d{1,3}$/ },
            location: { required: true }
        };
        
        this.init();
    }

    async init() {
        await this.loadManufacturers();
        await this.loadLocations();
        this.setupEventListeners();
        this.initializeDefaults();
    }

    async loadManufacturers() {
        try {
            const response = await fetch('/api/cameras/manufacturers');
            if (response.ok) {
                this.manufacturers = await response.json();
                this.populateManufacturerSuggestions();
            }
        } catch (error) {
            console.error('Failed to load manufacturers:', error);
            this.manufacturers = this.getFallbackManufacturers();
        }
    }

    async loadLocations() {
        try {
            const response = await fetch('/api/locations');
            if (response.ok) {
                this.locations = await response.json();
                this.populateLocationDropdown();
            }
        } catch (error) {
            console.error('Failed to load locations:', error);
            this.locations = this.getFallbackLocations();
            this.populateLocationDropdown();
        }
    }

    getFallbackManufacturers() {
        return [
            { key: 'reolink', name: 'Reolink', stream_paths: ['/h264Preview_01_main', '/h264Preview_01_sub'] },
            { key: 'hikvision', name: 'Hikvision', stream_paths: ['/Streaming/Channels/101', '/Streaming/Channels/102'] },
            { key: 'dahua', name: 'Dahua', stream_paths: ['/cam/realmonitor?channel=1&subtype=0', '/cam/realmonitor?channel=1&subtype=1'] },
            { key: 'axis', name: 'Axis', stream_paths: ['/axis-media/media.amp?videocodec=h264', '/mjpg/video.mjpg'] },
            { key: 'generic', name: 'Generic', stream_paths: ['/stream', '/live', '/video'] }
        ];
    }

    getFallbackLocations() {
        return [
            { id: 'main_entrance', name: 'Main Entrance' },
            { id: 'parking_lot', name: 'Parking Lot' },
            { id: 'exit_gate', name: 'Exit Gate' },
            { id: 'loading_dock', name: 'Loading Dock' },
            { id: 'security_office', name: 'Security Office' }
        ];
    }

    populateManufacturerSuggestions() {
        const datalist = document.getElementById('manufacturerSuggestions');
        if (!datalist) return;

        datalist.innerHTML = this.manufacturers.map(manufacturer => 
            `<option value="${manufacturer.name}">`
        ).join('');
    }

    populateLocationDropdown() {
        const select = document.getElementById('location');
        if (!select) return;

        const defaultOption = select.querySelector('option[value=""]');
        select.innerHTML = '';
        select.appendChild(defaultOption);

        this.locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location.id;
            option.textContent = location.name;
            select.appendChild(option);
        });
    }

    setupEventListeners() {
        // Form validation
        ['cameraName', 'ipAddress', 'location'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', this.validateForm.bind(this));
                element.addEventListener('blur', this.validateField.bind(this, id));
            }
        });

        // Real-time IP validation
        const ipInput = document.getElementById('ipAddress');
        if (ipInput) {
            ipInput.addEventListener('input', this.validateIPAddress.bind(this));
        }

        // Auto-update port when connection type changes
        const connectionType = document.getElementById('connectionType');
        if (connectionType) {
            connectionType.addEventListener('change', this.updateDefaultPort.bind(this));
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });

        // Modal overlay click to close
        const modalOverlay = document.getElementById('ipCameraModal');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.closeModal();
                }
            });
        }
    }

    initializeDefaults() {
        // Set default values
        const elements = {
            port: '554',
            username: 'admin',
            connectionType: 'rtsp'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.value = value;
            }
        });
    }

    validateField(fieldId) {
        const element = document.getElementById(fieldId);
        const errorElement = document.getElementById(`${fieldId}Error`);
        
        if (!element || !errorElement) return true;

        const value = element.value.trim();
        const rule = this.validationRules[fieldId];
        
        if (!rule) return true;

        // Required field validation
        if (rule.required && !value) {
            this.showFieldError(element, errorElement, 'This field is required');
            return false;
        }

        // Pattern validation
        if (rule.pattern && value && !rule.pattern.test(value)) {
            this.showFieldError(element, errorElement, 'Please enter a valid format');
            return false;
        }

        // Length validation
        if (rule.minLength && value.length < rule.minLength) {
            this.showFieldError(element, errorElement, `Minimum length is ${rule.minLength}`);
            return false;
        }

        if (rule.maxLength && value.length > rule.maxLength) {
            this.showFieldError(element, errorElement, `Maximum length is ${rule.maxLength}`);
            return false;
        }

        // IP address specific validation
        if (fieldId === 'ipAddress' && value) {
            const octets = value.split('.');
            const isValidRange = octets.every(octet => {
                const num = parseInt(octet, 10);
                return num >= 0 && num <= 255;
            });

            if (!isValidRange) {
                this.showFieldError(element, errorElement, 'IP address octets must be between 0 and 255');
                return false;
            }
        }

        this.clearFieldError(element, errorElement);
        return true;
    }

    showFieldError(element, errorElement, message) {
        element.classList.add('error');
        element.classList.remove('success');
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

    clearFieldError(element, errorElement) {
        element.classList.remove('error');
        element.classList.add('success');
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }

    validateIPAddress() {
        const ipInput = document.getElementById('ipAddress');
        const errorDiv = document.getElementById('ipAddressError');
        
        if (!ipInput || !errorDiv) return;

        const ip = ipInput.value.trim();
        
        if (!ip) {
            ipInput.classList.remove('error', 'success');
            errorDiv.textContent = '';
            this.validateForm();
            return;
        }

        if (this.validateField('ipAddress')) {
            this.validateForm();
        }
    }

    updateDefaultPort() {
        const connectionType = document.getElementById('connectionType');
        const portInput = document.getElementById('port');
        
        if (!connectionType || !portInput) return;

        const defaultPorts = {
            rtsp: 554,
            http: 80,
            https: 443,
            onvif: 80
        };

        portInput.value = defaultPorts[connectionType.value] || 554;
        
        // Update stream path suggestions based on connection type
        this.updateStreamPathSuggestions();
    }

    updateStreamPathSuggestions() {
        const connectionType = document.getElementById('connectionType');
        const datalist = document.getElementById('streamPathSuggestions');
        
        if (!connectionType || !datalist) return;

        const suggestions = {
            rtsp: ['/stream', '/live', '/h264Preview_01_main', '/Streaming/Channels/101', '/cam/realmonitor?channel=1&subtype=0'],
            http: ['/video', '/mjpg/video.mjpg', '/snapshot.jpg', '/axis-media/media.amp'],
            https: ['/video', '/mjpg/video.mjpg', '/snapshot.jpg', '/axis-media/media.amp'],
            onvif: ['/onvif/media_service/stream_uri', '/onvif/device_service']
        };

        datalist.innerHTML = (suggestions[connectionType.value] || suggestions.rtsp)
            .map(path => `<option value="${path}">`)
            .join('');
    }

    validateForm() {
        const fields = ['cameraName', 'ipAddress', 'location'];
        const isValid = fields.every(fieldId => this.validateField(fieldId));
        
        const saveBtn = document.getElementById('saveBtn');
        if (saveBtn) {
            saveBtn.disabled = !isValid;
        }

        return isValid;
    }

    async discoverCameras() {
        if (this.isDiscovering) return;

        this.isDiscovering = true;
        this.updateDiscoveryUI(true);

        try {
            const response = await fetch('/api/cameras/scan-network', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip_range: this.getNetworkRange(),
                    timeout: 3,
                    ports: [80, 554, 8000, 8080, 443]
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.displayDiscoveredCameras(data.cameras || []);
            } else {
                throw new Error('Discovery failed');
            }
        } catch (error) {
            console.error('Discovery error:', error);
            this.showStatus('error', 'Camera discovery failed. Please check your network connection.');
        } finally {
            this.isDiscovering = false;
            this.updateDiscoveryUI(false);
        }
    }

    getNetworkRange() {
        // Try to get network range from current IP or default to common range
        const ipInput = document.getElementById('ipAddress');
        const ip = ipInput ? ipInput.value.trim() : '';
        
        if (ip && this.isValidIP(ip)) {
            const parts = ip.split('.');
            return `${parts[0]}.${parts[1]}.${parts[2]}.0/24`;
        }
        
        return '192.168.1.0/24';
    }

    updateDiscoveryUI(isDiscovering) {
        const discoverBtn = document.getElementById('discoverBtn');
        const discoverText = document.getElementById('discoverText');
        const discoverSpinner = document.getElementById('discoverSpinner');

        if (!discoverBtn || !discoverText || !discoverSpinner) return;

        if (isDiscovering) {
            discoverBtn.disabled = true;
            discoverText.textContent = 'Discovering...';
            discoverSpinner.style.display = 'inline-block';
        } else {
            discoverBtn.disabled = false;
            discoverText.textContent = 'Discover Cameras';
            discoverSpinner.style.display = 'none';
        }
    }

    displayDiscoveredCameras(cameras) {
        const container = document.getElementById('discoveredCameras');
        if (!container) return;

        if (cameras.length === 0) {
            container.innerHTML = '<p class="helper-text">No cameras found on the network</p>';
            container.classList.add('show');
            return;
        }

        const cameraElements = cameras.map((camera, index) => `
            <div class="discovered-camera" data-index="${index}" onclick="window.ipCameraModal.selectDiscoveredCamera(${index})">
                <div style="font-weight: 500; margin-bottom: 4px;">${camera.ip_address}</div>
                <div style="font-size: 12px; color: var(--gray-600);">
                    ${camera.manufacturer || 'Unknown'} • ${camera.protocols?.join(', ') || 'Unknown protocols'}
                </div>
                <div style="font-size: 11px; color: var(--gray-500); margin-top: 2px;">
                    Confidence: ${Math.round((camera.confidence || 0.5) * 100)}%
                </div>
            </div>
        `).join('');

        container.innerHTML = cameraElements;
        container.classList.add('show');
        
        // Store discovered cameras for selection
        this.discoveredCameras = cameras;
    }

    selectDiscoveredCamera(index) {
        const camera = this.discoveredCameras[index];
        if (!camera) return;

        // Clear previous selections
        document.querySelectorAll('.discovered-camera').forEach(cam => {
            cam.classList.remove('selected');
        });

        // Select current camera
        document.querySelector(`[data-index="${index}"]`).classList.add('selected');

        // Fill form with discovered camera data
        document.getElementById('ipAddress').value = camera.ip_address;
        document.getElementById('cameraName').value = `${camera.manufacturer || 'IP'} Camera`;

        // Update port based on detected protocols
        if (camera.protocols && camera.protocols.includes('RTSP')) {
            document.getElementById('connectionType').value = 'rtsp';
        } else if (camera.protocols && camera.protocols.includes('HTTP')) {
            document.getElementById('connectionType').value = 'http';
        }

        // Update port and stream path suggestions
        this.updateDefaultPort();

        // Clear previous validation states
        this.clearAllValidationErrors();

        // Validate form
        this.validateForm();
    }

    clearAllValidationErrors() {
        document.querySelectorAll('.form-input').forEach(input => {
            input.classList.remove('error', 'success');
        });

        document.querySelectorAll('.error-text').forEach(error => {
            error.textContent = '';
            error.style.display = 'none';
        });
    }

    async testConnection() {
        if (this.isTestingConnection) return;

        if (!this.validateForm()) {
            this.showStatus('error', 'Please fill in all required fields correctly.');
            return;
        }

        this.isTestingConnection = true;
        this.updateTestUI(true);
        this.showStatus('testing', 'Testing connection...');

        try {
            const connectionData = {
                ip_address: document.getElementById('ipAddress').value.trim(),
                port: document.getElementById('port').value.trim() || "554",
                connection_type: document.getElementById('connectionType').value,
                stream_path: document.getElementById('streamPath').value.trim(),
                username: document.getElementById('username').value.trim(),
                password: document.getElementById('password').value
            };

            const response = await fetch('/api/cameras/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(connectionData)
            });

            if (response.ok) {
                const result = await response.json();

                if (result.success) {
                    this.showStatus('success', result.detail || 'Connection successful! Camera is accessible.');
                    this.connectionTest = result;
                } else {
                    this.showStatus('error', result.detail || 'Connection failed. Please check your settings.');
                }
            } else {
                throw new Error('Connection test failed');
            }
        } catch (error) {
            console.error('Connection test error:', error);
            this.showStatus('error', 'Connection test failed. Please check your network and camera settings.');
        } finally {
            this.isTestingConnection = false;
            this.updateTestUI(false);
        }
    }

    updateTestUI(isTesting) {
        const testBtn = document.getElementById('testBtn');
        const testText = document.getElementById('testText');
        const testSpinner = document.getElementById('testSpinner');

        if (!testBtn || !testText || !testSpinner) return;

        if (isTesting) {
            testBtn.disabled = true;
            testText.textContent = 'Testing...';
            testSpinner.style.display = 'inline-block';
        } else {
            testBtn.disabled = false;
            testText.textContent = 'Test Connection';
            testSpinner.style.display = 'none';
        }
    }

    updateFormWithTestResults(result) {
        // Update stream path if empty and suggestions are available
        const streamPathInput = document.getElementById('streamPath');
        if (streamPathInput && !streamPathInput.value.trim() && result.suggested_streams) {
            const suggestions = result.suggested_streams;
            if (suggestions.length > 0) {
                streamPathInput.value = suggestions[0].path;
            }
        }
    }

    showStatus(type, message) {
        const statusDiv = document.getElementById('connectionStatus');
        if (!statusDiv) return;

        statusDiv.className = `connection-status show ${type}`;
        statusDiv.textContent = message;
    }

    async saveCamera() {
        if (!this.validateForm()) {
            this.showStatus('error', 'Please fill in all required fields correctly.');
            return;
        }

        const saveBtn = document.getElementById('saveBtn');
        if (!saveBtn) return;

        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
            const cameraData = {
                name: document.getElementById('cameraName').value.trim(),
                ip_address: document.getElementById('ipAddress').value.trim(),
                location_id: document.getElementById('location').value,
                connection_type: document.getElementById('connectionType').value,
                port: parseInt(document.getElementById('port').value) || 554,
                stream_path: document.getElementById('streamPath').value.trim(),
                username: document.getElementById('username').value.trim(),
                password: document.getElementById('password').value,
                camera_type: 'ip_camera',
                manufacturer: 'generic',
                model: 'generic',
                resolution_width: 1920,
                resolution_height: 1080,
                fps: 30
            };

            const response = await fetch('/api/cameras/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(cameraData)
            });

            if (response.ok) {
                const result = await response.json();
                this.showStatus('success', 'Camera added successfully!');

                // Close modal after 1 second
                setTimeout(() => {
                    this.closeModal();
                    // Refresh cameras list if callback exists
                    if (window.refreshCamerasList) {
                        window.refreshCamerasList();
                    }
                    // Dispatch custom event for other components
                    window.dispatchEvent(new CustomEvent('cameraAdded', { detail: result }));
                }, 1000);
            } else {
                const error = await response.json();
                if (response.status === 409) {
                    this.showStatus('error', 'A camera with this IP address already exists.');
                } else {
                    throw new Error(error.detail || 'Failed to add camera');
                }
            }
        } catch (error) {
            console.error('Save camera error:', error);
            this.showStatus('error', error.message || 'Failed to add camera. Please try again.');
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Add Camera';
        }
    }

    closeModal() {
        const modal = document.getElementById('ipCameraModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.resetForm();
    }

    showModal() {
        const modal = document.getElementById('ipCameraModal');
        if (modal) {
            modal.style.display = 'flex';
            // Focus on first input for accessibility
            const firstInput = document.getElementById('cameraName');
            if (firstInput) {
                firstInput.focus();
            }
        }
    }

    resetForm() {
        const form = document.getElementById('cameraForm');
        if (form) {
            form.reset();
        }

        // Restore defaults
        this.initializeDefaults();

        // Clear validation states
        this.clearAllValidationErrors();

        // Hide status and discovered cameras
        const statusDiv = document.getElementById('connectionStatus');
        if (statusDiv) {
            statusDiv.classList.remove('show');
        }

        const discoveredDiv = document.getElementById('discoveredCameras');
        if (discoveredDiv) {
            discoveredDiv.classList.remove('show');
        }

        // Reset button states
        const saveBtn = document.getElementById('saveBtn');
        if (saveBtn) {
            saveBtn.disabled = true;
        }

        // Reset state
        this.isTestingConnection = false;
        this.isDiscovering = false;
        this.connectionTest = null;
        this.discoveredCameras = [];
    }

    isValidIP(ip) {
        const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (!ipPattern.test(ip)) return false;

        const octets = ip.split('.');
        return octets.every(octet => {
            const num = parseInt(octet, 10);
            return num >= 0 && num <= 255;
        });
    }
}

// Initialize modal when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.ipCameraModal = new IPCameraModal();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IPCameraModal;
}