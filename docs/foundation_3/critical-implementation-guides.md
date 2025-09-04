# Foundation 3 - Critical Implementation Guides

## 1. Reolink Camera Integration Guide (Day 1 Priority)

### Testing Your Specific Reolink Models

```python
# File: camera_testing/reolink_compatibility.py
import cv2
import requests
from requests.auth import HTTPDigestAuth
import asyncio
import logging
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class ReolinkCameraTester:
    """Test and validate Reolink camera compatibility"""
    
    # Known Reolink configurations
    REOLINK_MODELS = {
        'RLC-811A': {
            'rtsp_paths': [
                '/h264Preview_01_main',    # Main stream
                '/h264Preview_01_sub',     # Sub stream
                '/h265Preview_01_main'     # H.265 if available
            ],
            'http_port': 80,
            'rtsp_port': 554,
            'onvif_port': 8000,
            'auth_type': 'digest',
            'capabilities': ['4k', 'poe', 'night_vision', 'motion_detection']
        },
        'RLC-822A': {
            'rtsp_paths': ['/h264Preview_01_main', '/h265Preview_01_main'],
            'capabilities': ['4k', 'poe', 'ptz', '3x_zoom', 'person_vehicle_detection']
        },
        'RLC-1212A': {
            'rtsp_paths': ['/h264Preview_01_main'],
            'capabilities': ['12mp', 'wide_angle', 'poe']
        }
    }
    
    def __init__(self, camera_ip: str, username: str, password: str):
        self.camera_ip = camera_ip
        self.username = username
        self.password = password
        self.auth = HTTPDigestAuth(username, password)
        self.working_config = None
        
    async def full_compatibility_test(self) -> Dict[str, Any]:
        """Run complete compatibility test suite"""
        results = {
            'ip': self.camera_ip,
            'rtsp_working': False,
            'http_api_working': False,
            'snapshot_working': False,
            'onvif_working': False,
            'stream_quality': {},
            'recommended_config': None
        }
        
        # 1. Test RTSP streams
        logger.info(f"Testing RTSP streams for {self.camera_ip}")
        rtsp_results = await self._test_rtsp_streams()
        results['rtsp_working'] = rtsp_results['working']
        results['stream_quality'] = rtsp_results['quality']
        
        # 2. Test HTTP API
        logger.info("Testing HTTP API")
        results['http_api_working'] = await self._test_http_api()
        
        # 3. Test snapshot capability
        logger.info("Testing snapshot capability")
        results['snapshot_working'] = await self._test_snapshot()
        
        # 4. Test ONVIF if available
        logger.info("Testing ONVIF compatibility")
        results['onvif_working'] = await self._test_onvif()
        
        # 5. Determine best configuration
        results['recommended_config'] = self._determine_best_config(results)
        
        return results
    
    async def _test_rtsp_streams(self) -> Dict[str, Any]:
        """Test all possible RTSP stream paths"""
        results = {'working': False, 'quality': {}}
        
        # Try each known RTSP path
        for model, config in self.REOLINK_MODELS.items():
            for rtsp_path in config['rtsp_paths']:
                stream_url = f"rtsp://{self.username}:{self.password}@{self.camera_ip}:554{rtsp_path}"
                
                logger.info(f"Testing RTSP URL: {rtsp_path}")
                quality = await self._test_single_rtsp(stream_url)
                
                if quality:
                    results['working'] = True
                    results['quality'][rtsp_path] = quality
                    
                    # Test with TCP transport (more reliable)
                    tcp_url = stream_url + "?tcp"
                    tcp_quality = await self._test_single_rtsp(tcp_url)
                    if tcp_quality:
                        results['quality'][rtsp_path + '_tcp'] = tcp_quality
        
        return results
    
    async def _test_single_rtsp(self, url: str) -> Optional[Dict[str, Any]]:
        """Test single RTSP stream and return quality metrics"""
        try:
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            
            # Try to read frames
            frames_read = 0
            start_time = asyncio.get_event_loop().time()
            
            for _ in range(30):  # Read 30 frames
                ret, frame = cap.read()
                if ret:
                    frames_read += 1
                else:
                    break
            
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if frames_read > 0:
                # Get stream properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                cap.release()
                
                return {
                    'resolution': f"{width}x{height}",
                    'fps': fps,
                    'actual_fps': frames_read / elapsed,
                    'codec': self._get_codec_info(cap),
                    'latency_test': elapsed / frames_read * 1000  # ms per frame
                }
            
            cap.release()
            return None
            
        except Exception as e:
            logger.error(f"RTSP test failed: {e}")
            return None
    
    async def _test_http_api(self) -> bool:
        """Test Reolink HTTP API"""
        try:
            # Test basic API endpoint
            response = requests.get(
                f"http://{self.camera_ip}/api.cgi?cmd=GetDevInfo",
                auth=self.auth,
                timeout=5
            )
            
            if response.status_code == 200:
                # Try to get device info
                device_info = response.json()
                logger.info(f"Camera model: {device_info.get('model', 'Unknown')}")
                return True
                
        except Exception as e:
            logger.error(f"HTTP API test failed: {e}")
        
        return False
    
    async def _test_snapshot(self) -> bool:
        """Test snapshot capability"""
        snapshot_urls = [
            "/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=randomstring",
            "/snap.jpeg",
            "/snapshot.cgi"
        ]
        
        for url in snapshot_urls:
            try:
                response = requests.get(
                    f"http://{self.camera_ip}{url}",
                    auth=self.auth,
                    timeout=5
                )
                
                if response.status_code == 200 and len(response.content) > 1000:
                    logger.info(f"Snapshot working at: {url}")
                    return True
                    
            except:
                continue
        
        return False
    
    async def _test_onvif(self) -> bool:
        """Test ONVIF compatibility"""
        try:
            # Basic ONVIF discovery
            onvif_url = f"http://{self.camera_ip}:8000/onvif/device_service"
            
            # ONVIF GetCapabilities request
            soap_request = '''<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
                <soap:Body>
                    <GetCapabilities xmlns="http://www.onvif.org/ver10/device/wsdl">
                        <Category>All</Category>
                    </GetCapabilities>
                </soap:Body>
            </soap:Envelope>'''
            
            response = requests.post(
                onvif_url,
                data=soap_request,
                headers={'Content-Type': 'application/soap+xml'},
                auth=self.auth,
                timeout=5
            )
            
            return response.status_code == 200
            
        except:
            return False
    
    def _determine_best_config(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal configuration based on test results"""
        config = {
            'primary_stream': None,
            'secondary_stream': None,
            'snapshot_url': None,
            'transport': 'tcp',  # More reliable for Reolink
            'buffer_size': 1048576,  # 1MB buffer
            'reconnect_delay': 5000,
            'auth_method': 'digest'
        }
        
        # Find best quality stream
        if test_results['stream_quality']:
            # Prefer H.264 main stream with TCP
            for path, quality in test_results['stream_quality'].items():
                if 'h264' in path and 'main' in path and 'tcp' in path:
                    config['primary_stream'] = path
                    break
            
            # Fallback to any working stream
            if not config['primary_stream']:
                config['primary_stream'] = list(test_results['stream_quality'].keys())[0]
        
        # Set snapshot URL if working
        if test_results['snapshot_working']:
            config['snapshot_url'] = "/cgi-bin/api.cgi?cmd=Snap&channel=0"
        
        return config

# Usage example
async def test_your_cameras():
    """Run this on Day 1 with your actual cameras"""
    
    # Your camera details
    cameras = [
        {'ip': '192.168.1.101', 'username': 'admin', 'password': 'your_password'},
        {'ip': '192.168.1.102', 'username': 'admin', 'password': 'your_password'},
        # Add all your cameras
    ]
    
    for camera in cameras:
        tester = ReolinkCameraTester(
            camera['ip'], 
            camera['username'], 
            camera['password']
        )
        
        results = await tester.full_compatibility_test()
        
        print(f"\n{'='*60}")
        print(f"Camera: {camera['ip']}")
        print(f"RTSP Working: {results['rtsp_working']}")
        print(f"Recommended Config: {results['recommended_config']}")
        print(f"Stream Quality: {results['stream_quality']}")
        
        # Save results for later use
        with open(f"camera_{camera['ip'].replace('.', '_')}_config.json", 'w') as f:
            json.dump(results, f, indent=2)
```

