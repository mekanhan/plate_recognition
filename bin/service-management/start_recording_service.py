#!/usr/bin/env python3
"""
Start Script for 24/7 Recording Service
Run this to start the recording service on port 8002
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ.setdefault('PYTHONPATH', str(project_root))

if __name__ == "__main__":
    # Import and run the recording service
    import uvicorn
    from recording_service.main import app
    
    print("Starting 24/7 Recording Service...")
    print("Service will be available at: http://localhost:8002")
    print("API Documentation: http://localhost:8002/docs")
    print("Health Check: http://localhost:8002/health")
    print()
    print("Press Ctrl+C to stop the service")
    
    # Create necessary directories
    os.makedirs(project_root / "recordings", exist_ok=True)
    os.makedirs(project_root / "recording_service/logs", exist_ok=True)
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Run the service
    uvicorn.run(
        "recording_service.main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,  # Set to True for development
        log_level="info"
    )