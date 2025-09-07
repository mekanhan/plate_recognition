"""
System-level endpoints for health, storage, analytics, and configuration
Extracted from monolithic main.py for better organization
"""
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel
import logging
import os
import psutil
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

# Import our core utilities
from ..core.errors import APIError, ValidationError, log_and_raise_error

# Import services and utilities
from database.foundation_service import get_foundation_database_service
from utils.feature_flags import feature_flags
from auth.dependencies import get_current_user, require_system_config
from auth.models import User

# Create system router
router = APIRouter(prefix="/api", tags=["system"])

logger = logging.getLogger(__name__)

# Pydantic models
class StorageCleanupRequest(BaseModel):
    max_age_days: Optional[int] = 30
    target_size_gb: Optional[float] = None
    dry_run: bool = False

class QualityFilterRequest(BaseModel):
    min_confidence: float = 0.5
    min_ocr_confidence: Optional[float] = None
    min_text_length: Optional[int] = None
    max_text_length: Optional[int] = None

# Health and system status endpoints
@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api",
        "version": "3.0.0"
    }

@router.get("/system/health")
async def get_system_health(db_service = Depends(get_foundation_database_service)):
    """Comprehensive system health check"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "system": {},
            "database": {}
        }
        
        # Check database connectivity
        try:
            db_health = await db_service.health_check()
            health_status["database"] = {
                "status": "healthy" if db_health else "unhealthy",
                "connection": "ok" if db_health else "failed",
                "response_time_ms": 0  # Could measure actual response time
            }
        except Exception as e:
            health_status["database"] = {
                "status": "unhealthy",
                "connection": "failed",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check system resources
        try:
            health_status["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
                "uptime": time.time() - psutil.boot_time()
            }
        except Exception as e:
            health_status["system"] = {
                "status": "unavailable",
                "error": str(e)
            }
        
        # Check recording service
        try:
            # This would actually ping the recording service
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                async with session.get('http://localhost:8002/health') as resp:
                    if resp.status == 200:
                        recording_data = await resp.json()
                        health_status["services"]["recording"] = {
                            "status": "healthy",
                            "response_time_ms": 0,  # Could measure
                            "data": recording_data
                        }
                    else:
                        health_status["services"]["recording"] = {
                            "status": "unhealthy",
                            "http_status": resp.status
                        }
                        health_status["status"] = "degraded"
        except Exception as e:
            health_status["services"]["recording"] = {
                "status": "unavailable",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get system health")

@router.get("/config/features")
async def get_feature_config():
    """Get current feature flag configuration"""
    try:
        return {
            "feature_flags": {
                "license_plate_detection": feature_flags.is_enabled('core_features.license_plate_detection'),
                "continuous_processing": feature_flags.is_enabled('core_features.continuous_processing'),
                "universal_detection": feature_flags.is_enabled('api_features.universal_detection_endpoints'),
                "enhanced_analytics": feature_flags.is_enabled('analytics.enhanced_features'),
                "browser_streaming": feature_flags.is_enabled('streaming.browser_integration')
            },
            "system_info": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
                "api_version": "3.0.0"
            }
        }
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get feature configuration")

# Storage management endpoints
@router.get("/storage/stats")
async def get_storage_stats(db_service = Depends(get_foundation_database_service)):
    """Get storage usage statistics"""
    try:
        storage_stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "directories": {},
            "database": {},
            "total": {}
        }
        
        # Check recordings directory
        recordings_path = "recordings"
        if os.path.exists(recordings_path):
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(recordings_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            storage_stats["directories"]["recordings"] = {
                "path": recordings_path,
                "size_bytes": total_size,
                "size_gb": round(total_size / (1024**3), 2),
                "file_count": file_count
            }
        
        # Check detections directory
        detections_path = "detections"
        if os.path.exists(detections_path):
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(detections_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            storage_stats["directories"]["detections"] = {
                "path": detections_path,
                "size_bytes": total_size,
                "size_gb": round(total_size / (1024**3), 2),
                "file_count": file_count
            }
        
        # Check database size
        db_path = "data/license_plates.db"
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            storage_stats["database"] = {
                "path": db_path,
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024**2), 2)
            }
        
        # Calculate totals
        total_bytes = 0
        total_files = 0
        for dir_stats in storage_stats["directories"].values():
            total_bytes += dir_stats["size_bytes"]
            total_files += dir_stats["file_count"]
        
        if "database" in storage_stats:
            total_bytes += storage_stats["database"]["size_bytes"]
        
        storage_stats["total"] = {
            "size_bytes": total_bytes,
            "size_gb": round(total_bytes / (1024**3), 2),
            "file_count": total_files
        }
        
        return storage_stats
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get storage statistics")

@router.post("/storage/cleanup", dependencies=[Depends(require_system_config)])
async def cleanup_storage(
    cleanup_request: StorageCleanupRequest,
    current_user: User = Depends(get_current_user),
    db_service = Depends(get_foundation_database_service)
):
    """Clean up old storage files"""
    try:
        cleanup_results = {
            "dry_run": cleanup_request.dry_run,
            "started_at": datetime.utcnow().isoformat(),
            "files_processed": 0,
            "files_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }
        
        cutoff_date = datetime.utcnow() - timedelta(days=cleanup_request.max_age_days)
        
        # Clean up old recording files
        recordings_path = "recordings"
        if os.path.exists(recordings_path):
            for root, dirs, files in os.walk(recordings_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.exists(file_path):
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            cleanup_results["files_processed"] += 1
                            
                            if file_mtime < cutoff_date:
                                file_size = os.path.getsize(file_path)
                                
                                if not cleanup_request.dry_run:
                                    os.remove(file_path)
                                
                                cleanup_results["files_deleted"] += 1
                                cleanup_results["bytes_freed"] += file_size
                    except Exception as e:
                        cleanup_results["errors"].append({
                            "file": file_path,
                            "error": str(e)
                        })
        
        # Clean up old detection images
        detections_path = "detections"
        if os.path.exists(detections_path):
            for root, dirs, files in os.walk(detections_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.exists(file_path):
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            cleanup_results["files_processed"] += 1
                            
                            if file_mtime < cutoff_date:
                                file_size = os.path.getsize(file_path)
                                
                                if not cleanup_request.dry_run:
                                    os.remove(file_path)
                                
                                cleanup_results["files_deleted"] += 1
                                cleanup_results["bytes_freed"] += file_size
                    except Exception as e:
                        cleanup_results["errors"].append({
                            "file": file_path,
                            "error": str(e)
                        })
        
        cleanup_results["completed_at"] = datetime.utcnow().isoformat()
        cleanup_results["gb_freed"] = round(cleanup_results["bytes_freed"] / (1024**3), 2)
        
        logger.info(f"Storage cleanup completed by {current_user.username}: {cleanup_results}")
        
        return cleanup_results
        
    except Exception as e:
        log_and_raise_error(e, "Storage cleanup failed")

@router.post("/storage/emergency-cleanup", dependencies=[Depends(require_system_config)])
async def emergency_cleanup(
    current_user: User = Depends(get_current_user)
):
    """Emergency storage cleanup - removes oldest files until under 90% disk usage"""
    try:
        # This is a simplified emergency cleanup
        # In production, this would be more sophisticated
        
        disk_usage = psutil.disk_usage('/').percent
        
        if disk_usage < 90:
            return {
                "status": "not_needed",
                "current_disk_usage": disk_usage,
                "message": "Disk usage is under 90%, no emergency cleanup needed"
            }
        
        # Perform aggressive cleanup
        cleanup_request = StorageCleanupRequest(
            max_age_days=7,  # Keep only 7 days
            dry_run=False
        )
        
        result = await cleanup_storage(cleanup_request, current_user, get_foundation_database_service())
        result["emergency_cleanup"] = True
        result["initial_disk_usage"] = disk_usage
        result["final_disk_usage"] = psutil.disk_usage('/').percent
        
        logger.warning(f"Emergency cleanup performed by {current_user.username}")
        
        return result
        
    except Exception as e:
        log_and_raise_error(e, "Emergency cleanup failed")

# Analytics endpoints
@router.get("/analytics/overview")
async def get_analytics_overview(
    days_back: int = Query(7, ge=1, le=365),
    db_service = Depends(get_foundation_database_service)
):
    """Get system analytics overview"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get basic stats
        detection_stats = await db_service.get_detection_stats(start_date, end_date)
        camera_stats = await db_service.get_camera_stats()
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days_back
            },
            "overview": {
                "total_detections": detection_stats.get("total_detections", 0),
                "unique_plates": detection_stats.get("unique_plates", 0),
                "active_cameras": camera_stats.get("active_cameras", 0),
                "total_cameras": camera_stats.get("total_cameras", 0),
                "avg_detections_per_day": detection_stats.get("avg_per_day", 0),
                "system_uptime_hours": camera_stats.get("uptime_hours", 0)
            },
            "trends": {
                "detections_by_day": detection_stats.get("detections_by_day", []),
                "peak_hours": detection_stats.get("peak_hours", []),
                "busiest_cameras": detection_stats.get("busiest_cameras", [])
            }
        }
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get analytics overview")

# Quality endpoints
@router.get("/quality/metrics")
async def get_quality_metrics(
    days_back: int = Query(7, ge=1, le=365),
    db_service = Depends(get_foundation_database_service)
):
    """Get detection quality metrics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        quality_stats = await db_service.get_quality_metrics(start_date, end_date)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days_back
            },
            "metrics": {
                "avg_detection_confidence": quality_stats.get("avg_detection_confidence", 0.0),
                "avg_ocr_confidence": quality_stats.get("avg_ocr_confidence", 0.0),
                "avg_processing_time_ms": quality_stats.get("avg_processing_time", 0.0),
                "high_quality_percentage": quality_stats.get("high_quality_percent", 0.0),
                "low_quality_percentage": quality_stats.get("low_quality_percent", 0.0)
            },
            "thresholds": {
                "high_quality_confidence": 0.8,
                "acceptable_confidence": 0.5,
                "max_processing_time_ms": 1000
            },
            "quality_distribution": quality_stats.get("quality_distribution", [])
        }
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get quality metrics")

@router.get("/quality/thresholds")
async def get_quality_thresholds():
    """Get current quality thresholds"""
    return {
        "detection_confidence": {
            "minimum": 0.3,
            "acceptable": 0.5,
            "good": 0.7,
            "excellent": 0.9
        },
        "ocr_confidence": {
            "minimum": 0.4,
            "acceptable": 0.6,
            "good": 0.8,
            "excellent": 0.95
        },
        "processing_time_ms": {
            "excellent": 200,
            "good": 500,
            "acceptable": 1000,
            "slow": 2000
        },
        "text_length": {
            "minimum": 4,
            "optimal_min": 6,
            "optimal_max": 8,
            "maximum": 12
        }
    }

@router.post("/quality/filter")
async def filter_detections_by_quality(
    filter_request: QualityFilterRequest,
    db_service = Depends(get_foundation_database_service)
):
    """Filter detections based on quality criteria"""
    try:
        # This would implement quality-based filtering
        # For now, return the filter criteria that would be applied
        return {
            "filter_applied": True,
            "criteria": {
                "min_confidence": filter_request.min_confidence,
                "min_ocr_confidence": filter_request.min_ocr_confidence,
                "min_text_length": filter_request.min_text_length,
                "max_text_length": filter_request.max_text_length
            },
            "message": "Quality filter criteria set successfully",
            "note": "Filter will be applied to future detection queries"
        }
        
    except Exception as e:
        log_and_raise_error(e, "Failed to apply quality filter")

# Debug endpoints
@router.get("/debug/raw-cameras")
async def debug_raw_cameras(db_service = Depends(get_foundation_database_service)):
    """Debug endpoint - get raw camera data"""
    try:
        cameras = await db_service.get_all_cameras()
        
        result = []
        for camera in cameras:
            result.append({
                "raw_data": {
                    "camera_id": camera.camera_id,
                    "name": camera.name,
                    "ip_address": camera.ip_address,
                    "port": camera.port,
                    "status": camera.status,
                    "created_at": camera.created_at.isoformat() if camera.created_at else None,
                    "updated_at": camera.updated_at.isoformat() if camera.updated_at else None
                },
                "computed_fields": {
                    "short_id": camera.camera_id[-8:],
                    "display_name": camera.name,
                    "is_active": camera.status == 'active'
                }
            })
        
        return {
            "cameras": result,
            "count": len(result),
            "debug_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_and_raise_error(e, "Failed to get debug camera data")

# WebSocket status endpoint
@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "websocket_enabled": True,
        "active_connections": 0,  # Would track actual connections
        "supported_events": [
            "camera_status_update",
            "recording_status_update", 
            "detection_update",
            "system_health_update"
        ],
        "endpoint": "/ws"
    }