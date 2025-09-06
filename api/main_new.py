"""
FastAPI Backend - Modular Architecture
IMPORTANT: This serves data and snapshots, NOT video streams!

This is the new modular version of main.py that imports organized endpoint modules.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import logging
from pathlib import Path

# Import our core utilities
from api.core.config import setup_logging
from api.core.errors import APIError

# Import endpoint modules
from api.endpoints.cameras import router as cameras_router
from api.endpoints.detections import router as detections_router  
from api.endpoints.system import router as system_router

# Import existing modules that are already modular
from auth.endpoints import auth_router, users_router
from monitoring.endpoints import monitoring_router, periodic_metrics_update
from monitoring.middleware import setup_monitoring_middleware
from analytics.endpoints import analytics_router

# Import other existing endpoint modules
try:
    from api.camera_endpoints import router as legacy_camera_router, init_camera_api
    from api.storage_endpoints import storage_router
    HAS_STORAGE_ENDPOINTS = True
except ImportError:
    legacy_camera_router = None
    storage_router = None
    HAS_STORAGE_ENDPOINTS = False

# Import universal detection router if enabled
try:
    from utils.feature_flags import feature_flags
    universal_detection_router = None
    if feature_flags.is_enabled('api_features.universal_detection_endpoints'):
        from api.universal_detection_endpoints import router as universal_detection_router
except ImportError:
    universal_detection_router = None

# Import WebSocket and background services
try:
    from api.websocket_manager import websocket_manager, broadcast_camera_status, broadcast_recording_status
    from api.background_monitor import start_background_monitoring, stop_background_monitoring
except ImportError:
    websocket_manager = None
    start_background_monitoring = None
    stop_background_monitoring = None

# Import services for initialization
from ai_pipeline.filtered_pipeline import get_filtered_pipeline
from database.foundation_service import get_foundation_database_service
from utils.feature_flags import is_license_plate_detection_enabled
from analytics import initialize_analytics_system

# Setup logging
logger = setup_logging("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Foundation 3 API Service...")
    
    try:
        # Initialize database service
        db_service = await get_foundation_database_service()
        logger.info("Database service initialized")
        
        # Initialize AI pipeline if enabled
        if is_license_plate_detection_enabled():
            pipeline = get_filtered_pipeline()
            logger.info("License plate detection pipeline initialized with filtering")
        else:
            logger.warning("License plate detection disabled - detection will not function")
        
        # Initialize analytics system
        try:
            await initialize_analytics_system()
            logger.info("Analytics system initialized")
        except Exception as e:
            logger.warning(f"Analytics initialization failed: {e}")
        
        # Start background monitoring
        if start_background_monitoring:
            await start_background_monitoring()
            logger.info("Background monitoring started")
        
        # Start periodic metrics update
        asyncio.create_task(periodic_metrics_update())
        logger.info("Periodic metrics update started")
        
        app.state.start_time = asyncio.get_event_loop().time()
        logger.info("API service startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down API service...")
        
        if stop_background_monitoring:
            await stop_background_monitoring()
            logger.info("Background monitoring stopped")
        
        logger.info("API service shutdown completed")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Foundation 3 - License Plate Recognition API",
    description="Production-ready AI video surveillance system with license plate detection",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup monitoring middleware
setup_monitoring_middleware(app)

# Mount static files
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include modular endpoint routers
app.include_router(cameras_router, prefix="", tags=["cameras"])
app.include_router(detections_router, prefix="", tags=["detections"])
app.include_router(system_router, prefix="", tags=["system"])

# Include existing modular routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(monitoring_router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])

# Include optional routers
if HAS_STORAGE_ENDPOINTS and storage_router:
    app.include_router(storage_router, prefix="/api/storage", tags=["storage"])

if universal_detection_router:
    app.include_router(universal_detection_router, prefix="/api/universal", tags=["universal_detection"])

if legacy_camera_router:
    # Include legacy camera router for backward compatibility
    app.include_router(legacy_camera_router, prefix="/api/legacy", tags=["legacy_cameras"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    if not websocket_manager:
        await websocket.close(code=1000, reason="WebSocket not available")
        return
    
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data}")
            
            # Echo back or process the message as needed
            await websocket.send_text(f"Server received: {data}")
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Foundation 3 - License Plate Recognition API",
        "version": "3.0.0",
        "status": "running",
        "architecture": "modular",
        "endpoints": {
            "health": "/health",
            "docs": "/docs", 
            "cameras": "/api/cameras",
            "detections": "/api/detections",
            "system": "/api/system",
            "auth": "/api/auth",
            "websocket": "/ws"
        },
        "features": {
            "modular_architecture": True,
            "standardized_errors": True,
            "comprehensive_logging": True,
            "real_time_websockets": websocket_manager is not None,
            "monitoring": True,
            "analytics": True
        }
    }

# Error handlers
@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    """Handle custom API errors"""
    return exc

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return APIError(
        status_code=500,
        message="Internal server error",
        error_code="INTERNAL_ERROR"
    )

if __name__ == "__main__":
    import uvicorn
    
    # Initialize camera API if available
    if init_camera_api:
        asyncio.run(init_camera_api())
    
    # Run the server
    uvicorn.run(
        "api.main_new:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Set to True for development
        log_level="info"
    )