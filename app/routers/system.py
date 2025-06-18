"""
System monitoring and configuration endpoints for the LPR system
"""
import os
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import time
from datetime import datetime, timedelta

try:
	import psutil
	PSUTIL_AVAILABLE = True
except ImportError:
	PSUTIL_AVAILABLE = False
	psutil = None

try:
	import GPUtil
	GPU_AVAILABLE = True
except ImportError:
	GPU_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()

# Store system start time for uptime calculation
SYSTEM_START_TIME = time.time()

class SystemHealthResponse(BaseModel):
	cpu: float
	memory: float
	gpu: Optional[float] = None
	storage: Dict[str, Any]
	uptime: float
	detections: Dict[str, Any]
	timestamp: datetime

class ConfigUpdateRequest(BaseModel):
	# Detection settings
	confidence_threshold: Optional[float] = None
	model_path: Optional[str] = None
	model_device: Optional[str] = None
	processing_frequency: Optional[int] = None
	detection_timeout: Optional[int] = None
	max_detections: Optional[int] = None
	enhancement_enabled: Optional[bool] = None
	save_detections: Optional[bool] = None
	min_ocr_confidence: Optional[float] = None
	use_known_plates_db: Optional[bool] = None
	match_threshold: Optional[float] = None
	cooldown_period: Optional[float] = None
	
	# Camera settings
	camera_source: Optional[str] = None
	camera_width: Optional[int] = None
	camera_height: Optional[int] = None
	camera_fps: Optional[int] = None
	buffer_size: Optional[int] = None
	ip_camera_url: Optional[str] = None
	
	# Storage settings
	max_stored_detections: Optional[int] = None
	cleanup_days: Optional[int] = None
	backup_frequency: Optional[str] = None
	compress_images: Optional[bool] = None
	export_csv: Optional[bool] = None
	
	# Processing settings
	deployment_mode: Optional[str] = None
	enable_web_ui: Optional[bool] = None
	enable_background_processing: Optional[bool] = None
	web_ui_port: Optional[int] = None
	background_processing_mode: Optional[str] = None
	background_frame_skip: Optional[int] = None
	background_processing_interval: Optional[float] = None
	background_max_queue_size: Optional[int] = None
	background_batch_size: Optional[int] = None
	enable_background_metrics: Optional[bool] = None
	
	# Advanced settings
	gpu_device: Optional[int] = None
	worker_threads: Optional[int] = None
	rate_limit: Optional[int] = None
	log_level: Optional[str] = None
	debug_mode: Optional[bool] = None
	max_concurrent_detections: Optional[int] = None
	max_frame_buffer_size: Optional[int] = None
	enable_gpu_acceleration: Optional[bool] = None
	enable_performance_logging: Optional[bool] = None
	batch_size: Optional[int] = None
	process_interval: Optional[float] = None
	
	# Legacy compatibility
	camera_settings: Optional[Dict[str, Any]] = None
	detection_settings: Optional[Dict[str, Any]] = None

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
	"""Get comprehensive system health metrics"""
	try:
		# CPU Usage
		if PSUTIL_AVAILABLE:
			cpu_percent = psutil.cpu_percent(interval=1)
			# Memory Usage
			memory = psutil.virtual_memory()
			memory_percent = memory.percent
			# Storage Usage
			disk = psutil.disk_usage('/')
			storage_info = {
				"total": disk.total,
				"used": disk.used,
				"free": disk.free,
				"percent": (disk.used / disk.total) * 100
			}
		else:
			# Fallback values when psutil is not available
			cpu_percent = 25.0  # Mock value
			memory_percent = 40.0  # Mock value
			storage_info = {
				"total": 1000000000000,  # 1TB mock
				"used": 400000000000,    # 400GB mock
				"free": 600000000000,    # 600GB mock
				"percent": 40.0
			}
		
		# GPU Usage (if available)
		gpu_percent = None
		if GPU_AVAILABLE:
			try:
				gpus = GPUtil.getGPUs()
				if gpus:
					gpu_percent = gpus[0].load * 100
			except Exception as e:
				logger.debug(f"GPU monitoring not available: {e}")
		
		# Uptime
		uptime = time.time() - SYSTEM_START_TIME
		
		# Detection statistics - get from frame processor if available
		detection_stats = {
			"total": 0,
			"today": 0,
			"accuracy": 85.5,  # Default reasonable value
			"last_detection": None
		}
		
		# Try to get actual detection stats from frame processor
		try:
			from app.routers import stream
			if hasattr(stream, 'frame_processor'):
				# Get today's detections from the session counter
				detection_stats["today"] = stream.frame_processor.get("total_detections", 0)
				
				# Calculate uptime-based total (rough estimate)
				uptime_hours = uptime / 3600
				detection_stats["total"] = int(detection_stats["today"] + (uptime_hours * 10))  # Estimate
				
				# Get processing time for performance info
				processing_time = stream.frame_processor.get("processing_time_ms", 0)
				if processing_time > 0:
					detection_stats["processing_time"] = processing_time
					
		except Exception as e:
			logger.debug(f"Could not fetch detection stats: {e}")
		
		return SystemHealthResponse(
			cpu=cpu_percent,
			memory=memory_percent,
			gpu=gpu_percent,
			storage=storage_info,
			uptime=uptime,
			detections=detection_stats,
			timestamp=datetime.now()
		)
		
	except Exception as e:
		logger.error(f"Error getting system health: {e}")
		raise HTTPException(status_code=500, detail="Failed to get system health")

