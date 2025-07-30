Fixed Card Display System
Concept
Camera 1: 4K (3840x2160) ┐
Camera 2: 1080p (1920x1080) ├── All display as → 640x480 cards
Camera 3: 720p (1280x720) ┘
Implementation
1. Update streaming.py
python# Fixed card dimensions
CARD_WIDTH = 640
CARD_HEIGHT = 480

def generate_mjpeg(camera_id: str):
    """Generate MJPEG stream at fixed card size"""
    camera = camera_manager.get_camera(camera_id)
    
    while True:
        frame = camera.get_latest_frame()
        if frame is None:
            continue
        
        # Get original dimensions
        height, width = frame.shape[:2]
        
        # Calculate scaling to fit in card while maintaining aspect ratio
        scale = min(CARD_WIDTH / width, CARD_HEIGHT / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize frame
        frame_resized = cv2.resize(frame, (new_width, new_height))
        
        # Create black canvas of card size
        card = np.zeros((CARD_HEIGHT, CARD_WIDTH, 3), dtype=np.uint8)
        
        # Center the resized frame in the card
        y_offset = (CARD_HEIGHT - new_height) // 2
        x_offset = (CARD_WIDTH - new_width) // 2
        card[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = frame_resized
        
        # Add camera info overlay
        cv2.putText(card, f"{camera.camera_info['name']} ({width}x{height})", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Encode
        _, buffer = cv2.imencode('.jpg', card, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + 
               buffer.tobytes() + b'\r\n')

@router.get("/camera_info")
async def get_camera_info():
    """Get all camera information including native resolutions"""
    cameras = camera_manager.get_all_cameras()
    camera_info = []
    
    for cam_id, camera in cameras.items():
        if camera.cap and camera.cap.isOpened():
            # Get actual camera resolution
            width = int(camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(camera.cap.get(cv2.CAP_PROP_FPS))
        else:
            width = height = fps = 0
            
        camera_info.append({
            "id": cam_id,
            "name": camera.camera_info.get('name', cam_id),
            "native_resolution": f"{width}x{height}",
            "native_width": width,
            "native_height": height,
            "fps": fps,
            "status": "online" if camera.cap else "offline",
            "card_width": CARD_WIDTH,
            "card_height": CARD_HEIGHT
        })
    
    return {"cameras": camera_info}
2. Frontend HTML/CSS
html<!DOCTYPE html>
<html>
<head>
    <title>LPR Camera Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: #fff;
            margin: 0;
            padding: 20px;
        }
        
        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(660px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .camera-card {
            background: #2a2a2a;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .camera-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding: 0 5px;
        }
        
        .camera-name {
            font-size: 18px;
            font-weight: bold;
        }
        
        .camera-info {
            font-size: 12px;
            color: #888;
        }
        
        .camera-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        .status-online {
            background: #4ade80;
            color: #000;
        }
        
        .status-offline {
            background: #ef4444;
            color: #fff;
        }
        
        .camera-view {
            width: 640px;
            height: 480px;
            background: #000;
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }
        
        .camera-view img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        
        .camera-controls {
            margin-top: 10px;
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        
        .btn-primary:hover {
            background: #2563eb;
        }
        
        .resolution-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.7);
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>LPR System - Camera Dashboard</h1>
    <div id="camera-grid" class="camera-grid"></div>
    
    <script>
        async function loadCameras() {
            const response = await fetch('/api/streaming/camera_info');
            const data = await response.json();
            
            const grid = document.getElementById('camera-grid');
            grid.innerHTML = '';
            
            data.cameras.forEach(camera => {
                const card = document.createElement('div');
                card.className = 'camera-card';
                
                card.innerHTML = `
                    <div class="camera-header">
                        <div>
                            <div class="camera-name">${camera.name}</div>
                            <div class="camera-info">
                                Native: ${camera.native_resolution} @ ${camera.fps}fps
                            </div>
                        </div>
                        <span class="camera-status status-${camera.status}">
                            ${camera.status.toUpperCase()}
                        </span>
                    </div>
                    <div class="camera-view">
                        <img id="cam-${camera.id}" 
                             src="/api/streaming/video_feed/${camera.id}" 
                             alt="${camera.name}">
                        <div class="resolution-badge">${camera.native_resolution}</div>
                    </div>
                    <div class="camera-controls">
                        <button class="btn btn-primary" 
                                onclick="viewHighRes('${camera.id}')">
                            View Full Resolution
                        </button>
                        <button class="btn btn-primary" 
                                onclick="downloadSnapshot('${camera.id}')">
                            Download Snapshot
                        </button>
                    </div>
                `;
                
                grid.appendChild(card);
            });
        }
        
        function viewHighRes(cameraId) {
            // Open full resolution in new window
            window.open(`/api/streaming/snapshot/${cameraId}?fullres=true`, '_blank');
        }
        
        function downloadSnapshot(cameraId) {
            const link = document.createElement('a');
            link.href = `/api/streaming/snapshot/${cameraId}?fullres=true`;
            link.download = `camera_${cameraId}_${Date.now()}.jpg`;
            link.click();
        }
        
        // Load cameras on page load
        loadCameras();
        
        // Refresh camera info every 30 seconds
        setInterval(loadCameras, 30000);
    </script>
</body>
</html>
3. Add Full Resolution Snapshot Option
python@router.get("/snapshot/{camera_id}")
async def get_snapshot(camera_id: str, fullres: bool = False):
    """Get snapshot at card size or full resolution"""
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    frame = camera.get_latest_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="No frame available")
    
    if not fullres:
        # Return card-sized image
        frame = resize_to_card(frame)
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    return Response(
        content=buffer.tobytes(),
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache"}
    )
Benefits of This Approach

Uniform Display

All cameras look the same size
Clean, professional grid layout
No layout jumping when switching cameras


Performance

Same bandwidth for all cameras (640x480)
Predictable CPU usage
Smooth playback


Flexibility

Still record at full resolution
AI processes full resolution
Can view/download full res when needed


User Experience

See all cameras at once
Quick overview of system status
Access to full quality on-demand



