# ONVIF Discovery Implementation Guide

## Overview

ONVIF discovery uses the WS-Discovery protocol to automatically find IP cameras on your network. It operates by sending UDP multicast messages to discover ONVIF-compliant devices.

## Key Concepts

### WS-Discovery Protocol
- **Multicast Address**: 239.255.255.250
- **Port**: 3702
- **Protocol**: SOAP over UDP
- **Message Types**: Probe (discovery request) and ProbeMatch (device response)

### Discovery Methods

1. **Multicast Discovery**
   - Sends a single UDP broadcast to all devices
   - Fastest method but limited by network segmentation
   - Doesn't work across routers/NAT

2. **Network Scan (Unicast)**
   - Probes each IP address individually in a subnet
   - Works across network segments
   - Slower but more reliable

## Implementation

### Python Implementation Using `wsdiscovery`

```python
import socket
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import threading
from typing import List, Dict, Optional
import ipaddress
import concurrent.futures

class ONVIFDevice:
    """Represents a discovered ONVIF device"""
    def __init__(self, ip: str, port: int, service_address: str, scopes: List[str]):
        self.ip = ip
        self.port = port
        self.service_address = service_address
        self.scopes = scopes
        self.manufacturer = self._extract_manufacturer()
        self.model = self._extract_model()
        self.hardware_id = self._extract_hardware_id()
        
    def _extract_manufacturer(self) -> Optional[str]:
        for scope in self.scopes:
            if 'manufacturer' in scope.lower():
                return scope.split('/')[-1]
        return None
    
    def _extract_model(self) -> Optional[str]:
        for scope in self.scopes:
            if 'model' in scope.lower():
                return scope.split('/')[-1]
        return None
    
    def _extract_hardware_id(self) -> Optional[str]:
        for scope in self.scopes:
            if 'hardware' in scope.lower():
                return scope.split('/')[-1]
        return None
    
    def __repr__(self):
        return f"ONVIFDevice(ip={self.ip}, port={self.port}, manufacturer={self.manufacturer}, model={self.model})"

class ONVIFDiscovery:
    """
    @doc
    @purpose: Discovers ONVIF devices on the network using WS-Discovery protocol
    @methods: multicast and unicast (network scan)
    @timeout: configurable discovery timeout (default 5 seconds)
    """
    
    MULTICAST_IP = "239.255.255.250"
    MULTICAST_PORT = 3702
    DISCOVERY_TIMEOUT = 5
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.discovered_devices: List[ONVIFDevice] = []
        self._discovery_lock = threading.Lock()
        
    def create_probe_message(self) -> str:
        """
        @doc
        @purpose: Creates WS-Discovery Probe message
        @returns: SOAP XML message for device discovery
        @note: Message ID must be unique for each probe
        """
        message_id = str(uuid.uuid4())
        
        probe_message = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" 
               xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" 
               xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery">
    <soap:Header>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
        <wsa:MessageID>uuid:{message_id}</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    </soap:Header>
    <soap:Body>
        <wsd:Probe>
            <wsd:Types>tds:Device</wsd:Types>
        </wsd:Probe>
    </soap:Body>
</soap:Envelope>"""
        return probe_message
    
    def parse_probe_match(self, data: bytes, source_ip: str) -> Optional[ONVIFDevice]:
        """
        @doc
        @purpose: Parses ProbeMatch response from ONVIF device
        @param data: Raw SOAP XML response
        @param source_ip: IP address of responding device
        @returns: ONVIFDevice instance or None if parsing fails
        """
        try:
            # Remove XML declaration if it appears multiple times
            xml_data = data.decode('utf-8', errors='ignore')
            xml_start = xml_data.find('<?xml')
            if xml_start > 0:
                xml_data = xml_data[xml_start:]
            
            # Parse XML
            root = ET.fromstring(xml_data)
            
            # Extract namespaces
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'wsd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery',
                'wsa': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
                'd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery'
            }
            
            # Find ProbeMatch
            probe_matches = root.findall('.//wsd:ProbeMatch', namespaces) or \
                           root.findall('.//d:ProbeMatch', namespaces)
            
            if not probe_matches:
                return None
            
            for match in probe_matches:
                # Extract XAddrs (service addresses)
                xaddrs_elem = match.find('.//wsd:XAddrs', namespaces) or \
                             match.find('.//d:XAddrs', namespaces)
                
                if xaddrs_elem is not None and xaddrs_elem.text:
                    service_address = xaddrs_elem.text.strip().split()[0]
                    
                    # Extract port from service address
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(service_address)
                        port = parsed.port or 80
                    except:
                        port = 80
                    
                    # Extract scopes
                    scopes = []
                    scopes_elem = match.find('.//wsd:Scopes', namespaces) or \
                                 match.find('.//d:Scopes', namespaces)
                    
                    if scopes_elem is not None and scopes_elem.text:
                        scopes = scopes_elem.text.strip().split()
                    
                    return ONVIFDevice(
                        ip=source_ip,
                        port=port,
                        service_address=service_address,
                        scopes=scopes
                    )
                    
        except Exception as e:
            print(f"Error parsing response from {source_ip}: {e}")
            
        return None
    
    def discover_multicast(self) -> List[ONVIFDevice]:
        """
        @doc
        @purpose: Performs multicast WS-Discovery
        @method: Sends UDP broadcast to 239.255.255.250:3702
        @returns: List of discovered ONVIF devices
        @limitations: Doesn't work across routers or VLANs
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.5)
        
        # Bind to any available port
        sock.bind(('', 0))
        
        # Send probe message
        probe_msg = self.create_probe_message().encode('utf-8')
        sock.sendto(probe_msg, (self.MULTICAST_IP, self.MULTICAST_PORT))
        
        # Listen for responses
        end_time = time.time() + self.timeout
        devices = []
        
        while time.time() < end_time:
            try:
                data, (ip, port) = sock.recvfrom(65535)
                device = self.parse_probe_match(data, ip)
                if device and not any(d.ip == device.ip for d in devices):
                    devices.append(device)
                    print(f"Discovered device: {device}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error during multicast discovery: {e}")
                
        sock.close()
        return devices
    
    def discover_unicast(self, target_ip: str) -> Optional[ONVIFDevice]:
        """
        @doc
        @purpose: Performs unicast WS-Discovery to specific IP
        @param target_ip: IP address to probe
        @returns: ONVIFDevice if discovered, None otherwise
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        
        try:
            # Send probe message
            probe_msg = self.create_probe_message().encode('utf-8')
            sock.sendto(probe_msg, (target_ip, self.MULTICAST_PORT))
            
            # Wait for response
            data, (ip, port) = sock.recvfrom(65535)
            device = self.parse_probe_match(data, ip)
            return device
            
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error probing {target_ip}: {e}")
            return None
        finally:
            sock.close()
    
    def discover_network_scan(self, subnet: str, max_workers: int = 50) -> List[ONVIFDevice]:
        """
        @doc
        @purpose: Scans entire subnet for ONVIF devices
        @param subnet: CIDR notation subnet (e.g., "192.168.1.0/24")
        @param max_workers: Maximum concurrent probes
        @returns: List of discovered devices
        @note: Slower but works across network segments
        """
        devices = []
        network = ipaddress.ip_network(subnet)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all IPs for scanning
            future_to_ip = {
                executor.submit(self.discover_unicast, str(ip)): ip 
                for ip in network.hosts()
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_ip):
                device = future.result()
                if device:
                    devices.append(device)
                    print(f"Found device via unicast: {device}")
                    
        return devices
    
    def discover(self, method: str = "both", subnets: List[str] = None) -> List[ONVIFDevice]:
        """
        @doc
        @purpose: Main discovery method combining multicast and unicast
        @param method: "multicast", "netscan", or "both"
        @param subnets: List of subnets for network scanning
        @returns: List of all discovered devices
        """
        all_devices = []
        
        if method in ["multicast", "both"]:
            print("Starting multicast discovery...")
            multicast_devices = self.discover_multicast()
            all_devices.extend(multicast_devices)
            
        if method in ["netscan", "both"] and subnets:
            print("Starting network scan discovery...")
            for subnet in subnets:
                print(f"Scanning subnet: {subnet}")
                scan_devices = self.discover_network_scan(subnet)
                
                # Add only new devices
                for device in scan_devices:
                    if not any(d.ip == device.ip for d in all_devices):
                        all_devices.append(device)
                        
        return all_devices

# Usage example with better error handling
class ONVIFDiscoveryManager:
    """
    @doc
    @purpose: High-level manager for ONVIF discovery with persistence
    @features: Device caching, automatic rediscovery, change detection
    """
    
    def __init__(self):
        self.discovered_devices: Dict[str, ONVIFDevice] = {}
        self.discovery = ONVIFDiscovery()
        
    def discover_all(self, subnets: List[str] = None) -> Dict[str, ONVIFDevice]:
        """Discover devices using all available methods"""
        # Default to local subnet if none provided
        if not subnets:
            subnets = [self._get_local_subnet()]
            
        devices = self.discovery.discover(method="both", subnets=subnets)
        
        # Update device cache
        for device in devices:
            self.discovered_devices[device.ip] = device
            
        return self.discovered_devices
    
    def _get_local_subnet(self) -> str:
        """Get local subnet in CIDR notation"""
        import subprocess
        try:
            # Try to get subnet using ip command (Linux)
            result = subprocess.run(
                ["ip", "-4", "-o", "addr", "show", "scope", "global"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'inet' in line:
                        parts = line.split()
                        for part in parts:
                            if '/' in part and '.' in part:
                                return part
        except:
            pass
            
        # Fallback to common subnet
        return "192.168.1.0/24"
    
    def save_devices(self, filename: str = "discovered_devices.json"):
        """Save discovered devices to file"""
        import json
        devices_data = {
            ip: {
                "port": device.port,
                "service_address": device.service_address,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "hardware_id": device.hardware_id,
                "scopes": device.scopes
            }
            for ip, device in self.discovered_devices.items()
        }
        
        with open(filename, 'w') as f:
            json.dump(devices_data, f, indent=2)
            
    def load_devices(self, filename: str = "discovered_devices.json"):
        """Load previously discovered devices"""
        import json
        try:
            with open(filename, 'r') as f:
                devices_data = json.load(f)
                
            for ip, data in devices_data.items():
                self.discovered_devices[ip] = ONVIFDevice(
                    ip=ip,
                    port=data["port"],
                    service_address=data["service_address"],
                    scopes=data["scopes"]
                )
        except FileNotFoundError:
            print(f"No saved devices found at {filename}")

# Example usage
if __name__ == "__main__":
    # Create discovery manager
    manager = ONVIFDiscoveryManager()
    
    # Discover devices on specific subnets
    subnets = ["192.168.1.0/24", "10.0.0.0/24"]
    devices = manager.discover_all(subnets=subnets)
    
    # Print discovered devices
    print(f"\nDiscovered {len(devices)} devices:")
    for ip, device in devices.items():
        print(f"  - {device}")
    
    # Save for future use
    manager.save_devices()
```