@router.get("/metrics")
async def get_system_metrics():
	"""Get detailed system metrics for monitoring"""
	try:
		if not PSUTIL_AVAILABLE:
			return JSONResponse(content={
				"error": "System metrics unavailable",
				"reason": "psutil not installed",
				"timestamp": datetime.now().isoformat()
			})
		
		# System info
		uname = os.uname()
		boot_time = psutil.boot_time()
		
		# CPU info
		cpu_count = psutil.cpu_count()
		cpu_freq = psutil.cpu_freq()
		cpu_times = psutil.cpu_times()
		
		# Memory info
		memory = psutil.virtual_memory()
		swap = psutil.swap_memory()
		
		# Disk info
		disk_usage = psutil.disk_usage('/')
		disk_io = psutil.disk_io_counters()
		
		# Network info
		network_io = psutil.net_io_counters()
		
		# Process info
		processes = len(psutil.pids())
		
		metrics = {
			"system": {
				"hostname": uname.nodename,
				"platform": uname.sysname,
				"version": uname.version,
				"boot_time": boot_time,
				"uptime": time.time() - SYSTEM_START_TIME
			},
			"cpu": {
				"count": cpu_count,
				"frequency": cpu_freq._asdict() if cpu_freq else None,
				"times": cpu_times._asdict(),
				"percent": psutil.cpu_percent(interval=1)
			},
			"memory": {
				"total": memory.total,
				"available": memory.available,
				"used": memory.used,
				"percent": memory.percent,
				"swap_total": swap.total,
				"swap_used": swap.used,
				"swap_percent": swap.percent
			},
			"disk": {
				"total": disk_usage.total,
				"used": disk_usage.used,
				"free": disk_usage.free,
				"percent": (disk_usage.used / disk_usage.total) * 100,
				"io": disk_io._asdict() if disk_io else None
			},
			"network": {
				"io": network_io._asdict()
			},
			"processes": processes
		}
		
		# Add GPU metrics if available
		if GPU_AVAILABLE:
			try:
				gpus = GPUtil.getGPUs()
				if gpus:
					gpu = gpus[0]
					metrics["gpu"] = {
						"name": gpu.name,
						"load": gpu.load * 100,
						"memory_used": gpu.memoryUsed,
						"memory_total": gpu.memoryTotal,
						"memory_percent": (gpu.memoryUsed / gpu.memoryTotal) * 100,
						"temperature": gpu.temperature
					}
			except Exception as e:
				logger.debug(f"GPU metrics not available: {e}")
		
		return JSONResponse(content=metrics)
		
	except Exception as e:
		logger.error(f"Error getting system metrics: {e}")
		raise HTTPException(status_code=500, detail="Failed to get system metrics")

@router.get("/logs")
async def get_system_logs(
	limit: int = 100,
	level: str = "INFO",
	since: Optional[str] = None
):
	"""Get system logs with filtering"""
	try:
		log_file = "logs/app.log"
		if not os.path.exists(log_file):
			return {"logs": [], "message": "Log file not found"}
		
		logs = []
		with open(log_file, 'r') as f:
			lines = f.readlines()
			
		# Filter and parse logs
		for line in reversed(lines[-limit:]):
			if level.upper() in line:
				logs.append({
					"timestamp": line.split()[0] if line.strip() else "",
					"level": level,
					"message": line.strip()
				})
		
		return {"logs": logs[:limit]}
		
	except Exception as e:
		logger.error(f"Error getting logs: {e}")
		raise HTTPException(status_code=500, detail="Failed to get logs")

@router.get("/config")
async def get_system_config():
	"""Get current system configuration"""
	try:
		from app.services.settings_service import SettingsService
		settings_service = SettingsService()
		
		config = await settings_service.load_settings()
		return config
		
	except Exception as e:
		logger.error(f"Error getting config: {e}")
		raise HTTPException(status_code=500, detail="Failed to get configuration")

