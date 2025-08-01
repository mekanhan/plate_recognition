/**
 * Recordings Page Component
 * Complete rewrite following documentation requirements
 * Integrates RecordingCalendar, TimelineControl, and enhanced VideoPlaybackPlayer
 */
import VideoPlaybackPlayer from '../components/playback/VideoPlaybackPlayer.js';
import RecordingCalendar from '../components/playback/RecordingCalendar.js';
import TimelineControl from '../components/playback/TimelineControl.js';
import playbackService from '../services/PlaybackService.js';

class RecordingsPage {
    constructor() {
        // Camera state
        this.cameras = [];
        this.selectedCamera = null;
        
        // Date/time state
        this.selectedDate = new Date();
        this.timeRange = { start: null, end: null };
        
        // Recording data
        this.segments = [];
        this.currentSegment = null;
        
        // UI state
        this.isLoading = false;
        this.error = null;
        
        // Components
        this.videoPlayer = null;
        this.calendar = null;
        this.timeline = null;
        
        // Storage data
        this.storageStats = null;
        
        // Filter state
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
                    <h1 class="page-title">
                        <i class="fas fa-video"></i>
                        Recordings
                    </h1>
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
                
                <div class="recordings-layout">
                    <!-- Left Sidebar -->
                    <div class="recordings-sidebar">
                        <!-- Camera Selection -->
                        <div class="sidebar-section">
                            <h3>Camera</h3>
                            <div id="camera-list-container" class="camera-list">
                                <!-- Camera list will be rendered here -->
                            </div>
                        </div>
                        
                        <!-- Calendar -->
                        <div class="sidebar-section">
                            <h3>Calendar</h3>
                            <div id="recording-calendar" class="recording-calendar-container">
                                <!-- Calendar will be rendered here -->
                            </div>
                        </div>
                        
                        <!-- Storage Summary -->
                        <div class="sidebar-section">
                            <h3>Storage</h3>
                            <div class="storage-summary">
                                <div class="storage-stats">
                                    <div class="stat-item">
                                        <div class="stat-label">Used</div>
                                        <div class="stat-value" id="storage-used">-</div>
                                    </div>
                                    <div class="stat-item">
                                        <div class="stat-label">Available</div>
                                        <div class="stat-value" id="storage-available">-</div>
                                    </div>
                                    <div class="stat-item">
                                        <div class="stat-label">Usage</div>
                                        <div class="stat-value" id="storage-percentage">-</div>
                                    </div>
                                </div>
                                <div class="storage-actions">
                                    <button class="btn btn-sm btn-secondary" id="cleanup-btn">
                                        <i class="fas fa-broom"></i>
                                        Cleanup
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Main Content -->
                    <div class="recordings-main">
                        <!-- Video Player -->
                        <div class="video-player-section">
                            <div id="video-player-container" class="video-player-container">
                                <div class="no-video-message">
                                    <i class="fas fa-calendar-alt"></i>
                                    <h3>Select a Date to View Recordings</h3>
                                    <p>Use the calendar to choose a date with available recordings</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Timeline Control -->
                        <div class="timeline-section">
                            <div id="timeline-control" class="timeline-control-container">
                                <!-- Timeline will be rendered here -->
                            </div>
                        </div>
                        
                        <!-- Recording Details -->
                        <div class="recording-details-section">
                            <div class="section-header">
                                <h3>Recording Details</h3>
                                <div class="details-actions">
                                    <button class="btn btn-sm btn-secondary" id="show-segments-btn">
                                        <i class="fas fa-list"></i>
                                        Segments
                                    </button>
                                    <button class="btn btn-sm btn-secondary" id="show-stats-btn">
                                        <i class="fas fa-chart-bar"></i>
                                        Statistics
                                    </button>
                                </div>
                            </div>
                            
                            <div class="recording-info">
                                <div class="info-row">
                                    <span class="info-label">Date:</span>
                                    <span class="info-value" id="selected-date">No date selected</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Coverage:</span>
                                    <span class="info-value" id="coverage-percentage">-</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Duration:</span>
                                    <span class="info-value" id="total-duration">-</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Size:</span>
                                    <span class="info-value" id="total-size">-</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Segments:</span>
                                    <span class="info-value" id="segment-count">-</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Loading Overlay -->
                <div class="loading-overlay" style="display: none;">
                    <div class="loading-content">
                        <i class="fas fa-spinner fa-spin"></i>
                        <h3>Loading Recordings...</h3>
                        <p>Please wait while we load the recording data</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    initializePlayer() {
        // Initialize video player
        const playerContainer = document.getElementById('video-player-container');
        if (playerContainer) {
            this.videoPlayer = new VideoPlaybackPlayer(playerContainer, {
                cameraId: null,
                controls: true,
                timeline: false, // We use separate timeline control
                autoplay: false
            });
        }
        
        // Initialize calendar
        const calendarContainer = document.getElementById('recording-calendar');
        if (calendarContainer) {
            this.calendar = new RecordingCalendar(calendarContainer, {
                onDateSelect: (date, recordingData) => this.handleDateSelect(date, recordingData),
                onMonthChange: (year, month, calendarData) => this.handleMonthChange(year, month, calendarData),
                highlightToday: true
            });
        }
        
        // Initialize timeline control
        const timelineContainer = document.getElementById('timeline-control');
        if (timelineContainer) {
            this.timeline = new TimelineControl(timelineContainer, {
                onSeek: (seconds) => this.handleTimelineSeek(seconds),
                onSegmentClick: (segment) => this.handleSegmentClick(segment),
                onSegmentHover: (segment, action) => this.handleSegmentHover(segment, action),
                showHourMarkers: true,
                allowSeek: true
            });
        }
    }
    
    attachEventListeners() {
        // Header actions
        document.getElementById('refresh-btn')?.addEventListener('click', () => this.refreshData());
        document.getElementById('export-btn')?.addEventListener('click', () => this.showExportDialog());
        
        // Storage actions
        document.getElementById('cleanup-btn')?.addEventListener('click', () => this.triggerStorageCleanup());
        
        // Recording details actions
        document.getElementById('show-segments-btn')?.addEventListener('click', () => this.showSegmentsList());
        document.getElementById('show-stats-btn')?.addEventListener('click', () => this.showRecordingStats());
    }
    
    async loadInitialData() {
        this.showLoading(true);
        
        try {
            // Load cameras from main API
            await this.loadCameras();
            
            // Load storage statistics
            await this.loadStorageStats();
            
            // Load today's data for the first camera
            if (this.cameras.length > 0) {
                this.selectedCamera = this.cameras[0].id;
                
                // Load calendar for current month
                await this.loadCalendarForCurrentMonth();
                
                // Set today as selected date and load recordings
                this.selectedDate = new Date();
                await this.loadRecordingsForDate(this.selectedDate);
            } else {
                this.showNoCamerasMessage();
            }
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load recordings data');
        } finally {
            this.showLoading(false);
        }
    }

    async loadCameras() {
        try {
            // Load cameras from main API (port 8000)
            const response = await fetch('http://localhost:8000/api/cameras');
            if (!response.ok) {
                throw new Error(`Failed to load cameras: ${response.status}`);
            }
            
            const cameras = await response.json();
            this.cameras = cameras.filter(camera => camera.status === 'online');
            
            // Render camera list
            this.renderCameraList();
            
        } catch (error) {
            console.error('Failed to load cameras:', error);
            // Fallback to test data
            this.cameras = [
                { id: 'entrance_cam', name: 'Entrance Camera', status: 'online' }
            ];
            this.renderCameraList();
        }
    }

    renderCameraList() {
        const cameraListContainer = document.getElementById('camera-list-container');
        if (!cameraListContainer) return;
        
        if (this.cameras.length === 0) {
            cameraListContainer.innerHTML = `
                <div class="no-cameras-message">
                    <i class="fas fa-video-slash"></i>
                    <p>No cameras available</p>
                </div>
            `;
            return;
        }
        
        const camerasHtml = this.cameras.map(camera => `
            <div class="camera-item ${camera.id === this.selectedCamera ? 'selected' : ''}" 
                 data-camera-id="${camera.id}">
                <div class="camera-info">
                    <div class="camera-name">${camera.name}</div>
                    <div class="camera-status ${camera.status}">
                        <i class="fas fa-circle"></i>
                        ${camera.status}
                    </div>
                </div>
            </div>
        `).join('');
        
        cameraListContainer.innerHTML = camerasHtml;
        
        // Attach click listeners
        cameraListContainer.querySelectorAll('.camera-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const cameraId = e.currentTarget.dataset.cameraId;
                this.selectCamera(cameraId);
            });
        });
    }

    // Event Handlers
    async handleDateSelect(date, recordingData) {
        this.selectedDate = new Date(date);
        await this.loadRecordingsForDate(this.selectedDate);
        this.updateSelectedDateDisplay();
    }

    handleMonthChange(year, month, calendarData) {
        // Month changed in calendar - could update storage stats for month
        console.log(`Month changed to ${year}-${month}`, calendarData);
    }

    handleTimelineSeek(seconds) {
        // Convert seconds to timestamp and seek video player
        if (this.videoPlayer && this.selectedDate) {
            const dayStart = new Date(this.selectedDate);
            dayStart.setHours(0, 0, 0, 0);
            const targetTime = new Date(dayStart.getTime() + (seconds * 1000));
            
            this.videoPlayer.seekToTime(targetTime.toISOString());
        }
    }

    async handleSegmentClick(segment) {
        if (this.videoPlayer) {
            await this.videoPlayer.loadSegment(segment);
            this.currentSegment = segment;
            this.updateRecordingDetails();
        }
    }

    handleSegmentHover(segment, action) {
        // Show segment tooltip or preview on hover
        if (action === 'enter') {
            // Could show segment preview or details
            console.log('Segment hover:', segment.filename);
        }
    }

    async selectCamera(cameraId) {
        if (this.selectedCamera === cameraId) return;
        
        this.selectedCamera = cameraId;
        
        // Update camera list selection
        document.querySelectorAll('.camera-item').forEach(item => {
            item.classList.toggle('selected', item.dataset.cameraId === cameraId);
        });
        
        // Reload calendar and recordings for new camera
        await this.loadCalendarForCurrentMonth();
        await this.loadRecordingsForDate(this.selectedDate);
    }

    async loadCalendarForCurrentMonth() {
        if (!this.calendar || !this.selectedCamera) return;
        
        const now = new Date();
        await this.calendar.loadMonth(
            this.selectedCamera, 
            now.getFullYear(), 
            now.getMonth() + 1
        );
    }

    async loadRecordingsForDate(date) {
        if (!this.selectedCamera || !date) return;
        
        this.showLoading(true);
        
        try {
            // Load recordings for selected date using video player
            if (this.videoPlayer) {
                await this.videoPlayer.loadRecordingsForDate(this.selectedCamera, date);
                
                // Get timeline data and update timeline control
                const dateStr = playbackService.formatDate(date);
                const timelineData = await playbackService.getTimelineSegments(this.selectedCamera, dateStr);
                
                this.segments = timelineData.segments || [];
                
                // Update timeline control
                if (this.timeline) {
                    this.timeline.loadSegments(this.segments);
                }
                
                // Update recording details
                this.updateRecordingDetails(timelineData);
            }
            
        } catch (error) {
            console.error('Failed to load recordings for date:', error);
            this.showError('Failed to load recordings');
        } finally {
            this.showLoading(false);
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
        
        const usedEl = document.getElementById('storage-used');
        if (usedEl) usedEl.textContent = playbackService.formatFileSize(this.storageStats.total_used_bytes || 0);
        
        const availableEl = document.getElementById('storage-available');
        if (availableEl) availableEl.textContent = playbackService.formatFileSize(this.storageStats.available_bytes || 0);
        
        const percentageEl = document.getElementById('storage-percentage');
        if (percentageEl) percentageEl.textContent = `${Math.round(this.storageStats.percentage_used || 0)}%`;
    }

    updateSelectedDateDisplay() {
        const selectedDateEl = document.getElementById('selected-date');
        if (selectedDateEl) {
            selectedDateEl.textContent = this.selectedDate.toLocaleDateString();
        }
    }

    updateRecordingDetails(timelineData = null) {
        if (timelineData) {
            const coverageEl = document.getElementById('coverage-percentage');
            if (coverageEl) coverageEl.textContent = `${Math.round(timelineData.coverage_percentage || 0)}%`;
            
            const durationEl = document.getElementById('total-duration');
            if (durationEl) durationEl.textContent = playbackService.formatDuration(timelineData.total_duration || 0);
            
            const sizeEl = document.getElementById('total-size');
            if (sizeEl) sizeEl.textContent = playbackService.formatFileSize(timelineData.total_size || 0);
            
            const countEl = document.getElementById('segment-count');
            if (countEl) countEl.textContent = (timelineData.segments?.length || 0).toString();
        }
    }

    // UI State Management
    showLoading(show) {
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }

    showError(message) {
        console.error('RecordingsPage error:', message);
        // Could implement toast notifications here
        alert(`Error: ${message}`);
    }

    showNoCamerasMessage() {
        const mainContent = document.querySelector('.recordings-main');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="no-cameras-content">
                    <i class="fas fa-video-slash"></i>
                    <h3>No Cameras Available</h3>
                    <p>No cameras are currently online or configured for recording.</p>
                </div>
            `;
        }
    }

    // Action Methods
    async refreshData() {
        await this.loadStorageStats();
        
        if (this.selectedCamera && this.selectedDate) {
            await this.loadRecordingsForDate(this.selectedDate);
        }
        
        if (this.calendar && this.selectedCamera) {
            await this.loadCalendarForCurrentMonth();
        }
    }

    async triggerStorageCleanup() {
        if (!this.storageStats) return;
        
        const confirmed = confirm('Are you sure you want to trigger storage cleanup? This will remove old recordings to free up space.');
        if (!confirmed) return;
        
        try {
            this.showLoading(true);
            const result = await playbackService.triggerCleanup();
            
            alert(`Cleanup completed: ${result.deleted_count} segments removed, ${playbackService.formatFileSize(result.deleted_size)} freed`);
            
            // Refresh data after cleanup
            await this.refreshData();
            
        } catch (error) {
            console.error('Failed to trigger cleanup:', error);
            this.showError('Failed to trigger storage cleanup');
        } finally {
            this.showLoading(false);
        }
    }

    showExportDialog() {
        // TODO: Implement export functionality
        alert('Export functionality not yet implemented');
    }

    showSegmentsList() {
        // TODO: Show detailed segments list in modal or panel
        console.log('Show segments list:', this.segments);
    }

    showRecordingStats() {
        // TODO: Show detailed recording statistics
        console.log('Show recording stats for:', this.selectedDate);
    }

    // Cleanup
    destroy() {
        if (this.videoPlayer) {
            this.videoPlayer.destroy();
        }
        if (this.calendar) {
            this.calendar.destroy();
        }
        if (this.timeline) {
            this.timeline.destroy();
        }
}
}

export default RecordingsPage;