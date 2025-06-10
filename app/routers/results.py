from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
import datetime
import time
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
detection_service = None

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

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring storage and database status"""
    try:
        status = {
            "status": "healthy",
            "services": {},
            "timestamp": time.time()
        }
        
        # Check storage service
        if storage_service and hasattr(storage_service, 'initialization_complete'):
            status["services"]["storage"] = {
                "initialized": storage_service.initialization_complete,
                "detections_saved_json": getattr(storage_service, 'detections_saved_to_json', 0),
                "detections_saved_sql": getattr(storage_service, 'detections_saved_to_db', 0),
                "session_file": getattr(storage_service, 'session_file', None)
            }
        
        # Check detection service
        if detection_service and hasattr(detection_service, 'license_plate_service'):
            status["services"]["detection"] = {
                "initialized": detection_service.license_plate_service is not None,
                "detections_processed": getattr(detection_service, 'detections_processed', 0),
                "frame_count": getattr(detection_service, 'frame_count', 0)
            }
        
        # Check database connectivity
        try:
            from app.database import async_session
            from sqlalchemy import text
            async with async_session() as session:
                result = await session.execute(text("SELECT COUNT(*) FROM detections"))
                db_count = result.scalar()
                status["services"]["database"] = {
                    "connected": True,
                    "detection_count": db_count
                }
        except Exception as e:
            status["services"]["database"] = {
                "connected": False,
                "error": str(e)
            }
        
        return status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@router.get("/database/json")
async def get_database_detections():
    """Get detections directly from the SQL database"""
    try:
        from app.database import async_session
        from app.models import Detection
        from sqlalchemy import select
        
        async with async_session() as session:
            result = await session.execute(
                select(Detection).order_by(Detection.timestamp.desc()).limit(50)
            )
            detections = result.scalars().all()
            
            # Convert to dict format
            detection_list = []
            for detection in detections:
                detection_dict = {
                    "detection_id": detection.id,
                    "plate_text": detection.plate_text,
                    "confidence": detection.confidence,
                    "timestamp": detection.timestamp.timestamp() if detection.timestamp else None,
                    "box": [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2] 
                        if all(x is not None for x in [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2]) 
                        else None,
                    "frame_id": detection.frame_id,
                    "raw_text": detection.raw_text,
                    "state": detection.state,
                    "status": detection.status,
                    "image_path": detection.image_path,
                    "video_path": detection.video_path
                }
                detection_list.append(detection_dict)
            
            return {
                "source": "sql_database",
                "count": len(detection_list),
                "detections": detection_list
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "source": "sql_database"
        }