/**
 * Simple Camera Modal Functions
 * Clean, working implementation without conflicts
 */

// Simple Modal Functions
function openCameraModal() {
    console.log('Opening camera modal...');
    const modal = document.getElementById('add-camera-modal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('show');
        
        // Reset modal for new camera creation
        resetModalForNewCamera();
        
        // Load locations when modal opens
        loadLocations();
        
        const cameraNameInput = document.getElementById('cameraName');
        if (cameraNameInput) {
            cameraNameInput.focus();
        }
    }
}

function resetModalForNewCamera() {
    // Reset modal title
    const modalTitle = document.querySelector('.modal-title');
    if (modalTitle) {
        modalTitle.textContent = 'Add New IP Camera';
    }
    
    // Reset save button text
    const form = document.getElementById('cameraForm');
    if (form) {
        // Remove editing ID
        delete form.dataset.editingId;
        
        const saveBtn = form.querySelector('button[type="submit"]');
        if (saveBtn) {
            saveBtn.textContent = 'Save Camera';
        }
    }
    
    // Clear form
    clearCameraForm();
}

function closeCameraModal() {
    console.log('Closing camera modal...');
    const modal = document.getElementById('add-camera-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300); // Wait for transition to complete
        clearCameraForm();
    }
}

function clearCameraForm() {
    const form = document.getElementById('cameraForm');
    if (form) {
        form.reset();
        // Reset to default values
        document.getElementById('port').value = '554';
        document.getElementById('manufacturer').value = 'generic';
        document.getElementById('username').value = 'admin';
        document.getElementById('streamPath').value = '/stream1';
    }
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.innerHTML = '';
    }
}

function showCameraMessage(message, type = 'success') {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        const messageClass = type === 'success' ? 'success-message' : 'error-message';
        // Handle multiline messages by converting \n to <br>
        const formattedMessage = message.replace(/\n/g, '<br>');
        messageDiv.innerHTML = `<div class="${messageClass}" style="color: ${type === 'success' ? '#28a745' : '#dc3545'}; background: ${type === 'success' ? '#d4edda' : '#f8d7da'}; border: 1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'}; padding: 10px; border-radius: 4px; margin-top: 10px; white-space: pre-line;">${formattedMessage}</div>`;
    }
}

async function testCameraConnection() {
    console.log('Testing camera connection...');
    const ipAddress = document.getElementById('ipAddress').value;
    const port = document.getElementById('port').value;
    const username = document.getElementById('username').value || 'admin';
    const password = document.getElementById('password').value;
    const streamPath = document.getElementById('streamPath').value || '/stream1';
    
    if (!ipAddress) {
        showCameraMessage('Please enter an IP address first', 'error');
        return;
    }
    
    if (!password) {
        showCameraMessage('Please enter a password for testing', 'error');
        return;
    }
    
    showCameraMessage('Testing connection to ' + ipAddress + ':' + port + streamPath + '...', 'success');
    
    try {
        const testData = {
            ip_address: ipAddress,
            port: parseInt(port) || 554,
            username: username,
            password: password,
            stream_path: streamPath
        };
        
        const response = await fetch('/api/cameras/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showCameraMessage(`✅ Connection successful! Response time: ${result.response_time}ms. Stream format: ${result.stream_info || 'Unknown'}`, 'success');
        } else {
            const errorMsg = result.error || 'Connection failed';
            let enhancedError = `❌ Connection failed: ${errorMsg}`;
            
            // Provide specific suggestions based on error type
            if (errorMsg.includes('timeout')) {
                enhancedError += '\n💡 Suggestion: Check if camera is powered on and network is reachable.';
            } else if (errorMsg.includes('auth') || errorMsg.includes('401')) {
                enhancedError += '\n💡 Suggestion: Verify username and password are correct.';
            } else if (errorMsg.includes('stream') || errorMsg.includes('path') || errorMsg.includes('404')) {
                enhancedError += '\n💡 Suggestion: Try different stream paths from the dropdown suggestions.';
            } else if (errorMsg.includes('port') || errorMsg.includes('refused')) {
                enhancedError += '\n💡 Suggestion: Check if the port is correct (554 for RTSP, 80 for HTTP).';
            }
            
            showCameraMessage(enhancedError, 'error');
        }
    } catch (error) {
        console.error('Error testing camera connection:', error);
        showCameraMessage('Network error during connection test. Please check your settings and try again.', 'error');
    }
}

// Handle form submission
function setupCameraModal() {
    const form = document.getElementById('cameraForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Saving camera...');
            
            const formData = {
                name: document.getElementById('cameraName').value.trim(),
                ip_address: document.getElementById('ipAddress').value.trim(),
                port: parseInt(document.getElementById('port').value) || 554,
                username: document.getElementById('username').value.trim() || 'admin',
                password: document.getElementById('password').value,
                stream_path: document.getElementById('streamPath').value.trim() || '/stream1',
                location_id: document.getElementById('location').value.trim(),
                manufacturer: document.getElementById('manufacturer').value || 'generic',
                camera_type: 'ip_camera',
                connection_type: 'rtsp',
                model: 'IP Camera',
                auth_type: 'basic',
                resolution_width: 1920,
                resolution_height: 1080,
                fps: 30
            };
            
            // Validate all fields before submission
            if (!validateAllFields()) {
                showCameraMessage('Please fix the validation errors above', 'error');
                return;
            }
            
            if (!formData.name || !formData.ip_address || !formData.location_id) {
                showCameraMessage('Please fill in required fields (Name, IP Address, and Location)', 'error');
                return;
            }
            
            console.log('Sending camera data to API:', formData);
            
            // Check if we're editing an existing camera
            const editingId = form.dataset.editingId;
            const isEditing = !!editingId;
            
            try {
                showCameraMessage(isEditing ? 'Updating camera...' : 'Saving camera...', 'success');
                
                const url = isEditing ? `/api/cameras/${editingId}` : '/api/cameras/';
                const method = isEditing ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('Camera saved successfully:', result);
                    showCameraMessage(
                        isEditing 
                            ? `✅ Camera "${formData.name}" updated successfully!` 
                            : `✅ Camera "${formData.name}" saved successfully!`, 
                        'success'
                    );
                    
                    setTimeout(() => {
                        closeCameraModal();
                        // Reload the cameras section
                        loadCameras();
                    }, 1500);
                } else {
                    const error = await response.json();
                    console.error('Failed to save camera:', error);
                    
                    // Enhanced error handling based on status codes
                    let errorMessage = '';
                    switch (response.status) {
                        case 400:
                            errorMessage = '❌ Invalid camera data. Please check all fields.';
                            break;
                        case 409:
                            errorMessage = `❌ A camera with IP address ${formData.ip_address} already exists.`;
                            break;
                        case 422:
                            errorMessage = '❌ Validation error. Please check required fields.';
                            break;
                        case 500:
                            errorMessage = '❌ Server error. Please try again later.';
                            break;
                        default:
                            errorMessage = error.detail || `❌ Failed to ${isEditing ? 'update' : 'save'} camera. Please try again.`;
                    }
                    showCameraMessage(errorMessage, 'error');
                }
            } catch (error) {
                console.error('Error saving camera:', error);
                showCameraMessage('Network error. Please check your connection and try again.', 'error');
            }
        });
    }
}

// Close modal when clicking outside
function setupCameraModalEvents() {
    const modal = document.getElementById('add-camera-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeCameraModal();
            }
        });
    }

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('add-camera-modal');
            if (modal && modal.classList.contains('show')) {
                closeCameraModal();
            }
        }
    });
}

// Load locations into dropdown
async function loadLocations() {
    console.log('Loading locations...');
    
    try {
        const response = await fetch('/api/locations/');
        if (response.ok) {
            const locations = await response.json();
            console.log('Loaded locations:', locations);
            
            const locationSelect = document.getElementById('location');
            if (locationSelect) {
                // Clear existing options except the first one
                locationSelect.innerHTML = '<option value="">Select Location</option>';
                
                // Add location options
                locations.forEach(location => {
                    const option = document.createElement('option');
                    option.value = location.id;
                    option.textContent = location.name;
                    locationSelect.appendChild(option);
                });
            }
        } else {
            console.error('Failed to load locations:', response.status);
        }
    } catch (error) {
        console.error('Error loading locations:', error);
    }
}

// Load and display cameras
async function loadCameras() {
    console.log('Loading cameras...');
    
    try {
        const response = await fetch('/api/cameras/');
        if (response.ok) {
            const cameras = await response.json();
            console.log('Loaded cameras:', cameras);
            displayCameras(cameras);
        } else {
            console.error('Failed to load cameras:', response.status);
            displayCameras([]); // Show empty state
        }
    } catch (error) {
        console.error('Error loading cameras:', error);
        displayCameras([]); // Show empty state
    }
}

