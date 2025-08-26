"""
Storage Management API Endpoints
Provides REST API for storage monitoring and cleanup operations
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os
import sqlite3
import json

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


# Enhanced Storage Monitoring Endpoints

class StorageStatsResponse(BaseModel):
    total_gb: float
    used_gb: float
    available_gb: float
    usage_percentage: float
    health_status: str
    cleanup_potential_gb: float

class CleanupPreviewResponse(BaseModel):
    old_images_count: int
    old_images_size_mb: float
    database_wal_size_mb: float
    total_cleanup_potential_gb: float


def get_disk_stats() -> Dict:
    """Get disk usage statistics using df command"""
    try:
        import subprocess
        result = subprocess.run(['df', '.'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        
        if len(lines) >= 2:
            parts = lines[1].split()
            total_kb = int(parts[1])
            used_kb = int(parts[2])
            available_kb = int(parts[3])
            
            total_gb = total_kb / (1024**2)
            used_gb = used_kb / (1024**2)
            available_gb = available_kb / (1024**2)
            usage_pct = (used_kb / total_kb) * 100
            
            return {
                "total_gb": total_gb,
                "used_gb": used_gb,
                "available_gb": available_gb,
                "usage_percentage": usage_pct
            }
    except Exception as e:
        logger.error(f"Failed to get disk stats: {e}")
    
    return {"total_gb": 0, "used_gb": 0, "available_gb": 0, "usage_percentage": 0}


def get_cleanup_potential() -> float:
    """Calculate potential storage savings from cleanup"""
    potential_gb = 0.0
    
    # Old detection images (>1 day)
    cutoff = (datetime.now() - timedelta(days=1)).timestamp()
    detection_path = Path("detections")
    
    try:
        for img_type in ['frames', 'plates']:
            img_dir = detection_path / img_type
            if img_dir.exists():
                for img_file in img_dir.glob('*.jpg'):
                    try:
                        if img_file.stat().st_mtime < cutoff:
                            potential_gb += img_file.stat().st_size / (1024**3)
                    except:
                        continue
    except Exception as e:
        logger.error(f"Error calculating image cleanup potential: {e}")
    
    # Database WAL file
    try:
        wal_path = "data/license_plates.db-wal"
        if os.path.exists(wal_path):
            potential_gb += os.path.getsize(wal_path) / (1024**3)
    except Exception as e:
        logger.error(f"Error calculating WAL cleanup potential: {e}")
    
    return potential_gb


def count_old_images(max_age_days: int = 1) -> Dict:
    """Count old detection images for cleanup preview"""
    cutoff = (datetime.now() - timedelta(days=max_age_days)).timestamp()
    
    old_count = 0
    old_size_mb = 0.0
    
    detection_path = Path("detections")
    try:
        for img_type in ['frames', 'plates']:
            img_dir = detection_path / img_type
            if img_dir.exists():
                for img_file in img_dir.glob('*.jpg'):
                    try:
                        if img_file.stat().st_mtime < cutoff:
                            old_count += 1
                            old_size_mb += img_file.stat().st_size / (1024**2)
                    except:
                        continue
    except Exception as e:
        logger.error(f"Error counting old images: {e}")
    
    return {"count": old_count, "size_mb": old_size_mb}


@storage_router.get("/stats/enhanced", response_model=StorageStatsResponse)
async def get_enhanced_storage_stats():
    """Get enhanced storage statistics with cleanup potential"""
    disk_stats = get_disk_stats()
    cleanup_potential = get_cleanup_potential()
    
    # Determine health status
    usage_pct = disk_stats["usage_percentage"]
    if usage_pct < 80:
        health_status = "healthy"
    elif usage_pct < 90:
        health_status = "warning"
    elif usage_pct < 95:
        health_status = "critical"
    else:
        health_status = "emergency"
    
    return StorageStatsResponse(
        total_gb=disk_stats["total_gb"],
        used_gb=disk_stats["used_gb"],
        available_gb=disk_stats["available_gb"],
        usage_percentage=usage_pct,
        health_status=health_status,
        cleanup_potential_gb=cleanup_potential
    )


@storage_router.get("/cleanup/preview", response_model=CleanupPreviewResponse)
async def preview_storage_cleanup(image_age_days: int = 1):
    """Preview what would be cleaned up"""
    # Count old images
    old_images = count_old_images(image_age_days)
    
    # Get WAL file size
    wal_path = "data/license_plates.db-wal"
    wal_size_mb = 0.0
    try:
        if os.path.exists(wal_path):
            wal_size_mb = os.path.getsize(wal_path) / (1024**2)
    except Exception as e:
        logger.error(f"Error getting WAL size: {e}")
    
    total_cleanup_gb = (old_images["size_mb"] + wal_size_mb) / 1024
    
    return CleanupPreviewResponse(
        old_images_count=old_images["count"],
        old_images_size_mb=old_images["size_mb"],
        database_wal_size_mb=wal_size_mb,
        total_cleanup_potential_gb=total_cleanup_gb
    )


@storage_router.post("/cleanup/execute")
async def execute_storage_cleanup(
    background_tasks: BackgroundTasks,
    image_age_days: int = 1,
    dry_run: bool = False
):
    """Execute storage cleanup in background"""
    
    def _run_cleanup():
        """Run the actual cleanup"""
        import subprocess
        import sys
        
        try:
            # Run our cleanup script
            cmd = [sys.executable, "bin/storage_cleanup.py"]
            if not dry_run:
                cmd.append("--execute")
            if image_age_days != 1:
                cmd.extend(["--max-age", str(image_age_days)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            # Save result
            cleanup_result = {
                "timestamp": datetime.now().isoformat(),
                "dry_run": dry_run,
                "image_age_days": image_age_days,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }
            
            os.makedirs("logs", exist_ok=True)
            with open("logs/last_storage_cleanup.json", "w") as f:
                json.dump(cleanup_result, f, indent=2)
                
        except Exception as e:
            logger.error(f"Cleanup execution error: {e}")
            cleanup_result = {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
            
            os.makedirs("logs", exist_ok=True)
            with open("logs/last_storage_cleanup.json", "w") as f:
                json.dump(cleanup_result, f, indent=2)
    
    background_tasks.add_task(_run_cleanup)
    
    return {
        "status": "started",
        "message": f"Storage cleanup {'preview' if dry_run else 'execution'} started in background",
        "dry_run": dry_run,
        "image_age_days": image_age_days
    }


@storage_router.get("/cleanup/status")
async def get_cleanup_status():
    """Get status of last cleanup operation"""
    try:
        with open("logs/last_storage_cleanup.json", "r") as f:
            result = json.load(f)
        return {"status": "found", "result": result}
    except FileNotFoundError:
        return {"status": "not_found", "message": "No cleanup history found"}
    except Exception as e:
        logger.error(f"Error reading cleanup status: {e}")
        return {"status": "error", "message": str(e)}