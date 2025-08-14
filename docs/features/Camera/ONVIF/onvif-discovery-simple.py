# onvif_discovery.py
"""
ONVIF Camera Discovery Module
Discovers IP cameras on the network using WS-Discovery protocol
"""

import socket
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import threading
from typing import List, Dict, Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)

class DiscoveredCamera:
    """Represents a discovered ONVIF camera"""
    def __init__(self, data: dict):
        self.ip = data.get('ip')
        self.port = data.get('port', 80)
        self.service_url = data.get('service_url', '')
        self.name = data.get('name', f'Camera_{self.ip}')
        self.manufacturer = data.get('manufacturer', 'Unknown')
        self.model = data.get('model', 'Unknown')
        self.mac_address = data.get('mac_address', '')
        self.scopes = data.get('scopes', [])
        self.discovered_at = data.get('discovered_at', datetime.now().isoformat())
        
    def to_dict(self) -> dict:
        return {
            'ip': self.ip,
            'port': self.port,
            'service_url': self.service_url,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'mac_address': self.mac_address,
            'scopes': self.scopes,
            'discovered_at': self.discovered_at
        }

class ONVIFDiscovery:
    """Simple ONVIF discovery implementation"""
    
    MULTICAST_IP = "239.255.255.250"
    MULTICAST_PORT = 3702
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.discovered_cameras: Dict[str, DiscoveredCamera] = {}
        
    def discover(self) -> List[DiscoveredCamera]:
        """
        Discover ONVIF cameras using multicast WS-Discovery
        Returns list of discovered cameras
        """
        # Create probe message with unique ID
        message_id = str(uuid.uuid4())
        probe_message = self._create_probe_message(message_id)
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.5)
        
        try:
            # Bind to any available port
            sock.bind(('', 0))
            
            # Send probe message
            logger.info(f"Sending WS-Discovery probe to {self.MULTICAST_IP}:{self.MULTICAST_PORT}")
            sock.sendto(probe_message.encode('utf-8'), (self.MULTICAST_IP, self.MULTICAST_PORT))
            
            # Listen for responses
            end_time = time.time() + self.timeout
            while time.time() < end_time:
                try:
                    data, (sender_ip, sender_port) = sock.recvfrom(65535)
                    camera = self._parse_probe_response(data, sender_ip)
                    if camera:
                        self.discovered_cameras[camera.ip] = camera
                        logger.info(f"Discovered camera: {camera.ip} - {camera.manufacturer} {camera.model}")
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error parsing response: {e}")
                    
        except Exception as e:
            logger.error(f"Discovery error: {e}")
        finally:
            sock.close()
            
        return list(self.discovered_cameras.values())
    
    def _create_probe_message(self, message_id: str) -> str:
        """Create WS-Discovery Probe message"""
        return f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope" 
    xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" 
    xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery"
    xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
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
</soap:Envelope>'''
    
    def _parse_probe_response(self, data: bytes, sender_ip: str) -> Optional[DiscoveredCamera]:
        """Parse ProbeMatch response from camera"""
        try:
            # Decode and clean XML
            xml_str = data.decode('utf-8', errors='ignore')
            
            # Find actual XML start (some cameras send garbage before XML)
            xml_start = xml_str.find('<?xml')
            if xml_start > 0:
                xml_str = xml_str[xml_start:]
                
            # Parse XML
            root = ET.fromstring(xml_str)
            
            # Define namespaces
            ns = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'wsd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery',
                'd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery',
                'wsa': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
                'wsadis': 'http://schemas.xmlsoap.org/ws/2004/08/addressing'
            }
            
            # Find ProbeMatch element
            probe_match = None
            for prefix in ['wsd', 'd']:
                probe_match = root.find(f'.//{{{ns.get(prefix)}}}ProbeMatch')
                if probe_match is not None:
                    break
                    
            if probe_match is None:
                return None
                
            # Extract XAddrs (service URL)
            service_url = None
            for prefix in ['wsd', 'd']:
                xaddrs = probe_match.find(f'.//{{{ns.get(prefix)}}}XAddrs')
                if xaddrs is not None and xaddrs.text:
                    service_url = xaddrs.text.strip().split()[0]
                    break
                    
            if not service_url:
                return None
                
            # Extract scopes
            scopes = []
            for prefix in ['wsd', 'd']:
                scopes_elem = probe_match.find(f'.//{{{ns.get(prefix)}}}Scopes')
                if scopes_elem is not None and scopes_elem.text:
                    scopes = scopes_elem.text.strip().split()
                    break
                    
            # Parse camera information from scopes
            camera_data = {
                'ip': sender_ip,
                'service_url': service_url,
                'scopes': scopes,
                'discovered_at': datetime.now().isoformat()
            }
            
            # Extract port from service URL
            try:
                from urllib.parse import urlparse
                parsed = urlparse(service_url)
                camera_data['port'] = parsed.port or 80
            except:
                camera_data['port'] = 80
                
            # Parse manufacturer, model, MAC from scopes
            for scope in scopes:
                scope_lower = scope.lower()
                if 'manufacturer' in scope_lower:
                    camera_data['manufacturer'] = scope.split('/')[-1]
                elif 'model' in scope_lower:
                    camera_data['model'] = scope.split('/')[-1]
                elif 'mac' in scope_lower:
                    camera_data['mac_address'] = scope.split('/')[-1]
                elif 'name' in scope_lower:
                    camera_data['name'] = scope.split('/')[-1]
                    
            return DiscoveredCamera(camera_data)
            
        except Exception as e:
            logger.error(f"Failed to parse response from {sender_ip}: {e}")
            return None
    
    def save_discovered_cameras(self, filename: str = 'discovered_cameras.json'):
        """Save discovered cameras to JSON file"""
        cameras_data = {
            ip: camera.to_dict() 
            for ip, camera in self.discovered_cameras.items()
        }
        
        with open(filename, 'w') as f:
            json.dump(cameras_data, f, indent=2)
        logger.info(f"Saved {len(cameras_data)} cameras to {filename}")
        
    def load_discovered_cameras(self, filename: str = 'discovered_cameras.json') -> List[DiscoveredCamera]:
        """Load previously discovered cameras from JSON file"""
        try:
            with open(filename, 'r') as f:
                cameras_data = json.load(f)
                
            self.discovered_cameras = {
                ip: DiscoveredCamera(data)
                for ip, data in cameras_data.items()
            }
            logger.info(f"Loaded {len(self.discovered_cameras)} cameras from {filename}")
            return list(self.discovered_cameras.values())
            
        except FileNotFoundError:
            logger.warning(f"No saved cameras found at {filename}")
            return []

# Simple usage example
def discover_cameras(timeout: float = 5.0) -> List[DiscoveredCamera]:
    """
    Simple function to discover ONVIF cameras
    
    Args:
        timeout: Discovery timeout in seconds
        
    Returns:
        List of discovered cameras
    """
    discovery = ONVIFDiscovery(timeout=timeout)
    cameras = discovery.discover()
    
    if cameras:
        # Save for future use
        discovery.save_discovered_cameras()
        
    return cameras

# Integration with your camera manager
class CameraAutoDiscovery:
    """
    @doc
    @purpose: Automatic camera discovery service
    @features: Periodic discovery, new camera detection, persistence
    """
    
    def __init__(self, camera_manager):
        self.camera_manager = camera_manager
        self.discovery = ONVIFDiscovery()
        self.discovery_interval = 300  # 5 minutes
        self._stop_event = threading.Event()
        self._discovery_thread = None
        
    def start(self):
        """Start automatic discovery service"""
        logger.info("Starting camera auto-discovery service")
        self._discovery_thread = threading.Thread(target=self._discovery_loop)
        self._discovery_thread.daemon = True
        self._discovery_thread.start()
        
    def stop(self):
        """Stop automatic discovery service"""
        logger.info("Stopping camera auto-discovery service")
        self._stop_event.set()
        if self._discovery_thread:
            self._discovery_thread.join()
            
    def _discovery_loop(self):
        """Background discovery loop"""
        # Do initial discovery immediately
        self._run_discovery()
        
        while not self._stop_event.is_set():
            # Wait for interval or stop event
            if self._stop_event.wait(self.discovery_interval):
                break
                
            self._run_discovery()
            
    def _run_discovery(self):
        """Run discovery and add new cameras"""
        try:
            logger.info("Running camera discovery...")
            cameras = self.discovery.discover()
            
            new_cameras = 0
            for camera in cameras:
                if not self._camera_exists(camera.ip):
                    self._add_camera(camera)
                    new_cameras += 1
                    
            if new_cameras > 0:
                logger.info(f"Added {new_cameras} new cameras")
            else:
                logger.info("No new cameras found")
                
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            
    def _camera_exists(self, ip: str) -> bool:
        """Check if camera already exists in manager"""
        # Implement based on your camera manager
        return self.camera_manager.get_camera_by_ip(ip) is not None
        
    def _add_camera(self, camera: DiscoveredCamera):
        """Add discovered camera to manager"""
        logger.info(f"Adding new camera: {camera.ip} ({camera.manufacturer} {camera.model})")
        
        # Create camera configuration
        camera_config = {
            'ip': camera.ip,
            'port': camera.port,
            'name': camera.name or f"{camera.manufacturer} {camera.model}",
            'username': 'admin',  # Default username
            'password': '',       # Default password (should be configurable)
            'rtsp_url': f"rtsp://{camera.ip}:554/stream1",  # Default RTSP URL
            'onvif_port': camera.port,
            'onvif_service_url': camera.service_url,
            'manufacturer': camera.manufacturer,
            'model': camera.model,
            'auto_discovered': True
        }
        
        # Add to camera manager
        self.camera_manager.add_camera(camera_config)

# Command-line interface
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run discovery
    print("Discovering ONVIF cameras...")
    cameras = discover_cameras(timeout=10.0)
    
    if cameras:
        print(f"\nFound {len(cameras)} cameras:")
        for camera in cameras:
            print(f"  - {camera.ip}: {camera.manufacturer} {camera.model}")
            print(f"    Service URL: {camera.service_url}")
            print(f"    MAC: {camera.mac_address}")
            print()
    else:
        print("No cameras found")
        print("\nTroubleshooting tips:")
        print("  1. Ensure cameras are ONVIF compliant")
        print("  2. Check if you're on the same network segment")
        print("  3. Verify firewall allows UDP port 3702")
        print("  4. Try running with sudo/admin privileges")