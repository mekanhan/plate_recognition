"""
Background Stream Manager for headless operation.

This service provides autonomous license plate detection processing that runs
independently of web UI requests, making it suitable for:
- Jetson Nano and embedded deployments
- Microservice architectures  
- Headless server environments
- Continuous monitoring applications
"""

import asyncio
import logging
import time
import uuid
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)

class BackgroundStreamManager:
	"""
	Manages autonomous background processing of video streams for license plate detection.
	
	This service operates independently of web requests and provides:
	- Continuous frame capture and processing
	- Autonomous detection pipeline
	- Resource management and optimization
	- Error recovery and health monitoring
	- Multiple output channel support
	"""
	
	def __init__(self, 
	             camera_service=None, 
	             detection_service=None, 
	             storage_service=None,
	             output_manager=None,
	             video_recording_service=None):
		self.camera_service = camera_service
		self.detection_service = detection_service
		self.storage_service = storage_service
		self.output_manager = output_manager
		self.video_recording_service = video_recording_service
		
		# Processing state
		self.is_running = False
		self.is_paused = False
		self.processing_task: Optional[asyncio.Task] = None
		
		# Configuration
		self.config = {
			"frame_skip": 5,  # Process every Nth frame
			"processing_interval": 0.033,  # ~30 FPS target
			"max_queue_size": 100,
			"error_recovery_delay": 5.0,
			"health_check_interval": 30.0,
			"enable_performance_metrics": True,
			"cooldown_period": 5.0,  # From stream.py plate tracker
			"confidence_threshold": 0.5,  # From stream.py plate tracker
			"process_interval": 2.0  # From stream.py plate tracker
		}
		
		# State tracking
		self.stats = {
			"total_frames_processed": 0,
			"total_detections": 0,
			"start_time": None,
			"last_detection_time": None,
			"processing_time_ms": 0.0,
			"errors": 0,
			"restarts": 0
		}
		
		# Frame processing control
		self.frame_counter = 0
		self.detection_queue: List[Dict[Any, Any]] = []
		self.processing_lock = asyncio.Lock()
		
		# License plate tracking for deduplication (from stream.py)
		self.plate_tracker = {
			"last_seen": {},       # Maps plate text to last seen timestamp
			"cooldown_period": self.config["cooldown_period"], # Only store the same plate again after N seconds
			"confidence_threshold": self.config["confidence_threshold"], # Minimum confidence to store a plate
			"last_process_time": 0, # Last time we processed the queue
			"process_interval": self.config["process_interval"], # Process queue every N seconds
			"detection_queue": [],   # Queue of detections waiting to be processed
			"processing_lock": asyncio.Lock()  # Lock to prevent concurrent processing
		}
		
		# Health monitoring
		self.health_task: Optional[asyncio.Task] = None
		self.last_health_check = time.time()
		
		logger.info("BackgroundStreamManager initialized")
	
	async def start(self) -> bool:
		"""
		Start the background processing service.
		
		Returns:
			bool: True if started successfully, False otherwise
		"""
		if self.is_running:
			logger.warning("Background stream manager is already running")
			return False
		
		if not self._validate_services():
			logger.error("Required services not available for background processing")
			return False
		
		try:
			self.is_running = True
			self.is_paused = False
			self.stats["start_time"] = time.time()
			
			# Start main processing loop
			self.processing_task = asyncio.create_task(self._processing_loop())
			
			# Start health monitoring
			self.health_task = asyncio.create_task(self._health_monitor())
			
			logger.info("Background stream processing started")
			return True
			
		except Exception as e:
			logger.error(f"Failed to start background stream manager: {e}")
			self.is_running = False
			return False
	
	async def stop(self) -> bool:
		"""
		Stop the background processing service gracefully.
		
		Returns:
			bool: True if stopped successfully, False otherwise
		"""
		if not self.is_running:
			logger.warning("Background stream manager is not running")
			return False
		
		try:
			logger.info("Stopping background stream processing...")
			self.is_running = False
			
			# Cancel tasks
			if self.processing_task and not self.processing_task.done():
				self.processing_task.cancel()
				try:
					await self.processing_task
				except asyncio.CancelledError:
					pass
			
			if self.health_task and not self.health_task.done():
				self.health_task.cancel()
				try:
					await self.health_task
				except asyncio.CancelledError:
					pass
			
			# Process remaining detections
			await self._flush_detection_queue()
			
			logger.info("Background stream processing stopped")
			return True
			
		except Exception as e:
			logger.error(f"Error stopping background stream manager: {e}")
			return False
	
	async def pause(self) -> bool:
		"""Pause processing without stopping the service."""
		if not self.is_running:
			return False
		
		self.is_paused = True
		logger.info("Background processing paused")
		return True
	
	async def resume(self) -> bool:
		"""Resume processing if paused."""
		if not self.is_running:
			return False
		
		self.is_paused = False
		logger.info("Background processing resumed")
		return True
	
	def get_status(self) -> Dict[str, Any]:
		"""
		Get current status and statistics.
		
		Returns:
			Dict containing status information
		"""
		uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
		
		return {
			"is_running": self.is_running,
			"is_paused": self.is_paused,
			"uptime_seconds": uptime,
			"stats": self.stats.copy(),
			"config": self.config.copy(),
			"queue_size": len(self.detection_queue),
			"services_available": self._validate_services(),
			"last_health_check": self.last_health_check
		}
	
	def update_config(self, new_config: Dict[str, Any]) -> bool:
		"""
		Update configuration parameters.
		
		Args:
			new_config: Dictionary of configuration updates
			
		Returns:
			bool: True if updated successfully
		"""
		try:
			for key, value in new_config.items():
				if key in self.config:
					self.config[key] = value
					logger.info(f"Updated config: {key} = {value}")
					
					# Update plate tracker config as well
					if key in ["cooldown_period", "confidence_threshold", "process_interval"]:
						self.plate_tracker[key] = value
						logger.info(f"Updated plate tracker: {key} = {value}")
				else:
					logger.warning(f"Unknown config key: {key}")
			return True
		except Exception as e:
			logger.error(f"Failed to update config: {e}")
			return False
	
	async def _processing_loop(self):
		"""Main processing loop for continuous frame analysis."""
		logger.info("Starting main processing loop")
		
		while self.is_running:
			try:
				if self.is_paused:
					await asyncio.sleep(1.0)
					continue
				
				# Capture frame
				start_time = time.time()
				frame, timestamp = await self.camera_service.get_frame()
				
				# Frame skipping for performance
				self.frame_counter += 1
				should_process = self.frame_counter % self.config["frame_skip"] == 0
				
				if should_process:
					# Process frame for detections
					await self._process_frame(frame, timestamp)
				
				# Send frame to video recording service (every frame, not just processed ones)
				if self.video_recording_service:
					try:
						await self.video_recording_service.add_frame(frame, timestamp)
					except Exception as e:
						logger.debug(f"Error adding frame to video recording: {e}")
				
				# Performance tracking
				processing_time = (time.time() - start_time) * 1000
				self.stats["processing_time_ms"] = processing_time
				self.stats["total_frames_processed"] += 1
				
				# Process plate tracker queue periodically (like stream.py)
				if len(self.plate_tracker["detection_queue"]) > 0:
					asyncio.create_task(self._process_plate_tracker_queue())
				
				# Adaptive sleep to maintain target frame rate
				sleep_time = max(0.001, self.config["processing_interval"] - (time.time() - start_time))
				await asyncio.sleep(sleep_time)
				
			except Exception as e:
				logger.error(f"Error in processing loop: {e}")
				self.stats["errors"] += 1
				await asyncio.sleep(self.config["error_recovery_delay"])
	
	async def _process_frame(self, frame, timestamp):
		"""Process a single frame for license plate detection."""
		try:
			if not self.detection_service:
				return
			
			# Run detection
			processed_frame, detections = await self.detection_service.process_frame(frame)
			
			# Add valid detections to the plate tracker queue (like stream.py)
			if detections:
				for detection in detections:
					if detection.get("plate_text") and detection.get("confidence", 0) > 0:
						# Add timestamp if not present
						if "timestamp" not in detection:
							detection["timestamp"] = timestamp
						
						# Add frame info
						detection["frame_id"] = self.frame_counter
						if "detection_id" not in detection:
							detection["detection_id"] = str(uuid.uuid4())
						
						# Add to plate tracker queue
						self.plate_tracker["detection_queue"].append(detection)
						
						# Increment detection counter
						self.stats["total_detections"] += 1
			
		except Exception as e:
			logger.error(f"Frame processing error: {e}")
			self.stats["errors"] += 1
	
	async def _queue_detection(self, detection_data):
		"""Add detection to processing queue."""
		async with self.processing_lock:
			if len(self.detection_queue) < self.config["max_queue_size"]:
				self.detection_queue.append(detection_data)
			else:
				# Remove oldest detection if queue is full
				self.detection_queue.pop(0)
				self.detection_queue.append(detection_data)
				logger.warning("Detection queue full, removed oldest entry")
	
	async def _process_detection_queue(self):
		"""Process queued detections."""
		async with self.processing_lock:
			while self.detection_queue:
				detection_data = self.detection_queue.pop(0)
				
				try:
					# Store detection
					if self.storage_service:
						await self._store_detection(detection_data)
					
					# Send to output channels
					if self.output_manager:
						await self.output_manager.send_detection(detection_data)
					
					# Update statistics
					self.stats["total_detections"] += 1
					self.stats["last_detection_time"] = time.time()
					
					logger.info(f"Processed detection: {detection_data['detection'].get('plate_text', 'Unknown')}")
					
				except Exception as e:
					logger.error(f"Error processing detection: {e}")
					self.stats["errors"] += 1
	
	async def _process_plate_tracker_queue(self):
		"""Process any pending detections in the plate tracker queue (from stream.py)"""
		current_time = time.time()

		# Only process if enough time has passed since last processing
		if current_time - self.plate_tracker["last_process_time"] < self.plate_tracker["process_interval"]:
			return

		# Try to acquire the lock, but don't block if already processing
		if self.plate_tracker["processing_lock"].locked():
			return  # Skip if already processing

		async with self.plate_tracker["processing_lock"]:
			# Update last process time
			self.plate_tracker["last_process_time"] = current_time

			# Get the current queue and clear it
			queue = self.plate_tracker["detection_queue"].copy()
			self.plate_tracker["detection_queue"] = []

			if not queue:
				return

			logger.info(f"Processing {len(queue)} detections from plate tracker queue")

			# Group by plate text to find the best confidence for each plate
			plates_to_process = {}
			for detection in queue:
				plate_text = detection.get("plate_text", "").upper()
				if not plate_text:
					continue

				# Check if this is a better detection than what we already have
				current_confidence = detection.get("confidence", 0)
				if (plate_text not in plates_to_process or
					current_confidence > plates_to_process[plate_text].get("confidence", 0)):
					plates_to_process[plate_text] = detection

			# Process each unique plate (best confidence version)
			for plate_text, detection in plates_to_process.items():
				# Skip low confidence detections
				confidence = detection.get("confidence", 0)
				if confidence < self.plate_tracker["confidence_threshold"]:
					logger.debug(f"Skipping low confidence detection: {plate_text} ({confidence:.2f})")
					continue

				# Check cooldown period
				last_seen = self.plate_tracker["last_seen"].get(plate_text, 0)
				if current_time - last_seen < self.plate_tracker["cooldown_period"]:
					logger.debug(f"Skipping plate in cooldown: {plate_text}")
					continue

				# Update last seen time
				self.plate_tracker["last_seen"][plate_text] = current_time

				# Store this detection using storage service directly
				if self.storage_service:
					try:
						logger.info(f"Storing plate: {plate_text} (Confidence: {confidence:.2f})")
						await self.storage_service.add_detections([detection])
						
						# Trigger video recording if video service is available
						if self.video_recording_service:
							try:
								logger.info(f"Triggering video recording for detection {detection['detection_id']}")
								await self.video_recording_service.trigger_recording(detection['detection_id'])
							except Exception as e:
								logger.error(f"Error triggering video recording: {e}")
						
						# Send to output channels
						if self.output_manager:
							detection_data = {
								"detection_id": detection["detection_id"],
								"timestamp": detection["timestamp"],
								"detection": detection,
								"frame_number": detection.get("frame_id", 0)
							}
							await self.output_manager.send_detection(detection_data)
							
					except Exception as e:
						logger.error(f"Error storing detection: {e}")
						self.stats["errors"] += 1

	async def _store_detection(self, detection_data):
		"""Store detection using storage service."""
		try:
			# Use storage service directly instead of detection service
			await self.storage_service.add_detections([detection_data["detection"]])
		except Exception as e:
			logger.error(f"Storage error: {e}")
			raise
	
	async def _flush_detection_queue(self):
		"""Process all remaining detections in queue."""
		logger.info("Flushing remaining detection queue...")
		# Process old detection queue if any
		while self.detection_queue:
			await self._process_detection_queue()
			await asyncio.sleep(0.1)
		
		# Process plate tracker queue
		while self.plate_tracker["detection_queue"]:
			await self._process_plate_tracker_queue()
			await asyncio.sleep(0.1)
	
	async def _health_monitor(self):
		"""Monitor service health and performance."""
		while self.is_running:
			try:
				self.last_health_check = time.time()
				
				# Check service availability
				if not self._validate_services():
					logger.warning("Service validation failed during health check")
				
				# Log statistics periodically
				if self.config["enable_performance_metrics"]:
					uptime = time.time() - self.stats["start_time"]
					logger.info(f"Health check - Uptime: {uptime:.1f}s, "
					          f"Frames: {self.stats['total_frames_processed']}, "
					          f"Detections: {self.stats['total_detections']}, "
					          f"Errors: {self.stats['errors']}")
				
				await asyncio.sleep(self.config["health_check_interval"])
				
			except Exception as e:
				logger.error(f"Health monitor error: {e}")
				await asyncio.sleep(5.0)
	
	def _validate_services(self) -> bool:
		"""Validate that required services are available."""
		required_services = [
			("camera_service", self.camera_service),
			("detection_service", self.detection_service)
		]
		
		for name, service in required_services:
			if service is None:
				logger.error(f"Required service not available: {name}")
				return False
		
		return True
	
	def set_services(self, camera_service=None, detection_service=None, 
	                storage_service=None, output_manager=None, video_recording_service=None):
		"""Update service references."""
		if camera_service:
			self.camera_service = camera_service
		if detection_service:
			self.detection_service = detection_service
		if storage_service:
			self.storage_service = storage_service
		if output_manager:
			self.output_manager = output_manager
		if video_recording_service:
			self.video_recording_service = video_recording_service
		
		logger.info("Background stream manager services updated")