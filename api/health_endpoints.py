"""
System Health Monitoring API Endpoints
Comprehensive health checks for all system components
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import asyncio
from datetime import datetime
import psutil
import os

from database.db_config import check_database_health
from config.app_config import get_config

router = APIRouter(prefix="/api/health", tags=["health"])
logger = logging.getLogger("HealthAPI")

@router.get("/database")
async def database_health() -> Dict[str, Any]:
    """Get detailed database health information"""
    try:
        health = await check_database_health()
        return {
            "status": "healthy" if health["status"] == "healthy" else "unhealthy",
            "details": health,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/system")
async def system_health() -> Dict[str, Any]:
    """Get comprehensive system health information"""
    try:
        config = get_config()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process information
        current_process = psutil.Process()
        
        # Database health
        db_health = await check_database_health()
        
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "used": disk.used,
                    "percent": (disk.used / disk.total) * 100
                },
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            "process": {
                "pid": current_process.pid,
                "memory_info": current_process.memory_info()._asdict(),
                "cpu_percent": current_process.cpu_percent(),
                "create_time": current_process.create_time(),
                "num_threads": current_process.num_threads()
            },
            "database": db_health,
            "services": {
                "main_api": "running",  # We're responding, so we're running
                "recording_service": await _check_recording_service(),
                "frontend": await _check_frontend_service()
            },
            "configuration": {
                "log_level": config.log_level,
                "debug_mode": config.debug,
                "data_directory": config.data_dir,
                "recordings_directory": config.recordings_dir
            }
        }
        
        # Determine overall health status
        issues = []
        
        # Check critical thresholds
        if cpu_percent > 90:
            issues.append("High CPU usage")
        
        if memory.percent > 90:
            issues.append("High memory usage")
        
        if disk.percent > 90:
            issues.append("Low disk space")
        
        if db_health["status"] != "healthy":
            issues.append("Database unhealthy")
        
        if issues:
            health_data["status"] = "degraded"
            health_data["issues"] = issues
        
        return health_data
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/services")
async def services_health() -> Dict[str, Any]:
    """Check health of all LPR services"""
    try:
        services = {
            "main_api": {
                "status": "running",
                "port": 8001,
                "endpoint": "/docs"
            },
            "recording_service": {
                "status": await _check_recording_service(),
                "port": 8002,
                "endpoint": "/health"
            },
            "frontend": {
                "status": await _check_frontend_service(),
                "port": 8080,
                "endpoint": "/"
            }
        }
        
        # Overall status
        all_healthy = all(service["status"] == "running" for service in services.values())
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy" if all_healthy else "degraded",
            "services": services
        }
        
    except Exception as e:
        logger.error(f"Services health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/storage")
async def storage_health() -> Dict[str, Any]:
    """Check storage health and usage"""
    try:
        config = get_config()
        
        storage_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "paths": {}
        }
        
        # Check main directories
        paths_to_check = [
            ("data", config.data_dir),
            ("recordings", config.recordings_dir),
            ("logs", config.logs_dir)
        ]
        
        total_used = 0
        
        for name, path in paths_to_check:
            if os.path.exists(path):
                size = _get_directory_size(path)
                storage_info["paths"][name] = {
                    "path": path,
                    "size_bytes": size,
                    "size_mb": size / (1024 * 1024),
                    "exists": True
                }
                total_used += size
            else:
                storage_info["paths"][name] = {
                    "path": path,
                    "exists": False
                }
        
        # Disk space for the main disk
        disk = psutil.disk_usage('/')
        storage_info["disk"] = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        storage_info["lpr_usage"] = {
            "total_bytes": total_used,
            "total_mb": total_used / (1024 * 1024),
            "total_gb": total_used / (1024 * 1024 * 1024)
        }
        
        # Determine status
        if disk.percent > 95:
            storage_info["status"] = "critical"
        elif disk.percent > 85:
            storage_info["status"] = "warning"
        else:
            storage_info["status"] = "healthy"
        
        return storage_info
        
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

async def _check_recording_service() -> str:
    """Check if recording service is running"""
    try:
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get('http://localhost:8002/health') as response:
                if response.status == 200:
                    return "running"
                else:
                    return "unhealthy"
    except:
        return "offline"

async def _check_frontend_service() -> str:
    """Check if frontend service is running"""
    try:
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get('http://localhost:8080/') as response:
                if response.status == 200:
                    return "running"
                else:
                    return "unhealthy"
    except:
        return "offline"

def _get_directory_size(path: str) -> int:
    """Get total size of directory in bytes"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
    except (OSError, IOError):
        pass
    return total_size