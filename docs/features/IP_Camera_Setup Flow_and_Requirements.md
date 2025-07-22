# Complete Camera Setup Module Specification

## Module Overview
A 4-step wizard for adding IP cameras to an LPR (License Plate Recognition) system. The module provides intelligent camera discovery, configuration, testing, and preview capabilities with a modern, user-friendly interface.

## Visual Design & Layout

### Overall Container
- **Container**: `max-w-4xl mx-auto` - Centered container with maximum width
- **Background**: White background with rounded corners (`rounded-lg`) and shadow (`shadow-lg`)
- **Padding**: `p-6` - 24px padding on all sides
- **Typography**: Uses Tailwind's default font stack (Inter/system fonts)

### Header Section
```jsx
<div className="mb-8">
  <h2 className="text-2xl font-bold text-gray-900 mb-2">Add New IP Camera</h2>
  <div className="flex items-center justify-between">
    <div className="text-sm text-gray-600">Step {currentStep} of 4</div>
    <div className="flex space-x-2">
      {/* Progress dots */}
    </div>
  </div>
</div>
```

**Elements:**
- **Main Title**: 24px bold text in dark gray (`text-2xl font-bold text-gray-900`)
- **Step Indicator**: Small text showing current step (`text-sm text-gray-600`)
- **Progress Dots**: 4 circular indicators (12px diameter)
  - Current step: Blue (`bg-blue-600`)
  - Completed steps: Green (`bg-green-500`)
  - Future steps: Light gray (`bg-gray-300`)

## Step 1: Basic Camera Information

### Layout Structure
```jsx
<div className="space-y-6">
  <h3 className="text-lg font-semibold text-gray-900">Basic Camera Information</h3>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {/* Form fields */}
  </div>
</div>
```

### Form Fields

#### Camera Name Field
```jsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">Camera Name</label>
  <input
    type="text"
    value={formData.name}
    onChange={(e) => updateFormData('name', e.target.value)}
    placeholder="e.g., Front Gate Camera"
    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
  />
</div>
```

**Styling Details:**
- **Label**: Small, medium weight, dark gray text (`text-sm font-medium text-gray-700`)
- **Input**: Full width, 12px horizontal padding, 8px vertical padding
- **Border**: Light gray border that becomes blue on focus
- **Focus Ring**: 2px blue ring around input when focused
- **Placeholder**: Helpful example text

#### Location Dropdown
```jsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
  <select
    value={formData.location}
    onChange={(e) => updateFormData('location', e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    <option value="">Select Location</option>
    {locations.map(loc => (
      <option key={loc.id} value={loc.id}>{loc.name}</option>
    ))}
  </select>
</div>
```

**Data Structure:**
```javascript
const locations = [
  { id: 'loc1', name: 'Main Entrance' },
  { id: 'loc2', name: 'Parking Lot A' },
  { id: 'loc3', name: 'Exit Gate' },
  { id: 'loc4', name: 'Loading Dock' }
];
```

#### Manufacturer Dropdown with Smart Configuration
```jsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">Manufacturer</label>
  <select
    value={formData.manufacturer}
    onChange={(e) => updateFormData('manufacturer', e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    <option value="">Select Manufacturer</option>
    {Object.entries(manufacturers).map(([key, mfg]) => (
      <option key={key} value={key}>{mfg.name}</option>
    ))}
    <option value="other">Other/Generic</option>
  </select>
</div>
```

**Manufacturer Database Structure:**
```javascript
const manufacturers = {
  'reolink': {
    name: 'Reolink',
    models: ['RLC-811A', 'RLC-820A', 'RLC-823A', 'RLC-410A'],
    streamPaths: {
      rtsp: '/h264Preview_01_main',
      rtsps: '/h264Preview_01_main',
      http: '/flv?port=1935&app=bcs&stream=channel0_main.bcs'
    },
    defaultPorts: { rtsp: 554, rtsps: 322, http: 80, https: 443 }
  },
  // ... other manufacturers
};
```

#### Model Field with Auto-Suggestions
```jsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
  <input
    type="text"
    value={formData.model}
    onChange={(e) => updateFormData('model', e.target.value)}
    placeholder="Camera model number"
    list="model-suggestions"
    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
  />
  {formData.manufacturer && manufacturers[formData.manufacturer] && (
    <datalist id="model-suggestions">
      {manufacturers[formData.manufacturer].models.map(model => (
        <option key={model} value={model} />
      ))}
    </datalist>
  )}
</div>
```

**Behavior:** When manufacturer is selected, datalist populates with common models for auto-completion.

## Step 2: Camera Discovery

