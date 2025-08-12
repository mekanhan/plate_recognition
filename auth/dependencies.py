"""
FastAPI Dependencies for Authentication
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models import User, Permission
from .jwt_handler import jwt_handler


# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return jwt_handler.get_user_from_token(credentials.credentials)


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return jwt_handler.get_user_from_token(credentials.credentials)
    except HTTPException:
        return None


def require_permission(permission: Permission):
    """Dependency factory to require specific permission"""
    async def check_permission(current_user: User = Depends(get_current_user)):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return current_user
    return check_permission


def require_admin():
    """Dependency to require admin role"""
    return require_permission(Permission.USER_MANAGE)


def require_operator():
    """Dependency to require operator role or higher"""
    async def check_operator(current_user: User = Depends(get_current_user)):
        if not current_user.has_permission(Permission.CAMERA_MANAGE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator role or higher required"
            )
        return current_user
    return check_operator


# Common permission dependencies
require_camera_view = require_permission(Permission.CAMERA_VIEW)
require_camera_manage = require_permission(Permission.CAMERA_MANAGE)
require_detection_view = require_permission(Permission.DETECTION_VIEW)
require_recording_view = require_permission(Permission.RECORDING_VIEW)
require_system_config = require_permission(Permission.SYSTEM_CONFIG)