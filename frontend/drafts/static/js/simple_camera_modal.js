// Camera Modal Functions for simple_camera_modal.html

// Modal Functions
function openModal() {
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById('cameraName').focus();
    if (!editingCameraId) {
        updateCameraDefaults(currentCameraType);
    }
}

function openEditModal(camera) {
    editingCameraId = camera.id || camera.camera_id;
    editingCamera = camera;

    // Update modal title
    document.querySelector('.modal-title').innerHTML = '<i class="fas fa-edit"></i> Edit IP Camera';

    // Pre-fill form with existing data
    document.getElementById('cameraName').value = camera.name || camera.camera_name || '';
    document.getElementById('ipAddress').value = camera.ip_address || camera.ip || '';
    document.getElementById('port').value = camera.port || 554;
    document.getElementById('username').value = camera.username || 'admin';
    document.getElementById('password').value = camera.password || '';
    document.getElementById('streamPath').value = camera.stream_path || '';
    document.getElementById('location').value = camera.installation_location || camera.location || '';

    // Set camera type and update defaults
    const cameraType = camera.manufacturer || camera.camera_type || 'reolink';
    setActiveConnectionType(cameraType);

    // Update save button text
    const saveBtn = document.querySelector('button[type="submit"]');
    saveBtn.innerHTML = '<i class="fas fa-save"></i> Update Camera';

    openModal();
}

function closeModal() {
    document.getElementById('modalOverlay').style.display = 'none';
    clearForm();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple Camera Modal initialized');
    loadCameras();
    setActiveConnectionType('reolink');
    
    // Add button event listener to ensure it's properly connected
    document.querySelector('.add-camera-btn').addEventListener('click', function() {
        console.log('Add camera button clicked');
        openModal();
    });
});

// Add this to ensure the rest of your functions work
let currentCameraType = 'reolink';
let editingCameraId = null;
let editingCamera = null;

// Function stubs to prevent errors - these should be defined in your main HTML
function clearForm() {
    console.log('clearForm called');
    // Implement as needed
}

function updateCameraDefaults() {
    console.log('updateCameraDefaults called');
    // Implement as needed
}

function setActiveConnectionType() {
    console.log('setActiveConnectionType called');
    // Implement as needed
}

function loadCameras() {
    console.log('loadCameras called');
    // Implement as needed
}