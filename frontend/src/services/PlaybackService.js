/**
 * Playback Service
 * Handles all video playback and recording-related API calls
 */
import config from '../config/app.config.js';

class PlaybackService {
    constructor() {
        this.baseUrl = config.buildApiUrl(config.API_ENDPOINTS.PLAYBACK);
    }

    /**
     * Get health status of playback system
     */
    async getHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Playback health check failed:', error);
            throw error;
        }
    }

    /**
     * Get video timeline for a camera within a time range
     */
    async getTimeline(cameraId, startTime, endTime) {
        try {
            const params = new URLSearchParams({
                start_time: startTime,
                end_time: endTime
            });
            
            const response = await fetch(`${this.baseUrl}/cameras/${cameraId}/timeline?${params}`);
            
            if (!response.ok) {
                throw new Error(`Timeline request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get timeline:', error);
            throw error;
        }
    }

    /**
     * Get playback info for a specific timestamp
     */
    async getPlaybackInfo(cameraId, timestamp) {
        try {
            const params = new URLSearchParams({
                timestamp: timestamp
            });
            
            const response = await fetch(`${this.baseUrl}/cameras/${cameraId}/info?${params}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    return null; // No recording found for timestamp
                }
                throw new Error(`Playback info request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get playback info:', error);
            throw error;
        }
    }

    /**
     * Get video stream URL for a segment
     */
    getStreamUrl(segmentId) {
        return `${this.baseUrl}/segments/${segmentId}/stream`;
    }

    /**
     * Get segment information
     */
    async getSegmentInfo(segmentId) {
        try {
            const response = await fetch(`${this.baseUrl}/segments/${segmentId}/info`);
            
            if (!response.ok) {
                throw new Error(`Segment info request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get segment info:', error);
            throw error;
        }
    }

    /**
     * Search recordings with criteria
     */
    async searchRecordings(cameraId, startDate, endDate, options = {}) {
        try {
            const params = new URLSearchParams({
                start_date: startDate,
                end_date: endDate
            });
            
            if (options.minDuration) {
                params.append('min_duration', options.minDuration);
            }
            if (options.maxDuration) {
                params.append('max_duration', options.maxDuration);
            }
            
            const response = await fetch(`${this.baseUrl}/cameras/${cameraId}/search?${params}`);
            
            if (!response.ok) {
                throw new Error(`Search request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to search recordings:', error);
            throw error;
        }
    }

    /**
     * Get storage report
     */
    async getStorageReport() {
        try {
            const response = await fetch(`${this.baseUrl}/storage/report`);
            
            if (!response.ok) {
                throw new Error(`Storage report request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get storage report:', error);
            throw error;
        }
    }

    /**
     * Get storage stats for a specific camera
     */
    async getCameraStorageStats(cameraId) {
        try {
            const response = await fetch(`${this.baseUrl}/storage/cameras/${cameraId}/stats`);
            
            if (!response.ok) {
                throw new Error(`Camera storage stats request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get camera storage stats:', error);
            throw error;
        }
    }

    /**
     * Trigger manual storage cleanup
     */
    async triggerCleanup(cameraId = null) {
        try {
            const params = cameraId ? `?camera_id=${cameraId}` : '';
            const response = await fetch(`${this.baseUrl}/storage/cleanup${params}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`Cleanup request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to trigger cleanup:', error);
            throw error;
        }
    }

    /**
     * Format datetime for API calls
     */
    formatDateTime(date) {
        return new Date(date).toISOString().slice(0, 19);
    }

    /**
     * Get today's date range
     */
    getTodayRange() {
        const today = new Date();
        const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        const endOfDay = new Date(startOfDay.getTime() + 24 * 60 * 60 * 1000 - 1);
        
        return {
            start: this.formatDateTime(startOfDay),
            end: this.formatDateTime(endOfDay)
        };
    }

    /**
     * Get date range for last N days
     */
    getLastNDaysRange(days) {
        const end = new Date();
        const start = new Date(end.getTime() - (days * 24 * 60 * 60 * 1000));
        
        return {
            start: this.formatDateTime(start),
            end: this.formatDateTime(end)
        };
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(2)} ${units[unitIndex]}`;
    }

    /**
     * Format duration in seconds to human readable
     */
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

// Export singleton instance
const playbackService = new PlaybackService();
export default playbackService;