## 2. Robust Streaming Implementation

### Multi-Method Streaming with Automatic Fallback

```python
# File: streaming/reliable_stream_manager.py
import asyncio
from enum import Enum
from typing import Dict, Any, Optional, Callable
import time
import logging

logger = logging.getLogger(__name__)

class StreamMethod(Enum):
    WEBRTC = "webrtc"
    HLS = "hls"
    WEBSOCKET = "websocket"
    SNAPSHOTS = "snapshots"

class StreamHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DEAD = "dead"

class ReliableStreamManager:
    """Manages multiple streaming methods with automatic fallback"""
    
    def __init__(self):
        self.active_streams: Dict[str, StreamInfo] = {}
        self.method_priority = [
            StreamMethod.WEBRTC,
            StreamMethod.HLS,
            StreamMethod.WEBSOCKET,
            StreamMethod.SNAPSHOTS
        ]
        self.health_thresholds = {
            'latency_ms': 500,
            'packet_loss_percent': 5,
            'fps_minimum': 10,
            'reconnect_max': 3
        }
        
    async def start_stream(self, camera_id: str, client_id: str) -> Dict[str, Any]:
        """Start streaming with automatic method selection"""
        stream_info = StreamInfo(camera_id, client_id)
        
        # Try each method in priority order
        for method in self.method_priority:
            try:
                logger.info(f"Attempting {method.value} for camera {camera_id}")
                
                stream = await self._create_stream(camera_id, method)
                stream_info.current_method = method
                stream_info.stream_object = stream
                stream_info.health_status = StreamHealth.HEALTHY
                
                # Start health monitoring
                asyncio.create_task(self._monitor_stream_health(stream_info))
                
                self.active_streams[f"{camera_id}:{client_id}"] = stream_info
                
                return {
                    'success': True,
                    'method': method.value,
                    'stream_id': stream_info.stream_id,
                    'connection_info': self._get_connection_info(method, stream)
                }
                
            except Exception as e:
                logger.warning(f"{method.value} failed for camera {camera_id}: {e}")
                continue
        
        # All methods failed
        return {
            'success': False,
            'error': 'All streaming methods failed',
            'fallback': 'snapshots_only'
        }
    
    async def _create_stream(self, camera_id: str, method: StreamMethod):
        """Create stream based on method"""
        if method == StreamMethod.WEBRTC:
            return await self._create_webrtc_stream(camera_id)
        elif method == StreamMethod.HLS:
            return await self._create_hls_stream(camera_id)
        elif method == StreamMethod.WEBSOCKET:
            return await self._create_websocket_stream(camera_id)
        elif method == StreamMethod.SNAPSHOTS:
            return await self._create_snapshot_stream(camera_id)
    
    async def _monitor_stream_health(self, stream_info: StreamInfo):
        """Continuous health monitoring with automatic recovery"""
        consecutive_failures = 0
        
        while stream_info.stream_id in [s.stream_id for s in self.active_streams.values()]:
            try:
                # Get stream metrics
                metrics = await self._get_stream_metrics(stream_info)
                
                # Evaluate health
                health = self._evaluate_health(metrics)
                stream_info.health_status = health
                stream_info.last_health_check = time.time()
                
                if health == StreamHealth.UNHEALTHY:
                    consecutive_failures += 1
                    
                    if consecutive_failures >= self.health_thresholds['reconnect_max']:
                        # Try fallback method
                        await self._fallback_to_next_method(stream_info)
                        consecutive_failures = 0
                else:
                    consecutive_failures = 0
                
                # Adaptive check interval
                check_interval = 1 if health == StreamHealth.UNHEALTHY else 3
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Health check error for {stream_info.camera_id}: {e}")
                await asyncio.sleep(5)
    
    async def _fallback_to_next_method(self, stream_info: StreamInfo):
        """Fallback to next available streaming method"""
        current_index = self.method_priority.index(stream_info.current_method)
        
        # Try next methods
        for i in range(current_index + 1, len(self.method_priority)):
            next_method = self.method_priority[i]
            
            try:
                logger.info(f"Falling back from {stream_info.current_method.value} to {next_method.value}")
                
                # Clean up old stream
                await self._cleanup_stream(stream_info)
                
                # Create new stream
                new_stream = await self._create_stream(stream_info.camera_id, next_method)
                stream_info.stream_object = new_stream
                stream_info.current_method = next_method
                stream_info.fallback_count += 1
                
                # Notify client of method change
                await self._notify_client_method_change(stream_info)
                
                return
                
            except Exception as e:
                logger.error(f"Fallback to {next_method.value} failed: {e}")
                continue
        
        # All fallbacks failed
        stream_info.health_status = StreamHealth.DEAD
        await self._notify_client_stream_failed(stream_info)
    
    def _evaluate_health(self, metrics: Dict[str, Any]) -> StreamHealth:
        """Evaluate stream health based on metrics"""
        if not metrics:
            return StreamHealth.UNHEALTHY
        
        issues = 0
        
        # Check latency
        if metrics.get('latency_ms', float('inf')) > self.health_thresholds['latency_ms']:
            issues += 2  # Latency is critical
        
        # Check packet loss
        if metrics.get('packet_loss_percent', 100) > self.health_thresholds['packet_loss_percent']:
            issues += 1
        
        # Check FPS
        if metrics.get('fps', 0) < self.health_thresholds['fps_minimum']:
            issues += 1
        
        # Check last frame time
        if time.time() - metrics.get('last_frame_time', 0) > 5:
            issues += 3  # No frames is critical
        
        if issues == 0:
            return StreamHealth.HEALTHY
        elif issues <= 2:
            return StreamHealth.DEGRADED
        else:
            return StreamHealth.UNHEALTHY

class StreamInfo:
    """Information about an active stream"""
    def __init__(self, camera_id: str, client_id: str):
        self.stream_id = f"{camera_id}:{client_id}:{time.time()}"
        self.camera_id = camera_id
        self.client_id = client_id
        self.current_method: Optional[StreamMethod] = None
        self.stream_object: Any = None
        self.health_status: StreamHealth = StreamHealth.HEALTHY
        self.last_health_check: float = time.time()
        self.fallback_count: int = 0
        self.start_time: float = time.time()
        self.metrics_history: List[Dict[str, Any]] = []
```

