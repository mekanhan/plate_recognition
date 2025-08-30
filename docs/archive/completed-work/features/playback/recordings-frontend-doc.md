# Recordings Page Frontend Implementation Guide

## Overview
This document provides implementation guidelines for the Recordings page frontend component. The page displays recorded video segments from security cameras with playback controls, calendar navigation, and filtering capabilities.

## Component Structure

```
recordings/
├── RecordingsPage.js         # Main page component
├── components/
│   ├── VideoPlaybackPlayer.js # Video player with controls
│   ├── RecordingCalendar.js  # Calendar widget
│   ├── TimelineControl.js    # Timeline scrubber
│   ├── CameraList.js         # Camera selection panel
│   └── EventList.js          # Event/segment list
├── services/
│   └── PlaybackService.js    # API communication
└── styles/
    └── recordings.css        # Page-specific styles
```

## Main Component: RecordingsPage.js

### State Management
```javascript
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
        
        // Filter state
        this.filters = {
            camera: 'all',
            dateRange: 'today',
            customStart: '',
            customEnd: ''
        };
    }
}
```

### Component Lifecycle
```javascript
init() {
    this.render();
    this.attachEventListeners();
    this.loadInitialData();
}

async loadInitialData() {
    try {
        // Load cameras
        await this.loadCameras();
        
        // Load storage stats
        await this.loadStorageStats();
        
        // Load today's recordings for first camera
        if (this.cameras.length > 0) {
            this.selectedCamera = this.cameras[0].id;
            await this.loadRecordingsForDate(new Date());
        }
    } catch (error) {
        this.showError('Failed to load recordings');
    }
}
```

## Key Components

### 1. VideoPlaybackPlayer Component

```javascript
class VideoPlaybackPlayer {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            autoplay: false,
            controls: true,
            timeline: true,
            ...options
        };
        
        // Player state
        this.video = null;
        this.currentSegment = null;
        this.isPlaying = false;
        this.currentTime = 0;
        this.duration = 0;
        this.playbackRate = 1.0;
    }
    
    // Core methods
    async loadSegment(segment) {
        // Load video segment for playback
    }
    
    async loadTimeRange(cameraId, startTime, endTime) {
        // Load all segments in time range
    }
    
    play() { /* Play video */ }
    pause() { /* Pause video */ }
    seek(time) { /* Seek to time */ }
    setPlaybackRate(rate) { /* Set speed */ }
}
```

### 2. RecordingCalendar Component

```javascript
class RecordingCalendar {
    constructor(container, options = {}) {
        this.container = container;
        this.currentMonth = new Date();
        this.recordingDays = new Map(); // day -> hasRecordings
        
        this.options = {
            onDateSelect: null,
            onMonthChange: null,
            ...options
        };
    }
    
    async loadMonth(cameraId, year, month) {
        // Fetch calendar data from API
        const calendarData = await playbackService.getCalendarData(
            cameraId, year, month
        );
        
        // Update recording indicators
        this.updateRecordingDays(calendarData.days);
    }
    
    render() {
        // Render calendar with recording indicators
    }
}
```

### 3. TimelineControl Component

```javascript
class TimelineControl {
    constructor(container, options = {}) {
        this.container = container;
        this.segments = [];
        this.currentTime = 0;
        this.duration = 86400; // 24 hours in seconds
        
        this.options = {
            onSeek: null,
            onSegmentClick: null,
            ...options
        };
    }
    
    loadSegments(segments) {
        this.segments = segments;
        this.renderTimeline();
    }
    
    renderTimeline() {
        // Render segments with color coding
        // Green: continuous recording
        // Orange: motion detection
        // Red: alarm events
        // Gray: gaps/no recording
    }
    
    seekToTime(seconds) {
        // Update cursor position and trigger callback
    }
}
```

### 4. CameraList Component

```javascript
class CameraList {
    constructor(container, options = {}) {
        this.container = container;
        this.cameras = [];
        this.selectedCameraId = null;
        
        this.options = {
            onCameraSelect: null,
            showStatus: true,
            searchable: true,
            ...options
        };
    }
    
    loadCameras(cameras) {
        this.cameras = cameras;
        this.render();
    }
    
    selectCamera(cameraId) {
        this.selectedCameraId = cameraId;
        this.updateSelection();
        this.options.onCameraSelect?.(cameraId);
    }
}
```

## PlaybackService API Integration

