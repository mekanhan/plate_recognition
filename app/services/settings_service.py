"""
Comprehensive settings service for managing all LPR system configuration.
Handles loading, saving, and persistence of settings across application restarts.
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

from config.settings import Config, DeploymentMode, ProcessingMode
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class SettingsService:
    """
    Centralized service for managing all system settings with persistence.
    """
    
    def __init__(self):
        self.config = Config()
        self.env_file = Path(".env")
        self.config_backup_dir = Path("config/backups")
        self.config_backup_dir.mkdir(parents=True, exist_ok=True)
        
    async def load_settings(self) -> Dict[str, Any]:
        """Load current settings from all sources"""
        try:
            # Get current config values
            settings = {
                "detection": {
                    "confidence_threshold": self.config.confidence_threshold,
                    "model_path": self.config.model_path,
                    "model_device": self.config.model_device,
                    "processing_frequency": self.config.stream_processing_frequency,
                    "detection_timeout": 30,  # Default timeout
                    "max_detections": 10,  # Default max detections
                    "enhancement_enabled": True,  # Default enhancement
                    "save_detections": self.config.enable_storage_output,
                    "min_ocr_confidence": self.config.min_ocr_confidence,
                    "use_known_plates_db": self.config.use_known_plates_db,
                    "match_threshold": self.config.match_threshold,
                    "cooldown_period": self.config.cooldown_period
                },
                "camera": await self._get_unified_camera_config(),
                "storage": {
                    "max_detections": 10000,  # Default
                    "cleanup_days": 30,  # Default
                    "backup_frequency": "daily" if self.config.enable_database_backup else "never",
                    "compress_images": True,  # Default
                    "export_csv": False,  # Default
                    "license_plates_dir": self.config.license_plates_dir,
                    "enhanced_plates_dir": self.config.enhanced_plates_dir,
                    "known_plates_path": self.config.known_plates_path
                },
                "processing": {
                    "deployment_mode": self.config.deployment_mode.value,
                    "enable_web_ui": self.config.enable_web_ui,
                    "enable_background_processing": self.config.enable_background_processing,
                    "web_ui_port": self.config.web_ui_port,
                    "background_processing_mode": self.config.background_processing_mode.value,
                    "background_frame_skip": self.config.background_frame_skip,
                    "background_processing_interval": self.config.background_processing_interval,
                    "background_max_queue_size": self.config.background_max_queue_size,
                    "background_batch_size": self.config.background_batch_size,
                    "enable_background_metrics": self.config.enable_background_metrics
                },
                "output_channels": {
                    "enable_storage_output": self.config.enable_storage_output,
                    "enable_websocket_output": self.config.enable_websocket_output,
                    "enable_api_output": self.config.enable_api_output,
                    "enable_webhook_output": self.config.enable_webhook_output,
                    "webhook_url": self.config.webhook_url,
                    "webhook_timeout": self.config.webhook_timeout
                },
                "advanced": {
                    "gpu_device": 0 if self.config.model_device == "cuda" else None,
                    "worker_threads": self.config.max_concurrent_detections,
                    "rate_limit": 100,  # Default API rate limit
                    "log_level": self.config.log_level,
                    "debug_mode": self.config.log_level == "DEBUG",
                    "max_concurrent_detections": self.config.max_concurrent_detections,
                    "max_frame_buffer_size": self.config.max_frame_buffer_size,
                    "enable_gpu_acceleration": self.config.enable_gpu_acceleration,
                    "enable_performance_logging": self.config.enable_performance_logging,
                    "batch_size": self.config.batch_size,
                    "process_interval": self.config.process_interval
                },
                "security": {
                    "enable_cors": self.config.enable_cors,
                    "cors_origins": self.config.cors_origins,
                    "api_key": self.config.api_key,
                    "require_api_key": self.config.require_api_key
                },
                "database": {
                    "database_url": self.config.database_url,
                    "enable_database_backup": self.config.enable_database_backup,
                    "backup_interval_hours": self.config.backup_interval_hours
                }
            }
            
            return settings
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return await self._get_default_settings()
    
    async def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Save settings with validation and persistence"""
        try:
            # Backup current configuration
            await self._backup_current_config()
            
            # Validate settings structure
            validated_settings = await self._validate_settings(settings)
            
            # Update environment variables
            env_updates = await self._prepare_env_updates(validated_settings)
            
            # Write to .env file
            await self._update_env_file(env_updates)
            
            # Save camera-specific configuration and attempt hot switch
            camera_switched = False
            if "camera" in validated_settings:
                await self._save_camera_config(validated_settings["camera"])
                
                # Attempt hot camera switch if only camera source changed
                if ("source" in validated_settings["camera"] and 
                    len(validated_settings) == 1 and 
                    len(validated_settings["camera"]) == 1):
                    try:
                        camera_switched = await self._attempt_hot_camera_switch(validated_settings["camera"]["source"])
                    except Exception as e:
                        logger.warning(f"Hot camera switch failed, restart will be required: {e}")
            
            # Update runtime config
            self._update_runtime_config(validated_settings)
            
            logger.info("Settings saved successfully")
            
            restart_required = self._check_restart_required(validated_settings) and not camera_switched
            
            return {
                "success": True,
                "message": "Settings saved successfully" + (" - Camera switched without restart" if camera_switched else ""),
                "updated_fields": list(validated_settings.keys()),
                "restart_required": restart_required,
                "camera_switched": camera_switched,
                "timestamp": datetime.now().isoformat()
            }
            
        except ValidationError as e:
            logger.error(f"Settings validation error: {e}")
            return {
                "success": False,
                "error": "validation_error",
                "message": "Invalid settings provided",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return {
                "success": False,
                "error": "save_error", 
                "message": f"Failed to save settings: {str(e)}"
            }
    
    async def reset_to_defaults(self) -> Dict[str, Any]:
        """Reset all settings to default values"""
        try:
            await self._backup_current_config()
            
            # Get default settings
            default_settings = await self._get_default_settings()
            
            # Save defaults
            result = await self.save_settings(default_settings)
            
            if result["success"]:
                result["message"] = "Settings reset to defaults successfully"
                logger.info("Settings reset to defaults")
            
            return result
            
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return {
                "success": False,
                "error": "reset_error",
                "message": f"Failed to reset settings: {str(e)}"
            }
    
    async def export_settings(self) -> Dict[str, Any]:
        """Export current settings to JSON format"""
        try:
            settings = await self.load_settings()
            
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "exported_by": "LPR System Settings Service"
                },
                "settings": settings
            }
            
            return {
                "success": True,
                "data": export_data,
                "filename": f"lpr_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
            
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return {
                "success": False,
                "error": "export_error",
                "message": f"Failed to export settings: {str(e)}"
            }
    
    async def import_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import settings from JSON data"""
        try:
            # Validate import data structure
            if "settings" not in settings_data:
                raise ValueError("Invalid import data: missing 'settings' key")
            
            # Extract settings
            settings = settings_data["settings"]
            
            # Save imported settings
            result = await self.save_settings(settings)
            
            if result["success"]:
                result["message"] = "Settings imported successfully"
                logger.info("Settings imported from external data")
            
            return result
            
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return {
                "success": False,
                "error": "import_error",
                "message": f"Failed to import settings: {str(e)}"
            }
    
    async def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate settings against expected schema"""
        validated = {}
        
        # Validate detection settings
        if "detection" in settings:
            detection = settings["detection"]
            validated["detection"] = {
                "confidence_threshold": self._validate_float(detection.get("confidence_threshold"), 0.1, 1.0, 0.5),
                "model_path": self._validate_model_path(detection.get("model_path", "app/models/yolo11m_best.pt")),
                "model_device": self._validate_choice(detection.get("model_device"), ["auto", "cpu", "cuda"], "auto"),
                "processing_frequency": self._validate_int(detection.get("processing_frequency"), 1, 10, 3),
                "detection_timeout": self._validate_int(detection.get("detection_timeout"), 5, 60, 30),
                "max_detections": self._validate_int(detection.get("max_detections"), 1, 100, 10),
                "enhancement_enabled": bool(detection.get("enhancement_enabled", True)),
                "save_detections": bool(detection.get("save_detections", True)),
                "min_ocr_confidence": self._validate_float(detection.get("min_ocr_confidence"), 0.1, 1.0, 0.3),
                "use_known_plates_db": bool(detection.get("use_known_plates_db", True)),
                "match_threshold": self._validate_float(detection.get("match_threshold"), 0.1, 1.0, 0.8),
                "cooldown_period": self._validate_float(detection.get("cooldown_period"), 1.0, 60.0, 5.0)
            }
        
        # Validate camera settings
        if "camera" in settings:
            camera = settings["camera"]
            validated["camera"] = {
                "source": str(camera.get("source", "0")),
                "width": self._validate_int(camera.get("width"), 320, 3840, 1280),
                "height": self._validate_int(camera.get("height"), 240, 2160, 720),
                "fps": self._validate_int(camera.get("fps"), 5, 60, 30),
                "buffer_size": self._validate_int(camera.get("buffer_size"), 1, 10, 1),
                "ip_url": camera.get("ip_url")  # Can be None
            }
        
        # Validate storage settings
        if "storage" in settings:
            storage = settings["storage"]
            validated["storage"] = {
                "max_detections": self._validate_int(storage.get("max_detections"), 100, 100000, 10000),
                "cleanup_days": self._validate_int(storage.get("cleanup_days"), 1, 365, 30),
                "backup_frequency": self._validate_choice(storage.get("backup_frequency"), ["never", "daily", "weekly", "monthly"], "daily"),
                "compress_images": bool(storage.get("compress_images", True)),
                "export_csv": bool(storage.get("export_csv", False))
            }
        
        # Validate processing settings
        if "processing" in settings:
            processing = settings["processing"]
            validated["processing"] = {
                "deployment_mode": self._validate_choice(processing.get("deployment_mode"), ["web_ui", "headless", "hybrid"], "web_ui"),
                "enable_web_ui": bool(processing.get("enable_web_ui", True)),
                "enable_background_processing": bool(processing.get("enable_background_processing", False)),
                "web_ui_port": self._validate_int(processing.get("web_ui_port"), 8000, 9999, 8001),
                "background_processing_mode": self._validate_choice(processing.get("background_processing_mode"), ["continuous", "interval", "triggered"], "interval"),
                "background_frame_skip": self._validate_int(processing.get("background_frame_skip"), 1, 30, 5),
                "background_processing_interval": self._validate_float(processing.get("background_processing_interval"), 0.1, 10.0, 0.5),
                "background_max_queue_size": self._validate_int(processing.get("background_max_queue_size"), 10, 1000, 100),
                "background_batch_size": self._validate_int(processing.get("background_batch_size"), 1, 100, 10),
                "enable_background_metrics": bool(processing.get("enable_background_metrics", True))
            }
        
        # Validate advanced settings
        if "advanced" in settings:
            advanced = settings["advanced"]
            validated["advanced"] = {
                "gpu_device": self._validate_int(advanced.get("gpu_device"), 0, 8, 0) if advanced.get("gpu_device") is not None else None,
                "worker_threads": self._validate_int(advanced.get("worker_threads"), 1, 16, 4),
                "rate_limit": self._validate_int(advanced.get("rate_limit"), 10, 1000, 100),
                "log_level": self._validate_choice(advanced.get("log_level"), ["DEBUG", "INFO", "WARNING", "ERROR"], "INFO"),
                "debug_mode": bool(advanced.get("debug_mode", False)),
                "max_concurrent_detections": self._validate_int(advanced.get("max_concurrent_detections"), 1, 20, 5),
                "max_frame_buffer_size": self._validate_int(advanced.get("max_frame_buffer_size"), 5, 100, 30),
                "enable_gpu_acceleration": bool(advanced.get("enable_gpu_acceleration", True)),
                "enable_performance_logging": bool(advanced.get("enable_performance_logging", True)),
                "batch_size": self._validate_int(advanced.get("batch_size"), 1, 100, 10),
                "process_interval": self._validate_float(advanced.get("process_interval"), 0.1, 10.0, 0.5)
            }
        
        return validated
    
    def _validate_float(self, value, min_val: float, max_val: float, default: float) -> float:
        """Validate float value within range"""
        try:
            val = float(value)
            return max(min_val, min(max_val, val))
        except (ValueError, TypeError):
            return default
    
    def _validate_int(self, value, min_val: int, max_val: int, default: int) -> int:
        """Validate integer value within range"""
        try:
            val = int(value)
            return max(min_val, min(max_val, val))
        except (ValueError, TypeError):
            return default
    
    def _validate_choice(self, value, choices: list, default: str) -> str:
        """Validate value is in allowed choices"""
        return value if value in choices else default
    
    def _validate_model_path(self, path: str) -> str:
        """Validate model path exists"""
        if path and os.path.exists(path):
            return path
        
        # Try default paths
        default_paths = [
            "app/models/yolo11m_best.pt",
            "app/models/yolov8m.pt",
            "app/models/yolo11n.pt"
        ]
        
        for default_path in default_paths:
            if os.path.exists(default_path):
                return default_path
        
        return "app/models/yolo11m_best.pt"  # Fallback
    
    
    async def _prepare_env_updates(self, settings: Dict[str, Any]) -> Dict[str, str]:
        """Prepare environment variable updates"""
        env_updates = {}
        
        # Detection settings
        if "detection" in settings:
            det = settings["detection"]
            env_updates.update({
                "CONFIDENCE_THRESHOLD": str(det["confidence_threshold"]),
                "MODEL_PATH": det["model_path"],
                "MODEL_DEVICE": det["model_device"],
                "STREAM_PROCESSING_FREQUENCY": str(det["processing_frequency"]),
                "MIN_OCR_CONFIDENCE": str(det["min_ocr_confidence"]),
                "USE_KNOWN_PLATES_DB": str(det["use_known_plates_db"]).lower(),
                "MATCH_THRESHOLD": str(det["match_threshold"]),
                "COOLDOWN_PERIOD": str(det["cooldown_period"])
            })
        
        # Camera settings
        if "camera" in settings:
            cam = settings["camera"]
            env_updates.update({
                "CAMERA_ID": cam["source"],
                "CAMERA_WIDTH": str(cam["width"]),
                "CAMERA_HEIGHT": str(cam["height"]),
                "CAMERA_FPS": str(cam["fps"])
            })
        
        # Processing settings
        if "processing" in settings:
            proc = settings["processing"]
            env_updates.update({
                "DEPLOYMENT_MODE": proc["deployment_mode"],
                "ENABLE_WEB_UI": str(proc["enable_web_ui"]).lower(),
                "ENABLE_BACKGROUND_PROCESSING": str(proc["enable_background_processing"]).lower(),
                "WEB_UI_PORT": str(proc["web_ui_port"]),
                "BACKGROUND_PROCESSING_MODE": proc["background_processing_mode"],
                "BACKGROUND_FRAME_SKIP": str(proc["background_frame_skip"]),
                "BACKGROUND_PROCESSING_INTERVAL": str(proc["background_processing_interval"]),
                "BACKGROUND_MAX_QUEUE_SIZE": str(proc["background_max_queue_size"]),
                "BACKGROUND_BATCH_SIZE": str(proc["background_batch_size"]),
                "ENABLE_BACKGROUND_METRICS": str(proc["enable_background_metrics"]).lower()
            })
        
        # Advanced settings
        if "advanced" in settings:
            adv = settings["advanced"]
            env_updates.update({
                "LOG_LEVEL": adv["log_level"],
                "ENABLE_PERFORMANCE_LOGGING": str(adv["enable_performance_logging"]).lower(),
                "MAX_CONCURRENT_DETECTIONS": str(adv["max_concurrent_detections"]),
                "MAX_FRAME_BUFFER_SIZE": str(adv["max_frame_buffer_size"]),
                "ENABLE_GPU_ACCELERATION": str(adv["enable_gpu_acceleration"]).lower(),
                "BATCH_SIZE": str(adv["batch_size"]),
                "PROCESS_INTERVAL": str(adv["process_interval"])
            })
        
        return env_updates
    
    async def _update_env_file(self, env_updates: Dict[str, str]):
        """Update .env file with new values"""
        try:
            # Read existing .env file
            existing_env = {}
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_env[key.strip()] = value.strip()
            
            # Update with new values
            existing_env.update(env_updates)
            
            # Write back to file
            with open(self.env_file, 'w') as f:
                f.write(f"# LPR System Configuration\n")
                f.write(f"# Last updated: {datetime.now().isoformat()}\n\n")
                
                for key, value in existing_env.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Updated .env file with {len(env_updates)} new values")
            
        except Exception as e:
            logger.error(f"Error updating .env file: {e}")
            raise
    
    async def _save_camera_config(self, camera_settings: Dict[str, Any]):
        """Save camera-specific configuration"""
        try:
            config_file = Path("config/camera_config.json")
            config_file.parent.mkdir(exist_ok=True)
            
            config_data = {
                "camera_source": camera_settings["source"],
                "ip_camera_url": camera_settings.get("ip_url"),
                "resolution": {
                    "width": camera_settings["width"],
                    "height": camera_settings["height"]
                },
                "fps": camera_settings["fps"],
                "buffer_size": camera_settings["buffer_size"],
                "updated_at": datetime.now().isoformat()
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info("Camera configuration saved")
            
        except Exception as e:
            logger.error(f"Error saving camera config: {e}")
            raise
    
    async def _get_unified_camera_config(self) -> Dict[str, Any]:
        """Get unified camera configuration from all sources with proper precedence"""
        # Start with defaults from config
        unified_config = {
            "source": self.config.camera_id,
            "width": self.config.camera_width,
            "height": self.config.camera_height,
            "fps": self.config.camera_fps,
            "buffer_size": 1,  # Default buffer size
            "ip_url": None  # Default no IP camera
        }
        
        # Override with saved camera config if exists
        saved_config = await self._load_camera_config()
        if saved_config:
            unified_config.update(saved_config)
        
        return unified_config
    
    async def _load_camera_config(self) -> Optional[Dict[str, Any]]:
        """Load camera-specific configuration"""
        try:
            config_file = Path("config/camera_config.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                return {
                    "source": data.get("camera_source", "0"),
                    "ip_url": data.get("ip_camera_url"),
                    "width": data.get("resolution", {}).get("width", 1280),
                    "height": data.get("resolution", {}).get("height", 720),
                    "fps": data.get("fps", 30),
                    "buffer_size": data.get("buffer_size", 1)
                }
                
        except Exception as e:
            logger.debug(f"Could not load camera config: {e}")
        
        return None
    
    async def _attempt_hot_camera_switch(self, camera_id: str) -> bool:
        """Attempt to switch camera without restart"""
        try:
            # Import here to avoid circular imports
            from app.services.camera_service import CameraService
            
            # Validate camera is available
            available_cameras = CameraService.detect_available_cameras()
            target_camera = next((cam for cam in available_cameras if cam["id"] == camera_id), None)
            
            if not target_camera or not target_camera["is_working"]:
                logger.warning(f"Camera {camera_id} not available for hot switch")
                return False
            
            # Get app instance to access services
            try:
                from app.main import app
                if hasattr(app.state, 'camera_service'):
                    camera_service = app.state.camera_service
                    
                    logger.info(f"Attempting hot switch to camera {camera_id}")
                    
                    # Reinitialize camera service with new camera ID
                    await camera_service.initialize(
                        camera_id=camera_id,
                        width=self.config.camera_width,
                        height=self.config.camera_height
                    )
                    
                    # Update background stream manager if it exists
                    if hasattr(app.state, 'background_stream_manager'):
                        background_manager = app.state.background_stream_manager
                        if hasattr(background_manager, 'set_services'):
                            background_manager.set_services(camera_service=camera_service)
                    
                    # Test the switch worked
                    await asyncio.sleep(1.0)
                    frame, _ = await camera_service.get_frame()
                    
                    if frame is not None and frame.size > 0:
                        logger.info(f"Successfully switched to camera {camera_id}")
                        return True
                    else:
                        logger.warning(f"Hot switch failed - no frames from camera {camera_id}")
                        return False
                else:
                    logger.warning("Camera service not available for hot switch")
                    return False
                    
            except ImportError:
                logger.warning("App not available for hot switch")
                return False
                
        except Exception as e:
            logger.error(f"Hot camera switch failed: {e}")
            return False
    
    async def _backup_current_config(self):
        """Backup current configuration"""
        try:
            current_settings = await self.load_settings()
            
            backup_file = self.config_backup_dir / f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(current_settings, f, indent=2)
            
            # Keep only last 10 backups
            backups = sorted(self.config_backup_dir.glob("config_backup_*.json"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
            
            logger.debug(f"Configuration backed up to {backup_file}")
            
        except Exception as e:
            logger.warning(f"Could not backup configuration: {e}")
    
    def _update_runtime_config(self, settings: Dict[str, Any]):
        """Update runtime configuration object"""
        try:
            # This would update the running config instance
            # In practice, most changes require restart to take effect
            logger.info("Runtime configuration updated (restart may be required)")
            
        except Exception as e:
            logger.error(f"Error updating runtime config: {e}")
    
    def _check_restart_required(self, settings: Dict[str, Any]) -> bool:
        """Check if restart is required for settings to take effect"""
        restart_required_fields = [
            "camera.source",
            "camera.width", 
            "camera.height",
            "camera.fps",
            "processing.deployment_mode",
            "processing.web_ui_port",
            "detection.model_path",
            "detection.model_device"
        ]
        
        # Check if any restart-required fields were updated
        for field in restart_required_fields:
            section, key = field.split(".")
            if section in settings and key in settings[section]:
                return True
        
        return False
    
    async def _get_default_settings(self) -> Dict[str, Any]:
        """Get default system settings"""
        return {
            "detection": {
                "confidence_threshold": 0.5,
                "model_path": "app/models/yolo11m_best.pt",
                "model_device": "auto",
                "processing_frequency": 5,
                "detection_timeout": 30,
                "max_detections": 10,
                "enhancement_enabled": True,
                "save_detections": True,
                "min_ocr_confidence": 0.3,
                "use_known_plates_db": True,
                "match_threshold": 0.8,
                "cooldown_period": 5.0
            },
            "camera": {
                "source": "0",
                "width": 1280,
                "height": 720,
                "fps": 30,
                "buffer_size": 1,
                "ip_url": None
            },
            "storage": {
                "max_detections": 10000,
                "cleanup_days": 30,
                "backup_frequency": "daily",
                "compress_images": True,
                "export_csv": False
            },
            "processing": {
                "deployment_mode": "web_ui",
                "enable_web_ui": True,
                "enable_background_processing": False,
                "web_ui_port": 8001,
                "background_processing_mode": "interval",
                "background_frame_skip": 5,
                "background_processing_interval": 0.5,
                "background_max_queue_size": 100,
                "background_batch_size": 10,
                "enable_background_metrics": True
            },
            "advanced": {
                "gpu_device": 0,
                "worker_threads": 4,
                "rate_limit": 100,
                "log_level": "INFO",
                "debug_mode": False,
                "max_concurrent_detections": 5,
                "max_frame_buffer_size": 30,
                "enable_gpu_acceleration": True,
                "enable_performance_logging": True,
                "batch_size": 10,
                "process_interval": 0.5
            }
        }