### Frontend Streaming Client with Fallback

```javascript
// File: frontend/js/reliable-stream-client.js
class ReliableStreamClient {
    constructor(cameraId, containerElement) {
        this.cameraId = cameraId;
        this.container = containerElement;
        this.currentMethod = null;
        this.streamObject = null;
        this.healthChecker = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        // Performance metrics
        this.metrics = {
            framesReceived: 0,
            lastFrameTime: Date.now(),
            frozenFrameThreshold: 3000, // 3 seconds
            memoryCheckInterval: 30000, // 30 seconds
            maxMemoryMB: 500 // Restart stream if over 500MB
        };
        
        // Method implementations
        this.streamMethods = {
            webrtc: new WebRTCMethod(this),
            hls: new HLSMethod(this),
            websocket: new WebSocketMethod(this),
            snapshots: new SnapshotMethod(this)
        };
    }
    
    async start() {
        try {
            // Request stream from server
            const response = await fetch(`/api/stream/start`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    camera_id: this.cameraId,
                    client_capabilities: this.getClientCapabilities()
                })
            });
            
            const streamInfo = await response.json();
            
            if (!streamInfo.success) {
                throw new Error(streamInfo.error);
            }
            
            // Start streaming with selected method
            await this.startStreamingMethod(streamInfo.method, streamInfo.connection_info);
            
            // Start health monitoring
            this.startHealthMonitoring();
            
            // Start memory monitoring
            this.startMemoryMonitoring();
            
        } catch (error) {
            console.error('Failed to start stream:', error);
            this.showError('Unable to start video stream');
        }
    }
    
    async startStreamingMethod(method, connectionInfo) {
        this.currentMethod = method;
        const methodImpl = this.streamMethods[method];
        
        if (!methodImpl) {
            throw new Error(`Unknown streaming method: ${method}`);
        }
        
        // Create appropriate UI element
        this.clearContainer();
        const element = methodImpl.createElement();
        this.container.appendChild(element);
        
        // Start streaming
        this.streamObject = await methodImpl.start(connectionInfo);
    }
    
    startHealthMonitoring() {
        this.healthChecker = setInterval(() => {
            this.checkStreamHealth();
        }, 1000);
    }
    
    async checkStreamHealth() {
        const now = Date.now();
        const timeSinceLastFrame = now - this.metrics.lastFrameTime;
        
        // Check if stream is frozen
        if (timeSinceLastFrame > this.metrics.frozenFrameThreshold) {
            console.warn(`Stream frozen for ${timeSinceLastFrame}ms`);
            
            // Try to recover
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                await this.reconnect();
            } else {
                // Request fallback method
                await this.requestFallback();
            }
        }
        
        // Check method-specific health
        const methodImpl = this.streamMethods[this.currentMethod];
        if (methodImpl && methodImpl.checkHealth) {
            const health = await methodImpl.checkHealth(this.streamObject);
            
            if (health.needsReconnect) {
                await this.reconnect();
            }
        }
    }
    
    startMemoryMonitoring() {
        setInterval(() => {
            if (performance.memory) {
                const usedMB = performance.memory.usedJSHeapSize / 1024 / 1024;
                
                if (usedMB > this.metrics.maxMemoryMB) {
                    console.warn(`Memory usage high: ${usedMB}MB, restarting stream`);
                    this.restart();
                }
            }
        }, this.metrics.memoryCheckInterval);
    }
    
    async reconnect() {
        this.reconnectAttempts++;
        console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
        
        // Clean up current stream
        this.cleanup();
        
        // Wait before reconnecting (exponential backoff)
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 30000);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // Try to reconnect
        try {
            await this.start();
            this.reconnectAttempts = 0; // Reset on success
        } catch (error) {
            console.error('Reconnection failed:', error);
        }
    }
    
    async requestFallback() {
        console.log('Requesting fallback streaming method');
        
        const response = await fetch(`/api/stream/fallback`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                camera_id: this.cameraId,
                current_method: this.currentMethod,
                failure_reason: 'frozen_stream'
            })
        });
        
        const fallbackInfo = await response.json();
        
        if (fallbackInfo.success) {
            // Switch to fallback method
            this.cleanup();
            await this.startStreamingMethod(fallbackInfo.method, fallbackInfo.connection_info);
            this.reconnectAttempts = 0;
        }
    }
    
    getClientCapabilities() {
        return {
            webrtc: 'RTCPeerConnection' in window,
            hls: this.canPlayHLS(),
            websocket: 'WebSocket' in window,
            mediaSource: 'MediaSource' in window,
            webgl: this.hasWebGL(),
            maxResolution: this.getMaxResolution(),
            userAgent: navigator.userAgent
        };
    }
    
    canPlayHLS() {
        const video = document.createElement('video');
        return video.canPlayType('application/vnd.apple.mpegurl') !== '';
    }
    
    hasWebGL() {
        try {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
        } catch (e) {
            return false;
        }
    }
    
    getMaxResolution() {
        // Estimate based on device
        if (window.screen.width > 3840) return '4k';
        if (window.screen.width > 1920) return '1440p';
        if (window.screen.width > 1280) return '1080p';
        return '720p';
    }
    
    cleanup() {
        if (this.healthChecker) {
            clearInterval(this.healthChecker);
        }
        
        if (this.streamObject && this.currentMethod) {
            const methodImpl = this.streamMethods[this.currentMethod];
            if (methodImpl && methodImpl.cleanup) {
                methodImpl.cleanup(this.streamObject);
            }
        }
        
        this.clearContainer();
    }
    
    clearContainer() {
        while (this.container.firstChild) {
            this.container.removeChild(this.container.firstChild);
        }
    }
    
    showError(message) {
        this.clearContainer();
        const errorDiv = document.createElement('div');
        errorDiv.className = 'stream-error';
        errorDiv.innerHTML = `
            <div class="error-icon">📹❌</div>
            <div class="error-message">${message}</div>
            <button onclick="this.parentElement.parentElement.streamClient.start()">
                Retry
            </button>
        `;
        this.container.appendChild(errorDiv);
    }
}

// WebRTC Method Implementation
class WebRTCMethod {
    constructor(client) {
        this.client = client;
    }
    
    createElement() {
        const video = document.createElement('video');
        video.autoplay = true;
        video.muted = true;
        video.playsInline = true;
        video.style.width = '100%';
        video.style.height = '100%';
        return video;
    }
    
    async start(connectionInfo) {
        const pc = new RTCPeerConnection({
            iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
        });
        
        // Handle incoming stream
        pc.ontrack = (event) => {
            const video = this.client.container.querySelector('video');
            video.srcObject = event.streams[0];
            
            // Update frame metrics
            video.onloadeddata = () => {
                this.monitorFrameRate(video);
            };
        };
        
        // Set remote offer
        await pc.setRemoteDescription({
            type: 'offer',
            sdp: connectionInfo.sdp
        });
        
        // Create and send answer
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        
        await fetch('/api/webrtc/answer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                stream_id: connectionInfo.stream_id,
                sdp: answer.sdp
            })
        });
        
        return pc;
    }
    
    monitorFrameRate(video) {
        let lastFrameCount = 0;
        
        setInterval(() => {
            if (video.webkitDecodedFrameCount !== undefined) {
                const currentFrameCount = video.webkitDecodedFrameCount;
                if (currentFrameCount > lastFrameCount) {
                    this.client.metrics.lastFrameTime = Date.now();
                    this.client.metrics.framesReceived = currentFrameCount;
                }
                lastFrameCount = currentFrameCount;
            }
        }, 1000);
    }
    
    async checkHealth(pc) {
        const stats = await pc.getStats();
        let inboundStats = null;
        
        stats.forEach(report => {
            if (report.type === 'inbound-rtp' && report.mediaType === 'video') {
                inboundStats = report;
            }
        });
        
        if (!inboundStats) {
            return { needsReconnect: true };
        }
        
        // Check packet loss
        const packetLoss = inboundStats.packetsLost / 
            (inboundStats.packetsReceived + inboundStats.packetsLost);
        
        // Check if receiving data
        const bytesReceived = inboundStats.bytesReceived || 0;
        
        return {
            needsReconnect: packetLoss > 0.05 || bytesReceived === 0,
            packetLoss: packetLoss,
            bytesReceived: bytesReceived
        };
    }
    
    cleanup(pc) {
        if (pc) {
            pc.close();
        }
    }
}

// Add HLS, WebSocket, and Snapshot implementations...
```

