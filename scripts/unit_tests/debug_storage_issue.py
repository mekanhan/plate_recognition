#!/usr/bin/env python
"""
Debug script to diagnose issues with license plate detection and storage.
This script provides detailed logging and verification of the storage process.
"""
import os
import sys
import asyncio
import argparse
import time
import cv2
import numpy as np
import json
import uuid
import logging
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('storage_debug.log')
    ]
)
logger = logging.getLogger("storage_debug")

# Import project modules
from app.services.storage_service import StorageService
from app.services.detection_service import DetectionService
from app.services.license_plate_recognition_service import LicensePlateRecognitionService

class StorageDebugger:
    """Helper class to debug storage issues"""
    
    def __init__(self):
        self.storage_service = None
        self.detection_service = None
        self.lpr_service = None
    
    async def initialize(self):
        """Initialize all services with debug logging"""
        logger.info("Initializing debug session")
        
        # Initialize storage service
        logger.info("Creating storage service")
        self.storage_service = StorageService()
        
        # Monkey patch the _save_data method to add extra logging
        original_save_data = self.storage_service._save_data
        
        async def enhanced_save_data():
            logger.debug(f"Enhanced _save_data called")
            logger.debug(f"Current detections: {len(self.storage_service.plate_database['detections'])}")
            logger.debug(f"Session file: {self.storage_service.session_file}")
            await original_save_data()
            
            # Verify file was created
            if os.path.exists(self.storage_service.session_file):
                file_size = os.path.getsize(self.storage_service.session_file)
                logger.debug(f"File saved: {self.storage_service.session_file} ({file_size} bytes)")
                # Check contents
                try:
                    with open(self.storage_service.session_file, 'r') as f:
                        data = json.load(f)
                        logger.debug(f"File contains {len(data.get('detections', []))} detections")
                except Exception as e:
                    logger.error(f"Error reading saved file: {e}")
            else:
                logger.error(f"File was not created: {self.storage_service.session_file}")
        
        self.storage_service._save_data = enhanced_save_data
        
        # Also enhance add_detections
        original_add_detections = self.storage_service.add_detections
        
        async def enhanced_add_detections(detections):
            logger.debug(f"Enhanced add_detections called with {len(detections)} detections")
            for i, detection in enumerate(detections):
                logger.debug(f"  Detection {i}: {detection.get('plate_text', 'Unknown')} "
                             f"(ID: {detection.get('detection_id', 'No ID')})")
            
            # Check current state before adding
            before_count = len(self.storage_service.plate_database["detections"])
            logger.debug(f"Detections before adding: {before_count}")
            
            # Call original method
            await original_add_detections(detections)
            
            # Check after
            after_count = len(self.storage_service.plate_database["detections"])
            logger.debug(f"Detections after adding: {after_count}")
            logger.debug(f"Difference: {after_count - before_count}")
            
            # Force an immediate save for debugging
            logger.debug("Forcing immediate save for debugging")
            await self.storage_service._save_data()
        
        self.storage_service.add_detections = enhanced_add_detections
        
        # Initialize with debug options
        logger.info("Initializing storage service")
        await self.storage_service.initialize()
        logger.info(f"Storage service initialized. Session file: {self.storage_service.session_file}")
        
        # Initialize LPR service
        logger.info("Initializing license plate recognition service")
        self.lpr_service = LicensePlateRecognitionService()
        await self.lpr_service.initialize()
        logger.info("LPR service initialized")
        
        # Initialize detection service
        logger.info("Initializing detection service")
        self.detection_service = DetectionService()
        self.detection_service.license_plate_service = self.lpr_service
        self.detection_service.storage_service = self.storage_service
        await self.detection_service.initialize()
        logger.info("Detection service initialized")
        
        # Enhance process_detection in detection service
        original_process_detection = self.detection_service.process_detection
        
        async def enhanced_process_detection(detection_id, detection_result):
            logger.debug(f"Enhanced process_detection called")
            logger.debug(f"  Detection ID: {detection_id}")
            logger.debug(f"  Plate text: {detection_result.get('plate_text', 'Unknown')}")
            logger.debug(f"  Confidence: {detection_result.get('confidence', 0)}")
            logger.debug(f"  Storage service available: {hasattr(self.detection_service, 'storage_service')}")
            
            # Call original method
            await original_process_detection(detection_id, detection_result)
            
            logger.debug("process_detection completed")
        
        self.detection_service.process_detection = enhanced_process_detection
    
    async def shutdown(self):
        """Shut down all services"""
        logger.info("Shutting down services")
        if self.detection_service:
            await self.detection_service.shutdown()
        if self.storage_service:
            await self.storage_service.shutdown()
        logger.info("All services shut down")
    
    async def test_with_sample_image(self, image_path=None):
        """Test detection and storage with a sample image"""
        logger.info("Starting test with sample image")
        
        # Get or create test image
        if image_path and os.path.exists(image_path):
            logger.info(f"Loading image from {image_path}")
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Failed to load image. Using generated image instead.")
                image = self.create_test_image()
        else:
            logger.info("Using generated test image")
            image = self.create_test_image()
        
        # Process the image
        logger.info("Processing image for license plate detection")
        display_frame, detections = await self.detection_service.process_frame(image)
        
        logger.info(f"Found {len(detections)} license plates")
        for i, detection in enumerate(detections):
            logger.info(f"  Plate {i+1}: {detection.get('plate_text', 'Unknown')} "
                       f"(Confidence: {detection.get('confidence', 0):.2f})")
        
        # Process each detection
        logger.info("Processing detections for storage")
        for i, detection in enumerate(detections):
            detection_id = f"debug-{uuid.uuid4()}"
            logger.info(f"  Processing detection {i+1} with ID {detection_id}")
            await self.detection_service.process_detection(detection_id, detection)
        
        # Wait for any background processing
        logger.info("Waiting for storage operations to complete")
        await asyncio.sleep(2)
        
        # Verify storage
        self.verify_storage()
    
    def verify_storage(self):
        """Verify storage status"""
        logger.info("Verifying storage")
        
        if not self.storage_service:
            logger.error("Storage service not initialized")
            return
        
        # Check session file
        session_file = self.storage_service.session_file
        logger.info(f"Session file: {session_file}")
        
        if os.path.exists(session_file):
            file_size = os.path.getsize(session_file)
            logger.info(f"File exists: {session_file} ({file_size} bytes)")
            
            # Check contents
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    detection_count = len(data.get("detections", []))
                    logger.info(f"File contains {detection_count} detections")
                    
                    # Log some details about the detections
                    for i, detection in enumerate(data.get("detections", [])[:5]):  # First 5 for brevity
                        logger.info(f"  Detection {i+1}: {detection.get('plate_text', 'Unknown')} "
                                   f"(ID: {detection.get('detection_id', 'No ID')})")
                    
                    if detection_count > 5:
                        logger.info(f"  ... and {detection_count - 5} more")
            except Exception as e:
                logger.error(f"Error reading file: {e}")
        else:
            logger.error(f"File does not exist: {session_file}")
            
            # Check directory
            directory = os.path.dirname(session_file)
            if os.path.exists(directory):
                logger.info(f"Directory exists: {directory}")
                files = os.listdir(directory)
                logger.info(f"Directory contains {len(files)} files")
                for file in files[:10]:  # First 10 for brevity
                    logger.info(f"  {file}")
            else:
                logger.error(f"Directory does not exist: {directory}")
        
        # Check in-memory database
        detection_count = len(self.storage_service.plate_database.get("detections", []))
        logger.info(f"In-memory database contains {detection_count} detections")
    
    def create_test_image(self):
        """Create a test image with a license plate"""
        logger.debug("Creating test image")
        # Create blank image (gray background)
        img = np.ones((720, 1280, 3), dtype=np.uint8) * 200
        
        # Add a car-like shape
        cv2.rectangle(img, (440, 300), (840, 500), (120, 120, 120), -1)
        cv2.rectangle(img, (500, 350), (780, 450), (150, 150, 150), -1)
        
        # Add license plate
        plate_x1, plate_y1 = 550, 380
        plate_x2, plate_y2 = 730, 430
        
        # White plate background
        cv2.rectangle(img, (plate_x1, plate_y1), (plate_x2, plate_y2), (255, 255, 255), -1)
        # Black border
        cv2.rectangle(img, (plate_x1, plate_y1), (plate_x2, plate_y2), (0, 0, 0), 2)
        
        # Add license plate text
        cv2.putText(img, "ABC123", (plate_x1 + 20, plate_y1 + 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        logger.debug("Test image created")
        return img
    
    async def test_direct_storage(self):
        """Test storage directly without going through detection"""
        logger.info("Testing direct storage functionality")
        
        # Create test detection data
        test_detections = [
            {
                "detection_id": f"direct-test-{i}",
                "plate_text": f"TEST{i}",
                "confidence": 0.9,
                "timestamp": time.time(),
                "box": [100, 100, 300, 200],
                "raw_text": f"TEST {i}"
            } for i in range(1, 4)
        ]
        
        # Add directly to storage
        logger.info(f"Adding {len(test_detections)} test detections directly to storage")
        await self.storage_service.add_detections(test_detections)
        
        # Force a save
        logger.info("Forcing save")
        await self.storage_service._save_data()
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Verify storage
        self.verify_storage()

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Debug license plate storage issues")
    parser.add_argument("--image", help="Path to test image (optional)")
    parser.add_argument("--direct", action="store_true", help="Test direct storage without detection")
    args = parser.parse_args()
    
    # Create debugger
    debugger = StorageDebugger()
    
    try:
        # Initialize
        await debugger.initialize()
        
        # Run appropriate test
        if args.direct:
            await debugger.test_direct_storage()
        else:
            await debugger.test_with_sample_image(args.image)
            
    finally:
        # Clean up
        await debugger.shutdown()

if __name__ == "__main__":
    asyncio.run(main())