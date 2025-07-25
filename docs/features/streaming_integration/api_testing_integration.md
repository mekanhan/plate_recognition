# 🔧 API Testing Tools Integration

**Date**: 2025-01-24  
**Parent Feature**: Streaming UI Integration  
**Source**: `frontend/src/test_streaming.html`  
**Target**: Camera Modal Integration

## 🎯 Overview

Extract and integrate the comprehensive API testing functionality from `test_streaming.html` into the camera modal, providing users with real-time diagnostics and troubleshooting tools directly within the camera management interface.

## 📍 Source Analysis

### Existing test_streaming.html Features
The standalone testing page provides excellent diagnostic capabilities:

1. **Backend Health Checks** (Lines 164-180)
2. **Camera List Validation** (Lines 182-199)  
3. **Stream Status Monitoring** (Lines 201-217)
4. **Stream Control Testing** (Lines 219-271)
5. **Real-time API Logging** (Lines 150-156)
6. **Endpoint Availability Tests** (Lines 291-312)

### Key Functions to Extract
```javascript
// Core testing functions from test_streaming.html
- checkBackendHealth()    // Backend connectivity
- getCameraList()         // Camera API validation
- getStreamStatus()       // Stream monitoring
- startStream()           // Stream control testing
- stopStream()            // Stream management
- testVideoEndpoint()     // Endpoint validation
- log()                   // Real-time logging
```

## 🚀 Integration Target

### Camera Modal Enhancement
Integrate testing tools into existing camera modal as a new "Diagnostics" tab:

**Target Location**: Camera Modal (accessed via camera card "Configure" button)  
**Integration Method**: New tab within existing modal structure  
**User Flow**: Configure Camera → Diagnostics Tab → Real-time Testing

## 🔧 Technical Implementation

### 1. CameraApiTester Component

Create reusable component for API testing functionality:

```javascript
class CameraApiTester {
    constructor(camera) {
        this.camera = camera;
        this.apiBase = 'http://localhost:8001';
        this.testResults = new Map();
        this.logEntries = [];
        this.isTestingInProgress = false;
    }

    render() {
        return `
            <div class="api-tester-container">
                <!-- Test Controls Section -->
                <div class="test-controls-section">
                    <h4 class="section-title">
                        <i class="fas fa-tools"></i>
                        API Diagnostics for ${this.camera.name}
                    </h4>
                    
                    <div class="test-controls-grid">
                        <!-- Backend Health -->
                        <div class="test-control-group">
                            <label>Backend Health</label>
                            <button class="test-btn" id="test-backend-health" 
                                    onclick="apiTester.testBackendHealth()">
                                <i class="fas fa-heartbeat"></i>
                                Test Backend
                            </button>
                            <div class="test-result" id="backend-health-result"></div>
                        </div>

                        <!-- Camera Connectivity -->
                        <div class="test-control-group">
                            <label>Camera Connectivity</label>
                            <button class="test-btn" id="test-camera-connection" 
                                    onclick="apiTester.testCameraConnection()">
                                <i class="fas fa-plug"></i>
                                Test Connection
                            </button>
                            <div class="test-result" id="camera-connection-result"></div>
                        </div>

                        <!-- Stream Status -->
                        <div class="test-control-group">
                            <label>Stream Status</label>
                            <button class="test-btn" id="test-stream-status" 
                                    onclick="apiTester.testStreamStatus()">
                                <i class="fas fa-info-circle"></i>
                                Check Status
                            </button>
                            <div class="test-result" id="stream-status-result"></div>
                        </div>

                        <!-- Stream Control -->
                        <div class="test-control-group">
                            <label>Stream Control</label>
                            <div class="test-btn-group">
                                <button class="test-btn test-btn-success" id="test-start-stream" 
                                        onclick="apiTester.testStartStream()">
                                    <i class="fas fa-play"></i>
                                    Start
                                </button>
                                <button class="test-btn test-btn-danger" id="test-stop-stream" 
                                        onclick="apiTester.testStopStream()">
                                    <i class="fas fa-stop"></i>
                                    Stop
                                </button>
                            </div>
                            <div class="test-result" id="stream-control-result"></div>
                        </div>

                        <!-- Video Endpoint -->
                        <div class="test-control-group">
                            <label>Video Endpoint</label>
                            <button class="test-btn" id="test-video-endpoint" 
                                    onclick="apiTester.testVideoEndpoint()">
                                <i class="fas fa-video"></i>
                                Test Streaming
                            </button>
                            <div class="test-result" id="video-endpoint-result"></div>
                        </div>

                        <!-- Thumbnail Test -->
                        <div class="test-control-group">
                            <label>Thumbnail Test</label>
                            <button class="test-btn" id="test-thumbnail" 
                                    onclick="apiTester.testThumbnail()">
                                <i class="fas fa-image"></i>
                                Get Thumbnail
                            </button>
                            <div class="test-result" id="thumbnail-result"></div>
                        </div>
                    </div>

                    <!-- Quick Test All -->
                    <div class="quick-test-section">
                        <button class="test-btn test-btn-primary test-btn-large" 
                                id="run-all-tests" 
                                onclick="apiTester.runAllTests()">
                            <i class="fas fa-play-circle"></i>
                            Run All Tests
                        </button>
                        <button class="test-btn test-btn-secondary" 
                                id="clear-results" 
                                onclick="apiTester.clearResults()">
                            <i class="fas fa-trash"></i>
                            Clear Results
                        </button>
                    </div>
                </div>

                <!-- Results & Logging Section -->
                <div class="test-results-section">
                    <div class="results-header">
                        <h4 class="section-title">
                            <i class="fas fa-clipboard-list"></i>
                            Test Results & Logs
                        </h4>
                        <div class="results-controls">
                            <button class="results-btn" onclick="apiTester.exportResults()">
                                <i class="fas fa-download"></i>
                                Export
                            </button>
                            <button class="results-btn" onclick="apiTester.copyToClipboard()">
                                <i class="fas fa-copy"></i>
                                Copy
                            </button>
                        </div>
                    </div>

                    <!-- Real-time Log -->
                    <div class="api-log-container">
                        <div class="log-header">
                            <span class="log-title">API Test Log</span>
                            <span class="log-count" id="log-count">0 entries</span>
                        </div>
                        <div class="api-log" id="api-test-log">
                            <div class="log-entry log-info">
                                [${new Date().toLocaleTimeString()}] INFO: API Tester initialized for ${this.camera.name}
                            </div>
                        </div>
                    </div>

                    <!-- Summary Stats -->
                    <div class="test-summary">
                        <div class="summary-stat">
                            <span class="stat-label">Tests Passed:</span>
                            <span class="stat-value stat-success" id="tests-passed">0</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Tests Failed:</span>
                            <span class="stat-value stat-error" id="tests-failed">0</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Total Tests:</span>
                            <span class="stat-value" id="tests-total">0</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Last Updated:</span>
                            <span class="stat-value" id="last-updated">Never</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
