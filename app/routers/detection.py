from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import asyncio
import time
import uuid
from app.dependencies.detection import get_detection_service

# Initialize router
router = APIRouter()


@router.post("/detect")
async def detect_license_plate(
    background_tasks: BackgroundTasks,
    detection_svc = Depends(get_detection_service)
):
    """Detect license plate from the current camera frame"""
    # Get current detection result
    detection_result = await detection_svc.detect_from_camera()
    
    if not detection_result:
        raise HTTPException(status_code=404, detail="No license plate detected")
    
    # Process detection in background
    detection_id = str(uuid.uuid4())
    background_tasks.add_task(
        detection_svc.process_detection,
        detection_id=detection_id,
        detection_result=detection_result
    )
    
    return {
        "detection_id": detection_id,
        "timestamp": time.time(),
        "detection": detection_result
    }

@router.post("/detect/upload")
async def detect_from_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    detection_svc = Depends(get_detection_service)
):
    """Detect license plate from uploaded image"""
    # Read the uploaded file
    contents = await file.read()
    
    # Detect from the uploaded image
    detection_result = await detection_svc.detect_from_image(contents)
    
    if not detection_result:
        raise HTTPException(status_code=404, detail="No license plate detected in the uploaded image")
    
    # Process detection in background
    detection_id = str(uuid.uuid4())
    background_tasks.add_task(
        detection_svc.process_detection,
        detection_id=detection_id,
        detection_result=detection_result
    )
    
    return {
        "detection_id": detection_id,
        "timestamp": time.time(),
        "detection": detection_result
    }

@router.get("/status")
async def detection_status(detection_svc = Depends(get_detection_service)):
    """Get the detection service status"""
    return {
        "status": "active",
        "detections_processed": detection_svc.detections_processed,
        "last_detection_time": detection_svc.last_detection_time
    }

@router.get("/test-storage")
async def test_storage(
    detection_svc = Depends(get_detection_service)
):
    """Test storage functionality with a dummy detection"""
    detection_id = str(uuid.uuid4())
    dummy_detection = {
        "plate_text": "TEST123",
        "confidence": 0.9,
        "box": [100, 100, 200, 150],
        "timestamp": time.time(),
        "ocr_confidence": 0.9,
        "state": "CA",
        "raw_text": "TEST LICENSE PLATE"
    }

    # Process the dummy detection
    await detection_svc.process_detection(
        detection_id=detection_id,
        detection_result=dummy_detection
    )

    return {
        "success": True,
        "message": "Test detection processed and should be stored",
        "detection_id": detection_id
    }
