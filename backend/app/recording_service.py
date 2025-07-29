"""
24/7 Recording Service - Runs independently on port 8002
Separate from web UI to ensure continuous recording
"""
import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.recording.recording_manager import RecordingManager
from core.storage.storage_manager import StorageManager, StorageConfig
from database import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/recording_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global recording manager instance
recording_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global recording_manager
    
    # Startup
    logger.info("Starting 24/7 Recording Service...")
    
    try:
        # Initialize storage configuration
        storage_config = StorageConfig({
            'base_storage_path': 'recordings',
            'retention_days': 30,
            'cleanup_interval_hours': 1,
            'max_storage_gb_per_camera': 1000,
            'warning_threshold_percent': 80
        })
        
        # Initialize recording manager
        recording_manager = RecordingManager(
            config_file="config/cameras.json",
            storage_config=storage_config
        )
        
        # Start all recordings
        await recording_manager.start_all_recordings()
        
        logger.info("24/7 Recording Service started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start recording service: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down 24/7 Recording Service...")
    
    if recording_manager:
        await recording_manager.stop_all_recordings()
    
    logger.info("24/7 Recording Service stopped")


# Create FastAPI app with lifespan management
app = FastAPI(
    title="24/7 Recording Service",
    description="Continuous camera recording service independent of web UI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Service health check"""
    return {
        "service": "24/7 Recording Service",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        # Get recording status for all cameras
        all_status = recording_manager.get_all_status()
        
        # Count active recordings
        active_recordings = sum(1 for status in all_status.values() if status['is_recording'])
        total_cameras = len(all_status)
        
        # Get storage health
        storage_report = await recording_manager.get_storage_report()
        
        return {
            "status": "healthy" if active_recordings > 0 else "degraded",
            "service_running": recording_manager.is_running,
            "active_recordings": active_recordings,
            "total_cameras": total_cameras,
            "storage_health": {
                "total_size": storage_report.get("system_stats", {}).get("total_size_formatted", "0 B"),
                "total_segments": storage_report.get("system_stats", {}).get("total_segments", 0),
                "disk_free_percent": storage_report.get("disk_usage", {}).get("free_percent", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/recordings/status")
async def get_all_recording_status():
    """Get recording status for all cameras"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        all_status = recording_manager.get_all_status()
        
        return {
            "service_running": recording_manager.is_running,
            "total_recorders": len(all_status),
            "active_recordings": sum(1 for s in all_status.values() if s['is_recording']),
            "cameras": all_status,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting recording status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recordings/status/{camera_id}")
async def get_camera_recording_status(camera_id: int):
    """Get recording status for a specific camera"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        status = recording_manager.get_camera_status(camera_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"No recording found for camera {camera_id}")
        
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting camera {camera_id} status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recordings/start/{camera_id}")
async def start_camera_recording(camera_id: int, db: AsyncSession = Depends(get_database)):
    """Start recording for a specific camera"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        # Get camera config from database
        from services.camera_crud import get_camera_by_id
        camera = await get_camera_by_id(db, camera_id)
        
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        if not camera.enabled:
            raise HTTPException(status_code=400, detail=f"Camera {camera_id} is disabled")
        
        # Convert database camera to recording config format
        camera_config = {
            'id': camera.id,
            'name': camera.name,
            'ip_address': camera.ip_address,
            'port': camera.port,
            'connection_type': camera.connection_type,
            'stream_path': camera.stream_path,
            'username': camera.username,
            'password': camera.password,
            'recording_enabled': True,
            'rtsp_url': f"rtsp://{camera.username}:{camera.password}@{camera.ip_address}:{camera.port}{camera.stream_path}"
        }
        
        # Start recording
        await recording_manager.start_camera_recording(camera_config)
        
        return {
            "camera_id": camera_id,
            "status": "recording_started",
            "message": f"Started recording for camera {camera.name}",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting recording for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recordings/stop/{camera_id}")
async def stop_camera_recording(camera_id: int):
    """Stop recording for a specific camera"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        recording_manager.stop_camera_recording(camera_id)
        
        return {
            "camera_id": camera_id,
            "status": "recording_stopped",
            "message": f"Stopped recording for camera {camera_id}",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error stopping recording for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recordings/{camera_id}/segments")
async def get_camera_recordings(
    camera_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """Get available recordings for a camera"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        # Parse time parameters
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
        else:
            start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
        else:
            end_dt = datetime.now()
        
        # Get recordings from the recording manager
        # Note: This method needs to be implemented in recording_manager
        recordings = []  # recording_manager.get_available_recordings(camera_id, start_dt, end_dt)
        
        return {
            "camera_id": camera_id,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "recordings": recordings,
            "total_segments": len(recordings)
        }
    
    except Exception as e:
        logger.error(f"Error getting recordings for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage/report")
async def get_storage_report():
    """Get comprehensive storage report"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        report = await recording_manager.get_storage_report()
        return report
    
    except Exception as e:
        logger.error(f"Error generating storage report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage/cleanup")
async def trigger_storage_cleanup():
    """Trigger immediate storage cleanup"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        # Force cleanup through storage manager
        storage_manager = recording_manager.get_storage_manager()
        await storage_manager.cleanup_old_recordings()
        
        return {
            "status": "cleanup_completed",
            "message": "Storage cleanup completed successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error during storage cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage/cleanup/{camera_id}")
async def cleanup_camera_storage(camera_id: int):
    """Trigger cleanup for specific camera"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        result = await recording_manager.cleanup_camera_storage(camera_id)
        return result
    
    except Exception as e:
        logger.error(f"Error cleaning up camera {camera_id} storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recordings/health-check")
async def perform_health_check():
    """Perform health check and restart failed recordings"""
    if not recording_manager:
        raise HTTPException(status_code=503, detail="Recording manager not initialized")
    
    try:
        await recording_manager.health_check()
        
        return {
            "status": "health_check_completed",
            "message": "Health check completed, unhealthy recordings restarted",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        # FastAPI will handle the graceful shutdown through lifespan
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    import uvicorn
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Create logs directory
    import os
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Starting 24/7 Recording Service on port 8002...")
    
    # Run the service
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        reload=False,  # Don't use reload in production
        log_level="info"
    )