# Global vs Camera-Specific Settings Analysis

## Settings Categorization

### 🌐 Global Settings (Apply to All Cameras)

#### 1. **Storage & Recording**
- **Base Recording Path**: `/recordings/` (cameras create subfolders)
- **Retention Policy**: Days to keep recordings (e.g., 30 days)
- **Storage Quota**: Total storage limit for all cameras
- **Auto-Delete When Full**: System-wide policy
- **File Format**: MP4/AVI/MKV (standardized)
- **Segment Duration**: 10-minute segments for all

#### 2. **System Policies**
- **Audit Logging**: Enable/disable for all cameras
- **Watermark Settings**: Timestamp format, position
- **Debug Logging**: System-wide debug mode
- **Compression Settings**: H.264/H.265 preference
- **Backup Schedule**: When to backup configs

#### 3. **Alert & Notification Defaults**
- **Email Server Settings**: SMTP configuration
- **Default Recipients**: Security team emails
- **Alert Cooldown Period**: Prevent spam (e.g., 5 min)
- **Include Snapshot in Alerts**: Default on/off
- **Alert Schedule**: Business hours vs 24/7

#### 4. **Network Defaults**
- **Connection Timeout**: Default 10 seconds
- **Retry Attempts**: Default 3 attempts
- **Keep-Alive Interval**: Default 30 seconds
- **RTSP/HTTP Preference**: Protocol preference

#### 5. **Recording Defaults**
- **Pre-Record Buffer**: Default 5 seconds
- **Post-Record Buffer**: Default 10 seconds
- **Default Recording Mode**: Continuous/Motion/Schedule
- **Motion Sensitivity Default**: 75%

#### 6. **Performance Settings**
- **Max Concurrent Streams**: Limit for bandwidth
- **Transcoding Settings**: When to use sub-stream
- **Cache Duration**: How long to cache snapshots
- **Database Cleanup Schedule**: When to purge old data

### 📹 Camera-Specific Settings (Per Camera)

#### 1. **Identity & Location**
- **Camera Name**: "Main Entrance"
- **Physical Location**: "Building A - Front Door"
- **Priority**: High/Medium/Low
- **Tags**: entrance, outdoor, critical
- **GPS Coordinates**: Lat/Long

#### 2. **Network Configuration**
- **IP Address**: 10.0.0.181
- **Port**: 554
- **Username/Password**: Credentials
- **Stream URLs**: Main/Sub/Snapshot paths
- **Connection Type**: RTSP/HTTP/ONVIF

#### 3. **Video Settings**
- **Resolution**: 4K/1080p/720p (camera capability)
- **Frame Rate**: Based on camera model
- **Bitrate**: Based on resolution/bandwidth
- **Day/Night Mode**: Auto/Manual
- **Image Settings**: Brightness, Contrast, Saturation

#### 4. **Motion Detection**
- **Enable/Disable**: Per camera choice
- **Sensitivity Override**: If different from global
- **Detection Zones**: Specific area masks
- **Exclude Zones**: Areas to ignore

#### 5. **AI Analytics**
- **People Detection**: On/Off per camera
- **Vehicle Detection**: Parking lot only
- **Face Detection**: Entrance cameras only
- **License Plate Recognition**: Gate cameras
- **Line Crossing**: Specific boundaries

#### 6. **PTZ Settings** (if applicable)
- **Preset Positions**: Camera-specific views
- **Patrol Routes**: Custom patterns
- **Home Position**: Default view
- **Speed Settings**: Pan/Tilt/Zoom speeds

#### 7. **Privacy & Security**
- **Privacy Masks**: Specific areas (windows, etc.)
- **Access Permissions**: Who can view/control
- **Stream Encryption**: High-security cameras only

#### 8. **Recording Overrides**
- **Recording Mode Override**: Different from global
- **Custom Schedule**: Camera-specific hours
- **Storage Location Override**: Special backup path

## Implementation Design

### Global Settings Management

```javascript
// Global settings structure
const globalSettings = {
  storage: {
    basePath: "/recordings",
    retentionDays: 30,
    maxStorageGB: 10000,
    autoDelete: true,
    fileFormat: "mp4",
    segmentMinutes: 10
  },
  defaults: {
    recording: {
      mode: "continuous",
      preBuffer: 5,
      postBuffer: 10,
      motionSensitivity: 75
    },
    network: {
      timeout: 10,
      retryAttempts: 3,
      keepAlive: 30,
      preferredProtocol: "rtsp"
    },
    video: {
      preferredCodec: "h264",
      maxBitrate: 8000,
      keyframeInterval: 2
    }
  },
  alerts: {
    smtp: {
      server: "smtp.company.com",
      port: 587,
      secure: true
    },
    defaultRecipients: ["security@company.com"],
    cooldownMinutes: 5,
    includeSnapshot: true,
    schedule: "24/7" // or "business_hours"
  },
  system: {
    enableAudit: true,
    debugMode: false,
    maxConcurrentStreams: 20,
    snapshotCacheTTL: 300
  }
};
```

