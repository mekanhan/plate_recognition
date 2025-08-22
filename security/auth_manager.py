"""
Authentication and Authorization Manager
Comprehensive security system for LPR platform
"""
import os
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import bcrypt
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"           # Full system access
    OPERATOR = "operator"     # Camera management, view recordings
    VIEWER = "viewer"         # View-only access
    API_CLIENT = "api_client" # Programmatic API access

class Permission(Enum):
    """Granular permission system"""
    # Camera permissions
    CAMERA_VIEW = "camera:view"
    CAMERA_CREATE = "camera:create"
    CAMERA_EDIT = "camera:edit"
    CAMERA_DELETE = "camera:delete"
    CAMERA_CONTROL = "camera:control"  # Start/stop recording
    
    # Recording permissions
    RECORDING_VIEW = "recording:view"
    RECORDING_DOWNLOAD = "recording:download"
    RECORDING_DELETE = "recording:delete"
    
    # Detection permissions
    DETECTION_VIEW = "detection:view"
    DETECTION_EXPORT = "detection:export"
    DETECTION_DELETE = "detection:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_HEALTH = "system:health"
    SYSTEM_CONFIG = "system:config"
    
    # User management permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"

@dataclass
class AuthConfig:
    """Authentication configuration"""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    password_min_length: int = 8
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    require_mfa: bool = False

class SecurityManager:
    """Core security management system"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.role_permissions = self._init_role_permissions()
        
    def _init_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize role-based permission mappings"""
        return {
            UserRole.ADMIN: [p for p in Permission],  # All permissions
            UserRole.OPERATOR: [
                Permission.CAMERA_VIEW, Permission.CAMERA_CREATE, Permission.CAMERA_EDIT,
                Permission.CAMERA_CONTROL, Permission.RECORDING_VIEW, Permission.RECORDING_DOWNLOAD,
                Permission.DETECTION_VIEW, Permission.DETECTION_EXPORT, Permission.SYSTEM_HEALTH
            ],
            UserRole.VIEWER: [
                Permission.CAMERA_VIEW, Permission.RECORDING_VIEW, 
                Permission.DETECTION_VIEW, Permission.SYSTEM_HEALTH
            ],
            UserRole.API_CLIENT: [
                Permission.CAMERA_VIEW, Permission.RECORDING_VIEW, Permission.DETECTION_VIEW,
                Permission.DETECTION_EXPORT, Permission.SYSTEM_HEALTH
            ]
        }
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    def create_jwt_token(self, user_id: str, role: UserRole, 
                        permissions: Optional[List[Permission]] = None) -> str:
        """Create JWT token with user claims"""
        if permissions is None:
            permissions = self.role_permissions.get(role, [])
        
        payload = {
            'user_id': user_id,
            'role': role.value,
            'permissions': [p.value for p in permissions],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.config.jwt_expiry_hours)
        }
        
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def has_permission(self, user_permissions: List[str], required_permission: Permission) -> bool:
        """Check if user has required permission"""
        return required_permission.value in user_permissions
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password meets security requirements"""
        result = {
            'valid': True,
            'errors': [],
            'score': 0
        }
        
        if len(password) < self.config.password_min_length:
            result['valid'] = False
            result['errors'].append(f"Password must be at least {self.config.password_min_length} characters")
        else:
            result['score'] += 1
        
        if not any(c.isupper() for c in password):
            result['errors'].append("Password must contain at least one uppercase letter")
        else:
            result['score'] += 1
        
        if not any(c.islower() for c in password):
            result['errors'].append("Password must contain at least one lowercase letter")
        else:
            result['score'] += 1
        
        if not any(c.isdigit() for c in password):
            result['errors'].append("Password must contain at least one number")
        else:
            result['score'] += 1
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            result['errors'].append("Password must contain at least one special character")
        else:
            result['score'] += 1
        
        if result['errors']:
            result['valid'] = False
        
        return result

class AuthenticationManager:
    """Handles user authentication operations"""
    
    def __init__(self, security_manager: SecurityManager, db_session_factory):
        self.security = security_manager
        self.db_session_factory = db_session_factory
        self.failed_attempts: Dict[str, List[datetime]] = {}
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password"""
        # Check if user is locked out
        if self._is_locked_out(username):
            logger.warning(f"Authentication blocked for locked out user: {username}")
            return None
        
        async with self.db_session_factory() as session:
            from database.models import User
            
            # Get user from database
            result = await session.execute(
                select(User).where(User.username == username, User.is_active == True)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                self._record_failed_attempt(username)
                logger.warning(f"Authentication failed - user not found: {username}")
                return None
            
            # Verify password
            if not self.security.verify_password(password, user.password_hash):
                self._record_failed_attempt(username)
                logger.warning(f"Authentication failed - invalid password: {username}")
                return None
            
            # Clear failed attempts on successful login
            self._clear_failed_attempts(username)
            
            # Update last login
            user.last_login = datetime.utcnow()
            await session.commit()
            
            logger.info(f"User authenticated successfully: {username}")
            
            return {
                'user_id': user.id,
                'username': user.username,
                'role': UserRole(user.role),
                'permissions': self.security.role_permissions.get(UserRole(user.role), [])
            }
    
    async def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate using API key"""
        async with self.db_session_factory() as session:
            from database.models import ApiKey
            
            # Hash the provided API key for comparison
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            result = await session.execute(
                select(ApiKey).where(
                    ApiKey.key_hash == key_hash,
                    ApiKey.is_active == True,
                    ApiKey.expires_at > datetime.utcnow()
                )
            )
            api_key_obj = result.scalar_one_or_none()
            
            if not api_key_obj:
                logger.warning("API key authentication failed")
                return None
            
            # Update last used
            api_key_obj.last_used = datetime.utcnow()
            await session.commit()
            
            logger.info(f"API key authenticated: {api_key_obj.name}")
            
            return {
                'user_id': f"api_{api_key_obj.id}",
                'username': api_key_obj.name,
                'role': UserRole.API_CLIENT,
                'permissions': self.security.role_permissions.get(UserRole.API_CLIENT, [])
            }
    
    def _is_locked_out(self, username: str) -> bool:
        """Check if user is locked out due to failed attempts"""
        if username not in self.failed_attempts:
            return False
        
        recent_attempts = [
            attempt for attempt in self.failed_attempts[username]
            if datetime.utcnow() - attempt < timedelta(minutes=self.security.config.lockout_duration_minutes)
        ]
        
        return len(recent_attempts) >= self.security.config.max_login_attempts
    
    def _record_failed_attempt(self, username: str):
        """Record failed authentication attempt"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        self.failed_attempts[username].append(datetime.utcnow())
        
        # Clean up old attempts
        cutoff = datetime.utcnow() - timedelta(minutes=self.security.config.lockout_duration_minutes)
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username]
            if attempt > cutoff
        ]
    
    def _clear_failed_attempts(self, username: str):
        """Clear failed attempts for user"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]

class AuthorizationManager:
    """Handles authorization and permission checking"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
    
    def check_permission(self, user_claims: Dict[str, Any], required_permission: Permission) -> bool:
        """Check if user has required permission"""
        user_permissions = user_claims.get('permissions', [])
        return self.security.has_permission(user_permissions, required_permission)
    
    def check_role(self, user_claims: Dict[str, Any], required_role: UserRole) -> bool:
        """Check if user has required role or higher"""
        user_role = UserRole(user_claims.get('role', ''))
        
        # Role hierarchy check
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.API_CLIENT: 2,
            UserRole.OPERATOR: 3,
            UserRole.ADMIN: 4
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def get_resource_permissions(self, user_claims: Dict[str, Any], resource_type: str) -> List[str]:
        """Get user permissions for specific resource type"""
        all_permissions = user_claims.get('permissions', [])
        return [p for p in all_permissions if p.startswith(f"{resource_type}:")]

# Global security manager instance
def get_security_config() -> AuthConfig:
    """Get security configuration from environment"""
    secret_key = os.getenv('JWT_SECRET_KEY')
    if not secret_key:
        # Generate a secure random key for development
        secret_key = secrets.token_urlsafe(64)
        logger.warning("JWT_SECRET_KEY not set, using generated key (not suitable for production)")
    
    return AuthConfig(
        jwt_secret_key=secret_key,
        jwt_expiry_hours=int(os.getenv('JWT_EXPIRY_HOURS', '24')),
        password_min_length=int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
        session_timeout_minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', '60')),
        max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
        lockout_duration_minutes=int(os.getenv('LOCKOUT_DURATION_MINUTES', '15')),
        require_mfa=os.getenv('REQUIRE_MFA', 'false').lower() == 'true'
    )

# Global instances
security_config = get_security_config()
security_manager = SecurityManager(security_config)