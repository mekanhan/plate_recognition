"""
Authentication System Initialization
"""

from .models import User, UserRole, Permission, ROLE_PERMISSIONS
from .jwt_handler import jwt_handler
from .user_manager import user_manager
from .dependencies import (
    get_current_user, get_optional_user, require_admin, require_operator,
    require_permission, require_camera_view, require_camera_manage, 
    require_detection_view, require_recording_view, require_system_config
)
from .endpoints import auth_router, users_router

__all__ = [
    "User", "UserRole", "Permission", "ROLE_PERMISSIONS",
    "jwt_handler", "user_manager",
    "get_current_user", "get_optional_user", "require_admin", "require_operator",
    "require_permission", "require_camera_view", "require_camera_manage",
    "require_detection_view", "require_recording_view", "require_system_config",
    "auth_router", "users_router"
]

def initialize_auth_system():
    """Initialize the authentication system on startup"""
    print("🔐 Initializing authentication system...")
    
    # The user manager will automatically create default admin user
    # when initialized if no users exist
    users = user_manager.list_users()
    
    print(f"   Authentication system initialized with {len(users)} users")
    return True