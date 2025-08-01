"""
Recording Manager - Handles 24/7 continuous camera recording
Creates 10-minute video segments and maintains database index
"""
import asyncio
import cv2
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import time
from database.models import VideoRecording, Camera

logger = logging.getLogger(__name__)

class CameraRecorder:
    """Handles recording for a single camera"""
    
    def __init__(self, camera_config: dict, storage_path: str, db_service):
        self.camera_config = camera_config
        self.camera_id = camera_config['camera_id']
        self.name = camera_config['name']
        self.rtsp_url = self._build_rtsp_url()
        self.storage_path = Path(storage_path) / f"camera_{self.camera_id}"
        self.db_service = db_service
        
        # Recording state
        self.is_recording = False
        self.current_capture = None
        self.current_writer = None
        self.segment_start_time = None
        self.current_segment_path = None
        
        # Statistics
        self.total_segments = 0
        self.total_size_bytes = 0
        self.last_frame_time = None
        self.error_count = 0
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Camera recorder initialized: {self.name} ({self.camera_id})")
    
    def _build_rtsp_url(self) -> str:
        """Build RTSP URL from camera configuration"""
        config = self.camera_config
        username = config.get('username', '')
        password = config.get('password', '')
        ip_address = config.get('ip_address', '')
        port = config.get('port', 554)
        stream_path = config.get('stream_path', '/h264Preview_01_main')
        
        if username and password:
            auth = f"{username}:{password}@"
        else:
            auth = ""
        
        return f"rtsp://{auth}{ip_address}:{port}{stream_path}"
    
    async def start_recording(self):
        """Start continuous recording"""
        if self.is_recording:
            logger.warning(f"Recording already active for {self.name}")
            return
        
        self.is_recording = True
        logger.info(f"Starting recording for {self.name}")
        
        # Start recording loop in background
        asyncio.create_task(self._recording_loop())
    
    async def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        
        if self.current_writer:
            self.current_writer.release()
            self.current_writer = None
        
        if self.current_capture:
            self.current_capture.release()
            self.current_capture = None
        
        # Save current segment to database if exists
        if self.current_segment_path and self.segment_start_time:
            await self._save_segment_to_db()
        
        logger.info(f"Recording stopped for {self.name}")
    
    async def _recording_loop(self):
        """Main recording loop"""
        reconnect_delay = 5
        
        while self.is_recording:
            try:
                # Connect to camera
                if not await self._connect_to_camera():
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 1.5, 60)
                    continue
                
                reconnect_delay = 5  # Reset on successful connect
                self.error_count = 0
                
                # Start new segment
                await self._start_new_segment()
                
                # Record frames for this segment (10 minutes)
                segment_duration = 600  # 10 minutes in seconds
                segment_end_time = time.time() + segment_duration
                frame_count = 0
                
                while self.is_recording and time.time() < segment_end_time:
                    ret, frame = self.current_capture.read()
                    
                    if not ret or frame is None:
                        logger.warning(f"Failed to read frame from {self.name}")
                        break
                    
                    # Write frame to video file
                    if self.current_writer:
                        self.current_writer.write(frame)
                        frame_count += 1
                        self.last_frame_time = datetime.now()
                    
                    # Small delay to prevent overwhelming CPU
                    await asyncio.sleep(1/30)  # ~30 FPS
                
                # Finish current segment
                await self._finish_current_segment()
                
                logger.info(f"Completed segment for {self.name}: {frame_count} frames")
                
            except Exception as e:
                logger.error(f"Recording error for {self.name}: {e}")
                self.error_count += 1
                
                # Clean up on error
                if self.current_writer:
                    self.current_writer.release()
                    self.current_writer = None
                
                if self.current_capture:
                    self.current_capture.release()
                    self.current_capture = None
                
                # Wait before retry
                await asyncio.sleep(5)
    
    async def _connect_to_camera(self) -> bool:
        """Connect to camera via RTSP"""
        try:
            logger.info(f"Connecting to {self.name} at {self.rtsp_url}")
            
            self.current_capture = cv2.VideoCapture(self.rtsp_url)
            self.current_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.current_capture.isOpened():
                logger.error(f"Failed to open RTSP stream for {self.name}")
                return False
            
            # Test read
            ret, frame = self.current_capture.read()
            if not ret or frame is None:
                logger.error(f"Failed to read test frame from {self.name}")
                return False
            
            logger.info(f"Successfully connected to {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Connection error for {self.name}: {e}")
            return False
    
    async def _start_new_segment(self):
        """Start recording a new 10-minute segment"""
        now = datetime.now()
        self.segment_start_time = now
        
        # Create directory structure: YYYY/MM/DD/HH
        date_path = self.storage_path / now.strftime("%Y/%m/%d/%H")
        date_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename: camera_id_YYYYMMDD_HHMMSS_600.avi
        filename = f"camera_{self.camera_id}_{now.strftime('%Y%m%d_%H%M%S')}_600.avi"
        self.current_segment_path = date_path / filename
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.current_writer = cv2.VideoWriter(
            str(self.current_segment_path),
            fourcc,
            30.0,  # FPS
            (3840, 2160)  # 4K resolution
        )
        
        if not self.current_writer.isOpened():
            logger.error(f"Failed to initialize video writer for {self.name}")
            self.current_writer = None
            return
        
        logger.info(f"Started new segment: {self.current_segment_path}")
    
    async def _finish_current_segment(self):
        """Finish current segment and save to database"""
        if not self.current_writer or not self.current_segment_path:
            return
        
        # Release video writer
        self.current_writer.release()
        self.current_writer = None
        
        # Save segment metadata to database
        await self._save_segment_to_db()
        
        self.total_segments += 1
    
    async def _save_segment_to_db(self):
        """Save segment metadata to database"""
        if not self.current_segment_path or not self.segment_start_time:
            return
        
        try:
            # Get file size
            file_size = self.current_segment_path.stat().st_size
            self.total_size_bytes += file_size
            
            # Create database record
            segment_record = VideoRecording(
                filename=self.current_segment_path.name,
                camera_id=self.camera_id,
                file_path=str(self.current_segment_path.relative_to(Path.cwd())),
                start_time=self.segment_start_time,
                end_time=self.segment_start_time + timedelta(minutes=10),
                duration_seconds=600,  # 10 minutes
                file_size_bytes=file_size,
                video_codec='xvid',
                video_width=3840,
                video_height=2160,
                video_fps=30,
                is_compressed=True,
                has_audio=False
            )
            
            # Save to database
            async with self.db_service.get_session() as session:
                session.add(segment_record)
                await session.commit()
            
            logger.info(f"Saved segment to database: {self.current_segment_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to save segment to database: {e}")
    
    def get_status(self) -> Dict:
        """Get current recording status"""
        return {
            "camera_id": self.camera_id,
            "name": self.name,
            "is_recording": self.is_recording,
            "total_segments": self.total_segments,
            "total_size_bytes": self.total_size_bytes,
            "last_frame_time": self.last_frame_time.isoformat() if self.last_frame_time else None,
            "error_count": self.error_count,
            "current_segment": self.current_segment_path.name if self.current_segment_path else None
        }


