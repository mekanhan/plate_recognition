/**
 * WebSocket Client for Real-time Camera Feeds
 * Connects to the WebSocket multiplexer for live video streaming
 */

class CameraWebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.subscribedCameras = new Set();
        this.messageHandlers = new Map();
        this.isConnected = false;
        
        // Message types
        this.MessageTypes = {
            CAMERA_FRAME: 'camera_frame',
            CAMERA_FRAME_BINARY: 'camera_frame_binary',
            CAMERA_STATUS: 'camera_status',
            DETECTION_RESULT: 'detection_result',
            SYSTEM_STATS: 'system_stats',
            SUBSCRIBE: 'subscribe',
            UNSUBSCRIBE: 'unsubscribe',
            PING: 'ping',
            PONG: 'pong',
            ERROR: 'error'
        };
        
        // Subscription types
        this.SubscriptionTypes = {
            CAMERA_FRAMES: 'camera_frames',
            CAMERA_STATUS: 'camera_status',
            DETECTION_RESULTS: 'detection_results',
            SYSTEM_STATS: 'system_stats',
            ALL: 'all'
        };
    }
    
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws/camera-feeds`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        try {
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }
    
    setupEventHandlers() {
        this.ws.onopen = (event) => {
            console.log('WebSocket connected successfully');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Re-subscribe to cameras if we were subscribed before
            if (this.subscribedCameras.size > 0) {
                this.subscribeToCameraFrames(Array.from(this.subscribedCameras));
            }
            
            // Start ping interval
            this.startPingInterval();
        };
        
        this.ws.onmessage = (event) => {
            this.handleMessage(event);
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            this.isConnected = false;
            this.stopPingInterval();
            
            if (event.code !== 1000) { // Not a normal closure
                this.scheduleReconnect();
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.isConnected = false;
        };
    }
    
    handleMessage(event) {
        try {
            if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
                // Handle binary data (binary frames)
                this.handleBinaryMessage(event.data);
            } else {
                // Handle text data (JSON messages)
                const message = JSON.parse(event.data);
                this.handleTextMessage(message);
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }
    
    handleTextMessage(message) {
        const { type, data, camera_id } = message;
        
        switch (type) {
            case this.MessageTypes.CAMERA_FRAME:
                this.handleCameraFrame(camera_id, data);
                break;
                
            case this.MessageTypes.CAMERA_STATUS:
                this.handleCameraStatus(camera_id, data);
                break;
                
            case this.MessageTypes.DETECTION_RESULT:
                this.handleDetectionResult(camera_id, data);
                break;
                
            case this.MessageTypes.SYSTEM_STATS:
                this.handleSystemStats(data);
                break;
                
            case this.MessageTypes.PONG:
                console.debug('Received pong from server');
                break;
                
            case this.MessageTypes.ERROR:
                console.error('WebSocket error from server:', data.error);
                break;
                
            default:
                console.warn('Unknown message type:', type);
        }
        
        // Call custom handlers
        if (this.messageHandlers.has(type)) {
            this.messageHandlers.get(type)(data, camera_id);
        }
    }
    
    async handleBinaryMessage(data) {
        try {
            // Binary message format: [4 bytes header size][header JSON][binary data]
            const arrayBuffer = data instanceof Blob ? await data.arrayBuffer() : data;
            const dataView = new DataView(arrayBuffer);
            
            // Read header size (first 4 bytes, big endian)
            const headerSize = dataView.getUint32(0, false);
            
            // Extract header JSON
            const headerBytes = new Uint8Array(arrayBuffer, 4, headerSize);
            const headerText = new TextDecoder().decode(headerBytes);
            const header = JSON.parse(headerText);
            
            // Extract binary frame data
            const frameData = new Uint8Array(arrayBuffer, 4 + headerSize);
            
            // Handle binary camera frame
            this.handleBinaryCameraFrame(header.camera_id, frameData, header);
            
        } catch (error) {
            console.error('Error handling binary message:', error);
        }
    }
    
    handleCameraFrame(cameraId, frameData) {
        // Handle base64 encoded frame
        if (frameData.image && frameData.encoding === 'base64') {
            const streamImg = document.getElementById(`camera-stream-${cameraId}`);
            if (streamImg) {
                streamImg.src = `data:image/jpeg;base64,${frameData.image}`;
                streamImg.style.display = 'block';
                
                // Hide placeholder
                const placeholder = streamImg.nextElementSibling;
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
            }
        }
    }
    
    handleBinaryCameraFrame(cameraId, frameData, header) {
        // Handle binary frame data
        const blob = new Blob([frameData], { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);
        
        const streamImg = document.getElementById(`camera-stream-${cameraId}`);
        if (streamImg) {
            // Clean up previous object URL
            if (streamImg.dataset.objectUrl) {
                URL.revokeObjectURL(streamImg.dataset.objectUrl);
            }
            
            streamImg.src = url;
            streamImg.dataset.objectUrl = url;
            streamImg.style.display = 'block';
            
            // Hide placeholder
            const placeholder = streamImg.nextElementSibling;
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            // Update stream info overlay
            const overlay = streamImg.parentNode.querySelector('.stream-overlay');
            if (overlay) {
                overlay.textContent = `LIVE - ${header.quality || 'HD'}`;
            }
        }
    }
    
    handleCameraStatus(cameraId, statusData) {
        console.log('Camera status update:', cameraId, statusData);
        
        // Update camera status indicator
        const cameraCard = document.querySelector(`[data-camera-id="${cameraId}"]`);
        if (cameraCard) {
            const statusElement = cameraCard.querySelector('.camera-status');
            if (statusElement) {
                const isOnline = statusData.status === 'online';
                statusElement.textContent = isOnline ? 'Online' : 'Offline';
                statusElement.className = `camera-status ${isOnline ? 'online' : 'offline'}`;
                statusElement.style.background = isOnline ? '#28a745' : '#dc3545';
            }
        }
    }
    
    handleDetectionResult(cameraId, detectionData) {
        console.log('Detection result:', cameraId, detectionData);
        // TODO: Implement detection result handling (overlay on video, notifications, etc.)
    }
    
    handleSystemStats(statsData) {
        console.debug('System stats:', statsData);
        // TODO: Implement system stats display
    }
    
    subscribeToCameraFrames(cameraIds, options = {}) {
        if (!this.isConnected) {
            console.warn('Cannot subscribe: WebSocket not connected');
            return;
        }
        
        const message = {
            type: this.MessageTypes.SUBSCRIBE,
            subscription: this.SubscriptionTypes.CAMERA_FRAMES,
            camera_ids: Array.isArray(cameraIds) ? cameraIds : [cameraIds],
            streaming_options: {
                binary_mode: options.binaryMode || true,
                compression_enabled: options.compression || true,
                quality_preference: options.quality || 'balanced',
                frame_rate_limit: options.frameRate || 30,
                max_frame_size: options.maxFrameSize || 1024 * 1024
            }
        };
        
        this.ws.send(JSON.stringify(message));
        
        // Track subscribed cameras
        message.camera_ids.forEach(id => this.subscribedCameras.add(id));
        
        console.log('Subscribed to camera frames:', message.camera_ids);
    }
    
    unsubscribeFromCameraFrames(cameraIds) {
        if (!this.isConnected) {
            return;
        }
        
        const message = {
            type: this.MessageTypes.UNSUBSCRIBE,
            subscription: this.SubscriptionTypes.CAMERA_FRAMES,
            camera_ids: Array.isArray(cameraIds) ? cameraIds : [cameraIds]
        };
        
        this.ws.send(JSON.stringify(message));
        
        // Remove from tracked cameras
        message.camera_ids.forEach(id => this.subscribedCameras.delete(id));
        
        console.log('Unsubscribed from camera frames:', message.camera_ids);
    }
    
    subscribeToSystemStats() {
        if (!this.isConnected) {
            return;
        }
        
        const message = {
            type: this.MessageTypes.SUBSCRIBE,
            subscription: this.SubscriptionTypes.SYSTEM_STATS,
            camera_ids: []
        };
        
        this.ws.send(JSON.stringify(message));
        console.log('Subscribed to system stats');
    }
    
    ping() {
        if (this.isConnected) {
            this.ws.send(JSON.stringify({
                type: this.MessageTypes.PING,
                timestamp: Date.now()
            }));
        }
    }
    
    startPingInterval() {
        this.stopPingInterval();
        this.pingInterval = setInterval(() => {
            this.ping();
        }, 30000); // Ping every 30 seconds
    }
    
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }
    
    disconnect() {
        this.stopPingInterval();
        
        if (this.ws) {
            this.ws.close(1000, 'User disconnect');
            this.ws = null;
        }
        
        this.isConnected = false;
        this.subscribedCameras.clear();
    }
    
    // Event handler registration
    onMessage(messageType, handler) {
        this.messageHandlers.set(messageType, handler);
    }
    
    offMessage(messageType) {
        this.messageHandlers.delete(messageType);
    }
}

// Global WebSocket client instance
let cameraWebSocketClient = null;

// Initialize WebSocket client
function initializeWebSocketClient() {
    if (!cameraWebSocketClient) {
        cameraWebSocketClient = new CameraWebSocketClient();
        
        // Set up custom handlers
        cameraWebSocketClient.onMessage('detection_result', (data, cameraId) => {
            // Show detection notification
            showDetectionNotification(cameraId, data);
        });
        
        // Connect to WebSocket
        cameraWebSocketClient.connect();
        
        console.log('WebSocket client initialized');
    }
    
    return cameraWebSocketClient;
}

// Enable WebSocket streaming for a camera
function enableWebSocketStreaming(cameraId) {
    const client = initializeWebSocketClient();
    
    if (client.isConnected) {
        client.subscribeToCameraFrames([cameraId], {
            binaryMode: true,
            compression: true,
            quality: 'balanced',
            frameRate: 15
        });
    } else {
        // Wait for connection and then subscribe
        setTimeout(() => enableWebSocketStreaming(cameraId), 1000);
    }
}

// Disable WebSocket streaming for a camera
function disableWebSocketStreaming(cameraId) {
    if (cameraWebSocketClient) {
        cameraWebSocketClient.unsubscribeFromCameraFrames([cameraId]);
    }
}

// Show detection notification
function showDetectionNotification(cameraId, detection) {
    console.log('Detection on camera', cameraId, ':', detection);
    
    // TODO: Show detection overlay or notification
    // For now, just log to console
}

// Initialize WebSocket client when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Delay initialization to allow other scripts to load
    setTimeout(() => {
        if (window.location.pathname === '/' || window.location.pathname.includes('cameras')) {
            initializeWebSocketClient();
        }
    }, 1000);
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (cameraWebSocketClient) {
        cameraWebSocketClient.disconnect();
    }
});