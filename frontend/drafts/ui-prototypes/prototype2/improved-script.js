function initRangeSliders() {
    const rangeSliders = document.querySelectorAll('.form-range');
    
    rangeSliders.forEach(slider => {
        const updateValue = () => {
            const value = slider.value;
            const min = slider.min || 0;
            const max = slider.max || 100;
            const percentage = ((value - min) / (max - min)) * 100;
            
            // Update visual feedback
            slider.style.background = `linear-gradient(to right, var(--brand-primary) 0%, var(--brand-primary) ${percentage}%, var(--color-border) ${percentage}%, var(--color-border) 100%)`;
            
            // Update associated value display
            const valueDisplay = slider.parentElement.querySelector('.range-value');
            if (valueDisplay) {
                valueDisplay.textContent = value + '%';
            }
        };
        
        // Initialize and add event listener
        updateValue();
        slider.addEventListener('input', updateValue);
    });
}

function initSearchFunctionality() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            // Debounce search
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.id === 'plateSearch') {
                    searchDetections(query);
                } else {
                    searchCameras(query);
                }
            }, 300);
            
            // Visual feedback
            updateSearchVisualFeedback(this, query);
        });
        
        // Clear search on escape
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                this.dispatchEvent(new Event('input'));
                this.blur();
            }
        });
        
        // Enhanced accessibility
        input.setAttribute('role', 'searchbox');
        input.setAttribute('autocomplete', 'off');
    });
}

function updateSearchVisualFeedback(input, query) {
    if (query.length > 0) {
        input.style.borderColor = 'var(--brand-primary)';
        input.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.1)';
    } else {
        input.style.borderColor = '';
        input.style.boxShadow = '';
    }
}

function initButtonInteractions() {
    // Use event delegation for better performance
    document.addEventListener('click', function(e) {
        const button = e.target.closest('.btn:not([disabled])');
        if (!button) return;
        
        // Create ripple effect
        createRippleEffect(button, e);
        
        // Handle button-specific actions
        handleButtonClick(button);
    });
    
    // Enhanced hover effects
    document.addEventListener('mouseenter', function(e) {
        const button = e.target.closest('.btn:not([disabled])');
        if (button) {
            button.style.transform = 'translateY(-1px)';
        }
    }, true);
    
    document.addEventListener('mouseleave', function(e) {
        const button = e.target.closest('.btn:not([disabled])');
        if (button) {
            button.style.transform = '';
        }
    }, true);
}

function createRippleEffect(button, event) {
    const ripple = document.createElement('div');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255, 255, 255, 0.4);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
        z-index: 1;
    `;
    
    // Ensure button has relative positioning
    const originalPosition = button.style.position;
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
        if (!originalPosition) {
            button.style.position = '';
        }
    }, 600);
}

function handleButtonClick(button) {
    const btnText = button.textContent.trim();
    
    if (btnText.includes('Refresh')) {
        simulateRefresh(button);
    } else if (btnText.includes('Export')) {
        simulateExport(button);
    } else if (btnText.includes('Generate Report')) {
        simulateReportGeneration(button);
    } else if (btnText.includes('View')) {
        simulateDetailView(button);
    } else if (btnText.includes('Enhance')) {
        simulateEnhancement(button);
    } else if (btnText.includes('Save')) {
        simulateSave(button);
    } else if (btnText.includes('Configure')) {
        // Handled by modal system
    }
}

function initCameraInteractions() {
    document.addEventListener('click', function(e) {
        const cameraFeed = e.target.closest('.camera-feed');
        const cameraCard = e.target.closest('.camera-card');
        
        if (cameraFeed && !cameraCard) {
            highlightCameraFeed(cameraFeed);
        }
    });
    
    document.addEventListener('dblclick', function(e) {
        const cameraElement = e.target.closest('.camera-feed, .camera-card');
        if (cameraElement) {
            simulateFullscreen(cameraElement);
        }
    });
}

function highlightCameraFeed(feed) {
    // Remove previous highlights
    document.querySelectorAll('.camera-feed').forEach(f => {
        f.style.transform = '';
        f.style.zIndex = '';
        f.style.boxShadow = '';
    });
    
    // Highlight selected feed
    feed.style.transform = 'scale(1.05)';
    feed.style.zIndex = '10';
    feed.style.boxShadow = '0 8px 25px rgba(37, 99, 235, 0.3)';
    
    setTimeout(() => {
        feed.style.transform = '';
        feed.style.zIndex = '';
        feed.style.boxShadow = '';
    }, 2000);
    
    // Announce to screen readers
    announceToScreenReader('Camera feed selected');
}

function simulateFullscreen(element) {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.95);
        z-index: 3000;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        backdrop-filter: blur(10px);
    `;
    
    const content = element.cloneNode(true);
    content.style.cssText = `
        transform: scale(2.5);
        background: var(--color-surface);
        border-radius: var(--radius-lg);
        padding: 2rem;
        border: 2px solid var(--color-border);
        box-shadow: var(--shadow-xl);
    `;
    
    overlay.appendChild(content);
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';
    
    // Close on click or escape
    const closeFullscreen = () => {
        overlay.remove();
        document.body.style.overflow = 'auto';
    };
    
    overlay.addEventListener('click', closeFullscreen);
    
    const escapeListener = (e) => {
        if (e.key === 'Escape') {
            closeFullscreen();
            document.removeEventListener('keydown', escapeListener);
        }
    };
    document.addEventListener('keydown', escapeListener);
    
    showNotification('Press ESC or click to exit fullscreen', 'info', 3000);
}

function initDetectionInteractions() {
    document.addEventListener('click', function(e) {
        const detectionItem = e.target.closest('.detection-item');
        if (detectionItem) {
            selectDetectionItem(detectionItem);
        }
    });
}

