# app/services/camera_discovery_service.py
# Advanced camera discovery and auto-configuration service
import asyncio
import logging
import time
import json
import socket
import struct
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import ipaddress
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import uuid
import base64
import hashlib

# Import camera configuration system from prototype6
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../ui-prototypes/prototype6'))
from camera_config import CameraConfigurationManager, CameraVendor, CameraConfigurationError

from app.models import Camera, CameraType, CameraStatus, Location
from app.services.camera_registry_service import CameraRegistryService
from app.services.location_service import LocationService
from app.database import async_session
from sqlalchemy import select

logger = logging.getLogger(__name__)

class DiscoveryMethod(Enum):
    ONVIF = "onvif"
    VENDOR_API = "vendor_api"
    RTSP_PROBE = "rtsp_probe"
    HTTP_PROBE = "http_probe"
    UPNP = "upnp"
    MDNS = "mdns"

class CameraCapability(Enum):
    PTZ = "ptz"
    AUDIO = "audio"
    NIGHT_VISION = "night_vision"
    MOTION_DETECTION = "motion_detection"
    AI_DETECTION = "ai_detection"
    TWO_WAY_AUDIO = "two_way_audio"
    RECORDING = "recording"
    STREAMING = "streaming"

@dataclass
class DiscoveredCamera:
    """Represents a discovered camera with all available information"""
    ip_address: str
    port: int = 80
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None
    
    # Network configuration
    rtsp_port: int = 554
    onvif_port: int = 80
    http_port: int = 80
    https_port: int = 443
    
    # Stream URLs
    main_stream_url: Optional[str] = None
    sub_stream_url: Optional[str] = None
    snapshot_url: Optional[str] = None
    
    # Authentication
    default_username: str = "admin"
    default_password: str = ""
    auth_required: bool = True
    auth_method: str = "digest"
    
    # Capabilities
    capabilities: List[CameraCapability] = None
    supported_resolutions: List[str] = None
    supported_codecs: List[str] = None
    
    # Discovery metadata
    discovery_method: DiscoveryMethod = DiscoveryMethod.HTTP_PROBE
    discovery_time: datetime = None
    response_time_ms: float = 0
    confidence_score: float = 0.0  # 0-1 score of detection confidence
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.supported_resolutions is None:
            self.supported_resolutions = ["1920x1080", "1280x720", "640x480"]
        if self.supported_codecs is None:
            self.supported_codecs = ["H.264", "MJPEG"]
        if self.discovery_time is None:
            self.discovery_time = datetime.utcnow()