### Discovery Method Selection
```jsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">Discovery Method</label>
  <div className="space-y-2">
    <label className="flex items-center">
      <input
        type="radio"
        value="auto"
        checked={formData.discoveryMethod === 'auto'}
        onChange={(e) => updateFormData('discoveryMethod', e.target.value)}
        className="mr-2"
      />
      Auto-Discover (ONVIF/Network Scan)
    </label>
    <label className="flex items-center">
      <input
        type="radio"
        value="manual"
        checked={formData.discoveryMethod === 'manual'}
        onChange={(e) => updateFormData('discoveryMethod', e.target.value)}
        className="mr-2"
      />
      Manual Configuration
    </label>
  </div>
</div>
```

### IP Address Input with Scan Button
```jsx
<div className="flex gap-4 items-end">
  <div className="flex-1">
    <label className="block text-sm font-medium text-gray-700 mb-2">IP Address</label>
    <input
      type="text"
      value={formData.ipAddress}
      onChange={(e) => updateFormData('ipAddress', e.target.value)}
      placeholder="192.168.1.100"
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
  </div>
  <button
    onClick={discoverCameras}
    disabled={isDiscovering}
    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
  >
    {isDiscovering ? <Loader className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
    {isDiscovering ? 'Scanning...' : 'Scan Network'}
  </button>
</div>
```

**Button States:**
- **Normal**: Blue background with Search icon
- **Loading**: Spinning loader icon with "Scanning..." text
- **Disabled**: 50% opacity when scanning

### Discovery Results Display
```jsx
{discoveredCameras.length > 0 && (
  <div>
    <h4 className="font-medium text-gray-900 mb-2">Discovered Cameras</h4>
    <div className="space-y-2">
      {discoveredCameras.map((camera, index) => (
        <div
          key={index}
          className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
          onClick={() => {/* Auto-fill camera data */}}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Camera found at {camera.ip}</div>
              <div className="text-sm text-gray-500">
                {camera.manufacturer} {camera.model}
              </div>
              <div className="text-sm text-gray-500">
                Protocols: {camera.protocols.join(', ')}
              </div>
            </div>
            <CheckCircle className="w-5 h-5 text-green-500" />
          </div>
        </div>
      ))}
    </div>
  </div>
)}
```

**Interaction:** Clicking a discovered camera auto-fills manufacturer, model, and IP address in the form.

### Discovery Function Logic
```javascript
const discoverCameras = async () => {
  setIsDiscovering(true);
  
  // Simulate camera discovery (replace with actual implementation)
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  const mockDiscovered = [
    {
      ip: '192.168.1.100',
      manufacturer: 'Reolink',
      model: 'RLC-811A',
      protocols: ['RTSP', 'HTTP', 'ONVIF'],
      status: 'responsive'
    }
  ];
  
  setDiscoveredCameras(mockDiscovered);
  setIsDiscovering(false);
};
```

## Step 3: Connection Configuration

### Connection Type Dropdown
```jsx
<div className="md:col-span-2">
  <label className="block text-sm font-medium text-gray-700 mb-2">Connection Type</label>
  <select
    value={formData.connectionType}
    onChange={(e) => updateFormData('connectionType', e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    <option value="rtsp">RTSP (Recommended)</option>
    <option value="rtsps">RTSPS (Secure RTSP)</option>
    <option value="http">HTTP</option>
    <option value="https">HTTPS</option>
    <option value="onvif">ONVIF (Auto-discover)</option>
  </select>
</div>
```

### Auto-Configuration Logic
```javascript
useEffect(() => {
  // Auto-update port and stream path when connection type or manufacturer changes
  if (formData.manufacturer && manufacturers[formData.manufacturer]) {
    const manufacturerData = manufacturers[formData.manufacturer];
    const newPort = manufacturerData.defaultPorts[formData.connectionType] || 554;
    const newStreamPath = manufacturerData.streamPaths[formData.connectionType] || '';
    
    setFormData(prev => ({
      ...prev,
      port: newPort,
      streamPath: newStreamPath
    }));
  }
}, [formData.connectionType, formData.manufacturer]);
```

### Connection Testing Section
```jsx
<div className="border-t pt-4">
  <button
    onClick={testConnection}
    disabled={isTesting || !formData.ipAddress}
    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
  >
    {isTesting ? <Loader className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
    Test Connection
  </button>
  
  {connectionStatus && (
    <div className={`mt-4 p-4 rounded-md ${
      connectionStatus.status === 'success' 
        ? 'bg-green-50 border border-green-200' 
        : connectionStatus.status === 'error'
        ? 'bg-red-50 border border-red-200'
        : 'bg-blue-50 border border-blue-200'
    }`}>
      {/* Status display */}
    </div>
  )}
</div>
```