### Integration with Your Project

```python
# camera_discovery.py
@doc
@purpose: ONVIF camera discovery module for automatic camera detection
@integration: Call from main application or schedule periodic discovery
@persistence: Saves discovered devices for quick reconnection

class CameraDiscoveryService:
    def __init__(self, camera_manager):
        self.camera_manager = camera_manager
        self.discovery_manager = ONVIFDiscoveryManager()
        self.discovery_thread = None
        self.running = False
        
    def start_continuous_discovery(self, interval: int = 300):
        """Start discovery thread that runs every interval seconds"""
        self.running = True
        self.discovery_thread = threading.Thread(
            target=self._discovery_loop,
            args=(interval,)
        )
        self.discovery_thread.start()
        
    def _discovery_loop(self, interval: int):
        while self.running:
            try:
                self.discover_and_add_cameras()
            except Exception as e:
                print(f"Discovery error: {e}")
            
            time.sleep(interval)
            
    def discover_and_add_cameras(self):
        """Discover cameras and add them to camera manager"""
        devices = self.discovery_manager.discover_all()
        
        for ip, device in devices.items():
            if not self.camera_manager.has_camera(ip):
                # Add new camera
                self.camera_manager.add_camera({
                    'ip': device.ip,
                    'port': device.port,
                    'onvif_port': device.port,
                    'username': 'admin',  # Default, should be configurable
                    'password': '',       # Default, should be configurable
                    'name': f"{device.manufacturer} {device.model}" if device.manufacturer else f"Camera {ip}",
                    'rtsp_url': f"rtsp://{device.ip}:554/stream1",  # Default, discover via ONVIF later
                    'onvif_service_url': device.service_address
                })
                print(f"Added new camera: {ip}")
```

