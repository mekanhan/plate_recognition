"""
Background Monitoring Service
Monitors camera status, recording status, and system health to broadcast updates via WebSocket
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import aiohttp
from database.service import DatabaseService
try:
    from .websocket_manager import broadcast_camera_status, broadcast_recording_status, websocket_manager
except ImportError:
    from api.websocket_manager import broadcast_camera_status, broadcast_recording_status, websocket_manager

logger = logging.getLogger(__name__)

class BackgroundMonitor:
    """Background service for monitoring camera and recording status"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.monitoring_tasks = {}
        self.is_running = False
        self.camera_status_cache = {}
        self.recording_status_cache = {}
        
        # Monitoring intervals (in seconds)
        self.camera_check_interval = 30    # Check camera status every 30s
        self.recording_check_interval = 15  # Check recording status every 15s
        self.health_check_interval = 60    # System health every 60s
        
        # HTTP session for API calls
        self.session = None
        
    async def start(self):
        """Start all background monitoring tasks"""
        if self.is_running:
            logger.warning("Background monitor already running")
            return
        
        self.is_running = True
        self.session = aiohttp.ClientSession()
        
        # Start monitoring tasks
        self.monitoring_tasks['camera_status'] = asyncio.create_task(
            self._monitor_camera_status()
        )
        self.monitoring_tasks['recording_status'] = asyncio.create_task(
            self._monitor_recording_status()
        )
        self.monitoring_tasks['system_health'] = asyncio.create_task(
            self._monitor_system_health()
        )
        
        logger.info("Background monitoring started")
    
    async def stop(self):
        """Stop all monitoring tasks"""
        self.is_running = False
        
        # Cancel all tasks
        for task_name, task in self.monitoring_tasks.items():
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Cancelled monitoring task: {task_name}")
        
        # Close HTTP session
        if self.session:
            await self.session.close()
            self.session = None
        
        self.monitoring_tasks.clear()
        logger.info("Background monitoring stopped")
    
    async def _monitor_camera_status(self):
        """Monitor camera connection status and broadcast changes"""
        while self.is_running:
            try:
                # Get all cameras from database
                cameras = await self.db.get_all_cameras()
                
                for camera in cameras:
                    if not camera.enabled:
                        continue
                    
                    # Check camera status
                    current_status = await self._check_camera_connection(camera)
                    previous_status = self.camera_status_cache.get(camera.camera_id)
                    
                    # Broadcast if status changed
                    if current_status != previous_status:
                        await broadcast_camera_status(
                            camera_id=camera.camera_id,
                            status=current_status,
                            details={
                                "name": camera.name,
                                "ip_address": camera.ip_address,
                                "connection_type": camera.connection_type,
                                "last_check": datetime.now().isoformat()
                            }
                        )
                        
                        # Update database status if significantly different
                        if current_status != camera.status:
                            await self.db.update_camera_status(camera.camera_id, current_status)
                        
                        logger.info(f"Camera {camera.name} status changed: {previous_status} -> {current_status}")
                    
                    # Update cache
                    self.camera_status_cache[camera.camera_id] = current_status
                
            except Exception as e:
                logger.error(f"Error in camera status monitoring: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.camera_check_interval)
    
    async def _monitor_recording_status(self):
        """Monitor recording status and broadcast changes"""
        while self.is_running:
            try:
                # Check recording service status
                recording_statuses = await self._get_recording_statuses()
                
                for camera_id, status_data in recording_statuses.items():
                    current_recording = status_data.get('is_recording', False)
                    previous_recording = self.recording_status_cache.get(camera_id)
                    
                    # Broadcast if recording status changed
                    if current_recording != previous_recording:
                        await broadcast_recording_status(
                            camera_id=camera_id,
                            is_recording=current_recording,
                            details=status_data
                        )
                        
                        logger.info(f"Camera {camera_id} recording status changed: {previous_recording} -> {current_recording}")
                    
                    # Update cache
                    self.recording_status_cache[camera_id] = current_recording
                
            except Exception as e:
                logger.error(f"Error in recording status monitoring: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.recording_check_interval)
    
    async def _monitor_system_health(self):
        """Monitor overall system health"""
        while self.is_running:
            try:
                # Get system health data
                health_data = await self._get_system_health()
                
                # Broadcast system health (subscribers can choose to listen or not)
                await websocket_manager.broadcast_to_subscribers("system_health", health_data)
                
                logger.debug("System health broadcast sent")
                
            except Exception as e:
                logger.error(f"Error in system health monitoring: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.health_check_interval)
    
    async def _check_camera_connection(self, camera) -> str:
        """Check if camera is accessible via network ping or connection test"""
        try:
            # Simple connection test - try to connect to camera port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            
            try:
                result = sock.connect_ex((camera.ip_address, camera.port or 554))
                sock.close()
                
                if result == 0:
                    return 'online'
                else:
                    return 'offline'
            except Exception:
                return 'offline'
            
        except Exception as e:
            logger.debug(f"Error checking camera {camera.camera_id}: {e}")
            return 'error'
    
    async def _get_recording_statuses(self) -> Dict[str, Any]:
        """Get recording status from recording service"""
        try:
            if not self.session:
                return {}
            
            # Call recording service API
            async with self.session.get('http://localhost:8002/recordings/status', timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    # Extract camera statuses from response
                    return data.get('cameras', {}) if isinstance(data, dict) else {}
                else:
                    logger.warning(f"Recording service returned status {response.status}")
                    return {}
                    
        except asyncio.TimeoutError:
            logger.warning("Timeout getting recording status")
            return {}
        except Exception as e:
            logger.error(f"Error getting recording statuses: {e}")
            return {}
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        try:
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "services": {}
            }
            
            # Check main API health (self)
            health_data["services"]["main_api"] = {
                "status": "online",
                "response_time": 0  # Always 0 for self
            }
            
            # Check recording service
            if self.session:
                try:
                    start_time = datetime.now()
                    async with self.session.get('http://localhost:8002/health', timeout=5) as response:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        health_data["services"]["recording_service"] = {
                            "status": "online" if response.status == 200 else "degraded",
                            "response_time": round(response_time, 2)
                        }
                except asyncio.TimeoutError:
                    health_data["services"]["recording_service"] = {
                        "status": "timeout",
                        "response_time": None
                    }
                except Exception:
                    health_data["services"]["recording_service"] = {
                        "status": "offline",
                        "response_time": None
                    }
            
            # Add WebSocket connection stats
            ws_stats = websocket_manager.get_connection_stats()
            health_data["websocket"] = {
                "active_connections": ws_stats["total_connections"],
                "subscriptions": ws_stats["subscriptions"]
            }
            
            # Add camera summary
            total_cameras = len(self.camera_status_cache)
            online_cameras = sum(1 for status in self.camera_status_cache.values() if status == 'online')
            
            health_data["cameras"] = {
                "total": total_cameras,
                "online": online_cameras,
                "offline": total_cameras - online_cameras
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Failed to get system health",
                "services": {}
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "is_running": self.is_running,
            "active_tasks": len([t for t in self.monitoring_tasks.values() if t and not t.done()]),
            "camera_status_cache_size": len(self.camera_status_cache),
            "recording_status_cache_size": len(self.recording_status_cache),
            "intervals": {
                "camera_check": self.camera_check_interval,
                "recording_check": self.recording_check_interval, 
                "health_check": self.health_check_interval
            }
        }

# Global instance
background_monitor: Optional[BackgroundMonitor] = None

async def start_background_monitoring(db_service: DatabaseService):
    """Start background monitoring service"""
    global background_monitor
    
    if background_monitor is None:
        background_monitor = BackgroundMonitor(db_service)
    
    await background_monitor.start()
    return background_monitor

async def stop_background_monitoring():
    """Stop background monitoring service"""
    global background_monitor
    
    if background_monitor:
        await background_monitor.stop()