"""
Shared configuration for API services
"""
import logging
import sys
from pathlib import Path

def setup_logging(service_name: str = "api") -> logging.Logger:
    """Setup standardized logging configuration"""
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/{service_name}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(service_name)
    logger.info(f"{service_name.capitalize()} service logging initialized")
    
    return logger