// Display cameras in the grid
function displayCameras(cameras) {
    const cameraGrid = document.getElementById('cameras-grid');
    if (!cameraGrid) {
        console.warn('Camera grid element not found');
        return;
    }
    
    if (cameras.length === 0) {
        cameraGrid.innerHTML = `
            <div class="empty-state" style="text-align: center; padding: 40px; color: #666;">
                <i class="fas fa-video" style="font-size: 3rem; margin-bottom: 1rem; display: block;"></i>
                <h3>No Cameras Configured</h3>
                <p>Add your first IP camera to start monitoring</p>
                <button class="btn btn-primary" onclick="openCameraModal()" style="margin-top: 10px;">
                    <i class="fas fa-plus"></i> Add Camera
                </button>
            </div>
        `;
        return;
    }
    
    cameraGrid.innerHTML = cameras.map(camera => `
        <div class="camera-card" data-camera-id="${camera.id}" style="background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <div class="camera-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #333;">${camera.name}</h3>
                <span class="camera-status ${camera.status === 'online' ? 'online' : 'offline'}" style="padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; background: ${camera.status === 'online' ? '#28a745' : '#dc3545'};">
                    ${camera.status === 'online' ? 'Online' : 'Offline'}
                </span>
            </div>
            <div class="camera-details" style="margin-bottom: 15px;">
                <p style="margin: 5px 0; color: #666;"><strong>IP:</strong> ${camera.ip_address}:${camera.port}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Location:</strong> ${camera.location_name || camera.location_id}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Type:</strong> ${camera.camera_type.toUpperCase()}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Stream:</strong> ${camera.stream_path || '/stream1'}</p>
            </div>
            <div class="camera-preview" style="background: #f8f9fa; border-radius: 4px; padding: 5px; text-align: center; margin-bottom: 15px; position: relative; height: 240px;">
                <div class="video-container" style="width: 100%; height: 100%; position: relative; background: #000; border-radius: 4px; overflow: hidden;">
                    <img id="camera-stream-${camera.id}" 
                         class="camera-stream" 
                         style="width: 100%; height: 100%; object-fit: cover; display: none;"
                         alt="Camera ${camera.name}"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="stream-placeholder" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #6c757d; background: #f8f9fa;">
                        <i class="fas fa-video" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <p style="margin: 0; font-size: 14px;">Loading Stream...</p>
                        <button class="btn btn-sm btn-primary" onclick="startCameraStream('${camera.id}')" style="margin-top: 10px; font-size: 12px;">
                            <i class="fas fa-play"></i> Start Stream
                        </button>
                    </div>
                    <div class="stream-overlay" style="position: absolute; bottom: 5px; left: 5px; background: rgba(0,0,0,0.7); color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">
                        ${camera.status === 'online' ? 'LIVE' : 'OFFLINE'}
                    </div>
                </div>
            </div>
            <div class="camera-actions" style="display: flex; gap: 8px; justify-content: flex-end;">
                <button class="btn btn-sm btn-secondary" onclick="editCamera('${camera.id}')" style="padding: 6px 12px; font-size: 12px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-sm ${camera.is_streaming ? 'btn-warning' : 'btn-success'}" 
                        onclick="toggleCameraStream('${camera.id}', ${camera.is_streaming})" 
                        id="stream-btn-${camera.id}"
                        style="padding: 6px 12px; font-size: 12px; background: ${camera.is_streaming ? '#ffc107' : '#28a745'}; color: ${camera.is_streaming ? '#212529' : 'white'}; border: none; border-radius: 4px; cursor: pointer;">
                    <i class="fas fa-${camera.is_streaming ? 'stop' : 'play'}"></i> ${camera.is_streaming ? 'Stop' : 'Stream'}
                </button>
                <button class="btn btn-sm btn-primary" onclick="takeCameraSnapshot('${camera.id}')" style="padding: 6px 12px; font-size: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    <i class="fas fa-camera"></i> Snap
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteCamera('${camera.id}')" style="padding: 6px 12px; font-size: 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
    
    // Auto-start streams for online cameras after a short delay
    setTimeout(() => {
        cameras.forEach(camera => {
            if (camera.status === 'online') {
                console.log('Auto-starting stream for online camera:', camera.name);
                initializeCameraStream(camera.id);
            }
        });
    }, 500);
}

// Camera action functions
async function editCamera(cameraId) {
    console.log('Edit camera:', cameraId);
    
    try {
        // Fetch camera data
        const response = await fetch(`/api/cameras/${cameraId}`);
        if (!response.ok) {
            console.error('Failed to fetch camera data');
            alert('Failed to load camera data');
            return;
        }
        
        const camera = await response.json();
        console.log('Loading camera for edit:', camera);
        
        // Open modal
        openCameraModal();
        
        // Populate form with existing data
        document.getElementById('cameraName').value = camera.name || '';
        document.getElementById('ipAddress').value = camera.ip_address || '';
        document.getElementById('port').value = camera.port || 554;
        document.getElementById('manufacturer').value = camera.manufacturer || 'generic';
        document.getElementById('username').value = camera.username || 'admin';
        document.getElementById('password').value = camera.password || '';
        document.getElementById('streamPath').value = camera.stream_path || '/stream1';
        
        // Set location after locations are loaded
        setTimeout(() => {
            if (camera.location_id) {
                document.getElementById('location').value = camera.location_id;
            }
        }, 500);
        
        // Change modal title and form behavior for editing
        const modalTitle = document.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Camera';
        }
        
        // Store camera ID for updating
        const form = document.getElementById('cameraForm');
        if (form) {
            form.dataset.editingId = cameraId;
        }
        
        // Change save button text
        const saveBtn = form.querySelector('button[type="submit"]');
        if (saveBtn) {
            saveBtn.textContent = 'Update Camera';
        }
        
        // Show preview section for existing cameras
        const previewSection = document.getElementById('camera-preview-section');
        if (previewSection) {
            previewSection.style.display = 'block';
            
            // Try to start preview automatically if camera is online
            if (camera.status === 'online') {
                setTimeout(() => {
                    startModalPreview();
                }, 1000);
            }
        }
        
    } catch (error) {
        console.error('Error loading camera for edit:', error);
        alert('Error loading camera data');
    }
}

// Camera streaming functions
async function toggleCameraStream(cameraId, isCurrentlyStreaming) {
    console.log('Toggling camera stream:', cameraId, 'Currently streaming:', isCurrentlyStreaming);
    
    if (isCurrentlyStreaming) {
        await stopCameraStream(cameraId);
    } else {
        await startCameraStream(cameraId);
    }
}

async function startCameraStream(cameraId) {
    console.log('Starting camera stream:', cameraId);
    
    try {
        // First try to start the camera stream via API
        const startResponse = await fetch(`/api/cameras/${cameraId}/start`, {
            method: 'POST'
        });
        
        if (startResponse.ok) {
            console.log('Camera stream started successfully');
            
            // Update the toggle button
            updateStreamButton(cameraId, true);
            
            // Wait a moment for stream to initialize
            setTimeout(() => {
                initializeCameraStream(cameraId);
            }, 1000);
        } else {
            console.warn('Failed to start camera stream, trying direct stream access');
            // Try direct stream access anyway
            initializeCameraStream(cameraId);
        }
    } catch (error) {
        console.error('Error starting camera stream:', error);
        // Fallback to direct stream access
        initializeCameraStream(cameraId);
    }
}

function initializeCameraStream(cameraId) {
    const streamImg = document.getElementById(`camera-stream-${cameraId}`);
    if (!streamImg) {
        console.error('Stream image element not found for camera:', cameraId);
        return;
    }
    
    // Try WebSocket streaming first (if available)
    if (window.cameraWebSocketClient && window.cameraWebSocketClient.isConnected) {
        console.log('Using WebSocket streaming for camera:', cameraId);
        enableWebSocketStreaming(cameraId);
        return;
    }
    
    // Fallback to MJPEG stream
    const streamUrl = `/api/cameras/${cameraId}/stream?t=${Date.now()}`;
    console.log('Using MJPEG streaming for camera:', cameraId, 'URL:', streamUrl);
    
    // Update the image source to start streaming
    streamImg.src = streamUrl;
    
    // Set up stream refresh mechanism for MJPEG
    const refreshStream = () => {
        if (streamImg.src) {
            // Add timestamp to prevent caching
            const baseUrl = streamImg.src.split('?')[0];
            streamImg.src = `${baseUrl}?t=${Date.now()}`;
        }
    };
    
    // Refresh stream every 30 seconds to prevent timeout
    const refreshInterval = setInterval(refreshStream, 30000);
    
    // Store interval ID for cleanup
    streamImg.dataset.refreshInterval = refreshInterval;
    
    // Handle stream errors
    streamImg.onerror = function() {
        console.warn('MJPEG stream error for camera:', cameraId, 'trying WebSocket fallback');
        clearInterval(refreshInterval);
        
        // Try WebSocket as fallback
        if (window.cameraWebSocketClient) {
            enableWebSocketStreaming(cameraId);
        } else {
            // Show error state
            const placeholder = this.nextElementSibling;
            if (placeholder) {
                placeholder.style.display = 'flex';
                placeholder.innerHTML = `
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px; color: #dc3545;"></i>
                    <p style="margin: 0; font-size: 14px;">Stream Unavailable</p>
                    <button class="btn btn-sm btn-primary" onclick="startCameraStream('${cameraId}')" style="margin-top: 10px; font-size: 12px;">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                `;
            }
        }
    };
    
    // Handle successful stream load
    streamImg.onload = function() {
        console.log('MJPEG stream loaded successfully for camera:', cameraId);
        this.style.display = 'block';
        const placeholder = this.nextElementSibling;
        if (placeholder) {
            placeholder.style.display = 'none';
        }
    };
}

async function stopCameraStream(cameraId) {
    console.log('Stopping camera stream:', cameraId);
    
    try {
        const response = await fetch(`/api/cameras/${cameraId}/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            console.log('Camera stream stopped successfully');
            
            // Update the toggle button
            updateStreamButton(cameraId, false);
            
            // Clear the stream image
            const streamImg = document.getElementById(`camera-stream-${cameraId}`);
            if (streamImg) {
                streamImg.src = '';
                streamImg.style.display = 'none';
                
                // Clear refresh interval
                if (streamImg.dataset.refreshInterval) {
                    clearInterval(parseInt(streamImg.dataset.refreshInterval));
                    delete streamImg.dataset.refreshInterval;
                }
                
                // Show placeholder
                const placeholder = streamImg.nextElementSibling;
                if (placeholder) {
                    placeholder.style.display = 'flex';
                    placeholder.innerHTML = `
                        <i class="fas fa-video" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <p style="margin: 0; font-size: 14px;">Stream Stopped</p>
                        <p style="margin: 5px 0 0 0; font-size: 11px; color: #888;">Use Stream button to start</p>
                    `;
                }
            }
        } else {
            console.error('Failed to stop camera stream');
        }
    } catch (error) {
        console.error('Error stopping camera stream:', error);
    }
}

