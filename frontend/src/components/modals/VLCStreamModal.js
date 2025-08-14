/**
 * VLC Stream Modal Component
 * Professional stream URL handling for external VLC media player
 */
import config from '../../config/app.config.js';

class VLCStreamModal {
    constructor() {
        this.modal = null;
        this.currentCamera = null;
        
        // Create modal on instantiation
        this.createModal();
        this.attachEventListeners();
    }

    createModal() {
        const modalHTML = `
            <div class="modal-backdrop vlc-modal-backdrop" id="vlc-modal-backdrop">
                <div class="vlc-modal">
                    <div class="vlc-modal-content">
                        <div class="vlc-header">
                            <div class="vlc-icon-wrapper">
                                <div class="vlc-icon">▶</div>
                            </div>
                            <div class="vlc-title-section">
                                <h3 class="vlc-title">Open Stream in VLC Player</h3>
                                <p class="vlc-subtitle" id="vlc-camera-name">Camera Stream</p>
                            </div>
                            <button class="vlc-close" id="vlc-close-btn">✕</button>
                        </div>
                        
                        <div class="vlc-body">
                            <div class="stream-urls-section">
                                <div class="stream-url-group">
                                    <div class="stream-label">Main Stream (High Quality)</div>
                                    <div class="stream-input-wrapper">
                                        <input type="text" 
                                               class="stream-url-input" 
                                               id="main-stream-url" 
                                               readonly>
                                        <button class="copy-btn" data-target="main-stream-url">
                                            <i class="fas fa-copy"></i> Copy
                                        </button>
                                    </div>
                                    <div class="stream-details">
                                        <span class="stream-detail">Resolution: <strong id="main-resolution">--</strong></span>
                                        <span class="stream-detail">Bitrate: <strong id="main-bitrate">--</strong></span>
                                    </div>
                                </div>
                                
                                <div class="stream-url-group">
                                    <div class="stream-label">Sub Stream (Low Bandwidth)</div>
                                    <div class="stream-input-wrapper">
                                        <input type="text" 
                                               class="stream-url-input" 
                                               id="sub-stream-url" 
                                               readonly>
                                        <button class="copy-btn" data-target="sub-stream-url">
                                            <i class="fas fa-copy"></i> Copy
                                        </button>
                                    </div>
                                    <div class="stream-details">
                                        <span class="stream-detail">Resolution: <strong id="sub-resolution">--</strong></span>
                                        <span class="stream-detail">Bitrate: <strong id="sub-bitrate">--</strong></span>
                                    </div>
                                </div>
                                
                                <div class="stream-url-group">
                                    <div class="stream-label">Snapshot URL (Still Images)</div>
                                    <div class="stream-input-wrapper">
                                        <input type="text" 
                                               class="stream-url-input" 
                                               id="snapshot-url" 
                                               readonly>
                                        <button class="copy-btn" data-target="snapshot-url">
                                            <i class="fas fa-copy"></i> Copy
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="vlc-instructions">
                                <div class="instructions-header">
                                    <i class="fas fa-info-circle"></i>
                                    <h4>How to open in VLC Media Player:</h4>
                                </div>
                                <ol class="instructions-list">
                                    <li>Copy the stream URL above (Main Stream recommended)</li>
                                    <li>Open VLC Media Player</li>
                                    <li>Go to <strong>Media → Open Network Stream</strong> (or press <kbd>Ctrl+N</kbd>)</li>
                                    <li>Paste the URL in the network URL field</li>
                                    <li>Click <strong>Play</strong></li>
                                    <li>Enter credentials if prompted (configured in camera settings)</li>
                                </ol>
                                
                                <div class="instructions-note">
                                    <i class="fas fa-lightbulb"></i>
                                    <strong>Pro Tip:</strong> Save as a playlist in VLC for quick access. The stream will automatically reconnect if the connection is lost.
                                </div>
                            </div>
                            
                            <div class="connection-info" id="connection-info">
                                <div class="connection-item">
                                    <span class="connection-label">Protocol:</span>
                                    <span class="connection-value" id="connection-protocol">RTSP</span>
                                </div>
                                <div class="connection-item">
                                    <span class="connection-label">Authentication:</span>
                                    <span class="connection-value" id="connection-auth">Required</span>
                                </div>
                                <div class="connection-item">
                                    <span class="connection-label">Port:</span>
                                    <span class="connection-value" id="connection-port">554</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="vlc-footer">
                            <div class="vlc-footer-actions">
                                <button class="action-btn secondary" id="vlc-test-btn">
                                    <i class="fas fa-play-circle"></i>
                                    Test Stream
                                </button>
                                <button class="action-btn secondary" id="vlc-cancel-btn">
                                    Cancel
                                </button>
                                <button class="action-btn primary" id="vlc-open-btn">
                                    <i class="fas fa-external-link-alt"></i>
                                    Open in VLC
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('vlc-modal-backdrop');
    }

    attachEventListeners() {
        // Close button
        document.getElementById('vlc-close-btn')?.addEventListener('click', () => this.close());
        document.getElementById('vlc-cancel-btn')?.addEventListener('click', () => this.close());
        
        // Copy buttons
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.copyToClipboard(e));
        });
        
        // Action buttons
        document.getElementById('vlc-test-btn')?.addEventListener('click', () => this.testStream());
        document.getElementById('vlc-open-btn')?.addEventListener('click', () => this.openInVLC());
        
        // Close on backdrop click
        this.modal?.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal?.classList.contains('show')) {
                this.close();
            }
        });
    }

    open(camera) {
        console.log('🔧 VLC Modal v2.1 - Security Fixed Version');
        if (!camera) {
            console.error('No camera data provided to VLC modal');
            return;
        }

        this.currentCamera = camera;
        this.populateStreamData(camera);
        this.modal?.classList.add('show');
        
        // Focus management for accessibility
        setTimeout(() => {
            document.getElementById('main-stream-url')?.focus();
        }, 300);
    }

    close() {
        this.modal?.classList.remove('show');
        this.currentCamera = null;
    }

    populateStreamData(camera) {
        console.log('🔍 VLC Modal Debug - populateStreamData called with:', {
            camera_name: camera.name,
            username: camera.username,
            password_present: !!camera.password,
            password_length: camera.password ? camera.password.length : 0,
            ip_address: camera.ip_address,
            features: {
                MASK_SENSITIVE_DATA: config.FEATURES.MASK_SENSITIVE_DATA,
                VLC_SHOW_PASSWORDS: config.FEATURES.VLC_SHOW_PASSWORDS
            }
        });
        
        // Update modal title
        document.getElementById('vlc-camera-name').textContent = camera.display_name || camera.name;
        
        // Generate stream URLs based on camera configuration
        // Use display mode based on security feature flags
        const shouldMaskPasswords = config.FEATURES.MASK_SENSITIVE_DATA && !config.FEATURES.VLC_SHOW_PASSWORDS;
        console.log('🔍 shouldMaskPasswords:', shouldMaskPasswords);
        
        const displayBaseUrl = this.generateBaseUrl(camera, shouldMaskPasswords);
        const mainStreamPath = camera.stream_path || '/h264Preview_01_main';
        const subStreamPath = camera.stream_path?.replace('main', 'sub') || '/h264Preview_01_sub';
        
        // Store the current camera for clipboard operations
        this.currentCamera = camera;
        
        // Populate stream URLs (with masked passwords for display)
        document.getElementById('main-stream-url').value = `${displayBaseUrl}${mainStreamPath}`;
        document.getElementById('sub-stream-url').value = `${displayBaseUrl}${subStreamPath}`;
        document.getElementById('snapshot-url').value = config.buildApiUrl(config.API_ENDPOINTS.CAMERA_SNAPSHOT(camera.id));
        
        // Update stream details
        const resolution = camera.resolution_width && camera.resolution_height 
            ? `${camera.resolution_width}×${camera.resolution_height}` 
            : 'Unknown';
        
        document.getElementById('main-resolution').textContent = resolution;
        document.getElementById('sub-resolution').textContent = resolution === 'Unknown' ? 'Unknown' : '640×480';
        document.getElementById('main-bitrate').textContent = this.formatBitrate(camera.max_bitrate || 8000);
        document.getElementById('sub-bitrate').textContent = this.formatBitrate(1000);
        
        // Update connection info
        document.getElementById('connection-protocol').textContent = (camera.connection_type || 'rtsp').toUpperCase();
        document.getElementById('connection-auth').textContent = camera.username ? 'Required' : 'None';
        document.getElementById('connection-port').textContent = camera.port || 554;
    }

    generateBaseUrl(camera, displayMode = false) {
        const protocol = camera.connection_type || 'rtsp';
        const ipAddress = camera.ip_address || camera.ipAddress; // Handle both snake_case and camelCase
        const port = camera.port || 554;
        
        // Debug logging with security considerations
        if (!displayMode && config.FEATURES.VLC_SHOW_PASSWORDS) {
            console.log('VLC URL Generation Debug:', {
                username: camera.username,
                password: camera.password ? '[PRESENT]' : '[MISSING]',
                passwordLength: camera.password ? camera.password.length : 0,
                ipAddress: ipAddress,
                port: port,
                displayMode: displayMode
            });
        }
        
        // Only include credentials if both username and password exist
        let credentials = '';
        
        // Debug credentials check only when passwords are allowed to be shown
        if (!displayMode && config.FEATURES.VLC_SHOW_PASSWORDS) {
            console.log('🔍 generateBaseUrl - credentials check:', {
                username: camera.username,
                password_exists: !!camera.password,
                displayMode: displayMode
            });
        }
        
        if (camera.username && camera.password) {
            if (displayMode) {
                // Display mode: mask password with asterisks
                credentials = `${camera.username}:***@`;
                if (config.FEATURES.VLC_SHOW_PASSWORDS) {
                    console.log('🔒 Using masked credentials for display');
                }
            } else {
                // Real mode: use actual password for clipboard
                credentials = `${camera.username}:${camera.password}@`;
                if (config.FEATURES.VLC_SHOW_PASSWORDS) {
                    console.log('🔐 Using real credentials for clipboard');
                }
            }
        } else if (camera.username) {
            credentials = `${camera.username}@`; // Username only
            console.log('⚠️ Using username only (missing password)');
        } else {
            console.log('❌ No credentials available');
        }
        
        if (!ipAddress) {
            console.error('Camera IP address not found:', camera);
            return 'rtsp://invalid-camera-ip/';
        }
        
        const finalUrl = `${protocol}://${credentials}${ipAddress}:${port}`;
        
        // Only log sensitive URLs if explicitly allowed
        if (!displayMode && config.FEATURES.VLC_SHOW_PASSWORDS) {
            console.log('Generated VLC Base URL:', finalUrl);
        } else if (!displayMode) {
            // Log masked version for security
            const maskedUrl = finalUrl.replace(/:([^@]+)@/, ':***@');
            console.log('Generated VLC Base URL (masked):', maskedUrl);
        }
        
        return finalUrl;
    }

