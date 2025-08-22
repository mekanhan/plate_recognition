"""
Storage Management API Endpoints
Provides REST API for storage monitoring and cleanup operations
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging

try:
    from core.storage.media_retention_manager import MediaRetentionManager
    HAS_RETENTION_MANAGER = True
except ImportError:
    HAS_RETENTION_MANAGER = False

logger = logging.getLogger(__name__)

# Storage management router
storage_router = APIRouter(prefix="/api/v1/storage", tags=["storage"])

# Global retention manager instance
retention_manager = None

def get_retention_manager():
    """Get or create retention manager instance"""
    global retention_manager
    if retention_manager is None and HAS_RETENTION_MANAGER:
        retention_manager = MediaRetentionManager()
    return retention_manager


@storage_router.get("/status")
async def get_storage_status():
    """Get comprehensive storage status for all managed directories"""
    if not HAS_RETENTION_MANAGER:
        raise HTTPException(status_code=501, detail="Storage management not available")
    
    try:
        manager = get_retention_manager()
        if not manager:
            raise HTTPException(status_code=500, detail="Failed to initialize storage manager")
        
        overview = await manager.get_storage_overview()
        return {
            "status": "success",
            "data": overview,
            "timestamp": overview.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Error getting storage status: {e}")
        raise HTTPException(status_code=500, detail=f"Storage status error: {str(e)}")


@storage_router.get("/policies")
async def get_retention_policies():
    """Get current retention policies"""
    if not HAS_RETENTION_MANAGER:
        raise HTTPException(status_code=501, detail="Storage management not available")
    
    try:
        manager = get_retention_manager()
        if not manager:
            raise HTTPException(status_code=500, detail="Failed to initialize storage manager")
        
        policies_info = []
        for policy in manager.policies:
            policies_info.append({
                "path": policy.path,
                "max_age_days": policy.max_age_days,
                "max_size_gb": policy.max_size_gb,
                "cleanup_threshold": policy.cleanup_threshold,
                "emergency_cleanup_threshold": policy.emergency_cleanup_threshold,
                "min_free_space_gb": policy.min_free_space_gb,
                "file_patterns": policy.file_patterns,
                "priority": policy.priority
            })
        
        return {
            "status": "success",
            "data": {
                "policies": policies_info,
                "total_policies": len(policies_info)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting retention policies: {e}")
        raise HTTPException(status_code=500, detail=f"Policies error: {str(e)}")


@storage_router.post("/cleanup")
async def trigger_storage_cleanup(
    policy_path: Optional[str] = Query(None, description="Specific policy path to cleanup (optional)"),
    force: bool = Query(False, description="Force cleanup regardless of thresholds")
):
    """Trigger storage cleanup for specific policy or all policies"""
    if not HAS_RETENTION_MANAGER:
        raise HTTPException(status_code=501, detail="Storage management not available")
    
    try:
        manager = get_retention_manager()
        if not manager:
            raise HTTPException(status_code=500, detail="Failed to initialize storage manager")
        
        logger.info(f"Cleanup triggered via API - policy_path: {policy_path}, force: {force}")
        
        cleanup_result = await manager.perform_cleanup(
            policy_path=policy_path,
            force=force
        )
        
        return {
            "status": "success",
            "data": cleanup_result,
            "message": f"Cleanup completed: {cleanup_result['total_files_deleted']} files deleted, "
                      f"{cleanup_result['total_bytes_freed'] / (1024**3):.2f}GB freed"
        }
        
    except Exception as e:
        logger.error(f"Error during storage cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")


@storage_router.get("/statistics")
async def get_storage_statistics():
    """Get detailed storage statistics for monitoring and alerting"""
    if not HAS_RETENTION_MANAGER:
        raise HTTPException(status_code=501, detail="Storage management not available")
    
    try:
        manager = get_retention_manager()
        if not manager:
            raise HTTPException(status_code=500, detail="Failed to initialize storage manager")
        
        overview = await manager.get_storage_overview()
        
        # Calculate additional statistics
        statistics = {
            "summary": {
                "total_managed_size_gb": overview["total_managed_size_gb"],
                "total_files": overview["total_files"],
                "cleanup_recommended": overview["cleanup_recommended"],
                "emergency_cleanup_required": overview["emergency_cleanup_required"]
            },
            "system_disk": overview.get("system_disk_usage", {}),
            "cleanup_history": overview.get("cleanup_history", {}),
            "policies": []
        }
        
        # Detailed per-policy statistics
        for policy_info in overview["policies"]:
            stats = policy_info["stats"]
            policy = policy_info["policy"]
            
            # Calculate additional metrics
            avg_file_size_mb = (stats["total_size_gb"] * 1024) / max(stats["file_count"], 1)
            age_range_days = stats["oldest_file_age_days"] - stats["newest_file_age_days"]
            
            policy_stats = {
                "path": policy_info["path"],
                "size": {
                    "total_gb": stats["total_size_gb"],
                    "usage_percentage": stats["usage_percentage"],
                    "limit_gb": policy["max_size_gb"],
                    "available_gb": max(0, policy["max_size_gb"] - stats["total_size_gb"])
                },
                "files": {
                    "count": stats["file_count"],
                    "avg_size_mb": round(avg_file_size_mb, 2)
                },
                "age": {
                    "oldest_days": stats["oldest_file_age_days"],
                    "newest_days": stats["newest_file_age_days"],
                    "range_days": age_range_days
                },
                "health": {
                    "requires_cleanup": stats["requires_cleanup"],
                    "priority": stats["priority"],
                    "status": "critical" if stats["usage_percentage"] > 95 else 
                             "warning" if stats["usage_percentage"] > 85 else "healthy"
                }
            }
            
            statistics["policies"].append(policy_stats)
        
        return {
            "status": "success",
            "data": statistics,
            "timestamp": overview.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Error getting storage statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics error: {str(e)}")


@storage_router.get("/health")
async def get_storage_health():
    """Get storage health status for health monitoring systems"""
    if not HAS_RETENTION_MANAGER:
        return {
            "status": "unavailable",
            "message": "Storage management not available",
            "health": "unknown"
        }
    
    try:
        manager = get_retention_manager()
        if not manager:
            return {
                "status": "error",
                "message": "Failed to initialize storage manager",
                "health": "critical"
            }
        
        overview = await manager.get_storage_overview()
        
        # Determine overall health status
        if overview["emergency_cleanup_required"]:
            health_status = "critical"
            message = "Emergency cleanup required"
        elif overview["cleanup_recommended"]:
            health_status = "warning"
            message = "Cleanup recommended"
        else:
            health_status = "healthy"
            message = "Storage within acceptable limits"
        
        # Check system disk usage
        system_disk = overview.get("system_disk_usage", {})
        if system_disk.get("percentage_used", 0) > 95:
            health_status = "critical"
            message = "System disk critically full"
        elif system_disk.get("percentage_used", 0) > 85:
            if health_status != "critical":
                health_status = "warning"
                message = "System disk usage high"
        
        return {
            "status": "success",
            "health": health_status,
            "message": message,
            "data": {
                "total_managed_gb": overview["total_managed_size_gb"],
                "total_files": overview["total_files"],
                "system_disk_usage_percent": system_disk.get("percentage_used", 0),
                "emergency_cleanup_required": overview["emergency_cleanup_required"],
                "cleanup_recommended": overview["cleanup_recommended"]
            },
            "timestamp": overview.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Error getting storage health: {e}")
        return {
            "status": "error",
            "health": "critical",
            "message": f"Health check error: {str(e)}"
        }