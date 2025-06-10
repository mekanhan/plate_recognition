# might need to remove this file.

from fastapi import Request

async def get_detection_service(request: Request):
    """Return the detection service instance from application state."""
    return request.app.state.detection_service
