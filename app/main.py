import uvicorn
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.routers import stream, detection, results
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.enhancer_service import EnhancerService
from app.services.storage_service import StorageService
from app.utils.config import Settings, get_settings

# Initialize FastAPI app
app = FastAPI(
    title="License Plate Recognition Microservice",
    description="A microservice for license plate recognition with real-time enhancement",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize services
camera_service = CameraService()
detection_service = DetectionService()
enhancer_service = EnhancerService()
storage_service = StorageService()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    settings = get_settings()
    
    # Start camera
    await camera_service.initialize(camera_id=settings.camera_id)
    
    # Start detection service
    await detection_service.initialize(
        model_path=settings.model_path,
        camera_service=camera_service
    )
    
    # Start enhancer service
    await enhancer_service.initialize(
        known_plates_path=settings.known_plates_path
    )
    
    # Start storage service
    await storage_service.initialize(
        license_plates_dir=settings.license_plates_dir,
        enhanced_plates_dir=settings.enhanced_plates_dir
    )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources"""
    await camera_service.shutdown()
    await detection_service.shutdown()

# Include routers
app.include_router(stream.router, prefix="/stream", tags=["streaming"])
app.include_router(detection.router, prefix="/detection", tags=["detection"])
app.include_router(results.router, prefix="/results", tags=["results"])

# Root endpoint
@app.get("/")
async def root():
    return {"status": "LPR Microservice is running"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)