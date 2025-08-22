/**
 * Video Playback Player Component
 * Professional video player with timeline scrubbing for recorded segments
 */
import playbackService from '../../services/PlaybackService.js';

class VideoPlaybackPlayer {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.getElementById(container) : container;
        this.options = {
            cameraId: options.cameraId || null,
            autoplay: options.autoplay || false,
            controls: options.controls !== false,
            timeline: options.timeline !== false,
            ...options
        };
        
        // State
        this.currentSegment = null;
        this.segments = [];
        this.isPlaying = false;
        this.currentTime = 0;
        this.duration = 0;
        this.volume = 1.0;
        this.playbackRate = 1.0;
        
        // DOM elements
        this.video = null;
        this.controls = null;
        this.timeline = null;
        this.timeDisplay = null;
        
        // Playback state
        this.timeRange = null;
        this.loadingSegment = false;
        
        this.init();
    }
    
    init() {
        this.createPlayer();
        this.attachEventListeners();
    }
    
    createPlayer() {
        this.container.innerHTML = this.getTemplate();
        
        // Get DOM references
        this.video = this.container.querySelector('.playback-video');
        this.controls = this.container.querySelector('.playback-controls');
        this.timeline = this.container.querySelector('.timeline-container');
        this.timeDisplay = this.container.querySelector('.time-display');
        
        // Setup video element
        this.video.preload = 'metadata';
        if (this.options.autoplay) {
            this.video.autoplay = true;
        }
    }
    
    getTemplate() {
        return `
            <div class="video-playback-player">
                <div class="video-container">
                    <video class="playback-video" ${this.options.controls ? 'controls' : ''}></video>
                    <div class="video-overlay">
                        <div class="loading-indicator" style="display: none;">
                            <i class="fas fa-spinner fa-spin"></i>
                            <span>Loading...</span>
                        </div>
                        <div class="play-overlay" style="display: none;">
                            <button class="play-btn">
                                <i class="fas fa-play"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                ${this.options.controls ? this.getControlsTemplate() : ''}
                ${this.options.timeline ? this.getTimelineTemplate() : ''}
            </div>
        `;
    }
    
    getControlsTemplate() {
        return `
            <div class="playback-controls">
                <div class="controls-left">
                    <button class="control-btn play-pause-btn" title="Play/Pause">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="control-btn stop-btn" title="Stop">
                        <i class="fas fa-stop"></i>
                    </button>
                    <div class="volume-control">
                        <button class="control-btn volume-btn" title="Volume">
                            <i class="fas fa-volume-up"></i>
                        </button>
                        <input type="range" class="volume-slider" min="0" max="1" step="0.1" value="1">
                    </div>
                    <div class="time-display">
                        <span class="current-time">00:00</span>
                        <span class="separator">/</span>
                        <span class="total-time">00:00</span>
                    </div>
                </div>
                
                <div class="controls-center">
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-filled"></div>
                            <div class="progress-handle"></div>
                        </div>
                    </div>
                </div>
                
                <div class="controls-right">
                    <div class="speed-control">
                        <select class="speed-select">
                            <option value="0.25">0.25x</option>
                            <option value="0.5">0.5x</option>
                            <option value="1" selected>1x</option>
                            <option value="1.25">1.25x</option>
                            <option value="1.5">1.5x</option>
                            <option value="2">2x</option>
                        </select>
                    </div>
                    <button class="control-btn fullscreen-btn" title="Fullscreen">
                        <i class="fas fa-expand"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    getTimelineTemplate() {
        return `
            <div class="timeline-container">
                <div class="timeline-header">
                    <div class="timeline-date"></div>
                    <div class="timeline-info">
                        <span class="segment-count">0 segments</span>
                        <span class="total-duration">0:00:00</span>
                    </div>
                </div>
                <div class="timeline-track">
                    <div class="timeline-segments"></div>
                    <div class="timeline-cursor"></div>
                </div>
                <div class="timeline-scale">
                    <div class="timeline-hours"></div>
                </div>
            </div>
        `;
    }
    
    attachEventListeners() {
        // Video events
        this.video.addEventListener('loadedmetadata', () => this.onVideoLoaded());
        this.video.addEventListener('timeupdate', () => this.onTimeUpdate());
        this.video.addEventListener('play', () => this.onPlay());
        this.video.addEventListener('pause', () => this.onPause());
        this.video.addEventListener('ended', () => this.onEnded());
        this.video.addEventListener('error', (e) => this.onVideoError(e));
        
        if (this.options.controls) {
            this.attachControlsListeners();
        }
        
        if (this.options.timeline) {
            this.attachTimelineListeners();
        }
    }
    
    attachControlsListeners() {
        // Play/Pause button
        const playPauseBtn = this.controls.querySelector('.play-pause-btn');
        playPauseBtn?.addEventListener('click', () => this.togglePlayPause());
        
        // Stop button
        const stopBtn = this.controls.querySelector('.stop-btn');
        stopBtn?.addEventListener('click', () => this.stop());
        
        // Volume control
        const volumeSlider = this.controls.querySelector('.volume-slider');
        volumeSlider?.addEventListener('input', (e) => this.setVolume(parseFloat(e.target.value)));
        
        // Speed control
        const speedSelect = this.controls.querySelector('.speed-select');
        speedSelect?.addEventListener('change', (e) => this.setPlaybackRate(parseFloat(e.target.value)));
        
        // Progress bar
        const progressContainer = this.controls.querySelector('.progress-container');
        progressContainer?.addEventListener('click', (e) => this.seekToProgress(e));
        
        // Fullscreen
        const fullscreenBtn = this.controls.querySelector('.fullscreen-btn');
        fullscreenBtn?.addEventListener('click', () => this.toggleFullscreen());
    }
    
    attachTimelineListeners() {
        const timelineTrack = this.timeline?.querySelector('.timeline-track');
        timelineTrack?.addEventListener('click', (e) => this.seekToTimelinePosition(e));
    }
    
    /**
     * Load recordings for a specific time range
     */
    async loadTimeRange(cameraId, startTime, endTime) {
        if (!cameraId) {
            throw new Error('Camera ID is required');
        }
        
        this.showLoading(true);
        
        try {
            // Convert time range to date format for API
            const date = playbackService.formatDate(new Date(startTime));
            
            // Get timeline segments for the date
            const timelineData = await playbackService.getTimelineSegments(cameraId, date);
            
            this.segments = playbackService.processTimelineSegments(timelineData.segments || []);
            this.timeRange = { startTime, endTime, cameraId, date };
            
            // Update timeline display
            this.updateTimelineDisplay();
            
            // Load first segment if available
            if (this.segments.length > 0) {
                await this.loadSegment(this.segments[0]);
            } else {
                this.showNoRecordings();
            }
            
        } catch (error) {
            console.error('Failed to load time range:', error);
            this.showError();
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Load recordings for a specific date
     */
    async loadRecordingsForDate(cameraId, date) {
        if (!cameraId || !date) {
            throw new Error('Camera ID and date are required');
        }
        
        this.showLoading(true);
        
        try {
            const dateStr = typeof date === 'string' ? date : playbackService.formatDate(date);
            
            // Get timeline segments for the date
            const timelineData = await playbackService.getTimelineSegments(cameraId, dateStr);
            
            this.segments = playbackService.processTimelineSegments(timelineData.segments || []);
            this.timeRange = { 
                cameraId, 
                date: dateStr,
                totalDuration: timelineData.total_duration || 0,
                totalSize: timelineData.total_size || 0,
                coveragePercentage: timelineData.coverage_percentage || 0
            };
            
            // Update timeline display
            this.updateTimelineDisplay();
            
            // Load first segment if available and autoplay is enabled
            if (this.segments.length > 0) {
                // Prefer MP4 files over AVI files for better browser compatibility
                const firstSegment = this.findBestSegmentToLoad(this.segments);
                await this.loadSegment(firstSegment);
                if (this.options.autoplay) {
                    this.play();
                }
            } else {
                this.showNoRecordings();
            }
            
        } catch (error) {
            console.error('Failed to load recordings for date:', error);
            this.showError();
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Find the best segment to load (prefer MP4 over AVI for browser compatibility)
     */
    findBestSegmentToLoad(segments) {
        if (!segments || segments.length === 0) return null;
        
        // First, try to find an MP4 file
        const mp4Segment = segments.find(segment => 
            segment.filename && segment.filename.toLowerCase().endsWith('.mp4')
        );
        
        if (mp4Segment) {
            console.log('Selected MP4 segment for playback:', mp4Segment.filename);
            return mp4Segment;
        }
        
        // Fallback to first segment (likely AVI) - but warn user
        console.warn('No MP4 segments found, using first available segment (may have compatibility issues):', segments[0]?.filename);
        return segments[0];
    }
    
    /**
     * Check if segment is compatible with browser video playback
     */
    isBrowserCompatible(segment) {
        if (!segment || !segment.filename) return false;
        
        const filename = segment.filename.toLowerCase();
        const compatibleFormats = ['.mp4', '.webm', '.ogg'];
        
        return compatibleFormats.some(format => filename.endsWith(format));
    }
    
    /**
     * Load a specific segment
     */
    async loadSegment(segment) {
        if (!segment || this.loadingSegment) return;
        
        // Check if segment is browser-compatible
        if (!this.isBrowserCompatible(segment)) {
            console.warn('Segment not browser compatible:', segment.filename);
            this.showError();
            return;
        }
        
        this.loadingSegment = true;
        this.showLoading(true);
        
        try {
            const streamUrl = playbackService.getStreamUrl(segment.filename);
            
            // Update video source
            this.video.src = streamUrl;
            this.currentSegment = segment;
            
            // Wait for video to load
            await new Promise((resolve, reject) => {
                const onLoad = () => {
                    this.video.removeEventListener('loadeddata', onLoad);
                    this.video.removeEventListener('error', onError);
                    resolve();
                };
                
                const onError = (e) => {
                    this.video.removeEventListener('loadeddata', onLoad);
                    this.video.removeEventListener('error', onError);
                    reject(e);
                };
                
                this.video.addEventListener('loadeddata', onLoad);
                this.video.addEventListener('error', onError);
            });
            
        } catch (error) {
            console.error('Failed to load segment:', error);
            this.showError();
        } finally {
            this.loadingSegment = false;
            this.showLoading(false);
        }
    }
    
    /**
     * Seek to a specific time in the timeline
     */
    async seekToTime(timestamp) {
        // Find the segment containing this timestamp
        const targetTime = new Date(timestamp);
        
        for (const segment of this.segments) {
            const segmentStart = new Date(segment.start_time);
            const segmentEnd = new Date(segment.end_time);
            
            if (targetTime >= segmentStart && targetTime <= segmentEnd) {
                // Load this segment
                await this.loadSegment(segment);
                
                // Calculate offset within segment
                const offsetSeconds = (targetTime - segmentStart) / 1000;
                this.video.currentTime = offsetSeconds;
                
                return;
            }
        }
        
        console.warn('No segment found for timestamp:', timestamp);
    }
    
    // Playback controls
    play() {
        this.video.play();
    }
    
    pause() {
        this.video.pause();
    }
    
    stop() {
        this.video.pause();
        this.video.currentTime = 0;
    }
    
    togglePlayPause() {
        if (this.video.paused) {
            this.play();
        } else {
            this.pause();
        }
    }
    
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        this.video.volume = this.volume;
        
        // Update volume icon
        const volumeBtn = this.controls?.querySelector('.volume-btn i');
        if (volumeBtn) {
            if (this.volume === 0) {
                volumeBtn.className = 'fas fa-volume-mute';
            } else if (this.volume < 0.5) {
                volumeBtn.className = 'fas fa-volume-down';
            } else {
                volumeBtn.className = 'fas fa-volume-up';
            }
        }
    }
    
    setPlaybackRate(rate) {
        this.playbackRate = rate;
        this.video.playbackRate = rate;
    }
    
    // Event handlers
    onVideoLoaded() {
        this.duration = this.video.duration;
        this.updateTimeDisplay();
        this.updateProgressBar();
    }
    
    onTimeUpdate() {
        this.currentTime = this.video.currentTime;
        this.updateTimeDisplay();
        this.updateProgressBar();
        this.updateTimelineCursor();
    }
    
    onPlay() {
        this.isPlaying = true;
        const playPauseBtn = this.controls?.querySelector('.play-pause-btn i');
        if (playPauseBtn) {
            playPauseBtn.className = 'fas fa-pause';
        }
    }
    
    onPause() {
        this.isPlaying = false;
        const playPauseBtn = this.controls?.querySelector('.play-pause-btn i');
        if (playPauseBtn) {
            playPauseBtn.className = 'fas fa-play';
        }
    }
    
    onEnded() {
        // Try to load next segment for continuous playback
        this.loadNextSegment();
    }

    /**
     * Load next segment in sequence
     */
    async loadNextSegment() {
        if (!this.currentSegment || !this.segments.length) return;
        
        const currentIndex = this.segments.findIndex(s => s.filename === this.currentSegment.filename);
        if (currentIndex < this.segments.length - 1) {
            const nextSegment = this.segments[currentIndex + 1];
            
            // Check for gap before next segment
            if (nextSegment.has_gap_before) {
                this.showGapIndicator(nextSegment.gap_duration);
                // Wait a moment to show gap indicator
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            
            await this.loadSegment(nextSegment);
            if (this.isPlaying) {
                this.play();
            }
        } else {
            // End of recordings
            this.showEndOfRecordings();
        }
    }

    /**
     * Load previous segment in sequence
     */
    async loadPreviousSegment() {
        if (!this.currentSegment || !this.segments.length) return;
        
        const currentIndex = this.segments.findIndex(s => s.filename === this.currentSegment.filename);
        if (currentIndex > 0) {
            const prevSegment = this.segments[currentIndex - 1];
            await this.loadSegment(prevSegment);
            if (this.isPlaying) {
                this.play();
            }
        }
    }
    
    onVideoError(error) {
        console.error('Video error:', error);
        this.showError();
    }
    
    // UI updates
    updateTimeDisplay() {
        if (!this.timeDisplay) return;
        
        const currentTimeEl = this.timeDisplay.querySelector('.current-time');
        const totalTimeEl = this.timeDisplay.querySelector('.total-time');
        
        if (currentTimeEl) {
            currentTimeEl.textContent = this.formatTime(this.currentTime);
        }
        if (totalTimeEl) {
            totalTimeEl.textContent = this.formatTime(this.duration);
        }
    }
    
    updateProgressBar() {
        if (!this.controls) return;
        
        const progressFilled = this.controls.querySelector('.progress-filled');
        const progressHandle = this.controls.querySelector('.progress-handle');
        
        if (progressFilled && this.duration > 0) {
            const progress = (this.currentTime / this.duration) * 100;
            progressFilled.style.width = `${progress}%`;
            if (progressHandle) {
                progressHandle.style.left = `${progress}%`;
            }
        }
    }
    
    updateTimelineDisplay() {
        if (!this.timeline || !this.segments.length) return;
        
        // Update timeline info
        const segmentCount = this.timeline.querySelector('.segment-count');
        const totalDuration = this.timeline.querySelector('.total-duration');
        
        if (segmentCount) {
            segmentCount.textContent = `${this.segments.length} segments`;
        }
        
        if (totalDuration) {
            const total = this.segments.reduce((sum, seg) => sum + seg.duration_seconds, 0);
            totalDuration.textContent = playbackService.formatDuration(total);
        }
        
        // Render timeline segments
        this.renderTimelineSegments();
    }
    
    renderTimelineSegments() {
        const segmentsContainer = this.timeline?.querySelector('.timeline-segments');
        if (!segmentsContainer || !this.segments.length) return;
        
        segmentsContainer.innerHTML = '';
        
        // Calculate timeline scale
        const startTime = new Date(this.timeRange.startTime).getTime();
        const endTime = new Date(this.timeRange.endTime).getTime();
        const totalDuration = endTime - startTime;
        
        this.segments.forEach(segment => {
            const segmentStart = new Date(segment.start_time).getTime();
            const segmentEnd = new Date(segment.end_time).getTime();
            
            const leftPercent = ((segmentStart - startTime) / totalDuration) * 100;
            const widthPercent = ((segmentEnd - segmentStart) / totalDuration) * 100;
            
            const segmentEl = document.createElement('div');
            segmentEl.className = 'timeline-segment';
            segmentEl.style.left = `${leftPercent}%`;
            segmentEl.style.width = `${widthPercent}%`;
            segmentEl.title = `${segment.filename} (${playbackService.formatDuration(segment.duration_seconds)})`;
            
            segmentEl.addEventListener('click', () => this.loadSegment(segment));
            
            segmentsContainer.appendChild(segmentEl);
        });
    }
    
    // Utility methods
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    showLoading(show) {
        const loadingIndicator = this.container.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = show ? 'flex' : 'none';
        }
    }
    
    showError(message = 'Unable to play video') {
        console.error('Playback error:', message);
        
        // Show simplified error overlay
        const videoContainer = this.container.querySelector('.video-container');
        if (videoContainer) {
            const existingError = videoContainer.querySelector('.error-overlay');
            if (existingError) {
                existingError.remove();
            }
            
            const errorOverlay = document.createElement('div');
            errorOverlay.className = 'error-overlay';
            errorOverlay.innerHTML = `
                <div class="error-content">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Unable to Play Video</h3>
                    <p>Please try a different recording or check your connection.</p>
                </div>
            `;
            
            videoContainer.appendChild(errorOverlay);
        }
    }

    showNoRecordings() {
        const videoContainer = this.container.querySelector('.video-container');
        if (videoContainer) {
            const noRecordingsOverlay = document.createElement('div');
            noRecordingsOverlay.className = 'no-recordings-overlay';
            noRecordingsOverlay.innerHTML = `
                <div class="no-recordings-content">
                    <i class="fas fa-video-slash"></i>
                    <h3>No Recordings Available</h3>
                    <p>No video recordings found for the selected time period.</p>
                </div>
            `;
            
            videoContainer.appendChild(noRecordingsOverlay);
        }
    }

    showGapIndicator(gapDuration) {
        const videoContainer = this.container.querySelector('.video-container');
        if (videoContainer) {
            const gapOverlay = document.createElement('div');
            gapOverlay.className = 'gap-overlay';
            gapOverlay.innerHTML = `
                <div class="gap-content">
                    <i class="fas fa-pause-circle"></i>
                    <h3>Recording Gap</h3>
                    <p>No recording for ${playbackService.formatDuration(gapDuration)}</p>
                </div>
            `;
            
            videoContainer.appendChild(gapOverlay);
            
            // Auto-remove after 2 seconds
            setTimeout(() => {
                gapOverlay.remove();
            }, 2000);
        }
    }

    showEndOfRecordings() {
        const videoContainer = this.container.querySelector('.video-container');
        if (videoContainer) {
            const endOverlay = document.createElement('div');
            endOverlay.className = 'end-overlay';
            endOverlay.innerHTML = `
                <div class="end-content">
                    <i class="fas fa-stop-circle"></i>
                    <h3>End of Recordings</h3>
                    <p>You have reached the end of available recordings.</p>
                    <button class="btn btn-primary restart-btn">Restart</button>
                </div>
            `;
            
            endOverlay.querySelector('.restart-btn').addEventListener('click', () => {
                endOverlay.remove();
                if (this.segments.length > 0) {
                    this.loadSegment(this.segments[0]);
                }
            });
            
            videoContainer.appendChild(endOverlay);
        }
    }

    /**
     * Toggle fullscreen mode
     */
    toggleFullscreen() {
        const videoContainer = this.container.querySelector('.video-container');
        
        if (!document.fullscreenElement) {
            if (videoContainer.requestFullscreen) {
                videoContainer.requestFullscreen();
            } else if (videoContainer.webkitRequestFullscreen) {
                videoContainer.webkitRequestFullscreen();
            } else if (videoContainer.msRequestFullscreen) {
                videoContainer.msRequestFullscreen();
            }
            
            // Update fullscreen button
            const fullscreenBtn = this.controls?.querySelector('.fullscreen-btn i');
            if (fullscreenBtn) {
                fullscreenBtn.className = 'fas fa-compress';
            }
            
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            
            // Update fullscreen button
            const fullscreenBtn = this.controls?.querySelector('.fullscreen-btn i');
            if (fullscreenBtn) {
                fullscreenBtn.className = 'fas fa-expand';
            }
        }
    }

    /**
     * Seek to progress bar position
     */
    seekToProgress(e) {
        if (!this.duration) return;
        
        const progressContainer = e.currentTarget;
        const rect = progressContainer.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = Math.max(0, Math.min(1, clickX / rect.width));
        
        const seekTime = percentage * this.duration;
        this.video.currentTime = seekTime;
    }

    /**
     * Seek to timeline position
     */
    seekToTimelinePosition(e) {
        if (!this.segments.length || !this.timeRange) return;
        
        const timelineTrack = e.currentTarget;
        const rect = timelineTrack.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = Math.max(0, Math.min(1, clickX / rect.width));
        
        // Calculate target timestamp within the day
        const dayStart = new Date(this.timeRange.date + 'T00:00:00.000Z');
        const targetTime = new Date(dayStart.getTime() + (percentage * 24 * 60 * 60 * 1000));
        
        // Find segment containing this time and seek to it
        this.seekToTime(targetTime.toISOString());
    }

    /**
     * Update timeline cursor position
     */
    updateTimelineCursor() {
        if (!this.timeline || !this.currentSegment) return;
        
        const cursor = this.timeline.querySelector('.timeline-cursor');
        if (!cursor) return;
        
        // Calculate current position within the day
        const segmentStart = new Date(this.currentSegment.start_time);
        const currentVideoTime = segmentStart.getTime() + (this.currentTime * 1000);
        
        const dayStart = new Date(this.timeRange.date + 'T00:00:00.000Z');
        const dayProgress = (currentVideoTime - dayStart.getTime()) / (24 * 60 * 60 * 1000);
        
        cursor.style.left = `${Math.max(0, Math.min(100, dayProgress * 100))}%`;
    }

    /**
     * Set minimal controls for fullscreen
     */
    setMinimalControls(minimal) {
        const controls = this.container.querySelector('.playback-controls');
        if (controls) {
            if (minimal) {
                controls.classList.add('minimal');
            } else {
                controls.classList.remove('minimal');
            }
        }
    }

    /**
     * Get current playback state
     */
    getPlaybackState() {
        return {
            currentSegment: this.currentSegment,
            currentTime: this.currentTime,
            duration: this.duration,
            isPlaying: this.isPlaying,
            playbackRate: this.playbackRate,
            volume: this.volume,
            segmentCount: this.segments.length,
            timeRange: this.timeRange
        };
    }
    
    // Cleanup
    destroy() {
        if (this.video) {
            this.video.pause();
            this.video.src = '';
        }
    }
}

export default VideoPlaybackPlayer;