# 📹 Unified Camera Card Architecture

**Date**: 2025-07-25  
**Status**: 🔄 **IN PROGRESS**  
**Goal**: Consistent camera streaming across Dashboard and Cameras pages

## 🎯 Problem Statement

Currently we have:
- **Dashboard**: Placeholder camera feeds with mock data
- **Cameras Page**: Camera cards with separate streaming logic
- **Inconsistent UX**: Different behaviors and controls between pages
- **Duplicated Code**: Similar functionality implemented twice

## 🚀 Proposed Solution

### Unified Camera Card Component
Create a single, reusable `CameraCard` component that adapts based on context:

```javascript
// Single component, multiple use cases
<CameraCard 
  camera={camera}
  variant="dashboard"     // or "gallery" 
  size="compact"          // or "detailed"
  autoStream={true}       // continuous streaming
  showControls={true}     // stream controls visible
  showDetails={false}     // camera info visibility
/>
```

## 🏗️ Component Architecture

### Base CameraCard Component
```
CameraCard/
├── CameraCard.js              # Main component
├── CameraVideo.js             # Video streaming logic
├── CameraControls.js          # Stream controls
├── CameraStatus.js            # Status indicators
├── CameraInfo.js              # Camera details
└── CameraCard.css             # Unified styles
```

### Variant Configurations

#### Dashboard Variant (Compact)
- **Size**: Smaller footprint for grid layout
- **Focus**: Live video stream + basic controls
- **Auto-stream**: Starts streaming immediately when online
- **Info**: Minimal (camera name, status indicator)

#### Cameras Page Variant (Detailed)
- **Size**: Full card with comprehensive details
- **Focus**: Camera management + streaming capability
- **Controls**: Full stream controls + configuration
- **Info**: Complete (IP, resolution, health, location)

## 🔧 Technical Implementation

### 1. Continuous Streaming Strategy

Instead of manual start/stop, implement auto-streaming:

```javascript
class CameraCard {
    constructor(camera, options) {
        this.camera = camera;
        this.autoStream = options.autoStream ?? true;
        this.streamManager = new CameraStreamManager(camera.id);
    }

    async componentDidMount() {
        if (this.autoStream && this.camera.status === 'online') {
            await this.startContinuousStream();
        }
        
        // Monitor camera status changes
        this.statusWatcher = new CameraStatusWatcher(this.camera.id);
        this.statusWatcher.on('statusChange', this.handleStatusChange.bind(this));
    }

    async startContinuousStream() {
        try {
            await this.streamManager.startStream({
                quality: 'medium',
                autoReconnect: true,
                maxRetries: 5
            });
            this.setState({ streaming: true });
        } catch (error) {
            console.error('Stream start failed:', error);
            this.setState({ streamError: error.message });
        }
    }

    handleStatusChange(newStatus) {
        if (newStatus === 'online' && this.autoStream) {
            this.startContinuousStream();
        } else if (newStatus === 'offline') {
            this.streamManager.stopStream();
            this.setState({ streaming: false });
        }
    }
}
```

### 2. Stream State Management

Centralized stream state across components:

```javascript
// Global stream state manager
class GlobalStreamManager {
    constructor() {
        this.activeStreams = new Map();
        this.streamStates = new Map();
    }

    async ensureStream(cameraId) {
        if (!this.activeStreams.has(cameraId)) {
            const stream = new CameraStream(cameraId);
            this.activeStreams.set(cameraId, stream);
            await stream.connect();
        }
        return this.activeStreams.get(cameraId);
    }

    getStreamUrl(cameraId) {
        return `/stream/video/${cameraId}?t=${Date.now()}`;
    }

    isStreaming(cameraId) {
        return this.streamStates.get(cameraId) === 'active';
    }
}

// Global instance
window.streamManager = new GlobalStreamManager();
```

## 📱 Responsive Design

### Dashboard Grid Layout
```css
.dashboard-camera-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
    padding: 20px;
}

.camera-card--dashboard {
    aspect-ratio: 16/9;
    height: 200px;
}
```

### Cameras Page Layout
```css
.cameras-gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
    padding: 20px;
}

.camera-card--gallery {
    height: auto;
    min-height: 400px;
}
```

## 🔄 Data Flow

### Initialization Flow
```
Page Load
    ↓
Load Cameras from API
    ↓
Render CameraCard Components
    ↓
Auto-start Streams (online cameras)
    ↓
Poll Status Updates (30s interval)
```

### Stream Management Flow
```
Camera Online
    ↓
Auto-start Stream
    ↓
Display Live Video
    ↓
Monitor Connection Health
    ↓
Auto-reconnect on Failure
```

## 📊 Benefits

### For Users
- **Consistent Experience**: Same controls and behavior everywhere
- **Always Live**: No manual stream starting required
- **Instant Feedback**: Real-time status and health indicators
- **Context Aware**: Appropriate level of detail per page

### For Developers
- **Code Reuse**: Single component, multiple contexts
- **Easier Maintenance**: One place to fix bugs or add features
- **Performance**: Shared stream management and connection pooling
- **Testing**: Single component to test comprehensively

## 🚦 Implementation Plan

### Phase 1: Component Creation (2 days)
1. Create base CameraCard component
2. Implement variant system (dashboard/gallery)
3. Add continuous streaming logic
4. Basic styling and responsive design

### Phase 2: Dashboard Integration (1 day)
1. Replace current dashboard camera feeds
2. Implement grid layout controls
3. Add auto-streaming functionality
4. Test multi-camera performance

### Phase 3: Cameras Page Integration (1 day)
1. Update Cameras page to use unified component
2. Maintain existing functionality (modals, actions)
3. Enhance with continuous streaming
4. Test full feature set

### Phase 4: Polish & Optimization (1 day)
1. Performance optimization
2. Error handling improvements
3. User experience refinements
4. Cross-browser testing

## ✅ Success Criteria

- [ ] Single CameraCard component works in both contexts
- [ ] Auto-streaming starts immediately for online cameras
- [ ] Consistent controls and behavior across pages
- [ ] No performance degradation with multiple streams
- [ ] Graceful error handling and recovery
- [ ] Mobile responsive design
- [ ] Stream state persists across page navigation

This unified approach will provide a consistent, professional streaming experience while reducing code duplication and maintenance overhead.