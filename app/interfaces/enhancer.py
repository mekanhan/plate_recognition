"""
Interfaces for license plate enhancement.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class LicensePlateEnhancer(ABC):
    """Interface for license plate enhancement implementations."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the enhancer."""
        pass
        
    @abstractmethod
    async def enhance_detection(self, detection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enhance a license plate detection.
        
        Args:
            detection: Detection data to enhance
            
        Returns:
            Enhanced detection data or None if enhancement failed
        """
        pass
        
    @abstractmethod
    async def enhance_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance multiple license plate detections.
        
        Args:
            detections: List of detection data to enhance
            
        Returns:
            List of enhanced detection data
        """
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the enhancer and release resources."""
        pass