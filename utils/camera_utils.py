"""
Camera Utility Functions
Provides consistent camera ID generation and management across the system
"""
import uuid
import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CameraIDGenerator:
    """Handles consistent camera ID generation and validation"""
    
    # Camera ID format: camera_{12-char-hex}
    CAMERA_ID_PREFIX = "camera_"
    HEX_LENGTH = 12  # Increased from 8 for better uniqueness
    CAMERA_ID_PATTERN = re.compile(r'^camera_[0-9a-f]{12}$')
    
    @classmethod
    def generate_camera_id(cls) -> str:
        """
        Generate a unique camera ID with improved uniqueness
        Format: camera_{12-char-hex}
        Example: camera_a1b2c3d4e5f6
        """
        hex_part = uuid.uuid4().hex[:cls.HEX_LENGTH]
        camera_id = f"{cls.CAMERA_ID_PREFIX}{hex_part}"
        
        logger.debug(f"Generated camera ID: {camera_id}")
        return camera_id
    
    @classmethod
    def is_valid_camera_id(cls, camera_id: str) -> bool:
        """
        Validate camera ID format
        
        Args:
            camera_id: The camera ID to validate
            
        Returns:
            bool: True if valid format, False otherwise
        """
        if not isinstance(camera_id, str):
            return False
        
        return bool(cls.CAMERA_ID_PATTERN.match(camera_id))
    
    @classmethod
    def normalize_camera_id(cls, camera_id: str) -> Optional[str]:
        """
        Normalize camera ID to standard format
        Handles legacy formats and ensures consistency
        
        Args:
            camera_id: The camera ID to normalize
            
        Returns:
            str: Normalized camera ID or None if invalid
        """
        if not isinstance(camera_id, str):
            return None
        
        # Already in correct format
        if cls.is_valid_camera_id(camera_id):
            return camera_id
        
        # Handle legacy shorter hex format (camera_12345678)
        legacy_pattern = re.compile(r'^camera_[0-9a-f]{8}$')
        if legacy_pattern.match(camera_id):
            # Extend to 12 characters by padding with random hex
            hex_part = camera_id[7:]  # Remove "camera_" prefix
            additional_hex = uuid.uuid4().hex[:4]  # Add 4 more characters
            return f"{cls.CAMERA_ID_PREFIX}{hex_part}{additional_hex}"
        
        # Handle numeric IDs (convert to proper format)
        if camera_id.isdigit():
            logger.warning(f"Converting numeric camera ID {camera_id} to standard format")
            return cls.generate_camera_id()
        
        # Handle name-based IDs (convert to proper format)
        if camera_id and not camera_id.startswith(cls.CAMERA_ID_PREFIX):
            logger.warning(f"Converting non-standard camera ID {camera_id} to standard format")
            return cls.generate_camera_id()
        
        logger.error(f"Cannot normalize invalid camera ID: {camera_id}")
        return None
    
    @classmethod
    def extract_hex_part(cls, camera_id: str) -> Optional[str]:
        """
        Extract the hex part from a camera ID
        
        Args:
            camera_id: The camera ID
            
        Returns:
            str: Hex part or None if invalid
        """
        if cls.is_valid_camera_id(camera_id):
            return camera_id[len(cls.CAMERA_ID_PREFIX):]
        return None