```

### 2. Testing Functions Implementation

Extract and adapt functions from test_streaming.html:

```javascript
    async testBackendHealth() {
        this.setTestStatus('test-backend-health', 'testing');
        this.log('Testing backend health...', 'info');

        try {
            const response = await fetch(`${this.apiBase}/health`);
            const data = await response.json();

            if (response.ok) {
                this.setTestResult('backend-health-result', `Backend healthy: ${data.status}`, 'success');
                this.log(`Backend health check successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('backend-health', true);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.setTestResult('backend-health-result', `Backend error: ${error.message}`, 'error');
            this.log(`Backend health check failed: ${error.message}`, 'error');
            this.recordTestResult('backend-health', false);
        } finally {
            this.setTestStatus('test-backend-health', 'complete');
        }
    }

    async testCameraConnection() {
        this.setTestStatus('test-camera-connection', 'testing');
        this.log(`Testing connection to camera ${this.camera.name} (ID: ${this.camera.id})...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/api/v1/cameras/${this.camera.id}`);
            const data = await response.json();

            if (response.ok) {
                this.setTestResult('camera-connection-result', 
                    `Camera found: ${data.name} at ${data.ip_address}:${data.port}`, 'success');
                this.log(`Camera connection test successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('camera-connection', true);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.setTestResult('camera-connection-result', `Connection error: ${error.message}`, 'error');
            this.log(`Camera connection test failed: ${error.message}`, 'error');
            this.recordTestResult('camera-connection', false);
        } finally {
            this.setTestStatus('test-camera-connection', 'complete');
        }
    }

    async testStreamStatus() {
        this.setTestStatus('test-stream-status', 'testing');
        this.log(`Checking stream status for camera ${this.camera.id}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/api/v1/streams/status/${this.camera.id}`);
            const data = await response.json();

            if (response.ok) {
                this.setTestResult('stream-status-result', 
                    `Stream status: ${data.status}`, data.status === 'active' ? 'success' : 'info');
                this.log(`Stream status check successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('stream-status', true);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.setTestResult('stream-status-result', `Status error: ${error.message}`, 'error');
            this.log(`Stream status check failed: ${error.message}`, 'error');
            this.recordTestResult('stream-status', false);
        } finally {
            this.setTestStatus('test-stream-status', 'complete');
        }
    }

    async testStartStream() {
        this.setTestStatus('test-start-stream', 'testing');
        this.log(`Testing stream start for camera ${this.camera.id}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/api/v1/streams/start/${this.camera.id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    quality: 'medium',
                    max_fps: 30,
                    detection_enabled: false,
                    confidence_threshold: 0.7
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.setTestResult('stream-control-result', 
                    `Stream started: ${data.status}`, 'success');
                this.log(`Stream start test successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('stream-start', true);
            } else {
                // Expected to fail if camera not accessible
                this.setTestResult('stream-control-result', 
                    `Expected error: ${data.detail || 'Connection failed'}`, 'warning');
                this.log(`Stream start failed (expected): ${JSON.stringify(data)}`, 'warning');
                this.recordTestResult('stream-start', false, 'expected');
            }
        } catch (error) {
            this.setTestResult('stream-control-result', `Start error: ${error.message}`, 'error');
            this.log(`Stream start test failed: ${error.message}`, 'error');
            this.recordTestResult('stream-start', false);
        } finally {
            this.setTestStatus('test-start-stream', 'complete');
        }
    }

    async testVideoEndpoint() {
        this.setTestStatus('test-video-endpoint', 'testing');
        this.log(`Testing video endpoint for camera ${this.camera.id}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/stream/video/${this.camera.id}`, {
                method: 'HEAD'
            });

            if (response.status === 503) {
                this.setTestResult('video-endpoint-result', 
                    'Video endpoint exists (camera unavailable)', 'warning');
                this.log(`Video endpoint test: HTTP ${response.status} - Camera unavailable (expected)`, 'warning');
                this.recordTestResult('video-endpoint', true, 'expected');
            } else if (response.ok) {
                this.setTestResult('video-endpoint-result', 'Video endpoint working', 'success');
                this.log(`Video endpoint test: HTTP ${response.status} - Working`, 'success');
                this.recordTestResult('video-endpoint', true);
            } else {
                this.setTestResult('video-endpoint-result', `Video endpoint error: ${response.status}`, 'error');
                this.log(`Video endpoint test failed: HTTP ${response.status}`, 'error');
                this.recordTestResult('video-endpoint', false);
            }
        } catch (error) {
            this.setTestResult('video-endpoint-result', `Video test error: ${error.message}`, 'error');
            this.log(`Video endpoint test failed: ${error.message}`, 'error');
            this.recordTestResult('video-endpoint', false);
        } finally {
            this.setTestStatus('test-video-endpoint', 'complete');
        }
    }

    async testThumbnail() {
        this.setTestStatus('test-thumbnail', 'testing');
        this.log(`Testing thumbnail endpoint for camera ${this.camera.id}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/stream/thumbnail/${this.camera.id}`, {
                method: 'HEAD'
            });

            if (response.ok) {
                this.setTestResult('thumbnail-result', 'Thumbnail endpoint working', 'success');
                this.log(`Thumbnail test: HTTP ${response.status} - Working`, 'success');
                this.recordTestResult('thumbnail', true);
            } else {
                this.setTestResult('thumbnail-result', `Thumbnail error: ${response.status}`, 'error');
                this.log(`Thumbnail test failed: HTTP ${response.status}`, 'error');
                this.recordTestResult('thumbnail', false);
            }
        } catch (error) {
            this.setTestResult('thumbnail-result', `Thumbnail error: ${error.message}`, 'error');
            this.log(`Thumbnail test failed: ${error.message}`, 'error');
            this.recordTestResult('thumbnail', false);
        } finally {
            this.setTestStatus('test-thumbnail', 'complete');
        }
    }
```

### 3. Utility Functions

```javascript
    // Logging system
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            type,
            message,
            id: Date.now()
        };
        
        this.logEntries.push(logEntry);
        
        const logDiv = document.getElementById('api-test-log');
        if (logDiv) {
            const logElement = document.createElement('div');
            logElement.className = `log-entry log-${type}`;
            logElement.innerHTML = `[${timestamp}] ${type.toUpperCase()}: ${message}`;
            logDiv.appendChild(logElement);
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        this.updateLogCount();
    }

    // Test result management
    setTestResult(elementId, message, type = 'info') {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.className = `test-result test-result-${type}`;
        }
    }

    setTestStatus(buttonId, status) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        const icon = button.querySelector('i');
        
        switch (status) {
            case 'testing':
                button.disabled = true;
                if (icon) icon.className = 'fas fa-spinner fa-spin';
                break;
            case 'complete':
                button.disabled = false;
                if (icon) {
                    // Restore original icon based on button ID
                    const iconMap = {
                        'test-backend-health': 'fa-heartbeat',
                        'test-camera-connection': 'fa-plug',
                        'test-stream-status': 'fa-info-circle',
                        'test-start-stream': 'fa-play',
                        'test-stop-stream': 'fa-stop',
                        'test-video-endpoint': 'fa-video',
                        'test-thumbnail': 'fa-image'
                    };
                    icon.className = `fas ${iconMap[buttonId] || 'fa-check'}`;
                }
                break;
        }
    }

    recordTestResult(testName, passed, note = null) {
        this.testResults.set(testName, { passed, note, timestamp: new Date() });
        this.updateSummaryStats();
    }

    updateSummaryStats() {
        const passed = Array.from(this.testResults.values()).filter(r => r.passed).length;
        const total = this.testResults.size;
        const failed = total - passed;

        document.getElementById('tests-passed').textContent = passed;
        document.getElementById('tests-failed').textContent = failed;
        document.getElementById('tests-total').textContent = total;
        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
    }

    updateLogCount() {
        const countElement = document.getElementById('log-count');
        if (countElement) {
            countElement.textContent = `${this.logEntries.length} entries`;
        }
    }

    // Batch testing
    async runAllTests() {
        this.log('Running all API tests...', 'info');
        this.clearResults();

        const tests = [
            () => this.testBackendHealth(),
            () => this.testCameraConnection(),
            () => this.testStreamStatus(),
            () => this.testStartStream(),
            () => this.testVideoEndpoint(),
            () => this.testThumbnail()
        ];

        for (const test of tests) {
            await test();
            // Small delay between tests
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        this.log('All tests completed', 'info');
    }

    clearResults() {
        // Clear test results
        document.querySelectorAll('.test-result').forEach(el => {
            el.textContent = '';
            el.className = 'test-result';
        });

        // Clear log
        const logDiv = document.getElementById('api-test-log');
        if (logDiv) {
            logDiv.innerHTML = `
                <div class="log-entry log-info">
                    [${new Date().toLocaleTimeString()}] INFO: Test results cleared
                </div>
            `;
        }

        // Reset data
        this.testResults.clear();
        this.logEntries = [];
        this.updateSummaryStats();
        this.updateLogCount();
    }

    // Export functionality
    exportResults() {
        const results = {
            camera: this.camera,
            testResults: Object.fromEntries(this.testResults),
            logEntries: this.logEntries,
            timestamp: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `camera_${this.camera.id}_api_test_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
        this.log('Test results exported', 'info');
    }

    copyToClipboard() {
        const results = this.logEntries.map(entry => 
            `[${entry.timestamp}] ${entry.type.toUpperCase()}: ${entry.message}`
        ).join('\n');

        navigator.clipboard.writeText(results).then(() => {
            this.log('Test log copied to clipboard', 'info');
        }).catch(err => {
            this.log('Failed to copy to clipboard', 'error');
        });
    }
}
```

### 4. Modal Integration

Modify camera modal to include diagnostics tab:

```javascript
// Update camera modal in CamerasPage.js or CameraModal.js
showCameraDetailsModal(camera) {
    const modalHtml = `
        <div class="modal-overlay camera-modal" id="camera-details-modal">
            <div class="modal-container modal-large">
                <div class="modal-header">
                    <h3>
                        <i class="fas fa-cog"></i>
                        ${camera.name} Configuration
                    </h3>
                    <button class="modal-close" id="close-details-modal">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <!-- Modal Tabs -->
                <div class="modal-tabs">
                    <button class="modal-tab active" data-tab="details">
                        <i class="fas fa-info-circle"></i>
                        Details
                    </button>
                    <button class="modal-tab" data-tab="configuration">
                        <i class="fas fa-cog"></i>
                        Configuration
                    </button>
                    <button class="modal-tab" data-tab="diagnostics">
                        <i class="fas fa-tools"></i>
                        Diagnostics
                    </button>
                </div>
                
                <div class="modal-content">
                    <!-- Details Tab -->
                    <div class="tab-content active" id="details-tab">
                        <!-- Existing camera details content -->
                    </div>
                    
                    <!-- Configuration Tab -->
                    <div class="tab-content" id="configuration-tab">
                        <!-- Camera configuration form -->
                    </div>
                    
                    <!-- Diagnostics Tab -->
                    <div class="tab-content" id="diagnostics-tab">
                        <div id="api-tester-container">
                            <!-- API Tester will be rendered here -->
                        </div>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="close-modal-btn">Close</button>
                    <button class="btn btn-primary" id="save-changes-btn">
                        <i class="fas fa-save"></i>
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    `;

    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Initialize API Tester when diagnostics tab is opened
    let apiTester = null;
    
    document.querySelectorAll('.modal-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const tabName = e.target.dataset.tab;
            
            // Switch tabs
            document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            e.target.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Initialize API Tester when diagnostics tab is opened
            if (tabName === 'diagnostics' && !apiTester) {
                apiTester = new CameraApiTester(camera);
                document.getElementById('api-tester-container').innerHTML = apiTester.render();
                
                // Make apiTester globally accessible for onclick handlers
                window.apiTester = apiTester;
            }
        });
    });

    // Rest of modal setup...
}
```

## 🎨 Styling for API Testing

### CSS for Diagnostics Tab

```css
/* API Tester Styling */
.api-tester-container {
    max-height: 600px;
    overflow-y: auto;
    padding: 20px;
}

.test-controls-section {
    margin-bottom: 30px;
}

.test-controls-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.test-control-group {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 6px;
    border: 1px solid #e9ecef;
}

.test-control-group label {
    display: block;
    font-weight: 600;
    margin-bottom: 8px;
    color: #495057;
}

.test-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
    background: #6c757d;
    color: white;
    width: 100%;
    justify-content: center;
}

.test-btn:hover:not(:disabled) {
    background: #5a6268;
    transform: translateY(-1px);
}

.test-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.test-btn-success { background: #28a745; }
.test-btn-success:hover:not(:disabled) { background: #218838; }

.test-btn-danger { background: #dc3545; }
.test-btn-danger:hover:not(:disabled) { background: #c82333; }

.test-btn-primary { background: #007bff; }
.test-btn-primary:hover:not(:disabled) { background: #0056b3; }

.test-btn-secondary { background: #6c757d; }
.test-btn-secondary:hover:not(:disabled) { background: #5a6268; }

.test-btn-large {
    padding: 12px 24px;
    font-size: 16px;
}

.test-btn-group {
    display: flex;
    gap: 8px;
}

.test-btn-group .test-btn {
    width: auto;
    flex: 1;
}

.test-result {
    margin-top: 8px;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 12px;
    min-height: 16px;
}

.test-result-success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.test-result-error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.test-result-warning {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.test-result-info {
    background: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}

/* Quick Test Section */
.quick-test-section {
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e9ecef;
}

/* Results Section */
.test-results-section {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    overflow: hidden;
}

.results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
}

.results-controls {
    display: flex;
    gap: 8px;
}

.results-btn {
    padding: 6px 12px;
    background: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 4px;
}

.results-btn:hover {
    background: #5a6268;
}

/* API Log */
.api-log-container {
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
}

.log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: #e9ecef;
    font-size: 14px;
    font-weight: 600;
}

.log-count {
    font-size: 12px;
    color: #6c757d;
    font-weight: normal;
}

.api-log {
    height: 200px;
    overflow-y: auto;
    padding: 16px 20px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    background: #f8f9fa;
}

.log-entry {
    margin-bottom: 4px;
    padding: 2px 0;
}

.log-info { color: #17a2b8; }
.log-success { color: #28a745; }
.log-warning { color: #ffc107; }
.log-error { color: #dc3545; }

/* Test Summary */
.test-summary {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    padding: 16px 20px;
    background: white;
}

.summary-stat {
    text-align: center;
}

.stat-label {
    display: block;
    font-size: 12px;
    color: #6c757d;
    margin-bottom: 4px;
}

.stat-value {
    display: block;
    font-size: 18px;
    font-weight: bold;
    color: #495057;
}

.stat-success { color: #28a745; }
.stat-error { color: #dc3545; }

/* Modal Tabs */
.modal-tabs {
    display: flex;
    border-bottom: 1px solid #e9ecef;
    background: #f8f9fa;
}

.modal-tab {
    padding: 12px 20px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: #6c757d;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
}

.modal-tab:hover {
    background: #e9ecef;
    color: #495057;
}

.modal-tab.active {
    color: #007bff;
    border-bottom-color: #007bff;
    background: white;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* Responsive Design */
@media (max-width: 768px) {
    .test-controls-grid {
        grid-template-columns: 1fr;
    }
    
    .quick-test-section {
        flex-direction: column;
    }
    
    .test-summary {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .modal-tabs {
        flex-direction: column;
    }
    
    .api-tester-container {
        padding: 12px;
    }
}
```

## 📱 Real-time Updates

### Auto-refresh Integration

```javascript
// Auto-refresh capabilities for live monitoring
class CameraApiTester {
    constructor(camera) {
        // ... existing properties ...
        this.autoRefreshInterval = null;
        this.autoRefreshEnabled = false;
    }

    enableAutoRefresh(intervalSeconds = 30) {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }

        this.autoRefreshEnabled = true;
        this.autoRefreshInterval = setInterval(async () => {
            if (this.autoRefreshEnabled) {
                await this.testStreamStatus();
                await this.testBackendHealth();
            }
        }, intervalSeconds * 1000);

        this.log(`Auto-refresh enabled (${intervalSeconds}s interval)`, 'info');
    }

    disableAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
        this.autoRefreshEnabled = false;
        this.log('Auto-refresh disabled', 'info');
    }

    destroy() {
        this.disableAutoRefresh();
    }
}
```

## ✅ Testing & Validation

### Integration Testing Checklist
- [ ] API Tester loads in camera modal diagnostics tab
- [ ] All test functions work correctly
- [ ] Real-time logging displays properly
- [ ] Test results update in real-time
- [ ] Export functionality works
- [ ] Auto-refresh operates correctly
- [ ] Modal tabs switch properly
- [ ] Responsive design functions on mobile

### Error Handling
- [ ] Network errors handled gracefully
- [ ] API timeout scenarios covered
- [ ] Invalid responses managed properly
- [ ] UI remains responsive during testing

---

## 🚀 Implementation Priority

1. **High Priority**: Core CameraApiTester component
2. **High Priority**: Modal tab integration
3. **Medium Priority**: Real-time logging and results
4. **Medium Priority**: Export and copy functionality
5. **Low Priority**: Auto-refresh and advanced features

**This integration provides users with powerful diagnostic capabilities directly within the camera management interface, leveraging the comprehensive testing functionality from the standalone test page.**