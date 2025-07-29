/**
 * Recordings Page Component
 * Main interface for viewing and managing recorded video segments
 */
import VideoPlaybackPlayer from '../components/playback/VideoPlaybackPlayer.js';
import playbackService from '../services/PlaybackService.js';

class RecordingsPage {
    constructor() {
        this.cameras = [];
        this.selectedCamera = null;
        this.selectedDate = new Date();
        this.currentTimeRange = null;
        this.recordings = [];
        this.videoPlayer = null;
        this.storageStats = null;
        
        this.filters = {
            camera: 'all',
            dateRange: 'today',
            customStart: '',
            customEnd: '',
            minDuration: '',
            maxDuration: ''
        };
        
        this.init();
    }
    
    init() {
        this.render();
        this.attachEventListeners();
        this.loadInitialData();
    }
    
    render() {
        const container = document.getElementById('recordings');
        if (!container) return;
        
        container.innerHTML = this.getTemplate();
        this.initializePlayer();
    }
    
    getTemplate() {
        return `
            <div class="recordings-page">
                <div class="page-header">
                    <h1 class="page-title">Recordings</h1>
                    <div class="header-actions">
                        <button class="btn btn-secondary" id="refresh-btn">
                            <i class="fas fa-sync-alt"></i>
                            Refresh
                        </button>
                        <button class="btn btn-primary" id="export-btn">
                            <i class="fas fa-download"></i>
                            Export
                        </button>
                    </div>
                </div>
                
                <div class="recordings-content">
                    <!-- Filters Panel -->
                    <div class="filters-panel">
                        <div class="filter-section">
                            <h3>Camera</h3>
                            <select id="camera-filter" class="form-select">
                                <option value="all">All Cameras</option>
                            </select>
                        </div>
                        
                        <div class="filter-section">
                            <h3>Date Range</h3>
                            <select id="date-range-filter" class="form-select">
                                <option value="today">Today</option>
                                <option value="yesterday">Yesterday</option>
                                <option value="last7days">Last 7 Days</option>
                                <option value="last30days">Last 30 Days</option>
                                <option value="custom">Custom Range</option>
                            </select>
                            
                            <div id="custom-date-range" class="custom-date-range" style="display: none;">
                                <div class="date-input-group">
                                    <label>From:</label>
                                    <input type="datetime-local" id="start-date" class="form-input">
                                </div>
                                <div class="date-input-group">
                                    <label>To:</label>
                                    <input type="datetime-local" id="end-date" class="form-input">
                                </div>
                            </div>
                        </div>
                        
                        <div class="filter-section">
                            <h3>Duration</h3>
                            <div class="duration-filters">
                                <div class="duration-input-group">
                                    <label>Min (seconds):</label>
                                    <input type="number" id="min-duration" class="form-input" placeholder="0">
                                </div>
                                <div class="duration-input-group">
                                    <label>Max (seconds):</label>
                                    <input type="number" id="max-duration" class="form-input" placeholder="Any">
                                </div>
                            </div>
                        </div>
                        
                        <div class="filter-actions">
                            <button class="btn btn-primary" id="apply-filters">
                                <i class="fas fa-search"></i>
                                Search
                            </button>
                            <button class="btn btn-secondary" id="clear-filters">
                                <i class="fas fa-times"></i>
                                Clear
                            </button>
                        </div>
                    </div>
                    
                    <!-- Main Content -->
                    <div class="recordings-main">
                        <!-- Storage Summary -->
                        <div class="storage-summary">
                            <div class="storage-stats">
                                <div class="stat-item">
                                    <div class="stat-value" id="total-recordings">-</div>
                                    <div class="stat-label">Total Recordings</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="total-storage">-</div>
                                    <div class="stat-label">Storage Used</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="retention-days">-</div>
                                    <div class="stat-label">Retention Days</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" id="disk-usage">-</div>
                                    <div class="stat-label">Disk Usage</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Video Player -->
                        <div class="video-player-section">
                            <div id="video-player-container" class="video-player-container">
                                <div class="no-video-message">
                                    <i class="fas fa-video"></i>
                                    <h3>Select a time range to view recordings</h3>
                                    <p>Use the filters on the left to search for specific recordings</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Recordings List -->
                        <div class="recordings-list-section">
                            <div class="section-header">
                                <h3>Recordings</h3>
                                <div class="list-controls">
                                    <select id="sort-by" class="form-select">
                                        <option value="newest">Newest First</option>
                                        <option value="oldest">Oldest First</option>
                                        <option value="duration">By Duration</option>
                                        <option value="size">By Size</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="recordings-list" id="recordings-list">
                                <div class="no-recordings-message">
                                    <i class="fas fa-film"></i>
                                    <h4>No recordings found</h4>
                                    <p>Try adjusting your search filters</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    initializePlayer() {
        const playerContainer = document.getElementById('video-player-container');
        if (playerContainer) {
            this.videoPlayer = new VideoPlaybackPlayer(playerContainer, {
                cameraId: null,
                controls: true,
                timeline: true,
                autoplay: false
            });
        }
    }
    
    attachEventListeners() {
        // Refresh button
        document.getElementById('refresh-btn')?.addEventListener('click', () => this.refreshData());
        
        // Export button
        document.getElementById('export-btn')?.addEventListener('click', () => this.showExportDialog());
        
        // Filter controls
        document.getElementById('camera-filter')?.addEventListener('change', (e) => {
            this.filters.camera = e.target.value;
        });
        
        document.getElementById('date-range-filter')?.addEventListener('change', (e) => {
            this.filters.dateRange = e.target.value;
            this.toggleCustomDateRange();
        });
        
        // Filter actions
        document.getElementById('apply-filters')?.addEventListener('click', () => this.applyFilters());
        document.getElementById('clear-filters')?.addEventListener('click', () => this.clearFilters());
        
        // Sort control
        document.getElementById('sort-by')?.addEventListener('change', (e) => {
            this.sortRecordings(e.target.value);
        });
    }
    
    async loadInitialData() {
        try {
            // Load cameras first
            await this.loadCameras();
            
            // Load storage statistics
            await this.loadStorageStats();
            
            // Load today's recordings for the first camera
            if (this.cameras.length > 0) {
                this.selectedCamera = this.cameras[0].id;
                document.getElementById('camera-filter').value = this.selectedCamera;
                await this.applyFilters();
            }
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load recordings data');
        }
    }
    
    async loadCameras() {
        try {
            // For now, we'll use a mock camera list
            // In a real implementation, this would come from the cameras API
            this.cameras = [
                { id: 3, name: 'Test Camera 1', status: 'online' }
            ];
            
            // Populate camera filter
            const cameraFilter = document.getElementById('camera-filter');
            if (cameraFilter) {
                // Clear existing options except "All Cameras"
                while (cameraFilter.children.length > 1) {
                    cameraFilter.removeChild(cameraFilter.lastChild);
                }
                
                // Add camera options
                this.cameras.forEach(camera => {
                    const option = document.createElement('option');
                    option.value = camera.id;
                    option.textContent = `Camera ${camera.id} - ${camera.name}`;
                    cameraFilter.appendChild(option);
                });
            }
            
        } catch (error) {
            console.error('Failed to load cameras:', error);
        }
    }
    
    async loadStorageStats() {
        try {
            const storageReport = await playbackService.getStorageReport();
            this.storageStats = storageReport;
            
            // Update storage display
            this.updateStorageDisplay();
            
        } catch (error) {
            console.error('Failed to load storage stats:', error);
        }
    }
    
    updateStorageDisplay() {
        if (!this.storageStats) return;
        
        const stats = this.storageStats.system_stats;
        
        document.getElementById('total-recordings').textContent = stats.total_segments || 0;
        document.getElementById('total-storage').textContent = stats.total_size_formatted || '0 B';
        document.getElementById('retention-days').textContent = `${this.storageStats.retention_days || 30} days`;
        document.getElementById('disk-usage').textContent = `${stats.disk_used_percent || 0}%`;
    }
    
    toggleCustomDateRange() {
        const customRange = document.getElementById('custom-date-range');
        const isCustom = this.filters.dateRange === 'custom';
        
        if (customRange) {
            customRange.style.display = isCustom ? 'block' : 'none';
        }
    }
    
    async applyFilters() {
        try {
            // Determine date range
            const dateRange = this.getDateRange();
            if (!dateRange) {
                this.showError('Please select a valid date range');
                return;
            }
            
            // Determine camera ID
            const cameraId = this.filters.camera === 'all' ? 
                (this.cameras.length > 0 ? this.cameras[0].id : null) : 
                parseInt(this.filters.camera);
            
            if (!cameraId) {
                this.showError('Please select a camera');
                return;
            }
            
            // Search options
            const searchOptions = {};
            if (this.filters.minDuration) {
                searchOptions.minDuration = parseInt(this.filters.minDuration);
            }
            if (this.filters.maxDuration) {
                searchOptions.maxDuration = parseInt(this.filters.maxDuration);
            }
            
            // Load recordings
            const searchResults = await playbackService.searchRecordings(
                cameraId,
                dateRange.start,
                dateRange.end,
                searchOptions
            );
            
            this.recordings = searchResults.segments || [];
            
            // Update UI
            this.renderRecordingsList();
            
            // Load timeline in video player
            if (this.videoPlayer && this.recordings.length > 0) {
                await this.videoPlayer.loadTimeRange(cameraId, dateRange.start, dateRange.end);
            }
            
        } catch (error) {
            console.error('Failed to apply filters:', error);
            this.showError('Failed to search recordings');
        }
    }
    
    getDateRange() {
        const now = new Date();
        
        switch (this.filters.dateRange) {
            case 'today':
                return playbackService.getTodayRange();
                
            case 'yesterday':
                const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                const startOfYesterday = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
                const endOfYesterday = new Date(startOfYesterday.getTime() + 24 * 60 * 60 * 1000 - 1);
                return {
                    start: playbackService.formatDateTime(startOfYesterday),
                    end: playbackService.formatDateTime(endOfYesterday)
                };
                
            case 'last7days':
                return playbackService.getLastNDaysRange(7);
                
            case 'last30days':
                return playbackService.getLastNDaysRange(30);
                
            case 'custom':
                const startDate = document.getElementById('start-date')?.value;
                const endDate = document.getElementById('end-date')?.value;
                
                if (!startDate || !endDate) {
                    return null;
                }
                
                return {
                    start: playbackService.formatDateTime(new Date(startDate)),
                    end: playbackService.formatDateTime(new Date(endDate))
                };
                
            default:
                return playbackService.getTodayRange();
        }
    }
    
    renderRecordingsList() {
        const listContainer = document.getElementById('recordings-list');
        if (!listContainer) return;
        
        if (this.recordings.length === 0) {
            listContainer.innerHTML = `
                <div class="no-recordings-message">
                    <i class="fas fa-film"></i>
                    <h4>No recordings found</h4>
                    <p>Try adjusting your search filters</p>
                </div>
            `;
            return;
        }
        
        const recordingsHtml = this.recordings.map(recording => this.getRecordingItemTemplate(recording)).join('');
        listContainer.innerHTML = recordingsHtml;
        
        // Attach click listeners
        listContainer.querySelectorAll('.recording-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const recordingId = e.currentTarget.dataset.recordingId;
                const recording = this.recordings.find(r => r.id.toString() === recordingId);
                if (recording) {
                    this.playRecording(recording);
                }
            });
        });
    }
    
    getRecordingItemTemplate(recording) {
        const startTime = new Date(recording.start_time);
        const duration = playbackService.formatDuration(recording.duration_seconds);
        const fileSize = playbackService.formatFileSize(recording.file_size);
        
        return `
            <div class="recording-item" data-recording-id="${recording.id}">
                <div class="recording-info">
                    <div class="recording-time">
                        <i class="fas fa-clock"></i>
                        ${startTime.toLocaleString()}
                    </div>
                    <div class="recording-filename">${recording.filename}</div>
                </div>
                <div class="recording-stats">
                    <span class="stat">
                        <i class="fas fa-stopwatch"></i>
                        ${duration}
                    </span>
                    <span class="stat">
                        <i class="fas fa-hdd"></i>
                        ${fileSize}
                    </span>
                    <span class="status ${recording.exists ? 'exists' : 'missing'}">
                        <i class="fas ${recording.exists ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
                        ${recording.exists ? 'Available' : 'Missing'}
                    </span>
                </div>
                <div class="recording-actions">
                    <button class="btn btn-sm btn-primary play-btn" title="Play">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-sm btn-secondary download-btn" title="Download">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    async playRecording(recording) {
        if (!this.videoPlayer || !recording.exists) return;
        
        try {
            // Load the specific segment
            await this.videoPlayer.loadSegment(recording);
            
            // Scroll to video player
            document.getElementById('video-player-container')?.scrollIntoView({ 
                behavior: 'smooth' 
            });
            
        } catch (error) {
            console.error('Failed to play recording:', error);
            this.showError('Failed to play recording');
        }
    }
    
