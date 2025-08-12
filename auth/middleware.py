"""
Authentication Middleware for Static Files
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from .dependencies import get_optional_user
from .jwt_handler import jwt_handler

logger = logging.getLogger(__name__)


class StaticFileAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to protect static file access"""
    
    def __init__(self, app, protected_paths: list = None):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/images"]
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is a protected static file path
        is_protected = any(request.url.path.startswith(path) for path in self.protected_paths)
        
        if is_protected:
            # Try to get user from authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header:
                try:
                    token = jwt_handler.extract_token_from_header(auth_header)
                    if token:
                        user = jwt_handler.get_user_from_token(token)
                        # User is authenticated, allow access
                        return await call_next(request)
                except Exception as e:
                    logger.debug(f"Token validation failed for static file: {e}")
            
            # No valid authentication for protected resource
            # For now, we'll allow access but log the attempt
            # In production, you might want to restrict this
            logger.warning(f"Unauthenticated access to protected static file: {request.url.path}")
        
        return await call_next(request)