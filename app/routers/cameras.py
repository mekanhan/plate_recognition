
# app/routers/cameras.py
# Camera management API endpoints for centralized architecture
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import asyncio
import json
import io
import ipaddress
import socket

from app.services.multi_camera_service import MultiCameraService
from app.services.camera_registry_service import CameraRegistryService, CameraConflictException
from app.services.location_service import LocationService
from app.services.gpu_resource_manager import GPUResourceManager
from app.services.multi_stream_processor import MultiStreamProcessor
from app.services.manufacturer_database_service import ManufacturerDatabaseService
from app.services.connection_test_service import ConnectionTestService
from app.services.stream_preview_service import StreamPreviewService
from app.services.onvif_discovery_service import ONVIFDiscoveryService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()
class CameraConnectionTestRequest(BaseModel):
    connection_type: str = "rtsp"  # rtsp, http, https, onvif
    ip_address: str
    port: str = ""
    username: str = "admin"
    password: str = ""
    stream_path: str = ""

@router.post("/test-connection", response_model=Dict[str, Any])
async def test_camera_connection(
    test_data: CameraConnectionTestRequest
):
    """Test connection to a camera using provided parameters."""
    import requests
    from app.services.camera_service import CameraService
    try:
        if test_data.connection_type == "rtsp":
            # Build RTSP URL with proper format
            url = f"rtsp://{test_data.username}:{test_data.password}@{test_data.ip_address}"
            if test_data.port:
                url += f":{test_data.port}"
            if test_data.stream_path:
                url += test_data.stream_path if test_data.stream_path.startswith('/') else f"/{test_data.stream_path}"
            
            # Use improved test method with timeout and detailed feedback
            test_result = CameraService.test_ip_camera(
                ip_address=test_data.ip_address,
                username=test_data.username,
                password=test_data.password,
                timeout=10  # 10 second timeout
            )
            
            return {
                "success": test_result["success"],
                "detail": test_result["message"],
                "url": url,
                "details": test_result.get("details", {}),
                "connection_info": {
                    "protocol": "RTSP",
                    "timeout_used": "10 seconds"
                }
            }
        elif test_data.connection_type in ["http", "https"]:
            scheme = test_data.connection_type
            url = f"{scheme}://{test_data.ip_address}"
            if test_data.port:
                url += f":{test_data.port}"
            try:
                resp = requests.get(url, auth=(test_data.username, test_data.password), timeout=5, verify=False)
                if resp.status_code == 200:
                    return {"success": True, "detail": f"HTTP(S) connection successful to {url}"}
                elif resp.status_code == 401:
                    return {"success": False, "detail": f"Authentication failed for {url}"}
                else:
                    return {"success": False, "detail": f"HTTP(S) connection returned status {resp.status_code} for {url}"}
            except Exception as e:
                return {"success": False, "detail": f"HTTP(S) connection error: {str(e)}"}
        elif test_data.connection_type == "onvif":
            # Placeholder for ONVIF connection test
            return {"success": False, "detail": "ONVIF test not implemented yet."}
        else:
            return {"success": False, "detail": "Unknown connection type."}
    except Exception as e:
        return {"success": False, "detail": str(e)}

# Enhanced connection testing with manufacturer database
class EnhancedConnectionTestRequest(BaseModel):
    ip_address: str
    manufacturer: str = "generic"
    model: str = ""
    connection_type: str = "rtsp"
    port: Optional[int] = None
    stream_path: Optional[str] = None
    username: str = "admin"
    password: str = ""
    test_streams: bool = True
    detect_capabilities: bool = True

@router.post("/test-connection-enhanced", response_model=Dict[str, Any])
async def test_camera_connection_enhanced(
    test_data: EnhancedConnectionTestRequest
):
    """Enhanced connection test with manufacturer database integration."""
    import requests
    import asyncio
    from app.services.camera_service import CameraService
    
    try:
        # Get manufacturer configuration
        manufacturer_config = manufacturer_db_service.get_manufacturer_config(test_data.manufacturer)
        
        # Auto-populate missing values from manufacturer database
        if not test_data.port:
            test_data.port = manufacturer_db_service.get_default_port(test_data.manufacturer, test_data.connection_type)
        
        if not test_data.stream_path:
            test_data.stream_path = manufacturer_db_service.get_stream_path(test_data.manufacturer, test_data.connection_type)
        
        # Build connection URL
        url = manufacturer_db_service.build_stream_url(
            test_data.manufacturer,
            test_data.connection_type,
            test_data.ip_address,
            test_data.port,
            test_data.stream_path,
            test_data.username,
            test_data.password
        )
        
        result = {
            "success": False,
            "url": url,
            "manufacturer": manufacturer_config.name if manufacturer_config else "Generic",
            "connection_type": test_data.connection_type,
            "port": test_data.port,
            "stream_path": test_data.stream_path,
            "tests_performed": [],
            "capabilities": [],
            "suggested_streams": [],
            "warnings": []
        }
        
        # Test 1: Basic connectivity (ping)
        import subprocess
        try:
            ping_result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", test_data.ip_address], 
                capture_output=True, text=True, timeout=5
            )
            ping_success = ping_result.returncode == 0
            result["tests_performed"].append({
                "test": "ping",
                "success": ping_success,
                "detail": "IP is reachable" if ping_success else "IP is not reachable"
            })
        except Exception as e:
            result["tests_performed"].append({
                "test": "ping",
                "success": False,
                "detail": f"Ping test failed: {str(e)}"
            })
        
        # Test 2: Port connectivity
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                port_result = sock.connect_ex((test_data.ip_address, test_data.port))
                port_success = port_result == 0
                result["tests_performed"].append({
                    "test": "port",
                    "success": port_success,
                    "detail": f"Port {test_data.port} is {'open' if port_success else 'closed'}"
                })
        except Exception as e:
            result["tests_performed"].append({
                "test": "port",
                "success": False,
                "detail": f"Port test failed: {str(e)}"
            })
        
        # Test 3: Authentication and stream access
        if test_data.connection_type == "rtsp":
            try:
                # Use ffprobe to test RTSP stream
                import subprocess
                ffprobe_cmd = [
                    "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams",
                    "-rtsp_transport", "tcp", "-i", url
                ]
                ffprobe_result = subprocess.run(
                    ffprobe_cmd, capture_output=True, text=True, timeout=10
                )
                stream_success = ffprobe_result.returncode == 0
                
                if stream_success:
                    try:
                        import json
                        stream_info = json.loads(ffprobe_result.stdout)
                        streams = stream_info.get("streams", [])
                        
                        result["tests_performed"].append({
                            "test": "rtsp_stream",
                            "success": True,
                            "detail": f"RTSP stream accessible, found {len(streams)} streams"
                        })
                        
                        # Extract stream capabilities
                        for stream in streams:
                            if stream.get("codec_type") == "video":
                                result["capabilities"].append({
                                    "type": "video",
                                    "codec": stream.get("codec_name", "unknown"),
                                    "resolution": f"{stream.get('width', 0)}x{stream.get('height', 0)}",
                                    "fps": stream.get("r_frame_rate", "unknown")
                                })
                            elif stream.get("codec_type") == "audio":
                                result["capabilities"].append({
                                    "type": "audio",
                                    "codec": stream.get("codec_name", "unknown"),
                                    "channels": stream.get("channels", "unknown")
                                })
                    except json.JSONDecodeError:
                        result["tests_performed"].append({
                            "test": "rtsp_stream",
                            "success": True,
                            "detail": "RTSP stream accessible but could not parse stream info"
                        })
                else:
                    result["tests_performed"].append({
                        "test": "rtsp_stream",
                        "success": False,
                        "detail": f"RTSP stream failed: {ffprobe_result.stderr}"
                    })
            except subprocess.TimeoutExpired:
                result["tests_performed"].append({
                    "test": "rtsp_stream",
                    "success": False,
                    "detail": "RTSP stream test timed out"
                })
            except Exception as e:
                result["tests_performed"].append({
                    "test": "rtsp_stream",
                    "success": False,
                    "detail": f"RTSP stream test failed: {str(e)}"
                })
        
        elif test_data.connection_type in ["http", "https"]:
            try:
                http_url = f"{test_data.connection_type}://{test_data.ip_address}:{test_data.port}{test_data.stream_path}"
                response = requests.get(
                    http_url, 
                    auth=(test_data.username, test_data.password),
                    timeout=10,
                    verify=False
                )
                
                if response.status_code == 200:
                    result["tests_performed"].append({
                        "test": "http_stream",
                        "success": True,
                        "detail": f"HTTP stream accessible, content-type: {response.headers.get('content-type', 'unknown')}"
                    })
                    
                    # Check if it's a video stream
                    content_type = response.headers.get('content-type', '')
                    if 'video' in content_type or 'image' in content_type:
                        result["capabilities"].append({
                            "type": "video",
                            "format": content_type,
                            "protocol": test_data.connection_type.upper()
                        })
                else:
                    result["tests_performed"].append({
                        "test": "http_stream",
                        "success": False,
                        "detail": f"HTTP stream failed with status {response.status_code}"
                    })
            except Exception as e:
                result["tests_performed"].append({
                    "test": "http_stream",
                    "success": False,
                    "detail": f"HTTP stream test failed: {str(e)}"
                })
        
        # Get suggested alternative streams
        if test_data.test_streams:
            suggested_paths = manufacturer_db_service.get_suggested_stream_paths(
                test_data.manufacturer, test_data.connection_type
            )
            result["suggested_streams"] = [
                {
                    "path": path,
                    "url": manufacturer_db_service.build_stream_url(
                        test_data.manufacturer, test_data.connection_type,
                        test_data.ip_address, test_data.port, path,
                        test_data.username, test_data.password
                    )
                }
                for path in suggested_paths[:5]  # Limit to 5 suggestions
            ]
        
        # Validate configuration
        validation = manufacturer_db_service.validate_configuration(
            test_data.manufacturer, test_data.connection_type, test_data.stream_path
        )
        result["warnings"] = validation.get("warnings", [])
        
        # Overall success if most tests pass
        successful_tests = sum(1 for test in result["tests_performed"] if test["success"])
        total_tests = len(result["tests_performed"])
        result["success"] = successful_tests >= max(1, total_tests // 2)
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced connection test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "detail": "Connection test failed due to internal error"
        }

# Manufacturer database endpoints
@router.get("/manufacturers", response_model=List[Dict[str, str]])
async def get_manufacturers():
    """Get list of supported camera manufacturers."""
    return manufacturer_db_service.get_manufacturer_list()

@router.get("/manufacturers/{manufacturer_key}/models", response_model=List[str])
async def get_manufacturer_models(manufacturer_key: str):
    """Get common models for a manufacturer."""
    return manufacturer_db_service.get_common_models(manufacturer_key)

@router.get("/manufacturers/{manufacturer_key}/config", response_model=Dict[str, Any])
async def get_manufacturer_config(manufacturer_key: str):
    """Get manufacturer configuration details."""
    config = manufacturer_db_service.get_manufacturer_config(manufacturer_key)
    if not config:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    return {
        "name": config.name,
        "common_models": config.common_models,
        "default_ports": config.default_ports,
        "stream_paths": config.stream_paths,
        "default_auth": config.default_auth,
        "default_username": config.default_username,
        "supported_codecs": config.supported_codecs,
        "capabilities": config.capabilities
    }

@router.get("/manufacturers/{manufacturer_key}/stream-paths", response_model=List[str])
async def get_manufacturer_stream_paths(
    manufacturer_key: str,
    connection_type: str = Query("rtsp", description="Connection type (rtsp, http, https)")
):
    """Get suggested stream paths for manufacturer and connection type."""
    return manufacturer_db_service.get_suggested_stream_paths(manufacturer_key, connection_type)

@router.post("/manufacturers/suggest", response_model=List[Dict[str, str]])
async def suggest_manufacturers(query: Dict[str, str]):
    """Get manufacturer suggestions based on query."""
    search_query = query.get("query", "")
    return manufacturer_db_service.get_manufacturer_suggestions(search_query)

# Comprehensive connection testing with new service
class ComprehensiveConnectionTestRequest(BaseModel):
    ip_address: str = Field(..., description="Camera IP address")
    manufacturer: str = Field("generic", description="Camera manufacturer")
    model: Optional[str] = Field(None, description="Camera model")
    connection_type: str = Field("rtsp", description="Connection type (rtsp, http, https, onvif)")
    port: Optional[int] = Field(None, description="Port number (auto-detected if not provided)")
    stream_path: Optional[str] = Field(None, description="Stream path (auto-detected if not provided)")
    username: str = Field("admin", description="Username for authentication")
    password: str = Field("", description="Password for authentication")

@router.post("/test-connection-comprehensive", response_model=Dict[str, Any])
async def test_camera_connection_comprehensive(
    test_data: ComprehensiveConnectionTestRequest
):
    """Comprehensive camera connection test using the enhanced ConnectionTestService."""
    try:
        logger.info(f"Starting comprehensive connection test for {test_data.ip_address}")
        
        # Auto-populate missing values from manufacturer database
        if not test_data.port:
            test_data.port = manufacturer_db_service.get_default_port(
                test_data.manufacturer, test_data.connection_type
            )
        
        if not test_data.stream_path:
            test_data.stream_path = manufacturer_db_service.get_stream_path(
                test_data.manufacturer, test_data.connection_type, "main"
            )
        
        # Perform comprehensive connection test
        result = await connection_test_service.test_camera_connection_comprehensive(
            ip_address=test_data.ip_address,
            manufacturer=test_data.manufacturer,
            connection_type=test_data.connection_type,
            port=test_data.port,
            stream_path=test_data.stream_path,
            credentials={
                "username": test_data.username,
                "password": test_data.password
            },
            model=test_data.model
        )
        
        # Format response for frontend
        response = {
            "success": result.success,
            "ip_address": result.ip_address,
            "response_time_ms": result.response_time_ms,
            "error_message": result.error_message,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
            
            # Connectivity details
            "connectivity": {
                "ping_success": result.connectivity.success,
                "ping_time_ms": result.connectivity.ping_response_time_ms,
                "open_ports": result.connectivity.open_ports,
                "connectivity_error": result.connectivity.error_message
            },
            
            # Authentication details
            "authentication": None,
            
            # Stream test details
            "stream_test": None,
            
            # Capabilities
            "capabilities": None,
            
            # Manufacturer validation
            "manufacturer_validation": result.manufacturer_validation
        }
        
        if result.authentication:
            response["authentication"] = {
                "success": result.authentication.success,
                "auth_method": result.authentication.auth_method,
                "response_code": result.authentication.response_code,
                "response_time_ms": result.authentication.response_time_ms,
                "error_message": result.authentication.error_message
            }
        
        if result.stream_test:
            response["stream_test"] = {
                "success": result.stream_test.success,
                "stream_url": result.stream_test.stream_url,
                "response_time_ms": result.stream_test.response_time_ms,
                "codec_info": result.stream_test.codec_info,
                "resolution": result.stream_test.resolution,
                "fps": result.stream_test.fps,
                "accessible": result.stream_test.accessible,
                "error_message": result.stream_test.error_message
            }
        
        if result.capabilities:
            response["capabilities"] = {
                "supported_codecs": result.capabilities.supported_codecs,
                "resolutions": result.capabilities.resolutions,
                "fps_ranges": result.capabilities.fps_ranges,
                "audio_support": result.capabilities.audio_support,
                "ptz_support": result.capabilities.ptz_support,
                "max_bitrate": result.capabilities.max_bitrate,
                "protocols": result.capabilities.protocols
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Comprehensive connection test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "detail": "Comprehensive connection test failed due to internal error"
        }

