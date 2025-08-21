"""
ONVIF Discovery Service for Vision Port
Integrates ONVIF camera discovery with the existing camera management system
"""

import socket
import uuid
import xml.etree.ElementTree as ET
import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import asyncio
import ipaddress
import concurrent.futures

logger = logging.getLogger(__name__)

class ONVIFCamera:
    """Represents a discovered ONVIF camera"""
    def __init__(self, ip: str, port: int, service_url: str, scopes: List[str]):
        self.ip = ip
        self.port = port
        self.service_url = service_url
        self.scopes = scopes
        self.manufacturer = self._extract_from_scopes('manufacturer')
        self.model = self._extract_from_scopes('model')
        self.hardware_id = self._extract_from_scopes('hardware')
        self.name = self._extract_from_scopes('name') or f"Camera_{ip}"
        
    def _extract_from_scopes(self, key: str) -> Optional[str]:
        """Extract information from ONVIF scopes"""
        for scope in self.scopes:
            if key.lower() in scope.lower():
                parts = scope.split('/')
                return parts[-1] if parts else None
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'ip': self.ip,
            'port': self.port,
            'service_url': self.service_url,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'hardware_id': self.hardware_id,
            'name': self.name,
            'scopes': self.scopes
        }

class ONVIFDiscoveryService:
    """
    ONVIF Discovery Service integrated with Vision Port
    Based on the documented ONVIF implementation
    """
    
    MULTICAST_IP = "239.255.255.250"
    MULTICAST_PORT = 3702
    
    # Brand-specific configurations
    BRAND_CONFIGS = {
        'reolink': {
            'keywords': ['reolink'],
            'default_paths': {
                'main': '/h265Preview_01_main',  # H.265 is common for newer Reolink cameras
                'sub': '/h265Preview_01_sub'
            },
            'default_port': 554,
            'onvif_port': 8000,  # Updated to match your camera
            'onvif_ports': [8000, 8080],  # Common Reolink ONVIF ports
            'default_username': 'admin'
        },
        'hikvision': {
            'keywords': ['hikvision', 'hikvis'],
            'default_paths': {
                'main': '/Streaming/Channels/101',
                'sub': '/Streaming/Channels/102'
            },
            'default_port': 554,
            'onvif_port': 80,
            'default_username': 'admin'
        },
        'dahua': {
            'keywords': ['dahua'],
            'default_paths': {
                'main': '/cam/realmonitor?channel=1&subtype=0',
                'sub': '/cam/realmonitor?channel=1&subtype=1'
            },
            'default_port': 554,
            'onvif_port': 80,
            'default_username': 'admin'
        },
        'axis': {
            'keywords': ['axis'],
            'default_paths': {
                'main': '/axis-media/media.amp',
                'sub': '/axis-media/media.amp?resolution=640x480'
            },
            'default_port': 554,
            'onvif_port': 80,
            'default_username': 'root'
        },
        'generic': {
            'keywords': [],
            'default_paths': {
                'main': '/stream1',
                'sub': '/stream2'
            },
            'default_port': 554,
            'onvif_port': 80,
            'default_username': 'admin'
        }
    }
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.discovered_cameras = {}
        self.cache_file = Path("data/onvif_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        self.onvif_username = None
        self.onvif_password = None
    
    def set_credentials(self, username: str, password: str):
        """Set ONVIF credentials for authenticated discovery"""
        self.onvif_username = username
        self.onvif_password = password
        logger.info(f"Using ONVIF credentials for discovery: username={username}")
        
    def discover(self, method: str = "multicast", subnets: List[str] = None) -> List[ONVIFCamera]:
        """
        Main discovery method
        Args:
            method: "multicast", "unicast", or "both"
            subnets: List of subnets for unicast scanning (e.g., ["192.168.1.0/24"])
        Returns:
            List of discovered ONVIF cameras
        """
        cameras = []
        
        if method in ["multicast", "both"]:
            logger.info("Starting multicast ONVIF discovery...")
            multicast_cameras = self._discover_multicast()
            cameras.extend(multicast_cameras)
            
        if method in ["unicast", "both"] and subnets:
            logger.info(f"Starting unicast discovery on subnets: {subnets}")
            for subnet in subnets:
                subnet_cameras = self._scan_subnet(subnet)
                cameras.extend(subnet_cameras)
        
        # Remove duplicates based on IP
        unique_cameras = {}
        for camera in cameras:
            if camera.ip not in unique_cameras:
                unique_cameras[camera.ip] = camera
        
        self.discovered_cameras = unique_cameras
        self._save_cache()
        
        return list(unique_cameras.values())
    
    def _create_probe_message(self, message_id: str) -> str:
        """Create WS-Discovery Probe message"""
        return f"""<?xml version="1.0" encoding="utf-8"?>
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
    
    def _parse_probe_response(self, data: bytes, source_ip: str) -> Optional[ONVIFCamera]:
        """Parse ProbeMatch response from ONVIF device"""
        try:
            xml_data = data.decode('utf-8', errors='ignore')
            
            # Find XML start
            xml_start = xml_data.find('<?xml')
            if xml_start > 0:
                xml_data = xml_data[xml_start:]
            
            root = ET.fromstring(xml_data)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'wsd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery',
                'wsa': 'http://schemas.xmlsoap.org/ws/2004/08/addressing'
            }
            
            # Find ProbeMatch elements
            probe_matches = root.findall('.//wsd:ProbeMatch', namespaces)
            
            for match in probe_matches:
                # Extract service address
                xaddrs = match.find('.//wsd:XAddrs', namespaces)
                if xaddrs is not None and xaddrs.text:
                    service_url = xaddrs.text.strip().split()[0]
                    
                    # Extract port from service URL
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(service_url)
                        port = parsed.port or 80
                    except:
                        port = 80
                    
                    # Extract scopes
                    scopes = []
                    scopes_elem = match.find('.//wsd:Scopes', namespaces)
                    if scopes_elem is not None and scopes_elem.text:
                        scopes = scopes_elem.text.strip().split()
                    
                    return ONVIFCamera(source_ip, port, service_url, scopes)
                    
        except Exception as e:
            logger.error(f"Error parsing response from {source_ip}: {e}")
            
        return None
    
    def _discover_multicast(self) -> List[ONVIFCamera]:
        """Perform multicast WS-Discovery"""
        cameras = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.5)
            
            # Bind to any available port
            sock.bind(('', 0))
            
            # Send probe message
            probe_msg = self._create_probe_message(str(uuid.uuid4()))
            sock.sendto(probe_msg.encode('utf-8'), (self.MULTICAST_IP, self.MULTICAST_PORT))
            logger.info(f"Sent multicast probe to {self.MULTICAST_IP}:{self.MULTICAST_PORT}")
            
            # Listen for responses
            end_time = time.time() + self.timeout
            while time.time() < end_time:
                try:
                    data, (ip, port) = sock.recvfrom(65535)
                    camera = self._parse_probe_response(data, ip)
                    if camera:
                        cameras.append(camera)
                        logger.info(f"Discovered: {camera.manufacturer} {camera.model} at {camera.ip}")
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error during multicast discovery: {e}")
                    
            sock.close()
            
        except Exception as e:
            logger.error(f"Multicast discovery failed: {e}")
            
        return cameras
    
    def _discover_unicast(self, target_ip: str) -> Optional[ONVIFCamera]:
        """Perform unicast discovery to specific IP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            
            # Send probe
            probe_msg = self._create_probe_message(str(uuid.uuid4()))
            sock.sendto(probe_msg.encode('utf-8'), (target_ip, self.MULTICAST_PORT))
            
            # Wait for response
            data, (ip, port) = sock.recvfrom(65535)
            camera = self._parse_probe_response(data, ip)
            
            sock.close()
            return camera
            
        except socket.timeout:
            # If WS-Discovery fails, try direct ONVIF probing
            return self._discover_direct_onvif(target_ip)
        except Exception as e:
            logger.debug(f"No ONVIF response from {target_ip}: {e}")
            # Try direct ONVIF as fallback
            return self._discover_direct_onvif(target_ip)
    
    def _scan_subnet(self, subnet: str, max_workers: int = 50) -> List[ONVIFCamera]:
        """Scan subnet for ONVIF cameras using unicast"""
        cameras = []
        
        try:
            network = ipaddress.ip_network(subnet)
            logger.info(f"Scanning subnet {subnet} ({network.num_addresses} addresses)")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all IPs for scanning
                futures = {
                    executor.submit(self._discover_unicast, str(ip)): ip 
                    for ip in network.hosts()
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(futures):
                    camera = future.result()
                    if camera:
                        cameras.append(camera)
                        logger.info(f"Found via unicast: {camera.manufacturer} at {camera.ip}")
                        
        except Exception as e:
            logger.error(f"Subnet scan failed for {subnet}: {e}")
            
        return cameras
    
    def _discover_direct_onvif(self, target_ip: str) -> Optional[ONVIFCamera]:
        """
        Direct ONVIF discovery via HTTP SOAP calls
        Fallback method for cameras that don't respond to WS-Discovery
        """
        import requests
        from urllib.parse import urljoin
        
        # Common ONVIF ports to try
        onvif_ports = [80, 8080, 8000, 8081, 8888, 554]
        
        for port in onvif_ports:
            try:
                # Try to get device information via SOAP
                service_url = f"http://{target_ip}:{port}/onvif/device_service"
                
                # Create GetDeviceInformation SOAP request
                soap_body = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Header/>
    <soap:Body>
        <tds:GetDeviceInformation/>
    </soap:Body>
</soap:Envelope>'''
                
                headers = {
                    'Content-Type': 'application/soap+xml; charset=utf-8',
                    'SOAPAction': '"http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation"'
                }
                
                # Use credentials if provided
                auth = None
                if self.onvif_username and self.onvif_password:
                    auth = (self.onvif_username, self.onvif_password)
                
                # Make SOAP request with short timeout
                response = requests.post(service_url, data=soap_body, headers=headers, 
                                       auth=auth, timeout=2)
                
                if response.status_code == 200 and 'GetDeviceInformationResponse' in response.text:
                    # Parse device information from SOAP response
                    device_info = self._parse_device_info_response(response.text)
                    
                    if device_info:
                        logger.info(f"Direct ONVIF discovery successful: {target_ip}:{port}")
                        
                        # Create camera with discovered information
                        scopes = [
                            f"onvif://www.onvif.org/name/{device_info.get('Model', 'Unknown')}",
                            f"onvif://www.onvif.org/hardware/{device_info.get('SerialNumber', 'Unknown')}",
                            f"onvif://www.onvif.org/manufacturer/{device_info.get('Manufacturer', 'Unknown')}"
                        ]
                        
                        return ONVIFCamera(
                            ip=target_ip,
                            port=port,
                            service_url=service_url,
                            scopes=scopes
                        )
                
                elif response.status_code == 401 or 'NotAuthorized' in response.text:
                    # Camera responded with authentication error - it's an ONVIF camera!
                    if self.onvif_username and self.onvif_password:
                        # Credentials were provided but failed
                        logger.info(f"ONVIF camera detected (auth failed): {target_ip}:{port}")
                        camera_name = "Camera (Auth Failed)"
                    else:
                        # No credentials provided
                        logger.info(f"ONVIF camera detected (requires auth): {target_ip}:{port}")
                        camera_name = "Camera (Auth Required)"
                    
                    # Create camera entry even without detailed info
                    scopes = [
                        f"onvif://www.onvif.org/name/{camera_name}",
                        f"onvif://www.onvif.org/manufacturer/Unknown"
                    ]
                    
                    return ONVIFCamera(
                        ip=target_ip,
                        port=port,
                        service_url=service_url,
                        scopes=scopes
                    )
                
            except requests.exceptions.RequestException:
                continue
            except Exception as e:
                logger.debug(f"Direct ONVIF probe failed for {target_ip}:{port}: {e}")
                continue
        
        return None
    
    def _parse_device_info_response(self, response_xml: str) -> Optional[dict]:
        """Parse GetDeviceInformation SOAP response"""
        try:
            root = ET.fromstring(response_xml)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'tds': 'http://www.onvif.org/ver10/device/wsdl'
            }
            
            # Find device info elements
            device_info = {}
            
            manufacturer = root.find('.//tds:Manufacturer', namespaces)
            if manufacturer is not None:
                device_info['Manufacturer'] = manufacturer.text
                
            model = root.find('.//tds:Model', namespaces)
            if model is not None:
                device_info['Model'] = model.text
                
            serial = root.find('.//tds:SerialNumber', namespaces)
            if serial is not None:
                device_info['SerialNumber'] = serial.text
                
            firmware = root.find('.//tds:FirmwareVersion', namespaces)
            if firmware is not None:
                device_info['FirmwareVersion'] = firmware.text
            
            return device_info if device_info else None
            
        except Exception as e:
            logger.debug(f"Failed to parse device info response: {e}")
            return None

    def detect_brand(self, camera: ONVIFCamera) -> str:
        """Detect camera brand from manufacturer/model info"""
        info = f"{camera.manufacturer or ''} {camera.model or ''}".lower()
        
        for brand, config in self.BRAND_CONFIGS.items():
            for keyword in config['keywords']:
                if keyword in info:
                    return brand
        
        return 'generic'
    
    def get_camera_config(self, camera: ONVIFCamera) -> dict:
        """
        Generate Vision Port camera configuration from ONVIF camera
        """
        brand = self.detect_brand(camera)
        brand_config = self.BRAND_CONFIGS[brand]
        
        return {
            'camera_id': f"onvif_{camera.ip.replace('.', '_')}",
            'name': camera.name or f"{camera.manufacturer} {camera.model}".strip() or f"Camera {camera.ip}",
            'ip_address': camera.ip,
            'port': brand_config['default_port'],
            'connection_type': 'rtsp',
            'stream_path': brand_config['default_paths']['main'],
            'username': brand_config['default_username'],
            'password': '',  # Must be set manually
            'brand': camera.manufacturer,
            'model': camera.model,
            # ONVIF metadata
            'onvif_service_url': camera.service_url,
            'onvif_port': brand_config['onvif_port'],
            'manufacturer': camera.manufacturer,
            'discovered_via': 'onvif',
            'discovery_timestamp': datetime.utcnow().isoformat(),
            'hardware_id': camera.hardware_id,
            'onvif_scopes': camera.scopes,
            # Detected brand info
            'detected_brand': brand,
            'sub_stream_path': brand_config['default_paths']['sub']
        }
    
    def _save_cache(self):
        """Save discovered cameras to cache file"""
        try:
            cache_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'cameras': [camera.to_dict() for camera in self.discovered_cameras.values()]
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"Saved {len(self.discovered_cameras)} cameras to cache")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def load_cache(self) -> List[ONVIFCamera]:
        """Load previously discovered cameras from cache"""
        if not self.cache_file.exists():
            return []
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cameras = []
            for camera_data in cache_data.get('cameras', []):
                camera = ONVIFCamera(
                    ip=camera_data['ip'],
                    port=camera_data['port'],
                    service_url=camera_data['service_url'],
                    scopes=camera_data.get('scopes', [])
                )
                cameras.append(camera)
                self.discovered_cameras[camera.ip] = camera
            
            logger.info(f"Loaded {len(cameras)} cameras from cache")
            return cameras
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return []
    
    def get_local_subnet(self) -> str:
        """Get local network subnet for scanning"""
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Convert to /24 subnet
            parts = local_ip.split('.')
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            return subnet
            
        except Exception as e:
            logger.error(f"Failed to get local subnet: {e}")
            return "192.168.1.0/24"  # Default fallback
    
    def get_all_local_subnets(self) -> List[str]:
        """Get all local network subnets for comprehensive scanning"""
        import netifaces
        subnets = []
        
        try:
            # Get all network interfaces
            for interface in netifaces.interfaces():
                if interface.startswith('lo'):  # Skip loopback
                    continue
                    
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info.get('addr')
                        netmask = addr_info.get('netmask')
                        
                        if ip and netmask and not ip.startswith('127.'):
                            # Calculate network address
                            network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                            subnets.append(str(network))
            
            if not subnets:
                # Fallback to single subnet detection
                subnets = [self.get_local_subnet()]
                
        except ImportError:
            logger.warning("netifaces not available, using single subnet detection")
            subnets = [self.get_local_subnet()]
        except Exception as e:
            logger.error(f"Failed to get all subnets: {e}")
            subnets = [self.get_local_subnet()]
            
        return subnets

# Async wrapper for integration with FastAPI
async def discover_onvif_cameras(method: str = "both", subnets: List[str] = None, 
                                username: str = None, password: str = None) -> List[dict]:
    """
    Async wrapper for ONVIF discovery with optional authentication
    Returns list of camera configurations ready for Vision Port
    """
    discovery = ONVIFDiscoveryService()
    
    # Store credentials for authenticated discovery
    if username or password:
        discovery.set_credentials(username, password)
    
    # Use all local subnets if none provided (more comprehensive discovery)
    if not subnets:
        subnets = discovery.get_all_local_subnets()
        logger.info(f"Auto-detected subnets for discovery: {subnets}")
    
    # Run discovery in executor to avoid blocking
    loop = asyncio.get_event_loop()
    cameras = await loop.run_in_executor(None, discovery.discover, method, subnets)
    
    # Convert to Vision Port configurations
    configs = [discovery.get_camera_config(camera) for camera in cameras]
    
    return configs