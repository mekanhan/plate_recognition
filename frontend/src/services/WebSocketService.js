import config from '../config/app.config.js';

class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.subscribers = new Map();
        this.isConnected = false;
        this.heartbeatInterval = null;
        this.lastHeartbeat = null;
        
        this.EVENT_TYPES = {
            CAMERA_STATUS: 'camera_status',
            RECORDING_STATUS: 'recording_status',
            MOTION_DETECTION: 'motion_detection',
            SYSTEM_HEALTH: 'system_health',
            ANALYTICS_EVENT: 'analytics_event',
            DETECTION_CONSOLE: 'detection_console'
        };
        
        this.loadConfiguration();
        this.setDefaults();
    }

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

    async loadConfiguration() {
        try {
            const response = await fetch('/config/websocket_config.json');
            if (!response.ok) {
                throw new Error('Failed to load WebSocket config');
            }
            
            const config = await response.json();
            this.LOG_LEVELS = config.logging.levels;
            this.VERBOSE_ONLY_EVENTS = config.logging.verboseOnlyEvents;
            
            const savedLevel = localStorage.getItem('ws_log_level');
            this.logLevel = savedLevel || config.logging.defaultLevel;
            
            this.maxReconnectAttempts = config.connection.maxReconnectAttempts;
            this.reconnectDelay = config.connection.initialReconnectDelay;
            this.maxReconnectDelay = config.connection.maxReconnectDelay;
            this.heartbeatIntervalMs = config.connection.heartbeatInterval;
            this.heartbeatTimeoutMs = config.connection.heartbeatTimeout;
            this.enableHeartbeat = config.features.enableHeartbeat;
            this.enableAutoReconnect = config.features.enableAutoReconnect;
            this.persistLogLevel = config.features.persistLogLevel;
            
            if (config.features.enableLoggingControls) {
                this.setupGlobalLoggingControls();
            }
            
            console.log('✅ WebSocket configuration loaded from /config/websocket_config.json');
        } catch (error) {
            console.warn('Using default WebSocket configuration:', error.message);
        }
    }

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
• wsLogging.disable() - Turn off all WebSocket logs
• wsLogging.enable() - Show all logs (including detections)
• wsLogging.info() - Show important events only (default)
• wsLogging.debug() - Show debug info (no detections)
• wsLogging.setLevel(lvl) - Set specific level: ${Object.keys(this.LOG_LEVELS).join(', ')}
• wsLogging.getLevel() - Current level: ${this.logLevel}
• wsLogging.levels() - List all available levels
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current level: ${this.logLevel}`);
                }
            };
            console.log('📡 WebSocket logging controls ready. Type "wsLogging.help()" for options.');
        }
    }

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

    log(level, message, ...args) {
        const currentLevel = this.LOG_LEVELS[this.logLevel];
        const messageLevel = this.LOG_LEVELS[level];
        
        if (currentLevel === 0) return;
        if (messageLevel <= currentLevel) {
            const prefix = `[WS:${level}]`;
            switch (level) {
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

    shouldLogEvent(eventType) {
        if (this.logLevel === 'VERBOSE') return true;
        if (this.VERBOSE_ONLY_EVENTS.includes(eventType)) return false;
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
            this.notifySubscribers('connection', { status: 'disconnected' });
            
            if (event.code !== 1000) {
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

        if (type === 'heartbeat' || type === 'pong') {
            this.lastHeartbeat = Date.now();
            return;
        }

        if (this.shouldLogEvent(type)) {
            this.log('DEBUG', `Message received: ${type}`, payload);
        }

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
        this.notifySubscribers('camera_status', {
            cameraId: camera_id,
            status: status,
            details: details,
            timestamp: Date.now()
        });
    }

    handleRecordingStatus(payload) {
        const { camera_id, is_recording, recording_details } = payload;
        this.notifySubscribers('recording_status', {
            cameraId: camera_id,
            isRecording: is_recording,
            details: recording_details,
            timestamp: Date.now()
        });
    }

    handleMotionDetection(payload) {
        const { camera_id, detected, zone, confidence } = payload;
        this.notifySubscribers('motion_detection', {
            cameraId: camera_id,
            detected: detected,
            zone: zone,
            confidence: confidence,
            timestamp: Date.now()
        });
    }

    handleSystemHealth(payload) {
        this.notifySubscribers('system_health', {
            ...payload,
            timestamp: Date.now()
        });
    }

    handleAnalyticsEvent(payload) {
        const { camera_id, event_type, data } = payload;
        this.notifySubscribers('analytics_event', {
            cameraId: camera_id,
            eventType: event_type,
            data: data,
            timestamp: Date.now()
        });
    }

    handleDetectionConsole(payload) {
        this.notifySubscribers('detection_console', payload);
    }

    subscribe(eventType, callback) {
        if (!this.subscribers.has(eventType)) {
            this.subscribers.set(eventType, new Set());
        }
        
        this.subscribers.get(eventType).add(callback);
        
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

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
                
                if (this.lastHeartbeat && Date.now() - this.lastHeartbeat > 60000) {
                    console.warn('WebSocket heartbeat timeout, reconnecting...');
                    this.reconnect();
                }
            }
        }, 30000);
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

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

        this.reconnectDelay = Math.min(this.reconnectDelay * 2 + Math.random() * 1000, 30000);
    }

    reconnect() {
        if (this.ws) {
            this.ws.close();
        }
        this.connect();
    }

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

    requestCameraStatus(cameraId) {
        return this.send('request_camera_status', { camera_id: cameraId });
    }

    requestAllCamerasStatus() {
        return this.send('request_all_status', {});
    }

    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
        this.subscribers.clear();
        this.isConnected = false;
    }

    getConnectionStatus() {
        return {
            connected: this.isConnected,
            attempts: this.reconnectAttempts,
            lastHeartbeat: this.lastHeartbeat
        };
    }
}

const webSocketService = new WebSocketService();

export default webSocketService;