/**
 * Simple Camera Test Modal
 * Basic IP camera connection testing modal
 */
import config from '../../config/app.config.js';

class SimpleCameraModal {
    constructor() {
        this.isVisible = false;
        this.editMode = false;
        this.editingCameraId = null;
        this.activeTab = 'network'; // Track active tab
        this.formData = {
            name: '',
            ip_address: '',
            connection_type: 'http',
            port: 80,
            stream_path: '/mjpeg',
            stream_type: 'custom',
            location: '',
            username: 'admin',
            password: '',
            // Video settings
            brand: '',
            model: '',
            resolution_width: 1920,
            resolution_height: 1080,
            max_fps: 30,
            video_quality: 'medium',
            low_latency: true
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
                
                <!-- Tab Navigation -->
                <div class="modal-tabs">
                    <button type="button" class="tab-btn ${this.activeTab === 'network' ? 'active' : ''}" data-tab="network">
                        <i class="fas fa-network-wired"></i>
                        Network
                    </button>
                    <button type="button" class="tab-btn ${this.activeTab === 'video' ? 'active' : ''}" data-tab="video">
                        <i class="fas fa-video"></i>
                        Video Settings
                    </button>
                </div>
                
                <div class="modal-content">
                    <form id="camera-test-form" class="camera-form">
                        <!-- Network Tab Content -->
                        <div class="tab-content ${this.activeTab === 'network' ? 'active' : ''}" data-tab="network">
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
                                <label for="stream-type-input">Stream Type</label>
                                <select id="stream-type-input" class="form-select">
                                    <option value="custom">Custom Path</option>
                                    <option value="reolink_main" ${this.getStreamTypeSelection('reolink_main')}>Reolink Main Stream</option>
                                    <option value="reolink_sub" ${this.getStreamTypeSelection('reolink_sub')}>Reolink Sub Stream</option>
                                    <option value="reolink_h265" ${this.getStreamTypeSelection('reolink_h265')}>Reolink H.265 Main</option>
                                    <option value="reolink_h265_sub" ${this.getStreamTypeSelection('reolink_h265_sub')}>Reolink H.265 Sub</option>
                                    <option value="reolink_simple" ${this.getStreamTypeSelection('reolink_simple')}>Reolink Simple</option>
                                    <option value="hikvision_main" ${this.getStreamTypeSelection('hikvision_main')}>Hikvision Main</option>
                                    <option value="hikvision_sub" ${this.getStreamTypeSelection('hikvision_sub')}>Hikvision Sub</option>
                                    <option value="dahua_main" ${this.getStreamTypeSelection('dahua_main')}>Dahua Main</option>
                                    <option value="generic_mjpeg" ${this.getStreamTypeSelection('generic_mjpeg')}>Generic MJPEG</option>
                                </select>
                                <small class="form-help">Select stream type for auto-configuration</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="stream-path-input">Stream Path</label>
                                <input type="text" id="stream-path-input" class="form-input" 
                                       placeholder="/mjpeg" 
                                       value="${this.formData.stream_path}">
                                <small class="form-help">URL path to video stream (auto-filled based on stream type)</small>
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
                                <div class="test-buttons">
                                    <button type="button" class="btn btn-secondary" id="test-connection-btn">
                                        <i class="fas fa-plug"></i>
                                        Test Connection
                                    </button>
                                    <button type="button" class="btn btn-outline-secondary" id="test-all-paths-btn">
                                        <i class="fas fa-search"></i>
                                        Find Working Path
                                    </button>
                                </div>
                                <div class="test-result" id="test-result">
                                    ${this.getTestResultHTML()}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Video Settings Tab Content -->
                        <div class="tab-content ${this.activeTab === 'video' ? 'active' : ''}" data-tab="video">
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="camera-brand-input">Camera Brand</label>
                                    <select id="camera-brand-input" class="form-select">
                                        <option value="">Select Brand</option>
                                        <option value="Reolink" ${this.formData.brand === 'Reolink' ? 'selected' : ''}>Reolink</option>
                                        <option value="hikvision" ${this.formData.brand === 'hikvision' ? 'selected' : ''}>Hikvision</option>
                                        <option value="dahua" ${this.formData.brand === 'dahua' ? 'selected' : ''}>Dahua</option>
                                        <option value="axis" ${this.formData.brand === 'axis' ? 'selected' : ''}>Axis</option>
                                        <option value="bosch" ${this.formData.brand === 'bosch' ? 'selected' : ''}>Bosch</option>
                                        <option value="samsung" ${this.formData.brand === 'samsung' ? 'selected' : ''}>Samsung</option>
                                        <option value="panasonic" ${this.formData.brand === 'panasonic' ? 'selected' : ''}>Panasonic</option>
                                        <option value="sony" ${this.formData.brand === 'sony' ? 'selected' : ''}>Sony</option>
                                        <option value="other" ${this.formData.brand === 'other' ? 'selected' : ''}>Other</option>
                                    </select>
                                    <small class="form-help">Camera brand affects optimal settings</small>
                                </div>
                                
                                <div class="form-group">
                                    <label for="camera-model-input">Camera Model</label>
                                    <input type="text" id="camera-model-input" class="form-input" 
                                           placeholder="e.g., DS-2CD2143G0-I" 
                                           value="${this.formData.model}">
                                    <small class="form-help">Optional: Camera model for specific optimizations</small>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="resolution-width-input">Resolution Width</label>
                                    <select id="resolution-width-input" class="form-select">
                                        <option value="640" ${this.formData.resolution_width === 640 ? 'selected' : ''}>640px</option>
                                        <option value="1280" ${this.formData.resolution_width === 1280 ? 'selected' : ''}>1280px (720p)</option>
                                        <option value="1920" ${this.formData.resolution_width === 1920 ? 'selected' : ''}>1920px (1080p)</option>
                                        <option value="2560" ${this.formData.resolution_width === 2560 ? 'selected' : ''}>2560px (1440p)</option>
                                        <option value="3840" ${this.formData.resolution_width === 3840 ? 'selected' : ''}>3840px (4K)</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label for="resolution-height-input">Resolution Height</label>
                                    <select id="resolution-height-input" class="form-select">
                                        <option value="480" ${this.formData.resolution_height === 480 ? 'selected' : ''}>480px</option>
                                        <option value="720" ${this.formData.resolution_height === 720 ? 'selected' : ''}>720px</option>
                                        <option value="1080" ${this.formData.resolution_height === 1080 ? 'selected' : ''}>1080px</option>
                                        <option value="1440" ${this.formData.resolution_height === 1440 ? 'selected' : ''}>1440px</option>
                                        <option value="2160" ${this.formData.resolution_height === 2160 ? 'selected' : ''}>2160px (4K)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="max-fps-input">Maximum FPS</label>
                                    <select id="max-fps-input" class="form-select">
                                        <option value="15" ${this.formData.max_fps === 15 ? 'selected' : ''}>15 FPS</option>
                                        <option value="20" ${this.formData.max_fps === 20 ? 'selected' : ''}>20 FPS</option>
                                        <option value="25" ${this.formData.max_fps === 25 ? 'selected' : ''}>25 FPS</option>
                                        <option value="30" ${this.formData.max_fps === 30 ? 'selected' : ''}>30 FPS</option>
                                        <option value="60" ${this.formData.max_fps === 60 ? 'selected' : ''}>60 FPS</option>
                                    </select>
                                    <small class="form-help">Higher FPS = smoother video but more bandwidth</small>
                                </div>
                                
                                <div class="form-group">
                                    <label for="video-quality-input">Video Quality</label>
                                    <select id="video-quality-input" class="form-select">
                                        <option value="low" ${this.formData.video_quality === 'low' ? 'selected' : ''}>Low (faster, less bandwidth)</option>
                                        <option value="medium" ${this.formData.video_quality === 'medium' ? 'selected' : ''}>Medium (balanced)</option>
                                        <option value="high" ${this.formData.video_quality === 'high' ? 'selected' : ''}>High (best quality)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="low-latency-input" ${this.formData.low_latency ? 'checked' : ''}>
                                    <span class="checkbox-checkmark"></span>
                                    Enable Low Latency Mode
                                </label>
                                <small class="form-help">Reduces stream delay but may impact quality. Recommended for real-time monitoring.</small>
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

    getStreamTypeSelection(streamType) {
        return this.formData.stream_type === streamType ? 'selected' : '';
    }

    getStreamPathForType(streamType) {
        const streamPaths = {
            'custom': this.formData.stream_path || '/mjpeg',
            'reolink_main': '/Preview_01_main',
            'reolink_sub': '/Preview_01_sub', 
            'reolink_h265': '/h265Preview_01_main',
            'reolink_h265_sub': '/h265Preview_01_sub',
            'reolink_simple': '/',
            'hikvision_main': '/h264/ch1/main/av_stream',
            'hikvision_sub': '/h264/ch1/sub/av_stream',
            'dahua_main': '/cam/realmonitor?channel=1&subtype=0',
            'generic_mjpeg': '/mjpeg'
        };
        return streamPaths[streamType] || '/mjpeg';
    }

    updateStreamPathFromType(streamType) {
        if (streamType !== 'custom') {
            this.formData.stream_path = this.getStreamPathForType(streamType);
            const pathInput = document.getElementById('stream-path-input');
            if (pathInput) {
                pathInput.value = this.formData.stream_path;
            }
        }
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
        
        document.getElementById('stream-type-input')?.addEventListener('change', (e) => {
            this.formData.stream_type = e.target.value;
            this.updateStreamPathFromType(e.target.value);
        });
        
        document.getElementById('stream-path-input')?.addEventListener('input', (e) => {
            this.formData.stream_path = e.target.value;
            // If user manually edits path, switch to custom type
            if (this.getStreamPathForType(this.formData.stream_type) !== e.target.value) {
                this.formData.stream_type = 'custom';
                const typeSelect = document.getElementById('stream-type-input');
                if (typeSelect) {
                    typeSelect.value = 'custom';
                }
            }
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
        
        // Video settings event listeners
        this.attachVideoSettingsListeners();
        
        // Password toggle
        document.getElementById('password-toggle-btn')?.addEventListener('click', () => this.togglePassword());
        
        // Test connection
        document.getElementById('test-connection-btn')?.addEventListener('click', () => this.testConnection());
        document.getElementById('test-all-paths-btn')?.addEventListener('click', () => this.testAllPaths());
        
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
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const targetTab = e.currentTarget.dataset.tab;
                this.switchTab(targetTab);
            });
        });
    }

    validateForm() {
        const saveBtn = document.getElementById('save-camera-btn');
        if (saveBtn) {
            saveBtn.disabled = !this.isFormValid();
        }
        
        // Real-time validation feedback
        this.updateFieldValidation('camera-name-input', this.formData.name.trim().length > 0);
        this.updateFieldValidation('camera-ip-input', this.isValidIP(this.formData.ip_address));
        this.updateFieldValidation('camera-port-input', this.isValidPort(this.formData.port));
        this.updateFieldValidation('camera-location-input', this.formData.location.length > 0);
    }

    updateFieldValidation(fieldId, isValid) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.toggle('invalid', !isValid);
            field.classList.toggle('valid', isValid);
        }
    }

    isFormValid() {
        const { name, ip_address, location, port } = this.formData;
        const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
        
        // Basic validation
        if (!name.trim() || !ip_address.trim() || !location) {
            return false;
        }
        
        // IP address validation  
        if (!ipRegex.test(ip_address)) {
            return false;
        }
        
        // Port validation
        if (!port || port < 1 || port > 65535) {
            return false;
        }
        
        // Additional IP validation - check ranges
        const ipParts = ip_address.split('.').map(Number);
        for (const part of ipParts) {
            if (part < 0 || part > 255) {
                return false;
            }
        }
        
        return true;
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
            const response = await fetch(config.buildApiUrl(config.API_ENDPOINTS.CAMERA_TEST_CONNECTION), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip_address: this.formData.ip_address,
                    port: this.formData.port || 80,
                    connection_type: this.formData.connection_type || 'http',
                    stream_path: this.formData.stream_path || '/mjpeg',
                    username: this.formData.username || 'admin',
                    password: this.formData.password || '',
                    timeout: 10
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

    async testAllPaths() {
        const testAllBtn = document.getElementById('test-all-paths-btn');
        
        // Validate required fields for test
        if (!this.formData.ip_address || !this.isValidIP(this.formData.ip_address)) {
            this.showTestResult({
                success: false,
                message: 'Please enter a valid IP address'
            });
            return;
        }
        
        // Show loading state
        const originalContent = testAllBtn.innerHTML;
        testAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Finding...';
        testAllBtn.disabled = true;
        
        // Also disable regular test button during multi-path test
        const testBtn = document.getElementById('test-connection-btn');
        testBtn.disabled = true;
        
        try {
            const response = await fetch(config.buildApiUrl(config.API_ENDPOINTS.CAMERA_TEST_ALL_PATHS), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip_address: this.formData.ip_address,
                    port: this.formData.port || 80,
                    connection_type: this.formData.connection_type || 'http',
                    stream_path: this.formData.stream_path || '/mjpeg',
                    username: this.formData.username || 'admin',
                    password: this.formData.password || '',
                    brand: this.formData.brand || 'reolink',
                    timeout: 3  // Shorter timeout for multiple tests
                })
            });
            
            const result = await response.json();
            this.showAllPathsResult(result);
            
        } catch (error) {
            console.error('Multi-path test failed:', error);
            this.showTestResult({
                success: false,
                message: 'Path discovery failed: ' + error.message
            });
        } finally {
            testAllBtn.innerHTML = originalContent;
            testAllBtn.disabled = false;
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

    showAllPathsResult(result) {
        const testResultDiv = document.getElementById('test-result');
        if (!testResultDiv) return;

        const successfulPath = result.successful_path;
        
        if (successfulPath) {
            // Update form with working path
            this.formData.stream_path = successfulPath;
            this.formData.stream_type = this.detectStreamType(successfulPath);
            
            // Update UI fields
            const pathInput = document.getElementById('stream-path-input');
            const typeSelect = document.getElementById('stream-type-input');
            if (pathInput) pathInput.value = successfulPath;
            if (typeSelect) typeSelect.value = this.formData.stream_type;
            
            // Show success message
            testResultDiv.innerHTML = `
                <div class="result-status success">
                    <i class="fas fa-check-circle"></i>
                    <span>Found working stream path: ${successfulPath}</span>
                    <small>Tested ${result.total_tested} paths</small>
                </div>
                <div class="path-details">
                    <strong>All tested paths:</strong>
                    <ul class="path-list">
                        ${result.results.map(r => `
                            <li class="path-item ${r.success ? 'success' : 'failed'}">
                                <span class="path">${r.stream_path}</span>
                                <span class="status">${r.success ? '✓' : '✗'}</span>
                                ${r.recommended ? '<span class="recommended">RECOMMENDED</span>' : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        } else {
            // Show failure message with all attempts
            testResultDiv.innerHTML = `
                <div class="result-status error">
                    <i class="fas fa-times-circle"></i>
                    <span>No working stream path found</span>
                    <small>Tested ${result.total_tested} paths</small>
                </div>
                <div class="path-details">
                    <strong>Attempted paths:</strong>
                    <ul class="path-list">
                        ${result.results.map(r => `
                            <li class="path-item failed">
                                <span class="path">${r.stream_path}</span>
                                <span class="status">✗</span>
                                <small class="error-msg">${r.error || r.message}</small>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
    }

    isValidIP(ip) {
        const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
        if (!ipRegex.test(ip)) return false;
        
        // Check each part is in valid range
        const parts = ip.split('.').map(Number);
        return parts.every(part => part >= 0 && part <= 255);
    }

    isValidPort(port) {
        return port && port >= 1 && port <= 65535;
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
                enabled: true,
                // Video settings
                brand: this.formData.brand || '',
                model: this.formData.model || '',
                resolution_width: this.formData.resolution_width || 1920,
                resolution_height: this.formData.resolution_height || 1080,
                max_fps: this.formData.max_fps || 30,
                video_quality: this.formData.video_quality || 'medium',
                low_latency: this.formData.low_latency !== undefined ? this.formData.low_latency : true
            };
            
            let response;
            let savedCamera;
            
            if (this.editMode) {
                // Update existing camera
                const updateUrl = config.buildApiUrl(config.API_ENDPOINTS.CAMERA_BY_ID(this.editingCameraId));
                response = await fetch(updateUrl, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(cameraData)
                });
            } else {
                // Create new camera
                response = await fetch(config.buildApiUrl(config.API_ENDPOINTS.CAMERAS), {
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
            
            // Check if camera was created but connection test failed
            const isTestFailed = savedCamera.last_test_result === 'failed';
            
            // Dispatch event to notify other components
            window.dispatchEvent(new CustomEvent(this.editMode ? 'cameraUpdated' : 'cameraAdded', { 
                detail: savedCamera 
            }));
            
            // Show appropriate success message
            if (isTestFailed && !this.editMode) {
                this.showToast(`Camera created but connection test failed. Check network settings.`, 'warning');
            } else {
                this.showToast(`Camera ${this.editMode ? 'updated' : 'added'} successfully`, 'success');
            }
            
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
        const streamPath = camera.streamPath || camera.stream_path || '/mjpeg';
        
        this.formData = {
            name: camera.name || '',
            ip_address: camera.ipAddress || camera.ip_address || '',
            connection_type: camera.connectionType || camera.connection_type || 'http',
            port: camera.port || 80,
            stream_path: streamPath,
            stream_type: this.detectStreamType(streamPath),
            location: camera.location || '',
            username: camera.username || 'admin',
            password: camera.password || '',
            // Video settings
            brand: camera.brand || '',
            model: camera.model || '',
            resolution_width: camera.resolution_width || 1920,
            resolution_height: camera.resolution_height || 1080,
            max_fps: camera.max_fps || 30,
            video_quality: camera.video_quality || 'medium',
            low_latency: camera.low_latency !== undefined ? camera.low_latency : true
        };
        this.testResult = null;
    }

    detectStreamType(streamPath) {
        const pathMap = {
            '/Preview_01_main': 'reolink_main',
            '/Preview_01_sub': 'reolink_sub',
            '/h265Preview_01_main': 'reolink_h265',
            '/': 'reolink_simple',
            '/h264/ch1/main/av_stream': 'hikvision_main',
            '/h264/ch1/sub/av_stream': 'hikvision_sub',
            '/cam/realmonitor?channel=1&subtype=0': 'dahua_main',
            '/mjpeg': 'generic_mjpeg'
        };
        return pathMap[streamPath] || 'custom';
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
            stream_type: 'custom',
            location: '',
            username: 'admin',
            password: '',
            // Video settings
            brand: '',
            model: '',
            resolution_width: 1920,
            resolution_height: 1080,
            max_fps: 30,
            video_quality: 'medium',
            low_latency: true
        };
        this.testResult = null;
        this.activeTab = 'network';
    }

    cleanup() {
        this.resetForm();
        // Event listeners are automatically removed when modal content is replaced
    }

    switchTab(tabName) {
        this.activeTab = tabName;
        
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.dataset.tab === tabName);
        });
    }

    attachVideoSettingsListeners() {
        // Brand selection
        document.getElementById('camera-brand-input')?.addEventListener('change', (e) => {
            this.formData.brand = e.target.value;
        });
        
        // Model input
        document.getElementById('camera-model-input')?.addEventListener('input', (e) => {
            this.formData.model = e.target.value;
        });
        
        // Resolution inputs
        document.getElementById('resolution-width-input')?.addEventListener('change', (e) => {
            this.formData.resolution_width = parseInt(e.target.value);
            this.updateResolutionHeight();
        });
        
        document.getElementById('resolution-height-input')?.addEventListener('change', (e) => {
            this.formData.resolution_height = parseInt(e.target.value);
        });
        
        // FPS input
        document.getElementById('max-fps-input')?.addEventListener('change', (e) => {
            this.formData.max_fps = parseInt(e.target.value);
        });
        
        // Video quality
        document.getElementById('video-quality-input')?.addEventListener('change', (e) => {
            this.formData.video_quality = e.target.value;
        });
        
        // Low latency checkbox
        document.getElementById('low-latency-input')?.addEventListener('change', (e) => {
            this.formData.low_latency = e.target.checked;
        });
    }

    updateResolutionHeight() {
        const widthSelect = document.getElementById('resolution-width-input');
        const heightSelect = document.getElementById('resolution-height-input');
        
        if (!widthSelect || !heightSelect) return;
        
        // Auto-select appropriate height based on width
        const aspectRatioMap = {
            640: 480,
            1280: 720,
            1920: 1080,
            2560: 1440,
            3840: 2160
        };
        
        const width = parseInt(widthSelect.value);
        const suggestedHeight = aspectRatioMap[width];
        
        if (suggestedHeight) {
            heightSelect.value = suggestedHeight;
            this.formData.resolution_height = suggestedHeight;
        }
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