## Network Configuration

### Docker Configuration
When running in Docker, you need special network configuration:

```yaml
# docker-compose.yml
services:
  camera-app:
    image: your-app
    network_mode: host  # Required for multicast
    environment:
      - DISCOVERY_MODE=both
      - DISCOVERY_SUBNETS=192.168.1.0/24,10.0.0.0/24
      - DISCOVERY_TIMEOUT=10
```

### Firewall Rules
Allow UDP port 3702 for WS-Discovery:
```bash
# Linux iptables
sudo iptables -A INPUT -p udp --dport 3702 -j ACCEPT

# Windows Firewall
netsh advfirewall firewall add rule name="ONVIF Discovery" dir=in action=allow protocol=UDP localport=3702
```

## Troubleshooting

### Common Issues

1. **No devices found with multicast**
   - Check if multicast is blocked by firewall
   - Verify devices are on same network segment
   - Try unicast/netscan method instead

2. **Timeout errors**
   - Increase discovery timeout
   - Reduce number of concurrent connections
   - Check network connectivity

3. **XML parsing errors**
   - Some cameras send malformed XML
   - Use error handling and fallback parsing

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Debug specific device
discovery = ONVIFDiscovery(timeout=10)
device = discovery.discover_unicast("192.168.1.100")
if device:
    print(f"Device info: {device.__dict__}")
```

## Best Practices

1. **Cache discovered devices** - Don't rediscover on every startup
2. **Use both methods** - Multicast for speed, unicast for reliability  
3. **Handle network changes** - Rediscover when network changes
4. **Implement retry logic** - Network operations can fail
5. **Validate devices** - Verify ONVIF compliance after discovery

## Next Steps

After discovery, you should:
1. Connect to device using ONVIF protocol
2. Get device capabilities
3. Retrieve stream URLs
4. Configure device settings

See the ONVIF Device Management guide for next steps.