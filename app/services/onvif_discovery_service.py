# app/services/onvif_discovery_service.py
"""
Basic ONVIF discovery service for IP cameras.
Provides network discovery and basic ONVIF device information.
"""
import asyncio
import socket
import struct
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import ipaddress
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth

logger = logging.getLogger(__name__)

@dataclass
class ONVIFDevice:
    """ONVIF device information"""
    ip_address: str
    name: str = "Unknown Device"
    manufacturer: str = "Unknown"
    model: str = "Unknown"
    onvif_port: int = 80
    rtsp_port: int = 554
    capabilities: List[str] = None
    profiles: List[Dict[str, Any]] = None
    discovery_method: str = "ws_discovery"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.capabilities is None:
            self.capabilities = []
        if self.profiles is None:
            self.profiles = []

class ONVIFDiscoveryService:
    """Basic ONVIF discovery service"""
    
    def __init__(self):
        self.discovered_devices = []
        self.ws_discovery_port = 3702
        self.timeout_seconds = 5
        
    async def discover_onvif_devices(self, network_range: str = None) -> List[ONVIFDevice]:
        """
        Discover ONVIF devices on the network using multiple methods
        """
        devices = []
        
        try:
            # Method 1: WS-Discovery (ONVIF standard)
            ws_devices = await self._ws_discovery()
            devices.extend(ws_devices)
            
            # Method 2: Port scanning for common ONVIF ports
            if network_range:
                scan_devices = await self._port_scan_discovery(network_range)
                devices.extend(scan_devices)
            
            # Method 3: SSDP discovery (UPnP)
            ssdp_devices = await self._ssdp_discovery()
            devices.extend(ssdp_devices)
            
            # Remove duplicates based on IP address
            unique_devices = {}
            for device in devices:
                if device.ip_address not in unique_devices:
                    unique_devices[device.ip_address] = device
                else:
                    # Merge information from multiple discovery methods
                    existing = unique_devices[device.ip_address]
                    if device.name != "Unknown Device" and existing.name == "Unknown Device":
                        existing.name = device.name
                    if device.manufacturer != "Unknown" and existing.manufacturer == "Unknown":
                        existing.manufacturer = device.manufacturer
                    if device.model != "Unknown" and existing.model == "Unknown":
                        existing.model = device.model
            
            self.discovered_devices = list(unique_devices.values())
            logger.info(f"Discovered {len(self.discovered_devices)} ONVIF devices")
            
        except Exception as e:
            logger.error(f"ONVIF discovery error: {str(e)}")
        
        return self.discovered_devices
    
    async def _ws_discovery(self) -> List[ONVIFDevice]:
        """WS-Discovery for ONVIF devices"""
        devices = []
        
        try:
            # Create WS-Discovery probe message
            probe_message = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:tns="http://schemas.xmlsoap.org/ws/2005/04/discovery">
    <soap:Header>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
        <wsa:MessageID>urn:uuid:1234567890</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    </soap:Header>
    <soap:Body>
        <tns:Probe>
            <tns:Types>dn:NetworkVideoTransmitter</tns:Types>
        </tns:Probe>
    </soap:Body>
