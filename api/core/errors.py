"""
Standardized error handling for API services
"""
from fastapi import HTTPException
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class APIError(HTTPException):
    """Base API error class with consistent formatting"""
    def __init__(
        self, 
        status_code: int, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.details = details or {}
        
        detail = {
            "message": message,
            "error_code": error_code,
            "details": self.details
        }
        
        super().__init__(status_code=status_code, detail=detail)

# Common error types
class CameraNotFoundError(APIError):
    def __init__(self, camera_id: str):
        super().__init__(
            status_code=404,
            message=f"Camera with ID '{camera_id}' not found",
            error_code="CAMERA_NOT_FOUND",
            details={"camera_id": camera_id}
        )

class CameraConnectionError(APIError):
    def __init__(self, camera_id: str, reason: str = "Connection failed"):
        super().__init__(
            status_code=503,
            message=f"Failed to connect to camera '{camera_id}': {reason}",
            error_code="CAMERA_CONNECTION_ERROR",
            details={"camera_id": camera_id, "reason": reason}
        )

class DetectionNotFoundError(APIError):
    def __init__(self, detection_id: str):
        super().__init__(
            status_code=404,
            message=f"Detection with ID '{detection_id}' not found",
            error_code="DETECTION_NOT_FOUND",
            details={"detection_id": detection_id}
        )

class ValidationError(APIError):
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            status_code=400,
            message=f"Validation error: {message}",
            error_code="VALIDATION_ERROR",
            details=details
        )

class ServiceUnavailableError(APIError):
    def __init__(self, service_name: str):
        super().__init__(
            status_code=503,
            message=f"Service '{service_name}' is currently unavailable",
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service_name}
        )

def log_and_raise_error(error: Exception, context: str = ""):
    """Log error with context and re-raise as appropriate API error"""
    
    if isinstance(error, APIError):
        logger.warning(f"{context}: {error.detail}")
        raise error
    
    # Convert common exceptions to API errors
    if isinstance(error, FileNotFoundError):
        logger.error(f"{context}: File not found - {str(error)}")
        raise APIError(
            status_code=404,
            message="Resource not found",
            error_code="RESOURCE_NOT_FOUND"
        )
    
    if isinstance(error, PermissionError):
        logger.error(f"{context}: Permission denied - {str(error)}")
        raise APIError(
            status_code=403,
            message="Access denied",
            error_code="ACCESS_DENIED"
        )
    
    # Generic error handling
    logger.error(f"{context}: Unexpected error - {str(error)}", exc_info=True)
    raise APIError(
        status_code=500,
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        details={"original_error": str(error)}
    )