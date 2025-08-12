"""
Comprehensive Health Monitoring System
"""
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""
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
    details: Dict[str, Any] = None
    duration_ms: float = 0
    checked_at: datetime = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow()
        if self.details is None:
            self.details = {}


class HealthMonitor:
    """Comprehensive health monitoring for LPR system"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.check_intervals: Dict[str, int] = {
            'system_resources': 30,  # seconds
            'database': 60,
            'cameras': 45,
            'ai_models': 120,
            'storage': 90,
            'auth_system': 300,  # 5 minutes
            'recording_service': 60
        }
        self.running = False
        self.last_full_check = None
    
    async def check_system_resources(self) -> HealthCheck:
        """Check system resource health"""
        start_time = time.time()
        
        try:
            import psutil
            
            # CPU check
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            status = HealthStatus.HEALTHY
            issues = []
            
            # CPU thresholds
            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                issues.append(f"CPU usage critical: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = HealthStatus.WARNING
                issues.append(f"CPU usage high: {cpu_percent:.1f}%")
            
            # Memory thresholds
            if memory.percent > 90:
                status = HealthStatus.CRITICAL
                issues.append(f"Memory usage critical: {memory.percent:.1f}%")
            elif memory.percent > 80:
                status = HealthStatus.WARNING
                issues.append(f"Memory usage high: {memory.percent:.1f}%")
            
            # Disk thresholds
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 95:
                status = HealthStatus.CRITICAL
                issues.append(f"Disk usage critical: {disk_percent:.1f}%")
            elif disk_percent > 85:
                status = HealthStatus.WARNING
                issues.append(f"Disk usage high: {disk_percent:.1f}%")
            
            message = "System resources healthy" if not issues else "; ".join(issues)
            
            details = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk_percent,
                'disk_free_gb': disk.free / (1024**3),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Failed to check system resources: {str(e)}"
            details = {'error': str(e)}
        
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheck('system_resources', status, message, details, duration_ms)
    
    async def check_database(self) -> HealthCheck:
        """Check database connectivity and health"""
        start_time = time.time()
        
        try:
            from database.service import DatabaseService
            
            # Create test database connection
            db = DatabaseService()
            
            # Test basic connectivity
            cameras = await db.get_all_cameras()
            recent_detections = await db.get_recent_detections(limit=1)
            
            # Check database file size and accessibility
            import os
            db_path = "data/license_plates.db"
            db_size_mb = 0
            
            if os.path.exists(db_path):
                db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
            
            status = HealthStatus.HEALTHY
            message = "Database healthy"
            
            # Check for potential issues
            if db_size_mb > 1000:  # > 1GB
                status = HealthStatus.WARNING
                message = f"Database size large: {db_size_mb:.1f}MB"
            
            details = {
                'cameras_count': len(cameras),
                'has_recent_detections': len(recent_detections) > 0,
                'database_size_mb': db_size_mb,
                'database_path': db_path
            }
            
            await db.close()
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Database check failed: {str(e)}"
            details = {'error': str(e)}
        
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheck('database', status, message, details, duration_ms)
    
    async def check_cameras(self) -> HealthCheck:
        """Check camera connectivity and status"""
        start_time = time.time()
        
        try:
            from database.service import DatabaseService
            
            db = DatabaseService()
            cameras = await db.get_all_cameras()
            await db.close()
            
            total_cameras = len(cameras)
            online_cameras = 0
            offline_cameras = 0
            camera_details = {}
            
            for camera in cameras:
                # This is a simplified check - in reality you'd test actual connectivity
                if camera.status == 'active':
                    online_cameras += 1
                else:
                    offline_cameras += 1
                
                camera_details[camera.camera_id] = {
                    'name': camera.name,
                    'status': camera.status,
                    'ip_address': camera.ip_address,
                    'last_test_result': camera.last_test_result
                }
            
            # Determine overall camera health
            if total_cameras == 0:
                status = HealthStatus.WARNING
                message = "No cameras configured"
            elif offline_cameras == 0:
                status = HealthStatus.HEALTHY
                message = f"All {total_cameras} cameras online"
            elif offline_cameras >= total_cameras * 0.5:  # 50% or more offline
                status = HealthStatus.CRITICAL
                message = f"{offline_cameras}/{total_cameras} cameras offline"
            else:
                status = HealthStatus.WARNING
                message = f"{offline_cameras}/{total_cameras} cameras offline"
            
            details = {
                'total_cameras': total_cameras,
                'online_cameras': online_cameras,
                'offline_cameras': offline_cameras,
                'camera_details': camera_details
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Camera check failed: {str(e)}"
            details = {'error': str(e)}
        
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheck('cameras', status, message, details, duration_ms)
    
    async def check_ai_models(self) -> HealthCheck:
        """Check AI model loading and health"""
        start_time = time.time()
        
        try:
            import torch
            import os
            
            model_status = {}
            issues = []
            
            # Check CUDA availability
            cuda_available = torch.cuda.is_available()
            gpu_count = torch.cuda.device_count() if cuda_available else 0
            
            # Check model files existence
            model_files = {
                'yolo_vehicle': 'ai_pipeline/train/models/pretrained/yolo11m_best.pt',
                'yolo_plate': 'app/models/yolo11m_best.pt',
                'backup_model': 'models/yolo11m_best.pt'
            }
            
            available_models = 0
            for model_name, model_path in model_files.items():
                exists = os.path.exists(model_path)
                model_status[model_name] = {
                    'path': model_path,
                    'exists': exists,
                    'size_mb': os.path.getsize(model_path) / (1024*1024) if exists else 0
                }
                if exists:
                    available_models += 1
            
            # Check EasyOCR (if available)
            try:
                import easyocr
                model_status['easyocr'] = {'available': True}
            except ImportError:
                model_status['easyocr'] = {'available': False}
                issues.append("EasyOCR not available")
            
            # Determine overall status
            if available_models == 0:
                status = HealthStatus.CRITICAL
                issues.append("No YOLO models found")
            elif available_models < 2:
                status = HealthStatus.WARNING
                issues.append("Limited model availability")
            else:
                status = HealthStatus.HEALTHY
            
            message = "AI models healthy" if not issues else "; ".join(issues)
            
            details = {
                'cuda_available': cuda_available,
                'gpu_count': gpu_count,
                'available_models': available_models,
                'total_model_paths': len(model_files),
                'model_status': model_status
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"AI model check failed: {str(e)}"
            details = {'error': str(e)}
        
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheck('ai_models', status, message, details, duration_ms)
    
    async def check_storage(self) -> HealthCheck:
        """Check storage health and usage"""
        start_time = time.time()
        
        try:
            from ai_features.core.storage_manager import StorageManager
            
            storage_mgr = StorageManager()
            storage_stats = storage_mgr.get_storage_usage()
            
            status = HealthStatus.HEALTHY
            issues = []
            
            # Check storage thresholds
            usage_percent = storage_stats.get('percentage_used', 0)
            
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
                issues.append(f"Storage critically full: {usage_percent:.1f}%")
            elif usage_percent > 85:
                status = HealthStatus.WARNING
                issues.append(f"Storage usage high: {usage_percent:.1f}%")
            
            # Check if cleanup is working
            cleanup_threshold = storage_mgr.config.get('cleanup_threshold_gb', 9.0)
            total_gb = storage_stats.get('total_size_gb', 0)
            
            if total_gb > cleanup_threshold:
                issues.append("Storage cleanup may not be working properly")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            
            message = "Storage healthy" if not issues else "; ".join(issues)
            
            details = {
                'total_size_gb': storage_stats.get('total_size_gb', 0),
                'percentage_used': usage_percent,
                'cleanup_threshold_gb': cleanup_threshold,
                'max_storage_gb': storage_mgr.config.get('max_storage_gb', 10.0),
                'directories': storage_stats.get('directories', {})
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Storage check failed: {str(e)}"
            details = {'error': str(e)}
        
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheck('storage', status, message, details, duration_ms)
    
    async def check_auth_system(self) -> HealthCheck:
        """Check authentication system health"""
        start_time = time.time()
        
        try:
            from auth.user_manager import user_manager
            from auth.jwt_handler import jwt_handler
            import os
            
            # Check user system
            users = user_manager.list_users()
            
            # Check JWT configuration
            jwt_configured = bool(os.getenv('JWT_SECRET_KEY'))
            
            status = HealthStatus.HEALTHY
            issues = []
            
            if len(users) == 0:
                status = HealthStatus.CRITICAL
                issues.append("No users configured")
            
            if not jwt_configured:
                issues.append("JWT_SECRET_KEY not configured")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            
            # Check default password usage
            if len(users) > 0:
                admin_users = [u for u in users if u.role.value == 'admin']
                if admin_users and user_manager.authenticate_user('admin', 'admin123'):
                    issues.append("Default admin password in use")
                    status = HealthStatus.WARNING
            
            message = "Authentication system healthy" if not issues else "; ".join(issues)
            
            details = {
                'user_count': len(users),
                'jwt_configured': jwt_configured,
                'users': [{'username': u.username, 'role': u.role.value} for u in users[:5]]  # First 5 users
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Auth system check failed: {str(e)}"
            details = {'error': str(e)}
        
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheck('auth_system', status, message, details, duration_ms)
    
    async def check_recording_service(self) -> HealthCheck:
        """Check recording service health"""
        start_time = time.time()
        
        try:
            import httpx
            
            # Try to connect to recording service
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8002/health")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    status = HealthStatus.HEALTHY
                    message = "Recording service healthy"
                    
                    details = {
                        'service_available': True,
                        'response_data': data
                    }
                else:
                    status = HealthStatus.WARNING
                    message = f"Recording service returned {response.status_code}"
                    details = {'service_available': False, 'status_code': response.status_code}
            
        except Exception as e:
            status = HealthStatus.WARNING  # Not critical if recording service is down
            message = f"Recording service unavailable: {str(e)}"
            details = {'service_available': False, 'error': str(e)}
        
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheck('recording_service', status, message, details, duration_ms)
    
    async def run_health_check(self, check_name: str) -> HealthCheck:
        """Run a specific health check"""
        check_methods = {
            'system_resources': self.check_system_resources,
            'database': self.check_database,
            'cameras': self.check_cameras,
            'ai_models': self.check_ai_models,
            'storage': self.check_storage,
            'auth_system': self.check_auth_system,
            'recording_service': self.check_recording_service
        }
        
        if check_name in check_methods:
            try:
                result = await check_methods[check_name]()
                self.checks[check_name] = result
                return result
            except Exception as e:
                error_check = HealthCheck(
                    check_name, 
                    HealthStatus.CRITICAL, 
                    f"Health check failed: {str(e)}",
                    {'error': str(e)}
                )
                self.checks[check_name] = error_check
                return error_check
        else:
            raise ValueError(f"Unknown health check: {check_name}")
    
    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        tasks = []
        for check_name in self.check_intervals.keys():
            tasks.append(self.run_health_check(check_name))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                check_name = list(self.check_intervals.keys())[i]
                logger.error(f"Health check '{check_name}' failed: {result}")
        
        self.last_full_check = datetime.utcnow()
        return self.checks
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in self.checks.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        overall_status = self.get_overall_status()
        
        critical_issues = [
            check for check in self.checks.values() 
            if check.status == HealthStatus.CRITICAL
        ]
        
        warning_issues = [
            check for check in self.checks.values() 
            if check.status == HealthStatus.WARNING
        ]
        
        return {
            'overall_status': overall_status.value,
            'last_check': self.last_full_check.isoformat() if self.last_full_check else None,
            'checks': {name: {
                'status': check.status.value,
                'message': check.message,
                'duration_ms': check.duration_ms,
                'checked_at': check.checked_at.isoformat()
            } for name, check in self.checks.items()},
            'summary': {
                'total_checks': len(self.checks),
                'healthy_checks': len([c for c in self.checks.values() if c.status == HealthStatus.HEALTHY]),
                'warning_checks': len(warning_issues),
                'critical_checks': len(critical_issues),
                'critical_issues': [c.message for c in critical_issues],
                'warning_issues': [c.message for c in warning_issues]
            }
        }


# Global health monitor instance
health_monitor = HealthMonitor()