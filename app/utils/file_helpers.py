import os
import json
import time
import logging
import traceback
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        True if directory exists or was created, False on error
    """
    try:
        if not os.path.exists(directory_path):
            logger.info(f"Creating directory: {directory_path}")
            os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {e}")
        logger.error(traceback.format_exc())
        return False

def is_directory_writable(directory_path: str) -> bool:
    """
    Check if a directory is writable
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        True if directory is writable, False otherwise
    """
    try:
        test_file = os.path.join(directory_path, f"test_write_{time.time()}.txt")
        with open(test_file, 'w') as f:
            f.write("Test write")
        os.remove(test_file)
        return True
    except Exception as e:
        logger.error(f"Directory is not writable: {directory_path}")
        logger.error(f"Error: {e}")
        return False

def save_json_file(file_path: str, data: Dict[str, Any], create_backup: bool = True) -> bool:
    """
    Save data to a JSON file with safe atomic writing
    
    Args:
        file_path: Path to the file
        data: Data to save
        create_backup: Whether to create a backup before writing
        
    Returns:
        True if successful, False otherwise
    """
    directory = os.path.dirname(file_path)
    
    # Ensure directory exists
    if not ensure_directory_exists(directory):
        logger.error(f"Could not ensure directory exists: {directory}")
        return False
    
    # Create backup if requested and file exists
    if create_backup and os.path.exists(file_path):
        try:
            backup_path = f"{file_path}.bak"
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            logger.debug(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
    
    try:
        # Create temp file for atomic write
        temp_file = f"{file_path}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Rename temp file to final file (atomic operation)
        os.replace(temp_file, file_path)
        logger.debug(f"Successfully wrote file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving file {file_path}: {e}")
        logger.error(traceback.format_exc())
        
        # Try alternate location if main save failed
        try:
            recovery_file = f"recovery_{os.path.basename(file_path)}_{time.time()}.json"
            with open(recovery_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved recovery file: {recovery_file}")
        except Exception as recovery_error:
            logger.error(f"Failed to save recovery file: {recovery_error}")
            
        return False

def load_json_file(file_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load data from a JSON file with error handling
    
    Args:
        file_path: Path to the file
        default: Default value to return if file doesn't exist or can't be read
        
    Returns:
        Loaded data or default value
    """
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return default if default is not None else {}
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        logger.error(traceback.format_exc())
        
        # Try to load backup if available
        backup_path = f"{file_path}.bak"
        if os.path.exists(backup_path):
            try:
                logger.info(f"Attempting to load backup: {backup_path}")
                with open(backup_path, 'r') as f:
                    return json.load(f)
            except Exception as backup_error:
                logger.error(f"Error loading backup: {backup_error}")
        
        return default if default is not None else {}