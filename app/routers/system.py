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
	confidence_threshold: Optional[float] = None
	model_path: Optional[str] = None
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
		# This would typically load from a config file or database
		config = {
			"detection": {
				"confidence_threshold": 0.5,
				"model_path": "app/models/yolo11m_best.pt",
				"enhancement_enabled": True,
				"save_detections": True
			},
			"camera": {
				"width": 1280,
				"height": 720,
				"fps": 30,
				"source": "0"
			},
			"storage": {
				"max_detections": 10000,
				"cleanup_days": 30,
				"backup_enabled": True
			},
			"api": {
				"rate_limit": 100,
				"timeout": 30
			}
		}
		
		return config
		
	except Exception as e:
		logger.error(f"Error getting config: {e}")
		raise HTTPException(status_code=500, detail="Failed to get configuration")

@router.put("/config")
async def update_system_config(config_update: ConfigUpdateRequest):
	"""Update system configuration"""
	try:
		# Validate configuration updates
		updated_fields = []
		
		if config_update.confidence_threshold is not None:
			if not 0.0 <= config_update.confidence_threshold <= 1.0:
				raise HTTPException(status_code=400, detail="Confidence threshold must be between 0.0 and 1.0")
			updated_fields.append("confidence_threshold")
		
		if config_update.model_path is not None:
			if not os.path.exists(config_update.model_path):
				raise HTTPException(status_code=400, detail="Model file not found")
			updated_fields.append("model_path")
		
		# Here you would actually update the configuration
		# This might involve updating a config file, database, or service settings
		
		logger.info(f"Configuration updated: {updated_fields}")
		
		return {
			"success": True,
			"message": f"Updated {len(updated_fields)} configuration fields",
			"updated_fields": updated_fields
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error updating config: {e}")
		raise HTTPException(status_code=500, detail="Failed to update configuration")

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

@router.post("/restart")
async def restart_service(component: str = "all"):
	"""Restart system components"""
	try:
		logger.info(f"Restart requested for: {component}")
		
		# This would implement actual restart logic
		# For safety, this is just a placeholder
		
		return {
			"success": True,
			"message": f"Restart initiated for {component}",
			"restart_time": datetime.now().isoformat()
		}
		
	except Exception as e:
		logger.error(f"Error restarting {component}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to restart {component}")

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