# app/services/stream_preview_service.py
"""
Stream preview service for managing temporary camera preview sessions.
Provides snapshot capture, stream stability testing, and session management.
"""
import asyncio
import cv2
import logging
import time
import threading
import uuid
import base64
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PreviewSession:
    """Active preview session"""
    session_id: str
    camera_config: Dict[str, Any]
    stream_url: str
    created_at: datetime
    last_accessed: datetime
    is_active: bool = True
    frame_count: int = 0
    error_count: int = 0
    current_frame: Optional[np.ndarray] = None
    frame_timestamp: Optional[datetime] = None
    
@dataclass
class SnapshotResult:
    """Result of snapshot capture"""
    success: bool
    session_id: str
    snapshot_data: Optional[bytes] = None
    file_path: Optional[str] = None
    timestamp: datetime = None
    error_message: Optional[str] = None
    frame_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class StabilityResult:
    """Result of stream stability testing"""
    success: bool
    session_id: str
    test_duration_seconds: int
    frames_captured: int
    frames_dropped: int
    average_fps: float
    stability_score: float  # 0.0 to 1.0
    error_rate: float
    quality_metrics: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class StreamPreviewService:
    """Service for managing camera stream preview sessions"""
    
    def __init__(self, max_sessions: int = 10, session_timeout_minutes: int = 30):
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.active_sessions: Dict[str, PreviewSession] = {}
        self.session_threads: Dict[str, threading.Thread] = {}
        self.session_locks: Dict[str, threading.Lock] = {}
        self.snapshots_dir = Path("data/preview_snapshots")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
    
    async def start_preview_session(
        self,
        camera_config: Dict[str, Any]
    ) -> PreviewSession:
        """Start a temporary preview session"""
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Check session limit
            if len(self.active_sessions) >= self.max_sessions:
                # Remove oldest session
                await self._remove_oldest_session()
            
            # Build stream URL
            stream_url = self._build_stream_url(camera_config)
            
            # Create session
            session = PreviewSession(
                session_id=session_id,
                camera_config=camera_config,
                stream_url=stream_url,
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )
            
            # Store session
            self.active_sessions[session_id] = session
            self.session_locks[session_id] = threading.Lock()
            
            # Start streaming thread
            stream_thread = threading.Thread(
                target=self._stream_worker,
                args=(session_id,),
                daemon=True
            )
            stream_thread.start()
            self.session_threads[session_id] = stream_thread
            
            logger.info(f"Started preview session {session_id} for {camera_config.get('ip_address')}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to start preview session: {e}")
            raise
    
    async def capture_snapshot(
        self,
        session_id: str,
        save_to_file: bool = True,
        return_base64: bool = False
    ) -> SnapshotResult:
        """Capture a snapshot from preview stream"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return SnapshotResult(
                    success=False,
                    session_id=session_id,
                    error_message="Session not found"
                )
            
            if not session.is_active:
                return SnapshotResult(
                    success=False,
                    session_id=session_id,
                    error_message="Session is not active"
                )
            
            # Update last accessed time
            session.last_accessed = datetime.now()
            
            # Get current frame
            with self.session_locks[session_id]:
                if session.current_frame is None:
                    return SnapshotResult(
                        success=False,
                        session_id=session_id,
                        error_message="No frame available"
                    )
                
                frame = session.current_frame.copy()
                frame_timestamp = session.frame_timestamp
            
            # Encode frame as JPEG
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not success:
                return SnapshotResult(
                    success=False,
                    session_id=session_id,
                    error_message="Failed to encode frame as JPEG"
                )
            
            snapshot_data = buffer.tobytes()
            
            # Save to file if requested
            file_path = None
            if save_to_file:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"snapshot_{session_id}_{timestamp_str}.jpg"
                file_path = self.snapshots_dir / filename
                
                with open(file_path, 'wb') as f:
                    f.write(snapshot_data)
            
            # Get frame info
            frame_info = {
                "width": frame.shape[1],
                "height": frame.shape[0],
                "channels": frame.shape[2] if len(frame.shape) > 2 else 1,
                "size_bytes": len(snapshot_data),
                "format": "JPEG",
                "quality": 90
            }
            
            # Convert to base64 if requested
            base64_data = None
            if return_base64:
                base64_data = base64.b64encode(snapshot_data).decode('utf-8')
            
            return SnapshotResult(
                success=True,
                session_id=session_id,
                snapshot_data=base64_data.encode('utf-8') if base64_data else snapshot_data,
                file_path=str(file_path) if file_path else None,
                frame_info=frame_info
            )
            
        except Exception as e:
            logger.error(f"Failed to capture snapshot for session {session_id}: {e}")
            return SnapshotResult(
                success=False,
                session_id=session_id,
                error_message=f"Snapshot capture failed: {str(e)}"
            )
    
    async def test_stream_stability(
        self,
        session_id: str,
        duration: int = 30
    ) -> StabilityResult:
        """Test stream stability and quality metrics"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return StabilityResult(
                    success=False,
                    session_id=session_id,
                    test_duration_seconds=0,
                    frames_captured=0,
                    frames_dropped=0,
                    average_fps=0.0,
                    stability_score=0.0,
                    error_rate=1.0,
                    quality_metrics={}
                )
            
            # Update last accessed time
            session.last_accessed = datetime.now()
            
            # Record initial state
            initial_frame_count = session.frame_count
            initial_error_count = session.error_count
            start_time = time.time()
            
            # Monitor for specified duration
            await asyncio.sleep(duration)
            
            # Calculate metrics
            end_time = time.time()
            actual_duration = end_time - start_time
            frames_captured = session.frame_count - initial_frame_count
            errors_occurred = session.error_count - initial_error_count
            
            # Calculate FPS
            average_fps = frames_captured / actual_duration if actual_duration > 0 else 0.0
            
            # Calculate error rate
            error_rate = errors_occurred / max(frames_captured, 1)
            
            # Calculate stability score (higher is better)
            # Based on FPS consistency and error rate
            expected_fps = 25.0  # Assume 25 FPS target
            fps_score = min(average_fps / expected_fps, 1.0) if expected_fps > 0 else 0.0
            error_score = max(0.0, 1.0 - error_rate)
            stability_score = (fps_score * 0.7) + (error_score * 0.3)
            
            # Quality metrics
            quality_metrics = {
                "expected_fps": expected_fps,
                "actual_fps": average_fps,
                "fps_ratio": fps_score,
                "error_score": error_score,
                "frames_per_error": frames_captured / max(errors_occurred, 1),
                "stream_health": "good" if stability_score > 0.8 else "fair" if stability_score > 0.5 else "poor"
            }
            
            return StabilityResult(
                success=True,
                session_id=session_id,
                test_duration_seconds=int(actual_duration),
                frames_captured=frames_captured,
                frames_dropped=errors_occurred,
                average_fps=average_fps,
                stability_score=stability_score,
                error_rate=error_rate,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to test stream stability for session {session_id}: {e}")
            return StabilityResult(
                success=False,
                session_id=session_id,
                test_duration_seconds=duration,
                frames_captured=0,
                frames_dropped=0,
                average_fps=0.0,
                stability_score=0.0,
                error_rate=1.0,
                quality_metrics={"error": str(e)}
            )
    
    async def stop_preview_session(self, session_id: str) -> bool:
        """Stop and cleanup preview session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            # Mark session as inactive
            session.is_active = False
            
            # Wait for thread to finish (with timeout)
            thread = self.session_threads.get(session_id)
            if thread and thread.is_alive():
                thread.join(timeout=5.0)
            
            # Cleanup
            self.active_sessions.pop(session_id, None)
            self.session_threads.pop(session_id, None)
            self.session_locks.pop(session_id, None)
            
            logger.info(f"Stopped preview session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop preview session {session_id}: {e}")
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a preview session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "camera_config": session.camera_config,
            "stream_url": session.stream_url,
            "created_at": session.created_at.isoformat(),
            "last_accessed": session.last_accessed.isoformat(),
            "is_active": session.is_active,
            "frame_count": session.frame_count,
            "error_count": session.error_count,
            "has_current_frame": session.current_frame is not None,
            "frame_timestamp": session.frame_timestamp.isoformat() if session.frame_timestamp else None
        }
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active preview sessions"""
        sessions = []
        for session_id, session in self.active_sessions.items():
            session_info = await self.get_session_info(session_id)
            if session_info:
                sessions.append(session_info)
        return sessions
    
    def _build_stream_url(self, camera_config: Dict[str, Any]) -> str:
        """Build stream URL from camera configuration"""
        ip_address = camera_config.get("ip_address")
        port = camera_config.get("port", 554)
        connection_type = camera_config.get("connection_type", "rtsp")
        stream_path = camera_config.get("stream_path", "/stream1")
        username = camera_config.get("username", "admin")
        password = camera_config.get("password", "")
        
        if connection_type.startswith("rtsp"):
            if username and password:
                return f"rtsp://{username}:{password}@{ip_address}:{port}{stream_path}"
            else:
                return f"rtsp://{ip_address}:{port}{stream_path}"
        else:
            return f"{connection_type}://{ip_address}:{port}{stream_path}"
    
    def _stream_worker(self, session_id: str):
        """Worker thread for handling stream capture"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        cap = None
        try:
            logger.info(f"Starting stream worker for session {session_id}")
            
            # Open video capture
            cap = cv2.VideoCapture(session.stream_url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10 second timeout
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)   # 5 second read timeout
            
            if not cap.isOpened():
                logger.error(f"Failed to open stream for session {session_id}")
                session.is_active = False
                return
            
            # Stream loop
            while session.is_active:
                try:
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        # Update session with new frame
                        with self.session_locks[session_id]:
                            session.current_frame = frame
                            session.frame_timestamp = datetime.now()
                            session.frame_count += 1
                    else:
                        session.error_count += 1
                        logger.warning(f"Failed to read frame from session {session_id}")
                        
                        # If too many consecutive errors, mark as inactive
                        if session.error_count > session.frame_count + 10:
                            logger.error(f"Too many errors for session {session_id}, marking inactive")
                            session.is_active = False
                            break
                    
                    # Small delay to prevent CPU overload
                    time.sleep(0.04)  # ~25 FPS
                    
                except Exception as e:
                    logger.error(f"Error in stream worker for session {session_id}: {e}")
                    session.error_count += 1
                    time.sleep(1.0)  # Wait before retrying
                    
        except Exception as e:
            logger.error(f"Stream worker failed for session {session_id}: {e}")
            session.is_active = False
        finally:
            if cap:
                cap.release()
            logger.info(f"Stream worker finished for session {session_id}")
    
    async def _cleanup_expired_sessions(self):
        """Background task to cleanup expired sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if current_time - session.last_accessed > self.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    logger.info(f"Cleaning up expired session {session_id}")
                    await self.stop_preview_session(session_id)
                
                # Wait 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in session cleanup task: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _remove_oldest_session(self):
        """Remove the oldest active session to make room for a new one"""
        if not self.active_sessions:
            return
        
        oldest_session_id = min(
            self.active_sessions.keys(),
            key=lambda sid: self.active_sessions[sid].created_at
        )
        
        logger.info(f"Removing oldest session {oldest_session_id} to make room for new session")
        await self.stop_preview_session(oldest_session_id)
    
    async def get_live_frame(self, session_id: str) -> Optional[Tuple[bytes, datetime]]:
        """Get the current live frame as JPEG bytes"""
        try:
            session = self.active_sessions.get(session_id)
            if not session or not session.is_active:
                return None
            
            # Update last accessed time
            session.last_accessed = datetime.now()
            
            # Get current frame
            with self.session_locks[session_id]:
                if session.current_frame is None:
                    return None
                
                frame = session.current_frame.copy()
                frame_timestamp = session.frame_timestamp
            
            # Encode as JPEG
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not success:
                return None
            
            return buffer.tobytes(), frame_timestamp
            
        except Exception as e:
            logger.error(f"Failed to get live frame for session {session_id}: {e}")
            return None
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            # Cancel cleanup task
            if hasattr(self, '_cleanup_task'):
                self._cleanup_task.cancel()
            
            # Stop all sessions
            for session_id in list(self.active_sessions.keys()):
                asyncio.create_task(self.stop_preview_session(session_id))
        except Exception:
            pass