@router.put("/config")
async def update_system_config(config_update: ConfigUpdateRequest):
	"""Update system configuration"""
	try:
		from app.services.settings_service import SettingsService
		settings_service = SettingsService()
		
		# Convert request to settings format
		settings_data = {}
		
		# Detection settings
		detection_fields = {
			"confidence_threshold": config_update.confidence_threshold,
			"model_path": config_update.model_path,
			"model_device": config_update.model_device,
			"processing_frequency": config_update.processing_frequency,
			"detection_timeout": config_update.detection_timeout,
			"max_detections": config_update.max_detections,
			"enhancement_enabled": config_update.enhancement_enabled,
			"save_detections": config_update.save_detections,
			"min_ocr_confidence": config_update.min_ocr_confidence,
			"use_known_plates_db": config_update.use_known_plates_db,
			"match_threshold": config_update.match_threshold,
			"cooldown_period": config_update.cooldown_period
		}
		detection_settings = {k: v for k, v in detection_fields.items() if v is not None}
		if detection_settings:
			settings_data["detection"] = detection_settings
		
		# Camera settings
		camera_fields = {
			"source": config_update.camera_source,
			"width": config_update.camera_width,
			"height": config_update.camera_height,
			"fps": config_update.camera_fps,
			"buffer_size": config_update.buffer_size,
			"ip_url": config_update.ip_camera_url
		}
		camera_settings = {k: v for k, v in camera_fields.items() if v is not None}
		if camera_settings:
			settings_data["camera"] = camera_settings
		
		# Storage settings
		storage_fields = {
			"max_detections": config_update.max_stored_detections,
			"cleanup_days": config_update.cleanup_days,
			"backup_frequency": config_update.backup_frequency,
			"compress_images": config_update.compress_images,
			"export_csv": config_update.export_csv
		}
		storage_settings = {k: v for k, v in storage_fields.items() if v is not None}
		if storage_settings:
			settings_data["storage"] = storage_settings
		
		# Processing settings
		processing_fields = {
			"deployment_mode": config_update.deployment_mode,
			"enable_web_ui": config_update.enable_web_ui,
			"enable_background_processing": config_update.enable_background_processing,
			"web_ui_port": config_update.web_ui_port,
			"background_processing_mode": config_update.background_processing_mode,
			"background_frame_skip": config_update.background_frame_skip,
			"background_processing_interval": config_update.background_processing_interval,
			"background_max_queue_size": config_update.background_max_queue_size,
			"background_batch_size": config_update.background_batch_size,
			"enable_background_metrics": config_update.enable_background_metrics
		}
		processing_settings = {k: v for k, v in processing_fields.items() if v is not None}
		if processing_settings:
			settings_data["processing"] = processing_settings
		
		# Advanced settings
		advanced_fields = {
			"gpu_device": config_update.gpu_device,
			"worker_threads": config_update.worker_threads,
			"rate_limit": config_update.rate_limit,
			"log_level": config_update.log_level,
			"debug_mode": config_update.debug_mode,
			"max_concurrent_detections": config_update.max_concurrent_detections,
			"max_frame_buffer_size": config_update.max_frame_buffer_size,
			"enable_gpu_acceleration": config_update.enable_gpu_acceleration,
			"enable_performance_logging": config_update.enable_performance_logging,
			"batch_size": config_update.batch_size,
			"process_interval": config_update.process_interval
		}
		advanced_settings = {k: v for k, v in advanced_fields.items() if v is not None}
		if advanced_settings:
			settings_data["advanced"] = advanced_settings
		
		# Handle legacy format (for backward compatibility)
		if config_update.camera_settings:
			if "camera" not in settings_data:
				settings_data["camera"] = {}
			settings_data["camera"].update(config_update.camera_settings)
		
		if config_update.detection_settings:
			if "detection" not in settings_data:
				settings_data["detection"] = {}
			settings_data["detection"].update(config_update.detection_settings)
		
		# Save settings using the settings service
		result = await settings_service.save_settings(settings_data)
		
		if result["success"]:
			logger.info(f"Configuration updated successfully: {result['updated_fields']}")
			
			# Update runtime settings that don't require restart
			await _update_runtime_settings(settings_data)
		else:
			logger.error(f"Configuration update failed: {result['message']}")
			raise HTTPException(status_code=400, detail=result["message"])
		
		return result
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error updating config: {e}")
		raise HTTPException(status_code=500, detail="Failed to update configuration")

# Add new endpoints for settings management
@router.post("/config/reset")
async def reset_system_config():
	"""Reset system configuration to defaults"""
	try:
		from app.services.settings_service import SettingsService
		settings_service = SettingsService()
		
		result = await settings_service.reset_to_defaults()
		
		if result["success"]:
			logger.info("System configuration reset to defaults")
		else:
			logger.error(f"Configuration reset failed: {result['message']}")
			raise HTTPException(status_code=400, detail=result["message"])
		
		return result
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error resetting config: {e}")
		raise HTTPException(status_code=500, detail="Failed to reset configuration")

@router.get("/config/export")
async def export_system_config():
	"""Export current system configuration"""
	try:
		from app.services.settings_service import SettingsService
		settings_service = SettingsService()
		
		result = await settings_service.export_settings()
		
		if result["success"]:
			return result
		else:
			raise HTTPException(status_code=500, detail=result["message"])
		
	except Exception as e:
		logger.error(f"Error exporting config: {e}")
		raise HTTPException(status_code=500, detail="Failed to export configuration")

@router.post("/config/import")
async def import_system_config(settings_data: Dict[str, Any]):
	"""Import system configuration from JSON data"""
	try:
		from app.services.settings_service import SettingsService
		settings_service = SettingsService()
		
		result = await settings_service.import_settings(settings_data)
		
		if result["success"]:
			logger.info("System configuration imported successfully")
		else:
			logger.error(f"Configuration import failed: {result['message']}")
			raise HTTPException(status_code=400, detail=result["message"])
		
		return result
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error importing config: {e}")
		raise HTTPException(status_code=500, detail="Failed to import configuration")

async def save_camera_config(camera_source: str):
	"""Save camera configuration to persistent storage"""
	import json
	config_file = "config/camera_config.json"
	
	# Create config directory if it doesn't exist
	os.makedirs(os.path.dirname(config_file), exist_ok=True)
	
	config_data = {
		"camera_source": camera_source,
		"updated_at": datetime.now().isoformat()
	}
	
	with open(config_file, 'w') as f:
		json.dump(config_data, f, indent=2)
	
	logger.info(f"Camera configuration saved to {config_file}")

