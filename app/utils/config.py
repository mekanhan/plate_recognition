from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    # Camera settings
    camera_id: int = 0
    camera_width: int = 1280
    camera_height: int = 720
    
    # Model settings
    model_path: str = "models/yolo11m_best.pt"
    
    # Directory settings
    license_plates_dir: str = "data/license_plates"
    enhanced_plates_dir: str = "data/enhanced_plates"
    known_plates_path: str = "data/known_plates.json"
    
    # Processing settings
    detection_interval: float = 1.0  # Seconds between detection runs
    enhancement_interval: float = 1.0  # Seconds between enhancement runs
    save_interval: float = 10.0  # Seconds between saving to file
    
    # Confidence thresholds
    min_detection_confidence: float = 0.5
    min_ocr_confidence: float = 0.3
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    """Return cached settings"""
    return Settings()