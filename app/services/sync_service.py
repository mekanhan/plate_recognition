"""
Sync Service for handling cloud synchronization with offline-first approach
"""
import asyncio
import json
import gzip
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import aiohttp
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SyncQueue, SyncStatus, Priority, Detection, EnhancedResult
from app.database import async_session
from app.services.device_service import DeviceService

logger = logging.getLogger(__name__)

@dataclass
class SyncResult:
    """Result of a sync operation"""
    accepted_count: int = 0
    rejected_count: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class SyncService:
    """Manages data synchronization with cloud platform"""
    
    def __init__(self, device_service: DeviceService, config: Optional[Dict] = None):
        self.device = device_service
        self.config = config or {}
        self.running = False
        self._sync_lock = asyncio.Lock()
        self.workers = []
        
        # Configuration
        self.sync_mode = self.config.get('sync_mode', 'batch')  # 'immediate' or 'batch'
        self.sync_interval = self.config.get('sync_interval', 300)  # seconds
        self.sync_batch_size = self.config.get('sync_batch_size', 50)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay_base = self.config.get('retry_delay_base', 60)  # seconds
        self.compression_threshold = self.config.get('compression_threshold', 10240)  # bytes
        self.data_retention_days = self.config.get('data_retention_days', 30)
        
    async def start(self):
        """Start sync service workers"""
        if self.running:
            return
            
        self.running = True
        
        # Start appropriate worker based on sync mode
        if self.sync_mode == 'immediate':
            self.workers.append(asyncio.create_task(self._immediate_sync_worker()))
        else:
            self.workers.append(asyncio.create_task(self._batch_sync_worker()))
        
        # Start retry worker
        self.workers.append(asyncio.create_task(self._retry_worker()))
        
        # Start cleanup worker
        self.workers.append(asyncio.create_task(self._cleanup_worker()))
        
        logger.info(f"Sync service started in {self.sync_mode} mode")
    
    async def stop(self):
        """Stop sync service"""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
        logger.info("Sync service stopped")
    
    async def queue_detection_sync(self, detection_data: Dict[str, Any], priority: Priority = Priority.NORMAL):
        """Queue a detection for synchronization"""
        try:
            async with async_session() as session:
                sync_item = SyncQueue(
                    item_type='detection',
                    item_id=detection_data.get('detection_id', str(time.time())),
                    data=detection_data,
                    priority=priority,
                    device_id=self.device.device_id
                )
                
                session.add(sync_item)
                await session.commit()
                
                logger.debug(f"Queued detection for sync: {sync_item.item_id}")
                
        except Exception as e:
            logger.error(f"Failed to queue detection sync: {e}")
    
    async def queue_health_sync(self, health_data: Dict[str, Any]):
        """Queue health data for synchronization"""
        try:
            async with async_session() as session:
                sync_item = SyncQueue(
                    item_type='health',
                    item_id=f"health_{int(time.time())}",
                    data=health_data,
                    priority=Priority.LOW,
                    device_id=self.device.device_id
                )
                
                session.add(sync_item)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to queue health sync: {e}")
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync queue status"""
        try:
            async with async_session() as session:
                # Count items by status
                pending_result = await session.execute(
                    select(SyncQueue).where(SyncQueue.status == SyncStatus.PENDING)
                )
                pending_count = len(pending_result.scalars().all())
                
                retry_result = await session.execute(
                    select(SyncQueue).where(SyncQueue.status == SyncStatus.RETRY)
                )
                retry_count = len(retry_result.scalars().all())
                
                failed_result = await session.execute(
                    select(SyncQueue).where(SyncQueue.status == SyncStatus.FAILED)
                )
                failed_count = len(failed_result.scalars().all())
                
                return {
                    'pending': pending_count,
                    'retry': retry_count,
                    'failed': failed_count,
                    'sync_mode': self.sync_mode,
                    'device_id': self.device.device_id,
                    'last_sync': await self._get_last_sync_time()
                }
                
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {'error': str(e)}
    
    async def _immediate_sync_worker(self):
        """Process items immediately as they arrive"""
        while self.running:
            try:
                # Get one pending item
                items = await self._get_pending_sync_items(limit=1)
                
                if items:
                    await self._sync_items(items)
                else:
                    # No items, wait briefly
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Immediate sync error: {e}")
                await asyncio.sleep(5)
    
    async def _batch_sync_worker(self):
        """Process items in batches at intervals"""
        while self.running:
            try:
                # Wait for batch interval
                await asyncio.sleep(self.sync_interval)
                
                # Get batch of items
                items = await self._get_pending_sync_items(limit=self.sync_batch_size)
                
                if items:
                    await self._sync_items(items)
                    
            except Exception as e:
                logger.error(f"Batch sync error: {e}")
                await asyncio.sleep(30)
    
    async def _get_pending_sync_items(self, limit: int = 50) -> List[SyncQueue]:
        """Get items pending synchronization"""
        try:
            async with async_session() as session:
                # Get items that are pending or ready for retry
                now = datetime.utcnow()
                
                result = await session.execute(
                    select(SyncQueue)
                    .where(
                        (SyncQueue.status == SyncStatus.PENDING) |
                        (
                            (SyncQueue.status == SyncStatus.RETRY) &
                            ((SyncQueue.next_retry_at.is_(None)) |
                             (SyncQueue.next_retry_at <= now))
                        )
                    )
                    .order_by(SyncQueue.priority.desc(), SyncQueue.created_at)
                    .limit(limit)
                )
                
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to get pending sync items: {e}")
            return []
    
    async def _sync_items(self, items: List[SyncQueue]):
        """Sync a list of items to cloud"""
        if not items:
            return
            
        async with self._sync_lock:
            # Group items by type for efficient upload
            grouped_items = self._group_items_by_type(items)
            
            for item_type, type_items in grouped_items.items():
                await self._upload_items(item_type, type_items)
    
    def _group_items_by_type(self, items: List[SyncQueue]) -> Dict[str, List[SyncQueue]]:
        """Group sync items by type"""
        groups = {}
        for item in items:
            if item.item_type not in groups:
                groups[item.item_type] = []
            groups[item.item_type].append(item)
        return groups
    
    async def _upload_items(self, item_type: str, items: List[SyncQueue]):
        """Upload items to cloud API"""
        if not items:
            return
            
        try:
            # Prepare payload
            payload = {
                'device_id': self.device.device_id,
                'timestamp': datetime.utcnow().isoformat(),
                'item_type': item_type,
                'items': [item.data for item in items]
            }
            
            # Serialize and potentially compress
            data = json.dumps(payload).encode('utf-8')
            headers = self.device.get_auth_headers()
            
            if len(data) > self.compression_threshold:
                data = gzip.compress(data)
                headers['Content-Encoding'] = 'gzip'
            
            # Upload with retry logic
            success = await self._upload_with_retry(
                url=f"{self.device.cloud_endpoint}/api/v1/sync/{item_type}",
                data=data,
                headers=headers
            )
            
            # Update sync status
            await self._update_items_status(items, success)
            
        except Exception as e:
            logger.error(f"Upload error for {item_type}: {e}")
            await self._update_items_status(items, False, str(e))
    
    async def _upload_with_retry(self, url: str, data: bytes, headers: Dict, max_retries: int = 3) -> bool:
        """Upload with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, data=data, headers=headers) as response:
                        if response.status == 200:
                            logger.info(f"Successfully uploaded to {url}")
                            return True
                        elif response.status == 401:
                            # Re-authenticate if needed
                            logger.warning("Authentication failed during sync")
                            return False
                        else:
                            logger.warning(f"Upload failed with status {response.status}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Upload timeout (attempt {attempt + 1})")
            except aiohttp.ClientError as e:
                logger.warning(f"Upload client error: {e}")
            except Exception as e:
                logger.error(f"Upload error: {e}")
                
            # Exponential backoff
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                
        return False
    
    async def _update_items_status(self, items: List[SyncQueue], success: bool, error: str = None):
        """Update sync status for items"""
        try:
            async with async_session() as session:
                for item in items:
                    if success:
                        item.status = SyncStatus.SYNCED
                        item.synced_at = datetime.utcnow()
                        item.last_error = None
                    else:
                        item.attempts += 1
                        item.error_count += 1
                        item.last_error = error
                        item.updated_at = datetime.utcnow()
                        
                        if item.attempts >= self.max_retries:
                            item.status = SyncStatus.FAILED
                        else:
                            item.status = SyncStatus.RETRY
                            # Calculate next retry time with exponential backoff
                            delay = self.retry_delay_base * (2 ** (item.attempts - 1))
                            item.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
                    
                    session.add(item)
                
                await session.commit()
                
                if success:
                    logger.info(f"Marked {len(items)} items as synced")
                else:
                    logger.warning(f"Updated {len(items)} items with sync failure")
                    
        except Exception as e:
            logger.error(f"Failed to update sync status: {e}")
    
    async def _retry_worker(self):
        """Handle failed items with exponential backoff"""
        while self.running:
            try:
                # Check every minute
                await asyncio.sleep(60)
                
                # Get items ready for retry
                items = await self._get_pending_sync_items(limit=10)
                retry_items = [
                    item for item in items 
                    if item.status == SyncStatus.RETRY
                ]
                
                if retry_items:
                    logger.info(f"Retrying {len(retry_items)} failed items")
                    await self._sync_items(retry_items)
                    
            except Exception as e:
                logger.error(f"Retry worker error: {e}")
    
    async def _cleanup_worker(self):
        """Clean up old synced data"""
        while self.running:
            try:
                # Run cleanup daily
                await asyncio.sleep(86400)  # 24 hours
                
                await self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _cleanup_old_data(self):
        """Remove old synced data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.data_retention_days)
            
            async with async_session() as session:
                # Delete old synced items
                await session.execute(
                    delete(SyncQueue)
                    .where(
                        (SyncQueue.status == SyncStatus.SYNCED) &
                        (SyncQueue.synced_at < cutoff_date)
                    )
                )
                
                await session.commit()
                logger.info(f"Cleaned up sync data older than {self.data_retention_days} days")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def _get_last_sync_time(self) -> Optional[str]:
        """Get timestamp of last successful sync"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(SyncQueue.synced_at)
                    .where(SyncQueue.status == SyncStatus.SYNCED)
                    .order_by(SyncQueue.synced_at.desc())
                    .limit(1)
                )
                
                last_sync = result.scalar_one_or_none()
                return last_sync.isoformat() if last_sync else None
                
        except Exception as e:
            logger.debug(f"Failed to get last sync time: {e}")
            return None
    
    async def force_sync_all(self) -> SyncResult:
        """Force sync all pending items immediately"""
        try:
            items = await self._get_pending_sync_items(limit=1000)
            if items:
                await self._sync_items(items)
                return SyncResult(accepted_count=len(items))
            else:
                return SyncResult()
                
        except Exception as e:
            logger.error(f"Force sync failed: {e}")
            return SyncResult(errors=[str(e)])
    
    async def clear_failed_items(self) -> int:
        """Clear all failed sync items"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    delete(SyncQueue).where(SyncQueue.status == SyncStatus.FAILED)
                )
                count = result.rowcount
                await session.commit()
                
                logger.info(f"Cleared {count} failed sync items")
                return count
                
        except Exception as e:
            logger.error(f"Failed to clear failed items: {e}")
            return 0