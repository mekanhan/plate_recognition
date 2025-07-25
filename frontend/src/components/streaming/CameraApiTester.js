/**
 * CameraApiTester Component
 * API testing and diagnostics for cameras
 * Extracted from test_streaming.html functionality
 */

class CameraApiTester {
    constructor(camera) {
        this.camera = camera;
        this.apiBase = 'http://localhost:8001';
        this.testResults = new Map();
        this.logEntries = [];
        this.isTestingInProgress = false;
        this.containerId = `api-tester-${this.camera.id}-${Date.now()}`;
    }

    render() {
        return `
            <div class="api-tester-container" id="${this.containerId}">
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
                            <button class="test-btn" id="test-backend-health-${this.camera.id}" 
                                    onclick="window.cameraApiTesters?.get('${this.containerId}')?.testBackendHealth()">
                                <i class="fas fa-heartbeat"></i>
                                Test Backend
                            </button>
                            <div class="test-result" id="backend-health-result-${this.camera.id}"></div>
                        </div>

                        <!-- Camera Connectivity -->
                        <div class="test-control-group">
                            <label>Camera Connectivity</label>
                            <button class="test-btn" id="test-camera-connection-${this.camera.id}" 
                                    onclick="window.cameraApiTesters?.get('${this.containerId}')?.testCameraConnection()">
                                <i class="fas fa-plug"></i>
                                Test Connection
                            </button>
                            <div class="test-result" id="camera-connection-result-${this.camera.id}"></div>
                        </div>

                        <!-- Stream Status -->
                        <div class="test-control-group">
                            <label>Stream Status</label>
                            <button class="test-btn" id="test-stream-status-${this.camera.id}" 
                                    onclick="window.cameraApiTesters?.get('${this.containerId}')?.testStreamStatus()">
                                <i class="fas fa-info-circle"></i>
                                Check Status
                            </button>
                            <div class="test-result" id="stream-status-result-${this.camera.id}"></div>
                        </div>

                        <!-- Stream Control -->
                        <div class="test-control-group">
                            <label>Stream Control</label>
                            <div class="test-btn-group">
                                <button class="test-btn test-btn-success" id="test-start-stream-${this.camera.id}" 
                                        onclick="window.cameraApiTesters?.get('${this.containerId}')?.testStartStream()">
                                    <i class="fas fa-play"></i>
                                    Start
                                </button>
                                <button class="test-btn test-btn-danger" id="test-stop-stream-${this.camera.id}" 
                                        onclick="window.cameraApiTesters?.get('${this.containerId}')?.testStopStream()">
                                    <i class="fas fa-stop"></i>
                                    Stop
                                </button>
                            </div>
                            <div class="test-result" id="stream-control-result-${this.camera.id}"></div>
                        </div>

                        <!-- Video Endpoint -->
                        <div class="test-control-group">
                            <label>Video Endpoint</label>
                            <button class="test-btn" id="test-video-endpoint-${this.camera.id}" 
                                    onclick="window.cameraApiTesters?.get('${this.containerId}')?.testVideoEndpoint()">
                                <i class="fas fa-video"></i>
                                Test Streaming
                            </button>
                            <div class="test-result" id="video-endpoint-result-${this.camera.id}"></div>
                        </div>

                        <!-- Thumbnail Test -->
                        <div class="test-control-group">
                            <label>Thumbnail Test</label>
                            <button class="test-btn" id="test-thumbnail-${this.camera.id}" 
                                    onclick="window.cameraApiTesters?.get('${this.containerId}')?.testThumbnail()">
                                <i class="fas fa-image"></i>
                                Get Thumbnail
                            </button>
                            <div class="test-result" id="thumbnail-result-${this.camera.id}"></div>
                        </div>
                    </div>

                    <!-- Quick Test All -->
                    <div class="quick-test-section">
                        <button class="test-btn test-btn-primary test-btn-large" 
                                id="run-all-tests-${this.camera.id}" 
                                onclick="window.cameraApiTesters?.get('${this.containerId}')?.runAllTests()">
                            <i class="fas fa-play-circle"></i>
                            Run All Tests
                        </button>
                        <button class="test-btn test-btn-secondary" 
                                id="clear-results-${this.camera.id}" 
                                onclick="window.cameraApiTesters?.get('${this.containerId}')?.clearResults()">
                            <i class="fas fa-trash"></i>
                            Clear Results
                        </button>
                        <button class="test-btn test-btn-info" 
                                id="auto-refresh-${this.camera.id}" 
                                onclick="window.cameraApiTesters?.get('${this.containerId}')?.toggleAutoRefresh()">
                            <i class="fas fa-sync-alt"></i>
                            Auto Refresh
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
                            <button class="results-btn" onclick="window.cameraApiTesters?.get('${this.containerId}')?.exportResults()">
                                <i class="fas fa-download"></i>
                                Export
                            </button>
                            <button class="results-btn" onclick="window.cameraApiTesters?.get('${this.containerId}')?.copyToClipboard()">
                                <i class="fas fa-copy"></i>
                                Copy
                            </button>
                        </div>
                    </div>

                    <!-- Real-time Log -->
                    <div class="api-log-container">
                        <div class="log-header">
                            <span class="log-title">API Test Log</span>
                            <span class="log-count" id="log-count-${this.camera.id}">0 entries</span>
                        </div>
                        <div class="api-log" id="api-test-log-${this.camera.id}">
                            <div class="log-entry log-info">
                                [${new Date().toLocaleTimeString()}] INFO: API Tester initialized for ${this.camera.name}
                            </div>
                        </div>
                    </div>

                    <!-- Summary Stats -->
                    <div class="test-summary">
                        <div class="summary-stat">
                            <span class="stat-label">Tests Passed:</span>
                            <span class="stat-value stat-success" id="tests-passed-${this.camera.id}">0</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Tests Failed:</span>
                            <span class="stat-value stat-error" id="tests-failed-${this.camera.id}">0</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Total Tests:</span>
                            <span class="stat-value" id="tests-total-${this.camera.id}">0</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Last Updated:</span>
                            <span class="stat-value" id="last-updated-${this.camera.id}">Never</span>
                        </div>
                    </div>
                </div>

                <!-- Camera Details Panel -->
                <div class="camera-details-panel">
                    <h4 class="section-title">
                        <i class="fas fa-info-circle"></i>
                        Camera Configuration
                    </h4>
                    <div class="camera-details-grid">
                        <div class="detail-item">
                            <label>Camera ID:</label>
                            <span>${this.camera.id}</span>
                        </div>
                        <div class="detail-item">
                            <label>IP Address:</label>
                            <span>${this.camera.ipAddress}</span>
                        </div>
                        <div class="detail-item">
                            <label>Port:</label>
                            <span>${this.camera.port}</span>
                        </div>
                        <div class="detail-item">
                            <label>Connection Type:</label>
                            <span>${this.camera.connectionType?.toUpperCase()}</span>
                        </div>
                        <div class="detail-item">
                            <label>Stream Path:</label>
                            <span>${this.camera.streamPath || 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <label>Status:</label>
                            <span class="status-${this.camera.status}">${this.capitalizeFirst(this.camera.status)}</span>
                        </div>
                        <div class="detail-item">
                            <label>Stream URL:</label>
                            <span class="url-text">${this.apiBase}/stream/video/${this.camera.id}</span>
                        </div>
                        <div class="detail-item">
                            <label>Thumbnail URL:</label>
                            <span class="url-text">${this.apiBase}/stream/thumbnail/${this.camera.id}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    init() {
        // Store instance reference for global access
        if (!window.cameraApiTesters) {
            window.cameraApiTesters = new Map();
        }
        window.cameraApiTesters.set(this.containerId, this);

        // Initialize log with starting message
        this.log('API Tester initialized for ' + this.camera.name, 'info');
        this.updateLogCount();

        return this;
    }

    // Testing Functions
    async testBackendHealth() {
        this.setTestStatus(`test-backend-health-${this.camera.id}`, 'testing');
        this.log('Testing backend health...', 'info');

        try {
            const response = await fetch(`${this.apiBase}/health`);
            const data = await response.json();

            if (response.ok) {
                this.setTestResult(`backend-health-result-${this.camera.id}`, `Backend healthy: ${data.status}`, 'success');
                this.log(`Backend health check successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('backend-health', true);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.setTestResult(`backend-health-result-${this.camera.id}`, `Backend error: ${error.message}`, 'error');
            this.log(`Backend health check failed: ${error.message}`, 'error');
            this.recordTestResult('backend-health', false);
        } finally {
            this.setTestStatus(`test-backend-health-${this.camera.id}`, 'complete');
        }
    }

    async testCameraConnection() {
        this.setTestStatus(`test-camera-connection-${this.camera.id}`, 'testing');
        this.log(`Testing connection to camera ${this.camera.name} (ID: ${this.camera.id})...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/api/v1/cameras/${this.camera.id}`);
            const data = await response.json();

            if (response.ok) {
                this.setTestResult(`camera-connection-result-${this.camera.id}`, 
                    `Camera found: ${data.name} at ${data.ip_address}:${data.port}`, 'success');
                this.log(`Camera connection test successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('camera-connection', true);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.setTestResult(`camera-connection-result-${this.camera.id}`, `Connection error: ${error.message}`, 'error');
            this.log(`Camera connection test failed: ${error.message}`, 'error');
            this.recordTestResult('camera-connection', false);
        } finally {
            this.setTestStatus(`test-camera-connection-${this.camera.id}`, 'complete');
        }
    }

    async testStreamStatus() {
        this.setTestStatus(`test-stream-status-${this.camera.id}`, 'testing');
        this.log(`Checking stream status for camera ${this.camera.id}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/api/v1/streams/status/${this.camera.id}`);
            const data = await response.json();

            if (response.ok) {
                this.setTestResult(`stream-status-result-${this.camera.id}`, 
                    `Stream status: ${data.status}`, data.status === 'active' ? 'success' : 'info');
                this.log(`Stream status check successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('stream-status', true);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.setTestResult(`stream-status-result-${this.camera.id}`, `Status error: ${error.message}`, 'error');
            this.log(`Stream status check failed: ${error.message}`, 'error');
            this.recordTestResult('stream-status', false);
        } finally {
            this.setTestStatus(`test-stream-status-${this.camera.id}`, 'complete');
        }
    }

    async testStartStream() {
        this.setTestStatus(`test-start-stream-${this.camera.id}`, 'testing');
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
                this.setTestResult(`stream-control-result-${this.camera.id}`, 
                    `Stream started: ${data.status}`, 'success');
                this.log(`Stream start test successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('stream-start', true);
            } else {
                // Expected to fail if camera not accessible
                this.setTestResult(`stream-control-result-${this.camera.id}`, 
                    `Expected error: ${data.detail || 'Connection failed'}`, 'warning');
                this.log(`Stream start failed (expected): ${JSON.stringify(data)}`, 'warning');
                this.recordTestResult('stream-start', false, 'expected');
            }
        } catch (error) {
            this.setTestResult(`stream-control-result-${this.camera.id}`, `Start error: ${error.message}`, 'error');
            this.log(`Stream start test failed: ${error.message}`, 'error');
            this.recordTestResult('stream-start', false);
        } finally {
            this.setTestStatus(`test-start-stream-${this.camera.id}`, 'complete');
        }
    }

    async testStopStream() {
        this.setTestStatus(`test-stop-stream-${this.camera.id}`, 'testing');
        this.log(`Testing stream stop for camera ${this.camera.id}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/api/v1/streams/stop/${this.camera.id}`, {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                this.setTestResult(`stream-control-result-${this.camera.id}`, 
                    `Stream stopped: ${data.status}`, 'info');
                this.log(`Stream stop test successful: ${JSON.stringify(data)}`, 'success');
                this.recordTestResult('stream-stop', true);
            } else {
                this.setTestResult(`stream-control-result-${this.camera.id}`, `Stop error: ${data.detail}`, 'error');
                this.log(`Stream stop test failed: ${JSON.stringify(data)}`, 'error');
                this.recordTestResult('stream-stop', false);
            }
        } catch (error) {
            this.setTestResult(`stream-control-result-${this.camera.id}`, `Stop error: ${error.message}`, 'error');
            this.log(`Stream stop test failed: ${error.message}`, 'error');
            this.recordTestResult('stream-stop', false);
        } finally {
            this.setTestStatus(`test-stop-stream-${this.camera.id}`, 'complete');
        }
    }

    async testVideoEndpoint() {
        this.setTestStatus(`test-video-endpoint-${this.camera.id}`, 'testing');
        this.log(`Testing video endpoint for camera ${this.camera.id}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/stream/video/${this.camera.id}`, {
                method: 'HEAD'
            });

            if (response.status === 503) {
                this.setTestResult(`video-endpoint-result-${this.camera.id}`, 
                    'Video endpoint exists (camera unavailable)', 'warning');
                this.log(`Video endpoint test: HTTP ${response.status} - Camera unavailable (expected)`, 'warning');
                this.recordTestResult('video-endpoint', true, 'expected');
            } else if (response.ok) {
                this.setTestResult(`video-endpoint-result-${this.camera.id}`, 'Video endpoint working', 'success');
                this.log(`Video endpoint test: HTTP ${response.status} - Working`, 'success');
                this.recordTestResult('video-endpoint', true);
            } else {
                this.setTestResult(`video-endpoint-result-${this.camera.id}`, `Video endpoint error: ${response.status}`, 'error');
                this.log(`Video endpoint test failed: HTTP ${response.status}`, 'error');
                this.recordTestResult('video-endpoint', false);
            }
        } catch (error) {
            this.setTestResult(`video-endpoint-result-${this.camera.id}`, `Video test error: ${error.message}`, 'error');
            this.log(`Video endpoint test failed: ${error.message}`, 'error');
            this.recordTestResult('video-endpoint', false);
        } finally {
            this.setTestStatus(`test-video-endpoint-${this.camera.id}`, 'complete');
        }
    }

    async testThumbnail() {
        this.setTestStatus(`test-thumbnail-${this.camera.id}`, 'testing');
        this.log(`Testing thumbnail endpoint for camera ${this.camera.id}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/stream/thumbnail/${this.camera.id}`, {
                method: 'HEAD'
            });

            if (response.ok) {
                this.setTestResult(`thumbnail-result-${this.camera.id}`, 'Thumbnail endpoint working', 'success');
                this.log(`Thumbnail test: HTTP ${response.status} - Working`, 'success');
                this.recordTestResult('thumbnail', true);
            } else {
                this.setTestResult(`thumbnail-result-${this.camera.id}`, `Thumbnail error: ${response.status}`, 'error');
                this.log(`Thumbnail test failed: HTTP ${response.status}`, 'error');
                this.recordTestResult('thumbnail', false);
            }
        } catch (error) {
            this.setTestResult(`thumbnail-result-${this.camera.id}`, `Thumbnail error: ${error.message}`, 'error');
            this.log(`Thumbnail test failed: ${error.message}`, 'error');
            this.recordTestResult('thumbnail', false);
        } finally {
            this.setTestStatus(`test-thumbnail-${this.camera.id}`, 'complete');
        }
    }

    // Batch Testing
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

    // Utility Functions
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            type,
            message,
            id: Date.now()
        };
        
        this.logEntries.push(logEntry);
        
        const logDiv = document.getElementById(`api-test-log-${this.camera.id}`);
        if (logDiv) {
            const logElement = document.createElement('div');
            logElement.className = `log-entry log-${type}`;
            logElement.innerHTML = `[${timestamp}] ${type.toUpperCase()}: ${message}`;
            logDiv.appendChild(logElement);
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        this.updateLogCount();
    }

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
                        [`test-backend-health-${this.camera.id}`]: 'fa-heartbeat',
                        [`test-camera-connection-${this.camera.id}`]: 'fa-plug',
                        [`test-stream-status-${this.camera.id}`]: 'fa-info-circle',
                        [`test-start-stream-${this.camera.id}`]: 'fa-play',
                        [`test-stop-stream-${this.camera.id}`]: 'fa-stop',
                        [`test-video-endpoint-${this.camera.id}`]: 'fa-video',
                        [`test-thumbnail-${this.camera.id}`]: 'fa-image'
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

        document.getElementById(`tests-passed-${this.camera.id}`).textContent = passed;
        document.getElementById(`tests-failed-${this.camera.id}`).textContent = failed;
        document.getElementById(`tests-total-${this.camera.id}`).textContent = total;
        document.getElementById(`last-updated-${this.camera.id}`).textContent = new Date().toLocaleTimeString();
    }

    updateLogCount() {
        const countElement = document.getElementById(`log-count-${this.camera.id}`);
        if (countElement) {
            countElement.textContent = `${this.logEntries.length} entries`;
        }
    }

    clearResults() {
        // Clear test results
        document.querySelectorAll(`#${this.containerId} .test-result`).forEach(el => {
            el.textContent = '';
            el.className = 'test-result';
        });

        // Clear log
        const logDiv = document.getElementById(`api-test-log-${this.camera.id}`);
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

    // Auto-refresh functionality
    toggleAutoRefresh() {
        if (this.autoRefreshInterval) {
            this.disableAutoRefresh();
        } else {
            this.enableAutoRefresh();
        }
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
        
        // Update button
        const btn = document.getElementById(`auto-refresh-${this.camera.id}`);
        if (btn) {
            btn.innerHTML = '<i class="fas fa-pause"></i> Stop Auto Refresh';
            btn.classList.add('active');
        }
    }

    disableAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
        this.autoRefreshEnabled = false;
        this.log('Auto-refresh disabled', 'info');
        
        // Update button
        const btn = document.getElementById(`auto-refresh-${this.camera.id}`);
        if (btn) {
            btn.innerHTML = '<i class="fas fa-sync-alt"></i> Auto Refresh';
            btn.classList.remove('active');
        }
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

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    // Cleanup
    destroy() {
        this.disableAutoRefresh();
        
        // Remove from global registry
        if (window.cameraApiTesters) {
            window.cameraApiTesters.delete(this.containerId);
        }
        
        console.log(`CameraApiTester for ${this.camera.name} destroyed`);
    }

    // Static factory method
    static create(camera) {
        const tester = new CameraApiTester(camera);
        return tester;
    }
}

export default CameraApiTester;