function updateStreamButton(cameraId, isStreaming) {
    const streamBtn = document.getElementById(`stream-btn-${cameraId}`);
    if (streamBtn) {
        const icon = streamBtn.querySelector('i');
        const text = streamBtn.childNodes[streamBtn.childNodes.length - 1];
        
        if (isStreaming) {
            // Change to stop button
            streamBtn.className = 'btn btn-sm btn-warning';
            streamBtn.style.background = '#ffc107';
            streamBtn.style.color = '#212529';
            streamBtn.onclick = () => toggleCameraStream(cameraId, true);
            if (icon) icon.className = 'fas fa-stop';
            if (text) text.textContent = ' Stop';
        } else {
            // Change to start button
            streamBtn.className = 'btn btn-sm btn-success';
            streamBtn.style.background = '#28a745';
            streamBtn.style.color = 'white';
            streamBtn.onclick = () => toggleCameraStream(cameraId, false);
            if (icon) icon.className = 'fas fa-play';
            if (text) text.textContent = ' Stream';
        }
    }
}

async function takeCameraSnapshot(cameraId) {
    console.log('Taking snapshot for camera:', cameraId);
    
    try {
        const response = await fetch(`/api/cameras/${cameraId}/snapshot`);
        
        if (response.ok) {
            // Create a blob from the response and show in new tab
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            window.open(url, '_blank');
            
            // Clean up the object URL after a delay
            setTimeout(() => URL.revokeObjectURL(url), 1000);
            
            showCameraMessage('✅ Snapshot captured successfully!', 'success');
        } else {
            console.error('Failed to capture snapshot');
            showCameraMessage('❌ Failed to capture snapshot', 'error');
        }
    } catch (error) {
        console.error('Error capturing snapshot:', error);
        showCameraMessage('❌ Error capturing snapshot', 'error');
    }
}

