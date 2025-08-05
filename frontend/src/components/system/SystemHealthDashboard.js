import React, { useState, useEffect } from 'react';
import config from '../../config/app.config.js';

function SystemHealthDashboard() {
    const [systemHealth, setSystemHealth] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [autoRefresh, setAutoRefresh] = useState(true);

    useEffect(() => {
        fetchSystemHealth();
        
        let interval;
        if (autoRefresh) {
            interval = setInterval(fetchSystemHealth, 10000); // Update every 10 seconds
        }
        
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [autoRefresh]);

    const fetchSystemHealth = async () => {
        try {
            const response = await fetch(config.buildApiUrl('/api/system/health'));
            if (response.ok) {
                const data = await response.json();
                setSystemHealth(data);
                setLastUpdate(new Date());
            }
        } catch (error) {
            console.error('Failed to fetch system health:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const getStatusColor = (status) => {
        if (typeof status === 'boolean') {
            return status ? '#4CAF50' : '#f44336';
        }
        switch (status?.toLowerCase()) {
            case 'healthy':
            case 'running':
            case 'connected':
            case 'online':
                return '#4CAF50';
            case 'offline':
            case 'disconnected':
                return '#f44336';
            case 'warning':
                return '#ff9800';
            default:
                return '#9e9e9e';
        }
    };

    const getStatusIcon = (status) => {
        if (typeof status === 'boolean') {
            return status ? '✅' : '❌';
        }
        switch (status?.toLowerCase()) {
            case 'healthy':
            case 'running':
            case 'connected':
            case 'online':
                return '✅';
            case 'offline':
            case 'disconnected':
                return '❌';
            case 'warning':
                return '⚠️';
            default:
                return '❓';
        }
    };

    if (isLoading) {
        return (
            <div className="system-health-dashboard loading">
                <div className="loading-spinner"></div>
                <p>Loading system health...</p>
            </div>
        );
    }

    if (!systemHealth) {
        return (
            <div className="system-health-dashboard error">
                <h3>⚠️ System Health Unavailable</h3>
                <p>Cannot connect to backend API</p>
                <button onClick={fetchSystemHealth}>Retry</button>
            </div>
        );
    }

    return (
        <div className="system-health-dashboard">
            <div className="dashboard-header">
                <h3>🏥 System Health Dashboard</h3>
                <div className="header-controls">
                    <label className="auto-refresh-toggle">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                        />
                        Auto Refresh
                    </label>
                    <button className="refresh-btn" onClick={fetchSystemHealth}>
                        🔄 Refresh
                    </button>
                </div>
            </div>

            {lastUpdate && (
                <div className="last-update">
                    Last updated: {lastUpdate.toLocaleTimeString()}
                </div>
            )}

            <div className="health-sections">
                {/* Core System Status */}
                <div className="health-section">
                    <h4>🖥️ Core System</h4>
                    <div className="status-grid">
                        <div className="status-item">
                            <span className="status-icon">
                                {getStatusIcon(systemHealth.api_status)}
                            </span>
                            <span className="status-label">API Server</span>
                            <span 
                                className="status-value"
                                style={{ color: getStatusColor(systemHealth.api_status) }}
                            >
                                {systemHealth.api_status}
                            </span>
                        </div>
                        <div className="status-item">
                            <span className="status-icon">
                                {getStatusIcon(systemHealth.database_status)}
                            </span>
                            <span className="status-label">Database</span>
                            <span 
                                className="status-value"
                                style={{ color: getStatusColor(systemHealth.database_status) }}
                            >
                                {systemHealth.database_status}
                            </span>
                        </div>
                        <div className="status-item">
                            <span className="status-icon">
                                {getStatusIcon(systemHealth.camera_manager_status)}
                            </span>
                            <span className="status-label">Camera Manager</span>
                            <span 
                                className="status-value"
                                style={{ color: getStatusColor(systemHealth.camera_manager_status) }}
                            >
                                {systemHealth.camera_manager_status}
                            </span>
                        </div>
                        <div className="status-item">
                            <span className="status-icon">
                                {getStatusIcon(systemHealth.processing_loop_status)}
                            </span>
                            <span className="status-label">Processing Loop</span>
                            <span 
                                className="status-value"
                                style={{ color: getStatusColor(systemHealth.processing_loop_status) }}
                            >
                                {systemHealth.processing_loop_status}
                            </span>
                        </div>
                    </div>
                </div>

                {/* AI Models Status */}
                <div className="health-section">
                    <h4>🤖 AI Models</h4>
                    <div className="status-grid">
                        <div className="status-item">
                            <span className="status-icon">
                                {getStatusIcon(systemHealth.ai_models_loaded?.yolo_vehicle)}
                            </span>
                            <span className="status-label">YOLO Vehicle</span>
                            <span 
                                className="status-value"
                                style={{ color: getStatusColor(systemHealth.ai_models_loaded?.yolo_vehicle) }}
                            >
                                {systemHealth.ai_models_loaded?.yolo_vehicle ? 'Loaded' : 'Not Loaded'}
                            </span>
                        </div>
                        <div className="status-item">
                            <span className="status-icon">
                                {getStatusIcon(systemHealth.ai_models_loaded?.yolo_plate)}
                            </span>
                            <span className="status-label">YOLO Plate</span>
                            <span 
                                className="status-value"
                                style={{ color: getStatusColor(systemHealth.ai_models_loaded?.yolo_plate) }}
                            >
                                {systemHealth.ai_models_loaded?.yolo_plate ? 'Loaded' : 'Not Loaded'}
                            </span>
                        </div>
                        <div className="status-item">
                            <span className="status-icon">
                                {getStatusIcon(systemHealth.ai_models_loaded?.ocr_reader)}
                            </span>
                            <span className="status-label">OCR Reader</span>
                            <span 
                                className="status-value"
                                style={{ color: getStatusColor(systemHealth.ai_models_loaded?.ocr_reader) }}
                            >
                                {systemHealth.ai_models_loaded?.ocr_reader ? 'Loaded' : 'Not Loaded'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Camera Summary */}
                <div className="health-section">
                    <h4>📹 Cameras ({systemHealth.total_cameras} total)</h4>
                    <div className="cameras-summary">
                        {systemHealth.cameras?.map((camera, index) => (
                            <div key={camera.camera_id} className="camera-summary-item">
                                <span className="camera-icon">
                                    {getStatusIcon(camera.status)}
                                </span>
                                <div className="camera-info">
                                    <span className="camera-name">{camera.name}</span>
                                    <span 
                                        className="camera-status"
                                        style={{ color: getStatusColor(camera.status) }}
                                    >
                                        {camera.status}
                                        {camera.last_frame_age !== null && (
                                            <small> ({Math.round(camera.last_frame_age)}s ago)</small>
                                        )}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SystemHealthDashboard;