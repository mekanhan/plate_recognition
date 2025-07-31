import React from 'react';
import SystemHealthDashboard from '../components/system/SystemHealthDashboard';

function SystemHealthPage() {
    return (
        <div className="page-container">
            <div className="page-header">
                <h1>System Health & Status</h1>
                <p>Monitor the health and performance of your LPR system components</p>
            </div>
            
            <div className="page-content">
                <SystemHealthDashboard />
                
                <div className="health-tips">
                    <h3>💡 Health Tips</h3>
                    <ul>
                        <li><strong>Camera Offline:</strong> Check RTSP credentials and network connectivity</li>
                        <li><strong>High Frame Age:</strong> Camera may be experiencing network issues</li>
                        <li><strong>AI Models Not Loaded:</strong> Check GPU availability and model files</li>
                        <li><strong>Recording Service Unavailable:</strong> Start the 24/7 recording service on port 8002</li>
                        <li><strong>Database Issues:</strong> Verify SQLite database file permissions</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

export default SystemHealthPage;