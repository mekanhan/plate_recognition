from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
import xml.etree.ElementTree as ET

class CameraVendor(Enum):
    REOLINK = "reolink"
    HIKVISION = "hikvision"
    DAHUA = "dahua"
    AXIS = "axis"
    GENERIC_ONVIF = "onvif"

@dataclass
class NetworkConfig:
    ip_address: str
    subnet_mask: str = "255.255.255.0"
    gateway: str = ""
    dns_primary: str = "8.8.8.8"
    dns_secondary: str = "8.8.4.4"
    dhcp_enabled: bool = False

@dataclass
class StreamConfig:
    main_stream_url: str
    sub_stream_url: str
    mobile_stream_url: Optional[str] = None
    codec: str = "H.264"
    resolution_main: str = "1920x1080"
    resolution_sub: str = "640x480"
    fps_main: int = 30
    fps_sub: int = 15
    bitrate_main: int = 2048
    bitrate_sub: int = 512

@dataclass
class SecurityConfig:
    username: str
    password: str
    encryption_enabled: bool = True
    https_enabled: bool = True
    auth_method: str = "digest"  # digest, basic, wsse

@dataclass
class RecordingConfig:
    continuous_recording: bool = True
    motion_detection: bool = True
    sensitivity: int = 50  # 0-100
    recording_quality: str = "high"
    storage_days: int = 30

class CameraConfigurationError(Exception):
    pass

class CameraAdapter(ABC):
    """Abstract base class for camera-specific adapters"""
    
    @abstractmethod
    async def discover_camera(self, ip_address: str) -> Dict[str, Any]:
        """Auto-discover camera capabilities and model"""
        pass
    
    @abstractmethod
    async def get_default_config(self) -> Dict[str, Any]:
        """Get vendor-specific default configuration"""
        pass
    
    @abstractmethod
    async def validate_credentials(self, ip: str, username: str, password: str) -> bool:
        """Validate camera credentials"""
        pass
    
    @abstractmethod
    async def configure_camera(self, config: Dict[str, Any]) -> bool:
        """Apply configuration to camera"""
        pass
    
    @abstractmethod
    def get_stream_urls(self, ip: str, username: str, password: str) -> StreamConfig:
        """Generate stream URLs for this camera type"""
        pass

class ReolinkAdapter(CameraAdapter):
    """Reolink-specific camera adapter"""
    
    async def discover_camera(self, ip_address: str) -> Dict[str, Any]:
        """Discover Reolink camera through API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Reolink API endpoint for device info
                url = f"http://{ip_address}/cgi-bin/api.cgi"
                payload = [{
                    "cmd": "GetDevInfo",
                    "action": 0,
                    "param": {}
                }]
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        device_info = data[0]["value"]["DevInfo"]
                        return {
                            "vendor": "reolink",
                            "model": device_info.get("model", "Unknown"),
                            "serial": device_info.get("serial", "Unknown"),
                            "firmware": device_info.get("firmVer", "Unknown"),
                            "channels": device_info.get("channelNum", 1),
                            "capabilities": self._parse_capabilities(device_info)
                        }
        except Exception as e:
            raise CameraConfigurationError(f"Failed to discover Reolink camera: {e}")
    
    async def get_default_config(self) -> Dict[str, Any]:
        """Reolink default configuration"""
        return {
            "network": {
                "http_port": 80,
                "https_port": 443,
                "rtsp_port": 554,
                "onvif_port": 8000
            },
            "streams": {
                "main": {"resolution": "1920x1080", "fps": 30, "bitrate": 2048},
                "sub": {"resolution": "640x480", "fps": 15, "bitrate": 512}
            },
            "recording": {
                "format": "mp4",
                "continuous": True,
                "motion_detection": True
            },
            "security": {
                "default_username": "admin",
                "auth_method": "digest",
                "encryption": True
            }
        }
    
    async def validate_credentials(self, ip: str, username: str, password: str) -> bool:
        """Validate Reolink credentials"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{ip}/cgi-bin/api.cgi"
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
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[0]["code"] == 0
                    return False
        except:
            return False
    
    async def configure_camera(self, config: Dict[str, Any]) -> bool:
        """Configure Reolink camera"""
        try:
            # Implementation for Reolink configuration
            # This would involve multiple API calls to set network, stream, recording settings
            return True
        except Exception as e:
            raise CameraConfigurationError(f"Failed to configure Reolink camera: {e}")
    
    def get_stream_urls(self, ip: str, username: str, password: str) -> StreamConfig:
        """Generate Reolink stream URLs"""
        return StreamConfig(
            main_stream_url=f"rtsp://{username}:{password}@{ip}:554/h264Preview_01_main",
            sub_stream_url=f"rtsp://{username}:{password}@{ip}:554/h264Preview_01_sub",
            mobile_stream_url=f"rtsp://{username}:{password}@{ip}:554/h264Preview_01_mobile"
        )
    
    def _parse_capabilities(self, device_info: Dict) -> List[str]:
        """Parse camera capabilities from device info"""
        capabilities = []
        if device_info.get("audioNum", 0) > 0:
            capabilities.append("audio")
        if device_info.get("ptza", False):
            capabilities.append("ptz")
        if device_info.get("ai", False):
            capabilities.append("ai_detection")
        return capabilities