class CameraDiscoveryService:
    """
    Advanced camera discovery service that can detect and configure IP cameras
    using multiple discovery methods and protocols
    """
    
    def __init__(self, camera_registry: CameraRegistryService, location_service: LocationService):
        self.camera_registry = camera_registry
        self.location_service = location_service
        self.camera_config_manager = CameraConfigurationManager()
        
        # Discovery configuration
        self.discovery_timeout = 30  # seconds
        self.concurrent_scans = 50  # max concurrent IP scans
        self.port_scan_timeout = 3  # seconds per port
        self.camera_test_timeout = 10  # seconds for camera tests
        
        # Common camera ports to scan
        self.common_ports = [80, 443, 554, 8080, 8000, 8899, 37777, 34567]
        
        # Discovery cache
        self.discovery_cache: Dict[str, DiscoveredCamera] = {}
        self.cache_expiry = timedelta(hours=1)
        
        # Statistics
        self.discovery_stats = {
            "total_scans": 0,
            "successful_discoveries": 0,
            "failed_discoveries": 0,
            "cache_hits": 0,
            "avg_discovery_time": 0.0
        }
    
    async def discover_cameras_on_network(self, 
                                        ip_range: str = "192.168.1.0/24",
                                        methods: List[DiscoveryMethod] = None,
                                        include_cached: bool = True,
                                        port_config: Dict[str, List[int]] = None) -> List[DiscoveredCamera]:
        """
        Discover cameras on network using multiple methods
        
        Args:
            ip_range: Network range to scan (CIDR notation)
            methods: Discovery methods to use (default: all methods)
            include_cached: Include cached discoveries
            port_config: Custom port configuration for each method
            
        Returns:
            List of discovered cameras
        """
        if methods is None:
            methods = [DiscoveryMethod.HTTP_PROBE, DiscoveryMethod.ONVIF, DiscoveryMethod.VENDOR_API, 
                      DiscoveryMethod.RTSP_PROBE, DiscoveryMethod.UPNP]
        
        # Set up port configuration
        if port_config is None:
            port_config = {
                'onvif': [80, 8080, 8899],
                'http': [80, 443, 8080, 8443],
                'rtsp': [554, 8554],
                'upnp': [1900]
            }
        
        logger.info(f"Starting camera discovery on {ip_range} using methods: {[m.value for m in methods]}")
        logger.info(f"Port configuration: {port_config}")
        start_time = time.time()
        
        try:
            # Parse IP range
            network = ipaddress.IPv4Network(ip_range, strict=False)
            ip_addresses = list(network.hosts())
            
            # Limit IP range for performance
            if len(ip_addresses) > 1000:
                logger.warning(f"Large IP range ({len(ip_addresses)} addresses), limiting to first 1000")
                ip_addresses = ip_addresses[:1000]
            
            # Check cache first
            discovered_cameras = []
            if include_cached:
                discovered_cameras.extend(self._get_cached_discoveries(ip_addresses))
            
            # Get IPs not in cache
            cached_ips = {cam.ip_address for cam in discovered_cameras}
            ips_to_scan = [str(ip) for ip in ip_addresses if str(ip) not in cached_ips]
            
            logger.info(f"Scanning {len(ips_to_scan)} IPs (cached: {len(cached_ips)})")
            
            # Concurrent discovery
            semaphore = asyncio.Semaphore(self.concurrent_scans)
            discovery_tasks = []
            
            for ip_str in ips_to_scan:
                task = asyncio.create_task(self._discover_camera_at_ip(ip_str, methods, semaphore, port_config))
                discovery_tasks.append(task)
            
            # Wait for all discoveries with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*discovery_tasks, return_exceptions=True),
                    timeout=self.discovery_timeout
                )
                
                # Process results
                for result in results:
                    if isinstance(result, DiscoveredCamera):
                        discovered_cameras.append(result)
                        self._cache_discovery(result)
                    elif isinstance(result, Exception):
                        logger.debug(f"Discovery error: {result}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Discovery timed out after {self.discovery_timeout} seconds")
                # Cancel remaining tasks
                for task in discovery_tasks:
                    if not task.done():
                        task.cancel()
            
            # Sort by IP address
            discovered_cameras.sort(key=lambda x: ipaddress.IPv4Address(x.ip_address))
            
            discovery_time = time.time() - start_time
            self.discovery_stats["total_scans"] += 1
            self.discovery_stats["successful_discoveries"] += len(discovered_cameras)
            self.discovery_stats["avg_discovery_time"] = discovery_time
            
            logger.info(f"Discovery complete: {len(discovered_cameras)} cameras found in {discovery_time:.2f}s")
            return discovered_cameras
            
        except Exception as e:
            logger.error(f"Camera discovery failed: {e}")
            self.discovery_stats["failed_discoveries"] += 1
            return []
    
    async def _discover_camera_at_ip(self, 
                                   ip_address: str,
                                   methods: List[DiscoveryMethod],
                                   semaphore: asyncio.Semaphore,
                                   port_config: Dict[str, List[int]]) -> Optional[DiscoveredCamera]:
        """Discover camera at specific IP using multiple methods"""
        async with semaphore:
            start_time = time.time()
            
            try:
                # Try each discovery method
                for method in methods:
                    try:
                        if method == DiscoveryMethod.HTTP_PROBE:
                            camera = await self._http_probe_discovery(ip_address, port_config.get('http', [80, 443, 8080, 8443]))
                        elif method == DiscoveryMethod.ONVIF:
                            camera = await self._discover_onvif_camera_enhanced(ip_address, port_config.get('onvif', [80, 8080, 8899]))
                        elif method == DiscoveryMethod.VENDOR_API:
                            camera = await self._vendor_api_discovery(ip_address, port_config.get('http', [80, 443, 8080, 8443]))
                        elif method == DiscoveryMethod.RTSP_PROBE:
                            camera = await self._rtsp_probe_discovery(ip_address, port_config.get('rtsp', [554, 8554]))
                        elif method == DiscoveryMethod.UPNP:
                            upnp_cameras = await self._upnp_discovery(ip_address)
                            camera = upnp_cameras[0] if upnp_cameras else None
                        elif method == DiscoveryMethod.MDNS:
                            mdns_cameras = await self._mdns_discovery(ip_address)
                            camera = mdns_cameras[0] if mdns_cameras else None
                        else:
                            continue
                        
                        if camera:
                            camera.discovery_method = method
                            camera.response_time_ms = (time.time() - start_time) * 1000
                            
                            # Try to get additional info and test streams
                            await self._enrich_camera_info(camera)
                            
                            logger.debug(f"Camera discovered at {ip_address} via {method.value}")
                            return camera
                            
                    except Exception as e:
                        logger.debug(f"Discovery method {method.value} failed for {ip_address}: {e}")
                        continue
                
                return None
                
            except Exception as e:
                logger.debug(f"Discovery failed for {ip_address}: {e}")
                return None
    
    async def _http_probe_discovery(self, ip_address: str, ports: List[int] = None) -> Optional[DiscoveredCamera]:
        """Discover camera using HTTP probing"""
        if ports is None:
            ports = [80, 8080, 8000]
        
        try:
            # Try configured HTTP ports
            for port in ports:
                try:
                    url = f"http://{ip_address}:{port}"
                    
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.port_scan_timeout)) as session:
                        async with session.get(url) as response:
                            if response.status == 401:  # Authentication required - likely a camera
                                # Check WWW-Authenticate header for clues
                                auth_header = response.headers.get('WWW-Authenticate', '')
                                
                                camera = DiscoveredCamera(
                                    ip_address=ip_address,
                                    port=port,
                                    http_port=port,
                                    auth_required=True,
                                    auth_method="digest" if "digest" in auth_header.lower() else "basic"
                                )
                                
                                # Try to identify vendor from headers or response
                                server_header = response.headers.get('Server', '').lower()
                                if 'reolink' in server_header:
                                    camera.vendor = 'reolink'
                                elif 'hikvision' in server_header:
                                    camera.vendor = 'hikvision'
                                elif 'dahua' in server_header:
                                    camera.vendor = 'dahua'
                                
                                camera.confidence_score = 0.7  # Medium confidence
                                return camera
                                
                            elif response.status == 200:
                                # Check response content for camera indicators
                                content = await response.text()
                                content_lower = content.lower()
                                
                                camera_indicators = [
                                    'ip camera', 'network camera', 'web camera',
                                    'surveillance', 'security camera', 'ipcam',
                                    'reolink', 'hikvision', 'dahua', 'axis',
                                    'live view', 'video stream', 'rtsp'
                                ]
                                
                                if any(indicator in content_lower for indicator in camera_indicators):
                                    camera = DiscoveredCamera(
                                        ip_address=ip_address,
                                        port=port,
                                        http_port=port,
                                        auth_required=False
                                    )
                                    
                                    # Try to extract vendor info
                                    for vendor in ['reolink', 'hikvision', 'dahua', 'axis']:
                                        if vendor in content_lower:
                                            camera.vendor = vendor
                                            break
                                    
                                    camera.confidence_score = 0.8  # High confidence
                                    return camera
                
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"HTTP probe failed for {ip_address}: {e}")
            return None
    
    async def _onvif_discovery(self, ip_address: str) -> Optional[DiscoveredCamera]:
        """Discover camera using ONVIF protocol"""
        try:
            # Try common ONVIF ports
            for port in [80, 8080, 8000]:
                try:
                    url = f"http://{ip_address}:{port}/onvif/device_service"
                    
                    # ONVIF GetDeviceInformation request
                    soap_body = """<?xml version="1.0" encoding="UTF-8"?>
                    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                                   xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
                        <soap:Body>
                            <tds:GetDeviceInformation/>
                        </soap:Body>
                    </soap:Envelope>"""
                    
                    headers = {
                        'Content-Type': 'application/soap+xml; charset=utf-8',
                        'SOAPAction': '"http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation"'
                    }
                    
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.port_scan_timeout)) as session:
                        async with session.post(url, data=soap_body, headers=headers) as response:
                            if response.status == 200:
                                xml_content = await response.text()
                                
                                # Parse ONVIF response
                                camera_info = self._parse_onvif_response(xml_content)
                                
                                if camera_info:
                                    camera = DiscoveredCamera(
                                        ip_address=ip_address,
                                        port=port,
                                        onvif_port=port,
                                        vendor=camera_info.get('manufacturer', 'unknown'),
                                        model=camera_info.get('model', 'unknown'),
                                        serial_number=camera_info.get('serialNumber'),
                                        firmware_version=camera_info.get('firmwareVersion'),
                                        auth_required=True,
                                        auth_method="digest"
                                    )
                                    
                                    camera.capabilities.append(CameraCapability.STREAMING)
                                    camera.confidence_score = 0.9  # High confidence for ONVIF
                                    return camera
                
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"ONVIF discovery failed for {ip_address}: {e}")
            return None
    
    async def _vendor_api_discovery(self, ip_address: str, ports: List[int] = None) -> Optional[DiscoveredCamera]:
        """Discover camera using vendor-specific APIs"""
        try:
            # Try Reolink API
            reolink_camera = await self._discover_reolink_camera(ip_address)
            if reolink_camera:
                return reolink_camera
            
            # Try enhanced Hikvision API
            hikvision_camera = await self._discover_enhanced_hikvision_camera(ip_address)
            if hikvision_camera:
                return hikvision_camera
            
            # Try enhanced Dahua API
            dahua_camera = await self._discover_dahua_camera(ip_address)
            if dahua_camera:
                return dahua_camera
            
            # Try Axis API
            axis_camera = await self._discover_axis_camera(ip_address)
            if axis_camera:
                return axis_camera
            
            return None
            
        except Exception as e:
            logger.debug(f"Vendor API discovery failed for {ip_address}: {e}")
            return None
    
    async def _discover_reolink_camera(self, ip_address: str) -> Optional[DiscoveredCamera]:
        """Discover Reolink camera using their API"""
        try:
            url = f"http://{ip_address}/cgi-bin/api.cgi"
            payload = [{
                "cmd": "GetDevInfo",
                "action": 0,
                "param": {}
            }]
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.port_scan_timeout)) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0 and data[0].get("code") == 0:
                            device_info = data[0]["value"]["DevInfo"]
                            
                            camera = DiscoveredCamera(
                                ip_address=ip_address,
                                vendor="reolink",
                                model=device_info.get("model", "Unknown"),
                                serial_number=device_info.get("serial", "Unknown"),
                                firmware_version=device_info.get("firmVer", "Unknown"),
                                default_username="admin",
                                default_password="",
                                auth_required=True,
                                auth_method="digest"
                            )
                            
                            # Parse capabilities
                            if device_info.get("audioNum", 0) > 0:
                                camera.capabilities.append(CameraCapability.AUDIO)
                            if device_info.get("ai", False):
                                camera.capabilities.append(CameraCapability.AI_DETECTION)
                            
                            camera.confidence_score = 0.95  # Very high confidence
                            return camera
            
            return None
            
        except Exception as e:
            logger.debug(f"Reolink discovery failed for {ip_address}: {e}")
            return None
    
    async def _discover_hikvision_camera(self, ip_address: str) -> Optional[DiscoveredCamera]:
        """Discover Hikvision camera using ISAPI"""
        try:
            url = f"http://{ip_address}/ISAPI/System/deviceInfo"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.port_scan_timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 401:  # Authentication required
                        camera = DiscoveredCamera(
                            ip_address=ip_address,
                            vendor="hikvision",
                            default_username="admin",
                            default_password="12345",
                            auth_required=True,
                            auth_method="digest"
                        )
                        camera.confidence_score = 0.8
                        return camera
            
            return None
            
        except Exception as e:
            logger.debug(f"Hikvision discovery failed for {ip_address}: {e}")
            return None
    
    async def _discover_dahua_camera(self, ip_address: str) -> Optional[DiscoveredCamera]:
        """Discover Dahua camera using their API"""
        try:
            # Try multiple Dahua API endpoints
            dahua_endpoints = [
                f"http://{ip_address}/cgi-bin/magicBox.cgi?action=getDeviceType",
                f"http://{ip_address}/cgi-bin/magicBox.cgi?action=getMachineName",
                f"http://{ip_address}/cgi-bin/deviceInfo.cgi?action=getDeviceInfo"
            ]
            
            for endpoint in dahua_endpoints:
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.port_scan_timeout)) as session:
                        async with session.get(endpoint) as response:
                            if response.status == 401:  # Authentication required
                                camera = DiscoveredCamera(
                                    ip_address=ip_address,
                                    vendor="dahua",
                                    default_username="admin",
                                    default_password="admin",
                                    auth_required=True,
                                    auth_method="digest",
                                    confidence_score=0.85
                                )
                                
                                # Set Dahua-specific stream URLs
                                camera.main_stream_url = f"rtsp://admin:admin@{ip_address}:554/cam/realmonitor?channel=1&subtype=0"
                                camera.sub_stream_url = f"rtsp://admin:admin@{ip_address}:554/cam/realmonitor?channel=1&subtype=1"
                                camera.snapshot_url = f"http://{ip_address}/cgi-bin/snapshot.cgi?channel=1"
                                
                                camera.capabilities.extend([
                                    CameraCapability.STREAMING,
                                    CameraCapability.RECORDING,
                                    CameraCapability.MOTION_DETECTION
                                ])
                                
                                return camera
                                
                            elif response.status == 200:
                                # Try to parse device information
                                content = await response.text()
                                
                                camera = DiscoveredCamera(
                                    ip_address=ip_address,
                                    vendor="dahua",
                                    default_username="admin",
                                    default_password="admin",
                                    auth_required=False,
                                    confidence_score=0.9
                                )
                                
                                # Parse device info from response
                                if 'DeviceType=' in content:
                                    device_type = content.split('DeviceType=')[1].split('\r\n')[0]
                                    camera.model = device_type
                                
                                if 'MachineName=' in content:
                                    machine_name = content.split('MachineName=')[1].split('\r\n')[0]
                                    camera.model = machine_name or camera.model
                                
                                camera.main_stream_url = f"rtsp://admin:admin@{ip_address}:554/cam/realmonitor?channel=1&subtype=0"
                                camera.sub_stream_url = f"rtsp://admin:admin@{ip_address}:554/cam/realmonitor?channel=1&subtype=1"
                                camera.snapshot_url = f"http://{ip_address}/cgi-bin/snapshot.cgi?channel=1"
                                
                                camera.capabilities.extend([
                                    CameraCapability.STREAMING,
                                    CameraCapability.RECORDING,
                                    CameraCapability.MOTION_DETECTION,
                                    CameraCapability.AI_DETECTION
                                ])
                                
                                return camera
                
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Dahua discovery failed for {ip_address}: {e}")
            return None

    async def _discover_axis_camera(self, ip_address: str) -> Optional[DiscoveredCamera]:
        """Discover Axis camera using their API"""
        try:
            # Try Axis API endpoints
            axis_endpoints = [
                f"http://{ip_address}/axis-cgi/param.cgi?action=list&group=Properties.System",
                f"http://{ip_address}/axis-cgi/basicdeviceinfo.cgi",
                f"http://{ip_address}/axis-cgi/jpg/image.cgi"
            ]
            
            for endpoint in axis_endpoints:
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.port_scan_timeout)) as session:
                        async with session.get(endpoint) as response:
                            if response.status == 401:  # Authentication required
                                camera = DiscoveredCamera(
                                    ip_address=ip_address,
                                    vendor="axis",
                                    default_username="root",
                                    default_password="pass",
                                    auth_required=True,
                                    auth_method="digest",
                                    confidence_score=0.85
                                )
                                
                                # Set Axis-specific stream URLs
                                camera.main_stream_url = f"rtsp://root:pass@{ip_address}:554/axis-media/media.amp?videocodec=h264"
                                camera.sub_stream_url = f"rtsp://root:pass@{ip_address}:554/axis-media/media.amp?videocodec=h264&resolution=320x240"
                                camera.snapshot_url = f"http://{ip_address}/axis-cgi/jpg/image.cgi"
                                
                                camera.capabilities.extend([
                                    CameraCapability.STREAMING,
                                    CameraCapability.RECORDING,
                                    CameraCapability.PTZ,
                                    CameraCapability.AUDIO,
                                    CameraCapability.MOTION_DETECTION
                                ])
                                
                                return camera
                                
                            elif response.status == 200:
                                content = await response.text()
                                
                                # Check for Axis-specific content
                                if 'axis' in content.lower() or 'Properties.System' in content:
                                    camera = DiscoveredCamera(
                                        ip_address=ip_address,
                                        vendor="axis",
                                        default_username="root",
                                        default_password="pass",
                                        auth_required=False,
                                        confidence_score=0.9
                                    )
                                    
                                    # Parse device info
                                    if 'ProdNbr=' in content:
                                        model = content.split('ProdNbr=')[1].split('\n')[0].strip()
                                        camera.model = model
                                    
                                    if 'Version=' in content:
                                        firmware = content.split('Version=')[1].split('\n')[0].strip()
                                        camera.firmware_version = firmware
                                    
                                    camera.main_stream_url = f"rtsp://root:pass@{ip_address}:554/axis-media/media.amp"
                                    camera.sub_stream_url = f"rtsp://root:pass@{ip_address}:554/axis-media/media.amp?resolution=320x240"
                                    camera.snapshot_url = f"http://{ip_address}/axis-cgi/jpg/image.cgi"
                                    
                                    camera.capabilities.extend([
                                        CameraCapability.STREAMING,
                                        CameraCapability.RECORDING,
                                        CameraCapability.PTZ,
                                        CameraCapability.AUDIO,
                                        CameraCapability.MOTION_DETECTION
                                    ])
                                    
                                    return camera
                
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Axis discovery failed for {ip_address}: {e}")
            return None

    async def _discover_enhanced_hikvision_camera(self, ip_address: str) -> Optional[DiscoveredCamera]:
        """Enhanced Hikvision camera discovery using ISAPI"""
        try:
            # Try multiple Hikvision ISAPI endpoints
            hikvision_endpoints = [
                f"http://{ip_address}/ISAPI/System/deviceInfo",
                f"http://{ip_address}/ISAPI/System/status",
                f"http://{ip_address}/ISAPI/Streaming/channels",
                f"http://{ip_address}/SDK/webLanguage"
            ]
            
            for endpoint in hikvision_endpoints:
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.port_scan_timeout)) as session:
                        async with session.get(endpoint) as response:
                            if response.status == 401:  # Authentication required
                                camera = DiscoveredCamera(
                                    ip_address=ip_address,
                                    vendor="hikvision",
                                    default_username="admin",
                                    default_password="12345",
                                    auth_required=True,
                                    auth_method="digest",
                                    confidence_score=0.85
                                )
                                
                                # Set Hikvision-specific stream URLs
                                camera.main_stream_url = f"rtsp://admin:12345@{ip_address}:554/Streaming/Channels/101"
                                camera.sub_stream_url = f"rtsp://admin:12345@{ip_address}:554/Streaming/Channels/102"
                                camera.snapshot_url = f"http://{ip_address}/ISAPI/Streaming/channels/101/picture"
                                
                                camera.capabilities.extend([
                                    CameraCapability.STREAMING,
                                    CameraCapability.RECORDING,
                                    CameraCapability.PTZ,
                                    CameraCapability.AUDIO,
                                    CameraCapability.MOTION_DETECTION,
                                    CameraCapability.AI_DETECTION
                                ])
                                
                                return camera
                                
                            elif response.status == 200:
                                content = await response.text()
                                
                                # Check for Hikvision-specific content
                                if 'hikvision' in content.lower() or 'DeviceInfo' in content or 'isapi' in content.lower():
                                    camera = DiscoveredCamera(
                                        ip_address=ip_address,
                                        vendor="hikvision",
                                        default_username="admin",
                                        default_password="12345",
                                        auth_required=False,
                                        confidence_score=0.9
                                    )
                                    
                                    # Parse XML device info
                                    try:
                                        root = ET.fromstring(content)
                                        
                                        model_elem = root.find('.//model')
                                        if model_elem is not None:
                                            camera.model = model_elem.text
                                        
                                        firmware_elem = root.find('.//firmwareVersion')
                                        if firmware_elem is not None:
                                            camera.firmware_version = firmware_elem.text
                                        
                                        serial_elem = root.find('.//serialNumber')
                                        if serial_elem is not None:
                                            camera.serial_number = serial_elem.text
                                            
                                    except ET.ParseError:
                                        pass
                                    
                                    camera.main_stream_url = f"rtsp://admin:12345@{ip_address}:554/Streaming/Channels/101"
                                    camera.sub_stream_url = f"rtsp://admin:12345@{ip_address}:554/Streaming/Channels/102"
                                    camera.snapshot_url = f"http://{ip_address}/ISAPI/Streaming/channels/101/picture"
                                    
                                    camera.capabilities.extend([
                                        CameraCapability.STREAMING,
                                        CameraCapability.RECORDING,
                                        CameraCapability.PTZ,
                                        CameraCapability.AUDIO,
                                        CameraCapability.MOTION_DETECTION,
                                        CameraCapability.AI_DETECTION
                                    ])
                                    
                                    return camera
                
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Enhanced Hikvision discovery failed for {ip_address}: {e}")
            return None
            
        except Exception as e:
            logger.debug(f"Dahua discovery failed for {ip_address}: {e}")
            return None
    
    async def _rtsp_probe_discovery(self, ip_address: str, ports: List[int] = None) -> Optional[DiscoveredCamera]:
        """Discover camera by probing RTSP port"""
        if ports is None:
            ports = [554, 8554]
        
        try:
            # Check if any RTSP port is open
            for port in ports:
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(ip_address, port),
                        timeout=self.port_scan_timeout
                    )
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    # RTSP port is open, likely a camera
                    camera = DiscoveredCamera(
                        ip_address=ip_address,
                        rtsp_port=port,
                        auth_required=True,
                        auth_method="digest"
                    )
                    camera.confidence_score = 0.6  # Medium confidence
                    return camera
                    
                except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                    continue  # Try next port
                    
            return None  # No ports responded
            
        except Exception as e:
            logger.debug(f"RTSP discovery failed for {ip_address}: {e}")
            return None
    
    async def _enrich_camera_info(self, camera: DiscoveredCamera) -> None:
        """Enrich camera information with additional details"""
        try:
            # Try to get stream URLs using camera configuration manager
            if camera.vendor:
                try:
                    # Use existing camera config manager
                    config_result = await self.camera_config_manager.setup_camera(
                        camera.ip_address,
                        camera.default_username,
                        camera.default_password
                    )
                    
                    if config_result and "streams" in config_result:
                        streams = config_result["streams"]
                        camera.main_stream_url = streams.main_stream_url
                        camera.sub_stream_url = streams.sub_stream_url
                        
                        # Update camera info from config
                        if "camera_info" in config_result:
                            info = config_result["camera_info"]
                            if not camera.model:
                                camera.model = info.get("model", "Unknown")
                            if not camera.serial_number:
                                camera.serial_number = info.get("serial", "Unknown")
                            if not camera.firmware_version:
                                camera.firmware_version = info.get("firmware", "Unknown")
                
                except Exception as e:
                    logger.debug(f"Camera config enrichment failed for {camera.ip_address}: {e}")
            
            # If no stream URLs, generate generic ones
            if not camera.main_stream_url:
                camera.main_stream_url = f"rtsp://{camera.default_username}:{camera.default_password}@{camera.ip_address}:{camera.rtsp_port}/stream1"
            if not camera.sub_stream_url:
                camera.sub_stream_url = f"rtsp://{camera.default_username}:{camera.default_password}@{camera.ip_address}:{camera.rtsp_port}/stream2"
            
            # Generate snapshot URL
            if not camera.snapshot_url:
                camera.snapshot_url = f"http://{camera.ip_address}:{camera.http_port}/snapshot.jpg"
            
        except Exception as e:
            logger.debug(f"Camera info enrichment failed for {camera.ip_address}: {e}")
    
    async def auto_configure_camera(self, discovered_camera: DiscoveredCamera, 
                                  location_id: str,
                                  camera_name: Optional[str] = None) -> str:
        """
        Automatically configure and register a discovered camera
        
        Args:
            discovered_camera: Camera discovered by discovery service
            location_id: Location ID to assign camera to
            camera_name: Optional custom name for camera
            
        Returns:
            Camera ID of registered camera
        """
        try:
            # Generate camera name if not provided
            if not camera_name:
                camera_name = f"{discovered_camera.vendor or 'Camera'} {discovered_camera.ip_address}"
            
            # Prepare camera configuration
            camera_config = {
                "name": camera_name,
                "ip_address": discovered_camera.ip_address,
                "location_id": location_id,
                "camera_type": "ip_camera",
                "manufacturer": discovered_camera.vendor,
                "model": discovered_camera.model,
                "serial_number": discovered_camera.serial_number,
                "username": discovered_camera.default_username,
                "password": discovered_camera.default_password,
                "port": discovered_camera.rtsp_port,
                "main_stream_url": discovered_camera.main_stream_url,
                "sub_stream_url": discovered_camera.sub_stream_url,
                "snapshot_url": discovered_camera.snapshot_url,
                "resolution_width": 1920,
                "resolution_height": 1080,
                "fps": 30,
                "codec": "H.264",
                "installation_location": f"Auto-discovered at {discovered_camera.ip_address}",
                "auto_discovery": True
            }
            
            # Register camera
            camera_id = await self.camera_registry.register_camera(camera_config)
            
            logger.info(f"Auto-configured camera: {camera_name} ({camera_id}) at {discovered_camera.ip_address}")
            return camera_id
            
        except Exception as e:
            logger.error(f"Auto-configuration failed for camera {discovered_camera.ip_address}: {e}")
            raise
    
    async def bulk_auto_configure(self, discovered_cameras: List[DiscoveredCamera],
                                location_id: str) -> List[Dict[str, Any]]:
        """
        Bulk auto-configure multiple discovered cameras
        
        Args:
            discovered_cameras: List of discovered cameras
            location_id: Location ID to assign cameras to
            
        Returns:
            List of configuration results
        """
        results = []
        
        for camera in discovered_cameras:
            try:
                camera_id = await self.auto_configure_camera(camera, location_id)
                results.append({
                    "ip_address": camera.ip_address,
                    "camera_id": camera_id,
                    "status": "success",
                    "name": f"{camera.vendor or 'Camera'} {camera.ip_address}"
                })
            except Exception as e:
                results.append({
                    "ip_address": camera.ip_address,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def _parse_onvif_response(self, xml_content: str) -> Optional[Dict[str, Any]]:
        """Parse ONVIF GetDeviceInformation response"""
        try:
            # Remove namespace prefixes for easier parsing
            xml_content = xml_content.replace('tds:', '').replace('tt:', '')
            
            root = ET.fromstring(xml_content)
            
            # Find GetDeviceInformationResponse
            response_elem = root.find('.//GetDeviceInformationResponse')
            if response_elem is None:
                return None
            
            device_info = {}
            
            # Extract device information
            for child in response_elem:
                if child.tag in ['Manufacturer', 'Model', 'FirmwareVersion', 'SerialNumber', 'HardwareId']:
                    device_info[child.tag.lower()] = child.text
            
            return device_info if device_info else None
            
        except Exception as e:
            logger.debug(f"Failed to parse ONVIF response: {e}")
            return None
    
    def _get_cached_discoveries(self, ip_addresses: List[ipaddress.IPv4Address]) -> List[DiscoveredCamera]:
        """Get cached discoveries that are still valid"""
        cached_cameras = []
        current_time = datetime.utcnow()
        
        for ip in ip_addresses:
            ip_str = str(ip)
            if ip_str in self.discovery_cache:
                cached_camera = self.discovery_cache[ip_str]
                if current_time - cached_camera.discovery_time < self.cache_expiry:
                    cached_cameras.append(cached_camera)
                    self.discovery_stats["cache_hits"] += 1
                else:
                    # Remove expired cache entry
                    del self.discovery_cache[ip_str]
        
        return cached_cameras
    
    def _cache_discovery(self, camera: DiscoveredCamera) -> None:
        """Cache discovered camera"""
        self.discovery_cache[camera.ip_address] = camera
        
        # Limit cache size
        if len(self.discovery_cache) > 1000:
            # Remove oldest entries
            sorted_cache = sorted(
                self.discovery_cache.items(),
                key=lambda x: x[1].discovery_time
            )
            
            # Keep only newest 500 entries
            self.discovery_cache = dict(sorted_cache[-500:])
    
    async def get_discovery_statistics(self) -> Dict[str, Any]:
        """Get discovery service statistics"""
        return {
            **self.discovery_stats,
            "cache_size": len(self.discovery_cache),
            "cache_expiry_hours": self.cache_expiry.total_seconds() / 3600,
            "supported_vendors": [vendor.value for vendor in CameraVendor],
            "discovery_methods": [method.value for method in DiscoveryMethod]
        }
    
    async def test_camera_connection(self, camera: DiscoveredCamera) -> Dict[str, Any]:
        """Test connection to discovered camera"""
        test_results = {
            "ip_address": camera.ip_address,
            "tests": {},
            "overall_status": "unknown"
        }
        
        try:
            # Test HTTP connection
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(f"http://{camera.ip_address}:{camera.http_port}") as response:
                        test_results["tests"]["http"] = {
                            "status": "success",
                            "response_code": response.status,
                            "response_time_ms": 0  # Would need to measure
                        }
            except Exception as e:
                test_results["tests"]["http"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Test RTSP connection
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(camera.ip_address, camera.rtsp_port),
                    timeout=5
                )
                writer.close()
                await writer.wait_closed()
                
                test_results["tests"]["rtsp"] = {
                    "status": "success",
                    "port": camera.rtsp_port
                }
            except Exception as e:
                test_results["tests"]["rtsp"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Determine overall status
            successful_tests = sum(1 for test in test_results["tests"].values() if test["status"] == "success")
            total_tests = len(test_results["tests"])
            
            if successful_tests == total_tests:
                test_results["overall_status"] = "healthy"
            elif successful_tests > 0:
                test_results["overall_status"] = "partial"
            else:
                test_results["overall_status"] = "failed"
            
            return test_results
            
        except Exception as e:
            test_results["overall_status"] = "error"
            test_results["error"] = str(e)
            return test_results

    # Enhanced ONVIF Profile S/T Discovery Methods
    async def _discover_onvif_camera_enhanced(self, ip_address: str, ports: List[int] = None) -> Optional[DiscoveredCamera]:
        """Enhanced ONVIF discovery with Profile S/T support"""
        try:
            # Try ONVIF WS-Discovery first
            onvif_devices = await self._onvif_ws_discovery(ip_address)
            if onvif_devices:
                return onvif_devices[0]
            
            # Try direct ONVIF probe
            onvif_camera = await self._probe_onvif_device(ip_address)
            if onvif_camera:
                return onvif_camera
            
            return None
            
        except Exception as e:
            logger.debug(f"Enhanced ONVIF discovery failed for {ip_address}: {e}")
            return None

    async def _onvif_ws_discovery(self, target_ip: str = None) -> List[DiscoveredCamera]:
        """ONVIF WS-Discovery implementation"""
        discovered_cameras = []
        
        try:
            # Create WS-Discovery probe message
            probe_uuid = str(uuid.uuid4())
            probe_message = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery">
    <soap:Header>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
        <wsa:MessageID>urn:uuid:{probe_uuid}</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    </soap:Header>
    <soap:Body>
        <wsd:Probe>
            <wsd:Types xmlns:tds="http://www.onvif.org/ver10/device/wsdl">tds:Device</wsd:Types>
        </wsd:Probe>
    </soap:Body>
</soap:Envelope>'''

            # Set up UDP multicast
            multicast_address = "239.255.255.250"
            multicast_port = 3702
            
            # Create UDP socket
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)
            
            if target_ip:
                # Direct probe to specific IP
                sock.sendto(probe_message.encode('utf-8'), (target_ip, multicast_port))
            else:
                # Multicast probe
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                sock.sendto(probe_message.encode('utf-8'), (multicast_address, multicast_port))
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < 5.0:
                try:
                    data, addr = sock.recvfrom(4096)
                    response = data.decode('utf-8')
                    
                    # Parse ONVIF response
                    camera = await self._parse_onvif_probe_response(response, addr[0])
                    if camera:
                        discovered_cameras.append(camera)
                        
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Error processing ONVIF response: {e}")
                    
            sock.close()
            
        except Exception as e:
            logger.error(f"ONVIF WS-Discovery error: {e}")
            
        return discovered_cameras

    async def _parse_onvif_probe_response(self, response: str, ip_address: str) -> Optional[DiscoveredCamera]:
        """Parse ONVIF WS-Discovery response"""
        try:
            root = ET.fromstring(response)
            
            # Extract device information
            camera = DiscoveredCamera(
                ip_address=ip_address,
                vendor="onvif",
                discovery_method=DiscoveryMethod.ONVIF,
                confidence_score=0.9
            )
            
            # Parse namespace-aware elements
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'wsa': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
                'wsd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery',
                'tds': 'http://www.onvif.org/ver10/device/wsdl'
            }
            
            # Extract XAddrs (service endpoints)
            xaddrs_elem = root.find('.//wsd:XAddrs', namespaces)
            if xaddrs_elem is not None:
                xaddrs = xaddrs_elem.text.strip().split()
                for xaddr in xaddrs:
                    if ip_address in xaddr:
                        # Extract port from service URL
                        import re
                        port_match = re.search(r':(\d+)/', xaddr)
                        if port_match:
                            camera.onvif_port = int(port_match.group(1))
                        break
            
            # Extract device types and scopes
            types_elem = root.find('.//wsd:Types', namespaces)
            if types_elem is not None:
                types_text = types_elem.text
                if 'NetworkVideoTransmitter' in types_text:
                    camera.capabilities.append(CameraCapability.STREAMING)
                if 'Device' in types_text:
                    camera.capabilities.append(CameraCapability.RECORDING)
            
            scopes_elem = root.find('.//wsd:Scopes', namespaces)
            if scopes_elem is not None:
                scopes_text = scopes_elem.text
                
                # Extract manufacturer and model from scopes
                scope_parts = scopes_text.split()
                for scope in scope_parts:
                    if 'hardware/' in scope:
                        camera.model = scope.split('hardware/')[-1]
                    elif 'name/' in scope:
                        device_name = scope.split('name/')[-1]
                        # Try to extract vendor from device name
                        for vendor in ['hikvision', 'dahua', 'axis', 'reolink']:
                            if vendor.lower() in device_name.lower():
                                camera.vendor = vendor
                                break
            
            # Set ONVIF-specific defaults
            camera.default_username = "admin"
            camera.default_password = ""
            camera.auth_required = True
            camera.auth_method = "digest"
            
            return camera
            
        except Exception as e:
            logger.debug(f"Error parsing ONVIF response: {e}")
            return None

    async def _probe_onvif_device(self, ip_address: str, port: int = 80) -> Optional[DiscoveredCamera]:
        """Direct ONVIF device probe"""
        try:
            # Try common ONVIF service endpoints
            endpoints = [
                f"http://{ip_address}:{port}/onvif/device_service",
                f"http://{ip_address}:{port}/onvif/Device",
                f"http://{ip_address}:{port}/device_service",
                f"http://{ip_address}:{port}/Device"
            ]
            
            for endpoint in endpoints:
                try:
                    camera = await self._test_onvif_endpoint(ip_address, endpoint, port)
                    if camera:
                        return camera
                except Exception as e:
                    logger.debug(f"ONVIF endpoint {endpoint} failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"ONVIF device probe failed for {ip_address}: {e}")
            return None

    async def _test_onvif_endpoint(self, ip_address: str, endpoint: str, port: int) -> Optional[DiscoveredCamera]:
        """Test specific ONVIF endpoint"""
        try:
            # Create GetDeviceInformation SOAP request
            soap_request = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
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
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.port_scan_timeout)) as session:
                async with session.post(endpoint, data=soap_request, headers=headers) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        return await self._parse_onvif_device_info(response_text, ip_address, port)
                    elif response.status == 401:
                        # Authentication required - still a valid ONVIF device
                        camera = DiscoveredCamera(
                            ip_address=ip_address,
                            port=port,
                            vendor="onvif",
                            onvif_port=port,
                            discovery_method=DiscoveryMethod.ONVIF,
                            confidence_score=0.8,
                            auth_required=True,
                            auth_method="digest"
                        )
                        camera.capabilities.append(CameraCapability.STREAMING)
                        return camera
            
            return None
            
        except Exception as e:
            logger.debug(f"ONVIF endpoint test failed: {e}")
            return None

    async def _parse_onvif_device_info(self, response: str, ip_address: str, port: int) -> Optional[DiscoveredCamera]:
        """Parse ONVIF GetDeviceInformation response"""
        try:
            root = ET.fromstring(response)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'tds': 'http://www.onvif.org/ver10/device/wsdl'
            }
            
            camera = DiscoveredCamera(
                ip_address=ip_address,
                port=port,
                onvif_port=port,
                discovery_method=DiscoveryMethod.ONVIF,
                confidence_score=0.95,
                auth_required=True,
                auth_method="digest"
            )
            
            # Extract device information
            body = root.find('.//soap:Body', namespaces)
            if body is not None:
                device_info = body.find('.//tds:GetDeviceInformationResponse', namespaces)
                if device_info is not None:
                    
                    manufacturer = device_info.find('.//tds:Manufacturer', namespaces)
                    if manufacturer is not None:
                        camera.vendor = manufacturer.text.lower()
                    
                    model = device_info.find('.//tds:Model', namespaces)
                    if model is not None:
                        camera.model = model.text
                    
                    firmware_version = device_info.find('.//tds:FirmwareVersion', namespaces)
                    if firmware_version is not None:
                        camera.firmware_version = firmware_version.text
                    
                    serial_number = device_info.find('.//tds:SerialNumber', namespaces)
                    if serial_number is not None:
                        camera.serial_number = serial_number.text
                    
                    hardware_id = device_info.find('.//tds:HardwareId', namespaces)
                    if hardware_id is not None:
                        camera.mac_address = hardware_id.text
            
            # Set vendor-specific defaults based on manufacturer
            if camera.vendor:
                if 'hikvision' in camera.vendor:
                    camera.vendor = "hikvision"
                    camera.default_username = "admin"
                    camera.default_password = "12345"
                elif 'dahua' in camera.vendor:
                    camera.vendor = "dahua"
                    camera.default_username = "admin"
                    camera.default_password = "admin"
                elif 'axis' in camera.vendor:
                    camera.vendor = "axis"
                    camera.default_username = "root"
                    camera.default_password = "pass"
                elif 'reolink' in camera.vendor:
                    camera.vendor = "reolink"
                    camera.default_username = "admin"
                    camera.default_password = ""
                else:
                    camera.default_username = "admin"
                    camera.default_password = ""
            
            # Add ONVIF capabilities
            camera.capabilities.extend([
                CameraCapability.STREAMING,
                CameraCapability.RECORDING
            ])
            
            return camera
            
        except Exception as e:
            logger.debug(f"Error parsing ONVIF device info: {e}")
            return None

    async def get_onvif_profiles(self, camera: DiscoveredCamera, username: str = None, password: str = None) -> Dict[str, Any]:
        """Get ONVIF profiles and capabilities for a camera"""
        try:
            auth_user = username or camera.default_username
            auth_pass = password or camera.default_password
            
            # Create authenticated session
            auth = aiohttp.BasicAuth(auth_user, auth_pass) if auth_user else None
            
            endpoint = f"http://{camera.ip_address}:{camera.onvif_port}/onvif/device_service"
            
            # Get profiles request
            soap_request = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
    <soap:Header/>
    <soap:Body>
        <trt:GetProfiles/>
    </soap:Body>
</soap:Envelope>'''

            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': '"http://www.onvif.org/ver10/media/wsdl/GetProfiles"'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(endpoint, data=soap_request, headers=headers, auth=auth) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        return await self._parse_onvif_profiles(response_text)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting ONVIF profiles: {e}")
            return {}

    async def _parse_onvif_profiles(self, response: str) -> Dict[str, Any]:
        """Parse ONVIF GetProfiles response"""
        try:
            root = ET.fromstring(response)
            
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'trt': 'http://www.onvif.org/ver10/media/wsdl',
                'tt': 'http://www.onvif.org/ver10/schema'
            }
            
            profiles = []
            
            # Find all profiles
            profile_elements = root.findall('.//trt:Profiles', namespaces)
            
            for profile_elem in profile_elements:
                profile_info = {}
                
                # Profile token
                token = profile_elem.get('token')
                if token:
                    profile_info['token'] = token
                
                # Video source configuration
                video_source = profile_elem.find('.//tt:VideoSourceConfiguration', namespaces)
                if video_source is not None:
                    bounds = video_source.find('.//tt:Bounds', namespaces)
                    if bounds is not None:
                        profile_info['resolution'] = {
                            'width': bounds.get('width'),
                            'height': bounds.get('height')
                        }
                
                # Video encoder configuration
                video_encoder = profile_elem.find('.//tt:VideoEncoderConfiguration', namespaces)
                if video_encoder is not None:
                    encoding = video_encoder.find('.//tt:Encoding', namespaces)
                    if encoding is not None:
                        profile_info['encoding'] = encoding.text
                    
                    resolution = video_encoder.find('.//tt:Resolution', namespaces)
                    if resolution is not None:
                        width = resolution.find('.//tt:Width', namespaces)
                        height = resolution.find('.//tt:Height', namespaces)
                        if width is not None and height is not None:
                            profile_info['encoder_resolution'] = {
                                'width': width.text,
                                'height': height.text
                            }
                    
                    quality = video_encoder.find('.//tt:Quality', namespaces)
                    if quality is not None:
                        profile_info['quality'] = quality.text
                    
                    framerate = video_encoder.find('.//tt:RateControl/tt:FrameRateLimit', namespaces)
                    if framerate is not None:
                        profile_info['framerate'] = framerate.text
                
                # Audio encoder configuration
                audio_encoder = profile_elem.find('.//tt:AudioEncoderConfiguration', namespaces)
                if audio_encoder is not None:
                    encoding = audio_encoder.find('.//tt:Encoding', namespaces)
                    if encoding is not None:
                        profile_info['audio_encoding'] = encoding.text
                
                profiles.append(profile_info)
            
            return {
                'profiles': profiles,
                'profile_count': len(profiles)
            }
            
        except Exception as e:
            logger.debug(f"Error parsing ONVIF profiles: {e}")
            return {}

    async def _rtsp_probe_discovery(self, ip_address: str) -> Optional[DiscoveredCamera]:
        """Discover camera using RTSP probing"""
        try:
            # Try common RTSP ports
            rtsp_ports = [554, 8554, 1935]
            
            for port in rtsp_ports:
                try:
                    # Test TCP connection to RTSP port
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(ip_address, port),
                        timeout=self.port_scan_timeout
                    )
                    
                    # Send RTSP OPTIONS request
                    options_request = f"OPTIONS rtsp://{ip_address}:{port} RTSP/1.0\r\nCSeq: 1\r\n\r\n"
                    writer.write(options_request.encode())
                    await writer.drain()
                    
                    # Read response
                    response = await asyncio.wait_for(reader.read(1024), timeout=3)
                    response_str = response.decode('utf-8', errors='ignore')
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    # Check if it's a valid RTSP response
                    if 'RTSP/1.0' in response_str and ('200' in response_str or '401' in response_str):
                        camera = DiscoveredCamera(
                            ip_address=ip_address,
                            rtsp_port=port,
                            discovery_method=DiscoveryMethod.RTSP_PROBE,
                            confidence_score=0.7,
                            auth_required='401' in response_str,
                            auth_method="digest"
                        )
                        
                        # Try to determine vendor from server header
                        if 'Server:' in response_str:
                            server_line = [line for line in response_str.split('\r\n') if line.startswith('Server:')]
                            if server_line:
                                server = server_line[0].lower()
                                if 'hikvision' in server:
                                    camera.vendor = 'hikvision'
                                elif 'dahua' in server:
                                    camera.vendor = 'dahua'
                                elif 'axis' in server:
                                    camera.vendor = 'axis'
                                elif 'reolink' in server:
                                    camera.vendor = 'reolink'
                        
                        camera.capabilities.append(CameraCapability.STREAMING)
                        
                        # Set common RTSP stream URLs
                        camera.main_stream_url = f"rtsp://{ip_address}:{port}/stream1"
                        camera.sub_stream_url = f"rtsp://{ip_address}:{port}/stream2"
                        
                        logger.debug(f"RTSP camera discovered at {ip_address}:{port}")
                        return camera
                
                except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                    continue
                except Exception as e:
                    logger.debug(f"RTSP probe error for {ip_address}:{port}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"RTSP probe discovery failed for {ip_address}: {e}")
            return None

    async def _upnp_discovery(self, ip_address: str = None) -> List[DiscoveredCamera]:
        """Discover cameras using UPnP SSDP"""
        discovered_cameras = []
        
        try:
            # UPnP SSDP M-SEARCH request
            ssdp_request = '''M-SEARCH * HTTP/1.1\r
HOST: 239.255.255.250:1900\r
MAN: "ssdp:discover"\r
ST: upnp:rootdevice\r
MX: 3\r\n\r\n'''

            # Set up UDP socket for SSDP
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)
            
            if ip_address:
                # Direct probe to specific IP
                sock.sendto(ssdp_request.encode('utf-8'), (ip_address, 1900))
            else:
                # Multicast probe
                sock.sendto(ssdp_request.encode('utf-8'), ('239.255.255.250', 1900))
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < 5.0:
                try:
                    data, addr = sock.recvfrom(4096)
                    response = data.decode('utf-8', errors='ignore')
                    
                    # Parse UPnP response
                    camera = await self._parse_upnp_response(response, addr[0])
                    if camera:
                        discovered_cameras.append(camera)
                        
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Error processing UPnP response: {e}")
                    
            sock.close()
            
        except Exception as e:
            logger.error(f"UPnP discovery error: {e}")
            
        return discovered_cameras

    async def _parse_upnp_response(self, response: str, ip_address: str) -> Optional[DiscoveredCamera]:
        """Parse UPnP SSDP response"""
        try:
            # Look for camera-related device types
            camera_indicators = [
                'MediaRenderer', 'MediaServer', 'NetworkCamera',
                'VideoDevice', 'SecurityDevice', 'IPCamera'
            ]
            
            response_lower = response.lower()
            
            # Check if this is a camera device
            if any(indicator.lower() in response_lower for indicator in camera_indicators):
                camera = DiscoveredCamera(
                    ip_address=ip_address,
                    discovery_method=DiscoveryMethod.UPNP,
                    confidence_score=0.6,
                    auth_required=True
                )
                
                # Extract device information from headers
                lines = response.split('\r\n')
                for line in lines:
                    if line.startswith('SERVER:') or line.startswith('Server:'):
                        server = line.split(':', 1)[1].strip().lower()
                        if 'hikvision' in server:
                            camera.vendor = 'hikvision'
                        elif 'dahua' in server:
                            camera.vendor = 'dahua'
                        elif 'axis' in server:
                            camera.vendor = 'axis'
                        elif 'reolink' in server:
                            camera.vendor = 'reolink'
                    
                    elif line.startswith('LOCATION:') or line.startswith('Location:'):
                        location_url = line.split(':', 1)[1].strip()
                        # Extract port from location URL if present
                        import re
                        port_match = re.search(r':(\d+)/', location_url)
                        if port_match:
                            camera.http_port = int(port_match.group(1))
                
                camera.capabilities.append(CameraCapability.STREAMING)
                return camera
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing UPnP response: {e}")
            return None

    async def _mdns_discovery(self, ip_address: str = None) -> List[DiscoveredCamera]:
        """Discover cameras using mDNS/Bonjour"""
        discovered_cameras = []
        
        try:
            # mDNS query for camera services
            mdns_query = '''
            _http._tcp.local.
            _rtsp._tcp.local.
            _onvif._tcp.local.
            _camera._tcp.local.
            '''
            
            # This is a simplified implementation
            # In production, you'd use a proper mDNS library like python-zeroconf
            logger.debug("mDNS discovery not fully implemented - requires zeroconf library")
            
        except Exception as e:
            logger.error(f"mDNS discovery error: {e}")
            
        return discovered_cameras

    # Auto-Configuration Engine with Credential Testing
    async def auto_configure_discovered_camera(self, discovered_camera: DiscoveredCamera, 
                                             test_credentials: bool = True) -> Dict[str, Any]:
        """
        Auto-configure discovered camera with credential testing and stream validation
        
        Args:
            discovered_camera: DiscoveredCamera object
            test_credentials: Whether to test credentials
            
        Returns:
            Configuration result dictionary
        """
        config_result = {
            "ip_address": discovered_camera.ip_address,
            "vendor": discovered_camera.vendor,
            "status": "pending",
            "credentials": {},
            "streams": {},
            "capabilities": [],
            "errors": []
        }
        
        try:
            # Step 1: Test and validate credentials
            if test_credentials:
                credential_result = await self._test_camera_credentials(discovered_camera)
                config_result["credentials"] = credential_result
                
                if not credential_result.get("valid", False):
                    config_result["status"] = "failed"
                    config_result["errors"].append("Invalid credentials")
                    return config_result
            
            # Step 2: Validate stream URLs
            stream_result = await self._validate_camera_streams(discovered_camera)
            config_result["streams"] = stream_result
            
            # Step 3: Test camera capabilities
            capability_result = await self._test_camera_capabilities(discovered_camera)
            config_result["capabilities"] = capability_result
            
            # Step 4: Generate optimized configuration
            optimized_config = await self._generate_optimized_config(discovered_camera)
            config_result["config"] = optimized_config
            
            config_result["status"] = "success"
            
        except Exception as e:
            config_result["status"] = "error"
            config_result["errors"].append(str(e))
            logger.error(f"Auto-configuration failed for {discovered_camera.ip_address}: {e}")
        
        return config_result

    async def _test_camera_credentials(self, camera: DiscoveredCamera) -> Dict[str, Any]:
        """Test camera credentials using multiple methods"""
        credential_result = {
            "valid": False,
            "username": None,
            "password": None,
            "auth_method": "digest",
            "tested_combinations": []
        }
        
        # Common credential combinations to test
        credential_combinations = [
            (camera.default_username, camera.default_password),
            ("admin", ""),
            ("admin", "admin"),
            ("admin", "12345"),
            ("admin", "123456"),
            ("admin", "password"),
            ("root", "pass"),
            ("root", ""),
            ("user", "user"),
            ("", "")
        ]
        
        # Add vendor-specific credentials
        if camera.vendor == "hikvision":
            credential_combinations.extend([
                ("admin", "12345"),
                ("admin", "hik12345"),
                ("admin", "hikadmin")
            ])
        elif camera.vendor == "dahua":
            credential_combinations.extend([
                ("admin", "admin"),
                ("admin", "dahua123"),
                ("admin", "888888")
            ])
        elif camera.vendor == "axis":
            credential_combinations.extend([
                ("root", "pass"),
                ("admin", "axis"),
                ("viewer", "")
            ])
        elif camera.vendor == "reolink":
            credential_combinations.extend([
                ("admin", ""),
                ("admin", "reolink"),
                ("admin", "123456")
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_combinations = []
        for combo in credential_combinations:
            if combo not in seen:
                seen.add(combo)
                unique_combinations.append(combo)
        
        # Test each credential combination
        for username, password in unique_combinations:
            try:
                # Test credentials using vendor-specific method
                is_valid = await self._test_specific_credentials(camera, username, password)
                
                credential_result["tested_combinations"].append({
                    "username": username,
                    "password": password,
                    "valid": is_valid
                })
                
                if is_valid:
                    credential_result["valid"] = True
                    credential_result["username"] = username
                    credential_result["password"] = password
                    break
                    
            except Exception as e:
                logger.debug(f"Credential test failed for {username}:{password} on {camera.ip_address}: {e}")
                continue
        
        return credential_result

    async def _test_specific_credentials(self, camera: DiscoveredCamera, username: str, password: str) -> bool:
        """Test specific credentials against camera"""
        try:
            # Choose test method based on vendor
            if camera.vendor == "reolink":
                return await self._test_reolink_credentials(camera.ip_address, username, password)
            elif camera.vendor == "hikvision":
                return await self._test_hikvision_credentials(camera.ip_address, username, password)
            elif camera.vendor == "dahua":
                return await self._test_dahua_credentials(camera.ip_address, username, password)
            elif camera.vendor == "axis":
                return await self._test_axis_credentials(camera.ip_address, username, password)
            else:
                # Generic ONVIF test
                return await self._test_onvif_credentials(camera.ip_address, username, password)
                
        except Exception as e:
            logger.debug(f"Credential test error: {e}")
            return False

    async def _test_reolink_credentials(self, ip_address: str, username: str, password: str) -> bool:
        """Test Reolink credentials using API login"""
        try:
            url = f"http://{ip_address}/cgi-bin/api.cgi"
            payload = [{
                "cmd": "Login",
                "action": 0,
                "param": {
                    "User": {
                        "userName": username,
                        "password": password
                    }
                }
            }]
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[0]["code"] == 0
            
            return False
            
        except Exception:
            return False

    async def _test_hikvision_credentials(self, ip_address: str, username: str, password: str) -> bool:
        """Test Hikvision credentials using ISAPI"""
        try:
            url = f"http://{ip_address}/ISAPI/System/deviceInfo"
            auth = aiohttp.BasicAuth(username, password)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url, auth=auth) as response:
                    return response.status == 200
            
        except Exception:
            return False

    async def _test_dahua_credentials(self, ip_address: str, username: str, password: str) -> bool:
        """Test Dahua credentials using API"""
        try:
            url = f"http://{ip_address}/cgi-bin/magicBox.cgi?action=getDeviceType"
            auth = aiohttp.BasicAuth(username, password)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url, auth=auth) as response:
                    return response.status == 200
            
        except Exception:
            return False

    async def _test_axis_credentials(self, ip_address: str, username: str, password: str) -> bool:
        """Test Axis credentials using API"""
        try:
            url = f"http://{ip_address}/axis-cgi/param.cgi?action=list&group=Properties"
            auth = aiohttp.BasicAuth(username, password)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url, auth=auth) as response:
                    return response.status == 200
            
        except Exception:
            return False

    async def _test_onvif_credentials(self, ip_address: str, username: str, password: str) -> bool:
        """Test ONVIF credentials"""
        try:
            url = f"http://{ip_address}/onvif/device_service"
            auth = aiohttp.BasicAuth(username, password)
            
            soap_request = '''<?xml version="1.0" encoding="UTF-8"?>
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
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(url, data=soap_request, headers=headers, auth=auth) as response:
                    return response.status == 200
            
        except Exception:
            return False

    async def _validate_camera_streams(self, camera: DiscoveredCamera) -> Dict[str, Any]:
        """Validate camera stream URLs"""
        stream_result = {
            "main_stream": {"valid": False, "url": None, "error": None},
            "sub_stream": {"valid": False, "url": None, "error": None},
            "snapshot": {"valid": False, "url": None, "error": None}
        }
        
        # Test main stream
        if camera.main_stream_url:
            stream_result["main_stream"]["url"] = camera.main_stream_url
            try:
                is_valid = await self._test_rtsp_stream(camera.main_stream_url)
                stream_result["main_stream"]["valid"] = is_valid
            except Exception as e:
                stream_result["main_stream"]["error"] = str(e)
        
        # Test sub stream
        if camera.sub_stream_url:
            stream_result["sub_stream"]["url"] = camera.sub_stream_url
            try:
                is_valid = await self._test_rtsp_stream(camera.sub_stream_url)
                stream_result["sub_stream"]["valid"] = is_valid
            except Exception as e:
                stream_result["sub_stream"]["error"] = str(e)
        
        # Test snapshot URL
        if camera.snapshot_url:
            stream_result["snapshot"]["url"] = camera.snapshot_url
            try:
                is_valid = await self._test_http_snapshot(camera.snapshot_url)
                stream_result["snapshot"]["valid"] = is_valid
            except Exception as e:
                stream_result["snapshot"]["error"] = str(e)
        
        return stream_result

    async def _test_rtsp_stream(self, stream_url: str) -> bool:
        """Test RTSP stream connectivity"""
        try:
            # Parse RTSP URL to get host and port
            import re
            match = re.match(r'rtsp://(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?', stream_url)
            if not match:
                return False
            
            username, password, host, port = match.groups()
            port = int(port) if port else 554
            
            # Test TCP connection to RTSP port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5
            )
            
            # Send RTSP OPTIONS request
            options_request = f"OPTIONS {stream_url} RTSP/1.0\r\nCSeq: 1\r\n\r\n"
            writer.write(options_request.encode())
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(reader.read(1024), timeout=3)
            response_str = response.decode('utf-8', errors='ignore')
            
            writer.close()
            await writer.wait_closed()
            
            # Check for valid RTSP response
            return 'RTSP/1.0' in response_str and ('200' in response_str or '401' in response_str)
            
        except Exception as e:
            logger.debug(f"RTSP stream test failed: {e}")
            return False

    async def _test_http_snapshot(self, snapshot_url: str) -> bool:
        """Test HTTP snapshot URL"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(snapshot_url) as response:
                    return response.status == 200 and 'image' in response.headers.get('content-type', '')
        except Exception:
            return False

    async def _test_camera_capabilities(self, camera: DiscoveredCamera) -> List[str]:
        """Test camera capabilities"""
        tested_capabilities = []
        
        # Test based on known capabilities
        for capability in camera.capabilities:
            if capability == CameraCapability.PTZ:
                if await self._test_ptz_capability(camera):
                    tested_capabilities.append("ptz")
            elif capability == CameraCapability.AUDIO:
                if await self._test_audio_capability(camera):
                    tested_capabilities.append("audio")
            elif capability == CameraCapability.MOTION_DETECTION:
                tested_capabilities.append("motion_detection")
            elif capability == CameraCapability.AI_DETECTION:
                tested_capabilities.append("ai_detection")
            elif capability == CameraCapability.STREAMING:
                tested_capabilities.append("streaming")
            elif capability == CameraCapability.RECORDING:
                tested_capabilities.append("recording")
        
        return tested_capabilities

    async def _test_ptz_capability(self, camera: DiscoveredCamera) -> bool:
        """Test PTZ capability"""
        # This would require vendor-specific PTZ commands
        # For now, just return True if PTZ capability is advertised
        return CameraCapability.PTZ in camera.capabilities

    async def _test_audio_capability(self, camera: DiscoveredCamera) -> bool:
        """Test audio capability"""
        # This would require checking audio streams
        # For now, just return True if audio capability is advertised
        return CameraCapability.AUDIO in camera.capabilities

    async def _generate_optimized_config(self, camera: DiscoveredCamera) -> Dict[str, Any]:
        """Generate optimized configuration for camera"""
        config = {
            "network": {
                "ip_address": camera.ip_address,
                "http_port": camera.http_port,
                "rtsp_port": camera.rtsp_port,
                "onvif_port": camera.onvif_port
            },
            "authentication": {
                "username": camera.default_username,
                "password": camera.default_password,
                "auth_method": camera.auth_method
            },
            "streaming": {
                "main_stream_url": camera.main_stream_url,
                "sub_stream_url": camera.sub_stream_url,
                "snapshot_url": camera.snapshot_url,
                "preferred_codec": "H.264",
                "preferred_resolution": "1920x1080",
                "preferred_fps": 15  # Optimized for LPPR
            },
            "detection": {
                "enabled": True,
                "detection_zones": [],
                "confidence_threshold": 0.7,
                "processing_interval": 0.5
            },
            "recording": {
                "continuous": False,
                "motion_triggered": True,
                "retention_days": 7
            },
            "capabilities": [cap.value for cap in camera.capabilities],
            "vendor_specific": self._get_vendor_specific_config(camera)
        }
        
        return config

    def _get_vendor_specific_config(self, camera: DiscoveredCamera) -> Dict[str, Any]:
        """Get vendor-specific configuration options"""
        vendor_config = {}
        
        if camera.vendor == "reolink":
            vendor_config = {
                "api_version": "v1",
                "channel": 0,
                "spotlight_enabled": True,
                "ai_detection_types": ["person", "vehicle", "pet"]
            }
        elif camera.vendor == "hikvision":
            vendor_config = {
                "isapi_version": "v2.0",
                "channel": 101,
                "smart_detection": True,
                "line_crossing_detection": True
            }
        elif camera.vendor == "dahua":
            vendor_config = {
                "api_version": "v3",
                "channel": 1,
                "ivs_enabled": True,
                "face_detection": True
            }
        elif camera.vendor == "axis":
            vendor_config = {
                "vapix_version": "3.0",
                "analytics_enabled": True,
                "audio_detection": True
            }
        
        return vendor_config