class CameraDisplayUtils:
    """Utilities for displaying camera information in user-friendly formats"""
    
    @staticmethod
    def generate_display_name(camera_name: str, camera_id: str, index: Optional[int] = None) -> str:
        """
        Generate a user-friendly display name for a camera
        
        Args:
            camera_name: The camera's configured name
            camera_id: The technical camera ID
            index: Optional numeric index for display
            
        Returns:
            str: User-friendly display name
        """
        if camera_name and camera_name.strip():
            return camera_name.strip()
        
        if index is not None:
            return f"Camera {index}"
        
        # Use last 6 characters of hex for compact display
        hex_part = CameraIDGenerator.extract_hex_part(camera_id)
        if hex_part:
            return f"Camera {hex_part[-6:].upper()}"
        
        return f"Camera {camera_id[-8:].upper()}"
    
    @staticmethod
    def generate_short_id(camera_id: str) -> str:
        """
        Generate a short ID for display in compact spaces
        
        Args:
            camera_id: The full camera ID
            
        Returns:
            str: Short display ID
        """
        hex_part = CameraIDGenerator.extract_hex_part(camera_id)
        if hex_part:
            return hex_part[-6:].upper()
        
        return camera_id[-6:].upper()
    
    @staticmethod
    def create_camera_summary(camera_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Create a summary with both technical and display information
        
        Args:
            camera_data: Dictionary containing camera information
            
        Returns:
            dict: Summary with display fields
        """
        camera_id = camera_data.get('camera_id', '')
        camera_name = camera_data.get('name', '')
        
        return {
            'technical_id': camera_id,
            'display_name': CameraDisplayUtils.generate_display_name(camera_name, camera_id),
            'short_id': CameraDisplayUtils.generate_short_id(camera_id),
            'name': camera_name,
            'location': camera_data.get('location', ''),
            'ip_address': camera_data.get('ip_address', ''),
            'status': camera_data.get('status', 'unknown')
        }

class CameraValidation:
    """Camera configuration validation utilities"""
    
    @staticmethod
    def validate_camera_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize camera configuration
        
        Args:
            config: Camera configuration dictionary
            
        Returns:
            dict: Validation result with errors and normalized config
        """
        errors = []
        normalized_config = config.copy()
        
        # Validate camera_id
        camera_id = config.get('camera_id')
        if camera_id:
            if not CameraIDGenerator.is_valid_camera_id(camera_id):
                normalized_id = CameraIDGenerator.normalize_camera_id(camera_id)
                if normalized_id:
                    normalized_config['camera_id'] = normalized_id
                    logger.info(f"Normalized camera ID from {camera_id} to {normalized_id}")
                else:
                    errors.append(f"Invalid camera ID format: {camera_id}")
        else:
            # Generate new ID if missing
            normalized_config['camera_id'] = CameraIDGenerator.generate_camera_id()
            logger.info(f"Generated new camera ID: {normalized_config['camera_id']}")
        
        # Validate required fields
        required_fields = ['name', 'ip_address']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate IP address format (basic check)
        ip_address = config.get('ip_address')
        if ip_address:
            ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
            if not ip_pattern.match(ip_address):
                errors.append(f"Invalid IP address format: {ip_address}")
        
        # Validate port
        port = config.get('port')
        if port is not None:
            try:
                port_int = int(port)
                if not (1 <= port_int <= 65535):
                    errors.append(f"Port must be between 1 and 65535: {port}")
                normalized_config['port'] = port_int
            except (ValueError, TypeError):
                errors.append(f"Invalid port format: {port}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'normalized_config': normalized_config
        }

# Convenience functions for backward compatibility and ease of use
def generate_camera_id() -> str:
    """Generate a new camera ID (convenience function)"""
    return CameraIDGenerator.generate_camera_id()

def validate_camera_id(camera_id: str) -> bool:
    """Validate camera ID format (convenience function)"""
    return CameraIDGenerator.is_valid_camera_id(camera_id)

def normalize_camera_id(camera_id: str) -> Optional[str]:
    """Normalize camera ID (convenience function)"""
    return CameraIDGenerator.normalize_camera_id(camera_id)

def create_display_name(camera_name: str, camera_id: str) -> str:
    """Create display name (convenience function)"""
    return CameraDisplayUtils.generate_display_name(camera_name, camera_id)

# Example usage and testing
if __name__ == "__main__":
    # Test ID generation
    print("Testing Camera ID Generation:")
    for i in range(3):
        new_id = generate_camera_id()
        print(f"  Generated: {new_id} (Valid: {validate_camera_id(new_id)})")
    
    # Test validation
    print("\nTesting ID Validation:")
    test_ids = [
        "camera_a1b2c3d4e5f6",  # Valid new format
        "camera_12345678",       # Valid legacy format
        "camera_invalid",        # Invalid
        "123",                   # Numeric
        "entrance_cam"           # Name-based
    ]
    
    for test_id in test_ids:
        is_valid = validate_camera_id(test_id)
        normalized = normalize_camera_id(test_id)
        print(f"  ID: {test_id:20} Valid: {is_valid:5} Normalized: {normalized}")
    
    # Test display utilities
    print("\nTesting Display Names:")
    test_cameras = [
        {"camera_id": "camera_a1b2c3d4e5f6", "name": "Front Door Camera"},
        {"camera_id": "camera_b2c3d4e5f6a1", "name": ""},
        {"camera_id": "camera_c3d4e5f6a1b2", "name": "Parking Lot Entrance"}
    ]
    
    for camera in test_cameras:
        summary = CameraDisplayUtils.create_camera_summary(camera)
        print(f"  {summary['technical_id']} -> {summary['display_name']} ({summary['short_id']})")