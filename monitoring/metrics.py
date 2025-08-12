"""
Prometheus Metrics for LPR System
"""
import time
import psutil
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Gauge, Histogram, Info, CollectorRegistry, 
    generate_latest, CONTENT_TYPE_LATEST
)
import logging

logger = logging.getLogger(__name__)


class LPRMetrics:
    """Centralized metrics collection for LPR system"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._init_metrics()
        self._start_time = time.time()
    
    def _init_metrics(self):
        """Initialize all Prometheus metrics"""
        
        # System Information
        self.system_info = Info(
            'lpr_system_info',
            'LPR System Information',
            registry=self.registry
        )
        
        # System Metrics
        self.cpu_usage = Gauge(
            'lpr_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'lpr_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],  # physical, virtual, swap
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'lpr_disk_usage_bytes',
            'Disk usage in bytes',
            ['path', 'type'],  # type: used, free, total
            registry=self.registry
        )
        
        self.system_uptime = Gauge(
            'lpr_system_uptime_seconds',
            'System uptime in seconds',
            registry=self.registry
        )
        
        # Detection Metrics
        self.detections_total = Counter(
            'lpr_detections_total',
            'Total number of license plate detections',
            ['camera_id', 'vehicle_type'],
            registry=self.registry
        )
        
        self.detection_confidence = Histogram(
            'lpr_detection_confidence',
            'Distribution of detection confidence scores',
            ['camera_id'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        self.ocr_confidence = Histogram(
            'lpr_ocr_confidence',
            'Distribution of OCR confidence scores',
            ['camera_id'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        self.processing_duration = Histogram(
            'lpr_processing_duration_seconds',
            'Time spent processing frames',
            ['camera_id', 'stage'],  # stage: detection, ocr, total
            registry=self.registry
        )
        
        # Camera Metrics
        self.cameras_total = Gauge(
            'lpr_cameras_total',
            'Total number of configured cameras',
            registry=self.registry
        )
        
        self.cameras_online = Gauge(
            'lpr_cameras_online',
            'Number of cameras currently online',
            registry=self.registry
        )
        
        self.camera_status = Gauge(
            'lpr_camera_status',
            'Camera status (1=online, 0=offline)',
            ['camera_id', 'name', 'ip_address'],
            registry=self.registry
        )
        
        self.camera_fps = Gauge(
            'lpr_camera_fps',
            'Camera frames per second',
            ['camera_id'],
            registry=self.registry
        )
        
        self.camera_errors = Counter(
            'lpr_camera_errors_total',
            'Total camera errors',
            ['camera_id', 'error_type'],
            registry=self.registry
        )
        
        self.camera_reconnects = Counter(
            'lpr_camera_reconnects_total',
            'Total camera reconnection attempts',
            ['camera_id'],
            registry=self.registry
        )
        
        # Storage Metrics
        self.storage_usage = Gauge(
            'lpr_storage_usage_bytes',
            'Storage usage in bytes',
            ['type'],  # detections, recordings, total
            registry=self.registry
        )
        
        self.storage_files_total = Gauge(
            'lpr_storage_files_total',
            'Total number of stored files',
            ['type'],  # frames, plates, recordings
            registry=self.registry
        )
        
        self.storage_cleanup_events = Counter(
            'lpr_storage_cleanup_events_total',
            'Total storage cleanup events',
            ['type'],  # automatic, manual, emergency
            registry=self.registry
        )
        
        self.deduplication_savings = Counter(
            'lpr_deduplication_savings_total',
            'Total files saved by deduplication',
            ['camera_id'],
            registry=self.registry
        )
        
        # API Metrics
        self.api_requests_total = Counter(
            'lpr_api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'lpr_api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Authentication Metrics
        self.auth_attempts = Counter(
            'lpr_auth_attempts_total',
            'Total authentication attempts',
            ['result'],  # success, failure
            registry=self.registry
        )
        
        self.active_tokens = Gauge(
            'lpr_active_tokens',
            'Number of active JWT tokens',
            registry=self.registry
        )
        
        self.permission_denials = Counter(
            'lpr_permission_denials_total',
            'Total permission denied events',
            ['user_role', 'required_permission'],
            registry=self.registry
        )
        
        # Model Performance Metrics
        self.model_load_time = Gauge(
            'lpr_model_load_time_seconds',
            'Time taken to load AI models',
            ['model_type'],  # yolo, ocr
            registry=self.registry
        )
        
        self.model_inference_time = Histogram(
            'lpr_model_inference_time_seconds',
            'Model inference time',
            ['model_type'],
            registry=self.registry
        )
        
        self.model_memory_usage = Gauge(
            'lpr_model_memory_usage_bytes',
            'Memory usage by AI models',
            ['model_type'],
            registry=self.registry
        )
    
    def update_system_info(self, version: str, deployment_mode: str, gpu_available: bool):
        """Update system information"""
        self.system_info.info({
            'version': version,
            'deployment_mode': deployment_mode,
            'gpu_available': str(gpu_available),
            'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
            'platform': psutil.sys.platform
        })
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.labels(type='physical_used').set(memory.used)
            self.memory_usage.labels(type='physical_available').set(memory.available)
            self.memory_usage.labels(type='physical_total').set(memory.total)
            
            swap = psutil.swap_memory()
            self.memory_usage.labels(type='swap_used').set(swap.used)
            self.memory_usage.labels(type='swap_total').set(swap.total)
            
            # Disk usage for key directories
            for path in ['.', 'detections', 'recordings']:
                try:
                    disk = psutil.disk_usage(path)
                    self.disk_usage.labels(path=path, type='used').set(disk.used)
                    self.disk_usage.labels(path=path, type='free').set(disk.free)
                    self.disk_usage.labels(path=path, type='total').set(disk.total)
                except:
                    pass  # Path might not exist
            
            # System uptime
            self.system_uptime.set(time.time() - self._start_time)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def record_detection(self, camera_id: str, vehicle_type: str, confidence: float, 
                        ocr_confidence: float, processing_time: float):
        """Record a license plate detection"""
        self.detections_total.labels(
            camera_id=camera_id, 
            vehicle_type=vehicle_type
        ).inc()
        
        self.detection_confidence.labels(camera_id=camera_id).observe(confidence)
        self.ocr_confidence.labels(camera_id=camera_id).observe(ocr_confidence)
        self.processing_duration.labels(
            camera_id=camera_id, 
            stage='total'
        ).observe(processing_time)
    
    def update_camera_metrics(self, camera_data: Dict[str, Any]):
        """Update camera-related metrics"""
        total_cameras = len(camera_data)
        online_cameras = sum(1 for cam in camera_data.values() if cam.get('status') == 'online')
        
        self.cameras_total.set(total_cameras)
        self.cameras_online.set(online_cameras)
        
        for camera_id, cam_info in camera_data.items():
            status_value = 1 if cam_info.get('status') == 'online' else 0
            self.camera_status.labels(
                camera_id=camera_id,
                name=cam_info.get('name', 'unknown'),
                ip_address=cam_info.get('ip_address', 'unknown')
            ).set(status_value)
            
            if 'fps' in cam_info:
                self.camera_fps.labels(camera_id=camera_id).set(cam_info['fps'])
    
    def record_camera_error(self, camera_id: str, error_type: str):
        """Record a camera error"""
        self.camera_errors.labels(camera_id=camera_id, error_type=error_type).inc()
    
    def record_camera_reconnect(self, camera_id: str):
        """Record a camera reconnection attempt"""
        self.camera_reconnects.labels(camera_id=camera_id).inc()
    
    def update_storage_metrics(self, storage_stats: Dict[str, Any]):
        """Update storage-related metrics"""
        if 'detections_size' in storage_stats:
            self.storage_usage.labels(type='detections').set(storage_stats['detections_size'])
        
        if 'recordings_size' in storage_stats:
            self.storage_usage.labels(type='recordings').set(storage_stats['recordings_size'])
        
        if 'total_size' in storage_stats:
            self.storage_usage.labels(type='total').set(storage_stats['total_size'])
        
        if 'file_counts' in storage_stats:
            counts = storage_stats['file_counts']
            for file_type, count in counts.items():
                self.storage_files_total.labels(type=file_type).set(count)
    
    def record_storage_cleanup(self, cleanup_type: str, files_deleted: int = 1):
        """Record storage cleanup event"""
        self.storage_cleanup_events.labels(type=cleanup_type).inc(files_deleted)
    
    def record_deduplication_save(self, camera_id: str, files_saved: int = 1):
        """Record files saved by deduplication"""
        self.deduplication_savings.labels(camera_id=camera_id).inc(files_saved)
    
    def record_api_request(self, method: str, endpoint: str, status: str, duration: float):
        """Record API request metrics"""
        self.api_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status=status
        ).inc()
        
        self.api_request_duration.labels(
            method=method, 
            endpoint=endpoint
        ).observe(duration)
    
    def record_auth_attempt(self, success: bool):
        """Record authentication attempt"""
        result = 'success' if success else 'failure'
        self.auth_attempts.labels(result=result).inc()
    
    def update_active_tokens(self, count: int):
        """Update active token count"""
        self.active_tokens.set(count)
    
    def record_permission_denial(self, user_role: str, required_permission: str):
        """Record permission denial"""
        self.permission_denials.labels(
            user_role=user_role,
            required_permission=required_permission
        ).inc()
    
    def record_model_load_time(self, model_type: str, load_time: float):
        """Record model loading time"""
        self.model_load_time.labels(model_type=model_type).set(load_time)
    
    def record_model_inference(self, model_type: str, inference_time: float):
        """Record model inference time"""
        self.model_inference_time.labels(model_type=model_type).observe(inference_time)
    
    def update_model_memory_usage(self, model_type: str, memory_bytes: int):
        """Update model memory usage"""
        self.model_memory_usage.labels(model_type=model_type).set(memory_bytes)
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        # Update system metrics before returning
        self.update_system_metrics()
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST


# Global metrics instance
metrics = LPRMetrics()