## 3. GPU Memory Management

### Critical GPU Resource Manager

```python
# File: gpu/gpu_resource_manager.py
import nvidia_ml_py as nvml
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class StreamGPUAllocation:
    camera_id: str
    resolution: Tuple[int, int]
    fps: int
    allocated_memory_mb: int
    processing_type: str  # 'detection', 'recording', 'both'
    priority: int  # 1-10, higher = more important

class GPUResourceManager:
    """Manages GPU resources to prevent OOM"""
    
    def __init__(self, gpu_index: int = 0):
        self.gpu_index = gpu_index
        self.allocations: Dict[str, StreamGPUAllocation] = {}
        self.total_memory_mb = 0
        self.reserved_memory_mb = 1024  # Reserve 1GB for system
        
        # Initialize NVML
        nvml.nvmlInit()
        self.handle = nvml.nvmlDeviceGetHandleByIndex(gpu_index)
        
        # Get total GPU memory
        info = nvml.nvmlDeviceGetMemoryInfo(self.handle)
        self.total_memory_mb = info.total // (1024 * 1024)
        
        logger.info(f"GPU {gpu_index}: {self.total_memory_mb}MB total memory")
        
        # Memory requirements per operation
        self.memory_requirements = {
            'yolo_model': 800,  # YOLOv8 model
            'tensorrt_overhead': 200,
            'frame_buffer_per_stream': 50,  # Per 1080p stream
            'batch_processing_overhead': 300,
            'detection_buffer': 100  # Per stream
        }
        
    def get_available_memory(self) -> int:
        """Get currently available GPU memory"""
        info = nvml.nvmlDeviceGetMemoryInfo(self.handle)
        available_mb = info.free // (1024 * 1024)
        
        # Subtract our reserved amount
        return max(0, available_mb - self.reserved_memory_mb)
    
    def estimate_stream_memory(self, resolution: Tuple[int, int], fps: int, 
                             processing_type: str) -> int:
        """Estimate memory required for a stream"""
        width, height = resolution
        
        # Base frame buffer size
        frame_size_mb = (width * height * 3) / (1024 * 1024)  # RGB
        frames_in_buffer = min(fps // 5, 10)  # Buffer up to 10 frames
        buffer_memory = frame_size_mb * frames_in_buffer
        
        # Processing memory
        processing_memory = 0
        if processing_type in ['detection', 'both']:
            processing_memory += self.memory_requirements['detection_buffer']
            
        # Additional buffer for 4K streams
        if width >= 3840:
            processing_memory += 100
            
        total_mb = int(buffer_memory + processing_memory)
        logger.info(f"Stream {width}x{height}@{fps}fps needs ~{total_mb}MB")
        
        return total_mb
    
    def can_add_stream(self, camera_id: str, resolution: Tuple[int, int], 
                      fps: int, processing_type: str = 'both') -> Tuple[bool, str]:
        """Check if we can add a new stream without OOM"""
        required_mb = self.estimate_stream_memory(resolution, fps, processing_type)
        available_mb = self.get_available_memory()
        
        # Check current allocations
        current_used = sum(a.allocated_memory_mb for a in self.allocations.values())
        
        # Safety check - never use more than 80% of GPU memory
        max_allowed = int((self.total_memory_mb - self.reserved_memory_mb) * 0.8)
        
        if current_used + required_mb > max_allowed:
            return False, f"Would exceed 80% GPU memory limit ({max_allowed}MB)"
        
        if required_mb > available_mb:
            return False, f"Insufficient memory: need {required_mb}MB, have {available_mb}MB"
        
        return True, "OK"
    
    async def allocate_stream(self, camera_id: str, resolution: Tuple[int, int],
                            fps: int, processing_type: str = 'both', 
                            priority: int = 5) -> bool:
        """Allocate GPU resources for a stream"""
        # Check if we can add it
        can_add, reason = self.can_add_stream(camera_id, resolution, fps, processing_type)
        
        if not can_add:
            # Try to free up space by removing lower priority streams
            freed = await self._try_free_memory_for_priority(priority, 
                self.estimate_stream_memory(resolution, fps, processing_type))
            
            if not freed:
                logger.error(f"Cannot allocate stream {camera_id}: {reason}")
                return False
        
        # Allocate
        allocation = StreamGPUAllocation(
            camera_id=camera_id,
            resolution=resolution,
            fps=fps,
            allocated_memory_mb=self.estimate_stream_memory(resolution, fps, processing_type),
            processing_type=processing_type,
            priority=priority
        )
        
        self.allocations[camera_id] = allocation
        
        logger.info(f"Allocated {allocation.allocated_memory_mb}MB for {camera_id}")
        self._log_memory_status()
        
        return True
    
    async def _try_free_memory_for_priority(self, new_priority: int, 
                                          required_mb: int) -> bool:
        """Try to free memory by removing lower priority streams"""
        # Sort allocations by priority (ascending)
        sorted_allocations = sorted(
            self.allocations.items(), 
            key=lambda x: x[1].priority
        )
        
        freed_mb = 0
        to_remove = []
        
        for camera_id, allocation in sorted_allocations:
            if allocation.priority < new_priority:
                to_remove.append(camera_id)
                freed_mb += allocation.allocated_memory_mb
                
                if freed_mb >= required_mb:
                    break
        
        if freed_mb < required_mb:
            return False
        
        # Remove lower priority streams
        for camera_id in to_remove:
            await self.deallocate_stream(camera_id)
            logger.warning(f"Evicted lower priority stream {camera_id}")
        
        return True
    
    async def deallocate_stream(self, camera_id: str):
        """Free GPU resources for a stream"""
        if camera_id in self.allocations:
            allocation = self.allocations[camera_id]
            del self.allocations[camera_id]
            
            logger.info(f"Freed {allocation.allocated_memory_mb}MB from {camera_id}")
            self._log_memory_status()
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory usage status"""
        info = nvml.nvmlDeviceGetMemoryInfo(self.handle)
        current_used = sum(a.allocated_memory_mb for a in self.allocations.values())
        
        return {
            'total_mb': self.total_memory_mb,
            'used_mb': info.used // (1024 * 1024),
            'free_mb': info.free // (1024 * 1024),
            'allocated_mb': current_used,
            'reserved_mb': self.reserved_memory_mb,
            'streams': len(self.allocations),
            'utilization_percent': (info.used / info.total) * 100
        }
    
    def _log_memory_status(self):
        """Log current memory status"""
        status = self.get_memory_status()
        logger.info(
            f"GPU Memory: {status['allocated_mb']}/{status['total_mb']}MB allocated, "
            f"{status['streams']} streams, {status['utilization_percent']:.1f}% utilized"
        )
    
    async def monitor_memory_pressure(self):
        """Monitor for memory pressure and take action"""
        while True:
            try:
                status = self.get_memory_status()
                
                # Critical - over 90% utilization
                if status['utilization_percent'] > 90:
                    logger.critical(f"GPU memory critical: {status['utilization_percent']:.1f}%")
                    
                    # Emergency: Remove lowest priority stream
                    if self.allocations:
                        lowest = min(self.allocations.items(), key=lambda x: x[1].priority)
                        await self.deallocate_stream(lowest[0])
                
                # Warning - over 80% utilization
                elif status['utilization_percent'] > 80:
                    logger.warning(f"GPU memory high: {status['utilization_percent']:.1f}%")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
                await asyncio.sleep(30)

# Integration with stream manager
class GPUAwareStreamManager:
    """Stream manager that respects GPU memory limits"""
    
    def __init__(self):
        self.gpu_manager = GPUResourceManager(gpu_index=0)
        self.active_streams = {}
        
        # Start memory monitoring
        asyncio.create_task(self.gpu_manager.monitor_memory_pressure())
    
    async def add_camera_stream(self, camera_id: str, camera_config: Dict[str, Any]):
        """Add camera stream with GPU memory check"""
        resolution = (camera_config['width'], camera_config['height'])
        fps = camera_config.get('fps', 30)
        priority = camera_config.get('priority', 5)
        
        # Try to allocate GPU resources
        allocated = await self.gpu_manager.allocate_stream(
            camera_id, resolution, fps, 'both', priority
        )
        
        if not allocated:
            raise Exception(f"Cannot allocate GPU resources for {camera_id}")
        
        try:
            # Start the actual stream
            stream = await self._start_stream(camera_id, camera_config)
            self.active_streams[camera_id] = stream
            
        except Exception as e:
            # Rollback GPU allocation on failure
            await self.gpu_manager.deallocate_stream(camera_id)
            raise
    
    async def remove_camera_stream(self, camera_id: str):
        """Remove camera stream and free GPU resources"""
        if camera_id in self.active_streams:
            # Stop stream
            await self._stop_stream(camera_id)
            del self.active_streams[camera_id]
            
            # Free GPU resources
            await self.gpu_manager.deallocate_stream(camera_id)
```

