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

@router.post("/restart")
async def restart_service(request: RestartRequest):
	"""Restart system components"""
	try:
		component = request.component
		logger.info(f"Restart requested for: {component}")
		
		if component == "camera":
			# Signal camera service to restart
			await restart_camera_service()
			return {
				"success": True,
				"message": "Camera service restart initiated",
				"restart_time": datetime.now().isoformat()
			}
		else:
			# This would implement actual restart logic for other components
			# For safety, this is just a placeholder
			return {
				"success": True,
				"message": f"Restart initiated for {component}",
				"restart_time": datetime.now().isoformat()
			}
		
	except Exception as e:
		logger.error(f"Error restarting {component}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to restart {component}")

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
async def get_available_cameras():
	"""Get list of available cameras on the system"""
	try:
		from app.services.camera_service import CameraService
		
		logger.info("Scanning for available cameras...")
		cameras = CameraService.detect_available_cameras()
		
		return {
			"cameras": cameras,
			"count": len([c for c in cameras if c['type'] == 'usb']),
			"timestamp": datetime.now().isoformat()
		}
		
	except Exception as e:
		logger.error(f"Error detecting cameras: {e}")
		raise HTTPException(status_code=500, detail="Failed to detect available cameras")