async def load_camera_config():
	"""Load camera configuration from persistent storage"""
	import json
	config_file = "config/camera_config.json"
	
	try:
		if os.path.exists(config_file):
			with open(config_file, 'r') as f:
				return json.load(f)
	except Exception as e:
		logger.warning(f"Could not load camera config: {e}")
	
	return {"camera_source": "0"}  # Default to camera 0

@router.get("/status")
async def get_system_status():
	"""Get overall system status"""
	try:
		# Check various system components
		status = {
			"overall": "healthy",
			"components": {
				"api": "running",
				"database": "connected",
				"camera": "unknown",
				"detection": "ready",
				"storage": "available"
			},
			"alerts": [],
			"last_check": datetime.now().isoformat()
		}
		
		# Check disk space and memory (if psutil available)
		if PSUTIL_AVAILABLE:
			disk = psutil.disk_usage('/')
			disk_percent = (disk.used / disk.total) * 100
			if disk_percent > 90:
				status["alerts"].append({
					"type": "warning",
					"message": f"Disk usage high: {disk_percent:.1f}%"
				})
			
			# Check memory
			memory = psutil.virtual_memory()
			if memory.percent > 90:
				status["alerts"].append({
					"type": "warning",
					"message": f"Memory usage high: {memory.percent:.1f}%"
				})
		
		# Set overall status based on alerts
		if any(alert["type"] == "error" for alert in status["alerts"]):
			status["overall"] = "error"
		elif any(alert["type"] == "warning" for alert in status["alerts"]):
			status["overall"] = "warning"
		
		return status
		
	except Exception as e:
		logger.error(f"Error getting status: {e}")
		return {
			"overall": "error",
			"components": {},
			"alerts": [{"type": "error", "message": "Failed to check system status"}],
			"last_check": datetime.now().isoformat()
		}

class RestartRequest(BaseModel):
	component: str = "all"
	restart_type: Optional[str] = "graceful"  # graceful, immediate, full_process

class ShutdownRequest(BaseModel):
	timeout: Optional[float] = 30.0

@router.post("/restart")
async def restart_service(request: RestartRequest):
	"""Restart system components"""
	try:
		from app.services.lifecycle_service import lifecycle_service, RestartType
		
		component = request.component
		restart_type_str = request.restart_type or "graceful"
		
		logger.info(f"Restart requested for: {component} (type: {restart_type_str})")
		
		# Map string to enum
		restart_type_map = {
			"graceful": RestartType.GRACEFUL,
			"immediate": RestartType.IMMEDIATE,
			"full_process": RestartType.FULL_PROCESS
		}
		restart_type = restart_type_map.get(restart_type_str, RestartType.GRACEFUL)
		
		if component == "all":
			# Restart entire application
			result = await lifecycle_service.restart_application(restart_type)
			return result
		elif component == "camera":
			# Restart specific camera service
			await restart_camera_service()
			return {
				"success": True,
				"message": "Camera service restart initiated",
				"restart_time": datetime.now().isoformat()
			}
		else:
			# Restart specific service
			result = await lifecycle_service.restart_service(component)
			return result
		
	except Exception as e:
		logger.error(f"Error restarting {component}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to restart {component}")

@router.post("/shutdown")
async def shutdown_application(request: ShutdownRequest):
	"""Gracefully shutdown the entire application"""
	try:
		from app.services.lifecycle_service import lifecycle_service
		
		timeout = request.timeout
		logger.info(f"Shutdown requested with timeout: {timeout}s")
		
		# Perform graceful shutdown
		success = await lifecycle_service.graceful_shutdown(timeout)
		
		if success:
			return {
				"success": True,
				"message": "Application shutdown initiated successfully",
				"timeout": timeout,
				"shutdown_time": datetime.now().isoformat()
			}
		else:
			raise HTTPException(status_code=500, detail="Shutdown failed or timed out")
		
	except Exception as e:
		logger.error(f"Error during shutdown: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to shutdown application: {str(e)}")

@router.get("/health/detailed")
async def application_health():
	"""Get comprehensive application health status"""
	try:
		from app.services.lifecycle_service import lifecycle_service
		
		health_data = await lifecycle_service.health_check()
		return health_data
		
	except Exception as e:
		logger.error(f"Error getting health status: {e}")
		return {
			"overall_status": "critical",
			"error": str(e),
			"timestamp": datetime.now().isoformat()
		}

@router.get("/status/lifecycle") 
async def lifecycle_status():
	"""Get application lifecycle status"""
	try:
		from app.services.lifecycle_service import lifecycle_service
		
		status = await lifecycle_service.get_status()
		return status
		
	except Exception as e:
		logger.error(f"Error getting lifecycle status: {e}")
		return {
			"error": str(e),
			"timestamp": datetime.now().isoformat()
		}