function selectDetectionItem(item) {
    // Remove previous selections
    document.querySelectorAll('.detection-item').forEach(i => {
        i.style.background = '';
        i.style.borderLeft = '';
        i.classList.remove('selected');
    });
    
    // Highlight selected item
    item.style.background = 'var(--color-success-bg)';
    item.style.borderLeft = '4px solid var(--color-success)';
    item.classList.add('selected');
    
    const plateNumber = item.querySelector('h4').textContent;
    showNotification(`Selected detection: ${plateNumber}`, 'info', 2000);
    
    // Announce to screen readers
    announceToScreenReader(`Detection ${plateNumber} selected`);
}

function initAutoRefreshToggle() {
    const autoRefreshToggle = document.getElementById('autoRefresh');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function() {
            if (this.checked) {
                showNotification('Auto-refresh enabled', 'success', 2000);
                startAutoRefresh();
            } else {
                showNotification('Auto-refresh disabled', 'warning', 2000);
                stopAutoRefresh();
            }
        });
    }
}

function initFormEnhancements() {
    // Enhanced form validation and feedback
    const formControls = document.querySelectorAll('.form-control');
    
    formControls.forEach(control => {
        // Real-time validation feedback
        control.addEventListener('blur', function() {
            validateField(this);
        });
        
        control.addEventListener('input', function() {
            if (this.classList.contains('error')) {
                validateField(this);
            }
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    const type = field.type;
    
    // Remove previous validation state
    field.classList.remove('error', 'success');
    
    // Basic validation
    if (isRequired && !value) {
        setFieldError(field, 'This field is required');
        return false;
    }
    
    if (type === 'email' && value && !isValidEmail(value)) {
        setFieldError(field, 'Please enter a valid email address');
        return false;
    }
    
    if (field.placeholder && field.placeholder.includes('192.168') && value) {
        if (!isValidIP(value)) {
            setFieldError(field, 'Please enter a valid IP address');
            return false;
        }
    }
    
    // Field is valid
    setFieldSuccess(field);
    return true;
}

function setFieldError(field, message) {
    field.classList.add('error');
    field.style.borderColor = 'var(--color-error)';
    
    // Add error message
    let errorElement = field.parentElement.querySelector('.field-error');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.style.cssText = `
            color: var(--color-error);
            font-size: 0.75rem;
            margin-top: 0.25rem;
        `;
        field.parentElement.appendChild(errorElement);
    }
    errorElement.textContent = message;
}

function setFieldSuccess(field) {
    field.classList.add('success');
    field.style.borderColor = 'var(--color-success)';
    
    // Remove error message
    const errorElement = field.parentElement.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidIP(ip) {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
}

// ==============================================
// REAL-TIME SIMULATION
// ==============================================
let autoRefreshInterval;
let metricsInterval;
let detectionsInterval;

function initRealTimeSimulation() {
    startAutoRefresh();
    startMetricsUpdates();
    updateLastUpdateTime();
    
    // Update time display
    setInterval(updateLastUpdateTime, 1000);
}

function startAutoRefresh() {
    // Simulate new detections
    detectionsInterval = setInterval(() => {
        const autoRefresh = document.getElementById('autoRefresh');
        if (!autoRefresh || autoRefresh.checked) {
            addNewDetection();
            updateDetectionCount();
        }
    }, 12000); // Every 12 seconds
    
    // Simulate camera status changes
    setInterval(() => {
        simulateCameraStatusChange();
    }, 30000); // Every 30 seconds
}

function stopAutoRefresh() {
    if (detectionsInterval) {
        clearInterval(detectionsInterval);
    }
}

function startMetricsUpdates() {
    metricsInterval = setInterval(() => {
        updateMetrics();
    }, 5000); // Every 5 seconds
}

function updateLastUpdateTime() {
    const lastUpdateElement = document.getElementById('lastUpdate');
    if (lastUpdateElement) {
        const now = new Date();
        const lastUpdate = window.lastUpdateTime || now.getTime();
        const seconds = Math.floor((now.getTime() - lastUpdate) / 1000);
        
        if (seconds < 5) {
            lastUpdateElement.textContent = 'Just now';
        } else if (seconds < 60) {
            lastUpdateElement.textContent = `${seconds}s ago`;
        } else {
            const minutes = Math.floor(seconds / 60);
            lastUpdateElement.textContent = `${minutes}m ago`;
        }
    }
}

function addNewDetection() {
    const recentDetections = document.getElementById('recentDetections');
    const detectionsTable = document.getElementById('detectionsTable');
    
    if (!recentDetections && !detectionsTable) return;
    
    const plateNumbers = ['ABC-1234', 'XYZ-5678', 'DEF-9012', 'GHI-3456', 'JKL-7890', 'MNO-2345'];
    const cameras = ['Main Entrance', 'Parking Lot A', 'Side Entrance', 'Exit Gate', 'Loading Dock'];
    const vehicleTypes = ['Sedan', 'SUV', 'Truck', 'Motorcycle', 'Van'];
    const vehicleIcons = ['fa-car', 'fa-truck', 'fa-motorcycle', 'fa-bus'];
    
    const randomPlate = plateNumbers[Math.floor(Math.random() * plateNumbers.length)];
    const randomCamera = cameras[Math.floor(Math.random() * cameras.length)];
    const randomVehicle = vehicleTypes[Math.floor(Math.random() * vehicleTypes.length)];
    const randomIcon = vehicleIcons[Math.floor(Math.random() * vehicleIcons.length)];
    const randomConfidence = 75 + Math.floor(Math.random() * 25); // 75-99%
    const now = new Date();
    
    // Add to recent detections list
    if (recentDetections && document.getElementById('dashboard').classList.contains('active')) {
        const newDetection = createDetectionItem(randomPlate, randomCamera, 'Just now', randomConfidence, randomIcon);
        recentDetections.insertBefore(newDetection, recentDetections.firstChild);
        
        // Remove last item if more than 3
        const items = recentDetections.querySelectorAll('.detection-item');
        if (items.length > 3) {
            recentDetections.removeChild(items[items.length - 1]);
        }
        
        // Animate new detection
        animateNewElement(newDetection);
    }
    
    // Add to detections table
    if (detectionsTable && document.getElementById('detections').classList.contains('active')) {
        const newRow = createDetectionTableRow(randomPlate, randomCamera, now, randomConfidence, randomVehicle, randomIcon);
        detectionsTable.insertBefore(newRow, detectionsTable.firstChild);
        
        // Animate new row
        animateNewElement(newRow);
    }
    
    // Show notification for high confidence detections
    if (randomConfidence >= 95) {
        showNotification(`High confidence detection: ${randomPlate} (${randomConfidence}%)`, 'success');
    }
    
    // Update timestamp
    window.lastUpdateTime = now.getTime();
}

function animateNewElement(element) {
    element.style.background = 'var(--color-success-bg)';
    element.style.transform = 'translateX(-20px)';
    element.style.opacity = '0';
    
    setTimeout(() => {
        element.style.transition = 'all 0.5s ease';
        element.style.transform = 'translateX(0)';
        element.style.opacity = '1';
    }, 100);
    
    setTimeout(() => {
        element.style.background = '';
        element.style.transition = '';
    }, 3000);
}

function createDetectionItem(plateNumber, camera, timestamp, confidence, iconClass) {
    const item = document.createElement('div');
    item.className = 'detection-item';
    item.setAttribute('role', 'button');
    item.setAttribute('tabindex', '0');
    
    const confidenceClass = confidence >= 90 ? 'high' : confidence >= 80 ? 'medium' : 'low';
    
    item.innerHTML = `
        <div class="detection-thumbnail">
            <i class="fas ${iconClass}"></i>
        </div>
        <div class="detection-info">
            <h4>${plateNumber}</h4>
            <p>${camera}</p>
            <span class="timestamp">${timestamp}</span>
        </div>
        <div class="detection-confidence">
            <span class="confidence ${confidenceClass}">${confidence}%</span>
        </div>
    `;
    
    // Add click and keyboard handlers
    item.addEventListener('click', function() {
        selectDetectionItem(this);
    });
    
    item.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            selectDetectionItem(this);
        }
    });
    
    return item;
}

function createDetectionTableRow(plateNumber, camera, timestamp, confidence, vehicleType, iconClass) {
    const row = document.createElement('tr');
    const confidenceClass = confidence >= 90 ? 'high' : confidence >= 80 ? 'medium' : 'low';
    
    row.innerHTML = `
        <td>
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 40px; height: 40px; background: var(--brand-primary); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; color: white;">
                    <i class="fas ${iconClass}"></i>
                </div>
                <strong>${plateNumber}</strong>
            </div>
        </td>
        <td>${camera}</td>
        <td>${timestamp.toLocaleString()}</td>
        <td><span class="confidence ${confidenceClass}">${confidence}%</span></td>
        <td>${vehicleType}</td>
        <td>
            <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-primary btn-sm">
                    <i class="fas fa-eye"></i> View
                </button>
                <button class="btn btn-outline btn-sm">
                    <i class="fas fa-magic"></i> Enhance
                </button>
            </div>
        </td>
    `;
    
    return row;
}

function updateDetectionCount() {
    const detectionMetric = document.getElementById('detectionsCount');
    if (detectionMetric) {
        const currentCount = parseInt(detectionMetric.textContent.replace(/,/g, ''));
        const newCount = currentCount + Math.floor(Math.random() * 3) + 1;
        
        animateNumberChange(detectionMetric, currentCount, newCount);
    }
}

function updateMetrics() {
    const accuracyMetric = document.getElementById('accuracyRate');
    if (accuracyMetric) {
        const currentAccuracy = parseFloat(accuracyMetric.textContent);
        const change = (Math.random() - 0.5) * 0.4;
        const newAccuracy = Math.max(90, Math.min(99.9, currentAccuracy + change));
        
        accuracyMetric.textContent = newAccuracy.toFixed(1) + '%';
        
        // Visual feedback
        if (Math.abs(change) > 0.2) {
            accuracyMetric.style.color = change > 0 ? 'var(--color-success)' : 'var(--color-error)';
            setTimeout(() => {
                accuracyMetric.style.color = '';
            }, 2000);
        }
    }
}

function animateNumberChange(element, fromValue, toValue) {
    const duration = 1200;
    const startTime = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.round(fromValue + (toValue - fromValue) * easeOut);
        element.textContent = currentValue.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    // Add visual emphasis
    element.style.color = 'var(--color-success)';
    element.style.transform = 'scale(1.05)';
    
    setTimeout(() => {
        element.style.color = '';
        element.style.transform = '';
    }, 1500);
    
    requestAnimationFrame(animate);
}

function simulateCameraStatusChange() {
    const cameraCards = document.querySelectorAll('.camera-card');
    if (cameraCards.length === 0) return;
    
    const randomCamera = cameraCards[Math.floor(Math.random() * cameraCards.length)];
    const statusIndicator = randomCamera.querySelector('.status');
    const isOnline = statusIndicator.classList.contains('online');
    
    // 10% chance of status change
    if (Math.random() < 0.1) {
        const cameraName = randomCamera.querySelector('h3').textContent;
        
        if (isOnline) {
            // Go offline
            statusIndicator.classList.remove('online');
            statusIndicator.classList.add('offline');
            statusIndicator.textContent = 'OFFLINE';
            randomCamera.classList.remove('online');
            randomCamera.classList.add('offline');
            
            updateCameraPreview(randomCamera, false);
            showNotification(`${cameraName} went offline`, 'warning');
        } else {
            // Come online
            statusIndicator.classList.remove('offline');
            statusIndicator.classList.add('online');
            statusIndicator.textContent = 'ONLINE';
            randomCamera.classList.remove('offline');
            randomCamera.classList.add('online');
            
            updateCameraPreview(randomCamera, true);
            showNotification(`${cameraName} is back online`, 'success');
        }
        
        // Flash effect
        randomCamera.style.borderColor = 'var(--color-warning)';
        randomCamera.style.boxShadow = '0 0 20px rgba(217, 119, 6, 0.5)';
        
        setTimeout(() => {
            randomCamera.style.borderColor = '';
            randomCamera.style.boxShadow = '';
        }, 3000);
        
        updateCameraStats();
    }
}

function updateCameraPreview(cameraCard, isOnline) {
    const preview = cameraCard.querySelector('.camera-preview');
    const icon = preview.querySelector('i');
    
    if (isOnline) {
        icon.className = 'fas fa-video';
        preview.classList.remove('offline');
    } else {
        icon.className = 'fas fa-video-slash';
        preview.classList.add('offline');
    }
}

function updateCameraStats() {
    const onlineCameras = document.querySelectorAll('.camera-card.online').length;
    const offlineCameras = document.querySelectorAll('.camera-card.offline').length;
    
    // Update stats in camera management section
    const onlineStatCard = document.querySelector('.camera-stats-grid .stat-card:first-child .stat-number');
    const offlineStatCard = document.querySelector('.camera-stats-grid .stat-card:nth-child(2) .stat-number');
    
    if (onlineStatCard) onlineStatCard.textContent = onlineCameras;
    if (offlineStatCard) offlineStatCard.textContent = offlineCameras;
    
    // Update header status
    const headerStatus = document.querySelector('.header-status .status.online');
    if (headerStatus) {
        headerStatus.textContent = `${onlineCameras} Online`;
    }
}

// ==============================================
// BUTTON ACTION SIMULATIONS
// ==============================================
function simulateRefresh(button) {
    const originalText = button.innerHTML;
    
    button.innerHTML = '<div class="loading-spinner"></div> Refreshing...';
    button.disabled = true;
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
        showNotification('Data refreshed successfully!', 'success');
        
        // Update timestamp
        window.lastUpdateTime = new Date().getTime();
    }, 2000);
}

