import uvicorn
import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.services.enhancer_service import EnhancerService
from app.routers import stream, detection, results
from app.utils.logging_config import setup_logging
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # Add the missing fields:
    camera_id: str = "0"
    camera_width: str = "1280"
    camera_height: str = "720"
    model_path: str = "app/models/yolo11m_best.pt"
    license_plates_dir: str = "data/license_plates"
    enhanced_plates_dir: str = "data/enhanced_plates"
    known_plates_path: str = "data/known_plates.json"

    # Your existing fields...

    class Config:
        env_file = ".env"
        # If you want to allow arbitrary fields, you can add:
        # extra = "allow"

setup_logging()

config = Config()
app = FastAPI(
    title="License Plate Recognition Microservice",
    description="A microservice for license plate recognition with real-time enhancement",
    version="1.0.0"
)
app.state.config = config

os.makedirs("data/license_plates", exist_ok=True)
os.makedirs("data/enhanced_plates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# After initializing services
camera_service = CameraService()
detection_service = DetectionService()
storage_service = StorageService()
enhancer_service = EnhancerService()

app.state.camera_service = camera_service
app.state.detection_service = detection_service
app.state.storage_service = storage_service
app.state.enhancer_service = enhancer_service

# Connect detection service to storage service
detection_service.storage_service = storage_service
print("Connected detection service to storage service")

# Set the services in the routers
stream.camera_service = camera_service
stream.detection_service = detection_service
detection.detection_service = detection_service
results.detection_service = detection_service
results.storage_service = storage_service

@app.on_event("startup")
async def startup_event():
    # Initialize storage first
    await storage_service.initialize()
    print("Storage service initialized")

    # Then camera
    await camera_service.initialize()
    print("Camera service initialized")

    # Then detection (which depends on camera)
    await detection_service.initialize(camera_service=camera_service)
    print("Detection service initialized")

    # Finally enhancer
    await enhancer_service.initialize()
    print("Enhancer service initialized")

    print("All services initialized successfully")
async def startup_event():
    await camera_service.initialize()
    await detection_service.initialize(camera_service=camera_service)
    await storage_service.initialize()
    await enhancer_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await camera_service.shutdown()
    await detection_service.shutdown()
    await storage_service.shutdown()

# Then include the routers
app.include_router(stream.router, prefix="/stream", tags=["streaming"])
app.include_router(detection.router, prefix="/detection", tags=["detection"])
app.include_router(results.router, prefix="/results", tags=["results"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/detection-test", response_class=HTMLResponse)
async def detection_test_page(request: Request):
    return templates.TemplateResponse("detection_test.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)