const environment = window.APP_ENV || 'development';

const getCurrentHost = () => {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return window.location.hostname;
    }
    return 'localhost';
};

const currentHost = getCurrentHost();

const configs = {
    development: {
        API_BASE_URL: `http://${currentHost}:8001`,
        WS_BASE_URL: `ws://${currentHost}:8001`,
        RECORDING_API_URL: `http://${currentHost}:8002`
    },
    production: {
        API_BASE_URL: `http://${currentHost}:8001`,
        WS_BASE_URL: `ws://${currentHost}:8001`,
        RECORDING_API_URL: `http://${currentHost}:8002`
    },
    staging: {
        API_BASE_URL: 'https://staging-api.example.com',
        WS_BASE_URL: 'wss://staging-api.example.com',
        RECORDING_API_URL: 'https://staging-recording.example.com'
    }
};

const selectedConfig = configs[environment] || configs.development;

const config = {
    ENV: environment,
    ...selectedConfig,
    
    API_ENDPOINTS: {
        // Camera Management
        CAMERAS: '/api/cameras',
        CAMERA_BY_ID: (id) => `/api/cameras/${id}`,
        CAMERA_SNAPSHOT: (id) => `/api/cameras/${id}/snapshot`,
        CAMERA_HEALTH: (id) => `/api/cameras/${id}/health`,
        CAMERA_TEST_CONNECTION: '/api/cameras/test',
        CAMERA_TEST_ALL_PATHS: '/api/cameras/test-all-paths',
        
        // Recording Management (Removed manual start/stop - now auto-managed)
        CAMERA_RECORDING_QUALITY: (id) => `/api/cameras/${id}/recording/quality`,
        
        // System Health and Monitoring
        SYSTEM_HEALTH: '/api/system/health',
        HEALTH: '/health',
        
        // Playback and Storage
        PLAYBACK: '/api/v1/playback/',
        PLAYBACK_SEGMENTS: (cameraId) => `/api/v1/playbook/cameras/${cameraId}/segments`,
        RECORDINGS: '/api/v1/recordings/',
        RECORDING_STATUS: (cameraId) => `/recordings/status/${cameraId}`,
        RECORDING_SEGMENTS: (cameraId) => `/recordings/${cameraId}/segments`
    },
    
    WS_ENDPOINTS: {
        NOTIFICATIONS: '/ws/notifications',
        CAMERA_HEALTH: '/ws/camera-health',
        RECORDING_STATUS: '/ws/recording-status'
    },
    
    FEATURES: {
        // Core Features
        ENABLE_RECORDING: true,
        ENABLE_PLAYBACK: true,
        ENABLE_DETECTION: true,
        ENABLE_ANALYTICS: true,
        
        // Auto-Recording Management (New)
        AUTO_RECORDING: true,
        HEALTH_MONITORING: true,
        AUTO_RECOVERY: true,
        PREDICTIVE_ALERTS: true,
        
        // UI Features
        NEW_CAMERA_UI: true,
        VLC_INTEGRATION: true,
        MODERN_SETTINGS_MODAL: false,
        VLC_SHOW_PASSWORDS: false,
        MASK_SENSITIVE_DATA: true,
        WEBSOCKET_UPDATES: true,
        
        // Advanced Features (Disabled for now)
        LIVE_MOTION_DETECTION: false,
        GLOBAL_SETTINGS: false,
        ADVANCED_ANALYTICS: false,
        BULK_OPERATIONS: false,
        
        // Performance Features
        LAZY_LOADING: true,
        IMAGE_OPTIMIZATION: true
    },
    
    TIMEOUTS: {
        API_REQUEST: 10000,
        STATUS_POLLING: 30000,
        HEALTH_CHECK: 60000,
        THUMBNAIL_REFRESH: 5000,
        
        // Auto-Recovery Timeouts (New)
        RECOVERY_RETRY: 5000,
        HEALTH_MONITOR: 30000,
        CONNECTION_TIMEOUT: 15000
    },
    
    RETRY: {
        MAX_ATTEMPTS: 3,
        BACKOFF_MULTIPLIER: 2,
        BASE_DELAY: 1000,
        
        // Health Monitoring Retry (New)
        HEALTH_MAX_ATTEMPTS: 5,
        HEALTH_BACKOFF: 1.5,
        HEALTH_BASE_DELAY: 2000
    },
    
    // Health Monitoring Thresholds (New)
    HEALTH_THRESHOLDS: {
        RECORDING_GAP_WARNING: 60000,    // 1 minute gap
        RECORDING_GAP_CRITICAL: 300000,  // 5 minute gap
        ERROR_RATE_WARNING: 0.05,        // 5% error rate
        ERROR_RATE_CRITICAL: 0.15,       // 15% error rate
        DISK_USAGE_WARNING: 0.85,        // 85% disk usage
        DISK_USAGE_CRITICAL: 0.95,       // 95% disk usage
        CAMERA_OFFLINE_WARNING: 30000,   // 30 seconds offline
        CAMERA_OFFLINE_CRITICAL: 120000  // 2 minutes offline
    }
};

// Build API URL helper
config.buildApiUrl = (endpoint) => {
    if (typeof endpoint === 'function') {
        return (...args) => `${config.API_BASE_URL}${endpoint(...args)}`;
    }
    return `${config.API_BASE_URL}${endpoint}`;
};

// Build WebSocket URL helper
config.buildWsUrl = (endpoint) => {
    if (typeof endpoint === 'function') {
        return (...args) => `${config.WS_BASE_URL}${endpoint(...args)}`;
    }
    return `${config.WS_BASE_URL}${endpoint}`;
};

// Build Recording API URL helper
config.buildRecordingUrl = (endpoint) => {
    if (typeof endpoint === 'function') {
        return (...args) => `${config.RECORDING_API_URL}${endpoint(...args)}`;
    }
    return `${config.RECORDING_API_URL}${endpoint}`;
};

// Development logging
if (environment === 'development') {
    console.log('🔧 App Configuration:', {
        environment: config.ENV,
        apiBaseUrl: config.API_BASE_URL,
        wsBaseUrl: config.WS_BASE_URL,
        recordingApiUrl: config.RECORDING_API_URL,
        autoRecording: config.FEATURES.AUTO_RECORDING,
        healthMonitoring: config.FEATURES.HEALTH_MONITORING
    });
}

export default config;