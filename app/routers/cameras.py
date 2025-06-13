# app/routers/cameras.py
import asyncio
import base64
import io
import qrcode
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.camera_models import (
    CameraRegistration, CameraInfo, CameraUpdate, CameraType, CameraStatus,
    NetworkScanResult, CameraHealthCheck, QRCodeRequest, CameraFrame
)
from app.services.camera_manager import CameraManager
from app.services.stream_processor import UniversalStreamProcessor
from app.dependencies.detection import get_detection_service

router = APIRouter(prefix="/api/cameras", tags=["cameras"])

# Global camera manager and stream processor instances
camera_manager = CameraManager()
universal_stream_processor = UniversalStreamProcessor()

@router.post("/register", response_model=dict)
async def register_camera(
    registration: CameraRegistration,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new camera source"""
    try:
        camera_id = await camera_manager.register_camera(registration, db)
        
        # Start stream processing if not PWA type
        if registration.type != CameraType.PWA:
            await universal_stream_processor.add_camera_source(
                camera_id, registration.type, registration.config
            )
        
        return {
            "success": True,
            "camera_id": camera_id,
            "message": f"Camera '{registration.name}' registered successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[CameraInfo])
async def list_cameras(
    include_offline: bool = True,
    db: AsyncSession = Depends(get_db_session)
):
    """List all registered cameras"""
    try:
        cameras = await camera_manager.list_cameras(db, include_offline)
        return cameras
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}", response_model=CameraInfo)
async def get_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get detailed information about a specific camera"""
    try:
        camera = await camera_manager.get_camera_info(camera_id, db)
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        return camera
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{camera_id}", response_model=dict)
async def update_camera(
    camera_id: str,
    update: CameraUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update camera configuration"""
    try:
        success = await camera_manager.update_camera(camera_id, update, db)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update camera")
        
        return {
            "success": True,
            "message": f"Camera {camera_id} updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{camera_id}", response_model=dict)
async def remove_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Remove a camera and stop its processing"""
    try:
        # Stop stream processing
        await universal_stream_processor.stop_camera_stream(camera_id)
        
        # Remove from camera manager
        success = await camera_manager.remove_camera(camera_id, db)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove camera")
        
        return {
            "success": True,
            "message": f"Camera {camera_id} removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/discovery/scan", response_model=NetworkScanResult)
async def discover_cameras(
    network_range: str = "192.168.1.0/24"
):
    """Auto-discover cameras on the network"""
    try:
        result = await camera_manager.discover_cameras(network_range)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/health", response_model=CameraHealthCheck)
async def check_camera_health(camera_id: str):
    """Check camera health and connectivity"""
    try:
        health = await camera_manager.check_camera_health(camera_id)
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/stream", response_model=dict)
async def handle_camera_stream(
    camera_id: str,
    file: UploadFile = File(...),
    detection_service = Depends(get_detection_service)
):
    """Handle incoming frame from any camera source"""
    try:
        # Read frame data
        frame_data = await file.read()
        
        # Process frame through universal stream processor
        detections = await universal_stream_processor.process_frame(
            camera_id, frame_data, detection_service
        )
        
        # Update camera stats
        await camera_manager.update_camera_stats(
            camera_id, 
            frames_delta=1, 
            detections_delta=len(detections) if detections else 0
        )
        
        return {
            "success": True,
            "camera_id": camera_id,
            "detections_count": len(detections) if detections else 0,
            "detections": detections or []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/control/start", response_model=dict)
async def start_camera_stream(
    camera_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Start stream processing for a camera"""
    try:
        camera = await camera_manager.get_camera_info(camera_id, db)
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Start stream processing
        success = await universal_stream_processor.add_camera_source(
            camera_id, camera.type, camera.config
        )
        
        if success:
            await camera_manager.set_camera_status(camera_id, CameraStatus.ONLINE, db)
        
        return {
            "success": success,
            "message": f"Camera {camera_id} stream {'started' if success else 'failed to start'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/control/stop", response_model=dict)
async def stop_camera_stream(
    camera_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Stop stream processing for a camera"""
    try:
        success = await universal_stream_processor.stop_camera_stream(camera_id)
        
        if success:
            await camera_manager.set_camera_status(camera_id, CameraStatus.OFFLINE, db)
        
        return {
            "success": success,
            "message": f"Camera {camera_id} stream {'stopped' if success else 'failed to stop'}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/stats", response_model=dict)
async def get_camera_stats(camera_id: str):
    """Get real-time statistics for a camera"""
    try:
        stats = await universal_stream_processor.get_camera_stats(camera_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Camera not found or not active")
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/all", response_model=dict)
async def get_all_camera_stats():
    """Get comprehensive statistics for all cameras"""
    try:
        stats = await universal_stream_processor.get_all_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qr/{computer_ip}", response_class=StreamingResponse)
async def generate_camera_qr(
    computer_ip: str,
    camera_name: Optional[str] = None
):
    """Generate QR code for mobile camera setup"""
    try:
        # Create setup URL
        setup_url = f"http://{computer_ip}:8001/camera?auto_setup=true"
        if camera_name:
            setup_url += f"&name={camera_name}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(setup_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return StreamingResponse(
            io.BytesIO(img_bytes.read()),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=camera_setup_qr.png"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoints for real-time camera streaming

@router.websocket("/{camera_id}/ws")
async def camera_websocket(websocket, camera_id: str):
    """WebSocket endpoint for real-time camera streaming"""
    await websocket.accept()
    
    try:
        # Register WebSocket connection
        if camera_id in universal_stream_processor.active_streams:
            stream_info = universal_stream_processor.active_streams[camera_id]
            
            while True:
                # Send camera status and stats
                stats = await universal_stream_processor.get_camera_stats(camera_id)
                if stats:
                    await websocket.send_json({
                        "type": "stats",
                        "data": stats
                    })
                
                await asyncio.sleep(1)  # Send updates every second
                
    except Exception as e:
        print(f"WebSocket error for camera {camera_id}: {e}")
    finally:
        await websocket.close()

# PWA-specific endpoints

@router.post("/pwa/{camera_id}/frame", response_model=dict)
async def pwa_camera_frame(
    camera_id: str,
    request: Request,
    detection_service = Depends(get_detection_service)
):
    """Handle frame upload from PWA camera client"""
    try:
        # Read raw frame data from request body
        frame_data = await request.body()
        
        # Process frame
        detections = await universal_stream_processor.process_frame(
            camera_id, frame_data, detection_service
        )
        
        # Update stats
        await camera_manager.update_camera_stats(
            camera_id,
            frames_delta=1,
            detections_delta=len(detections) if detections else 0
        )
        
        return {
            "success": True,
            "detections": detections or [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pwa/setup/{computer_ip}", response_model=dict)
async def pwa_setup_info(computer_ip: str):
    """Get PWA setup information"""
    try:
        return {
            "setup_url": f"http://{computer_ip}:8001/camera",
            "stream_endpoint": f"http://{computer_ip}:8001/api/cameras/pwa/{{camera_id}}/frame",
            "registration_endpoint": f"http://{computer_ip}:8001/api/cameras/register",
            "supported_formats": ["jpeg", "webp"],
            "recommended_resolution": "1280x720",
            "recommended_fps": 15
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin and debug endpoints

@router.get("/debug/active", response_model=dict)
async def debug_active_streams():
    """Debug endpoint to see active streams"""
    try:
        return {
            "active_cameras": len(universal_stream_processor.active_streams),
            "streams": {
                camera_id: {
                    "type": info["type"].value,
                    "status": info["status"],
                    "frame_count": info["frame_count"],
                    "error_count": info["error_count"]
                }
                for camera_id, info in universal_stream_processor.active_streams.items()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/debug/test-camera", response_model=dict)
async def test_camera_connection(
    camera_type: CameraType,
    config_data: dict
):
    """Test camera connection without registering"""
    try:
        from app.models.camera_models import CameraConfig
        config = CameraConfig(**config_data)
        
        # Perform basic connection test
        if camera_type == CameraType.RTSP:
            # Test RTSP connection
            import socket
            host = config.url.split("//")[1].split("/")[0].split(":")[0]
            port = 554
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(config.timeout_seconds)
            result = sock.connect_ex((host, port))
            sock.close()
            success = result == 0
        elif camera_type == CameraType.USB:
            # Test USB camera
            import cv2
            cap = cv2.VideoCapture(config.device_id)
            success = cap.isOpened()
            if success:
                cap.release()
        else:
            success = True  # Assume success for other types
        
        return {
            "success": success,
            "camera_type": camera_type.value,
            "message": "Connection test completed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }