/**
 * Playback Service
 * Handles all video playback and recording-related API calls
 * Updated to match implemented backend API (port 8002)
 */
import config from '../config/app.config.js';

class PlaybackService {
    constructor() {
        // Use recording service port 8002
        this.baseUrl = 'http://localhost:8002';
    }

    /**
     * Get health status of recording system
     */
    async getHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Recording service health check failed:', error);
            throw error;
        }
    }

    /**
     * Get recording status for all cameras
     */
    async getRecordingStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/recordings/status`);
            if (!response.ok) {
                throw new Error(`Recording status request failed: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Failed to get recording status:', error);
            throw error;
        }
    }

    /**
     * Get recording status for specific camera
     */
    async getCameraRecordingStatus(cameraId) {
        try {
            const response = await fetch(`${this.baseUrl}/recordings/status/${cameraId}`);
            if (!response.ok) {
                throw new Error(`Camera recording status request failed: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Failed to get camera recording status:', error);
            throw error;
        }
    }

    /**
     * Get calendar data for a camera and month
     */
    async getCalendarData(cameraId, year, month) {
        try {
            const response = await fetch(
                `${this.baseUrl}/api/v1/recordings/cameras/${cameraId}/calendar?year=${year}&month=${month}`
            );
            
            if (!response.ok) {
                throw new Error(`Calendar data request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get calendar data:', error);
            throw error;
        }
    }

    /**
     * Get timeline segments for a specific date
     */
    async getTimelineSegments(cameraId, date, startHour = null, endHour = null) {
        try {
            const params = new URLSearchParams({ date });
            if (startHour !== null) params.append('start_hour', startHour);
            if (endHour !== null) params.append('end_hour', endHour);
            
            const response = await fetch(
                `${this.baseUrl}/api/v1/recordings/cameras/${cameraId}/timeline?${params}`
            );
            
            if (!response.ok) {
                throw new Error(`Timeline request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get timeline segments:', error);
            throw error;
        }
    }

    /**
     * Get video stream URL for a segment
     */
    getStreamUrl(segmentFilename) {
        return `${this.baseUrl}/api/v1/recordings/stream/${segmentFilename}`;
    }

    /**
     * Get recording details for a specific date
     */
    async getRecordingDetails(cameraId, date) {
        try {
            const response = await fetch(
                `${this.baseUrl}/api/v1/recordings/cameras/${cameraId}/details?date=${date}`
            );
            
            if (!response.ok) {
                throw new Error(`Recording details request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get recording details:', error);
            throw error;
        }
    }

    /**
     * Search recordings with filters
     */
    async searchRecordings(cameraId, searchParams) {
        try {
            const response = await fetch(
                `${this.baseUrl}/api/v1/recordings/cameras/${cameraId}/search`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(searchParams)
                }
            );
            
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
     * Get comprehensive storage statistics
     */
    async getStorageReport() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/storage/report`);
            
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
     * Trigger manual storage cleanup
     */
    async triggerCleanup(targetSizeGb = null, deleteBeforeDate = null) {
        try {
            const params = new URLSearchParams();
            if (targetSizeGb !== null) params.append('target_size_gb', targetSizeGb);
            if (deleteBeforeDate !== null) params.append('delete_before_date', deleteBeforeDate);
            
            const response = await fetch(`${this.baseUrl}/api/v1/storage/cleanup?${params}`, {
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
     * Format datetime for API calls (YYYY-MM-DD format)
     */
    formatDate(date) {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * Format datetime for API calls (ISO format)
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
            end: this.formatDateTime(endOfDay),
            date: this.formatDate(today)
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
            end: this.formatDateTime(end),
            startDate: this.formatDate(start),
            endDate: this.formatDate(end)
        };
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(unitIndex === 0 ? 0 : 2)} ${units[unitIndex]}`;
    }

    /**
     * Format duration in seconds to human readable
     */
    formatDuration(seconds) {
        if (!seconds || seconds === 0) return '0:00';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Get time range for a specific date
     */
    getDateRange(date) {
        const d = new Date(date);
        const startOfDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        const endOfDay = new Date(startOfDay.getTime() + 24 * 60 * 60 * 1000 - 1);
        
        return {
            start: this.formatDateTime(startOfDay),
            end: this.formatDateTime(endOfDay),
            date: this.formatDate(d)
        };
    }

    /**
     * Parse segment filename to extract metadata
     */
    parseSegmentFilename(filename) {
        // camera_entrance_cam_20250801_010000_600.avi
        const match = filename.match(/camera_([^_]+)_(\d{8})_(\d{6})_(\d+)\.(\w+)/);
        if (match) {
            const [, cameraId, dateStr, timeStr, duration, ext] = match;
            const year = dateStr.substr(0, 4);
            const month = dateStr.substr(4, 2);
            const day = dateStr.substr(6, 2);
            const hour = timeStr.substr(0, 2);
            const minute = timeStr.substr(2, 2);
            const second = timeStr.substr(4, 2);
            
            return {
                cameraId,
                date: `${year}-${month}-${day}`,
                time: `${hour}:${minute}:${second}`,
                duration: parseInt(duration),
                extension: ext
            };
        }
        return null;
    }

    /**
     * Convert timeline segments for easier consumption
     */
    processTimelineSegments(segments) {
        return segments.map(segment => ({
            ...segment,
            metadata: this.parseSegmentFilename(segment.filename),
            streamUrl: this.getStreamUrl(segment.filename),
            formattedDuration: this.formatDuration(segment.duration_seconds),
            formattedSize: this.formatFileSize(segment.file_size),
            startTimeMs: new Date(segment.start_time).getTime(),
            endTimeMs: new Date(segment.end_time).getTime()
        }));
    }
}

// Export singleton instance
const playbackService = new PlaybackService();
export default playbackService;