function simulateExport(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
    button.disabled = true;
    
    showNotification('Preparing export...', 'info');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
        showNotification('Export completed! Download ready.', 'success');
        
        // Simulate file download
        simulateFileDownload('lpr-detections-export.csv');
    }, 3000);
}

function simulateReportGeneration(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    button.disabled = true;
    
    showNotification('Generating analytics report...', 'info');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
        showNotification('Report generated successfully!', 'success');
        
        simulateReportPreview();
    }, 4000);
}

function simulateDetailView(button) {
    const row = button.closest('tr');
    if (row) {
        const plateNumber = row.querySelector('strong').textContent;
        showNotification(`Opening detailed view for ${plateNumber}...`, 'info');
        
        setTimeout(() => {
            showDetailModal(plateNumber);
        }, 1000);
    }
}

function simulateEnhancement(button) {
    const row = button.closest('tr');
    if (row) {
        const plateNumber = row.querySelector('strong').textContent;
        const originalText = button.innerHTML;
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enhancing...';
        button.disabled = true;
        
        showNotification(`Enhancing image for ${plateNumber}...`, 'info');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
            showNotification('Image enhancement completed!', 'success');
            
            // Simulate confidence improvement
            const confidenceElement = row.querySelector('.confidence');
            if (confidenceElement) {
                const currentConfidence = parseInt(confidenceElement.textContent);
                const newConfidence = Math.min(99, currentConfidence + Math.floor(Math.random() * 8) + 3);
                
                confidenceElement.textContent = newConfidence + '%';
                confidenceElement.className = newConfidence >= 90 ? 'confidence high' : 'confidence medium';
                
                // Flash effect
                confidenceElement.style.background = 'var(--color-success-bg)';
                setTimeout(() => {
                    confidenceElement.style.background = '';
                }, 2000);
            }
        }, 3000);
    }
}

