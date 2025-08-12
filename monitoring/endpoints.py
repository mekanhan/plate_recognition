"""
Monitoring API Endpoints
"""
from fastapi import APIRouter, Response, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
import asyncio
import logging
import time
import psutil
from typing import Dict, Any, Optional

from .metrics import metrics
from .health import health_monitor, HealthStatus
from auth.dependencies import require_system_config, require_admin, get_optional_user
from auth.models import User

logger = logging.getLogger(__name__)

# Create monitoring router
monitoring_router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@monitoring_router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Get Prometheus metrics (public endpoint for monitoring systems)
    """
    try:
        return Response(
            content=metrics.get_metrics(),
            media_type=metrics.get_content_type()
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return PlainTextResponse("# Failed to generate metrics\n", status_code=500)


@monitoring_router.get("/health")
async def basic_health():
    """
    Basic health check (public endpoint)
    """
    return {
        "status": "healthy",
        "timestamp": metrics._start_time,
        "service": "lpr-system"
    }


@monitoring_router.get("/health/detailed")
async def detailed_health(current_user: User = Depends(require_system_config)):
    """
    Detailed health information (requires authentication)
    """
    try:
        # Run quick health checks
        checks = await health_monitor.run_all_checks()
        summary = health_monitor.get_health_summary()
        
        return {
            "overall_status": summary["overall_status"],
            "last_check": summary["last_check"],
            "checks": summary["checks"],
            "summary": summary["summary"],
            "user": current_user.username if current_user else None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "overall_status": "critical",
            "error": str(e),
            "timestamp": health_monitor.last_full_check
        }


@monitoring_router.post("/health/check/{check_name}")
async def run_specific_health_check(
    check_name: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_system_config)
):
    """
    Run a specific health check
    """
    valid_checks = list(health_monitor.check_intervals.keys())
    
    if check_name not in valid_checks:
        return {
            "error": f"Invalid check name. Valid checks: {valid_checks}",
            "status": "error"
        }
    
    try:
        result = await health_monitor.run_health_check(check_name)
        return {
            "check_name": check_name,
            "status": result.status.value,
            "message": result.message,
            "duration_ms": result.duration_ms,
            "details": result.details,
            "checked_at": result.checked_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Health check '{check_name}' failed: {e}")
        return {
            "check_name": check_name,
            "status": "critical",
            "error": str(e)
        }


@monitoring_router.get("/health/summary")
async def health_summary(current_user: Optional[User] = Depends(get_optional_user)):
    """
    Health summary (requires authentication for detailed info)
    """
    if not health_monitor.checks:
        # Run a quick check if none exist
        await health_monitor.run_health_check('system_resources')
    
    summary = health_monitor.get_health_summary()
    
    if current_user:
        return summary
    else:
        # Return limited info for unauthenticated requests
        return {
            "overall_status": summary["overall_status"],
            "total_checks": summary["summary"]["total_checks"],
            "healthy_checks": summary["summary"]["healthy_checks"],
            "warning_checks": summary["summary"]["warning_checks"],
            "critical_checks": summary["summary"]["critical_checks"]
        }


@monitoring_router.get("/system/stats")
async def system_stats(current_user: User = Depends(require_system_config)):
    """
    Get detailed system statistics
    """
    try:
        import psutil
        import os
        from datetime import datetime
        
        # System info
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        # Process info
        process = psutil.Process()
        
        # Memory info
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk info
        disk_usage = {}
        for path in ['.', 'detections', 'recordings', 'data']:
            if os.path.exists(path):
                usage = psutil.disk_usage(path)
                disk_usage[path] = {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': (usage.used / usage.total) * 100
                }
        
        # Network info (if available)
        network_stats = {}
        try:
            net_io = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except:
            pass
        
        return {
            'system': {
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': (datetime.now() - boot_time).total_seconds(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            'process': {
                'pid': process.pid,
                'memory_info': process.memory_info()._asdict(),
                'cpu_percent': process.cpu_percent(),
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat(),
                'num_threads': process.num_threads()
            },
            'memory': {
                'virtual': memory._asdict(),
                'swap': swap._asdict()
            },
            'disk': disk_usage,
            'network': network_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        return {"error": str(e)}


@monitoring_router.get("/performance/overview")
async def performance_overview(current_user: User = Depends(require_system_config)):
    """
    Get performance overview with key metrics
    """
    try:
        # This would typically query your metrics database
        # For now, return current system state
        
        from database.service import DatabaseService
        
        db = DatabaseService()
        
        # Get detection stats
        recent_detections = await db.get_recent_detections(limit=100)
        detection_count_last_hour = len([
            d for d in recent_detections 
            if (d.detected_at and 
                (d.detected_at.timestamp() > (metrics._start_time + 3600)))
        ])
        
        # Get camera stats
        cameras = await db.get_all_cameras()
        online_cameras = len([c for c in cameras if c.status == 'active'])
        
        await db.close()
        
        return {
            'detection_performance': {
                'total_detections': len(recent_detections),
                'detections_last_hour': detection_count_last_hour,
                'average_confidence': sum(d.confidence for d in recent_detections) / len(recent_detections) if recent_detections else 0
            },
            'camera_performance': {
                'total_cameras': len(cameras),
                'online_cameras': online_cameras,
                'offline_cameras': len(cameras) - online_cameras
            },
            'system_performance': {
                'uptime_seconds': time.time() - metrics._start_time,
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance overview: {e}")
        return {"error": str(e)}


@monitoring_router.post("/metrics/update")
async def update_metrics(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin())
):
    """
    Manually trigger metrics update (admin only)
    """
    def update_all_metrics():
        try:
            # Update system info
            metrics.update_system_info("1.0.0", "production", False)  # You'd get these dynamically
            
            # Update system metrics
            metrics.update_system_metrics()
            
            logger.info("Metrics updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            return False
    
    background_tasks.add_task(update_all_metrics)
    
    return {
        "message": "Metrics update triggered",
        "status": "success"
    }


@monitoring_router.get("/alerts")
async def get_alerts(current_user: User = Depends(require_system_config)):
    """
    Get system alerts based on health checks
    """
    try:
        if not health_monitor.checks:
            await health_monitor.run_all_checks()
        
        alerts = []
        
        for name, check in health_monitor.checks.items():
            if check.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                alerts.append({
                    'alert_id': f"{name}_{check.status.value}",
                    'component': name,
                    'severity': check.status.value,
                    'message': check.message,
                    'details': check.details,
                    'timestamp': check.checked_at.isoformat(),
                    'duration_ms': check.duration_ms
                })
        
        return {
            'alerts': alerts,
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a['severity'] == 'critical']),
            'warning_alerts': len([a for a in alerts if a['severity'] == 'warning'])
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return {"error": str(e)}


# Background task to periodically update metrics
async def periodic_metrics_update():
    """Background task to update metrics periodically"""
    while True:
        try:
            # Update system metrics
            metrics.update_system_metrics()
            
            # Update health checks (less frequently)
            await health_monitor.run_all_checks()
            
            logger.debug("Periodic metrics update completed")
            
        except Exception as e:
            logger.error(f"Periodic metrics update failed: {e}")
        
        # Wait 30 seconds before next update
        await asyncio.sleep(30)