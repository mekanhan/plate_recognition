"""
Simple Object Tracker for License Plates
Tracks objects across frames using IoU and feature matching
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta
import uuid


@dataclass
class TrackedObject:
    """Represents a tracked object (vehicle or plate)"""
    track_id: str
    object_type: str  # 'vehicle' or 'plate'
    first_seen: datetime
    last_seen: datetime
    bbox: List[int]
    confidence: float
    plate_text: Optional[str] = None
    appearances: int = 1
    camera_id: Optional[str] = None
    
    def update(self, bbox: List[int], confidence: float, plate_text: Optional[str] = None):
        """Update tracked object with new detection"""
        self.last_seen = datetime.now()
        self.bbox = bbox
        self.confidence = max(self.confidence, confidence)  # Keep best confidence
        self.appearances += 1
        if plate_text:
            self.plate_text = plate_text


class SimpleObjectTracker:
    """Simple object tracker using IoU and temporal proximity"""
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger("ObjectTracker")
        
        # Default configuration
        self.config = {
            'max_lost_frames': 30,  # Remove track after 30 frames without detection
            'min_iou_threshold': 0.3,  # Minimum IoU for matching
            'max_track_age_seconds': 60,  # Remove tracks older than 60 seconds
            'min_appearances_for_stable': 3,  # Min appearances to consider track stable
        }
        
        if config:
            self.config.update(config)
        
        # Active tracks per camera
        self.tracks: Dict[str, Dict[str, TrackedObject]] = {}  # camera_id -> track_id -> TrackedObject
        self.next_track_id = 1
        
        # Statistics
        self.total_tracks_created = 0
        self.active_tracks = 0
    
    def update(self, camera_id: str, detections: List[Dict]) -> List[Tuple[str, Dict]]:
        """
        Update tracker with new detections
        Returns: List of (track_id, detection) tuples
        """
        if camera_id not in self.tracks:
            self.tracks[camera_id] = {}
        
        camera_tracks = self.tracks[camera_id]
        current_time = datetime.now()
        matched_tracks = []
        
        # Clean up old tracks first
        self._cleanup_old_tracks(camera_id)
        
        # Match detections to existing tracks
        unmatched_detections = []
        matched_track_ids = set()
        
        for detection in detections:
            best_match = self._find_best_match(camera_tracks, detection, matched_track_ids)
            
            if best_match:
                # Update existing track
                track = camera_tracks[best_match]
                track.update(
                    bbox=detection.get('bbox', []),
                    confidence=detection.get('confidence', 0.0),
                    plate_text=detection.get('plate_text')
                )
                matched_tracks.append((best_match, detection))
                matched_track_ids.add(best_match)
            else:
                # No match found
                unmatched_detections.append(detection)
        
        # Create new tracks for unmatched detections
        for detection in unmatched_detections:
            track_id = self._create_new_track(camera_id, detection)
            matched_tracks.append((track_id, detection))
        
        # Update statistics
        self.active_tracks = sum(len(tracks) for tracks in self.tracks.values())
        
        return matched_tracks
    
    def _find_best_match(self, camera_tracks: Dict[str, TrackedObject], 
                        detection: Dict, matched_ids: set) -> Optional[str]:
        """Find best matching track for a detection"""
        best_match_id = None
        best_iou = self.config['min_iou_threshold']
        
        detection_bbox = detection.get('bbox', [])
        if not detection_bbox or len(detection_bbox) != 4:
            return None
        
        for track_id, track in camera_tracks.items():
            # Skip already matched tracks
            if track_id in matched_ids:
                continue
            
            # Calculate IoU
            iou = self._calculate_iou(track.bbox, detection_bbox)
            
            # Consider text matching for plates
            text_bonus = 0
            if track.plate_text and detection.get('plate_text'):
                if track.plate_text == detection['plate_text']:
                    text_bonus = 0.3  # Bonus for matching plate text
            
            effective_iou = iou + text_bonus
            
            if effective_iou > best_iou:
                best_iou = effective_iou
                best_match_id = track_id
        
        return best_match_id
    
    def _calculate_iou(self, bbox1: List[int], bbox2: List[int]) -> float:
        """Calculate Intersection over Union for two bounding boxes"""
        if not bbox1 or not bbox2 or len(bbox1) != 4 or len(bbox2) != 4:
            return 0.0
        
        # Calculate intersection
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        # Calculate union
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        if union <= 0:
            return 0.0
        
        return intersection / union
    
    def _create_new_track(self, camera_id: str, detection: Dict) -> str:
        """Create a new track for a detection"""
        track_id = f"track_{self.next_track_id:06d}"
        self.next_track_id += 1
        
        current_time = datetime.now()
        
        track = TrackedObject(
            track_id=track_id,
            object_type=detection.get('object_type', 'plate'),
            first_seen=current_time,
            last_seen=current_time,
            bbox=detection.get('bbox', []),
            confidence=detection.get('confidence', 0.0),
            plate_text=detection.get('plate_text'),
            camera_id=camera_id
        )
        
        self.tracks[camera_id][track_id] = track
        self.total_tracks_created += 1
        
        self.logger.debug(f"Created new track {track_id} for camera {camera_id}")
        
        return track_id
    
    def _cleanup_old_tracks(self, camera_id: str):
        """Remove old/lost tracks"""
        if camera_id not in self.tracks:
            return
        
        current_time = datetime.now()
        max_age = timedelta(seconds=self.config['max_track_age_seconds'])
        tracks_to_remove = []
        
        for track_id, track in self.tracks[camera_id].items():
            age = current_time - track.last_seen
            if age > max_age:
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.tracks[camera_id][track_id]
            self.logger.debug(f"Removed old track {track_id}")
    
    def get_stable_tracks(self, camera_id: str) -> List[TrackedObject]:
        """Get tracks that are considered stable (multiple appearances)"""
        if camera_id not in self.tracks:
            return []
        
        stable_tracks = []
        min_appearances = self.config['min_appearances_for_stable']
        
        for track in self.tracks[camera_id].values():
            if track.appearances >= min_appearances:
                stable_tracks.append(track)
        
        return stable_tracks
    
    def get_track_by_id(self, camera_id: str, track_id: str) -> Optional[TrackedObject]:
        """Get a specific track by ID"""
        if camera_id in self.tracks and track_id in self.tracks[camera_id]:
            return self.tracks[camera_id][track_id]
        return None
    
    def is_new_object(self, camera_id: str, detection: Dict) -> bool:
        """Check if a detection represents a new object (not seen recently)"""
        if camera_id not in self.tracks:
            return True
        
        # Try to match with existing tracks
        best_match = self._find_best_match(self.tracks[camera_id], detection, set())
        
        if not best_match:
            return True
        
        # Check if track is stable enough
        track = self.tracks[camera_id][best_match]
        return track.appearances < self.config['min_appearances_for_stable']
    
    def get_track_stats(self) -> Dict:
        """Get tracking statistics"""
        stable_tracks = 0
        
        for camera_tracks in self.tracks.values():
            for track in camera_tracks.values():
                if track.appearances >= self.config['min_appearances_for_stable']:
                    stable_tracks += 1
        
        return {
            'total_tracks_created': self.total_tracks_created,
            'active_tracks': self.active_tracks,
            'stable_tracks': stable_tracks,
            'cameras_tracked': len(self.tracks)
        }
    
    def clear_camera_tracks(self, camera_id: str):
        """Clear all tracks for a specific camera"""
        if camera_id in self.tracks:
            self.tracks[camera_id].clear()
            self.logger.info(f"Cleared all tracks for camera {camera_id}")
    
    def reset(self):
        """Reset all tracking data"""
        self.tracks.clear()
        self.next_track_id = 1
        self.total_tracks_created = 0
        self.active_tracks = 0
        self.logger.info("Tracker reset complete")