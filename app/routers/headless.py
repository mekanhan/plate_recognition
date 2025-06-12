"""
Headless API endpoints for background processing control and monitoring.

These endpoints provide API access to the background processing system
for headless deployments and microservice integration.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

class ProcessingStatus(BaseModel):
    """Background processing status model."""
    is_running: bool
    is_paused: bool
    uptime_seconds: float
    total_frames_processed: int
    total_detections: int
    processing_time_ms: float
    errors: int
    queue_size: int
    services_available: bool

class OutputChannelStats(BaseModel):
    """Output channel statistics model."""
    total_outputs_sent: int
    api_buffer_size: int
    websocket_connections: int
    pending_webhooks: int
    channels: Dict[str, Dict[str, Any]]

class DetectionResult(BaseModel):
    """Detection result model for API responses."""
    detection_id: str
    timestamp: float
    plate_text: Optional[str]
    confidence: float
    frame_number: int

class SystemHealthResponse(BaseModel):
    """System health status response."""
    status: str
    background_processing: ProcessingStatus
    output_channels: OutputChannelStats
    last_detection_time: Optional[float]
    timestamp: float

def get_background_manager(request: Request):
    """Get background stream manager from app state."""
    if not hasattr(request.app.state, 'background_stream_manager'):
        raise HTTPException(status_code=503, detail="Background stream manager not available")
    return request.app.state.background_stream_manager

def get_output_manager(request: Request):
    """Get output channel manager from app state."""
    if not hasattr(request.app.state, 'output_manager'):
        raise HTTPException(status_code=503, detail="Output manager not available")
    return request.app.state.output_manager

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    request: Request,
    background_manager = Depends(get_background_manager),
    output_manager = Depends(get_output_manager)
):
    """
    Get comprehensive system health status.
    
    Returns current status of background processing, output channels,
    and recent detection activity.
    """
    try:
        # Get background processing status
        bg_status = background_manager.get_status()
        processing_status = ProcessingStatus(
            is_running=bg_status["is_running"],
            is_paused=bg_status["is_paused"],
            uptime_seconds=bg_status["uptime_seconds"],
            total_frames_processed=bg_status["stats"]["total_frames_processed"],
            total_detections=bg_status["stats"]["total_detections"],
            processing_time_ms=bg_status["stats"]["processing_time_ms"],
            errors=bg_status["stats"]["errors"],
            queue_size=bg_status["queue_size"],
            services_available=bg_status["services_available"]
        )
        
        # Get output channel stats
        output_stats = output_manager.get_stats()
        output_channel_stats = OutputChannelStats(
            total_outputs_sent=output_stats["total_outputs_sent"],
            api_buffer_size=output_stats["api_buffer_size"],
            websocket_connections=output_stats["websocket_connections"],
            pending_webhooks=output_stats["pending_webhooks"],
            channels=output_stats["channels"]
        )
        
        # Determine overall status
        if not processing_status.is_running:
            overall_status = "stopped"
        elif processing_status.errors > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return SystemHealthResponse(
            status=overall_status,
            background_processing=processing_status,
            output_channels=output_channel_stats,
            last_detection_time=bg_status["stats"]["last_detection_time"],
            timestamp=time.time()
        )
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")

@router.get("/status")
async def get_processing_status(background_manager = Depends(get_background_manager)):
    """
    Get background processing status and statistics.
    
    Returns detailed information about the background processing state,
    performance metrics, and configuration.
    """
    try:
        status = background_manager.get_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")

@router.post("/control/start")
async def start_processing(background_manager = Depends(get_background_manager)):
    """Start background processing."""
    try:
        success = await background_manager.start()
        if success:
            return {"message": "Background processing started", "status": "success"}
        else:
            raise HTTPException(status_code=400, detail="Failed to start processing")
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start processing")

@router.post("/control/stop")
async def stop_processing(background_manager = Depends(get_background_manager)):
    """Stop background processing."""
    try:
        success = await background_manager.stop()
        if success:
            return {"message": "Background processing stopped", "status": "success"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop processing")
    except Exception as e:
        logger.error(f"Error stopping processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop processing")

@router.post("/control/pause")
async def pause_processing(background_manager = Depends(get_background_manager)):
    """Pause background processing."""
    try:
        success = await background_manager.pause()
        if success:
            return {"message": "Background processing paused", "status": "success"}
        else:
            raise HTTPException(status_code=400, detail="Failed to pause processing")
    except Exception as e:
        logger.error(f"Error pausing processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause processing")

@router.post("/control/resume")
async def resume_processing(background_manager = Depends(get_background_manager)):
    """Resume background processing."""
    try:
        success = await background_manager.resume()
        if success:
            return {"message": "Background processing resumed", "status": "success"}
        else:
            raise HTTPException(status_code=400, detail="Failed to resume processing")
    except Exception as e:
        logger.error(f"Error resuming processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume processing")

@router.get("/detections/recent")
async def get_recent_detections(
    limit: int = 50,
    output_manager = Depends(get_output_manager)
):
    """
    Get recent detection results from the API buffer.
    
    Args:
        limit: Maximum number of detections to return (default: 50, max: 1000)
    
    Returns:
        List of recent detection results
    """
    try:
        # Validate limit
        if limit > 1000:
            limit = 1000
        
        # Get recent detections from API buffer
        recent_detections = output_manager.get_api_buffer(limit=limit)
        
        # Format for API response
        formatted_detections = []
        for detection_data in recent_detections:
            detection = detection_data["detection"]
            formatted_detections.append(DetectionResult(
                detection_id=detection_data["detection_id"],
                timestamp=detection_data["timestamp"],
                plate_text=detection.get("plate_text"),
                confidence=detection.get("confidence", 0.0),
                frame_number=detection_data.get("frame_number", 0)
            ))
        
        return {
            "detections": formatted_detections,
            "count": len(formatted_detections),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error getting recent detections: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent detections")

@router.delete("/detections/clear")
async def clear_detection_buffer(output_manager = Depends(get_output_manager)):
    """Clear the API detection buffer."""
    try:
        output_manager.clear_api_buffer()
        return {"message": "Detection buffer cleared", "status": "success"}
    except Exception as e:
        logger.error(f"Error clearing detection buffer: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear detection buffer")

@router.get("/metrics")
async def get_metrics(
    background_manager = Depends(get_background_manager),
    output_manager = Depends(get_output_manager)
):
    """
    Get detailed performance metrics.
    
    Returns comprehensive metrics for monitoring and analytics.
    """
    try:
        bg_status = background_manager.get_status()
        output_stats = output_manager.get_stats()
        
        # Calculate additional metrics
        uptime = bg_status["uptime_seconds"]
        total_frames = bg_status["stats"]["total_frames_processed"]
        total_detections = bg_status["stats"]["total_detections"]
        
        metrics = {
            "performance": {
                "uptime_seconds": uptime,
                "uptime_hours": uptime / 3600,
                "total_frames_processed": total_frames,
                "total_detections": total_detections,
                "frames_per_second": total_frames / max(uptime, 1),
                "detections_per_hour": (total_detections / max(uptime, 1)) * 3600,
                "detection_rate_percent": (total_detections / max(total_frames, 1)) * 100,
                "average_processing_time_ms": bg_status["stats"]["processing_time_ms"],
                "error_count": bg_status["stats"]["errors"],
                "error_rate_percent": (bg_status["stats"]["errors"] / max(total_frames, 1)) * 100
            },
            "output_channels": output_stats,
            "system": {
                "is_running": bg_status["is_running"],
                "is_paused": bg_status["is_paused"],
                "services_available": bg_status["services_available"],
                "queue_size": bg_status["queue_size"],
                "last_health_check": bg_status["last_health_check"]
            },
            "timestamp": time.time()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.put("/config")
async def update_configuration(
    config_update: Dict[str, Any],
    background_manager = Depends(get_background_manager),
    output_manager = Depends(get_output_manager)
):
    """
    Update system configuration.
    
    Allows runtime configuration changes for background processing
    and output channel settings.
    """
    try:
        updated_items = []
        
        # Update background processing config
        bg_config = {}
        bg_keys = ["frame_skip", "processing_interval", "max_queue_size", "health_check_interval"]
        for key in bg_keys:
            if key in config_update:
                bg_config[key] = config_update[key]
                updated_items.append(f"background.{key}")
        
        if bg_config:
            background_manager.update_config(bg_config)
        
        # Update output channel config
        output_config = {}
        output_keys = ["api_buffer_max_size", "webhook_timeout", "webhook_retry_count", "batch_size"]
        for key in output_keys:
            if key in config_update:
                output_config[key] = config_update[key]
                updated_items.append(f"output.{key}")
        
        if output_config:
            output_manager.update_config(output_config)
        
        return {
            "message": f"Configuration updated: {', '.join(updated_items)}",
            "updated_items": updated_items,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@router.get("/info")
async def get_system_info():
    """
    Get basic system information.
    
    Returns version, deployment mode, and capability information.
    """
    try:
        import os
        from config.settings import Config as AppConfig
        
        app_config = AppConfig()
        
        return {
            "service": "License Plate Recognition System",
            "version": "1.0.0",
            "mode": "headless" if app_config.is_headless_mode else "hybrid",
            "capabilities": {
                "background_processing": app_config.is_background_processing_enabled,
                "web_ui": app_config.is_web_ui_enabled,
                "storage_output": app_config.enable_storage_output,
                "api_output": app_config.enable_api_output,
                "websocket_output": app_config.enable_websocket_output,
                "webhook_output": app_config.enable_webhook_output
            },
            "endpoints": {
                "health": "/api/headless/health",
                "status": "/api/headless/status",
                "recent_detections": "/api/headless/detections/recent",
                "metrics": "/api/headless/metrics",
                "control": "/api/headless/control/{start|stop|pause|resume}"
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system info")