## 4. Edge Recording Implementation

### Reliable Edge Recording with Sync

```python
# File: edge/edge_recording_manager.py
import asyncio
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import aiofiles
import logging

logger = logging.getLogger(__name__)

@dataclass
class EdgeRecording:
    camera_id: str
    file_path: Path
    start_time: datetime
    end_time: Optional[datetime]
    size_mb: float
    synced: bool
    sync_attempts: int
    metadata: Dict[str, Any]

class EdgeRecordingManager:
    """Manages local edge recording when server/network fails"""
    
    def __init__(self, edge_storage_path: str = "/edge/recordings"):
        self.edge_path = Path(edge_storage_path)
        self.edge_path.mkdir(exist_ok=True, parents=True)
        
        # Recordings tracking
        self.active_recordings: Dict[str, subprocess.Popen] = {}
        self.recording_database: List[EdgeRecording] = []
        self.sync_queue: List[EdgeRecording] = []
        
        # Configuration
        self.segment_duration = 600  # 10-minute segments
        self.max_storage_gb = 100    # Maximum edge storage
        self.sync_batch_size = 5     # Files to sync at once
        self.retention_days = 7      # Keep edge recordings for 7 days
        
        # State
        self.server_available = True
        self.sync_in_progress = False
        
        # Load existing recordings database
        asyncio.create_task(self._load_recording_database())
    
    async def start_edge_recording(self, camera_id: str, rtsp_url: str):
        """Start edge recording for a camera"""
        if camera_id in self.active_recordings:
            logger.warning(f"Edge recording already active for {camera_id}")
            return
        
        # Create camera directory
        camera_path = self.edge_path / camera_id
        camera_path.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_pattern = str(camera_path / f"{timestamp}_%03d.mp4")
        
        # FFmpeg command for edge recording
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-c:v', 'copy',  # No transcoding to save CPU
            '-c:a', 'copy',
            '-f', 'segment',
            '-segment_time', str(self.segment_duration),
            '-segment_format', 'mp4',
            '-segment_atclocktime', '1',
            '-strftime', '1',
            '-reset_timestamps', '1',
            '-movflags', '+faststart',  # For quick playback start
            output_pattern
        ]
        
        # Start recording process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.active_recordings[camera_id] = process
        
        logger.info(f"Started edge recording for {camera_id}")
        
        # Monitor the recording
        asyncio.create_task(self._monitor_recording(camera_id, camera_path))
    
    async def stop_edge_recording(self, camera_id: str):
        """Stop edge recording for a camera"""
        if camera_id not in self.active_recordings:
            return
        
        process = self.active_recordings[camera_id]
        process.terminate()
        
        # Wait for process to finish
        try:
            await asyncio.wait_for(
                asyncio.create_task(self._wait_process(process)), 
                timeout=5.0
            )
        except asyncio.TimeoutError:
            process.kill()
        
        del self.active_recordings[camera_id]
        logger.info(f"Stopped edge recording for {camera_id}")
    
    async def _monitor_recording(self, camera_id: str, camera_path: Path):
        """Monitor recording process and catalog files"""
        while camera_id in self.active_recordings:
            try:
                # Find new recording files
                for file_path in camera_path.glob("*.mp4"):
                    # Check if already cataloged
                    if not any(r.file_path == file_path for r in self.recording_database):
                        # Get file info
                        stat = file_path.stat()
                        
                        recording = EdgeRecording(
                            camera_id=camera_id,
                            file_path=file_path,
                            start_time=datetime.fromtimestamp(stat.st_mtime),
                            end_time=None,
                            size_mb=stat.st_size / (1024 * 1024),
                            synced=False,
                            sync_attempts=0,
                            metadata={
                                'edge_node': 'primary',
                                'reason': 'network_failure'
                            }
                        )
                        
                        self.recording_database.append(recording)
                        self.sync_queue.append(recording)
                        
                        logger.info(f"New edge recording: {file_path.name} ({recording.size_mb:.1f}MB)")
                
                # Check storage space
                await self._check_storage_space()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring recordings: {e}")
                await asyncio.sleep(60)
    
    async def sync_recordings_to_server(self):
        """Sync edge recordings to server when connection available"""
        if self.sync_in_progress or not self.server_available:
            return
        
        self.sync_in_progress = True
        
        try:
            while self.sync_queue and self.server_available:
                # Get batch of recordings to sync
                batch = self.sync_queue[:self.sync_batch_size]
                
                for recording in batch:
                    try:
                        await self._sync_single_recording(recording)
                        
                        # Mark as synced
                        recording.synced = True
                        recording.sync_attempts = 0
                        
                        # Remove from queue
                        self.sync_queue.remove(recording)
                        
                        # Delete local file after successful sync (optional)
                        if self._should_delete_after_sync():
                            recording.file_path.unlink()
                            logger.info(f"Deleted synced file: {recording.file_path}")
                        
                    except Exception as e:
                        recording.sync_attempts += 1
                        logger.error(f"Failed to sync {recording.file_path}: {e}")
                        
                        if recording.sync_attempts > 3:
                            # Move to end of queue
                            self.sync_queue.remove(recording)
                            self.sync_queue.append(recording)
                
                # Save database state
                await self._save_recording_database()
                
                # Brief pause between batches
                await asyncio.sleep(5)
                
        finally:
            self.sync_in_progress = False
    
    async def _sync_single_recording(self, recording: EdgeRecording):
        """Sync single recording file to server"""
        # Create multipart upload for large files
        file_size = recording.file_path.stat().st_size
        chunk_size = 5 * 1024 * 1024  # 5MB chunks
        
        # Prepare metadata
        metadata = {
            'camera_id': recording.camera_id,
            'start_time': recording.start_time.isoformat(),
            'end_time': recording.end_time.isoformat() if recording.end_time else None,
            'edge_node': recording.metadata.get('edge_node'),
            'original_filename': recording.file_path.name
        }
        
        # Upload file
        async with aiofiles.open(recording.file_path, 'rb') as f:
            chunk_number = 0
            
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                
                # Upload chunk
                response = await self._upload_chunk(
                    recording.camera_id,
                    recording.file_path.name,
                    chunk,
                    chunk_number,
                    file_size
                )
                
                if not response['success']:
                    raise Exception(f"Upload failed: {response['error']}")
                
                chunk_number += 1
        
        logger.info(f"Successfully synced {recording.file_path.name}")
    
    async def _check_storage_space(self):
        """Check and manage edge storage space"""
        # Calculate total used space
        total_size = sum(f.stat().st_size for f in self.edge_path.rglob("*.mp4"))
        total_gb = total_size / (1024 ** 3)
        
        if total_gb > self.max_storage_gb:
            logger.warning(f"Edge storage full: {total_gb:.1f}GB / {self.max_storage_gb}GB")
            
            # Delete oldest synced recordings
            synced_recordings = sorted(
                [r for r in self.recording_database if r.synced],
                key=lambda r: r.start_time
            )
            
            for recording in synced_recordings:
                if recording.file_path.exists():
                    size_gb = recording.size_mb / 1024
                    recording.file_path.unlink()
                    total_gb -= size_gb
                    
                    logger.info(f"Deleted old recording: {recording.file_path}")
                    
                    if total_gb < self.max_storage_gb * 0.8:  # Keep 20% free
                        break
    
    async def handle_server_status_change(self, server_available: bool):
        """Handle server availability changes"""
        self.server_available = server_available
        
        if server_available and self.sync_queue:
            logger.info("Server available, starting sync...")
            asyncio.create_task(self.sync_recordings_to_server())
        elif not server_available:
            logger.warning("Server unavailable, continuing edge recording")
    
    async def _save_recording_database(self):
        """Save recording database to disk"""
        db_path = self.edge_path / "recording_database.json"
        
        data = []
        for recording in self.recording_database:
            data.append({
                'camera_id': recording.camera_id,
                'file_path': str(recording.file_path),
                'start_time': recording.start_time.isoformat(),
                'end_time': recording.end_time.isoformat() if recording.end_time else None,
                'size_mb': recording.size_mb,
                'synced': recording.synced,
                'sync_attempts': recording.sync_attempts,
                'metadata': recording.metadata
            })
        
        async with aiofiles.open(db_path, 'w') as f:
            await f.write(json.dumps(data, indent=2))
    
    async def _load_recording_database(self):
        """Load recording database from disk"""
        db_path = self.edge_path / "recording_database.json"
        
        if not db_path.exists():
            return
        
        try:
            async with aiofiles.open(db_path, 'r') as f:
                data = json.loads(await f.read())
            
            for item in data:
                recording = EdgeRecording(
                    camera_id=item['camera_id'],
                    file_path=Path(item['file_path']),
                    start_time=datetime.fromisoformat(item['start_time']),
                    end_time=datetime.fromisoformat(item['end_time']) if item['end_time'] else None,
                    size_mb=item['size_mb'],
                    synced=item['synced'],
                    sync_attempts=item['sync_attempts'],
                    metadata=item['metadata']
                )
                
                self.recording_database.append(recording)
                
                # Add unsynced recordings to queue
                if not recording.synced and recording.file_path.exists():
                    self.sync_queue.append(recording)
            
            logger.info(f"Loaded {len(self.recording_database)} recordings, {len(self.sync_queue)} to sync")
            
        except Exception as e:
            logger.error(f"Failed to load recording database: {e}")
```

