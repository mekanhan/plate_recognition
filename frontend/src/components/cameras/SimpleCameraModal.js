/**
 * Simple Camera Test Modal
 * Basic IP camera connection testing modal
 */
class SimpleCameraModal {
    constructor() {
        this.isVisible = false;
        this.editMode = false;
        this.editingCameraId = null;
        this.formData = {
            name: '',
            ip_address: '',
            connection_type: 'http',
            port: 80,
            stream_path: '/mjpeg',
            location: '',
            username: 'admin',
            password: ''
        };
        this.testResult = null;
    }

    show(camera = null) {
        if (this.isVisible) return;
        
        this.isVisible = true;
        this.editMode = !!camera;
        this.editingCameraId = camera?.id || null;
        
        if (camera) {
            this.loadCameraData(camera);
        } else {
            this.resetForm();
        }
        
        this.render();
        this.attachEventListeners();
        
        const modal = document.getElementById('simple-camera-modal');
        if (modal) {
            modal.style.display = 'flex';
            // Force reflow before adding show class for proper animation
            modal.offsetHeight;
            setTimeout(() => modal.classList.add('show'), 10);
        }
    }

    hide() {
        if (!this.isVisible) return;
        
        const modal = document.getElementById('simple-camera-modal');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
                this.cleanup();
            }, 300);
        }
        this.isVisible = false;
    }

    render() {
        let modal = document.getElementById('simple-camera-modal');
        if (!modal) {
            modal = this.createModalElement();
            document.body.appendChild(modal);
        }
        
        modal.innerHTML = this.getTemplate();
    }

    createModalElement() {
        const modal = document.createElement('div');
        modal.id = 'simple-camera-modal';
        modal.className = 'modal-overlay simple-camera-modal';
        return modal;
    }

    getTemplate() {
        return `
            <div class="modal-container">
                <div class="modal-header">
                    <h3>
                        <i class="fas fa-video"></i>
                        ${this.editMode ? 'Edit Camera' : 'Add IP Camera'}
                    </h3>
                    <button class="modal-close" id="close-simple-camera">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="modal-content">
                    <form id="camera-test-form" class="camera-form">
                        <div class="form-group">
                            <label for="camera-name-input" class="required">Camera Name</label>
                            <input type="text" id="camera-name-input" class="form-input" 
                                   placeholder="e.g., Entrance Camera" 
                                   value="${this.formData.name}" required>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="camera-ip-input" class="required">IP Address</label>
                                <input type="text" id="camera-ip-input" class="form-input" 
                                       placeholder="192.168.1.100" 
                                       value="${this.formData.ip_address}" 
                                       pattern="^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="connection-type-input" class="required">Connection Type</label>
                                <select id="connection-type-input" class="form-select" required>
                                    <option value="http" ${this.formData.connection_type === 'http' ? 'selected' : ''}>HTTP</option>
                                    <option value="https" ${this.formData.connection_type === 'https' ? 'selected' : ''}>HTTPS</option>
                                    <option value="rtsp" ${this.formData.connection_type === 'rtsp' ? 'selected' : ''}>RTSP</option>
                                    <option value="rtsps" ${this.formData.connection_type === 'rtsps' ? 'selected' : ''}>RTSPS (Secure)</option>
                                    <option value="onvif" ${this.formData.connection_type === 'onvif' ? 'selected' : ''}>ONVIF</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="camera-port-input" class="required">Port</label>
                                <input type="number" id="camera-port-input" class="form-input" 
                                       value="${this.formData.port}" min="1" max="65535" required>
                                <small class="form-help">Default ports: HTTP(80), HTTPS(443), RTSP(554), ONVIF(80)</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="stream-path-input">Stream Path</label>
                                <input type="text" id="stream-path-input" class="form-input" 
                                       placeholder="/mjpeg" 
                                       value="${this.formData.stream_path}">
                                <small class="form-help">URL path to video stream (e.g., /mjpeg, /stream1)</small>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="camera-location-input" class="required">Location</label>
                            <select id="camera-location-input" class="form-select" required>
                                <option value="">Select Location</option>
                                <option value="entrance" ${this.formData.location === 'entrance' ? 'selected' : ''}>Entrance</option>
                                <option value="parking" ${this.formData.location === 'parking' ? 'selected' : ''}>Parking</option>
                                <option value="exit" ${this.formData.location === 'exit' ? 'selected' : ''}>Exit</option>
                                <option value="loading" ${this.formData.location === 'loading' ? 'selected' : ''}>Loading Dock</option>
                            </select>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="camera-username-input">Username</label>
                                <input type="text" id="camera-username-input" class="form-input" 
                                       placeholder="admin" 
                                       value="${this.formData.username}">
                            </div>
                            
                            <div class="form-group">
                                <label for="camera-password-input">Password</label>
                                <div class="password-input">
                                    <input type="password" id="camera-password-input" class="form-input" 
                                           placeholder="Enter password" 
                                           value="${this.formData.password}">
                                    <button type="button" class="password-toggle" id="password-toggle-btn">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="test-section">
                            <button type="button" class="btn btn-secondary" id="test-connection-btn">
                                <i class="fas fa-plug"></i>
                                Test Connection
                            </button>
                            <div class="test-result" id="test-result">
                                ${this.getTestResultHTML()}
                            </div>
                        </div>
                    </form>
                </div>
                
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" id="cancel-camera-btn">Cancel</button>
                    <button type="button" class="btn btn-primary" id="save-camera-btn" 
                            ${this.isFormValid() ? '' : 'disabled'}>
                        <i class="fas fa-save"></i>
                        ${this.editMode ? 'Update Camera' : 'Add Camera'}
                    </button>
                </div>
            </div>
        `;
    }

    getTestResultHTML() {
        if (!this.testResult) return '';
        
        const iconClass = this.testResult.success ? 'fa-check-circle' : 'fa-times-circle';
        const statusClass = this.testResult.success ? 'success' : 'error';
        
        return `
            <div class="result-status ${statusClass}">
                <i class="fas ${iconClass}"></i>
                <span>${this.testResult.message}</span>
                ${this.testResult.response_time ? `<small>Response: ${this.testResult.response_time}ms</small>` : ''}
            </div>
        `;
    }

    attachEventListeners() {
        // Modal controls
        document.getElementById('close-simple-camera')?.addEventListener('click', () => this.hide());
        document.getElementById('cancel-camera-btn')?.addEventListener('click', () => this.hide());
        document.getElementById('save-camera-btn')?.addEventListener('click', () => this.saveCamera());
        
        // Form inputs
        document.getElementById('camera-name-input')?.addEventListener('input', (e) => {
            this.formData.name = e.target.value;
            this.validateForm();
        });
        
        document.getElementById('camera-ip-input')?.addEventListener('input', (e) => {
            this.formData.ip_address = e.target.value;
            this.validateForm();
        });
        
        document.getElementById('connection-type-input')?.addEventListener('change', (e) => {
            this.formData.connection_type = e.target.value;
            this.updateDefaultPort();
            this.updateDefaultStreamPath();
            this.validateForm();
        });
        
        document.getElementById('camera-port-input')?.addEventListener('input', (e) => {
            this.formData.port = parseInt(e.target.value) || 80;
            this.validateForm();
        });
        
        document.getElementById('stream-path-input')?.addEventListener('input', (e) => {
            this.formData.stream_path = e.target.value;
        });
        
        document.getElementById('camera-location-input')?.addEventListener('change', (e) => {
            this.formData.location = e.target.value;
            this.validateForm();
        });
        
        document.getElementById('camera-username-input')?.addEventListener('input', (e) => {
            this.formData.username = e.target.value;
        });
        
        document.getElementById('camera-password-input')?.addEventListener('input', (e) => {
            this.formData.password = e.target.value;
        });
        
        // Password toggle
        document.getElementById('password-toggle-btn')?.addEventListener('click', () => this.togglePassword());
        
        // Test connection
        document.getElementById('test-connection-btn')?.addEventListener('click', () => this.testConnection());
        
        // Close on outside click
        document.getElementById('simple-camera-modal')?.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.hide();
            }
        });
        
        // Prevent form submission
        document.getElementById('camera-test-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
        });
    }

    validateForm() {
        const saveBtn = document.getElementById('save-camera-btn');
        if (saveBtn) {
            saveBtn.disabled = !this.isFormValid();
        }
    }

    isFormValid() {
        const { name, ip_address, location } = this.formData;
        const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
        
        return name.trim() && 
               ip_address.trim() && 
               ipRegex.test(ip_address) && 
               location;
    }

    togglePassword() {
        const passwordInput = document.getElementById('camera-password-input');
        const toggleBtn = document.getElementById('password-toggle-btn');
        const icon = toggleBtn.querySelector('i');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            passwordInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    async testConnection() {
        const testBtn = document.getElementById('test-connection-btn');
        
        // Validate required fields for test
        if (!this.formData.ip_address || !this.isValidIP(this.formData.ip_address)) {
            this.showTestResult({
                success: false,
                message: 'Please enter a valid IP address'
            });
            return;
        }
        
        // Show loading state
        const originalContent = testBtn.innerHTML;
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        testBtn.disabled = true;
        
        try {
            const response = await fetch('http://localhost:8000/api/v1/cameras/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip_address: this.formData.ip_address,
                    port: this.formData.port || 80,
                    username: this.formData.username || 'admin',
                    password: this.formData.password || ''
                })
            });
            
            const result = await response.json();
            this.showTestResult(result);
            
        } catch (error) {
            console.error('Connection test failed:', error);
            this.showTestResult({
                success: false,
                message: 'Connection test failed: ' + error.message
            });
        } finally {
            testBtn.innerHTML = originalContent;
            testBtn.disabled = false;
        }
    }

    showTestResult(result) {
        this.testResult = result;
        const testResultDiv = document.getElementById('test-result');
        if (testResultDiv) {
            testResultDiv.innerHTML = this.getTestResultHTML();
        }
    }

    isValidIP(ip) {
        const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
        return ipRegex.test(ip);
    }

    updateDefaultPort() {
        const defaultPorts = {
            'http': 80,
            'https': 443,
            'rtsp': 554,
            'rtsps': 322,
            'onvif': 80
        };
        
        this.formData.port = defaultPorts[this.formData.connection_type] || 80;
        const portInput = document.getElementById('camera-port-input');
        if (portInput) {
            portInput.value = this.formData.port;
        }
    }

    updateDefaultStreamPath() {
        const defaultPaths = {
            'http': '/mjpeg',
            'https': '/mjpeg',
            'rtsp': '/stream1',
            'rtsps': '/stream1',
            'onvif': '/onvif/media_service/stream_0'
        };
        
        this.formData.stream_path = defaultPaths[this.formData.connection_type] || '/mjpeg';
        const pathInput = document.getElementById('stream-path-input');
        if (pathInput) {
            pathInput.value = this.formData.stream_path;
        }
    }

    async saveCamera() {
        if (!this.isFormValid()) {
            alert('Please fill in all required fields');
            return;
        }
        
        const saveBtn = document.getElementById('save-camera-btn');
        const originalContent = saveBtn.innerHTML;
        saveBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${this.editMode ? 'Updating...' : 'Saving...'}`;
        saveBtn.disabled = true;
        
        try {
            // Create camera data
            const cameraData = {
                name: this.formData.name,
                ip_address: this.formData.ip_address,
                port: this.formData.port,
                connection_type: this.formData.connection_type,
                stream_path: this.formData.stream_path,
                location: this.formData.location,
                username: this.formData.username || 'admin',
                password: this.formData.password || '',
                enabled: true
            };
            
            let response;
            let savedCamera;
            
            if (this.editMode) {
                // Update existing camera
                response = await fetch(`http://localhost:8000/api/v1/cameras/${parseInt(this.editingCameraId)}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(cameraData)
                });
            } else {
                // Create new camera
                response = await fetch('http://localhost:8000/api/v1/cameras/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(cameraData)
                });
            }
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `Failed to ${this.editMode ? 'update' : 'save'} camera`);
            }
            
            savedCamera = await response.json();
            
            // Dispatch event to notify other components
            window.dispatchEvent(new CustomEvent(this.editMode ? 'cameraUpdated' : 'cameraAdded', { 
                detail: savedCamera 
            }));
            
            // Show success and close modal
            this.showToast(`Camera ${this.editMode ? 'updated' : 'added'} successfully`, 'success');
            this.hide();
            
        } catch (error) {
            console.error('Error saving camera:', error);
            this.showToast(`Failed to ${this.editMode ? 'update' : 'add'} camera`, 'error');
        } finally {
            saveBtn.innerHTML = originalContent;
            saveBtn.disabled = false;
        }
    }

    loadCameraData(camera) {
        this.formData = {
            name: camera.name || '',
            ip_address: camera.ipAddress || camera.ip_address || '',
            connection_type: camera.connectionType || camera.connection_type || 'http',
            port: camera.port || 80,
            stream_path: camera.streamPath || camera.stream_path || '/mjpeg',
            location: camera.location || '',
            username: camera.username || 'admin',
            password: camera.password || ''
        };
        this.testResult = null;
    }

    resetForm() {
        this.editMode = false;
        this.editingCameraId = null;
        this.formData = {
            name: '',
            ip_address: '',
            connection_type: 'http',
            port: 80,
            stream_path: '/mjpeg',
            location: '',
            username: 'admin',
            password: ''
        };
        this.testResult = null;
    }

    cleanup() {
        this.resetForm();
        // Event listeners are automatically removed when modal content is replaced
    }

    showToast(message, type = 'info') {
        // Create simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check' : 'fa-exclamation'}"></i>
            <span>${message}</span>
        `;
        
        // Style the toast
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 16px',
            backgroundColor: type === 'success' ? '#10b981' : '#ef4444',
            color: 'white',
            borderRadius: '6px',
            zIndex: '10000',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        });
        
        document.body.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 3000);
    }
}

export default SimpleCameraModal;