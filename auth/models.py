"""
Authentication Models
"""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    VIEWER = "viewer"
    OPERATOR = "operator"


class Permission(str, Enum):
    """System permissions"""
    # Camera permissions
    CAMERA_VIEW = "camera:view"
    CAMERA_MANAGE = "camera:manage"
    CAMERA_CONFIGURE = "camera:configure"
    
    # Detection permissions
    DETECTION_VIEW = "detection:view"
    DETECTION_EXPORT = "detection:export"
    DETECTION_DELETE = "detection:delete"
    
    # Recording permissions
    RECORDING_VIEW = "recording:view"
    RECORDING_MANAGE = "recording:manage"
    RECORDING_EXPORT = "recording:export"
    
    # System permissions
    SYSTEM_STATUS = "system:status"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    
    # User management
    USER_VIEW = "user:view"
    USER_MANAGE = "user:manage"


# Role-based permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # Full access
        Permission.CAMERA_VIEW,
        Permission.CAMERA_MANAGE,
        Permission.CAMERA_CONFIGURE,
        Permission.DETECTION_VIEW,
        Permission.DETECTION_EXPORT,
        Permission.DETECTION_DELETE,
        Permission.RECORDING_VIEW,
        Permission.RECORDING_MANAGE,
        Permission.RECORDING_EXPORT,
        Permission.SYSTEM_STATUS,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_LOGS,
        Permission.USER_VIEW,
        Permission.USER_MANAGE,
    ],
    UserRole.OPERATOR: [
        # Can manage cameras and view everything
        Permission.CAMERA_VIEW,
        Permission.CAMERA_MANAGE,
        Permission.DETECTION_VIEW,
        Permission.DETECTION_EXPORT,
        Permission.RECORDING_VIEW,
        Permission.RECORDING_EXPORT,
        Permission.SYSTEM_STATUS,
    ],
    UserRole.VIEWER: [
        # Read-only access
        Permission.CAMERA_VIEW,
        Permission.DETECTION_VIEW,
        Permission.RECORDING_VIEW,
        Permission.SYSTEM_STATUS,
    ]
}


class User(BaseModel):
    """User model"""
    username: str
    email: Optional[str] = None
    role: UserRole
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        if not self.is_active:
            return False
        return permission in ROLE_PERMISSIONS.get(self.role, [])
    
    def get_permissions(self) -> List[Permission]:
        """Get all permissions for user's role"""
        if not self.is_active:
            return []
        return ROLE_PERMISSIONS.get(self.role, [])


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    role: UserRole
    permissions: List[str]


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class CreateUserRequest(BaseModel):
    """Create user request"""
    username: str
    password: str
    email: Optional[str] = None
    role: UserRole = UserRole.VIEWER


class UpdateUserRequest(BaseModel):
    """Update user request"""
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None