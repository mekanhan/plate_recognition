# app/routers/websocket_router.py
# WebSocket endpoints for real-time multi-camera feeds
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
import asyncio
import json

from app.services.websocket_manager import WebSocketMultiplexer

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Service instance (will be injected)
websocket_multiplexer: Optional[WebSocketMultiplexer] = None

@router.websocket("/camera-feeds")
async def websocket_camera_feeds_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for camera feeds (used by JavaScript client)"""
    if not websocket_multiplexer:
        await websocket.close(code=1011, reason="WebSocket service not available")
        return
    
    client_id = None
    
    try:
        # Extract client information
        client_info = {
            "user_agent": websocket.headers.get("user-agent"),
            "remote_address": websocket.client.host if websocket.client else "unknown"
        }
        
        # Connect client
        client_id = await websocket_multiplexer.connect_client(websocket, client_info)
        logger.info(f"Camera feeds WebSocket client connected: {client_id}")
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                await websocket_multiplexer.handle_client_message(client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Camera feeds client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling message from camera feeds client {client_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"Camera feeds WebSocket connection error: {e}")
    
    finally:
        if client_id:
            await websocket_multiplexer.disconnect_client(client_id)

@router.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for dashboard connections"""
    if not websocket_multiplexer:
        await websocket.close(code=1011, reason="WebSocket service not available")
        return
    
    client_id = None
    
    try:
        # Extract client information
        client_info = {
            "user_agent": websocket.headers.get("user-agent"),
            "remote_address": websocket.client.host if websocket.client else "unknown"
        }
        
        # Connect client
        client_id = await websocket_multiplexer.connect_client(websocket, client_info)
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                await websocket_multiplexer.handle_client_message(client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        if client_id:
            await websocket_multiplexer.disconnect_client(client_id)

@router.websocket("/ws/camera/{camera_id}")
async def websocket_camera_endpoint(websocket: WebSocket, camera_id: str):
    """WebSocket endpoint for single camera feed"""
    if not websocket_multiplexer:
        await websocket.close(code=1011, reason="WebSocket service not available")
        return
    
    client_id = None
    
    try:
        # Extract client information
        client_info = {
            "user_agent": websocket.headers.get("user-agent"),
            "remote_address": websocket.client.host if websocket.client else "unknown"
        }
        
        # Connect client
        client_id = await websocket_multiplexer.connect_client(websocket, client_info)
        
        # Auto-subscribe to camera frames for this camera
        subscribe_message = {
            "type": "subscribe",
            "subscription": "camera_frames",
            "camera_ids": [camera_id]
        }
        
        await websocket_multiplexer.handle_client_message(client_id, json.dumps(subscribe_message))
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                await websocket_multiplexer.handle_client_message(client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected from camera {camera_id}")
                break
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error for camera {camera_id}: {e}")
    
    finally:
        if client_id:
            await websocket_multiplexer.disconnect_client(client_id)

@router.websocket("/ws/detections")
async def websocket_detections_endpoint(websocket: WebSocket):
    """WebSocket endpoint for detection results only"""
    if not websocket_multiplexer:
        await websocket.close(code=1011, reason="WebSocket service not available")
        return
    
    client_id = None
    
    try:
        # Extract client information
        client_info = {
            "user_agent": websocket.headers.get("user-agent"),
            "remote_address": websocket.client.host if websocket.client else "unknown"
        }
        
        # Connect client
        client_id = await websocket_multiplexer.connect_client(websocket, client_info)
        
        # Auto-subscribe to detection results
        subscribe_message = {
            "type": "subscribe",
            "subscription": "detection_results",
            "camera_ids": []  # All cameras
        }
        
        await websocket_multiplexer.handle_client_message(client_id, json.dumps(subscribe_message))
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                await websocket_multiplexer.handle_client_message(client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected from detections feed")
                break
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error for detections: {e}")
    
    finally:
        if client_id:
            await websocket_multiplexer.disconnect_client(client_id)

@router.websocket("/ws/system")
async def websocket_system_endpoint(websocket: WebSocket):
    """WebSocket endpoint for system statistics only"""
    if not websocket_multiplexer:
        await websocket.close(code=1011, reason="WebSocket service not available")
        return
    
    client_id = None
    
    try:
        # Extract client information
        client_info = {
            "user_agent": websocket.headers.get("user-agent"),
            "remote_address": websocket.client.host if websocket.client else "unknown"
        }
        
        # Connect client
        client_id = await websocket_multiplexer.connect_client(websocket, client_info)
        
        # Auto-subscribe to system stats
        subscribe_message = {
            "type": "subscribe",
            "subscription": "system_stats",
            "camera_ids": []
        }
        
        await websocket_multiplexer.handle_client_message(client_id, json.dumps(subscribe_message))
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                await websocket_multiplexer.handle_client_message(client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected from system feed")
                break
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error for system: {e}")
    
    finally:
        if client_id:
            await websocket_multiplexer.disconnect_client(client_id)

# HTTP endpoints for WebSocket management
@router.get("/stats", response_model=Dict[str, Any])
async def get_websocket_stats():
    """Get WebSocket multiplexer statistics"""
    try:
        if not websocket_multiplexer:
            raise HTTPException(status_code=503, detail="WebSocket service not available")
        
        stats = websocket_multiplexer.get_multiplexer_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients", response_model=Dict[str, Any])
async def get_websocket_clients():
    """Get information about connected WebSocket clients"""
    try:
        if not websocket_multiplexer:
            raise HTTPException(status_code=503, detail="WebSocket service not available")
        
        clients_info = []
        for client_id, client in websocket_multiplexer.clients.items():
            clients_info.append({
                "client_id": client_id,
                "subscriptions": [sub.value for sub in client.subscriptions],
                "subscribed_cameras": list(client.subscribed_cameras),
                "connected_at": client.connected_at,
                "last_ping": client.last_ping,
                "is_active": client.is_active,
                "user_agent": client.user_agent,
                "remote_address": client.remote_address
            })
        
        return {
            "total_clients": len(clients_info),
            "clients": clients_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast/detection", response_model=Dict[str, str])
async def broadcast_detection_result(detection_data: Dict[str, Any]):
    """Manually broadcast a detection result to WebSocket clients"""
    try:
        if not websocket_multiplexer:
            raise HTTPException(status_code=503, detail="WebSocket service not available")
        
        await websocket_multiplexer.broadcast_detection_result(detection_data)
        
        return {"message": "Detection result broadcasted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to broadcast detection result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast/status", response_model=Dict[str, str])
async def broadcast_camera_status(camera_id: str, status_data: Dict[str, Any]):
    """Manually broadcast camera status to WebSocket clients"""
    try:
        if not websocket_multiplexer:
            raise HTTPException(status_code=503, detail="WebSocket service not available")
        
        await websocket_multiplexer.broadcast_camera_status(camera_id, status_data)
        
        return {"message": "Camera status broadcasted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to broadcast camera status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast/system", response_model=Dict[str, str])
async def broadcast_system_stats(stats_data: Dict[str, Any]):
    """Manually broadcast system statistics to WebSocket clients"""
    try:
        if not websocket_multiplexer:
            raise HTTPException(status_code=503, detail="WebSocket service not available")
        
        await websocket_multiplexer.broadcast_system_stats(stats_data)
        
        return {"message": "System statistics broadcasted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to broadcast system statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function for dependency injection
def get_websocket_multiplexer():
    if not websocket_multiplexer:
        raise HTTPException(status_code=503, detail="WebSocket service not available")
    return websocket_multiplexer