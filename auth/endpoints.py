"""
Authentication API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List
from datetime import datetime

from .models import (
    Token, LoginRequest, CreateUserRequest, UpdateUserRequest, 
    User, UserRole, Permission
)
from .jwt_handler import jwt_handler
from .user_manager import user_manager
from .dependencies import get_current_user, require_admin, require_permission


# Create router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["User Management"])

# Basic auth for initial setup
basic_auth = HTTPBasic()


@auth_router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    user = user_manager.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Create JWT token
    access_token = jwt_handler.create_access_token(user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=jwt_handler.access_token_expire_minutes * 60,
        role=user.role,
        permissions=[p.value for p in user.get_permissions()]
    )


@auth_router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@auth_router.get("/permissions")
async def get_current_permissions(current_user: User = Depends(get_current_user)):
    """Get current user's permissions"""
    return {
        "role": current_user.role.value,
        "permissions": [p.value for p in current_user.get_permissions()]
    }


@auth_router.post("/check-permission")
async def check_permission(
    permission: str,
    current_user: User = Depends(get_current_user)
):
    """Check if current user has specific permission"""
    try:
        perm = Permission(permission)
        has_permission = current_user.has_permission(perm)
        return {
            "permission": permission,
            "granted": has_permission,
            "user_role": current_user.role.value
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {permission}"
        )


# User Management Endpoints (Admin only)
@users_router.get("/", response_model=List[User])
async def list_users(admin_user: User = Depends(require_admin())):
    """List all users (admin only)"""
    return user_manager.list_users()


@users_router.post("/", response_model=User)
async def create_user(
    request: CreateUserRequest,
    admin_user: User = Depends(require_admin())
):
    """Create new user (admin only)"""
    try:
        return user_manager.create_user(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@users_router.get("/{username}", response_model=User)
async def get_user(
    username: str,
    admin_user: User = Depends(require_admin())
):
    """Get user by username (admin only)"""
    user = user_manager.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@users_router.put("/{username}", response_model=User)
async def update_user(
    username: str,
    request: UpdateUserRequest,
    admin_user: User = Depends(require_admin())
):
    """Update user (admin only)"""
    update_data = request.dict(exclude_unset=True)
    user = user_manager.update_user(username, **update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@users_router.delete("/{username}")
async def delete_user(
    username: str,
    admin_user: User = Depends(require_admin())
):
    """Delete user (admin only)"""
    if username == admin_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    if user_manager.delete_user(username):
        return {"message": f"User '{username}' deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@users_router.post("/{username}/change-password")
async def change_user_password(
    username: str,
    new_password: str,
    admin_user: User = Depends(require_admin())
):
    """Change user password (admin only)"""
    user = user_manager.update_user(username, password=new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": f"Password changed for user '{username}'"}


# Health check endpoint (no auth required)
@auth_router.get("/health")
async def auth_health():
    """Authentication system health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "total_users": len(user_manager.list_users())
    }