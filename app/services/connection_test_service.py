# app/services/connection_test_service.py
"""
Enhanced connection testing service for IP cameras.
Provides comprehensive connectivity, authentication, and stream testing capabilities.
"""
import asyncio
import cv2
import logging
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import subprocess
import socket
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import aiohttp
import json

from ..services.manufacturer_database_service import ManufacturerDatabaseService

logger = logging.getLogger(__name__)

@dataclass
class ConnectivityResult:
    """Result of basic network connectivity test"""
    success: bool
    ping_response_time_ms: Optional[float] = None
    open_ports: List[int] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.open_ports is None:
            self.open_ports = []

@dataclass
class AuthResult:
    """Result of authentication test"""
    success: bool
    auth_method: str
    response_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    requires_digest: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class StreamTestResult:
    """Result of stream accessibility test"""
    success: bool
    stream_url: str
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    codec_info: Optional[str] = None
    resolution: Optional[Tuple[int, int]] = None
    fps: Optional[float] = None
    accessible: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class StreamCapabilities:
    """Stream capability information"""
    supported_codecs: List[str]
    resolutions: List[Tuple[int, int]]
    fps_ranges: List[Tuple[float, float]]
    audio_support: bool
    ptz_support: bool
    max_bitrate: Optional[int] = None
    protocols: List[str] = None
    
    def __post_init__(self):
        if self.protocols is None:
            self.protocols = []

@dataclass 
class ConnectionTestResult:
    """Comprehensive connection test result"""
    success: bool
    ip_address: str
    connectivity: ConnectivityResult
    authentication: Optional[AuthResult] = None
    stream_test: Optional[StreamTestResult] = None
    capabilities: Optional[StreamCapabilities] = None
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    manufacturer_validation: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []

class ConnectionTestService:
    """Enhanced connection testing service for IP cameras"""
    
    def __init__(self):
        self.manufacturer_db = ManufacturerDatabaseService()
        self.timeout_seconds = 30  # Increased for Reolink cameras
        self.max_concurrent_tests = 5
        self.rtsp_timeout_seconds = 30  # Extended RTSP timeout
        self.connection_retry_attempts = 3
        
    async def test_basic_connectivity(self, ip_address: str) -> ConnectivityResult:
        """Test basic network connectivity (ping, port scan)"""
        try:
            # Test ping connectivity
            ping_time = await self._ping_host(ip_address)
            
            if ping_time is None:
                return ConnectivityResult(
                    success=False,
                    error_message=f"Host {ip_address} is not reachable (ping failed)"
                )
            
            # Test common camera ports
            common_ports = [554, 80, 443, 8080, 8000, 322, 1935]
            open_ports = await self._scan_ports(ip_address, common_ports)
            
            return ConnectivityResult(
                success=True,
                ping_response_time_ms=ping_time,
                open_ports=open_ports
            )
            
        except Exception as e:
            logger.error(f"Connectivity test failed for {ip_address}: {str(e)}")
            return ConnectivityResult(
                success=False,
                error_message=f"Connectivity test error: {str(e)}"
            )
    
    async def test_authentication(
        self,
        url: str,
        credentials: Dict[str, str],
        auth_methods: List[str] = None
    ) -> AuthResult:
        """Test camera authentication with multiple methods"""
        
        if auth_methods is None:
            auth_methods = ['basic', 'digest']
        
        username = credentials.get('username', 'admin')
        password = credentials.get('password', '')
        
        for auth_method in auth_methods:
            try:
                start_time = time.time()
                
                if auth_method == 'basic':
                    auth = HTTPBasicAuth(username, password)
                elif auth_method == 'digest':
                    auth = HTTPDigestAuth(username, password)
                else:
                    continue
                
                response = requests.get(
                    url,
                    auth=auth,
                    timeout=self.timeout_seconds,
                    verify=False  # Allow self-signed certificates
                )
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return AuthResult(
                        success=True,
                        auth_method=auth_method,
                        response_code=response.status_code,
                        response_time_ms=response_time
                    )
                elif response.status_code == 401:
                    # Authentication failed, but server is responsive
                    continue
                else:
                    # Other error codes
                    return AuthResult(
                        success=False,
                        auth_method=auth_method,
                        response_code=response.status_code,
                        response_time_ms=response_time,
                        error_message=f"HTTP {response.status_code}: {response.reason}"
                    )
                    
            except requests.exceptions.Timeout:
                return AuthResult(
                    success=False,
                    auth_method=auth_method,
                    error_message="Authentication timeout"
                )
            except requests.exceptions.ConnectionError:
                return AuthResult(
                    success=False,
                    auth_method=auth_method,
                    error_message="Connection refused"
                )
            except Exception as e:
                logger.error(f"Authentication test failed: {str(e)}")
                return AuthResult(
                    success=False,
                    auth_method=auth_method,
                    error_message=f"Authentication error: {str(e)}"
                )
        
        # All auth methods failed
        return AuthResult(
            success=False,
            auth_method='none',
            error_message="All authentication methods failed"
        )
    
    async def test_stream_access(
        self,
        stream_url: str,
        timeout: int = 10
    ) -> StreamTestResult:
        """Test stream accessibility and basic properties"""
        
        result = {"success": False, "accessible": False}
        
        def test_stream():
            try:
                cap = cv2.VideoCapture(stream_url)
                # Set comprehensive timeout properties for better RTSP handling
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
                
                # Additional OpenCV properties for RTSP streams
                if stream_url.startswith('rtsp://'):
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
                    cap.set(cv2.CAP_PROP_FPS, 5)  # Lower FPS for testing
                    
                    # Try different backends for RTSP
                    if not cap.isOpened():
                        cap.release()
                        cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
                        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
                        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
                
                if cap.isOpened():
                    # Try to read a frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        result["success"] = True
                        result["accessible"] = True
                        result["resolution"] = (
                            int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        )
                        result["fps"] = cap.get(cv2.CAP_PROP_FPS)
                        
                        # Get codec information
                        fourcc = cap.get(cv2.CAP_PROP_FOURCC)
                        if fourcc:
                            result["codec_info"] = self._fourcc_to_string(fourcc)
                    else:
                        result["error_message"] = "Stream opened but no frames available"
                else:
                    result["error_message"] = "Unable to open stream"
                    
                cap.release()
                
            except Exception as e:
                result["error_message"] = f"Stream test error: {str(e)}"
        
        # Run test in thread with timeout
        start_time = time.time()
        thread = threading.Thread(target=test_stream)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        response_time = (time.time() - start_time) * 1000
        
        if thread.is_alive():
            result["error_message"] = f"Stream test timed out after {timeout} seconds"
        
        return StreamTestResult(
            success=result.get("success", False),
            stream_url=stream_url,
            response_time_ms=response_time,
            error_message=result.get("error_message"),
            codec_info=result.get("codec_info"),
            resolution=result.get("resolution"),
            fps=result.get("fps"),
            accessible=result.get("accessible", False)
        )
    
    async def get_stream_capabilities(
        self,
        stream_url: str
    ) -> StreamCapabilities:
        """Analyze stream capabilities (codecs, resolution, fps)"""
        
        capabilities = StreamCapabilities(
            supported_codecs=[],
            resolutions=[],
            fps_ranges=[],
            audio_support=False,
            ptz_support=False,
            protocols=[]
        )
        
        try:
            cap = cv2.VideoCapture(stream_url)
            
            if cap.isOpened():
                # Get basic stream properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                if width > 0 and height > 0:
                    capabilities.resolutions.append((width, height))
                
                if fps > 0:
                    capabilities.fps_ranges.append((fps, fps))
                
                # Get codec information
                fourcc = cap.get(cv2.CAP_PROP_FOURCC)
                if fourcc:
                    codec_name = self._fourcc_to_string(fourcc)
                    capabilities.supported_codecs.append(codec_name)
                
                # Determine protocol from URL
                if stream_url.startswith('rtsp://'):
                    capabilities.protocols.append('RTSP')
                elif stream_url.startswith('http://'):
                    capabilities.protocols.append('HTTP')
                elif stream_url.startswith('https://'):
                    capabilities.protocols.append('HTTPS')
                
                cap.release()
                
        except Exception as e:
            logger.error(f"Error analyzing stream capabilities: {str(e)}")
        
        return capabilities
    
    async def test_camera_connection_comprehensive(
        self,
        ip_address: str,
        manufacturer: str,
        connection_type: str,
        port: int,
        stream_path: str,
        credentials: Dict[str, str],
        model: str = None
    ) -> ConnectionTestResult:
        """Comprehensive camera connection test with manufacturer integration"""
        
        start_time = time.time()
        
        # Step 1: Basic connectivity test
        connectivity = await self.test_basic_connectivity(ip_address)
        
        if not connectivity.success:
            return ConnectionTestResult(
                success=False,
                ip_address=ip_address,
                connectivity=connectivity,
                error_message=connectivity.error_message,
                suggestions=self._get_connectivity_suggestions(ip_address)
            )
        
        # Step 2: Manufacturer validation
        manufacturer_validation = self.manufacturer_db.validate_configuration(
            manufacturer, connection_type, stream_path
        )
        
        # Step 3: Build URLs for testing
        base_url = f"{connection_type}://{ip_address}:{port}"
        stream_url = f"{connection_type}://{ip_address}:{port}{stream_path}"
        
        # Add authentication to stream URL if provided
        username = credentials.get('username')
        password = credentials.get('password')
        if username and password:
            if connection_type.startswith('rtsp'):
                stream_url = f"{connection_type}://{username}:{password}@{ip_address}:{port}{stream_path}"
        
        # Step 4: Authentication test (for HTTP-based protocols)
        auth_result = None
        if connection_type in ['http', 'https']:
            auth_result = await self.test_authentication(base_url, credentials)
            
            if not auth_result.success:
                return ConnectionTestResult(
                    success=False,
                    ip_address=ip_address,
                    connectivity=connectivity,
                    authentication=auth_result,
                    error_message=auth_result.error_message,
                    suggestions=self._get_auth_suggestions(manufacturer)
                )
        
        # Step 5: Stream accessibility test with retry logic for Reolink
        stream_test = await self._test_stream_with_retries(
            ip_address, manufacturer, connection_type, port, stream_path, credentials
        )
        
        if not stream_test.success:
            return ConnectionTestResult(
                success=False,
                ip_address=ip_address,
                connectivity=connectivity,
                authentication=auth_result,
                stream_test=stream_test,
                error_message=stream_test.error_message,
                suggestions=self._get_stream_suggestions(manufacturer, connection_type, stream_path),
                manufacturer_validation=manufacturer_validation
            )
        
        # Step 6: Get stream capabilities
        capabilities = await self.get_stream_capabilities(stream_url)
        
        # Calculate total response time
        total_time = (time.time() - start_time) * 1000
        
        # Generate warnings based on manufacturer validation
        warnings = []
        if manufacturer_validation.get("warnings"):
            warnings.extend(manufacturer_validation["warnings"])
        
        return ConnectionTestResult(
            success=True,
            ip_address=ip_address,
            connectivity=connectivity,
            authentication=auth_result,
            stream_test=stream_test,
            capabilities=capabilities,
            response_time_ms=total_time,
            warnings=warnings,
            manufacturer_validation=manufacturer_validation
        )
    
    async def _ping_host(self, ip_address: str) -> Optional[float]:
        """Ping host and return response time in milliseconds"""
        try:
            # Use subprocess to ping (works on both Windows and Unix)
            import platform
            
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '1', '-w', '3000', ip_address]
            else:
                cmd = ['ping', '-c', '1', '-W', '3', ip_address]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse ping time from output
                output = result.stdout.lower()
                if 'time=' in output:
                    import re
                    time_match = re.search(r'time[=<]([0-9.]+)', output)
                    if time_match:
                        return float(time_match.group(1))
                return 1.0  # Default if we can't parse time but ping succeeded
            
            return None
            
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            logger.error(f"Ping error: {str(e)}")
            return None
    
    async def _scan_ports(self, ip_address: str, ports: List[int]) -> List[int]:
        """Scan list of ports and return open ones"""
        open_ports = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip_address, port))
                sock.close()
                
                if result == 0:
                    open_ports.append(port)
                    
            except Exception:
                continue
        
        return open_ports
    
    def _fourcc_to_string(self, fourcc: float) -> str:
        """Convert OpenCV FOURCC to string"""
        try:
            fourcc_int = int(fourcc)
            return "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
        except:
            return "Unknown"
    
    def _get_connectivity_suggestions(self, ip_address: str) -> List[str]:
        """Get suggestions for connectivity issues"""
        return [
            "Check if camera is powered on and connected to network",
            "Verify IP address is correct and camera is on same network segment",
            "Check firewall settings that might block communication",
            "Try pinging the camera manually from command line",
            f"Ensure {ip_address} is not conflicting with another device"
        ]
    
    def _get_auth_suggestions(self, manufacturer: str) -> List[str]:
        """Get suggestions for authentication issues"""
        manufacturer_config = self.manufacturer_db.get_manufacturer_config(manufacturer)
        suggestions = [
            "Verify username and password are correct",
            "Check if camera requires initial setup through web interface"
        ]
        
        if manufacturer_config:
            default_username = manufacturer_config.default_username
            suggestions.append(f"Try default username '{default_username}' for {manufacturer_config.name}")
            
            if manufacturer.lower() in ['hikvision', 'dahua']:
                suggestions.append("Some cameras require admin activation before use")
        
        return suggestions
    
    def _get_stream_suggestions(
        self,
        manufacturer: str,
        connection_type: str,
        stream_path: str
    ) -> List[str]:
        """Get suggestions for stream access issues"""
        manufacturer_config = self.manufacturer_db.get_manufacturer_config(manufacturer)
        suggestions = [
            "Check if stream path is correct for your camera model",
            "Try using main stream instead of sub stream or vice versa",
            "Verify camera supports the selected protocol"
        ]
        
        if manufacturer_config:
            suggested_path = self.manufacturer_db.get_stream_path(
                manufacturer, connection_type, "main"
            )
            if suggested_path != stream_path:
                suggestions.append(f"Try using recommended path: {suggested_path}")
            
            # Add manufacturer-specific suggestions
            if manufacturer.lower() == 'reolink':
                suggestions.append("Ensure camera firmware is up to date")
            elif manufacturer.lower() == 'hikvision':
                suggestions.append("Check if RTSP is enabled in camera settings")
            elif manufacturer.lower() == 'dahua':
                suggestions.append("Verify channel number in stream path")
        
        return suggestions
    
    async def _test_stream_with_retries(
        self,
        ip_address: str,
        manufacturer: str,
        connection_type: str,
        port: int,
        stream_path: str,
        credentials: Dict[str, str]
    ) -> StreamTestResult:
        """Test stream with retries and manufacturer-specific configurations"""
        
        # Build primary stream URL
        username = credentials.get('username')
        password = credentials.get('password')
        
        if username and password and connection_type.startswith('rtsp'):
            stream_url = f"{connection_type}://{username}:{password}@{ip_address}:{port}{stream_path}"
        else:
            stream_url = f"{connection_type}://{ip_address}:{port}{stream_path}"
        
        # For Reolink cameras, try multiple configurations
        if manufacturer.lower() == 'reolink':
            test_configurations = [
                # Primary configuration
                {
                    'url': stream_url,
                    'timeout': 30,
                    'description': 'Primary RTSP stream'
                },
                # Try RTSPS port (322)
                {
                    'url': f"{connection_type}://{username}:{password}@{ip_address}:322{stream_path}" if username and password else f"{connection_type}://{ip_address}:322{stream_path}",
                    'timeout': 30,
                    'description': 'RTSPS port 322'
                },
                # Try alternative stream paths
                {
                    'url': f"{connection_type}://{username}:{password}@{ip_address}:{port}/live" if username and password else f"{connection_type}://{ip_address}:{port}/live",
                    'timeout': 30,
                    'description': 'Alternative /live path'
                },
                {
                    'url': f"{connection_type}://{username}:{password}@{ip_address}:{port}/Preview_01_main" if username and password else f"{connection_type}://{ip_address}:{port}/Preview_01_main",
                    'timeout': 30,
                    'description': 'Alternative Preview path'
                }
            ]
            
            # Also try HTTPS streaming as fallback
            if connection_type == 'rtsp':
                https_url = f"https://{ip_address}/cgi-bin/api.cgi?cmd=Snap&channel=0"
                test_configurations.append({
                    'url': https_url,
                    'timeout': 15,
                    'description': 'HTTPS snapshot fallback'
                })
        else:
            # Standard configuration for other manufacturers
            test_configurations = [
                {
                    'url': stream_url,
                    'timeout': self.rtsp_timeout_seconds,
                    'description': 'Standard stream test'
                }
            ]
        
        last_error = None
        
        # Try each configuration
        for config in test_configurations:
            try:
                logger.info(f"Testing {config['description']}: {config['url']}")
                
                # Test HTTPS snapshot differently
                if config['url'].startswith('https://') and 'Snap' in config['url']:
                    result = await self._test_https_snapshot(config['url'], credentials, config['timeout'])
                else:
                    result = await self.test_stream_access(config['url'], config['timeout'])
                
                if result.success:
                    logger.info(f"Stream test successful with {config['description']}")
                    return result
                else:
                    last_error = result.error_message
                    logger.warning(f"{config['description']} failed: {last_error}")
                    
            except Exception as e:
                last_error = f"Exception in {config['description']}: {str(e)}"
                logger.error(last_error)
                continue
        
        # All configurations failed
        return StreamTestResult(
            success=False,
            stream_url=stream_url,
            error_message=f"All stream configurations failed. Last error: {last_error}",
            accessible=False
        )
    
    async def _test_https_snapshot(
        self,
        snapshot_url: str,
        credentials: Dict[str, str],
        timeout: int
    ) -> StreamTestResult:
        """Test HTTPS snapshot capability as streaming fallback"""
        try:
            username = credentials.get('username', 'admin')
            password = credentials.get('password', '')
            
            start_time = time.time()
            
            response = requests.get(
                snapshot_url,
                auth=HTTPBasicAuth(username, password),
                timeout=timeout,
                verify=False
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                return StreamTestResult(
                    success=True,
                    stream_url=snapshot_url,
                    response_time_ms=response_time,
                    accessible=True,
                    codec_info="HTTPS_SNAPSHOT"
                )
            else:
                return StreamTestResult(
                    success=False,
                    stream_url=snapshot_url,
                    response_time_ms=response_time,
                    error_message=f"HTTPS snapshot failed: HTTP {response.status_code}",
                    accessible=False
                )
                
        except Exception as e:
            return StreamTestResult(
                success=False,
                stream_url=snapshot_url,
                error_message=f"HTTPS snapshot error: {str(e)}",
                accessible=False
            )