import asyncio
import json
import os
import time
import datetime
from typing import List, Dict, Any, Optional
from app.utils.plate_database import PlateDatabase
import logging

logger = logging.getLogger(__name__)

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
        self.task = None
    
    async def initialize(self, license_plates_dir: str = "data/license_plates",
                         enhanced_plates_dir: str = "data/enhanced_plates") -> None:
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
        
        logger.info("Storage service initialized")
        logger.info("License plate data will be saved to: %s", self.session_file)
        logger.info("Enhanced results will be saved to: %s", self.enhanced_session_file)
    
    async def shutdown(self) -> None:
        """Shutdown the storage service"""
        # Save any pending data
        await self._save_data()
        
        # Cancel background task
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Storage service shutdown")

    async def _periodic_save(self) -> None:
        """Periodically save data to files"""
        while True:
            current_time = time.time()

            if current_time - self.last_save_time >= self.save_interval:
                await self._save_data()
                self.last_save_time = current_time

            await asyncio.sleep(self.save_interval / 2)  # Check twice as often as save interval

    async def _save_data(self) -> None:
        """Save data to files"""
        async with self.storage_lock:
            # Save raw detections
            if self.plate_database["detections"]:
                with open(self.session_file, 'w') as f:
                    json.dump(self.plate_database, f, indent=2)

            # Save enhanced results
            if self.enhanced_database["enhanced_results"]:
                with open(self.enhanced_session_file, 'w') as f:
                    json.dump(self.enhanced_database, f, indent=2)

    async def add_detections(self, detections: List[Dict[str, Any]]) -> None:
        """Add detections to the database"""
        async with self.storage_lock:
            self.plate_database["detections"].extend(detections)

    async def add_enhanced_results(self, results: List[Dict[str, Any]]) -> None:
        """Add enhanced results to the database"""
        async with self.storage_lock:
            self.enhanced_database["enhanced_results"].extend(results)

    async def get_detections(self) -> List[Dict[str, Any]]:
        """Get all detections"""
        async with self.storage_lock:
            return self.plate_database["detections"].copy()

    async def get_enhanced_results(self) -> List[Dict[str, Any]]:
        """Get all enhanced results"""
        async with self.storage_lock:
            return self.enhanced_database["enhanced_results"].copy()