</soap:Envelope>'''.encode('utf-8')
            
            # Send multicast probe
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(self.timeout_seconds)
            
            multicast_addr = ('239.255.255.250', self.ws_discovery_port)
            sock.sendto(probe_message, multicast_addr)
            
            # Listen for responses
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < self.timeout_seconds:
                try:
                    data, addr = sock.recvfrom(8192)
                    device = self._parse_ws_discovery_response(data.decode('utf-8'), addr[0])
                    if device:
                        devices.append(device)
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"WS-Discovery parsing error: {str(e)}")
                    continue
            
            sock.close()
            
        except Exception as e:
            logger.error(f"WS-Discovery error: {str(e)}")
        
        return devices
    
    async def _port_scan_discovery(self, network_range: str) -> List[ONVIFDevice]:
        """Port scanning for ONVIF devices"""
        devices = []
        
        try:
            network = ipaddress.IPv4Network(network_range, strict=False)
            common_onvif_ports = [80, 8080, 8000, 554, 8554]
            
            # Limit to first 254 hosts for performance
            hosts = list(network.hosts())[:254]
            
            for host in hosts:
                ip_str = str(host)
                for port in common_onvif_ports:
                    if await self._check_onvif_port(ip_str, port):
                        device = await self._probe_onvif_device(ip_str, port)
                        if device:
                            devices.append(device)
                        break  # Found ONVIF on this IP, move to next host
                        
        except Exception as e:
            logger.error(f"Port scan discovery error: {str(e)}")
        
        return devices
    
    async def _ssdp_discovery(self) -> List[ONVIFDevice]:
        """SSDP/UPnP discovery for network devices"""
        devices = []
        
        try:
            # SSDP discovery message
            ssdp_request = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nST: upnp:rootdevice\r\nMX: 3\r\n\r\n'
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout_seconds)
            
            sock.sendto(ssdp_request.encode(), ('239.255.255.250', 1900))
            
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < self.timeout_seconds:
                try:
                    data, addr = sock.recvfrom(8192)
                    # Basic check if this might be a camera device
                    response = data.decode('utf-8', errors='ignore').lower()
                    if any(keyword in response for keyword in ['camera', 'video', 'onvif', 'ipcam']):
                        device = ONVIFDevice(
                            ip_address=addr[0],
                            name="SSDP Device",
                            discovery_method="ssdp"
                        )
                        devices.append(device)
                except socket.timeout:
                    break
                except Exception:
                    continue
            
            sock.close()
            
        except Exception as e:
            logger.error(f"SSDP discovery error: {str(e)}")
        
        return devices
    
    async def _check_onvif_port(self, ip_address: str, port: int) -> bool:
        """Check if a port responds to ONVIF requests"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip_address, port))
            sock.close()
            return result == 0
        except:
            return False
    
    async def _probe_onvif_device(self, ip_address: str, port: int) -> Optional[ONVIFDevice]:
        """Probe device for ONVIF capabilities"""
        try:
            # Try to get device information via ONVIF GetDeviceInformation
            device_info_url = f"http://{ip_address}:{port}/onvif/device_service"
            
            device_info_soap = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Header/>
    <soap:Body>
        <tds:GetDeviceInformation/>
    </soap:Body>
</soap:Envelope>'''
            
            response = requests.post(
                device_info_url,
                data=device_info_soap,
                headers={'Content-Type': 'application/soap+xml'},
                timeout=5
            )
            
            if response.status_code == 200:
                # Parse device information
                device = self._parse_device_info(response.text, ip_address, port)
                if device:
                    return device
            
            # Fallback: create basic device entry
            return ONVIFDevice(
                ip_address=ip_address,
                onvif_port=port,
                discovery_method="port_scan"
            )
            
        except Exception as e:
            logger.debug(f"ONVIF probe error for {ip_address}:{port}: {str(e)}")
            return None
    
    def _parse_ws_discovery_response(self, response_xml: str, ip_address: str) -> Optional[ONVIFDevice]:
        """Parse WS-Discovery response"""
        try:
            root = ET.fromstring(response_xml)
            
            # Extract device information from WS-Discovery response
            device = ONVIFDevice(
                ip_address=ip_address,
                discovery_method="ws_discovery"
            )
            
            # Try to extract more information from the response
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'wsa': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
                'tns': 'http://schemas.xmlsoap.org/ws/2005/04/discovery'
            }
            
            # Look for XAddrs (device URLs)
            xaddrs_elem = root.find('.//tns:XAddrs', namespaces)
            if xaddrs_elem is not None and xaddrs_elem.text:
                # Extract port from XAddrs URL
                import re
                port_match = re.search(r':(\d+)/', xaddrs_elem.text)
                if port_match:
                    device.onvif_port = int(port_match.group(1))
            
            return device
            
        except Exception as e:
            logger.debug(f"WS-Discovery parsing error: {str(e)}")
            return None
    
    def _parse_device_info(self, response_xml: str, ip_address: str, port: int) -> Optional[ONVIFDevice]:
        """Parse ONVIF GetDeviceInformation response"""
        try:
            root = ET.fromstring(response_xml)
            
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'tds': 'http://www.onvif.org/ver10/device/wsdl'
            }
            
            device = ONVIFDevice(
                ip_address=ip_address,
                onvif_port=port,
                discovery_method="onvif_probe"
            )
            
            # Extract device information
            info_response = root.find('.//tds:GetDeviceInformationResponse', namespaces)
            if info_response is not None:
                manufacturer_elem = info_response.find('tds:Manufacturer', namespaces)
                if manufacturer_elem is not None:
                    device.manufacturer = manufacturer_elem.text or "Unknown"
                
                model_elem = info_response.find('tds:Model', namespaces)
                if model_elem is not None:
                    device.model = model_elem.text or "Unknown"
                    device.name = f"{device.manufacturer} {device.model}".strip()
            
            return device
            
        except Exception as e:
            logger.debug(f"Device info parsing error: {str(e)}")
            return None
    
    async def get_device_profiles(self, device: ONVIFDevice, username: str = None, password: str = None) -> List[Dict[str, Any]]:
        """Get media profiles from ONVIF device"""
        profiles = []
        
        try:
            profiles_url = f"http://{device.ip_address}:{device.onvif_port}/onvif/media_service"
            
            profiles_soap = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
    <soap:Header/>
    <soap:Body>
        <trt:GetProfiles/>
    </soap:Body>
