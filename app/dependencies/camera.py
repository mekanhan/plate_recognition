# might need to remove this file.

from fastapi import Request

async def get_camera_service(request: Request):
    return request.app.state.camera_service