function testCamera(cameraId) {
    console.log('Test camera:', cameraId);
    // Start the camera stream for testing
    startCameraStream(cameraId);
}

async function deleteCamera(cameraId) {
    if (!confirm('Are you sure you want to delete this camera?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/cameras/${cameraId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            console.log('Camera deleted successfully');
            loadCameras(); // Reload the camera list
        } else {
            console.error('Failed to delete camera');
            alert('Failed to delete camera');
        }
    } catch (error) {
        console.error('Error deleting camera:', error);
        alert('Error deleting camera');
    }
}

// Enhanced manufacturer configurations
const manufacturerConfigs = {
    'generic': {
        streamPaths: ['/stream1', '/stream2', '/live1.sdp', '/videostream.cgi'],
        defaultPort: 554,
        defaultPath: '/stream1',
        commonPorts: [554, 80, 8080, 1935],
        description: 'Generic IP camera with standard RTSP'
    },
    'reolink': {
        streamPaths: ['/h264Preview_01_main', '/h264Preview_01_sub', '/h264Preview_02_main'],
        defaultPort: 554,
        defaultPath: '/h264Preview_01_main',
        commonPorts: [554, 80, 8000],
        description: 'Reolink cameras with H.264 streaming'
    },
    'hikvision': {
        streamPaths: ['/Streaming/Channels/101/', '/Streaming/Channels/102/', '/Streaming/Channels/1/'],
        defaultPort: 554,
        defaultPath: '/Streaming/Channels/101/',
        commonPorts: [554, 8000, 80],
        description: 'Hikvision cameras with channel-based streaming'
    },
    'dahua': {
        streamPaths: ['/cam/realmonitor?channel=1&subtype=0', '/cam/realmonitor?channel=1&subtype=1', '/cam/realmonitor?channel=0&subtype=0'],
        defaultPort: 554,
        defaultPath: '/cam/realmonitor?channel=1&subtype=0',
        commonPorts: [554, 37777, 80],
        description: 'Dahua cameras with channel monitoring'
    },
    'axis': {
        streamPaths: ['/axis-media/media.amp', '/mjpg/video.mjpg', '/axis-media/media.amp?camera=1'],
        defaultPort: 554,
        defaultPath: '/axis-media/media.amp',
        commonPorts: [554, 80, 8080],
        description: 'Axis cameras with media streaming'
    },
    'foscam': {
        streamPaths: ['/videostream.cgi?user=admin&pwd=', '/video.cgi', '/livestream.cgi'],
        defaultPort: 88,
        defaultPath: '/videostream.cgi?user=admin&pwd=',
        commonPorts: [88, 80, 554],
        description: 'Foscam cameras with CGI-based streaming'
    },
    'amcrest': {
        streamPaths: ['/cam/realmonitor?channel=1&subtype=0', '/cam/realmonitor?channel=1&subtype=1'],
        defaultPort: 554,
        defaultPath: '/cam/realmonitor?channel=1&subtype=0',
        commonPorts: [554, 37777, 80],
        description: 'Amcrest cameras (Dahua-based)'
    }
};

