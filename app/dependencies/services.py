"""
FastAPI dependencies for services and repositories.
"""
from fastapi import Depends
from app.interfaces.camera import Camera
from app.interfaces.detector import LicensePlateDetector
from app.interfaces.enhancer import LicensePlateEnhancer
from app.interfaces.storage import DetectionRepository, EnhancementRepository
from app.factories.service_factory import service_factory
from app.repositories.sql_repository import SQLiteVideoRepository
from app.services.video_service import VideoRecordingService

async def get_camera() -> Camera:
    """
    Get the camera service.
    
    Returns:
        Camera: The camera service
    """
    camera = service_factory.get_service("camera")
    if not camera:
        camera = await service_factory.create_camera()
    return camera

async def get_detector() -> LicensePlateDetector:
    """
    Get the license plate detector.
    
    Returns:
        LicensePlateDetector: The license plate detector
    """
    detector = service_factory.get_service("detector")
    if not detector:
        detector = await service_factory.create_detector()
    return detector

async def get_enhancer() -> LicensePlateEnhancer:
    """
    Get the license plate enhancer.
    
    Returns:
        LicensePlateEnhancer: The license plate enhancer
    """
    enhancer = service_factory.get_service("enhancer")
    if not enhancer:
        enhancer = await service_factory.create_enhancer()
    return enhancer

async def get_detection_repository() -> DetectionRepository:
    """
    Get the detection repository.
    
    Returns:
        DetectionRepository: The detection repository
    """
    repo = service_factory.get_repository("detection_repository")
    if not repo:
        repo = await service_factory.create_detection_repository()
    return repo

async def get_enhancement_repository() -> EnhancementRepository:
    """
    Get the enhancement repository.
    
    Returns:
        EnhancementRepository: The enhancement repository
    """
    repo = service_factory.get_repository("enhancement_repository")
    if not repo:
        repo = await service_factory.create_enhancement_repository()
    return repo

async def get_video_repository() -> SQLiteVideoRepository:
    """
    Get the video repository.
    
    Returns:
        SQLiteVideoRepository: The video repository
    """
    repo = service_factory.get_repository("video_repository")
    if not repo:
        repo = await service_factory.create_video_repository()
    return repo

async def get_video_recording_service() -> VideoRecordingService:
    """
    Get the video recording service.
    
    Returns:
        VideoRecordingService: The video recording service
    """
    service = service_factory.get_service("video_recording_service")
    if not service:
        service = await service_factory.create_video_recording_service()
    return service