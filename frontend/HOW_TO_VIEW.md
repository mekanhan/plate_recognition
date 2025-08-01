# How to View the LPR Frontend

## 🚀 Quick Start - New Method (Recommended)

The frontend is now automatically served as part of the complete LPR system:

```bash
# From project root directory
cd /home/mekanhan/github/learning/plate_recognition
python3 start_lpr.py
```

Then access: **http://localhost:8080/**

This starts all three services:
- ✅ Main API (Port 8001)
- ✅ Recording Service (Port 8002)  
- ✅ Frontend Server (Port 8080)

## 📁 Current Frontend Structure

```
frontend/
├── index.html              # Main dashboard
├── cameras.html            # Camera management page
├── recordings.html         # Recording playback interface
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── recordings/    # Recording-specific components
│   │   └── streaming/     # Camera viewing components
│   ├── services/          # API communication layer
│   ├── styles/            # CSS architecture
│   └── config/            # Configuration files
└── assets/                # Static resources (images, fonts)
```

## 🎯 What You'll See

### **Dashboard** (http://localhost:8080/)
- System overview with live metrics
- Camera grid showing current snapshots
- Recent license plate detections
- System health status
- Quick navigation to other pages

### **Camera Management** (http://localhost:8080/cameras.html)
- Add/edit/delete cameras through web UI
- Test camera connections before saving
- Real-time camera status monitoring
- Bulk operations for multiple cameras
- Camera configuration wizard

### **Recording Playback** (http://localhost:8080/recordings.html)
- Calendar view for browsing recordings by date
- Timeline control for navigating 24-hour periods
- Video playback of 10-minute segments
- Detection markers showing when plates were found
- Multi-camera playback support

## 🔧 Manual Frontend Server (Alternative)

If you need to run just the frontend server manually:

```bash
# From project root
cd frontend
python3 -m http.server 8080
```

Then access: http://localhost:8080/

## 🎨 Key Features

### Dynamic Camera Management
- **Web-based Configuration**: No more editing config files
- **Connection Testing**: Validate camera settings before saving
- **Real-time Status**: Live camera health monitoring
- **Automatic Integration**: Cameras configured via UI are automatically used by recording service

### Recording System Integration
- **24/7 Recording**: Continuous recording to 10-minute segments
- **Calendar Navigation**: Browse recordings by date
- **Timeline Playback**: Scrub through 24-hour timeline
- **Detection Events**: See when license plates were detected

### Modern UI Architecture
- **Component-based**: Modular, reusable components
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Themes**: Automatic theme switching
- **Real-time Updates**: Live data from backend services

## 🔌 Backend Integration

The frontend integrates with two backend services:

### Main API Service (Port 8001)
- Camera management endpoints
- License plate detection results
- System health and status
- Camera snapshot serving

### Recording Service (Port 8002)
- Recording segment management
- Video playback streaming
- Recording metadata and statistics
- Storage management

## 🚨 Important Notes

1. **No Browser Video Streaming**: The system shows camera snapshots, not live video
2. **VLC Integration**: Use "Open in VLC" buttons for live RTSP streams
3. **Database-driven**: All camera configurations are stored in SQLite database
4. **Auto-refresh**: Camera views and status update automatically

## 🐛 Troubleshooting

### Frontend Not Loading
1. Ensure the system is running: `python3 start_lpr.py`
2. Check service status: `python3 check_services.py`
3. Verify port 8080 is not blocked by firewall
4. Clear browser cache and reload

### Camera Shows "Offline"
1. Check camera configuration in the Cameras page
2. Test camera connection using the "Test" button
3. Verify network connectivity to camera
4. Check Main API service logs: `tail -f logs/main_api_*.log`

### Recordings Not Playing
1. Ensure Recording Service is running (port 8002)
2. Check if recordings exist for the selected date
3. Verify browser supports the video codec
4. Check Recording Service logs: `tail -f logs/recording_service_*.log`

## 🧑‍💻 Development Mode

For development with live reload, you can use tools like:

### Live Server (VS Code Extension)
1. Install "Live Server" extension
2. Right-click on `frontend/index.html`
3. Select "Open with Live Server"

### Node.js http-server
```bash
npm install -g http-server
cd frontend
http-server -p 8080
```

## 📱 Mobile Experience

The interface is fully responsive:
- **Desktop**: Full sidebar with all features
- **Tablet**: Collapsible sidebar, touch-friendly controls
- **Mobile**: Bottom navigation, stacked layouts, optimized for touch

## 🔄 Service Integration Testing

To verify everything is working correctly:

```bash
# Check all services are healthy
python3 check_services.py

# Test camera management
curl http://localhost:8001/api/cameras/

# Test recording service
curl http://localhost:8002/health

# Test frontend server
curl http://localhost:8080/
```

## 🎉 Production Deployment

For production deployment:

1. **Configure Environment**: Set production API endpoints in `src/config/app.config.js`
2. **Secure Services**: Add authentication and HTTPS
3. **Optimize Assets**: Minify CSS/JS and optimize images
4. **Monitor Services**: Use the built-in health checking for monitoring

The frontend now provides a complete, integrated experience for managing cameras, monitoring the system, and reviewing recorded footage.