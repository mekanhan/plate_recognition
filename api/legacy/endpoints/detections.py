"""
Detection endpoints for license plate detection results
Extracted from monolithic main.py for better organization
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# Import our core utilities
from ..core.errors import (
    APIError, DetectionNotFoundError, ValidationError, log_and_raise_error
)

# Import services and utilities
from database.foundation_service import get_foundation_database_service
from auth.dependencies import get_current_user, require_detection_view
from auth.models import User

# Create detection router
router = APIRouter(prefix="/api/detections", tags=["detections"])

logger = logging.getLogger(__name__)

# Helper functions
def _calculate_similarity_score(target: str, candidate: str) -> float:
    """Calculate similarity score between two license plate texts"""
    if not target or not candidate:
        return 0.0
    
    # Use sequence matcher for similarity
    return SequenceMatcher(None, target.upper(), candidate.upper()).ratio()

# Detection endpoints
@router.get("/recent", dependencies=[Depends(require_detection_view)])
async def get_recent_detections(
    limit: int = Query(50, ge=1, le=1000),
    camera_id: Optional[str] = Query(None),
    db_service = Depends(get_foundation_database_service)
):
    """Get recent license plate detections"""
    try:
        detections = await db_service.get_recent_detections(
            limit=limit,
            camera_id=camera_id
        )
        
        result = []
        for d in detections:
            result.append({
                "id": d.id,
                "detection_id": str(d.id),
                "camera_id": d.camera_id,
                "plate_text": d.plate_text,
                "confidence": d.confidence,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                "bbox_x": d.bbox_x,
                "bbox_y": d.bbox_y,
                "bbox_width": d.bbox_width,
                "bbox_height": d.bbox_height,
                "image_path": d.image_path,
                "full_frame_path": d.full_frame_path,
                "vehicle_type": d.vehicle_type,
                "vehicle_color": d.vehicle_color,
                "processing_time_ms": d.processing_time_ms,
                "ocr_confidence": d.ocr_confidence
            })
        
        return {
            "detections": result,
            "count": len(result),
            "limit": limit,
            "camera_id": camera_id
        }
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get recent detections")

@router.get("/search", dependencies=[Depends(require_detection_view)])
async def search_detections(
    plate_text: Optional[str] = Query(None, min_length=1),
    camera_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db_service = Depends(get_foundation_database_service)
):
    """Search license plate detections with filters"""
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise ValidationError("start_date must be before end_date")
        
        detections = await db_service.search_detections(
            plate_text=plate_text,
            camera_id=camera_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        result = []
        for d in detections:
            result.append({
                "id": d.id,
                "detection_id": str(d.id),
                "camera_id": d.camera_id,
                "plate_text": d.plate_text,
                "confidence": d.confidence,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                "bbox_x": d.bbox_x,
                "bbox_y": d.bbox_y,
                "bbox_width": d.bbox_width,
                "bbox_height": d.bbox_height,
                "image_path": d.image_path,
                "full_frame_path": d.full_frame_path,
                "vehicle_type": d.vehicle_type,
                "vehicle_color": d.vehicle_color,
                "processing_time_ms": d.processing_time_ms,
                "ocr_confidence": d.ocr_confidence
            })
        
        return {
            "detections": result,
            "count": len(result),
            "filters": {
                "plate_text": plate_text,
                "camera_id": camera_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "limit": limit
            }
        }
        
    except Exception as e:
        log_and_raise_error(e, "Failed to search detections")

@router.get("/similar/{plate_text}", dependencies=[Depends(require_detection_view)])
async def get_similar_detections(
    plate_text: str,
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=500),
    days_back: int = Query(30, ge=1, le=365),
    db_service = Depends(get_foundation_database_service)
):
    """Find detections with similar license plate text"""
    try:
        if not plate_text or len(plate_text.strip()) == 0:
            raise ValidationError("plate_text is required", "plate_text")
        
        # Get detections from the specified time period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        all_detections = await db_service.search_detections(
            start_date=start_date,
            end_date=end_date,
            limit=1000  # Get more to filter for similarity
        )
        
        # Calculate similarity scores
        similar_detections = []
        target_plate = plate_text.upper().strip()
        
        for detection in all_detections:
            if not detection.plate_text:
                continue
                
            similarity = _calculate_similarity_score(target_plate, detection.plate_text)
            
            if similarity >= threshold:
                similar_detections.append({
                    "id": detection.id,
                    "detection_id": str(detection.id),
                    "camera_id": detection.camera_id,
                    "plate_text": detection.plate_text,
                    "confidence": detection.confidence,
                    "similarity_score": round(similarity, 3),
                    "timestamp": detection.timestamp.isoformat() if detection.timestamp else None,
                    "image_path": detection.image_path,
                    "vehicle_type": detection.vehicle_type,
                    "vehicle_color": detection.vehicle_color
                })
        
        # Sort by similarity score (highest first)
        similar_detections.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Apply limit
        similar_detections = similar_detections[:limit]
        
        return {
            "target_plate": target_plate,
            "similar_detections": similar_detections,
            "count": len(similar_detections),
            "threshold": threshold,
            "days_searched": days_back,
            "total_candidates_checked": len(all_detections)
        }
        
    except Exception as e:
        log_and_raise_error(e, f"Failed to find similar detections for {plate_text}")

@router.get("/history/{plate_text}", dependencies=[Depends(require_detection_view)])
async def get_plate_history(
    plate_text: str,
    limit: int = Query(100, ge=1, le=1000),
    days_back: int = Query(90, ge=1, le=365),
    db_service = Depends(get_foundation_database_service)
):
    """Get detection history for a specific license plate"""
    try:
        if not plate_text or len(plate_text.strip()) == 0:
            raise ValidationError("plate_text is required", "plate_text")
        
        # Get detections for this specific plate
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        detections = await db_service.search_detections(
            plate_text=plate_text.upper().strip(),
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        result = []
        cameras_seen = set()
        
        for d in detections:
            cameras_seen.add(d.camera_id)
            result.append({
                "id": d.id,
                "detection_id": str(d.id),
                "camera_id": d.camera_id,
                "plate_text": d.plate_text,
                "confidence": d.confidence,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                "image_path": d.image_path,
                "full_frame_path": d.full_frame_path,
                "vehicle_type": d.vehicle_type,
                "vehicle_color": d.vehicle_color,
                "processing_time_ms": d.processing_time_ms,
                "ocr_confidence": d.ocr_confidence
            })
        
        # Sort by timestamp (most recent first)
        result.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        return {
            "plate_text": plate_text.upper().strip(),
            "detections": result,
            "count": len(result),
            "cameras_seen": list(cameras_seen),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days_back
            },
            "first_seen": result[-1]['timestamp'] if result else None,
            "last_seen": result[0]['timestamp'] if result else None
        }
        
    except Exception as e:
        log_and_raise_error(e, f"Failed to get history for plate {plate_text}")

@router.get("/stats", dependencies=[Depends(require_detection_view)])
async def get_detection_stats(
    days_back: int = Query(7, ge=1, le=365),
    db_service = Depends(get_foundation_database_service)
):
    """Get detection statistics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        stats = await db_service.get_detection_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days_back
            },
            "total_detections": stats.get("total_detections", 0),
            "unique_plates": stats.get("unique_plates", 0),
            "cameras_active": stats.get("cameras_active", 0),
            "avg_confidence": stats.get("avg_confidence", 0.0),
            "detections_by_day": stats.get("detections_by_day", []),
            "detections_by_camera": stats.get("detections_by_camera", []),
            "top_plates": stats.get("top_plates", []),
            "vehicle_types": stats.get("vehicle_types", [])
        }
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get detection stats")

