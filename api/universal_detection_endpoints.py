"""
Universal Detection API Endpoints
Supports searching and managing detections for any object type
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from database.service import DatabaseService
from auth.dependencies import require_detection_view, get_optional_user
from auth.models import User

logger = logging.getLogger("UniversalDetectionAPI")

router = APIRouter(prefix="/api/v2", tags=["universal-detections"])


# Pydantic models
class ObjectTypeResponse(BaseModel):
    type_code: str
    display_name: str
    icon: str
    color: str
    priority: int
    active: bool
    metadata_schema: Dict[str, Any]


class UniversalDetectionResponse(BaseModel):
    id: str
    camera_id: str
    object_type: str
    confidence: float
    detected_at: datetime
    bbox: Dict[str, int]
    frame_path: Optional[str]
    object_image_path: Optional[str]
    video_clip_id: Optional[str]
    video_thumbnail_path: Optional[str]
    metadata: Dict[str, Any]
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    tags: List[str]
    flagged: bool
    processing_time_ms: Optional[int]
    model_version: Optional[str]
    created_at: datetime
    updated_at: datetime


class SearchFilters(BaseModel):
    object_types: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    camera_ids: Optional[List[str]] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    status: Optional[str] = None
    flagged: Optional[bool] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    limit: int = 50
    offset: int = 0


class SmartSearchRequest(BaseModel):
    query: str
    filters: Optional[SearchFilters] = None


class DetectionUpdateRequest(BaseModel):
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    flagged: Optional[bool] = None


# Database connection
async def get_db():
    db = DatabaseService()
    try:
        yield db
    finally:
        await db.close()


@router.get("/object-types", response_model=List[ObjectTypeResponse])
async def get_object_types(
    active_only: bool = Query(True, description="Return only active object types"),
    db: DatabaseService = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get all available object types for filtering"""
    try:
        from sqlalchemy import text
        
        query = "SELECT * FROM object_types"
        if active_only:
            query += " WHERE active = TRUE"
        query += " ORDER BY priority ASC"
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text(query))
            rows = result.fetchall()
        
        object_types = []
        for row in rows:
            object_types.append(ObjectTypeResponse(
                type_code=row.type_code,
                display_name=row.display_name,
                icon=row.icon,
                color=row.color,
                priority=row.priority,
                active=row.active,
                metadata_schema=json.loads(row.metadata_schema) if row.metadata_schema else {}
            ))
        
        return object_types
        
    except Exception as e:
        logger.error(f"Error fetching object types: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch object types")


