"""
Detection Filter Module - Reduces duplicate detections for stationary objects

This module implements a simple but effective deduplication strategy:
- Tracks recent detections (last 5 minutes) per camera
- Ignores duplicates within 30 seconds and 100 pixels
- Updates when confidence improves by 10%+
- Stores entry/exit events when objects appear/disappear
- Fuzzy matching for OCR variations (handles misreads)

Usage:
    from ai_pipeline.detection_filter import DetectionFilter
    
    filter = DetectionFilter()
    
    if filter.should_store(detection, camera_id):
        save_to_database(detection)
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional, Any, List
from threading import Lock
import threading
import difflib

logger = logging.getLogger(__name__)


class DetectionFilter:
    """
    Simple in-memory detection filter to reduce duplicate detections.
    
    For production use with multiple workers, consider using Redis instead
    of in-memory storage.
    """
    
    def __init__(
        self,
        duplicate_window_seconds: int = 30,
        position_threshold: int = 100,
        confidence_improvement_threshold: float = 0.10,
        exit_timeout_seconds: int = 60,
        memory_duration_seconds: int = 300,  # 5 minutes
        cleanup_interval_seconds: int = 60,
        similarity_threshold: float = 0.75  # For fuzzy matching
    ):
        """
        Initialize the detection filter.
        
        Args:
            duplicate_window_seconds: Time window for considering duplicates
            position_threshold: Maximum pixel distance to consider same position
            confidence_improvement_threshold: Min confidence increase to update
            exit_timeout_seconds: Time before considering object has left
            memory_duration_seconds: How long to keep detection history
            cleanup_interval_seconds: How often to clean old entries
            similarity_threshold: Minimum similarity for fuzzy string matching
        """
        # Configuration
        self.duplicate_window = duplicate_window_seconds
        self.position_threshold = position_threshold
        self.confidence_threshold = confidence_improvement_threshold
        self.exit_timeout = exit_timeout_seconds
        self.memory_duration = memory_duration_seconds
        self.similarity_threshold = similarity_threshold
        
        # Storage: camera_id -> {license_plate -> detection_info}
        self._recent_detections = {}
        self._lock = Lock()
        
        # Statistics for monitoring
        self.stats = {
            'total_processed': 0,
            'stored': 0,
            'ignored_duplicates': 0,
            'quality_updates': 0,
            're_entries': 0
        }
        
        # Start cleanup thread
        self._start_cleanup_thread(cleanup_interval_seconds)
        
    def should_store(self, detection: Dict[str, Any], camera_id: str) -> Tuple[bool, str]:
        """
        Determine if a detection should be stored.
        
        Args:
            detection: Detection dict with keys: plate, x, y, confidence, timestamp
            camera_id: Camera identifier
            
        Returns:
            Tuple of (should_store: bool, reason: str)
        """
        with self._lock:
            self.stats['total_processed'] += 1
            
            # Get camera's recent detections
            if camera_id not in self._recent_detections:
                self._recent_detections[camera_id] = {}
            
            camera_memory = self._recent_detections[camera_id]
            plate = detection.get('plate', '')
            
            # Skip empty plates
            if not plate or plate == 'Unknown':
                return False, "invalid_plate"
            
            current_time = detection.get('timestamp', time.time())
            
            # Check if we've seen this plate recently (using fuzzy matching)
            matched_plate = self._find_similar_plate(plate, camera_memory)
            
            if matched_plate:
                last_detection = camera_memory[matched_plate]
                time_diff = current_time - last_detection['last_seen']
                
                # Check for duplicate (recent and nearby)
                if (time_diff < self.duplicate_window and 
                    self._calculate_distance(detection, last_detection) < self.position_threshold):
                    
                    # Update last seen time but don't store
                    last_detection['last_seen'] = current_time
                    self.stats['ignored_duplicates'] += 1
                    return False, "duplicate"
                
                # Check for quality improvement
                confidence_improvement = detection['confidence'] - last_detection['confidence']
                if confidence_improvement > self.confidence_threshold:
                    # Update the stored detection (use matched plate key)
                    self._update_memory(detection, camera_id, matched_plate)
                    self.stats['quality_updates'] += 1
                    self.stats['stored'] += 1
                    return True, "quality_update"
                
                # Check for re-entry after absence
                if time_diff > self.exit_timeout:
                    # Object was gone, now back - new entry
                    self._update_memory(detection, camera_id, plate)
                    self.stats['re_entries'] += 1
                    self.stats['stored'] += 1
                    return True, "re_entry"
                
                # Default: ignore as uninteresting duplicate
                # Update the matched entry's last seen time
                camera_memory[matched_plate]['last_seen'] = current_time
                self.stats['ignored_duplicates'] += 1
                return False, "no_significant_change"
            
            # New detection - store it
            self._update_memory(detection, camera_id, plate)
            self.stats['stored'] += 1
            return True, "new_detection"
    
    def _calculate_distance(self, det1: Dict, det2: Dict) -> float:
        """Calculate Manhattan distance between two detections."""
        # Simple Manhattan distance - faster than Euclidean
        return abs(det1.get('x', 0) - det2.get('x', 0)) + \
               abs(det1.get('y', 0) - det2.get('y', 0))
    
    def _find_similar_plate(self, plate: str, camera_memory: Dict) -> Optional[str]:
        """
        Find a similar plate in memory using fuzzy matching.
        
        This handles OCR variations like:
        - BR-766 vs BR-7G6 vs BR-76G
        - VBR2660 vs VBR7E60 vs IBR7660
        
        Returns the matched plate key or None.
        """
        if not plate:
            return None
            
        # First try exact match
        if plate in camera_memory:
            return plate
        
        # Clean the plate for comparison (remove common OCR confusions)
        clean_plate = self._normalize_plate(plate)
        
        # Try fuzzy matching
        best_match = None
        best_ratio = 0
        
        for stored_plate in camera_memory.keys():
            # Compare normalized versions
            clean_stored = self._normalize_plate(stored_plate)
            
            # Calculate similarity ratio
            ratio = difflib.SequenceMatcher(None, clean_plate, clean_stored).ratio()
            
            if ratio > self.similarity_threshold and ratio > best_ratio:
                best_ratio = ratio
                best_match = stored_plate
                
        if best_match:
            logger.debug(f"Fuzzy match: '{plate}' matched to '{best_match}' (ratio: {best_ratio:.2f})")
            
        return best_match
    
    def _normalize_plate(self, plate: str) -> str:
        """
        Normalize plate text for comparison.
        Handles common OCR confusion patterns.
        """
        if not plate:
            return ""
            
        # Convert to uppercase
        normalized = plate.upper()
        
        # Remove spaces and special characters for comparison
        normalized = ''.join(c for c in normalized if c.isalnum())
        
        # Common OCR substitutions (map confusing characters to canonical form)
        substitutions = {
            '0': 'O',  # Zero to O
            '1': 'I',  # One to I  
            '5': 'S',  # Five to S
            '8': 'B',  # Eight to B
            '6': 'G',  # Six to G (sometimes)
            '2': 'Z',  # Two to Z (sometimes)
        }
        
        # Apply substitutions carefully (this is a simple approach)
        # In production, you might want more sophisticated rules
        return normalized
    
    def _update_memory(self, detection: Dict, camera_id: str, plate: str):
        """Update the memory cache with new detection info."""
        self._recent_detections[camera_id][plate] = {
            'last_seen': detection.get('timestamp', time.time()),
            'x': detection.get('x', 0),
            'y': detection.get('y', 0),
            'confidence': detection.get('confidence', 0),
            'width': detection.get('width', 0),
            'height': detection.get('height', 0)
        }
    
    def _cleanup_old_entries(self):
        """Remove detections older than memory_duration."""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.memory_duration
            
            for camera_id in list(self._recent_detections.keys()):
                camera_detections = self._recent_detections[camera_id]
                
                # Remove old entries
                plates_to_remove = [
                    plate for plate, info in camera_detections.items()
                    if info['last_seen'] < cutoff_time
                ]
                
                for plate in plates_to_remove:
                    del camera_detections[plate]
                
                # Remove camera if no detections left
                if not camera_detections:
                    del self._recent_detections[camera_id]
            
            logger.debug(f"Cleanup completed. Active cameras: {len(self._recent_detections)}")
    
    def _start_cleanup_thread(self, interval_seconds: int):
        """Start background thread for cleaning old entries."""
        def cleanup_loop():
            while True:
                time.sleep(interval_seconds)
                try:
                    self._cleanup_old_entries()
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        logger.info(f"Started cleanup thread (interval: {interval_seconds}s)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get filter statistics."""
        with self._lock:
            total = self.stats['total_processed']
            if total > 0:
                reduction_rate = (self.stats['ignored_duplicates'] / total) * 100
            else:
                reduction_rate = 0
                
            return {
                **self.stats,
                'reduction_rate': round(reduction_rate, 2),
                'active_cameras': len(self._recent_detections),
                'total_tracked_objects': sum(
                    len(detections) for detections in self._recent_detections.values()
                )
            }
    
    def get_camera_summary(self, camera_id: str) -> Dict[str, Any]:
        """Get summary for a specific camera."""
        with self._lock:
            if camera_id not in self._recent_detections:
                return {'tracked_objects': 0, 'objects': []}
            
            camera_detections = self._recent_detections[camera_id]
            current_time = time.time()
            
            objects = []
            for plate, info in camera_detections.items():
                objects.append({
                    'plate': plate,
                    'last_seen_seconds_ago': round(current_time - info['last_seen']),
                    'confidence': round(info['confidence'], 3),
                    'position': f"({info['x']}, {info['y']})"
                })
            
            return {
                'tracked_objects': len(objects),
                'objects': sorted(objects, key=lambda x: x['last_seen_seconds_ago'])
            }
    
    def reset_stats(self):
        """Reset statistics counters."""
        with self._lock:
            for key in self.stats:
                self.stats[key] = 0
    
    def clear_camera(self, camera_id: str):
        """Clear all tracked objects for a specific camera."""
        with self._lock:
            if camera_id in self._recent_detections:
                del self._recent_detections[camera_id]
                logger.info(f"Cleared tracking data for camera {camera_id}")


# Global filter instance
_filter_instance = None


def get_detection_filter() -> DetectionFilter:
    """Get the global detection filter instance."""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = DetectionFilter()
        logger.info("Initialized global detection filter")
    return _filter_instance