// Auto-configure based on manufacturer selection
function setupManufacturerConfig() {
    const manufacturerSelect = document.getElementById('manufacturer');
    const streamPathInput = document.getElementById('streamPath');
    const portInput = document.getElementById('port');
    
    if (manufacturerSelect) {
        manufacturerSelect.addEventListener('change', function() {
            const manufacturer = this.value;
            const config = manufacturerConfigs[manufacturer];
            
            if (config) {
                // Update stream path if empty or default
                if (streamPathInput && (!streamPathInput.value || streamPathInput.value === '/stream1')) {
                    streamPathInput.value = config.defaultPath;
                }
                
                // Update port if still default (554) or empty
                if (portInput && (portInput.value === '554' || !portInput.value)) {
                    portInput.value = config.defaultPort;
                }
                
                // Update datalist suggestions
                updateStreamSuggestions(config.streamPaths);
                
                // Show helpful message about the manufacturer
                showCameraMessage(`${config.description} | Common ports: ${config.commonPorts.join(', ')}`, 'success');
                
                // Auto-clear message after 3 seconds
                setTimeout(() => {
                    const messageDiv = document.getElementById('message');
                    if (messageDiv) {
                        messageDiv.innerHTML = '';
                    }
                }, 3000);
            }
        });
    }
}

function updateStreamSuggestions(paths) {
    const datalist = document.getElementById('stream-suggestions');
    if (datalist) {
        // Keep existing options and add manufacturer-specific ones
        const existingOptions = Array.from(datalist.options).map(opt => opt.value);
        
        paths.forEach(path => {
            if (!existingOptions.includes(path)) {
                const option = document.createElement('option');
                option.value = path;
                option.textContent = path;
                datalist.appendChild(option);
            }
        });
    }
}

// Form validation functions
function validateField(fieldId, validationFn, errorMessage) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.getElementById(fieldId + '-error');
    
    if (!field) return true;
    
    const isValid = validationFn(field.value);
    
    if (isValid) {
        field.classList.remove('error');
        field.classList.add('success');
        if (errorDiv) {
            errorDiv.classList.remove('show');
            errorDiv.textContent = '';
        }
    } else {
        field.classList.remove('success');
        field.classList.add('error');
        if (errorDiv) {
            errorDiv.classList.add('show');
            errorDiv.textContent = errorMessage;
        }
    }
    
    return isValid;
}

function validateIPAddress(ip) {
    const ipRegex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ip.trim() !== '' && ipRegex.test(ip.trim());
}

function validateRequired(value) {
    return value.trim() !== '';
}

function validatePort(port) {
    const portNum = parseInt(port);
    return !isNaN(portNum) && portNum >= 1 && portNum <= 65535;
}