### Connection Status Display
**Success State:**
- Light green background (`bg-green-50`)
- Green border (`border-green-200`)
- Green checkmark icon
- Displays response time, supported codecs, max resolution

**Error State:**
- Light red background (`bg-red-50`)
- Red border (`border-red-200`)
- Red warning icon
- Shows error message and troubleshooting suggestions

**Testing State:**
- Light blue background (`bg-blue-50`)
- Blue border (`border-blue-200`)
- Spinning loader icon

### Test Connection Function
```javascript
const testConnection = async () => {
  setIsTesting(true);
  setConnectionStatus({ status: 'testing', message: 'Testing connection...' });
  
  // Simulate connection test
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  const success = Math.random() > 0.3; // 70% success rate for demo
  
  if (success) {
    setConnectionStatus({
      status: 'success',
      message: 'Connection successful! Camera is accessible.',
      details: {
        responseTime: '150ms',
        supportedCodecs: ['H.264', 'H.265'],
        maxResolution: '3840x2160'
      }
    });
    
    // Set available streams for next step
    setAvailableStreams([/* stream data */]);
  } else {
    setConnectionStatus({
      status: 'error',
      message: 'Connection failed',
      details: {
        error: 'Authentication failed. Please check username and password.',
        suggestions: [
          'Verify camera credentials',
          'Check if camera is powered on',
          'Ensure camera is on the same network'
        ]
      }
    });
  }
  
  setIsTesting(false);
};
```

## Step 4: Video Configuration & Preview

### Available Streams Display
```jsx
{availableStreams.length > 0 && (
  <div>
    <h4 className="font-medium text-gray-900 mb-3">Available Video Streams</h4>
    <div className="space-y-3">
      {availableStreams.map((stream, index) => (
        <div key={index} className="p-4 border border-gray-200 rounded-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <input
                type="radio"
                name="selectedStream"
                defaultChecked={index === 0}
                className="text-blue-600"
              />
              <span className="font-medium">{stream.name}</span>
            </div>
            <div className="text-sm text-gray-500">{stream.path}</div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Resolution:</span>
              <div className="font-medium">{stream.resolution}</div>
            </div>
            {/* More stream details */}
          </div>
        </div>
      ))}
    </div>
  </div>
)}
```

### Live Preview Section
```jsx
<div className="border border-gray-200 rounded-md p-4">
  <h4 className="font-medium text-gray-900 mb-3">Live Preview</h4>
  <div className="bg-gray-100 rounded-md h-64 flex items-center justify-center relative">
    {previewActive ? (
      <div className="w-full h-full bg-gray-800 rounded-md flex items-center justify-center">
        <div className="text-white text-center">
          <Camera className="w-12 h-12 mx-auto mb-2" />
          <div>Live Camera Feed</div>
          <div className="text-sm text-gray-300 mt-1">
            {formData.name || 'Camera Preview'}
          </div>
        </div>
      </div>
    ) : (
      <div className="text-center text-gray-500">
        <Camera className="w-12 h-12 mx-auto mb-2" />
        <div>Click "Start Preview" to view live feed</div>
      </div>
    )}
  </div>
  
  <div className="flex gap-2 mt-3">
    <button
      onClick={() => setPreviewActive(!previewActive)}
      className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
    >
      {previewActive ? (
        <>
          <Square className="w-4 h-4" />
          Stop Preview
        </>
      ) : (
        <>
          <Play className="w-4 h-4" />
          Start Preview
        </>
      )}
    </button>
    
    <button className="flex items-center gap-2 px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
      <Download className="w-4 h-4" />
      Snapshot
    </button>
    
    <button className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
      <CheckCircle className="w-4 h-4" />
      Test Stream
    </button>
  </div>
</div>
```

### Configuration Summary
```jsx
<div className="bg-blue-50 border border-blue-200 rounded-md p-4">
  <h4 className="font-medium text-blue-900 mb-2">Camera Configuration Summary</h4>
  <div className="text-sm text-blue-800 space-y-1">
    <div><strong>Name:</strong> {formData.name}</div>
    <div><strong>Location:</strong> {locations.find(l => l.id === formData.location)?.name}</div>
    <div><strong>Manufacturer:</strong> {manufacturers[formData.manufacturer]?.name}</div>
    <div><strong>Connection:</strong> {formData.connectionType.toUpperCase()}://{formData.ipAddress}:{formData.port}{formData.streamPath}</div>
    <div><strong>Authentication:</strong> {formData.authType} ({formData.username})</div>
  </div>
</div>
```

## Navigation Footer

