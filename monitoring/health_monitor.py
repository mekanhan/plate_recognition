"""
Comprehensive Health Monitoring System for LPR
Monitors services, cameras, disk usage, and system resources
"""
import asyncio
import aiohttp
import time
import psutil
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pathlib import Path

try:
    from config.app_config import get_config
    from utils.log_manager import get_service_logger
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    import logging


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'response_time_ms': self.response_time_ms
        }


@dataclass
class SystemHealth:
    """Overall system health status"""
    overall_status: HealthStatus
    checks: List[HealthCheck]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'overall_status': self.overall_status.value,
            'timestamp': self.timestamp.isoformat(),
            'checks': [check.to_dict() for check in self.checks],
            'summary': self.get_summary()
        }
    
    def get_summary(self) -> Dict[str, int]:
        """Get count of checks by status"""
        summary = {status.value: 0 for status in HealthStatus}
        for check in self.checks:
            summary[check.status.value] += 1
        return summary


class HealthMonitor:
    """
    Main health monitoring system
    """
    
    def __init__(self):
        if HAS_CONFIG:
            self.config = get_config()
            self.logger = get_service_logger('health_monitor')
        else:
            self.config = None
            self.logger = logging.getLogger('health_monitor')
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_health_check: Optional[SystemHealth] = None
        self.health_history: List[SystemHealth] = []
        self.max_history = 100  # Keep last 100 health checks
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_service_health(self, name: str, url: str) -> HealthCheck:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            async with self.session.get(f"{url}/health") as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        return HealthCheck(
                            name=f"service_{name}",
                            status=HealthStatus.HEALTHY,
                            message=f"{name} service is healthy",
                            response_time_ms=response_time,
                            details={'response_data': data}
                        )
                    except Exception:
                        # Service responded but not with JSON
                        return HealthCheck(
                            name=f"service_{name}",
                            status=HealthStatus.WARNING,
                            message=f"{name} service responded but with invalid JSON",
                            response_time_ms=response_time
                        )
                else:
                    return HealthCheck(
                        name=f"service_{name}",
                        status=HealthStatus.CRITICAL,
                        message=f"{name} service returned HTTP {response.status}",
                        response_time_ms=response_time
                    )
        
        except asyncio.TimeoutError:
            return HealthCheck(
                name=f"service_{name}",
                status=HealthStatus.CRITICAL,
                message=f"{name} service timeout",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return HealthCheck(
                name=f"service_{name}",
                status=HealthStatus.CRITICAL,
                message=f"{name} service error: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_disk_usage(self) -> HealthCheck:
        """Check disk usage for critical directories"""
        try:
            # Check main disk usage
            if self.config:
                paths_to_check = [
                    self.config.storage.recordings_dir,
                    self.config.storage.detections_dir,
                    self.config.logging.log_dir
                ]
            else:
                paths_to_check = ["recordings", "detections", "logs"]
            
            disk_info = {}
            max_usage = 0.0
            critical_path = None
            
            for path_str in paths_to_check:
                path = Path(path_str)
                if path.exists():
                    usage = psutil.disk_usage(str(path))
                    usage_percent = usage.used / usage.total
                    
                    disk_info[path_str] = {
                        'usage_percent': round(usage_percent * 100, 1),
                        'free_gb': round(usage.free / (1024**3), 1),
                        'total_gb': round(usage.total / (1024**3), 1)
                    }
                    
                    if usage_percent > max_usage:
                        max_usage = usage_percent
                        critical_path = path_str
            
            if max_usage > 0.95:  # 95%
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical: {critical_path} at {max_usage*100:.1f}%"
            elif max_usage > 0.85:  # 85%
                status = HealthStatus.WARNING
                message = f"Disk usage high: {critical_path} at {max_usage*100:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal (max: {max_usage*100:.1f}%)"
            
            return HealthCheck(
                name="disk_usage",
                status=status,
                message=message,
                details=disk_info
            )
            
        except Exception as e:
            return HealthCheck(
                name="disk_usage",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk usage: {e}"
            )
    
    def check_system_resources(self) -> HealthCheck:
        """Check system CPU, memory, and other resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            details = {
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory.percent, 1),
                'memory_available_gb': round(memory.available / (1024**3), 1),
                'memory_total_gb': round(memory.total / (1024**3), 1)
            }
            
            # Determine status based on thresholds
            if cpu_percent > 90 or memory.percent > 90:
                status = HealthStatus.CRITICAL
                message = f"High resource usage: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%"
            elif cpu_percent > 70 or memory.percent > 70:
                status = HealthStatus.WARNING
                message = f"Moderate resource usage: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Resource usage normal: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system resources: {e}"
            )
    
    async def check_database_health(self) -> HealthCheck:
        """Check database connectivity and basic operations"""
        try:
            # Try to import and test database
            from database.service import DatabaseService
            
            db_service = DatabaseService()
            
            # Test basic database operation
            start_time = time.time()
            async with db_service.async_session() as session:
                # Simple query to test connectivity
                result = await session.execute("SELECT 1")
                result.scalar()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database is accessible",
                response_time_ms=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="database",
                status=HealthStatus.CRITICAL,
                message=f"Database error: {str(e)}"
            )
    
    async def check_camera_connectivity(self) -> List[HealthCheck]:
        """Check connectivity to all configured cameras"""
        checks = []
        
        try:
            # Get camera list from database
            from database.service import DatabaseService
            
            db_service = DatabaseService()
            async with db_service.async_session() as session:
                cameras = await db_service.get_all_cameras()
            
            for camera in cameras:
                try:
                    # Build camera URL
                    if camera.connection_type == 'rtsp':
                        # For RTSP, we can't easily test connectivity without streaming
                        # So we'll just mark as unknown for now
                        checks.append(HealthCheck(
                            name=f"camera_{camera.camera_id}",
                            status=HealthStatus.UNKNOWN,
                            message=f"RTSP camera - connectivity not testable",
                            details={'camera_name': camera.name, 'ip': camera.ip_address}
                        ))
                    else:
                        # For HTTP cameras, try to connect
                        url = f"{camera.connection_type}://{camera.ip_address}:{camera.port}"
                        
                        start_time = time.time()
                        try:
                            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                                response_time = (time.time() - start_time) * 1000
                                
                                if response.status < 400:
                                    status = HealthStatus.HEALTHY
                                    message = f"Camera {camera.name} is accessible"
                                else:
                                    status = HealthStatus.WARNING
                                    message = f"Camera {camera.name} returned HTTP {response.status}"
                                
                                checks.append(HealthCheck(
                                    name=f"camera_{camera.camera_id}",
                                    status=status,
                                    message=message,
                                    response_time_ms=response_time,
                                    details={'camera_name': camera.name, 'ip': camera.ip_address}
                                ))
                        
                        except asyncio.TimeoutError:
                            checks.append(HealthCheck(
                                name=f"camera_{camera.camera_id}",
                                status=HealthStatus.CRITICAL,
                                message=f"Camera {camera.name} timeout",
                                details={'camera_name': camera.name, 'ip': camera.ip_address}
                            ))
                        except Exception as e:
                            checks.append(HealthCheck(
                                name=f"camera_{camera.camera_id}",
                                status=HealthStatus.CRITICAL,
                                message=f"Camera {camera.name} error: {str(e)}",
                                details={'camera_name': camera.name, 'ip': camera.ip_address}
                            ))
                
                except Exception as e:
                    checks.append(HealthCheck(
                        name=f"camera_unknown",
                        status=HealthStatus.UNKNOWN,
                        message=f"Failed to check camera: {str(e)}"
                    ))
        
        except Exception as e:
            checks.append(HealthCheck(
                name="cameras",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to get camera list: {str(e)}"
            ))
        
        return checks
    
    async def perform_full_health_check(self) -> SystemHealth:
        """Perform comprehensive health check of all system components"""
        checks = []
        
        # Check services
        if self.config:
            service_urls = {
                'main_api': self.config.services.main_api_url,
                'recording_api': self.config.services.recording_api_url
            }
        else:
            service_urls = {
                'main_api': 'http://localhost:8001',
                'recording_api': 'http://localhost:8002'
            }
        
        for service_name, url in service_urls.items():
            check = await self.check_service_health(service_name, url)
            checks.append(check)
        
        # Check database
        db_check = await self.check_database_health()
        checks.append(db_check)
        
        # Check system resources
        resource_check = self.check_system_resources()
        checks.append(resource_check)
        
        # Check disk usage
        disk_check = self.check_disk_usage()
        checks.append(disk_check)
        
        # Check cameras
        camera_checks = await self.check_camera_connectivity()
        checks.extend(camera_checks)
        
        # Determine overall status
        critical_count = sum(1 for check in checks if check.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for check in checks if check.status == HealthStatus.WARNING)
        
        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning_count > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
        
        system_health = SystemHealth(
            overall_status=overall_status,
            checks=checks
        )
        
        # Store in history
        self.last_health_check = system_health
        self.health_history.append(system_health)
        
        # Keep only recent history
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
        
        return system_health
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_checks = [
            check for check in self.health_history 
            if check.timestamp > cutoff_time
        ]
        
        if not recent_checks:
            return {'error': 'No recent health data available'}
        
        # Analyze trends
        status_counts = {status.value: 0 for status in HealthStatus}
        for check in recent_checks:
            status_counts[check.overall_status.value] += 1
        
        # Calculate uptime percentage
        healthy_count = status_counts[HealthStatus.HEALTHY.value]
        total_checks = len(recent_checks)
        uptime_percentage = (healthy_count / total_checks) * 100 if total_checks > 0 else 0
        
        return {
            'period_hours': hours,
            'total_checks': total_checks,
            'status_distribution': status_counts,
            'uptime_percentage': round(uptime_percentage, 1),
            'last_check': recent_checks[-1].timestamp.isoformat(),
            'oldest_check': recent_checks[0].timestamp.isoformat()
        }


# Convenience functions for quick health checks
async def quick_health_check() -> Dict[str, Any]:
    """Perform a quick health check and return results"""
    async with HealthMonitor() as monitor:
        health = await monitor.perform_full_health_check()
        return health.to_dict()


async def check_service_status(service_name: str, url: str) -> Dict[str, Any]:
    """Check status of a single service"""
    async with HealthMonitor() as monitor:
        check = await monitor.check_service_health(service_name, url)
        return check.to_dict()


if __name__ == "__main__":
    # CLI interface for health monitoring
    import json
    
    async def main():
        async with HealthMonitor() as monitor:
            print("Performing health check...")
            health = await monitor.perform_full_health_check()
            
            print(f"\nOverall Status: {health.overall_status.value.upper()}")
            print(f"Timestamp: {health.timestamp}")
            print(f"\nChecks Summary: {health.get_summary()}")
            
            print("\nDetailed Results:")
            for check in health.checks:
                status_icon = {
                    HealthStatus.HEALTHY: "✅",
                    HealthStatus.WARNING: "⚠️",
                    HealthStatus.CRITICAL: "❌",
                    HealthStatus.UNKNOWN: "❓"
                }.get(check.status, "❓")
                
                print(f"  {status_icon} {check.name}: {check.message}")
                if check.response_time_ms:
                    print(f"    Response time: {check.response_time_ms:.1f}ms")
    
    asyncio.run(main())