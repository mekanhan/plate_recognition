"""
Interfaces for license plate detection.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np

class LicensePlateDetector(ABC):
    """Interface for license plate detection implementations."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the detector."""
        pass
        
    @abstractmethod
    async def detect_and_recognize(self, image: np.ndarray) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Detect and recognize license plates in an image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Tuple of (list of detection results, annotated image)
        """
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the detector and release resources."""
        pass