function simulateSave(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    button.disabled = true;
    
    // Validate form if in a form
    const form = button.closest('form');
    let isValid = true;
    
    if (form) {
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!validateField(field)) {
                isValid = false;
            }
        });
    }
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
        
        if (isValid) {
            showNotification('Settings saved successfully!', 'success');
            
            // Close modal if in modal
            const modal = button.closest('.modal');
            if (modal) {
                hideModal(modal);
            }
        } else {
            showNotification('Please fix the errors and try again', 'error');
        }
    }, 1500);
}

// ==============================================
// SEARCH FUNCTIONS
// ==============================================
function searchDetections(query) {
    const tableRows = document.querySelectorAll('#detectionsTable tr');
    let visibleCount = 0;
    
    tableRows.forEach(row => {
        const plateNumber = row.querySelector('td strong')?.textContent.toLowerCase() || '';
        const camera = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
        
        if (plateNumber.includes(query) || camera.includes(query) || query === '') {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    updateSearchResults(visibleCount, tableRows.length, 'detections');
}

function searchCameras(query) {
    const cameraCards = document.querySelectorAll('.camera-card');
    let visibleCount = 0;
    
    cameraCards.forEach(card => {
        const cameraName = card.querySelector('h3')?.textContent.toLowerCase() || '';
        const cameraId = card.querySelector('.camera-id')?.textContent.toLowerCase() || '';
        
        if (cameraName.includes(query) || cameraId.includes(query) || query === '') {
            card.style.display = '';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    updateSearchResults(visibleCount, cameraCards.length, 'cameras');
}

function updateSearchResults(visible, total, type) {
    const tableFooter = document.querySelector('.table-footer span');
    if (tableFooter && type === 'detections') {
        tableFooter.textContent = `Showing ${visible} of ${total} detections`;
    }
    
    // Announce results to screen readers
    const message = `${visible} of ${total} ${type} found`;
    announceToScreenReader(message);
}

// ==============================================
// ENHANCED FEATURES
// ==============================================
function initEnhancedFeatures() {
    initKeyboardShortcuts();
    initTooltips();
    initProgressiveLoading();
    initPerformanceMonitoring();
    addCustomAnimations();
    initScrollEffects();
}

function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Skip if user is typing in an input
        if (e.target.matches('input, textarea, select')) return;
        
        // Ctrl/Cmd + R for refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            const refreshBtn = document.getElementById('refreshBtn');
            if (refreshBtn && !refreshBtn.disabled) {
                refreshBtn.click();
            }
        }
        
        // Ctrl/Cmd + E for export
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            const exportBtn = document.querySelector('.btn-secondary[title*="Export"], .btn-secondary:contains("Export")');
            if (exportBtn && !exportBtn.disabled) {
                exportBtn.click();
            }
        }
        
        // Ctrl/Cmd + T for theme toggle
        if ((e.ctrlKey || e.metaKey) && e.key === 't') {
            e.preventDefault();
            toggleTheme();
        }
        
        // Escape to close notifications and modals
        if (e.key === 'Escape') {
            // Close notifications
            const notifications = document.querySelectorAll('.notification');
            notifications.forEach(n => n.remove());
            
            // Close modals
            const openModal = document.querySelector('.modal[style*="block"]');
            if (openModal) {
                hideModal(openModal);
            }
        }
        
        // Number keys for navigation (1-5)
        if (e.key >= '1' && e.key <= '5' && !e.ctrlKey && !e.metaKey) {
            const navLinks = document.querySelectorAll('.nav-link');
            const index = parseInt(e.key) - 1;
            if (navLinks[index]) {
                navLinks[index].click();
            }
        }
        
        // Arrow keys for navigation within sections
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            navigateWithArrows(e.key === 'ArrowRight');
        }
    });
}

function navigateWithArrows(forward) {
    const activeLink = document.querySelector('.nav-link.active');
    const allLinks = Array.from(document.querySelectorAll('.nav-link'));
    const currentIndex = allLinks.indexOf(activeLink);
    
    if (currentIndex !== -1) {
        const nextIndex = forward 
            ? (currentIndex + 1) % allLinks.length 
            : (currentIndex - 1 + allLinks.length) % allLinks.length;
        
        allLinks[nextIndex].click();
    }
}

function initTooltips() {
    // Enhanced tooltip system with better positioning
    const elementsWithTooltips = document.querySelectorAll('[title]');
    
    elementsWithTooltips.forEach(element => {
        const originalTitle = element.getAttribute('title');
        element.removeAttribute('title');
        element.setAttribute('data-tooltip', originalTitle);
        
        element.addEventListener('mouseenter', function(e) {
            showTooltip(e.target, originalTitle);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
        
        element.addEventListener('focus', function(e) {
            showTooltip(e.target, originalTitle);
        });
        
        element.addEventListener('blur', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    // Remove existing tooltip
    hideTooltip();
    
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = text;
    tooltip.setAttribute('role', 'tooltip');
    
    tooltip.style.cssText = `
        position: absolute;
        background: var(--color-text-primary);
        color: var(--color-text-inverse);
        padding: 0.5rem 0.75rem;
        border-radius: var(--radius-md);
        font-size: 0.75rem;
        white-space: nowrap;
        z-index: 4000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s ease;
        box-shadow: var(--shadow-lg);
        max-width: 200px;
        word-wrap: break-word;
        white-space: normal;
    `;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
    let top = rect.top - tooltipRect.height - 8;
    
    // Adjust if tooltip goes off screen
    if (left < 0) left = 8;
    if (left + tooltipRect.width > window.innerWidth) {
        left = window.innerWidth - tooltipRect.width - 8;
    }
    if (top < 0) {
        top = rect.bottom + 8;
    }
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    
    // Show tooltip
    setTimeout(() => tooltip.style.opacity = '1', 50);
    
    window.currentTooltip = tooltip;
}

function hideTooltip() {
    if (window.currentTooltip) {
        window.currentTooltip.style.opacity = '0';
        setTimeout(() => {
            if (window.currentTooltip) {
                window.currentTooltip.remove();
                window.currentTooltip = null;
            }
        }, 200);
    }
}

function initScrollEffects() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Scroll-based animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe cards for scroll animations
    document.querySelectorAll('.card, .metric-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        scrollObserver.observe(card);
    });
}

// ==============================================
// ACCESSIBILITY ENHANCEMENTS
// ==============================================
function initAccessibility() {
    // Enhanced focus management
    initFocusManagement();
    
    // Screen reader announcements
    initScreenReaderSupport();
    
    // Keyboard navigation improvements
    initKeyboardNavigation();
    
    // Color contrast validation
    validateColorContrast();
}

function initFocusManagement() {
    // Focus trap for modals
    document.addEventListener('keydown', function(e) {
        const openModal = document.querySelector('.modal[style*="block"]');
        if (openModal && e.key === 'Tab') {
            trapFocus(openModal, e);
        }
    });
    
    // Skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = 'Skip to main content';
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        background: var(--brand-primary);
        color: white;
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        z-index: 9999;
        transition: top 0.3s;
    `;
    
    skipLink.addEventListener('focus', function() {
        this.style.top = '6px';
    });
    
    skipLink.addEventListener('blur', function() {
        this.style.top = '-40px';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add id to main content for skip link
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.id = 'main-content';
        mainContent.setAttribute('tabindex', '-1');
    }
}

function trapFocus(modal, e) {
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    if (e.shiftKey) {
        if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
        }
    } else {
        if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
        }
    }
}

function initScreenReaderSupport() {
    // Create live region for announcements
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.style.cssText = `
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    `;
    document.body.appendChild(liveRegion);
    window.liveRegion = liveRegion;
    
    // Add ARIA labels to interactive elements
    document.querySelectorAll('button').forEach(button => {
        if (!button.getAttribute('aria-label') && !button.textContent.trim()) {
            const icon = button.querySelector('i');
            if (icon) {
                const iconClass = icon.className;
                let label = 'Button';
                
                if (iconClass.includes('fa-sync')) label = 'Refresh';
                else if (iconClass.includes('fa-download')) label = 'Download';
                else if (iconClass.includes('fa-eye')) label = 'View details';
                else if (iconClass.includes('fa-cog')) label = 'Configure';
                else if (iconClass.includes('fa-times')) label = 'Close';
                
                button.setAttribute('aria-label', label);
            }
        }
    });
}

function announceToScreenReader(message) {
    if (window.liveRegion) {
        window.liveRegion.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            window.liveRegion.textContent = '';
        }, 1000);
    }
}

function initKeyboardNavigation() {
    // Enhanced keyboard navigation for custom elements
    document.addEventListener('keydown', function(e) {
        const target = e.target;
        
        // Card navigation with arrow keys
        if (target.closest('.metric-card, .camera-card, .detection-item')) {
            handleCardNavigation(e, target);
        }
        
        // Table navigation
        if (target.closest('table')) {
            handleTableNavigation(e, target);
        }
    });
}

function handleCardNavigation(e, target) {
    const card = target.closest('.metric-card, .camera-card, .detection-item');
    const container = card.parentElement;
    const cards = Array.from(container.children);
    const currentIndex = cards.indexOf(card);
    
    let nextIndex = -1;
    
    switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
            nextIndex = (currentIndex + 1) % cards.length;
            break;
        case 'ArrowLeft':
        case 'ArrowUp':
            nextIndex = (currentIndex - 1 + cards.length) % cards.length;
            break;
        case 'Home':
            nextIndex = 0;
            break;
        case 'End':
            nextIndex = cards.length - 1;
            break;
    }
    
    if (nextIndex !== -1) {
        e.preventDefault();
        const nextCard = cards[nextIndex];
        const focusableElement = nextCard.querySelector('button, a, [tabindex="0"]') || nextCard;
        focusableElement.focus();
    }
}

function handleTableNavigation(e, target) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
        const row = target.closest('tr');
        const table = target.closest('table');
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        const currentIndex = rows.indexOf(row);
        
        let nextIndex = -1;
        
        if (e.key === 'ArrowDown' && currentIndex < rows.length - 1) {
            nextIndex = currentIndex + 1;
        } else if (e.key === 'ArrowUp' && currentIndex > 0) {
            nextIndex = currentIndex - 1;
        }
        
        if (nextIndex !== -1) {
            e.preventDefault();
            const nextRow = rows[nextIndex];
            const focusableElement = nextRow.querySelector('button, a') || nextRow;
            focusableElement.focus();
        }
    }
}

function validateColorContrast() {
    // Basic color contrast validation for development
    if (process?.env?.NODE_ENV === 'development') {
        console.log('Color contrast validation would run in development mode');
    }
}

// ==============================================
// UTILITY FUNCTIONS
// ==============================================
function simulateFileDownload(filename) {
    const link = document.createElement('a');
    const csvContent = [
        'Plate Number,Camera,Detection Time,Confidence,Vehicle Type',
        'ABC-1234,Main Entrance,2025-01-09 14:30:25,96%,Sedan',
        'XYZ-5678,Parking Lot A,2025-01-09 14:25:12,87%,SUV',
        'DEF-9012,Side Entrance,2025-01-09 14:22:08,92%,Truck'
    ].join('\n');
    
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function simulateReportPreview() {
    const reportWindow = window.open('', '_blank', 'width=900,height=700');
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    
    reportWindow.document.write(`
        <html>
            <head>
                <title>LPR Analytics Report</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        padding: 2rem; 
                        background: ${currentTheme === 'dark' ? '#1e293b' : '#ffffff'};
                        color: ${currentTheme === 'dark' ? '#f8fafc' : '#1e293b'};
                    }
                    .header { border-bottom: 2px solid #2563eb; padding-bottom: 1rem; margin-bottom: 2rem; }
                    .metric { background: ${currentTheme === 'dark' ? '#334155' : '#f8fafc'}; padding: 1rem; margin: 1rem 0; border-radius: 8px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🛡️ LPR System Analytics Report</h1>
                    <p>Generated on: ${new Date().toLocaleDateString()}</p>
                </div>
                <div class="metric">
                    <h2>📊 Summary Statistics</h2>
                    <p><strong>Total Detections:</strong> 1,847</p>
                    <p><strong>Average Confidence:</strong> 94.2%</p>
                    <p><strong>System Uptime:</strong> 99.9%</p>
                    <p><strong>Active Cameras:</strong> 24</p>
                </div>
                <div class="metric">
                    <h2>📈 Performance Metrics</h2>
                    <p><strong>Processing Speed:</strong> 47ms average</p>
                    <p><strong>Peak Detection Hours:</strong> 8:00 AM - 10:00 AM</p>
                    <p><strong>Most Active Camera:</strong> Main Entrance (847 detections)</p>
                </div>
                <p><em>This is a simulated report preview demonstrating the LPR system's reporting capabilities.</em></p>
            </body>
        </html>
    `);
}

function showDetailModal(plateNumber) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-labelledby', 'detail-modal-title');
    modal.setAttribute('aria-modal', 'true');
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="detail-modal-title">Detection Details - ${plateNumber}</h2>
                <button class="modal-close" aria-label="Close modal">&times;</button>
            </div>
            <div class="modal-body">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
                    <div>
                        <h3>🚗 Vehicle Information</h3>
                        <p><strong>Plate Number:</strong> ${plateNumber}</p>
                        <p><strong>Vehicle Type:</strong> Sedan</p>
                        <p><strong>Color:</strong> Silver</p>
                        <p><strong>Make/Model:</strong> Honda Accord</p>
                    </div>
                    <div>
                        <h3>📋 Detection Details</h3>
                        <p><strong>Camera:</strong> Main Entrance</p>
                        <p><strong>Timestamp:</strong> ${new Date().toLocaleString()}</p>
                        <p><strong>Confidence:</strong> <span class="confidence high">96%</span></p>
                        <p><strong>Processing Time:</strong> 47ms</p>
                    </div>
                </div>
                <div>
                    <h3>🖼️ Image Preview</h3>
                    <div style="background: var(--color-surface-secondary); border: 2px dashed var(--color-border); height: 200px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-md); color: var(--color-text-tertiary);">
                        <i class="fas fa-image" style="font-size: 3rem; margin-right: 1rem;"></i>
                        <span>Image preview would appear here</span>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline">
                    <i class="fas fa-download"></i> Download Image
                </button>
                <button class="btn btn-primary">
                    <i class="fas fa-magic"></i> Enhance Image
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add close handlers
    const closeBtn = modal.querySelector('.modal-close');
    closeBtn.addEventListener('click', () => {
        modal.remove();
        announceToScreenReader('Modal closed');
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
            announceToScreenReader('Modal closed');
        }
    });
    
    // Focus management
    setTimeout(() => closeBtn.focus(), 100);
}

// ==============================================
// NOTIFICATION SYSTEM
// ==============================================
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications of the same type to prevent spam
    const existingNotifications = document.querySelectorAll(`.notification-${type}`);
    existingNotifications.forEach(n => n.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" aria-label="Close notification">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Close button functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        dismissNotification(notification);
    });
    
    // Auto-remove after duration
    const timeoutId = setTimeout(() => {
        if (notification.parentElement) {
            dismissNotification(notification);
        }
    }, duration);
    
    // Click anywhere on notification to dismiss
    notification.addEventListener('click', (e) => {
        if (e.target !== closeBtn) {
            clearTimeout(timeoutId);
            dismissNotification(notification);
        }
    });
    
    // Announce to screen readers
    announceToScreenReader(`${type}: ${message}`);
}

function dismissNotification(notification) {
    notification.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 300);
}

function getNotificationIcon(type) {
    const icons = {
        'info': 'fa-info-circle',
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-triangle',
        'error': 'fa-times-circle'
    };
    return icons[type] || icons['info'];
}

// ==============================================
// PERFORMANCE MONITORING
// ==============================================
function initPerformanceMonitoring() {
    // Monitor page load performance
    window.addEventListener('load', () => {
        const navigation = performance.getEntriesByType('navigation')[0];
        const loadTime = navigation.loadEventEnd - navigation.fetchStart;
        
        console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
        
        if (loadTime > 3000) {
            showNotification('Page load time is slower than expected', 'warning');
        }
        
        // Monitor memory usage if available
        if ('memory' in performance) {
            monitorMemoryUsage();
        }
    });
    
    // Monitor long tasks
    if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.duration > 50) {
                    console.warn(`Long task detected: ${entry.duration}ms`);
                }
            }
        });
        observer.observe({ entryTypes: ['longtask'] });
    }
}

function monitorMemoryUsage() {
    setInterval(() => {
        const memInfo = performance.memory;
        const usedMB = memInfo.usedJSHeapSize / 1024 / 1024;
        
        if (usedMB > 100) { // 100MB threshold
            console.warn(`High memory usage detected: ${usedMB.toFixed(2)}MB`);
        }
    }, 30000);
}

// ==============================================
// PROGRESSIVE LOADING
// ==============================================
function initProgressiveLoading() {
    // Simulate loading states for heavy content
    const heavyElements = document.querySelectorAll('.chart-placeholder');
    
    heavyElements.forEach((element, index) => {
        // Initial loading state
        element.style.opacity = '0.6';
        element.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Loading chart data...</p>
        `;
        
        // Simulate data loading
        setTimeout(() => {
            element.style.opacity = '1';
            element.innerHTML = `
                <i class="fas fa-chart-line" style="font-size: 3rem; color: var(--color-text-tertiary); margin-bottom: 1rem;"></i>
                <p>Chart visualization would appear here</p>
            `;
            
            // Add shimmer effect
            element.style.background = 'linear-gradient(90deg, var(--color-surface) 25%, var(--color-surface-hover) 50%, var(--color-surface) 75%)';
            element.style.backgroundSize = '200% 100%';
            element.style.animation = 'shimmer 2s infinite';
        }, 1000 + index * 500);
    });
}

// ==============================================
// CUSTOM ANIMATIONS
// ==============================================
function addCustomAnimations() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .loading-spinner {
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}// Enhanced LPR Dashboard with Theme System
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initThemeSystem();
    initNavigation();
    initSettingsTabs();
    initModals();
    initInteractiveElements();
    initRealTimeSimulation();
    initEnhancedFeatures();
    initAccessibility();
    
    // Show welcome notification after theme is set
    setTimeout(() => {
        showNotification('Welcome to LPR System Pro! All systems operational.', 'success');
    }, 1000);
});

