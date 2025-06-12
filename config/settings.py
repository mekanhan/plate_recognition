from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional

class DeploymentMode(str, Enum):
    """Deployment modes for the application"""
    WEB_UI = "web_ui"           # Full web interface with UI
    HEADLESS = "headless"       # Background processing only
    HYBRID = "hybrid"           # Both web UI and background processing

class ProcessingMode(str, Enum):
    """Processing modes for background stream manager"""
    CONTINUOUS = "continuous"   # Process every frame
    INTERVAL = "interval"       # Process at fixed intervals
    TRIGGERED = "triggered"     # Process only when triggered

class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Deployment Configuration
    deployment_mode: DeploymentMode = DeploymentMode.WEB_UI
    enable_web_ui: bool = True
    enable_background_processing: bool = False
    web_ui_port: int = 8001
    api_only_port: Optional[int] = None  # Separate port for API-only mode
    
    # Background Processing Configuration
    background_processing_mode: ProcessingMode = ProcessingMode.INTERVAL
    background_frame_skip: int = 5
    background_processing_interval: float = 0.5
    background_max_queue_size: int = 100
    background_batch_size: int = 10
    background_health_check_interval: float = 30.0
    enable_background_metrics: bool = True
    
    # Output Channels Configuration
    enable_storage_output: bool = True
    enable_websocket_output: bool = True
    enable_api_output: bool = True
    enable_webhook_output: bool = False
    webhook_url: Optional[str] = None
    webhook_timeout: float = 5.0
    
    # Validation settings
    min_ocr_confidence: float = 0.3
    match_threshold: float = 0.8
    use_known_plates_db: bool = True
    confidence_threshold: float = 0.5
    cooldown_period: float = 5.0

    # Paths
    known_plates_path: str = "data/known_plates.json"
    license_plates_dir: str = "data/license_plates"
    enhanced_plates_dir: str = "data/enhanced_plates"
    
    # Camera Configuration
    camera_id: str = "0"
    camera_width: int = 1280
    camera_height: int = 720
    camera_fps: int = 30
    
    # Model Configuration
    model_path: str = "app/models/yolo11m_best.pt"
    model_confidence: float = 0.5
    model_device: str = "auto"  # auto, cpu, cuda
    
    # Processing settings
    batch_size: int = 10
    process_interval: float = 0.5
    
    # Logging Configuration
    log_level: str = "INFO"
    enable_performance_logging: bool = True
    log_file: Optional[str] = "logs/app.log"
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///data/license_plates.db"
    enable_database_backup: bool = True
    backup_interval_hours: int = 24
    
    # Security Configuration
    enable_cors: bool = True
    cors_origins: list = ["*"]
    api_key: Optional[str] = None
    require_api_key: bool = False
    
    # Performance Configuration
    max_concurrent_detections: int = 5
    max_frame_buffer_size: int = 30
    enable_gpu_acceleration: bool = True
    
    @property
    def is_headless_mode(self) -> bool:
        """Check if running in headless mode"""
        return self.deployment_mode == DeploymentMode.HEADLESS
    
    @property
    def is_web_ui_enabled(self) -> bool:
        """Check if web UI should be enabled"""
        return self.deployment_mode in [DeploymentMode.WEB_UI, DeploymentMode.HYBRID]
    
    @property
    def is_background_processing_enabled(self) -> bool:
        """Check if background processing should be enabled"""
        return (self.deployment_mode in [DeploymentMode.HEADLESS, DeploymentMode.HYBRID] or 
                self.enable_background_processing)

    class Config:
        env_file = ".env"
        case_sensitive = False
