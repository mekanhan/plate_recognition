# Camera Information Standards

## Required Fields and Default Values

Every camera interface must display exactly these 8 fields, no more, no less:

### 1. **Location**
- **Valid Value Format**: Text string (e.g., "Entrance", "Main Gate", "Parking Lot")
- **Default Value**: `"Unknown"`
- **When to Use Default**: 
  - No location configured
  - Location data unavailable
  - Empty/null location field

### 2. **Connection**
- **Valid Value Format**: `[Protocol] ([IP Address])`
  - Example: `RTSP (10.0.0.181)`
  - Example: `HTTP (192.168.1.100)`
- **Default Value**: `"Unknown"`
- **When to Use Default**:
  - No connection established
  - Protocol/IP not detected
  - Connection info unavailable

### 3. **Recording Status**
- **Valid Value Formats**:
  - `▶️ Recording` (when actively recording)
  - `⏸️ Paused` (when recording is paused)
  - `⏹️ Stopped` (when recording is stopped)
- **Default Value**: `"Not Set"`
- **When to Use Default**:
  - Recording feature not configured
  - Status cannot be determined
  - Initial setup state

### 4. **Connection Status**
- **Valid Value Formats**:
  - `✅ Connected` (active connection)
  - `❌ Disconnected` (no connection)
  - `⚠️ Reconnecting` (attempting to reconnect)
  - `🔄 Connecting` (initial connection attempt)
- **Default Value**: `"Unknown"`
- **When to Use Default**:
  - Connection state cannot be determined
  - Service unavailable to check status

### 5. **FFmpeg PID**
- **Valid Value Format**: Numeric process ID (e.g., `439961`)
- **Default Value**: `"None"`
- **When to Use Default**:
  - FFmpeg not running
  - Process not started
  - PID cannot be retrieved

### 6. **Segments Created**
- **Valid Value Format**: `[Number] (last: [Timestamp])`
  - Example: `47 (last: 11:47:30 PM)`
  - Example: `152 (last: 2:30:45 AM)`
- **Default Value**: `"None"`
- **Special Cases**:
  - If count > 0 but no timestamp: `"12 (last: Unknown)"`
  - If recording just started: `"0"`

### 7. **Storage Used**
- **Valid Value Formats**:
  - `0 B` (zero bytes)
  - `1.5 KB` (kilobytes)
  - `250 MB` (megabytes)
  - `2.3 GB` (gigabytes)
  - `1.2 TB` (terabytes)
- **Default Value**: `"0 B"`
- **When to Use Default**:
  - No recordings exist
  - Storage calculation fails
  - New camera setup

### 8. **Recording Uptime**
- **Valid Value Formats**:
  - `29m` (minutes only)
  - `1h 15m` (hours and minutes)
  - `2d 3h 45m` (days, hours, and minutes)
  - `0m` (just started)
- **Default Value**: `"None"`
- **When to Use Default**:
  - Recording never started
  - Uptime cannot be calculated
  - Service not initialized

## Implementation Rules

### Formatting Requirements:
1. **Label Formatting**: Always use exact label names as specified above
2. **Colon Separator**: Always include colon after label (e.g., "Location:")
3. **Value Alignment**: Values should be right-aligned or consistently spaced
4. **Case Sensitivity**: 
   - Labels: Use title case as shown
   - Default values: Use exact casing as specified ("Unknown", "None", "Not Set")

### Value Handling Logic:
```javascript
// Example implementation pattern
function getFieldValue(fieldName, actualValue) {
  const defaults = {
    'location': 'Unknown',
    'connection': 'Unknown',
    'recordingStatus': 'Not Set',
    'connectionStatus': 'Unknown',
    'ffmpegPid': 'None',
    'segmentsCreated': 'None',
    'storageUsed': '0 B',
    'recordingUptime': 'None'
  };
  
  // Check various "empty" conditions
  if (actualValue === null || 
      actualValue === undefined || 
      actualValue === '' || 
      actualValue === 'N/A' ||
      actualValue === -1 ||
      (typeof actualValue === 'string' && actualValue.trim() === '')) {
    return defaults[fieldName];
  }
  
  return actualValue;
}
```

### Special Considerations:

1. **Never Show**:
   - Error messages in place of values
   - "Loading..." as a permanent value
   - Technical error codes
   - Null, undefined, or programming values

2. **Always Show**:
   - Exactly 8 fields
   - Consistent formatting
   - Appropriate default values
   - Clean, user-friendly text

3. **Validation Examples**:
   ```
   ❌ Wrong: "FFmpeg PID: null"
   ✅ Correct: "FFmpeg PID: None"
   
   ❌ Wrong: "Storage Used: ERROR"
   ✅ Correct: "Storage Used: 0 B"
   
   ❌ Wrong: "Location: "
   ✅ Correct: "Location: Unknown"
   ```

## Display Order
Always display fields in this exact order:
1. Location
2. Connection
3. Recording Status
4. Connection Status
5. FFmpeg PID
6. Segments Created
7. Storage Used
8. Recording Uptime

## Action Button Standards

### Recording Control Buttons
After the 8 standardized info fields, cameras display recording control buttons in a separate section:

#### **Start Recording Button**
- **When to Show**: Recording Status is "Not Set" or "⏹️ Stopped"
- **Button Text**: "▶ Start Recording"
- **Button Icon**: Play symbol (▶)
- **Styling**: Green border/text with white background
- **Hover State**: Green background with white text

#### **Stop Recording Button**
- **When to Show**: Recording Status is "▶️ Recording"
- **Button Text**: "⏹ Stop Recording"
- **Button Icon**: Stop symbol (⏹)
- **Styling**: Red border/text with white background
- **Hover State**: Red background with white text

#### **Refresh Status Button**
- **When to Show**: Always displayed alongside Start/Stop button
- **Button Text**: "🔄 Refresh Status"
- **Button Icon**: Refresh symbol (🔄)
- **Styling**: Blue border/text with white background
- **Hover State**: Blue background with white text

### Button Layout Requirements
- **Section**: Buttons appear in separate "recording-controls-section" below info fields
- **Alignment**: Centered horizontally within camera card
- **Spacing**: 12px gap between buttons
- **Minimum Width**: 120px per button for consistency
- **Dark Mode**: White text with appropriate colored backgrounds

### Button Behavior
- **Disabled State**: When camera is offline or service unavailable
- **Loading State**: Show processing indicator during API calls
- **Error Handling**: Display user-friendly error messages
- **Success Feedback**: Confirm actions with toast notifications

### Implementation Example
```css
.recording-controls-section {
    padding: 16px;
    border-bottom: 1px solid #f0f0f0;
    background: white;
}

.recording-controls {
    display: flex;
    gap: 12px;
    justify-content: center;
}

.recording-btn {
    padding: 10px 16px;
    border-radius: 8px;
    min-width: 120px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}
```