class RecordingManager:
    """Manages recording for all cameras"""
    
    def __init__(self, db_service, storage_manager):
        self.db_service = db_service
        self.storage_manager = storage_manager
        self.camera_recorders: Dict[str, CameraRecorder] = {}
        self.is_running = False
        
        logger.info("Recording Manager initialized")
    
    async def start_recording(self):
        """Start recording for all configured cameras"""
        if self.is_running:
            logger.warning("Recording manager already running")
            return
        
        self.is_running = True
        logger.info("Starting recording manager...")
        
        # Load camera configurations from database
        cameras = await self._load_camera_configs()
        
        # Start recording for each camera
        for camera_config in cameras:
            camera_id = camera_config['camera_id']
            recorder = CameraRecorder(
                camera_config=camera_config,
                storage_path="recordings",
                db_service=self.db_service
            )
            
            self.camera_recorders[camera_id] = recorder
            await recorder.start_recording()
        
        logger.info(f"Started recording for {len(self.camera_recorders)} cameras")
    
    async def stop_recording(self):
        """Stop recording for all cameras"""
        self.is_running = False
        
        # Stop all camera recorders
        for recorder in self.camera_recorders.values():
            await recorder.stop_recording()
        
        self.camera_recorders.clear()
        logger.info("Recording manager stopped")
    
    async def _load_camera_configs(self) -> List[Dict]:
        """Load camera configurations from database using new Camera model"""
        try:
            # Get all active cameras using the database service
            cameras = await self.db_service.get_all_cameras()
            
            camera_configs = []
            for camera in cameras:
                # Skip inactive cameras
                if camera.status != 'active':
                    continue
                
                # Build camera configuration
                camera_config = {
                    'camera_id': camera.camera_id,
                    'name': camera.name,
                    'ip_address': camera.ip_address,
                    'port': camera.port or 554,
                    'connection_type': camera.connection_type or 'rtsp',
                    'stream_path': camera.stream_path or '/h264Preview_01_main',
                    'username': camera.username or 'admin',
                    'password': camera.password or '',
                    'location': camera.location or '',
                    # Video settings
                    'resolution_width': camera.resolution_width or 1920,
                    'resolution_height': camera.resolution_height or 1080,
                    'max_fps': camera.max_fps or 30,
                    'video_quality': camera.video_quality or 'medium',
                    'low_latency': camera.low_latency if camera.low_latency is not None else True
                }
                camera_configs.append(camera_config)
                
                logger.info(f"Loaded camera config: {camera.name} ({camera.camera_id}) at {camera.ip_address}:{camera.port}")
            
            logger.info(f"Loaded {len(camera_configs)} active camera configurations from database")
            return camera_configs
                
        except Exception as e:
            logger.error(f"Failed to load camera configs from database: {e}")
            return []
    
    async def add_camera(self, camera_id: str) -> bool:
        """Add a new camera to recording (hot reload)"""
        try:
            if camera_id in self.camera_recorders:
                logger.warning(f"Camera {camera_id} is already being recorded")
                return True
            
            # Get camera configuration from database
            camera = await self.db_service.get_camera(camera_id)
            if not camera or camera.status != 'active':
                logger.error(f"Camera {camera_id} not found or not active")
                return False
            
            # Build camera configuration
            camera_config = {
                'camera_id': camera.camera_id,
                'name': camera.name,
                'ip_address': camera.ip_address,
                'port': camera.port or 554,
                'connection_type': camera.connection_type or 'rtsp',
                'stream_path': camera.stream_path or '/h264Preview_01_main',
                'username': camera.username or 'admin',
                'password': camera.password or '',
                'location': camera.location or '',
                'resolution_width': camera.resolution_width or 1920,
                'resolution_height': camera.resolution_height or 1080,
                'max_fps': camera.max_fps or 30,
                'video_quality': camera.video_quality or 'medium',
                'low_latency': camera.low_latency if camera.low_latency is not None else True
            }
            
            # Create and start camera recorder
            recorder = CameraRecorder(
                camera_config=camera_config,
                storage_path="recordings",
                db_service=self.db_service
            )
            
            await recorder.start_recording()
            self.camera_recorders[camera_id] = recorder
            
            logger.info(f"Added camera {camera.name} ({camera_id}) to recording")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add camera {camera_id} to recording: {e}")
            return False
    
    async def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from recording (hot reload)"""
        try:
            if camera_id not in self.camera_recorders:
                logger.warning(f"Camera {camera_id} is not being recorded")
                return True
            
            # Stop and remove camera recorder
            recorder = self.camera_recorders[camera_id]
            await recorder.stop_recording()
            del self.camera_recorders[camera_id]
            
            logger.info(f"Removed camera {camera_id} from recording")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove camera {camera_id} from recording: {e}")
            return False
    
    async def reload_cameras(self) -> bool:
        """Reload all cameras from database (hot reload)"""
        try:
            logger.info("Reloading cameras from database...")
            
            # Get current camera configurations from database
            new_camera_configs = await self._load_camera_configs()
            new_camera_ids = {config['camera_id'] for config in new_camera_configs}
            current_camera_ids = set(self.camera_recorders.keys())
            
            # Remove cameras that are no longer active
            cameras_to_remove = current_camera_ids - new_camera_ids
            for camera_id in cameras_to_remove:
                await self.remove_camera(camera_id)
            
            # Add new cameras
            cameras_to_add = new_camera_ids - current_camera_ids
            for camera_id in cameras_to_add:
                await self.add_camera(camera_id)
            
            # Update existing cameras if needed (stop and restart with new config)
            cameras_to_update = current_camera_ids & new_camera_ids
            for camera_id in cameras_to_update:
                # Get new config for this camera
                new_config = next((c for c in new_camera_configs if c['camera_id'] == camera_id), None)
                if new_config:
                    # For now, restart the camera (could be optimized to only restart if config changed)
                    await self.remove_camera(camera_id)
                    await self.add_camera(camera_id)
            
            logger.info(f"Camera reload complete. Recording {len(self.camera_recorders)} cameras")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload cameras: {e}")
            return False

    def is_recording(self) -> bool:
        """Check if recording is active"""
        return self.is_running
    
    async def get_status_all_cameras(self) -> Dict:
        """Get recording status for all cameras"""
        cameras_status = {}
        for recorder in self.camera_recorders.values():
            cameras_status[recorder.camera_id] = recorder.get_status()
        
        return {
            "recording_active": self.is_running,
            "total_cameras": len(self.camera_recorders),
            "cameras": cameras_status
        }
    
    async def get_camera_status(self, camera_id: str) -> Optional[Dict]:
        """Get recording status for specific camera"""
        recorder = self.camera_recorders.get(camera_id)
        return recorder.get_status() if recorder else None