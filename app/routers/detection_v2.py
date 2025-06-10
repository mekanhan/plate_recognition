"""
Improved detection routes using the new service architecture.
"""
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import logging

from app.services.detection_service_v2 import DetectionServiceV2
from app.interfaces.camera import Camera
from app.interfaces.detector import LicensePlateDetector
from app.dependencies.services import get_camera, get_detector

# Logger for this module
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Reference to detection service, set during app startup
detection_service: Optional[DetectionServiceV2] = None

@router.get("/status")
async def detection_status():
    """Get detection service status"""
    if not detection_service:
        raise HTTPException(status_code=503, detail="Detection service not initialized")
    
    return {
        "status": "running",
        "processed_detections": detection_service.detections_processed,
        "last_detection_time": detection_service.last_detection_time
    }

@router.get("/latest")
async def get_latest_detections():
    """Get the latest license plate detections"""
    if not detection_service:
        raise HTTPException(status_code=503, detail="Detection service not initialized")
    
    latest_detections = await detection_service.get_latest_detections()
    return {"detections": latest_detections}

@router.post("/detect-from-camera")
async def detect_from_camera(background_tasks: BackgroundTasks):
    """Detect license plate from the current camera frame"""
    if not detection_service:
        raise HTTPException(status_code=503, detail="Detection service not initialized")
    
    try:
        detection = await detection_service.detect_from_camera()
        
        if not detection:
            return JSONResponse(
                status_code=404,
                content={"detail": "No license plate detected in current frame"}
            )
        
        # Process the detection in the background
        background_tasks.add_task(
            detection_service.process_detection,
            detection.get("detection_id", "unknown"),
            detection
        )
        
        return {
            "detection_id": detection.get("detection_id", "unknown"),
            "plate_text": detection.get("plate_text", ""),
            "confidence": detection.get("confidence", 0),
            "timestamp": detection.get("timestamp", time.time())
        }
    except Exception as e:
        logger.error(f"Error detecting from camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-from-image")
async def detect_from_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Detect license plate from an uploaded image"""
    if not detection_service:
        raise HTTPException(status_code=503, detail="Detection service not initialized")
    
    try:
        # Read file contents
        image_data = await file.read()
        
        if not image_data:
            return JSONResponse(
                status_code=400,
                content={"detail": "Empty file uploaded"}
            )
        
        # Process the image
        detection = await detection_service.detect_from_image(image_data)
        
        if not detection:
            return JSONResponse(
                status_code=404,
                content={"detail": "No license plate detected in image"}
            )
        
        # Process the detection in the background
        background_tasks.add_task(
            detection_service.process_detection,
            detection.get("detection_id", "unknown"),
            detection
        )
        
        return {
            "detection_id": detection.get("detection_id", "unknown"),
            "plate_text": detection.get("plate_text", ""),
            "confidence": detection.get("confidence", 0),
            "timestamp": detection.get("timestamp", time.time())
        }
    except Exception as e:
        logger.error(f"Error detecting from image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug")
async def debug_info(
    camera: Camera = Depends(get_camera),
    detector: LicensePlateDetector = Depends(get_detector)
):
    """Get debug information about detection components"""
    if not detection_service:
        raise HTTPException(status_code=503, detail="Detection service not initialized")
    
    return {
        "detection_service": {
            "type": type(detection_service).__name__,
            "detections_processed": detection_service.detections_processed,
            "performance_metrics": detection_service.performance_metrics
        },
        "camera": {
            "type": type(camera).__name__
        },
        "detector": {
            "type": type(detector).__name__,
        }
    }