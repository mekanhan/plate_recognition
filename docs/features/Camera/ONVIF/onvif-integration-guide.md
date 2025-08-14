# ONVIF Discovery Integration Guide

## Quick Start

### 1. Install Dependencies

```bash
# No external dependencies required for basic discovery
# Uses only Python standard library

# Optional: For advanced features
pip install netifaces  # For automatic subnet detection
pip install python-onvif-zeep  # For full ONVIF protocol support
```

### 2. Basic Usage

```python
from onvif_discovery import discover_cameras

# Discover cameras with 10 second timeout
cameras = discover_cameras(timeout=10.0)

for camera in cameras:
    print(f"Found: {camera.ip} - {camera.manufacturer} {camera.model}")
```

### 3. Integration with Your Camera Manager

```python
# In your main application
from onvif_discovery import CameraAutoDiscovery

# Create auto-discovery service
auto_discovery = CameraAutoDiscovery(camera_manager)

# Start automatic discovery (runs every 5 minutes)
auto_discovery.start()

# Stop when shutting down
auto_discovery.stop()
```

## Advanced Integration

### Custom Discovery Handler

```python
@doc
@purpose: Custom discovery handler with authentication
@integration: Replaces default camera addition logic

class CustomCameraDiscovery(CameraAutoDiscovery):
    def __init__(self, camera_manager, credentials_manager):
        super().__init__(camera_manager)
        self.credentials_manager = credentials_manager
        
    def _add_camera(self, camera):
        """Override to add custom logic"""
        # Try to get credentials for this camera
        creds = self.credentials_manager.get_credentials(
            camera.manufacturer,
            camera.model
        )
        
        camera_config = {
            'ip': camera.ip,
            'port': camera.port,
            'name': self._generate_camera_name(camera),
            'username': creds.get('username', 'admin'),
            'password': creds.get('password', ''),
            'rtsp_url': self._discover_rtsp_url(camera),
            'onvif_service_url': camera.service_url,
            'capabilities': self._get_camera_capabilities(camera)
        }
        
        self.camera_manager.add_camera(camera_config)
        
    def _discover_rtsp_url(self, camera):
        """Use ONVIF to discover actual RTSP URL"""
        # This would use python-onvif-zeep to connect
        # and query the camera for its stream URLs
        return f"rtsp://{camera.ip}:554/stream1"
```

### Network-Specific Discovery

```python
@doc
@purpose: Discover cameras on specific network interfaces
@use_case: Multi-homed systems, VLANs

import netifaces

class NetworkAwareDiscovery(ONVIFDiscovery):
    def discover_on_interface(self, interface_name):
        """Discover cameras on specific network interface"""
        # Get interface addresses
        addrs = netifaces.ifaddresses(interface_name)
        if netifaces.AF_INET not in addrs:
            return []
            
        # Bind to specific interface
        interface_ip = addrs[netifaces.AF_INET][0]['addr']
        
        # Modify socket binding
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((interface_ip, 0))
        
        # Continue with discovery...
```

### Subnet Scanning (Unicast Discovery)

```python
@doc
@purpose: Scan specific subnets when multicast doesn't work
@note: Useful for cameras on different VLANs

import ipaddress
import concurrent.futures

def scan_subnet_for_cameras(subnet_cidr, timeout=1.0):
    """
    Scan subnet using unicast WS-Discovery
    
    Args:
        subnet_cidr: Subnet in CIDR notation (e.g., "192.168.1.0/24")
        timeout: Timeout per IP probe
    """
    discovery = ONVIFDiscovery(timeout=timeout)
    cameras = []
    
    # Parse subnet
    network = ipaddress.ip_network(subnet_cidr)
    
    def probe_ip(ip):
        """Probe single IP for ONVIF service"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        try:
            # Send probe to specific IP
            probe = discovery._create_probe_message(str(uuid.uuid4()))
            sock.sendto(probe.encode(), (str(ip), 3702))
            
            # Wait for response
            data, addr = sock.recvfrom(65535)
            camera = discovery._parse_probe_response(data, str(ip))
            return camera
        except:
            return None
        finally:
            sock.close()
    
    # Scan all IPs in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(probe_ip, ip) for ip in network.hosts()]
        
        for future in concurrent.futures.as_completed(futures):
            camera = future.result()
            if camera:
                cameras.append(camera)
                
    return cameras
```

## Configuration

### Environment Variables

