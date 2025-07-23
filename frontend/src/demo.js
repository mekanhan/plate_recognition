/**
 * Demo Enhancement Script
 * Adds interactive demo functionality to showcase the reorganized frontend
 */

// Wait for app to initialize
document.addEventListener('DOMContentLoaded', () => {
    // Add demo enhancements after a short delay
    setTimeout(() => {
        addDemoEnhancements();
    }, 2000);
});

function addDemoEnhancements() {
    // Add demo banner
    addDemoBanner();
    
    // Enhance mock data with realistic updates
    startMockDataUpdates();
    
    // Add demo-specific event handlers
    addDemoEventHandlers();
    
    console.log('🎯 Demo enhancements loaded! Try the following:');
    console.log('• Navigate between Dashboard and Cameras pages');
    console.log('• Toggle dark mode with the moon/sun icon');
    console.log('• Collapse the sidebar with the hamburger menu');
    console.log('• Click "Add Camera" to see the 4-step wizard');
    console.log('• Try the notification dropdown and user menu');
}

// function addDemoBanner() {
//     const banner = document.createElement('div');
//     banner.id = 'demo-banner';
//     banner.innerHTML = `
//         <div style="
//             position: fixed;
//             top: 0;
//             left: 0;
//             right: 0;
//             background: linear-gradient(90deg, #4299e1, #63b3ed);
//             color: white;
//             padding: 8px 16px;
//             text-align: center;
//             font-size: 14px;
//             z-index: 9999;
//             box-shadow: 0 2px 4px rgba(0,0,0,0.1);
//         ">
//             <strong>🎯 DEMO MODE</strong> - Reorganized Frontend Architecture Showcase
//             <button onclick="this.parentElement.parentElement.remove()" style="
//                 background: rgba(255,255,255,0.2);
//                 border: none;
//                 color: white;
//                 padding: 4px 8px;
//                 margin-left: 16px;
//                 border-radius: 4px;
//                 cursor: pointer;
//                 font-size: 12px;
//             ">×</button>
//         </div>
//     `;
    
//     document.body.appendChild(banner);
    
//     // Adjust body padding to account for banner
//     document.body.style.paddingTop = '40px';
// }

function startMockDataUpdates() {
    // Simulate real-time metric updates
    setInterval(() => {
        updateMetrics();
    }, 5000);
    
    // Simulate camera status changes
    setInterval(() => {
        updateCameraStatuses();
    }, 10000);
    
    // Simulate new detections
    setInterval(() => {
        addNewDetection();
    }, 15000);
}

function updateMetrics() {
    if (window.mockMetrics) {
        // Simulate detection count increases
        window.mockMetrics.detectionsToday += Math.floor(Math.random() * 5) + 1;
        
        // Occasionally change accuracy rate
        if (Math.random() < 0.3) {
            window.mockMetrics.accuracyRate += (Math.random() - 0.5) * 0.5;
            window.mockMetrics.accuracyRate = Math.max(90, Math.min(99, window.mockMetrics.accuracyRate));
            window.mockMetrics.accuracyRate = Math.round(window.mockMetrics.accuracyRate * 10) / 10;
        }
        
        // Trigger refresh if dashboard is active
        if (window.lprApp && window.lprApp.getCurrentPage() === 'dashboard') {
            const dashboard = window.lprApp.getComponent('pages')?.dashboard;
            if (dashboard && typeof dashboard.updateMetrics === 'function') {
                dashboard.updateMetrics();
            }
        }
    }
}

function updateCameraStatuses() {
    if (window.mockCameras && Math.random() < 0.4) {
        // Randomly change a camera status
        const camera = window.mockCameras[Math.floor(Math.random() * window.mockCameras.length)];
        const statuses = ['online', 'offline', 'warning'];
        const currentIndex = statuses.indexOf(camera.status);
        
        // Change to a different status
        const newStatuses = statuses.filter((_, i) => i !== currentIndex);
        camera.status = newStatuses[Math.floor(Math.random() * newStatuses.length)];
        camera.lastSeen = new Date();
        
        // Show notification for status change
        if (window.lprApp) {
            const header = window.lprApp.getComponent('header');
            if (header && typeof header.addNotification === 'function') {
                header.addNotification({
                    type: camera.status === 'offline' ? 'warning' : 'info',
                    title: 'Camera Status Changed',
                    message: `${camera.name} is now ${camera.status}`
                });
            }
        }
    }
}