class ONVIFAdapter(CameraAdapter):
    """Generic ONVIF adapter for standard IP cameras"""
    
    async def discover_camera(self, ip_address: str) -> Dict[str, Any]:
        """Discover camera through ONVIF"""
        try:
            # ONVIF discovery using WS-Discovery
            url = f"http://{ip_address}/onvif/device_service"
            soap_body = """<?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
                <soap:Body>
                    <tds:GetDeviceInformation xmlns:tds="http://www.onvif.org/ver10/device/wsdl"/>
                </soap:Body>
            </soap:Envelope>"""
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Content-Type': 'application/soap+xml',
                    'SOAPAction': 'http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation'
                }
                
                async with session.post(url, data=soap_body, headers=headers) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        return self._parse_onvif_response(xml_data)
        except Exception as e:
            raise CameraConfigurationError(f"ONVIF discovery failed: {e}")
    
    async def get_default_config(self) -> Dict[str, Any]:
        """Generic ONVIF configuration"""
        return {
            "network": {
                "http_port": 80,
                "rtsp_port": 554,
                "onvif_port": 80
            },
            "streams": {
                "main": {"resolution": "1920x1080", "fps": 25, "bitrate": 2048},
                "sub": {"resolution": "640x480", "fps": 15, "bitrate": 512}
            },
            "security": {
                "auth_method": "digest",
                "encryption": False
            }
        }
    
    async def validate_credentials(self, ip: str, username: str, password: str) -> bool:
        """Validate ONVIF credentials"""
        # Implementation would use ONVIF authentication
        return True
    
    async def configure_camera(self, config: Dict[str, Any]) -> bool:
        """Configure camera through ONVIF"""
        return True
    
    def get_stream_urls(self, ip: str, username: str, password: str) -> StreamConfig:
        """Generate generic ONVIF stream URLs"""
        return StreamConfig(
            main_stream_url=f"rtsp://{username}:{password}@{ip}:554/stream1",
            sub_stream_url=f"rtsp://{username}:{password}@{ip}:554/stream2"
        )
    
    def _parse_onvif_response(self, xml_data: str) -> Dict[str, Any]:
        """Parse ONVIF XML response"""
        try:
            root = ET.fromstring(xml_data)
            # Parse device information from ONVIF response
            return {
                "vendor": "onvif",
                "model": "Generic",
                "capabilities": ["onvif_compliant"]
            }
        except:
            return {"vendor": "unknown", "model": "unknown"}

