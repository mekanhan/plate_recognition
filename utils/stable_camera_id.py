"""
Utilities for stable camera ID generation and management
"""
import re
from typing import Set, Optional

def generate_stable_id(camera_name: str, existing_ids: Set[str] = None) -> str:
    """
    Generate a stable camera ID from camera name
    
    Args:
        camera_name: The camera's display name
        existing_ids: Set of already used stable IDs to avoid conflicts
        
    Returns:
        A valid stable camera ID
    """
    if existing_ids is None:
        existing_ids = set()
    
    # Start with normalized name
    base_id = normalize_camera_name(camera_name)
    
    # Ensure uniqueness
    stable_id = base_id
    counter = 1
    
    while stable_id in existing_ids:
        stable_id = f"{base_id}_{counter}"
        counter += 1
    
    return stable_id

def normalize_camera_name(name: str) -> str:
    """Convert camera name to stable ID format"""
    if not name or not name.strip():
        return "camera_unknown"
    
    # Convert to lowercase
    normalized = name.lower().strip()
    
    # Replace spaces and special characters with underscores
    normalized = re.sub(r'[^a-z0-9_]', '_', normalized)
    
    # Remove multiple underscores
    normalized = re.sub(r'_+', '_', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    # Ensure minimum length
    if len(normalized) < 3:
        normalized = f"camera_{normalized}" if normalized else "camera_unknown"
    
    # Ensure doesn't start with number
    if normalized and normalized[0].isdigit():
        normalized = f"cam_{normalized}"
    
    # Limit to 50 chars
    return normalized[:50]

def validate_stable_id(stable_id: str) -> bool:
    """
    Validate that a stable camera ID follows the required format
    
    Args:
        stable_id: The stable ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not stable_id or not isinstance(stable_id, str):
        return False
    
    # Length check
    if len(stable_id) < 3 or len(stable_id) > 50:
        return False
    
    # Format check: only lowercase letters, numbers, and underscores
    if not re.match(r'^[a-z][a-z0-9_]*[a-z0-9]$', stable_id):
        return False
    
    # No double underscores
    if '__' in stable_id:
        return False
    
    return True

def suggest_stable_id(camera_name: str) -> str:
    """
    Suggest a stable ID for a camera name (for UI)
    
    Args:
        camera_name: The camera's display name
        
    Returns:
        Suggested stable ID
    """
    return normalize_camera_name(camera_name)

# Common location-based stable ID suggestions
LOCATION_SUGGESTIONS = {
    'entrance': 'front_entrance',
    'front door': 'front_door', 
    'back door': 'back_door',
    'parking': 'parking_lot',
    'garage': 'garage_entrance',
    'loading dock': 'loading_dock',
    'warehouse': 'warehouse_main',
    'office': 'office_main',
    'reception': 'reception_desk',
    'lobby': 'lobby_main',
    'exit': 'main_exit',
    'side entrance': 'side_entrance',
    'gate': 'main_gate'
}

def get_location_suggestion(location_hint: str) -> Optional[str]:
    """
    Get a suggested stable ID based on location hint
    
    Args:
        location_hint: Location name or description
        
    Returns:
        Suggested stable ID or None if no good match
    """
    if not location_hint:
        return None
    
    location_lower = location_hint.lower()
    
    # Direct matches
    if location_lower in LOCATION_SUGGESTIONS:
        return LOCATION_SUGGESTIONS[location_lower]
    
    # Partial matches
    for key, suggestion in LOCATION_SUGGESTIONS.items():
        if key in location_lower or location_lower in key:
            return suggestion
    
    return None