"""
Application settings
"""
import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///data/license_plates.db"
    
    # Camera defaults
    default_camera_username: str = "admin"
    default_camera_password: str = "password"
    default_stream_path: str = "/stream"
    default_rtsp_port: int = 554
    
    # AI Models
    vehicle_model_path: str = "yolov8m.pt"
    plate_model_path: str = "yolo11m_best.pt"
    ocr_languages: List[str] = ["en"]
    ai_device: str = "auto"  # auto, cpu, cuda
    
    # Processing
    processing_fps: float = 10.0
    frame_buffer_size: int = 30
    detection_confidence_threshold: float = 0.5
    min_plate_text_length: int = 4
    save_detection_frames: bool = False
    
    # Storage
    detection_storage_path: str = "detections"
    recording_storage_path: str = "recordings"
    max_storage_gb: int = 100
    cleanup_older_than_days: int = 30
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Monitoring
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_prefix = "LPR_"

# Global settings instance
settings = Settings()