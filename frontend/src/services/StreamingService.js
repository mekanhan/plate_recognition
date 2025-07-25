/**
 * StreamingService
 * Frontend service for managing video streaming operations
 */

class StreamingService {
    constructor() {
        this.apiBase = 'http://localhost:8001';
        this.activeStreams = new Map();
        this.statusPollingInterval = null;
        this.pollingIntervalMs = 15000; // 15 seconds
        this.eventListeners = new Map();
        this.connectionErrors = new Map(); // Track connection errors per endpoint
        this.maxRetries = 3;
        this.backoffMultiplier = 2;
        this.baseDelay = 1000; // 1 second
    }

    // API Request with Retry Logic
    async makeApiRequest(url, options = {}, retryCount = 0) {
        const endpoint = new URL(url).pathname;
        
        try {
            const response = await fetch(url, {
                timeout: 10000, // 10 second timeout
                ...options
            });
            
            // Reset error count on successful request
            this.connectionErrors.delete(endpoint);
            
            return response;
            
        } catch (error) {
            const errorKey = `${endpoint}_${error.name}`;
            const currentErrors = this.connectionErrors.get(errorKey) || 0;
            
            // Check if we should retry
            if (retryCount < this.maxRetries && this.shouldRetry(error)) {
                const delay = this.calculateBackoffDelay(retryCount);
                
                console.warn(`API request failed (attempt ${retryCount + 1}/${this.maxRetries + 1}), retrying in ${delay}ms:`, error.message);
                
                // Track error
                this.connectionErrors.set(errorKey, currentErrors + 1);
                
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, delay));
                
                // Retry request
                return this.makeApiRequest(url, options, retryCount + 1);
            }
            
