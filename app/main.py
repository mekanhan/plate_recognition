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

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

app = FastAPI(
    title="License Plate Recognition Microservice",
    description="A microservice for license plate recognition with real-time enhancement",
    version="1.0.0"
)
os.makedirs("data/license_plates", exist_ok=True)
os.makedirs("data/enhanced_plates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

camera_service = CameraService()
detection_service = DetectionService()
storage_service = StorageService()
enhancer_service = EnhancerService()

stream.camera_service = camera_service
detection.detection_service = detection_service
results.detection_service = detection_service
results.storage_service = storage_service

@app.on_event("startup")
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