# might need to remove this file.

from fastapi import Request

async def get_detection_service(request: Request):
    """Return the detection service instance from application state."""
    try:
        # Try V2 service first (for main_v2.py), then fall back to V1 (for main.py)
        if hasattr(request.app.state, 'detection_service_v2'):
            return request.app.state.detection_service_v2
        elif hasattr(request.app.state, 'detection_service'):
            return request.app.state.detection_service
        else:
            # Fallback to global variable if app.state is not available
            from app.routers import results
            return results.detection_service
    except Exception as e:
        # If we can't get detection service, return None and let the router handle it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting detection service: {e}")
        return None