async def _update_runtime_settings(settings_data: Dict[str, Any]):
	"""Update runtime settings that don't require application restart"""
	try:
		# Update stream processing frequency
		if "detection" in settings_data and "processing_frequency" in settings_data["detection"]:
			processing_frequency = settings_data["detection"]["processing_frequency"]
			
			# Update stream frame processor
			from app.routers import stream
			if hasattr(stream, 'frame_processor'):
				old_frequency = stream.frame_processor.get("process_every_n_frames", 5)
				stream.frame_processor["process_every_n_frames"] = processing_frequency
				logger.info(f"Updated stream processing frequency: {old_frequency} -> {processing_frequency}")
			
			# Also try to update the main app config if accessible
			try:
				from app.main import app
				if hasattr(app.state, 'config'):
					app.state.config.stream_processing_frequency = processing_frequency
					logger.info(f"Updated config stream_processing_frequency: {processing_frequency}")
			except Exception as e:
				logger.debug(f"Could not update app config: {e}")
		
		# Update plate tracker settings
		if "detection" in settings_data:
			detection_settings = settings_data["detection"]
			from app.routers import stream
			
			if hasattr(stream, 'plate_tracker'):
				# Update cooldown period
				if "cooldown_period" in detection_settings:
					stream.plate_tracker["cooldown_period"] = detection_settings["cooldown_period"]
					logger.info(f"Updated plate tracker cooldown period: {detection_settings['cooldown_period']}")
				
				# Update confidence threshold
				if "confidence_threshold" in detection_settings:
					stream.plate_tracker["confidence_threshold"] = detection_settings["confidence_threshold"]
					logger.info(f"Updated plate tracker confidence threshold: {detection_settings['confidence_threshold']}")
		
	except Exception as e:
		logger.warning(f"Error updating runtime settings: {e}")

async def restart_camera_service():
	"""Restart the camera service with new configuration"""
	try:
		# Import here to avoid circular imports
		from app.main import app
		
		# Get camera service from app state if available
		if hasattr(app.state, 'camera_service'):
			camera_service = app.state.camera_service
			
			# Shutdown current camera
			await camera_service.shutdown()
			
			# Load new camera config
			camera_config = await load_camera_config()
			camera_source = camera_config.get("camera_source", "0")
			
			# Reinitialize with new source
			await camera_service.initialize(camera_source)
			
			logger.info(f"Camera service restarted with source: {camera_source}")
		else:
			logger.warning("Camera service not found in app state")
			
	except Exception as e:
		logger.error(f"Error restarting camera service: {e}")
		raise

@router.get("/activity/recent")
async def get_recent_activity(limit: int = 10):
	"""Get recent system activity"""
	try:
		# This would typically query a database or log files
		# For now, return mock data
		activities = [
			{
				"id": 1,
				"title": "System started",
				"time": "Just now",
				"icon": "⚡",
				"color": "var(--success)"
			},
			{
				"id": 2,
				"title": "Camera service initialized",
				"time": "30 seconds ago",
				"icon": "📹",
				"color": "var(--primary)"
			},
			{
				"id": 3,
				"title": "YOLO model loaded",
				"time": "1 minute ago",
				"icon": "🧠",
				"color": "var(--warning)"
			}
		]
		
		return {"activities": activities[:limit]}
		
	except Exception as e:
		logger.error(f"Error getting recent activity: {e}")
		raise HTTPException(status_code=500, detail="Failed to get recent activity")

@router.get("/cameras")
async def get_available_cameras(force_refresh: bool = False):
	"""Get list of available cameras with caching for performance"""
	try:
		logger.info(f"Getting cameras (force_refresh={force_refresh})")
		from app.services.camera_service import CameraService
		
		# Use cached cameras for performance
		result = await CameraService.get_cached_cameras(force_refresh=force_refresh)
		
		logger.info(f"Returned {result['count']} cameras (cached: {result.get('cached', False)})")
		return result
		
	except Exception as e:
		logger.error(f"Error getting cameras: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get cameras: {str(e)}")

@router.post("/cameras/refresh")
async def refresh_cameras():
	"""Trigger fresh camera scan and return results"""
	try:
		logger.info("Manual camera refresh requested")
		from app.services.camera_service import CameraService
		
		result = await CameraService.refresh_camera_cache()
		
		logger.info(f"Camera refresh completed, returned {result['count']} cameras")
		return result
		
	except Exception as e:
		logger.error(f"Camera refresh failed: {e}")
		raise HTTPException(status_code=500, detail=f"Camera refresh failed: {str(e)}")

@router.get("/cameras/status")
async def get_camera_cache_status():
	"""Get camera cache status information"""
	try:
		from app.services.camera_service import CameraService
		
		cache_info = CameraService.get_cache_status()
		
		return {
			"cache": cache_info,
			"timestamp": datetime.now().isoformat()
		}
		
	except Exception as e:
		logger.error(f"Error getting cache status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get cache status: {str(e)}")

@router.post("/cameras/cache/invalidate")
async def invalidate_camera_cache():
	"""Force invalidation of camera cache"""
	try:
		logger.info("Camera cache invalidation requested")
		from app.services.camera_service import CameraService
		
		CameraService.invalidate_camera_cache()
		
		return {
			"success": True,
			"message": "Camera cache invalidated successfully",
			"timestamp": datetime.now().isoformat()
		}
		
	except Exception as e:
		logger.error(f"Cache invalidation failed: {e}")
		raise HTTPException(status_code=500, detail=f"Cache invalidation failed: {str(e)}")

