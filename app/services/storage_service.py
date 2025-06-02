import asyncio
import json
import os
import time
from typing import List, Dict, Any, Optional

class StorageService:
    """Service for storing detection data"""
    
    def __init__(self):
        self.license_plates_dir = None
        self.enhanced_plates_dir = None
        self.session_timestamp = None
        self.session_file = None
        self.enhanced_session_file = None
        self.plate_database = None
        self.enhanced_database = None
        self.storage_lock = asyncio.Lock()
        self.last_save_time = 0
        self.save_interval = 10.0  # seconds
    
    async def initialize(self, license_plates_dir: str, enhanced_plates_dir: str) -> None:
        """Initialize the storage service"""
        self.license_plates_dir = license_plates_dir
        self.enhanced_plates_dir = enhanced_plates_dir
        
        # Create directories if they don't exist
        os.makedirs(license_plates_dir, exist_ok=True)
        os.makedirs(enhanced_plates_dir, exist_ok=True)
        
        # Initialize session
        self.session_timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.session_file = os.path.join(license_plates_dir, f"lpr_session_{self.session_timestamp}.json")
        self.enhanced_session_file = os.path.join(enhanced_plates_dir, f"enhanced_session_{self.session_timestamp}.json")
        
        # Initialize database structures
        self.plate_database = {
            "session_start": self.session_timestamp,
            "detections": []
        }
        
        self.enhanced_database = {
            "session_start": self.session_timestamp,
            "enhanced_results": []
        }
        
        # Start background save task
        self.task = asyncio.create_task(self._periodic_save())
        
        print(f"Storage service initialized")
        print(f"License plate data will be saved to: {self.session_file}")
        print(f"Enhanced results will be saved to: {self.enhanced_session_file}")
    
    async def shutdown(self) -> None:
        """Shutdown the storage service"""
        # Save any pending data
        await self._save_data()
        
        # Cancel background task
        if hasattr(self, 'task'):
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError