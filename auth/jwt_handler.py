"""
JWT Token Handler
"""
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from .models import User, UserRole, Permission
import secrets


class JWTHandler:
    """Handle JWT token generation and validation"""
    
    def __init__(self):
        # Use environment variable or generate a secure key
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            # Generate a secure random key (should be set in production)
            self.secret_key = secrets.token_urlsafe(32)
            print("⚠️  JWT_SECRET_KEY not set in environment, using generated key")
        
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))  # 12 hours default
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user.username,  # Subject (username)
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.get_permissions()],
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "is_active": user.is_active
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def get_user_from_token(self, token: str) -> User:
        """Extract user information from JWT token"""
        payload = self.decode_token(token)
        
        if not payload.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        user = User(
            username=payload["sub"],
            email=payload.get("email"),
            role=UserRole(payload["role"]),
            is_active=payload.get("is_active", True),
            created_at=datetime.utcnow(),  # We don't store this in JWT
            last_login=datetime.utcnow()
        )
        
        return user
    
    def verify_permission(self, token: str, required_permission: Permission) -> bool:
        """Verify if token has required permission"""
        try:
            user = self.get_user_from_token(token)
            return user.has_permission(required_permission)
        except HTTPException:
            return False
    
    def extract_token_from_header(self, authorization: Optional[str]) -> Optional[str]:
        """Extract token from Authorization header"""
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None


# Global JWT handler instance
jwt_handler = JWTHandler()