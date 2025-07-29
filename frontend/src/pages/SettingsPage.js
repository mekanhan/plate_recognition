/**
 * Settings Page Component
 * System configuration, user management, and preferences
 */
import config from '../config/app.config.js';

class SettingsPage {
    constructor() {
        this.currentSection = 'general';
        this.settings = {};
        this.users = [];
        this.roles = [];
        this.unsavedChanges = false;
        this.init();
    }

    init() {
        this.loadMockData();
        this.render();
        this.attachEventListeners();
        this.loadSettings();
    }

    loadMockData() {
        this.settings = {
            general: {
                systemName: 'License Plate Recognition System',
                timezone: 'America/New_York',
                dateFormat: 'MM/DD/YYYY',
                timeFormat: '12',
                language: 'en',
                autoLogout: 30,
                sessionTimeout: 120
            },
            detection: {
                confidence: 85,
                maxDetections: 10,
                enableEnhancement: true,
                enhancementLevel: 'medium',
                ocrEngine: 'easyocr',
                plateFormats: ['US', 'CA', 'EU'],
                minPlateSize: 50,
                maxPlateSize: 500,
                enableBoundingBox: true,
                saveDetectionImages: true,
                compressionQuality: 80
            },
            cameras: {
                maxCameras: 16,
                defaultResolution: '1920x1080',
                defaultFps: 30,
                connectionTimeout: 10,
                retryAttempts: 3,
                healthCheckInterval: 60,
                enableMotionDetection: false,
                motionSensitivity: 'medium'
            },
            storage: {
                maxStorageSize: 100, // GB
                retentionPeriod: 90, // days
                autoCleanup: true,
                cleanupSchedule: '0 2 * * *', // 2 AM daily
                backupEnabled: false,
                backupLocation: '',
                compressionEnabled: true
            },
            alerts: {
                enableEmailAlerts: true,
                emailServer: 'smtp.company.com',
                emailPort: 587,
                emailUsername: 'alerts@company.com',
                emailPassword: '********',
                enableSmsAlerts: false,
                smsProvider: '',
                smsApiKey: '',
                criticalAlertDelay: 0,
                warningAlertDelay: 5,
                infoAlertDelay: 30
            },
            security: {
                enableTwoFactor: false,
                passwordMinLength: 8,
                passwordRequireSpecial: true,
                passwordRequireNumbers: true,
                passwordRequireUppercase: true,
                maxLoginAttempts: 5,
                lockoutDuration: 15,
                sessionTokenExpiry: 24,
                enableAuditLog: true,
                enableIpWhitelist: false,
                allowedIps: []
            },
            api: {
                enableApi: true,
                apiKeyRequired: true,
                rateLimitEnabled: true,
                rateLimitRequests: 1000,
                rateLimitWindow: 3600,
                enableCors: true,
                allowedOrigins: ['*'],
                enableWebhooks: false,
                webhookUrl: '',
                webhookSecret: ''
            }
        };

        this.users = [
            {
                id: '1',
                username: 'admin',
                email: 'admin@company.com',
                firstName: 'System',
                lastName: 'Administrator',
                role: 'admin',
                status: 'active',
                lastLogin: new Date(Date.now() - 2 * 60 * 60 * 1000),
                createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
                twoFactorEnabled: true
            },
            {
                id: '2',
                username: 'operator',
                email: 'operator@company.com',
                firstName: 'Security',
                lastName: 'Operator',
                role: 'operator',
                status: 'active',
                lastLogin: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
                createdAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
                twoFactorEnabled: false
            },
            {
                id: '3',
                username: 'viewer',
                email: 'viewer@company.com',
                firstName: 'View',
                lastName: 'Only',
                role: 'viewer',
                status: 'inactive',
                lastLogin: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
                createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
                twoFactorEnabled: false
            }
        ];

        this.roles = [
            {
                id: 'admin',
                name: 'Administrator',
                description: 'Full system access and configuration',
                permissions: ['all']
            },
            {
                id: 'operator',
                name: 'Operator',
                description: 'Monitor cameras and manage detections',
                permissions: ['cameras.view', 'cameras.manage', 'detections.view', 'detections.manage', 'alerts.view']
            },
            {
                id: 'viewer',
                name: 'Viewer',
                description: 'Read-only access to system data',
                permissions: ['cameras.view', 'detections.view', 'alerts.view']
            }
        ];
    }

    render() {
        const container = document.getElementById('settings');
        if (!container) return;

        container.innerHTML = this.getTemplate();
        this.renderCurrentSection();
    }

    getTemplate() {
        return `
            <div class="page-header">
                <h1 class="page-title">Settings</h1>
                <p class="page-subtitle">System configuration and user management</p>
            </div>
            
            <!-- Settings Navigation -->
            <div class="settings-layout">
                <div class="settings-sidebar">
                    <nav class="settings-nav">
                        <button class="nav-item ${this.currentSection === 'general' ? 'active' : ''}" data-section="general">
                            <i class="fas fa-cog"></i>
                            <span>General</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'detection' ? 'active' : ''}" data-section="detection">
                            <i class="fas fa-search"></i>
                            <span>Detection</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'cameras' ? 'active' : ''}" data-section="cameras">
                            <i class="fas fa-video"></i>
                            <span>Cameras</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'storage' ? 'active' : ''}" data-section="storage">
                            <i class="fas fa-hdd"></i>
                            <span>Storage</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'alerts' ? 'active' : ''}" data-section="alerts">
                            <i class="fas fa-bell"></i>
                            <span>Alerts</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'security' ? 'active' : ''}" data-section="security">
                            <i class="fas fa-shield-alt"></i>
                            <span>Security</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'api' ? 'active' : ''}" data-section="api">
                            <i class="fas fa-code"></i>
                            <span>API</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'users' ? 'active' : ''}" data-section="users">
                            <i class="fas fa-users"></i>
                            <span>Users</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'roles' ? 'active' : ''}" data-section="roles">
                            <i class="fas fa-user-shield"></i>
                            <span>Roles</span>
                        </button>
                        <button class="nav-item ${this.currentSection === 'backup' ? 'active' : ''}" data-section="backup">
                            <i class="fas fa-download"></i>
                            <span>Backup</span>
                        </button>
                    </nav>
                </div>
                
                <div class="settings-main">
                    <!-- Unsaved Changes Bar -->
                    <div class="unsaved-changes-bar" id="unsaved-changes-bar" style="display: none;">
                        <div class="unsaved-message">
                            <i class="fas fa-exclamation-triangle"></i>
                            <span>You have unsaved changes</span>
                        </div>
                        <div class="unsaved-actions">
                            <button class="btn btn-small btn-secondary" id="discard-changes-btn">Discard</button>
                            <button class="btn btn-small btn-primary" id="save-changes-btn">Save Changes</button>
                        </div>
                    </div>
                    
                    <!-- Settings Content -->
                    <div class="settings-content" id="settings-content">
                        <!-- Content will be dynamically loaded -->
                    </div>
                </div>
            </div>
        `;
    }