# Stream preview endpoints
class PreviewSessionRequest(BaseModel):
    ip_address: str = Field(..., description="Camera IP address")
    manufacturer: str = Field("generic", description="Camera manufacturer")
    connection_type: str = Field("rtsp", description="Connection type")
    port: Optional[int] = Field(None, description="Port number")
    stream_path: Optional[str] = Field(None, description="Stream path")
    username: str = Field("admin", description="Username")
    password: str = Field("", description="Password")

@router.post("/preview/start", response_model=Dict[str, Any])
async def start_preview_session(preview_request: PreviewSessionRequest):
    """Start a new camera preview session"""
    try:
        # Auto-populate missing values
        if not preview_request.port:
            preview_request.port = manufacturer_db_service.get_default_port(
                preview_request.manufacturer, preview_request.connection_type
            )
        
        if not preview_request.stream_path:
            preview_request.stream_path = manufacturer_db_service.get_stream_path(
                preview_request.manufacturer, preview_request.connection_type, "main"
            )
        
        # Create camera config
        camera_config = {
            "ip_address": preview_request.ip_address,
            "manufacturer": preview_request.manufacturer,
            "connection_type": preview_request.connection_type,
            "port": preview_request.port,
            "stream_path": preview_request.stream_path,
            "username": preview_request.username,
            "password": preview_request.password
        }
        
        # Start preview session
        session = await stream_preview_service.start_preview_session(camera_config)
        
        return {
            "success": True,
            "session_id": session.session_id,
            "stream_url": session.stream_url,
            "created_at": session.created_at.isoformat(),
            "message": "Preview session started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start preview session: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start preview session"
        }

@router.post("/preview/{session_id}/snapshot", response_model=Dict[str, Any])
async def capture_preview_snapshot(
    session_id: str,
    save_to_file: bool = Query(True, description="Save snapshot to file"),
    return_base64: bool = Query(False, description="Return base64 encoded image")
):
    """Capture a snapshot from preview session"""
    try:
        result = await stream_preview_service.capture_snapshot(
            session_id, save_to_file, return_base64
        )
        
        response = {
            "success": result.success,
            "session_id": result.session_id,
            "timestamp": result.timestamp.isoformat(),
            "error_message": result.error_message
        }
        
        if result.success:
            response.update({
                "file_path": result.file_path,
                "frame_info": result.frame_info
            })
            
            if return_base64:
                response["image_data"] = result.snapshot_data.decode('utf-8')
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to capture snapshot: {e}")
        return {
            "success": False,
            "session_id": session_id,
            "error": str(e),
            "message": "Failed to capture snapshot"
        }

