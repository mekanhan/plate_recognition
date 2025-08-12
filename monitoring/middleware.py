"""
Monitoring Middleware for FastAPI
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .metrics import metrics

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect API metrics"""
    
    def __init__(self, app, excluded_paths: set = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or {
            '/metrics',
            '/health', 
            '/docs',
            '/openapi.json',
            '/favicon.ico'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for certain paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract endpoint path (remove query parameters and normalize)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method
        status = str(response.status_code)
        
        # Record metrics
        try:
            metrics.record_api_request(method, endpoint, status, duration)
        except Exception as e:
            logger.error(f"Failed to record API metrics: {e}")
        
        # Add response headers with timing info
        response.headers["X-Process-Time"] = str(duration)
        
        return response
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics grouping"""
        # Replace dynamic path parameters with placeholders
        # to avoid cardinality explosion in metrics
        
        # Common patterns to normalize
        import re
        
        # Replace UUIDs and IDs with placeholders
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace camera IDs
        path = re.sub(r'/camera_[a-zA-Z0-9_]+', '/camera_{id}', path)
        
        # Replace long detection IDs
        path = re.sub(r'/[a-f0-9]{32,}', '/{hash}', path)
        
        # Limit path length for metrics
        if len(path) > 100:
            path = path[:97] + "..."
        
        return path


class AuthMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect authentication metrics"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this is an auth-related request
        is_auth_request = (
            request.url.path.startswith('/api/auth/') or
            request.url.path.startswith('/api/users/')
        )
        
        response = await call_next(request)
        
        # Record auth metrics
        if is_auth_request:
            try:
                if request.url.path == '/api/auth/login':
                    success = response.status_code == 200
                    metrics.record_auth_attempt(success)
                
                # Check for permission denials
                if response.status_code == 403:
                    # Try to extract user info and permission from response
                    # This would require custom logic based on your error responses
                    metrics.record_permission_denial("unknown", "unknown")
            
            except Exception as e:
                logger.error(f"Failed to record auth metrics: {e}")
        
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Advanced performance monitoring middleware"""
    
    def __init__(self, app, slow_request_threshold: float = 2.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Add request start time to state
        request.state.start_time = start_time
        
        # Process request
        response = await call_next(request)
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration:.3f}s (threshold: {self.slow_request_threshold}s)"
            )
        
        # Add performance headers
        response.headers["X-Response-Time-ms"] = str(int(duration * 1000))
        response.headers["X-Server-Time"] = str(int(end_time))
        
        return response


def setup_monitoring_middleware(app):
    """Set up all monitoring middleware"""
    
    # Add performance monitoring (outermost)
    app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=2.0)
    
    # Add auth metrics
    app.add_middleware(AuthMetricsMiddleware)
    
    # Add general metrics (innermost)
    app.add_middleware(MetricsMiddleware)
    
    logger.info("Monitoring middleware configured")