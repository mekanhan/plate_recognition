// Interactive UI Prototype JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Navigation functionality
    initNavigation();
    
    // Settings tabs functionality
    initSettingsTabs();
    
    // Modal functionality
    initModals();
    
    // Interactive elements
    initInteractiveElements();
    
    // Simulation of real-time updates
    initRealTimeSimulation();
});

// Navigation between sections
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
            
            // Show corresponding section
            const targetSection = this.getAttribute('data-section');
            const section = document.getElementById(targetSection);
            if (section) {
                section.classList.add('active');
            }
        });
    });
}

// Settings tabs functionality
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

// Modal functionality
function initModals() {
    const modal = document.getElementById('cameraModal');
    const modalClose = document.querySelector('.modal-close');
    const addCameraBtn = document.querySelector('.btn-primary');
    const configureButtons = document.querySelectorAll('.camera-actions .btn:first-child');
    
    // Open modal when clicking "Add Camera" or "Configure"
    if (addCameraBtn) {
        addCameraBtn.addEventListener('click', function() {
            if (this.innerHTML.includes('Add Camera')) {
                showModal(modal);
            }
        });
    }
    
    configureButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            showModal(modal);
        });
    });
    
    // Close modal
    if (modalClose) {
        modalClose.addEventListener('click', function() {
            hideModal(modal);
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            hideModal(modal);
        }
    });
}

