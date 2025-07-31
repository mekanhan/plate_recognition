import React, { useState, useEffect } from 'react';

function RecordingControls({ camera }) {
    const [recordingQuality, setRecordingQuality] = useState('medium');
    const [recordingStatus, setRecordingStatus] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);

    useEffect(() => {
        if (camera.status === 'online') {
            fetchRecordingQuality();
        }
    }, [camera.id, camera.status]);

    const fetchRecordingQuality = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`/api/cameras/${camera.id}/recording/quality`);
            if (response.ok) {
                const data = await response.json();
                setRecordingQuality(data.current_quality);
                setRecordingStatus(data);
            }
        } catch (error) {
            console.error('Failed to fetch recording quality:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const updateRecordingQuality = async (newQuality) => {
        setIsUpdating(true);
        try {
            const response = await fetch(`/api/cameras/${camera.id}/recording/quality`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ quality: newQuality })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    setRecordingQuality(newQuality);
                    await fetchRecordingQuality(); // Refresh status
                    alert('Recording quality updated successfully!');
                } else {
                    alert(`Failed to update recording quality: ${result.message}`);
                }
            } else {
                throw new Error('Failed to update recording quality');
            }
        } catch (error) {
            console.error('Failed to update recording quality:', error);
            alert('Failed to update recording quality. Please try again.');
        } finally {
            setIsUpdating(false);
        }
    };

    const getQualityColor = (quality) => {
        switch (quality) {
            case 'high': return '#4CAF50';
            case 'medium': return '#ff9800';
            case 'low': return '#f44336';
            default: return '#9e9e9e';
        }
    };

    return (
        <div className="recording-controls">
            <div className="recording-header">
                <h4>Recording Settings</h4>
                {recordingStatus && (
                    <div className="recording-status">
                        <span 
                            className="recording-indicator"
                            style={{ 
                                backgroundColor: recordingStatus.recording_active ? '#f44336' : '#9e9e9e' 
                            }}
                        ></span>
                        <span className="recording-text">
                            {recordingStatus.recording_active ? 'Recording' : 'Not Recording'}
                        </span>
                    </div>
                )}
            </div>

            <div className="quality-settings">
                <label className="setting-label">Recording Quality:</label>
                <select 
                    className="quality-selector"
                    value={recordingQuality}
                    onChange={(e) => updateRecordingQuality(e.target.value)}
                    disabled={camera.status !== 'online' || isUpdating}
                    style={{ borderColor: getQualityColor(recordingQuality) }}
                >
                    <option value="high">High (1920x1080, 30fps, 4Mbps)</option>
                    <option value="medium">Medium (1280x720, 25fps, 2Mbps)</option>
                    <option value="low">Low (640x480, 15fps, 1Mbps)</option>
                </select>
            </div>

            {recordingStatus && (
                <div className="recording-details">
                    <div className="detail-row">
                        <span className="detail-label">Resolution:</span>
                        <span className="detail-value">{recordingStatus.resolution}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">FPS:</span>
                        <span className="detail-value">{recordingStatus.fps}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">Bitrate:</span>
                        <span className="detail-value">{recordingStatus.bitrate}</span>
                    </div>
                    {recordingStatus.recording_service_status === 'unavailable' && (
                        <div className="service-warning">
                            ⚠️ Recording service unavailable
                        </div>
                    )}
                </div>
            )}

            {(isLoading || isUpdating) && (
                <div className="loading-overlay">
                    <div className="loading-spinner"></div>
                    <span>{isUpdating ? 'Updating...' : 'Loading...'}</span>
                </div>
            )}
        </div>
    );
}

export default RecordingControls;