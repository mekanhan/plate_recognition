"""
Smart Deduplication for License Plate Detections
Prevents duplicate saves and manages detection grouping
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class DetectionRecord:
    """Record of a detection for deduplication tracking"""
    detection_id: str
    camera_id: str
    plate_text: str
    confidence: float
    ocr_confidence: float
    timestamp: datetime
    vehicle_bbox: List[int]
    plate_bbox: List[int]
    image_saved: bool = False
    group_id: Optional[str] = None
    is_best_shot: bool = False
    
    def get_hash(self) -> str:
        """Generate hash for this detection"""
        # Hash based on camera + plate text for grouping
        key = f"{self.camera_id}:{self.plate_text}"
        return hashlib.md5(key.encode()).hexdigest()[:8]


class DeduplicationManager:
    """Manages intelligent deduplication of detections"""
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger("DeduplicationManager")
        
        # Default configuration - MORE AGGRESSIVE
        self.config = {
            'window_seconds': 1800,  # 30-minute grouping window (was 5)
            'cooldown_minutes': 30,  # Don't save same plate for 30 minutes (was 5)
            'min_confidence_improvement': 0.25,  # 25% improvement required (was 10%)
            'max_per_plate_per_hour': 2,  # Max 2 detections per unique plate per hour (was 12)
            'min_bbox_distance': 100,  # Minimum pixel distance for "different" position (was 50)
            'quality_factors': {
                'confidence': 0.4,
                'ocr_confidence': 0.3,
                'bbox_size': 0.3  # Larger bbox = better quality
            }
        }
        
        if config:
            self.config.update(config)
        
        # In-memory tracking (would be better in Redis for production)
        self.recent_detections: Dict[str, List[DetectionRecord]] = {}
        self.detection_groups: Dict[str, List[DetectionRecord]] = {}
        self.last_saved: Dict[str, datetime] = {}  # Track last save time per plate+camera
        
        # Stats
        self.total_detections = 0
        self.detections_saved = 0
        self.detections_skipped = 0
    
    def should_save_detection(self, detection: DetectionRecord) -> Tuple[bool, str, Optional[str]]:
        """
        Determine if a detection should be saved
        Returns: (should_save, reason, group_id)
        """
        self.total_detections += 1
        
        # Generate unique key for this camera+plate combo
        detection_key = f"{detection.camera_id}:{detection.plate_text}"
        detection_hash = detection.get_hash()
        
        # AGGRESSIVE CHECK: Skip very common/invalid plates
        if self._is_noise_plate(detection.plate_text):
            self.detections_skipped += 1
            return False, "noise_plate", detection_hash
        
        # Check cooldown period - STRICT ENFORCEMENT
        if detection_key in self.last_saved:
            time_since_last = datetime.now() - self.last_saved[detection_key]
            cooldown_period = timedelta(minutes=self.config['cooldown_minutes'])
            
            if time_since_last < cooldown_period:
                # Within cooldown - ONLY save if DRAMATICALLY better
                existing_group = self._get_active_group(detection_key)
                if existing_group:
                    best_detection = self._get_best_detection(existing_group)
                    # Require 50% improvement during cooldown
                    if self._is_dramatically_better(detection, best_detection, improvement_threshold=0.5):
                        self.detections_saved += 1
                        self.last_saved[detection_key] = datetime.now()
                        return True, "dramatically_better", detection_hash
                
                self.detections_skipped += 1
                remaining_cooldown = (cooldown_period - time_since_last).total_seconds() / 60
                return False, f"cooldown ({remaining_cooldown:.0f}min remaining)", detection_hash
        
        # Check hourly limit
        hourly_count = self._get_hourly_count(detection_key)
        if hourly_count >= self.config['max_per_plate_per_hour']:
            self.detections_skipped += 1
            return False, f"hourly_limit ({hourly_count}/{self.config['max_per_plate_per_hour']})", detection_hash
        
        # Check if part of existing group
        group_id = self._find_or_create_group(detection)
        group = self.detection_groups.get(group_id, [])
        
        if group:
            # Group exists - check if this is better
            best_detection = self._get_best_detection(group)
            
            # Always save first detection in a group
            if not any(d.image_saved for d in group):
                self.detections_saved += 1
                self.last_saved[detection_key] = datetime.now()
                detection.image_saved = True
                detection.is_best_shot = True
                group.append(detection)
                return True, "first_in_group", group_id
            
            # Check if significantly better than current best
            if self._is_significantly_better(detection, best_detection):
                # Mark old best as not best
                best_detection.is_best_shot = False
                detection.is_best_shot = True
                detection.image_saved = True
                group.append(detection)
                
                self.detections_saved += 1
                self.last_saved[detection_key] = datetime.now()
                return True, "better_quality", group_id
            else:
                # Add to group but don't save image
                detection.image_saved = False
                group.append(detection)
                self.detections_skipped += 1
                return False, "not_better_than_existing", group_id
        else:
            # New group - save it
            detection.image_saved = True
            detection.is_best_shot = True
            detection.group_id = group_id
            self.detection_groups[group_id] = [detection]
            
            self.detections_saved += 1
            self.last_saved[detection_key] = datetime.now()
            return True, "new_detection", group_id
    
    def _find_or_create_group(self, detection: DetectionRecord) -> str:
        """Find existing group or create new one"""
        current_time = datetime.now()
        window = timedelta(seconds=self.config['window_seconds'])
        
        # Look for existing group within time window
        for group_id, group_detections in self.detection_groups.items():
            if not group_detections:
                continue
            
            # Check if this detection fits in this group
            first_detection = group_detections[0]
            
            # Same camera and plate text
            if (first_detection.camera_id == detection.camera_id and 
                first_detection.plate_text == detection.plate_text):
                
                # Within time window
                time_diff = current_time - first_detection.timestamp
                if time_diff <= window:
                    detection.group_id = group_id
                    return group_id
        
        # No existing group found - create new one
        new_group_id = f"{detection.get_hash()}_{current_time.strftime('%Y%m%d_%H%M%S')}"
        detection.group_id = new_group_id
        return new_group_id
    
    def _get_active_group(self, detection_key: str) -> Optional[List[DetectionRecord]]:
        """Get active group for a detection key"""
        current_time = datetime.now()
        window = timedelta(seconds=self.config['window_seconds'])
        
        for group_id, group_detections in self.detection_groups.items():
            if not group_detections:
                continue
            
            first_detection = group_detections[0]
            key = f"{first_detection.camera_id}:{first_detection.plate_text}"
            
            if key == detection_key:
                time_diff = current_time - first_detection.timestamp
                if time_diff <= window:
                    return group_detections
        
        return None
    
    def _get_best_detection(self, group: List[DetectionRecord]) -> Optional[DetectionRecord]:
        """Get the best detection from a group"""
        if not group:
            return None
        
        # Find detection marked as best shot
        for detection in group:
            if detection.is_best_shot:
                return detection
        
        # Fallback to quality scoring
        return max(group, key=self._calculate_quality_score)
    
    def _calculate_quality_score(self, detection: DetectionRecord) -> float:
        """Calculate quality score for a detection"""
        factors = self.config['quality_factors']
        
        # Confidence score
        conf_score = detection.confidence * factors['confidence']
        
        # OCR confidence score  
        ocr_score = detection.ocr_confidence * factors['ocr_confidence']
        
        # BBox size score (larger = better, normalized)
        bbox = detection.plate_bbox
        if bbox and len(bbox) == 4:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            area = width * height
            # Normalize to 0-1 (assume max area of 100,000 pixels)
            size_score = min(area / 100000, 1.0) * factors['bbox_size']
        else:
            size_score = 0
        
        return conf_score + ocr_score + size_score
    
    def _is_significantly_better(self, new: DetectionRecord, existing: DetectionRecord) -> bool:
        """Check if new detection is significantly better than existing"""
        if not existing:
            return True
        
        # Calculate quality scores
        new_score = self._calculate_quality_score(new)
        existing_score = self._calculate_quality_score(existing)
        
        # Check if improvement meets threshold
        improvement = new_score - existing_score
        min_improvement = self.config['min_confidence_improvement']
        
        if improvement >= min_improvement:
            return True
        
        # Special case: much clearer OCR reading
        if (new.ocr_confidence - existing.ocr_confidence) >= 0.2:
            return True
        
        # Special case: significantly different position (different angle)
        if self._is_different_position(new.plate_bbox, existing.plate_bbox):
            # Different angle might give better view
            if new_score >= existing_score * 0.9:  # Within 10% quality
                return True
        
        return False
    
    def _is_different_position(self, bbox1: List[int], bbox2: List[int]) -> bool:
        """Check if two bounding boxes are in significantly different positions"""
        if not bbox1 or not bbox2 or len(bbox1) != 4 or len(bbox2) != 4:
            return False
        
        # Calculate center points
        center1_x = (bbox1[0] + bbox1[2]) / 2
        center1_y = (bbox1[1] + bbox1[3]) / 2
        center2_x = (bbox2[0] + bbox2[2]) / 2
        center2_y = (bbox2[1] + bbox2[3]) / 2
        
        # Calculate distance
        distance = ((center2_x - center1_x)**2 + (center2_y - center1_y)**2)**0.5
        
        return distance >= self.config['min_bbox_distance']
    
    def _get_hourly_count(self, detection_key: str) -> int:
        """Get count of detections for this key in the last hour"""
        count = 0
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)
        
        for group_detections in self.detection_groups.values():
            for detection in group_detections:
                key = f"{detection.camera_id}:{detection.plate_text}"
                if key == detection_key and detection.timestamp >= one_hour_ago:
                    if detection.image_saved:
                        count += 1
        
        return count
    
    def cleanup_old_groups(self):
        """Clean up old detection groups from memory"""
        current_time = datetime.now()
        retention_period = timedelta(hours=2)  # Keep 2 hours in memory
        
        groups_to_delete = []
        
        for group_id, group_detections in self.detection_groups.items():
            if group_detections:
                oldest = min(d.timestamp for d in group_detections)
                if current_time - oldest > retention_period:
                    groups_to_delete.append(group_id)
        
        for group_id in groups_to_delete:
            del self.detection_groups[group_id]
        
        if groups_to_delete:
            self.logger.info(f"Cleaned up {len(groups_to_delete)} old detection groups")
    
    def get_stats(self) -> Dict:
        """Get deduplication statistics"""
        saved_percentage = (self.detections_saved / self.total_detections * 100) if self.total_detections > 0 else 0
        
        return {
            'total_detections': self.total_detections,
            'detections_saved': self.detections_saved,
            'detections_skipped': self.detections_skipped,
            'saved_percentage': round(saved_percentage, 2),
            'reduction_percentage': round(100 - saved_percentage, 2),
            'active_groups': len(self.detection_groups),
            'tracked_plates': len(self.last_saved)
        }
    
    def reset_stats(self):
        """Reset statistics (useful for testing)"""
        self.total_detections = 0
        self.detections_saved = 0
        self.detections_skipped = 0
    
    def _is_noise_plate(self, plate_text: str) -> bool:
        """Check if plate text is likely noise/misread"""
        if not plate_text:
            return True
        
        # Common misreads and noise patterns
        noise_patterns = [
            'TEXAS',  # Often misread from license plate frame
            'CALIFORNIA',
            'FLORIDA',
            'STATE',
            'DEALER',
            'EXEMPT'
        ]
        
        # Check if it's just a state name (not a real plate)
        upper_text = plate_text.upper().strip()
        if upper_text in noise_patterns:
            return True
        
        # Too short to be valid
        if len(upper_text) < 3:
            return True
        
        # All same character (like "AAAA" or "1111")
        if len(set(upper_text)) == 1:
            return True
        
        return False
    
    def _is_dramatically_better(self, new: DetectionRecord, existing: DetectionRecord, 
                                improvement_threshold: float = 0.5) -> bool:
        """Check if new detection is DRAMATICALLY better than existing"""
        if not existing:
            return True
        
        # Calculate quality scores
        new_score = self._calculate_quality_score(new)
        existing_score = self._calculate_quality_score(existing)
        
        # Require significant improvement
        improvement = (new_score - existing_score) / (existing_score + 0.001)
        
        if improvement >= improvement_threshold:
            self.logger.info(f"Dramatic improvement detected: {improvement:.1%}")
            return True
        
        # Special case: MUCH clearer OCR reading (50% better)
        if (new.ocr_confidence - existing.ocr_confidence) >= 0.5:
            return True
        
        return False