```python
# config.py
import os

DISCOVERY_CONFIG = {
    # Discovery method: 'multicast', 'unicast', or 'both'
    'method': os.getenv('DISCOVERY_METHOD', 'multicast'),
    
    # Discovery timeout in seconds
    'timeout': float(os.getenv('DISCOVERY_TIMEOUT', '5.0')),
    
    # Subnets for unicast scanning
    'subnets': os.getenv('DISCOVERY_SUBNETS', '').split(','),
    
    # Auto-discovery interval in seconds
    'interval': int(os.getenv('DISCOVERY_INTERVAL', '300')),
    
    # Save discovered cameras
    'persist': os.getenv('DISCOVERY_PERSIST', 'true').lower() == 'true',
    
    # Discovery cache file
    'cache_file': os.getenv('DISCOVERY_CACHE', 'discovered_cameras.json')
}
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install network tools for debugging
RUN apt-get update && apt-get install -y \
    iputils-ping \
    net-tools \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

# Run with host networking for multicast
CMD ["python", "camera_app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  camera-discovery:
    build: .
    network_mode: host  # Required for multicast
    environment:
      - DISCOVERY_METHOD=both
      - DISCOVERY_TIMEOUT=10
      - DISCOVERY_SUBNETS=192.168.1.0/24,10.0.0.0/24
      - DISCOVERY_INTERVAL=300
    volumes:
      - ./data:/app/data  # For persistence
```

## Debugging

### Enable Debug Logging

```python
import logging

# Enable debug logging for discovery
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('onvif_discovery')
logger.setLevel(logging.DEBUG)

# Add console handler with formatting
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)
```

### Network Debugging

```python
# Test multicast connectivity
def test_multicast():
    """Test if multicast is working"""
    import struct
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    
    # Join multicast group
    mreq = struct.pack("4sl", socket.inet_aton("239.255.255.250"), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    sock.bind(('', 3702))
    
    print("Listening for multicast packets...")
    try:
        data, addr = sock.recvfrom(65535)
        print(f"Received multicast from {addr}")
        return True
    except socket.timeout:
        print("No multicast packets received")
        return False
    finally:
        sock.close()
```

### Wireshark Filter

To debug WS-Discovery traffic in Wireshark:
```
# Filter for WS-Discovery
udp.port == 3702

# Filter for ONVIF discovery
udp.port == 3702 and data contains "onvif"
```

## Common Issues and Solutions

### 1. No Cameras Found

**Possible Causes:**
- Cameras not ONVIF compliant
- Different network segment/VLAN
- Firewall blocking UDP 3702
- Multicast disabled on network

**Solutions:**
```python
# Try unicast scanning
cameras = scan_subnet_for_cameras("192.168.1.0/24")

# Check specific camera
def test_camera(ip):
    discovery = ONVIFDiscovery()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    
    probe = discovery._create_probe_message(str(uuid.uuid4()))
    sock.sendto(probe.encode(), (ip, 3702))
    
    try:
        data, _ = sock.recvfrom(65535)
        print(f"Camera at {ip} responded!")
        return True
    except:
        print(f"No response from {ip}")
        return False
    finally:
        sock.close()
```

### 2. Partial Discovery

**Issue:** Some cameras found but not all

**Solution:**
```python
# Increase timeout and run multiple times
def thorough_discovery():
    all_cameras = {}
    
    # Run discovery multiple times
    for i in range(3):
        discovery = ONVIFDiscovery(timeout=10.0)
        cameras = discovery.discover()
        
        for camera in cameras:
            all_cameras[camera.ip] = camera
            
        time.sleep(2)  # Wait between attempts
        
    return list(all_cameras.values())
```

### 3. Docker/Container Issues

**Issue:** No discovery in Docker

**Solution:**
```yaml
# Use host networking
network_mode: host

# Or use macvlan for proper multicast
networks:
  camera_net:
    driver: macvlan
    driver_opts:
      parent: eth0
    ipam:
      config:
        - subnet: 192.168.1.0/24
```

## Performance Optimization

### Caching and Persistence

```python
class CachedDiscovery:
    def __init__(self, cache_duration=3600):
        self.cache_duration = cache_duration
        self.cache_file = "camera_cache.json"
        
    def discover_with_cache(self):
        # Check cache first
        cached = self._load_cache()
        if cached and self._is_cache_valid(cached):
            return cached['cameras']
            
        # Run discovery
        discovery = ONVIFDiscovery()
        cameras = discovery.discover()
        
        # Save to cache
        self._save_cache(cameras)
        
        return cameras
```

### Parallel Discovery

```python
def parallel_discovery(interfaces):
    """Discover on multiple interfaces in parallel"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(discover_on_interface, iface): iface
            for iface in interfaces
        }
        
        all_cameras = {}
        for future in concurrent.futures.as_completed(futures):
            cameras = future.result()
            for camera in cameras:
                all_cameras[camera.ip] = camera
                
    return list(all_cameras.values())
```

## Next Steps

1. **Implement ONVIF device management** - Connect to discovered cameras
2. **Get stream URLs** - Use ONVIF to get actual RTSP URLs
3. **Configure cameras** - Set resolution, framerate, etc.
4. **Monitor camera health** - Periodic connectivity checks
5. **Handle camera events** - Motion detection, tampering alerts

See the ONVIF Device Management guide for connecting to discovered cameras.