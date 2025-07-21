# app/services/websocket_manager.py
# WebSocket multiplexing service for real-time multi-camera feeds
import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import base64

from app.services.multi_camera_service import MultiCameraService
from app.services.multi_stream_processor import MultiStreamProcessor
from app.services.gpu_resource_manager import GPUResourceManager

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    CAMERA_FRAME = "camera_frame"
    CAMERA_FRAME_BINARY = "camera_frame_binary"
    CAMERA_STATUS = "camera_status"
    DETECTION_RESULT = "detection_result"
    SYSTEM_STATS = "system_stats"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    CAMERA_LIST = "camera_list"
    PROCESSING_STATS = "processing_stats"

class SubscriptionType(Enum):
    """Types of subscriptions clients can request"""
    CAMERA_FRAMES = "camera_frames"
    CAMERA_STATUS = "camera_status"
    DETECTION_RESULTS = "detection_results"
    SYSTEM_STATS = "system_stats"
    PROCESSING_STATS = "processing_stats"
    ALL = "all"

@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client"""
    client_id: str
    websocket: WebSocket
    subscriptions: Set[SubscriptionType] = field(default_factory=set)
    subscribed_cameras: Set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    is_active: bool = True
    user_agent: Optional[str] = None
    remote_address: Optional[str] = None
    
    # Enhanced streaming options
    binary_mode: bool = False
    compression_enabled: bool = True
    max_frame_size: int = 1024 * 1024  # 1MB
    quality_preference: str = "balanced"  # low, balanced, high
    frame_rate_limit: int = 30  # Max FPS per client

@dataclass
class WebSocketMessage:
    """Standard WebSocket message format"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    client_id: Optional[str] = None
    camera_id: Optional[str] = None

