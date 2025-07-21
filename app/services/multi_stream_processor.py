# app/services/multi_stream_processor.py
# Multi-stream processing engine with GPU resource management
import asyncio
import logging
import time
import uuid
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

from app.services.gpu_resource_manager import GPUResourceManager, ProcessingTask, TaskPriority, TaskStatus
from app.services.multi_camera_service import MultiCameraService
from app.services.detection_service import DetectionService
from app.models import Camera, Detection, ProcessingQueue, ProcessingStatus, Priority
from app.database import async_session
from sqlalchemy import select, update, insert

logger = logging.getLogger(__name__)

class StreamProcessingMode(Enum):
    REAL_TIME = "real_time"
    BATCH = "batch"
    ADAPTIVE = "adaptive"

@dataclass
class StreamProcessingConfig:
    """Configuration for stream processing"""
    mode: StreamProcessingMode = StreamProcessingMode.ADAPTIVE
    max_concurrent_streams: int = 16
    frame_buffer_size: int = 10
    detection_threshold: float = 0.7
    processing_fps: int = 2  # Process every N frames
    enable_gpu_acceleration: bool = True
    enable_frame_skipping: bool = True
    adaptive_quality: bool = True
    
@dataclass
class StreamProcessingResult:
    """Result of stream processing"""
    task_id: str
    camera_id: str
    frame_timestamp: float
    detections: List[Dict[str, Any]]
    processing_time: float
    metadata: Dict[str, Any]

