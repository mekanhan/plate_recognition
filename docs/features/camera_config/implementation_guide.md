# Camera Configuration UI Implementation Guide

**Date:** 2024-07-24  
**Version:** 1.0  
**Target:** Replace SimpleCameraModal with comprehensive tabbed interface

## Quick Start Checklist

### Before Implementation
- [ ] Review current `SimpleCameraModal.js` functionality
- [ ] Understand existing design system in `variables.css`
- [ ] Check mobile responsiveness requirements
- [ ] Plan backend API extensions needed

### Design System Integration
- [ ] Update color values to match `--accent-color: #5960ca`
- [ ] Replace fixed pixels with CSS custom properties
- [ ] Align class naming with existing conventions
- [ ] Test with current dark/light theme system

## Component Structure

### File Organization
```
frontend/src/components/cameras/
├── CameraConfigModal.js          # Main modal component
├── tabs/
│   ├── NetworkTab.js             # Network configuration
│   ├── CameraTab.js              # Camera settings
│   ├── AIDetectionTab.js         # AI & detection
│   └── AdvancedTab.js            # Advanced settings
├── common/
│   ├── ROICanvas.js              # Region of interest drawing
│   ├── TabNavigation.js          # Tab switching logic
│   └── ConfigurationSaver.js     # Save/load functionality
└── styles/
    └── camera-config-modal.css   # Component-specific styles
```

## CSS Variables Integration

### Update Proposal Colors
```css
/* Replace proposal colors with system colors */
:root {
    /* Current system colors to use */
    --accent-color: #5960ca;          /* Instead of #4299e1 */
    --bg-primary: #bebec7;            /* Light theme */
    --bg-secondary: #8f8f92;
    --text-primary: #1a1d23;
    --border-color: #b0b7be;
    
    /* Use spacing system */
    --spacing-sm: 0.5rem;             /* Instead of 8px */
    --spacing-md: 1rem;               /* Instead of 16px */
    --spacing-lg: 1.5rem;             /* Instead of 24px */
    --spacing-xl: 2rem;               /* Instead of 32px */
}
```

### Component CSS Structure
```css
/* camera-config-modal.css */
.camera-config-modal .modal-container {
    max-width: min(900px, 95vw);      /* Responsive width */
    max-height: 90vh;
}

.camera-config-tabs {
    display: flex;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 10;
}

.tab-button {
    flex: 1;
    padding: var(--spacing-md) var(--spacing-lg);
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    border-bottom: 3px solid transparent;
}

.tab-button.active {
    background: var(--bg-primary);
    color: var(--accent-color);
    border-bottom-color: var(--accent-color);
}

/* Mobile responsive tabs */
@media (max-width: 768px) {
    .camera-config-tabs {
        flex-wrap: wrap;
    }
    
    .tab-button {
        flex-basis: 50%;
        padding: var(--spacing-sm) var(--spacing-md);
        font-size: var(--font-size-sm);
    }
}
```

## Tab Implementation

