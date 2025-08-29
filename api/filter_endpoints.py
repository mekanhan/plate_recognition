"""
Detection Filter Monitoring API Endpoints

Provides monitoring and management endpoints for the detection filter system.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from ai_pipeline.filtered_pipeline import get_filtered_pipeline
from ai_pipeline.detection_filter import get_detection_filter
from auth.dependencies import get_optional_user
from auth.models import User

logger = logging.getLogger("FilterAPI")

router = APIRouter(prefix="/api/filter", tags=["detection-filter"])


class FilterStatsResponse(BaseModel):
    total_processed: int
    stored: int
    ignored_duplicates: int
    quality_updates: int
    re_entries: int
    reduction_rate: float
    active_cameras: int
    total_tracked_objects: int


class CameraTrackingResponse(BaseModel):
    camera_id: str
    tracked_objects: int
    objects: List[Dict[str, Any]]


class FilterActivityItem(BaseModel):
    timestamp: str
    camera_id: str
    plate_text: str
    action: str  # 'stored', 'filtered', 'updated'
    reason: str
    confidence: float


@router.get("/stats", response_model=FilterStatsResponse)
async def get_filter_statistics(
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get current detection filter statistics"""
    try:
        pipeline = get_filtered_pipeline()
        stats = pipeline.get_filter_stats()
        
        return FilterStatsResponse(
            total_processed=stats.get('total_processed', 0),
            stored=stats.get('stored', 0),
            ignored_duplicates=stats.get('ignored_duplicates', 0),
            quality_updates=stats.get('quality_updates', 0),
            re_entries=stats.get('re_entries', 0),
            reduction_rate=stats.get('reduction_rate', 0.0),
            active_cameras=stats.get('active_cameras', 0),
            total_tracked_objects=stats.get('total_tracked_objects', 0)
        )
        
    except Exception as e:
        logger.error(f"Error getting filter statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get filter statistics")


@router.get("/performance")
async def get_filter_performance(
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get comprehensive filter performance metrics"""
    try:
        pipeline = get_filtered_pipeline()
        performance = pipeline.get_performance_stats()
        
        return {
            "filter_stats": pipeline.get_filter_stats(),
            "performance_metrics": performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting filter performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get filter performance")


@router.get("/cameras/{camera_id}/tracking", response_model=CameraTrackingResponse)
async def get_camera_tracking_status(
    camera_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get tracking status for a specific camera"""
    try:
        pipeline = get_filtered_pipeline()
        tracking_data = pipeline.get_camera_tracking_status(camera_id)
        
        return CameraTrackingResponse(
            camera_id=camera_id,
            tracked_objects=tracking_data.get('tracked_objects', 0),
            objects=tracking_data.get('objects', [])
        )
        
    except Exception as e:
        logger.error(f"Error getting camera tracking status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get camera tracking status")


@router.post("/cameras/{camera_id}/reset")
async def reset_camera_tracking(
    camera_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Reset tracking data for a specific camera"""
    try:
        pipeline = get_filtered_pipeline()
        pipeline.reset_camera_tracking(camera_id)
        
        return {
            "message": f"Tracking data reset for camera {camera_id}",
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting camera tracking: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset camera tracking")


@router.get("/cameras")
async def get_all_cameras_tracking(
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get tracking status for all active cameras"""
    try:
        filter_instance = get_detection_filter()
        stats = filter_instance.get_stats()
        
        # Get tracking data for all active cameras
        cameras_data = []
        
        # Note: This is a simplified version since we don't have direct access to camera IDs
        # In a real implementation, you'd iterate through active cameras
        return {
            "active_cameras": stats.get('active_cameras', 0),
            "total_tracked_objects": stats.get('total_tracked_objects', 0),
            "summary": {
                "total_processed": stats.get('total_processed', 0),
                "reduction_rate": stats.get('reduction_rate', 0.0),
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting all cameras tracking: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cameras tracking status")


@router.get("/activity")
async def get_filter_activity_log(
    limit: int = Query(50, description="Maximum number of activity items"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get recent filter activity (simulated for demo)"""
    try:
        # Note: This is a simplified implementation for demo purposes
        # In a real implementation, you'd maintain an activity log
        
        filter_instance = get_detection_filter()
        stats = filter_instance.get_stats()
        
        # Generate sample activity based on current stats
        activity_items = []
        
        # Simulate recent activity
        import random
        sample_plates = ['ABC123', 'XYZ789', 'DEF456', 'GHI012', 'JKL345']
        sample_cameras = ['camera_01', 'camera_02', 'camera_03']
        actions = [
            ('stored', 'new_detection'),
            ('filtered', 'duplicate'),
            ('stored', 'quality_update'),
            ('filtered', 'no_significant_change'),
            ('stored', 're_entry')
        ]
        
        for i in range(min(limit, 20)):  # Generate up to 20 sample items
            plate = random.choice(sample_plates)
            camera = camera_id if camera_id else random.choice(sample_cameras)
            action, reason = random.choice(actions)
            
            activity_items.append({
                "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                "camera_id": camera,
                "plate_text": plate,
                "action": action,
                "reason": reason,
                "confidence": round(random.uniform(0.7, 0.98), 2)
            })
        
        return {
            "activity": activity_items,
            "filter_stats": stats,
            "pagination": {
                "limit": limit,
                "total_items": len(activity_items)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting filter activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to get filter activity")


@router.get("/health")
async def get_filter_health():
    """Get filter system health status"""
    try:
        filter_instance = get_detection_filter()
        pipeline = get_filtered_pipeline()
        
        # Check if components are working
        stats = filter_instance.get_stats()
        performance = pipeline.get_performance_stats()
        
        # Determine health status
        is_healthy = True
        issues = []
        
        # Check if filter is processing detections
        if stats.get('total_processed', 0) == 0:
            issues.append("No detections processed yet")
        
        # Check reduction rate (should be > 0 if there are duplicates)
        reduction_rate = stats.get('reduction_rate', 0)
        if reduction_rate > 95:
            issues.append("Very high reduction rate - possible over-filtering")
        
        health_status = "healthy" if is_healthy and not issues else "warning"
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "detection_filter": "active",
                "filtered_pipeline": "active",
                "statistics_collection": "active"
            },
            "metrics": {
                "total_processed": stats.get('total_processed', 0),
                "reduction_rate": reduction_rate,
                "active_cameras": stats.get('active_cameras', 0)
            },
            "issues": issues
        }
        
    except Exception as e:
        logger.error(f"Error getting filter health: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }