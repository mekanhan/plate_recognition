from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
import datetime
import time
import logging
from app.services.detection_service import DetectionService
from app.services.storage_service import StorageService
from app.dependencies.detection import get_detection_service
from config.settings import Config

router = APIRouter()

# Load configuration
config = Config()

# Initialize templates only if web UI is enabled
if config.is_web_ui_enabled:
    templates = Jinja2Templates(directory="templates")
    
    # Add custom filter to convert timestamp to readable format
    def fromtimestamp(value):
        try:
            return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return "Unknown"

    # Add pluralize filter
    def pluralize(value, singular='', plural='s'):
        try:
            count = int(value)
            return plural if count != 1 else singular
        except:
            return plural

    templates.env.filters["fromtimestamp"] = fromtimestamp
    templates.env.filters["pluralize"] = pluralize
else:
    templates = None

logger = logging.getLogger(__name__)

storage_service = None
detection_service = None

def _rank_search_results(results, search_query):
    """
    Rank search results based on match quality for contains/exact searches
    Priority: Exact > Starts with > Contains (by position)
    """
    if not results or not search_query:
        return results
    
    search_term = search_query.strip().upper()
    ranked_results = []
    
    for result in results:
        plate_text = (result.get('plate_text') or '').upper()
        
        # Calculate match score
        if plate_text == search_term:
            # Exact match (highest priority)
            result['search_score'] = 1.0
            result['match_type'] = 'exact'
        elif plate_text.startswith(search_term):
            # Starts with match
            result['search_score'] = 0.9
            result['match_type'] = 'starts_with'
        elif search_term in plate_text:
            # Contains match - score based on position (earlier = better)
            position = plate_text.index(search_term)
            position_score = max(0.5, 0.8 - (position * 0.1))
            result['search_score'] = position_score
            result['match_type'] = 'contains'
        else:
            # Fallback for edge cases
            result['search_score'] = 0.1
            result['match_type'] = 'fallback'
        
        ranked_results.append(result)
    
    # Sort by search score (descending), then by confidence, then by timestamp
    def safe_timestamp_sort(result):
        timestamp = result.get('timestamp', 0)
        # Handle string timestamps (ISO format)
        if isinstance(timestamp, str):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp_value = dt.timestamp()
            except:
                timestamp_value = 0
        elif isinstance(timestamp, (int, float)):
            timestamp_value = timestamp
        else:
            timestamp_value = 0
        
        return (
            -result.get('search_score', 0),
            -result.get('confidence', 0),
            -timestamp_value
        )
    
    ranked_results.sort(key=safe_timestamp_sort)
    
    return ranked_results

async def get_storage_service():
    """Dependency to get the storage service"""
    try:
        return storage_service
    except Exception as e:
        logger.error(f"Error getting storage service: {e}")
        return None

@router.get("/latest", response_class=HTMLResponse)
async def get_latest_detections(
    request: Request,
    detection_svc: DetectionService = Depends(get_detection_service)
):
    """Get the latest detections (Web UI only)"""
    if not config.is_web_ui_enabled or not templates:
        raise HTTPException(status_code=503, detail="Web UI not available in headless mode")
    
    try:
        # Try to get detections from database first, fall back to in-memory
        if detection_svc and hasattr(detection_svc, 'storage_service') and detection_svc.storage_service:
            detections = await detection_svc.storage_service.get_detections()
        else:
            detections = await detection_svc.get_latest_detections() if detection_svc else []
        
        # Convert detection format to include required fields for template
        formatted_detections = []
        for detection in detections:
            formatted_detection = {
                'plate_text': detection.get('plate_text', ''),
                'confidence': detection.get('confidence', 0.0),
                'timestamp': None,
                'state': detection.get('state', 'Unknown'),
                'detection_id': detection.get('detection_id', ''),
                'bbox': detection.get('bbox', detection.get('box', []))
            }
            
            # Handle timestamp conversion
            if 'timestamp' in detection:
                if isinstance(detection['timestamp'], (int, float)):
                    import datetime
                    formatted_detection['timestamp'] = datetime.datetime.fromtimestamp(detection['timestamp'])
                else:
                    formatted_detection['timestamp'] = detection['timestamp']
            
            formatted_detections.append(formatted_detection)
        
        return templates.TemplateResponse(
            "results.html", 
            {"request": request, "detections": formatted_detections}
        )
    except Exception as e:
        logger.error(f"Error getting latest detections: {e}")
        return templates.TemplateResponse(
            "results.html", 
            {"request": request, "detections": []}
        )

