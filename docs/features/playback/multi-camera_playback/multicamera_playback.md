Multi-Camera Playback System - Implementation Documentation
System Overview
A web-based multi-camera recording playback system with synchronized controls, dynamic layouts, and focus modes.
Architecture
Frontend Structure
/recordings
├── /components
│   ├── CameraSelector.js      # Camera selection grid
│   ├── Calendar.js            # Date picker with recording indicators
│   ├── RecordingsList.js      # Time-based recording segments
│   ├── VideoGrid.js           # Dynamic video panel grid
│   ├── VideoPanel.js          # Individual video player
│   ├── Timeline.js            # 24-hour timeline scrubber
│   ├── PlaybackControls.js    # Transport controls
│   └── AudioMixer.js          # Multi-channel audio control
├── /services
│   ├── RecordingService.js    # API calls for recordings
│   └── CameraService.js       # Camera management
└── RecordingsPage.js          # Main container component
API Endpoints Required
javascript// Camera Management
GET    /api/cameras                    // List all cameras
GET    /api/cameras/:id/status         // Camera health/status

// Recording Data
GET    /api/recordings/calendar        // Get dates with recordings
       ?year=2025&month=8&cameras=1,2,3

GET    /api/recordings/timeline        // Get segments for date
       ?date=2025-08-14&cameras=1,2,3

GET    /api/recordings/segment/:id     // Get segment metadata

// Video Streaming
GET    /api/recordings/stream/:filename // Stream video file
       Headers: Range support for seeking

// Events/Detections
GET    /api/recordings/events          // Get detection events
       ?date=2025-08-14&cameras=1,2,3&type=motion,lpd

// Export
POST   /api/recordings/export          // Create export job
       Body: { cameras: [], startTime, endTime, format }
State Management
javascript// Global Application State
const appState = {
  // Camera Selection
  cameras: [],              // All available cameras
  selectedCameras: [],      // Currently selected camera IDs
  focusedCamera: null,      // ID of focused camera
  
  // Playback State
  viewMode: 'normal',       // 'normal' | 'focus' | 'cinema'
  syncEnabled: true,        // Synchronized playback
  isPlaying: false,         
  playbackRate: 1,          // 0.5, 1, 2, 4, 8
  
  // Timeline State
  currentDate: '2025-08-14',
  currentTime: 0,           // Seconds since midnight
  recordings: [],           // Recording segments
  activeSegment: null,      // Current playing segment
  
  // Audio State
  masterVolume: 70,         // 0-100
  cameraVolumes: {},        // { cameraId: volume }
  mutedCameras: [],         // Array of muted camera IDs
}
Component Specifications
1. CameraSelector Component
javascript// Props
{
  cameras: Array,           // Available cameras
  selectedCameras: Array,   // Selected camera IDs
  onSelectionChange: Function
}

// Features
- Grid layout (2 columns)
- Select/Clear all buttons
- Visual selection state (checkmark)
- Camera status indicators
- Disabled state for offline cameras
2. VideoGrid Component
javascript// Props
{
  selectedCameras: Array,
  focusedCamera: Number,
  viewMode: String,
  recordings: Array,
  onFocusChange: Function,
  onAudioToggle: Function
}

// Grid Layout Logic
function calculateGridLayout(cameraCount, viewMode) {
  if (viewMode === 'focus') {
    return { 
      template: '2fr 1fr', 
      focused: 'span-all-rows' 
    }
  }
  
  switch(cameraCount) {
    case 1: return '1x1'
    case 2: return '1x2'
    case 3: return '2x2 with first spanning 2 cols'
    case 4: return '2x2'
    case 5-6: return '3x2'
    case 7-9: return '3x3'
    default: return 'auto-fit minmax(300px, 1fr)'
  }
}
3. Timeline Component
javascript// Props
{
  recordings: Array,        // Segment data
  currentTime: Number,      // Current position
  duration: Number,         // Total duration (86400 for 24h)
  onSeek: Function,
  events: Array            // Detection events
}

// Segment Rendering
- Each segment = (duration/total) * 100% width
- Active segment highlighted
- Gaps shown as empty space
- Event markers as vertical lines
4. PlaybackControls Component
javascript// Controls Structure
[Skip Back] [Prev Frame] [Play/Pause] [Next Frame] [Skip Forward]
[Time Display] [Skip Empty] [Next Event] [Speed] [Snapshot] [Fullscreen]

