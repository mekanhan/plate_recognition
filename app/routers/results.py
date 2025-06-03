from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService

router = APIRouter()

# These will be initialized in the main app
detection_service = None
storage_service = None

async def get_detection_service():
    """Dependency to get the detection service"""
    return detection_service

async def get_storage_service():
    """Dependency to get the storage service"""
    return storage_service

@router.get("/latest")
async def get_latest_detections(
    detection_svc: DetectionService = Depends(get_detection_service)
):
    """Get the latest detections"""
    return await detection_svc.get_latest_detections()

@router.get("/all")
async def get_all_detections(
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all detections from the current session"""
    return await storage_svc.get_detections()

@router.get("/enhanced")
async def get_enhanced_results(
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all enhanced results from the current session"""
    return await storage_svc.get_enhanced_results()