    renderCurrentSection() {
        const container = document.getElementById('settings-content');
        if (!container) return;

        switch (this.currentSection) {
            case 'general':
                container.innerHTML = this.renderGeneralSettings();
                break;
            case 'detection':
                container.innerHTML = this.renderDetectionSettings();
                break;
            case 'cameras':
                container.innerHTML = this.renderCameraSettings();
                break;
            case 'storage':
                container.innerHTML = this.renderStorageSettings();
                break;
            case 'alerts':
                container.innerHTML = this.renderAlertSettings();
                break;
            case 'security':
                container.innerHTML = this.renderSecuritySettings();
                break;
            case 'api':
                container.innerHTML = this.renderApiSettings();
                break;
            case 'users':
                container.innerHTML = this.renderUserManagement();
                break;
            case 'roles':
                container.innerHTML = this.renderRoleManagement();
                break;
            case 'backup':
                container.innerHTML = this.renderBackupRestore();
                break;
        }

        this.attachSectionEventListeners();
    }

    renderGeneralSettings() {
        const settings = this.settings.general;
        
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>General Settings</h3>
                    <p>Basic system configuration and preferences</p>
                </div>
                
                <div class="settings-form">
                    <div class="form-group">
                        <label for="system-name">System Name</label>
                        <input type="text" id="system-name" class="form-input" value="${settings.systemName}" data-setting="general.systemName">
                        <small class="form-help">Display name for the system</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="timezone">Timezone</label>
                        <select id="timezone" class="form-select" data-setting="general.timezone">
                            <option value="America/New_York" ${settings.timezone === 'America/New_York' ? 'selected' : ''}>Eastern Time</option>
                            <option value="America/Chicago" ${settings.timezone === 'America/Chicago' ? 'selected' : ''}>Central Time</option>
                            <option value="America/Denver" ${settings.timezone === 'America/Denver' ? 'selected' : ''}>Mountain Time</option>
                            <option value="America/Los_Angeles" ${settings.timezone === 'America/Los_Angeles' ? 'selected' : ''}>Pacific Time</option>
                        </select>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="date-format">Date Format</label>
                            <select id="date-format" class="form-select" data-setting="general.dateFormat">
                                <option value="MM/DD/YYYY" ${settings.dateFormat === 'MM/DD/YYYY' ? 'selected' : ''}>MM/DD/YYYY</option>
                                <option value="DD/MM/YYYY" ${settings.dateFormat === 'DD/MM/YYYY' ? 'selected' : ''}>DD/MM/YYYY</option>
                                <option value="YYYY-MM-DD" ${settings.dateFormat === 'YYYY-MM-DD' ? 'selected' : ''}>YYYY-MM-DD</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="time-format">Time Format</label>
                            <select id="time-format" class="form-select" data-setting="general.timeFormat">
                                <option value="12" ${settings.timeFormat === '12' ? 'selected' : ''}>12 Hour</option>
                                <option value="24" ${settings.timeFormat === '24' ? 'selected' : ''}>24 Hour</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="language">Language</label>
                        <select id="language" class="form-select" data-setting="general.language">
                            <option value="en" ${settings.language === 'en' ? 'selected' : ''}>English</option>
                            <option value="es" ${settings.language === 'es' ? 'selected' : ''}>Spanish</option>
                            <option value="fr" ${settings.language === 'fr' ? 'selected' : ''}>French</option>
                        </select>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="auto-logout">Auto Logout (minutes)</label>
                            <input type="number" id="auto-logout" class="form-input" value="${settings.autoLogout}" min="5" max="120" data-setting="general.autoLogout">
                        </div>
                        
                        <div class="form-group">
                            <label for="session-timeout">Session Timeout (minutes)</label>
                            <input type="number" id="session-timeout" class="form-input" value="${settings.sessionTimeout}" min="30" max="480" data-setting="general.sessionTimeout">
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderDetectionSettings() {
        const settings = this.settings.detection;
        
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>Detection Settings</h3>
                    <p>Configure license plate detection parameters</p>
                </div>
                
                <div class="settings-form">
                    <div class="form-group">
                        <label for="confidence">Detection Confidence Threshold (%)</label>
                        <div class="range-input">
                            <input type="range" id="confidence" class="form-range" min="50" max="95" value="${settings.confidence}" data-setting="detection.confidence">
                            <span class="range-value">${settings.confidence}%</span>
                        </div>
                        <small class="form-help">Minimum confidence required for valid detections</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="max-detections">Maximum Detections per Frame</label>
                        <input type="number" id="max-detections" class="form-input" value="${settings.maxDetections}" min="1" max="50" data-setting="detection.maxDetections">
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.enableEnhancement ? 'checked' : ''} data-setting="detection.enableEnhancement">
                            <span class="checkbox-custom"></span>
                            Enable Image Enhancement
                        </label>
                        <small class="form-help">Improve image quality before OCR processing</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="enhancement-level">Enhancement Level</label>
                        <select id="enhancement-level" class="form-select" data-setting="detection.enhancementLevel">
                            <option value="low" ${settings.enhancementLevel === 'low' ? 'selected' : ''}>Low</option>
                            <option value="medium" ${settings.enhancementLevel === 'medium' ? 'selected' : ''}>Medium</option>
                            <option value="high" ${settings.enhancementLevel === 'high' ? 'selected' : ''}>High</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="ocr-engine">OCR Engine</label>
                        <select id="ocr-engine" class="form-select" data-setting="detection.ocrEngine">
                            <option value="easyocr" ${settings.ocrEngine === 'easyocr' ? 'selected' : ''}>EasyOCR</option>
                            <option value="tesseract" ${settings.ocrEngine === 'tesseract' ? 'selected' : ''}>Tesseract</option>
                            <option value="paddleocr" ${settings.ocrEngine === 'paddleocr' ? 'selected' : ''}>PaddleOCR</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Supported Plate Formats</label>
                        <div class="checkbox-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.plateFormats.includes('US') ? 'checked' : ''} data-setting="detection.plateFormats" value="US">
                                <span class="checkbox-custom"></span>
                                US Format
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.plateFormats.includes('CA') ? 'checked' : ''} data-setting="detection.plateFormats" value="CA">
                                <span class="checkbox-custom"></span>
                                Canadian Format
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.plateFormats.includes('EU') ? 'checked' : ''} data-setting="detection.plateFormats" value="EU">
                                <span class="checkbox-custom"></span>
                                European Format
                            </label>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="min-plate-size">Minimum Plate Size (pixels)</label>
                            <input type="number" id="min-plate-size" class="form-input" value="${settings.minPlateSize}" min="20" max="200" data-setting="detection.minPlateSize">
                        </div>
                        
                        <div class="form-group">
                            <label for="max-plate-size">Maximum Plate Size (pixels)</label>
                            <input type="number" id="max-plate-size" class="form-input" value="${settings.maxPlateSize}" min="100" max="1000" data-setting="detection.maxPlateSize">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.enableBoundingBox ? 'checked' : ''} data-setting="detection.enableBoundingBox">
                            <span class="checkbox-custom"></span>
                            Show Detection Bounding Boxes
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.saveDetectionImages ? 'checked' : ''} data-setting="detection.saveDetectionImages">
                            <span class="checkbox-custom"></span>
                            Save Detection Images
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label for="compression-quality">Image Compression Quality (%)</label>
                        <div class="range-input">
                            <input type="range" id="compression-quality" class="form-range" min="30" max="100" value="${settings.compressionQuality}" data-setting="detection.compressionQuality">
                            <span class="range-value">${settings.compressionQuality}%</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderCameraSettings() {
        const settings = this.settings.cameras;
        
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>Camera Settings</h3>
                    <p>Default camera configuration and connection parameters</p>
                </div>
                
                <div class="settings-form">
                    <div class="form-group">
                        <label for="max-cameras">Maximum Cameras</label>
                        <input type="number" id="max-cameras" class="form-input" value="${settings.maxCameras}" min="1" max="64" data-setting="cameras.maxCameras">
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="default-resolution">Default Resolution</label>
                            <select id="default-resolution" class="form-select" data-setting="cameras.defaultResolution">
                                <option value="640x480" ${settings.defaultResolution === '640x480' ? 'selected' : ''}>640x480</option>
                                <option value="1280x720" ${settings.defaultResolution === '1280x720' ? 'selected' : ''}>1280x720 (HD)</option>
                                <option value="1920x1080" ${settings.defaultResolution === '1920x1080' ? 'selected' : ''}>1920x1080 (Full HD)</option>
                                <option value="3840x2160" ${settings.defaultResolution === '3840x2160' ? 'selected' : ''}>3840x2160 (4K)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="default-fps">Default Frame Rate</label>
                            <select id="default-fps" class="form-select" data-setting="cameras.defaultFps">
                                <option value="15" ${settings.defaultFps === 15 ? 'selected' : ''}>15 FPS</option>
                                <option value="25" ${settings.defaultFps === 25 ? 'selected' : ''}>25 FPS</option>
                                <option value="30" ${settings.defaultFps === 30 ? 'selected' : ''}>30 FPS</option>
                                <option value="60" ${settings.defaultFps === 60 ? 'selected' : ''}>60 FPS</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="connection-timeout">Connection Timeout (seconds)</label>
                            <input type="number" id="connection-timeout" class="form-input" value="${settings.connectionTimeout}" min="5" max="60" data-setting="cameras.connectionTimeout">
                        </div>
                        
                        <div class="form-group">
                            <label for="retry-attempts">Retry Attempts</label>
                            <input type="number" id="retry-attempts" class="form-input" value="${settings.retryAttempts}" min="1" max="10" data-setting="cameras.retryAttempts">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="health-check-interval">Health Check Interval (seconds)</label>
                        <input type="number" id="health-check-interval" class="form-input" value="${settings.healthCheckInterval}" min="30" max="300" data-setting="cameras.healthCheckInterval">
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.enableMotionDetection ? 'checked' : ''} data-setting="cameras.enableMotionDetection">
                            <span class="checkbox-custom"></span>
                            Enable Motion Detection
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label for="motion-sensitivity">Motion Detection Sensitivity</label>
                        <select id="motion-sensitivity" class="form-select" data-setting="cameras.motionSensitivity">
                            <option value="low" ${settings.motionSensitivity === 'low' ? 'selected' : ''}>Low</option>
                            <option value="medium" ${settings.motionSensitivity === 'medium' ? 'selected' : ''}>Medium</option>
                            <option value="high" ${settings.motionSensitivity === 'high' ? 'selected' : ''}>High</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }

    renderStorageSettings() {
        const settings = this.settings.storage;
        
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>Storage Settings</h3>
                    <p>Data retention and storage management</p>
                </div>
                
                <div class="settings-form">
                    <div class="storage-overview">
                        <div class="storage-stat">
                            <div class="stat-icon">
                                <i class="fas fa-hdd"></i>
                            </div>
                            <div class="stat-content">
                                <div class="stat-value">24.8 GB</div>
                                <div class="stat-label">Used Space</div>
                            </div>
                        </div>
                        <div class="storage-stat">
                            <div class="stat-icon">
                                <i class="fas fa-database"></i>
                            </div>
                            <div class="stat-content">
                                <div class="stat-value">75.2 GB</div>
                                <div class="stat-label">Available</div>
                            </div>
                        </div>
                        <div class="storage-stat">
                            <div class="stat-icon">
                                <i class="fas fa-images"></i>
                            </div>
                            <div class="stat-content">
                                <div class="stat-value">1,247</div>
                                <div class="stat-label">Images</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="max-storage-size">Maximum Storage Size (GB)</label>
                        <input type="number" id="max-storage-size" class="form-input" value="${settings.maxStorageSize}" min="10" max="1000" data-setting="storage.maxStorageSize">
                    </div>
                    
                    <div class="form-group">
                        <label for="retention-period">Data Retention Period (days)</label>
                        <input type="number" id="retention-period" class="form-input" value="${settings.retentionPeriod}" min="7" max="365" data-setting="storage.retentionPeriod">
                        <small class="form-help">Automatically delete data older than this period</small>
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.autoCleanup ? 'checked' : ''} data-setting="storage.autoCleanup">
                            <span class="checkbox-custom"></span>
                            Enable Automatic Cleanup
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label for="cleanup-schedule">Cleanup Schedule (Cron)</label>
                        <input type="text" id="cleanup-schedule" class="form-input" value="${settings.cleanupSchedule}" data-setting="storage.cleanupSchedule">
                        <small class="form-help">When to run automatic cleanup (e.g., 0 2 * * * for 2 AM daily)</small>
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.backupEnabled ? 'checked' : ''} data-setting="storage.backupEnabled">
                            <span class="checkbox-custom"></span>
                            Enable Automatic Backup
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label for="backup-location">Backup Location</label>
                        <input type="text" id="backup-location" class="form-input" value="${settings.backupLocation}" placeholder="/path/to/backup/location" data-setting="storage.backupLocation">
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.compressionEnabled ? 'checked' : ''} data-setting="storage.compressionEnabled">
                            <span class="checkbox-custom"></span>
                            Enable Data Compression
                        </label>
                    </div>
                    
                    <div class="storage-actions">
                        <button class="btn btn-secondary" id="cleanup-now-btn">
                            <i class="fas fa-broom"></i>
                            Run Cleanup Now
                        </button>
                        <button class="btn btn-secondary" id="backup-now-btn">
                            <i class="fas fa-download"></i>
                            Backup Now
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderAlertSettings() {
        const settings = this.settings.alerts;
        
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>Alert Settings</h3>
                    <p>Configure notification methods and alert thresholds</p>
                </div>
                
                <div class="settings-form">
                    <div class="subsection">
                        <h4>Email Notifications</h4>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.enableEmailAlerts ? 'checked' : ''} data-setting="alerts.enableEmailAlerts">
                                <span class="checkbox-custom"></span>
                                Enable Email Alerts
                            </label>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="email-server">SMTP Server</label>
                                <input type="text" id="email-server" class="form-input" value="${settings.emailServer}" data-setting="alerts.emailServer">
                            </div>
                            
                            <div class="form-group">
                                <label for="email-port">SMTP Port</label>
                                <input type="number" id="email-port" class="form-input" value="${settings.emailPort}" data-setting="alerts.emailPort">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="email-username">Username</label>
                                <input type="email" id="email-username" class="form-input" value="${settings.emailUsername}" data-setting="alerts.emailUsername">
                            </div>
                            
                            <div class="form-group">
                                <label for="email-password">Password</label>
                                <input type="password" id="email-password" class="form-input" value="${settings.emailPassword}" data-setting="alerts.emailPassword">
                            </div>
                        </div>
                        
                        <button class="btn btn-secondary" id="test-email-btn">
                            <i class="fas fa-envelope"></i>
                            Send Test Email
                        </button>
                    </div>
                    
                    <div class="subsection">
                        <h4>SMS Notifications</h4>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.enableSmsAlerts ? 'checked' : ''} data-setting="alerts.enableSmsAlerts">
                                <span class="checkbox-custom"></span>
                                Enable SMS Alerts
                            </label>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="sms-provider">SMS Provider</label>
                                <select id="sms-provider" class="form-select" data-setting="alerts.smsProvider">
                                    <option value="">Select Provider</option>
                                    <option value="twilio" ${settings.smsProvider === 'twilio' ? 'selected' : ''}>Twilio</option>
                                    <option value="aws-sns" ${settings.smsProvider === 'aws-sns' ? 'selected' : ''}>AWS SNS</option>
                                    <option value="nexmo" ${settings.smsProvider === 'nexmo' ? 'selected' : ''}>Nexmo</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="sms-api-key">API Key</label>
                                <input type="password" id="sms-api-key" class="form-input" value="${settings.smsApiKey}" data-setting="alerts.smsApiKey">
                            </div>
                        </div>
                    </div>
                    
                    <div class="subsection">
                        <h4>Alert Delays</h4>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="critical-alert-delay">Critical Alert Delay (minutes)</label>
                                <input type="number" id="critical-alert-delay" class="form-input" value="${settings.criticalAlertDelay}" min="0" max="60" data-setting="alerts.criticalAlertDelay">
                            </div>
                            
                            <div class="form-group">
                                <label for="warning-alert-delay">Warning Alert Delay (minutes)</label>
                                <input type="number" id="warning-alert-delay" class="form-input" value="${settings.warningAlertDelay}" min="0" max="60" data-setting="alerts.warningAlertDelay">
                            </div>
                            
                            <div class="form-group">
                                <label for="info-alert-delay">Info Alert Delay (minutes)</label>
                                <input type="number" id="info-alert-delay" class="form-input" value="${settings.infoAlertDelay}" min="0" max="60" data-setting="alerts.infoAlertDelay">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderSecuritySettings() {
        const settings = this.settings.security;
        
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>Security Settings</h3>
                    <p>Authentication, authorization, and security policies</p>
                </div>
                
                <div class="settings-form">
                    <div class="subsection">
                        <h4>Authentication</h4>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.enableTwoFactor ? 'checked' : ''} data-setting="security.enableTwoFactor">
                                <span class="checkbox-custom"></span>
                                Enable Two-Factor Authentication
                            </label>
                        </div>
                        
                        <div class="form-group">
                            <label for="password-min-length">Minimum Password Length</label>
                            <input type="number" id="password-min-length" class="form-input" value="${settings.passwordMinLength}" min="6" max="32" data-setting="security.passwordMinLength">
                        </div>
                        
                        <div class="form-group">
                            <label>Password Requirements</label>
                            <div class="checkbox-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" ${settings.passwordRequireSpecial ? 'checked' : ''} data-setting="security.passwordRequireSpecial">
                                    <span class="checkbox-custom"></span>
                                    Require Special Characters
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" ${settings.passwordRequireNumbers ? 'checked' : ''} data-setting="security.passwordRequireNumbers">
                                    <span class="checkbox-custom"></span>
                                    Require Numbers
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" ${settings.passwordRequireUppercase ? 'checked' : ''} data-setting="security.passwordRequireUppercase">
                                    <span class="checkbox-custom"></span>
                                    Require Uppercase Letters
                                </label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="subsection">
                        <h4>Session Management</h4>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="max-login-attempts">Max Login Attempts</label>
                                <input type="number" id="max-login-attempts" class="form-input" value="${settings.maxLoginAttempts}" min="1" max="10" data-setting="security.maxLoginAttempts">
                            </div>
                            
                            <div class="form-group">
                                <label for="lockout-duration">Lockout Duration (minutes)</label>
                                <input type="number" id="lockout-duration" class="form-input" value="${settings.lockoutDuration}" min="1" max="60" data-setting="security.lockoutDuration">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="session-token-expiry">Session Token Expiry (hours)</label>
                            <input type="number" id="session-token-expiry" class="form-input" value="${settings.sessionTokenExpiry}" min="1" max="168" data-setting="security.sessionTokenExpiry">
                        </div>
                    </div>
                    
                    <div class="subsection">
                        <h4>Access Control</h4>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.enableAuditLog ? 'checked' : ''} data-setting="security.enableAuditLog">
                                <span class="checkbox-custom"></span>
                                Enable Audit Logging
                            </label>
                        </div>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.enableIpWhitelist ? 'checked' : ''} data-setting="security.enableIpWhitelist">
                                <span class="checkbox-custom"></span>
                                Enable IP Whitelist
                            </label>
                        </div>
                        
                        <div class="form-group">
                            <label for="allowed-ips">Allowed IP Addresses</label>
                            <textarea id="allowed-ips" class="form-textarea" rows="4" placeholder="192.168.1.0/24&#10;10.0.0.1&#10;203.0.113.0/24" data-setting="security.allowedIps">${settings.allowedIps.join('\n')}</textarea>
                            <small class="form-help">One IP address or CIDR block per line</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderApiSettings() {
        const settings = this.settings.api;
        
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>API Settings</h3>
                    <p>Configure API access and integration settings</p>
                </div>
                
                <div class="settings-form">
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.enableApi ? 'checked' : ''} data-setting="api.enableApi">
                            <span class="checkbox-custom"></span>
                            Enable API Access
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" ${settings.apiKeyRequired ? 'checked' : ''} data-setting="api.apiKeyRequired">
                            <span class="checkbox-custom"></span>
                            Require API Key Authentication
                        </label>
                    </div>
                    
                    <div class="subsection">
                        <h4>Rate Limiting</h4>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.rateLimitEnabled ? 'checked' : ''} data-setting="api.rateLimitEnabled">
                                <span class="checkbox-custom"></span>
                                Enable Rate Limiting
                            </label>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="rate-limit-requests">Max Requests</label>
                                <input type="number" id="rate-limit-requests" class="form-input" value="${settings.rateLimitRequests}" min="100" max="10000" data-setting="api.rateLimitRequests">
                            </div>
                            
                            <div class="form-group">
                                <label for="rate-limit-window">Time Window (seconds)</label>
                                <input type="number" id="rate-limit-window" class="form-input" value="${settings.rateLimitWindow}" min="60" max="86400" data-setting="api.rateLimitWindow">
                            </div>
                        </div>
                    </div>
                    
                    <div class="subsection">
                        <h4>CORS Settings</h4>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.enableCors ? 'checked' : ''} data-setting="api.enableCors">
                                <span class="checkbox-custom"></span>
                                Enable CORS
                            </label>
                        </div>
                        
                        <div class="form-group">
                            <label for="allowed-origins">Allowed Origins</label>
                            <textarea id="allowed-origins" class="form-textarea" rows="3" placeholder="https://example.com&#10;https://app.example.com&#10;*" data-setting="api.allowedOrigins">${settings.allowedOrigins.join('\n')}</textarea>
                            <small class="form-help">One origin per line. Use * for all origins</small>
                        </div>
                    </div>
                    
                    <div class="subsection">
                        <h4>Webhooks</h4>
                        
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" ${settings.enableWebhooks ? 'checked' : ''} data-setting="api.enableWebhooks">
                                <span class="checkbox-custom"></span>
                                Enable Webhooks
                            </label>
                        </div>
                        
                        <div class="form-group">
                            <label for="webhook-url">Webhook URL</label>
                            <input type="url" id="webhook-url" class="form-input" value="${settings.webhookUrl}" placeholder="https://your-app.com/webhook" data-setting="api.webhookUrl">
                        </div>
                        
                        <div class="form-group">
                            <label for="webhook-secret">Webhook Secret</label>
                            <input type="password" id="webhook-secret" class="form-input" value="${settings.webhookSecret}" data-setting="api.webhookSecret">
                        </div>
                        
                        <button class="btn btn-secondary" id="test-webhook-btn">
                            <i class="fas fa-link"></i>
                            Test Webhook
                        </button>
                    </div>
                    
                    <div class="api-info">
                        <h4>API Information</h4>
                        <div class="info-item">
                            <label>Base URL:</label>
                            <code>${config.API_BASE_URL}${config.API_ENDPOINTS.CAMERAS.slice(0, -1)}</code>
                        </div>
                        <div class="info-item">
                            <label>Documentation:</label>
                            <a href="/api/docs" target="_blank">View API Documentation</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderUserManagement() {
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>User Management</h3>
                    <p>Manage system users and their access</p>
                    <button class="btn btn-primary" id="add-user-btn">
                        <i class="fas fa-plus"></i>
                        Add User
                    </button>
                </div>
                
                <div class="users-table">
                    <div class="table-header">
                        <div class="header-cell">User</div>
                        <div class="header-cell">Role</div>
                        <div class="header-cell">Status</div>
                        <div class="header-cell">Last Login</div>
                        <div class="header-cell">Actions</div>
                    </div>
                    
                    ${this.users.map(user => `
                        <div class="table-row ${user.status}">
                            <div class="table-cell user-info">
                                <div class="user-avatar">
                                    <i class="fas fa-user"></i>
                                </div>
                                <div class="user-details">
                                    <div class="user-name">${user.firstName} ${user.lastName}</div>
                                    <div class="user-email">${user.email}</div>
                                    <div class="user-username">@${user.username}</div>
                                </div>
                            </div>
                            <div class="table-cell">
                                <span class="role-badge ${user.role}">${this.capitalizeFirst(user.role)}</span>
                            </div>
                            <div class="table-cell">
                                <span class="status-badge ${user.status}">${this.capitalizeFirst(user.status)}</span>
                                ${user.twoFactorEnabled ? '<i class="fas fa-shield-alt" title="2FA Enabled"></i>' : ''}
                            </div>
                            <div class="table-cell">
                                <span class="last-login">${this.getRelativeTime(user.lastLogin)}</span>
                            </div>
                            <div class="table-cell actions">
                                <button class="action-btn edit" data-action="edit-user" data-user-id="${user.id}" title="Edit User">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="action-btn ${user.status === 'active' ? 'warning' : 'success'}" data-action="toggle-status" data-user-id="${user.id}" title="${user.status === 'active' ? 'Deactivate' : 'Activate'} User">
                                    <i class="fas ${user.status === 'active' ? 'fa-pause' : 'fa-play'}"></i>
                                </button>
                                <button class="action-btn danger" data-action="delete-user" data-user-id="${user.id}" title="Delete User">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderRoleManagement() {
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>Role Management</h3>
                    <p>Define user roles and permissions</p>
                    <button class="btn btn-primary" id="add-role-btn">
                        <i class="fas fa-plus"></i>
                        Add Role
                    </button>
                </div>
                
                <div class="roles-grid">
                    ${this.roles.map(role => `
                        <div class="role-card">
                            <div class="role-header">
                                <h4>${role.name}</h4>
                                <div class="role-actions">
                                    <button class="action-btn edit" data-action="edit-role" data-role-id="${role.id}" title="Edit Role">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    ${role.id !== 'admin' ? `
                                        <button class="action-btn danger" data-action="delete-role" data-role-id="${role.id}" title="Delete Role">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                            
                            <p class="role-description">${role.description}</p>
                            
                            <div class="role-permissions">
                                <h5>Permissions:</h5>
                                <div class="permissions-list">
                                    ${role.permissions.map(permission => `
                                        <span class="permission-tag">${permission === 'all' ? 'All Permissions' : permission}</span>
                                    `).join('')}
                                </div>
                            </div>
                            
                            <div class="role-users">
                                <h5>Users (${this.users.filter(u => u.role === role.id).length}):</h5>
                                <div class="users-list">
                                    ${this.users.filter(u => u.role === role.id).map(user => `
                                        <span class="user-tag">${user.firstName} ${user.lastName}</span>
                                    `).join('') || '<span class="no-users">No users assigned</span>'}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderBackupRestore() {
        return `
            <div class="settings-section">
                <div class="section-header">
                    <h3>Backup & Restore</h3>
                    <p>Backup system data and restore from previous backups</p>
                </div>
                
                <div class="backup-section">
                    <div class="backup-card">
                        <div class="backup-icon">
                            <i class="fas fa-download"></i>
                        </div>
                        <div class="backup-content">
                            <h4>Create Backup</h4>
                            <p>Create a backup of all system data including settings, users, and detection history</p>
                            <div class="backup-options">
                                <label class="checkbox-label">
                                    <input type="checkbox" checked id="backup-settings">
                                    <span class="checkbox-custom"></span>
                                    System Settings
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" checked id="backup-users">
                                    <span class="checkbox-custom"></span>
                                    Users & Roles
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" checked id="backup-detections">
                                    <span class="checkbox-custom"></span>
                                    Detection History
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" id="backup-images">
                                    <span class="checkbox-custom"></span>
                                    Detection Images
                                </label>
                            </div>
                            <button class="btn btn-primary" id="create-backup-btn">
                                <i class="fas fa-download"></i>
                                Create Backup
                            </button>
                        </div>
                    </div>
                    
                    <div class="backup-card">
                        <div class="backup-icon">
                            <i class="fas fa-upload"></i>
                        </div>
                        <div class="backup-content">
                            <h4>Restore from Backup</h4>
                            <p>Restore system data from a previous backup file</p>
                            <div class="file-upload-area" id="backup-upload-area">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>Drag and drop backup file here or click to browse</p>
                                <input type="file" id="backup-file-input" accept=".zip,.tar.gz" style="display: none;">
                            </div>
                            <button class="btn btn-warning" id="restore-backup-btn" disabled>
                                <i class="fas fa-upload"></i>
                                Restore Backup
                            </button>
                            <small class="form-help warning">Warning: Restoring will overwrite current system data</small>
                        </div>
                    </div>
                </div>
                
                <div class="backup-history">
                    <h4>Backup History</h4>
                    <div class="backup-list">
                        <div class="backup-item">
                            <div class="backup-info">
                                <div class="backup-name">system_backup_2025-01-23_14-30.zip</div>
                                <div class="backup-details">
                                    <span class="backup-date">January 23, 2025 2:30 PM</span>
                                    <span class="backup-size">45.7 MB</span>
                                    <span class="backup-type">Full Backup</span>
                                </div>
                            </div>
                            <div class="backup-actions">
                                <button class="action-btn download" title="Download">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="action-btn restore" title="Restore">
                                    <i class="fas fa-undo"></i>
                                </button>
                                <button class="action-btn danger" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div class="backup-item">
                            <div class="backup-info">
                                <div class="backup-name">system_backup_2025-01-22_02-00.zip</div>
                                <div class="backup-details">
                                    <span class="backup-date">January 22, 2025 2:00 AM</span>
                                    <span class="backup-size">44.2 MB</span>
                                    <span class="backup-type">Scheduled Backup</span>
                                </div>
                            </div>
                            <div class="backup-actions">
                                <button class="action-btn download" title="Download">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="action-btn restore" title="Restore">
                                    <i class="fas fa-undo"></i>
                                </button>
                                <button class="action-btn danger" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => this.changeSection(e.target.dataset.section));
        });

        // Unsaved changes
        document.getElementById('save-changes-btn')?.addEventListener('click', () => this.saveSettings());
        document.getElementById('discard-changes-btn')?.addEventListener('click', () => this.discardChanges());
    }

    attachSectionEventListeners() {
        // Form inputs
        document.querySelectorAll('[data-setting]').forEach(input => {
            input.addEventListener('change', (e) => this.handleSettingChange(e));
            input.addEventListener('input', (e) => this.handleSettingChange(e));
        });

        // Range inputs
        document.querySelectorAll('.form-range').forEach(range => {
            range.addEventListener('input', (e) => {
                const valueSpan = e.target.parentElement.querySelector('.range-value');
                if (valueSpan) {
                    valueSpan.textContent = e.target.value + '%';
                }
            });
        });

        // Storage actions
        document.getElementById('cleanup-now-btn')?.addEventListener('click', () => this.runCleanup());
        document.getElementById('backup-now-btn')?.addEventListener('click', () => this.runBackup());

        // Alert test buttons
        document.getElementById('test-email-btn')?.addEventListener('click', () => this.testEmail());
        document.getElementById('test-webhook-btn')?.addEventListener('click', () => this.testWebhook());

        // User management
        document.getElementById('add-user-btn')?.addEventListener('click', () => this.addUser());
        document.querySelectorAll('[data-action^="edit-user"], [data-action^="toggle-status"], [data-action^="delete-user"]').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleUserAction(e));
        });

        // Role management
        document.getElementById('add-role-btn')?.addEventListener('click', () => this.addRole());
        document.querySelectorAll('[data-action^="edit-role"], [data-action^="delete-role"]').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleRoleAction(e));
        });

        // Backup/Restore
        document.getElementById('create-backup-btn')?.addEventListener('click', () => this.createBackup());
        document.getElementById('backup-upload-area')?.addEventListener('click', () => {
            document.getElementById('backup-file-input').click();
        });
        document.getElementById('backup-file-input')?.addEventListener('change', (e) => this.handleBackupFileSelect(e));
        document.getElementById('restore-backup-btn')?.addEventListener('click', () => this.restoreBackup());
    }

    async loadSettings() {
        // Load settings from server
        console.log('Loading settings...');
    }

    changeSection(section) {
        if (this.unsavedChanges) {
            if (!confirm('You have unsaved changes. Are you sure you want to leave this section?')) {
                return;
            }
        }

        this.currentSection = section;
        
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.section === section);
        });
        
        this.renderCurrentSection();
    }

    handleSettingChange(e) {
        const settingPath = e.target.dataset.setting;
        if (!settingPath) return;

        const [section, key] = settingPath.split('.');
        let value = e.target.value;

        // Handle different input types
        if (e.target.type === 'checkbox') {
            value = e.target.checked;
        } else if (e.target.type === 'number') {
            value = parseInt(value);
        }

        // Handle array settings (like plate formats)
        if (key === 'plateFormats' || key === 'allowedIps' || key === 'allowedOrigins') {
            if (!this.settings[section][key]) {
                this.settings[section][key] = [];
            }
            
            if (e.target.type === 'checkbox') {
                if (value) {
                    this.settings[section][key].push(e.target.value);
                } else {
                    this.settings[section][key] = this.settings[section][key].filter(v => v !== e.target.value);
                }
            } else if (e.target.type === 'textarea') {
                this.settings[section][key] = value.split('\n').filter(v => v.trim());
            }
        } else {
            this.settings[section][key] = value;
        }

        this.markUnsavedChanges();
    }

    markUnsavedChanges() {
        this.unsavedChanges = true;
        const bar = document.getElementById('unsaved-changes-bar');
        if (bar) {
            bar.style.display = 'flex';
        }
    }

    async saveSettings() {
        try {
            // Save settings to server
            console.log('Saving settings:', this.settings);
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.unsavedChanges = false;
            const bar = document.getElementById('unsaved-changes-bar');
            if (bar) {
                bar.style.display = 'none';
            }
            
            this.showToast('Settings saved successfully', 'success');
        } catch (error) {
            this.showToast('Failed to save settings', 'error');
        }
    }

    discardChanges() {
        if (confirm('Are you sure you want to discard all changes?')) {
            this.loadMockData();
            this.unsavedChanges = false;
            const bar = document.getElementById('unsaved-changes-bar');
            if (bar) {
                bar.style.display = 'none';
            }
            this.renderCurrentSection();
            this.showToast('Changes discarded', 'info');
        }
    }

    async runCleanup() {
        if (confirm('Are you sure you want to run cleanup now? This will permanently delete old data.')) {
            try {
                this.showToast('Running cleanup...', 'info');
                // Simulate cleanup
                await new Promise(resolve => setTimeout(resolve, 3000));
                this.showToast('Cleanup completed successfully', 'success');
            } catch (error) {
                this.showToast('Cleanup failed', 'error');
            }
        }
    }

    async runBackup() {
        try {
            this.showToast('Creating backup...', 'info');
            // Simulate backup
            await new Promise(resolve => setTimeout(resolve, 2000));
            this.showToast('Backup created successfully', 'success');
        } catch (error) {
            this.showToast('Backup failed', 'error');
        }
    }

    async testEmail() {
        try {
            this.showToast('Sending test email...', 'info');
            // Simulate email test
            await new Promise(resolve => setTimeout(resolve, 2000));
            this.showToast('Test email sent successfully', 'success');
        } catch (error) {
            this.showToast('Test email failed', 'error');
        }
    }

    async testWebhook() {
        try {
            this.showToast('Testing webhook...', 'info');
            // Simulate webhook test
            await new Promise(resolve => setTimeout(resolve, 1500));
            this.showToast('Webhook test successful', 'success');
        } catch (error) {
            this.showToast('Webhook test failed', 'error');
        }
    }

    addUser() {
        console.log('Add new user');
        // This would open a user creation modal
    }

    handleUserAction(e) {
        const action = e.target.dataset.action;
        const userId = e.target.dataset.userId;
        
        switch (action) {
            case 'edit-user':
                this.editUser(userId);
                break;
            case 'toggle-status':
                this.toggleUserStatus(userId);
                break;
            case 'delete-user':
                this.deleteUser(userId);
                break;
        }
    }

    editUser(userId) {
        console.log('Edit user:', userId);
        // This would open a user edit modal
    }

    toggleUserStatus(userId) {
        const user = this.users.find(u => u.id === userId);
        if (user) {
            user.status = user.status === 'active' ? 'inactive' : 'active';
            this.renderCurrentSection();
            this.showToast(`User ${user.status === 'active' ? 'activated' : 'deactivated'}`, 'success');
        }
    }

    deleteUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (user && confirm(`Are you sure you want to delete user "${user.username}"?`)) {
            this.users = this.users.filter(u => u.id !== userId);
            this.renderCurrentSection();
            this.showToast('User deleted', 'success');
        }
    }

    addRole() {
        console.log('Add new role');
        // This would open a role creation modal
    }

    handleRoleAction(e) {
        const action = e.target.dataset.action;
        const roleId = e.target.dataset.roleId;
        
        switch (action) {
            case 'edit-role':
                this.editRole(roleId);
                break;
            case 'delete-role':
                this.deleteRole(roleId);
                break;
        }
    }

    editRole(roleId) {
        console.log('Edit role:', roleId);
        // This would open a role edit modal
    }

    deleteRole(roleId) {
        const role = this.roles.find(r => r.id === roleId);
        if (role && confirm(`Are you sure you want to delete role "${role.name}"?`)) {
            this.roles = this.roles.filter(r => r.id !== roleId);
            this.renderCurrentSection();
            this.showToast('Role deleted', 'success');
        }
    }

    createBackup() {
        const options = {
            settings: document.getElementById('backup-settings').checked,
            users: document.getElementById('backup-users').checked,
            detections: document.getElementById('backup-detections').checked,
            images: document.getElementById('backup-images').checked
        };
        
        console.log('Creating backup with options:', options);
        this.showToast('Creating backup...', 'info');
        
        // Simulate backup creation
        setTimeout(() => {
            this.showToast('Backup created successfully', 'success');
        }, 3000);
    }

    handleBackupFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            const uploadArea = document.getElementById('backup-upload-area');
            uploadArea.innerHTML = `
                <i class="fas fa-file-archive"></i>
                <p>Selected: ${file.name}</p>
                <small>${(file.size / 1024 / 1024).toFixed(1)} MB</small>
            `;
            document.getElementById('restore-backup-btn').disabled = false;
        }
    }

    restoreBackup() {
        if (confirm('Warning: This will overwrite all current system data. Are you sure you want to continue?')) {
            this.showToast('Restoring backup...', 'info');
            
            // Simulate restore
            setTimeout(() => {
                this.showToast('Backup restored successfully', 'success');
            }, 5000);
        }
    }

    // Utility methods
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

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

export default SettingsPage;