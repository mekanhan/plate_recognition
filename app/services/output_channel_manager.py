"""
Output Channel Manager for microservice integration.

This service manages multiple output channels for detection results, enabling:
- Local storage integration
- API endpoint buffering
- WebSocket broadcasting
- Webhook notifications
- Message queue integration
- File-based exports
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import aiohttp
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class OutputConfig:
	"""Configuration for an output channel."""
	name: str
	enabled: bool
	type: str  # 'storage', 'api', 'websocket', 'webhook', 'file'
	config: Dict[str, Any]

class OutputChannelManager:
	"""
	Manages multiple output channels for license plate detection results.
	
	Supports various output types:
	- Storage: Local database/file storage
	- API: Buffer for API endpoint access
	- WebSocket: Real-time broadcasting
	- Webhook: HTTP notifications to external services
	- File: Export to various file formats
	- MessageQueue: Integration with messaging systems
	"""
	
	def __init__(self):
		self.channels: Dict[str, OutputConfig] = {}
		self.is_running = False
		
		# Output buffers and queues
		self.api_buffer: List[Dict[str, Any]] = []
		self.websocket_connections: List[Any] = []
		self.pending_webhooks: List[Dict[str, Any]] = []
		
		# Statistics
		self.stats = {
			"total_outputs_sent": 0,
			"outputs_by_channel": {},
			"errors_by_channel": {},
			"last_output_time": None
		}
		
		# Processing configuration
		self.config = {
			"api_buffer_max_size": 1000,
			"webhook_timeout": 10.0,
			"webhook_retry_count": 3,
			"batch_processing_enabled": True,
			"batch_size": 10,
			"batch_timeout": 5.0
		}
		
		# Background tasks
		self.webhook_processor_task: Optional[asyncio.Task] = None
		self.batch_processor_task: Optional[asyncio.Task] = None
		
		logger.info("OutputChannelManager initialized")
	
	def add_channel(self, name: str, channel_type: str, config: Dict[str, Any], enabled: bool = True):
		"""
		Add an output channel.
		
		Args:
			name: Unique channel identifier
			channel_type: Type of channel ('storage', 'api', 'websocket', 'webhook', 'file')
			config: Channel-specific configuration
			enabled: Whether channel is active
		"""
		self.channels[name] = OutputConfig(
			name=name,
			enabled=enabled,
			type=channel_type,
			config=config
		)
		
		# Initialize statistics for this channel
		self.stats["outputs_by_channel"][name] = 0
		self.stats["errors_by_channel"][name] = 0
		
		logger.info(f"Added output channel: {name} ({channel_type})")
	
	def remove_channel(self, name: str):
		"""Remove an output channel."""
		if name in self.channels:
			del self.channels[name]
			logger.info(f"Removed output channel: {name}")
	
	def enable_channel(self, name: str):
		"""Enable an output channel."""
		if name in self.channels:
			self.channels[name].enabled = True
			logger.info(f"Enabled output channel: {name}")
	
	def disable_channel(self, name: str):
		"""Disable an output channel."""
		if name in self.channels:
			self.channels[name].enabled = False
			logger.info(f"Disabled output channel: {name}")
	
	async def start(self):
		"""Start the output channel manager."""
		if self.is_running:
			logger.warning("OutputChannelManager already running")
			return
		
		self.is_running = True
		
		# Start background processors
		self.webhook_processor_task = asyncio.create_task(self._webhook_processor())
		
		if self.config["batch_processing_enabled"]:
			self.batch_processor_task = asyncio.create_task(self._batch_processor())
		
		logger.info("OutputChannelManager started")
	
	async def stop(self):
		"""Stop the output channel manager."""
		if not self.is_running:
			return
		
		self.is_running = False
		
		# Cancel background tasks
		if self.webhook_processor_task:
			self.webhook_processor_task.cancel()
			try:
				await self.webhook_processor_task
			except asyncio.CancelledError:
				pass
		
		if self.batch_processor_task:
			self.batch_processor_task.cancel()
			try:
				await self.batch_processor_task
			except asyncio.CancelledError:
				pass
		
		# Process remaining webhooks
		await self._flush_pending_webhooks()
		
		logger.info("OutputChannelManager stopped")
	
	async def send_detection(self, detection_data: Dict[str, Any]):
		"""
		Send detection data to all enabled output channels.
		
		Args:
			detection_data: Detection information to output
		"""
		if not self.is_running:
			logger.warning("OutputChannelManager not running, skipping output")
			return
		
		self.stats["total_outputs_sent"] += 1
		self.stats["last_output_time"] = time.time()
		
		# Send to each enabled channel
		for channel_name, channel in self.channels.items():
			if not channel.enabled:
				continue
			
			try:
				await self._send_to_channel(channel, detection_data)
				self.stats["outputs_by_channel"][channel_name] += 1
				
			except Exception as e:
				logger.error(f"Error sending to channel {channel_name}: {e}")
				self.stats["errors_by_channel"][channel_name] += 1
	
	async def _send_to_channel(self, channel: OutputConfig, data: Dict[str, Any]):
		"""Send data to a specific output channel."""
		if channel.type == "storage":
			await self._send_to_storage(channel, data)
		elif channel.type == "api":
			await self._send_to_api_buffer(channel, data)
		elif channel.type == "websocket":
			await self._send_to_websocket(channel, data)
		elif channel.type == "webhook":
			await self._send_to_webhook(channel, data)
		elif channel.type == "file":
			await self._send_to_file(channel, data)
		else:
			logger.warning(f"Unknown channel type: {channel.type}")
	
	async def _send_to_storage(self, channel: OutputConfig, data: Dict[str, Any]):
		"""Send data to storage channel (handled by BackgroundStreamManager)."""
		# Storage is handled by the BackgroundStreamManager
		# This is just for statistics tracking
		pass
	
	async def _send_to_api_buffer(self, channel: OutputConfig, data: Dict[str, Any]):
		"""Add data to API buffer for endpoint access."""
		max_size = self.config["api_buffer_max_size"]
		
		# Add timestamp for API access
		api_data = {
			"timestamp": time.time(),
			"detection": data["detection"],
			"detection_id": data["detection_id"],
			"frame_number": data.get("frame_number", 0)
		}
		
		self.api_buffer.append(api_data)
		
		# Maintain buffer size
		if len(self.api_buffer) > max_size:
			self.api_buffer.pop(0)
		
		logger.debug(f"Added detection to API buffer (size: {len(self.api_buffer)})")
	
	async def _send_to_websocket(self, channel: OutputConfig, data: Dict[str, Any]):
		"""Broadcast data to WebSocket connections."""
		if not self.websocket_connections:
			return
		
		message = {
			"type": "detection",
			"timestamp": time.time(),
			"data": data["detection"]
		}
		
		message_json = json.dumps(message)
		
		# Broadcast to all connections
		for connection in self.websocket_connections[:]:  # Copy list to avoid modification issues
			try:
				await connection.send_text(message_json)
			except Exception as e:
				logger.debug(f"Removing dead WebSocket connection: {e}")
				if connection in self.websocket_connections:
					self.websocket_connections.remove(connection)
	
	async def _send_to_webhook(self, channel: OutputConfig, data: Dict[str, Any]):
		"""Queue webhook notification."""
		webhook_data = {
			"url": channel.config.get("url"),
			"method": channel.config.get("method", "POST"),
			"headers": channel.config.get("headers", {"Content-Type": "application/json"}),
			"payload": {
				"detection_id": data["detection_id"],
				"timestamp": data["timestamp"],
				"detection": data["detection"],
				"source": "lpr-system"
			},
			"retry_count": 0,
			"created_at": time.time()
		}
		
		self.pending_webhooks.append(webhook_data)
		logger.debug(f"Queued webhook for {webhook_data['url']}")
	
	async def _send_to_file(self, channel: OutputConfig, data: Dict[str, Any]):
		"""Export data to file."""
		try:
			file_path = channel.config.get("file_path", "detections.json")
			format_type = channel.config.get("format", "json")
			
			if format_type == "json":
				# Append to JSON file
				import aiofiles
				async with aiofiles.open(file_path, "a") as f:
					await f.write(json.dumps(data) + "\n")
			
			elif format_type == "csv":
				# Append to CSV file
				import aiofiles
				detection = data["detection"]
				csv_line = f"{data['timestamp']},{detection.get('plate_text', '')},{detection.get('confidence', 0)}\n"
				async with aiofiles.open(file_path, "a") as f:
					await f.write(csv_line)
			
			logger.debug(f"Exported detection to file: {file_path}")
			
		except Exception as e:
			logger.error(f"File export error: {e}")
			raise
	
	async def _webhook_processor(self):
		"""Background processor for webhook notifications."""
		while self.is_running:
			try:
				if self.pending_webhooks:
					webhook_data = self.pending_webhooks.pop(0)
					await self._process_webhook(webhook_data)
				else:
					await asyncio.sleep(0.1)
			except Exception as e:
				logger.error(f"Webhook processor error: {e}")
				await asyncio.sleep(1.0)
	
	async def _process_webhook(self, webhook_data: Dict[str, Any]):
		"""Process a single webhook notification."""
		try:
			async with aiohttp.ClientSession() as session:
				async with session.request(
					method=webhook_data["method"],
					url=webhook_data["url"],
					headers=webhook_data["headers"],
					json=webhook_data["payload"],
					timeout=self.config["webhook_timeout"]
				) as response:
					if response.status >= 400:
						raise aiohttp.ClientError(f"HTTP {response.status}")
					
					logger.debug(f"Webhook sent successfully to {webhook_data['url']}")
		
		except Exception as e:
			webhook_data["retry_count"] += 1
			
			if webhook_data["retry_count"] < self.config["webhook_retry_count"]:
				# Retry later
				self.pending_webhooks.append(webhook_data)
				logger.warning(f"Webhook failed, will retry: {e}")
			else:
				logger.error(f"Webhook failed permanently after {webhook_data['retry_count']} retries: {e}")
	
	async def _batch_processor(self):
		"""Background processor for batch operations."""
		batch = []
		last_batch_time = time.time()
		
		while self.is_running:
			try:
				# Check if batch should be processed
				current_time = time.time()
				should_process = (
					len(batch) >= self.config["batch_size"] or
					(batch and current_time - last_batch_time >= self.config["batch_timeout"])
				)
				
				if should_process and batch:
					await self._process_batch(batch)
					batch = []
					last_batch_time = current_time
				
				await asyncio.sleep(0.1)
				
			except Exception as e:
				logger.error(f"Batch processor error: {e}")
				await asyncio.sleep(1.0)
	
	async def _process_batch(self, batch: List[Dict[str, Any]]):
		"""Process a batch of detections."""
		logger.debug(f"Processing batch of {len(batch)} detections")
		
		# Example: Send batch to external analytics service
		# This can be customized based on requirements
		for item in batch:
			# Process each item in the batch
			pass
	
	async def _flush_pending_webhooks(self):
		"""Process all remaining webhook notifications."""
		logger.info("Flushing pending webhooks...")
		while self.pending_webhooks:
			webhook_data = self.pending_webhooks.pop(0)
			try:
				await self._process_webhook(webhook_data)
			except Exception as e:
				logger.error(f"Error flushing webhook: {e}")
	
	def get_api_buffer(self, limit: int = 100) -> List[Dict[str, Any]]:
		"""
		Get recent detections from API buffer.
		
		Args:
			limit: Maximum number of detections to return
			
		Returns:
			List of recent detection data
		"""
		return self.api_buffer[-limit:] if self.api_buffer else []
	
	def clear_api_buffer(self):
		"""Clear the API buffer."""
		self.api_buffer.clear()
		logger.info("API buffer cleared")
	
	def add_websocket_connection(self, websocket):
		"""Add a WebSocket connection for broadcasting."""
		self.websocket_connections.append(websocket)
		logger.debug(f"Added WebSocket connection (total: {len(self.websocket_connections)})")
	
	def remove_websocket_connection(self, websocket):
		"""Remove a WebSocket connection."""
		if websocket in self.websocket_connections:
			self.websocket_connections.remove(websocket)
			logger.debug(f"Removed WebSocket connection (total: {len(self.websocket_connections)})")
	
	def get_stats(self) -> Dict[str, Any]:
		"""Get output channel statistics."""
		return {
			"total_outputs_sent": self.stats["total_outputs_sent"],
			"outputs_by_channel": self.stats["outputs_by_channel"].copy(),
			"errors_by_channel": self.stats["errors_by_channel"].copy(),
			"last_output_time": self.stats["last_output_time"],
			"api_buffer_size": len(self.api_buffer),
			"websocket_connections": len(self.websocket_connections),
			"pending_webhooks": len(self.pending_webhooks),
			"channels": {name: {"enabled": ch.enabled, "type": ch.type} for name, ch in self.channels.items()}
		}
	
	def update_config(self, new_config: Dict[str, Any]):
		"""Update configuration parameters."""
		for key, value in new_config.items():
			if key in self.config:
				self.config[key] = value
				logger.info(f"Updated output config: {key} = {value}")