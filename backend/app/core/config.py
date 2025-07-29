"""
Application configuration using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_BASE_PATH: str = "/api/v1"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:8080",  # Frontend development server
        "http://localhost:3000",  # Alternative frontend port
        "http://localhost:8000",  # Backend API (for Swagger UI)
    ]
    
    # Recording Service Configuration
    RECORDING_API_HOST: str = "0.0.0.0"
    RECORDING_API_PORT: int = 8002
    
    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/license_plates.db"
    
    # Storage Configuration
    RECORDING_BASE_PATH: str = "./recordings"
    RETENTION_DAYS: int = 30
    SEGMENT_DURATION_SECONDS: int = 600  # 10 minutes
    
    # Camera Health Check
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    HEALTH_CHECK_TIMEOUT: int = 10   # seconds
    
    # Streaming Configuration
    STREAM_QUALITY_DEFAULT: str = "medium"
    STREAM_MAX_FPS_DEFAULT: int = 30
    STREAM_BUFFER_SIZE: int = 10
    
    # Frame Distribution Configuration
    FRAME_DIST_RECORDING_QUEUE_SIZE: int = 30       # 1 second at 30fps
    FRAME_DIST_DETECTION_QUEUE_SIZE: int = 10       # Smaller for processing
    FRAME_DIST_LATEST_FRAME_TIMEOUT: float = 5.0   # Max age in seconds
    FRAME_DIST_RECONNECT_DELAY: float = 2.0         # Delay between reconnects
    FRAME_DIST_MAX_RECONNECT_ATTEMPTS: int = 5      # Max reconnection attempts
    FRAME_DIST_FRAME_COPY_TIMEOUT: float = 0.1      # Queue operation timeout
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()