function setupFormValidation() {
    // Real-time validation for IP address
    const ipField = document.getElementById('ipAddress');
    if (ipField) {
        ipField.addEventListener('blur', function() {
            validateField('ipAddress', validateIPAddress, 'Please enter a valid IPv4 address (e.g., 192.168.1.100)');
        });
        
        ipField.addEventListener('input', function() {
            // Clear error state while typing
            this.classList.remove('error');
            const errorDiv = document.getElementById('ipAddress-error');
            if (errorDiv) {
                errorDiv.classList.remove('show');
            }
        });
    }
    
    // Real-time validation for required fields
    const requiredFields = ['cameraName', 'location'];
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', function() {
                validateField(fieldId, validateRequired, 'This field is required');
            });
            
            field.addEventListener('input', function() {
                // Clear error state while typing
                this.classList.remove('error');
                const errorDiv = document.getElementById(fieldId + '-error');
                if (errorDiv) {
                    errorDiv.classList.remove('show');
                }
            });
        }
    });
    
    // Port validation
    const portField = document.getElementById('port');
    if (portField) {
        portField.addEventListener('blur', function() {
            if (this.value) {
                validateField('port', validatePort, 'Port must be between 1 and 65535');
            }
        });
    }
}

function validateAllFields() {
    const validations = [
        validateField('cameraName', validateRequired, 'Camera name is required'),
        validateField('ipAddress', validateIPAddress, 'Please enter a valid IPv4 address'),
        validateField('location', validateRequired, 'Location selection is required')
    ];
    
    // Optional port validation if provided
    const portField = document.getElementById('port');
    if (portField && portField.value) {
        validations.push(validateField('port', validatePort, 'Port must be between 1 and 65535'));
    }
    
    return validations.every(isValid => isValid);
}

// Modal preview functions
let modalPreviewSession = null;

function startModalPreview() {
    const ipAddress = document.getElementById('ipAddress').value;
    const port = document.getElementById('port').value || '554';
    const username = document.getElementById('username').value || 'admin';
    const password = document.getElementById('password').value;
    const streamPath = document.getElementById('streamPath').value || '/stream1';
    const manufacturer = document.getElementById('manufacturer').value || 'generic';
    
    if (!ipAddress) {
        showCameraMessage('Please enter an IP address first', 'error');
        return;
    }
    
    console.log('Starting modal preview for:', ipAddress);
    
    // Show preview section
    const previewSection = document.getElementById('camera-preview-section');
    const previewImg = document.getElementById('modal-camera-preview');
    const placeholder = document.getElementById('preview-placeholder');
    
    if (previewSection) {
        previewSection.style.display = 'block';
        
        // Update placeholder to show loading
        placeholder.innerHTML = `
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 10px;"></i>
            <p style="margin: 0; font-size: 14px;">Starting Preview...</p>
        `;
    }
    
    // Start preview session via API
    startPreviewSession(ipAddress, port, username, password, streamPath, manufacturer);
}

async function startPreviewSession(ipAddress, port, username, password, streamPath, manufacturer) {
    try {
        const previewData = {
            ip_address: ipAddress,
            manufacturer: manufacturer,
            connection_type: 'rtsp',
            port: parseInt(port),
            stream_path: streamPath,
            username: username,
            password: password
        };
        
        const response = await fetch('/api/cameras/preview/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(previewData)
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                modalPreviewSession = result.session_id;
                console.log('Preview session started:', modalPreviewSession);
                
                // Start receiving preview frames
                startModalPreviewStream(modalPreviewSession);
            } else {
                showPreviewError('Failed to start preview session');
            }
        } else {
            // Fallback to direct snapshot method
            tryDirectSnapshot(ipAddress, port, username, password, streamPath);
        }
    } catch (error) {
        console.error('Error starting preview session:', error);
        tryDirectSnapshot(ipAddress, port, username, password, streamPath);
    }
}

function startModalPreviewStream(sessionId) {
    const previewImg = document.getElementById('modal-camera-preview');
    const placeholder = document.getElementById('preview-placeholder');
    
    // Try to get live frames from the preview session
    const updatePreview = async () => {
        try {
            const response = await fetch(`/api/cameras/preview/${sessionId}/live-frame`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                
                previewImg.src = url;
                previewImg.style.display = 'block';
                placeholder.style.display = 'none';
                
                // Clean up previous URL
                if (previewImg.dataset.previewUrl) {
                    URL.revokeObjectURL(previewImg.dataset.previewUrl);
                }
                previewImg.dataset.previewUrl = url;
                
            } else {
                console.warn('Preview frame not available');
                showPreviewError('Preview stream interrupted');
            }
        } catch (error) {
            console.error('Error updating preview:', error);
            showPreviewError('Preview error');
        }
    };
    
    // Update preview every 2 seconds
    const previewInterval = setInterval(updatePreview, 2000);
    
    // Store interval for cleanup
    previewImg.dataset.previewInterval = previewInterval;
    
    // Initial frame
    updatePreview();
}

