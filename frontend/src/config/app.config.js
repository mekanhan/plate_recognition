/**
 * Application Configuration
 * Centralized configuration for all API endpoints and environment settings
 */

// Determine environment - can be set via window.APP_ENV or defaults to development
const environment = window.APP_ENV || 'development';

// Environment-specific configurations
const configs = {
    development: {
        API_BASE_URL: 'http://localhost:8001',
        WS_BASE_URL: 'ws://localhost:8001',
        RECORDING_API_URL: 'http://localhost:8002'
    },
    production: {
        // In production, use the same origin as the frontend
        API_BASE_URL: window.location.origin,
        WS_BASE_URL: `ws://${window.location.host}`,
        RECORDING_API_URL: `${window.location.origin}:8002`
    },
    staging: {
        // Add staging configuration if needed
        API_BASE_URL: 'https://staging-api.example.com',
        WS_BASE_URL: 'wss://staging-api.example.com',
        RECORDING_API_URL: 'https://staging-recording.example.com'
    }
};

// Select configuration based on environment
const selectedConfig = configs[environment] || configs.development;

// Export configuration object
const config = {
    // Environment name
    ENV: environment,
    
    // Base URLs
    ...selectedConfig,
    
    // API Endpoints - relative paths that will be appended to API_BASE_URL
    API_ENDPOINTS: {
        // Camera endpoints
        CAMERAS: '/api/v1/cameras/',
        CAMERA_BY_ID: (id) => `/api/v1/cameras/${id}`,
        CAMERA_TEST_CONNECTION: '/api/v1/cameras/test-connection',
        
        // Streaming endpoints
        STREAMS: '/api/v1/streams/',
        STREAM_START: (id) => `/api/v1/streams/start/${id}`,
        STREAM_STOP: (id) => `/api/v1/streams/stop/${id}`,
        STREAM_STATUS: (id) => `/api/v1/streams/status/${id}`,
        
        // Video/Image endpoints (no /api/v1 prefix)
        STREAM_VIDEO: (id) => `/stream/video/${id}`,          // Legacy endpoint
        STREAM_MJPEG: (id) => `/stream/mjpeg/${id}`,          // New frame distribution endpoint
        STREAM_SNAPSHOT: (id) => `/stream/snapshot/${id}`,    // New snapshot endpoint
        STREAM_THUMBNAIL: (id) => `/stream/thumbnail/${id}`,  // Legacy thumbnail endpoint
        
        // Playback endpoints
        PLAYBACK: '/api/v1/playback/',
        PLAYBACK_SEGMENTS: (cameraId) => `/api/v1/playback/cameras/${cameraId}/segments`,
        
        // Recording endpoints (on different port)
        RECORDINGS: '/api/v1/recordings/',
        RECORDING_STATUS: (cameraId) => `/recordings/status/${cameraId}`,
        RECORDING_SEGMENTS: (cameraId) => `/recordings/${cameraId}/segments`,
        
        // Health check
        HEALTH: '/health'
    },
    
    // WebSocket endpoints
    WS_ENDPOINTS: {
        STREAM: (cameraId) => `/ws/stream/${cameraId}`,
        NOTIFICATIONS: '/ws/notifications'
    },
    
    // Feature flags
    FEATURES: {
        ENABLE_RECORDING: true,
        ENABLE_PLAYBACK: true,
        ENABLE_DETECTION: true,
        ENABLE_ANALYTICS: true,
        AUTO_START_STREAMS: true
    },
    
    // Timeouts and intervals (in milliseconds)
    TIMEOUTS: {
        API_REQUEST: 10000,        // 10 seconds
        STREAM_INIT: 15000,        // 15 seconds
        STATUS_POLLING: 30000,     // 30 seconds
        HEALTH_CHECK: 60000,       // 1 minute
        THUMBNAIL_REFRESH: 5000    // 5 seconds
    },
    
    // Retry configuration
    RETRY: {
        MAX_ATTEMPTS: 3,
        BACKOFF_MULTIPLIER: 2,
        BASE_DELAY: 1000  // 1 second
    }
};

// Helper function to build full API URL
config.buildApiUrl = (endpoint) => {
    // If endpoint is a function, it's expecting parameters
    if (typeof endpoint === 'function') {
        return (...args) => `${config.API_BASE_URL}${endpoint(...args)}`;
    }
    return `${config.API_BASE_URL}${endpoint}`;
};

// Helper function to build full WebSocket URL
config.buildWsUrl = (endpoint) => {
    if (typeof endpoint === 'function') {
        return (...args) => `${config.WS_BASE_URL}${endpoint(...args)}`;
    }
    return `${config.WS_BASE_URL}${endpoint}`;
};

// Helper function to build recording API URL
config.buildRecordingUrl = (endpoint) => {
    if (typeof endpoint === 'function') {
        return (...args) => `${config.RECORDING_API_URL}${endpoint(...args)}`;
    }
    return `${config.RECORDING_API_URL}${endpoint}`;
};

// Log configuration on load (only in development)
if (environment === 'development') {
    console.log('App Configuration:', {
        environment: config.ENV,
        apiBaseUrl: config.API_BASE_URL,
        wsBaseUrl: config.WS_BASE_URL,
        recordingApiUrl: config.RECORDING_API_URL
    });
}

export default config;