class WebSocketMultiplexer:
    """
    WebSocket multiplexing service for real-time multi-camera feeds
    Manages multiple WebSocket connections and distributes camera feeds,
    detection results, and system status to subscribed clients
    """
    
    def __init__(self, 
                 multi_camera_service: MultiCameraService,
                 multi_stream_processor: MultiStreamProcessor,
                 gpu_resource_manager: GPUResourceManager):
        self.multi_camera_service = multi_camera_service
        self.multi_stream_processor = multi_stream_processor
        self.gpu_resource_manager = gpu_resource_manager
        
        # Client management
        self.clients: Dict[str, WebSocketClient] = {}
        self.camera_subscribers: Dict[str, Set[str]] = {}  # camera_id -> set of client_ids
        self.subscription_callbacks: Dict[SubscriptionType, Callable] = {}
        
        # Background tasks
        self.running = False
        self.frame_broadcaster_task: Optional[asyncio.Task] = None
        self.status_broadcaster_task: Optional[asyncio.Task] = None
        self.ping_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Performance settings
        self.max_clients = 100
        self.frame_rate = 10  # Max FPS for WebSocket streaming
        self.ping_interval = 30  # seconds
        self.cleanup_interval = 60  # seconds
        
        # Enhanced Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "frames_streamed": 0,
            "binary_frames_sent": 0,
            "text_frames_sent": 0,
            "compressed_frames_sent": 0,
            "thumbnail_frames_sent": 0,
            "compression_savings": 0,  # bytes saved through compression
            "average_frame_size": 0,
            "peak_bandwidth": 0,
            "errors": 0
        }
        
        # Frame buffer for efficient streaming
        self.frame_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry = 1.0  # seconds
        
    async def initialize(self) -> None:
        """Initialize the WebSocket multiplexer"""
        logger.info("Initializing WebSocket Multiplexer...")
        
        try:
            # Start background tasks
            self.running = True
            self.frame_broadcaster_task = asyncio.create_task(self._frame_broadcaster_loop())
            self.status_broadcaster_task = asyncio.create_task(self._status_broadcaster_loop())
            self.ping_task = asyncio.create_task(self._ping_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            # Register callbacks
            self._register_callbacks()
            
            logger.info("WebSocket Multiplexer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket Multiplexer: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the WebSocket multiplexer"""
        logger.info("Shutting down WebSocket Multiplexer...")
        
        self.running = False
        
        # Disconnect all clients
        for client_id in list(self.clients.keys()):
            await self._disconnect_client(client_id)
        
        # Cancel background tasks
        for task in [self.frame_broadcaster_task, self.status_broadcaster_task, 
                     self.ping_task, self.cleanup_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("WebSocket Multiplexer shutdown complete")
    
    async def connect_client(self, websocket: WebSocket, client_info: Dict[str, Any] = None) -> str:
        """
        Connect a new WebSocket client
        
        Args:
            websocket: WebSocket connection
            client_info: Optional client information
            
        Returns:
            Client ID
        """
        if len(self.clients) >= self.max_clients:
            await websocket.close(code=1008, reason="Too many connections")
            raise Exception("Maximum number of clients reached")
        
        client_id = str(uuid.uuid4())
        
        try:
            await websocket.accept()
            
            # Create client record
            client = WebSocketClient(
                client_id=client_id,
                websocket=websocket,
                user_agent=client_info.get("user_agent") if client_info else None,
                remote_address=client_info.get("remote_address") if client_info else None
            )
            
            self.clients[client_id] = client
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            # Send welcome message
            await self._send_message(client_id, WebSocketMessage(
                type=MessageType.CAMERA_LIST,
                data={"cameras": await self._get_camera_list()}
            ))
            
            logger.info(f"Client {client_id} connected from {client.remote_address}")
            return client_id
            
        except Exception as e:
            logger.error(f"Failed to connect client: {e}")
            if client_id in self.clients:
                del self.clients[client_id]
            raise
    
    async def disconnect_client(self, client_id: str) -> None:
        """Disconnect a WebSocket client"""
        await self._disconnect_client(client_id)
    
    async def handle_client_message(self, client_id: str, message: str) -> None:
        """
        Handle incoming message from WebSocket client
        
        Args:
            client_id: Client ID
            message: JSON message string
        """
        try:
            data = json.loads(message)
            msg_type = MessageType(data.get("type"))
            
            self.stats["messages_received"] += 1
            
            if msg_type == MessageType.SUBSCRIBE:
                await self._handle_subscribe(client_id, data)
            elif msg_type == MessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe(client_id, data)
            elif msg_type == MessageType.PING:
                await self._handle_ping(client_id)
            else:
                logger.warning(f"Unknown message type from client {client_id}: {msg_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client_id}: {message}")
            await self._send_error(client_id, "Invalid JSON format")
        except ValueError as e:
            logger.error(f"Invalid message type from client {client_id}: {e}")
            await self._send_error(client_id, "Invalid message type")
        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            await self._send_error(client_id, "Internal server error")
    
    async def broadcast_detection_result(self, detection_data: Dict[str, Any]) -> None:
        """Broadcast detection result to subscribed clients"""
        if not detection_data.get("camera_id"):
            return
        
        camera_id = detection_data["camera_id"]
        message = WebSocketMessage(
            type=MessageType.DETECTION_RESULT,
            data=detection_data,
            camera_id=camera_id
        )
        
        await self._broadcast_to_camera_subscribers(camera_id, message, SubscriptionType.DETECTION_RESULTS)
    
    async def broadcast_camera_status(self, camera_id: str, status_data: Dict[str, Any]) -> None:
        """Broadcast camera status update to subscribed clients"""
        message = WebSocketMessage(
            type=MessageType.CAMERA_STATUS,
            data=status_data,
            camera_id=camera_id
        )
        
        await self._broadcast_to_camera_subscribers(camera_id, message, SubscriptionType.CAMERA_STATUS)
    
    async def broadcast_system_stats(self, stats_data: Dict[str, Any]) -> None:
        """Broadcast system statistics to subscribed clients"""
        message = WebSocketMessage(
            type=MessageType.SYSTEM_STATS,
            data=stats_data
        )
        
        await self._broadcast_to_subscribers(message, SubscriptionType.SYSTEM_STATS)
    
    def get_multiplexer_stats(self) -> Dict[str, Any]:
        """Get enhanced WebSocket multiplexer statistics"""
        # Calculate client statistics
        binary_clients = sum(1 for client in self.clients.values() if client.binary_mode)
        total_clients = len(self.clients)
        
        # Calculate bandwidth efficiency
        total_frames = self.stats["binary_frames_sent"] + self.stats["text_frames_sent"]
        compression_ratio = (
            self.stats["compression_savings"] / max(self.stats["bytes_sent"], 1) * 100
            if self.stats["bytes_sent"] > 0 else 0
        )
        
        return {
            **self.stats,
            "active_clients": total_clients,
            "binary_clients": binary_clients,
            "text_clients": total_clients - binary_clients,
            "binary_adoption_rate": (binary_clients / max(total_clients, 1)) * 100,
            "compression_ratio_percent": compression_ratio,
            "average_frame_size_kb": self.stats["average_frame_size"] / 1024,
            "peak_bandwidth_kb": self.stats["peak_bandwidth"] / 1024,
            "total_data_saved_mb": self.stats["compression_savings"] / (1024 * 1024),
            "camera_subscribers": {
                camera_id: len(subscribers) 
                for camera_id, subscribers in self.camera_subscribers.items()
            },
            "subscription_counts": {
                subscription.value: sum(
                    1 for client in self.clients.values() 
                    if subscription in client.subscriptions
                )
                for subscription in SubscriptionType
            },
            "client_preferences": {
                "binary_mode": binary_clients,
                "quality_low": sum(1 for c in self.clients.values() if c.quality_preference == "low"),
                "quality_balanced": sum(1 for c in self.clients.values() if c.quality_preference == "balanced"),
                "quality_high": sum(1 for c in self.clients.values() if c.quality_preference == "high"),
                "compression_enabled": sum(1 for c in self.clients.values() if c.compression_enabled)
            }
        }
    
    async def _disconnect_client(self, client_id: str) -> None:
        """Internal method to disconnect a client"""
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        
        try:
            # Remove from camera subscriptions
            for camera_id, subscribers in self.camera_subscribers.items():
                subscribers.discard(client_id)
            
            # Close WebSocket connection
            if client.websocket and client.is_active:
                await client.websocket.close()
            
            # Remove from clients
            del self.clients[client_id]
            self.stats["active_connections"] -= 1
            
            logger.info(f"Client {client_id} disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting client {client_id}: {e}")
    
    async def _handle_subscribe(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle subscription request from client with enhanced options"""
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        
        try:
            subscription_type = SubscriptionType(data.get("subscription"))
            camera_ids = data.get("camera_ids", [])
            
            # Handle streaming preferences for camera frame subscriptions
            if subscription_type == SubscriptionType.CAMERA_FRAMES:
                # Update client streaming preferences
                streaming_options = data.get("streaming_options", {})
                client.binary_mode = streaming_options.get("binary_mode", False)
                client.compression_enabled = streaming_options.get("compression_enabled", True)
                client.quality_preference = streaming_options.get("quality_preference", "balanced")
                client.frame_rate_limit = min(streaming_options.get("frame_rate_limit", 30), 60)
                client.max_frame_size = min(streaming_options.get("max_frame_size", 1024*1024), 5*1024*1024)
                
                logger.debug(f"Client {client_id} streaming preferences: binary={client.binary_mode}, "
                           f"quality={client.quality_preference}, fps_limit={client.frame_rate_limit}")
            
            # Add subscription
            client.subscriptions.add(subscription_type)
            
            # Add camera subscriptions
            for camera_id in camera_ids:
                client.subscribed_cameras.add(camera_id)
                
                if camera_id not in self.camera_subscribers:
                    self.camera_subscribers[camera_id] = set()
                self.camera_subscribers[camera_id].add(client_id)
            
            # Send confirmation with capabilities
            response_data = {
                "subscription": subscription_type.value,
                "camera_ids": camera_ids,
                "status": "success",
                "capabilities": {
                    "binary_streaming": True,
                    "compression": True,
                    "quality_options": ["low", "balanced", "high"],
                    "max_fps": 60,
                    "max_frame_size": 5*1024*1024
                }
            }
            
            if subscription_type == SubscriptionType.CAMERA_FRAMES:
                response_data["streaming_config"] = {
                    "binary_mode": client.binary_mode,
                    "compression_enabled": client.compression_enabled,
                    "quality_preference": client.quality_preference,
                    "frame_rate_limit": client.frame_rate_limit,
                    "max_frame_size": client.max_frame_size
                }
            
            await self._send_message(client_id, WebSocketMessage(
                type=MessageType.SUBSCRIBE,
                data=response_data
            ))
            
            logger.debug(f"Client {client_id} subscribed to {subscription_type.value} for cameras {camera_ids}")
            
        except ValueError as e:
            await self._send_error(client_id, f"Invalid subscription type: {e}")
        except Exception as e:
            await self._send_error(client_id, f"Subscription failed: {e}")
    
    async def _handle_unsubscribe(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle unsubscription request from client"""
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        
        try:
            subscription_type = SubscriptionType(data.get("subscription"))
            camera_ids = data.get("camera_ids", [])
            
            # Remove subscription
            client.subscriptions.discard(subscription_type)
            
            # Remove camera subscriptions
            for camera_id in camera_ids:
                client.subscribed_cameras.discard(camera_id)
                
                if camera_id in self.camera_subscribers:
                    self.camera_subscribers[camera_id].discard(client_id)
            
            # Send confirmation
            await self._send_message(client_id, WebSocketMessage(
                type=MessageType.UNSUBSCRIBE,
                data={
                    "subscription": subscription_type.value,
                    "camera_ids": camera_ids,
                    "status": "success"
                }
            ))
            
            logger.debug(f"Client {client_id} unsubscribed from {subscription_type.value} for cameras {camera_ids}")
            
        except ValueError as e:
            await self._send_error(client_id, f"Invalid subscription type: {e}")
        except Exception as e:
            await self._send_error(client_id, f"Unsubscription failed: {e}")
    
    async def _handle_ping(self, client_id: str) -> None:
        """Handle ping from client"""
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        client.last_ping = time.time()
        
        await self._send_message(client_id, WebSocketMessage(
            type=MessageType.PONG,
            data={"timestamp": time.time()}
        ))
    
    async def _send_message(self, client_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific client"""
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        
        try:
            message_data = {
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp
            }
            
            if message.camera_id:
                message_data["camera_id"] = message.camera_id
            
            message_json = json.dumps(message_data)
            await client.websocket.send_text(message_json)
            
            self.stats["messages_sent"] += 1
            self.stats["bytes_sent"] += len(message_json)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            await self._disconnect_client(client_id)
            return False
    
    async def _send_error(self, client_id: str, error_message: str) -> None:
        """Send error message to client"""
        await self._send_message(client_id, WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error_message}
        ))
    
    async def _broadcast_to_subscribers(self, message: WebSocketMessage, subscription_type: SubscriptionType) -> None:
        """Broadcast message to all clients subscribed to a specific type"""
        subscribers = [
            client_id for client_id, client in self.clients.items()
            if subscription_type in client.subscriptions or SubscriptionType.ALL in client.subscriptions
        ]
        
        for client_id in subscribers:
            await self._send_message(client_id, message)
    
    async def _broadcast_to_camera_subscribers(self, camera_id: str, message: WebSocketMessage, subscription_type: SubscriptionType) -> None:
        """Broadcast message to clients subscribed to a specific camera"""
        if camera_id not in self.camera_subscribers:
            return
        
        subscribers = [
            client_id for client_id in self.camera_subscribers[camera_id]
            if client_id in self.clients and (
                subscription_type in self.clients[client_id].subscriptions or
                SubscriptionType.ALL in self.clients[client_id].subscriptions
            )
        ]
        
        for client_id in subscribers:
            await self._send_message(client_id, message)
    
    async def _frame_broadcaster_loop(self) -> None:
        """Background task to broadcast camera frames"""
        while self.running:
            try:
                # Get list of cameras with subscribers
                subscribed_cameras = set()
                for client in self.clients.values():
                    if SubscriptionType.CAMERA_FRAMES in client.subscriptions:
                        subscribed_cameras.update(client.subscribed_cameras)
                
                # Broadcast frames for subscribed cameras
                for camera_id in subscribed_cameras:
                    await self._broadcast_camera_frame(camera_id)
                
                # Control frame rate
                await asyncio.sleep(1.0 / self.frame_rate)
                
            except Exception as e:
                logger.error(f"Frame broadcaster error: {e}")
                await asyncio.sleep(1.0)
    
    async def _broadcast_camera_frame(self, camera_id: str) -> None:
        """Broadcast single camera frame to subscribers with enhanced transmission"""
        try:
            # Check cache first
            current_time = time.time()
            if camera_id in self.frame_cache:
                cached_frame = self.frame_cache[camera_id]
                if current_time - cached_frame["timestamp"] < self.cache_expiry:
                    # Use cached frame for both binary and text subscribers
                    await self._broadcast_cached_frame(camera_id, cached_frame)
                    return
            
            # Get fresh frame
            frame_data, timestamp = await self.multi_camera_service.get_camera_jpeg_frame(camera_id)
            
            if frame_data is None:
                return
            
            # Prepare multiple frame formats for different client preferences
            frame_variants = await self._prepare_frame_variants(frame_data, camera_id, timestamp)
            
            # Cache frame variants
            self.frame_cache[camera_id] = {
                "variants": frame_variants,
                "timestamp": current_time,
                "original_size": len(frame_data)
            }
            
            # Broadcast to subscribers based on their preferences
            await self._broadcast_frame_variants(camera_id, frame_variants)
            self.stats["frames_streamed"] += 1
            
        except Exception as e:
            logger.error(f"Error broadcasting frame for camera {camera_id}: {e}")
            self.stats["errors"] += 1

    async def _prepare_frame_variants(self, frame_data: bytes, camera_id: str, timestamp: float) -> Dict[str, Any]:
        """Prepare different frame variants for different client capabilities"""
        variants = {}
        
        try:
            # Original JPEG binary data
            variants["binary_original"] = {
                "data": frame_data,
                "size": len(frame_data),
                "compression": "jpeg",
                "quality": "original"
            }
            
            # Compressed binary for bandwidth-limited clients
            if len(frame_data) > 500 * 1024:  # If larger than 500KB
                compressed_data = await self._compress_frame(frame_data, quality=60)
                variants["binary_compressed"] = {
                    "data": compressed_data,
                    "size": len(compressed_data),
                    "compression": "jpeg",
                    "quality": "compressed"
                }
            
            # Base64 encoded for legacy clients
            frame_b64 = base64.b64encode(frame_data).decode('utf-8')
            variants["base64_original"] = {
                "image": frame_b64,
                "timestamp": timestamp,
                "camera_id": camera_id,
                "format": "jpeg",
                "encoding": "base64"
            }
            
            # Thumbnail for preview clients
            thumbnail_data = await self._create_thumbnail(frame_data, size=(320, 240))
            if thumbnail_data:
                variants["thumbnail"] = {
                    "data": thumbnail_data,
                    "size": len(thumbnail_data),
                    "resolution": "320x240",
                    "compression": "jpeg"
                }
            
        except Exception as e:
            logger.error(f"Error preparing frame variants: {e}")
            # Fallback to base64 only
            frame_b64 = base64.b64encode(frame_data).decode('utf-8')
            variants["base64_original"] = {
                "image": frame_b64,
                "timestamp": timestamp,
                "camera_id": camera_id,
                "format": "jpeg",
                "encoding": "base64"
            }
        
        return variants

    async def _compress_frame(self, frame_data: bytes, quality: int = 60) -> bytes:
        """Compress JPEG frame with specified quality"""
        try:
            import cv2
            import numpy as np
            
            # Decode JPEG
            nparr = np.frombuffer(frame_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return frame_data
            
            # Re-encode with lower quality
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            _, compressed = cv2.imencode('.jpg', img, encode_params)
            
            return compressed.tobytes()
            
        except Exception as e:
            logger.debug(f"Frame compression failed: {e}")
            return frame_data

    async def _create_thumbnail(self, frame_data: bytes, size: tuple = (320, 240)) -> Optional[bytes]:
        """Create thumbnail from frame data"""
        try:
            import cv2
            import numpy as np
            
            # Decode JPEG
            nparr = np.frombuffer(frame_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None
            
            # Resize to thumbnail
            thumbnail = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
            
            # Encode as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
            _, encoded = cv2.imencode('.jpg', thumbnail, encode_params)
            
            return encoded.tobytes()
            
        except Exception as e:
            logger.debug(f"Thumbnail creation failed: {e}")
            return None

    async def _broadcast_cached_frame(self, camera_id: str, cached_frame: Dict[str, Any]) -> None:
        """Broadcast cached frame variants to subscribers"""
        variants = cached_frame.get("variants", {})
        await self._broadcast_frame_variants(camera_id, variants)

    async def _broadcast_frame_variants(self, camera_id: str, variants: Dict[str, Any]) -> None:
        """Broadcast frame variants to subscribers based on their preferences"""
        if camera_id not in self.camera_subscribers:
            return
        
        for client_id in self.camera_subscribers[camera_id]:
            if client_id not in self.clients:
                continue
                
            client = self.clients[client_id]
            if SubscriptionType.CAMERA_FRAMES not in client.subscriptions:
                continue
            
            # Select appropriate variant based on client preferences
            await self._send_optimal_frame_variant(client, camera_id, variants)

    async def _send_optimal_frame_variant(self, client: WebSocketClient, camera_id: str, 
                                        variants: Dict[str, Any]) -> None:
        """Send optimal frame variant based on client capabilities"""
        try:
            if client.binary_mode and "binary_original" in variants:
                # Send binary data for high-performance clients
                await self._send_binary_frame(client, camera_id, variants["binary_original"], "original")
                self.stats["binary_frames_sent"] += 1
            elif client.binary_mode and "binary_compressed" in variants:
                # Send compressed binary for bandwidth-limited clients
                await self._send_binary_frame(client, camera_id, variants["binary_compressed"], "compressed")
                self.stats["binary_frames_sent"] += 1
                self.stats["compressed_frames_sent"] += 1
                # Track compression savings
                original_size = variants.get("binary_original", {}).get("size", 0)
                compressed_size = variants["binary_compressed"]["size"]
                if original_size > 0:
                    self.stats["compression_savings"] += original_size - compressed_size
            elif client.quality_preference == "low" and "thumbnail" in variants:
                # Send thumbnail for low-quality preference
                await self._send_binary_frame(client, camera_id, variants["thumbnail"], "thumbnail")
                self.stats["binary_frames_sent"] += 1
                self.stats["thumbnail_frames_sent"] += 1
            else:
                # Fallback to base64 for legacy clients
                if "base64_original" in variants:
                    message = WebSocketMessage(
                        type=MessageType.CAMERA_FRAME,
                        data=variants["base64_original"],
                        camera_id=camera_id
                    )
                    await self._send_message(client.client_id, message)
                    self.stats["text_frames_sent"] += 1
        
        except Exception as e:
            logger.error(f"Error sending frame variant to client {client.client_id}: {e}")

    async def _send_binary_frame(self, client: WebSocketClient, camera_id: str, 
                               frame_variant: Dict[str, Any], variant_type: str = "original") -> None:
        """Send binary frame data to client"""
        try:
            # Create binary frame header
            header = {
                "type": MessageType.CAMERA_FRAME_BINARY.value,
                "camera_id": camera_id,
                "timestamp": time.time(),
                "size": frame_variant["size"],
                "compression": frame_variant.get("compression", "jpeg"),
                "quality": frame_variant.get("quality", "original"),
                "resolution": frame_variant.get("resolution", "original"),
                "variant": variant_type
            }
            
            # Send header as JSON followed by binary data
            header_json = json.dumps(header).encode('utf-8')
            header_size = len(header_json)
            
            # Create message: [4 bytes header size][header JSON][binary data]
            message_data = (
                header_size.to_bytes(4, byteorder='big') +
                header_json +
                frame_variant["data"]
            )
            
            # Check if message size is within client limits
            if len(message_data) > client.max_frame_size:
                logger.warning(f"Frame too large for client {client.client_id}: {len(message_data)} bytes")
                return
            
            # Send binary message
            await client.websocket.send_bytes(message_data)
            
            # Update enhanced stats
            self.stats["bytes_sent"] += len(message_data)
            self.stats["messages_sent"] += 1
            
            # Update average frame size
            current_avg = self.stats["average_frame_size"]
            frame_count = self.stats["frames_streamed"] + 1
            self.stats["average_frame_size"] = (current_avg * (frame_count - 1) + len(message_data)) / frame_count
            
            # Track peak bandwidth (approximate)
            current_bandwidth = len(message_data)
            if current_bandwidth > self.stats["peak_bandwidth"]:
                self.stats["peak_bandwidth"] = current_bandwidth
            
        except Exception as e:
            logger.error(f"Error sending binary frame to client {client.client_id}: {e}")
            await self._disconnect_client(client.client_id)
    
    async def _status_broadcaster_loop(self) -> None:
        """Background task to broadcast system status"""
        while self.running:
            try:
                # Broadcast system stats
                if any(SubscriptionType.SYSTEM_STATS in client.subscriptions for client in self.clients.values()):
                    system_stats = await self.multi_camera_service.get_system_stats()
                    await self.broadcast_system_stats(system_stats)
                
                # Broadcast processing stats
                if any(SubscriptionType.PROCESSING_STATS in client.subscriptions for client in self.clients.values()):
                    processing_stats = await self.multi_stream_processor.get_stream_stats()
                    message = WebSocketMessage(
                        type=MessageType.PROCESSING_STATS,
                        data=processing_stats
                    )
                    await self._broadcast_to_subscribers(message, SubscriptionType.PROCESSING_STATS)
                
                await asyncio.sleep(5.0)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Status broadcaster error: {e}")
                await asyncio.sleep(5.0)
    
    async def _ping_loop(self) -> None:
        """Background task to ping clients"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check for stale connections
                stale_clients = [
                    client_id for client_id, client in self.clients.items()
                    if current_time - client.last_ping > (self.ping_interval * 2)
                ]
                
                # Disconnect stale clients
                for client_id in stale_clients:
                    logger.warning(f"Client {client_id} is stale, disconnecting")
                    await self._disconnect_client(client_id)
                
                await asyncio.sleep(self.ping_interval)
                
            except Exception as e:
                logger.error(f"Ping loop error: {e}")
                await asyncio.sleep(self.ping_interval)
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up resources"""
        while self.running:
            try:
                current_time = time.time()
                
                # Clean up frame cache
                expired_cameras = [
                    camera_id for camera_id, cached_frame in self.frame_cache.items()
                    if current_time - cached_frame["timestamp"] > self.cache_expiry * 2
                ]
                
                for camera_id in expired_cameras:
                    del self.frame_cache[camera_id]
                
                # Clean up empty camera subscribers
                empty_subscribers = [
                    camera_id for camera_id, subscribers in self.camera_subscribers.items()
                    if not subscribers
                ]
                
                for camera_id in empty_subscribers:
                    del self.camera_subscribers[camera_id]
                
                await asyncio.sleep(self.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(self.cleanup_interval)
    
    async def _get_camera_list(self) -> List[Dict[str, Any]]:
        """Get list of available cameras"""
        try:
            cameras = await self.multi_camera_service.get_all_cameras()
            return cameras
        except Exception as e:
            logger.error(f"Error getting camera list: {e}")
            return []
    
    def _register_callbacks(self) -> None:
        """Register callbacks for subscription types"""
        # This can be extended to register specific callbacks
        # for different subscription types
        pass