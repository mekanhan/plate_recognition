"""
Core types for AI features
Enhanced detection types with backward compatibility
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

@dataclass
class Detection:
    """Enhanced detection result with backward compatibility"""
    # EXISTING FIELDS (maintain exact compatibility)
    detection_id: str
    camera_id: str
    timestamp: datetime
    plate_text: str
    confidence: float
    vehicle_type: str
    vehicle_bbox: List[int]
    plate_bbox: List[int]
    frame_path: str = ""
    plate_image_path: str = ""
    
    # NEW ENHANCED FIELDS (with defaults for backward compatibility)
    vehicle_color: str = "unknown"
    vehicle_make: str = "unknown"
    vehicle_model: str = "unknown"
    ocr_confidence: float = 0.0
    plate_type: str = "standard"  # standard, commercial, government, temporary
    plate_region: str = "unknown"  # state/country
    detection_metadata: Optional[Dict[str, Any]] = None
    processing_time_ms: float = 0.0
    
    # DEDUPLICATION FIELDS (for smart storage)
    group_id: Optional[str] = None  # Groups related detections
    track_id: Optional[str] = None  # Object tracking ID
    is_best_shot: bool = False  # Marks the best detection in a group
    image_saved: bool = True  # Whether image was saved (for dedup)
    
    def __post_init__(self):
        """Initialize metadata dict if None"""
        if self.detection_metadata is None:
            self.detection_metadata = {}

@dataclass
class VehicleInfo:
    """Vehicle classification information"""
    vehicle_type: str  # car, truck, motorcycle, bus, van
    color: str
    make: str = "unknown"
    model: str = "unknown"
    size_category: str = "unknown"  # small, medium, large
    confidence: float = 0.0
    bbox: List[int] = field(default_factory=list)

@dataclass 
class PlateInfo:
    """License plate specific information"""
    text: str
    confidence: float
    ocr_confidence: float
    plate_type: str = "standard"
    region: str = "unknown"
    bbox: List[int] = field(default_factory=list)
    
@dataclass
class ProcessingResult:
    """Result from AI processing pipeline"""
    success: bool
    detections: List[Detection] = field(default_factory=list)
    processing_time_ms: float = 0.0
    error_message: str = ""
    metadata: Optional[Dict[str, Any]] = None