@router.get("/preview/{session_id}/live-frame")
async def get_preview_live_frame(session_id: str):
    """Get current live frame from preview session"""
    try:
        frame_data = await stream_preview_service.get_live_frame(session_id)
        
        if frame_data is None:
            raise HTTPException(status_code=404, detail="No frame available")
        
        frame_bytes, timestamp = frame_data
        
        return StreamingResponse(
            io.BytesIO(frame_bytes),
            media_type="image/jpeg",
            headers={
                "X-Timestamp": timestamp.isoformat(),
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview/{session_id}/test-stability", response_model=Dict[str, Any])
async def test_preview_stability(
    session_id: str,
    duration: int = Query(30, ge=10, le=300, description="Test duration in seconds")
):
    """Test stream stability for preview session"""
    try:
        result = await stream_preview_service.test_stream_stability(session_id, duration)
        
        return {
            "success": result.success,
            "session_id": result.session_id,
            "test_duration_seconds": result.test_duration_seconds,
            "frames_captured": result.frames_captured,
            "frames_dropped": result.frames_dropped,
            "average_fps": result.average_fps,
            "stability_score": result.stability_score,
            "error_rate": result.error_rate,
            "quality_metrics": result.quality_metrics,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test stream stability: {e}")
        return {
            "success": False,
            "session_id": session_id,
            "error": str(e),
            "message": "Failed to test stream stability"
        }

@router.delete("/preview/{session_id}", response_model=Dict[str, Any])
async def stop_preview_session(session_id: str):
    """Stop and cleanup preview session"""
    try:
        success = await stream_preview_service.stop_preview_session(session_id)
        
        return {
            "success": success,
            "session_id": session_id,
            "message": "Preview session stopped" if success else "Failed to stop session"
        }
        
    except Exception as e:
        logger.error(f"Failed to stop preview session: {e}")
        return {
            "success": False,
            "session_id": session_id,
            "error": str(e),
            "message": "Failed to stop preview session"
        }

@router.get("/preview/{session_id}/info", response_model=Dict[str, Any])
async def get_preview_session_info(session_id: str):
    """Get information about a preview session"""
    try:
        session_info = await stream_preview_service.get_session_info(session_id)
        
        if session_info is None:
            raise HTTPException(status_code=404, detail="Preview session not found")
        
        return {
            "success": True,
            "session": session_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview/sessions", response_model=Dict[str, Any])
async def list_preview_sessions():
    """List all active preview sessions"""
    try:
        sessions = await stream_preview_service.list_active_sessions()
        
        return {
            "success": True,
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to list preview sessions: {e}")
        return {
            "success": False,
            "error": str(e),
            "sessions": [],
            "total_sessions": 0
        }

# Service instances (will be injected)
multi_camera_service: Optional[MultiCameraService] = None
camera_registry_service: Optional[CameraRegistryService] = None
location_service: Optional[LocationService] = None
gpu_resource_manager: Optional[GPUResourceManager] = None
multi_stream_processor: Optional[MultiStreamProcessor] = None
manufacturer_db_service: ManufacturerDatabaseService = ManufacturerDatabaseService()
connection_test_service: ConnectionTestService = ConnectionTestService()
stream_preview_service: StreamPreviewService = StreamPreviewService()

# Pydantic models for API
class CameraCreateRequest(BaseModel):
    name: str = Field(..., description="Camera name")
    ip_address: str = Field(..., description="Camera IP address")
    location_id: str = Field(..., description="Location ID")
    camera_group_id: Optional[str] = Field(None, description="Camera group ID")
    camera_type: str = Field("ip_camera", description="Camera type")
    manufacturer: Optional[str] = Field(None, description="Camera manufacturer")
    model: Optional[str] = Field(None, description="Camera model")
    username: str = Field("admin", description="Camera username")
    password: str = Field("", description="Camera password")
    resolution_width: int = Field(1920, description="Camera resolution width")
    resolution_height: int = Field(1080, description="Camera resolution height")
    fps: int = Field(30, description="Camera FPS")
    installation_location: Optional[str] = Field(None, description="Installation location")
    viewing_direction: Optional[str] = Field(None, description="Viewing direction")

class CameraUpdateRequest(BaseModel):
    name: Optional[str] = None
    location_id: Optional[str] = None
    camera_group_id: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[int] = None
    codec: Optional[str] = None
    stream_path: Optional[str] = None
    detection_enabled: Optional[bool] = None
    recording_enabled: Optional[bool] = None
    installation_location: Optional[str] = None
    viewing_direction: Optional[str] = None

class CameraGroupCreateRequest(BaseModel):
    name: str = Field(..., description="Group name")
    location_id: str = Field(..., description="Location ID")
    description: Optional[str] = Field(None, description="Group description")
    purpose: Optional[str] = Field(None, description="Group purpose")
    detection_threshold: float = Field(0.7, description="Detection threshold")
    processing_enabled: bool = Field(True, description="Processing enabled")
    recording_enabled: bool = Field(True, description="Recording enabled")
    alert_enabled: bool = Field(True, description="Alert enabled")

class CameraDiscoveryRequest(BaseModel):
    ip_range: str = Field("192.168.1.0/24", description="IP range to scan")
    port_config: Optional[Dict[str, List[int]]] = Field(None, description="Port configuration for discovery methods")
    methods: Optional[List[str]] = Field(None, description="Discovery methods to use")

# Dependency injection
async def get_multi_camera_service() -> MultiCameraService:
    if multi_camera_service is None:
        raise HTTPException(status_code=503, detail="MultiCameraService not available")
    return multi_camera_service

async def get_camera_registry_service() -> CameraRegistryService:
    if camera_registry_service is None:
        raise HTTPException(status_code=503, detail="CameraRegistryService not available")
    return camera_registry_service

async def get_location_service() -> LocationService:
    if location_service is None:
        raise HTTPException(status_code=503, detail="LocationService not available")
    return location_service

# Camera management endpoints
@router.get("/", response_model=List[Dict[str, Any]])
async def get_cameras(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    group_id: Optional[str] = Query(None, description="Filter by group ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    include_inactive: bool = Query(False, description="Include inactive cameras"),
    limit: int = Query(50, ge=1, le=100, description="Maximum cameras to return"),
    registry: CameraRegistryService = Depends(get_camera_registry_service),
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Get list of cameras with optional filtering"""
    try:
        if location_id:
            cameras = await registry.get_cameras_by_location(location_id, include_inactive)
        elif group_id:
            cameras = await registry.get_cameras_by_group(group_id)
        else:
            cameras = await registry.get_all_cameras(include_inactive)
        
        # Apply status filter
        if status:
            cameras = [c for c in cameras if c.get("status") == status]
        
        # Apply limit
        cameras = cameras[:limit]
        
        return cameras
        
    except Exception as e:
        logger.error(f"Failed to get cameras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Dict[str, str])
async def create_camera(
    camera_data: CameraCreateRequest,
    background_tasks: BackgroundTasks,
    registry: CameraRegistryService = Depends(get_camera_registry_service),
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Create a new camera"""
    try:
        # Register camera in registry
        camera_id = await registry.register_camera(camera_data.dict())
        
        # Add camera to multi-camera service
        await multi_cam.add_camera(camera_data.dict())
        
        # Start camera stream in background
        background_tasks.add_task(multi_cam.start_camera_stream, camera_id)
        
        return {"camera_id": camera_id, "message": "Camera created successfully"}
        
    except CameraConflictException as e:
        # Return 409 Conflict with details about the existing camera
        raise HTTPException(
            status_code=409, 
            detail={
                "message": str(e),
                "conflict_type": "ip_address",
                "existing_camera": {
                    "id": e.existing_camera_id,
                    "name": e.existing_camera_name,
                    "ip_address": e.ip_address
                }
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}", response_model=Dict[str, Any])
async def get_camera(
    camera_id: str,
    include_health: bool = Query(True, description="Include health information"),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get specific camera information"""
    try:
        cameras = await registry.get_all_cameras(include_inactive=True)  # Get all cameras including inactive
        logger.info(f"Found {len(cameras)} cameras in total")
        
        camera = next((c for c in cameras if c["id"] == camera_id), None)
        
        if not camera:
            logger.error(f"Camera {camera_id} not found in {len(cameras)} cameras")
            raise HTTPException(status_code=404, detail="Camera not found")
        
        logger.info(f"Found camera: {camera.get('name', 'Unknown')} ({camera_id})")
        
        if include_health:
            try:
                # Check if the method exists
                if hasattr(registry, 'get_camera_health'):
                    health = await registry.get_camera_health(camera_id)
                    camera["health"] = health
                else:
                    logger.warning(f"get_camera_health method not found in registry")
                    camera["health"] = None
            except Exception as health_error:
                logger.warning(f"Failed to get health for camera {camera_id}: {health_error}")
                camera["health"] = None
        
        return camera
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera {camera_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-ip/{ip_address}", response_model=Dict[str, Any])
async def get_camera_by_ip(
    ip_address: str,
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get camera by IP address"""
    try:
        camera = await registry.get_camera_by_ip(ip_address)
        
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        return camera
        
    except Exception as e:
        logger.error(f"Failed to get camera by IP {ip_address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{camera_id}", response_model=Dict[str, str])
async def update_camera(
    camera_id: str,
    updates: CameraUpdateRequest,
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Update camera configuration"""
    try:
        # Convert request to dict and filter out None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        
        # Update camera in registry
        success = await registry.update_camera(camera_id, update_dict)
        
        if not success:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        return {"camera_id": camera_id, "message": "Camera updated successfully"}
        
    except CameraConflictException as e:
        # Return 409 Conflict with details about the existing camera
        raise HTTPException(
            status_code=409, 
            detail={
                "message": str(e),
                "conflict_type": "ip_address",
                "existing_camera": {
                    "id": e.existing_camera_id,
                    "name": e.existing_camera_name,
                    "ip_address": e.ip_address
                }
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{camera_id}", response_model=Dict[str, str])
async def delete_camera(
    camera_id: str,
    registry: CameraRegistryService = Depends(get_camera_registry_service),
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Delete a camera"""
    try:
        # Stop camera stream
        await multi_cam.stop_camera_stream(camera_id)
        
        # Remove from multi-camera service (this handles database deletion)
        success = await multi_cam.remove_camera(camera_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Unregister from registry (this handles local cleanup only)
        await registry.unregister_camera(camera_id)
        
        return {"camera_id": camera_id, "message": "Camera deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera streaming endpoints
@router.get("/{camera_id}/stream")
async def get_camera_stream(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Get live video stream from camera"""
    try:
        async def generate_frames():
            while True:
                try:
                    frame_data, timestamp = await multi_cam.get_camera_jpeg_frame(camera_id)
                    
                    if frame_data is None:
                        # Return placeholder frame
                        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b'placeholder' + b'\r\n'
                    else:
                        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n'
                    
                    await asyncio.sleep(0.1)  # ~10 FPS for web streaming
                    
                except Exception as e:
                    logger.error(f"Stream error for camera {camera_id}: {e}")
                    break
        
        return StreamingResponse(
            generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Failed to get camera stream {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/live")
async def get_camera_live_stream(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Get live video stream from camera (alias for /stream endpoint)"""
    # Redirect to the actual stream endpoint
    return await get_camera_stream(camera_id, multi_cam)

@router.get("/{camera_id}/snapshot")
async def get_camera_snapshot(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Get single snapshot from camera"""
    try:
        frame_data, timestamp = await multi_cam.get_camera_jpeg_frame(camera_id)
        
        if frame_data is None:
            raise HTTPException(status_code=404, detail="No frame available")
        
        return StreamingResponse(
            io.BytesIO(frame_data),
            media_type="image/jpeg",
            headers={"X-Timestamp": str(timestamp)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera snapshot {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ONVIF Discovery endpoints
@router.post("/discover/onvif")
async def discover_onvif_devices(
    network_range: str = Query("192.168.1.0/24", description="Network range to scan (CIDR notation)")
):
    """Discover ONVIF devices on the network"""
    try:
        onvif_service = ONVIFDiscoveryService()
        devices = await onvif_service.discover_onvif_devices(network_range)
        
        return {
            "success": True,
            "devices_found": len(devices),
            "devices": onvif_service.format_devices_for_ui(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ONVIF discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"ONVIF discovery failed: {str(e)}")

@router.get("/discover/onvif/{ip_address}/profiles")
async def get_onvif_device_profiles(
    ip_address: str,
    port: int = Query(80, description="ONVIF port"),
    username: str = Query(None, description="Username for authentication"),
    password: str = Query(None, description="Password for authentication")
):
    """Get media profiles from an ONVIF device"""
    try:
        onvif_service = ONVIFDiscoveryService()
        
        # Create device object
        from app.services.onvif_discovery_service import ONVIFDevice
        device = ONVIFDevice(ip_address=ip_address, onvif_port=port)
        
        # Get profiles
        profiles = await onvif_service.get_device_profiles(device, username, password)
        
        return {
            "success": True,
            "device": {
                "ip_address": ip_address,
                "onvif_port": port
            },
            "profiles": profiles,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get ONVIF profiles for {ip_address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ONVIF profiles: {str(e)}")

# Debug endpoint for camera service status
@router.get("/{camera_id}/debug", response_model=Dict[str, Any])
async def debug_camera_status(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Debug camera status in MultiCameraService"""
    try:
        available_cameras = list(multi_cam.cameras.keys())
        is_in_service = camera_id in multi_cam.cameras
        has_stream = camera_id in multi_cam.streams
        has_task = camera_id in multi_cam.capture_tasks
        
        debug_info = {
            "camera_id": camera_id,
            "is_in_multi_cam_service": is_in_service,
            "has_stream_info": has_stream,
            "has_capture_task": has_task,
            "total_cameras_in_service": len(available_cameras),
            "available_camera_ids": available_cameras[:5],  # Show first 5 for brevity
            "stream_info": None,
            "camera_config": None
        }
        
        if is_in_service:
            camera = multi_cam.cameras[camera_id]
            debug_info["camera_config"] = {
                "name": camera.name,
                "ip_address": camera.ip_address,
                "port": camera.port,
                "username": camera.username,
                "main_stream_url": camera.main_stream_url,
                "status": camera.status.value if camera.status else "unknown"
            }
            
            # Try to build stream URL
            try:
                stream_url = multi_cam._build_stream_url(camera)
                debug_info["built_stream_url"] = stream_url
            except Exception as e:
                debug_info["stream_url_error"] = str(e)
        
        if has_stream:
            stream_info = multi_cam.streams[camera_id]
            debug_info["stream_info"] = {
                "stream_url": stream_info.stream_url,
                "is_connected": stream_info.is_connected,
                "error_count": stream_info.error_count,
                "frame_count": stream_info.frame_count,
                "last_error": stream_info.last_error
            }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Debug camera status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/test-connection", response_model=Dict[str, Any])
async def test_camera_connection(camera_id: str, multi_cam: MultiCameraService = Depends(get_multi_camera_service)):
    """Test camera RTSP connection with comprehensive diagnostics"""
    try:
        # Import the RTSP tester
        from app.services.rtsp_connection_tester import RTSPConnectionTester
        
        if camera_id not in multi_cam.cameras:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        camera = multi_cam.cameras[camera_id]
        tester = RTSPConnectionTester()
        
        # Extract password from camera (in production, this would be decrypted)
        password = camera.password_hash or ""
        
        # Run comprehensive RTSP test
        result = await tester.test_camera_connection(
            ip_address=camera.ip_address,
            username=camera.username or "admin",
            password=password,
            port=camera.port or 554
        )
        
        # Convert result to response format
        response = {
            "camera_id": camera_id,
            "camera_name": camera.name,
            "connection_successful": result.success,
            "result_code": result.result_code.value,
            "error_message": result.error_message,
            "working_rtsp_url": result.working_url,
            "camera_manufacturer": result.camera_manufacturer,
            "test_duration_seconds": round(result.test_duration, 2),
            "tested_urls_count": len(result.tested_urls) if result.tested_urls else 0,
            "recommended_fixes": result.recommended_fixes or []
        }
        
        # If we found a working URL, suggest updating the camera config
        if result.working_url and result.working_url != multi_cam._build_stream_url(camera):
            response["suggested_update"] = {
                "current_url": multi_cam._build_stream_url(camera),
                "recommended_url": result.working_url,
                "update_needed": True
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Connection test failed for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/quick-test", response_model=Dict[str, Any])
async def quick_camera_test(camera_id: str, multi_cam: MultiCameraService = Depends(get_multi_camera_service)):
    """Quick test of camera stream with multiple Reolink paths"""
    try:
        if camera_id not in multi_cam.cameras:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        camera = multi_cam.cameras[camera_id]
        
        # Test multiple Reolink paths quickly
        import cv2
        import time
        import urllib.parse
        
        test_paths = [
            "/h264Preview_01_main",
            "/h264Preview_01_sub", 
            "/Preview_01_main",
            "/Preview_01_sub",
            "/bcs/channel0_main.bcs",
            "/bcs/channel0_sub.bcs",
            "/live/main",
            "/live/sub",
            "/channel1",
            "/stream1"
        ]
        
        password = camera.password_hash or ""
        encoded_password = urllib.parse.quote(password, safe='')
        
        test_results = []
        working_url = None
        
        for path in test_paths:
            # Test with original password
            url = f"rtsp://{camera.username}:{password}@{camera.ip_address}:{camera.port or 554}{path}"
            can_open, frames_read = test_rtsp_quick(url)
            
            result = {
                "path": path,
                "password_encoded": False,
                "can_open": can_open,
                "frames_read": frames_read,
                "working": frames_read > 0
            }
            test_results.append(result)
            
            if frames_read > 0 and not working_url:
                working_url = url
                break
                
            # If not working, try encoded password
            if not can_open:
                url_encoded = f"rtsp://{camera.username}:{encoded_password}@{camera.ip_address}:{camera.port or 554}{path}"
                can_open_enc, frames_read_enc = test_rtsp_quick(url_encoded)
                
                if frames_read_enc > 0 and not working_url:
                    working_url = url_encoded
                    test_results.append({
                        "path": path,
                        "password_encoded": True,
                        "can_open": can_open_enc,
                        "frames_read": frames_read_enc,
                        "working": True
                    })
                    break
        
        response = {
            "camera_id": camera_id,
            "camera_name": camera.name,
            "total_paths_tested": len([r for r in test_results if not r.get("password_encoded", False)]),
            "working_url_found": working_url is not None,
            "working_url": working_url.replace(password, "***") if working_url else None,
            "test_results": test_results,
            "recommendation": None
        }
        
        if working_url:
            # Extract the working path
            working_path = None
            for result in test_results:
                if result["working"]:
                    working_path = result["path"]
                    break
            
            response["recommendation"] = {
                "action": "update_camera_stream_path",
                "current_path": multi_cam._get_manufacturer_stream_path(camera.manufacturer),
                "recommended_path": working_path,
                "needs_password_encoding": any(r.get("password_encoded") for r in test_results if r["working"])
            }
        else:
            response["recommendation"] = {
                "action": "troubleshoot_camera",
                "issues": [
                    "No RTSP paths returned video frames",
                    "Camera may not be streaming video",
                    "Check camera RTSP settings",
                    "Verify camera is not in maintenance mode"
                ]
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Quick test failed for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def test_rtsp_quick(url: str, timeout: int = 5) -> tuple[bool, int]:
    """Quick RTSP test with OpenCV - returns (can_open, frames_read)"""
    try:
        import cv2
        import time
        
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            return False, 0
        
        frames_read = 0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if ret and frame is not None:
                frames_read += 1
                if frames_read >= 3:  # Got some frames, good enough
                    break
            time.sleep(0.1)
        
        cap.release()
        return True, frames_read
        
    except Exception as e:
        return False, 0

@router.get("/{camera_id}/snapshot")
async def get_camera_snapshot(camera_id: str, multi_cam: MultiCameraService = Depends(get_multi_camera_service)):
    """Get a snapshot from the camera using multiple fallback methods"""
    try:
        from fastapi.responses import Response
        import requests
        import numpy as np
        import cv2
        
        if camera_id not in multi_cam.cameras:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        camera = multi_cam.cameras[camera_id]
        
        # Method 1: Try to get frame from MultiCameraService (if available)
        frame, timestamp = await multi_cam.get_camera_frame(camera_id)
        if frame is not None:
            logger.info(f"Got frame from MultiCameraService for camera {camera_id}")
            _, jpeg = cv2.imencode('.jpg', frame)
            return Response(content=jpeg.tobytes(), media_type="image/jpeg")
        
        # Method 2: Try HTTP snapshot from Reolink camera
        snapshot_urls = [
            f"http://{camera.ip_address}/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user={camera.username}&password={camera.password_hash}",
            f"http://{camera.ip_address}/tmpfs/snap.jpg",
            f"http://{camera.ip_address}/snapshot.jpg",
            f"http://{camera.ip_address}/jpg/image.jpg",
        ]
        
        for snapshot_url in snapshot_urls:
            try:
                response = requests.get(snapshot_url, timeout=3, auth=(camera.username, camera.password_hash))
                if response.status_code == 200 and len(response.content) > 1000:  # Reasonable image size
                    content_type = response.headers.get('content-type', '').lower()
                    if 'image' in content_type or response.content.startswith(b'\xff\xd8'):  # JPEG marker
                        logger.info(f"Got HTTP snapshot from {snapshot_url}")
                        return Response(content=response.content, media_type="image/jpeg")
            except Exception as e:
                logger.debug(f"HTTP snapshot failed for {snapshot_url}: {e}")
                continue
        
        # Method 3: Try direct RTSP frame capture (quick attempt)
        rtsp_url = multi_cam._build_stream_url(camera)
        try:
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
            
            if cap.isOpened():
                for i in range(10):  # Try multiple frame reads
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        logger.info(f"Got direct RTSP frame for camera {camera_id}")
                        cap.release()
                        _, jpeg = cv2.imencode('.jpg', frame)
                        return Response(content=jpeg.tobytes(), media_type="image/jpeg")
                    
            cap.release()
        except Exception as e:
            logger.debug(f"Direct RTSP capture failed: {e}")
        
        # Method 4: Create informative placeholder image
        logger.warning(f"All snapshot methods failed for camera {camera_id}, creating placeholder")
        
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img.fill(40)  # Dark background
        
        # Add camera information
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (200, 200, 200)
        thickness = 2
        
        # Get stream info from debug
        stream_info = multi_cam.streams.get(camera_id)
        
        text_lines = [
            f"Camera: {camera.name}",
            f"IP: {camera.ip_address}",
            f"Status: {camera.status.value.upper()}",
            "",
            "RTSP Stream Info:",
            f"URL: {multi_cam._build_stream_url(camera)[-30:]}...",  # Last 30 chars
            f"Connected: {'Yes' if stream_info and stream_info.is_connected else 'No'}",
            f"Frame Count: {stream_info.frame_count if stream_info else 0}",
            f"Error Count: {stream_info.error_count if stream_info else 0}",
            "",
            "Video streaming via RTSP works in VLC",
            "OpenCV compatibility issue detected",
            "Check camera RTSP settings or try",
            "different stream format"
        ]
        
        y_start = 30
        line_height = 30
        
        for i, line in enumerate(text_lines):
            if line:  # Skip empty lines
                y = y_start + (i * line_height)
                if y < 460:  # Keep within image bounds
                    cv2.putText(img, line, (20, y), font, font_scale, color, thickness)
        
        # Convert to JPEG
        _, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        
        return Response(content=jpeg.tobytes(), media_type="image/jpeg")
        
    except Exception as e:
        logger.error(f"Failed to get camera snapshot {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera control endpoints
@router.post("/{camera_id}/start", response_model=Dict[str, str])
async def start_camera_stream(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Start camera stream"""
    try:
        logger.info(f"Starting camera stream for camera_id: {camera_id}")
        
        # Check if camera exists in multi-camera service
        available_cameras = list(multi_cam.cameras.keys())
        logger.info(f"Available cameras in multi_cam service: {available_cameras}")
        
        if camera_id not in multi_cam.cameras:
            logger.error(f"Camera {camera_id} not found in MultiCameraService. Available: {available_cameras}")
            
            # Try to reload cameras from database
            await multi_cam._load_cameras_from_database()
            available_cameras = list(multi_cam.cameras.keys())
            logger.info(f"After reload, available cameras: {available_cameras}")
            
            if camera_id not in multi_cam.cameras:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Camera {camera_id} not found. Available cameras: {len(available_cameras)}"
                )
        
        success = await multi_cam.start_camera_stream(camera_id)
        
        if not success:
            logger.error(f"start_camera_stream returned False for camera {camera_id}")
            raise HTTPException(status_code=400, detail="Failed to start camera stream - check camera configuration")
        
        logger.info(f"Successfully started camera stream for {camera_id}")
        return {"camera_id": camera_id, "message": "Camera stream started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception starting camera stream {camera_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/stop", response_model=Dict[str, str])
async def stop_camera_stream(
    camera_id: str,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Stop camera stream"""
    try:
        success = await multi_cam.stop_camera_stream(camera_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop camera stream")
        
        return {"camera_id": camera_id, "message": "Camera stream stopped"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop camera stream {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera discovery endpoints
@router.post("/discover", response_model=List[Dict[str, Any]])
async def discover_cameras(
    discovery_request: CameraDiscoveryRequest,
    multi_cam: MultiCameraService = Depends(get_multi_camera_service)
):
    """Discover cameras on network"""
    try:
        discovered_cameras = await multi_cam.discover_cameras_on_network(
            discovery_request.ip_range,
            port_config=discovery_request.port_config
        )
        
        return discovered_cameras
        
    except Exception as e:
        logger.error(f"Failed to discover cameras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera group management
@router.get("/groups/", response_model=List[Dict[str, Any]])
async def get_camera_groups(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get camera groups"""
    try:
        # TODO: Implement get_groups in registry service
        return []
        
    except Exception as e:
        logger.error(f"Failed to get camera groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/", response_model=Dict[str, str])
async def create_camera_group(
    group_data: CameraGroupCreateRequest,
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Create camera group"""
    try:
        group_id = await registry.create_camera_group(group_data.dict())
        
        return {"group_id": group_id, "message": "Camera group created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create camera group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/assign-group", response_model=Dict[str, str])
async def assign_camera_to_group(
    camera_id: str,
    group_id: str = Query(..., description="Group ID"),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Assign camera to group"""
    try:
        success = await registry.assign_camera_to_group(camera_id, group_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to assign camera to group")
        
        return {"camera_id": camera_id, "group_id": group_id, "message": "Camera assigned to group"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign camera to group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Camera health and statistics
@router.get("/{camera_id}/health", response_model=Dict[str, Any])
async def get_camera_health(
    camera_id: str,
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get camera health information"""
    try:
        health = await registry.get_camera_health(camera_id)
        
        if not health:
            raise HTTPException(status_code=404, detail="Camera health not found")
        
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera health {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/processing-queue", response_model=List[Dict[str, Any]])
async def get_camera_processing_queue(
    camera_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum queue items"),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get camera processing queue"""
    try:
        queue = await registry.get_camera_processing_queue(camera_id, limit)
        
        return queue
        
    except Exception as e:
        logger.error(f"Failed to get processing queue for {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System statistics
@router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_camera_system_statistics(
    multi_cam: MultiCameraService = Depends(get_multi_camera_service),
    registry: CameraRegistryService = Depends(get_camera_registry_service)
):
    """Get overall camera system statistics"""
    try:
        multi_cam_stats = await multi_cam.get_system_stats()
        registry_stats = await registry.get_registry_statistics()
        
        combined_stats = {
            **multi_cam_stats,
            **registry_stats,
            "service": "centralized_camera_system",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return combined_stats
        
    except Exception as e:
        logger.error(f"Failed to get camera system statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# GPU Resource Management endpoints
@router.get("/gpu/statistics", response_model=Dict[str, Any])
async def get_gpu_statistics():
    """Get GPU resource statistics"""
    try:
        if not gpu_resource_manager:
            raise HTTPException(status_code=503, detail="GPU resource manager not available")
        
        stats = gpu_resource_manager.get_gpu_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get GPU statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing/statistics", response_model=Dict[str, Any])
async def get_processing_statistics():
    """Get multi-stream processing statistics"""
    try:
        if not multi_stream_processor:
            raise HTTPException(status_code=503, detail="Multi-stream processor not available")
        
        stats = await multi_stream_processor.get_stream_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get processing statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/processing/statistics", response_model=Dict[str, Any])
async def get_camera_processing_statistics(camera_id: str):
    """Get processing statistics for a specific camera"""
    try:
        if not multi_stream_processor:
            raise HTTPException(status_code=503, detail="Multi-stream processor not available")
        
        stats = await multi_stream_processor.get_stream_stats(camera_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Camera processing statistics not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera processing statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Multi-stream processing control endpoints
@router.post("/{camera_id}/processing/start", response_model=Dict[str, str])
async def start_camera_processing(
    camera_id: str,
    priority: Optional[str] = Query("normal", description="Processing priority: low, normal, high, critical")
):
    """Start processing frames from camera"""
    try:
        if not multi_stream_processor:
            raise HTTPException(status_code=503, detail="Multi-stream processor not available")
        
        # Convert priority string to Priority enum
        from app.models import Priority
        priority_map = {
            "low": Priority.LOW,
            "normal": Priority.NORMAL,
            "high": Priority.HIGH,
            "critical": Priority.CRITICAL
        }
        
        priority_enum = priority_map.get(priority.lower(), Priority.NORMAL)
        
        success = await multi_stream_processor.start_stream_processing(camera_id, priority_enum)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start camera processing")
        
        return {"camera_id": camera_id, "message": "Camera processing started", "priority": priority}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start camera processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/processing/stop", response_model=Dict[str, str])
async def stop_camera_processing(camera_id: str):
    """Stop processing frames from camera"""
    try:
        if not multi_stream_processor:
            raise HTTPException(status_code=503, detail="Multi-stream processor not available")
        
        success = await multi_stream_processor.stop_stream_processing(camera_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop camera processing")
        
        return {"camera_id": camera_id, "message": "Camera processing stopped"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop camera processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/processing/priority", response_model=Dict[str, str])
async def set_camera_processing_priority(
    camera_id: str,
    priority: str = Query(..., description="Processing priority: low, normal, high, critical")
):
    """Set processing priority for camera"""
    try:
        if not multi_stream_processor:
            raise HTTPException(status_code=503, detail="Multi-stream processor not available")
        
        # Convert priority string to Priority enum
        from app.models import Priority
        priority_map = {
            "low": Priority.LOW,
            "normal": Priority.NORMAL,
            "high": Priority.HIGH,
            "critical": Priority.CRITICAL
        }
        
        priority_enum = priority_map.get(priority.lower())
        if not priority_enum:
            raise HTTPException(status_code=400, detail="Invalid priority level")
        
        success = await multi_stream_processor.set_stream_priority(camera_id, priority_enum)
        
        if not success:
            raise HTTPException(status_code=404, detail="Camera not found or not processing")
        
        return {"camera_id": camera_id, "message": "Priority updated", "priority": priority}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set camera processing priority: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Direct frame processing endpoint
@router.post("/{camera_id}/process-frame", response_model=Dict[str, Any])
async def process_frame_direct(
    camera_id: str,
    background_tasks: BackgroundTasks
):
    """Process a single frame directly from camera"""
    try:
        if not multi_stream_processor:
            raise HTTPException(status_code=503, detail="Multi-stream processor not available")
        
        if not multi_camera_service:
            raise HTTPException(status_code=503, detail="Multi-camera service not available")
        
        # Get current frame from camera
        frame, timestamp = await multi_camera_service.get_camera_frame(camera_id)
        
        if frame is None:
            raise HTTPException(status_code=404, detail="No frame available from camera")
        
        # Process frame directly
        detections = await multi_stream_processor.process_frame_direct(camera_id, frame)
        
        return {
            "camera_id": camera_id,
            "timestamp": timestamp,
            "detections": detections,
            "processing_mode": "direct"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process frame directly: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions for dependency injection
def get_gpu_resource_manager():
    if not gpu_resource_manager:
        raise HTTPException(status_code=503, detail="GPU resource manager not available")
    return gpu_resource_manager

def get_multi_stream_processor():
    if not multi_stream_processor:
        raise HTTPException(status_code=503, detail="Multi-stream processor not available")
    return multi_stream_processor

# ========================================
# DISCOVERY ENDPOINTS
# ========================================

class NetworkScanRequest(BaseModel):
    ip_range: str = Field(..., description="IP range to scan (e.g., 192.168.1.0/24)")
    timeout: int = Field(default=2, description="Timeout in seconds for each IP")
    ports: List[int] = Field(default=[80, 554, 8000, 8080], description="Ports to scan")

class CameraDiscoveryRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to discover")
    timeout: int = Field(default=5, description="Discovery timeout in seconds")

@router.post("/scan-network", response_model=Dict[str, Any])
async def scan_network(scan_request: NetworkScanRequest):
    """Scan network for potential cameras"""
    try:
        logger.info(f"Starting network scan for range: {scan_request.ip_range}")
        
        # Parse IP range
        try:
            network = ipaddress.ip_network(scan_request.ip_range, strict=False)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid IP range: {str(e)}")
        
        discovered_cameras = []
        
        # Scan each IP in the range
        for ip in network.hosts():
            ip_str = str(ip)
            logger.debug(f"Scanning IP: {ip_str}")
            
            # Test if IP is reachable
            if await ping_ip(ip_str, scan_request.timeout):
                # Check for open ports
                open_ports = await scan_ports(ip_str, scan_request.ports, scan_request.timeout)
                
                if open_ports:
                    # Try to identify camera
                    camera_info = await identify_camera(ip_str, open_ports, scan_request.timeout)
                    
                    if camera_info:
                        discovered_cameras.append({
                            "ip_address": ip_str,
                            "open_ports": open_ports,
                            "manufacturer": camera_info.get("manufacturer", "Unknown"),
                            "model": camera_info.get("model", "Unknown"),
                            "protocols": camera_info.get("protocols", []),
                            "capabilities": camera_info.get("capabilities", []),
                            "confidence": camera_info.get("confidence", 0.5)
                        })
        
        logger.info(f"Network scan completed. Found {len(discovered_cameras)} potential cameras")
        
        return {
            "success": True,
            "scanned_range": scan_request.ip_range,
            "cameras": discovered_cameras,
            "scan_summary": {
                "total_ips_scanned": len(list(network.hosts())),
                "cameras_found": len(discovered_cameras),
                "scan_time": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Network scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Network scan failed: {str(e)}")

@router.post("/discover", response_model=Dict[str, Any])
async def discover_camera(discovery_request: CameraDiscoveryRequest):
    """Discover camera capabilities at a specific IP"""
    try:
        logger.info(f"Starting camera discovery for IP: {discovery_request.ip_address}")
        
        # Validate IP address
        try:
            ipaddress.ip_address(discovery_request.ip_address)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid IP address")
        
        # Test connectivity
        if not await ping_ip(discovery_request.ip_address, discovery_request.timeout):
            return {
                "discovered": False,
                "error": "IP address not reachable",
                "ip_address": discovery_request.ip_address
            }
        
        # Scan common camera ports
        common_ports = [80, 554, 8000, 8080, 443, 1935]
        open_ports = await scan_ports(discovery_request.ip_address, common_ports, discovery_request.timeout)
        
        if not open_ports:
            return {
                "discovered": False,
                "error": "No camera ports open",
                "ip_address": discovery_request.ip_address
            }
        
        # Try to identify camera
        camera_info = await identify_camera(discovery_request.ip_address, open_ports, discovery_request.timeout)
        
        if camera_info:
            return {
                "discovered": True,
                "camera": {
                    "ip_address": discovery_request.ip_address,
                    "open_ports": open_ports,
                    "manufacturer": camera_info.get("manufacturer", "Unknown"),
                    "model": camera_info.get("model", "Unknown"),
                    "protocols": camera_info.get("protocols", []),
                    "capabilities": camera_info.get("capabilities", []),
                    "onvif_info": camera_info.get("onvif_info", {}),
                    "confidence": camera_info.get("confidence", 0.5)
                }
            }
        else:
            return {
                "discovered": False,
                "error": "Could not identify camera type",
                "ip_address": discovery_request.ip_address,
                "open_ports": open_ports
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Camera discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Camera discovery failed: {str(e)}")

# ========================================
# DISCOVERY HELPER FUNCTIONS
# ========================================

async def ping_ip(ip_address: str, timeout: int = 2) -> bool:
    """Test if IP address is reachable"""
    try:
        # Use socket to test connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip_address, 80))
        sock.close()
        return result == 0
    except Exception:
        return False

async def scan_ports(ip_address: str, ports: List[int], timeout: int = 2) -> List[int]:
    """Scan for open ports on an IP address"""
    open_ports = []
    
    async def check_port(port: int) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_address, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    # Check ports concurrently
    tasks = [check_port(port) for port in ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for port, is_open in zip(ports, results):
        if is_open is True:
            open_ports.append(port)
    
    return open_ports

async def identify_camera(ip_address: str, open_ports: List[int], timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Try to identify camera manufacturer and capabilities"""
    import aiohttp
    import asyncio
    
    camera_info = {
        "manufacturer": "Unknown",
        "model": "Unknown", 
        "protocols": [],
        "capabilities": [],
        "onvif_info": {},
        "confidence": 0.1
    }
    
    # Try ONVIF discovery first (most reliable)
    if 80 in open_ports:
        onvif_info = await try_onvif_discovery(ip_address, 80, timeout)
        if onvif_info:
            camera_info.update(onvif_info)
            camera_info["protocols"].append("ONVIF")
            camera_info["confidence"] = 0.9
            return camera_info
    
    # Try HTTP identification
    if 80 in open_ports:
        http_info = await try_http_identification(ip_address, 80, timeout)
        if http_info:
            camera_info.update(http_info)
            camera_info["protocols"].append("HTTP")
            camera_info["confidence"] = max(camera_info["confidence"], 0.6)
    
    # Check for RTSP
    if 554 in open_ports:
        rtsp_info = await try_rtsp_identification(ip_address, 554, timeout)
        if rtsp_info:
            camera_info["protocols"].append("RTSP")
            camera_info["confidence"] = max(camera_info["confidence"], 0.7)
    
    # If we found any protocols, return the info
    if camera_info["protocols"]:
        return camera_info
    
    return None

async def try_onvif_discovery(ip_address: str, port: int, timeout: int) -> Optional[Dict[str, Any]]:
    """Try to discover camera via ONVIF"""
    try:
        # Simple ONVIF device discovery
        import aiohttp
        
        # ONVIF GetDeviceInformation request
        soap_body = """<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <soap:Body>
                <tds:GetDeviceInformation/>
            </soap:Body>
        </soap:Envelope>"""
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.post(
                f"http://{ip_address}:{port}/onvif/device_service",
                data=soap_body,
                headers={"Content-Type": "application/soap+xml", "SOAPAction": "http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation"}
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse basic info from ONVIF response
                    manufacturer = "Unknown"
                    model = "Unknown"
                    
                    if "Manufacturer" in content:
                        import re
                        match = re.search(r'<tds:Manufacturer>(.*?)</tds:Manufacturer>', content)
                        if match:
                            manufacturer = match.group(1)
                    
                    if "Model" in content:
                        match = re.search(r'<tds:Model>(.*?)</tds:Model>', content)
                        if match:
                            model = match.group(1)
                    
                    return {
                        "manufacturer": manufacturer,
                        "model": model,
                        "onvif_info": {
                            "device_service_url": f"http://{ip_address}:{port}/onvif/device_service",
                            "supported": True
                        },
                        "capabilities": ["video", "onvif"]
                    }
    except Exception as e:
        logger.debug(f"ONVIF discovery failed for {ip_address}: {e}")
    
    return None

async def try_http_identification(ip_address: str, port: int, timeout: int) -> Optional[Dict[str, Any]]:
    """Try to identify camera via HTTP"""
    try:
        import aiohttp
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # Try common camera paths
            paths = ["/", "/index.html", "/doc/page/login.asp", "/cgi-bin/hi3510/param.cgi"]
            
            for path in paths:
                try:
                    async with session.get(f"http://{ip_address}:{port}{path}") as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Look for manufacturer clues in HTML
                            content_lower = content.lower()
                            
                            manufacturers = {
                                "hikvision": ["hikvision", "hik-vision"],
                                "dahua": ["dahua", "dh-"],
                                "reolink": ["reolink"],
                                "axis": ["axis"],
                                "uniview": ["uniview", "ipc"],
                                "bosch": ["bosch"]
                            }
                            
                            for manufacturer, keywords in manufacturers.items():
                                if any(keyword in content_lower for keyword in keywords):
                                    return {
                                        "manufacturer": manufacturer.title(),
                                        "capabilities": ["video", "http"]
                                    }
                            
                            # Generic IP camera detection
                            if any(keyword in content_lower for keyword in ["camera", "ipcam", "webcam", "video"]):
                                return {
                                    "manufacturer": "Generic",
                                    "capabilities": ["video", "http"]
                                }
                
                except Exception:
                    continue
    
    except Exception as e:
        logger.debug(f"HTTP identification failed for {ip_address}: {e}")
    
    return None

async def try_rtsp_identification(ip_address: str, port: int, timeout: int) -> Optional[Dict[str, Any]]:
    """Try to identify camera via RTSP"""
    try:
        # Simple RTSP OPTIONS request
        import asyncio
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        if sock.connect_ex((ip_address, port)) == 0:
            # Send RTSP OPTIONS request
            request = f"OPTIONS rtsp://{ip_address}:{port}/ RTSP/1.0\r\nCSeq: 1\r\n\r\n"
            sock.send(request.encode())
            
            response = sock.recv(1024).decode()
            sock.close()
            
            if "RTSP/1.0 200 OK" in response:
                # Look for server information
                if "Server:" in response:
                    server_line = [line for line in response.split('\n') if line.startswith('Server:')]
                    if server_line:
                        server_info = server_line[0].split(':', 1)[1].strip()
                        return {
                            "rtsp_server": server_info,
                            "capabilities": ["video", "rtsp"]
                        }
                
                return {
                    "capabilities": ["video", "rtsp"]
                }
    
    except Exception as e:
        logger.debug(f"RTSP identification failed for {ip_address}: {e}")
    
    return None