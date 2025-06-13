🎯 Immediate: Simple Multi-Camera Network

  Architecture:

  Computer (Hub) - Main LPR System
  ├── Primary webcam (local processing)
  ├── HTTP API: /api/camera/frame
  ├── Single SQLite database
  └── Web UI shows all cameras

  Network Cameras (Pixel 6A, etc.)
  ├── PWA in browser (computer_ip:8001/mobile)
  ├── Send frames via HTTP POST
  └── No local processing/storage

  Implementation Steps:

  1. Add camera endpoint to existing FastAPI
  2. Enhance database with camera_id field
  3. Create mobile PWA for camera streaming
  4. Update web UI to show multi-camera feeds
  5. Add camera management interface

  Benefits:

  - ✅ Minimal changes to current codebase
  - ✅ No Android app development needed
  - ✅ Works with any device with camera + browser
  - ✅ Easy to add more cameras
  - ✅ Centralized processing and storage

# A universal camera system that handles any video source - Android     
   devices, IP cameras, USB cameras, RTSP streams. Let me design a unified approach.      

  🎯 Universal Camera Architecture

  Core Concept: Camera Source Abstraction

  # Any device that can stream video becomes a "Camera Source"
  Camera Sources:
  ├── Android devices (PWA + camera)
  ├── IP cameras (RTSP/HTTP streams)
  ├── USB webcams (local)
  ├── WiFi security cameras
  ├── Raspberry Pi cameras
  └── Any device with video streaming capability

  🏗️ Dynamic Camera Discovery & Registration

  Auto-Discovery Protocol:

  # 1. Network scanning for camera sources
  discovery_methods = [
      "UPnP/SSDP discovery",    # IP cameras
      "mDNS/Bonjour",           # Apple devices, modern cameras
      "UDP broadcast",          # Custom protocol
      "QR code registration",   # Manual setup
      "HTTP beacon"             # PWA self-registration
  ]

  Universal Camera Registration:

  {
      "camera_id": "auto_generated_uuid",
      "name": "User defined name",
      "type": "android|ip_camera|usb|rtsp|pwa",
      "source_url": "rtsp://192.168.1.100/stream1",
      "capabilities": {
          "resolution": ["1920x1080", "1280x720"],
          "formats": ["h264", "mjpeg"],
          "controls": ["zoom", "focus", "exposure"]
      },
      "location": "front_entrance",
      "auto_discovered": true,
      "last_seen": "2025-01-15T10:30:00Z"
  }

  📱 Universal Android Solution

  Progressive Web App (PWA) Approach:

  // Universal camera client that works on ANY Android device
  // Accessible via: http://computer_ip:8001/camera

  class UniversalCameraClient {
      async initialize() {
          // Auto-detect device capabilities
          const capabilities = await this.detectCapabilities();

          // Register with main system
          await this.registerCamera({
              device_info: capabilities,
              camera_specs: await this.getCameraSpecs()
          });

          // Start streaming
          this.startVideoStream();
      }

      async detectCapabilities() {
          return {
              device_model: navigator.userAgent,
              screen_size: `${screen.width}x${screen.height}`,
              cameras: await navigator.mediaDevices.enumerateDevices(),
              network_info: await this.getNetworkInfo()
          };
      }
  }

  Dynamic Camera Interface:

  <!-- Auto-adapting mobile interface -->
  <!DOCTYPE html>
  <html>
  <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>LPR Camera - Dynamic Setup</title>
  </head>
  <body>
      <!-- Step 1: Auto-detection -->
      <div id="setup-screen">
          <h2>Camera Setup</h2>
          <p>Device: <span id="device-info">Detecting...</span></p>
          <p>Available cameras: <span id="camera-count">Scanning...</span></p>
          <button onclick="startSetup()">Connect as Camera</button>
      </div>

      <!-- Step 2: Camera streaming -->
      <div id="camera-screen" style="display:none">
          <video id="video-preview" autoplay playsinline></video>
          <div id="controls">
              <button onclick="toggleStream()">Start/Stop</button>
              <select id="camera-select"><!-- Populated dynamically --></select>
              <select id="quality-select">
                  <option value="720p">720p (Recommended)</option>
                  <option value="1080p">1080p (High Quality)</option>
                  <option value="480p">480p (Low Bandwidth)</option>
              </select>
          </div>
          <div id="status">Status: <span
  id="connection-status">Connecting...</span></div>
      </div>
  </body>
  </html>

  🌐 Universal Video Source Handling

  Unified Stream Processor:

  class UniversalStreamProcessor:
      def __init__(self):
          self.supported_sources = {
              'rtsp': self.handle_rtsp_stream,
              'http': self.handle_http_stream,
              'usb': self.handle_usb_camera,
              'pwa': self.handle_pwa_frames,
              'websocket': self.handle_websocket_stream
          }

      async def add_camera_source(self, source_config):
          """Dynamically add any type of camera source"""
          source_type = self.detect_source_type(source_config)
          handler = self.supported_sources[source_type]

          camera = {
              'id': str(uuid.uuid4()),
              'name': source_config.get('name', f'Camera_{len(self.cameras)}'),
              'type': source_type,
              'handler': handler,
              'config': source_config,
              'status': 'initializing'
          }

          await self.initialize_camera(camera)
          return camera['id']

      def detect_source_type(self, config):
          """Auto-detect camera source type"""
          if 'rtsp://' in config.get('url', ''):
              return 'rtsp'
          elif 'http://' in config.get('url', ''):
              return 'http'
          elif config.get('device_id') is not None:
              return 'usb'
          elif config.get('pwa_session'):
              return 'pwa'
          else:
              return 'websocket'

  Camera Source Examples:

  # IP Camera (Hikvision, Dahua, etc.)
  ip_camera = {
      'url': 'rtsp://192.168.1.100:554/stream1',
      'username': 'admin',
      'password': 'password',
      'name': 'Front Door Camera'
  }

  # Android PWA
  android_camera = {
      'pwa_session': True,
      'device_info': 'Pixel 6A',
      'name': 'Mobile Camera 1'
  }

  # USB Webcam
  usb_camera = {
      'device_id': 0,
      'name': 'Computer Webcam'
  }

  # Generic RTSP Stream
  generic_stream = {
      'url': 'rtsp://camera.local/live',
      'name': 'Generic IP Camera'
  }

  🔧 Dynamic Setup Process

  1. Network Discovery:

  async def discover_cameras():
      """Auto-discover cameras on network"""
      discovered = []

      # RTSP port scanning
      for ip in network_range('192.168.1.0/24'):
          if await check_rtsp_port(ip, 554):
              discovered.append({
                  'type': 'rtsp',
                  'url': f'rtsp://{ip}:554/stream1',
                  'ip': ip
              })

      # UPnP discovery
      upnp_devices = await discover_upnp_cameras()
      discovered.extend(upnp_devices)

      return discovered

  2. QR Code Setup:

  # Generate QR code for easy mobile setup
  def generate_camera_qr(computer_ip):
      setup_url = f"http://{computer_ip}:8001/camera?auto_setup=true"
      qr_code = qrcode.make(setup_url)
      return qr_code

  # Mobile scans QR → auto-opens PWA → auto-registers

  3. Universal API Endpoints:

  # Dynamic camera management
  @router.post("/api/cameras/register")
  async def register_camera(camera_info: dict):
      """Register any type of camera source"""
      camera_id = await stream_processor.add_camera_source(camera_info)
      return {"camera_id": camera_id, "status": "registered"}

  @router.get("/api/cameras/discover")
  async def discover_cameras():
      """Auto-discover available cameras"""
      return await network_discovery.scan_for_cameras()

  @router.post("/api/cameras/{camera_id}/stream")
  async def handle_camera_stream(camera_id: str, frame_data: bytes):
      """Universal frame handler for any camera"""
      await process_frame(camera_id, frame_data)

  📊 Universal Database Schema

  -- Universal camera registry
  CREATE TABLE cameras (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      type TEXT NOT NULL,  -- 'android', 'ip_camera', 'usb', 'rtsp'
      source_config JSON,  -- Flexible config storage
      location TEXT,
      capabilities JSON,   -- Resolution, formats, etc.
      auto_discovered BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      last_seen TIMESTAMP,
      status TEXT DEFAULT 'offline'  -- online, offline, error
  );

  -- Enhanced detections with camera source
  CREATE TABLE detections (
      id TEXT PRIMARY KEY,
      camera_id TEXT REFERENCES cameras(id),
      license_plate TEXT,
      confidence REAL,
      bbox_x1 INTEGER, bbox_y1 INTEGER,
      bbox_x2 INTEGER, bbox_y2 INTEGER,
      image_path TEXT,
      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      processed BOOLEAN DEFAULT FALSE
  );

  🎯 Setup Experience

  For Android Devices:

  1. QR Code Scan → Opens PWA
  2. Auto-Detection → Device capabilities detected
  3. One-Click Setup → Camera registered and streaming
  4. Works Offline → PWA cached for offline use

  For IP Cameras:

  1. Auto-Discovery → Network scan finds cameras
  2. Credential Setup → Username/password if needed
  3. Stream Test → Verify connection
  4. Auto-Registration → Added to camera list

  For Any Device:

  1. Universal URL → http://computer_ip:8001/camera
  2. Device Detection → Auto-detects capabilities
  3. Stream Setup → Optimizes for device
  4. Instant Streaming → Starts processing immediately

  🚀 Benefits of Universal Approach

  - ✅ Works with ANY camera - Android, iPhone, IP cameras, webcams
  - ✅ Zero app installation - PWA works in any browser
  - ✅ Auto-discovery - Finds cameras automatically
  - ✅ Dynamic scaling - Add unlimited cameras
  - ✅ Cross-platform - iOS, Android, Windows, Linux devices
  - ✅ Future-proof - Works with new camera types
  - ✅ Cost-effective - Use existing devices

  This creates a truly universal LPR camera network that can incorporate any video        
  source!
