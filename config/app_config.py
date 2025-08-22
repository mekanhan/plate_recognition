"""
Centralized Application Configuration for LPR System
Handles environment-based settings, database paths, and service configuration
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str = "data/license_plates.db"
    backup_dir: str = "data/backups"
    pool_size: int = 5
    pool_timeout: int = 30
    connection_timeout: int = 10
    enable_foreign_keys: bool = True
    
    @property
    def absolute_path(self) -> str:
        """Get absolute database path"""
        return str(Path(self.path).resolve())
    
    @property
    def backup_path(self) -> str:
        """Get absolute backup directory path"""
        return str(Path(self.backup_dir).resolve())


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    log_dir: str = "logs"
    max_file_size_mb: int = 10
    max_files_per_service: int = 5
    retention_days: int = 7
    disk_usage_threshold: float = 0.85
    log_level: str = "INFO"
    
    @property
    def log_level_int(self) -> int:
        """Convert log level string to integer"""
        import logging
        return getattr(logging, self.log_level.upper(), logging.INFO)


@dataclass
class StorageConfig:
    """Storage and media file configuration"""
    recordings_dir: str = "recordings"
    detections_dir: str = "detections"
    models_dir: str = "ai_pipeline/models"
    temp_dir: str = "temp"
    
    # Retention policies
    recording_retention_days: int = 30
    detection_retention_days: int = 14
    temp_file_retention_hours: int = 24
    
    # Size limits (in GB) - Updated for real-world usage
    max_total_storage_gb: float = 500.0  # 500GB total limit
    max_recording_storage_gb: float = 400.0  # 400GB for recordings
    max_detection_storage_gb: float = 50.0  # 50GB for detections
    
    # Media retention settings
    min_recording_age_hours: int = 24  # Keep recordings for at least 24 hours
    min_detection_age_hours: int = 6   # Keep detections for at least 6 hours
    
    # Cleanup thresholds
    storage_cleanup_threshold: float = 0.90  # 90%
    emergency_cleanup_threshold: float = 0.95  # 95%


@dataclass
class ServiceConfig:
    """Service configuration settings"""
    main_api_port: int = 8001
    recording_api_port: int = 8002
    frontend_port: int = 8080
    
    # Service timeouts
    startup_timeout: int = 30
    health_check_timeout: int = 5
    shutdown_timeout: int = 10
    
    # Health monitoring
    health_check_interval: int = 30
    health_check_retries: int = 3
    
    # URLs
    @property
    def main_api_url(self) -> str:
        return f"http://localhost:{self.main_api_port}"
    
    @property
    def recording_api_url(self) -> str:
        return f"http://localhost:{self.recording_api_port}"
    
    @property
    def frontend_url(self) -> str:
        return f"http://localhost:{self.frontend_port}"


@dataclass 
class SecurityConfig:
    """Security configuration settings"""
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API security
    enable_cors: bool = True
    allowed_origins: list = field(default_factory=lambda: ["*"])
    api_rate_limit: str = "100/minute"
    
    # Data encryption
    encrypt_credentials: bool = True
    encryption_key_file: str = "config/.encryption_key"


@dataclass
class AIConfig:
    """AI and ML configuration"""
    yolo_model_path: str = "ai_pipeline/models/yolo11m_best.pt"
    ocr_languages: list = field(default_factory=lambda: ["en"])
    
    # Processing settings
    detection_confidence_threshold: float = 0.5
    ocr_confidence_threshold: float = 0.7
    max_detection_age_seconds: int = 300
    
    # Performance
    enable_gpu: bool = True
    max_workers: int = 2
    batch_size: int = 1


class LPRConfig:
    """
    Main configuration class that loads all settings from environment variables
    and provides centralized access to configuration
    """
    
    def __init__(self, env_file: Optional[str] = None):
        # Load environment variables from .env file if provided
        if env_file and Path(env_file).exists():
            self._load_env_file(env_file)
        
        # Initialize all configuration sections
        self.database = self._init_database_config()
        self.logging = self._init_logging_config()
        self.storage = self._init_storage_config()
        self.services = self._init_service_config()
        self.security = self._init_security_config()
        self.ai = self._init_ai_config()
        
        # Create necessary directories
        self._ensure_directories()
    
    def _load_env_file(self, env_file: str):
        """Load environment variables from .env file"""
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            # Manual parsing if python-dotenv not available
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    def _init_database_config(self) -> DatabaseConfig:
        return DatabaseConfig(
            path=os.getenv('LPR_DB_PATH', 'data/license_plates.db'),
            backup_dir=os.getenv('LPR_DB_BACKUP_DIR', 'data/backups'),
            pool_size=int(os.getenv('LPR_DB_POOL_SIZE', '5')),
            pool_timeout=int(os.getenv('LPR_DB_POOL_TIMEOUT', '30')),
            connection_timeout=int(os.getenv('LPR_DB_CONNECTION_TIMEOUT', '10')),
            enable_foreign_keys=os.getenv('LPR_DB_FOREIGN_KEYS', 'true').lower() == 'true'
        )
    
    def _init_logging_config(self) -> LoggingConfig:
        return LoggingConfig(
            log_dir=os.getenv('LPR_LOG_DIR', 'logs'),
            max_file_size_mb=int(os.getenv('LPR_LOG_MAX_SIZE_MB', '10')),
            max_files_per_service=int(os.getenv('LPR_LOG_MAX_FILES', '5')),
            retention_days=int(os.getenv('LPR_LOG_RETENTION_DAYS', '7')),
            disk_usage_threshold=float(os.getenv('LPR_LOG_DISK_THRESHOLD', '0.85')),
            log_level=os.getenv('LPR_LOG_LEVEL', 'INFO')
        )
    
    def _init_storage_config(self) -> StorageConfig:
        return StorageConfig(
            recordings_dir=os.getenv('LPR_RECORDINGS_DIR', 'recordings'),
            detections_dir=os.getenv('LPR_DETECTIONS_DIR', 'detections'),
            models_dir=os.getenv('LPR_MODELS_DIR', 'ai_pipeline/models'),
            temp_dir=os.getenv('LPR_TEMP_DIR', 'temp'),
            recording_retention_days=int(os.getenv('LPR_RECORDING_RETENTION_DAYS', '30')),
            detection_retention_days=int(os.getenv('LPR_DETECTION_RETENTION_DAYS', '14')),
            temp_file_retention_hours=int(os.getenv('LPR_TEMP_RETENTION_HOURS', '24')),
            max_total_storage_gb=float(os.getenv('LPR_MAX_STORAGE_GB', '500.0')),
            max_recording_storage_gb=float(os.getenv('LPR_MAX_RECORDING_GB', '400.0')),
            max_detection_storage_gb=float(os.getenv('LPR_MAX_DETECTION_GB', '50.0')),
            min_recording_age_hours=int(os.getenv('LPR_MIN_RECORDING_AGE_HOURS', '24')),
            min_detection_age_hours=int(os.getenv('LPR_MIN_DETECTION_AGE_HOURS', '6')),
            storage_cleanup_threshold=float(os.getenv('LPR_STORAGE_CLEANUP_THRESHOLD', '0.90')),
            emergency_cleanup_threshold=float(os.getenv('LPR_EMERGENCY_CLEANUP_THRESHOLD', '0.95'))
        )
    
    def _init_service_config(self) -> ServiceConfig:
        return ServiceConfig(
            main_api_port=int(os.getenv('LPR_MAIN_API_PORT', '8001')),
            recording_api_port=int(os.getenv('LPR_RECORDING_API_PORT', '8002')),
            frontend_port=int(os.getenv('LPR_FRONTEND_PORT', '8080')),
            startup_timeout=int(os.getenv('LPR_STARTUP_TIMEOUT', '30')),
            health_check_timeout=int(os.getenv('LPR_HEALTH_TIMEOUT', '5')),
            shutdown_timeout=int(os.getenv('LPR_SHUTDOWN_TIMEOUT', '10')),
            health_check_interval=int(os.getenv('LPR_HEALTH_INTERVAL', '30')),
            health_check_retries=int(os.getenv('LPR_HEALTH_RETRIES', '3'))
        )
    
    def _init_security_config(self) -> SecurityConfig:
        return SecurityConfig(
            jwt_secret_key=os.getenv('LPR_JWT_SECRET_KEY'),
            jwt_algorithm=os.getenv('LPR_JWT_ALGORITHM', 'HS256'),
            jwt_expiration_hours=int(os.getenv('LPR_JWT_EXPIRATION_HOURS', '24')),
            enable_cors=os.getenv('LPR_ENABLE_CORS', 'true').lower() == 'true',
            allowed_origins=os.getenv('LPR_ALLOWED_ORIGINS', '*').split(','),
            api_rate_limit=os.getenv('LPR_API_RATE_LIMIT', '100/minute'),
            encrypt_credentials=os.getenv('LPR_ENCRYPT_CREDENTIALS', 'true').lower() == 'true',
            encryption_key_file=os.getenv('LPR_ENCRYPTION_KEY_FILE', 'config/.encryption_key')
        )
    
    def _init_ai_config(self) -> AIConfig:
        return AIConfig(
            yolo_model_path=os.getenv('LPR_YOLO_MODEL_PATH', 'ai_pipeline/train/models/pretrained/yolo11m_best.pt'),
            ocr_languages=os.getenv('LPR_OCR_LANGUAGES', 'en').split(','),
            detection_confidence_threshold=float(os.getenv('LPR_DETECTION_CONFIDENCE', '0.5')),
            ocr_confidence_threshold=float(os.getenv('LPR_OCR_CONFIDENCE', '0.7')),
            max_detection_age_seconds=int(os.getenv('LPR_MAX_DETECTION_AGE', '300')),
            enable_gpu=os.getenv('LPR_ENABLE_GPU', 'true').lower() == 'true',
            max_workers=int(os.getenv('LPR_MAX_WORKERS', '2')),
            batch_size=int(os.getenv('LPR_BATCH_SIZE', '1'))
        )
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        dirs_to_create = [
            self.database.backup_dir,
            self.logging.log_dir,
            self.storage.recordings_dir,
            self.storage.detections_dir,
            self.storage.models_dir,
            self.storage.temp_dir,
            Path(self.database.path).parent,
            Path(self.security.encryption_key_file).parent
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get_database_url(self) -> str:
        """Get SQLite database URL for SQLAlchemy"""
        return f"sqlite+aiosqlite:///{self.database.absolute_path}"
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Check database path
        db_parent = Path(self.database.path).parent
        if not db_parent.exists():
            issues.append(f"Database directory does not exist: {db_parent}")
        
        # Check model file
        if not Path(self.ai.yolo_model_path).exists():
            issues.append(f"YOLO model file not found: {self.ai.yolo_model_path}")
        
        # Check port conflicts
        ports = [self.services.main_api_port, self.services.recording_api_port, self.services.frontend_port]
        if len(ports) != len(set(ports)):
            issues.append("Port conflicts detected in service configuration")
        
        # Check storage limits
        if self.storage.max_recording_storage_gb + self.storage.max_detection_storage_gb > self.storage.max_total_storage_gb:
            issues.append("Storage limits are inconsistent (recording + detection > total)")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            'database': self.database.__dict__,
            'logging': self.logging.__dict__,
            'storage': self.storage.__dict__,
            'services': self.services.__dict__,
            'security': {k: v for k, v in self.security.__dict__.items() if 'secret' not in k.lower()},
            'ai': self.ai.__dict__
        }


# Global configuration instance
config: Optional[LPRConfig] = None


def load_config(env_file: Optional[str] = None) -> LPRConfig:
    """Load or reload the global configuration"""
    global config
    config = LPRConfig(env_file)
    return config


def get_config() -> LPRConfig:
    """Get the global configuration instance"""
    global config
    if config is None:
        config = load_config()
    return config


if __name__ == "__main__":
    # CLI for configuration testing
    import json
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        cfg = load_config()
        validation = cfg.validate_config()
        
        print("Configuration Validation Results:")
        print(f"Valid: {validation['valid']}")
        
        if validation['issues']:
            print("\nIssues:")
            for issue in validation['issues']:
                print(f"  ❌ {issue}")
        
        if validation['warnings']:
            print("\nWarnings:")
            for warning in validation['warnings']:
                print(f"  ⚠️  {warning}")
        
        if validation['valid']:
            print("\n✅ Configuration is valid")
        else:
            print(f"\n❌ Configuration has {len(validation['issues'])} issues")
            sys.exit(1)
    
    else:
        cfg = load_config()
        print("LPR System Configuration:")
        print(json.dumps(cfg.to_dict(), indent=2))