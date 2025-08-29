"""
Filtered Processing Pipeline - Enhanced pipeline with detection filtering

This module wraps the enhanced processing pipeline with the new detection filter
for improved duplicate reduction while maintaining compatibility.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
import time
import numpy as np

from ai_features.vehicle.detection.pipeline import EnhancedProcessingPipeline
from ai_features.core.types import Detection
from .detection_processor import get_filtered_detection_processor

logger = logging.getLogger(__name__)


class FilteredProcessingPipeline:
    """
    Processing pipeline that combines enhanced AI processing with detection filtering.
    
    This pipeline:
    1. Uses the enhanced AI pipeline for detection
    2. Applies the new detection filter for duplicate reduction
    3. Maintains compatibility with existing interfaces
    """
    
    def __init__(self):
        # Initialize the enhanced processing pipeline
        self.enhanced_pipeline = EnhancedProcessingPipeline()
        
        # Get the filtered detection processor
        self.filtered_processor = get_filtered_detection_processor()
        
        # Performance tracking
        self.total_frames_processed = 0
        self.total_detections_found = 0
        self.total_detections_stored = 0
        self.filter_statistics = {}
        
        logger.info("Initialized filtered processing pipeline")
    
    async def process_frame(self, camera_id: str, frame: np.ndarray) -> List[Detection]:
        """
        Process a single frame with AI detection and filtering.
        
        Args:
            camera_id: Camera identifier
            frame: Frame to process
            
        Returns:
            List of filtered detections that were stored
        """
        start_time = time.time()
        stored_detections = []
        
        try:
            # Use the enhanced pipeline to get raw detections
            raw_detections = await self.enhanced_pipeline.process_frame(camera_id, frame)
            
            self.total_detections_found += len(raw_detections)
            
            # Process each detection through the filter
            for detection in raw_detections:
                detection_id = await self.filtered_processor.process_detection(
                    detection, camera_id, detection.timestamp
                )
                
                if detection_id:
                    # Detection was stored - update the detection ID and add to results
                    detection.detection_id = detection_id
                    stored_detections.append(detection)
                    self.total_detections_stored += 1
            
            # Update frame processing statistics
            self.total_frames_processed += 1
            processing_time = (time.time() - start_time) * 1000
            
            # Get current filter statistics
            self.filter_statistics = self.filtered_processor.get_filter_stats()
            
            logger.info(
                f"Filtered processing for {camera_id}: "
                f"{len(raw_detections)} found -> {len(stored_detections)} stored "
                f"in {processing_time:.1f}ms"
            )
            
        except Exception as e:
            logger.error(f"Error in filtered processing for {camera_id}: {e}")
        
        return stored_detections
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get comprehensive filtering statistics."""
        base_stats = self.filtered_processor.get_filter_stats()
        
        # Add pipeline-level statistics
        pipeline_stats = {
            'pipeline': {
                'total_frames_processed': self.total_frames_processed,
                'total_detections_found': self.total_detections_found,
                'total_detections_stored': self.total_detections_stored,
                'storage_rate': (
                    self.total_detections_stored / max(self.total_detections_found, 1) * 100
                ) if self.total_detections_found > 0 else 0
            }
        }
        
        # Merge statistics
        return {**base_stats, **pipeline_stats}
    
    def get_camera_tracking_status(self, camera_id: str) -> Dict[str, Any]:
        """Get tracking status for a specific camera."""
        return self.filtered_processor.get_camera_status(camera_id)
    
    def reset_camera_tracking(self, camera_id: str):
        """Reset tracking for a specific camera."""
        self.filtered_processor.reset_camera_tracking(camera_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from both pipelines."""
        enhanced_stats = self.enhanced_pipeline.get_performance_stats()
        filter_stats = self.get_filter_stats()
        
        return {
            'enhanced_pipeline': enhanced_stats,
            'filter_pipeline': filter_stats,
            'combined_metrics': {
                'total_frames': self.total_frames_processed,
                'detections_found': self.total_detections_found,
                'detections_stored': self.total_detections_stored,
                'filter_effectiveness': filter_stats.get('reduction_rate', 0)
            }
        }


# Global instance for backward compatibility
_filtered_pipeline_instance = None


def get_filtered_pipeline() -> FilteredProcessingPipeline:
    """Get the global filtered pipeline instance."""
    global _filtered_pipeline_instance
    if _filtered_pipeline_instance is None:
        _filtered_pipeline_instance = FilteredProcessingPipeline()
        logger.info("Initialized global filtered pipeline")
    return _filtered_pipeline_instance