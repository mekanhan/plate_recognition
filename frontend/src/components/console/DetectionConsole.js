/**
 * Real-time Detection Console Component
 * Displays live detection events via WebSocket for debugging and monitoring
 */
import webSocketService from '../../services/WebSocketService.js';

class DetectionConsole {
    constructor() {
        this.container = null;
        this.isVisible = true;
        this.events = [];
        this.maxEvents = 500;
        this.filterLevel = 'all'; // 'all', 'info', 'warning', 'error', 'success'
        this.selectedCamera = 'all';
        this.unsubscribeDetectionConsole = null;
        this.isAutoScroll = true;
        
        // Create console HTML
        this.createConsoleHTML();
        this.setupEventListeners();
        this.subscribeToDetectionEvents();
    }

    createConsoleHTML() {
        this.container = document.createElement('div');
        this.container.className = 'detection-console';
        this.container.innerHTML = `
            <div class="console-header">
                <div class="console-title">
                    <span class="console-icon">🔍</span>
                    <span>Real-time Detection Console</span>
                    <span class="event-count">(0 events)</span>
                </div>
                <div class="console-controls">
                    <select class="camera-filter" title="Filter by camera">
                        <option value="all">All Cameras</option>
                    </select>
                    <select class="severity-filter" title="Filter by severity">
                        <option value="all">All Events</option>
                        <option value="info">Info</option>
                        <option value="success">Success</option>
                        <option value="warning">Warning</option>
                        <option value="error">Error</option>
                    </select>
                    <button class="clear-btn" title="Clear console">🗑️</button>
                    <button class="scroll-btn active" title="Auto-scroll">📄</button>
                    <button class="export-btn" title="Export logs">💾</button>
                    <button class="toggle-btn" title="Toggle console">➖</button>
                </div>
            </div>
            <div class="console-body">
                <div class="events-container"></div>
                <div class="console-footer">
                    <div class="connection-status disconnected">
                        <span class="status-dot"></span>
                        <span class="status-text">Connecting...</span>
                    </div>
                    <div class="stats">
                        <span>Events: <span class="total-events">0</span></span>
                        <span class="separator">|</span>
                        <span>Success: <span class="success-count">0</span></span>
                        <span class="separator">|</span>
                        <span>Rejected: <span class="rejected-count">0</span></span>
                    </div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        const header = this.container.querySelector('.console-header');
        const toggleBtn = this.container.querySelector('.toggle-btn');
        const clearBtn = this.container.querySelector('.clear-btn');
        const scrollBtn = this.container.querySelector('.scroll-btn');
        const exportBtn = this.container.querySelector('.export-btn');
        const cameraFilter = this.container.querySelector('.camera-filter');
        const severityFilter = this.container.querySelector('.severity-filter');

        // Toggle console visibility
        toggleBtn.addEventListener('click', () => {
            this.toggleVisibility();
        });

        // Clear console
        clearBtn.addEventListener('click', () => {
            this.clearEvents();
        });

        // Toggle auto-scroll
        scrollBtn.addEventListener('click', () => {
            this.toggleAutoScroll();
        });

        // Export logs
        exportBtn.addEventListener('click', () => {
            this.exportLogs();
        });

        // Filter events
        cameraFilter.addEventListener('change', (e) => {
            this.selectedCamera = e.target.value;
            this.filterAndDisplayEvents();
        });

        severityFilter.addEventListener('change', (e) => {
            this.filterLevel = e.target.value;
            this.filterAndDisplayEvents();
        });

        // Subscribe to WebSocket connection status
        webSocketService.subscribe('connection', (data) => {
            this.updateConnectionStatus(data.status);
        });
    }

    subscribeToDetectionEvents() {
        // Subscribe to detection console events
        this.unsubscribeDetectionConsole = webSocketService.subscribe('detection_console', (event) => {
            this.addEvent(event);
        });

        // Send subscription request to server
        webSocketService.send('subscribe', { event_type: 'detection_console' });
    }

    addEvent(event) {
        // Add timestamp if not present
        if (!event.timestamp) {
            event.timestamp = new Date().toISOString();
        }

        // Add to events array
        this.events.unshift(event);

        // Maintain max events limit
        if (this.events.length > this.maxEvents) {
            this.events = this.events.slice(0, this.maxEvents);
        }

        // Update display
        this.filterAndDisplayEvents();
        this.updateStats();

        // Auto-scroll to top if enabled
        if (this.isAutoScroll && this.isVisible) {
            const container = this.container.querySelector('.events-container');
            container.scrollTop = 0;
        }
    }

    filterAndDisplayEvents() {
        const filteredEvents = this.events.filter(event => {
            // Filter by camera
            if (this.selectedCamera !== 'all' && event.camera_id !== this.selectedCamera) {
                return false;
            }

            // Filter by severity
            if (this.filterLevel !== 'all' && event.severity !== this.filterLevel) {
                return false;
            }

            return true;
        });

        this.displayEvents(filteredEvents);
        this.updateEventCount(filteredEvents.length);
    }

    displayEvents(events) {
        const container = this.container.querySelector('.events-container');
        
        container.innerHTML = events.map(event => {
            const time = new Date(event.timestamp).toLocaleTimeString();
            const severityClass = `severity-${event.severity || 'info'}`;
            const eventTypeClass = `event-${event.event_type || 'unknown'}`;
            
            let confidenceBar = '';
            if (event.confidence !== undefined && event.confidence !== null) {
                const confidence = Math.round(event.confidence * 100);
                confidenceBar = `<div class="confidence-bar" title="Confidence: ${confidence}%">
                    <div class="confidence-fill" style="width: ${confidence}%"></div>
                </div>`;
            }

            let processingTime = '';
            if (event.processing_time_ms !== undefined && event.processing_time_ms !== null) {
                processingTime = `<span class="processing-time">${Number(event.processing_time_ms).toFixed(1)}ms</span>`;
            }

            return `
                <div class="event-item ${severityClass} ${eventTypeClass}">
                    <div class="event-header">
                        <span class="event-time">${time}</span>
                        <span class="camera-id">Camera: ${event.camera_id}</span>
                        <span class="event-type">${event.event_type}</span>
                        ${processingTime}
                    </div>
                    <div class="event-message">${event.message}</div>
                    ${confidenceBar}
                    ${this.renderEventDetails(event.details)}
                </div>
            `;
        }).join('');
    }

    renderEventDetails(details) {
        if (!details || Object.keys(details).length === 0) {
            return '';
        }

        const detailsHtml = Object.entries(details).map(([key, value]) => {
            if (key === 'pop_metrics' && typeof value === 'object' && value !== null) {
                const qualityScore = value.quality_score !== undefined && value.quality_score !== null 
                    ? Number(value.quality_score).toFixed(1) 
                    : 'N/A';
                return `<div class="detail-item">
                    <strong>Quality:</strong> ${value.quality_level || 'unknown'} (${qualityScore}%)
                </div>`;
            } else if (key === 'reason') {
                return `<div class="detail-item"><strong>Reason:</strong> ${value}</div>`;
            } else if (key === 'plate_text') {
                return `<div class="detail-item"><strong>Text:</strong> "${value}"</div>`;
            } else if (key === 'ocr_confidence' && value !== null && value !== undefined) {
                return `<div class="detail-item"><strong>OCR:</strong> ${(Number(value) * 100).toFixed(1)}%</div>`;
            } else if (typeof value === 'number') {
                return `<div class="detail-item"><strong>${key}:</strong> ${Number(value).toFixed(2)}</div>`;
            } else if (typeof value === 'object' && value !== null) {
                return `<div class="detail-item"><strong>${key}:</strong> ${JSON.stringify(value)}</div>`;
            } else {
                return `<div class="detail-item"><strong>${key}:</strong> ${value}</div>`;
            }
        }).join('');

        return `<div class="event-details">${detailsHtml}</div>`;
    }

    updateEventCount(count) {
        const eventCount = this.container.querySelector('.event-count');
        eventCount.textContent = `(${count} events)`;
    }

    updateStats() {
        const totalEvents = this.events.length;
        const successCount = this.events.filter(e => e.event_type === 'accepted').length;
        const rejectedCount = this.events.filter(e => e.event_type === 'rejected').length;

        this.container.querySelector('.total-events').textContent = totalEvents;
        this.container.querySelector('.success-count').textContent = successCount;
        this.container.querySelector('.rejected-count').textContent = rejectedCount;
    }

    updateConnectionStatus(status) {
        const statusElement = this.container.querySelector('.connection-status');
        const statusText = this.container.querySelector('.status-text');

        statusElement.className = `connection-status ${status}`;
        
        switch (status) {
            case 'connected':
                statusText.textContent = 'Connected';
                break;
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                break;
            case 'failed':
                statusText.textContent = 'Connection Failed';
                break;
            default:
                statusText.textContent = 'Connecting...';
        }
    }

    updateCameraFilter(cameras) {
        const cameraFilter = this.container.querySelector('.camera-filter');
        const currentValue = cameraFilter.value;
        
        cameraFilter.innerHTML = '<option value="all">All Cameras</option>';
        
        cameras.forEach(camera => {
            const option = document.createElement('option');
            option.value = camera.id;
            option.textContent = `${camera.name} (${camera.id})`;
            cameraFilter.appendChild(option);
        });

        // Restore previous selection if valid
        if (cameras.find(c => c.id === currentValue)) {
            cameraFilter.value = currentValue;
        }
    }

    toggleVisibility() {
        const body = this.container.querySelector('.console-body');
        const toggleBtn = this.container.querySelector('.toggle-btn');
        
        this.isVisible = !this.isVisible;
        
        if (this.isVisible) {
            body.style.display = 'block';
            toggleBtn.textContent = '➖';
            toggleBtn.title = 'Minimize console';
        } else {
            body.style.display = 'none';
            toggleBtn.textContent = '➕';
            toggleBtn.title = 'Show console';
        }
    }

    toggleAutoScroll() {
        const scrollBtn = this.container.querySelector('.scroll-btn');
        this.isAutoScroll = !this.isAutoScroll;
        
        if (this.isAutoScroll) {
            scrollBtn.classList.add('active');
            scrollBtn.title = 'Auto-scroll enabled';
        } else {
            scrollBtn.classList.remove('active');
            scrollBtn.title = 'Auto-scroll disabled';
        }
    }

    clearEvents() {
        this.events = [];
        this.filterAndDisplayEvents();
        this.updateStats();
    }

    exportLogs() {
        const logsData = {
            timestamp: new Date().toISOString(),
            total_events: this.events.length,
            filters: {
                camera: this.selectedCamera,
                severity: this.filterLevel
            },
            events: this.events
        };

        const blob = new Blob([JSON.stringify(logsData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `detection-console-logs-${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    getElement() {
        return this.container;
    }

    destroy() {
        if (this.unsubscribeDetectionConsole) {
            this.unsubscribeDetectionConsole();
        }
        
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
    }
}

export default DetectionConsole;