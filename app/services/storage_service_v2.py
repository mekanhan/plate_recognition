"""
Improved storage service that uses repository interfaces.
"""
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional

from app.interfaces.storage import DetectionRepository, EnhancementRepository

logger = logging.getLogger(__name__)

class StorageServiceV2:
    """
    Improved storage service that uses repository interfaces for data persistence.
    This service acts as an adapter between the old API and new repository interfaces.
    """
    
    def __init__(self):
        self.detection_repository: Optional[DetectionRepository] = None
        self.enhancement_repository: Optional[EnhancementRepository] = None
        self.initialization_complete = False
    
    async def initialize(self, 
                        detection_repository: DetectionRepository,
                        enhancement_repository: EnhancementRepository,
                        license_plates_dir: str = "data/license_plates",
                        enhanced_plates_dir: str = "data/enhanced_plates") -> None:
        """
        Initialize the storage service with repository implementations.
        
        Args:
            detection_repository: Repository for detection storage
            enhancement_repository: Repository for enhancement storage
            license_plates_dir: Directory for license plate images (for backward compatibility)
            enhanced_plates_dir: Directory for enhanced plate images (for backward compatibility)
        """
        try:
            self.detection_repository = detection_repository
            self.enhancement_repository = enhancement_repository
            
            # For backward compatibility
            self.license_plates_dir = license_plates_dir
            self.enhanced_plates_dir = enhanced_plates_dir
            
            self.initialization_complete = True
            
            logger.info("Storage service initialized")
            logger.info(f"License plate data will be stored in: {license_plates_dir}")
            logger.info(f"Enhanced results will be stored in: {enhanced_plates_dir}")
            
        except Exception as e:
            logger.error(f"Error initializing storage service: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the storage service."""
        # No need to shut down repositories as they are managed by the factory
        logger.info("Storage service shutdown")
    
    async def add_detections(self, detections: List[Dict[str, Any]]) -> None:
        """Add detections to the repository."""
        if not detections:
            logger.debug("No detections to add")
            return

        if not self.initialization_complete:
            logger.warning("Attempted to add detections before initialization complete")
            return
        
        if not self.detection_repository:
            logger.warning("Detection repository not initialized")
            return
        
        try:
            # Forward to repository
            await self.detection_repository.add_detections(detections)
            
            # Log details of first detection for debugging
            if detections:
                first_detection = detections[0]
                logger.info(f"Added detection: ID={first_detection.get('detection_id', 'unknown')}, "
                           f"Plate={first_detection.get('plate_text', 'unknown')}, "
                           f"Confidence={first_detection.get('confidence', 0)}")
        except Exception as e:
            logger.error(f"Error adding detections: {e}")
    
    async def add_enhanced_results(self, results: List[Dict[str, Any]]) -> None:
        """Add enhanced results to the repository."""
        if not results:
            logger.debug("No enhanced results to add")
            return
        
        if not self.initialization_complete:
            logger.warning("Attempted to add enhanced results before initialization complete")
            return
        
        if not self.enhancement_repository:
            logger.warning("Enhancement repository not initialized")
            return
        
        try:
            # Forward to repository
            await self.enhancement_repository.add_enhanced_results(results)
            
            # Log details of first result for debugging
            if results:
                first_result = results[0]
                logger.info(f"Added enhanced result: ID={first_result.get('enhanced_id', 'unknown')}, "
                           f"Plate={first_result.get('plate_text', 'unknown')}, "
                           f"Confidence={first_result.get('confidence', 0)}")
        except Exception as e:
            logger.error(f"Error adding enhanced results: {e}")
    
    async def get_detections(self) -> List[Dict[str, Any]]:
        """Get all detections."""
        if not self.detection_repository:
            logger.warning("Detection repository not initialized")
            return []
        
        try:
            return await self.detection_repository.get_detections()
        except Exception as e:
            logger.error(f"Error getting detections: {e}")
            return []
    
    async def get_enhanced_results(self) -> List[Dict[str, Any]]:
        """Get all enhanced results."""
        if not self.enhancement_repository:
            logger.warning("Enhancement repository not initialized")
            return []
        
        try:
            return await self.enhancement_repository.get_enhanced_results()
        except Exception as e:
            logger.error(f"Error getting enhanced results: {e}")
            return []
    
    async def get_detections_by_tracking_id(self, tracking_id: str) -> List[Dict[str, Any]]:
        """
        Get all detections for a specific tracking ID.
        
        Args:
            tracking_id: The tracking ID to filter by
            
        Returns:
            List of detection records with the specified tracking ID
        """
        if not self.detection_repository:
            logger.warning("Detection repository not initialized")
            return []
        
        try:
            # Get all detections and filter by tracking ID
            all_detections = await self.detection_repository.get_detections()
            return [d for d in all_detections if d.get("tracking_id") == tracking_id]
        except Exception as e:
            logger.error(f"Error getting detections by tracking ID: {e}")
            return []