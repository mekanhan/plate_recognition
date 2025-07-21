# app/services/rtsp_connection_tester.py
# RTSP connection validation and troubleshooting service
import asyncio
import logging
import subprocess
import socket
import urllib.parse
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import cv2
import requests
import time

logger = logging.getLogger(__name__)

class ConnectionResult(Enum):
    SUCCESS = "success"
    NETWORK_UNREACHABLE = "network_unreachable"
    PORT_BLOCKED = "port_blocked"
    AUTH_FAILED = "auth_failed"
    INVALID_PATH = "invalid_path"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class RTSPTestResult:
    """Result of RTSP connection test"""
    success: bool
    result_code: ConnectionResult
    working_url: Optional[str] = None
    error_message: Optional[str] = None
    tested_urls: List[str] = None
    camera_manufacturer: Optional[str] = None
    recommended_fixes: List[str] = None
    test_duration: float = 0.0

class RTSPConnectionTester:
    """Service for testing and troubleshooting RTSP camera connections"""
    
    # Manufacturer-specific RTSP URL patterns
    MANUFACTURER_PATTERNS = {
        "reolink": [
            "/h264Preview_01_main",  # Main stream
            "/h264Preview_01_sub",   # Sub stream
            "/channel1",             # Alternative format
            "/cam/realmonitor?channel=1&subtype=0",  # NVR format
        ],
        "hikvision": [
            "/Streaming/Channels/101/",
            "/Streaming/Channels/102/",
            "/ISAPI/streaming/channels/101/",
        ],
        "dahua": [
            "/cam/realmonitor?channel=1&subtype=0",
            "/cam/realmonitor?channel=1&subtype=1",
        ],
        "axis": [
            "/axis-media/media.amp",
            "/mjpg/video.mjpg",
        ],
        "generic": [
            "/stream1",
            "/stream2", 
            "/live",
            "/video",
            "/cam1",
        ]
    }
    
    def __init__(self):
        self.test_timeout = 10.0  # seconds
        self.connection_timeout = 5.0  # seconds
        
    async def test_camera_connection(self, ip_address: str, username: str, password: str, 
                                   port: int = 554, manufacturer: Optional[str] = None) -> RTSPTestResult:
        """
        Comprehensive RTSP connection test
        
        Args:
            ip_address: Camera IP address
            username: RTSP username
            password: RTSP password
            port: RTSP port (default 554)
            manufacturer: Known manufacturer (optional)
            
        Returns:
            RTSPTestResult with detailed results
        """
        start_time = time.time()
        tested_urls = []
        recommended_fixes = []
        
        logger.info(f"Starting RTSP connection test for {ip_address}")
        
        # Step 1: Basic network connectivity
        if not await self._test_network_connectivity(ip_address):
            return RTSPTestResult(
                success=False,
                result_code=ConnectionResult.NETWORK_UNREACHABLE,
                error_message=f"Cannot reach {ip_address} - check network connectivity",
                tested_urls=tested_urls,
                recommended_fixes=["Check network connection", "Verify IP address", "Check firewall settings"],
                test_duration=time.time() - start_time
            )
        
        # Step 2: RTSP port connectivity
        if not await self._test_port_connectivity(ip_address, port):
            return RTSPTestResult(
                success=False,
                result_code=ConnectionResult.PORT_BLOCKED,
                error_message=f"RTSP port {port} is not accessible on {ip_address}",
                tested_urls=tested_urls,
                recommended_fixes=[f"Check if RTSP is enabled on camera", f"Verify port {port} is not blocked", "Try alternative RTSP ports (8554, 10554)"],
                test_duration=time.time() - start_time
            )
        
        # Step 3: Detect manufacturer if not provided
        if not manufacturer:
            manufacturer = await self._detect_manufacturer(ip_address)
            
        # Step 4: Test RTSP URLs with different patterns
        patterns = self._get_patterns_for_manufacturer(manufacturer)
        
        for pattern in patterns:
            # Test with original password (may have special chars)
            test_url = self._build_rtsp_url(ip_address, port, username, password, pattern)
            tested_urls.append(test_url)
            
            logger.info(f"Testing RTSP URL: {self._sanitize_url_for_log(test_url)}")
            
            result = await self._test_rtsp_url(test_url)
            if result.success:
                return RTSPTestResult(
                    success=True,
                    result_code=ConnectionResult.SUCCESS,
                    working_url=test_url,
                    tested_urls=tested_urls,
                    camera_manufacturer=manufacturer,
                    test_duration=time.time() - start_time
                )
            
            # Test with URL-encoded password for special characters
            if self._has_special_chars(password):
                encoded_password = urllib.parse.quote(password, safe='')
                encoded_test_url = self._build_rtsp_url(ip_address, port, username, encoded_password, pattern)
                tested_urls.append(encoded_test_url)
                
                logger.info(f"Testing with encoded password: {self._sanitize_url_for_log(encoded_test_url)}")
                
                result = await self._test_rtsp_url(encoded_test_url)
                if result.success:
                    return RTSPTestResult(
                        success=True,
                        result_code=ConnectionResult.SUCCESS,
                        working_url=encoded_test_url,
                        tested_urls=tested_urls,
                        camera_manufacturer=manufacturer,
                        recommended_fixes=["Password contained special characters that needed URL encoding"],
                        test_duration=time.time() - start_time
                    )
        
        # If all tests failed, provide comprehensive recommendations
        recommended_fixes = self._generate_failure_recommendations(manufacturer, password, tested_urls)
        
        return RTSPTestResult(
            success=False,
            result_code=ConnectionResult.AUTH_FAILED,  # Most likely cause after connectivity is verified
            error_message="All RTSP URL patterns failed - check credentials and stream paths",
            tested_urls=tested_urls,
            camera_manufacturer=manufacturer,
            recommended_fixes=recommended_fixes,
            test_duration=time.time() - start_time
        )
    
    async def _test_network_connectivity(self, ip_address: str) -> bool:
        """Test basic network connectivity with ping"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '3', ip_address,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            returncode = await proc.wait()
            return returncode == 0
        except Exception as e:
            logger.error(f"Ping test failed: {e}")
            return False
    
    async def _test_port_connectivity(self, ip_address: str, port: int) -> bool:
        """Test RTSP port connectivity"""
        try:
            future = asyncio.open_connection(ip_address, port)
            reader, writer = await asyncio.wait_for(future, timeout=self.connection_timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
    
    async def _detect_manufacturer(self, ip_address: str) -> str:
        """Detect camera manufacturer from web interface"""
        ports_to_try = [80, 8080, 443, 8000]
        
        for port in ports_to_try:
            for protocol in ['http', 'https']:
                try:
                    url = f"{protocol}://{ip_address}:{port}" if port != (80 if protocol == 'http' else 443) else f"{protocol}://{ip_address}"
                    
                    response = requests.get(
                        url, 
                        timeout=self.connection_timeout,
                        verify=False,  # Ignore SSL cert issues
                        allow_redirects=True
                    )
                    
                    content = response.text.lower()
                    
                    # Check for manufacturer indicators
                    if 'reolink' in content:
                        return 'reolink'
                    elif 'hikvision' in content or 'hik-connect' in content:
                        return 'hikvision'
                    elif 'dahua' in content:
                        return 'dahua'
                    elif 'axis' in content:
                        return 'axis'
                        
                except Exception:
                    continue
        
        return 'generic'
    
    def _get_patterns_for_manufacturer(self, manufacturer: str) -> List[str]:
        """Get RTSP URL patterns for specific manufacturer"""
        patterns = self.MANUFACTURER_PATTERNS.get(manufacturer, [])
        if not patterns:
            patterns = self.MANUFACTURER_PATTERNS['generic']
        
        # Always include generic patterns as fallback
        if manufacturer != 'generic':
            patterns.extend(self.MANUFACTURER_PATTERNS['generic'])
        
        return patterns
    
    def _build_rtsp_url(self, ip_address: str, port: int, username: str, password: str, path: str) -> str:
        """Build RTSP URL with credentials"""
        if path.startswith('/'):
            path = path[1:]  # Remove leading slash
            
        return f"rtsp://{username}:{password}@{ip_address}:{port}/{path}"
    
    def _has_special_chars(self, password: str) -> bool:
        """Check if password contains characters that need URL encoding"""
        special_chars = ['_', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=', '[', ']', '{', '}', '|', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/']
        return any(char in password for char in special_chars)
    
    def _sanitize_url_for_log(self, url: str) -> str:
        """Remove password from URL for safe logging"""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.password:
                sanitized = url.replace(parsed.password, '***')
                return sanitized
        except:
            pass
        return url.split('@')[0] + '@***'
    
    async def _test_rtsp_url(self, rtsp_url: str) -> RTSPTestResult:
        """Test a specific RTSP URL with OpenCV"""
        try:
            # Create a separate task to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self._opencv_test_url, rtsp_url)
            
            return RTSPTestResult(
                success=success,
                result_code=ConnectionResult.SUCCESS if success else ConnectionResult.UNKNOWN_ERROR
            )
        except Exception as e:
            return RTSPTestResult(
                success=False,
                result_code=ConnectionResult.UNKNOWN_ERROR,
                error_message=str(e)
            )
    
    def _opencv_test_url(self, rtsp_url: str) -> bool:
        """Test RTSP URL with OpenCV (blocking operation)"""
        try:
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                return False
            
            # Try to read a frame with timeout
            start_time = time.time()
            while time.time() - start_time < self.test_timeout:
                ret, frame = cap.read()
                if ret and frame is not None:
                    cap.release()
                    return True
                time.sleep(0.1)
            
            cap.release()
            return False
            
        except Exception as e:
            logger.error(f"OpenCV test failed: {e}")
            return False
    
    def _generate_failure_recommendations(self, manufacturer: str, password: str, tested_urls: List[str]) -> List[str]:
        """Generate troubleshooting recommendations based on test results"""
        recommendations = []
        
        # Password-related recommendations
        if self._has_special_chars(password):
            recommendations.append("Password contains special characters - try changing to alphanumeric only")
        
        # Manufacturer-specific recommendations
        if manufacturer == 'reolink':
            recommendations.extend([
                "For Reolink cameras, verify RTSP is enabled in camera settings",
                "Try accessing camera web interface and check Network > Advanced > Port Settings",
                "Common Reolink default credentials: admin/admin or admin/(blank)"
            ])
        elif manufacturer == 'hikvision':
            recommendations.extend([
                "For Hikvision cameras, check if RTSP authentication is required",
                "Try enabling 'digest/basic' authentication in camera settings"
            ])
        
        # General recommendations
        recommendations.extend([
            "Verify username and password are correct",
            "Check if camera RTSP service is enabled",
            "Try connecting with VLC Media Player to test RTSP URL manually",
            "Consider using different RTSP ports (8554, 10554)",
            "Check camera firmware version - newer versions may use different stream paths"
        ])
        
        return recommendations

    async def test_with_vlc(self, rtsp_url: str) -> bool:
        """Test RTSP URL with VLC command line (if available)"""
        try:
            # Try to use VLC to validate the stream
            proc = await asyncio.create_subprocess_exec(
                'vlc', '--intf', 'dummy', '--run-time=3', '--quit-after-eof', rtsp_url,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            returncode = await asyncio.wait_for(proc.wait(), timeout=10.0)
            return returncode == 0
        except Exception:
            return False