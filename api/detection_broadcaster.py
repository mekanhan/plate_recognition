"""
Detection Event Broadcasting
Streams real-time detection events via WebSocket for debugging console
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

@dataclass
class DetectionEvent:
    """Structured detection event for console streaming"""
    event_type: str  # 'attempt', 'accepted', 'rejected', 'processing', 'quality'
    camera_id: str
    timestamp: str
    message: str
    details: Dict[str, Any] = None
    confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None
    severity: str = 'info'  # 'info', 'success', 'warning', 'error'
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}

class DetectionBroadcaster:
    """Broadcasts detection events to WebSocket console"""
    
    def __init__(self):
        self.enabled = True
        self.event_buffer = []
        self.max_buffer_size = 1000
        
    async def broadcast_detection_attempt(self, camera_id: str, plate_text: str, 
                                        ocr_confidence: float, pop_metrics: Dict):
        """Broadcast when a detection attempt starts"""
        if not self.enabled:
            return
            
        event = DetectionEvent(
            event_type='attempt',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"Processing detection: '{plate_text}' (OCR: {ocr_confidence:.2f})",
            details={
                'plate_text': plate_text,
                'ocr_confidence': ocr_confidence,
                'pop_metrics': pop_metrics,
                'text_length': len(plate_text.strip()) if plate_text else 0
            },
            confidence=ocr_confidence,
            severity='info'
        )
        
        await self._send_event(event)
    
    async def broadcast_detection_accepted(self, camera_id: str, plate_text: str, 
                                         ocr_confidence: float, reason: str = "Validation passed"):
        """Broadcast when a detection is accepted"""
        if not self.enabled:
            return
            
        event = DetectionEvent(
            event_type='accepted',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"✅ ACCEPTED: '{plate_text}' (conf: {ocr_confidence:.2f}) - {reason}",
            details={
                'plate_text': plate_text,
                'ocr_confidence': ocr_confidence,
                'reason': reason
            },
            confidence=ocr_confidence,
            severity='success'
        )
        
        await self._send_event(event)
    
    async def broadcast_detection_rejected(self, camera_id: str, plate_text: str, 
                                         ocr_confidence: float, reason: str):
        """Broadcast when a detection is rejected"""
        if not self.enabled:
            return
            
        event = DetectionEvent(
            event_type='rejected',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"❌ REJECTED: '{plate_text}' (conf: {ocr_confidence:.2f}) - {reason}",
            details={
                'plate_text': plate_text,
                'ocr_confidence': ocr_confidence,
                'reason': reason
            },
            confidence=ocr_confidence,
            severity='warning'
        )
        
        await self._send_event(event)
    
    async def broadcast_vehicle_detection(self, camera_id: str, vehicle_count: int, 
                                        vehicle_confidences: list):
        """Broadcast vehicle detection results"""
        if not self.enabled:
            return
            
        avg_conf = sum(vehicle_confidences) / len(vehicle_confidences) if vehicle_confidences else 0
        
        event = DetectionEvent(
            event_type='processing',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"🚗 Found {vehicle_count} vehicle(s) (avg conf: {avg_conf:.2f})",
            details={
                'vehicle_count': vehicle_count,
                'confidences': vehicle_confidences,
                'avg_confidence': avg_conf
            },
            confidence=avg_conf,
            severity='info'
        )
        
        await self._send_event(event)
    
    async def broadcast_plate_detection(self, camera_id: str, plate_count: int, 
                                      plate_confidences: list):
        """Broadcast plate detection results"""
        if not self.enabled:
            return
            
        avg_conf = sum(plate_confidences) / len(plate_confidences) if plate_confidences else 0
        
        event = DetectionEvent(
            event_type='processing',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"🏷️  Found {plate_count} license plate(s) (avg conf: {avg_conf:.2f})",
            details={
                'plate_count': plate_count,
                'confidences': plate_confidences,
                'avg_confidence': avg_conf
            },
            confidence=avg_conf,
            severity='info'
        )
        
        await self._send_event(event)
    
    async def broadcast_image_quality(self, camera_id: str, pop_metrics: Dict, 
                                    is_4k: bool = False, preprocessing_applied: bool = False):
        """Broadcast image quality analysis"""
        if not self.enabled:
            return
            
        quality_score = pop_metrics.get('quality_score', 0)
        quality_level = pop_metrics.get('quality_level', 'unknown')
        
        preprocessing_msg = " (4K enhanced)" if preprocessing_applied else ""
        
        event = DetectionEvent(
            event_type='quality',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"📊 Image quality: {quality_level} ({quality_score:.1f}%){preprocessing_msg}",
            details={
                'pop_metrics': pop_metrics,
                'is_4k': is_4k,
                'preprocessing_applied': preprocessing_applied,
                'quality_score': quality_score,
                'quality_level': quality_level
            },
            confidence=quality_score / 100,
            severity='info' if quality_score >= 60 else 'warning'
        )
        
        await self._send_event(event)
    
    async def broadcast_processing_metrics(self, camera_id: str, processing_time_ms: float, 
                                         stage: str, details: Dict = None):
        """Broadcast processing performance metrics"""
        if not self.enabled:
            return
            
        event = DetectionEvent(
            event_type='processing',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"⏱️  {stage}: {processing_time_ms:.1f}ms",
            details={
                'stage': stage,
                'processing_time_ms': processing_time_ms,
                **(details or {})
            },
            processing_time_ms=processing_time_ms,
            severity='info' if processing_time_ms < 1000 else 'warning'
        )
        
        await self._send_event(event)
    
    async def broadcast_ocr_results(self, camera_id: str, raw_results: list, 
                                  selected_text: str, selected_confidence: float):
        """Broadcast OCR analysis results"""
        if not self.enabled:
            return
            
        result_summary = []
        for bbox, text, conf in raw_results:
            result_summary.append(f"'{text}' ({conf:.2f})")
        
        event = DetectionEvent(
            event_type='processing',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"🔍 OCR results: {len(raw_results)} candidates → selected: '{selected_text}' ({selected_confidence:.2f})",
            details={
                'raw_results_count': len(raw_results),
                'raw_results': result_summary,
                'selected_text': selected_text,
                'selected_confidence': selected_confidence,
                'full_results': raw_results
            },
            confidence=selected_confidence,
            severity='info'
        )
        
        await self._send_event(event)
    
    async def broadcast_state_name_filter(self, camera_id: str, text: str, 
                                        confidence: float, detected_states: list):
        """Broadcast state name filtering results"""
        if not self.enabled:
            return
            
        states_str = ", ".join(detected_states) if detected_states else "none"
        
        event = DetectionEvent(
            event_type='rejected',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"🚫 State name filter: '{text}' → detected states: {states_str}",
            details={
                'text': text,
                'confidence': confidence,
                'detected_states': detected_states,
                'filter_reason': 'state_name_detected'
            },
            confidence=confidence,
            severity='warning'
        )
        
        await self._send_event(event)
    
    async def broadcast_confidence_threshold(self, camera_id: str, text: str, 
                                           confidence: float, threshold: float, passed: bool):
        """Broadcast confidence threshold check results"""
        if not self.enabled:
            return
            
        status = "✅ PASSED" if passed else "❌ FAILED"
        
        event = DetectionEvent(
            event_type='accepted' if passed else 'rejected',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"🎯 Confidence check: '{text}' ({confidence:.2f}) vs threshold ({threshold:.2f}) → {status}",
            details={
                'text': text,
                'confidence': confidence,
                'threshold': threshold,
                'passed': passed,
                'margin': confidence - threshold
            },
            confidence=confidence,
            severity='success' if passed else 'warning'
        )
        
        await self._send_event(event)
    
    async def broadcast_frame_processing_start(self, camera_id: str, frame_info: Dict):
        """Broadcast frame processing start"""
        if not self.enabled:
            return
            
        resolution = f"{frame_info.get('width', 0)}x{frame_info.get('height', 0)}"
        is_4k = frame_info.get('width', 0) >= 3840 or frame_info.get('height', 0) >= 2160
        
        event = DetectionEvent(
            event_type='processing',
            camera_id=camera_id,
            timestamp=datetime.now().isoformat(),
            message=f"🎬 Processing frame: {resolution} {'(4K)' if is_4k else '(HD)'}",
            details={
                'resolution': resolution,
                'is_4k': is_4k,
                'frame_info': frame_info
            },
            severity='info'
        )
        
        await self._send_event(event)
    
    async def _send_event(self, event: DetectionEvent):
        """Send event via WebSocket and add to buffer"""
        try:
            # Add to buffer
            self._add_to_buffer(event)
            
            # Send via WebSocket
            payload = asdict(event)
            await websocket_manager.broadcast_to_subscribers("detection_console", payload)
            
        except Exception as e:
            logger.error(f"Failed to broadcast detection event: {e}")
    
    def _add_to_buffer(self, event: DetectionEvent):
        """Add event to buffer with size limit"""
        self.event_buffer.append(event)
        if len(self.event_buffer) > self.max_buffer_size:
            self.event_buffer.pop(0)
    
    def get_recent_events(self, limit: int = 100) -> list:
        """Get recent events from buffer"""
        return [asdict(event) for event in self.event_buffer[-limit:]]
    
    def clear_buffer(self):
        """Clear the event buffer"""
        self.event_buffer.clear()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable broadcasting"""
        self.enabled = enabled
        logger.info(f"Detection broadcasting {'enabled' if enabled else 'disabled'}")

# Global instance
detection_broadcaster = DetectionBroadcaster()