class CameraConfigurationManager:
    """Main camera configuration manager"""
    
    def __init__(self):
        self.adapters = {
            CameraVendor.REOLINK: ReolinkAdapter(),
            CameraVendor.GENERIC_ONVIF: ONVIFAdapter()
        }
    
    async def auto_discover_camera(self, ip_address: str) -> Dict[str, Any]:
        """Auto-discover camera type and capabilities"""
        
        # Try Reolink first (since you have these cameras)
        try:
            result = await self.adapters[CameraVendor.REOLINK].discover_camera(ip_address)
            if result:
                return result
        except:
            pass
        
        # Fallback to ONVIF
        try:
            result = await self.adapters[CameraVendor.GENERIC_ONVIF].discover_camera(ip_address)
            return result
        except:
            raise CameraConfigurationError(f"Unable to discover camera at {ip_address}")
    
    async def setup_camera(self, ip_address: str, username: str = "admin", password: str = "") -> Dict[str, Any]:
        """Complete camera setup process"""
        
        # Step 1: Discover camera
        camera_info = await self.auto_discover_camera(ip_address)
        vendor = CameraVendor(camera_info["vendor"])
        adapter = self.adapters[vendor]
        
        # Step 2: Validate credentials
        if not await adapter.validate_credentials(ip_address, username, password):
            # Try common default credentials
            default_creds = [
                ("admin", ""),
                ("admin", "admin"),
                ("admin", "123456"),
                ("admin", "password")
            ]
            
            for user, pwd in default_creds:
                if await adapter.validate_credentials(ip_address, user, pwd):
                    username, password = user, pwd
                    break
            else:
                raise CameraConfigurationError("Unable to authenticate with camera")
        
        # Step 3: Get default configuration
        default_config = await adapter.get_default_config()
        
        # Step 4: Generate stream URLs
        stream_config = adapter.get_stream_urls(ip_address, username, password)
        
        # Step 5: Build complete configuration
        complete_config = {
            "camera_info": camera_info,
            "network": NetworkConfig(ip_address=ip_address),
            "security": SecurityConfig(username=username, password=password),
            "streams": stream_config,
            "defaults": default_config
        }
        
        return complete_config
    
    async def configure_for_lppr(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize configuration for License Plate Recognition"""
        
        # LPPR-specific optimizations
        lppr_config = config.copy()
        
        # Optimize stream settings for LPPR
        lppr_config["streams"].resolution_main = "1920x1080"  # Higher resolution for better OCR
        lppr_config["streams"].fps_main = 15  # Lower FPS to reduce processing load
        lppr_config["streams"].codec = "H.264"  # Efficient codec
        
        # Motion detection settings
        lppr_config["recording"] = RecordingConfig(
            continuous_recording=False,  # Only record on motion for LPPR
            motion_detection=True,
            sensitivity=30,  # Lower sensitivity to avoid false triggers
            recording_quality="high",
            storage_days=7  # Shorter retention for LPPR events
        )
        
        # Add LPPR-specific metadata
        lppr_config["lppr_settings"] = {
            "detection_zones": [],  # Define areas where to detect plates
            "processing_interval": 0.5,  # Process every 0.5 seconds
            "confidence_threshold": 0.7,  # Minimum confidence for plate detection
            "enhancement_enabled": True,  # Enable image enhancement for better OCR
            "night_mode_compensation": True
        }
        
        return lppr_config

# Example usage
async def main():
    config_manager = CameraConfigurationManager()
    
    # Auto-discover and setup Reolink camera
    try:
        camera_config = await config_manager.setup_camera("192.168.1.100", "admin", "")
        print(f"Camera discovered: {camera_config['camera_info']['model']}")
        
        # Optimize for LPPR
        lppr_config = await config_manager.configure_for_lppr(camera_config)
        print(f"LPPR configuration ready")
        print(f"Main stream: {lppr_config['streams'].main_stream_url}")
        
    except CameraConfigurationError as e:
        print(f"Configuration error: {e}")

if __name__ == "__main__":
    asyncio.run(main())