    sortRecordings(sortBy) {
        if (!this.recordings.length) return;
        
        switch (sortBy) {
            case 'newest':
                this.recordings.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
                break;
            case 'oldest':
                this.recordings.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
                break;
            case 'duration':
                this.recordings.sort((a, b) => b.duration_seconds - a.duration_seconds);
                break;
            case 'size':
                this.recordings.sort((a, b) => b.file_size - a.file_size);
                break;
        }
        
        this.renderRecordingsList();
    }
    
    clearFilters() {
        this.filters = {
            camera: 'all',
            dateRange: 'today',
            customStart: '',
            customEnd: '',
            minDuration: '',
            maxDuration: ''
        };
        
        // Reset form elements
        document.getElementById('camera-filter').value = 'all';
        document.getElementById('date-range-filter').value = 'today';
        document.getElementById('min-duration').value = '';
        document.getElementById('max-duration').value = '';
        document.getElementById('start-date').value = '';
        document.getElementById('end-date').value = '';
        
        this.toggleCustomDateRange();
    }
    
    async refreshData() {
        await this.loadStorageStats();
        await this.applyFilters();
    }
    
    showExportDialog() {
        // TODO: Implement export dialog
        console.log('Export dialog not implemented yet');
    }
    
    showError(message) {
        console.error('Recordings page error:', message);
        // TODO: Implement proper error display
    }
    
    // Cleanup
    destroy() {
        if (this.videoPlayer) {
            this.videoPlayer.destroy();
        }
    }
}

export default RecordingsPage;