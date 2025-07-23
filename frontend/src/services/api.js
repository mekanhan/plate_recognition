/**
 * API Service Layer
 * Centralized API communication for the LPR application
 */
class APIService {
    constructor() {
        this.baseURL = window.location.origin;
        this.apiPrefix = '/api';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
        this.requestTimeout = 30000; // 30 seconds
    }

    /**
     * Generic request method
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${this.apiPrefix}${endpoint}`;
        
        const config = {
            timeout: this.requestTimeout,
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            },
            ...options
        };

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), config.timeout);
            
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new APIError(
                    `HTTP ${response.status}: ${response.statusText}`,
                    response.status,
                    await this.parseErrorResponse(response)
                );
            }

            return await this.parseResponse(response);
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new APIError('Request timeout', 408, { timeout: true });
            }
            
            if (error instanceof APIError) {
                throw error;
            }
            
            throw new APIError('Network error', 0, { network: true, original: error });
        }
    }

    /**
     * Parse response based on content type
     */
    async parseResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        if (contentType && contentType.includes('text/')) {
            return await response.text();
        }
        
        return await response.blob();
    }

    /**
     * Parse error response
     */
    async parseErrorResponse(response) {
        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return { message: await response.text() };
        } catch {
            return { message: 'Unknown error' };
        }
    }

    // HTTP method shortcuts
    async get(endpoint, params = {}) {
        const searchParams = new URLSearchParams(params);
        const queryString = searchParams.toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, { method: 'GET' });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * Upload file
     */
    async upload(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        Object.entries(additionalData).forEach(([key, value]) => {
            formData.append(key, value);
        });

        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            headers: {} // Remove Content-Type to let browser set it for FormData
        });
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, details = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }
}

/**
 * Camera API Service
 */
class CameraService extends APIService {
    constructor() {
        super();
        this.endpoint = '/cameras';
    }

    async getCameras(filters = {}) {
        return this.get(this.endpoint, filters);
    }

    async getCamera(id) {
        return this.get(`${this.endpoint}/${id}`);
    }

    async createCamera(cameraData) {
        return this.post(this.endpoint, cameraData);
    }

    async updateCamera(id, cameraData) {
        return this.put(`${this.endpoint}/${id}`, cameraData);
    }

    async deleteCamera(id) {
        return this.delete(`${this.endpoint}/${id}`);
    }

    async testConnection(connectionData) {
        return this.post(`${this.endpoint}/test-connection`, connectionData);
    }

    async testConnectionEnhanced(connectionData) {
        return this.post(`${this.endpoint}/test-connection-enhanced`, connectionData);
    }

    async discoverCameras(discoveryParams = {}) {
        return this.post(`${this.endpoint}/discover`, discoveryParams);
    }

    async getCameraStreams(cameraId) {
        return this.get(`${this.endpoint}/${cameraId}/streams`);
    }

    async getCameraSnapshot(cameraId, streamId = 'main') {
        return this.get(`${this.endpoint}/${cameraId}/snapshot`, { stream: streamId });
    }

    async startPreview(cameraId, streamId = 'main') {
        return this.post(`${this.endpoint}/${cameraId}/preview`, { stream: streamId });
    }

    async stopPreview(cameraId, sessionId) {
        return this.delete(`${this.endpoint}/${cameraId}/preview/${sessionId}`);
    }

    async getManufacturers() {
        return this.get(`${this.endpoint}/manufacturers`);
    }

    async bulkUpdate(cameraIds, updateData) {
        return this.post(`${this.endpoint}/bulk-update`, {
            camera_ids: cameraIds,
            ...updateData
        });
    }