### Footer Layout
```jsx
<div className="flex justify-between pt-6 border-t border-gray-200">
  <button
    onClick={handlePrevious}
    disabled={currentStep === 1}
    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
  >
    Previous
  </button>
  
  <div className="flex gap-2">
    {currentStep < 4 ? (
      <button
        onClick={handleNext}
        disabled={/* validation logic */}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next Step
      </button>
    ) : (
      <button
        onClick={handleSave}
        className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
      >
        Save Camera
      </button>
    )}
  </div>
</div>
```

### Navigation Logic
```javascript
const handleNext = () => {
  if (currentStep < 4) {
    setCurrentStep(currentStep + 1);
  }
};

const handlePrevious = () => {
  if (currentStep > 1) {
    setCurrentStep(currentStep - 1);
  }
};
```

### Validation Rules
```javascript
// Next button disabled when:
(currentStep === 1 && (!formData.name || !formData.location)) ||
(currentStep === 2 && !formData.ipAddress) ||
(currentStep === 3 && (!connectionStatus || connectionStatus.status !== 'success'))
```

## State Management

### Main Form State
```javascript
const [formData, setFormData] = useState({
  name: '',
  location: '',
  manufacturer: '',
  model: '',
  connectionType: 'rtsp',
  ipAddress: '',
  port: 554,
  streamPath: '',
  authType: 'basic',
  username: 'admin',
  password: '',
  discoveryMethod: 'manual'
});
```

### UI State Variables
```javascript
const [currentStep, setCurrentStep] = useState(1);
const [discoveredCameras, setDiscoveredCameras] = useState([]);
const [connectionStatus, setConnectionStatus] = useState(null);
const [isDiscovering, setIsDiscovering] = useState(false);
const [isTesting, setIsTesting] = useState(false);
const [availableStreams, setAvailableStreams] = useState([]);
const [previewActive, setPreviewActive] = useState(false);
```

### Update Function
```javascript
const updateFormData = (field, value) => {
  setFormData(prev => ({ ...prev, [field]: value }));
};
```

## Icon Usage (Lucide React)

### Required Icons
```javascript
import { 
  AlertCircle,    // Error states
  CheckCircle,    // Success states  
  Loader,         // Loading states
  Camera,         // Camera preview
  Search,         // Discovery button
  Play,           // Start preview
  Square,         // Stop preview
  Download        // Snapshot button
} from 'lucide-react';
```

### Icon Specifications
- **Size**: Most icons are `w-4 h-4` (16px) or `w-5 h-5` (20px)
- **Preview Icons**: `w-12 h-12` (48px) for main display
- **Animation**: Loader uses `animate-spin` class
- **Colors**: Icons inherit text color from parent or use specific color classes

## Responsive Design

### Grid System
```css
/* Step 1 & 3 forms */
.grid.grid-cols-1.md:grid-cols-2.gap-4

/* Stream details display */
.grid.grid-cols-2.md:grid-cols-4.gap-4
```

### Breakpoints
- **Mobile**: Single column layout
- **md (768px+)**: Two-column layout for forms, four-column for stream details

### Spacing System
- **Component Spacing**: `space-y-6` (24px vertical spacing)
- **Element Spacing**: `space-y-2`, `space-y-3`, `space-y-4`
- **Gap Spacing**: `gap-2`, `gap-4` for flexbox/grid

## Color Palette

### Primary Colors
- **Blue**: `bg-blue-600`, `hover:bg-blue-700`, `focus:ring-blue-500`
- **Green**: `bg-green-600`, `hover:bg-green-700`, `text-green-500`
- **Red**: `bg-red-50`, `border-red-200`, `text-red-700`
- **Gray**: `text-gray-900`, `text-gray-700`, `text-gray-500`, `bg-gray-100`

### Status Colors
- **Success**: Green backgrounds (`bg-green-50`) with green borders and text
- **Error**: Red backgrounds (`bg-red-50`) with red borders and text  
- **Info**: Blue backgrounds (`bg-blue-50`) with blue borders and text
- **Loading**: Blue theme with spinning animation

## Animation & Interactions

### Hover Effects
- **Buttons**: Background color darkens on hover
- **Cards**: Background lightens (`hover:bg-gray-50`) on hover
- **Inputs**: Focus ring appears with transition

### Loading States
- **Spinner**: `animate-spin` on Loader icon
- **Button Text**: Changes during loading ("Scanning..." vs "Scan Network")
- **Disabled States**: 50% opacity for disabled elements

### Transitions
- **Focus Rings**: Smooth transition on input focus
- **Button Hovers**: Smooth color transitions
- **State Changes**: Smooth transitions between UI states

This specification provides complete implementation details for recreating the camera setup module with identical functionality and appearance.