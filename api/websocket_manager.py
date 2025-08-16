"""
WebSocket Connection Manager
Handles real-time communication with frontend clients for live updates
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class WebSocketMessage:
    """Structured message for WebSocket communication"""
    type: str
    payload: Dict[str, Any]
    timestamp: str = None
    client_id: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self))

class WebSocketClient:
    """Represents a connected WebSocket client"""
    
    def __init__(self, websocket: WebSocket, client_id: str = None):
        self.websocket = websocket
        self.client_id = client_id or str(uuid.uuid4())
        self.connected_at = datetime.now()
        self.last_ping = None
        self.subscriptions: Set[str] = set()
        
    async def send_message(self, message: WebSocketMessage) -> bool:
        """Send message to client, return True if successful"""
        try:
            message.client_id = self.client_id
            await self.websocket.send_text(message.to_json())
            return True
        except Exception as e:
            logger.error(f"Failed to send message to client {self.client_id}: {e}")
            return False
    
    async def send_ping(self) -> bool:
        """Send ping to client for heartbeat"""
        ping_message = WebSocketMessage(
            type="heartbeat",
            payload={"status": "ping"}
        )
        success = await self.send_message(ping_message)
        if success:
            self.last_ping = datetime.now()
        return success

class WebSocketConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        # Active connections: client_id -> WebSocketClient
        self.active_connections: Dict[str, WebSocketClient] = {}
        
        # Event subscriptions: event_type -> set of client_ids
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # Message history for replay (limited size)
        self.message_history: List[WebSocketMessage] = []
        self.max_history = 100
        
        # Heartbeat task
        self.heartbeat_task = None
        self.heartbeat_interval = 30  # seconds
        
        logger.info("WebSocket Connection Manager initialized")

    async def connect(self, websocket: WebSocket) -> str:
        """Accept new WebSocket connection and return client ID"""
        await websocket.accept()
        
        client = WebSocketClient(websocket)
        self.active_connections[client.client_id] = client
        
        logger.info(f"WebSocket client connected: {client.client_id}")
        logger.info(f"Total active connections: {len(self.active_connections)}")
        
        # Start heartbeat if this is the first connection
        if len(self.active_connections) == 1 and not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Send connection confirmation
        welcome_message = WebSocketMessage(
            type="connection",
            payload={
                "status": "connected",
                "client_id": client.client_id,
                "server_time": datetime.now().isoformat()
            }
        )
        await client.send_message(welcome_message)
        
        return client.client_id

    async def disconnect(self, client_id: str):
        """Disconnect and cleanup client"""
        if client_id in self.active_connections:
            client = self.active_connections[client_id]
            
            # Remove from all subscriptions
            for event_type in list(self.subscriptions.keys()):
                self.subscriptions[event_type].discard(client_id)
                if not self.subscriptions[event_type]:
                    del self.subscriptions[event_type]
            
            # Remove connection
            del self.active_connections[client_id]
            
            logger.info(f"WebSocket client disconnected: {client_id}")
            logger.info(f"Total active connections: {len(self.active_connections)}")
            
            # Stop heartbeat if no connections left
            if not self.active_connections and self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None

    async def subscribe(self, client_id: str, event_type: str):
        """Subscribe client to specific event type"""
        if client_id not in self.active_connections:
            return False
            
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = set()
        
        self.subscriptions[event_type].add(client_id)
        self.active_connections[client_id].subscriptions.add(event_type)
        
        logger.debug(f"Client {client_id} subscribed to {event_type}")
        return True

    async def unsubscribe(self, client_id: str, event_type: str):
        """Unsubscribe client from specific event type"""
        if event_type in self.subscriptions:
            self.subscriptions[event_type].discard(client_id)
            
        if client_id in self.active_connections:
            self.active_connections[client_id].subscriptions.discard(event_type)
        
        logger.debug(f"Client {client_id} unsubscribed from {event_type}")

    async def broadcast_to_subscribers(self, event_type: str, payload: Dict[str, Any]) -> int:
        """Broadcast message to all subscribers of an event type"""
        if event_type not in self.subscriptions:
            return 0
        
        message = WebSocketMessage(
            type=event_type,
            payload=payload
        )
        
        # Add to history
        self._add_to_history(message)
        
        # Send to subscribers
        subscribers = self.subscriptions[event_type].copy()  # Copy to avoid modification during iteration
        successful_sends = 0
        failed_clients = []
        
        for client_id in subscribers:
            if client_id in self.active_connections:
                client = self.active_connections[client_id]
                success = await client.send_message(message)
                if success:
                    successful_sends += 1
                else:
                    failed_clients.append(client_id)
        
        # Clean up failed connections
        for client_id in failed_clients:
            await self.disconnect(client_id)
        
        if subscribers:
            logger.debug(f"Broadcast {event_type} to {successful_sends}/{len(subscribers)} clients")
        
        return successful_sends

    async def broadcast_to_all(self, message_type: str, payload: Dict[str, Any]) -> int:
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return 0
        
        message = WebSocketMessage(
            type=message_type,
            payload=payload
        )
        
        # Add to history
        self._add_to_history(message)
        
        successful_sends = 0
        failed_clients = []
        
        for client_id, client in self.active_connections.items():
            success = await client.send_message(message)
            if success:
                successful_sends += 1
            else:
                failed_clients.append(client_id)
        
        # Clean up failed connections
        for client_id in failed_clients:
            await self.disconnect(client_id)
        
        logger.debug(f"Broadcast to {successful_sends}/{len(self.active_connections)} clients")
        return successful_sends

    async def send_to_client(self, client_id: str, message_type: str, payload: Dict[str, Any]) -> bool:
        """Send message to specific client"""
        if client_id not in self.active_connections:
            return False
        
        message = WebSocketMessage(
            type=message_type,
            payload=payload
        )
        
        client = self.active_connections[client_id]
        return await client.send_message(message)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "subscriptions": {event: len(clients) for event, clients in self.subscriptions.items()},
            "history_size": len(self.message_history),
            "heartbeat_active": bool(self.heartbeat_task and not self.heartbeat_task.done())
        }

    def _add_to_history(self, message: WebSocketMessage):
        """Add message to history with size limit"""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)

    async def _heartbeat_loop(self):
        """Background heartbeat to maintain connections"""
        while self.active_connections:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send ping to all clients
                failed_clients = []
                for client_id, client in self.active_connections.items():
                    success = await client.send_ping()
                    if not success:
                        failed_clients.append(client_id)
                
                # Clean up failed connections
                for client_id in failed_clients:
                    await self.disconnect(client_id)
                
                if self.active_connections:
                    logger.debug(f"Heartbeat sent to {len(self.active_connections)} clients")
                
            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def handle_client_message(self, client_id: str, message_data: dict):
        """Handle incoming message from client"""
        message_type = message_data.get("type", "unknown")
        payload = message_data.get("payload", {})
        
        logger.debug(f"Received message from {client_id}: {message_type}")
        
        if message_type == "ping":
            # Respond to client ping
            await self.send_to_client(client_id, "pong", {"timestamp": datetime.now().isoformat()})
            
        elif message_type == "subscribe":
            # Subscribe to event type
            event_type = payload.get("event_type")
            if event_type:
                await self.subscribe(client_id, event_type)
                await self.send_to_client(client_id, "subscription_confirmed", {"event_type": event_type})
            
        elif message_type == "unsubscribe":
            # Unsubscribe from event type
            event_type = payload.get("event_type")
            if event_type:
                await self.unsubscribe(client_id, event_type)
                await self.send_to_client(client_id, "unsubscription_confirmed", {"event_type": event_type})
            
        elif message_type == "request_camera_status":
            # Request specific camera status (will be handled by the endpoint)
            pass
            
        elif message_type == "request_all_status":
            # Request all camera statuses (will be handled by the endpoint)
            pass
        
        else:
            logger.warning(f"Unknown message type from client {client_id}: {message_type}")

# Global instance
websocket_manager = WebSocketConnectionManager()

# Event broadcasting functions for easy use throughout the application
async def broadcast_camera_status(camera_id: str, status: str, details: Dict[str, Any] = None):
    """Broadcast camera status update"""
    payload = {
        "camera_id": camera_id,
        "status": status,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    return await websocket_manager.broadcast_to_subscribers("camera_status", payload)

async def broadcast_recording_status(camera_id: str, is_recording: bool, details: Dict[str, Any] = None):
    """Broadcast recording status update"""
    payload = {
        "camera_id": camera_id,
        "is_recording": is_recording,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    return await websocket_manager.broadcast_to_subscribers("recording_status", payload)

async def broadcast_motion_detection(camera_id: str, detected: bool, zone: str = None, confidence: float = None):
    """Broadcast motion detection event"""
    payload = {
        "camera_id": camera_id,
        "detected": detected,
        "zone": zone,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }
    return await websocket_manager.broadcast_to_subscribers("motion_detection", payload)

async def broadcast_system_health(health_data: Dict[str, Any]):
    """Broadcast system health update"""
    payload = {
        **health_data,
        "timestamp": datetime.now().isoformat()
    }
    return await websocket_manager.broadcast_to_subscribers("system_health", payload)

async def broadcast_universal_detection(detection: Dict[str, Any]):
    """Broadcast universal detection event"""
    payload = {
        "detection_id": detection["id"],
        "camera_id": detection["camera_id"],
        "object_type": detection["object_type"],
        "confidence": detection["confidence"],
        "detected_at": detection["detected_at"].isoformat() if hasattr(detection["detected_at"], 'isoformat') else detection["detected_at"],
        "bbox": detection["bbox"],
        "metadata": detection.get("metadata", {}),
        "status": detection.get("status", "unverified"),
        "processing_time_ms": detection.get("processing_time_ms", 0),
        "timestamp": datetime.now().isoformat()
    }
    return await websocket_manager.broadcast_to_subscribers("universal_detection", payload)

async def broadcast_object_type_stats(stats: Dict[str, Any]):
    """Broadcast object type statistics update"""
    payload = {
        **stats,
        "timestamp": datetime.now().isoformat()
    }
    return await websocket_manager.broadcast_to_subscribers("detection_stats", payload)