@router.get("/detections", response_model=Dict[str, Any])
async def search_detections(
    object_type: Optional[str] = Query(None, description="Filter by object type"),
    start_date: Optional[datetime] = Query(None, description="Start date for search"),
    end_date: Optional[datetime] = Query(None, description="End date for search"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    min_confidence: Optional[float] = Query(None, description="Minimum confidence threshold"),
    status: Optional[str] = Query(None, description="Detection status filter"),
    flagged: Optional[bool] = Query(None, description="Filter flagged detections"),
    limit: int = Query(50, description="Maximum results to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: DatabaseService = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Search universal detections with various filters"""
    try:
        from sqlalchemy import text
        
        # Build query conditions
        conditions = []
        params = {}
        
        if object_type:
            conditions.append("object_type = :object_type")
            params["object_type"] = object_type
        
        if start_date:
            conditions.append("detected_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("detected_at <= :end_date")
            params["end_date"] = end_date
        
        if camera_id:
            conditions.append("camera_id = :camera_id")
            params["camera_id"] = camera_id
        
        if min_confidence is not None:
            conditions.append("confidence >= :min_confidence")
            params["min_confidence"] = min_confidence
        
        if status:
            conditions.append("status = :status")
            params["status"] = status
        
        if flagged is not None:
            conditions.append("flagged = :flagged")
            params["flagged"] = flagged
        
        # Build WHERE clause
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Count total results
        count_query = f"""
            SELECT COUNT(*) as total
            FROM detections
            {where_clause}
        """
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            count_result = await conn.execute(text(count_query), params)
            total_count = count_result.fetchone().total
        
        # Get paginated results
        search_query = f"""
            SELECT d.*, 'License Plate' as object_type_name, 'car' as icon, '#4CAF50' as color
            FROM detections d
            {where_clause}
            ORDER BY ud.detected_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params.update({"limit": limit, "offset": offset})
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text(search_query), params)
            rows = result.fetchall()
        
        # Convert to response format
        detections = []
        for row in rows:
            # Handle datetime fields that may be strings from SQLite
            def safe_isoformat(dt_field):
                if dt_field is None:
                    return None
                if isinstance(dt_field, str):
                    return dt_field  # Already a string, likely from SQLite
                return dt_field.isoformat()  # Convert datetime object to string
            
            # Dynamically construct image paths if not in database
            frame_path = row.frame_path
            object_image_path = row.object_image_path
            
            if not frame_path or not object_image_path:
                import os
                detection_id = row.id
                
                # Check if image files exist and construct paths
                if not frame_path:
                    frame_file_path = f"detections/frames/{detection_id}_frame.jpg"
                    if os.path.exists(frame_file_path):
                        frame_path = frame_file_path
                
                if not object_image_path:
                    plate_file_path = f"detections/plates/{detection_id}_plate.jpg"
                    if os.path.exists(plate_file_path):
                        object_image_path = plate_file_path
            
            detections.append({
                "id": row.id,
                "camera_id": row.camera_id,
                "object_type": row.object_type,
                "object_type_name": row.object_type_name,
                "icon": row.icon,
                "color": row.color,
                "confidence": row.confidence,
                "detected_at": safe_isoformat(row.detected_at),
                "bbox": json.loads(row.bbox) if row.bbox else {},
                "frame_path": frame_path,
                "object_image_path": object_image_path,
                "video_clip_id": row.video_clip_id,
                "video_thumbnail_path": row.video_thumbnail_path,
                "metadata": json.loads(row.metadata) if row.metadata else {},
                "status": row.status,
                "reviewed_by": row.reviewed_by,
                "reviewed_at": safe_isoformat(row.reviewed_at),
                "tags": json.loads(row.tags) if row.tags else [],
                "flagged": row.flagged,
                "processing_time_ms": row.processing_time_ms,
                "model_version": row.model_version,
                "created_at": safe_isoformat(row.created_at),
                "updated_at": safe_isoformat(row.updated_at)
            })
        
        return {
            "detections": detections,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "filters_applied": {
                "object_type": object_type,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "camera_id": camera_id,
                "min_confidence": min_confidence,
                "status": status,
                "flagged": flagged
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching detections: {e}")
        raise HTTPException(status_code=500, detail="Failed to search detections")


@router.post("/detections/search", response_model=Dict[str, Any])
async def smart_search_detections(
    search_request: SmartSearchRequest,
    db: DatabaseService = Depends(get_db),
    current_user: Optional[User] = Depends(require_detection_view)
):
    """Smart search with natural language processing"""
    try:
        # For now, implement basic keyword search
        # This can be enhanced with NLP later
        query = search_request.query.lower()
        
        # Parse basic keywords
        object_type = None
        if "vehicle" in query or "car" in query:
            object_type = "vehicle"
        elif "person" in query or "people" in query:
            object_type = "person"
        elif "package" in query or "box" in query:
            object_type = "package"
        
        # Build filters
        filters = search_request.filters or SearchFilters()
        if object_type and not filters.object_types:
            filters.object_types = [object_type]
        
        # Use regular search endpoint logic
        return await search_detections(
            object_type=filters.object_types[0] if filters.object_types else None,
            start_date=filters.start_date,
            end_date=filters.end_date,
            camera_id=filters.camera_ids[0] if filters.camera_ids else None,
            min_confidence=filters.min_confidence,
            status=filters.status,
            flagged=filters.flagged,
            limit=filters.limit,
            offset=filters.offset,
            db=db,
            current_user=current_user
        )
        
    except Exception as e:
        logger.error(f"Error in smart search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform smart search")


@router.get("/license-plates/recent")
async def get_recent_license_plates(
    limit: int = Query(100, ge=1, le=500),
    camera_id: Optional[str] = Query(None),
    db: DatabaseService = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get recent license plate detections specifically"""
    try:
        from sqlalchemy import text
        import json
        
        # Build query for license plates
        conditions = ["object_type = 'vehicle'", "metadata LIKE '%plate_text%'"]
        params = {"limit": limit}
        
        if camera_id:
            conditions.append("camera_id = :camera_id")
            params["camera_id"] = camera_id
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        query = f"""
            SELECT id, camera_id, confidence, detected_at,
                   metadata, plate_image_path as object_image_path, frame_image_path as frame_path
            FROM detections
            {where_clause}
            ORDER BY detected_at DESC
            LIMIT :limit
        """
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text(query), params)
            rows = result.fetchall()
        
        detections = []
        for row in rows:
            metadata = json.loads(row.metadata) if row.metadata else {}
            detections.append({
                "id": row.id,
                "camera_id": row.camera_id,
                "plate_text": metadata.get('plate_text', 'unknown'),
                "confidence": row.confidence,
                "vehicle_type": metadata.get('vehicle_type', 'unknown'),
                "detected_at": row.detected_at.isoformat() if hasattr(row.detected_at, 'isoformat') else str(row.detected_at),
                "plate_image": row.object_image_path,
                "frame_image": row.frame_path,
                "ocr_confidence": metadata.get('ocr_confidence')
            })
        
        return {
            "total": len(detections),
            "detections": detections
        }
        
    except Exception as e:
        logger.error(f"Error getting recent license plates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent license plates")


@router.get("/detections/{detection_id}")
async def get_detection_details(
    detection_id: str,
    db: DatabaseService = Depends(get_db),
    current_user: Optional[User] = Depends(require_detection_view)
):
    """Get detailed information for a specific detection"""
    try:
        from sqlalchemy import text
        
        query = """
            SELECT d.*, 'License Plate' as object_type_name, 'car' as icon, '#4CAF50' as color
            FROM detections d
            WHERE ud.id = :detection_id
        """
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text(query), {"detection_id": detection_id})
            row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        # Handle datetime fields that may be strings from SQLite
        def safe_isoformat(dt_field):
            if dt_field is None:
                return None
            if isinstance(dt_field, str):
                return dt_field  # Already a string, likely from SQLite
            return dt_field.isoformat()  # Convert datetime object to string
        
        # Dynamically construct image paths if not in database
        frame_path = row.frame_path
        object_image_path = row.object_image_path
        
        if not frame_path or not object_image_path:
            import os
            detection_id = row.id
            
            # Check if image files exist and construct paths
            if not frame_path:
                frame_file_path = f"detections/frames/{detection_id}_frame.jpg"
                if os.path.exists(frame_file_path):
                    frame_path = frame_file_path
            
            if not object_image_path:
                plate_file_path = f"detections/plates/{detection_id}_plate.jpg"
                if os.path.exists(plate_file_path):
                    object_image_path = plate_file_path
        
        return {
            "id": row.id,
            "camera_id": row.camera_id,
            "object_type": row.object_type,
            "object_type_name": row.object_type_name,
            "icon": row.icon,
            "color": row.color,
            "confidence": row.confidence,
            "detected_at": safe_isoformat(row.detected_at),
            "bbox": json.loads(row.bbox) if row.bbox else {},
            "frame_path": frame_path,
            "object_image_path": object_image_path,
            "video_clip_id": row.video_clip_id,
            "video_thumbnail_path": row.video_thumbnail_path,
            "metadata": json.loads(row.metadata) if row.metadata else {},
            "status": row.status,
            "reviewed_by": row.reviewed_by,
            "reviewed_at": safe_isoformat(row.reviewed_at),
            "tags": json.loads(row.tags) if row.tags else [],
            "flagged": row.flagged,
            "processing_time_ms": row.processing_time_ms,
            "model_version": row.model_version,
            "created_at": safe_isoformat(row.created_at),
            "updated_at": safe_isoformat(row.updated_at)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching detection details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch detection details")


@router.put("/detections/{detection_id}")
async def update_detection(
    detection_id: str,
    update_request: DetectionUpdateRequest,
    db: DatabaseService = Depends(get_db),
    current_user: User = Depends(require_detection_view)
):
    """Update detection status, tags, or flags"""
    try:
        from sqlalchemy import text
        
        # Build update fields
        update_fields = []
        params = {"detection_id": detection_id}
        
        if update_request.status is not None:
            update_fields.append("status = :status")
            params["status"] = update_request.status
            
            # Set reviewer info
            update_fields.append("reviewed_by = :reviewed_by")
            update_fields.append("reviewed_at = :reviewed_at")
            params["reviewed_by"] = current_user.username
            params["reviewed_at"] = datetime.now()
        
        if update_request.tags is not None:
            update_fields.append("tags = :tags")
            params["tags"] = json.dumps(update_request.tags)
        
        if update_request.flagged is not None:
            update_fields.append("flagged = :flagged")
            params["flagged"] = update_request.flagged
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Always update the updated_at timestamp
        update_fields.append("updated_at = :updated_at")
        params["updated_at"] = datetime.now()
        
        query = f"""
            UPDATE detections
            SET {', '.join(update_fields)}
            WHERE id = :detection_id
        """
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text(query), params)
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        return {"message": "Detection updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating detection: {e}")
        raise HTTPException(status_code=500, detail="Failed to update detection")


@router.get("/statistics")
async def get_detection_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    camera_id: Optional[str] = Query(None),
    db: DatabaseService = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get detection statistics and analytics"""
    try:
        from sqlalchemy import text
        
        # Build conditions
        conditions = []
        params = {}
        
        if start_date:
            conditions.append("detected_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("detected_at <= :end_date")
            params["end_date"] = end_date
        
        if camera_id:
            conditions.append("camera_id = :camera_id")
            params["camera_id"] = camera_id
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Get overall statistics from detections table
        stats_query = f"""
            SELECT 
                COUNT(*) as total_detections,
                COUNT(DISTINCT camera_id) as unique_cameras,
                AVG(confidence) as avg_confidence,
                0 as flagged_count
            FROM detections
            {where_clause}
        """
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            stats_result = await conn.execute(text(stats_query), params)
            stats_row = stats_result.fetchone()
        
        # Get vehicle type distribution from detections table
        type_query = f"""
            SELECT 
                vehicle_type as object_type,
                vehicle_type as display_name,
                '#4CAF50' as color,
                COUNT(*) as count
            FROM detections
            {where_clause}
            GROUP BY vehicle_type
            ORDER BY count DESC
        """
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            type_result = await conn.execute(text(type_query), params)
            type_rows = type_result.fetchall()
        
        # Get hourly distribution for the last 24 hours
        hourly_query = f"""
            SELECT 
                strftime('%H', detected_at) as hour,
                COUNT(*) as count
            FROM detections
            WHERE detected_at >= datetime('now', '-24 hours')
            {' AND ' + ' AND '.join(conditions) if conditions else ''}
            GROUP BY strftime('%H', detected_at)
            ORDER BY hour
        """
        
        engine = await db.get_engine()
        async with engine.begin() as conn:
            hourly_result = await conn.execute(text(hourly_query), params)
            hourly_rows = hourly_result.fetchall()
        
        return {
            "summary": {
                "total_detections": stats_row.total_detections,
                "unique_cameras": stats_row.unique_cameras,
                "avg_confidence": round(stats_row.avg_confidence or 0, 3),
                "flagged_count": stats_row.flagged_count
            },
            "object_type_distribution": [
                {
                    "object_type": row.object_type,
                    "display_name": row.display_name,
                    "color": row.color,
                    "count": row.count
                }
                for row in type_rows
            ],
            "hourly_distribution": [
                {
                    "hour": row.hour,
                    "count": row.count
                }
                for row in hourly_rows
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")