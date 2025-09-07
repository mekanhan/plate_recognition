class CameraSetupModal {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.formData = {
            name: '',
            location_id: '',
            manufacturer: '',
            model: '',
            discovery_method: 'manual',
            ip_address: '',
            discovered_cameras: [],
            connection_type: 'rtsp',
            port: 554,
            stream_path: '',
            username: '',
            password: '',
            available_streams: [],
            selected_stream: null,
            preview_active: false
        };
        this.isVisible = false;
        this.validationRules = this.getValidationRules();
        this.cameraConfigs = this.getCameraConfigurations();
    }

    show() {
        if (this.isVisible) return;
        
        this.isVisible = true;
        this.currentStep = 1;
        this.resetFormData();
        this.render();
        this.attachEventListeners();
        
        const modal = document.getElementById('camera-setup-modal');
        if (modal) {
            modal.style.display = 'flex';
            setTimeout(() => modal.classList.add('show'), 10);
        }
    }

    hide() {
        if (!this.isVisible) return;
        
        const modal = document.getElementById('camera-setup-modal');
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
        let modal = document.getElementById('camera-setup-modal');
        if (!modal) {
            modal = this.createModalElement();
            document.body.appendChild(modal);
        }
        modal.innerHTML = this.getModalTemplate();
    }

    createModalElement() {
        const modal = document.createElement('div');
        modal.id = 'camera-setup-modal';
        modal.className = 'modal-overlay camera-setup-modal';
        return modal;
    }

    getModalTemplate() {
        return `
            <div class="modal-container">
                <div class="modal-header">
                    <div class="modal-title">
                        <i class="fas fa-video"></i>
                        <span>Add New Camera</span>
                    </div>
                    <div class="modal-progress">
                        <span class="step-indicator">Step ${this.currentStep} of ${this.totalSteps}</span>
                        <div class="progress-dots">
                            ${Array.from({length: this.totalSteps}, (_, i) => `
                                <div class="progress-dot ${i + 1 <= this.currentStep ? 'active' : ''}${i + 1 < this.currentStep ? 'completed' : ''}"></div>
                            `).join('')}
                        </div>
                    </div>
                    <button class="modal-close" id="close-camera-setup">
                        <i class="fas fa-times"></i>
                    </button>
                </div>

                <div class="modal-content">
                    ${this.getStepContent()}
                </div>

                <div class="modal-footer">
                    <div class="footer-left">
                        ${this.currentStep > 1 ? `
                            <button class="btn btn-secondary" id="prev-step-btn">
                                <i class="fas fa-chevron-left"></i>
                                Previous
                            </button>
                        ` : ''}
                    </div>
                    <div class="footer-right">
                        ${this.currentStep < this.totalSteps ? `
                            <button class="btn btn-primary" id="next-step-btn" ${this.isCurrentStepValid() ? '' : 'disabled'}>
                                Next Step
                                <i class="fas fa-chevron-right"></i>
                            </button>
                        ` : `
                            <button class="btn btn-success" id="save-camera-btn" ${this.isCurrentStepValid() ? '' : 'disabled'}>
                                <i class="fas fa-save"></i>
                                Save Camera
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;
    }

    getStepContent() {
        switch (this.currentStep) {
            case 1: return this.getStep1Template();
            case 2: return this.getStep2Template();
            case 3: return this.getStep3Template();
            case 4: return this.getStep4Template();
            default: return '';
        }
    }

    getStep1Template() {
        return `
            <div class="step-content step-1">
                <div class="step-header">
                    <h3>Basic Information</h3>
                    <p>Provide basic details about your camera</p>
                </div>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label for="camera-name" class="required">Camera Name</label>
                        <input type="text" id="camera-name" class="form-input" 
                               placeholder="e.g., Entrance Gate Camera" 
                               value="${this.formData.name}">
                        <div class="form-error" id="camera-name-error"></div>
                    </div>
                    
                    <div class="form-group">
                        <label for="camera-location" class="required">Location</label>
                        <select id="camera-location" class="form-select">
                            <option value="">Select Location</option>
                            <option value="entrance" ${this.formData.location_id === 'entrance' ? 'selected' : ''}>Entrance</option>
                            <option value="parking" ${this.formData.location_id === 'parking' ? 'selected' : ''}>Parking</option>
                            <option value="exit" ${this.formData.location_id === 'exit' ? 'selected' : ''}>Exit</option>
                            <option value="loading" ${this.formData.location_id === 'loading' ? 'selected' : ''}>Loading Dock</option>
                        </select>
                        <div class="form-error" id="camera-location-error"></div>
                    </div>
                    
                    <div class="form-group">
                        <label for="camera-manufacturer">Manufacturer</label>
                        <select id="camera-manufacturer" class="form-select">
                            <option value="">Select Manufacturer</option>
                            ${Object.keys(this.cameraConfigs).map(key => `
                                <option value="${key}" ${this.formData.manufacturer === key ? 'selected' : ''}>
                                    ${this.cameraConfigs[key].name}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="camera-model">Model</label>
                        <input type="text" id="camera-model" class="form-input" 
                               placeholder="e.g., DS-2CD2T85FWD-I8" 
                               value="${this.formData.model}">
                        <div class="model-suggestions" id="model-suggestions"></div>
                    </div>
                </div>
            </div>
        `;
    }

    getStep2Template() {
        return `
            <div class="step-content step-2">
                <div class="step-header">
                    <h3>Network Discovery</h3>
                    <p>Find your camera on the network</p>
                </div>
                
                <div class="discovery-methods">
                    <div class="method-selector">
                        <label class="radio-label">
                            <input type="radio" name="discovery-method" value="auto" 
                                   ${this.formData.discovery_method === 'auto' ? 'checked' : ''}>
                            <div class="radio-option">
                                <div class="radio-icon">
                                    <i class="fas fa-search"></i>
                                </div>
                                <div class="radio-content">
                                    <h4>Auto-Discover</h4>
                                    <p>Scan network for cameras automatically</p>
                                </div>
                            </div>
                        </label>
                        
                        <label class="radio-label">
                            <input type="radio" name="discovery-method" value="manual" 
                                   ${this.formData.discovery_method === 'manual' ? 'checked' : ''}>
                            <div class="radio-option">
                                <div class="radio-icon">
                                    <i class="fas fa-keyboard"></i>
                                </div>
                                <div class="radio-content">
                                    <h4>Manual Configuration</h4>
                                    <p>Enter camera IP address manually</p>
                                </div>
                            </div>
                        </label>
                    </div>
                </div>
                
                <div class="discovery-content">
                    ${this.formData.discovery_method === 'auto' ? this.getAutoDiscoveryTemplate() : this.getManualConfigTemplate()}
                </div>
            </div>
        `;
    }

    getAutoDiscoveryTemplate() {
        return `
            <div class="auto-discovery">
                <div class="discovery-controls">
                    <button class="btn btn-primary" id="start-discovery-btn">
                        <i class="fas fa-search"></i>
                        Start Network Scan
                    </button>
                    <div class="discovery-progress" id="discovery-progress" style="display:none;">
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                        <span class="progress-text">Scanning network...</span>
                    </div>
                </div>
                
                <div class="discovered-cameras" id="discovered-cameras">
                    ${this.formData.discovered_cameras.length > 0 ? this.getDiscoveredCamerasTemplate() : ''}
                </div>
            </div>
        `;
    }

    getManualConfigTemplate() {
        return `
            <div class="manual-config">
                <div class="form-group">
                    <label for="manual-ip" class="required">IP Address</label>
                    <input type="text" id="manual-ip" class="form-input" 
                           placeholder="192.168.1.100" 
                           value="${this.formData.ip_address}" 
                           pattern="^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$">
                    <div class="form-error" id="manual-ip-error"></div>
                    <div class="form-help">Enter the IP address of your camera</div>
                </div>
            </div>
        `;
    }

    getStep3Template() {
        const config = this.getCurrentCameraConfig();
        return `
            <div class="step-content step-3">
                <div class="step-header">
                    <h3>Connection Configuration</h3>
                    <p>Configure connection settings and test connectivity</p>
                </div>
                
                <div class="connection-form">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="connection-type">Connection Type</label>
                            <select id="connection-type" class="form-select">
                                <option value="rtsp" ${this.formData.connection_type === 'rtsp' ? 'selected' : ''}>RTSP</option>
                                <option value="rtsps" ${this.formData.connection_type === 'rtsps' ? 'selected' : ''}>RTSPS (Secure)</option>
                                <option value="http" ${this.formData.connection_type === 'http' ? 'selected' : ''}>HTTP</option>
                                <option value="https" ${this.formData.connection_type === 'https' ? 'selected' : ''}>HTTPS</option>
                                <option value="onvif" ${this.formData.connection_type === 'onvif' ? 'selected' : ''}>ONVIF</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="connection-port">Port</label>
                            <input type="number" id="connection-port" class="form-input" 
                                   value="${this.formData.port}" 
                                   min="1" max="65535">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="stream-path">Stream Path</label>
                        <div class="input-with-suggestions">
                            <input type="text" id="stream-path" class="form-input" 
                                   placeholder="/h264Preview_01_main" 
                                   value="${this.formData.stream_path}">
                            <div class="path-suggestions" id="path-suggestions">
                                ${config ? config.streamPaths.map(path => `
                                    <div class="suggestion-item" data-path="${path}">${path}</div>
                                `).join('') : ''}
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="camera-username">Username</label>
                            <input type="text" id="camera-username" class="form-input" 
                                   placeholder="${config?.defaultUsername || 'admin'}" 
                                   value="${this.formData.username}">
                        </div>
                        
                        <div class="form-group">
                            <label for="camera-password">Password</label>
                            <div class="password-input">
                                <input type="password" id="camera-password" class="form-input" 
                                       placeholder="Enter password" 
                                       value="${this.formData.password}">
                                <button type="button" class="password-toggle" id="password-toggle">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="connection-test">
                        <button class="btn btn-secondary" id="test-connection-btn">
                            <i class="fas fa-plug"></i>
                            Test Connection
                        </button>
                        <div class="test-result" id="test-result"></div>
                    </div>
                </div>
            </div>
        `;
    }

    getStep4Template() {
        return `
            <div class="step-content step-4">
                <div class="step-header">
                    <h3>Stream Preview & Save</h3>
                    <p>Preview camera feed and finalize configuration</p>
                </div>
                
                <div class="preview-section">
                    <div class="stream-info">
                        <h4>Available Streams</h4>
                        <div class="stream-list" id="stream-list">
                            ${this.getStreamListTemplate()}
                        </div>
                    </div>
                    
                    <div class="preview-container">
                        <div class="video-preview" id="video-preview">
                            ${this.formData.preview_active ? `
                                <video class="preview-video" autoplay muted>
                                    <source src="#" type="video/mp4">
                                </video>
                            ` : `
                                <div class="preview-placeholder">
                                    <i class="fas fa-play-circle"></i>
                                    <span>Click "Start Preview" to view live feed</span>
                                </div>
                            `}
                        </div>
                        
                        <div class="preview-controls">
                            <button class="btn btn-primary" id="start-preview-btn">
                                <i class="fas fa-play"></i>
                                Start Preview
                            </button>
                            <button class="btn btn-secondary" id="stop-preview-btn" style="display:none;">
                                <i class="fas fa-stop"></i>
                                Stop Preview
                            </button>
                            <button class="btn btn-secondary" id="snapshot-btn">
                                <i class="fas fa-camera"></i>
                                Snapshot
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="config-summary">
                    <h4>Configuration Summary</h4>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <label>Camera Name:</label>
                            <span>${this.formData.name}</span>
                        </div>
                        <div class="summary-item">
                            <label>IP Address:</label>
                            <span>${this.formData.ip_address}</span>
                        </div>
                        <div class="summary-item">
                            <label>Connection:</label>
                            <span>${this.formData.connection_type.toUpperCase()}:${this.formData.port}</span>
                        </div>
                        <div class="summary-item">
                            <label>Stream Path:</label>
                            <span>${this.formData.stream_path}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getStreamListTemplate() {
        if (this.formData.available_streams.length === 0) {
            return '<div class="no-streams">No streams detected. Please check connection settings.</div>';
        }
        
        return this.formData.available_streams.map(stream => `
            <div class="stream-item ${stream.id === this.formData.selected_stream?.id ? 'selected' : ''}" data-stream-id="${stream.id}">
                <div class="stream-info">
                    <div class="stream-name">${stream.name}</div>
                    <div class="stream-specs">
                        ${stream.resolution} • ${stream.fps}fps • ${stream.codec}${stream.bitrate ? ` • ${stream.bitrate}` : ''}
                    </div>
                </div>
                <div class="stream-actions">
                    <button class="btn btn-small btn-primary select-stream-btn" data-stream-id="${stream.id}">
                        Select
                    </button>
                </div>
            </div>
        `).join('');
    }

    attachEventListeners() {
        document.getElementById('close-camera-setup')?.addEventListener('click', () => this.hide());
        document.getElementById('prev-step-btn')?.addEventListener('click', () => this.previousStep());
        document.getElementById('next-step-btn')?.addEventListener('click', () => this.nextStep());
        document.getElementById('save-camera-btn')?.addEventListener('click', () => this.saveCamera());
        
        this.attachStepEventListeners();
        
        document.getElementById('camera-setup-modal')?.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.hide();
            }
        });
    }

    attachStepEventListeners() {
        switch (this.currentStep) {
            case 1: this.attachStep1Listeners(); break;
            case 2: this.attachStep2Listeners(); break;
            case 3: this.attachStep3Listeners(); break;
            case 4: this.attachStep4Listeners(); break;
        }
    }

    attachStep1Listeners() {
        document.getElementById('camera-name')?.addEventListener('input', (e) => {
            this.formData.name = e.target.value;
            this.validateStep();
        });
        
        document.getElementById('camera-location')?.addEventListener('change', (e) => {
            this.formData.location_id = e.target.value;
            this.validateStep();
        });
        
        document.getElementById('camera-manufacturer')?.addEventListener('change', (e) => {
            this.formData.manufacturer = e.target.value;
            this.updateDefaultsForManufacturer();
            this.validateStep();
        });
        
        document.getElementById('camera-model')?.addEventListener('input', (e) => {
            this.formData.model = e.target.value;
        });
    }

    attachStep2Listeners() {
        document.querySelectorAll('input[name="discovery-method"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.formData.discovery_method = e.target.value;
                this.render();
            });
        });
        
        if (this.formData.discovery_method === 'auto') {
            document.getElementById('start-discovery-btn')?.addEventListener('click', () => this.startNetworkDiscovery());
        } else {
            document.getElementById('manual-ip')?.addEventListener('input', (e) => {
                this.formData.ip_address = e.target.value;
                this.validateStep();
            });
        }
    }

    attachStep3Listeners() {
        document.getElementById('connection-type')?.addEventListener('change', (e) => {
            this.formData.connection_type = e.target.value;
            this.updateDefaultPort();
        });
        
        document.getElementById('connection-port')?.addEventListener('input', (e) => {
            this.formData.port = parseInt(e.target.value);
        });
        
        document.getElementById('stream-path')?.addEventListener('input', (e) => {
            this.formData.stream_path = e.target.value;
        });
        
        document.getElementById('camera-username')?.addEventListener('input', (e) => {
            this.formData.username = e.target.value;
        });
        
        document.getElementById('camera-password')?.addEventListener('input', (e) => {
            this.formData.password = e.target.value;
        });
        
        document.getElementById('password-toggle')?.addEventListener('click', () => this.togglePasswordVisibility());
        document.getElementById('test-connection-btn')?.addEventListener('click', () => this.testConnection());
        
        document.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', (e) => {
                document.getElementById('stream-path').value = e.target.dataset.path;
                this.formData.stream_path = e.target.dataset.path;
            });
        });
    }

    attachStep4Listeners() {
        document.getElementById('start-preview-btn')?.addEventListener('click', () => this.startPreview());
        document.getElementById('stop-preview-btn')?.addEventListener('click', () => this.stopPreview());
        document.getElementById('snapshot-btn')?.addEventListener('click', () => this.takeSnapshot());
        
        document.querySelectorAll('.select-stream-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectStream(e.target.dataset.streamId));
        });
    }

    async nextStep() {
        if (!this.validateCurrentStep()) return;
        
        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            if (this.currentStep === 4) {
                await this.loadAvailableStreams();
            }
            this.render();
            this.attachEventListeners();
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.render();
            this.attachEventListeners();
        }
    }

    validateCurrentStep() {
        switch (this.currentStep) {
            case 1: return this.validateStep1();
            case 2: return this.validateStep2();
            case 3: return this.validateStep3();
            case 4: return this.validateStep4();
            default: return false;
        }
    }

    validateStep1() {
        const errors = {};
        
        if (!this.formData.name.trim()) {
            errors['camera-name'] = 'Camera name is required';
        }
        
        if (!this.formData.location_id) {
            errors['camera-location'] = 'Location is required';
        }
        
        this.showValidationErrors(errors);
        return Object.keys(errors).length === 0;
    }

    validateStep2() {
        if (this.formData.discovery_method === 'manual') {
            const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
            if (!ipRegex.test(this.formData.ip_address)) {
                this.showValidationErrors({'manual-ip': 'Please enter a valid IP address'});
                return false;
            }
        }
        return true;
    }

    validateStep3() {
        return this.formData.connection_test_passed === true;
    }

    validateStep4() {
        return true;
    }

    isCurrentStepValid() {
        return this.validateCurrentStep();
    }

    validateStep() {
        const nextBtn = document.getElementById('next-step-btn');
        const saveBtn = document.getElementById('save-camera-btn');
        
        if (nextBtn) {
            nextBtn.disabled = !this.isCurrentStepValid();
        }
        if (saveBtn) {
            saveBtn.disabled = !this.isCurrentStepValid();
        }
    }

    showValidationErrors(errors) {
        document.querySelectorAll('.form-error').forEach(el => el.textContent = '');
        
        Object.entries(errors).forEach(([field, message]) => {
            const errorElement = document.getElementById(`${field}-error`);
            if (errorElement) {
                errorElement.textContent = message;
            }
        });
    }

    getCameraConfigurations() {
        return {
            reolink: {
                name: 'Reolink',
                defaultPort: 554,
                defaultUsername: 'admin',
                streamPaths: ['/h264Preview_01_main', '/h264Preview_01_sub', '/ONVIF/MediaInput']
            },
            hikvision: {
                name: 'Hikvision',
                defaultPort: 554,
                defaultUsername: 'admin',
                streamPaths: ['/ISAPI/Streaming/channels/101', '/h264/ch1/main/av_stream', '/ONVIF/channel1']
            },
            dahua: {
                name: 'Dahua',
                defaultPort: 554,
                defaultUsername: 'admin',
                streamPaths: ['/cam/realmonitor?channel=1&subtype=0', '/ONVIF/MediaInput']
            },
            axis: {
                name: 'Axis',
                defaultPort: 554,
                defaultUsername: 'root',
                streamPaths: ['/axis-media/media.amp', '/ONVIF/Media']
            },
            generic: {
                name: 'Generic RTSP',
                defaultPort: 554,
                defaultUsername: 'admin',
                streamPaths: ['/stream', '/live', '/video']
            },
            onvif: {
                name: 'ONVIF Compatible',
                defaultPort: 80,
                defaultUsername: 'admin',
                streamPaths: ['/ONVIF/MediaInput', '/onvif/media_service/stream_0']
            }
        };
    }

    getCurrentCameraConfig() {
        return this.cameraConfigs[this.formData.manufacturer] || null;
    }

    updateDefaultsForManufacturer() {
        const config = this.getCurrentCameraConfig();
        if (config) {
            this.formData.port = config.defaultPort;
            this.formData.username = config.defaultUsername;
            if (config.streamPaths.length > 0) {
                this.formData.stream_path = config.streamPaths[0];
            }
        }
    }

    updateDefaultPort() {
        const defaultPorts = {
            rtsp: 554,
            rtsps: 322,
            http: 80,
            https: 443,
            onvif: 80
        };
        
        this.formData.port = defaultPorts[this.formData.connection_type] || 554;
        
        const portInput = document.getElementById('connection-port');
        if (portInput) {
            portInput.value = this.formData.port;
        }
    }

    resetFormData() {
        this.formData = {
            name: '',
            location_id: '',
            manufacturer: '',
            model: '',
            discovery_method: 'manual',
            ip_address: '',
            discovered_cameras: [],
            connection_type: 'rtsp',
            port: 554,
            stream_path: '',
            username: '',
            password: '',
            available_streams: [],
            selected_stream: null,
            preview_active: false
        };
    }

    getValidationRules() {
        return {
            name: { required: true, minLength: 3 },
            location_id: { required: true },
            ip_address: { 
                required: true, 
                pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/ 
            }
        };
    }

    cleanup() {
        this.stopPreview();
        this.resetFormData();
        this.removeEventListeners();
    }

    removeEventListeners() {
        // Clean up event listeners
    }

    async startNetworkDiscovery() {
        // Mock network discovery
        return new Promise(resolve => setTimeout(resolve, 2000));
    }

    async testConnection() {
        // Mock connection test
        return new Promise(resolve => setTimeout(resolve, 1500));
    }

    async loadAvailableStreams() {
        // Mock stream loading
        this.formData.available_streams = [
            {
                id: 'main',
                name: 'Main Stream',
                resolution: '1920x1080',
                fps: 30,
                codec: 'H.264',
                bitrate: '2.5 Mbps'
            },
            {
                id: 'sub',
                name: 'Sub Stream',
                resolution: '640x480',
                fps: 15,
                codec: 'H.264',
                bitrate: '512 Kbps'
            }
        ];
    }

    async saveCamera() {
        try {
            // Mock save operation
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.hide();
            window.dispatchEvent(new CustomEvent('cameraAdded', {
                detail: this.formData
            }));
        } catch (error) {
            console.error('Error saving camera:', error);
        }
    }

    startPreview() {
        this.formData.preview_active = true;
        // Implement preview logic
    }

    stopPreview() {
        this.formData.preview_active = false;
        // Implement stop preview logic
    }

    takeSnapshot() {
        console.log('Taking snapshot...');
        // Implement snapshot logic
    }

    selectStream(streamId) {
        this.formData.selected_stream = this.formData.available_streams.find(s => s.id === streamId);
        this.render();
        this.attachEventListeners();
    }

    togglePasswordVisibility() {
        const passwordInput = document.getElementById('camera-password');
        const toggleBtn = document.getElementById('password-toggle');
        const icon = toggleBtn.querySelector('i');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            passwordInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }
}

export default CameraSetupModal;