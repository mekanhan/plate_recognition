#!/usr/bin/env python3
"""
Simple test server for camera database API endpoints
Tests the new database-driven camera management without YOLO dependencies
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from database.service import DatabaseService
from database.camera_service import CameraService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CameraAPITest")

# Initialize services
database_service = DatabaseService()
camera_service = CameraService(database_service)

# Create FastAPI app
app = FastAPI(title="Camera Database API Test", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await database_service.init_db()
    logger.info("Camera API Test server started")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Camera Database API Test Server", "status": "running"}

@app.get("/v2/api/cameras/status")
async def get_cameras_status():
    """Get status of all cameras (8-field standard)"""
    return await camera_service.get_cameras_status()

@app.get("/v2/api/cameras")
async def get_all_cameras():
    """Get all cameras with full details"""
    cameras = await camera_service.get_all_cameras()
    return {"cameras": cameras, "count": len(cameras)}

@app.get("/v2/api/cameras/{camera_id}")
async def get_camera(camera_id: str):
    """Get single camera by ID"""
    camera = await camera_service.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@app.get("/v2/api/cameras/{camera_id}/status")
async def get_camera_status(camera_id: str):
    """Get status for a specific camera"""
    # Get all cameras status and filter for specific camera
    all_status = await camera_service.get_cameras_status()
    for camera in all_status.get('cameras', []):
        if camera.get('id') == camera_id:
            return camera
    raise HTTPException(status_code=404, detail="Camera not found")

@app.post("/v2/api/cameras/{camera_id}/start")
async def start_recording(camera_id: str):
    """Start recording for a camera"""
    # For now, just update status in database
    success = await camera_service.update_camera_status(camera_id, {
        "recording_status": "recording",
        "connection_status": "connected"
    })
    if success:
        return {"message": f"Recording started for camera {camera_id}", "status": "success"}
    else:
        raise HTTPException(status_code=404, detail="Camera not found")

@app.post("/v2/api/cameras/{camera_id}/stop")
async def stop_recording(camera_id: str):
    """Stop recording for a camera"""
    success = await camera_service.update_camera_status(camera_id, {
        "recording_status": "stopped"
    })
    if success:
        return {"message": f"Recording stopped for camera {camera_id}", "status": "success"}
    else:
        raise HTTPException(status_code=404, detail="Camera not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        status = await camera_service.get_cameras_status()
        return {
            "status": "healthy",
            "database": "connected",
            "cameras_count": status.get("count", 0),
            "timestamp": status.get("timestamp")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": "error"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")