async function tryDirectSnapshot(ipAddress, port, username, password, streamPath) {
    try {
        // Try connection test which might provide a snapshot
        const testData = {
            ip_address: ipAddress,
            port: parseInt(port) || 554,
            username: username,
            password: password,
            stream_path: streamPath
        };
        
        const response = await fetch('/api/cameras/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success message instead of preview
            const placeholder = document.getElementById('preview-placeholder');
            placeholder.innerHTML = `
                <i class="fas fa-check-circle" style="font-size: 2rem; margin-bottom: 10px; color: #28a745;"></i>
                <p style="margin: 0; font-size: 14px;">Connection Successful</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #6c757d;">Preview not available, but camera is reachable</p>
            `;
        } else {
            showPreviewError(result.detail || 'Connection failed');
        }
    } catch (error) {
        console.error('Error testing connection:', error);
        showPreviewError('Connection test failed');
    }
}

function showPreviewError(message) {
    const placeholder = document.getElementById('preview-placeholder');
    if (placeholder) {
        placeholder.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px; color: #dc3545;"></i>
            <p style="margin: 0; font-size: 14px;">Preview Failed</p>
            <p style="margin: 5px 0; font-size: 12px; color: #6c757d;">${message}</p>
            <button type="button" class="btn btn-sm btn-primary" onclick="startModalPreview()" style="margin-top: 10px; font-size: 12px;">
                <i class="fas fa-redo"></i> Retry
            </button>
        `;
    }
}

function stopModalPreview() {
    const previewImg = document.getElementById('modal-camera-preview');
    const placeholder = document.getElementById('preview-placeholder');
    
    // Clear preview image
    if (previewImg) {
        previewImg.style.display = 'none';
        previewImg.src = '';
        
        // Clean up object URL
        if (previewImg.dataset.previewUrl) {
            URL.revokeObjectURL(previewImg.dataset.previewUrl);
            delete previewImg.dataset.previewUrl;
        }
        
        // Clear interval
        if (previewImg.dataset.previewInterval) {
            clearInterval(parseInt(previewImg.dataset.previewInterval));
            delete previewImg.dataset.previewInterval;
        }
    }
    
    // Reset placeholder
    if (placeholder) {
        placeholder.style.display = 'flex';
        placeholder.innerHTML = `
            <i class="fas fa-video" style="font-size: 2rem; margin-bottom: 10px;"></i>
            <p style="margin: 0; font-size: 14px;">No Preview Available</p>
            <button type="button" class="btn btn-sm btn-primary" onclick="startModalPreview()" style="margin-top: 10px; font-size: 12px;">
                <i class="fas fa-eye"></i> Start Preview
            </button>
        `;
    }
    
    // Stop preview session
    if (modalPreviewSession) {
        fetch(`/api/cameras/preview/${modalPreviewSession}`, { method: 'DELETE' })
            .catch(error => console.warn('Error stopping preview session:', error));
        modalPreviewSession = null;
    }
}

function clearCameraForm() {
    const form = document.getElementById('cameraForm');
    if (form) {
        form.reset();
        // Reset to default values
        document.getElementById('port').value = '554';
        document.getElementById('manufacturer').value = 'generic';
        document.getElementById('username').value = 'admin';
        document.getElementById('streamPath').value = '/stream1';
    }
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.innerHTML = '';
    }
    
    // Hide and stop preview
    const previewSection = document.getElementById('camera-preview-section');
    if (previewSection) {
        previewSection.style.display = 'none';
    }
    stopModalPreview();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupCameraModal();
    setupCameraModalEvents();
    setupManufacturerConfig();
    setupFormValidation();
    
    // Bind Add Camera button
    const addCameraBtn = document.getElementById('add-camera-btn');
    if (addCameraBtn) {
        addCameraBtn.addEventListener('click', openCameraModal);
    }
    
    // Bind Refresh Cameras button
    const refreshCamerasBtn = document.getElementById('refresh-cameras-btn');
    if (refreshCamerasBtn) {
        refreshCamerasBtn.addEventListener('click', loadCameras);
    }
    
    // Load cameras on page load
    loadCameras();
    
    // Make loadCameras globally available
    window.loadCameras = loadCameras;
    
    console.log('Camera modal initialized');
});