function showModal(modal) {
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function hideModal(modal) {
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Interactive elements
function initInteractiveElements() {
    // Range slider for confidence threshold
    const rangeSlider = document.querySelector('.form-range');
    const rangeValue = document.querySelector('.range-value');
    
    if (rangeSlider && rangeValue) {
        rangeSlider.addEventListener('input', function() {
            rangeValue.textContent = this.value + '%';
        });
    }
    
    // Search functionality simulation
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('.detections-table tbody tr');
            
            tableRows.forEach(row => {
                const plateNumber = row.querySelector('td:first-child').textContent.toLowerCase();
                if (plateNumber.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Button interactions
    const buttons = document.querySelectorAll('.btn:not(.btn-disabled)');
    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Visual feedback for button clicks
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Simulate actions based on button content
            const btnText = this.textContent.trim();
            if (btnText.includes('Refresh')) {
                simulateRefresh();
            } else if (btnText.includes('Export')) {
                simulateExport();
            } else if (btnText.includes('Generate Report')) {
                simulateReportGeneration();
            } else if (btnText.includes('View')) {
                simulateDetailView();
            } else if (btnText.includes('Enhance')) {
                simulateEnhancement();
            }
        });
    });
    
    // Camera feed interactions
    const cameraFeeds = document.querySelectorAll('.camera-feed');
    cameraFeeds.forEach(feed => {
        feed.addEventListener('click', function() {
            const placeholder = this.querySelector('.camera-placeholder');
            placeholder.style.borderColor = '#667eea';
            placeholder.style.backgroundColor = '#f0f4ff';
            
            setTimeout(() => {
                placeholder.style.borderColor = '';
                placeholder.style.backgroundColor = '';
            }, 1000);
        });
    });
    
    // Detection items click simulation
    const detectionItems = document.querySelectorAll('.detection-item');
    detectionItems.forEach(item => {
        item.addEventListener('click', function() {
            this.style.backgroundColor = '#f0f4ff';
            setTimeout(() => {
                this.style.backgroundColor = '';
            }, 500);
        });
    });
}

// Real-time simulation
function initRealTimeSimulation() {
    // Simulate new detections
    setInterval(() => {
        updateDetectionCount();
        addNewDetection();
    }, 10000); // Every 10 seconds
    
    // Simulate metric updates
    setInterval(() => {
        updateMetrics();
    }, 5000); // Every 5 seconds
    
    // Simulate camera status changes
    setInterval(() => {
        simulateCameraStatusChange();
    }, 30000); // Every 30 seconds
}

function updateDetectionCount() {
    const detectionMetric = document.querySelector('.metric-card:nth-child(2) .metric-value');
    if (detectionMetric) {
        const currentCount = parseInt(detectionMetric.textContent.replace(',', ''));
        const newCount = currentCount + Math.floor(Math.random() * 5) + 1;
        detectionMetric.textContent = newCount.toLocaleString();
        
        // Add animation
        detectionMetric.style.color = '#27ae60';
        setTimeout(() => {
            detectionMetric.style.color = '';
        }, 1000);
    }
}

function addNewDetection() {
    const detectionsList = document.querySelector('.detections-list');
    const detectionTable = document.querySelector('.detections-table tbody');
    
    if (detectionsList || detectionTable) {
        const plateNumbers = ['ABC-1234', 'XYZ-5678', 'DEF-9012', 'GHI-3456', 'JKL-7890', 'MNO-2345'];
        const cameras = ['Main Entrance', 'Parking Lot A', 'Side Entrance', 'Exit Gate'];
        const vehicleTypes = ['Sedan', 'SUV', 'Truck', 'Motorcycle'];
        
        const randomPlate = plateNumbers[Math.floor(Math.random() * plateNumbers.length)];
        const randomCamera = cameras[Math.floor(Math.random() * cameras.length)];
        const randomVehicle = vehicleTypes[Math.floor(Math.random() * vehicleTypes.length)];
        const randomConfidence = 75 + Math.floor(Math.random() * 25);
        const now = new Date();
        
        // Add to recent detections list if visible
        if (detectionsList && document.getElementById('dashboard').classList.contains('active')) {
            const newDetection = createDetectionItem(randomPlate, randomCamera, 'Just now', randomConfidence);
            detectionsList.insertBefore(newDetection, detectionsList.firstChild);
            
            // Remove last item if more than 3
            const items = detectionsList.querySelectorAll('.detection-item');
            if (items.length > 3) {
                detectionsList.removeChild(items[items.length - 1]);
            }
            
            // Highlight new detection
            newDetection.style.backgroundColor = '#e8f5e8';
            setTimeout(() => {
                newDetection.style.backgroundColor = '';
            }, 3000);
        }
        
        // Add to detections table if visible
        if (detectionTable && document.getElementById('detections').classList.contains('active')) {
            const newRow = createDetectionTableRow(randomPlate, randomCamera, now, randomConfidence, randomVehicle);
            detectionTable.insertBefore(newRow, detectionTable.firstChild);
            
            // Highlight new row
            newRow.style.backgroundColor = '#e8f5e8';
            setTimeout(() => {
                newRow.style.backgroundColor = '';
            }, 3000);
        }
    }
}

function createDetectionItem(plateNumber, camera, timestamp, confidence) {
    const item = document.createElement('div');
    item.className = 'detection-item';
    
    const confidenceClass = confidence >= 90 ? 'high' : confidence >= 80 ? 'medium' : 'low';
    
    item.innerHTML = `
        <div class="detection-thumbnail">
            <i class="fas fa-car"></i>
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
    
    return item;
}

function createDetectionTableRow(plateNumber, camera, timestamp, confidence, vehicleType) {
    const row = document.createElement('tr');
    const confidenceClass = confidence >= 90 ? 'high' : confidence >= 80 ? 'medium' : 'low';
    
    row.innerHTML = `
        <td><strong>${plateNumber}</strong></td>
        <td>${camera}</td>
        <td>${timestamp.toLocaleString()}</td>
        <td><span class="confidence ${confidenceClass}">${confidence}%</span></td>
        <td>${vehicleType}</td>
        <td>
            <button class="btn btn-sm">View</button>
            <button class="btn btn-sm btn-outline">Enhance</button>
        </td>
    `;
    
    return row;
}

function updateMetrics() {
    // Update accuracy rate slightly
    const accuracyMetric = document.querySelector('.metric-card:nth-child(3) .metric-value');
    if (accuracyMetric) {
        const currentAccuracy = parseFloat(accuracyMetric.textContent);
        const change = (Math.random() - 0.5) * 0.2; // Random change between -0.1 and +0.1
        const newAccuracy = Math.max(90, Math.min(99, currentAccuracy + change));
        accuracyMetric.textContent = newAccuracy.toFixed(1) + '%';
    }
}

function simulateCameraStatusChange() {
    const cameraCards = document.querySelectorAll('.camera-card');
    if (cameraCards.length > 0) {
        const randomCamera = cameraCards[Math.floor(Math.random() * cameraCards.length)];
        const statusIndicator = randomCamera.querySelector('.status-indicator');
        const currentStatus = statusIndicator.classList.contains('online') ? 'online' : 'offline';
        
        // 10% chance of status change
        if (Math.random() < 0.1) {
            if (currentStatus === 'online') {
                statusIndicator.classList.remove('online');
                statusIndicator.classList.add('offline');
            } else {
                statusIndicator.classList.remove('offline');
                statusIndicator.classList.add('online');
            }
            
            // Flash the camera card to indicate change
            randomCamera.style.borderColor = '#ffc107';
            setTimeout(() => {
                randomCamera.style.borderColor = '';
            }, 2000);
        }
    }
}

// Simulation functions for user interactions
function simulateRefresh() {
    showNotification('Refreshing data...', 'info');
    
    // Add loading animation
    const refreshBtn = event.target;
    const originalText = refreshBtn.innerHTML;
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    refreshBtn.disabled = true;
    
    setTimeout(() => {
        refreshBtn.innerHTML = originalText;
        refreshBtn.disabled = false;
        showNotification('Data refreshed successfully!', 'success');
    }, 2000);
}

function simulateExport() {
    showNotification('Preparing export...', 'info');
    
    setTimeout(() => {
        showNotification('Export completed! Download should start automatically.', 'success');
    }, 3000);
}

function simulateReportGeneration() {
    showNotification('Generating analytics report...', 'info');
    
    setTimeout(() => {
        showNotification('Report generated successfully!', 'success');
    }, 4000);
}

function simulateDetailView() {
    showNotification('Opening detailed view...', 'info');
}

function simulateEnhancement() {
    showNotification('Enhancing image quality...', 'info');
    
    setTimeout(() => {
        showNotification('Image enhancement completed!', 'success');
    }, 3000);
}

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(n => n.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">&times;</button>
    `;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 3000;
        display: flex;
        align-items: center;
        gap: 15px;
        max-width: 400px;
        animation: slideIn 0.3s ease;
    `;
    
    // Add notification to page
    document.body.appendChild(notification);
    
    // Close button functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
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

function getNotificationColor(type) {
    const colors = {
        'info': '#3498db',
        'success': '#27ae60',
        'warning': '#f39c12',
        'error': '#e74c3c'
    };
    return colors[type] || colors['info'];
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 10px;
        flex: 1;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        font-size: 1.2rem;
        cursor: pointer;
        opacity: 0.8;
        transition: opacity 0.3s ease;
    }
    
    .notification-close:hover {
        opacity: 1;
    }
`;
document.head.appendChild(style);

// Initialize tooltip functionality
function initTooltips() {
    const elementsWithTooltips = document.querySelectorAll('[data-tooltip]');
    
    elementsWithTooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            
            tooltip.style.cssText = `
                position: absolute;
                background: #2c3e50;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 0.8rem;
                white-space: nowrap;
                z-index: 4000;
                pointer-events: none;
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
            
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

// Initialize tooltips
initTooltips();