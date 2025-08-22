"""
FastAPI Security Dependencies
Authentication and authorization dependencies for API endpoints
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from .auth_manager import (
    security_manager, AuthenticationManager, AuthorizationManager,
    UserRole, Permission
)
from database.db_config import db_config

logger = logging.getLogger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

# Global instances
auth_manager = AuthenticationManager(security_manager, db_config.get_session)
authz_manager = AuthorizationManager(security_manager)

class SecurityContext:
    """Security context for request"""
    def __init__(self, user_claims: Dict[str, Any], request: Request):
        self.user_claims = user_claims
        self.request = request
        self.user_id = user_claims.get('user_id')
        self.username = user_claims.get('username')
        self.role = UserRole(user_claims.get('role', 'viewer'))
        self.permissions = user_claims.get('permissions', [])
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if current user has permission"""
        return authz_manager.check_permission(self.user_claims, permission)
    
    def has_role(self, role: UserRole) -> bool:
        """Check if current user has role or higher"""
        return authz_manager.check_role(self.user_claims, role)
    
    def require_permission(self, permission: Permission):
        """Require permission or raise HTTP 403"""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
    
    def require_role(self, role: UserRole):
        """Require role or raise HTTP 403"""
        if not self.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}"
            )

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_scheme)
) -> SecurityContext:
    """Get current authenticated user from JWT token or API key"""
    
    # Try JWT authentication first
    if credentials:
        token_payload = security_manager.verify_jwt_token(credentials.credentials)
        if token_payload:
            # Log successful authentication
            await _log_auth_event(
                request, token_payload.get('user_id'), 
                'jwt_auth_success', True
            )
            return SecurityContext(token_payload, request)
    
    # Try API key authentication
    if api_key:
        user_claims = await auth_manager.authenticate_api_key(api_key)
        if user_claims:
            # Log successful API key authentication
            await _log_auth_event(
                request, user_claims.get('user_id'),
                'api_key_auth_success', True
            )
            return SecurityContext(user_claims, request)
    
    # Log failed authentication
    await _log_auth_event(request, None, 'auth_failed', False)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_scheme)
) -> Optional[SecurityContext]:
    """Get current user if authenticated, otherwise return None"""
    try:
        return await get_current_user(request, credentials, api_key)
    except HTTPException:
        return None

def require_permission(permission: Permission):
    """Decorator factory for requiring specific permission"""
    async def permission_checker(
        security_context: SecurityContext = Depends(get_current_user)
    ) -> SecurityContext:
        security_context.require_permission(permission)
        return security_context
    
    return permission_checker

def require_role(role: UserRole):
    """Decorator factory for requiring specific role"""
    async def role_checker(
        security_context: SecurityContext = Depends(get_current_user)
    ) -> SecurityContext:
        security_context.require_role(role)
        return security_context
    
    return role_checker

def require_admin():
    """Require admin role"""
    return require_role(UserRole.ADMIN)

def require_operator():
    """Require operator role or higher"""
    return require_role(UserRole.OPERATOR)

def require_any_permission(*permissions: Permission):
    """Require any of the specified permissions"""
    async def any_permission_checker(
        security_context: SecurityContext = Depends(get_current_user)
    ) -> SecurityContext:
        if not any(security_context.has_permission(p) for p in permissions):
            permission_list = ', '.join(p.value for p in permissions)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {permission_list}"
            )
        return security_context
    
    return any_permission_checker

def require_all_permissions(*permissions: Permission):
    """Require all of the specified permissions"""
    async def all_permissions_checker(
        security_context: SecurityContext = Depends(get_current_user)
    ) -> SecurityContext:
        missing_permissions = [
            p for p in permissions 
            if not security_context.has_permission(p)
        ]
        if missing_permissions:
            permission_list = ', '.join(p.value for p in missing_permissions)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {permission_list}"
            )
        return security_context
    
    return all_permissions_checker

# Rate limiting dependencies
class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window_seconds: int = 3600) -> bool:
        """Check if request is allowed within rate limit"""
        now = datetime.utcnow().timestamp()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests outside window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Record this request
        self.requests[key].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter()

def rate_limit(requests_per_hour: int = 1000):
    """Rate limiting decorator"""
    async def rate_limit_checker(
        request: Request,
        security_context: SecurityContext = Depends(get_current_user)
    ) -> SecurityContext:
        # Use user ID as rate limit key
        key = f"user:{security_context.user_id}"
        
        if not rate_limiter.is_allowed(key, requests_per_hour, 3600):
            await _log_auth_event(
                request, security_context.user_id,
                'rate_limit_exceeded', False
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return security_context
    
    return rate_limit_checker

async def _log_auth_event(request: Request, user_id: Optional[str], 
                         event_type: str, success: bool):
    """Log authentication event for audit"""
    try:
        from database.auth_models import AuditLog
        
        async with db_config.get_session() as session:
            audit_log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                event_category='auth',
                description=f"Authentication event: {event_type}",
                ip_address=_get_client_ip(request),
                user_agent=request.headers.get('user-agent'),
                endpoint=str(request.url.path),
                method=request.method,
                severity='info' if success else 'warning',
                success=success
            )
            session.add(audit_log)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to log auth event: {e}")

def _get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded IP (behind proxy)
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    # Check for real IP (behind proxy)
    real_ip = request.headers.get('x-real-ip')
    if real_ip:
        return real_ip
    
    # Fall back to direct connection
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    return 'unknown'

# Security middleware dependencies
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    
    return response