function addNewDetection() {
    if (window.mockDetections && Math.random() < 0.6) {
        const plates = ['GHI-789', 'JKL-012', 'MNO-345', 'PQR-678', 'STU-901'];
        const cameras = ['Entrance Gate', 'Parking Lot A', 'Loading Dock', 'Side Entrance'];
        const vehicles = ['Sedan', 'SUV', 'Truck', 'Van', 'Motorcycle'];
        const colors = ['Blue', 'White', 'Black', 'Red', 'Silver', 'Gray'];
        
        const newDetection = {
            id: Date.now().toString(),
            plate: plates[Math.floor(Math.random() * plates.length)],
            camera: cameras[Math.floor(Math.random() * cameras.length)],
            timestamp: new Date(),
            confidence: Math.round((Math.random() * 20 + 80) * 10) / 10, // 80-100%
            vehicle: vehicles[Math.floor(Math.random() * vehicles.length)],
            color: colors[Math.floor(Math.random() * colors.length)]
        };
        
        // Add to beginning of array and limit to 10 recent detections
        window.mockDetections.unshift(newDetection);
        window.mockDetections = window.mockDetections.slice(0, 10);
        
        // Update metrics
        if (window.mockMetrics) {
            window.mockMetrics.detectionsToday++;
        }
        
        // Show toast notification
        showDemoToast(`New detection: ${newDetection.plate}`, 'info');
    }
}

function addDemoEventHandlers() {
    // Add keyboard shortcuts info
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'h':
                    e.preventDefault();
                    showKeyboardShortcuts();
                    break;
                case 'd':
                    e.preventDefault();
                    toggleDemoInfo();
                    break;
            }
        }
    });
    
    // Add context menu for demo info
    document.addEventListener('contextmenu', (e) => {
        if (e.ctrlKey) {
            e.preventDefault();
            showDemoContextMenu(e.clientX, e.clientY);
        }
    });
}

function showKeyboardShortcuts() {
    const shortcuts = `
        <h3>🎯 Demo Keyboard Shortcuts</h3>
        <div style="text-align: left; margin: 16px 0;">
            <strong>Navigation:</strong><br>
            • Ctrl+R - Refresh data<br>
            • Ctrl+N - New camera<br>
            • ESC - Close modals<br><br>
            
            <strong>Demo Features:</strong><br>
            • Ctrl+H - Show this help<br>
            • Ctrl+D - Toggle demo info<br>
            • Ctrl+Right-click - Demo menu<br><br>
            
            <strong>UI Features:</strong><br>
            • Click sidebar items to navigate<br>
            • Toggle dark mode with moon/sun icon<br>
            • Collapse sidebar with hamburger menu<br>
            • Try the notification dropdown<br>
        </div>
    `;
    
    showDemoModal('Keyboard Shortcuts', shortcuts);
}

function toggleDemoInfo() {
    const existing = document.getElementById('demo-info-panel');
    if (existing) {
        existing.remove();
        return;
    }
    
    const panel = document.createElement('div');
    panel.id = 'demo-info-panel';
    panel.innerHTML = `
        <div style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--bg-primary, #fff);
            border: 1px solid var(--border-color, #ccc);
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            max-width: 300px;
            font-size: 14px;
        ">
            <h4 style="margin: 0 0 12px 0; color: var(--text-primary, #333);">📊 Demo Statistics</h4>
            <div id="demo-stats" style="color: var(--text-secondary, #666);"></div>
            <button onclick="this.parentElement.parentElement.remove()" style="
                position: absolute;
                top: 8px;
                right: 8px;
                background: none;
                border: none;
                font-size: 16px;
                cursor: pointer;
                color: var(--text-muted, #999);
            ">×</button>
        </div>
    `;
    
    document.body.appendChild(panel);
    updateDemoStats();
    
    // Update stats every 2 seconds
    const interval = setInterval(updateDemoStats, 2000);
    panel.addEventListener('remove', () => clearInterval(interval));
}