// ==============================================
// THEME SYSTEM
// ==============================================
function initThemeSystem() {
    // Create theme toggle button
    createThemeToggle();
    
    // Load saved theme or detect system preference
    const savedTheme = localStorage.getItem('lpr-theme');
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const initialTheme = savedTheme || systemTheme;
    
    // Apply initial theme
    setTheme(initialTheme);
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('lpr-theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
}

function createThemeToggle() {
    const themeToggle = document.createElement('button');
    themeToggle.className = 'theme-toggle';
    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    themeToggle.setAttribute('aria-label', 'Toggle dark mode');
    themeToggle.setAttribute('title', 'Toggle theme');
    
    themeToggle.addEventListener('click', toggleTheme);
    
    document.body.appendChild(themeToggle);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('lpr-theme', theme);
    
    // Update toggle icon
    const themeToggle = document.querySelector('.theme-toggle i');
    if (themeToggle) {
        themeToggle.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
    
    // Update toggle aria-label
    const toggleButton = document.querySelector('.theme-toggle');
    if (toggleButton) {
        toggleButton.setAttribute('aria-label', 
            theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
        );
    }
    
    // Trigger theme change event for other components
    document.dispatchEvent(new CustomEvent('themeChange', { detail: { theme } }));
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    
    // Show feedback
    showNotification(
        `Switched to ${newTheme} mode`, 
        'info', 
        2000
    );
}

// ==============================================
// ENHANCED NAVIGATION
// ==============================================
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.content-section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and sections
            navLinks.forEach(l => l.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding section with animation
            const targetSection = this.getAttribute('data-section');
            const section = document.getElementById(targetSection);
            if (section) {
                section.classList.add('active');
                
                // Trigger section-specific animations
                triggerSectionAnimations(targetSection);
                
                // Update URL without refresh
                updateURL(targetSection);
            }
            
            // Update page title
            updatePageTitle(this.textContent.trim());
        });
    });
    
    // Handle browser back/forward
    window.addEventListener('popstate', handlePopState);
    
    // Load initial section from URL
    loadSectionFromURL();
}

