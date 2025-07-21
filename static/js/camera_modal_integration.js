/**
 * Integration example for IP Camera Modal
 * This file shows how to integrate the IP Camera Modal into your main application
 */

// Example: How to integrate the modal into your cameras page
function initializeCameraModal() {
    // Load the modal HTML dynamically
    const modalHTML = `
        <div class="modal-overlay" id="ipCameraModal" style="display: none;">
            <div class="modal-container" role="dialog" aria-labelledby="modal-title" aria-describedby="modal-description">
                <!-- Modal content would be loaded here -->
            </div>
        </div>
    `;
    
    // Add modal to page if it doesn't exist
    if (!document.getElementById('ipCameraModal')) {
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
}

// Example: How to show the modal
function showAddCameraModal() {
    // Initialize modal if not already done
    if (!window.ipCameraModal) {
        initializeCameraModal();
    }
    
    // Show the modal
    const modal = document.getElementById('ipCameraModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

// Example: How to handle camera addition success
function onCameraAdded(cameraData) {
    console.log('Camera added:', cameraData);
    
    // Refresh the cameras list
    if (typeof refreshCamerasList === 'function') {
        refreshCamerasList();
    }
    
    // Show success notification
    showNotification('Camera added successfully!', 'success');
    
    // Close modal
    const modal = document.getElementById('ipCameraModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Example: How to handle camera addition error
function onCameraAddError(error) {
    console.error('Camera addition error:', error);
    
    // Show error notification
    showNotification('Failed to add camera: ' + error.message, 'error');
}

// Example: Simple notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 9999;
        opacity: 0;
        transform: translateY(-20px);
        transition: all 0.3s ease;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#16a34a',
        error: '#dc2626',
        warning: '#ea580c',
        info: '#2563eb'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Example: How to bind modal to existing "Add Camera" buttons
function bindAddCameraButtons() {
    const addButtons = document.querySelectorAll('[data-action="add-camera"]');
    addButtons.forEach(button => {
        button.addEventListener('click', showAddCameraModal);
    });
}

// Example: How to initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Bind existing buttons
    bindAddCameraButtons();
    
    // Listen for camera addition events
    window.addEventListener('cameraAdded', function(event) {
        onCameraAdded(event.detail);
    });
    
    window.addEventListener('cameraAddError', function(event) {
        onCameraAddError(event.detail);
    });
});

// Export functions for global use
window.CameraModalIntegration = {
    showAddCameraModal,
    onCameraAdded,
    onCameraAddError,
    showNotification,
    bindAddCameraButtons
};