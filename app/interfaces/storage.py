"""
Interfaces for storage operations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DetectionRepository(ABC):
    """Interface for license plate detection storage."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository."""
        pass
        
    @abstractmethod
    async def add_detections(self, detections: List[Dict[str, Any]]) -> None:
        """Add detections to the repository."""
        pass
        
    @abstractmethod
    async def get_detections(self) -> List[Dict[str, Any]]:
        """Retrieve all detections."""
        pass
        
    @abstractmethod
    async def get_detection_by_id(self, detection_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a detection by ID."""
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the repository and release resources."""
        pass
        
class EnhancementRepository(ABC):
    """Interface for license plate enhancement storage."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository."""
        pass
        
    @abstractmethod
    async def add_enhanced_results(self, results: List[Dict[str, Any]]) -> None:
        """Add enhanced results to the repository."""
        pass
        
    @abstractmethod
    async def get_enhanced_results(self) -> List[Dict[str, Any]]:
        """Retrieve all enhanced results."""
        pass
        
    @abstractmethod
    async def get_enhanced_result_by_id(self, enhanced_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an enhanced result by ID."""
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the repository and release resources."""
        pass