### 1. Network Tab (Phase 1)
```javascript
// NetworkTab.js
class NetworkTab {
    constructor(formData, onUpdate) {
        this.formData = formData;
        this.onUpdate = onUpdate;
    }
    
    render() {
        return `
            <div class="tab-content" id="network-tab">
                <div class="section">
                    <h3 class="section-title">
                        <i class="fas fa-globe"></i>
                        Network Connection
                    </h3>
                    
                    <div class="form-grid">
                        <!-- Camera Type Selection -->
                        <div class="form-group full-width">
                            <label class="form-label">Camera Type <span class="required">*</span></label>
                            <div class="button-group">
                                <button class="btn-option ${this.formData.camera_type === 'ip' ? 'active' : ''}" 
                                        data-type="ip">IP Camera</button>
                                <button class="btn-option ${this.formData.camera_type === 'usb' ? 'active' : ''}" 
                                        data-type="usb">USB Camera</button>
                                <button class="btn-option ${this.formData.camera_type === 'csi' ? 'active' : ''}" 
                                        data-type="csi">CSI Camera</button>
                            </div>
                        </div>
                        
                        <!-- IP Camera Settings -->
                        <div id="ip-settings" class="camera-type-settings ${this.formData.camera_type === 'ip' ? '' : 'hidden'}">
                            ${this.renderIPSettings()}
                        </div>
                        
                        <!-- USB Camera Settings -->
                        <div id="usb-settings" class="camera-type-settings ${this.formData.camera_type === 'usb' ? '' : 'hidden'}">
                            ${this.renderUSBSettings()}
                        </div>
                        
                        <!-- CSI Camera Settings -->
                        <div id="csi-settings" class="camera-type-settings ${this.formData.camera_type === 'csi' ? '' : 'hidden'}">
                            ${this.renderCSISettings()}
                        </div>
                    </div>
                </div>
                
                <div class="test-connection">
                    <button class="btn btn-primary" id="test-connection-btn">
                        <i class="fas fa-plug"></i>
                        Test Connection
                    </button>
                    <div class="test-result" id="test-result"></div>
                </div>
            </div>
        `;
    }
    
    renderIPSettings() {
        return `
            <div class="form-group">
                <label class="form-label">IP Address <span class="required">*</span></label>
                <input type="text" class="form-input" value="${this.formData.ip_address}" 
                       placeholder="192.168.1.100" data-field="ip_address" required>
            </div>
            <!-- Additional IP camera fields... -->
        `;
    }
    
    renderUSBSettings() {
        return `
            <div class="form-group">
                <label class="form-label">USB Device ID <span class="required">*</span></label>
                <select class="form-select" data-field="usb_id" required>
                    <option value="">Select USB Camera</option>
                    <option value="0" ${this.formData.usb_id === '0' ? 'selected' : ''}>Camera 0</option>
                    <option value="1" ${this.formData.usb_id === '1' ? 'selected' : ''}>Camera 1</option>
                </select>
            </div>
        `;
    }
    
    renderCSISettings() {
        return `
            <div class="form-group">
                <label class="form-label">CSI Port</label>
                <select class="form-select" data-field="csi_port">
                    <option value="0" ${this.formData.csi_port === '0' ? 'selected' : ''}>CSI Port 0</option>
                    <option value="1" ${this.formData.csi_port === '1' ? 'selected' : ''}>CSI Port 1</option>
                </select>
            </div>
        `;
    }
}
```

### 2. ROI Canvas Component
```javascript
// ROICanvas.js
class ROICanvas {
    constructor(canvasId, onZoneUpdate) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.zones = [];
        this.onZoneUpdate = onZoneUpdate;
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Mouse events for desktop
        this.canvas.addEventListener('mousedown', this.startDrawing.bind(this));
        this.canvas.addEventListener('mousemove', this.drawZone.bind(this));
        this.canvas.addEventListener('mouseup', this.endDrawing.bind(this));
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', this.handleTouch.bind(this));
        this.canvas.addEventListener('touchmove', this.handleTouch.bind(this));
        this.canvas.addEventListener('touchend', this.handleTouch.bind(this));
    }
    
    handleTouch(e) {
        e.preventDefault();
        const touch = e.touches[0] || e.changedTouches[0];
        const rect = this.canvas.getBoundingClientRect();
        const mouseEvent = new MouseEvent(e.type.replace('touch', 'mouse'), {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.canvas.dispatchEvent(mouseEvent);
    }
    
    // Additional ROI methods...
}
```

## Backend API Extensions

### Required Endpoints
```javascript
// New API endpoints needed
const newEndpoints = {
    // Camera discovery
    'GET /api/v1/cameras/discover': {
        description: 'Auto-discover cameras on network',
        response: [
            { ip: '192.168.1.100', manufacturer: 'Reolink', model: 'RLC-811A' },
            { ip: '192.168.1.101', manufacturer: 'Hikvision', model: 'DS-2CD2T85G1' }
        ]
    },
    
    // USB camera detection
    'GET /api/v1/cameras/usb': {
        description: 'List available USB cameras',
        response: [
            { id: 0, name: 'USB Camera 0', resolution: '1920x1080' },
            { id: 1, name: 'USB Camera 1', resolution: '1280x720' }
        ]
    },
    
    // Advanced camera settings
    'PUT /api/v1/cameras/{id}/video-settings': {
        description: 'Update video quality settings',
        body: {
            resolution: '1080p',
            frame_rate: 30,
            bitrate: 2000,
            compression: 'h264'
        }
    },
    
    // AI configuration
    'PUT /api/v1/cameras/{id}/ai-settings': {
        description: 'Update AI detection settings',
        body: {
            lpr_enabled: true,
            confidence_threshold: 0.75,
            detection_zones: [
                { name: 'Zone 1', x: 100, y: 80, width: 440, height: 200 }
            ]
        }
    }
};
```