### Camera Settings with Global Inheritance

```javascript
// Camera-specific settings with override capability
const cameraSettings = {
  id: "camera_001",
  general: {
    name: "Main Entrance",
    location: "Building A - Front Door",
    priority: "high",
    tags: ["entrance", "outdoor", "critical"]
  },
  network: {
    ip: "10.0.0.181",
    port: 554,
    username: "admin",
    password: "encrypted_password",
    streamUrls: {
      main: "/h264Preview_01_main",
      sub: "/h264Preview_01_sub"
    }
  },
  recording: {
    // Inherits from global unless overridden
    mode: "inherit", // or specific: "motion"
    customSchedule: null, // or schedule object
    preBuffer: "inherit", // or specific: 10
    postBuffer: "inherit" // or specific: 20
  },
  video: {
    resolution: "3840x2160", // Camera-specific capability
    fps: 25,
    bitrate: 8000,
    dayNightMode: "auto"
  },
  // ... other camera-specific settings
};
```

## UI Design for Global Settings

### Settings Modal Enhancement

```
┌─────────────────────────────────────┐
│ Camera Settings                     │
├─────────────────────────────────────┤
│ 🌐 Global | 📹 This Camera         │
├─────────────────────────────────────┤
│ [Global Settings Tab]               │
│                                     │
│ Storage & Recording                 │
│ ├─ Base Path: /recordings          │
│ ├─ Retention: [30] days            │
│ └─ Apply to all cameras            │
│                                     │
│ Default Recording Settings          │
│ ├─ Mode: [Continuous ▼]            │
│ ├─ Pre-buffer: [5] seconds         │
│ └─ Post-buffer: [10] seconds       │
│                                     │
│ [Save Global Settings]              │
└─────────────────────────────────────┘
```

### Inheritance Indicators

```
┌─────────────────────────────────────┐
│ Recording Settings                  │
├─────────────────────────────────────┤
│ Mode: [Continuous ▼] 🌐 (global)    │
│       [✓] Override global setting   │
│                                     │
│ Pre-buffer: [5] seconds 🌐          │
│       [✓] Override: [___] seconds   │
└─────────────────────────────────────┘
```

## Benefits of This Approach

### 1. **Simplified Management**
- Change retention policy once, applies everywhere
- Consistent recording quality across system
- Easier compliance with regulations

### 2. **Flexible Overrides**
- High-security cameras can have longer retention
- Outdoor cameras can have different motion settings
- Critical cameras can have higher quality

### 3. **Storage Optimization**
- Centralized path management
- Easier to implement quotas
- Simplified backup strategies

### 4. **Better UX**
- Less repetitive configuration
- Clear inheritance model
- Bulk operations support

## Implementation Strategy

### 1. **Database Schema Update**

```sql
-- Global settings table
CREATE TABLE global_settings (
    category VARCHAR(50) PRIMARY KEY,
    settings JSON NOT NULL,
    updated_at TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Camera settings with inheritance
ALTER TABLE camera_settings 
ADD COLUMN use_global_defaults BOOLEAN DEFAULT TRUE;
ADD COLUMN overrides JSON;
```

### 2. **API Endpoints**

```python
# Global settings management
GET    /api/v2/settings/global
PUT    /api/v2/settings/global/{category}
POST   /api/v2/settings/global/apply-all

# Camera with inheritance
GET    /api/v2/cameras/{id}/effective-settings
PUT    /api/v2/cameras/{id}/override-setting
DELETE /api/v2/cameras/{id}/override-setting/{key}
```

### 3. **Settings Resolution Logic**

```javascript
function getEffectiveSettings(camera, globalSettings) {
  const effective = { ...globalSettings };
  
  // Apply camera-specific overrides
  if (camera.overrides) {
    Object.keys(camera.overrides).forEach(key => {
      if (camera.overrides[key] !== 'inherit') {
        _.set(effective, key, camera.overrides[key]);
      }
    });
  }
  
  // Always use camera-specific identity/network
  effective.identity = camera.identity;
  effective.network = camera.network;
  
  return effective;
}
```

## Recommended Global Defaults

Based on typical deployments:

```javascript
const recommendedGlobalDefaults = {
  recording: {
    basePath: "/var/recordings",
    retentionDays: 30,
    segmentMinutes: 10,
    format: "mp4",
    mode: "continuous"
  },
  video: {
    preferredCodec: "h264", // Better compatibility
    keyframeInterval: 2,
    qualityPreset: "balanced" // vs "quality" or "performance"
  },
  motion: {
    sensitivity: 75,
    threshold: 10,
    cooldown: 5
  },
  alerts: {
    enabled: true,
    includeSnapshot: true,
    maxPerHour: 10, // Prevent spam
    quietHours: null // or "22:00-06:00"
  },
  maintenance: {
    autoUpdate: false, // Require manual firmware updates
    restartSchedule: "sunday-03:00",
    logRetentionDays: 7
  }
};
```

This approach significantly reduces configuration overhead while maintaining flexibility for special cases. The inheritance model with clear override capabilities provides the best of both worlds.