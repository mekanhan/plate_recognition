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
        // Update modal title
        document.getElementById('vlc-camera-name').textContent = camera.display_name || camera.name;
        
        // Generate stream URLs based on camera configuration
        const baseUrl = this.generateBaseUrl(camera);
        const mainStreamPath = camera.stream_path || '/h264Preview_01_main';
        const subStreamPath = camera.stream_path?.replace('main', 'sub') || '/h264Preview_01_sub';
        
        // Populate stream URLs
        document.getElementById('main-stream-url').value = `${baseUrl}${mainStreamPath}`;
        document.getElementById('sub-stream-url').value = `${baseUrl}${subStreamPath}`;
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

    generateBaseUrl(camera) {
        const protocol = camera.connection_type || 'rtsp';
        const username = camera.username ? `${camera.username}:***@` : '';
        return `${protocol}://${username}${camera.ip_address}:${camera.port}`;
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
        
        try {
            await navigator.clipboard.writeText(input.value);
            
            // Success feedback
            e.currentTarget.innerHTML = '<i class="fas fa-check"></i> Copied!';
            e.currentTarget.classList.add('success');
            
            setTimeout(() => {
                e.currentTarget.innerHTML = originalText;
                e.currentTarget.classList.remove('success');
            }, 2000);
            
        } catch (error) {
            // Fallback for older browsers
            input.select();
            document.execCommand('copy');
            
            e.currentTarget.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => {
                e.currentTarget.innerHTML = originalText;
            }, 2000);
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
        const mainStreamUrl = document.getElementById('main-stream-url').value;
        
        // Attempt to open VLC with the stream URL
        // Note: This requires VLC to be associated with the protocol handler
        try {
            window.location.href = `vlc://${mainStreamUrl}`;
        } catch (error) {
            console.log('Direct VLC launch not supported, showing alternative');
        }
        
        this.showToast('info', 'Stream URL copied to clipboard. Open VLC and paste the URL (Ctrl+N)');
        
        // Also copy to clipboard as backup
        navigator.clipboard.writeText(mainStreamUrl).catch(() => {
            // Fallback for clipboard access
        });
        
        this.close();
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