import asyncio
import json
import os
import time
import datetime
import traceback
import uuid
from typing import List, Dict, Any, Optional
from app.utils.plate_database import PlateDatabase
from app.utils.file_helpers import ensure_directory_exists, is_directory_writable, save_json_file, load_json_file
from app.repositories.sql_repository import SQLiteDetectionRepository
from app.database import async_session
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """Service for storing detection data with dual JSON and SQL storage"""
    
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
        self.save_interval = 2.0  # seconds - reduced from 10.0 to save more frequently
        self.task = None
        self.initialization_complete = False
        self.save_count = 0
        self.pending_save = False
        self.save_queued = False
        
        # Add SQL repository for database storage
        self.sql_repository = SQLiteDetectionRepository(async_session)
        self.detections_saved_to_db = 0
        self.detections_saved_to_json = 0
    
    async def initialize(self, license_plates_dir: str = "data/license_plates",
                         enhanced_plates_dir: str = "data/enhanced_plates") -> None:
        """Initialize the storage service"""
        try:
            # Convert relative paths to absolute paths
            self.license_plates_dir = os.path.abspath(license_plates_dir)
            self.enhanced_plates_dir = os.path.abspath(enhanced_plates_dir)
            
            logger.info(f"Storage directories: license_plates={self.license_plates_dir}, enhanced_plates={self.enhanced_plates_dir}")
            
            # Create directories if they don't exist
            if not os.path.exists(self.license_plates_dir):
                logger.info(f"Creating license plates directory: {self.license_plates_dir}")
                os.makedirs(self.license_plates_dir, exist_ok=True)
                
            if not os.path.exists(self.enhanced_plates_dir):
                logger.info(f"Creating enhanced plates directory: {self.enhanced_plates_dir}")
                os.makedirs(self.enhanced_plates_dir, exist_ok=True)
            
            # Check if paths are writable
            # Test write to license plates directory
            test_file = os.path.join(self.license_plates_dir, f"test_write_{time.time()}.txt")
            with open(test_file, 'w') as f:
                f.write("Test write")
            os.remove(test_file)
            
            # Test write to enhanced plates directory
            test_file = os.path.join(self.enhanced_plates_dir, f"test_write_{time.time()}.txt")
            with open(test_file, 'w') as f:
                f.write("Test write")
            os.remove(test_file)
            
            logger.info("Storage directories are writable")
            
            # Initialize session
            self.session_timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.session_file = os.path.join(self.license_plates_dir, f"lpr_session_{self.session_timestamp}.json")
            self.enhanced_session_file = os.path.join(self.enhanced_plates_dir, f"enhanced_session_{self.session_timestamp}.json")
            
            # Initialize database structures with metadata
            self.plate_database = {
                "session_id": str(uuid.uuid4()),
                "session_start": self.session_timestamp,
                "session_metadata": {
                    "source": "camera_service",
                    "configuration": {
                        "model": "yolov11",
                        "storage_version": "1.0"
                    }
                },
                "detections": []
            }
            
            self.enhanced_database = {
                "session_id": str(uuid.uuid4()),
                "session_start": self.session_timestamp,
                "session_metadata": {
                    "enhancement_model": "v1.0",
                    "configuration": {
                        "confidence_threshold": 0.4,
                        "storage_version": "1.0"
                    }
                },
                "enhanced_results": []
            }
            
            # Perform initial save to ensure files are created
            # Save initial empty plate database
            with open(self.session_file, 'w') as f:
                json.dump(self.plate_database, f, indent=2)
                
            # Save initial empty enhanced database
            with open(self.enhanced_session_file, 'w') as f:
                json.dump(self.enhanced_database, f, indent=2)
                
            logger.info("Initial database files created successfully")
            
            # Initialize SQL repository
            await self.sql_repository.initialize()
            logger.info("SQL repository initialized")
            
            # Start background save task
            self.task = asyncio.create_task(self._periodic_save())
            
            self.initialization_complete = True
            
            logger.info("Storage service initialized with dual JSON/SQL storage")
            logger.info("License plate data will be saved to: %s", self.session_file)
            logger.info("Enhanced results will be saved to: %s", self.enhanced_session_file)
            logger.info("Database storage enabled for persistent data")
            
        except Exception as e:
            logger.error(f"Error initializing storage service: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the storage service"""
        # Save any pending data
        try:
            if self.initialization_complete:
                await self._save_data(force=True)
                logger.info("Final data save completed during shutdown")
        except Exception as e:
            logger.error(f"Error during final save: {e}")
            logger.error(traceback.format_exc())
        
        # Cancel background task
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error cancelling background task: {e}")

        logger.info("Storage service shutdown")

    async def _periodic_save(self) -> None:
        """Periodically save data to files"""
        logger.info("Starting periodic save task")
        while True:
            try:
                current_time = time.time()

                # Save if enough time has passed or if a save was explicitly requested
                if (current_time - self.last_save_time >= self.save_interval) or self.pending_save:
                    await self._save_data()
                    self.last_save_time = current_time
                    self.pending_save = False

                await asyncio.sleep(0.5)  # Check more frequently
            except asyncio.CancelledError:
                logger.info("Periodic save task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic save: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(1.0)  # Wait before retrying

    async def _save_data(self, force: bool = False) -> None:
        """Save data to files"""
        if not self.initialization_complete:
            logger.warning("Attempted to save data before initialization complete")
            return
        
        # If already saving, just mark as pending and return
        if self.save_queued and not force:
            self.pending_save = True
            return
            
        self.save_queued = True
        try:
            async with self.storage_lock:
                # Save raw detections
                detection_count = len(self.plate_database["detections"])
                logger.debug(f"Attempting to save {detection_count} detections")
                
                if detection_count > 0 or force:
                    try:
                        # Save in a separate task to avoid blocking
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(
                            None,
                            self._sync_save_detections,
                            self.plate_database,
                            self.session_file
                        )
                        
                        self.save_count += 1
                        logger.info(f"Successfully saved {detection_count} detections to {self.session_file} (Save #{self.save_count})")
                    except Exception as e:
                        logger.error(f"Error saving detections to file: {e}")
                        logger.error(traceback.format_exc())

                # Save enhanced results
                enhanced_count = len(self.enhanced_database["enhanced_results"])
                logger.debug(f"Attempting to save {enhanced_count} enhanced results")
                
                if enhanced_count > 0 or force:
                    try:
                        # Save in a separate task to avoid blocking
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(
                            None,
                            self._sync_save_enhanced,
                            self.enhanced_database,
                            self.enhanced_session_file
                        )
                        
                        logger.info(f"Successfully saved {enhanced_count} enhanced results to {self.enhanced_session_file} (Save #{self.save_count})")
                    except Exception as e:
                        logger.error(f"Error saving enhanced results to file: {e}")
                        logger.error(traceback.format_exc())
        finally:
            self.save_queued = False
                
    def _sync_save_detections(self, data, filepath):
        """Synchronous method to save detections (used with run_in_executor)"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Create temp file for atomic write
            temp_file = f"{filepath}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Rename temp file to final file (atomic operation)
            os.replace(temp_file, filepath)
            return True
        except Exception as e:
            logger.error(f"Error in sync save detections: {e}")
            # Try alternate location
            try:
                recovery_file = f"recovery_lpr_session_{time.time()}.json"
                with open(recovery_file, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Saved recovery file to current directory: {recovery_file}")
            except:
                pass
            return False
            
    def _sync_save_enhanced(self, data, filepath):
        """Synchronous method to save enhanced results (used with run_in_executor)"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Create temp file for atomic write
            temp_file = f"{filepath}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Rename temp file to final file (atomic operation)
            os.replace(temp_file, filepath)
            return True
        except Exception as e:
            logger.error(f"Error in sync save enhanced: {e}")
            # Try alternate location
            try:
                recovery_file = f"recovery_enhanced_session_{time.time()}.json"
                with open(recovery_file, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Saved recovery file to current directory: {recovery_file}")
            except:
                pass
            return False
    
    async def add_detections(self, detections: List[Dict[str, Any]]) -> None:
        """Add detections to both JSON and SQL storage"""
        if not detections:
            logger.debug("No detections to add")
            return

        if not self.initialization_complete:
            logger.warning("Attempted to add detections before initialization complete")
            return

        async with self.storage_lock:
            logger.info(f"Adding {len(detections)} detections to storage (JSON + SQL)")
            
            # Add timestamp and ID if missing
            for detection in detections:
                if "timestamp" not in detection:
                    detection["timestamp"] = time.time()
                    
                # Add status if missing
                if "status" not in detection:
                    detection["status"] = "active"
                    
                # Add unique ID if missing
                if "detection_id" not in detection:
                    detection["detection_id"] = str(uuid.uuid4())
            
            # Save to JSON storage (existing logic)
            self.plate_database["detections"].extend(detections)
            logger.debug(f"Total detections in JSON database: {len(self.plate_database['detections'])}")
            self.detections_saved_to_json += len(detections)

            # Save to SQL database
            try:
                await self.sql_repository.add_detections(detections)
                self.detections_saved_to_db += len(detections)
                logger.info(f"Successfully saved {len(detections)} detections to SQL database")
            except Exception as e:
                logger.error(f"Error saving detections to SQL database: {e}")
                logger.error(traceback.format_exc())

            # Don't force immediate save - just mark as pending for JSON
            self.pending_save = True
            
            # Log details of first detection for debugging
            if detections:
                first_detection = detections[0]
                logger.info(f"Added detection: ID={first_detection.get('detection_id', 'unknown')}, "
                           f"Plate={first_detection.get('plate_text', 'unknown')}, "
                           f"Confidence={first_detection.get('confidence', 0)}")
                logger.info(f"Storage stats: JSON={self.detections_saved_to_json}, SQL={self.detections_saved_to_db}")

    async def add_enhanced_results(self, results: List[Dict[str, Any]]) -> None:
        """Add enhanced results to the database"""
        if not results:
            logger.debug("No enhanced results to add")
            return
            
        if not self.initialization_complete:
            logger.warning("Attempted to add enhanced results before initialization complete")
            return
            
        async with self.storage_lock:
            logger.debug(f"Adding {len(results)} enhanced results to database")
            
            # Add timestamp and ID if missing
            for result in results:
                if "timestamp" not in result:
                    result["timestamp"] = time.time()
                
                if "enhanced_id" not in result:
                    result["enhanced_id"] = f"enh-{str(uuid.uuid4())}"
                    
                if "enhanced_at" not in result:
                    result["enhanced_at"] = time.time()
            
            self.enhanced_database["enhanced_results"].extend(results)
            logger.debug(f"Total enhanced results in database: {len(self.enhanced_database['enhanced_results'])}")
            
            # Don't force immediate save - just mark as pending
            self.pending_save = True
            
            # Log details of first result for debugging
            if results:
                first_result = results[0]
                logger.info(f"Added enhanced result: ID={first_result.get('enhanced_id', 'unknown')}, "
                           f"Plate={first_result.get('plate_text', 'unknown')}, "
                           f"Confidence={first_result.get('confidence', 0)}")
    
    async def get_detections(self) -> List[Dict[str, Any]]:
        """Get all detections"""
        async with self.storage_lock:
            return [d.copy() for d in self.plate_database["detections"]]

    async def get_enhanced_results(self) -> List[Dict[str, Any]]:
        """Get all enhanced results"""
        async with self.storage_lock:
            return [r.copy() for r in self.enhanced_database["enhanced_results"]]
            
    async def get_detections_by_tracking_id(self, tracking_id: str) -> List[Dict[str, Any]]:
        """
        Get all detections for a specific tracking ID
        
        Args:
            tracking_id: The tracking ID to filter by
            
        Returns:
            List of detection records with the specified tracking ID
        """
        async with self.storage_lock:
            return [d.copy() for d in self.plate_database["detections"] 
                  if d.get("tracking_id") == tracking_id]