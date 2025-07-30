# Live View Solutions

## Prerequisites
- Camera integration working (Document 02)
- Web dashboard running (Document 05)
- Understanding that browsers can't handle RTSP well

## Overview
This guide provides multiple solutions for viewing live camera feeds using appropriate tools, NOT web browsers.

## Solution 1: VLC Media Player (Simplest)

### Direct RTSP Viewing

```bash
# Command line
vlc rtsp://admin:password@10.0.0.181:554/stream

# Or with GUI
1. Open VLC
2. Media → Open Network Stream
3. Enter RTSP URL
4. Play
```

### VLC Mosaic for Multiple Cameras

```bash
# Create VLC playlist file: cameras.xspf
<?xml version="1.0" encoding="UTF-8"?>
<playlist xmlns="http://www.videolan.org/vlc/playlist/ns/0/" version="1">
  <title>Security Cameras</title>
  <trackList>
    <track>
      <location>rtsp://admin:pass@10.0.0.181:554/stream</location>
      <title>Entrance Camera</title>
    </track>
    <track>
      <location>rtsp://admin:pass@10.0.0.182:554/stream</location>
      <title>Exit Camera</title>
    </track>
  </trackList>
</playlist>

# Play all cameras
vlc cameras.xspf
```

### Web Interface Integration

```python
# api/vlc_launcher.py
import subprocess
import platform
from typing import List

class VLCLauncher:
    """Launch VLC from web interface"""
    
    def __init__(self):
        self.vlc_path = self._find_vlc()
        
    def _find_vlc(self) -> str:
        """Find VLC installation"""
        system = platform.system()
        
        if system == "Windows":
            paths = [
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
            ]
        elif system == "Darwin":  # macOS
            paths = ["/Applications/VLC.app/Contents/MacOS/VLC"]
        else:  # Linux
            paths = ["/usr/bin/vlc", "/usr/local/bin/vlc"]
            
        for path in paths:
            if os.path.exists(path):
                return path
                
        return "vlc"  # Hope it's in PATH
    
    def launch_camera(self, camera_url: str, title: str = ""):
        """Launch single camera in VLC"""
        cmd = [
            self.vlc_path,
            camera_url,
            "--meta-title", title,
            "--no-video-title-show"
        ]
        subprocess.Popen(cmd)
    
    def launch_mosaic(self, cameras: List[Dict[str, str]]):
        """Launch multiple cameras in grid"""
        # Create temporary playlist
        playlist = self._create_playlist(cameras)
        
        cmd = [
            self.vlc_path,
            playlist,
            "--intf", "qt",
            "--no-video-title-show"
        ]
        subprocess.Popen(cmd)

# Add API endpoint
@app.post("/api/cameras/{camera_id}/open-vlc")
async def open_camera_in_vlc(camera_id: str):
    """Open camera in VLC player"""
    camera = await db.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, "Camera not found")
    
    launcher = VLCLauncher()
    camera_url = f"rtsp://{camera.username}:{camera.password}@{camera.ip_address}:554{camera.stream_path}"
    launcher.launch_camera(camera_url, camera.name)
    
    return {"status": "launched", "player": "vlc"}
```

### Frontend Integration

```jsx
// components/LiveViewButton.jsx
import React from 'react';
import axios from 'axios';

function LiveViewButton({ camera }) {
  const handleOpenVLC = async () => {
    try {
      await axios.post(`/api/cameras/${camera.id}/open-vlc`);
      // Show notification
      toast.success('Opening camera in VLC...');
    } catch (error) {
      // Fallback to manual method
      const rtspUrl = `rtsp://${camera.username}:${camera.password}@${camera.ip_address}:554${camera.stream_path}`;
      
      // Try browser protocol handler
      window.location.href = `vlc://${rtspUrl}`;
      
      // Show manual instructions
      setShowManualInstructions(true);
    }
  };
  
  return (
    <button onClick={handleOpenVLC} className="live-view-btn">
      <i className="fas fa-play"></i> Open in VLC
    </button>
  );
}
```

## Solution 2: Native Desktop Application

### PyQt5 Application

```python
# native_viewer/main.py
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import numpy as np
from datetime import datetime