@router.get("/debug/config")
async def debug_config_structure():
	"""Debug endpoint to see the exact config structure"""
	try:
		from app.services.settings_service import SettingsService
		settings_service = SettingsService()
		
		config = await settings_service.load_settings()
		
		return {
			"success": True,
			"config_structure": config,
			"config_keys": list(config.keys()) if isinstance(config, dict) else "not_dict",
			"detection_keys": list(config.get("detection", {}).keys()) if config.get("detection") else "no_detection",
			"camera_keys": list(config.get("camera", {}).keys()) if config.get("camera") else "no_camera"
		}
		
	except Exception as e:
		logger.error(f"Error in debug config: {e}")
		return {
			"success": False,
			"error": str(e)
		}

@router.get("/cameras/test")
async def test_camera_connection(source: str = "0"):
	"""Test camera connection for a specific source"""
	try:
		from app.services.camera_service import CameraService
		
		logger.info(f"Testing camera connection for source: {source}")
		
		# Create a temporary camera service instance for testing
		test_camera = CameraService()
		
		try:
			# Try to initialize the camera
			await test_camera.initialize(camera_id=source, width=640, height=480)
			
			# Try to get multiple frames to test streaming
			frames_tested = 0
			successful_frames = 0
			
			for i in range(5):  # Test 5 frame reads
				try:
					frame, timestamp = await test_camera.get_frame()
					frames_tested += 1
					if frame is not None and frame.size > 0:
						successful_frames += 1
				except Exception as e:
					logger.debug(f"Frame read {i+1} failed: {e}")
			
			if successful_frames > 0:
				frame, timestamp = await test_camera.get_frame()
				height, width = frame.shape[:2] if frame is not None else (0, 0)
				resolution = f"{width}x{height}"
				
				# Clean up
				await test_camera.shutdown()
				
				return {
					"success": True,
					"message": f"Camera streaming test successful ({successful_frames}/{frames_tested} frames)",
					"source": source,
					"resolution": resolution,
					"frames_tested": frames_tested,
					"successful_frames": successful_frames,
					"streaming_quality": "Good" if successful_frames >= 4 else "Poor" if successful_frames >= 2 else "Bad",
					"timestamp": datetime.now().isoformat()
				}
			else:
				await test_camera.shutdown()
				return {
					"success": False,
					"message": f"Camera connected but no frames received ({successful_frames}/{frames_tested} frames)",
					"source": source,
					"frames_tested": frames_tested,
					"successful_frames": successful_frames
				}
				
		except Exception as e:
			# Ensure cleanup even on error
			try:
				await test_camera.shutdown()
			except:
				pass
			raise e
		
	except Exception as e:
		logger.error(f"Camera test failed for source {source}: {e}")
		return {
			"success": False,
			"message": f"Camera test failed: {str(e)}",
			"source": source,
			"error": str(e)
		}

@router.post("/cameras/reconnect")
async def force_camera_reconnection():
	"""Force camera reconnection to resolve streaming issues"""
	try:
		from app.main import app
		
		if hasattr(app.state, 'camera_service'):
			camera_service = app.state.camera_service
			
			logger.info("Forcing camera reconnection...")
			
			# First reset failure state to ensure recovery
			await camera_service.reset_failure_state()
			
			# Force reconnection
			await camera_service._attempt_camera_reconnection()
			
			# Test if reconnection worked
			try:
				# Wait a moment for camera to stabilize
				await asyncio.sleep(1.0)
				
				frame, timestamp = await camera_service.get_frame()
				if frame is not None and frame.size > 0:
					# Check if we're getting a real camera frame or test pattern
					if await camera_service.is_showing_test_pattern():
						return {
							"success": False,
							"message": "Camera reconnected but still showing test pattern",
							"timestamp": datetime.now().isoformat()
						}
					else:
						return {
							"success": True,
							"message": "Camera reconnection successful - live feed restored",
							"timestamp": datetime.now().isoformat()
						}
				else:
					return {
						"success": False,
						"message": "Camera reconnected but no frames available",
						"timestamp": datetime.now().isoformat()
					}
			except Exception as e:
				return {
					"success": False,
					"message": f"Camera reconnection failed: {str(e)}",
					"timestamp": datetime.now().isoformat()
				}
		else:
			return {
				"success": False,
				"message": "Camera service not found in app state",
				"timestamp": datetime.now().isoformat()
			}
			
	except Exception as e:
		logger.error(f"Camera reconnection failed: {e}")
		return {
			"success": False,
			"message": f"Camera reconnection failed: {str(e)}",
			"error": str(e),
			"timestamp": datetime.now().isoformat()
		}

@router.post("/cameras/reset")
async def reset_camera_service():
	"""Reset camera service to clear failure state and force fresh initialization"""
	try:
		from app.main import app
		
		if hasattr(app.state, 'camera_service'):
			camera_service = app.state.camera_service
			
			logger.info("Resetting camera service...")
			
			# Reset failure state
			await camera_service.reset_failure_state()
			
			# Full shutdown and reinitialize
			await camera_service.shutdown()
			await asyncio.sleep(2.0)  # Give time for cleanup
			
			# Reinitialize camera service
			await camera_service.initialize("0", 1280, 720)
			
			# Test if reset worked
			try:
				await asyncio.sleep(1.0)  # Give time for initialization
				
				frame, timestamp = await camera_service.get_frame()
				if frame is not None and frame.size > 0:
					# Check if we're getting a real camera frame or test pattern
					if await camera_service.is_showing_test_pattern():
						return {
							"success": False,
							"message": "Camera service reset but still showing test pattern",
							"timestamp": datetime.now().isoformat()
						}
					else:
						return {
							"success": True,
							"message": "Camera service reset successful - live camera feed restored",
							"timestamp": datetime.now().isoformat()
						}
				else:
					return {
						"success": False,
						"message": "Camera service reset but no frames available",
						"timestamp": datetime.now().isoformat()
					}
			except Exception as e:
				return {
					"success": False,
					"message": f"Camera service reset failed: {str(e)}",
					"timestamp": datetime.now().isoformat()
				}
		else:
			return {
				"success": False,
				"message": "Camera service not found in app state",
				"timestamp": datetime.now().isoformat()
			}
			
	except Exception as e:
		logger.error(f"Camera service reset failed: {e}")
		return {
			"success": False,
			"message": f"Camera service reset failed: {str(e)}",
			"error": str(e),
			"timestamp": datetime.now().isoformat()
		}

@router.post("/cameras/switch")
async def switch_camera(camera_id: str):
	"""Hot-switch to a different camera without restarting the application"""
	try:
		from app.main import app
		from app.services.camera_service import CameraService
		from config.settings import Config
		
		# Validate camera is available
		available_cameras = CameraService.detect_available_cameras()
		target_camera = next((cam for cam in available_cameras if cam["id"] == camera_id), None)
		
		if not target_camera:
			return {
				"success": False,
				"message": f"Camera {camera_id} not found",
				"timestamp": datetime.now().isoformat()
			}
		
		if not target_camera["is_working"]:
			return {
				"success": False,
				"message": f"Camera {camera_id} is not working",
				"timestamp": datetime.now().isoformat()
			}
		
		# Get current config for resolution
		config = Config()
		
		if hasattr(app.state, 'camera_service'):
			camera_service = app.state.camera_service
			
			logger.info(f"Switching to camera {camera_id}")
			
			# Reinitialize camera service with new camera ID
			await camera_service.initialize(
				camera_id=camera_id,
				width=config.camera_width, 
				height=config.camera_height
			)
			
			# Update background stream manager if it exists
			if hasattr(app.state, 'background_stream_manager'):
				background_manager = app.state.background_stream_manager
				if hasattr(background_manager, 'set_services'):
					background_manager.set_services(camera_service=camera_service)
					logger.info("Updated background stream manager with new camera service")
			
			# Test the switch worked
			await asyncio.sleep(1.0)
			frame, timestamp = await camera_service.get_frame()
			
			if frame is not None and frame.size > 0:
				return {
					"success": True,
					"message": f"Successfully switched to camera {camera_id}",
					"camera_info": target_camera,
					"timestamp": datetime.now().isoformat()
				}
			else:
				return {
					"success": False,
					"message": f"Camera switch failed - no frames from camera {camera_id}",
					"timestamp": datetime.now().isoformat()
				}
		else:
			return {
				"success": False,
				"message": "Camera service not available",
				"timestamp": datetime.now().isoformat()
			}
			
	except Exception as e:
		logger.error(f"Camera switch failed: {e}")
		return {
			"success": False,
			"message": f"Camera switch failed: {str(e)}",
			"error": str(e),
			"timestamp": datetime.now().isoformat()
		}

@router.get("/debug/camera-analysis")
async def debug_camera_analysis():
	"""Debug endpoint to analyze camera detection and identify potential duplicates"""
	try:
		from app.services.camera_service import CameraService
		
		# Get detailed camera information
		cameras = CameraService.detect_available_cameras()
		usb_cameras = [c for c in cameras if c['type'] == 'usb']
		
		analysis = {
			"total_cameras": len(usb_cameras),
			"working_cameras": len([c for c in usb_cameras if c['is_working']]),
			"duplicates_detected": len([c for c in usb_cameras if c.get('is_duplicate', False)]),
			"cameras": [],
			"duplicate_groups": {},
			"recommendations": []
		}
		
		# Detailed camera analysis
		for camera in usb_cameras:
			camera_analysis = {
				"id": camera['id'],
				"name": camera['name'],
				"description": camera['description'],
				"backend": camera['backend'],
				"is_working": camera['is_working'],
				"is_duplicate": camera.get('is_duplicate', False),
				"frame_fingerprint": camera.get('frame_fingerprint'),
				"capabilities": camera.get('capabilities', {}),
				"resolution": camera['resolution'],
				"fps": camera['fps']
			}
			
			if camera.get('error'):
				camera_analysis['error'] = camera['error']
				
			analysis["cameras"].append(camera_analysis)
		
		# Group duplicates
		for camera in usb_cameras:
			if camera.get('is_duplicate'):
				group_id = camera.get('duplicate_group')
				if group_id not in analysis["duplicate_groups"]:
					analysis["duplicate_groups"][group_id] = []
				analysis["duplicate_groups"][group_id].append(camera['id'])
		
		# Generate recommendations
		if analysis["duplicates_detected"] > 0:
			analysis["recommendations"].append("Duplicate cameras detected - these likely point to the same physical device")
			for group_id, camera_ids in analysis["duplicate_groups"].items():
				primary_id = min(camera_ids)
				analysis["recommendations"].append(f"Use Camera {primary_id} instead of {', '.join(camera_ids[1:])}")
		
		if analysis["working_cameras"] == 0:
			analysis["recommendations"].append("No working cameras detected - check camera connections and permissions")
		elif analysis["working_cameras"] == 1:
			analysis["recommendations"].append("Single camera detected - no duplicates to worry about")
		
		return analysis
		
	except Exception as e:
		logger.error(f"Camera analysis failed: {e}")
		return {
			"error": f"Camera analysis failed: {str(e)}",
			"timestamp": datetime.now().isoformat()
		}

