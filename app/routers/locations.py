# app/routers/locations.py
# Location management API endpoints for multi-site deployment
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.services.location_service import LocationService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Service instance (will be injected)
location_service: Optional[LocationService] = None

# Pydantic models for API
class LocationCreateRequest(BaseModel):
    name: str = Field(..., description="Location name")
    address: Optional[str] = Field(None, description="Physical address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    country: str = Field("USA", description="Country")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    timezone: str = Field("UTC", description="Timezone")
    description: Optional[str] = Field(None, description="Location description")
    contact_info: Optional[Dict[str, Any]] = Field({}, description="Contact information")

class LocationUpdateRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    description: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None

class LocationSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")

class NearbyLocationRequest(BaseModel):
    latitude: float = Field(..., description="Center latitude")
    longitude: float = Field(..., description="Center longitude")
    radius_km: float = Field(50, ge=1, le=1000, description="Search radius in kilometers")

# Dependency injection
async def get_location_service() -> LocationService:
    if location_service is None:
        raise HTTPException(status_code=503, detail="LocationService not available")
    return location_service

# Location management endpoints
@router.get("/", response_model=List[Dict[str, Any]])
async def get_locations(
    include_inactive: bool = Query(False, description="Include inactive locations"),
    limit: int = Query(50, ge=1, le=100, description="Maximum locations to return"),
    service: LocationService = Depends(get_location_service)
):
    """Get list of all locations"""
    try:
        locations = await service.get_all_locations(include_inactive)
        
        # Apply limit
        locations = locations[:limit]
        
        return locations
        
    except Exception as e:
        logger.error(f"Failed to get locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Dict[str, str])
async def create_location(
    location_data: LocationCreateRequest,
    service: LocationService = Depends(get_location_service)
):
    """Create a new location"""
    try:
        location_id = await service.create_location(location_data.dict())
        
        return {"location_id": location_id, "message": "Location created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create location: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{location_id}", response_model=Dict[str, Any])
async def get_location(
    location_id: str,
    include_statistics: bool = Query(True, description="Include location statistics"),
    service: LocationService = Depends(get_location_service)
):
    """Get specific location information"""
    try:
        location = await service.get_location(location_id)
        
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        
        if include_statistics:
            stats = await service.get_location_statistics(location_id)
            location["statistics"] = stats
        
        return location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get location {location_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{location_id}", response_model=Dict[str, str])
async def update_location(
    location_id: str,
    updates: LocationUpdateRequest,
    service: LocationService = Depends(get_location_service)
):
    """Update location information"""
    try:
        # Filter out None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        success = await service.update_location(location_id, update_dict)
        
        if not success:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {"location_id": location_id, "message": "Location updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update location {location_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{location_id}", response_model=Dict[str, str])
async def delete_location(
    location_id: str,
    force: bool = Query(False, description="Force deletion even if cameras exist"),
    service: LocationService = Depends(get_location_service)
):
    """Delete a location"""
    try:
        success = await service.delete_location(location_id, force)
        
        if not success:
            if not force:
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot delete location: cameras exist. Use force=true to override."
                )
            else:
                raise HTTPException(status_code=404, detail="Location not found")
        
        return {"location_id": location_id, "message": "Location deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete location {location_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Location search and discovery
@router.post("/search", response_model=List[Dict[str, Any]])
async def search_locations(
    search_request: LocationSearchRequest,
    service: LocationService = Depends(get_location_service)
):
    """Search locations by name, address, or description"""
    try:
        locations = await service.search_locations(
            search_request.query, 
            search_request.limit
        )
        
        return locations
        
    except Exception as e:
        logger.error(f"Failed to search locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/nearby", response_model=List[Dict[str, Any]])
async def find_nearby_locations(
    nearby_request: NearbyLocationRequest,
    service: LocationService = Depends(get_location_service)
):
    """Find locations within a radius of a point"""
    try:
        locations = await service.get_nearby_locations(
            nearby_request.latitude,
            nearby_request.longitude,
            nearby_request.radius_km
        )
        
        return locations
        
    except Exception as e:
        logger.error(f"Failed to find nearby locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Location statistics and analytics
@router.get("/{location_id}/statistics", response_model=Dict[str, Any])
async def get_location_statistics(
    location_id: str,
    service: LocationService = Depends(get_location_service)
):
    """Get detailed statistics for a location"""
    try:
        stats = await service.get_location_statistics(location_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Location not found or no statistics available")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get location statistics {location_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{location_id}/cameras", response_model=List[Dict[str, Any]])
async def get_location_cameras(
    location_id: str,
    include_inactive: bool = Query(False, description="Include inactive cameras"),
    service: LocationService = Depends(get_location_service)
):
    """Get all cameras at a location"""
    try:
        # This endpoint depends on camera registry service integration
        # For now, return placeholder
        return []
        
    except Exception as e:
        logger.error(f"Failed to get location cameras {location_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bulk operations
@router.post("/bulk/create", response_model=List[Dict[str, str]])
async def bulk_create_locations(
    locations_data: List[LocationCreateRequest],
    service: LocationService = Depends(get_location_service)
):
    """Create multiple locations in bulk"""
    try:
        results = []
        
        for location_data in locations_data:
            try:
                location_id = await service.create_location(location_data.dict())
                results.append({
                    "location_id": location_id,
                    "name": location_data.name,
                    "status": "created"
                })
            except Exception as e:
                results.append({
                    "name": location_data.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to bulk create locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Geographic utilities
@router.get("/utilities/timezones", response_model=List[str])
async def get_available_timezones():
    """Get list of available timezones"""
    try:
        import pytz
        return sorted(pytz.all_timezones)
    except ImportError:
        # Fallback if pytz not available
        return [
            "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo",
            "Asia/Shanghai", "Australia/Sydney"
        ]

@router.get("/utilities/countries", response_model=List[Dict[str, str]])
async def get_available_countries():
    """Get list of available countries"""
    return [
        {"code": "US", "name": "United States"},
        {"code": "CA", "name": "Canada"},
        {"code": "MX", "name": "Mexico"},
        {"code": "GB", "name": "United Kingdom"},
        {"code": "DE", "name": "Germany"},
        {"code": "FR", "name": "France"},
        {"code": "JP", "name": "Japan"},
        {"code": "CN", "name": "China"},
        {"code": "AU", "name": "Australia"},
        {"code": "BR", "name": "Brazil"}
    ]

# Health check
@router.get("/health", response_model=Dict[str, Any])
async def location_service_health(
    service: LocationService = Depends(get_location_service)
):
    """Check location service health"""
    try:
        # Test service by getting location count
        locations = await service.get_all_locations(include_inactive=True)
        
        return {
            "status": "healthy",
            "service": "location_service",
            "total_locations": len(locations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Location service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "location_service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }