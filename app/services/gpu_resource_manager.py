# app/services/gpu_resource_manager.py
# GPU resource management for multi-stream processing
import asyncio
import logging
import time
import psutil
import torch
import threading
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProcessingTask:
    """Represents a processing task for GPU execution"""
    task_id: str
    camera_id: str
    frame_data: Any
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    assigned_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    gpu_id: Optional[int] = None
    worker_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0  # seconds
    callback: Optional[callable] = None

@dataclass
class GPUInfo:
    """Information about a GPU device"""
    gpu_id: int
    name: str
    memory_total: int  # MB
    memory_used: int  # MB
    memory_free: int  # MB
    utilization: float  # percentage
    temperature: float  # celsius
    power_usage: float  # watts
    compute_capability: Tuple[int, int]
    is_available: bool = True
    last_updated: float = field(default_factory=time.time)

@dataclass
class WorkerInfo:
    """Information about a processing worker"""
    worker_id: str
    gpu_id: int
    process_id: int
    is_busy: bool = False
    current_task: Optional[ProcessingTask] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_processing_time: float = 0.0
    last_activity: float = field(default_factory=time.time)
    queue_length: int = 0

class GPUResourceManager:
    """
    Manages GPU resources for multi-stream processing
    Handles task scheduling, load balancing, and resource monitoring
    """
    
    def __init__(self, max_workers_per_gpu: int = 2):
        self.max_workers_per_gpu = max_workers_per_gpu
        self.gpus: Dict[int, GPUInfo] = {}
        self.workers: Dict[str, WorkerInfo] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.pending_tasks: Dict[str, ProcessingTask] = {}
        self.completed_tasks: Dict[str, ProcessingTask] = {}
        self.processing_tasks: Dict[str, ProcessingTask] = {}
        
        # Scheduling and monitoring
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_processing_time": 0.0,
            "avg_queue_time": 0.0,
            "throughput": 0.0,  # tasks per second
            "gpu_utilization": 0.0,
            "memory_usage": 0.0
        }
        
        # Thread safety
        self.lock = threading.Lock()
        
    async def initialize(self) -> None:
        """Initialize the GPU resource manager"""
        logger.info("Initializing GPU Resource Manager...")
        
        try:
            # Detect available GPUs
            await self._detect_gpus()
            
            # Initialize workers
            await self._initialize_workers()
            
            # Start background tasks
            self.running = True
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info(f"GPU Resource Manager initialized with {len(self.gpus)} GPUs and {len(self.workers)} workers")
            
        except Exception as e:
            logger.error(f"Failed to initialize GPU Resource Manager: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the GPU resource manager"""
        logger.info("Shutting down GPU Resource Manager...")
        
        self.running = False
        
        # Cancel pending tasks
        while not self.task_queue.empty():
            try:
                task = await self.task_queue.get()
                task.status = TaskStatus.CANCELLED
                self.task_queue.task_done()
            except:
                break
        
        # Cancel background tasks
        for task in [self.scheduler_task, self.monitor_task, self.cleanup_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Clean up workers
        await self._cleanup_workers()
        
        logger.info("GPU Resource Manager shutdown complete")
    
    async def submit_task(self, task: ProcessingTask) -> str:
        """
        Submit a processing task to the queue
        
        Args:
            task: Processing task to submit
            
        Returns:
            Task ID
        """
        with self.lock:
            self.pending_tasks[task.task_id] = task
            self.stats["total_tasks"] += 1
        
        await self.task_queue.put(task)
        logger.debug(f"Task {task.task_id} submitted to queue")
        return task.task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task"""
        with self.lock:
            if task_id in self.pending_tasks:
                return self.pending_tasks[task_id].status
            elif task_id in self.processing_tasks:
                return self.processing_tasks[task_id].status
            elif task_id in self.completed_tasks:
                return self.completed_tasks[task_id].status
            return None
    
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get the result of a completed task"""
        with self.lock:
            if task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                if task.status == TaskStatus.COMPLETED:
                    return task.result
                elif task.status == TaskStatus.FAILED:
                    raise Exception(f"Task failed: {task.error}")
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or processing task"""
        with self.lock:
            if task_id in self.pending_tasks:
                task = self.pending_tasks[task_id]
                if task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
                    task.status = TaskStatus.CANCELLED
                    return True
            elif task_id in self.processing_tasks:
                task = self.processing_tasks[task_id]
                if task.status == TaskStatus.PROCESSING:
                    task.status = TaskStatus.CANCELLED
                    return True
            return False
    
    async def get_optimal_gpu(self, task: ProcessingTask) -> Optional[int]:
        """
        Select the optimal GPU for a task based on current load
        
        Args:
            task: Processing task
            
        Returns:
            GPU ID or None if no GPU available
        """
        best_gpu = None
        best_score = float('inf')
        
        for gpu_id, gpu_info in self.gpus.items():
            if not gpu_info.is_available:
                continue
            
            # Calculate GPU workers load
            gpu_workers = [w for w in self.workers.values() if w.gpu_id == gpu_id]
            busy_workers = sum(1 for w in gpu_workers if w.is_busy)
            
            if busy_workers >= self.max_workers_per_gpu:
                continue
            
            # Calculate load score (lower is better)
            memory_usage = gpu_info.memory_used / gpu_info.memory_total
            utilization = gpu_info.utilization / 100.0
            queue_length = sum(w.queue_length for w in gpu_workers)
            
            # Weighted score
            score = (memory_usage * 0.4) + (utilization * 0.3) + (queue_length * 0.3)
            
            if score < best_score:
                best_score = score
                best_gpu = gpu_id
        
        return best_gpu
    
    async def get_available_worker(self, gpu_id: int) -> Optional[str]:
        """Get an available worker for a specific GPU"""
        gpu_workers = [w for w in self.workers.values() if w.gpu_id == gpu_id and not w.is_busy]
        
        if not gpu_workers:
            return None
        
        # Select worker with least queue length
        best_worker = min(gpu_workers, key=lambda w: w.queue_length)
        return best_worker.worker_id
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """Get current GPU statistics"""
        with self.lock:
            return {
                "gpus": {
                    gpu_id: {
                        "name": gpu.name,
                        "memory_total": gpu.memory_total,
                        "memory_used": gpu.memory_used,
                        "memory_free": gpu.memory_free,
                        "utilization": gpu.utilization,
                        "temperature": gpu.temperature,
                        "is_available": gpu.is_available
                    }
                    for gpu_id, gpu in self.gpus.items()
                },
                "workers": {
                    worker_id: {
                        "gpu_id": worker.gpu_id,
                        "is_busy": worker.is_busy,
                        "tasks_completed": worker.tasks_completed,
                        "tasks_failed": worker.tasks_failed,
                        "avg_processing_time": worker.avg_processing_time,
                        "queue_length": worker.queue_length
                    }
                    for worker_id, worker in self.workers.items()
                },
                "queue_stats": {
                    "pending_tasks": len(self.pending_tasks),
                    "processing_tasks": len(self.processing_tasks),
                    "completed_tasks": len(self.completed_tasks),
                    "queue_size": self.task_queue.qsize()
                },
                "performance": self.stats.copy()
            }
    
    async def _detect_gpus(self) -> None:
        """Detect available GPU devices"""
        try:
            if not torch.cuda.is_available():
                logger.warning("CUDA not available - falling back to CPU processing")
                return
            
            device_count = torch.cuda.device_count()
            logger.info(f"Detected {device_count} GPU devices")
            
            for gpu_id in range(device_count):
                try:
                    # Get GPU properties
                    props = torch.cuda.get_device_properties(gpu_id)
                    
                    # Get memory info
                    torch.cuda.set_device(gpu_id)
                    memory_total = torch.cuda.get_device_properties(gpu_id).total_memory // (1024 ** 2)  # MB
                    memory_used = torch.cuda.memory_allocated(gpu_id) // (1024 ** 2)  # MB
                    memory_free = memory_total - memory_used
                    
                    # Create GPU info
                    gpu_info = GPUInfo(
                        gpu_id=gpu_id,
                        name=props.name,
                        memory_total=memory_total,
                        memory_used=memory_used,
                        memory_free=memory_free,
                        utilization=0.0,  # Will be updated by monitoring
                        temperature=0.0,  # Will be updated by monitoring
                        power_usage=0.0,  # Will be updated by monitoring
                        compute_capability=(props.major, props.minor),
                        is_available=True
                    )
                    
                    self.gpus[gpu_id] = gpu_info
                    logger.info(f"GPU {gpu_id}: {props.name} ({memory_total}MB)")
                    
                except Exception as e:
                    logger.error(f"Error detecting GPU {gpu_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error detecting GPUs: {e}")
    
    async def _initialize_workers(self) -> None:
        """Initialize worker processes for each GPU"""
        for gpu_id in self.gpus.keys():
            for worker_idx in range(self.max_workers_per_gpu):
                worker_id = f"worker_{gpu_id}_{worker_idx}"
                
                worker_info = WorkerInfo(
                    worker_id=worker_id,
                    gpu_id=gpu_id,
                    process_id=0,  # Will be set when worker starts
                    is_busy=False,
                    tasks_completed=0,
                    tasks_failed=0,
                    avg_processing_time=0.0,
                    queue_length=0
                )
                
                self.workers[worker_id] = worker_info
                logger.debug(f"Initialized worker: {worker_id} on GPU {gpu_id}")
    
    async def _scheduler_loop(self) -> None:
        """Main scheduling loop"""
        while self.running:
            try:
                # Get next task from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Skip cancelled tasks
                if task.status == TaskStatus.CANCELLED:
                    self.task_queue.task_done()
                    continue
                
                # Find optimal GPU
                optimal_gpu = await self.get_optimal_gpu(task)
                if optimal_gpu is None:
                    # No GPU available, put task back in queue
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.1)
                    continue
                
                # Find available worker
                worker_id = await self.get_available_worker(optimal_gpu)
                if worker_id is None:
                    # No worker available, put task back in queue
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.1)
                    continue
                
                # Assign task to worker
                await self._assign_task_to_worker(task, worker_id)
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(1.0)
    
    async def _assign_task_to_worker(self, task: ProcessingTask, worker_id: str) -> None:
        """Assign a task to a specific worker"""
        try:
            worker = self.workers[worker_id]
            
            # Update task status
            task.status = TaskStatus.ASSIGNED
            task.assigned_at = time.time()
            task.gpu_id = worker.gpu_id
            task.worker_id = worker_id
            
            # Move task to processing queue
            with self.lock:
                if task.task_id in self.pending_tasks:
                    del self.pending_tasks[task.task_id]
                self.processing_tasks[task.task_id] = task
            
            # Update worker status
            worker.is_busy = True
            worker.current_task = task
            worker.queue_length += 1
            
            # Start processing task
            asyncio.create_task(self._process_task(task))
            
            logger.debug(f"Task {task.task_id} assigned to worker {worker_id} on GPU {worker.gpu_id}")
            
        except Exception as e:
            logger.error(f"Error assigning task to worker: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
    
    async def _process_task(self, task: ProcessingTask) -> None:
        """Process a task using the assigned worker"""
        worker = self.workers[task.worker_id]
        
        try:
            # Update task status
            task.status = TaskStatus.PROCESSING
            task.started_at = time.time()
            
            # TODO: Implement actual GPU processing here
            # This is where you would integrate with your detection service
            # For now, simulate processing
            processing_time = await self._simulate_processing(task)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            
            # Update worker statistics
            worker.tasks_completed += 1
            worker.avg_processing_time = (
                (worker.avg_processing_time * (worker.tasks_completed - 1) + processing_time) /
                worker.tasks_completed
            )
            
            # Execute callback if provided
            if task.callback:
                try:
                    await task.callback(task)
                except Exception as e:
                    logger.error(f"Task callback error: {e}")
            
            # Move task to completed queue
            with self.lock:
                if task.task_id in self.processing_tasks:
                    del self.processing_tasks[task.task_id]
                self.completed_tasks[task.task_id] = task
                self.stats["completed_tasks"] += 1
            
            logger.debug(f"Task {task.task_id} completed in {processing_time:.2f}s")
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task.task_id} timed out")
            task.status = TaskStatus.FAILED
            task.error = "Task timeout"
            worker.tasks_failed += 1
            
        except Exception as e:
            logger.error(f"Task {task.task_id} processing error: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            worker.tasks_failed += 1
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                await self.task_queue.put(task)
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")
            else:
                with self.lock:
                    if task.task_id in self.processing_tasks:
                        del self.processing_tasks[task.task_id]
                    self.completed_tasks[task.task_id] = task
                    self.stats["failed_tasks"] += 1
        
        finally:
            # Reset worker status
            worker.is_busy = False
            worker.current_task = None
            worker.queue_length = max(0, worker.queue_length - 1)
            worker.last_activity = time.time()
    
    async def _simulate_processing(self, task: ProcessingTask) -> float:
        """Simulate GPU processing (replace with actual detection logic)"""
        # Simulate processing time based on task priority
        if task.priority == TaskPriority.CRITICAL:
            await asyncio.sleep(0.1)
            return 0.1
        elif task.priority == TaskPriority.HIGH:
            await asyncio.sleep(0.2)
            return 0.2
        elif task.priority == TaskPriority.NORMAL:
            await asyncio.sleep(0.3)
            return 0.3
        else:  # LOW
            await asyncio.sleep(0.5)
            return 0.5
    
    async def _monitor_loop(self) -> None:
        """Monitor GPU usage and update statistics"""
        while self.running:
            try:
                await self._update_gpu_stats()
                await self._update_performance_stats()
                await asyncio.sleep(5.0)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5.0)
    
    async def _update_gpu_stats(self) -> None:
        """Update GPU utilization and memory statistics"""
        for gpu_id, gpu_info in self.gpus.items():
            try:
                torch.cuda.set_device(gpu_id)
                
                # Update memory usage
                gpu_info.memory_used = torch.cuda.memory_allocated(gpu_id) // (1024 ** 2)
                gpu_info.memory_free = gpu_info.memory_total - gpu_info.memory_used
                
                # Update utilization (simplified - would need nvidia-ml-py for accurate data)
                gpu_workers = [w for w in self.workers.values() if w.gpu_id == gpu_id]
                busy_workers = sum(1 for w in gpu_workers if w.is_busy)
                gpu_info.utilization = (busy_workers / self.max_workers_per_gpu) * 100
                
                gpu_info.last_updated = time.time()
                
            except Exception as e:
                logger.error(f"Error updating GPU {gpu_id} stats: {e}")
                gpu_info.is_available = False
    
    async def _update_performance_stats(self) -> None:
        """Update overall performance statistics"""
        try:
            with self.lock:
                total_tasks = self.stats["total_tasks"]
                completed_tasks = self.stats["completed_tasks"]
                failed_tasks = self.stats["failed_tasks"]
                
                if total_tasks > 0:
                    # Calculate average processing time
                    total_processing_time = sum(
                        (task.completed_at - task.started_at) 
                        for task in self.completed_tasks.values()
                        if task.started_at and task.completed_at
                    )
                    
                    if completed_tasks > 0:
                        self.stats["avg_processing_time"] = total_processing_time / completed_tasks
                    
                    # Calculate throughput (tasks per second)
                    current_time = time.time()
                    recent_tasks = [
                        task for task in self.completed_tasks.values()
                        if task.completed_at and current_time - task.completed_at < 60
                    ]
                    self.stats["throughput"] = len(recent_tasks) / 60.0
                
                # Calculate overall GPU utilization
                if self.gpus:
                    self.stats["gpu_utilization"] = sum(
                        gpu.utilization for gpu in self.gpus.values()
                    ) / len(self.gpus)
                
                # Calculate memory usage
                if self.gpus:
                    total_memory = sum(gpu.memory_total for gpu in self.gpus.values())
                    used_memory = sum(gpu.memory_used for gpu in self.gpus.values())
                    self.stats["memory_usage"] = (used_memory / total_memory) * 100 if total_memory > 0 else 0
                
        except Exception as e:
            logger.error(f"Error updating performance stats: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Clean up old completed tasks"""
        while self.running:
            try:
                current_time = time.time()
                cleanup_threshold = current_time - 3600  # 1 hour
                
                with self.lock:
                    # Remove old completed tasks
                    expired_tasks = [
                        task_id for task_id, task in self.completed_tasks.items()
                        if task.completed_at and task.completed_at < cleanup_threshold
                    ]
                    
                    for task_id in expired_tasks:
                        del self.completed_tasks[task_id]
                
                if expired_tasks:
                    logger.debug(f"Cleaned up {len(expired_tasks)} expired tasks")
                
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_workers(self) -> None:
        """Clean up worker processes"""
        for worker_id, worker in self.workers.items():
            try:
                if worker.current_task:
                    worker.current_task.status = TaskStatus.CANCELLED
                worker.is_busy = False
                worker.current_task = None
                
            except Exception as e:
                logger.error(f"Error cleaning up worker {worker_id}: {e}")