import asyncio
import json
import os
import time
import datetime
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
        
        print(f"Storage service initialized")
        print(f"License plate data will be saved to: {self.session_file}")
        print(f"Enhanced results will be saved to: {self.enhanced_session_file}")
    
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

        print("Storage service shutdown")

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


class PlateDatabase:
    """Handler for the local plate database"""
    
    def __init__(self, db_file: str = "data/known_plates.json"):
        self.db_file = db_file
        self.plates = []
        self._load_database()
        
    def _load_database(self) -> None:
        """Load the database from file"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    self.plates = [plate["plate_number"] for plate in data.get("plates", [])]
                    self.full_data = data
                print(f"Loaded {len(self.plates)} known plates from database")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading database: {e}")
                self.plates = []
                self.full_data = {"plates": [], "last_updated": datetime.datetime.now().strftime("%Y-%m-%d")}
        else:
            # Initialize with VBR7660 as requested
            self.plates = ["VBR7660"]
            self.full_data = {
                "plates": [{"plate_number": "VBR7660", "first_seen": datetime.datetime.now().strftime("%Y-%m-%d"), "metadata": {}}],
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            print("Created new plate database with VBR7660")
            self._save_database()
    
    def _save_database(self) -> None:
        """Save the database to file"""
        self.full_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(self.db_file, 'w') as f:
            json.dump(self.full_data, f, indent=2)
            
    def get_all_plates(self) -> List[str]:
        """Get all known plates"""
        return self.plates
    
    def add_plate(self, plate_number: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a new plate to the database"""
        if plate_number in self.plates:
            return False  # Already exists
            
        new_plate = {
            "plate_number": plate_number,
            "first_seen": datetime.datetime.now().strftime("%Y-%m-%d"),
            "metadata": metadata or {}
        }
        
        self.full_data["plates"].append(new_plate)
        self.plates.append(plate_number)
        self._save_database()
        return True
        
    def auto_add_high_confidence_plates(self, plate_text: str, confidence: float, min_confidence: float = 0.8) -> bool:
        """Automatically add plates with high confidence to the database"""
        if confidence >= min_confidence and plate_text not in self.plates:
            print(f"Auto-adding high confidence plate to database: {plate_text} ({confidence:.2f})")
            return self.add_plate(plate_text)
        return False

