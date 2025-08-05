#!/usr/bin/env python3
"""
Camera Connection Diagnostics Agent
Automatically diagnoses and fixes camera connection issues
"""

import asyncio
import socket
import subprocess
import platform
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import cv2
import aiohttp
import asyncio
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CameraDiagnostics")


@dataclass
class CameraConfig:
    """Camera configuration"""
    camera_id: str
    name: str
    ip_address: str
    username: str = "admin"
    password: str = ""
    port: int = 554
    stream_path: str = ""
    protocol: str = "rtsp"
    auth_method: str = "basic"  # basic or digest
    
    @property
    def base_url(self) -> str:
        """Base URL without auth"""
        return f"{self.protocol}://{self.ip_address}:{self.port}"
    
    @property
    def stream_url(self) -> str:
        """Complete stream URL with auth"""
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.ip_address}:{self.port}{self.stream_path}"


@dataclass
class DiagnosticResult:
    """Results from diagnostic tests"""
    success: bool
    test_name: str
    message: str
    details: Dict = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class CameraManufacturerProfiles:
    """Known camera manufacturer profiles and stream paths"""
    
    PROFILES = {
        "hikvision": {
            "detection_strings": ["Hikvision", "HIK", "DS-2"],
            "stream_paths": [
                "/Streaming/Channels/101",     # Main stream
                "/Streaming/Channels/102",     # Sub stream  
                "/Streaming/Channels/1",
                "/h264/ch1/main/av_stream",
                "/ISAPI/Streaming/channels/101"
            ],
            "ports": [554, 8554, 80, 443],
            "auth_methods": ["digest", "basic"],
            "onvif_path": "/onvif/device_service"
        },
        "dahua": {
            "detection_strings": ["Dahua", "DH-", "IPC-"],
            "stream_paths": [
                "/cam/realmonitor?channel=1&subtype=0",  # Main
                "/cam/realmonitor?channel=1&subtype=1",  # Sub
                "/live",
                "/video1",
                "/h264Preview_01_main"
            ],
            "ports": [554, 37777, 80],
            "auth_methods": ["digest", "basic"],
            "onvif_path": "/onvif/device_service"
        },
        "axis": {
            "detection_strings": ["AXIS", "Axis Communications"],
            "stream_paths": [
                "/axis-cgi/mjpg/video.cgi",
                "/mjpg/video.mjpg",
                "/h264/media.amp",
                "/onvif-media/media.amp"
            ],
            "ports": [554, 80, 443],
            "auth_methods": ["digest", "basic"],
            "onvif_path": "/onvif/device_service"
        },
        "reolink": {
            "detection_strings": ["Reolink"],
            "stream_paths": [
                "/h264Preview_01_main",      # H.264 main stream
                "/h264Preview_01_sub",       # H.264 sub stream
                "/h265Preview_01_main",      # H.265 main stream
                "/h265Preview_01_sub",       # H.265 sub stream
                "/Preview_01_main",
                "/Preview_01_sub"
            ],
            "ports": [554, 8554],
            "auth_methods": ["basic"],
            "onvif_path": "/onvif/device_service"
        },
        "generic": {
            "detection_strings": [],
            "stream_paths": [
                "/stream",
                "/video",
                "/live",
                "/h264",
                "/media/video1",
                "/1",
                "/live/ch00_0",
                "/user=admin&password=&channel=1&stream=0.sdp",
                "/videoMain",
                "/stream1",
                "/mpeg4/media.amp",
                "/video.mjpg"
            ],
            "ports": [554, 8554, 80, 8080],
            "auth_methods": ["basic", "digest", "none"],
            "onvif_path": "/onvif/device_service"
        }
    }


class CameraDiagnosticsAgent:
    """Main diagnostics agent for camera connections"""
    
    def __init__(self, history_file: str = "camera_diagnostics_history.json"):
        self.history_file = history_file
        self.successful_configs: Dict[str, Dict] = self.load_history()
        self.manufacturer_profiles = CameraManufacturerProfiles.PROFILES
        
    def load_history(self) -> Dict:
        """Load successful configurations from history"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_history(self):
        """Save successful configurations"""
        with open(self.history_file, 'w') as f:
            json.dump(self.successful_configs, f, indent=2)
    
    async def diagnose_camera(self, config: CameraConfig) -> Dict:
        """
        Run complete diagnostic suite on camera
        Returns diagnostic report with working configuration if found
        """
        logger.info(f"Starting diagnostics for camera: {config.name} ({config.ip_address})")
        
        results = {
            "camera_id": config.camera_id,
            "camera_name": config.name,
            "timestamp": datetime.now().isoformat(),
            "network_tests": await self.run_network_tests(config),
            "manufacturer_detection": await self.detect_manufacturer(config),
            "stream_discovery": await self.discover_streams(config),
            "working_config": None,
            "recommendations": []
        }
        
        # Check if we found a working configuration
        for test in results["stream_discovery"]:
            if test.success and test.details and test.details.get("working_url"):
                results["working_config"] = {
                    "url": test.details["working_url"],
                    "stream_path": test.details.get("stream_path", ""),
                    "auth_method": test.details.get("auth_method", "basic"),
                    "manufacturer": results["manufacturer_detection"].get("detected_manufacturer", "unknown")
                }
                # Save to history
                self.successful_configs[config.ip_address] = results["working_config"]
                self.save_history()
                break
        
        # Generate recommendations
        results["recommendations"] = self.generate_recommendations(results)
        
        return results
    
    async def run_network_tests(self, config: CameraConfig) -> List[DiagnosticResult]:
        """Run network connectivity tests"""
        results = []
        
        # Test 1: Ping
        ping_result = await self.test_ping(config.ip_address)
        results.append(ping_result)
        
        # Test 2: Port scan
        port_results = await self.scan_ports(config.ip_address)
        results.append(port_results)
        
        # Test 3: HTTP probe (might reveal camera web interface)
        http_result = await self.test_http_interface(config)
        results.append(http_result)
        
        return results
    
    async def test_ping(self, ip_address: str) -> DiagnosticResult:
        """Test if camera responds to ping"""
        try:
            # Platform-specific ping command
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', ip_address]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return DiagnosticResult(
                    success=True,
                    test_name="ping",
                    message=f"Camera at {ip_address} is reachable",
                    details={"output": result.stdout}
                )
            else:
                return DiagnosticResult(
                    success=False,
                    test_name="ping",
                    message=f"Camera at {ip_address} is not responding to ping",
                    details={"output": result.stderr}
                )
        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                success=False,
                test_name="ping",
                message=f"Ping to {ip_address} timed out",
                details={"error": "timeout"}
            )
        except Exception as e:
            return DiagnosticResult(
                success=False,
                test_name="ping",
                message=f"Ping test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def scan_ports(self, ip_address: str) -> DiagnosticResult:
        """Scan common camera ports"""
        common_ports = [554, 8554, 80, 443, 8080, 37777, 7070]
        open_ports = []
        
        for port in common_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                result = sock.connect_ex((ip_address, port))
                if result == 0:
                    open_ports.append(port)
            except Exception:
                pass
            finally:
                sock.close()
        
        if open_ports:
            return DiagnosticResult(
                success=True,
                test_name="port_scan",
                message=f"Found open ports: {open_ports}",
                details={"open_ports": open_ports}
            )
        else:
            return DiagnosticResult(
                success=False,
                test_name="port_scan",
                message="No common camera ports are open",
                details={"scanned_ports": common_ports}
            )
    
    async def test_http_interface(self, config: CameraConfig) -> DiagnosticResult:
        """Test if camera has HTTP interface"""
        http_ports = [80, 443, 8080]
        
        for port in http_ports:
            for protocol in ['http', 'https']:
                url = f"{protocol}://{config.ip_address}:{port}"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5, ssl=False) as response:
                            if response.status < 500:
                                headers = dict(response.headers)
                                return DiagnosticResult(
                                    success=True,
                                    test_name="http_interface",
                                    message=f"Found HTTP interface at {url}",
                                    details={
                                        "url": url,
                                        "status": response.status,
                                        "server": headers.get('Server', 'Unknown')
                                    }
                                )
                except Exception:
                    continue
        
        return DiagnosticResult(
            success=False,
            test_name="http_interface",
            message="No HTTP interface found",
            details={"tested_ports": http_ports}
        )
    
    async def detect_manufacturer(self, config: CameraConfig) -> Dict:
        """Detect camera manufacturer"""
        detected = {
            "detected_manufacturer": None,
            "confidence": 0,
            "detection_method": None
        }
        
        # Method 1: Check previous successful configs
        if config.ip_address in self.successful_configs:
            manufacturer = self.successful_configs[config.ip_address].get("manufacturer")
            if manufacturer:
                detected["detected_manufacturer"] = manufacturer
                detected["confidence"] = 0.9
                detected["detection_method"] = "history"
                return detected
        
        # Method 2: HTTP header inspection
        http_result = await self.test_http_interface(config)
        if http_result.success and http_result.details:
            server_header = http_result.details.get("server", "").lower()
            for manufacturer, profile in self.manufacturer_profiles.items():
                for detection_string in profile["detection_strings"]:
                    if detection_string.lower() in server_header:
                        detected["detected_manufacturer"] = manufacturer
                        detected["confidence"] = 0.8
                        detected["detection_method"] = "http_header"
                        return detected
        
        # Method 3: ONVIF probe
        onvif_result = await self.test_onvif(config)
        if onvif_result and onvif_result.get("manufacturer"):
            detected["detected_manufacturer"] = onvif_result["manufacturer"]
            detected["confidence"] = 0.9
            detected["detection_method"] = "onvif"
            return detected
        
        # Default to generic
        detected["detected_manufacturer"] = "generic"
        detected["confidence"] = 0.3
        detected["detection_method"] = "default"
        
        return detected
    
    async def test_onvif(self, config: CameraConfig) -> Optional[Dict]:
        """Test ONVIF compatibility"""
        # Simplified ONVIF detection
        onvif_paths = ["/onvif/device_service", "/onvif/device"]
        
        for path in onvif_paths:
            for port in [80, 8080]:
                url = f"http://{config.ip_address}:{port}{path}"
                try:
                    # This is a simplified check - real ONVIF requires SOAP
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=3) as response:
                            if response.status == 200:
                                return {"manufacturer": "onvif_compatible"}
                except Exception:
                    continue
        
        return None
    
    async def discover_streams(self, config: CameraConfig) -> List[DiagnosticResult]:
        """Discover working stream URLs"""
        results = []
        manufacturer_info = await self.detect_manufacturer(config)
        manufacturer = manufacturer_info.get("detected_manufacturer", "generic")
        
        # Get profile for detected manufacturer
        profile = self.manufacturer_profiles.get(manufacturer, self.manufacturer_profiles["generic"])
        
        # Test each potential stream path
        for stream_path in profile["stream_paths"]:
            for auth_method in profile["auth_methods"]:
                result = await self.test_stream_url(config, stream_path, auth_method)
                if result.success:
                    results.append(result)
                    return results  # Return first working config
        
        # If no working path found, return all attempts
        if not any(r.success for r in results):
            results.append(DiagnosticResult(
                success=False,
                test_name="stream_discovery",
                message=f"No working stream found for {manufacturer} camera",
                details={"tested_paths": profile["stream_paths"]}
            ))
        
        return results
    
    async def test_stream_url(self, config: CameraConfig, stream_path: str, auth_method: str) -> DiagnosticResult:
        """Test specific stream URL"""
        # Build URL based on auth method
        if auth_method == "none":
            test_url = f"{config.protocol}://{config.ip_address}:{config.port}{stream_path}"
        else:
            test_url = f"{config.protocol}://{config.username}:{config.password}@{config.ip_address}:{config.port}{stream_path}"
        
        try:
            # Test with OpenCV
            cap = cv2.VideoCapture(test_url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    cap.release()
                    
                    return DiagnosticResult(
                        success=True,
                        test_name="stream_test",
                        message=f"Working stream found: {stream_path}",
                        details={
                            "working_url": test_url,
                            "stream_path": stream_path,
                            "auth_method": auth_method,
                            "resolution": f"{width}x{height}"
                        }
                    )
            
            cap.release()
            
        except Exception as e:
            logger.debug(f"Stream test failed for {test_url}: {str(e)}")
        
        return DiagnosticResult(
            success=False,
            test_name="stream_test",
            message=f"Stream test failed for {stream_path}",
            details={"tested_url": test_url, "auth_method": auth_method}
        )
    
    def generate_recommendations(self, diagnostic_results: Dict) -> List[str]:
        """Generate recommendations based on diagnostic results"""
        recommendations = []
        
        # Check network tests
        network_tests = diagnostic_results.get("network_tests", [])
        ping_success = any(test.test_name == "ping" and test.success for test in network_tests)
        ports_found = any(test.test_name == "port_scan" and test.success for test in network_tests)
        
        if not ping_success:
            recommendations.append("Camera is not responding to ping. Check if camera is powered on and connected to network.")
            recommendations.append("Verify camera IP address is correct.")
            recommendations.append("Check if camera is on a different VLAN or subnet.")
        
        if not ports_found:
            recommendations.append("No camera ports are open. Camera may be behind a firewall.")
            recommendations.append("Check firewall rules on both camera and network.")
        
        # Check if working config was found
        if not diagnostic_results.get("working_config"):
            recommendations.append("No working stream configuration found.")
            recommendations.append("Try using camera manufacturer's app to verify camera is working.")
            recommendations.append("Check camera username and password.")
            recommendations.append("Camera may require specific authentication method (digest vs basic).")
        else:
            recommendations.append(f"✓ Working configuration found! Use: {diagnostic_results['working_config']['url']}")
        
        return recommendations
    
    async def quick_test(self, config: CameraConfig) -> bool:
        """Quick test to see if camera is accessible"""
        result = await self.test_ping(config.ip_address)
        return result.success
    
    def print_report(self, diagnostic_results: Dict):
        """Print formatted diagnostic report"""
        print("\n" + "="*60)
        print(f"CAMERA DIAGNOSTIC REPORT")
        print(f"Camera: {diagnostic_results['camera_name']}")
        print(f"Time: {diagnostic_results['timestamp']}")
        print("="*60)
        
        # Network Tests
        print("\n📡 NETWORK TESTS:")
        for test in diagnostic_results.get("network_tests", []):
            status = "✅" if test.success else "❌"
            print(f"{status} {test.test_name}: {test.message}")
        
        # Manufacturer Detection
        print("\n🏭 MANUFACTURER DETECTION:")
        mfg_info = diagnostic_results.get("manufacturer_detection", {})
        print(f"Detected: {mfg_info.get('detected_manufacturer', 'Unknown')}")
        print(f"Confidence: {mfg_info.get('confidence', 0) * 100:.0f}%")
        print(f"Method: {mfg_info.get('detection_method', 'none')}")
        
        # Stream Discovery
        print("\n📹 STREAM DISCOVERY:")
        stream_tests = diagnostic_results.get("stream_discovery", [])
        for test in stream_tests:
            if test.success:
                print(f"✅ Found working stream!")
                if test.details:
                    print(f"   Path: {test.details.get('stream_path', 'unknown')}")
                    print(f"   Resolution: {test.details.get('resolution', 'unknown')}")
                    print(f"   Auth: {test.details.get('auth_method', 'unknown')}")
            else:
                print(f"❌ {test.message}")
        
        # Working Configuration
        print("\n🔧 WORKING CONFIGURATION:")
        working_config = diagnostic_results.get("working_config")
        if working_config:
            print(f"✅ URL: {working_config.get('url', 'none')}")
            print(f"   Stream Path: {working_config.get('stream_path', 'none')}")
            print(f"   Auth Method: {working_config.get('auth_method', 'none')}")
        else:
            print("❌ No working configuration found")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(diagnostic_results.get("recommendations", []), 1):
            print(f"{i}. {rec}")
        
        print("\n" + "="*60 + "\n")


# Example usage and testing
async def main():
    """Example usage of the diagnostics agent"""
    
    # Create diagnostics agent
    agent = CameraDiagnosticsAgent()
    
    # Example camera configuration
    camera_config = CameraConfig(
        camera_id="test_camera_1",
        name="Front Entrance Camera",
        ip_address="192.168.1.100",  # Replace with your camera IP
        username="admin",
        password="admin123",
        port=554
    )
    
    print("🔍 Starting Camera Diagnostics...")
    
    # Run full diagnostics
    results = await agent.diagnose_camera(camera_config)
    
    # Print formatted report
    agent.print_report(results)
    
    # Example: Quick connectivity test
    print("\n⚡ Running quick connectivity test...")
    is_reachable = await agent.quick_test(camera_config)
    print(f"Camera reachable: {'Yes' if is_reachable else 'No'}")
    
    # Save results to file
    with open(f"diagnostic_report_{camera_config.camera_id}.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Detailed report saved to: diagnostic_report_{camera_config.camera_id}.json")


if __name__ == "__main__":
    asyncio.run(main())