```javascript
class PlaybackService {
    constructor() {
        this.baseUrl = config.RECORDING_API_URL; // http://localhost:8002
    }
    
    // Calendar data
    async getCalendarData(cameraId, year, month) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/recordings/cameras/${cameraId}/calendar?year=${year}&month=${month}`
        );
        return response.json();
    }
    
    // Timeline segments
    async getTimelineSegments(cameraId, date, startHour, endHour) {
        const params = new URLSearchParams({
            date: date,
            ...(startHour && { start_hour: startHour }),
            ...(endHour && { end_hour: endHour })
        });
        
        const response = await fetch(
            `${this.baseUrl}/api/v1/recordings/cameras/${cameraId}/timeline?${params}`
        );
        return response.json();
    }
    
    // Video streaming URL
    getStreamUrl(segmentFilename) {
        return `${this.baseUrl}/api/v1/recordings/stream/${segmentFilename}`;
    }
    
    // Recording details
    async getRecordingDetails(cameraId, date) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/recordings/cameras/${cameraId}/details?date=${date}`
        );
        return response.json();
    }
    
    // Search recordings
    async searchRecordings(cameraId, searchParams) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/recordings/cameras/${cameraId}/search`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(searchParams)
            }
        );
        return response.json();
    }
    
    // Storage report
    async getStorageReport() {
        const response = await fetch(`${this.baseUrl}/api/v1/storage/report`);
        return response.json();
    }
}
```

## Event Handling

### Camera Selection
```javascript
handleCameraSelect(cameraId) {
    this.selectedCamera = cameraId;
    
    // Update UI
    this.updateCameraDisplay();
    
    // Load recordings for selected date
    this.loadRecordingsForDate(this.selectedDate);
}
```

### Date Selection
```javascript
handleDateSelect(date) {
    this.selectedDate = date;
    
    // Load timeline for selected date
    this.loadTimelineSegments(this.selectedCamera, date);
    
    // Update calendar highlighting
    this.calendar.setSelectedDate(date);
}
```

### Timeline Interaction
```javascript
handleTimelineSeek(timeInSeconds) {
    // Find segment containing this time
    const segment = this.findSegmentAtTime(timeInSeconds);
    
    if (segment) {
        // Calculate offset within segment
        const segmentOffset = timeInSeconds - segment.startTimeSeconds;
        
        // Load and seek video
        this.videoPlayer.loadSegment(segment);
        this.videoPlayer.seek(segmentOffset);
    }
}
```

### Playback Controls
```javascript
handlePlaybackControl(action) {
    switch(action) {
        case 'play':
            this.videoPlayer.play();
            break;
        case 'pause':
            this.videoPlayer.pause();
            break;
        case 'previous':
            this.loadPreviousSegment();
            break;
        case 'next':
            this.loadNextSegment();
            break;
        case 'speed':
            this.videoPlayer.setPlaybackRate(this.selectedSpeed);
            break;
    }
}
```

## Data Flow

### Loading Recordings for a Date
```javascript
async loadRecordingsForDate(date) {
    this.showLoading(true);
    
    try {
        // Get timeline segments
        const dateStr = this.formatDate(date);
        const timeline = await playbackService.getTimelineSegments(
            this.selectedCamera,
            dateStr
        );
        
        // Update timeline display
        this.timelineControl.loadSegments(timeline.segments);
        
        // Update recording info
        this.updateRecordingInfo({
            duration: timeline.total_duration,
            size: timeline.total_size,
            coverage: timeline.coverage_percentage
        });
        
        // Load first segment if available
        if (timeline.segments.length > 0) {
            await this.videoPlayer.loadSegment(timeline.segments[0]);
        }
        
    } catch (error) {
        this.showError('Failed to load recordings');
    } finally {
        this.showLoading(false);
    }
}
```

### Continuous Playback
```javascript
async handleSegmentEnd() {
    // Get next segment
    const currentIndex = this.segments.findIndex(
        s => s.filename === this.currentSegment.filename
    );
    
    if (currentIndex < this.segments.length - 1) {
        const nextSegment = this.segments[currentIndex + 1];
        
        // Check for gap
        if (nextSegment.has_gap_before) {
            // Show gap indicator
            this.showGapIndicator(nextSegment.gap_duration);
        }
        
        // Load next segment
        await this.videoPlayer.loadSegment(nextSegment);
        this.videoPlayer.play();
    } else {
        // End of recordings
        this.videoPlayer.pause();
        this.showEndOfRecordings();
    }
}
```

## UI State Management

### Loading States
```javascript
showLoading(show) {
    this.isLoading = show;
    
    // Update UI elements
    document.querySelector('.loading-overlay').style.display = 
        show ? 'flex' : 'none';
    
    // Disable controls during loading
    this.setControlsEnabled(!show);
}
```

### Error Handling
```javascript
showError(message, duration = 5000) {
    const errorElement = document.querySelector('.error-message');
    errorElement.textContent = message;
    errorElement.classList.add('show');
    
    setTimeout(() => {
        errorElement.classList.remove('show');
    }, duration);
}
```

### Storage Warning
```javascript
checkStorageStatus(storageReport) {
    const percentageUsed = storageReport.percentage_used;
    
    if (percentageUsed > 90) {
        this.showStorageWarning('critical');
    } else if (percentageUsed > 80) {
        this.showStorageWarning('warning');
    }
    
    // Update storage display
    this.updateStorageDisplay(storageReport);
}
```

## Performance Optimizations

### 1. Lazy Loading
```javascript
// Load segments on demand
async loadVisibleSegments() {
    const visibleTimeRange = this.getVisibleTimeRange();
    
    // Only load segments in visible range
    const segments = await playbackService.getTimelineSegments(
        this.selectedCamera,
        this.selectedDate,
        visibleTimeRange.startHour,
        visibleTimeRange.endHour
    );
    
    this.updateTimelineSegments(segments);
}
```

### 2. Thumbnail Caching
```javascript
class ThumbnailCache {
    constructor(maxSize = 100) {
        this.cache = new Map();
        this.maxSize = maxSize;
    }
    
