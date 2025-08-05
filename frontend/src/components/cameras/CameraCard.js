import React, { useState, useEffect } from 'react';
import RecordingControls from './RecordingControls';
import config from '../../config/app.config.js';

function CameraCard({ camera }) {
    const [snapshotUrl, setSnapshotUrl] = useState('');
    const [lastUpdate, setLastUpdate] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [snapshotQuality, setSnapshotQuality] = useState('medium');
    const [cameraHealth, setCameraHealth] = useState(null);
    const [recordingStatus, setRecordingStatus] = useState(null);
    
    useEffect(() => {
        // Initial snapshot load
        updateSnapshot();
        
        // Refresh snapshot every 5 seconds for online cameras
        let interval;
        if (camera.status === 'online') {
            interval = setInterval(updateSnapshot, 5000);
        }
        
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [camera.id, camera.status, snapshotQuality]);

    const updateSnapshot = async () => {
        if (camera.status !== 'online') return;
        
        setIsLoading(true);
        try {
            // Add timestamp to prevent caching and include quality parameter
            const timestamp = Date.now();
            const newUrl = config.buildApiUrl(`/api/cameras/${camera.id}/snapshot?quality=${snapshotQuality}&t=${timestamp}`);
            setSnapshotUrl(newUrl);
            setLastUpdate(new Date());
        } catch (error) {
            console.error('Failed to update snapshot:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchCameraHealth = async () => {
        if (camera.status !== 'online') return;
        
        try {
            const response = await fetch(config.buildApiUrl(`/api/cameras/${camera.id}/health`));
            if (response.ok) {
                const healthData = await response.json();
                setCameraHealth(healthData);
            }
        } catch (error) {
            console.error('Failed to fetch camera health:', error);
        }
    };

    const fetchRecordingStatus = async () => {
        try {
            const response = await fetch(config.buildRecordingUrl(`/recordings/status/${camera.id}`));
            if (response.ok) {
                const statusData = await response.json();
                setRecordingStatus(statusData);
            }
        } catch (error) {
            console.error('Failed to fetch recording status:', error);
            setRecordingStatus(null);
        }
    };

    // Add health check and recording status to useEffect
    useEffect(() => {
        if (camera.status === 'online') {
            fetchCameraHealth();
            const healthInterval = setInterval(fetchCameraHealth, 30000); // Every 30 seconds
            return () => clearInterval(healthInterval);
        }
    }, [camera.id, camera.status]);

    // Recording status polling
    useEffect(() => {
        fetchRecordingStatus();
        const recordingInterval = setInterval(fetchRecordingStatus, 30000); // Every 30 seconds
        return () => clearInterval(recordingInterval);
    }, [camera.id]);

    const openInVLC = async () => {
        try {
            const response = await fetch(config.buildApiUrl(`/api/cameras/${camera.id}/open-vlc`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            if (!response.ok) {
                throw new Error('Failed to get RTSP URL');
            }
            
            const data = await response.json();
            
            // Try to open VLC directly (may not work in all browsers)
            const vlcUrl = `vlc://${data.rtsp_url}`;
            window.location.href = vlcUrl;
            
            // Also show instructions to user
            alert(`Opening in VLC...\n\nIf VLC doesn't open automatically:\n1. Open VLC Media Player\n2. Go to Media > Open Network Stream\n3. Enter URL: ${data.rtsp_url}`);
            
        } catch (error) {
            console.error('Failed to open VLC:', error);
            alert('Failed to open VLC. Please check if the camera is online and VLC is installed.');
        }
    };

    const copyRTSPUrl = async () => {
        try {
            const response = await fetch(config.buildApiUrl(`/api/cameras/${camera.id}/open-vlc`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            if (!response.ok) {
                throw new Error('Failed to get RTSP URL');
            }
            
            const data = await response.json();
            
            // Copy to clipboard
            await navigator.clipboard.writeText(data.rtsp_url);
            alert('RTSP URL copied to clipboard!');
            
        } catch (error) {
            console.error('Failed to copy RTSP URL:', error);
            alert('Failed to copy RTSP URL to clipboard.');
        }
    };

    const openFullscreen = (imageUrl) => {
        const fullscreenDiv = document.createElement('div');
        fullscreenDiv.className = 'fullscreen-overlay';
        fullscreenDiv.innerHTML = `
            <div class="fullscreen-container">
                <img src="${imageUrl}" alt="Camera Snapshot" class="fullscreen-image" />
                <div class="fullscreen-controls">
                    <button class="fullscreen-close" onclick="this.closest('.fullscreen-overlay').remove()">✕</button>
                    <button class="fullscreen-download" onclick="downloadSnapshot('${imageUrl}', '${camera.display_name || camera.name}')">⬇</button>
                </div>
                <div class="fullscreen-info">
                    <h3>${camera.display_name || camera.name}</h3>
                    <p>Captured: ${lastUpdate ? lastUpdate.toLocaleString() : 'Now'}</p>
                </div>
            </div>
        `;
        
        fullscreenDiv.addEventListener('click', (e) => {
            if (e.target === fullscreenDiv) {
                fullscreenDiv.remove();
            }
        });
        
        document.body.appendChild(fullscreenDiv);
        
        // Make download function globally available
        window.downloadSnapshot = (imageUrl, cameraName) => {
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = `${cameraName.replace(/[^a-z0-9]/gi, '_')}_snapshot_${new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-')}.jpg`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        };
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'online': return '#4CAF50';
            case 'offline': return '#f44336';
            default: return '#ff9800';
        }
    };

    const formatLastDetection = (lastDetection) => {
        if (!lastDetection) return 'Never';
        
        const date = new Date(lastDetection);
        const now = new Date();
        const diffInHours = (now - date) / (1000 * 60 * 60);
        
        if (diffInHours < 1) {
            const diffInMinutes = Math.floor(diffInHours * 60);
            return `${diffInMinutes} min ago`;
        } else if (diffInHours < 24) {
            return `${Math.floor(diffInHours)} hours ago`;
        } else {
            return date.toLocaleDateString();
        }
    };

    return (
        <div className="camera-card">
            <div className="camera-header">
                <h3>{camera.display_name || camera.name}</h3>
                {camera.short_id && (
                    <div className="camera-id-badge">
                        <span className="short-id">#{camera.short_id}</span>
                    </div>
                )}
                <div className="camera-status">
                    <span 
                        className="status-indicator"
                        style={{ backgroundColor: getStatusColor(camera.status) }}
                    ></span>
                    <span className="status-text">{camera.status}</span>
                    {recordingStatus && recordingStatus.is_recording && (
                        <div className="recording-indicator">
                            <span 
                                className="recording-dot"
                                style={{ backgroundColor: '#f44336' }}
                            ></span>
                            <span className="recording-text">Rec</span>
                        </div>
                    )}
                </div>
            </div>
            
            <div className="camera-snapshot-container">
                {camera.status === 'online' ? (
                    <div className="snapshot-wrapper">
                        <img 
                            src={snapshotUrl} 
                            alt={camera.display_name || camera.name}
                            className="camera-snapshot"
                            onClick={() => openFullscreen(snapshotUrl)}
                            onError={(e) => {
                                e.target.src = '/static/camera_offline.jpg';
                            }}
                        />
                        {lastUpdate && (
                            <div className="snapshot-timestamp">
                                {lastUpdate.toLocaleTimeString()}
                            </div>
                        )}
                        {isLoading && (
                            <div className="loading-overlay">
                                <div className="loading-spinner"></div>
                            </div>
                        )}
                        <div className="snapshot-overlay">
                            <button 
                                className="refresh-btn"
                                onClick={updateSnapshot}
                                disabled={isLoading}
                                title="Refresh snapshot"
                            >
                                =
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="offline-placeholder">
                        <div className="offline-icon">=�</div>
                        <p>Camera Offline</p>
                    </div>
                )}
            </div>
            
            <div className="camera-info">
                <div className="info-row">
                    <span className="info-label">Location:</span>
                    <span className="info-value">{camera.location || 'Not specified'}</span>
                </div>
                <div className="info-row">
                    <span className="info-label">IP Address:</span>
                    <span className="info-value">{camera.ip_address}</span>
                </div>
                <div className="info-row">
                    <span className="info-label">Last Detection:</span>
                    <span className="info-value">{formatLastDetection(camera.last_detection)}</span>
                </div>
                {cameraHealth && (
                    <div className="info-row">
                        <span className="info-label">Backend Status:</span>
                        <span className="info-value">
                            <span style={{ 
                                color: cameraHealth.connection_status === 'connected' ? '#4CAF50' : '#f44336' 
                            }}>
                                {cameraHealth.connection_status === 'connected' ? '🟢' : '🔴'} 
                                {cameraHealth.connection_status}
                            </span>
                            {cameraHealth.last_frame_age_seconds && (
                                <small> ({Math.round(cameraHealth.last_frame_age_seconds)}s ago)</small>
                            )}
                        </span>
                    </div>
                )}
                {lastUpdate && (
                    <div className="info-row">
                        <span className="info-label">Last Update:</span>
                        <span className="info-value">{lastUpdate.toLocaleTimeString()}</span>
                    </div>
                )}
            </div>
            
            <div className="quality-controls">
                <label className="quality-label">Snapshot Quality:</label>
                <select 
                    className="quality-selector"
                    value={snapshotQuality}
                    onChange={(e) => setSnapshotQuality(e.target.value)}
                    disabled={camera.status !== 'online'}
                    title="Adjust snapshot quality and file size"
                >
                    <option value="high">High (95% quality, full resolution)</option>
                    <option value="medium">Medium (85% quality, full resolution)</option>
                    <option value="low">Low (70% quality, 50% resolution)</option>
                </select>
            </div>
            
            <RecordingControls camera={camera} />
            
            <div className="camera-controls">
                <button 
                    className="control-btn primary"
                    onClick={openInVLC}
                    disabled={camera.status !== 'online'}
                    title="Open live view in VLC Media Player"
                >
                    <span className="btn-icon">�</span>
                    Open in VLC
                </button>
                
                <button 
                    className="control-btn secondary"
                    onClick={copyRTSPUrl}
                    disabled={camera.status !== 'online'}
                    title="Copy RTSP URL to clipboard"
                >
                    <span className="btn-icon">=�</span>
                    Copy URL
                </button>
            </div>
        </div>
    );
}

export default CameraCard;