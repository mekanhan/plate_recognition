# Web Dashboard

## Prerequisites
- Database setup complete (Document 04)
- FastAPI backend running
- Node.js 16+ for frontend development

## Overview
Build a web dashboard that displays detection data, analytics, and video playback. NO live streaming - only data visualization and recorded video playback.

## Backend API

### 1. FastAPI Application

```python
# api/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
from pathlib import Path

app = FastAPI(title="LPR Dashboard API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for images
app.mount("/images", StaticFiles(directory="detections"), name="images")

# Database service instance
from database.service import DatabaseService
db = DatabaseService("postgresql+asyncpg://user:pass@localhost/lpr")

@app.get("/api/detections/recent")
async def get_recent_detections(
    limit: int = Query(100, ge=1, le=500),
    camera_id: Optional[str] = None
):
    """Get recent detections with images"""
    detections = await db.get_recent_detections(limit)
    
    return [{
        "id": str(d.id),
        "camera_id": d.camera_id,
        "plate_text": d.plate_text,
        "confidence": d.confidence,
        "vehicle_type": d.vehicle_type,
        "detected_at": d.detected_at.isoformat(),
        "plate_image": f"/images/plates/{d.id}_plate.jpg",
        "has_video": d.video_clip_id is not None,
        "video_clip_id": str(d.video_clip_id) if d.video_clip_id else None
    } for d in detections]

@app.get("/api/detections/search")
async def search_detections(
    plate: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    camera_id: Optional[str] = None
):
    """Search detections by criteria"""
    # Implementation here
    pass

@app.get("/api/cameras")
async def get_cameras():
    """Get all cameras with current status"""
    cameras = await db.get_all_cameras()
    
    # Get current status from camera manager
    from camera_manager import camera_manager
    
    return [{
        "id": c.camera_id,
        "name": c.name,
        "location": c.location,
        "status": camera_manager.get_camera(c.camera_id).is_healthy() 
                  if camera_manager.get_camera(c.camera_id) else "offline",
        "ip_address": str(c.ip_address),
        "last_detection": await db.get_last_detection_time(c.camera_id)
    } for c in cameras]

@app.get("/api/cameras/{camera_id}/snapshot")
async def get_camera_snapshot(camera_id: str):
    """Get current camera snapshot"""
    from camera_manager import camera_manager
    
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    frame = camera.get_snapshot()
    if frame is None:
        return FileResponse("static/camera_offline.jpg")
    
    # Convert frame to JPEG
    import cv2
    _, buffer = cv2.imencode('.jpg', frame)
    
    return StreamingResponse(
        io.BytesIO(buffer.tobytes()),
        media_type="image/jpeg"
    )

@app.get("/api/analytics/overview")
async def get_analytics_overview():
    """Get dashboard analytics"""
    now = datetime.now()
    
    return {
        "total_detections_today": await db.count_detections(
            start_time=now.replace(hour=0, minute=0),
            end_time=now
        ),
        "unique_plates_today": await db.count_unique_plates(
            start_time=now.replace(hour=0, minute=0),
            end_time=now
        ),
        "active_cameras": await db.count_active_cameras(),
        "storage_used_gb": await db.get_storage_usage() / 1024,
        "hourly_trend": await db.get_hourly_trend(now - timedelta(days=1), now),
        "top_vehicles": await db.get_top_vehicle_types(limit=5)
    }

@app.get("/api/video/clip/{clip_id}")
async def get_video_clip(clip_id: str):
    """Serve video clip for playback"""
    clip = await db.get_video_clip(clip_id)
    if not clip:
        raise HTTPException(404, "Video clip not found")
    
    return FileResponse(
        clip.file_path,
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"inline; filename=clip_{clip_id}.mp4",
            "Accept-Ranges": "bytes"
        }
    )

@app.get("/api/video/recording/{recording_id}")
async def get_video_recording(
    recording_id: str,
    start: Optional[int] = None,
    end: Optional[int] = None
):
    """Serve full video recording with range support"""
    recording = await db.get_video_recording(recording_id)
    if not recording:
        raise HTTPException(404, "Recording not found")
    
    return FileResponse(
        recording.file_path,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(recording.file_size_mb * 1024 * 1024)
        }
    )
```

## Frontend Dashboard

### 1. React Application Structure

```jsx
// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Detections from './pages/Detections';
import Cameras from './pages/Cameras';
import VideoPlayback from './pages/VideoPlayback';
import Layout from './components/Layout';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/detections" element={<Detections />} />
          <Route path="/cameras" element={<Cameras />} />
          <Route path="/playback/:detectionId" element={<VideoPlayback />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
```

### 2. Dashboard Component

```jsx
// src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import StatCard from '../components/StatCard';
import RecentDetections from '../components/RecentDetections';
import CameraGrid from '../components/CameraGrid';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/analytics/overview`);
      setAnalytics(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h1>License Plate Recognition Dashboard</h1>
      
      {/* Statistics Cards */}
      <div className="stats-grid">
        <StatCard
          title="Detections Today"
          value={analytics.total_detections_today}
          icon="🚗"
          trend="+12%"
        />
        <StatCard
          title="Unique Plates"
          value={analytics.unique_plates_today}
          icon="🔢"
        />
        <StatCard
          title="Active Cameras"
          value={`${analytics.active_cameras.active}/${analytics.active_cameras.total}`}
          icon="📹"
        />
        <StatCard
          title="Storage Used"
          value={`${analytics.storage_used_gb.toFixed(1)} GB`}
          icon="💾"
        />
      </div>

      {/* Hourly Trend Chart */}
      <div className="chart-container">
        <h2>Detection Trend (24 Hours)</h2>
        <LineChart width={800} height={300} data={analytics.hourly_trend}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="hour" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="detections" stroke="#8884d8" />
        </LineChart>
      </div>

      <div className="dashboard-grid">
        {/* Camera Snapshots */}
        <div className="cameras-section">
          <h2>Cameras</h2>
          <CameraGrid />
        </div>

        {/* Recent Detections */}
        <div className="detections-section">
          <h2>Recent Detections</h2>
          <RecentDetections limit={10} />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
```

### 3. Camera Grid Component (Snapshots, NOT Live)

```jsx
// src/components/CameraGrid.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function CameraGrid() {
  const [cameras, setCameras] = useState([]);
  const [snapshots, setSnapshots] = useState({});

  useEffect(() => {
    fetchCameras();
    const interval = setInterval(updateSnapshots, 5000); // Update every 5s
    return () => clearInterval(interval);
  }, []);

  const fetchCameras = async () => {
    const response = await axios.get(`${API_BASE}/api/cameras`);
    setCameras(response.data);
    updateSnapshots(response.data);
  };

  const updateSnapshots = async (cameraList = cameras) => {
    const newSnapshots = {};
    for (const camera of cameraList) {
      if (camera.status === 'online') {
        // Add timestamp to prevent caching
        newSnapshots[camera.id] = `${API_BASE}/api/cameras/${camera.id}/snapshot?t=${Date.now()}`;
      }
    }
    setSnapshots(newSnapshots);
  };

  return (
    <div className="camera-grid">
      {cameras.map(camera => (
        <div key={camera.id} className="camera-card">
          <div className="camera-header">
            <h3>{camera.name}</h3>
            <span className={`status ${camera.status}`}>
              {camera.status === 'online' ? '🟢' : '🔴'} {camera.status}
            </span>
          </div>
          
          <div className="camera-snapshot">
            {camera.status === 'online' ? (
              <img 
                src={snapshots[camera.id]} 
                alt={camera.name}
                onError={(e) => {
                  e.target.src = '/camera-offline.png';
                }}
              />
            ) : (
              <div className="offline-placeholder">
                <p>Camera Offline</p>
              </div>
            )}
          </div>
          
          <div className="camera-info">
            <p>{camera.location}</p>
            <p>Last detection: {camera.last_detection || 'Never'}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default CameraGrid;
```

### 4. Video Playback Component

```jsx
// src/components/VideoPlayback.jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

function VideoPlayback() {
  const { detectionId } = useParams();
  const [detection, setDetection] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);

  useEffect(() => {
    fetchDetection();
  }, [detectionId]);

  const fetchDetection = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/detections/${detectionId}`);
      setDetection(response.data);
      
      if (response.data.video_clip_id) {
        setVideoUrl(`${API_BASE}/api/video/clip/${response.data.video_clip_id}`);
      }
    } catch (error) {
      console.error('Failed to fetch detection:', error);
    }
  };

  if (!detection) return <div>Loading...</div>;

  return (
    <div className="video-playback">
      <h1>Detection Details</h1>
      
      <div className="playback-grid">
        <div className="video-section">
          <h2>Video Clip</h2>
          {videoUrl ? (
            <video 
              controls 
              autoPlay 
              style={{ width: '100%', maxWidth: '800px' }}
            >
              <source src={videoUrl} type="video/mp4" />
              Your browser does not support video playback.
            </video>
          ) : (
            <p>No video available for this detection</p>
          )}
        </div>
        
        <div className="detection-info">
          <h2>Detection Information</h2>
          <dl>
            <dt>Plate Number:</dt>
            <dd>{detection.plate_text}</dd>
            
            <dt>Confidence:</dt>
            <dd>{(detection.confidence * 100).toFixed(1)}%</dd>
            
            <dt>Vehicle Type:</dt>
            <dd>{detection.vehicle_type}</dd>
            
            <dt>Camera:</dt>
            <dd>{detection.camera_name}</dd>
            
            <dt>Time:</dt>
            <dd>{new Date(detection.detected_at).toLocaleString()}</dd>
          </dl>
          
          <div className="plate-image">
            <h3>License Plate</h3>
            <img 
              src={`${API_BASE}${detection.plate_image}`} 
              alt="License plate"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default VideoPlayback;
```

### 5. CSS Styling

```css
/* src/styles/dashboard.css */
.dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.camera-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.camera-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.camera-snapshot {
  width: 100%;
  height: 200px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-snapshot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status.online { color: #4CAF50; }
.status.offline { color: #f44336; }

/* Video playback */
.video-section video {
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.detection-info dl {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 10px;
}

.plate-image img {
  max-width: 300px;
  border: 2px solid #ddd;
  border-radius: 4px;
}
```

## Common Pitfalls

### ❌ DON'T:
1. Try to stream live video to the dashboard
2. Poll APIs too frequently (wastes resources)
3. Load all detections at once (pagination!)
4. Store video URLs in state (memory leak)

### ✅ DO:
1. Show snapshots that update periodically
2. Use WebSocket for real-time updates (optional)
3. Implement proper pagination and filtering
4. Stream video clips on demand

## Performance Tips

1. **Image Optimization**: Compress snapshots before serving
2. **Lazy Loading**: Load images/videos only when visible
3. **Caching**: Cache static resources and API responses
4. **Pagination**: Never load more than 100 items at once

## Next Steps

Continue to: **[06 - Live View Solutions](./06-live-view-solutions.md)**

---

*AI Agent Note: This dashboard shows data and recorded clips. For live video viewing, use VLC or native apps as described in the next document.*