## 5. Performance Monitoring & Validation

### Comprehensive Performance Monitor

```python
# File: monitoring/performance_monitor.py
import asyncio
import time
import psutil
import statistics
from typing import Dict, List, Any
from collections import deque, defaultdict
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor system performance against Foundation 3 requirements"""
    
    def __init__(self):
        # Foundation 3 Performance Requirements
        self.requirements = {
            'detection_latency_ms': 500,
            'stream_latency_ms': 500,
            'gpu_utilization_percent': 80,
            'cpu_utilization_percent': 80,
            'memory_per_camera_mb': 2048,
            'fps_minimum': 5,
            'network_bandwidth_mbps_per_camera': 50
        }
        
        # Metrics storage (keep last 5 minutes)
        self.metrics_window = 300  # seconds
        self.metrics = defaultdict(lambda: deque(maxlen=300))
        
        # Alerts
        self.alerts = []
        self.alert_callbacks = []
        
        # Start monitoring
        self.monitoring = True
        asyncio.create_task(self._monitoring_loop())
    
    async def record_detection_latency(self, camera_id: str, latency_ms: float):
        """Record AI detection latency"""
        self.metrics[f'detection_latency_{camera_id}'].append({
            'timestamp': time.time(),
            'value': latency_ms
        })
        
        # Check against requirement
        if latency_ms > self.requirements['detection_latency_ms']:
            await self._create_alert(
                'high_detection_latency',
                f'Detection latency {latency_ms}ms exceeds limit',
                severity='warning'
            )
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                
                # Record metrics
                for key, value in metrics.items():
                    self.metrics[key].append({
                        'timestamp': time.time(),
                        'value': value
                    })
                
                # Check against requirements
                await self._check_requirements(metrics)
                
                # Sleep for 1 second
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        metrics = {}
        
        # CPU metrics
        metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        metrics['cpu_per_core'] = psutil.cpu_percent(percpu=True)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics['memory_percent'] = memory.percent
        metrics['memory_available_mb'] = memory.available / (1024 ** 2)
        
        # GPU metrics (if available)
        gpu_stats = await self._get_gpu_stats()
        if gpu_stats:
            metrics.update(gpu_stats)
        
        # Network metrics
        net_io = psutil.net_io_counters()
        metrics['network_bytes_sent'] = net_io.bytes_sent
        metrics['network_bytes_recv'] = net_io.bytes_recv
        
        return metrics
    
    async def _get_gpu_stats(self) -> Dict[str, float]:
        """Get GPU statistics using nvidia-smi"""
        try:
            import nvidia_ml_py as nvml
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            
            # GPU utilization
            util = nvml.nvmlDeviceGetUtilizationRates(handle)
            
            # GPU memory
            mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
            
            return {
                'gpu_utilization_percent': util.gpu,
                'gpu_memory_percent': (mem_info.used / mem_info.total) * 100,
                'gpu_memory_used_mb': mem_info.used / (1024 ** 2),
                'gpu_temperature': nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
            }
            
        except Exception as e:
            logger.error(f"Failed to get GPU stats: {e}")
            return {}
    
    async def _check_requirements(self, current_metrics: Dict[str, float]):
        """Check metrics against requirements"""
        # CPU check
        if current_metrics.get('cpu_percent', 0) > self.requirements['cpu_utilization_percent']:
            await self._create_alert(
                'high_cpu_usage',
                f"CPU usage {current_metrics['cpu_percent']:.1f}% exceeds limit",
                severity='warning'
            )
        
        # GPU check
        if current_metrics.get('gpu_utilization_percent', 0) > self.requirements['gpu_utilization_percent']:
            await self._create_alert(
                'high_gpu_usage',
                f"GPU usage {current_metrics['gpu_utilization_percent']:.1f}% exceeds limit",
                severity='critical'
            )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'metrics': {},
            'requirements_met': True,
            'alerts': self.alerts[-10:]  # Last 10 alerts
        }
        
        # Calculate averages for each metric
        for metric_name, values in self.metrics.items():
            if values:
                recent_values = [v['value'] for v in values if time.time() - v['timestamp'] < 60]
                if recent_values:
                    report['metrics'][metric_name] = {
                        'current': recent_values[-1],
                        'avg_1min': statistics.mean(recent_values),
                        'max_1min': max(recent_values),
                        'min_1min': min(recent_values)
                    }
        
        # Check if requirements are met
        if any(a['severity'] == 'critical' for a in self.alerts if time.time() - a['timestamp'] < 300):
            report['status'] = 'critical'
            report['requirements_met'] = False
        elif any(a['severity'] == 'warning' for a in self.alerts if time.time() - a['timestamp'] < 300):
            report['status'] = 'warning'
        
        return report

# Integration test to verify requirements
async def validate_foundation3_requirements():
    """Run comprehensive test to validate all requirements"""
    monitor = PerformanceMonitor()
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Test 1: Detection latency
    print("Testing detection latency...")
    for i in range(10):
        start = time.time()
        # Simulate detection
        await asyncio.sleep(0.1)  # Replace with actual detection
        latency = (time.time() - start) * 1000
        
        await monitor.record_detection_latency('test_cam', latency)
        
        if latency < 500:
            results['passed'].append(f"Detection latency: {latency:.1f}ms")
        else:
            results['failed'].append(f"Detection latency: {latency:.1f}ms > 500ms")
    
    # Test 2: GPU memory with multiple streams
    print("Testing GPU memory allocation...")
    gpu_manager = GPUResourceManager()
    cameras_added = 0
    
    for i in range(25):  # Try to add 25 cameras
        can_add, reason = gpu_manager.can_add_stream(
            f"camera_{i}",
            (1920, 1080),
            30,
            'both'
        )
        
        if can_add:
            await gpu_manager.allocate_stream(f"camera_{i}", (1920, 1080), 30)
            cameras_added += 1
        else:
            break
    
    if cameras_added >= 20:
        results['passed'].append(f"GPU can handle {cameras_added} cameras")
    else:
        results['failed'].append(f"GPU can only handle {cameras_added} cameras (need 20+)")
    
    # Generate report
    report = monitor.get_performance_report()
    
    print("\n" + "="*60)
    print("FOUNDATION 3 VALIDATION RESULTS")
    print("="*60)
    print(f"PASSED: {len(results['passed'])}")
    for item in results['passed']:
        print(f"  ✓ {item}")
    
    print(f"\nFAILED: {len(results['failed'])}")
    for item in results['failed']:
        print(f"  ✗ {item}")
    
    print(f"\nSYSTEM STATUS: {report['status']}")
    print(f"REQUIREMENTS MET: {report['requirements_met']}")
    
    return results
```

These implementation guides provide everything you need for the critical components of Foundation 3. Each component has been designed to handle the real-world challenges you'll face with streaming reliability. The key is to implement ALL the safety mechanisms - skip any and you'll have problems in production!