"""
Recording API Service - REST API for 24/7 Recording System
Provides HTTP endpoints to monitor and control the recording system
"""
import os
import sqlite3
import shutil
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="24/7 Recording API",
    description="REST API for monitoring and controlling the 24/7 camera recording system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
RECORDINGS_BASE_PATH = Path("recordings")
STORAGE_CONFIG_PATH = Path("config/storage_settings.json")


@app.get("/")
async def root():
    """API health check"""
    return {
        "service": "24/7 Recording API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check if recordings directory exists
        recordings_exist = RECORDINGS_BASE_PATH.exists()
        
        # Get camera directories
        camera_dirs = [d for d in RECORDINGS_BASE_PATH.iterdir() if d.is_dir() and d.name.startswith('camera_')]
        
        # Check active recordings
        active_cameras = []
        total_segments = 0
        total_size = 0
        
        for camera_dir in camera_dirs:
            camera_id = int(camera_dir.name.split('_')[1])
            
            # Check if database exists
            db_path = camera_dir / "index.db"
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    
                    # Get segment count and total size
                    cursor.execute("SELECT COUNT(*), SUM(file_size) FROM segments")
                    result = cursor.fetchone()
                    
                    segments = result[0] or 0
                    size = result[1] or 0
                    
                    total_segments += segments
                    total_size += size
                    
                    # Check if recently active (last segment within 15 minutes)
                    cursor.execute("SELECT MAX(start_time) FROM segments")
                    last_segment = cursor.fetchone()[0]
                    
                    is_active = False
                    if last_segment:
                        last_time = datetime.fromisoformat(last_segment)
                        is_active = (datetime.now() - last_time).total_seconds() < 900  # 15 minutes
                    
                    active_cameras.append({
                        "camera_id": camera_id,
                        "segments": segments,
                        "size_bytes": size,
                        "is_active": is_active,
                        "last_segment": last_segment
                    })
                    
                    conn.close()
                    
                except Exception as e:
                    logger.error(f"Error checking camera {camera_id}: {e}")
        
        # Get disk usage
        disk_usage = shutil.disk_usage(RECORDINGS_BASE_PATH)
        disk_free_percent = (disk_usage.free / disk_usage.total) * 100
        
        return {
            "status": "healthy" if active_cameras else "no_recordings",
            "recordings_directory_exists": recordings_exist,
            "active_cameras": len([c for c in active_cameras if c["is_active"]]),
            "total_cameras": len(active_cameras),
            "total_segments": total_segments,
            "total_size_bytes": total_size,
            "total_size_formatted": _format_bytes(total_size),
            "disk_free_percent": round(disk_free_percent, 1),
            "disk_free_formatted": _format_bytes(disk_usage.free),
            "cameras": active_cameras,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/recordings/status")
async def get_all_recordings_status():
    """Get recording status for all cameras"""
    try:
        camera_dirs = [d for d in RECORDINGS_BASE_PATH.iterdir() if d.is_dir() and d.name.startswith('camera_')]
        
        cameras = {}
        for camera_dir in camera_dirs:
            camera_id = int(camera_dir.name.split('_')[1])
            status = await _get_camera_status(camera_id)
            cameras[camera_id] = status
        
        return {
            "total_cameras": len(cameras),
            "cameras": cameras,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recordings status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recordings/status/{camera_id}")
async def get_camera_recording_status(camera_id: int):
    """Get recording status for a specific camera"""
    try:
        status = await _get_camera_status(camera_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"No recordings found for camera {camera_id}")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting camera {camera_id} status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recordings/{camera_id}/segments")
async def get_camera_segments(
    camera_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100
):
    """Get available segments for a camera"""
    try:
        camera_dir = RECORDINGS_BASE_PATH / f"camera_{camera_id}"
        db_path = camera_dir / "index.db"
        
        if not db_path.exists():
            raise HTTPException(status_code=404, detail=f"No recordings found for camera {camera_id}")
        
        # Parse time parameters
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
        else:
            start_dt = datetime.now() - timedelta(days=1)  # Default to last 24 hours
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
        else:
            end_dt = datetime.now()
        
        # Query segments
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT filename, start_time, end_time, duration, file_size
            FROM segments 
            WHERE datetime(start_time) >= datetime(?) 
            AND datetime(start_time) <= datetime(?)
            ORDER BY start_time DESC
            LIMIT ?
        ''', (start_dt.isoformat(), end_dt.isoformat(), limit))
        
        segments = []
        for row in cursor.fetchall():
            segments.append({
                "filename": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "duration": row[3],
                "file_size": row[4],
                "file_size_formatted": _format_bytes(row[4]) if row[4] else "0 B"
            })
        
        conn.close()
        
        return {
            "camera_id": camera_id,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "total_segments": len(segments),
            "segments": segments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting segments for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage/report")
async def get_storage_report():
    """Get comprehensive storage report"""
    try:
        camera_dirs = [d for d in RECORDINGS_BASE_PATH.iterdir() if d.is_dir() and d.name.startswith('camera_')]
        
        # System totals
        total_segments = 0
        total_size = 0
        camera_stats = {}
        oldest_recording = None
        newest_recording = None
        
        for camera_dir in camera_dirs:
            camera_id = int(camera_dir.name.split('_')[1])
            db_path = camera_dir / "index.db"
            
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    
                    # Get camera stats
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as segments,
                            SUM(file_size) as total_size,
                            MIN(start_time) as oldest,
                            MAX(start_time) as newest
                        FROM segments
                    ''')
                    
                    result = cursor.fetchone()
                    if result:
                        cam_segments = result[0] or 0
                        cam_size = result[1] or 0
                        cam_oldest = result[2]
                        cam_newest = result[3]
                        
                        total_segments += cam_segments
                        total_size += cam_size
                        
                        # Update global oldest/newest
                        if cam_oldest and (not oldest_recording or cam_oldest < oldest_recording):
                            oldest_recording = cam_oldest
                        if cam_newest and (not newest_recording or cam_newest > newest_recording):
                            newest_recording = cam_newest
                        
                        camera_stats[camera_id] = {
                            "segments": cam_segments,
                            "size_bytes": cam_size,
                            "size_formatted": _format_bytes(cam_size),
                            "oldest_recording": cam_oldest,
                            "newest_recording": cam_newest
                        }
                    
                    conn.close()
                    
                except Exception as e:
                    logger.error(f"Error getting stats for camera {camera_id}: {e}")
        
        # Get disk usage
        disk_usage = shutil.disk_usage(RECORDINGS_BASE_PATH)
        
        return {
            "system_stats": {
                "total_segments": total_segments,
                "total_size_bytes": total_size,
                "total_size_formatted": _format_bytes(total_size),
                "oldest_recording": oldest_recording,
                "newest_recording": newest_recording,
                "total_cameras": len(camera_stats)
            },
            "disk_usage": {
                "total_bytes": disk_usage.total,
                "used_bytes": disk_usage.used,
                "free_bytes": disk_usage.free,
                "free_percent": round((disk_usage.free / disk_usage.total) * 100, 1),
                "total_formatted": _format_bytes(disk_usage.total),
                "used_formatted": _format_bytes(disk_usage.used),
                "free_formatted": _format_bytes(disk_usage.free)
            },
            "camera_stats": camera_stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating storage report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_camera_status(camera_id: int) -> Optional[Dict]:
    """Get status for a specific camera"""
    camera_dir = RECORDINGS_BASE_PATH / f"camera_{camera_id}"
    
    if not camera_dir.exists():
        return None
    
    db_path = camera_dir / "index.db"
    if not db_path.exists():
        return None
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('''
            SELECT 
                COUNT(*) as segments,
                SUM(file_size) as total_size,
                MAX(start_time) as last_segment
            FROM segments
        ''')
        
        result = cursor.fetchone()
        segments = result[0] or 0
        total_size = result[1] or 0
        last_segment = result[2]
        
        # Check if actively recording (last segment within 15 minutes)
        is_active = False
        if last_segment:
            last_time = datetime.fromisoformat(last_segment)
            is_active = (datetime.now() - last_time).total_seconds() < 900
        
        # Get recent segments (last 10)
        cursor.execute('''
            SELECT filename, start_time, file_size
            FROM segments 
            ORDER BY start_time DESC 
            LIMIT 10
        ''')
        
        recent_segments = []
        for row in cursor.fetchall():
            recent_segments.append({
                "filename": row[0],
                "start_time": row[1],
                "file_size": row[2]
            })
        
        conn.close()
        
        return {
            "camera_id": camera_id,
            "is_active": is_active,
            "total_segments": segments,
            "total_size_bytes": total_size,
            "total_size_formatted": _format_bytes(total_size),
            "last_segment_time": last_segment,
            "recent_segments": recent_segments,
            "storage_path": str(camera_dir)
        }
        
    except Exception as e:
        logger.error(f"Error getting status for camera {camera_id}: {e}")
        return None


def _format_bytes(bytes_size: int) -> str:
    """Format bytes as human readable string"""
    if bytes_size == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while bytes_size >= 1024 and i < len(units) - 1:
        bytes_size /= 1024
        i += 1
    
    return f"{bytes_size:.1f} {units[i]}"


if __name__ == "__main__":
    import uvicorn
    
    # Ensure directories exist
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Starting 24/7 Recording API Service on port 8002...")
    
    # Run the API service
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        reload=False
    )