@router.get("/{detection_id}", dependencies=[Depends(require_detection_view)])
async def get_detection(
    detection_id: int,
    db_service = Depends(get_foundation_database_service)
):
    """Get a specific detection by ID"""
    try:
        detection = await db_service.get_detection(detection_id)
        
        if not detection:
            raise DetectionNotFoundError(str(detection_id))
        
        return {
            "id": detection.id,
            "detection_id": str(detection.id),
            "camera_id": detection.camera_id,
            "plate_text": detection.plate_text,
            "confidence": detection.confidence,
            "timestamp": detection.timestamp.isoformat() if detection.timestamp else None,
            "bbox_x": detection.bbox_x,
            "bbox_y": detection.bbox_y,
            "bbox_width": detection.bbox_width,
            "bbox_height": detection.bbox_height,
            "image_path": detection.image_path,
            "full_frame_path": detection.full_frame_path,
            "vehicle_type": detection.vehicle_type,
            "vehicle_color": detection.vehicle_color,
            "processing_time_ms": detection.processing_time_ms,
            "ocr_confidence": detection.ocr_confidence,
            "created_at": detection.created_at.isoformat() if hasattr(detection, 'created_at') and detection.created_at else None
        }
        
    except Exception as e:
        log_and_raise_error(e, f"Failed to get detection {detection_id}")

@router.get("/{detection_id}/quality", dependencies=[Depends(require_detection_view)])
async def get_detection_quality(
    detection_id: int,
    db_service = Depends(get_foundation_database_service)
):
    """Get quality metrics for a specific detection"""
    try:
        detection = await db_service.get_detection(detection_id)
        
        if not detection:
            raise DetectionNotFoundError(str(detection_id))
        
        # Calculate quality metrics
        quality_score = 0.0
        quality_factors = []
        
        # Confidence score (0-100%)
        if detection.confidence:
            conf_score = min(100, detection.confidence * 100)
            quality_score += conf_score * 0.4  # 40% weight
            quality_factors.append({
                "factor": "detection_confidence",
                "score": conf_score,
                "weight": 0.4,
                "description": "YOLO detection confidence"
            })
        
        # OCR confidence (0-100%)
        if detection.ocr_confidence:
            ocr_score = min(100, detection.ocr_confidence)
            quality_score += ocr_score * 0.4  # 40% weight
            quality_factors.append({
                "factor": "ocr_confidence",
                "score": ocr_score,
                "weight": 0.4,
                "description": "OCR text recognition confidence"
            })
        
        # Processing time (faster is better, 0-100%)
        if detection.processing_time_ms:
            # Assume 500ms is baseline (50 points), scale from there
            time_score = max(0, min(100, 100 - (detection.processing_time_ms - 500) / 10))
            quality_score += time_score * 0.1  # 10% weight
            quality_factors.append({
                "factor": "processing_speed",
                "score": time_score,
                "weight": 0.1,
                "description": "Processing speed (faster is better)"
            })
        
        # Plate text length and format (0-100%)
        if detection.plate_text:
            text_len = len(detection.plate_text.strip())
            # Assume 6-8 characters is optimal for license plates
            if 6 <= text_len <= 8:
                text_score = 100
            elif text_len < 6:
                text_score = max(0, text_len * 16.67)  # Scale up to 100
            else:
                text_score = max(0, 100 - (text_len - 8) * 10)  # Scale down from 100
            
            quality_score += text_score * 0.1  # 10% weight
            quality_factors.append({
                "factor": "text_format",
                "score": text_score,
                "weight": 0.1,
                "description": "License plate text format quality"
            })
        
        return {
            "detection_id": detection_id,
            "overall_quality_score": round(quality_score, 2),
            "quality_grade": (
                "excellent" if quality_score >= 90 else
                "good" if quality_score >= 75 else
                "fair" if quality_score >= 60 else
                "poor"
            ),
            "quality_factors": quality_factors,
            "raw_metrics": {
                "detection_confidence": detection.confidence,
                "ocr_confidence": detection.ocr_confidence,
                "processing_time_ms": detection.processing_time_ms,
                "plate_text_length": len(detection.plate_text) if detection.plate_text else 0,
                "bbox_area": (detection.bbox_width * detection.bbox_height) if (detection.bbox_width and detection.bbox_height) else 0
            }
        }
        
    except Exception as e:
        log_and_raise_error(e, f"Failed to get quality metrics for detection {detection_id}")

@router.get("/object-types", dependencies=[Depends(require_detection_view)])
async def get_object_types():
    """Get available object types for detection"""
    return {
        "object_types": [
            "license_plate",
            "vehicle",
            "car",
            "truck", 
            "motorcycle",
            "bus"
        ],
        "primary_type": "license_plate",
        "description": "Available object types for detection filtering"
    }