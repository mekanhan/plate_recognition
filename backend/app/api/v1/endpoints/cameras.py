"""
Camera management endpoints
"""
import asyncio
import socket
import time
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, validator

from app.database import get_database
from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse, CameraListResponse
from app.services.camera_crud import (
    get_cameras, get_camera_count, get_camera_by_id, get_camera_by_ip, create_camera, 
    update_camera, delete_camera, update_camera_status
)

router = APIRouter()


class CameraTestRequest(BaseModel):
    ip_address: str
    port: int = 80
    username: str = "admin"
    password: str = ""
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format"""
        try:
            socket.inet_aton(v)
            return v
        except socket.error:
            raise ValueError('Invalid IP address format')


class CameraTestResponse(BaseModel):
    success: bool
    message: str
    response_time: int = None


@router.post("/test-connection", response_model=CameraTestResponse)
async def test_camera_connection(request: CameraTestRequest) -> CameraTestResponse:
    """
    Test connection to IP camera
    
    Performs basic connectivity test to camera IP address
    """
    start_time = time.time()
    
    try:
        # Test basic IP connectivity with ping-like socket test
        response_time = await ping_test(request.ip_address)
        
        if response_time is None:
            return CameraTestResponse(
                success=False,
                message=f"Cannot reach {request.ip_address} - Host unreachable"
            )
        
        # Test the specified port
        port_accessible = await test_specific_port(request.ip_address, request.port)
        
        if not port_accessible:
            return CameraTestResponse(
                success=False,
                message=f"Host {request.ip_address} reachable but port {request.port} is closed",
                response_time=response_time
            )
        
        # Success response
        return CameraTestResponse(
            success=True,
            message=f"Camera accessible on {request.ip_address}:{request.port}",
            response_time=response_time
        )
        
    except Exception as e:
        return CameraTestResponse(
            success=False,
            message=f"Connection test failed: {str(e)}"
        )


async def ping_test(ip_address: str, timeout: float = 3.0) -> int:
    """
    Test basic connectivity to IP address
    Returns response time in milliseconds, or None if unreachable
    """
    try:
        start_time = time.time()
        
        # Create socket connection test (faster than subprocess ping)
        future = asyncio.open_connection(ip_address, 80)
        
        try:
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            
            response_time = int((time.time() - start_time) * 1000)
            return response_time
            
        except (asyncio.TimeoutError, ConnectionRefusedError):
            # Port 80 failed, try ICMP-style test with socket
            return await socket_ping_test(ip_address, timeout)
            
    except Exception:
        return None


async def socket_ping_test(ip_address: str, timeout: float = 3.0) -> int:
    """
    Alternative connectivity test using socket
    """
    try:
        start_time = time.time()
        
        # Test with a raw socket approach
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((ip_address, 80))
        sock.close()
        
        response_time = int((time.time() - start_time) * 1000)
        
        # Even if connection refused, host is reachable
        if result in [0, 111]:  # 0=success, 111=connection refused but host reachable
            return response_time
        
        return None
        
    except Exception:
        return None


async def test_specific_port(ip_address: str, port: int, timeout: float = 2.0) -> bool:
    """
    Test if a specific port is accessible on the given IP address
    Returns True if port is accessible, False otherwise
    """
    try:
        future = asyncio.open_connection(ip_address, port)
        reader, writer = await asyncio.wait_for(future, timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except:
        return False


async def test_camera_ports(ip_address: str, timeout: float = 2.0) -> list:
    """
    Test common camera service ports
    Returns list of accessible ports
    """
    common_camera_ports = [80, 554, 8080, 8000, 8554, 1935]
    accessible_ports = []
    
    async def test_port(port):
        try:
            future = asyncio.open_connection(ip_address, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return port
        except:
            return None
    
    # Test ports concurrently
    tasks = [test_port(port) for port in common_camera_ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if result is not None and not isinstance(result, Exception):
            accessible_ports.append(result)
    
    return accessible_ports


# CRUD Endpoints

@router.get("/", response_model=CameraListResponse)
async def list_cameras(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_database)
) -> CameraListResponse:
    """Get list of all cameras"""
    cameras = await get_cameras(db, skip=skip, limit=limit)
    total = await get_camera_count(db)
    
    return CameraListResponse(
        cameras=[CameraResponse.model_validate(camera) for camera in cameras],
        total=total
    )


@router.post("/", response_model=CameraResponse)
async def create_new_camera(
    camera: CameraCreate,
    db: AsyncSession = Depends(get_database)
) -> CameraResponse:
    """Create a new camera"""
    # Check if camera with same IP already exists
    existing_camera = await get_camera_by_ip(db, camera.ip_address)
    if existing_camera:
        raise HTTPException(
            status_code=400,
            detail=f"Camera with IP address {camera.ip_address} already exists"
        )
    
    db_camera = await create_camera(db, camera)
    return CameraResponse.model_validate(db_camera)


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_database)
) -> CameraResponse:
    """Get a specific camera by ID"""
    camera = await get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return CameraResponse.model_validate(camera)


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_existing_camera(
    camera_id: int,
    camera_update: CameraUpdate,
    db: AsyncSession = Depends(get_database)
) -> CameraResponse:
    """Update an existing camera"""
    camera = await update_camera(db, camera_id, camera_update)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return CameraResponse.model_validate(camera)


@router.delete("/{camera_id}")
async def delete_existing_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_database)
) -> dict:
    """Delete a camera"""
    success = await delete_camera(db, camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return {"message": "Camera deleted successfully"}


@router.patch("/{camera_id}/status")
async def update_camera_status_endpoint(
    camera_id: int,
    status: str,
    db: AsyncSession = Depends(get_database)
) -> CameraResponse:
    """Update camera status (online/offline/error)"""
    allowed_statuses = ["online", "offline", "error"]
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {allowed_statuses}"
        )
    
    camera = await update_camera_status(db, camera_id, status)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return CameraResponse.model_validate(camera)