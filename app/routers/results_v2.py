"""
Improved results routes using the new service architecture.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List, Optional
import logging
import datetime

from app.interfaces.storage import DetectionRepository, EnhancementRepository
from app.dependencies.services import get_detection_repository, get_enhancement_repository

# Logger for this module
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Templates for HTML responses
templates = Jinja2Templates(directory="templates")

# Add custom filter to convert timestamp to readable format
def fromtimestamp(value):
    try:
        return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Unknown"

templates.env.filters["fromtimestamp"] = fromtimestamp

@router.get("/latest", response_class=HTMLResponse)
async def get_latest_detections(
    request: Request,
    detection_repository: DetectionRepository = Depends(get_detection_repository)
):
    """Get the latest detections for display in the web UI (backward compatibility with V1)."""
    try:
        # Get all detections from repository
        all_detections = await detection_repository.get_detections()
        
        # Sort by timestamp (newest first) and take the last 20
        latest_detections = sorted(
            all_detections,
            key=lambda d: d.get("timestamp", 0),
            reverse=True
        )[:20]
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "detections": latest_detections,
            "total_detections": len(all_detections)
        })
    except Exception as e:
        logger.error(f"Error getting latest detections: {e}")
        # Return empty results on error to prevent page crash
        return templates.TemplateResponse("results.html", {
            "request": request,
            "detections": [],
            "total_detections": 0,
            "error": str(e)
        })

@router.get("/detections")
async def get_detections(
    limit: int = Query(10, description="Maximum number of detections to return"),
    skip: int = Query(0, description="Number of detections to skip"),
    min_confidence: float = Query(0.0, description="Minimum confidence threshold"),
    detection_repository: DetectionRepository = Depends(get_detection_repository)
):
    """
    Get license plate detections.
    
    Args:
        limit: Maximum number of detections to return
        skip: Number of detections to skip
        min_confidence: Minimum confidence threshold
    """
    try:
        # Get all detections from repository
        all_detections = await detection_repository.get_detections()
        
        # Filter by confidence
        filtered_detections = [
            d for d in all_detections
            if d.get("confidence", 0) >= min_confidence
        ]
        
        # Sort by timestamp (newest first)
        sorted_detections = sorted(
            filtered_detections,
            key=lambda d: d.get("timestamp", 0),
            reverse=True
        )
        
        # Apply pagination
        paginated_detections = sorted_detections[skip:skip+limit]
        
        return {
            "total": len(filtered_detections),
            "limit": limit,
            "skip": skip,
            "detections": paginated_detections
        }
    except Exception as e:
        logger.error(f"Error getting detections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/enhanced-results")
async def get_enhanced_results(
    limit: int = Query(10, description="Maximum number of enhanced results to return"),
    skip: int = Query(0, description="Number of enhanced results to skip"),
    min_confidence: float = Query(0.0, description="Minimum confidence threshold"),
    enhancement_repository: EnhancementRepository = Depends(get_enhancement_repository)
):
    """
    Get enhanced license plate results.
    
    Args:
        limit: Maximum number of enhanced results to return
        skip: Number of enhanced results to skip
        min_confidence: Minimum confidence threshold
    """
    try:
        # Get all enhanced results from repository
        all_results = await enhancement_repository.get_enhanced_results()
        
        # Filter by confidence
        filtered_results = [
            r for r in all_results
            if r.get("confidence", 0) >= min_confidence
        ]
        
        # Sort by timestamp (newest first)
        sorted_results = sorted(
            filtered_results,
            key=lambda r: r.get("timestamp", 0),
            reverse=True
        )
        
        # Apply pagination
        paginated_results = sorted_results[skip:skip+limit]
        
        return {
            "total": len(filtered_results),
            "limit": limit,
            "skip": skip,
            "enhanced_results": paginated_results
        }
    except Exception as e:
        logger.error(f"Error getting enhanced results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detection/{detection_id}")
async def get_detection_by_id(
    detection_id: str,
    detection_repository: DetectionRepository = Depends(get_detection_repository)
):
    """
    Get a specific detection by ID.
    
    Args:
        detection_id: Detection ID
    """
    try:
        # Get detection by ID
        detection = await detection_repository.get_detection_by_id(detection_id)
        
        if not detection:
            raise HTTPException(status_code=404, detail=f"Detection with ID {detection_id} not found")
        
        return detection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detection by ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/enhanced-result/{enhanced_id}")
async def get_enhanced_result_by_id(
    enhanced_id: str,
    enhancement_repository: EnhancementRepository = Depends(get_enhancement_repository)
):
    """
    Get a specific enhanced result by ID.
    
    Args:
        enhanced_id: Enhanced result ID
    """
    try:
        # Get enhanced result by ID
        enhanced_result = await enhancement_repository.get_enhanced_result_by_id(enhanced_id)
        
        if not enhanced_result:
            raise HTTPException(status_code=404, detail=f"Enhanced result with ID {enhanced_id} not found")
        
        return enhanced_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enhanced result by ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics(
    detection_repository: DetectionRepository = Depends(get_detection_repository),
    enhancement_repository: EnhancementRepository = Depends(get_enhancement_repository)
):
    """Get statistics about license plate detections and enhancements."""
    try:
        # Get all detections and enhanced results
        all_detections = await detection_repository.get_detections()
        all_enhanced_results = await enhancement_repository.get_enhanced_results()
        
        # Calculate statistics
        detection_count = len(all_detections)
        enhanced_count = len(all_enhanced_results)
        
        # Calculate average confidence
        avg_detection_confidence = 0
        if detection_count > 0:
            avg_detection_confidence = sum(d.get("confidence", 0) for d in all_detections) / detection_count
        
        avg_enhanced_confidence = 0
        if enhanced_count > 0:
            avg_enhanced_confidence = sum(r.get("confidence", 0) for r in all_enhanced_results) / enhanced_count
        
        # Count unique plates
        unique_plates = set(d.get("plate_text", "") for d in all_detections if d.get("plate_text"))
        unique_plate_count = len(unique_plates)
        
        return {
            "detection_count": detection_count,
            "enhanced_count": enhanced_count,
            "unique_plate_count": unique_plate_count,
            "avg_detection_confidence": avg_detection_confidence,
            "avg_enhanced_confidence": avg_enhanced_confidence
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))