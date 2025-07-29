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
            // Get timeline data
            const timelineData = await playbackService.getTimeline(
                cameraId,
                startTime,
                endTime
            );
            
            this.segments = timelineData.segments || [];
            this.timeRange = { startTime, endTime };
            
            // Update timeline display
            this.updateTimelineDisplay();
            
            // Load first segment if available
            if (this.segments.length > 0) {
                await this.loadSegment(this.segments[0]);
            }
            
        } catch (error) {
            console.error('Failed to load time range:', error);
            this.showError('Failed to load recordings');
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Load a specific segment
     */
    async loadSegment(segment) {
        if (!segment || this.loadingSegment) return;
        
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
            this.showError('Failed to load video segment');
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
        // Try to load next segment
        this.loadNextSegment();
    }
    
    onVideoError(error) {
        console.error('Video error:', error);
        this.showError('Video playback error');
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
    
    showError(message) {
        console.error('Playback error:', message);
        // Could show error overlay here
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