### Database Schema Updates
```sql
-- Add new columns to cameras table
ALTER TABLE cameras ADD COLUMN camera_type VARCHAR(10) DEFAULT 'ip';
ALTER TABLE cameras ADD COLUMN usb_id INTEGER NULL;
ALTER TABLE cameras ADD COLUMN csi_port INTEGER NULL;
ALTER TABLE cameras ADD COLUMN video_settings JSON NULL;
ALTER TABLE cameras ADD COLUMN ai_settings JSON NULL;
ALTER TABLE cameras ADD COLUMN detection_zones JSON NULL;

-- Create camera templates table
CREATE TABLE camera_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_data JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert default templates
INSERT INTO camera_templates (name, description, template_data) VALUES
('Entrance Camera', 'Standard entrance monitoring setup', '{"location": "entrance", "ai_settings": {"lpr_enabled": true}}'),
('Parking Lot', 'Parking area monitoring configuration', '{"location": "parking", "ai_settings": {"vehicle_detection": true}}'),
('Exit Gate', 'Exit monitoring with speed detection', '{"location": "exit", "ai_settings": {"speed_estimation": true}}');
```

## Save/Load Implementation

### Configuration Saver Component
```javascript
// ConfigurationSaver.js
class ConfigurationSaver {
    constructor(modalInstance) {
        this.modal = modalInstance;
        this.autoSaveInterval = null;
        this.setupAutoSave();
    }
    
    setupAutoSave() {
        // Auto-save every 2 seconds
        this.autoSaveInterval = setInterval(() => {
            this.saveDraft();
        }, 2000);
    }
    
    async saveDraft() {
        const draftData = this.modal.getAllFormData();
        localStorage.setItem(`camera_config_draft_${this.modal.cameraId}`, JSON.stringify({
            data: draftData,
            timestamp: Date.now(),
            tabs_completed: this.getCompletedTabs()
        }));
    }
    
    async saveTabConfiguration(tabName) {
        const tabData = this.modal.getTabData(tabName);
        const isValid = this.validateTab(tabName, tabData);
        
        if (!isValid) {
            throw new Error(`${tabName} tab has validation errors`);
        }
        
        // Save to backend
        const response = await fetch(`/api/v1/cameras/${this.modal.cameraId}/${tabName}-settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tabData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save ${tabName} settings`);
        }
        
        // Update UI to show saved state
        this.showTabSavedIndicator(tabName);
        return await response.json();
    }
    
    async exportConfiguration() {
        const allData = this.modal.getAllFormData();
        const configBlob = new Blob([JSON.stringify(allData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(configBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `camera_config_${this.modal.formData.name}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    async importConfiguration(file) {
        const text = await file.text();
        const config = JSON.parse(text);
        
        // Validate configuration structure
        if (!this.validateImportedConfig(config)) {
            throw new Error('Invalid configuration file format');
        }
        
        // Load into modal
        this.modal.loadConfiguration(config);
        this.showImportSuccessMessage();
    }
}
```

### Per-Tab Save Buttons
```javascript
// Add save buttons to each tab
const addTabSaveButton = (tabId, tabName) => {
    return `
        <div class="tab-save-section">
            <button class="btn btn-success btn-save-tab" data-tab="${tabId}">
                <i class="fas fa-save"></i>
                Save ${tabName} Settings
            </button>
            <div class="save-status" id="${tabId}-save-status"></div>
        </div>
    `;
};

// Handle tab save button clicks
document.addEventListener('click', async (e) => {
    if (e.target.classList.contains('btn-save-tab')) {
        const tabId = e.target.dataset.tab;
        const saveBtn = e.target;
        
        try {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            
            await configSaver.saveTabConfiguration(tabId);
            
            saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved!';
            setTimeout(() => {
                saveBtn.innerHTML = `<i class="fas fa-save"></i> Save ${tabId} Settings`;
                saveBtn.disabled = false;
            }, 2000);
            
        } catch (error) {
            console.error('Save failed:', error);
            saveBtn.innerHTML = '<i class="fas fa-exclamation"></i> Save Failed';
            saveBtn.disabled = false;
        }
    }
});
```

## Mobile Optimization

### Responsive Tab Navigation
```css
/* Mobile-friendly tabs */
@media (max-width: 768px) {
    .camera-config-tabs {
        flex-direction: column;
        position: static; /* Remove sticky on mobile */
    }
    
    .tab-button {
        border-bottom: 1px solid var(--border-color);
        border-right: none;
        text-align: left;
        padding: var(--spacing-md);
    }
    
    .tab-button.active {
        border-left: 4px solid var(--accent-color);
        border-bottom: 1px solid var(--border-color);
    }
    
    /* Collapsible tabs for very small screens */
    .tabs-collapsed .camera-config-tabs {
        height: auto;
        overflow: hidden;
    }
    
    .tabs-collapsed .tab-button:not(.active) {
        display: none;
    }
    
    .tab-toggle {
        display: block;
        width: 100%;
        padding: var(--spacing-md);
        background: var(--bg-secondary);
        border: none;
        color: var(--text-primary);
        text-align: left;
    }
}

