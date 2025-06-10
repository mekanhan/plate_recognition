# service_factory.py
from app.database import async_session, init_db
from app.repositories import SQLiteDetectionRepository, SQLiteVideoRepository
from app.video_service import VideoRecordingService

class ServiceFactory:
    """Factory for creating and managing service instances"""
    
    def __init__(self):
        self._services = {}
        self._repositories = {}
        self._config = {}
        self._db_initialized = False
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Set configuration values"""
        self._config = config
    
    async def initialize_database(self) -> None:
        """Initialize the database"""
        if not self._db_initialized:
            await init_db()
            self._db_initialized = True
    
    async def create_detection_repository(self) -> SQLiteDetectionRepository:
        """Create and initialize the detection repository"""
        if "detection_repository" in self._repositories:
            return self._repositories["detection_repository"]
        
        await self.initialize_database()
        
        repository = SQLiteDetectionRepository(async_session)
        await repository.initialize()
        
        self._repositories["detection_repository"] = repository
        return repository
    
    async def create_video_repository(self) -> SQLiteVideoRepository:
        """Create the video repository"""
        if "video_repository" in self._repositories:
            return self._repositories["video_repository"]
        
        await self.initialize_database()
        
        repository = SQLiteVideoRepository(async_session)
        self._repositories["video_repository"] = repository
        return repository
    
    async def create_video_recording_service(self) -> VideoRecordingService:
        """Create and initialize the video recording service"""
        if "video_recording_service" in self._services:
            return self._services["video_recording_service"]
        
        # Get required repositories
        detection_repo = await self.create_detection_repository()
        video_repo = await self.create_video_repository()
        
        # Create and initialize service
        service = VideoRecordingService(detection_repo, video_repo)
        await service.initialize()
        
        self._services["video_recording_service"] = service
        return service
    
    # Other factory methods from previous implementation
    # ...
    
    async def shutdown_all(self) -> None:
        """Shutdown all services and repositories"""
        # Shutdown services in reverse order of dependencies
        for service_name in reversed(list(self._services.keys())):
            service = self._services[service_name]
            if hasattr(service, "shutdown"):
                await service.shutdown()
        
        # Shutdown repositories
        for repo_name in reversed(list(self._repositories.keys())):
            repo = self._repositories[repo_name]
            if hasattr(repo, "shutdown"):
                await repo.shutdown()

# Create singleton instance
service_factory = ServiceFactory()