// Keyboard Bindings
{
  'Space': togglePlayPause,
  'ArrowLeft': skipBack10s,
  'ArrowRight': skipForward10s,
  'Shift+ArrowLeft': previousFrame,
  'Shift+ArrowRight': nextFrame,
  'F': toggleFocusMode,
  'Shift+F': fullscreenFocused,
  '1-9': focusCamera(n),
  'M': muteFocused,
  'A': toggleAudioMixer,
  'S': takeSnapshot,
  'Escape': exitFullscreen
}
Video Synchronization Logic
javascriptclass VideoSyncManager {
  constructor() {
    this.videos = new Map() // cameraId -> video element
    this.syncEnabled = true
    this.masterTime = 0
  }
  
  play() {
    if (this.syncEnabled) {
      // Start all videos together
      this.videos.forEach(video => {
        video.currentTime = this.masterTime
        video.play()
      })
    }
  }
  
  seek(time) {
    this.masterTime = time
    if (this.syncEnabled) {
      this.videos.forEach(video => {
        video.currentTime = time
      })
    }
  }
  
  handleVideoTimeUpdate(cameraId, time) {
    if (this.syncEnabled && this.focusedCamera === cameraId) {
      // Focused camera drives the sync
      this.masterTime = time
      this.videos.forEach((video, id) => {
        if (id !== cameraId) {
          video.currentTime = time
        }
      })
    }
  }
}
Audio Management
javascriptclass AudioManager {
  constructor() {
    this.masterVolume = 0.7
    this.cameraVolumes = new Map()
    this.focusedCamera = null
  }
  
  setFocusedCamera(cameraId) {
    this.focusedCamera = cameraId
    this.updateVolumes()
  }
  
  updateVolumes() {
    this.videos.forEach((video, cameraId) => {
      const baseVolume = this.cameraVolumes.get(cameraId) || 1
      const masterAdjusted = baseVolume * this.masterVolume
      
      if (this.focusMode && cameraId === this.focusedCamera) {
        video.volume = masterAdjusted // Full volume
      } else if (this.focusMode) {
        video.volume = masterAdjusted * 0.2 // 20% for non-focused
      } else {
        video.volume = masterAdjusted
      }
    })
  }
}
Performance Optimizations
javascript// 1. Lazy Loading
- Only load video streams for visible cameras
- Preload next segment 10 seconds before end
- Unload hidden videos in focus mode

// 2. Quality Adaptation
function getVideoQuality(gridSize) {
  if (gridSize === 1) return 'high'    // 1080p
  if (gridSize <= 4) return 'medium'   // 720p
  return 'low'                          // 480p
}

// 3. Debounced Updates
- Timeline seeking: 100ms debounce
- Grid resize: 300ms debounce
- Volume changes: 50ms debounce

// 4. Virtual Scrolling
- Recording list: Only render visible items
- Calendar: Lazy render on month change
Error Handling
javascript// Connection Errors
- Retry video loading 3 times with exponential backoff
- Show "Camera Offline" placeholder
- Disable controls for offline cameras

// Playback Errors
- Fallback to next available segment
- Show error message with retry option
- Log errors to monitoring service

// Missing Data
- Show "No recordings" for empty periods
- Gray out dates without recordings
- Disable timeline for no data
CSS Architecture
css/* Component Structure */
.recordings-page
  .sidebar
    .camera-selector
    .calendar-widget  
    .recordings-list
  .main-content
    .control-bar
    .video-grid-container
      .video-panel (dynamic count)
    .timeline-container
    .playback-controls

/* Responsive Breakpoints */
- Desktop: > 1024px (full layout)
- Tablet: 768-1024px (stacked sidebar)
- Mobile: < 768px (vertical layout)

/* CSS Variables for Theming */
--primary-color: #4361ee
--video-bg: #000000
--panel-bg: #ffffff
--border-color: #dee2e6
Testing Requirements
javascript// Unit Tests
- Grid layout calculation
- Time formatting functions
- Sync logic
- Keyboard shortcuts

// Integration Tests
- Camera selection → Grid update
- Timeline seek → Video sync
- Focus mode → Audio adjustment
- Export functionality

// E2E Tests
- Full playback workflow
- Multi-camera sync
- Error recovery
- Performance under load
Deployment Considerations
yaml# Environment Variables
API_BASE_URL: https://api.example.com
VIDEO_BUFFER_SIZE: 10MB
MAX_CONCURRENT_STREAMS: 9
DEFAULT_VIDEO_QUALITY: medium

# Browser Requirements
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

# Performance Targets
- Initial load: < 2s
- Camera switch: < 500ms
- Seek response: < 200ms
- 60fps UI animations
