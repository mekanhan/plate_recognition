"""
Factory for creating and managing service instances.
"""
import logging
from typing import Dict, Any, Optional
from app.interfaces.camera import Camera
from app.interfaces.detector import LicensePlateDetector
from app.interfaces.enhancer import LicensePlateEnhancer
from app.interfaces.storage import DetectionRepository, EnhancementRepository
from app.services.camera_service import CameraService
from app.services.license_plate_recognition_service import LicensePlateRecognitionService
from app.services.enhancer_service import EnhancerService
from app.services.video_service import VideoRecordingService
from app.repositories.json_repository import JSONDetectionRepository, JSONEnhancementRepository
from app.repositories.sql_repository import SQLiteDetectionRepository, SQLiteEnhancementRepository, SQLiteVideoRepository

logger = logging.getLogger(__name__)

class ServiceFactory:
    """Factory for creating and managing service instances with dependency injection."""
    
    def __init__(self):
        self._services = {}
        self._repositories = {}
        self._config = {}
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Set the configuration for service initialization."""
        self._config = config
    
    async def create_camera(self) -> Camera:
        """Create and initialize a camera service."""
        if "camera" in self._services:
            return self._services["camera"]
        
        logger.info("Creating camera service")
        camera = CameraService()
        
        # Get camera configuration
        camera_id = int(self._config.get("camera_id", 0))
        width = int(self._config.get("camera_width", 1280))
        height = int(self._config.get("camera_height", 720))
        
        # Initialize the camera
        await camera.initialize(camera_id=camera_id, width=width, height=height)
        
        # Store the instance
        self._services["camera"] = camera
        
        return camera
    
    async def create_detection_repository(self) -> DetectionRepository:
        """Create and initialize a detection repository"""
        if "detection_repository" in self._repositories:
            return self._repositories["detection_repository"]
        
        logger.info("Creating SQL detection repository")
        repository = SQLiteDetectionRepository()
        await repository.initialize()
        
        self._repositories["detection_repository"] = repository
        return repository
    
    async def create_enhancement_repository(self) -> EnhancementRepository:
        """Create and initialize an enhancement repository"""
        if "enhancement_repository" in self._repositories:
            return self._repositories["enhancement_repository"]
        
        logger.info("Creating SQL enhancement repository")
        repository = SQLiteEnhancementRepository()
        await repository.initialize()
        
        self._repositories["enhancement_repository"] = repository
        return repository
    
    async def create_video_repository(self) -> SQLiteVideoRepository:
        """Create a video repository"""
        if "video_repository" in self._repositories:
            return self._repositories["video_repository"]
        
        logger.info("Creating SQL video repository")
        repository = SQLiteVideoRepository()

        self._repositories["video_repository"] = repository
        return repository

    async def create_video_recording_service(self) -> VideoRecordingService:
        """Create and initialize a video recording service"""
        if "video_recording_service" in self._services:
            return self._services["video_recording_service"]

        logger.info("Creating video recording service")

        # Get required repositories
        detection_repo = await self.create_detection_repository()
        video_repo = await self.create_video_repository()

        # Create and initialize service
        service = VideoRecordingService(detection_repo, video_repo)
        await service.initialize()
        
        self._services["video_recording_service"] = service
        return service

    async def create_detector(self) -> LicensePlateDetector:
        """Create and initialize a license plate detector."""
        if "detector" in self._services:
            return self._services["detector"]
        
        logger.info("Creating license plate detector")
        detector = LicensePlateRecognitionService()
        
        # Initialize the detector
        await detector.initialize()
        # Store the instance
        self._services["detector"] = detector
        
        return detector
    
    async def create_enhancer(self) -> LicensePlateEnhancer:
        """Create and initialize a license plate enhancer."""
        if "enhancer" in self._services:
            return self._services["enhancer"]
        
        logger.info("Creating license plate enhancer")
        enhancer = EnhancerService()
        
        # Get enhancer configuration
        known_plates_path = self._config.get("known_plates_path")
        
        # Get enhancement repository dependency
        enhancement_repository = await self.create_enhancement_repository()
        
        # Initialize the enhancer
        await enhancer.initialize(known_plates_path=known_plates_path, storage_service=enhancement_repository)
        
        # Store the instance
        self._services["enhancer"] = enhancer
        
        return enhancer
    
    async def shutdown_all(self) -> None:
        """Shutdown all services and repositories."""
        logger.info("Shutting down all services and repositories")
        
        # Shutdown services in reverse order of dependencies
        for service_name in reversed(list(self._services.keys())):
            service = self._services[service_name]
            logger.info(f"Shutting down {service_name} service")
            try:
                await service.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {service_name} service: {e}")
        
        # Shutdown repositories
        for repo_name in reversed(list(self._repositories.keys())):
            repo = self._repositories[repo_name]
            logger.info(f"Shutting down {repo_name} repository")
            try:
                await repo.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {repo_name} repository: {e}")
        
        logger.info("All services and repositories shut down")
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name."""
        return self._services.get(service_name)
    
    def get_repository(self, repository_name: str) -> Optional[Any]:
        """Get a repository by name."""
        return self._repositories.get(repository_name)

# Create a singleton instance
service_factory = ServiceFactory()