@media (min-width: 769px) {
    .tab-toggle {
        display: none;
    }
}
```

### Touch-Optimized ROI Canvas
```javascript
// Enhanced touch support for ROI canvas
class TouchOptimizedROI extends ROICanvas {
    constructor(canvasId, onZoneUpdate) {
        super(canvasId, onZoneUpdate);
        this.touchStartTime = 0;
        this.touchMoved = false;
    }
    
    handleTouch(e) {
        e.preventDefault();
        const touch = e.touches[0] || e.changedTouches[0];
        
        if (e.type === 'touchstart') {
            this.touchStartTime = Date.now();
            this.touchMoved = false;
        } else if (e.type === 'touchmove') {
            this.touchMoved = true;
        } else if (e.type === 'touchend') {
            const touchDuration = Date.now() - this.touchStartTime;
            
            // Long press for zone creation, short tap for selection
            if (!this.touchMoved && touchDuration > 500) {
                this.startZoneCreation(touch);
            } else if (!this.touchMoved) {
                this.selectZone(touch);
            }
        }
        
        // Convert to mouse event for existing logic
        const mouseEvent = new MouseEvent(this.getTouchMouseType(e.type), {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.canvas.dispatchEvent(mouseEvent);
    }
    
    getTouchMouseType(touchType) {
        const mapping = {
            'touchstart': 'mousedown',
            'touchmove': 'mousemove',
            'touchend': 'mouseup'
        };
        return mapping[touchType] || touchType;
    }
}
```

## Testing Strategy

### Unit Tests
```javascript
// Test tab switching functionality
describe('CameraConfigModal', () => {
    test('should switch tabs correctly', () => {
        const modal = new CameraConfigModal();
        modal.switchTab('camera');
        expect(modal.activeTab).toBe('camera');
        expect(document.querySelector('.tab-content.active').id).toBe('camera-tab');
    });
    
    test('should validate form data per tab', () => {
        const modal = new CameraConfigModal();
        const networkData = { ip_address: '', camera_type: 'ip' };
        expect(modal.validateTab('network', networkData)).toBe(false);
        
        networkData.ip_address = '192.168.1.100';
        expect(modal.validateTab('network', networkData)).toBe(true);
    });
});
```

### Integration Tests
```javascript
// Test save/load functionality
describe('Configuration Persistence', () => {
    test('should save and load tab configuration', async () => {
        const saver = new ConfigurationSaver(modal);
        const testData = { resolution: '1080p', frame_rate: 30 };
        
        await saver.saveTabConfiguration('camera', testData);
        const savedData = await saver.loadTabConfiguration('camera');
        
        expect(savedData).toEqual(testData);
    });
});
```

### Mobile Testing Checklist
- [ ] Tab navigation works on touch devices
- [ ] ROI canvas responds to touch gestures  
- [ ] Form fields are properly sized for mobile
- [ ] Modal fits within viewport on all screen sizes
- [ ] Save/load functions work on mobile browsers

## Deployment Steps

### Phase 1: Basic Replacement
1. Create new `CameraConfigModal.js` component
2. Implement Network tab with IP/USB/CSI support
3. Update CSS to match design system
4. Replace current modal usage in `CamerasPage.js`
5. Test basic functionality

### Phase 2: Enhanced Features
1. Add Camera settings tab
2. Implement ROI canvas with touch support
3. Add per-tab save functionality
4. Create configuration templates

### Phase 3: Advanced Features
1. Complete AI & Detection tab
2. Implement Advanced settings
3. Add export/import functionality
4. Full mobile optimization

### Phase 4: Polish & Testing
1. Cross-browser testing
2. Mobile device testing
3. Performance optimization
4. User acceptance testing

This implementation guide provides a comprehensive roadmap for replacing the current SimpleCameraModal with the proposed comprehensive interface while maintaining design consistency and adding robust new functionality.