            // Max retries reached or non-retryable error
            this.connectionErrors.set(errorKey, currentErrors + 1);
            throw error;
        }
    }
    
    shouldRetry(error) {
        // Retry on network errors, timeouts, and 5xx server errors
        return (
            error.name === 'TypeError' || // Network error
            error.name === 'AbortError' || // Timeout
            error.message.includes('Failed to fetch') ||
            error.message.includes('fetch')
        );
    }
    
    calculateBackoffDelay(retryCount) {
        return this.baseDelay * Math.pow(this.backoffMultiplier, retryCount) + Math.random() * 1000;
    }
    
    isEndpointHealthy(endpoint) {
        const errorKey = `${endpoint}_TypeError`;
        const errors = this.connectionErrors.get(errorKey) || 0;
        return errors < 5; // Consider unhealthy after 5 consecutive errors
    }

    // Event System
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // Stream Management
    async startStream(cameraId, options = {}) {
        try {
            const config = {
                quality: options.quality || 'medium',
                max_fps: options.maxFps || 30,
                detection_enabled: options.detectionEnabled || false,
                confidence_threshold: options.confidenceThreshold || 0.7,
                ...options
            };

            const response = await this.makeApiRequest(`${this.apiBase}/api/v1/streams/start/${cameraId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            // Track active stream
            this.activeStreams.set(cameraId, {
                cameraId,
                status: 'active',
                startTime: new Date(),
                config,
                ...result
            });

            // Emit event
            this.emit('streamStarted', { cameraId, result });

            // Start polling if not already running
            this.startStatusPolling();

            return result;

        } catch (error) {
            console.error(`Failed to start stream for camera ${cameraId}:`, error);
            this.emit('streamError', { cameraId, error: error.message, operation: 'start' });
            throw error;
        }
    }

    async stopStream(cameraId) {
        try {
            const response = await this.makeApiRequest(`${this.apiBase}/api/v1/streams/stop/${cameraId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            // Remove from active streams
            this.activeStreams.delete(cameraId);

            // Emit event
            this.emit('streamStopped', { cameraId, result });

            // Stop polling if no active streams
            if (this.activeStreams.size === 0) {
                this.stopStatusPolling();
            }

            return result;

        } catch (error) {
            console.error(`Failed to stop stream for camera ${cameraId}:`, error);
            this.emit('streamError', { cameraId, error: error.message, operation: 'stop' });
            throw error;
        }
    }

    async getStreamStatus(cameraId) {
        try {
            const response = await this.makeApiRequest(`${this.apiBase}/api/v1/streams/status/${cameraId}`);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const status = await response.json();
            
            // Update local tracking
            if (status.status === 'active') {
                if (!this.activeStreams.has(cameraId)) {
                    this.activeStreams.set(cameraId, {
                        cameraId,
                        status: 'active',
                        startTime: new Date(),
                        ...status
                    });
                }
            } else {
                this.activeStreams.delete(cameraId);
            }

            return status;

        } catch (error) {
            console.error(`Failed to get stream status for camera ${cameraId}:`, error);
            throw error;
        }
    }

    async getAllActiveStreams() {
        try {
            const response = await this.makeApiRequest(`${this.apiBase}/api/v1/streams/`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Update local tracking
            this.activeStreams.clear();
            if (data.streams) {
                data.streams.forEach(stream => {
                    this.activeStreams.set(stream.camera_id, {
                        cameraId: stream.camera_id,
                        status: stream.status,
                        startTime: new Date(stream.started_at || Date.now()),
                        ...stream
                    });
                });
            }

            return data;

        } catch (error) {
            console.error('Failed to get active streams:', error);
            throw error;
        }
    }

    // Camera Operations
    async getCameras() {
        const endpoint = '/api/v1/cameras/';
        
        // Check if endpoint is healthy before making request
        if (!this.isEndpointHealthy(endpoint)) {
            console.warn('Camera endpoint appears unhealthy, skipping request');
            return []; // Return empty array instead of throwing
        }
        
        try {
            const response = await this.makeApiRequest(`${this.apiBase}${endpoint}`);
            
            if (!response.ok) {
                if (response.status >= 500) {
                    throw new Error(`Server error: HTTP ${response.status}`);
                } else if (response.status === 404) {
                    console.warn('Camera endpoint not found, backend may not be running');
                    return [];
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }

            const data = await response.json();
            return data.cameras || [];

        } catch (error) {
            console.error('Failed to get cameras:', error);
            
            // Return empty array on connection errors to prevent UI breakage
            if (error.name === 'TypeError' || error.message.includes('fetch')) {
                console.warn('Backend connection failed, using offline mode');
                return [];
            }
            
            throw error;
        }
    }

    async getCamera(cameraId) {
        const endpoint = `/api/v1/cameras/${cameraId}`;
        
        try {
            const response = await this.makeApiRequest(`${this.apiBase}${endpoint}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error(`Camera ${cameraId} not found`);
                }
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();

        } catch (error) {
            console.error(`Failed to get camera ${cameraId}:`, error);
            throw error;
        }
    }

    // Thumbnail Operations
    getThumbnailUrl(cameraId, options = {}) {
        const params = new URLSearchParams();
        if (options.timestamp !== false) {
            params.append('t', Date.now().toString());
        }
        if (options.width) {
            params.append('width', options.width.toString());
        }
        if (options.height) {
            params.append('height', options.height.toString());
        }

        const queryString = params.toString();
        return `${this.apiBase}/stream/thumbnail/${cameraId}${queryString ? '?' + queryString : ''}`;
    }

    getStreamUrl(cameraId, options = {}) {
        const params = new URLSearchParams();
        if (options.timestamp !== false) {
            params.append('t', Date.now().toString());
        }
        if (options.quality) {
            params.append('quality', options.quality);
        }

        const queryString = params.toString();
        return `${this.apiBase}/stream/video/${cameraId}${queryString ? '?' + queryString : ''}`;
    }

    async refreshThumbnail(cameraId) {
        // Force a new thumbnail by requesting with timestamp
        return this.getThumbnailUrl(cameraId, { timestamp: true });
    }

    // Health Check
    async checkBackendHealth() {
        try {
            const response = await this.makeApiRequest(`${this.apiBase}/health`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Backend health check failed:', error);
            throw error;
        }
    }

    // Status Polling
    startStatusPolling() {
        if (this.statusPollingInterval) {
            return; // Already polling
        }

        this.statusPollingInterval = setInterval(async () => {
            try {
                await this.pollStreamStatuses();
            } catch (error) {
                console.error('Status polling error:', error);
            }
        }, this.pollingIntervalMs);

        console.log('Started stream status polling');
    }

    stopStatusPolling() {
        if (this.statusPollingInterval) {
            clearInterval(this.statusPollingInterval);
            this.statusPollingInterval = null;
            console.log('Stopped stream status polling');
        }
    }

    async pollStreamStatuses() {
        if (this.activeStreams.size === 0) {
            return;
        }

        try {
            const data = await this.getAllActiveStreams();
            
            // Check for streams that were stopped externally
            const serverStreamIds = new Set(data.streams?.map(s => s.camera_id) || []);
            
            for (const [cameraId, streamInfo] of this.activeStreams.entries()) {
                if (!serverStreamIds.has(cameraId)) {
                    // Stream was stopped externally
                    this.activeStreams.delete(cameraId);
                    this.emit('streamStatusChanged', {
                        cameraId,
                        status: 'stopped',
                        reason: 'external'
                    });
                }
            }

            // Emit status update event
            this.emit('statusUpdate', {
                activeStreams: Array.from(this.activeStreams.values()),
                serverData: data
            });

        } catch (error) {
            console.error('Failed to poll stream statuses:', error);
            this.emit('pollingError', { error: error.message });
        }
    }

    // Stream State Queries
    isStreamActive(cameraId) {
        return this.activeStreams.has(cameraId);
    }

    getActiveStreamInfo(cameraId) {
        return this.activeStreams.get(cameraId) || null;
    }

    getAllActiveStreamInfo() {
        return Array.from(this.activeStreams.values());
    }

    getActiveStreamCount() {
        return this.activeStreams.size;
    }

    // Batch Operations
    async startMultipleStreams(cameraIds, options = {}) {
        const results = [];
        const errors = [];

        for (const cameraId of cameraIds) {
            try {
                const result = await this.startStream(cameraId, options);
                results.push({ cameraId, success: true, result });
            } catch (error) {
                errors.push({ cameraId, success: false, error: error.message });
            }
        }

        return { results, errors };
    }

    async stopMultipleStreams(cameraIds) {
        const results = [];
        const errors = [];

        for (const cameraId of cameraIds) {
            try {
                const result = await this.stopStream(cameraId);
                results.push({ cameraId, success: true, result });
            } catch (error) {
                errors.push({ cameraId, success: false, error: error.message });
            }
        }

        return { results, errors };
    }

    async stopAllStreams() {
        const activeStreams = Array.from(this.activeStreams.keys());
        return await this.stopMultipleStreams(activeStreams);
    }

    // Statistics
    getStreamStatistics() {
        const stats = {
            total: this.activeStreams.size,
            byStatus: {},
            durations: {},
            averageDuration: 0
        };

        let totalDuration = 0;
        
        for (const [cameraId, streamInfo] of this.activeStreams.entries()) {
            // Count by status
            const status = streamInfo.status || 'unknown';
            stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;

            // Calculate duration
            const duration = Date.now() - streamInfo.startTime.getTime();
            stats.durations[cameraId] = duration;
            totalDuration += duration;
        }

        if (stats.total > 0) {
            stats.averageDuration = totalDuration / stats.total;
        }

        return stats;
    }

    // Configuration
    setPollingInterval(intervalMs) {
        this.pollingIntervalMs = intervalMs;
        
        if (this.statusPollingInterval) {
            this.stopStatusPolling();
            this.startStatusPolling();
        }
    }

    setApiBase(newApiBase) {
        this.apiBase = newApiBase;
    }

    // Cleanup
    destroy() {
        // Stop all streams
        this.stopAllStreams();
        
        // Stop polling
        this.stopStatusPolling();
        
        // Clear tracking
        this.activeStreams.clear();
        
        // Clear event listeners
        this.eventListeners.clear();
        
        console.log('StreamingService destroyed');
    }
}

// Create singleton instance
const streamingService = new StreamingService();

export default streamingService;