</soap:Envelope>'''
            
            auth = None
            if username and password:
                auth = HTTPDigestAuth(username, password)
            
            response = requests.post(
                profiles_url,
                data=profiles_soap,
                headers={'Content-Type': 'application/soap+xml'},
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 200:
                profiles = self._parse_media_profiles(response.text)
                device.profiles = profiles
            
        except Exception as e:
            logger.error(f"Error getting device profiles: {str(e)}")
        
        return profiles
    
    def _parse_media_profiles(self, response_xml: str) -> List[Dict[str, Any]]:
        """Parse ONVIF media profiles response"""
        profiles = []
        
        try:
            root = ET.fromstring(response_xml)
            
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'trt': 'http://www.onvif.org/ver10/media/wsdl',
                'tt': 'http://www.onvif.org/ver10/schema'
            }
            
            profile_elements = root.findall('.//trt:Profiles', namespaces)
            
            for profile_elem in profile_elements:
                profile = {
                    'token': profile_elem.get('token', ''),
                    'name': '',
                    'video_encoding': 'Unknown',
                    'resolution': 'Unknown',
                    'framerate': 'Unknown'
                }
                
                name_elem = profile_elem.find('tt:Name', namespaces)
                if name_elem is not None:
                    profile['name'] = name_elem.text or ''
                
                # Extract video configuration
                video_config = profile_elem.find('.//tt:VideoEncoderConfiguration', namespaces)
                if video_config is not None:
                    encoding_elem = video_config.find('tt:Encoding', namespaces)
                    if encoding_elem is not None:
                        profile['video_encoding'] = encoding_elem.text or 'Unknown'
                    
                    resolution_elem = video_config.find('.//tt:Resolution', namespaces)
                    if resolution_elem is not None:
                        width_elem = resolution_elem.find('tt:Width', namespaces)
                        height_elem = resolution_elem.find('tt:Height', namespaces)
                        if width_elem is not None and height_elem is not None:
                            profile['resolution'] = f"{width_elem.text}x{height_elem.text}"
                    
                    framerate_elem = video_config.find('.//tt:FrameRateLimit', namespaces)
                    if framerate_elem is not None:
                        profile['framerate'] = framerate_elem.text or 'Unknown'
                
                profiles.append(profile)
            
        except Exception as e:
            logger.error(f"Error parsing media profiles: {str(e)}")
        
        return profiles
    
    def format_devices_for_ui(self) -> List[Dict[str, Any]]:
        """Format discovered devices for UI display"""
        return [
            {
                'ip_address': device.ip_address,
                'name': device.name,
                'manufacturer': device.manufacturer,
                'model': device.model,
                'onvif_port': device.onvif_port,
                'rtsp_port': device.rtsp_port,
                'capabilities': device.capabilities,
                'profiles': device.profiles,
                'discovery_method': device.discovery_method,
                'timestamp': device.timestamp.isoformat()
            }
            for device in self.discovered_devices
        ]