function updateDemoStats() {
    const statsEl = document.getElementById('demo-stats');
    if (statsEl && window.mockMetrics && window.mockCameras) {
        const onlineCameras = window.mockCameras.filter(c => c.status === 'online').length;
        const offlineCameras = window.mockCameras.filter(c => c.status === 'offline').length;
        
        statsEl.innerHTML = `
            <div>📹 Cameras: ${onlineCameras} online, ${offlineCameras} offline</div>
            <div>🔍 Detections: ${window.mockMetrics.detectionsToday}</div>
            <div>📊 Accuracy: ${window.mockMetrics.accuracyRate}%</div>
            <div>⚠️ Alerts: ${window.mockMetrics.activeAlerts}</div>
            <div style="margin-top: 8px; font-size: 12px; opacity: 0.7;">
                Updates every 5s
            </div>
        `;
    }
}

function showDemoContextMenu(x, y) {
    const menu = document.createElement('div');
    menu.innerHTML = `
        <div style="
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            background: var(--bg-primary, #fff);
            border: 1px solid var(--border-color, #ccc);
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            z-index: 10000;
            padding: 8px 0;
            min-width: 180px;
        ">
            <div onclick="showKeyboardShortcuts(); this.parentElement.parentElement.remove();" style="
                padding: 8px 16px;
                cursor: pointer;
                transition: background 0.15s;
            " onmouseover="this.style.background='var(--bg-secondary, #f5f5f5)'" onmouseout="this.style.background='transparent'">
                🎯 Show Demo Help
            </div>
            <div onclick="toggleDemoInfo(); this.parentElement.parentElement.remove();" style="
                padding: 8px 16px;
                cursor: pointer;
                transition: background 0.15s;
            " onmouseover="this.style.background='var(--bg-secondary, #f5f5f5)'" onmouseout="this.style.background='transparent'">
                📊 Toggle Demo Stats
            </div>
            <div onclick="window.location.reload();" style="
                padding: 8px 16px;
                cursor: pointer;
                transition: background 0.15s;
            " onmouseover="this.style.background='var(--bg-secondary, #f5f5f5)'" onmouseout="this.style.background='transparent'">
                🔄 Reload Demo
            </div>
        </div>
    `;
    
    document.body.appendChild(menu);
    
    setTimeout(() => {
        document.addEventListener('click', () => menu.remove(), { once: true });
    }, 100);
}

function showDemoModal(title, content) {
    const modal = document.createElement('div');
    modal.innerHTML = `
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        " onclick="this.parentElement.remove()">
            <div style="
                background: var(--bg-primary, #fff);
                border-radius: 8px;
                padding: 24px;
                max-width: 500px;
                max-height: 70vh;
                overflow-y: auto;
                margin: 20px;
            " onclick="event.stopPropagation()">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                ">
                    <h2 style="margin: 0; color: var(--text-primary, #333);">${title}</h2>
                    <button onclick="this.closest('.modal-overlay').remove()" style="
                        background: none;
                        border: none;
                        font-size: 20px;
                        cursor: pointer;
                        color: var(--text-muted, #999);
                    ">×</button>
                </div>
                <div style="color: var(--text-secondary, #666);">
                    ${content}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function showDemoToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type] || 'fa-info-circle'}"></i>
        <span>${message}</span>
        <button class="toast-close">
            <i class="fas fa-times"></i>
        </button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 4000);
}

// Make functions available globally for onclick handlers
window.showKeyboardShortcuts = showKeyboardShortcuts;
window.toggleDemoInfo = toggleDemoInfo;