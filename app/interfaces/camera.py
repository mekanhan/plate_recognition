"""
Interfaces for camera operations.
"""
from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

class Camera(ABC):
    """Interface for camera implementations."""
    
    @abstractmethod
    async def initialize(self, camera_id: int = 0, width: int = 1280, height: int = 720) -> None:
        """Initialize the camera."""
        pass
        
    @abstractmethod
    async def get_frame(self) -> Tuple[np.ndarray, float]:
        """
        Get the latest frame from the camera.
        
        Returns:
            Tuple of (frame, timestamp)
        """
        pass
        
    @abstractmethod
    async def get_jpeg_frame(self) -> Tuple[bytes, float]:
        """
        Get the latest frame as JPEG bytes.
        
        Returns:
            Tuple of (jpeg_bytes, timestamp)
        """
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the camera and release resources."""
        pass