    async bulkDelete(cameraIds) {
        return this.delete(`${this.endpoint}/bulk-delete`, {
            body: JSON.stringify({ camera_ids: cameraIds }),
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

/**
 * Detection API Service
 */
class DetectionService extends APIService {
    constructor() {
        super();
        this.endpoint = '/detections';
    }

    async getDetections(filters = {}) {
        return this.get(this.endpoint, filters);
    }

    async getDetection(id) {
        return this.get(`${this.endpoint}/${id}`);
    }

    async updateDetection(id, data) {
        return this.put(`${this.endpoint}/${id}`, data);
    }

    async deleteDetection(id) {
        return this.delete(`${this.endpoint}/${id}`);
    }

    async getRecentDetections(limit = 10) {
        return this.get(`${this.endpoint}/recent`, { limit });
    }

    async exportDetections(filters = {}, format = 'csv') {
        return this.get(`${this.endpoint}/export`, { ...filters, format });
    }

    async getDetectionStats(timeframe = '24h') {
        return this.get(`${this.endpoint}/stats`, { timeframe });
    }

    async flagDetection(id, reason = '') {
        return this.post(`${this.endpoint}/${id}/flag`, { reason });
    }

    async verifyDetection(id) {
        return this.post(`${this.endpoint}/${id}/verify`);
    }

    async bulkAction(detectionIds, action, data = {}) {
        return this.post(`${this.endpoint}/bulk-action`, {
            detection_ids: detectionIds,
            action,
            ...data
        });
    }
}

/**
 * System API Service
 */
class SystemService extends APIService {
    constructor() {
        super();
        this.endpoint = '/system';
    }

    async getHealth() {
        return this.get(`${this.endpoint}/health`);
    }

    async getStatus() {
        return this.get(`${this.endpoint}/status`);
    }

    async getMetrics() {
        return this.get(`${this.endpoint}/metrics`);
    }

    async getVersion() {
        return this.get(`${this.endpoint}/version`);
    }

    async getLogs(level = 'info', limit = 100) {
        return this.get(`${this.endpoint}/logs`, { level, limit });
    }

    async runDiagnostics() {
        return this.post(`${this.endpoint}/diagnostics`);
    }

    async getConfiguration() {
        return this.get(`${this.endpoint}/config`);
    }

    async updateConfiguration(config) {
        return this.put(`${this.endpoint}/config`, config);
    }

    async restartService(service) {
        return this.post(`${this.endpoint}/restart`, { service });
    }

    async exportData(dataType, filters = {}) {
        return this.get(`${this.endpoint}/export/${dataType}`, filters);
    }

    async importData(dataType, file) {
        return this.upload(`${this.endpoint}/import/${dataType}`, file);
    }
}

/**
 * API Service Factory
 * Provides access to all API services
 */
class APIServiceFactory {
    constructor() {
        this.camera = new CameraService();
        this.detection = new DetectionService();
        this.system = new SystemService();
    }

    // Global error handler
    static handleError(error) {
        console.error('API Error:', error);
        
        if (error instanceof APIError) {
            switch (error.status) {
                case 401:
                    // Unauthorized - redirect to login
                    window.location.href = '/login';
                    break;
                case 403:
                    // Forbidden - show permission error
                    window.dispatchEvent(new CustomEvent('showError', {
                        detail: 'You do not have permission to perform this action'
                    }));
                    break;
                case 404:
                    // Not found
                    window.dispatchEvent(new CustomEvent('showError', {
                        detail: 'The requested resource was not found'
                    }));
                    break;
                case 408:
                    // Timeout
                    window.dispatchEvent(new CustomEvent('showError', {
                        detail: 'Request timed out. Please try again.'
                    }));
                    break;
                case 500:
                    // Server error
                    window.dispatchEvent(new CustomEvent('showError', {
                        detail: 'Server error. Please try again later.'
                    }));
                    break;
                default:
                    window.dispatchEvent(new CustomEvent('showError', {
                        detail: error.message || 'An unexpected error occurred'
                    }));
            }
        } else {
            window.dispatchEvent(new CustomEvent('showError', {
                detail: 'Network error. Please check your connection.'
            }));
        }
        
        return error;
    }
}

// Create global API instance
const api = new APIServiceFactory();

// Export for module systems
export { APIServiceFactory, APIError, api };
export default api;