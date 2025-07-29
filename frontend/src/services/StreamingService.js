/**
 * StreamingService
 * Frontend service for managing video streaming operations
 */
import config from '../config/app.config.js';

class StreamingService {
    constructor() {
        this.apiBase = config.API_BASE_URL;
        this.activeStreams = new Map();
        this.statusPollingInterval = null;
        this.pollingIntervalMs = config.TIMEOUTS.STATUS_POLLING / 2; // 15 seconds
        this.eventListeners = new Map();
        this.connectionErrors = new Map(); // Track connection errors per endpoint
        this.maxRetries = config.RETRY.MAX_ATTEMPTS;
        this.backoffMultiplier = config.RETRY.BACKOFF_MULTIPLIER;
        this.baseDelay = config.RETRY.BASE_DELAY;
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

    // Fallback camera data when main API is unavailable
    getFallbackCameraData() {
        console.log('📷 Using fallback camera data - API unavailable');
        // Return camera data based on known working stream endpoints
        const fallbackCameras = [
            {
                id: 3,
                name: "Camera 3",
                ip_address: "10.0.0.181",
                port: 554,
                connection_type: "RTSP",
                stream_path: "/h264Preview_01_sub",
                location: "Recording Station",
                enabled: true,
                status: "online",
                username: "admin",
                password: "***",
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            },
            {
                id: 4,
                name: "Demo Camera 4",
                ip_address: "10.0.0.182",
                port: 554,
                connection_type: "RTSP",
                stream_path: "/h264Preview_01_sub",
                location: "Demo Location",
                enabled: true,
                status: "offline",
                username: "admin",
                password: "***",
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            }
        ];
        console.log(`📷 Returning ${fallbackCameras.length} fallback cameras`);
        return fallbackCameras;
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

            const response = await this.makeApiRequest(config.buildApiUrl(config.API_ENDPOINTS.STREAM_START)(cameraId), {
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
            const response = await this.makeApiRequest(config.buildApiUrl(config.API_ENDPOINTS.STREAM_STOP)(cameraId), {
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
            const response = await this.makeApiRequest(config.buildApiUrl(config.API_ENDPOINTS.STREAM_STATUS)(cameraId));
            
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
            const response = await this.makeApiRequest(config.buildApiUrl(config.API_ENDPOINTS.STREAMS));
            
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
    async getCameras(retryCount = 0) {
        const endpoint = config.API_ENDPOINTS.CAMERAS;
        const maxRetries = 3;
        
        console.log(`🔍 Loading cameras from API (attempt ${retryCount + 1}/${maxRetries + 1})...`);
        console.log(`📡 Making request to: ${config.buildApiUrl(endpoint)}`);
        
        try {
            console.log('🚀 Making fetch request with timeout...');
            
            // Create AbortController for timeout
            const controller = new AbortController();
            const timeoutMs = 3000; // Reduced to 3 seconds for faster failures
            const timeoutId = setTimeout(() => {
                console.log(`⏰ Request timeout after ${timeoutMs}ms`);
                controller.abort();
            }, timeoutMs);
            
            const response = await fetch(config.buildApiUrl(endpoint), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            console.log('📨 Got response:', response.status, response.statusText);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            console.log('🔄 Parsing JSON response...');
            const data = await response.json();
            console.log('📝 Parsed data:', data);
            const cameras = data.cameras || [];
            
            if (cameras.length === 0) {
                console.warn('⚠️ API returned empty camera list, using fallback data');
                const fallbackData = this.getFallbackCameraData();
                console.log('📷 Returning fallback data:', fallbackData.length, 'cameras');
                return fallbackData;
            }
            
            console.log(`✅ Successfully loaded ${cameras.length} cameras from API`);
            return cameras;

        } catch (error) {
            console.error(`❌ API request failed (attempt ${retryCount + 1}). Error:`, error.message);
            
            // Retry with exponential backoff if we haven't exceeded max retries
            if (retryCount < maxRetries) {
                const delay = Math.min(1000 * Math.pow(2, retryCount), 5000); // Max 5 second delay
                console.log(`🔄 Retrying in ${delay}ms...`);
                
                await new Promise(resolve => setTimeout(resolve, delay));
                return this.getCameras(retryCount + 1);
            }
            
            // All retries exhausted, use fallback data
            console.error('❌ All retry attempts failed, using fallback data');
            const fallbackData = this.getFallbackCameraData();
            console.log('🔄 Returning fallback camera data:', fallbackData.length, 'cameras');
            return fallbackData;
        }
    }

    async getCamera(cameraId) {
        const endpoint = config.API_ENDPOINTS.CAMERA_BY_ID(cameraId);
        
        try {
            const response = await this.makeApiRequest(config.buildApiUrl(endpoint));
            
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
        return `${this.apiBase}${config.API_ENDPOINTS.STREAM_THUMBNAIL(cameraId)}${queryString ? '?' + queryString : ''}`;
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
        return `${this.apiBase}${config.API_ENDPOINTS.STREAM_VIDEO(cameraId)}${queryString ? '?' + queryString : ''}`;
    }

    async refreshThumbnail(cameraId) {
        // Force a new thumbnail by requesting with timestamp
        return this.getThumbnailUrl(cameraId, { timestamp: true });
    }

    // Health Check
    async checkBackendHealth() {
        try {
            const response = await this.makeApiRequest(config.buildApiUrl(config.API_ENDPOINTS.HEALTH));
            
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