    formatBitrate(kbps) {
        if (kbps >= 1000) {
            return `${(kbps / 1000).toFixed(1)} Mbps`;
        }
        return `${kbps} Kbps`;
    }

    async copyToClipboard(e) {
        const targetId = e.currentTarget.dataset.target;
        const input = document.getElementById(targetId);
        const originalText = e.currentTarget.innerHTML;
        
        // Generate the real URL (with actual password) for clipboard
        let urlToCopy = input.value;
        
        if (this.currentCamera && (targetId === 'main-stream-url' || targetId === 'sub-stream-url')) {
            // Always use real credentials for clipboard, regardless of display settings
            // This ensures VLC gets working URLs even when passwords are masked in UI
            const realBaseUrl = this.generateBaseUrl(this.currentCamera, false); // false = real password mode
            
            if (targetId === 'main-stream-url') {
                const mainStreamPath = this.currentCamera.stream_path || '/h264Preview_01_main';
                urlToCopy = `${realBaseUrl}${mainStreamPath}`;
            } else if (targetId === 'sub-stream-url') {
                const subStreamPath = this.currentCamera.stream_path?.replace('main', 'sub') || '/h264Preview_01_sub';
                urlToCopy = `${realBaseUrl}${subStreamPath}`;
            }
            
            // Only log sensitive URL if explicitly allowed by security settings
            if (config.FEATURES.VLC_SHOW_PASSWORDS) {
                console.log('🔐 Copying URL to clipboard:', urlToCopy);
            } else {
                // Show masked version for security but confirm real password is present
                const maskedUrl = urlToCopy.replace(/:([^@]+)@/, ':***@');
                console.log('🔐 Copying URL to clipboard (masked for console):', maskedUrl);
                console.log('📋 Real password is present in clipboard:', urlToCopy.includes('Mekus_1987') ? '✅ YES' : '❌ NO');
            }
        }
        
        try {
            await navigator.clipboard.writeText(urlToCopy);
            
            // Success feedback
            e.currentTarget.innerHTML = '<i class="fas fa-check"></i> Copied!';
            e.currentTarget.classList.add('success');
            
            setTimeout(() => {
                e.currentTarget.innerHTML = originalText;
                e.currentTarget.classList.remove('success');
            }, 2000);
            
        } catch (error) {
            console.log('Modern clipboard API failed, using fallback:', error);
            // Fallback for older browsers
            // Create a temporary input with the real URL
            const tempInput = document.createElement('input');
            tempInput.value = urlToCopy;
            tempInput.style.position = 'fixed';
            tempInput.style.opacity = '0';
            document.body.appendChild(tempInput);
            tempInput.select();
            tempInput.setSelectionRange(0, 99999); // For mobile devices
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    console.log('✅ Fallback copy successful');
                    // Update button UI
                    if (e.currentTarget) {
                        e.currentTarget.innerHTML = '<i class="fas fa-check"></i> Copied!';
                        setTimeout(() => {
                            if (e.currentTarget) {
                                e.currentTarget.innerHTML = originalText;
                            }
                        }, 2000);
                    }
                } else {
                    console.error('❌ Fallback copy failed');
                }
            } catch (fallbackError) {
                console.error('❌ Fallback copy error:', fallbackError);
            } finally {
                document.body.removeChild(tempInput);
            }
        }
    }

    async testStream() {
        if (!this.currentCamera) return;
        
        const testBtn = document.getElementById('vlc-test-btn');
        const originalText = testBtn.innerHTML;
        
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        testBtn.disabled = true;
        
        try {
            // Test main stream URL
            const mainUrl = document.getElementById('main-stream-url').value;
            
            // Simple connectivity test (not actual stream validation)
            const testResponse = await fetch(config.buildApiUrl(`/api/cameras/${this.currentCamera.id}/test`), {
                method: 'POST'
            });
            
            if (testResponse.ok) {
                this.showToast('success', 'Stream connectivity test passed');
                testBtn.innerHTML = '<i class="fas fa-check"></i> Test Passed';
                testBtn.classList.add('success');
            } else {
                throw new Error('Connection test failed');
            }
            
        } catch (error) {
            console.error('Stream test error:', error);
            this.showToast('error', 'Stream test failed - check camera connection');
            testBtn.innerHTML = '<i class="fas fa-times"></i> Test Failed';
            testBtn.classList.add('error');
        } finally {
            setTimeout(() => {
                testBtn.innerHTML = originalText;
                testBtn.disabled = false;
                testBtn.classList.remove('success', 'error');
            }, 3000);
        }
    }

    openInVLC() {
        // Generate real URL with actual password for VLC
        let mainStreamUrl = document.getElementById('main-stream-url').value;
        
        if (this.currentCamera) {
            const realBaseUrl = this.generateBaseUrl(this.currentCamera, false); // false = real password mode
            const mainStreamPath = this.currentCamera.stream_path || '/h264Preview_01_main';
            mainStreamUrl = `${realBaseUrl}${mainStreamPath}`;
            
            // Only log sensitive URL if explicitly allowed by security settings
            if (config.FEATURES.VLC_SHOW_PASSWORDS) {
                console.log('🎯 Opening in VLC with credentials:', mainStreamUrl);
            } else {
                console.log('🎯 Opening in VLC (credentials masked in console for security)');
            }
        }
        
        // Multiple methods to open VLC (in order of preference)
        let vlcOpened = false;
        
        // Method 1: Try VLC protocol handler (most reliable)
        try {
            // VLC protocol handler expects: vlc://rtsp://user:pass@host:port/path
            // Ensure we don't have double protocols
            let vlcUrl = mainStreamUrl;
            if (!vlcUrl.startsWith('rtsp://')) {
                vlcUrl = `rtsp://${vlcUrl}`;
            }
            
            const finalVlcUrl = `vlc://${vlcUrl}`;
            
            // Log masked URL for debugging
            if (config.FEATURES.VLC_SHOW_PASSWORDS) {
                console.log('🎯 Launching VLC with URL:', finalVlcUrl);
            } else {
                const maskedVlcUrl = finalVlcUrl.replace(/:([^@]+)@/, ':***@');
                console.log('🎯 Launching VLC with URL (masked):', maskedVlcUrl);
            }
            
            window.location.href = finalVlcUrl;
            vlcOpened = true;
            console.log('✅ Attempting VLC protocol handler');
        } catch (error) {
            // Mask the error message to prevent password leakage
            const maskedError = config.FEATURES.VLC_SHOW_PASSWORDS 
                ? error.message 
                : error.message.replace(/:([^@]+)@/, ':***@');
            console.log('⚠️ VLC protocol handler failed:', maskedError);
        }
        
        // Method 2: Try alternative VLC schemes if the first fails
        if (!vlcOpened) {
            try {
                // Some systems register different VLC schemes
                const altVlcUrl = `vlc-media://${mainStreamUrl}`;
                window.open(altVlcUrl, '_self');
                vlcOpened = true;
                console.log('✅ Attempting VLC media protocol');
            } catch (error) {
                const maskedError = config.FEATURES.VLC_SHOW_PASSWORDS 
                    ? error.message 
                    : error.message.replace(/:([^@]+)@/, ':***@');
                console.log('⚠️ VLC media protocol failed:', maskedError);
            }
        }
        
        // Method 3: Direct application launch (Windows/macOS)
        if (!vlcOpened) {
            try {
                // For Windows: vlc: protocol (without double slash)
                const directVlcUrl = `vlc:${mainStreamUrl}`;
                window.location.href = directVlcUrl;
                console.log('✅ Attempting direct VLC launch');
            } catch (error) {
                const maskedError = config.FEATURES.VLC_SHOW_PASSWORDS 
                    ? error.message 
                    : error.message.replace(/:([^@]+)@/, ':***@');
                console.log('⚠️ Direct VLC launch failed:', maskedError);
            }
        }
        
        // Provide user feedback and clipboard fallback
        this.showToast('info', 'Attempting to open in VLC... If VLC doesn\'t open automatically, the URL has been copied to clipboard (Ctrl+N in VLC)');
        
        // Always copy to clipboard as backup (with real credentials)
        navigator.clipboard.writeText(mainStreamUrl).catch(() => {
            // Fallback for clipboard access - create temporary input
            const tempInput = document.createElement('input');
            tempInput.value = mainStreamUrl;
            tempInput.style.position = 'fixed';
            tempInput.style.opacity = '0';
            document.body.appendChild(tempInput);
            tempInput.select();
            document.execCommand('copy');
            document.body.removeChild(tempInput);
        });
        
        // Keep modal open briefly to show the toast message, then close
        setTimeout(() => {
            this.close();
        }, 2000);
    }

    showToast(type, message) {
        // Simple toast notification
        // This should integrate with existing toast system
        if (window.camerasPage && typeof window.camerasPage.showToast === 'function') {
            window.camerasPage.showToast(type, message);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    destroy() {
        this.modal?.remove();
    }
}

export default VLCStreamModal;