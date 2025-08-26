/**
 * WebSocket Service for Real-time Updates
 * Handles live camera status, recording status, and motion detection events
 */
import config from '../config/app.config.js';

class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.subscribers = new Map();
        this.isConnected = false;
        this.heartbeatInterval = null;
        this.lastHeartbeat = null;
        
        // Event types we handle
        this.EVENT_TYPES = {
            CAMERA_STATUS: 'camera_status',
            RECORDING_STATUS: 'recording_status',
            MOTION_DETECTION: 'motion_detection',
            SYSTEM_HEALTH: 'system_health',
            ANALYTICS_EVENT: 'analytics_event',
            DETECTION_CONSOLE: 'detection_console'
        };
        
        // Load configuration (async, but don't block constructor)
        this.loadConfiguration();
        
        // Set defaults (will be overridden by config)
        this.setDefaults();
    }
    
    /**
     * Set default values (used before config loads)
     */
    setDefaults() {
        this.LOG_LEVELS = {
            OFF: 0,
            ERROR: 1,
            WARNING: 2,
            INFO: 3,
            DEBUG: 4,
            VERBOSE: 5
        };
        
        this.logLevel = 'INFO';
        this.VERBOSE_ONLY_EVENTS = ['detection_console', 'heartbeat', 'analytics_event'];
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.heartbeatIntervalMs = 30000;
        this.heartbeatTimeoutMs = 60000;
        this.enableHeartbeat = true;
        this.enableAutoReconnect = true;
        this.persistLogLevel = true;
        
        this.setupGlobalLoggingControls();
    }
    
    /**
     * Load configuration from centralized config file
     */
    async loadConfiguration() {
        try {
            const response = await fetch('/config/websocket_config.json');
            if (!response.ok) {
                throw new Error('Failed to load WebSocket config');
            }
            
            const config = await response.json();
            
            // Apply logging configuration
            this.LOG_LEVELS = config.logging.levels;
            this.VERBOSE_ONLY_EVENTS = config.logging.verboseOnlyEvents;
            
            // Load saved log level or use default from config
            const savedLevel = localStorage.getItem('ws_log_level');
            this.logLevel = savedLevel || config.logging.defaultLevel;
            
            // Apply connection configuration
            this.maxReconnectAttempts = config.connection.maxReconnectAttempts;
            this.reconnectDelay = config.connection.initialReconnectDelay;
            this.maxReconnectDelay = config.connection.maxReconnectDelay;
            this.heartbeatIntervalMs = config.connection.heartbeatInterval;
            this.heartbeatTimeoutMs = config.connection.heartbeatTimeout;
            
            // Apply feature flags
            this.enableHeartbeat = config.features.enableHeartbeat;
            this.enableAutoReconnect = config.features.enableAutoReconnect;
            this.persistLogLevel = config.features.persistLogLevel;
            
            // Re-setup logging controls with new config
            if (config.features.enableLoggingControls) {
                this.setupGlobalLoggingControls();
            }
            
            console.log('✅ WebSocket configuration loaded from /config/websocket_config.json');
        } catch (error) {
            console.warn('Using default WebSocket configuration:', error.message);
        }
    }

    /**
     * Setup global logging controls for easy access from browser console
     */
    setupGlobalLoggingControls() {
        if (typeof window !== 'undefined') {
            window.wsLogging = {
                setLevel: (level) => this.setLogLevel(level),
                getLevel: () => this.logLevel,
                levels: () => Object.keys(this.LOG_LEVELS),
                enable: () => this.setLogLevel('VERBOSE'),
                disable: () => this.setLogLevel('OFF'),
                info: () => this.setLogLevel('INFO'),
                debug: () => this.setLogLevel('DEBUG'),
                help: () => {
                    console.log(`
🔧 WebSocket Logging Controls:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• wsLogging.disable()     - Turn off all WebSocket logs
• wsLogging.enable()      - Show all logs (including detections)
• wsLogging.info()        - Show important events only (default)
• wsLogging.debug()       - Show debug info (no detections)
• wsLogging.setLevel(lvl) - Set specific level: ${Object.keys(this.LOG_LEVELS).join(', ')}
• wsLogging.getLevel()    - Current level: ${this.logLevel}
• wsLogging.levels()      - List all available levels
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current level: ${this.logLevel}
                    `);
                }
            };
            
            // Show help on initialization
            console.log('📡 WebSocket logging controls ready. Type "wsLogging.help()" for options.');
        }
    }
    
    /**
     * Set logging level
     */
    setLogLevel(level) {
        if (!this.LOG_LEVELS.hasOwnProperty(level)) {
            console.error(`Invalid log level: ${level}. Valid levels:`, Object.keys(this.LOG_LEVELS));
            return false;
        }
        
        this.logLevel = level;
        localStorage.setItem('ws_log_level', level);
        console.log(`✅ WebSocket log level set to: ${level}`);
        return true;
    }
    
    /**
     * Conditional logging based on level and event type
     */
    log(level, message, ...args) {
        const currentLevel = this.LOG_LEVELS[this.logLevel];
        const messageLevel = this.LOG_LEVELS[level];
        
        if (currentLevel === 0) return; // OFF
        
        if (messageLevel <= currentLevel) {
            const prefix = `[WS:${level}]`;
            
            switch(level) {
                case 'ERROR':
                    console.error(prefix, message, ...args);
                    break;
                case 'WARNING':
                    console.warn(prefix, message, ...args);
                    break;
                default:
                    console.log(prefix, message, ...args);
            }
        }
    }
    
    /**
     * Check if event should be logged based on current settings
     */
    shouldLogEvent(eventType) {
        // If verbose mode, log everything
        if (this.logLevel === 'VERBOSE') return true;
        
        // If event is in verbose-only list, don't log unless in verbose mode
        if (this.VERBOSE_ONLY_EVENTS.includes(eventType)) return false;
        
        // Otherwise, follow normal log level rules
        return this.LOG_LEVELS[this.logLevel] >= this.LOG_LEVELS.INFO;
    }

    connect() {
        if (!config.FEATURES.WEBSOCKET_UPDATES) {
            this.log('INFO', 'WebSocket updates disabled by feature flag');
            return;
        }

        if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
            this.log('DEBUG', 'WebSocket already connected or connecting');
            return;
        }

        try {
            const wsUrl = config.buildWsUrl('/ws/camera-updates');
            this.log('INFO', 'Connecting to WebSocket:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            this.setupEventListeners();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }

    setupEventListeners() {
        this.ws.onopen = (event) => {
            this.log('INFO', 'WebSocket connected successfully');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this.startHeartbeat();
            
            // Notify subscribers of connection
            this.notifySubscribers('connection', { status: 'connected' });
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        this.ws.onclose = (event) => {
            this.log('WARNING', 'WebSocket connection closed:', event.code, event.reason);
            this.isConnected = false;
            this.stopHeartbeat();
            
            // Notify subscribers of disconnection
            this.notifySubscribers('connection', { status: 'disconnected' });
            
            // Attempt to reconnect unless it was a deliberate close
            if (event.code !== 1000) { // 1000 = normal closure
                this.scheduleReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.isConnected = false;
        };
    }

    handleMessage(data) {
        const { type, payload, timestamp } = data;
        
        // Update last heartbeat time
        if (type === 'heartbeat') {
            this.lastHeartbeat = Date.now();
            return;
        }

        // Use smart logging based on event type and log level
        if (this.shouldLogEvent(type)) {
            this.log('DEBUG', `Message received: ${type}`, payload);
        }

        // Route message to appropriate subscribers
        switch (type) {
            case this.EVENT_TYPES.CAMERA_STATUS:
                this.handleCameraStatus(payload);
                break;
            case this.EVENT_TYPES.RECORDING_STATUS:
                this.handleRecordingStatus(payload);
                break;
            case this.EVENT_TYPES.MOTION_DETECTION:
                this.handleMotionDetection(payload);
                break;
            case this.EVENT_TYPES.SYSTEM_HEALTH:
                this.handleSystemHealth(payload);
                break;
            case this.EVENT_TYPES.ANALYTICS_EVENT:
                this.handleAnalyticsEvent(payload);
                break;
            case this.EVENT_TYPES.DETECTION_CONSOLE:
                this.handleDetectionConsole(payload);
                break;
            default:
                this.log('WARNING', 'Unknown WebSocket message type:', type);
        }
    }

    handleCameraStatus(payload) {
        const { camera_id, status, details } = payload;
        
        // Notify camera status subscribers
        this.notifySubscribers('camera_status', {
            cameraId: camera_id,
            status: status,
            details: details,
            timestamp: Date.now()
        });
    }

    handleRecordingStatus(payload) {
        const { camera_id, is_recording, recording_details } = payload;
        
        // Notify recording status subscribers
        this.notifySubscribers('recording_status', {
            cameraId: camera_id,
            isRecording: is_recording,
            details: recording_details,
            timestamp: Date.now()
        });
    }

    handleMotionDetection(payload) {
        const { camera_id, detected, zone, confidence } = payload;
        
        // Notify motion detection subscribers
        this.notifySubscribers('motion_detection', {
            cameraId: camera_id,
            detected: detected,
            zone: zone,
            confidence: confidence,
            timestamp: Date.now()
        });
    }

    handleSystemHealth(payload) {
        // Notify system health subscribers
        this.notifySubscribers('system_health', {
            ...payload,
            timestamp: Date.now()
        });
    }

    handleAnalyticsEvent(payload) {
        const { camera_id, event_type, data } = payload;
        
        // Notify analytics subscribers
        this.notifySubscribers('analytics_event', {
            cameraId: camera_id,
            eventType: event_type,
            data: data,
            timestamp: Date.now()
        });
    }

    handleDetectionConsole(payload) {
        // Forward the entire payload to detection console subscribers
        this.notifySubscribers('detection_console', payload);
    }

    // Subscription management
    subscribe(eventType, callback) {
        if (!this.subscribers.has(eventType)) {
            this.subscribers.set(eventType, new Set());
        }
        
        this.subscribers.get(eventType).add(callback);
        
        // Return unsubscribe function
        return () => {
            const subscribers = this.subscribers.get(eventType);
            if (subscribers) {
                subscribers.delete(callback);
            }
        };
    }

    unsubscribe(eventType, callback) {
        const subscribers = this.subscribers.get(eventType);
        if (subscribers) {
            subscribers.delete(callback);
        }
    }

    notifySubscribers(eventType, data) {
        const subscribers = this.subscribers.get(eventType);
        if (subscribers) {
            subscribers.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in WebSocket subscriber callback:', error);
                }
            });
        }
    }

    // Heartbeat mechanism
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
                
                // Check if we've missed heartbeats
                if (this.lastHeartbeat && Date.now() - this.lastHeartbeat > 60000) { // 1 minute
                    console.warn('WebSocket heartbeat timeout, reconnecting...');
                    this.reconnect();
                }
            }
        }, 30000); // Send ping every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    // Reconnection logic
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max WebSocket reconnection attempts reached');
            this.notifySubscribers('connection', { status: 'failed' });
            return;
        }

        this.reconnectAttempts++;
        this.log('INFO', `Scheduling WebSocket reconnect attempt ${this.reconnectAttempts} in ${this.reconnectDelay}ms`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);

        // Exponential backoff with jitter
        this.reconnectDelay = Math.min(this.reconnectDelay * 2 + Math.random() * 1000, 30000);
    }

    reconnect() {
        if (this.ws) {
            this.ws.close();
        }
        this.connect();
    }

    // Send message to server
    send(type, payload) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: type,
                payload: payload,
                timestamp: Date.now()
            };
            
            this.ws.send(JSON.stringify(message));
            return true;
        } else {
            console.warn('WebSocket not connected, cannot send message');
            return false;
        }
    }

    // Request specific camera status
    requestCameraStatus(cameraId) {
        return this.send('request_camera_status', { camera_id: cameraId });
    }

    // Request all cameras status
    requestAllCamerasStatus() {
        return this.send('request_all_status', {});
    }

    // Cleanup
    disconnect() {
        this.stopHeartbeat();
        
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
        
        this.subscribers.clear();
        this.isConnected = false;
    }

    // Status getters
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            attempts: this.reconnectAttempts,
            lastHeartbeat: this.lastHeartbeat
        };
    }
}

// Create singleton instance
const webSocketService = new WebSocketService();

export default webSocketService;