function triggerSectionAnimations(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    
    // Add stagger animation to cards
    const cards = section.querySelectorAll('.card, .metric-card, .camera-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 50);
    });
}

function updatePageTitle(sectionName) {
    document.title = `LPR System Pro - ${sectionName}`;
}

function updateURL(section) {
    const newURL = `${window.location.pathname}#${section}`;
    history.pushState({ section }, '', newURL);
}

function handlePopState(event) {
    const section = event.state?.section || window.location.hash.slice(1) || 'dashboard';
    activateSection(section);
}

function loadSectionFromURL() {
    const hash = window.location.hash.slice(1);
    if (hash) {
        activateSection(hash);
    }
}

function activateSection(sectionId) {
    const navLink = document.querySelector(`[data-section="${sectionId}"]`);
    if (navLink) {
        navLink.click();
    }
}

// ==============================================
// SETTINGS TABS
// ==============================================
function initSettingsTabs() {
    const settingsNavLinks = document.querySelectorAll('.settings-nav-link');
    const settingsTabs = document.querySelectorAll('.settings-tab');
    
    settingsNavLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all nav links and tabs
            settingsNavLinks.forEach(l => l.classList.remove('active'));
            settingsTabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding tab
            const targetTab = this.getAttribute('data-tab');
            const tab = document.querySelector(`[data-tab="${targetTab}"].settings-tab`);
            if (tab) {
                tab.classList.add('active');
            }
        });
    });
}

