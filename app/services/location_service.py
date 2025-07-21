# app/services/location_service.py
# Location management service for centralized multi-site deployment
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import uuid4

from app.models import Location, Camera, CameraGroup
from app.database import async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

class LocationService:
    """
    Service for managing multiple physical locations where cameras are deployed
    """
    
    def __init__(self):
        self.cached_locations: Dict[str, Location] = {}
        self.cache_timestamp = 0
        self.cache_ttl = 300  # 5 minutes
        self.initialization_complete = False
    
    async def initialize(self):
        """Initialize the location service"""
        try:
            # Check if we have any locations in the database
            async with async_session() as session:
                result = await session.execute(select(Location).limit(1))
                has_locations = result.scalar_one_or_none() is not None
            
            if not has_locations:
                logger.info("No locations found, creating default location")
                await self.create_default_location()
            
            self.initialization_complete = True
            logger.info("LocationService initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LocationService: {e}")
            raise
    
    async def create_default_location(self):
        """Create a default location for initial setup"""
        try:
            default_location = {
                "name": "Main Site",
                "address": "Default Location",
                "city": "Unknown",
                "state": "Unknown",
                "country": "USA",
                "timezone": "UTC",
                "description": "Default location created during system initialization"
            }
            
            location_id = await self.create_location(default_location)
            logger.info(f"Created default location: {location_id}")
            return location_id
            
        except Exception as e:
            logger.error(f"Error creating default location: {e}")
            raise
    
    async def create_location(self, location_data: Dict[str, Any]) -> str:
        """
        Create a new location
        
        Args:
            location_data: Location information dictionary
            
        Returns:
            Location ID of created location
        """
        async with async_session() as session:
            try:
                # Validate required fields
                required_fields = ["name"]
                for field in required_fields:
                    if field not in location_data:
                        raise ValueError(f"Missing required field: {field}")
                
                # Check for duplicate name
                existing = await session.execute(
                    select(Location).where(Location.name == location_data["name"])
                )
                if existing.scalar_one_or_none():
                    raise ValueError(f"Location with name '{location_data['name']}' already exists")
                
                # Create location
                location = Location(
                    name=location_data["name"],
                    address=location_data.get("address"),
                    city=location_data.get("city"),
                    state=location_data.get("state"),
                    country=location_data.get("country", "USA"),
                    latitude=location_data.get("latitude"),
                    longitude=location_data.get("longitude"),
                    timezone=location_data.get("timezone", "UTC"),
                    description=location_data.get("description"),
                    contact_info=location_data.get("contact_info", {})
                )
                
                session.add(location)
                await session.commit()
                await session.refresh(location)
                
                # Invalidate cache
                self._invalidate_cache()
                
                logger.info(f"Created location: {location.name} ({location.id})")
                return location.id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create location: {e}")
                raise
    
    async def get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Get location information by ID
        
        Args:
            location_id: Location ID
            
        Returns:
            Location information dictionary or None if not found
        """
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Location)
                    .options(
                        selectinload(Location.cameras),
                        selectinload(Location.camera_groups)
                    )
                    .where(Location.id == location_id)
                )
                location = result.scalar_one_or_none()
                
                if not location:
                    return None
                
                return await self._location_to_dict(location)
                
            except Exception as e:
                logger.error(f"Failed to get location {location_id}: {e}")
                return None
    
    async def get_all_locations(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all locations
        
        Args:
            include_inactive: Include inactive locations
            
        Returns:
            List of location information dictionaries
        """
        async with async_session() as session:
            try:
                query = select(Location).options(
                    selectinload(Location.cameras),
                    selectinload(Location.camera_groups)
                )
                
                if not include_inactive:
                    query = query.where(Location.active == True)
                
                result = await session.execute(query.order_by(Location.name))
                locations = result.scalars().all()
                
                location_list = []
                for location in locations:
                    location_dict = await self._location_to_dict(location)
                    location_list.append(location_dict)
                
                return location_list
                
            except Exception as e:
                logger.error(f"Failed to get locations: {e}")
                return []
    
    async def update_location(self, location_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update location information
        
        Args:
            location_id: Location ID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        async with async_session() as session:
            try:
                # Check if location exists
                result = await session.execute(
                    select(Location).where(Location.id == location_id)
                )
                location = result.scalar_one_or_none()
                
                if not location:
                    logger.error(f"Location not found: {location_id}")
                    return False
                
                # Apply updates
                update_dict = {k: v for k, v in updates.items() if hasattr(Location, k)}
                update_dict["updated_at"] = datetime.utcnow()
                
                await session.execute(
                    update(Location)
                    .where(Location.id == location_id)
                    .values(**update_dict)
                )
                
                await session.commit()
                
                # Invalidate cache
                self._invalidate_cache()
                
                logger.info(f"Updated location: {location_id}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update location {location_id}: {e}")
                return False
    
    async def delete_location(self, location_id: str, force: bool = False) -> bool:
        """
        Delete a location
        
        Args:
            location_id: Location ID
            force: Force deletion even if cameras exist
            
        Returns:
            True if successful, False otherwise
        """
        async with async_session() as session:
            try:
                # Check if location exists
                result = await session.execute(
                    select(Location)
                    .options(selectinload(Location.cameras))
                    .where(Location.id == location_id)
                )
                location = result.scalar_one_or_none()
                
                if not location:
                    logger.error(f"Location not found: {location_id}")
                    return False
                
                # Check for existing cameras
                if location.cameras and not force:
                    logger.error(f"Cannot delete location {location_id}: {len(location.cameras)} cameras exist")
                    return False
                
                # Delete location (cascade will handle related records)
                await session.execute(
                    delete(Location).where(Location.id == location_id)
                )
                
                await session.commit()
                
                # Invalidate cache
                self._invalidate_cache()
                
                logger.info(f"Deleted location: {location_id}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete location {location_id}: {e}")
                return False
    
    async def get_location_statistics(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a location
        
        Args:
            location_id: Location ID
            
        Returns:
            Statistics dictionary or None if location not found
        """
        async with async_session() as session:
            try:
                # Get camera counts by status
                camera_stats = await session.execute(
                    select(
                        Camera.status,
                        func.count(Camera.id).label('count')
                    )
                    .where(Camera.location_id == location_id)
                    .group_by(Camera.status)
                )
                
                status_counts = {row.status.value: row.count for row in camera_stats}
                
                # Get total cameras
                total_cameras = await session.execute(
                    select(func.count(Camera.id)).where(Camera.location_id == location_id)
                )
                total_cameras = total_cameras.scalar()
                
                # Get camera groups count
                total_groups = await session.execute(
                    select(func.count(CameraGroup.id)).where(CameraGroup.location_id == location_id)
                )
                total_groups = total_groups.scalar()
                
                # Get detection counts (last 24 hours)
                from app.models import Detection
                detections_24h = await session.execute(
                    select(func.count(Detection.id))
                    .where(
                        Detection.location_id == location_id,
                        Detection.timestamp >= datetime.utcnow() - timedelta(hours=24)
                    )
                )
                detections_24h = detections_24h.scalar()
                
                return {
                    "location_id": location_id,
                    "total_cameras": total_cameras,
                    "camera_groups": total_groups,
                    "detections_24h": detections_24h,
                    "camera_status_counts": status_counts,
                    "online_cameras": status_counts.get("online", 0),
                    "offline_cameras": status_counts.get("offline", 0),
                    "warning_cameras": status_counts.get("warning", 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Failed to get location statistics {location_id}: {e}")
                return None
    
    async def search_locations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search locations by name, address, or description
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching location dictionaries
        """
        async with async_session() as session:
            try:
                # Search in name, address, city, and description
                search_pattern = f"%{query}%"
                
                result = await session.execute(
                    select(Location)
                    .where(
                        (Location.name.ilike(search_pattern)) |
                        (Location.address.ilike(search_pattern)) |
                        (Location.city.ilike(search_pattern)) |
                        (Location.description.ilike(search_pattern))
                    )
                    .where(Location.active == True)
                    .order_by(Location.name)
                    .limit(limit)
                )
                
                locations = result.scalars().all()
                
                location_list = []
                for location in locations:
                    location_dict = await self._location_to_dict(location)
                    location_list.append(location_dict)
                
                return location_list
                
            except Exception as e:
                logger.error(f"Failed to search locations: {e}")
                return []
    
    async def get_nearby_locations(self, latitude: float, longitude: float, radius_km: float = 50) -> List[Dict[str, Any]]:
        """
        Get locations within a radius of a point
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            List of nearby location dictionaries
        """
        async with async_session() as session:
            try:
                # Simple distance calculation (not perfectly accurate but good enough)
                # For production, consider using PostGIS or similar
                lat_range = radius_km / 111.0  # Approximate km per degree latitude
                lng_range = radius_km / (111.0 * abs(latitude))  # Approximate km per degree longitude
                
                result = await session.execute(
                    select(Location)
                    .where(
                        Location.latitude.between(latitude - lat_range, latitude + lat_range),
                        Location.longitude.between(longitude - lng_range, longitude + lng_range),
                        Location.active == True
                    )
                    .order_by(Location.name)
                )
                
                locations = result.scalars().all()
                
                location_list = []
                for location in locations:
                    if location.latitude and location.longitude:
                        # Calculate actual distance
                        distance = self._calculate_distance(
                            latitude, longitude,
                            location.latitude, location.longitude
                        )
                        
                        if distance <= radius_km:
                            location_dict = await self._location_to_dict(location)
                            location_dict["distance_km"] = round(distance, 2)
                            location_list.append(location_dict)
                
                # Sort by distance
                location_list.sort(key=lambda x: x.get("distance_km", 0))
                
                return location_list
                
            except Exception as e:
                logger.error(f"Failed to get nearby locations: {e}")
                return []
    
    async def _location_to_dict(self, location: Location) -> Dict[str, Any]:
        """Convert Location model to dictionary"""
        return {
            "id": location.id,
            "name": location.name,
            "address": location.address,
            "city": location.city,
            "state": location.state,
            "country": location.country,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": location.timezone,
            "active": location.active,
            "description": location.description,
            "contact_info": location.contact_info,
            "created_at": location.created_at.isoformat() if location.created_at else None,
            "updated_at": location.updated_at.isoformat() if location.updated_at else None,
            "camera_count": len(location.cameras) if hasattr(location, 'cameras') and location.cameras else 0,
            "group_count": len(location.camera_groups) if hasattr(location, 'camera_groups') and location.camera_groups else 0
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Returns:
            Distance in kilometers
        """
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        r = 6371
        
        return c * r
    
    def _invalidate_cache(self):
        """Invalidate the location cache"""
        self.cached_locations.clear()
        self.cache_timestamp = 0