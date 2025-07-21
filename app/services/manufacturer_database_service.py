# app/services/manufacturer_database_service.py
# Manufacturer database service for IP camera configuration
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ManufacturerConfig:
    """Configuration for a specific manufacturer"""
    name: str
    common_models: List[str]
    default_ports: Dict[str, int]
    stream_paths: Dict[str, str]
    default_auth: str
    default_username: str
    supported_codecs: List[str] = None
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.supported_codecs is None:
            self.supported_codecs = ["H.264", "MJPEG"]
        if self.capabilities is None:
            self.capabilities = ["video", "audio"]

class ManufacturerDatabaseService:
    """Service for managing manufacturer-specific camera configurations"""
    
    def __init__(self):
        self.manufacturers: Dict[str, ManufacturerConfig] = {}
        self._load_manufacturer_data()
    
    def _load_manufacturer_data(self):
        """Load manufacturer configurations from data"""
        manufacturer_data = {
            "reolink": {
                "name": "Reolink",
                "common_models": ["RLC-811A", "RLC-820A", "RLC-823A", "RLC-410A", "RLC-512A"],
                "default_ports": {
                    "rtsp": 554,
                    "rtsps": 322,
                    "http": 80,
                    "https": 443,
                    "onvif": 8000
                },
                "stream_paths": {
                    "main_stream": "/h264Preview_01_main",
                    "sub_stream": "/h264Preview_01_sub",
                    "rtsp_main": "/h264Preview_01_main",
                    "rtsp_sub": "/h264Preview_01_sub",
                    "http_main": "/flv?port=1935&app=bcs&stream=channel0_main.bcs",
                    "http_sub": "/flv?port=1935&app=bcs&stream=channel0_sub.bcs"
                },
                "default_auth": "basic",
                "default_username": "admin",
                "supported_codecs": ["H.264", "H.265", "MJPEG"],
                "capabilities": ["video", "audio", "ptz", "night_vision"]
            },
            "hikvision": {
                "name": "Hikvision",
                "common_models": ["DS-2CD2085FWD-I", "DS-2CD2042WD-I", "DS-2DE3304W-DE", "DS-2CD2143G2-I"],
                "default_ports": {
                    "rtsp": 554,
                    "http": 80,
                    "https": 443,
                    "onvif": 80
                },
                "stream_paths": {
                    "main_stream": "/Streaming/Channels/101",
                    "sub_stream": "/Streaming/Channels/102",
                    "rtsp_main": "/Streaming/Channels/101",
                    "rtsp_sub": "/Streaming/Channels/102",
                    "http_main": "/ISAPI/Streaming/channels/101/httppreview",
                    "http_sub": "/ISAPI/Streaming/channels/102/httppreview"
                },
                "default_auth": "digest",
                "default_username": "admin",
                "supported_codecs": ["H.264", "H.265", "MJPEG"],
                "capabilities": ["video", "audio", "ptz", "analytics", "face_detection"]
            },
            "dahua": {
                "name": "Dahua",
                "common_models": ["IPC-HFW4431R-Z", "IPC-HDW4431C-A", "SD59225U-HNI", "IPC-HFW5831E-ZE"],
                "default_ports": {
                    "rtsp": 554,
                    "http": 80,
                    "https": 443,
                    "onvif": 80
                },
                "stream_paths": {
                    "main_stream": "/cam/realmonitor?channel=1&subtype=0",
                    "sub_stream": "/cam/realmonitor?channel=1&subtype=1",
                    "rtsp_main": "/cam/realmonitor?channel=1&subtype=0",
                    "rtsp_sub": "/cam/realmonitor?channel=1&subtype=1",
                    "http_main": "/cgi-bin/mjpg/video.cgi?channel=1&subtype=0",
                    "http_sub": "/cgi-bin/mjpg/video.cgi?channel=1&subtype=1"
                },
                "default_auth": "basic",
                "default_username": "admin",
                "supported_codecs": ["H.264", "H.265", "MJPEG"],
                "capabilities": ["video", "audio", "ptz", "analytics", "smart_detection"]
            },
            "axis": {
                "name": "Axis",
                "common_models": ["M3027-PVE", "P3367-VE", "Q1615", "P1448-LE", "M2026-LE"],
                "default_ports": {
                    "rtsp": 554,
                    "http": 80,
                    "https": 443,
                    "onvif": 80
                },
                "stream_paths": {
                    "main_stream": "/axis-media/media.amp?videocodec=h264",
                    "sub_stream": "/axis-media/media.amp?videocodec=h264&resolution=640x480",
                    "rtsp_main": "/axis-media/media.amp?videocodec=h264",
                    "rtsp_sub": "/axis-media/media.amp?videocodec=h264&resolution=640x480",
                    "http_main": "/mjpg/video.mjpg",
                    "http_sub": "/mjpg/video.mjpg?resolution=640x480"
                },
                "default_auth": "basic",
                "default_username": "root",
                "supported_codecs": ["H.264", "H.265", "MJPEG"],
                "capabilities": ["video", "audio", "ptz", "analytics", "edge_analytics"]
            },
            "uniview": {
                "name": "Uniview",
                "common_models": ["IPC2128SR3-DPF40-C", "IPC6128SFW-X22P", "IPC2324EBR3-DPF28"],
                "default_ports": {
                    "rtsp": 554,
                    "http": 80,
                    "https": 443,
                    "onvif": 80
                },
                "stream_paths": {
                    "main_stream": "/media/video1",
                    "sub_stream": "/media/video2",
                    "rtsp_main": "/media/video1",
                    "rtsp_sub": "/media/video2",
                    "http_main": "/cgi-bin/video.cgi?msubmenu=jpg",
                    "http_sub": "/cgi-bin/video.cgi?msubmenu=jpg&resolution=2"
                },
                "default_auth": "basic",
                "default_username": "admin",
                "supported_codecs": ["H.264", "H.265", "MJPEG"],
                "capabilities": ["video", "audio", "ptz", "smart_ir"]
            },
            "bosch": {
                "name": "Bosch",
                "common_models": ["NBE-6502-AL", "NDE-8112-RX", "NEI-50051-V3"],
                "default_ports": {
                    "rtsp": 554,
                    "http": 80,
                    "https": 443,
                    "onvif": 80
                },
                "stream_paths": {
                    "main_stream": "/rtsp_tunnel?h26x=4&line=1&inst=1",
                    "sub_stream": "/rtsp_tunnel?h26x=4&line=2&inst=1",
                    "rtsp_main": "/rtsp_tunnel?h26x=4&line=1&inst=1",
                    "rtsp_sub": "/rtsp_tunnel?h26x=4&line=2&inst=1",
                    "http_main": "/snap.jpg",
                    "http_sub": "/snap.jpg?res=half"
                },
                "default_auth": "basic",
                "default_username": "service",
                "supported_codecs": ["H.264", "H.265", "MJPEG"],
                "capabilities": ["video", "audio", "ptz", "analytics", "intelligent_video"]
            },
            "generic": {
                "name": "Generic/Other",
                "common_models": ["Generic IP Camera", "ONVIF Camera", "Standard RTSP Camera"],
                "default_ports": {
                    "rtsp": 554,
                    "http": 80,
                    "https": 443,
                    "onvif": 80
                },
                "stream_paths": {
                    "main_stream": "/stream1",
                    "sub_stream": "/stream2",
                    "rtsp_main": "/stream1",
                    "rtsp_sub": "/stream2",
                    "http_main": "/video.mjpg",
                    "http_sub": "/video.mjpg",
                    "common_paths": [
                        "/stream1",
                        "/stream2", 
                        "/live/main",
                        "/live/sub",
                        "/video.mjpg",
                        "/mjpg/video.mjpg",
                        "/cgi-bin/video.cgi",
                        "/onvif/media_service/stream_uri"
                    ]
                },
                "default_auth": "basic",
                "default_username": "admin",
                "supported_codecs": ["H.264", "MJPEG"],
                "capabilities": ["video"]
            }
        }
        
        # Convert to ManufacturerConfig objects
        for key, data in manufacturer_data.items():
            self.manufacturers[key] = ManufacturerConfig(**data)
    
    def get_manufacturer_list(self) -> List[Dict[str, str]]:
        """Get list of supported manufacturers"""
        return [
            {"key": key, "name": config.name} 
            for key, config in self.manufacturers.items()
        ]
    
    def get_manufacturer_config(self, manufacturer_key: str) -> Optional[ManufacturerConfig]:
        """Get configuration for a specific manufacturer"""
        return self.manufacturers.get(manufacturer_key.lower())
    
    def get_common_models(self, manufacturer_key: str) -> List[str]:
        """Get common models for a manufacturer"""
        config = self.get_manufacturer_config(manufacturer_key)
        return config.common_models if config else []
    
    def get_default_port(self, manufacturer_key: str, connection_type: str) -> int:
        """Get default port for manufacturer and connection type"""
        config = self.get_manufacturer_config(manufacturer_key)
        if not config:
            return {"rtsp": 554, "http": 80, "https": 443, "onvif": 80}.get(connection_type, 554)
        return config.default_ports.get(connection_type, 554)
    
    def get_stream_path(self, manufacturer_key: str, connection_type: str, stream_type: str = "main") -> str:
        """Get stream path for manufacturer, connection type, and stream type"""
        config = self.get_manufacturer_config(manufacturer_key)
        if not config:
            return "/stream1" if stream_type == "main" else "/stream2"
        
        # Try specific combination first
        path_key = f"{connection_type}_{stream_type}"
        if path_key in config.stream_paths:
            return config.stream_paths[path_key]
        
        # Fall back to generic stream type
        stream_key = f"{stream_type}_stream"
        if stream_key in config.stream_paths:
            return config.stream_paths[stream_key]
        
        # Default fallback
        return config.stream_paths.get("main_stream", "/stream1")
    
    def get_suggested_stream_paths(self, manufacturer_key: str, connection_type: str) -> List[str]:
        """Get all suggested stream paths for a manufacturer and connection type"""
        config = self.get_manufacturer_config(manufacturer_key)
        if not config:
            return ["/stream1", "/stream2", "/live/main", "/video.mjpg"]
        
        paths = []
        
        # Add specific paths for this connection type
        for key, path in config.stream_paths.items():
            if key.startswith(connection_type) or key.endswith("_stream"):
                paths.append(path)
        
        # Add common paths for generic manufacturer
        if manufacturer_key == "generic" and "common_paths" in config.stream_paths:
            paths.extend(config.stream_paths["common_paths"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        
        return unique_paths
    
    def get_default_auth_method(self, manufacturer_key: str) -> str:
        """Get default authentication method for manufacturer"""
        config = self.get_manufacturer_config(manufacturer_key)
        return config.default_auth if config else "basic"
    
    def get_default_username(self, manufacturer_key: str) -> str:
        """Get default username for manufacturer"""
        config = self.get_manufacturer_config(manufacturer_key)
        return config.default_username if config else "admin"
    
    def get_supported_codecs(self, manufacturer_key: str) -> List[str]:
        """Get supported codecs for manufacturer"""
        config = self.get_manufacturer_config(manufacturer_key)
        return config.supported_codecs if config else ["H.264", "MJPEG"]
    
    def get_capabilities(self, manufacturer_key: str) -> List[str]:
        """Get capabilities for manufacturer"""
        config = self.get_manufacturer_config(manufacturer_key)
        return config.capabilities if config else ["video"]
    
    def build_stream_url(self, manufacturer_key: str, connection_type: str, 
                        ip_address: str, port: int, stream_path: str, 
                        username: str = None, password: str = None) -> str:
        """Build complete stream URL"""
        if connection_type.startswith("rtsp"):
            if username and password:
                return f"{connection_type}://{username}:{password}@{ip_address}:{port}{stream_path}"
            else:
                return f"{connection_type}://{ip_address}:{port}{stream_path}"
        else:
            return f"{connection_type}://{ip_address}:{port}{stream_path}"
    
    def detect_manufacturer_from_onvif(self, onvif_info: Dict[str, Any]) -> Optional[str]:
        """Detect manufacturer from ONVIF device information"""
        if not onvif_info:
            return None
        
        manufacturer_name = onvif_info.get("manufacturer", "").lower()
        model_name = onvif_info.get("model", "").lower()
        
        # Check for direct manufacturer matches
        for key, config in self.manufacturers.items():
            if key in manufacturer_name or config.name.lower() in manufacturer_name:
                return key
        
        # Check for model-based detection
        for key, config in self.manufacturers.items():
            for model in config.common_models:
                if model.lower() in model_name:
                    return key
        
        return "generic"
    
    def get_manufacturer_suggestions(self, query: str) -> List[Dict[str, str]]:
        """Get manufacturer suggestions based on query"""
        query = query.lower()
        suggestions = []
        
        for key, config in self.manufacturers.items():
            if query in key or query in config.name.lower():
                suggestions.append({
                    "key": key,
                    "name": config.name,
                    "match_type": "name"
                })
        
        # Also check models for suggestions
        for key, config in self.manufacturers.items():
            for model in config.common_models:
                if query in model.lower():
                    suggestions.append({
                        "key": key,
                        "name": config.name,
                        "model": model,
                        "match_type": "model"
                    })
        
        return suggestions
    
    def validate_configuration(self, manufacturer_key: str, connection_type: str, 
                             stream_path: str) -> Dict[str, Any]:
        """Validate camera configuration against manufacturer specifications"""
        config = self.get_manufacturer_config(manufacturer_key)
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "suggestions": []
        }
        
        if not config:
            validation_result["warnings"].append(f"Unknown manufacturer: {manufacturer_key}")
            return validation_result
        
        # Check if connection type is supported
        if connection_type not in config.default_ports:
            validation_result["warnings"].append(
                f"Connection type '{connection_type}' may not be supported by {config.name}"
            )
            validation_result["suggestions"].append(
                f"Try using: {', '.join(config.default_ports.keys())}"
            )
        
        # Check if stream path looks correct
        known_paths = list(config.stream_paths.values())
        if stream_path not in known_paths:
            validation_result["warnings"].append(
                f"Stream path '{stream_path}' may not be correct for {config.name}"
            )
            suggested_path = self.get_stream_path(manufacturer_key, connection_type)
            validation_result["suggestions"].append(
                f"Try using: {suggested_path}"
            )
        
        return validation_result