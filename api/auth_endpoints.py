"""
Authentication API Endpoints
User authentication, registration, and session management
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import secrets
import hashlib
import logging

from security.auth_manager import security_manager, UserRole, Permission
from security.dependencies import (
    get_current_user, require_admin, require_permission, SecurityContext,
    auth_manager, _log_auth_event, _get_client_ip
)
from database.db_config import db_config
from database.auth_models import User, ApiKey, UserSession, AuditLog

router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

# Request/Response Models
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = "viewer"
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        validation = security_manager.validate_password_strength(v)
        if not validation['valid']:
            raise ValueError('; '.join(validation['errors']))
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v not in [role.value for role in UserRole]:
            raise ValueError(f'Invalid role. Must be one of: {[role.value for role in UserRole]}')
        return v

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    mfa_enabled: bool

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        validation = security_manager.validate_password_strength(v)
        if not validation['valid']:
            raise ValueError('; '.join(validation['errors']))
        return v

class CreateApiKeyRequest(BaseModel):
    name: str
    description: Optional[str] = None
    expires_in_days: Optional[int] = 365
    scopes: Optional[List[str]] = None

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key: Optional[str] = None  # Only returned on creation
    key_prefix: str
    expires_at: datetime
    scopes: Optional[str]
    created_at: datetime

# Authentication Endpoints

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        # Authenticate user
        user_claims = await auth_manager.authenticate_user(
            login_data.username, 
            login_data.password
        )
        
        if not user_claims:
            await _log_auth_event(
                request, None, 'login_failed', False
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create JWT token
        expiry_hours = 720 if login_data.remember_me else 24  # 30 days vs 1 day
        token = security_manager.create_jwt_token(
            user_claims['user_id'],
            user_claims['role'],
            user_claims['permissions']
        )
        
        # Create session record
        async with db_config.get_session() as session:
            user_session = UserSession(
                user_id=user_claims['user_id'],
                session_token=secrets.token_urlsafe(32),
                jwt_token_hash=hashlib.sha256(token.encode()).hexdigest(),
                ip_address=_get_client_ip(request),
                user_agent=request.headers.get('user-agent'),
                expires_at=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            session.add(user_session)
            await session.commit()
        
        # Log successful login
        await _log_auth_event(
            request, user_claims['user_id'], 'login_success', True
        )
        
        logger.info(f"User logged in successfully: {login_data.username}")
        
        return LoginResponse(
            access_token=token,
            expires_in=expiry_hours * 3600,  # Convert to seconds
            user={
                'id': user_claims['user_id'],
                'username': user_claims['username'],
                'role': user_claims['role'].value,
                'permissions': [p.value for p in user_claims['permissions']]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

@router.post("/logout")
async def logout(
    request: Request,
    security_context: SecurityContext = Depends(get_current_user)
):
    """Logout user and invalidate session"""
    try:
        # Get authorization header to find session
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # End session
            async with db_config.get_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(UserSession).where(
                        UserSession.jwt_token_hash == token_hash,
                        UserSession.is_active == True
                    )
                )
                user_session = result.scalar_one_or_none()
                
                if user_session:
                    user_session.end_session()
                    await session.commit()
        
        # Log logout
        await _log_auth_event(
            request, security_context.user_id, 'logout', True
        )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"message": "Logged out (with errors)"}

@router.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    register_data: RegisterRequest,
    security_context: SecurityContext = Depends(require_admin())
):
    """Register new user (admin only)"""
    try:
        async with db_config.get_session() as session:
            # Check if username or email already exists
            from sqlalchemy import select, or_
            result = await session.execute(
                select(User).where(
                    or_(User.username == register_data.username,
                        User.email == register_data.email)
                )
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                detail = "Username already exists" if existing_user.username == register_data.username else "Email already exists"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=detail
                )
            
            # Create new user
            password_hash = security_manager.hash_password(register_data.password)
            
            new_user = User(
                username=register_data.username,
                email=register_data.email,
                password_hash=password_hash,
                first_name=register_data.first_name,
                last_name=register_data.last_name,
                role=register_data.role,
                is_verified=True  # Admin-created users are pre-verified
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            # Log user creation
            await _log_auth_event(
                request, security_context.user_id, 'user_created', True
            )
            
            logger.info(f"New user registered: {register_data.username} by {security_context.username}")
            
            return UserResponse(**new_user.to_dict())
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service error"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    security_context: SecurityContext = Depends(get_current_user)
):
    """Get current user information"""
    try:
        async with db_config.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == security_context.user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserResponse(**user.to_dict())
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User service error"
        )

@router.put("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    security_context: SecurityContext = Depends(get_current_user)
):
    """Change user password"""
    try:
        async with db_config.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == security_context.user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not security_manager.verify_password(password_data.current_password, user.password_hash):
                await _log_auth_event(
                    request, security_context.user_id, 'password_change_failed', False
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Update password
            user.password_hash = security_manager.hash_password(password_data.new_password)
            user.updated_at = datetime.utcnow()
            
            await session.commit()
            
            # Log password change
            await _log_auth_event(
                request, security_context.user_id, 'password_changed', True
            )
            
            logger.info(f"Password changed for user: {security_context.username}")
            
            return {"message": "Password changed successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password service error"
        )

# API Key Management

@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    request: Request,
    api_key_data: CreateApiKeyRequest,
    security_context: SecurityContext = Depends(get_current_user)
):
    """Create new API key"""
    try:
        # Generate API key
        api_key = security_manager.generate_api_key()
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_prefix = api_key[:8]
        
        async with db_config.get_session() as session:
            new_api_key = ApiKey(
                user_id=security_context.user_id,
                name=api_key_data.name,
                description=api_key_data.description,
                key_hash=key_hash,
                key_prefix=key_prefix,
                scopes=str(api_key_data.scopes) if api_key_data.scopes else None,
                expires_at=ApiKey.create_expiry_date(api_key_data.expires_in_days)
            )
            
            session.add(new_api_key)
            await session.commit()
            await session.refresh(new_api_key)
            
            # Log API key creation
            await _log_auth_event(
                request, security_context.user_id, 'api_key_created', True
            )
            
            logger.info(f"API key created: {api_key_data.name} by {security_context.username}")
            
            response_data = new_api_key.to_dict()
            response_data['key'] = api_key  # Only returned on creation
            
            return ApiKeyResponse(**response_data)
            
    except Exception as e:
        logger.error(f"Create API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key service error"
        )

@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    security_context: SecurityContext = Depends(get_current_user)
):
    """List user's API keys"""
    try:
        async with db_config.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ApiKey).where(ApiKey.user_id == security_context.user_id)
            )
            api_keys = result.scalars().all()
            
            return [ApiKeyResponse(**key.to_dict()) for key in api_keys]
            
    except Exception as e:
        logger.error(f"List API keys error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key service error"
        )

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    request: Request,
    security_context: SecurityContext = Depends(get_current_user)
):
    """Delete API key"""
    try:
        async with db_config.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ApiKey).where(
                    ApiKey.id == key_id,
                    ApiKey.user_id == security_context.user_id
                )
            )
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            await session.delete(api_key)
            await session.commit()
            
            # Log API key deletion
            await _log_auth_event(
                request, security_context.user_id, 'api_key_deleted', True
            )
            
            logger.info(f"API key deleted: {api_key.name} by {security_context.username}")
            
            return {"message": "API key deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key service error"
        )