class MultiStreamProcessor:
    """
    Advanced multi-stream processing engine with GPU resource management
    Handles concurrent processing of multiple camera streams with intelligent
    resource allocation and adaptive quality control
    """
    
    def __init__(self, 
                 gpu_manager: GPUResourceManager,
                 multi_camera_service: MultiCameraService,
                 detection_service: DetectionService,
                 config: StreamProcessingConfig = None):
        self.gpu_manager = gpu_manager
        self.multi_camera_service = multi_camera_service
        self.detection_service = detection_service
        self.config = config or StreamProcessingConfig()
        
        # Stream processing state
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.frame_buffers: Dict[str, List[np.ndarray]] = {}
        self.processing_tasks: Dict[str, ProcessingTask] = {}
        self.results_queue: asyncio.Queue = asyncio.Queue()
        
        # Performance tracking
        self.stream_stats: Dict[str, Dict[str, Any]] = {}
        self.system_stats = {
            "total_frames_processed": 0,
            "total_detections": 0,
            "avg_processing_time": 0.0,
            "throughput": 0.0,
            "gpu_utilization": 0.0,
            "memory_usage": 0.0
        }
        
        # Control flags
        self.running = False
        self.processor_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.result_handler_task: Optional[asyncio.Task] = None
        
        # Frame processing interval
        self.frame_interval = 1.0 / self.config.processing_fps
        
    async def initialize(self) -> None:
        """Initialize the multi-stream processor"""
        logger.info("Initializing Multi-Stream Processor...")
        
        try:
            # Initialize GPU resource manager if not already done
            if not self.gpu_manager.running:
                await self.gpu_manager.initialize()
            
            # Start background tasks
            self.running = True
            self.processor_task = asyncio.create_task(self._stream_processor_loop())
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            self.result_handler_task = asyncio.create_task(self._result_handler_loop())
            
            logger.info("Multi-Stream Processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Multi-Stream Processor: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the multi-stream processor"""
        logger.info("Shutting down Multi-Stream Processor...")
        
        self.running = False
        
        # Stop all active streams
        for camera_id in list(self.active_streams.keys()):
            await self.stop_stream_processing(camera_id)
        
        # Cancel background tasks
        for task in [self.processor_task, self.monitor_task, self.result_handler_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Multi-Stream Processor shutdown complete")
    
    async def start_stream_processing(self, camera_id: str, 
                                    priority: Priority = Priority.NORMAL) -> bool:
        """
        Start processing frames from a specific camera stream
        
        Args:
            camera_id: ID of camera to process
            priority: Processing priority
            
        Returns:
            True if successful, False otherwise
        """
        if camera_id in self.active_streams:
            logger.warning(f"Stream processing already active for camera {camera_id}")
            return True
        
        try:
            # Initialize frame buffer
            self.frame_buffers[camera_id] = []
            
            # Initialize stream statistics
            self.stream_stats[camera_id] = {
                "frames_processed": 0,
                "detections_found": 0,
                "avg_processing_time": 0.0,
                "last_processed": 0,
                "errors": 0,
                "frame_drops": 0,
                "priority": priority
            }
            
            # Mark stream as active
            self.active_streams[camera_id] = {
                "priority": priority,
                "started_at": time.time(),
                "last_frame_time": 0,
                "frame_count": 0,
                "processing_enabled": True
            }
            
            logger.info(f"Started stream processing for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start stream processing for camera {camera_id}: {e}")
            return False
    
    async def stop_stream_processing(self, camera_id: str) -> bool:
        """
        Stop processing frames from a specific camera stream
        
        Args:
            camera_id: ID of camera to stop processing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from active streams
            if camera_id in self.active_streams:
                del self.active_streams[camera_id]
            
            # Clear frame buffer
            if camera_id in self.frame_buffers:
                del self.frame_buffers[camera_id]
            
            # Cancel any pending tasks for this camera
            pending_tasks = [
                task for task in self.processing_tasks.values()
                if task.camera_id == camera_id and task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]
            ]
            
            for task in pending_tasks:
                await self.gpu_manager.cancel_task(task.task_id)
            
            logger.info(f"Stopped stream processing for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop stream processing for camera {camera_id}: {e}")
            return False
    
    async def set_stream_priority(self, camera_id: str, priority: Priority) -> bool:
        """
        Set processing priority for a camera stream
        
        Args:
            camera_id: ID of camera
            priority: New priority level
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if camera_id in self.active_streams:
                self.active_streams[camera_id]["priority"] = priority
                self.stream_stats[camera_id]["priority"] = priority
                logger.info(f"Updated priority for camera {camera_id} to {priority}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to set priority for camera {camera_id}: {e}")
            return False
    
    async def get_stream_stats(self, camera_id: str = None) -> Dict[str, Any]:
        """
        Get processing statistics for streams
        
        Args:
            camera_id: Optional camera ID for specific stats
            
        Returns:
            Stream statistics dictionary
        """
        if camera_id:
            return self.stream_stats.get(camera_id, {})
        
        return {
            "active_streams": len(self.active_streams),
            "total_frames_processed": self.system_stats["total_frames_processed"],
            "total_detections": self.system_stats["total_detections"],
            "avg_processing_time": self.system_stats["avg_processing_time"],
            "throughput": self.system_stats["throughput"],
            "gpu_utilization": self.system_stats["gpu_utilization"],
            "memory_usage": self.system_stats["memory_usage"],
            "stream_details": self.stream_stats,
            "gpu_stats": self.gpu_manager.get_gpu_stats()
        }
    
    async def _stream_processor_loop(self) -> None:
        """Main stream processing loop"""
        while self.running:
            try:
                # Process frames from all active streams
                for camera_id in list(self.active_streams.keys()):
                    await self._process_camera_stream(camera_id)
                
                # Control processing rate
                await asyncio.sleep(self.frame_interval)
                
            except Exception as e:
                logger.error(f"Stream processor error: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_camera_stream(self, camera_id: str) -> None:
        """Process frames from a specific camera stream"""
        try:
            stream_info = self.active_streams.get(camera_id)
            if not stream_info or not stream_info["processing_enabled"]:
                return
            
            # Get latest frame from multi-camera service
            frame, timestamp = await self.multi_camera_service.get_camera_frame(camera_id)
            
            if frame is None:
                return
            
            # Check if frame is new
            if timestamp <= stream_info["last_frame_time"]:
                return
            
            # Update frame tracking
            stream_info["last_frame_time"] = timestamp
            stream_info["frame_count"] += 1
            
            # Apply frame skipping logic
            if self.config.enable_frame_skipping:
                stats = self.stream_stats[camera_id]
                if stats["frames_processed"] > 0:
                    # Skip frame if processing is behind
                    time_since_last = timestamp - stats["last_processed"]
                    if time_since_last < self.frame_interval:
                        return
            
            # Apply adaptive quality control
            if self.config.adaptive_quality:
                frame = await self._apply_adaptive_quality(frame, camera_id)
            
            # Create processing task
            task = ProcessingTask(
                task_id=str(uuid.uuid4()),
                camera_id=camera_id,
                frame_data={
                    "frame": frame,
                    "timestamp": timestamp,
                    "camera_id": camera_id,
                    "frame_number": stream_info["frame_count"]
                },
                priority=self._convert_priority(stream_info["priority"]),
                callback=self._processing_callback
            )
            
            # Submit task to GPU manager
            await self.gpu_manager.submit_task(task)
            self.processing_tasks[task.task_id] = task
            
        except Exception as e:
            logger.error(f"Error processing camera stream {camera_id}: {e}")
            if camera_id in self.stream_stats:
                self.stream_stats[camera_id]["errors"] += 1
    
    async def _apply_adaptive_quality(self, frame: np.ndarray, camera_id: str) -> np.ndarray:
        """Apply adaptive quality control based on processing load"""
        try:
            # Get current system load
            gpu_stats = self.gpu_manager.get_gpu_stats()
            gpu_utilization = gpu_stats["performance"]["gpu_utilization"]
            
            # Adjust quality based on load
            if gpu_utilization > 80:
                # High load - reduce quality
                height, width = frame.shape[:2]
                new_height = int(height * 0.75)
                new_width = int(width * 0.75)
                frame = cv2.resize(frame, (new_width, new_height))
            elif gpu_utilization > 60:
                # Medium load - slight quality reduction
                height, width = frame.shape[:2]
                new_height = int(height * 0.9)
                new_width = int(width * 0.9)
                frame = cv2.resize(frame, (new_width, new_height))
            
            return frame
            
        except Exception as e:
            logger.error(f"Error applying adaptive quality: {e}")
            return frame
    
    async def _processing_callback(self, task: ProcessingTask) -> None:
        """Callback function for completed processing tasks"""
        try:
            if task.status == TaskStatus.COMPLETED:
                # Create result object
                result = StreamProcessingResult(
                    task_id=task.task_id,
                    camera_id=task.camera_id,
                    frame_timestamp=task.frame_data["timestamp"],
                    detections=task.result or [],
                    processing_time=(task.completed_at - task.started_at) if task.completed_at and task.started_at else 0,
                    metadata={
                        "frame_number": task.frame_data["frame_number"],
                        "gpu_id": task.gpu_id,
                        "worker_id": task.worker_id
                    }
                )
                
                # Add to results queue
                await self.results_queue.put(result)
                
                # Update stream statistics
                if task.camera_id in self.stream_stats:
                    stats = self.stream_stats[task.camera_id]
                    stats["frames_processed"] += 1
                    stats["detections_found"] += len(result.detections)
                    stats["last_processed"] = task.frame_data["timestamp"]
                    
                    # Update average processing time
                    total_time = stats["avg_processing_time"] * (stats["frames_processed"] - 1)
                    stats["avg_processing_time"] = (total_time + result.processing_time) / stats["frames_processed"]
                
                # Update system statistics
                self.system_stats["total_frames_processed"] += 1
                self.system_stats["total_detections"] += len(result.detections)
                
            elif task.status == TaskStatus.FAILED:
                logger.error(f"Task {task.task_id} failed: {task.error}")
                if task.camera_id in self.stream_stats:
                    self.stream_stats[task.camera_id]["errors"] += 1
            
            # Clean up task
            if task.task_id in self.processing_tasks:
                del self.processing_tasks[task.task_id]
                
        except Exception as e:
            logger.error(f"Error in processing callback: {e}")
    
    async def _result_handler_loop(self) -> None:
        """Handle processed results and save to database"""
        while self.running:
            try:
                # Get result from queue
                result = await asyncio.wait_for(self.results_queue.get(), timeout=1.0)
                
                # Process detections
                await self._handle_detections(result)
                
                # Update processing queue status
                await self._update_processing_queue(result)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Result handler error: {e}")
                await asyncio.sleep(1.0)
    
    async def _handle_detections(self, result: StreamProcessingResult) -> None:
        """Handle detection results and save to database"""
        try:
            if not result.detections:
                return
            
            async with async_session() as session:
                for detection_data in result.detections:
                    # Create detection record
                    detection = Detection(
                        camera_id=result.camera_id,
                        location_id=detection_data.get("location_id"),
                        plate_text=detection_data.get("plate_text", ""),
                        confidence=detection_data.get("confidence", 0.0),
                        timestamp=datetime.fromtimestamp(result.frame_timestamp),
                        box_x1=detection_data.get("box_x1"),
                        box_y1=detection_data.get("box_y1"),
                        box_x2=detection_data.get("box_x2"),
                        box_y2=detection_data.get("box_y2"),
                        processing_time_ms=result.processing_time * 1000,
                        processing_node=f"GPU-{result.metadata.get('gpu_id', 'unknown')}",
                        frame_id=result.metadata.get("frame_number"),
                        raw_text=detection_data.get("raw_text"),
                        ocr_results=detection_data.get("ocr_results", {})
                    )
                    
                    session.add(detection)
                
                await session.commit()
                
                # Broadcast detection results to WebSocket clients
                await self._broadcast_detection_results(result)
                
        except Exception as e:
            logger.error(f"Error handling detections: {e}")
    
    async def _broadcast_detection_results(self, result: StreamProcessingResult) -> None:
        """Broadcast detection results to WebSocket clients"""
        try:
            # Import here to avoid circular imports
            from app.main import websocket_multiplexer
            
            if websocket_multiplexer:
                broadcast_data = {
                    "camera_id": result.camera_id,
                    "timestamp": result.frame_timestamp,
                    "detections": result.detections,
                    "processing_time": result.processing_time,
                    "metadata": result.metadata
                }
                
                await websocket_multiplexer.broadcast_detection_result(broadcast_data)
                
        except Exception as e:
            logger.error(f"Error broadcasting detection results: {e}")
    
    async def _update_processing_queue(self, result: StreamProcessingResult) -> None:
        """Update processing queue status"""
        try:
            async with async_session() as session:
                # Find corresponding queue entry
                queue_result = await session.execute(
                    select(ProcessingQueue).where(
                        ProcessingQueue.camera_id == result.camera_id,
                        ProcessingQueue.status == ProcessingStatus.PROCESSING
                    ).order_by(ProcessingQueue.created_at.desc()).limit(1)
                )
                
                queue_entry = queue_result.scalar_one_or_none()
                
                if queue_entry:
                    # Update queue entry
                    await session.execute(
                        update(ProcessingQueue)
                        .where(ProcessingQueue.id == queue_entry.id)
                        .values(
                            status=ProcessingStatus.COMPLETED,
                            completed_at=datetime.utcnow(),
                            processing_time_ms=result.processing_time * 1000
                        )
                    )
                    
                    await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating processing queue: {e}")
    
    async def _monitor_loop(self) -> None:
        """Monitor system performance and update statistics"""
        while self.running:
            try:
                await self._update_system_stats()
                await asyncio.sleep(10.0)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(10.0)
    
    async def _update_system_stats(self) -> None:
        """Update system-wide statistics"""
        try:
            # Get GPU stats
            gpu_stats = self.gpu_manager.get_gpu_stats()
            self.system_stats["gpu_utilization"] = gpu_stats["performance"]["gpu_utilization"]
            self.system_stats["memory_usage"] = gpu_stats["performance"]["memory_usage"]
            
            # Calculate throughput
            total_frames = sum(stats["frames_processed"] for stats in self.stream_stats.values())
            if total_frames > 0:
                current_time = time.time()
                # Calculate frames processed in last minute
                recent_frames = 0
                for stats in self.stream_stats.values():
                    if current_time - stats["last_processed"] < 60:
                        recent_frames += 1
                
                self.system_stats["throughput"] = recent_frames / 60.0
            
            # Calculate average processing time
            if self.stream_stats:
                total_avg_time = sum(stats["avg_processing_time"] for stats in self.stream_stats.values())
                self.system_stats["avg_processing_time"] = total_avg_time / len(self.stream_stats)
            
        except Exception as e:
            logger.error(f"Error updating system stats: {e}")
    
    def _convert_priority(self, priority: Priority) -> TaskPriority:
        """Convert model priority to task priority"""
        priority_map = {
            Priority.LOW: TaskPriority.LOW,
            Priority.NORMAL: TaskPriority.NORMAL,
            Priority.HIGH: TaskPriority.HIGH,
            Priority.CRITICAL: TaskPriority.CRITICAL
        }
        return priority_map.get(priority, TaskPriority.NORMAL)
    
    async def process_frame_direct(self, camera_id: str, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Process a single frame directly (for testing or manual processing)
        
        Args:
            camera_id: ID of camera
            frame: Frame to process
            
        Returns:
            List of detection results
        """
        try:
            # Create processing task
            task = ProcessingTask(
                task_id=str(uuid.uuid4()),
                camera_id=camera_id,
                frame_data={
                    "frame": frame,
                    "timestamp": time.time(),
                    "camera_id": camera_id,
                    "frame_number": 0
                },
                priority=TaskPriority.HIGH
            )
            
            # Submit task and wait for result
            task_id = await self.gpu_manager.submit_task(task)
            
            # Wait for completion
            timeout = 30.0  # 30 second timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                status = await self.gpu_manager.get_task_status(task_id)
                if status == TaskStatus.COMPLETED:
                    result = await self.gpu_manager.get_task_result(task_id)
                    return result or []
                elif status == TaskStatus.FAILED:
                    raise Exception(f"Task failed")
                
                await asyncio.sleep(0.1)
            
            # Timeout
            await self.gpu_manager.cancel_task(task_id)
            raise TimeoutError("Frame processing timeout")
            
        except Exception as e:
            logger.error(f"Error processing frame directly: {e}")
            return []