    async getThumbnail(segmentId) {
        if (this.cache.has(segmentId)) {
            return this.cache.get(segmentId);
        }
        
        const thumbnail = await this.loadThumbnail(segmentId);
        this.addToCache(segmentId, thumbnail);
        return thumbnail;
    }
}
```

### 3. Debounced Timeline Updates
```javascript
// Debounce timeline scrubbing
handleTimelineScrub = debounce((position) => {
    this.seekToPosition(position);
}, 100);
```

## Responsive Design

### Mobile Adaptations
```javascript
adaptForMobile() {
    if (window.innerWidth < 768) {
        // Stack layout vertically
        this.container.classList.add('mobile-layout');
        
        // Hide camera list by default
        this.cameraList.collapse();
        
        // Simplify timeline
        this.timelineControl.setCompactMode(true);
    }
}
```

### Fullscreen Support
```javascript
enterFullscreen() {
    const videoContainer = this.videoPlayer.container;
    
    if (videoContainer.requestFullscreen) {
        videoContainer.requestFullscreen();
    }
    
    // Add fullscreen class for styling
    videoContainer.classList.add('fullscreen');
    
    // Show minimal controls
    this.videoPlayer.setMinimalControls(true);
}
```

## Testing Checklist

- [ ] Camera selection updates video and timeline
- [ ] Calendar shows correct recording indicators
- [ ] Date selection loads appropriate recordings
- [ ] Timeline scrubbing seeks video correctly
- [ ] Playback controls function properly
- [ ] Speed controls adjust playback rate
- [ ] Continuous playback handles segment transitions
- [ ] Gap indicators show for missing recordings
- [ ] Storage warnings appear at thresholds
- [ ] Mobile layout adapts responsively
- [ ] Fullscreen mode works correctly
- [ ] Error states display appropriately
- [ ] Loading states prevent duplicate requests
- [ ] Keyboard shortcuts function
- [ ] Export functionality works

## Browser Compatibility

### Required Features
- HTML5 Video element
- Fetch API
- CSS Grid/Flexbox
- ES6+ JavaScript

### Tested Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Accessibility

### Keyboard Navigation
- Tab: Navigate between controls
- Space: Play/pause
- Arrow keys: Seek forward/backward
- Shift+Arrow: Fast seek
- F: Toggle fullscreen
- M: Toggle mute

### ARIA Labels
```javascript
// Add appropriate ARIA labels
this.playButton.setAttribute('aria-label', 'Play video');
this.timeline.setAttribute('role', 'slider');
this.timeline.setAttribute('aria-label', 'Video timeline');
this.calendar.setAttribute('role', 'grid');
```

### Screen Reader Support
- Announce state changes
- Provide alternative text for visual indicators
- Ensure focus management

## Integration Points

### With Dashboard
- Link from dashboard timeline widget
- Share camera selection state
- Consistent date formatting

### With Cameras Page
- Use same camera status indicators
- Share camera configuration
- Consistent styling

### With Detection Events
- Timeline markers for detection events
- Jump to detection timestamps
- Filter by event types (future enhancement)