// ==============================================
// ENHANCED MODAL SYSTEM
// ==============================================
function initModals() {
    const modal = document.getElementById('cameraModal');
    const modalClose = document.querySelector('.modal-close');
    const addCameraBtn = document.getElementById('addCameraBtn');
    
    // Open modal when clicking "Add Camera"
    if (addCameraBtn) {
        addCameraBtn.addEventListener('click', function() {
            showModal(modal, 'Add New Camera');
            clearModalForm();
        });
    }
    
    // Configure buttons (dynamically added)
    document.addEventListener('click', function(e) {
        if (e.target.matches('.camera-card .btn-primary') && 
            e.target.textContent.includes('Configure')) {
            const cameraCard = e.target.closest('.camera-card');
            const cameraName = cameraCard.querySelector('h3').textContent;
            showModal(modal, `Configure ${cameraName}`);
            populateModalForm(cameraCard);
        }
    });
    
    // Close modal
    if (modalClose) {
        modalClose.addEventListener('click', function() {
            hideModal(modal);
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            hideModal(e.target);
        }
    });
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal[style*="block"]');
            if (openModal) {
                hideModal(openModal);
            }
        }
    });
}

function showModal(modal, title) {
    if (modal) {
        const modalTitle = modal.querySelector('.modal-header h2');
        if (modalTitle) modalTitle.textContent = title;
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Focus management
        const firstInput = modal.querySelector('input, button');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 300);
        }
        
        // Trap focus in modal
        trapFocus(modal);
    }
}

function hideModal(modal) {
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Return focus to trigger element
        const activeElement = document.activeElement;
        if (activeElement && activeElement !== document.body) {
            activeElement.blur();
        }
    }
}

function clearModalForm() {
    const modal = document.getElementById('cameraModal');
    const inputs = modal.querySelectorAll('input');
    inputs.forEach(input => input.value = '');
}

function populateModalForm(cameraCard) {
    const modal = document.getElementById('cameraModal');
    const cameraName = cameraCard.querySelector('h3').textContent;
    const cameraIP = cameraCard.querySelector('p').textContent.split(' • ')[0];
    
    const nameInput = modal.querySelector('input[placeholder*="camera name"]');
    const ipInput = modal.querySelector('input[placeholder*="192.168"]');
    
    if (nameInput) nameInput.value = cameraName;
    if (ipInput) ipInput.value = cameraIP;
}

// ==============================================
// INTERACTIVE ELEMENTS
// ==============================================
function initInteractiveElements() {
    // Range slider for confidence threshold
    initRangeSliders();
    
    // Enhanced search functionality
    initSearchFunctionality();
    
    // Enhanced button interactions
    initButtonInteractions();
    
    // Camera feed interactions
    initCameraInteractions();
    
    // Detection items
    initDetectionInteractions();
    
    // Auto-refresh toggle
    initAutoRefreshToggle();
    
    // Form enhancements
    initFormEnhancements();
}

function initRangeSliders() {
    const rangeSliders = document.querySelectorAll('.form-range');
    
    rangeSliders.forEach(slider => {
        const updateValue = () => {
            const value = slider.value;
            const min = slider.min || 0;
            const max = slider.max || 100;
            const percentage = ((value - min) / (max - min)) * 100;
            
            // Update visual feedback
            slider.style.background = `linear-gradient(to right, var(--brand-primary) 0%, var(--