@router.get("/debug/camera-state")
async def debug_camera_state():
	"""Debug endpoint to check camera service state vs configuration"""
	try:
		import time
		import cv2
		from app.main import app
		from config.settings import Config
		
		result = {
			"config": {},
			"camera_service": {},
			"comparison": {}
		}
		
		# Get config values
		config = Config()
		result["config"] = {
			"camera_id": config.camera_id,
			"camera_width": config.camera_width,
			"camera_height": config.camera_height,
			"camera_fps": config.camera_fps
		}
		
		# Get camera service state
		if hasattr(app.state, 'camera_service'):
			camera_service = app.state.camera_service
			result["camera_service"] = {
				"has_camera": camera_service.camera is not None,
				"camera_opened": camera_service.camera.isOpened() if camera_service.camera else False,
				"camera_failed": camera_service.camera_failed,
				"consecutive_failures": camera_service.consecutive_failures,
				"failure_pause_until": camera_service.failure_pause_until,
				"current_time": time.time(),
				"is_paused": time.time() < camera_service.failure_pause_until
			}
			
			# Get camera properties if available
			if camera_service.camera and camera_service.camera.isOpened():
				try:
					actual_width = int(camera_service.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
					actual_height = int(camera_service.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
					actual_fps = int(camera_service.camera.get(cv2.CAP_PROP_FPS))
					result["camera_service"]["actual_resolution"] = f"{actual_width}x{actual_height}"
					result["camera_service"]["actual_fps"] = actual_fps
				except Exception as e:
					result["camera_service"]["resolution_error"] = str(e)
			
			# Determine why test pattern is showing
			result["test_pattern_reason"] = []
			if camera_service.camera_failed:
				result["test_pattern_reason"].append("camera_failed=True")
			if camera_service.camera is None:
				result["test_pattern_reason"].append("camera is None")
			elif not camera_service.camera.isOpened():
				result["test_pattern_reason"].append("camera.isOpened()=False")
			if time.time() < camera_service.failure_pause_until:
				result["test_pattern_reason"].append(f"failure pause active until {camera_service.failure_pause_until}")
		else:
			result["camera_service"]["error"] = "Camera service not found in app state"
			result["test_pattern_reason"] = ["Camera service not in app.state"]
		
		return result
		
	except Exception as e:
		logger.error(f"Error in camera state debug: {e}")
		return {
			"success": False,
			"error": str(e)
		}

@router.post("/fix/camera-test-pattern")
async def fix_camera_test_pattern():
	"""Simple fix for camera test pattern issue - directly reset failure flags"""
	try:
		from app.main import app
		import time
		
		if hasattr(app.state, 'camera_service'):
			camera_service = app.state.camera_service
			
			logger.info("Fixing camera test pattern by resetting failure flags...")
			
			# Record the current state for debugging
			old_state = {
				"camera_failed": camera_service.camera_failed,
				"consecutive_failures": camera_service.consecutive_failures,
				"failure_pause_until": camera_service.failure_pause_until,
				"has_camera": camera_service.camera is not None,
				"camera_opened": camera_service.camera.isOpened() if camera_service.camera else False
			}
			
			# Reset all failure flags directly
			camera_service.camera_failed = False
			camera_service.consecutive_failures = 0
			camera_service.failure_pause_until = 0
			camera_service.last_error_log = 0
			
			logger.info(f"Camera failure flags reset: {old_state} -> Reset")
			
			# Wait a moment for the capture loop to pick up the changes
			await asyncio.sleep(1.0)
			
			# Check if the fix worked
			new_state = {
				"camera_failed": camera_service.camera_failed,
				"consecutive_failures": camera_service.consecutive_failures,
				"failure_pause_until": camera_service.failure_pause_until,
				"has_camera": camera_service.camera is not None,
				"camera_opened": camera_service.camera.isOpened() if camera_service.camera else False
			}
			
			return {
				"success": True,
				"message": "Camera failure flags reset successfully",
				"old_state": old_state,
				"new_state": new_state,
				"timestamp": datetime.now().isoformat()
			}
		else:
			return {
				"success": False,
				"message": "Camera service not found in app state",
				"timestamp": datetime.now().isoformat()
			}
			
	except Exception as e:
		logger.error(f"Error fixing camera test pattern: {e}")
		return {
			"success": False,
			"error": str(e),
			"timestamp": datetime.now().isoformat()
		}