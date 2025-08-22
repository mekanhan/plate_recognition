/**
 * Recordings Page Component
 * Direct port of the working standalone recordings.html
 */

class RecordingsPage {
    constructor() {
        this.init();
    }
    
    init() {
        this.render();
        this.initializeStandaloneRecordings();
    }
    
    render() {
        const container = document.getElementById('recordings');
        if (!container) return;
        
        // Insert the complete working HTML from standalone recordings.html
        container.innerHTML = `
            <div class="page-container">
                <!-- Sidebar -->
                <div class="sidebar">
                    <div class="sidebar-header">
                        <h2><i class="fas fa-video"></i> Recordings</h2>
                    </div>
                    
                    <!-- Controls section below header -->
                    <div class="sidebar-controls">
                        <!-- Service Status Indicator -->
                        <div class="service-status checking" id="serviceStatus">
                            <span class="status-indicator"></span>
                            <span id="serviceStatusText">Checking service...</span>
                        </div>
                        
                        <div class="camera-selector">
                            <select id="cameraSelect" disabled>
                                <option value="">Loading cameras...</option>
                            </select>
                        </div>
                    </div>

                    <!-- Calendar -->
                    <div class="calendar-container">
                        <div class="calendar-header">
                            <span id="calendarMonth">Loading...</span>
                            <div class="calendar-nav">
                                <button id="prevMonth" disabled><i class="fas fa-chevron-left"></i></button>
                                <button id="todayBtn" disabled>Today</button>
                                <button id="nextMonth" disabled><i class="fas fa-chevron-right"></i></button>
                            </div>
                        </div>
                        <div class="calendar-weekdays">
                            <div class="calendar-weekday">S</div>
                            <div class="calendar-weekday">M</div>
                            <div class="calendar-weekday">T</div>
                            <div class="calendar-weekday">W</div>
                            <div class="calendar-weekday">T</div>
                            <div class="calendar-weekday">F</div>
                            <div class="calendar-weekday">S</div>
                        </div>
                        <div class="calendar-grid" id="calendarGrid">
                            <!-- Calendar skeleton loading -->
                            <div class="calendar-day skeleton"></div>
                            <div class="calendar-day skeleton"></div>
                            <div class="calendar-day skeleton"></div>
                            <div class="calendar-day skeleton"></div>
                            <div class="calendar-day skeleton"></div>
                            <div class="calendar-day skeleton"></div>
                            <div class="calendar-day skeleton"></div>
                        </div>
                    </div>

                    <!-- Timeline -->
                    <div class="timeline-container">
                        <div class="timeline-header">
                            <h3>Recordings</h3>
                            <span id="recordingCount">--</span>
                        </div>
                        <div id="recordingsList">
                            <!-- Loading skeleton -->
                            <div class="skeleton skeleton-item"></div>
                            <div class="skeleton skeleton-item"></div>
                            <div class="skeleton skeleton-item"></div>
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="recordings-content">
                    <!-- Video Player -->
                    <div class="video-container">
                        <div class="video-placeholder" id="videoPlaceholder">
                            <i class="fas fa-video"></i>
                            <p>Select a recording to begin playback</p>
                        </div>
                        
                        <video id="videoPlayer" controls style="display: none;">
                            Your browser does not support video playback.
                        </video>
                        
                        <div class="video-loading" id="videoLoading" style="display: none;">
                            <i class="fas fa-spinner"></i>
                            <p>Loading video...</p>
                        </div>
                        
                        <div class="video-error" id="videoError" style="display: none;">
                            <i class="fas fa-exclamation-circle"></i>
                            <h3>Unable to Play Video</h3>
                            <p>Please try a different recording or check your connection.</p>
                        </div>
                    </div>

                    <!-- Controls -->
                    <div class="controls-bar">
                        <div class="timeline-scrubber">
                            <div class="timeline-track" id="timelineTrack">
                                <!-- Timeline segments will be rendered here -->
                            </div>
                            <div class="timeline-time-labels">
                                <span>00:00</span>
                                <span>06:00</span>
                                <span>12:00</span>
                                <span>18:00</span>
                                <span>24:00</span>
                            </div>
                        </div>
                        
                        <div class="playback-controls">
                            <button class="control-btn" id="skipBackBtn" disabled>
                                <i class="fas fa-backward"></i>
                            </button>
                            <button class="control-btn" id="playPauseBtn" disabled>
                                <i class="fas fa-play"></i>
                            </button>
                            <button class="control-btn" id="skipForwardBtn" disabled>
                                <i class="fas fa-forward"></i>
                            </button>
                            
                            <span class="time-display" id="timeDisplay">--:--:-- / --:--:--</span>
                            
                            <div class="speed-selector">
                                <select id="speedSelect" disabled>
                                    <option value="0.5">0.5x</option>
                                    <option value="1" selected>1x</option>
                                    <option value="1.5">1.5x</option>
                                    <option value="2">2x</option>
                                    <option value="4">4x</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    initializeStandaloneRecordings() {
        // Load and execute the exact JavaScript from recordings.html
        const script = document.createElement('script');
        script.textContent = `
        // Configuration with fallbacks
        const CONFIG = {
            RECORDING_SERVICE_URL: window.RECORDING_SERVICE_URL || 'http://' + window.location.hostname + ':8002',
            API_TIMEOUT: 10000, // 10 seconds
            RETRY_ATTEMPTS: 3,
            RETRY_DELAY: 1000, // 1 second
            HEALTH_CHECK_INTERVAL: 30000, // 30 seconds
            DEFAULT_CAMERA: null  // Will be set to first available camera
        };
        
        // Utility class for API communication with error handling
        class ApiClient {
            constructor(baseUrl) {
                this.baseUrl = baseUrl;
            }
            
            async fetch(endpoint, options = {}) {
                // Create a promise that rejects after timeout
                const timeoutPromise = new Promise((_, reject) => {
                    setTimeout(() => reject(new Error('Request timeout')), CONFIG.API_TIMEOUT);
                });
                
                // Create the fetch promise
                const fetchPromise = fetch(\`\${this.baseUrl}\${endpoint}\`, options)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(\`HTTP error! status: \${response.status}\`);
                        }
                        return response.json();
                    });
                
                // Race between fetch and timeout
                try {
                    return await Promise.race([fetchPromise, timeoutPromise]);
                } catch (error) {
                    // Convert specific errors to more user-friendly messages
                    if (error.message === 'Failed to fetch') {
                        throw new Error('Network error - service may be offline');
                    }
                    throw error;
                }
            }
            
            async fetchWithRetry(endpoint, options = {}, attempts = CONFIG.RETRY_ATTEMPTS) {
                for (let i = 0; i < attempts; i++) {
                    try {
                        return await this.fetch(endpoint, options);
                    } catch (error) {
                        console.warn(\`Attempt \${i + 1} failed:\`, error.message);
                        
                        if (i === attempts - 1) {
                            throw error;
                        }
                        
                        // Wait before retrying with exponential backoff
                        await new Promise(resolve => 
                            setTimeout(resolve, CONFIG.RETRY_DELAY * Math.pow(2, i))
                        );
                    }
                }
            }
        }
        
        // Main application class - exact copy from recordings.html
        class RecordingsPageApp {
            constructor() {
                this.api = new ApiClient(CONFIG.RECORDING_SERVICE_URL);
                this.state = {
                    serviceOnline: false,
                    currentCamera: null,
                    cameras: [],
                    currentDate: new Date(),
                    selectedDate: new Date(),
                    recordings: [],
                    currentRecording: null,
                    timelineSegments: [],
                    calendarData: {},
                    isLoading: false,
                    playableRecordings: [],
                    unplayableRecordings: []
                };
                
                this.healthCheckInterval = null;
                this.videoRetryCount = 0;
                
                this.initializeElements();
                this.attachEventListeners();
                this.initialize();
            }
            
            // Check if a recording is playable in the browser
            isRecordingPlayable(recording) {
                const filename = recording.filename || '';
                const fileSize = recording.file_size || 0;
                
                // AVI files are not playable in browsers
                if (filename.endsWith('.avi')) {
                    return { playable: false, reason: 'AVI format not supported in browsers', format: 'avi' };
                }
                
                // Check for legacy OpenCV MP4 files (usually small and broken)
                if (filename.endsWith('_600.mp4') && fileSize < 10 * 1024 * 1024) { // Less than 10MB
                    return { playable: false, reason: 'Legacy OpenCV recording (corrupted)', format: 'legacy' };
                }
                
                // MP4 files should be playable
                if (filename.endsWith('.mp4')) {
                    return { playable: true, reason: 'MP4 format supported', format: 'mp4' };
                }
                
                // Unknown format
                return { playable: false, reason: 'Unknown format', format: 'unknown' };
            }
            
            initializeElements() {
                // Service status
                this.serviceStatus = document.getElementById('serviceStatus');
                this.serviceStatusText = document.getElementById('serviceStatusText');
                
                // Sidebar elements
                this.cameraSelect = document.getElementById('cameraSelect');
                this.calendarGrid = document.getElementById('calendarGrid');
                this.calendarMonth = document.getElementById('calendarMonth');
                this.recordingsList = document.getElementById('recordingsList');
                this.recordingCount = document.getElementById('recordingCount');
                
                // Calendar navigation
                this.prevMonthBtn = document.getElementById('prevMonth');
                this.nextMonthBtn = document.getElementById('nextMonth');
                this.todayBtn = document.getElementById('todayBtn');
                
                // Video player elements
                this.videoPlayer = document.getElementById('videoPlayer');
                this.videoLoading = document.getElementById('videoLoading');
                this.videoError = document.getElementById('videoError');
                this.videoErrorMessage = document.getElementById('videoErrorMessage');
                this.videoPlaceholder = document.getElementById('videoPlaceholder');
                
                // Control elements
                this.timelineTrack = document.getElementById('timelineTrack');
                this.playPauseBtn = document.getElementById('playPauseBtn');
                this.skipBackBtn = document.getElementById('skipBackBtn');
                this.skipForwardBtn = document.getElementById('skipForwardBtn');
                this.timeDisplay = document.getElementById('timeDisplay');
                this.speedSelect = document.getElementById('speedSelect');
            }
            
            attachEventListeners() {
                // Camera selection
                this.cameraSelect.addEventListener('change', (e) => {
                    this.state.currentCamera = e.target.value;
                    this.loadRecordingsForDate();
                });
                
                // Calendar navigation
                this.prevMonthBtn.addEventListener('click', () => {
                    this.state.currentDate.setMonth(this.state.currentDate.getMonth() - 1);
                    this.renderCalendar();
                    this.loadCalendarData();
                });
                
                this.nextMonthBtn.addEventListener('click', () => {
                    this.state.currentDate.setMonth(this.state.currentDate.getMonth() + 1);
                    this.renderCalendar();
                    this.loadCalendarData();
                });
                
                this.todayBtn.addEventListener('click', () => {
                    this.state.currentDate = new Date();
                    this.state.selectedDate = new Date();
                    this.renderCalendar();
                    this.loadCalendarData();
                    this.loadRecordingsForDate();
                });
                
                // Video player controls
                this.playPauseBtn.addEventListener('click', () => this.togglePlayPause());
                
                this.skipBackBtn.addEventListener('click', () => {
                    if (this.videoPlayer.readyState >= 2) {
                        this.videoPlayer.currentTime = Math.max(0, this.videoPlayer.currentTime - 10);
                    }
                });
                
                this.skipForwardBtn.addEventListener('click', () => {
                    if (this.videoPlayer.readyState >= 2) {
                        this.videoPlayer.currentTime = Math.min(
                            this.videoPlayer.duration, 
                            this.videoPlayer.currentTime + 10
                        );
                    }
                });
                
                this.speedSelect.addEventListener('change', (e) => {
                    this.videoPlayer.playbackRate = parseFloat(e.target.value);
                });
                
                // Video player events
                this.videoPlayer.addEventListener('loadstart', () => {
                    this.showVideoLoading();
                });
                
                this.videoPlayer.addEventListener('loadeddata', () => {
                    this.hideVideoLoading();
                    this.enableControls();
                    this.videoRetryCount = 0;
                });
                
                this.videoPlayer.addEventListener('timeupdate', () => {
                    this.updateTimeDisplay();
                });
                
                this.videoPlayer.addEventListener('play', () => {
                    this.playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
                });
                
                this.videoPlayer.addEventListener('pause', () => {
                    this.playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
                });
                
                this.videoPlayer.addEventListener('error', (e) => {
                    this.handleVideoError(e);
                });
                
                // Timeline click handler
                this.timelineTrack.addEventListener('click', (e) => {
                    this.handleTimelineClick(e);
                });
            }
            
            async initialize() {
                try {
                    // Check service health
                    await this.checkServiceHealth();
                    
                    // Start periodic health checks
                    this.startHealthChecks();
                    
                    // Load initial data if service is online
                    if (this.state.serviceOnline) {
                        await this.loadCameras();
                        this.renderCalendar();
                        await this.loadCalendarData();
                        await this.loadRecordingsForDate();
                    }
                } catch (error) {
                    console.error('Initialization error:', error);
                    this.showStatus('Failed to initialize', 'error');
                }
            }
            
            async checkServiceHealth() {
                try {
                    // Try to fetch from a simple endpoint
                    await this.api.fetch('/health', { method: 'GET' });
                    this.setServiceStatus(true);
                } catch (error) {
                    console.warn('Service health check failed:', error);
                    
                    // Try alternate endpoint
                    try {
                        await this.api.fetch('/api/v1/status', { method: 'GET' });
                        this.setServiceStatus(true);
                    } catch (altError) {
                        this.setServiceStatus(false);
                    }
                }
            }
            
            setServiceStatus(online) {
                this.state.serviceOnline = online;
                
                if (online) {
                    this.serviceStatus.className = 'service-status online';
                    this.serviceStatusText.textContent = 'Recording service online';
                    this.enableInterface();
                } else {
                    this.serviceStatus.className = 'service-status offline';
                    this.serviceStatusText.textContent = 'Recording service offline';
                    this.disableInterface();
                }
            }
            
            startHealthChecks() {
                // Clear any existing interval
                if (this.healthCheckInterval) {
                    clearInterval(this.healthCheckInterval);
                }
                
                // Check health periodically
                this.healthCheckInterval = setInterval(() => {
                    this.checkServiceHealth();
                }, CONFIG.HEALTH_CHECK_INTERVAL);
            }
            
            enableInterface() {
                this.cameraSelect.disabled = false;
                this.prevMonthBtn.disabled = false;
                this.nextMonthBtn.disabled = false;
                this.todayBtn.disabled = false;
            }
            
            disableInterface() {
                this.cameraSelect.disabled = true;
                this.prevMonthBtn.disabled = true;
                this.nextMonthBtn.disabled = true;
                this.todayBtn.disabled = true;
                this.disableControls();
            }
            
            enableControls() {
                this.playPauseBtn.disabled = false;
                this.skipBackBtn.disabled = false;
                this.skipForwardBtn.disabled = false;
                this.speedSelect.disabled = false;
            }
            
            disableControls() {
                this.playPauseBtn.disabled = true;
                this.skipBackBtn.disabled = true;
                this.skipForwardBtn.disabled = true;
                this.speedSelect.disabled = true;
            }
            
            async loadCameras() {
                try {
                    // Fetch cameras from the API
                    const response = await fetch('http://localhost:8001/api/cameras');
                    if (!response.ok) {
                        throw new Error('Failed to fetch cameras: ' + response.status);
                    }
                    
                    const cameras = await response.json();
                    
                    // Convert camera data to expected format
                    this.state.cameras = cameras.map(camera => ({
                        id: camera.camera_id,
                        name: camera.name
                    }));
                    
                    this.renderCameraSelector();
                    
                    // Set default camera
                    if (!this.state.currentCamera && this.state.cameras.length > 0) {
                        this.state.currentCamera = this.state.cameras[0].id;
                        this.cameraSelect.value = this.state.currentCamera;
                    }
                } catch (error) {
                    console.error('Failed to load cameras:', error);
                    this.showStatus('Failed to load cameras', 'error');
                }
            }
            
            renderCameraSelector() {
                this.cameraSelect.innerHTML = this.state.cameras.map(camera => 
                    \`<option value="\${camera.id}">\${camera.name}</option>\`
                ).join('');
                
                if (this.state.currentCamera) {
                    this.cameraSelect.value = this.state.currentCamera;
                }
            }
            
            renderCalendar() {
                const year = this.state.currentDate.getFullYear();
                const month = this.state.currentDate.getMonth();
                const today = new Date();
                
                // Update month display
                this.calendarMonth.textContent = new Intl.DateTimeFormat('en-US', {
                    month: 'long',
                    year: 'numeric'
                }).format(this.state.currentDate);
                
                // Clear calendar
                this.calendarGrid.innerHTML = '';
                
                // Get first day of month and days in month
                const firstDay = new Date(year, month, 1).getDay();
                const daysInMonth = new Date(year, month + 1, 0).getDate();
                
                // Add empty cells for days before month starts
                for (let i = 0; i < firstDay; i++) {
                    const emptyDay = document.createElement('div');
                    emptyDay.className = 'calendar-day disabled';
                    this.calendarGrid.appendChild(emptyDay);
                }
                
                // Add days of month
                for (let day = 1; day <= daysInMonth; day++) {
                    const dayElement = document.createElement('div');
                    dayElement.className = 'calendar-day';
                    dayElement.textContent = day;
                    
                    const date = new Date(year, month, day);
                    
                    // Check if this is today
                    if (this.isSameDay(date, today)) {
                        dayElement.classList.add('today');
                    }
                    
                    // Check if this is selected date
                    if (this.isSameDay(date, this.state.selectedDate)) {
                        dayElement.classList.add('selected');
                    }
                    
                    // Check if date has recordings from calendar data
                    const dateKey = this.formatDate(date);
                    if (this.state.calendarData[dateKey]) {
                        dayElement.classList.add('has-recordings');
                    }
                    
                    // Disable future dates
                    if (date > today) {
                        dayElement.classList.add('disabled');
                    } else {
                        dayElement.addEventListener('click', () => {
                            this.state.selectedDate = date;
                            this.renderCalendar();
                            this.loadRecordingsForDate();
                        });
                    }
                    
                    this.calendarGrid.appendChild(dayElement);
                }
            }
            
            async loadCalendarData() {
                if (!this.state.serviceOnline || !this.state.currentCamera) return;
                
                try {
                    const year = this.state.currentDate.getFullYear();
                    const month = this.state.currentDate.getMonth() + 1;
                    
                    // For now, mark current date as having recordings
                    const today = new Date();
                    const todayKey = this.formatDate(today);
                    this.state.calendarData = {
                        [todayKey]: { has_recordings: true }
                    };
                    
                    // Re-render calendar to show recording indicators
                    this.renderCalendar();
                    
                } catch (error) {
                    console.warn('Failed to load calendar data:', error);
                    // Don't show error to user, calendar will still function
                }
            }
            
            async loadRecordingsForDate() {
                if (!this.state.serviceOnline || !this.state.currentCamera) {
                    this.renderEmptyRecordingsList('Service offline');
                    return;
                }
                
                this.showRecordingsLoading();
                
                try {
                    const dateStr = this.formatDate(this.state.selectedDate);
                    
                    const data = await this.api.fetchWithRetry(
                        \`/api/v1/recordings/cameras/\${this.state.currentCamera}/timeline?date=\${dateStr}\`
                    );
                    
                    this.state.recordings = data.segments || [];
                    this.state.timelineSegments = data.timeline || data.segments || [];
                    
                    // Categorize recordings as playable or unplayable
                    this.state.playableRecordings = [];
                    this.state.unplayableRecordings = [];
                    
                    this.state.recordings.forEach(recording => {
                        const playabilityInfo = this.isRecordingPlayable(recording);
                        recording.playabilityInfo = playabilityInfo;
                        
                        if (playabilityInfo.playable) {
                            this.state.playableRecordings.push(recording);
                        } else {
                            this.state.unplayableRecordings.push(recording);
                        }
                    });
                    
                    this.renderRecordingsList();
                    this.renderTimeline();
                    
                    // Clear any previous video
                    this.clearVideo();
                    
                    // Auto-play first PLAYABLE recording if available
                    if (this.state.playableRecordings.length > 0 && this.state.serviceOnline) {
                        await this.playRecording(this.state.playableRecordings[0]);
                    } else if (this.state.recordings.length > 0 && this.state.playableRecordings.length === 0) {
                        // Show warning if no playable recordings
                        this.showUnplayableMessage();
                    }
                    
                } catch (error) {
                    console.error('Failed to load recordings:', error);
                    this.showStatus('Failed to load recordings', 'error');
                    this.renderEmptyRecordingsList('Failed to load recordings');
                    this.state.recordings = [];
                    this.state.timelineSegments = [];
                    this.renderTimeline();
                }
            }
            
            showRecordingsLoading() {
                this.recordingsList.innerHTML = \`
                    <div class="skeleton skeleton-item"></div>
                    <div class="skeleton skeleton-item"></div>
                    <div class="skeleton skeleton-item"></div>
                \`;
                this.recordingCount.textContent = 'Loading...';
            }
            
            renderRecordingsList() {
                const playableCount = this.state.playableRecordings.length;
                const totalCount = this.state.recordings.length;
                
                // Update count with playable info
                this.recordingCount.innerHTML = \`\${totalCount} clips\`;
                if (playableCount < totalCount) {
                    this.recordingCount.innerHTML += \`<span class="playable-count">(\${playableCount} playable)</span>\`;
                }
                
                if (this.state.recordings.length === 0) {
                    this.renderEmptyRecordingsList('No recordings found');
                    return;
                }
                
                this.recordingsList.innerHTML = this.state.recordings.map((recording, index) => {
                    const startTime = new Date(recording.start_time);
                    const duration = this.formatDuration(recording.duration_seconds || 0);
                    const fileSize = this.formatFileSize(recording.file_size || 0);
                    const playabilityInfo = recording.playabilityInfo || {};
                    const isPlayable = playabilityInfo.playable;
                    const format = playabilityInfo.format || 'unknown';
                    
                    // Format badge HTML
                    let formatBadge = '';
                    if (format === 'avi') {
                        formatBadge = '<span class="format-badge avi">AVI</span>';
                    } else if (format === 'legacy') {
                        formatBadge = '<span class="format-badge legacy">Legacy MP4</span>';
                    } else if (format === 'mp4' && isPlayable) {
                        formatBadge = '<span class="format-badge mp4">MP4</span>';
                    }
                    
                    return \`
                        <div class="recording-item \${!isPlayable ? 'unplayable' : ''}" 
                             data-index="\${index}"
                             title="\${!isPlayable ? playabilityInfo.reason : ''}">
                            <div class="recording-info">
                                <div class="recording-time">
                                    \${startTime.toLocaleTimeString()}
                                    \${formatBadge}
                                </div>
                                <div class="recording-details">
                                    <span><i class="fas fa-clock"></i> \${duration}</span>
                                    <span><i class="fas fa-hdd"></i> \${fileSize}</span>
                                </div>
                            </div>
                            <div class="recording-play">
                                <i class="fas \${!isPlayable ? 'fa-times-circle' : 'fa-play-circle'}"></i>
                            </div>
                        </div>
                    \`;
                }).join('');
                
                // Add click handlers
                this.recordingsList.querySelectorAll('.recording-item').forEach((item) => {
                    item.addEventListener('click', async (e) => {
                        const index = parseInt(e.currentTarget.dataset.index);
                        const recording = this.state.recordings[index];
                        
                        if (recording.playabilityInfo && !recording.playabilityInfo.playable) {
                            // Show message for unplayable recording
                            this.showStatus(
                                \`Cannot play: \${recording.playabilityInfo.reason}\`,
                                'warning',
                                5000
                            );
                        } else {
                            await this.playRecording(recording);
                        }
                    });
                });
            }
            
            renderEmptyRecordingsList(message) {
                this.recordingsList.innerHTML = \`
                    <div class="empty-state">
                        <i class="fas fa-film"></i>
                        <p>\${message}</p>
                    </div>
                \`;
                this.recordingCount.textContent = '0 clips';
            }
            
            renderTimeline() {
                this.timelineTrack.innerHTML = '';
                
                if (this.state.timelineSegments.length === 0) return;
                
                const dayStart = new Date(this.state.selectedDate);
                dayStart.setHours(0, 0, 0, 0);
                const dayEnd = new Date(this.state.selectedDate);
                dayEnd.setHours(23, 59, 59, 999);
                const dayDuration = dayEnd - dayStart;
                
                this.state.timelineSegments.forEach((segment, index) => {
                    const startTime = new Date(segment.start_time);
                    const duration = segment.duration_seconds || 0;
                    const endTime = new Date(startTime.getTime() + duration * 1000);
                    
                    // Calculate position and width as percentages
                    const startPercent = Math.max(0, ((startTime - dayStart) / dayDuration) * 100);
                    const widthPercent = Math.min(
                        100 - startPercent,
                        ((endTime - startTime) / dayDuration) * 100
                    );
                    
                    if (widthPercent > 0) {
                        const segmentEl = document.createElement('div');
                        segmentEl.className = 'timeline-segment';
                        
                        // Check if this segment is playable
                        const recording = this.state.recordings.find(r => r.filename === segment.filename);
                        if (recording && recording.playabilityInfo && !recording.playabilityInfo.playable) {
                            segmentEl.classList.add('unplayable');
                            segmentEl.title = recording.playabilityInfo.reason;
                        }
                        
                        segmentEl.style.left = \`\${startPercent}%\`;
                        segmentEl.style.width = \`\${widthPercent}%\`;
                        segmentEl.dataset.index = index;
                        
                        if (this.state.currentRecording && 
                            this.state.currentRecording.filename === segment.filename) {
                            segmentEl.classList.add('playing');
                        }
                        
                        this.timelineTrack.appendChild(segmentEl);
                    }
                });
            }
            
            handleTimelineClick(e) {
                if (!this.state.timelineSegments.length) return;
                
                const rect = this.timelineTrack.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const percentage = x / rect.width;
                
                // Find which segment was clicked
                const dayStart = new Date(this.state.selectedDate);
                dayStart.setHours(0, 0, 0, 0);
                const dayDuration = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
                const clickTime = new Date(dayStart.getTime() + dayDuration * percentage);
                
                // Find the segment that contains this time
                for (let i = 0; i < this.state.timelineSegments.length; i++) {
                    const segment = this.state.timelineSegments[i];
                    const startTime = new Date(segment.start_time);
                    const endTime = new Date(startTime.getTime() + (segment.duration_seconds || 0) * 1000);
                    
                    if (clickTime >= startTime && clickTime <= endTime) {
                        // Find corresponding recording
                        const recording = this.state.recordings.find(r => 
                            r.filename === segment.filename || r.id === segment.id
                        );
                        if (recording) {
                            this.playRecording(recording);
                        }
                        break;
                    }
                }
            }
            
            async playRecording(recording) {
                if (!this.state.serviceOnline) {
                    this.showStatus('Recording service is offline', 'warning');
                    return;
                }
                
                try {
                    this.state.currentRecording = recording;
                    
                    // Update UI to show playing state
                    this.recordingsList.querySelectorAll('.recording-item').forEach(item => {
                        item.classList.remove('playing');
                    });
                    
                    const recordingElements = this.recordingsList.querySelectorAll('.recording-item');
                    const index = this.state.recordings.indexOf(recording);
                    if (index >= 0 && recordingElements[index]) {
                        recordingElements[index].classList.add('playing');
                    }
                    
                    // Update timeline
                    this.renderTimeline();
                    
                    // Show video player
                    this.videoPlaceholder.style.display = 'none';
                    this.videoPlayer.style.display = 'block';
                    this.videoError.style.display = 'none';
                    
                    // Construct video URL
                    const videoUrl = \`\${CONFIG.RECORDING_SERVICE_URL}/api/v1/recordings/stream/\${recording.filename}\`;
                    
                    console.log('Loading video:', {
                        filename: recording.filename,
                        url: videoUrl,
                        recording: recording
                    });
                    
                    // Update video source
                    this.videoPlayer.src = videoUrl;
                    this.videoPlayer.load();
                    
                } catch (error) {
                    console.error('Failed to play recording:', error);
                    this.showStatus('Failed to play recording', 'error');
                    this.showVideoError();
                }
            }
            
            clearVideo() {
                this.videoPlayer.pause();
                this.videoPlayer.src = '';
                this.videoPlayer.style.display = 'none';
                this.videoPlaceholder.style.display = 'flex';
                this.videoError.style.display = 'none';
                this.state.currentRecording = null;
                this.disableControls();
                this.updateTimeDisplay();
            }
            
            showVideoLoading() {
                this.videoLoading.style.display = 'flex';
                this.videoError.style.display = 'none';
            }
            
            hideVideoLoading() {
                this.videoLoading.style.display = 'none';
            }
            
            showVideoError() {
                this.videoError.style.display = 'flex';
                this.videoLoading.style.display = 'none';
                this.videoPlayer.style.display = 'none';
                this.disableControls();
            }
            
            handleVideoError(e) {
                console.error('Video playback error:', e);
                
                const video = e.target;
                
                // Ignore errors if no valid video source
                if (!video.src || video.src === '' || video.src === window.location.href || video.src.endsWith('8080/')) {
                    console.log('Ignoring video error - no valid source set');
                    return;
                }
                
                // Log debug information for troubleshooting
                console.error('Video debug info:', {
                    videoSrc: video.src,
                    networkState: video.networkState,
                    readyState: video.readyState,
                    errorCode: video.error ? video.error.code : 'No error code',
                    errorMessage: video.error ? video.error.message : 'No error message'
                });
                
                this.showVideoError();
                this.showStatus('Unable to play video', 'error');
            }
            
            
            togglePlayPause() {
                if (!this.videoPlayer.src || this.videoPlayer.readyState < 2) return;
                
                if (this.videoPlayer.paused) {
                    this.videoPlayer.play().catch(error => {
                        console.error('Play failed:', error);
                        this.showStatus('Failed to play video', 'error');
                    });
                } else {
                    this.videoPlayer.pause();
                }
            }
            
            updateTimeDisplay() {
                const current = this.formatTime(this.videoPlayer.currentTime || 0);
                const duration = this.formatTime(this.videoPlayer.duration || 0);
                this.timeDisplay.textContent = \`\${current} / \${duration}\`;
            }
            
            // Utility functions
            formatDate(date) {
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return \`\${year}-\${month}-\${day}\`;
            }
            
            formatTime(seconds) {
                if (!isFinite(seconds)) return '--:--:--';
                const h = Math.floor(seconds / 3600);
                const m = Math.floor((seconds % 3600) / 60);
                const s = Math.floor(seconds % 60);
                return \`\${String(h).padStart(2, '0')}:\${String(m).padStart(2, '0')}:\${String(s).padStart(2, '0')}\`;
            }
            
            formatDuration(seconds) {
                if (!seconds || !isFinite(seconds)) return '0s';
                if (seconds < 60) return \`\${Math.floor(seconds)}s\`;
                const minutes = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                if (minutes < 60) return \`\${minutes}m \${secs}s\`;
                const hours = Math.floor(minutes / 60);
                const mins = minutes % 60;
                return \`\${hours}h \${mins}m\`;
            }
            
            formatFileSize(bytes) {
                if (!bytes || !isFinite(bytes)) return '0 B';
                const units = ['B', 'KB', 'MB', 'GB'];
                let size = bytes;
                let unitIndex = 0;
                
                while (size >= 1024 && unitIndex < units.length - 1) {
                    size /= 1024;
                    unitIndex++;
                }
                
                return \`\${size.toFixed(1)} \${units[unitIndex]}\`;
            }
            
            isSameDay(date1, date2) {
                return date1.getFullYear() === date2.getFullYear() &&
                       date1.getMonth() === date2.getMonth() &&
                       date1.getDate() === date2.getDate();
            }
            
            showStatus(message, type = 'info', duration = 3000) {
                // Remove any existing status messages
                document.querySelectorAll('.status-message').forEach(el => el.remove());
                
                const statusEl = document.createElement('div');
                statusEl.className = \`status-message \${type}\`;
                statusEl.innerHTML = \`
                    <i class="fas fa-\${
                        type === 'error' ? 'exclamation-circle' : 
                        type === 'success' ? 'check-circle' : 
                        type === 'warning' ? 'exclamation-triangle' :
                        'info-circle'
                    }"></i>
                    <span>\${message}</span>
                \`;
                
                document.body.appendChild(statusEl);
                
                // Auto-remove after duration
                if (duration > 0) {
                    setTimeout(() => {
                        statusEl.remove();
                    }, duration);
                }
            }
            
            showUnplayableMessage() {
                const videoContainer = document.querySelector('.video-container');
                if (!videoContainer) return;
                
                // Hide all video elements
                this.videoPlaceholder.style.display = 'none';
                this.videoPlayer.style.display = 'none';
                this.videoError.style.display = 'none';
                
                // Create and show unplayable message
                const messageDiv = document.createElement('div');
                messageDiv.className = 'unplayable-message';
                messageDiv.style.position = 'absolute';
                messageDiv.style.top = '50%';
                messageDiv.style.left = '50%';
                messageDiv.style.transform = 'translate(-50%, -50%)';
                messageDiv.style.maxWidth = '400px';
                messageDiv.innerHTML = \`
                    <i class="fas fa-exclamation-triangle"></i>
                    <div>
                        <strong>No playable recordings</strong><br>
                        All recordings for this date are in legacy formats (AVI or corrupted MP4) 
                        that cannot be played in browsers. New recordings will use the correct MP4 format.
                    </div>
                \`;
                
                // Remove any existing message
                videoContainer.querySelector('.unplayable-message')?.remove();
                videoContainer.appendChild(messageDiv);
            }
            
            // Cleanup
            destroy() {
                if (this.healthCheckInterval) {
                    clearInterval(this.healthCheckInterval);
                }
                this.videoPlayer.pause();
                this.videoPlayer.src = '';
            }
        }
        
        // Global instance for debugging
        let recordingsPage;
        
        // Initialize the page immediately
        recordingsPage = new RecordingsPageApp();
        
        // Make it globally accessible
        window.recordingsPage = recordingsPage;
        `;
        
        document.head.appendChild(script);
    }
    
    destroy() {
        if (window.recordingsPage) {
            window.recordingsPage.destroy();
        }
    }
}

export default RecordingsPage;