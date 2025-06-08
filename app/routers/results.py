from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
import datetime
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.dependencies.detection import get_detection_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Add custom filter to convert timestamp to readable format
def fromtimestamp(value):
    try:
        return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Unknown"

templates.env.filters["fromtimestamp"] = fromtimestamp

storage_service = None

async def get_storage_service():
    """Dependency to get the storage service"""
    return storage_service

@router.get("/latest", response_class=HTMLResponse)
async def get_latest_detections(
    request: Request,
    detection_svc: DetectionService = Depends(get_detection_service)
):
    """Get the latest detections"""
    detections = await detection_svc.get_latest_detections()
    return templates.TemplateResponse(
        "results.html", 
        {"request": request, "detections": detections}
    )

@router.get("/latest/json")
async def get_latest_detections_json(
    detection_svc: DetectionService = Depends(get_detection_service)
):
    """Get the latest detections as JSON"""
    return await detection_svc.get_latest_detections()

@router.get("/all", response_class=HTMLResponse)
async def get_all_detections(
    request: Request,
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all detections from the current session"""
    detections = await storage_svc.get_detections()
    return templates.TemplateResponse(
        "results.html", 
        {"request": request, "detections": detections}
    )

@router.get("/all/json")
async def get_all_detections_json(
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all detections from the current session as JSON"""
    return await storage_svc.get_detections()

@router.get("/enhanced", response_class=HTMLResponse)
async def get_enhanced_results(
    request: Request,
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all enhanced results from the current session"""
    enhanced_results = await storage_svc.get_enhanced_results()
    return templates.TemplateResponse(
        "results.html", 
        {"request": request, "detections": enhanced_results}
    )

@router.get("/enhanced/json")
async def get_enhanced_results_json(
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all enhanced results from the current session as JSON"""
    return await storage_svc.get_enhanced_results()