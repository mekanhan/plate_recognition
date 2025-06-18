"""
Camera Cache Service for optimized camera detection.

Provides caching layer for camera detection to avoid repeated hardware scanning.
Follows industry standards for performance optimization.
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CameraCacheService:
    """
    Caching service for camera detection results.
    
    Features:
    - In-memory cache with configurable TTL
    - Background refresh mechanism
    - Thread-safe operations
    - Fallback to live detection
    """
    
    def __init__(self, cache_ttl_minutes: int = 5):
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cache_data: Optional[Dict[str, Any]] = None
        self.cache_timestamp: Optional[datetime] = None
        self.refresh_lock = threading.Lock()
        self.is_refreshing = False
        self._refresh_task: Optional[asyncio.Task] = None
        
        logger.info(f"Camera cache service initialized with {cache_ttl_minutes}min TTL")
    
    def is_cache_valid(self) -> bool:
        """Check if current cache is still valid"""
        if self.cache_data is None or self.cache_timestamp is None:
            return False
        
        age = datetime.now() - self.cache_timestamp
        is_valid = age < self.cache_ttl
        
        logger.debug(f"Cache age: {age.total_seconds():.1f}s, valid: {is_valid}")
        return is_valid
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cache status"""
        if self.cache_timestamp is None:
            return {
                "cached": False,
                "last_scan": None,
                "age_seconds": None,
                "is_refreshing": self.is_refreshing
            }
        
        age = datetime.now() - self.cache_timestamp
        return {
            "cached": True,
            "last_scan": self.cache_timestamp.isoformat(),
            "age_seconds": int(age.total_seconds()),
            "ttl_seconds": int(self.cache_ttl.total_seconds()),
            "is_valid": self.is_cache_valid(),
            "is_refreshing": self.is_refreshing
        }
    
    async def get_cameras(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get camera list - from cache if valid, otherwise scan
        
        Args:
            force_refresh: If True, bypass cache and scan immediately
            
        Returns:
            Camera detection results with cache metadata
        """
        # Return cached results if valid and not forcing refresh
        if not force_refresh and self.is_cache_valid():
            logger.debug("Returning cached camera results")
            return {
                "cameras": self.cache_data["cameras"],
                "count": self.cache_data["count"],
                "cached": True,
                "cache_info": self.get_cache_info(),
                "timestamp": datetime.now().isoformat()
            }
        
        # Need fresh scan
        logger.info("Cache miss or force refresh - performing camera scan")
        return await self._perform_scan()
    
    async def refresh_cache_async(self) -> Dict[str, Any]:
        """
        Trigger asynchronous cache refresh
        
        Returns immediately with current cache, starts background refresh
        """
        # Return current cache immediately if available
        current_result = None
        if self.cache_data is not None:
            current_result = {
                "cameras": self.cache_data["cameras"],
                "count": self.cache_data["count"],
                "cached": True,
                "cache_info": self.get_cache_info(),
                "timestamp": datetime.now().isoformat()
            }
        
        # Start background refresh if not already running
        if not self.is_refreshing:
            self._refresh_task = asyncio.create_task(self._background_refresh())
        
        # Return current cache or indicate refresh started
        if current_result:
            current_result["cache_info"]["background_refresh_started"] = True
            return current_result
        else:
            # No cache available, must wait for scan
            return await self._perform_scan()
    
    async def _background_refresh(self):
        """Background task to refresh camera cache"""
        try:
            self.is_refreshing = True
            logger.info("Starting background camera cache refresh")
            
            # Perform the actual scan
            await self._perform_scan()
            
            logger.info("Background camera cache refresh completed")
        except Exception as e:
            logger.error(f"Background camera refresh failed: {e}")
        finally:
            self.is_refreshing = False
    
    async def _perform_scan(self) -> Dict[str, Any]:
        """
        Perform actual camera detection and update cache
        """
        from app.services.camera_service import CameraService
        
        try:
            scan_start = time.time()
            logger.info("Starting camera detection scan")
            
            # Perform actual camera detection
            cameras = CameraService.detect_available_cameras()
            
            scan_duration = time.time() - scan_start
            logger.info(f"Camera scan completed in {scan_duration:.2f}s")
            
            # Update cache
            with self.refresh_lock:
                self.cache_data = {
                    "cameras": cameras,
                    "count": len([c for c in cameras if c.get("type") == "usb"]),
                    "scan_duration": scan_duration
                }
                self.cache_timestamp = datetime.now()
            
            # Return results with cache info
            return {
                "cameras": cameras,
                "count": self.cache_data["count"],
                "cached": False,
                "cache_info": self.get_cache_info(),
                "scan_duration": scan_duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Camera detection scan failed: {e}")
            raise
    
    def invalidate_cache(self):
        """Force cache invalidation"""
        with self.refresh_lock:
            self.cache_data = None
            self.cache_timestamp = None
        logger.info("Camera cache invalidated")
    
    def get_cached_cameras_only(self) -> Optional[List[Dict[str, Any]]]:
        """Get only cached cameras without triggering scan"""
        if self.cache_data is None:
            return None
        return self.cache_data["cameras"]


# Global instance
camera_cache = CameraCacheService()