"""
24/7 Recording Service - Port 8002
Handles continuous camera recording and playback API
"""
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import uvicorn

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.service import DatabaseService
from recording_service.services.ffmpeg_recording_manager import FFmpegRecordingManager
from recording_service.services.playback_service import PlaybackService
from recording_service.services.storage_manager import StorageManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recording_service/logs/recording_service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global services
recording_manager = None
playback_service = None
storage_manager = None
db_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global recording_manager, playback_service, storage_manager, db_service
    
    logger.info("Starting 24/7 Recording Service...")
    
    # Initialize services
    db_service = DatabaseService()
    await db_service.init_db()
    
    storage_manager = StorageManager(
        recordings_path="recordings",
        storage_limit_gb=10  # Configurable
    )
    
    recording_manager = FFmpegRecordingManager(
        db_service=db_service,
        storage_path="recordings"
    )
    
    playback_service = PlaybackService(
        db_service=db_service,
        recordings_path="recordings"
    )
    
    # Start background recording
    await recording_manager.start()
    
    logger.info("Recording Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Recording Service...")
    if recording_manager:
        await recording_manager.stop()
    logger.info("Recording Service stopped")

# Create FastAPI app
app = FastAPI(
    title="24/7 Recording Service",
    description="Continuous camera recording and playback API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "service": "24/7 Recording Service",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "recording_active": bool(recording_manager and recording_manager.recorders)
    }

# Recording status endpoints
@app.get("/recordings/status")
async def get_all_recording_status():
    """Get recording status for all cameras"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    return await recording_manager.get_status_all_cameras()

@app.get("/recordings/status/{camera_id}")
async def get_camera_recording_status(camera_id: str):
    """Get recording status for specific camera"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    status = await recording_manager.get_camera_status(camera_id)
    if not status:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return status

# Camera management endpoints
@app.post("/recordings/cameras/{camera_id}/start")
async def start_camera_recording(camera_id: str):
    """Start recording for a specific camera"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    success = await recording_manager.add_camera(camera_id)
    if success:
        return {"message": f"Started recording for camera {camera_id}"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to start recording for camera {camera_id}")

@app.post("/recordings/cameras/{camera_id}/stop")
async def stop_camera_recording(camera_id: str):
    """Stop recording for a specific camera"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    success = await recording_manager.remove_camera(camera_id)
    if success:
        return {"message": f"Stopped recording for camera {camera_id}"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to stop recording for camera {camera_id}")

@app.post("/recordings/reload")
async def reload_all_cameras():
    """Reload all cameras from database (hot reload)"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    success = await recording_manager.reload_cameras()
    if success:
        status = await recording_manager.get_status_all_cameras()
        return {
            "message": "Cameras reloaded successfully",
            "active_cameras": len(status.get("cameras", {})),
            "status": status
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to reload cameras")

# Playback API endpoints (from documentation)
@app.get("/api/v1/recordings/cameras/{camera_id}/calendar")
async def get_calendar_data(
    camera_id: str,
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12)
):
    """Get recording availability for calendar display"""
    if not playback_service:
        raise HTTPException(status_code=503, detail="Playback service not initialized")
    
    return await playback_service.get_calendar_data(camera_id, year, month)

@app.get("/api/v1/recordings/cameras/{camera_id}/timeline")
async def get_timeline_segments(
    camera_id: str,
    date: str = Query(..., regex="^\\d{4}-\\d{2}-\\d{2}$"),
    start_hour: Optional[int] = Query(None, ge=0, le=23),
    end_hour: Optional[int] = Query(None, ge=0, le=23)
):
    """Get timeline segments for a specific date"""
    if not playback_service:
        raise HTTPException(status_code=503, detail="Playback service not initialized")
    
    return await playback_service.get_timeline_segments(camera_id, date, start_hour, end_hour)

@app.get("/api/v1/recordings/stream/{segment_filename}")
async def stream_video_segment(
    segment_filename: str,
    range: Optional[str] = Header(None)
):
    """Stream video segment with seek support"""
    if not playback_service:
        raise HTTPException(status_code=503, detail="Playback service not initialized")
    
    return await playback_service.stream_segment_file_based(segment_filename, range)

@app.options("/api/v1/recordings/stream/{segment_filename}")
async def stream_video_options(segment_filename: str):
    """Handle CORS preflight requests for video streaming"""
    return {
        "status": "ok",
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Range, Content-Type",
            "Access-Control-Max-Age": "3600"
        }
    }

@app.get("/api/v1/recordings/cameras/{camera_id}/details")
async def get_recording_details(
    camera_id: str,
    date: str = Query(..., regex="^\\d{4}-\\d{2}-\\d{2}$")
):
    """Get detailed recording statistics"""
    if not playback_service:
        raise HTTPException(status_code=503, detail="Playback service not initialized")
    
    return await playback_service.get_recording_details(camera_id, date)

@app.post("/api/v1/recordings/cameras/{camera_id}/search")
async def search_segments(camera_id: str, search_params: dict):
    """Search recordings with filters"""
    if not playback_service:
        raise HTTPException(status_code=503, detail="Playback service not initialized")
    
    return await playback_service.search_segments(camera_id, search_params)

# Storage management endpoints
@app.get("/api/v1/storage/report")
async def get_storage_report():
    """Get comprehensive storage statistics"""
    if not storage_manager:
        raise HTTPException(status_code=503, detail="Storage manager not initialized")
    
    return await storage_manager.get_storage_report()

@app.post("/api/v1/storage/cleanup")
async def trigger_storage_cleanup(
    target_size_gb: Optional[float] = Query(None, le=10),
    delete_before_date: Optional[str] = Query(None)
):
    """Manually trigger storage cleanup"""
    if not storage_manager:
        raise HTTPException(status_code=503, detail="Storage manager not initialized")
    
    return await storage_manager.cleanup_storage(target_size_gb, delete_before_date)

if __name__ == "__main__":
    # Create logs directory
    os.makedirs("recording_service/logs", exist_ok=True)
    
    # Run the service
    uvicorn.run(
        "recording_service.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )