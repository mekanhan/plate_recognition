"""
Storage Management API Endpoints
Provides storage monitoring, alerts, and optimization controls
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

class StorageStats(BaseModel):
    total_gb: float
    used_gb: float
    available_gb: float
    usage_percentage: float
    health_status: str
    cleanup_potential_gb: float
    
class StorageBreakdown(BaseModel):
    recordings_gb: float
    detection_images_gb: float
    database_mb: float
    logs_mb: float
    other_gb: float

class CleanupPreview(BaseModel):
    old_images_count: int
    old_images_size_mb: float
    old_database_records: int
    database_wal_size_mb: float
    total_cleanup_potential_gb: float

class CleanupResult(BaseModel):
    files_deleted: int
    space_freed_mb: float
    errors: List[str]
    timestamp: str

def get_storage_stats() -> Dict:
    """Get comprehensive storage statistics"""
    try:
        # Get disk usage using df
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
        else:
            raise Exception("Could not parse df output")
            
    except Exception as e:
        raise HTTPException(status_code=500, f"Failed to get disk stats: {e}")
    
    # Determine health status
    if usage_pct < 80:
        health_status = "healthy"
    elif usage_pct < 90:
        health_status = "warning"  
    elif usage_pct < 95:
        health_status = "critical"
    else:
        health_status = "emergency"
    
    # Calculate cleanup potential
    cleanup_potential_gb = get_cleanup_potential()
    
    return {
        "total_gb": total_gb,
        "used_gb": used_gb,
        "available_gb": available_gb,
        "usage_percentage": usage_pct,
        "health_status": health_status,
        "cleanup_potential_gb": cleanup_potential_gb
    }

def get_storage_breakdown() -> Dict:
    """Get detailed breakdown of storage usage by category"""
    
    def get_dir_size_gb(path: str) -> float:
        if not os.path.exists(path):
            return 0.0
        try:
            result = subprocess.run(['du', '-sb', path], capture_output=True, text=True)
            if result.returncode == 0:
                return int(result.stdout.split()[0]) / (1024**3)
        except:
            pass
        return 0.0
    
    import subprocess
    
    breakdown = {
        "recordings_gb": get_dir_size_gb("recordings"),
        "detection_images_gb": get_dir_size_gb("detections"),
        "logs_mb": get_dir_size_gb("logs") * 1024,  # Convert to MB
        "other_gb": 0.0
    }
    
    # Database size
    db_path = "data/license_plates.db"
    wal_path = f"{db_path}-wal"
    shm_path = f"{db_path}-shm"
    
    db_size_mb = 0
    for path in [db_path, wal_path, shm_path]:
        if os.path.exists(path):
            db_size_mb += os.path.getsize(path) / (1024**2)
    
    breakdown["database_mb"] = db_size_mb
    
    return breakdown

def get_cleanup_potential() -> float:
    """Calculate potential storage savings from cleanup"""
    potential_gb = 0.0
    
    # Old detection images (>1 day)
    cutoff = (datetime.now() - timedelta(days=1)).timestamp()
    detection_path = Path("detections")
    
    for img_type in ['frames', 'plates']:
        img_dir = detection_path / img_type
        if img_dir.exists():
            for img_file in img_dir.glob('*.jpg'):
                try:
                    if img_file.stat().st_mtime < cutoff:
                        potential_gb += img_file.stat().st_size / (1024**3)
                except:
                    continue
    
    # Database WAL file
    wal_path = "data/license_plates.db-wal"
    if os.path.exists(wal_path):
        potential_gb += os.path.getsize(wal_path) / (1024**3)
    
    return potential_gb

def count_old_images(max_age_days: int = 1) -> Dict:
    """Count old detection images for cleanup preview"""
    cutoff = (datetime.now() - timedelta(days=max_age_days)).timestamp()
    
    old_count = 0
    old_size_mb = 0.0
    
    detection_path = Path("detections")
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
    
    return {"count": old_count, "size_mb": old_size_mb}

def count_old_database_records(max_age_days: int = 30) -> int:
    """Count old detection records in database"""
    try:
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        conn = sqlite3.connect("data/license_plates.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM detections WHERE timestamp < ?",
            (cutoff_date.isoformat(),)
        )
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    except:
        return 0

@router.get("/stats", response_model=StorageStats)
async def get_storage_statistics():
    """Get current storage statistics"""
    stats = get_storage_stats()
    return StorageStats(**stats)

@router.get("/breakdown", response_model=StorageBreakdown)
async def get_storage_usage_breakdown():
    """Get detailed breakdown of storage usage"""
    breakdown = get_storage_breakdown()
    return StorageBreakdown(**breakdown)

@router.get("/cleanup/preview", response_model=CleanupPreview)
async def preview_cleanup(image_age_days: int = 1, db_age_days: int = 30):
    """Preview what would be cleaned up"""
    
    # Count old images
    old_images = count_old_images(image_age_days)
    
    # Count old database records
    old_db_records = count_old_database_records(db_age_days)
    
    # Get WAL file size
    wal_path = "data/license_plates.db-wal"
    wal_size_mb = os.path.getsize(wal_path) / (1024**2) if os.path.exists(wal_path) else 0
    
    total_cleanup_gb = (old_images["size_mb"] + wal_size_mb) / 1024
    
    return CleanupPreview(
        old_images_count=old_images["count"],
        old_images_size_mb=old_images["size_mb"],
        old_database_records=old_db_records,
        database_wal_size_mb=wal_size_mb,
        total_cleanup_potential_gb=total_cleanup_gb
    )

@router.post("/cleanup/images")
async def cleanup_old_images(
    background_tasks: BackgroundTasks,
    max_age_days: int = 1,
    dry_run: bool = False
):
    """Clean up old detection images"""
    
    def _cleanup_images():
        import subprocess
        import os
        
        cutoff = (datetime.now() - timedelta(days=max_age_days)).timestamp()
        
        deleted_count = 0
        freed_mb = 0.0
        errors = []
        
        detection_path = Path("detections")
        for img_type in ['frames', 'plates']:
            img_dir = detection_path / img_type
            if not img_dir.exists():
                continue
                
            for img_file in img_dir.glob('*.jpg'):
                try:
                    if img_file.stat().st_mtime < cutoff:
                        size_mb = img_file.stat().st_size / (1024**2)
                        
                        if not dry_run:
                            img_file.unlink()
                        
                        deleted_count += 1
                        freed_mb += size_mb
                        
                except Exception as e:
                    errors.append(f"Failed to process {img_file}: {e}")
        
        # Save results to a file for retrieval
        result = {
            "files_deleted": deleted_count,
            "space_freed_mb": freed_mb,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
        with open("logs/last_cleanup_result.json", "w") as f:
            import json
            json.dump(result, f)
    
    background_tasks.add_task(_cleanup_images)
    
    return {"status": "started", "message": "Cleanup task started in background"}

@router.post("/cleanup/database")
async def optimize_database(background_tasks: BackgroundTasks, dry_run: bool = False):
    """Optimize database and checkpoint WAL"""
    
    def _optimize_database():
        errors = []
        freed_mb = 0.0
        
        try:
            # Get WAL size before
            wal_path = "data/license_plates.db-wal"
            wal_size_before = os.path.getsize(wal_path) / (1024**2) if os.path.exists(wal_path) else 0
            
            if not dry_run:
                conn = sqlite3.connect("data/license_plates.db")
                cursor = conn.cursor()
                
                # Checkpoint WAL
                cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                
                # Optimize
                cursor.execute("PRAGMA optimize")
                
                conn.commit()
                conn.close()
            
            # Get WAL size after
            wal_size_after = os.path.getsize(wal_path) / (1024**2) if os.path.exists(wal_path) else 0
            freed_mb = wal_size_before - wal_size_after
            
        except Exception as e:
            errors.append(f"Database optimization error: {e}")
        
        # Save results
        result = {
            "files_deleted": 1 if freed_mb > 0 else 0,
            "space_freed_mb": freed_mb,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
        with open("logs/last_db_optimization_result.json", "w") as f:
            import json
            json.dump(result, f)
    
    background_tasks.add_task(_optimize_database)
    
    return {"status": "started", "message": "Database optimization started in background"}

@router.get("/cleanup/result")
async def get_cleanup_result():
    """Get result of last cleanup operation"""
    import json
    
    results = {}
    
    # Get image cleanup result
    try:
        with open("logs/last_cleanup_result.json", "r") as f:
            results["image_cleanup"] = json.load(f)
    except:
        results["image_cleanup"] = None
    
    # Get database optimization result
    try:
        with open("logs/last_db_optimization_result.json", "r") as f:
            results["database_optimization"] = json.load(f)
    except:
        results["database_optimization"] = None
    
    return results

@router.get("/health")
async def storage_health_check():
    """Quick storage health check for monitoring"""
    stats = get_storage_stats()
    
    return {
        "status": stats["health_status"],
        "usage_percentage": stats["usage_percentage"],
        "available_gb": stats["available_gb"],
        "cleanup_potential_gb": stats["cleanup_potential_gb"],
        "timestamp": datetime.now().isoformat(),
        "alerts": generate_storage_alerts(stats)
    }

def generate_storage_alerts(stats: Dict) -> List[Dict]:
    """Generate storage alerts based on current stats"""
    alerts = []
    
    usage_pct = stats["usage_percentage"]
    
    if usage_pct >= 95:
        alerts.append({
            "level": "critical",
            "message": f"Storage critically low: {usage_pct:.1f}% used",
            "action": "Immediate cleanup required"
        })
    elif usage_pct >= 90:
        alerts.append({
            "level": "warning", 
            "message": f"Storage running low: {usage_pct:.1f}% used",
            "action": "Consider running cleanup"
        })
    elif usage_pct >= 80:
        alerts.append({
            "level": "info",
            "message": f"Storage usage high: {usage_pct:.1f}% used", 
            "action": "Monitor storage usage"
        })
    
    # Alert if significant cleanup potential
    if stats["cleanup_potential_gb"] >= 5:
        alerts.append({
            "level": "info",
            "message": f"Large cleanup potential: {stats['cleanup_potential_gb']:.1f}GB",
            "action": "Run cleanup to free space"
        })
    
    return alerts