class CameraWidget(QWidget):
    """Widget for displaying single camera"""
    
    def __init__(self, camera_config):
        super().__init__()
        self.camera_config = camera_config
        self.capture = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        self.title_label = QLabel(self.camera_config['name'])
        self.title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.title_label)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setScaledContents(True)
        self.video_label.setStyleSheet("border: 1px solid #ccc;")
        layout.addWidget(self.video_label)
        
        # Status bar
        self.status_label = QLabel("Connecting...")
        layout.addWidget(self.status_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Connect")
        self.play_button.clicked.connect(self.toggle_stream)
        controls_layout.addWidget(self.play_button)
        
        self.snapshot_button = QPushButton("Snapshot")
        self.snapshot_button.clicked.connect(self.take_snapshot)
        controls_layout.addWidget(self.snapshot_button)
        
        self.fullscreen_button = QPushButton("Fullscreen")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        controls_layout.addWidget(self.fullscreen_button)
        
        layout.addLayout(controls_layout)
        self.setLayout(layout)
        
    def toggle_stream(self):
        if self.capture is None:
            self.start_stream()
        else:
            self.stop_stream()
            
    def start_stream(self):
        url = f"rtsp://{self.camera_config['username']}:{self.camera_config['password']}@" \
              f"{self.camera_config['ip_address']}:554{self.camera_config['stream_path']}"
        
        self.capture = cv2.VideoCapture(url)
        if self.capture.isOpened():
            self.timer.start(33)  # ~30 FPS
            self.play_button.setText("Disconnect")
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Connection failed")
            self.status_label.setStyleSheet("color: red;")
            
    def stop_stream(self):
        self.timer.stop()
        if self.capture:
            self.capture.release()
            self.capture = None
        self.play_button.setText("Connect")
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: gray;")
        
    def update_frame(self):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                # Convert frame to Qt format
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                # Scale to widget size
                pixmap = QPixmap.fromImage(qt_image)
                scaled_pixmap = pixmap.scaled(self.video_label.size(), 
                                             Qt.KeepAspectRatio, 
                                             Qt.SmoothTransformation)
                self.video_label.setPixmap(scaled_pixmap)
                
                # Update FPS
                self.status_label.setText(f"Connected - {w}x{h}")
            else:
                self.status_label.setText("Frame read error")
                
    def take_snapshot(self):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapshot_{self.camera_config['name']}_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                QMessageBox.information(self, "Snapshot", f"Saved: {filename}")
                
    def toggle_fullscreen(self):
        # Implement fullscreen logic
        pass


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.camera_widgets = []
        self.init_ui()
        self.load_cameras()
        
    def init_ui(self):
        self.setWindowTitle("LPR Live Viewer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(central_widget)
        
        # Camera grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.main_layout.addWidget(self.grid_widget)
        
        # Menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        refresh_action = QAction('Refresh Cameras', self)
        refresh_action.triggered.connect(self.load_cameras)
        file_menu.addAction(refresh_action)
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        grid_1x1 = QAction('1x1 Grid', self)
        grid_1x1.triggered.connect(lambda: self.set_grid_layout(1, 1))
        view_menu.addAction(grid_1x1)
        
        grid_2x2 = QAction('2x2 Grid', self)
        grid_2x2.triggered.connect(lambda: self.set_grid_layout(2, 2))
        view_menu.addAction(grid_2x2)
        
        grid_3x3 = QAction('3x3 Grid', self)
        grid_3x3.triggered.connect(lambda: self.set_grid_layout(3, 3))
        view_menu.addAction(grid_3x3)
        
    def load_cameras(self):
        # Load from API
        import requests
        
        try:
            response = requests.get('http://localhost:8000/api/cameras')
            cameras = response.json()
            
            # Clear existing widgets
            for widget in self.camera_widgets:
                widget.stop_stream()
                widget.deleteLater()
            self.camera_widgets.clear()
            
            # Create camera widgets
            for i, camera in enumerate(cameras):
                widget = CameraWidget(camera)
                self.camera_widgets.append(widget)
                
                # Add to grid
                row = i // 2
                col = i % 2
                self.grid_layout.addWidget(widget, row, col)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load cameras: {e}")
            
    def set_grid_layout(self, rows, cols):
        # Rearrange cameras in new grid
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        for i, widget in enumerate(self.camera_widgets[:rows*cols]):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(widget, row, col)
            
    def closeEvent(self, event):
        # Clean up all streams
        for widget in self.camera_widgets:
            widget.stop_stream()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
```

### Distribution

```python
# setup.py for PyInstaller
# pip install pyinstaller
# pyinstaller --onefile --windowed native_viewer/main.py

import PyInstaller.__main__

PyInstaller.__main__.run([
    'native_viewer/main.py',
    '--onefile',
    '--windowed',
    '--name=LPR_Live_Viewer',
    '--icon=icon.ico',
    '--add-data=config;config'
])
```

## Solution 3: Web-Based HLS Streaming (Compromise)

If you absolutely need some form of browser viewing:

```python
# services/hls_service.py
import subprocess
import os
from pathlib import Path

class HLSStreamingService:
    """Convert RTSP to HLS for delayed browser viewing"""
    
    def __init__(self, output_dir: str = "static/streams"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.processes = {}
        
    def start_hls_stream(self, camera_id: str, rtsp_url: str):
        """Start FFmpeg HLS conversion"""
        output_path = self.output_dir / camera_id
        output_path.mkdir(exist_ok=True)
        
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-c:v', 'copy',  # Don't re-encode if possible
            '-c:a', 'copy',
            '-f', 'hls',
            '-hls_time', '2',
            '-hls_list_size', '3',
            '-hls_flags', 'delete_segments',
            '-hls_segment_filename', str(output_path / 'segment_%03d.ts'),
            str(output_path / 'playlist.m3u8')
        ]
        
        process = subprocess.Popen(cmd)
        self.processes[camera_id] = process
        
    def stop_hls_stream(self, camera_id: str):
        """Stop HLS conversion"""
        if camera_id in self.processes:
            self.processes[camera_id].terminate()
            del self.processes[camera_id]

# Frontend HLS player
"""
<video id="video" controls></video>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
  var video = document.getElementById('video');
  var videoSrc = '/static/streams/camera1/playlist.m3u8';
  
  if (Hls.isSupported()) {
    var hls = new Hls();
    hls.loadSource(videoSrc);
    hls.attachMedia(video);
  } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = videoSrc;
  }
</script>
"""
```

## Solution 4: Mobile App

```javascript
// React Native app for mobile viewing
import React from 'react';
import { View, Text } from 'react-native';
import { VLCPlayer } from 'react-native-vlc-media-player';

export default function CameraView({ route }) {
  const { camera } = route.params;
  const rtspUrl = `rtsp://${camera.username}:${camera.password}@${camera.ip}:554${camera.path}`;
  
  return (
    <View style={{ flex: 1 }}>
      <Text style={{ padding: 10, fontSize: 18 }}>{camera.name}</Text>
      <VLCPlayer
        style={{ flex: 1 }}
        source={{ uri: rtspUrl }}
        autoplay={true}
      />
    </View>
  );
}
```

## Comparison Matrix

| Solution | Pros | Cons | Best For |
|----------|------|------|----------|
| **VLC** | - Zero development<br>- Reliable<br>- Free | - Separate app<br>- No integration | Quick viewing |
| **Native App** | - Full control<br>- Best performance<br>- Custom features | - Development time<br>- Platform specific | Professional use |
| **HLS** | - Works in browser<br>- No plugins | - 10-30s delay<br>- Server resources | Remote access |
| **Mobile App** | - Portable<br>- Touch controls | - App store deployment<br>- Development cost | Field workers |

## Integration with Dashboard

```jsx
// components/CameraCard.jsx
function CameraCard({ camera }) {
  const [showLiveOptions, setShowLiveOptions] = useState(false);
  
  return (
    <div className="camera-card">
      <h3>{camera.name}</h3>
      
      {/* Snapshot */}
      <img src={`/api/cameras/${camera.id}/snapshot`} />
      
      {/* Live View Options */}
      <button onClick={() => setShowLiveOptions(!showLiveOptions)}>
        <i className="fas fa-video"></i> Live View Options
      </button>
      
      {showLiveOptions && (
        <div className="live-options">
          <button onClick={() => openInVLC(camera)}>
            <i className="fas fa-play"></i> VLC Player
          </button>
          
          <button onClick={() => openNativeApp(camera)}>
            <i className="fas fa-desktop"></i> Native App
          </button>
          
          <button onClick={() => copyRTSPUrl(camera)}>
            <i className="fas fa-copy"></i> Copy RTSP URL
          </button>
          
          <a href={`/guides/live-viewing`} target="_blank">
            <i className="fas fa-question"></i> Help
          </a>
        </div>
      )}
    </div>
  );
}
```

## Best Practices

1. **Default to VLC**: It's installed on most systems
2. **Provide Options**: Let users choose their preferred method
3. **Clear Instructions**: Help users understand why not in browser
4. **Fallback Methods**: Always provide manual RTSP URL
5. **Mobile Support**: Consider field workers needs

## Next Steps

Continue to: **[07 - Deployment Guide](./07-deployment-guide.md)**

---

*AI Agent Note: Live viewing is intentionally separated from the web interface. This is a feature, not a limitation - it ensures reliable, high-quality video viewing.*