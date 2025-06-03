from pydantic_settings import BaseSettings

class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    # Validation settings
    min_ocr_confidence: float = 0.3
    match_threshold: float = 0.8
    use_known_plates_db: bool = True

    # Paths
    known_plates_file: str = "data/known_plates.json"
    results_output_dir: str = "data/license_plates"

    # Processing settings
    batch_size: int = 10
    process_interval: float = 0.5

    class Config:
        env_file = ".env"