@router.get("/latest/json")
async def get_latest_detections_json(
    detection_svc: DetectionService = Depends(get_detection_service)
):
    """Get the latest detections as JSON"""
    try:
        if detection_svc and hasattr(detection_svc, 'storage_service') and detection_svc.storage_service:
            return await detection_svc.storage_service.get_detections()
        else:
            return await detection_svc.get_latest_detections() if detection_svc else []
    except Exception as e:
        logger.error(f"Error getting latest detections JSON: {e}")
        return []

@router.get("/all", response_class=HTMLResponse)
async def get_all_detections(
    request: Request,
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all detections from the current session (Web UI only)"""
    if not config.is_web_ui_enabled or not templates:
        raise HTTPException(status_code=503, detail="Web UI not available in headless mode")
    
    try:
        if storage_svc:
            detections = await storage_svc.get_detections()
        else:
            detections = []
            
        # Convert detection format to include required fields for template
        formatted_detections = []
        for detection in detections:
            formatted_detection = {
                'plate_text': detection.get('plate_text', ''),
                'confidence': detection.get('confidence', 0.0),
                'timestamp': None,
                'state': detection.get('state', 'Unknown'),
                'detection_id': detection.get('detection_id', ''),
                'bbox': detection.get('bbox', detection.get('box', []))
            }
            
            # Handle timestamp conversion
            if 'timestamp' in detection:
                if isinstance(detection['timestamp'], (int, float)):
                    import datetime
                    formatted_detection['timestamp'] = datetime.datetime.fromtimestamp(detection['timestamp'])
                else:
                    formatted_detection['timestamp'] = detection['timestamp']
            
            formatted_detections.append(formatted_detection)
            
        return templates.TemplateResponse(
            "results.html", 
            {"request": request, "detections": formatted_detections}
        )
    except Exception as e:
        logger.error(f"Error getting all detections: {e}")
        return templates.TemplateResponse(
            "results.html", 
            {"request": request, "detections": []}
        )

@router.get("/all/json")
async def get_all_detections_json(
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all detections as JSON (works in both modes)"""
    try:
        if storage_svc:
            return await storage_svc.get_detections()
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting all detections JSON: {e}")
        return []

@router.get("/all/json")
async def get_all_detections_json(
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all detections from the current session as JSON"""
    return await storage_svc.get_detections()

@router.get("/enhanced", response_class=HTMLResponse)
async def get_enhanced_results(
    request: Request,
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all enhanced results from the current session"""
    try:
        if storage_svc and hasattr(storage_svc, 'get_enhanced_results'):
            enhanced_results = await storage_svc.get_enhanced_results()
        else:
            enhanced_results = []
            
        # Convert detection format to include required fields for template
        formatted_detections = []
        for detection in enhanced_results:
            formatted_detection = {
                'plate_text': detection.get('plate_text', ''),
                'confidence': detection.get('confidence', 0.0),
                'timestamp': None,
                'state': detection.get('state', 'Unknown'),
                'detection_id': detection.get('detection_id', ''),
                'bbox': detection.get('bbox', detection.get('box', []))
            }
            
            # Handle timestamp conversion
            if 'timestamp' in detection:
                if isinstance(detection['timestamp'], (int, float)):
                    import datetime
                    formatted_detection['timestamp'] = datetime.datetime.fromtimestamp(detection['timestamp'])
                else:
                    formatted_detection['timestamp'] = detection['timestamp']
            
            formatted_detections.append(formatted_detection)
            
        return templates.TemplateResponse(
            "results.html", 
            {"request": request, "detections": formatted_detections}
        )
    except Exception as e:
        logger.error(f"Error getting enhanced results: {e}")
        return templates.TemplateResponse(
            "results.html", 
            {"request": request, "detections": []}
        )

@router.get("/enhanced/json")
async def get_enhanced_results_json(
    storage_svc: StorageService = Depends(get_storage_service)
):
    """Get all enhanced results from the current session as JSON"""
    return await storage_svc.get_enhanced_results()

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring storage and database status"""
    try:
        status = {
            "status": "healthy",
            "services": {},
            "timestamp": time.time()
        }
        
        # Check storage service
        if storage_service and hasattr(storage_service, 'initialization_complete'):
            status["services"]["storage"] = {
                "initialized": storage_service.initialization_complete,
                "detections_saved_json": getattr(storage_service, 'detections_saved_to_json', 0),
                "detections_saved_sql": getattr(storage_service, 'detections_saved_to_db', 0),
                "session_file": getattr(storage_service, 'session_file', None)
            }
        
        # Check detection service
        if detection_service and hasattr(detection_service, 'license_plate_service'):
            status["services"]["detection"] = {
                "initialized": detection_service.license_plate_service is not None,
                "detections_processed": getattr(detection_service, 'detections_processed', 0),
                "frame_count": getattr(detection_service, 'frame_count', 0)
            }
        
        # Check database connectivity
        try:
            from app.database import async_session
            from sqlalchemy import text
            async with async_session() as session:
                result = await session.execute(text("SELECT COUNT(*) FROM detections"))
                db_count = result.scalar()
                status["services"]["database"] = {
                    "connected": True,
                    "detection_count": db_count
                }
        except Exception as e:
            status["services"]["database"] = {
                "connected": False,
                "error": str(e)
            }
        
        return status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@router.get("/detections")
async def get_detections_with_filters(
    plate: str = None,
    from_date: str = None,  # Called 'from' in frontend but 'from_date' here (from is reserved)
    to: str = None,
    confidence: float = None,
    sort: str = "timestamp",
    limit: int = 25,
    page: int = 1,
    fuzzy: bool = False,  # Fuzzy matching off by default
    time_range: str = None,  # Predefined time ranges: today, yesterday, this_week, etc.
    start_time: str = None,  # Time of day filtering (HH:MM format)
    end_time: str = None,
    exact: bool = False  # Force exact matching
):
    """Get detections with enhanced filtering and fuzzy search support"""
    try:
        # Debug logging to troubleshoot quick filter + search issue
        logger.info(f"Search parameters: plate='{plate}', time_range='{time_range}', from_date='{from_date}', to='{to}', fuzzy={fuzzy}, exact={exact}")
        
        # Special debug for the specific issue
        if plate and time_range == "last_hour":
            logger.info(f"LAST HOUR DEBUG: Searching for '{plate}' with last_hour filter")
        
        from app.database import async_session
        from app.models import Detection
        from sqlalchemy import select, and_, desc, asc, or_, text
        from app.utils.text_normalization import fuzzy_engine
        import datetime
        
        async with async_session() as session:
            # Start with base query
            query = select(Detection)
            filters = []
            
            # Enhanced plate text filtering with fuzzy matching
            if plate and len(plate.strip()) >= 2:
                if exact:
                    # Exact match only
                    normalized_plate = plate.strip().upper().replace(' ', '')
                    filters.append(text("UPPER(REPLACE(plate_text, ' ', '')) = :plate_exact").params(plate_exact=normalized_plate))
                elif fuzzy:
                    # Use fuzzy search engine
                    search_terms = fuzzy_engine.prepare_search_terms(plate)
                    if search_terms['exact_match']:
                        # Build fuzzy search conditions
                        fuzzy_conditions = []
                        params = {}
                        
                        # Exact match (highest priority)
                        normalized = search_terms['normalized']
                        fuzzy_conditions.append("UPPER(REPLACE(plate_text, ' ', '')) = :exact_match")
                        params['exact_match'] = normalized
                        
                        # Variant matches for OCR errors
                        for i, variant in enumerate(search_terms['variants'][:10]):
                            param_name = f"variant_{i}"
                            fuzzy_conditions.append(f"UPPER(REPLACE(plate_text, ' ', '')) = :{param_name}")
                            params[param_name] = variant
                        
                        # Contains match for partial searches
                        fuzzy_conditions.append("UPPER(plate_text) LIKE :contains_match")
                        params['contains_match'] = f"%{normalized}%"
                        
                        # Combine fuzzy conditions with OR
                        fuzzy_sql = " OR ".join(fuzzy_conditions)
                        filters.append(text(f"({fuzzy_sql})").params(**params))
                else:
                    # Enhanced "contains anywhere" search for better partial matching
                    search_term = plate.strip().upper()
                    
                    # Split search term by common separators and spaces
                    import re
                    search_parts = re.split(r'[\s\-_]+', search_term)
                    search_parts = [part for part in search_parts if len(part) >= 1]
                    
                    if len(search_parts) == 1:
                        # Single term - standard contains search
                        filters.append(Detection.plate_text.ilike(f"%{search_term}%"))
                    else:
                        # Multiple terms - each part should be found anywhere in the plate
                        part_conditions = []
                        for part in search_parts:
                            part_conditions.append(Detection.plate_text.ilike(f"%{part}%"))
                        
                        # All parts must be found (AND condition)
                        filters.append(and_(*part_conditions))
            
            # Enhanced time range filtering
            if time_range:
                now = datetime.datetime.now()
                
                if time_range == "today":
                    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    filters.append(Detection.timestamp >= start_of_day)
                elif time_range == "yesterday":
                    yesterday = now - datetime.timedelta(days=1)
                    start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_of_yesterday = start_of_yesterday + datetime.timedelta(days=1)
                    filters.append(and_(
                        Detection.timestamp >= start_of_yesterday,
                        Detection.timestamp < end_of_yesterday
                    ))
                elif time_range == "this_week":
                    # Start of current week (Monday)
                    days_since_monday = now.weekday()
                    start_of_week = now - datetime.timedelta(days=days_since_monday)
                    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                    filters.append(Detection.timestamp >= start_of_week)
                elif time_range == "last_week":
                    days_since_monday = now.weekday()
                    start_of_this_week = now - datetime.timedelta(days=days_since_monday)
                    start_of_last_week = start_of_this_week - datetime.timedelta(days=7)
                    start_of_last_week = start_of_last_week.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_of_last_week = start_of_this_week.replace(hour=0, minute=0, second=0, microsecond=0)
                    filters.append(and_(
                        Detection.timestamp >= start_of_last_week,
                        Detection.timestamp < end_of_last_week
                    ))
                elif time_range == "this_month":
                    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    filters.append(Detection.timestamp >= start_of_month)
                elif time_range == "last_month":
                    start_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    if start_of_this_month.month == 1:
                        start_of_last_month = start_of_this_month.replace(year=start_of_this_month.year - 1, month=12)
                    else:
                        start_of_last_month = start_of_this_month.replace(month=start_of_this_month.month - 1)
                    filters.append(and_(
                        Detection.timestamp >= start_of_last_month,
                        Detection.timestamp < start_of_this_month
                    ))
                elif time_range == "last_hour":
                    one_hour_ago = now - datetime.timedelta(hours=1)
                    filters.append(Detection.timestamp >= one_hour_ago)
                elif time_range == "last_24h":
                    twenty_four_hours_ago = now - datetime.timedelta(hours=24)
                    filters.append(Detection.timestamp >= twenty_four_hours_ago)
                elif time_range == "last_7d":
                    seven_days_ago = now - datetime.timedelta(days=7)
                    filters.append(Detection.timestamp >= seven_days_ago)
            
            # Custom date range filtering (original functionality)
            if from_date:
                try:
                    from_dt = datetime.datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                    filters.append(Detection.timestamp >= from_dt)
                except ValueError:
                    pass  # Skip invalid date
            
            if to:
                try:
                    to_dt = datetime.datetime.fromisoformat(to.replace('Z', '+00:00'))
                    # Add one day to include the full end date
                    to_dt = to_dt + datetime.timedelta(days=1)
                    filters.append(Detection.timestamp < to_dt)
                except ValueError:
                    pass  # Skip invalid date
            
            # Time-of-day filtering
            if start_time or end_time:
                time_conditions = []
                
                if start_time:
                    try:
                        start_hour, start_minute = map(int, start_time.split(':'))
                        time_conditions.append(text("strftime('%H:%M', timestamp) >= :start_time").params(start_time=start_time))
                    except ValueError:
                        pass
                
                if end_time:
                    try:
                        end_hour, end_minute = map(int, end_time.split(':'))
                        time_conditions.append(text("strftime('%H:%M', timestamp) <= :end_time").params(end_time=end_time))
                    except ValueError:
                        pass
                
                if time_conditions:
                    filters.append(and_(*time_conditions))
            
            # Confidence filtering
            if confidence is not None:
                filters.append(Detection.confidence >= confidence)
            
            # Apply filters to query
            if filters:
                query = query.where(and_(*filters))
            
            # Apply sorting
            if sort == "confidence":
                query = query.order_by(desc(Detection.confidence))
            elif sort == "plate_text":
                query = query.order_by(asc(Detection.plate_text))
            else:  # Default to timestamp
                query = query.order_by(desc(Detection.timestamp))
            
            # Get total count for pagination
            count_query = select(Detection).where(and_(*filters)) if filters else select(Detection)
            from sqlalchemy import func
            total_result = await session.execute(
                select(func.count()).select_from(count_query.subquery())
            )
            total = total_result.scalar()
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(query)
            detections = result.scalars().all()
            
            # Debug: log result count
            if plate and time_range == "last_hour":
                logger.info(f"LAST HOUR DEBUG: Found {len(detections)} results for '{plate}'")
            
            # Convert to dict format
            detection_list = []
            for detection in detections:
                detection_dict = {
                    "id": detection.id,
                    "plate_text": detection.plate_text,
                    "confidence": detection.confidence,
                    "timestamp": detection.timestamp.isoformat() if detection.timestamp else None,
                    "bbox": [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2] 
                        if all(x is not None for x in [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2]) 
                        else None,
                    "frame_id": detection.frame_id,
                    "raw_text": detection.raw_text,
                    "state": detection.state,
                    "status": detection.status,
                    "image_path": detection.image_path,
                    "video_path": detection.video_path
                }
                detection_list.append(detection_dict)
            
            # Apply enhanced ranking for all plate searches (not just fuzzy)
            if plate and len(plate.strip()) >= 2:
                if fuzzy:
                    # Use existing fuzzy ranking
                    detection_list = fuzzy_engine.rank_results(detection_list, plate)
                else:
                    # Apply custom ranking for contains/exact searches
                    detection_list = _rank_search_results(detection_list, plate)
            
            return {
                "detections": detection_list,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit  # Ceiling division
            }
            
    except Exception as e:
        logger.error(f"Error getting filtered detections: {e}")
        return {
            "detections": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 0,
            "error": str(e)
        }

@router.get("/detections/export")
async def export_detections_csv(
    plate: str = None,
    from_date: str = None,
    to: str = None,
    confidence: float = None,
    sort: str = "timestamp",
    fuzzy: bool = False,
    time_range: str = None,
    start_time: str = None,
    end_time: str = None,
    exact: bool = False,
    format: str = "csv"  # Support for future formats
):
    """Export filtered detections as CSV file"""
    try:
        from app.database import async_session
        from app.models import Detection
        from sqlalchemy import select, and_, desc, asc, text
        from app.utils.text_normalization import fuzzy_engine
        from fastapi.responses import StreamingResponse
        import datetime
        import io
        import csv
        
        async with async_session() as session:
            # Use the same filtering logic as get_detections_with_filters
            query = select(Detection)
            filters = []
            
            # Enhanced plate text filtering with fuzzy matching
            if plate and len(plate.strip()) >= 2:
                if exact:
                    # Exact match only
                    normalized_plate = plate.strip().upper().replace(' ', '')
                    filters.append(text("UPPER(REPLACE(plate_text, ' ', '')) = :plate_exact").params(plate_exact=normalized_plate))
                elif fuzzy:
                    # Use fuzzy search engine
                    search_terms = fuzzy_engine.prepare_search_terms(plate)
                    if search_terms['exact_match']:
                        # Build fuzzy search conditions
                        fuzzy_conditions = []
                        params = {}
                        
                        # Exact match (highest priority)
                        normalized = search_terms['normalized']
                        fuzzy_conditions.append("UPPER(REPLACE(plate_text, ' ', '')) = :exact_match")
                        params['exact_match'] = normalized
                        
                        # Variant matches for OCR errors
                        for i, variant in enumerate(search_terms['variants'][:10]):
                            param_name = f"variant_{i}"
                            fuzzy_conditions.append(f"UPPER(REPLACE(plate_text, ' ', '')) = :{param_name}")
                            params[param_name] = variant
                        
                        # Contains match for partial searches
                        fuzzy_conditions.append("UPPER(plate_text) LIKE :contains_match")
                        params['contains_match'] = f"%{normalized}%"
                        
                        # Combine fuzzy conditions with OR
                        fuzzy_sql = " OR ".join(fuzzy_conditions)
                        filters.append(text(f"({fuzzy_sql})").params(**params))
                else:
                    # Enhanced "contains anywhere" search for better partial matching
                    search_term = plate.strip().upper()
                    
                    # Split search term by common separators and spaces
                    import re
                    search_parts = re.split(r'[\s\-_]+', search_term)
                    search_parts = [part for part in search_parts if len(part) >= 1]
                    
                    if len(search_parts) == 1:
                        # Single term - standard contains search
                        filters.append(Detection.plate_text.ilike(f"%{search_term}%"))
                    else:
                        # Multiple terms - each part should be found anywhere in the plate
                        part_conditions = []
                        for part in search_parts:
                            part_conditions.append(Detection.plate_text.ilike(f"%{part}%"))
                        
                        # All parts must be found (AND condition)
                        filters.append(and_(*part_conditions))
            
            # Enhanced time range filtering (same logic as main endpoint)
            if time_range:
                now = datetime.datetime.now()
                
                if time_range == "today":
                    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    filters.append(Detection.timestamp >= start_of_day)
                elif time_range == "yesterday":
                    yesterday = now - datetime.timedelta(days=1)
                    start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_of_yesterday = start_of_yesterday + datetime.timedelta(days=1)
                    filters.append(and_(
                        Detection.timestamp >= start_of_yesterday,
                        Detection.timestamp < end_of_yesterday
                    ))
                elif time_range == "this_week":
                    days_since_monday = now.weekday()
                    start_of_week = now - datetime.timedelta(days=days_since_monday)
                    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                    filters.append(Detection.timestamp >= start_of_week)
                elif time_range == "last_week":
                    days_since_monday = now.weekday()
                    start_of_this_week = now - datetime.timedelta(days=days_since_monday)
                    start_of_last_week = start_of_this_week - datetime.timedelta(days=7)
                    start_of_last_week = start_of_last_week.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_of_last_week = start_of_this_week.replace(hour=0, minute=0, second=0, microsecond=0)
                    filters.append(and_(
                        Detection.timestamp >= start_of_last_week,
                        Detection.timestamp < end_of_last_week
                    ))
                elif time_range == "this_month":
                    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    filters.append(Detection.timestamp >= start_of_month)
                elif time_range == "last_month":
                    start_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    if start_of_this_month.month == 1:
                        start_of_last_month = start_of_this_month.replace(year=start_of_this_month.year - 1, month=12)
                    else:
                        start_of_last_month = start_of_this_month.replace(month=start_of_this_month.month - 1)
                    filters.append(and_(
                        Detection.timestamp >= start_of_last_month,
                        Detection.timestamp < start_of_this_month
                    ))
                elif time_range == "last_hour":
                    one_hour_ago = now - datetime.timedelta(hours=1)
                    filters.append(Detection.timestamp >= one_hour_ago)
                elif time_range == "last_24h":
                    twenty_four_hours_ago = now - datetime.timedelta(hours=24)
                    filters.append(Detection.timestamp >= twenty_four_hours_ago)
                elif time_range == "last_7d":
                    seven_days_ago = now - datetime.timedelta(days=7)
                    filters.append(Detection.timestamp >= seven_days_ago)
            
            # Custom date range filtering
            if from_date:
                try:
                    from_dt = datetime.datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                    filters.append(Detection.timestamp >= from_dt)
                except ValueError:
                    pass
            
            if to:
                try:
                    to_dt = datetime.datetime.fromisoformat(to.replace('Z', '+00:00'))
                    to_dt = to_dt + datetime.timedelta(days=1)
                    filters.append(Detection.timestamp < to_dt)
                except ValueError:
                    pass
            
            # Time-of-day filtering
            if start_time or end_time:
                time_conditions = []
                
                if start_time:
                    try:
                        start_hour, start_minute = map(int, start_time.split(':'))
                        time_conditions.append(text("strftime('%H:%M', timestamp) >= :start_time").params(start_time=start_time))
                    except ValueError:
                        pass
                
                if end_time:
                    try:
                        end_hour, end_minute = map(int, end_time.split(':'))
                        time_conditions.append(text("strftime('%H:%M', timestamp) <= :end_time").params(end_time=end_time))
                    except ValueError:
                        pass
                
                if time_conditions:
                    filters.append(and_(*time_conditions))
            
            # Confidence filtering
            if confidence is not None:
                filters.append(Detection.confidence >= confidence)
            
            # Apply filters to query
            if filters:
                query = query.where(and_(*filters))
            
            # Apply sorting
            if sort == "confidence":
                query = query.order_by(desc(Detection.confidence))
            elif sort == "plate_text":
                query = query.order_by(asc(Detection.plate_text))
            else:  # Default to timestamp
                query = query.order_by(desc(Detection.timestamp))
            
            # Execute query (no pagination for export - get all results)
            result = await session.execute(query)
            detections = result.scalars().all()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
            
            # Write CSV header
            writer.writerow([
                'ID',
                'License Plate',
                'Confidence',
                'Timestamp',
                'Date',
                'Time',
                'State',
                'Status',
                'Bounding Box (x1,y1,x2,y2)',
                'Frame ID',
                'Raw Text',
                'Image Path',
                'Video Path'
            ])
            
            # Write detection data
            for detection in detections:
                # Format timestamp
                if detection.timestamp:
                    timestamp_str = detection.timestamp.isoformat()
                    date_str = detection.timestamp.strftime('%Y-%m-%d')
                    time_str = detection.timestamp.strftime('%H:%M:%S')
                else:
                    timestamp_str = date_str = time_str = ''
                
                # Format bounding box
                bbox_str = ''
                if all(x is not None for x in [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2]):
                    bbox_str = f"{detection.box_x1},{detection.box_y1},{detection.box_x2},{detection.box_y2}"
                
                writer.writerow([
                    detection.id,
                    detection.plate_text or '',
                    f"{detection.confidence:.3f}" if detection.confidence else '',
                    timestamp_str,
                    date_str,
                    time_str,
                    detection.state or '',
                    detection.status or '',
                    bbox_str,
                    detection.frame_id or '',
                    detection.raw_text or '',
                    detection.image_path or '',
                    detection.video_path or ''
                ])
            
            # Apply fuzzy ranking if plate search was used
            if plate and len(plate.strip()) >= 2 and fuzzy:
                # Note: For CSV export, we keep database order rather than re-ranking
                # since ranking is more relevant for UI display
                pass
            
            # Prepare file for download
            output.seek(0)
            
            # Generate filename with timestamp
            now = datetime.datetime.now()
            filename = f"license_plate_detections_{now.strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Create response
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type='text/csv',
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "text/csv; charset=utf-8"
                }
            )
            
    except Exception as e:
        logger.error(f"Error exporting detections to CSV: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/debug/search_test")
async def debug_search_test(plate: str = "VBR7660"):
    """Debug endpoint to test search with and without time filters"""
    try:
        from app.database import async_session
        from app.models import Detection
        from sqlalchemy import select, and_, text, func
        import datetime
        
        async with async_session() as session:
            # First, check total records in database
            total_query = select(func.count(Detection.id))
            total_result = await session.execute(total_query)
            total_count = total_result.scalar()
            
            # Test 1: Search without time filter
            query1 = select(Detection).where(Detection.plate_text.ilike(f"%{plate}%"))
            result1 = await session.execute(query1)
            no_time_filter = result1.scalars().all()
            
            # Test 2: Search with last hour filter only
            now = datetime.datetime.now()
            one_hour_ago = now - datetime.timedelta(hours=1)
            query2 = select(Detection).where(Detection.timestamp >= one_hour_ago)
            result2 = await session.execute(query2)
            time_filter_only = result2.scalars().all()
            
            # Test 3: Search with both filters combined
            query3 = select(Detection).where(and_(
                Detection.plate_text.ilike(f"%{plate}%"),
                Detection.timestamp >= one_hour_ago
            ))
            result3 = await session.execute(query3)
            both_filters = result3.scalars().all()
            
            # Test 4: Check if the specific plate exists in last hour
            query4 = select(Detection).where(and_(
                Detection.plate_text == plate,
                Detection.timestamp >= one_hour_ago
            ))
            result4 = await session.execute(query4)
            exact_match = result4.scalars().all()
            
            # Test 5: Get latest detections to check timestamps
            latest_query = select(Detection).order_by(Detection.timestamp.desc()).limit(5)
            latest_result = await session.execute(latest_query)
            latest_detections = latest_result.scalars().all()
            
            return {
                "database_status": {
                    "total_detections_in_sql": total_count,
                    "latest_detections": [{
                        "plate": d.plate_text, 
                        "timestamp": d.timestamp.isoformat() if d.timestamp else None
                    } for d in latest_detections]
                },
                "search_term": plate,
                "no_time_filter_count": len(no_time_filter),
                "time_filter_only_count": len(time_filter_only), 
                "both_filters_count": len(both_filters),
                "exact_match_count": len(exact_match),
                "one_hour_ago": one_hour_ago.isoformat(),
                "current_time": now.isoformat(),
                "sample_plates_in_last_hour": [d.plate_text for d in time_filter_only[:10]],
                "sample_matching_plates": [d.plate_text for d in no_time_filter[:5]],
                "timestamps_in_last_hour": [d.timestamp.isoformat() if d.timestamp else None for d in time_filter_only[:5]]
            }
            
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/timestamps")
async def debug_timestamps():
    """Debug endpoint to check timestamp ranges in database"""
    try:
        from app.database import async_session
        from app.models import Detection
        from sqlalchemy import select, func
        import datetime
        
        async with async_session() as session:
            # Get timestamp range
            result = await session.execute(
                select(
                    func.min(Detection.timestamp).label('earliest'),
                    func.max(Detection.timestamp).label('latest'),
                    func.count(Detection.id).label('total_count')
                )
            )
            stats = result.first()
            
            # Get recent detection count (last hour)
            now = datetime.datetime.now()
            one_hour_ago = now - datetime.timedelta(hours=1)
            
            recent_result = await session.execute(
                select(func.count(Detection.id)).where(Detection.timestamp >= one_hour_ago)
            )
            recent_count = recent_result.scalar()
            
            return {
                "earliest_detection": stats.earliest.isoformat() if stats.earliest else None,
                "latest_detection": stats.latest.isoformat() if stats.latest else None,
                "total_detections": stats.total_count,
                "detections_last_hour": recent_count,
                "current_time": now.isoformat()
            }
            
    except Exception as e:
        return {"error": str(e)}

@router.get("/database/json")
async def get_database_detections():
    """Get detections directly from the SQL database"""
    try:
        from app.database import async_session
        from app.models import Detection
        from sqlalchemy import select
        
        async with async_session() as session:
            result = await session.execute(
                select(Detection).order_by(Detection.timestamp.desc()).limit(50)
            )
            detections = result.scalars().all()
            
            # Convert to dict format
            detection_list = []
            for detection in detections:
                detection_dict = {
                    "detection_id": detection.id,
                    "plate_text": detection.plate_text,
                    "confidence": detection.confidence,
                    "timestamp": detection.timestamp.timestamp() if detection.timestamp else None,
                    "box": [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2] 
                        if all(x is not None for x in [detection.box_x1, detection.box_y1, detection.box_x2, detection.box_y2]) 
                        else None,
                    "frame_id": detection.frame_id,
                    "raw_text": detection.raw_text,
                    "state": detection.state,
                    "status": detection.status,
                    "image_path": detection.image_path,
                    "video_path": detection.video_path
                }
                detection_list.append(detection_dict)
            
            return {
                "source": "sql_database",
                "count": len(detection_list),
                "detections": detection_list
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "source": "sql_database"
        }