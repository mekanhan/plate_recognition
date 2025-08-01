/**
 * Timeline Control Component
 * Timeline scrubber with segment visualization and gap indicators
 * Based on documentation requirements
 */
import playbackService from '../../services/PlaybackService.js';

class TimelineControl {
    constructor(container, options = {}) {
        this.container = container;
        this.segments = [];
        this.currentTime = 0; // Seconds from start of day
        this.duration = 86400; // 24 hours in seconds
        this.isDragging = false;
        this.selectedSegment = null;
        
        this.options = {
            onSeek: null,
            onSegmentClick: null,
            onSegmentHover: null,
            showHourMarkers: true,
            showMinuteMarkers: false,
            allowSeek: true,
            height: 80,
            ...options
        };
        
        // Colors for different segment types
        this.segmentColors = {
            continuous: '#28a745',      // Green: continuous recording
            motion: '#ffc107',          // Orange: motion detection
            alarm: '#dc3545',           // Red: alarm events
            gap: '#6c757d'              // Gray: gaps/no recording
        };
        
        this.init();
    }
    
    init() {
        this.render();
        this.attachEventListeners();
        this.renderTimeMarkers();
    }
    
    render() {
        if (!this.container) return;
        
        this.container.innerHTML = this.getTemplate();
    }
    
    getTemplate() {
        return `
            <div class="timeline-control" style="height: ${this.options.height}px;">
                <div class="timeline-header">
                    <div class="timeline-info">
                        <span class="current-time">00:00:00</span>
                        <span class="timeline-separator">•</span>
                        <span class="selected-segment-info">No segment selected</span>
                    </div>
                    <div class="timeline-controls">
                        <button class="btn btn-sm btn-secondary zoom-out" title="Zoom Out">
                            <i class="fas fa-search-minus"></i>
                        </button>
                        <button class="btn btn-sm btn-secondary zoom-in" title="Zoom In">
                            <i class="fas fa-search-plus"></i>
                        </button>
                        <button class="btn btn-sm btn-secondary fit-timeline" title="Fit to Timeline">
                            <i class="fas fa-expand-arrows-alt"></i>
                        </button>
                    </div>
                </div>
                
                <div class="timeline-body">
                    <div class="timeline-track">
                        <!-- Time markers will be rendered here -->
                        <div class="time-markers"></div>
                        
                        <!-- Segments will be rendered here -->
                        <div class="segments-container"></div>
                        
                        <!-- Current time cursor -->
                        <div class="timeline-cursor"></div>
                        
                        <!-- Hover indicator -->
                        <div class="timeline-hover-indicator"></div>
                    </div>
                </div>
                
                <div class="timeline-legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${this.segmentColors.continuous}"></div>
                        <span>Continuous Recording</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${this.segmentColors.motion}"></div>
                        <span>Motion Detection</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${this.segmentColors.alarm}"></div>
                        <span>Alarm Events</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${this.segmentColors.gap}"></div>
                        <span>Recording Gaps</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    attachEventListeners() {
        const track = this.container.querySelector('.timeline-track');
        const cursor = this.container.querySelector('.timeline-cursor');
        const hoverIndicator = this.container.querySelector('.timeline-hover-indicator');
        
        if (!track) return;
        
        // Mouse events for scrubbing
        track.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        track.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        track.addEventListener('mouseup', () => this.handleMouseUp());
        track.addEventListener('mouseleave', () => this.handleMouseLeave());
        
        // Prevent text selection during drag
        track.addEventListener('selectstart', (e) => e.preventDefault());
        
        // Global mouse events for dragging
        document.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                this.handleDrag(e);
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (this.isDragging) {
                this.handleMouseUp();
            }
        });
        
        // Zoom controls
        this.container.querySelector('.zoom-in')?.addEventListener('click', () => this.zoomIn());
        this.container.querySelector('.zoom-out')?.addEventListener('click', () => this.zoomOut());
        this.container.querySelector('.fit-timeline')?.addEventListener('click', () => this.fitToTimeline());
        
        // Keyboard shortcuts
        if (this.options.allowSeek) {
            document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        }
    }
    
    loadSegments(segments, totalDuration = null) {
        this.segments = playbackService.processTimelineSegments(segments || []);
        
        if (totalDuration) {
            this.duration = totalDuration;
        }
        
        this.renderSegments();
        this.updateTimelineInfo();
    }
    
    renderTimeMarkers() {
        const markersContainer = this.container.querySelector('.time-markers');
        if (!markersContainer) return;
        
        let markersHtml = '';
        
        // Hour markers
        if (this.options.showHourMarkers) {
            for (let hour = 0; hour < 24; hour++) {
                const position = (hour / 24) * 100;
                const timeStr = hour.toString().padStart(2, '0') + ':00';
                
                markersHtml += `
                    <div class="time-marker hour-marker" style="left: ${position}%;">
                        <div class="marker-line"></div>
                        <div class="marker-label">${timeStr}</div>
                    </div>
                `;
            }
        }
        
        // Minute markers (if enabled and zoomed in enough)
        if (this.options.showMinuteMarkers) {
            for (let hour = 0; hour < 24; hour++) {
                for (let minute = 15; minute < 60; minute += 15) {
                    const totalMinutes = hour * 60 + minute;
                    const position = (totalMinutes / (24 * 60)) * 100;
                    
                    markersHtml += `
                        <div class="time-marker minute-marker" style="left: ${position}%;">
                            <div class="marker-line"></div>
                        </div>
                    `;
                }
            }
        }
        
        markersContainer.innerHTML = markersHtml;
    }
    
    renderSegments() {
        const segmentsContainer = this.container.querySelector('.segments-container');
        if (!segmentsContainer || !this.segments.length) {
            segmentsContainer.innerHTML = '<div class="no-segments-message">No recordings available</div>';
            return;
        }
        
        let segmentsHtml = '';
        let lastEndTime = 0;
        
        // Get day start time for positioning calculations
        const dayStart = new Date(this.segments[0].start_time);
        dayStart.setHours(0, 0, 0, 0);
        const dayStartMs = dayStart.getTime();
        
        this.segments.forEach((segment, index) => {
            const startTimeMs = new Date(segment.start_time).getTime();
            const endTimeMs = new Date(segment.end_time).getTime();
            
            // Calculate position and width as percentage of 24 hours
            const startSeconds = (startTimeMs - dayStartMs) / 1000;
            const durationSeconds = (endTimeMs - startTimeMs) / 1000;
            
            const leftPercent = (startSeconds / 86400) * 100;
            const widthPercent = (durationSeconds / 86400) * 100;
            
            // Check for gap before this segment
            if (index > 0 && segment.has_gap_before) {
                const gapStart = lastEndTime;
                const gapEnd = startSeconds;
                const gapLeft = (gapStart / 86400) * 100;
                const gapWidth = ((gapEnd - gapStart) / 86400) * 100;
                
                if (gapWidth > 0.1) { // Only show gaps larger than ~8.6 seconds
                    segmentsHtml += `
                        <div class="timeline-segment gap-segment" 
                             style="left: ${gapLeft}%; width: ${gapWidth}%;"
                             title="Recording gap: ${playbackService.formatDuration(gapEnd - gapStart)}">
                        </div>
                    `;
                }
            }
            
            // Determine segment type and color
            const segmentType = this.getSegmentType(segment);
            const color = this.segmentColors[segmentType];
            
            // Create segment element
            segmentsHtml += `
                <div class="timeline-segment recording-segment ${segmentType}-segment" 
                     data-segment-index="${index}"
                     data-filename="${segment.filename}"
                     style="left: ${leftPercent}%; width: ${widthPercent}%; background-color: ${color};"
                     title="${this.getSegmentTooltip(segment)}">
                    <div class="segment-content">
                        <div class="segment-time">${this.formatTimeFromMs(startTimeMs)}</div>
                        <div class="segment-duration">${segment.formattedDuration}</div>
                    </div>
                </div>
            `;
            
            lastEndTime = startSeconds + durationSeconds;
        });
        
        segmentsContainer.innerHTML = segmentsHtml;
        
        // Attach click listeners to segments
        segmentsContainer.querySelectorAll('.recording-segment').forEach(segmentEl => {
            segmentEl.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(segmentEl.dataset.segmentIndex);
                this.selectSegment(this.segments[index]);
            });
            
            segmentEl.addEventListener('mouseenter', (e) => {
                const index = parseInt(segmentEl.dataset.segmentIndex);
                this.options.onSegmentHover?.(this.segments[index], 'enter');
            });
            
            segmentEl.addEventListener('mouseleave', (e) => {
                const index = parseInt(segmentEl.dataset.segmentIndex);
                this.options.onSegmentHover?.(this.segments[index], 'leave');
            });
        });
    }
    
    getSegmentType(segment) {
        // Determine segment type based on metadata
        // This can be enhanced with more sophisticated logic
        
        if (segment.has_gap_before) {
            return 'motion'; // Segments after gaps might be motion-triggered
        }
        
        // For now, treat all segments as continuous
        // This can be enhanced when detection data is integrated
        return 'continuous';
    }
    
    getSegmentTooltip(segment) {
        const startTime = this.formatTimeFromMs(new Date(segment.start_time).getTime());
        const endTime = this.formatTimeFromMs(new Date(segment.end_time).getTime());
        
        return [
            `Time: ${startTime} - ${endTime}`,
            `Duration: ${segment.formattedDuration}`,
            `Size: ${segment.formattedSize}`,
            `File: ${segment.filename}`
        ].join('\n');
    }
    
    formatTimeFromMs(timeMs) {
        const date = new Date(timeMs);
        return date.toLocaleTimeString('en-US', { hour12: false });
    }
    
    handleMouseDown(e) {
        if (!this.options.allowSeek) return;
        
        e.preventDefault();
        this.isDragging = true;
        this.updateCursorPosition(e);
    }
    
    handleMouseMove(e) {
        if (!this.isDragging) {
            this.updateHoverIndicator(e);
        }
    }
    
    handleDrag(e) {
        if (!this.isDragging) return;
        
        this.updateCursorPosition(e);
    }
    
    handleMouseUp() {
        if (this.isDragging) {
            this.isDragging = false;
            
            // Trigger seek callback
            this.options.onSeek?.(this.currentTime);
        }
    }
    
    handleMouseLeave() {
        const hoverIndicator = this.container.querySelector('.timeline-hover-indicator');
        if (hoverIndicator) {
            hoverIndicator.style.display = 'none';
        }
    }
    
    updateCursorPosition(e) {
        const track = this.container.querySelector('.timeline-track');
        if (!track) return;
        
        const rect = track.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
        
        // Convert percentage to seconds from start of day
        this.currentTime = (percentage / 100) * this.duration;
        
        // Update cursor position
        const cursor = this.container.querySelector('.timeline-cursor');
        if (cursor) {
            cursor.style.left = percentage + '%';
        }
        
        // Update time display
        this.updateCurrentTimeDisplay();
    }
    
    updateHoverIndicator(e) {
        const track = this.container.querySelector('.timeline-track');
        const hoverIndicator = this.container.querySelector('.timeline-hover-indicator');
        
        if (!track || !hoverIndicator) return;
        
        const rect = track.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
        
        hoverIndicator.style.left = percentage + '%';
        hoverIndicator.style.display = 'block';
        
        // Calculate hover time
        const hoverTime = (percentage / 100) * this.duration;
        const timeStr = this.formatSecondsToTime(hoverTime);
        hoverIndicator.title = timeStr;
    }
    
    seekToTime(seconds) {
        this.currentTime = Math.max(0, Math.min(this.duration, seconds));
        
        const percentage = (this.currentTime / this.duration) * 100;
        const cursor = this.container.querySelector('.timeline-cursor');
        
        if (cursor) {
            cursor.style.left = percentage + '%';
        }
        
        this.updateCurrentTimeDisplay();
        
        // Find segment containing this time
        const segment = this.findSegmentAtTime(this.currentTime);
        if (segment) {
            this.selectSegment(segment);
        }
    }
    
    findSegmentAtTime(seconds) {
        if (!this.segments.length) return null;
        
        // Convert seconds to timestamp
        const dayStart = new Date(this.segments[0].start_time);
        dayStart.setHours(0, 0, 0, 0);
        const targetTime = dayStart.getTime() + (seconds * 1000);
        
        return this.segments.find(segment => {
            const startTime = new Date(segment.start_time).getTime();
            const endTime = new Date(segment.end_time).getTime();
            return targetTime >= startTime && targetTime <= endTime;
        });
    }
    
    selectSegment(segment) {
        this.selectedSegment = segment;
        
        // Update visual selection
        this.container.querySelectorAll('.timeline-segment.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        const segmentEl = this.container.querySelector(`[data-filename="${segment.filename}"]`);
        if (segmentEl) {
            segmentEl.classList.add('selected');
        }
        
        // Update info display
        this.updateSelectedSegmentInfo();
        
        // Trigger callback
        this.options.onSegmentClick?.(segment);
    }
    
    updateCurrentTimeDisplay() {
        const timeDisplay = this.container.querySelector('.current-time');
        if (timeDisplay) {
            timeDisplay.textContent = this.formatSecondsToTime(this.currentTime);
        }
    }
    
    updateSelectedSegmentInfo() {
        const infoDisplay = this.container.querySelector('.selected-segment-info');
        if (!infoDisplay) return;
        
        if (this.selectedSegment) {
            const startTime = this.formatTimeFromMs(new Date(this.selectedSegment.start_time).getTime());
            infoDisplay.textContent = `${this.selectedSegment.filename} (${startTime})`;
        } else {
            infoDisplay.textContent = 'No segment selected';
        }
    }
    
    updateTimelineInfo() {
        // Update any overall timeline statistics
        const totalRecorded = this.segments.reduce((sum, segment) => sum + segment.duration_seconds, 0);
        const coveragePercent = (totalRecorded / this.duration) * 100;
        
        // This could be displayed in a timeline summary area
        console.log(`Timeline coverage: ${coveragePercent.toFixed(1)}% (${playbackService.formatDuration(totalRecorded)} recorded)`);
    }
    
    formatSecondsToTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    handleKeyDown(e) {
        if (!this.options.allowSeek) return;
        
        const step = e.shiftKey ? 60 : 10; // 1 minute or 10 seconds
        
        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.seekToTime(this.currentTime - step);
                this.options.onSeek?.(this.currentTime);
                break;
                
            case 'ArrowRight':
                e.preventDefault();
                this.seekToTime(this.currentTime + step);
                this.options.onSeek?.(this.currentTime);
                break;
        }
    }
    
    zoomIn() {
        // Implement zoom functionality
        console.log('Zoom in functionality not yet implemented');
    }
    
    zoomOut() {
        // Implement zoom functionality
        console.log('Zoom out functionality not yet implemented');
    }
    
    fitToTimeline() {
        // Reset zoom to show full timeline
        console.log('Fit to timeline functionality not yet implemented');
    }
    
    getSelectedSegment() {
        return this.selectedSegment;
    }
    
    getCurrentTime() {
        return this.currentTime;
    }
    
    destroy() {
        // Clean up event listeners
        document.removeEventListener('mousemove', this.handleDrag);
        document.removeEventListener('mouseup', this.handleMouseUp);
        document.removeEventListener('keydown', this.handleKeyDown);
        
        this.container.innerHTML = '';
    }
}

export default TimelineControl;