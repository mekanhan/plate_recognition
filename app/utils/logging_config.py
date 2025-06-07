import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO):
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - main log
    file_handler = RotatingFileHandler(
        "logs/app.log", 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Separate storage log file for debugging storage issues
    storage_handler = RotatingFileHandler(
        "logs/storage.log", 
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    storage_handler.setFormatter(formatter)
    
    # Configure specific loggers
    storage_logger = logging.getLogger("app.services.storage_service")
    storage_logger.addHandler(storage_handler)
    storage_logger.setLevel(logging.DEBUG)
    
    # Configure utility loggers
    utils_logger = logging.getLogger("app.utils")
    utils_logger.setLevel(logging.DEBUG)
    
    # Silence noisy libraries
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    # Log startup message
    root_logger.info("Logging configured")
    root_logger.info(f"Log level: {logging.getLevelName(log_level)}")
    root_logger.info(f"Log files: logs/app.log, logs/storage.log")